from abc import ABC, abstractmethod
from src.models import MinimalSource
from typing import List


MINIMUM_THRESHOLD = 100
OVERLAP_SIZE = 200


class BaseChunker(ABC):
    """
    Abstract base class for document chunkers.

    A chunker is responsible for splitting the content of a file into
    smaller chunks while preserving enough information to reconstruct
    their location in the original document.
    """

    def __init__(self,
                 minimum_threshold: int = MINIMUM_THRESHOLD,
                 overlap_size: int = OVERLAP_SIZE):
        """Initialize the chunker.

        Args:
            minimum_threshold: Fragments shorter than this may be merged
                with a neighbour.
            overlap_size: Characters repeated between consecutive chunks.
        """
        self.minimum_threshold = minimum_threshold
        self.overlap_size = overlap_size

    @abstractmethod
    def chunk(
            self,
            content: str,
            file_path: str,
            max_chunk_size: int) -> List[MinimalSource]:
        """Split content into chunks.

        Args:
            content: Full text of the file.
            file_path: Path stored in each returned source.
            max_chunk_size: Maximum characters allowed per chunk.

        Returns:
            One MinimalSource per chunk, with its character range.
        """
        pass

    def _save_fragment(
            self,
            fragments: list,
            text: str,
            start_offset: int
    ) -> int:
        """Append a fragment and return the offset where it ends."""
        if not text:
            return start_offset
        end_offset = start_offset + len(text)
        fragments.append({
            'text': text,
            'start': start_offset,
            'end': end_offset
        })
        return end_offset
