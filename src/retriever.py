from typing import List
from src.models import MinimalSource
from src.tokenizer import tokenize_text
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
            A list containing the top-k most relevant sources.
        """
        tokenized_query = [tokenize_text(query)]
        results, score = self.bm25_index.retrieve(tokenized_query, k=k)

        retrieved = []
        for pos in results[0]:
            retrieved.append(self.sources_metadata[pos])

        return retrieved
