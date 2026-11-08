from pathlib import Path
from zipfile import ZipFile, BadZipFile
from typing import List, Tuple
from src.models import MinimalSource
from src.errors import RagError
from src.chunkers.base_chunker import BaseChunker
from tqdm import tqdm
import sys


MIN_CHUNK_SIZE = 1
MAX_CHUNK_SIZE = 2000


class Ingestion:
    """Loads repository files and splits them into chunks."""

    def __init__(
            self, chunkers: dict[str, BaseChunker],
            raw_data_path: str = "data/raw/vllm-0.10.1") -> None:
        """Initialize ingestion with chunkers and the repository path."""
        self.chunkers: dict[str, BaseChunker] = chunkers
        self.raw_data_path: str = raw_data_path

    def ensure_repo_extracted(self) -> None:
        """Extract the repository archive if it is not already available.

        Raises:
            RagError: if neither the repository nor its zip exist,
                or if the zip file is corrupt.
        """
        path = Path(self.raw_data_path)
        if path.exists():
            return
        zip_path = Path(self.raw_data_path + ".zip")
        if not zip_path.is_file():
            raise RagError(
                f"Repository not found: {path} (and no {zip_path})")
        try:
            with ZipFile(zip_path, "r") as zip_file:
                zip_file.extractall(zip_path.parent)
        except BadZipFile as error:
            raise RagError(f"Corrupt zip file: {zip_path}") from error

    def _read_file(self, path: Path) -> str | None:
        """Return the file content, or None if it cannot be read."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except (OSError, UnicodeDecodeError) as error:
            print(f"Warning: skipping {path}: {error}", file=sys.stderr)
            return None

    def ingest(self, max_chunk_size: int) -> List[Tuple[MinimalSource, str]]:
        """Read supported files and return their chunks with metadata.

        Raises:
            RagError: if max_chunk_size is lower than 1 or no file is found.
        """
        if (not isinstance(max_chunk_size, int)
                or max_chunk_size < MIN_CHUNK_SIZE):
            raise RagError(
                f"max_chunk_size must be an integer >= {MIN_CHUNK_SIZE}")
        if max_chunk_size > MAX_CHUNK_SIZE:
            print(f"Warning: chunks above {MAX_CHUNK_SIZE} characters "
                  "are rejected by the grader", file=sys.stderr)
        self.ensure_repo_extracted()
        repo = Path(self.raw_data_path)
        files = sorted(
            p for p in repo.rglob("*")
            if p.is_file() and p.suffix.lower() in self.chunkers)
        if not files:
            raise RagError(f"No supported files found in {repo}")

        results: List[Tuple[MinimalSource, str]] = []
        for path in tqdm(files, desc="Chunking"):
            content = self._read_file(path)
            if content is None:
                continue
            chunker = self.chunkers[path.suffix.lower()]
            sources = chunker.chunk(content, str(path), max_chunk_size)
            for src in sources:
                text = content[
                    src.first_character_index:src.last_character_index]
                results.append((src, text))
        return results
