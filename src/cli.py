from src.chunkers.python_chunker import PythonChunker
from src.chunkers.markdown_chunker import MarkdownChunker
from src.models import MinimalSource, RagDataset, MinimalSearchResults
from src.generator import Generator
from src.models import MinimalAnswer, StudentSearchResultsAndAnswer
from src.models import StudentSearchResults
from src.evaluator import evaluate_files
from typing import List
from src.indexer import Indexer
from src.ingestion import Ingestion
from src.retriever import Retriever
from pathlib import Path
from tqdm import tqdm
import uuid


class RAGSystem:
    def __init__(
            self, index_path: str = "data/processed",
            raw_data_path: str = "data/raw/vllm-0.10.1") -> None:

        self.chunkers = {
            ".py": PythonChunker(),
            ".md": MarkdownChunker(),
            ".txt": MarkdownChunker()
        }
        self.ingestion: Ingestion = Ingestion(self.chunkers, raw_data_path)
        self.indexer: Indexer = Indexer(index_path)
        self.retriever: Retriever | None = None
        self.generator: Generator | None = None

    def index(self, max_chunk_size: int = 2000) -> None:
        self.indexer.build_index(self.ingestion.ingest(max_chunk_size))
        self.indexer.save()

    def search(self, question: str, k: int = 10) -> List[MinimalSource]:
        if self.retriever is None:
            self.indexer.load()
            self.retriever = Retriever(
                self.indexer.bm25_index, self.indexer.sources_metadata)
        return self.retriever.search(question, k)

    def search_dataset(
            self,
            dataset_path: str,
            k: int = 10,
            save_directory: str = "data/output/search_results",
    ) -> None:
        path = Path(dataset_path)
        if not path.is_file():
            print(f"Error: dataset file not found: {dataset_path}")
            return

        with open(dataset_path, "r") as f:
            content = f.read()

        dataset = RagDataset.model_validate_json(content)
        results = []
        for question in tqdm(dataset.rag_questions):
            sources = self.search(question.question, k)
            results.append(MinimalSearchResults(
                question_id=question.question_id,
                question=question.question,
                retrieved_sources=sources
            ))

        data = StudentSearchResults(search_results=results, k=k)
        out_dir = Path(save_directory)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / path.name

        with open(out_file, "w") as f:
            f.write(data.model_dump_json())

        print(f"Saved student_search_results to {out_file}")

    def evaluate(self, student_search_results_path: str,
                 dataset_path: str, k: int = 10) -> None:
        """Print Recall@k for the given search results."""
        evaluate_files(student_search_results_path, dataset_path, k)

    def _get_generator(self) -> Generator:
        if self.generator is None:
            self.generator = Generator()
        return self.generator

    def answer(self, question: str, k: int = 5) -> None:
        sources = self.search(question, k)
        text = self._get_generator().answer(question, sources)
        result = MinimalAnswer(
            question_id=str(uuid.uuid4()),
            question=question,
            retrieved_sources=sources,
            answer=text,
        )
        print(result.model_dump_json(indent=2))

    def answer_dataset(
            self,
            student_search_results_path: str,
            save_directory: str = "data/output/search_results_and_answer",
    ) -> None:
        path = Path(student_search_results_path)
        if not path.is_file():
            print(f"Error: file not found: {student_search_results_path}")
            return

        results = StudentSearchResults.model_validate_json(path.read_text())
        generator = self._get_generator()
        answers = []
        for item in tqdm(results.search_results):
            answers.append(MinimalAnswer(
                question_id=item.question_id,
                question=item.question,
                retrieved_sources=item.retrieved_sources,
                answer=generator.answer(
                    item.question, item.retrieved_sources),
            ))

        data = StudentSearchResultsAndAnswer(
            search_results=answers, k=results.k)
        out_dir = Path(save_directory)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / path.name
        out_file.write_text(data.model_dump_json())
        print(f"Saved student_search_results_and_answer to {out_file}")
