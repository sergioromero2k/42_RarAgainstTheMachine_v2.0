from typing import List
from src.models import MinimalSource
from src.tokenizer import tokenize_text
from src.errors import RagError
import bm25s


class Retriever:
    """Retrieves relevant sources using a BM25 search index."""

    def __init__(self, bm25_index: bm25s.BM25,
                 sources_metadata: List[MinimalSource]) -> None:
        """
        Initialize the retriever.

        Args:
            bm25_index: BM25 index used to retrieve relevant documents.
            sources_metadata: Metadata associated with the indexed sources.
        """
        self.bm25_index: bm25s.BM25 = bm25_index
        self.sources_metadata: List[MinimalSource] = sources_metadata

    def search(self, query: str, k: int) -> List[MinimalSource]:
        """
        Retrieve the top-k sources matching the given query.

        Args:
            query: Search query used to find relevant sources.
            k: Maximum number of sources to retrieve.

        Returns:
            Up to k relevant sources, best first. Empty if the query has
            no usable words or nothing in the index matches it.

        Raises:
            RagError: if k is not a positive integer.
        """
        if not isinstance(k, int) or k < 1:
            raise RagError("k must be an integer >= 1")
        tokens = tokenize_text(str(query))
        if not tokens or not self.sources_metadata:
            return []

        k = min(k, len(self.sources_metadata))
        results, scores = self.bm25_index.retrieve([tokens], k=k)

        retrieved: List[MinimalSource] = []
        for pos, score in zip(results[0], scores[0]):
            if score > 0:
                retrieved.append(self.sources_metadata[pos])
        return retrieved
