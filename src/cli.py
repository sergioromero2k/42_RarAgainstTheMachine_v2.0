from src.chunkers.python_chunker import PythonChunker
from src.chunkers.markdown_chunker import MarkdownChunker
from src.models import MinimalSource, RagDataset, MinimalSearchResults
from src.models import StudentSearchResults
from src.evaluator import evaluate_files
from typing import List
from src.indexer import Indexer
from src.ingestion import Ingestion
from src.retriever import Retriever
from pathlib import Path
from tqdm import tqdm


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

    def answer(self, question: str, k: int = 10) -> None:
        pass

    def answer_dataset(
            self,
            student_search_results_path: str,
            save_directory: str = "data/output/search_results_and_answer"
    ) -> None:
        pass

    def evaluate(self, student_search_results_path: str,
                 dataset_path: str, k: int = 10) -> None:
        """Print Recall@k for the given search results."""
        evaluate_files(student_search_results_path, dataset_path, k)