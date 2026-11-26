from src.models import (
    MinimalSource,
    StudentSearchResults,
    RagDataset,
    AnsweredQuestion,
)
from src.loading import load_dataset, load_search_results
from src.errors import RagError


IOU_THRESHOLD = 0.05
RECALL_KS = (1, 3, 5, 10)


def iou(a_start: int, a_end: int, b_start: int, b_end: int) -> float:
    """Return the IoU between two character ranges."""
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    intersection = max(0, end - start)
    union = max(a_end, b_end) - min(a_start, b_start)

    if union == 0:
        return 0.0
    return intersection/union


def is_match(retrieved: MinimalSource, correct: MinimalSource) -> bool:
    """Return True if both point to the same file and overlap enough."""
    if retrieved.file_path != correct.file_path:
        return False

    overlap = iou(
        retrieved.first_character_index,
        retrieved.last_character_index,
        correct.first_character_index,
        correct.last_character_index)
    return overlap >= IOU_THRESHOLD


def question_recall_at_k(
        retrieved: list[MinimalSource],
        correct: list[MinimalSource],
        k: int) -> float:
    """Return the share of correct sources found in the top k."""
    if not correct:
        return 0.0
    found = 0
    for src in correct:
        for piece in retrieved[:k]:
            if is_match(piece, src):
                found += 1
                break
    return found / len(correct)


def build_results_index(
        results: StudentSearchResults) -> dict[str, list[MinimalSource]]:
    """Map each question_id to its retrieved sources."""
    index: dict[str, list[MinimalSource]] = {}
    for r in results.search_results:
        index[r.question_id] = r.retrieved_sources
    return index


def source_recall_at_k(
        results: StudentSearchResults,
        dataset: RagDataset,
        k: int) -> float:
    """Mean over questions of the share of correct sources found."""
    index = build_results_index(results)
    score_sum = 0.0
    total = 0
    for question in dataset.rag_questions:
        if not isinstance(question, AnsweredQuestion):
            continue
        total += 1
        retrieved = index.get(question.question_id, [])
        score_sum += question_recall_at_k(retrieved, question.sources, k)
    if total == 0:
        return 0.0
    return score_sum / total


def evaluate_files(student_search_results_path: str,
                   dataset_path: str, k: int = 10) -> None:
    """Print Recall@k for the given search results and dataset.

    Args:
        student_search_results_path: JSON with the search results.
        dataset_path: JSON of the ground-truth (answered) dataset.
        k: Largest k to report.

    Raises:
        RagError: on invalid k, unreadable files or mismatched datasets.
    """
    if not isinstance(k, int) or k < 1:
        raise RagError("k must be an integer >= 1")
    results = load_search_results(student_search_results_path)
    dataset = load_dataset(dataset_path)

    answered = [q for q in dataset.rag_questions
                if isinstance(q, AnsweredQuestion)]
    if not answered:
        raise RagError(
            "The dataset has no answered questions: "
            "use the AnsweredQuestions file")
    index = build_results_index(results)
    if not any(q.question_id in index for q in answered):
        raise RagError(
            "No question of the dataset appears in the search results: "
            "are they from the same dataset?")

    for n in RECALL_KS:
        if n > k:
            continue
        recall = source_recall_at_k(results, dataset, n)
        print(f"recall@{n}: {recall * 100:.1f}%")
