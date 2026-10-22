from pathlib import Path
from src.models import (
    MinimalSource,
    StudentSearchResults,
    RagDataset,
    AnsweredQuestion,
)


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


def build_results_index(
        results: StudentSearchResults) -> dict[str, list[MinimalSource]]:
    """Map each question_id to its retrieved sources."""
    index = {}
    for r in results.search_results:
        index[r.question_id] = r.retrieved_sources
    return index


def is_match(retrieved: MinimalSource, correct: MinimalSource) -> bool:
    """Returns True if both point to the same file and overlap enough."""
    if retrieved.file_path != correct.file_path:
        return False

    a_start = retrieved.first_character_index
    a_end = retrieved.last_character_index
    b_start = correct.first_character_index
    b_end = correct.last_character_index
    iou_match = iou(a_start, a_end, b_start, b_end)
    if (iou_match >= IOU_THRESHOLD):
        return True
    return False


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
        retrieved = index[question.question_id]
        score_sum += question_recall_at_k(retrieved, question.sources, k)
    if total == 0:
        return 0.0
    return score_sum / total


def recall_at_k(results: StudentSearchResults,
                dataset: RagDataset, k: int) -> float:
    """Returns the fraction of questions with a hit in the top k."""
    index = build_results_index(results)
    answered_hits = 0
    answered_total = 0
    for question in dataset.rag_questions:
        if not isinstance(question, AnsweredQuestion):
            continue
        answered_total += 1
        retrieved = index[question.question_id]
        if hit_at_k(retrieved, question.sources, k):
            answered_hits += 1

    if answered_total == 0:
        return 0.0
    return answered_hits / answered_total


def evaluate_files(student_search_results_path: str,
                   dataset_path: str, k: int = 10) -> None:
    """Print Recall@k for the given search results and dataset."""
    results = StudentSearchResults.model_validate_json(
        Path(student_search_results_path).read_text())
    dataset = RagDataset.model_validate_json(
        Path(dataset_path).read_text())

    for n in RECALL_KS:
        if n > k:
            continue
        recall = source_recall_at_k(results, dataset, n)
        print(f"recall@{n}: {recall * 100:.1f}%")
