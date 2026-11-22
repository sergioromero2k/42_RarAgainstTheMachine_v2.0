from src.models import MinimalSource
from src.tokenizer import tokenize_text
from src.errors import RagError
from tqdm import tqdm
from typing import List, Tuple
from pathlib import Path
import bm25s
import json

METADATA_FILE = "sources_metadata.json"
BM25_K1 = 1.5
BM25_B = 0.5


class Indexer:
    """Build, persist, and load a BM25 search index and its source metadata."""

    def __init__(self, index_path: str) -> None:
        """Initialize the indexer with a storage path."""
        self.index_path: str = index_path
        self.bm25_index: bm25s.BM25 | None = None
        self.sources_metadata: List[MinimalSource] = []

    def build_index(self, chunks: List[Tuple[MinimalSource, str]]) -> None:
        """Build a BM25 index from text chunks and their associated metadata.

        Args:
            chunks: A list of tuples containing source metadata and the
                corresponding text content.

        Raises:
            RagError: if there are no chunks to index.
        """
        if not chunks:
            raise RagError("No chunks to index")
        texts: List[str] = []
        self.sources_metadata = []

        for src, text in chunks:
            texts.append(src.file_path + "\n" + text)
            self.sources_metadata.append(src)

        tokens = [tokenize_text(text)
                  for text in tqdm(texts, desc="Tokenizing")]
        self.bm25_index = bm25s.BM25(k1=BM25_K1, b=BM25_B)
        self.bm25_index.index(tokens)

    def save(self) -> None:
        """Save the BM25 index and source metadata to disk.

        Raises:
            RagError: if the index was not built or cannot be written.
        """
        if self.bm25_index is None:
            raise RagError("Nothing to save: the index has not been built")
        directory = Path(self.index_path)
        try:
            directory.mkdir(parents=True, exist_ok=True)
            self.bm25_index.save(self.index_path)
            raw = [src.model_dump() for src in self.sources_metadata]
            with open(directory / METADATA_FILE, "w", encoding="utf-8") as f:
                json.dump(raw, f)
        except OSError as error:
            raise RagError(
                f"Cannot write index to {directory}: {error}") from error

    def load(self) -> None:
        """Load the BM25 index and source metadata from disk.

        Raises:
            RagError: if the index is missing, incomplete or corrupt.
        """
        directory = Path(self.index_path)
        metadata_path = directory / METADATA_FILE
        if not metadata_path.is_file():
            raise RagError(
                f"No index found in {directory}. "
                "Run the index command first.")
        try:
            self.bm25_index = bm25s.BM25.load(self.index_path)
            with open(metadata_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.sources_metadata = [MinimalSource(**item) for item in raw]
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise RagError(
                f"Corrupt or incomplete index in {directory}: {error}"
            ) from error
