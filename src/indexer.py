from src.models import MinimalSource
from src.tokenizer import tokenize_text
from typing import List, Tuple
from pathlib import Path
import bm25s
import json


class Indexer:
    """Build, persist, and load a BM25 search index and its source metadata."""

    def __init__(self, index_path: str) -> None:
        """"Initialize the indexer with a storage path."""
        self.index_path: str = index_path
        self.bm25_index: bm25s.BM25 | None = None
        self.sources_metadata: List[MinimalSource] = []

    def build_index(self, chunks: List[Tuple[MinimalSource, str]]) -> None:
        """Build a BM25 index from text chunks and their associated metadata.

        Args:
            chunks: A list of tuples containing source metadata and the
                corresponding text content.
        """
        texts = []
        self.sources_metadata = []

        for src, text in chunks:
            texts.append(src.file_path + "\n" + text)
            self.sources_metadata.append(src)

        tokens = [tokenize_text(text) for text in texts]
        self.bm25_index = bm25s.BM25()
        self.bm25_index.index(tokens)

    def save(self) -> None:
        """Save the BM25 index and source metadata to disk."""
        Path(self.index_path).mkdir(parents=True, exist_ok=True)
        self.bm25_index.save(self.index_path)

        list_dict = []
        for src in self.sources_metadata:
            list_dict.append(src.model_dump())

        path_metadata = self.index_path + "/sources_metadata.json"
        with open(path_metadata, "w") as f:
            json.dump(list_dict, f)

    def load(self) -> None:
        """Load the BM25 index and source metadata from disk."""
        self.bm25_index = bm25s.BM25.load(self.index_path)
        path_metadata = self.index_path + "/sources_metadata.json"
        self.sources_metadata = []

        with open(path_metadata, "r") as f:
            list_dictionario = json.load(f)

        for d in list_dictionario:
            source = MinimalSource(**d)
            self.sources_metadata.append(source)
