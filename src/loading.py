"""Helpers to read and validate JSON files."""

from pathlib import Path

from pydantic import ValidationError

from src.errors import RagError
from src.models import RagDataset, StudentSearchResults


def _read_text(path: str) -> str:
    """Return the text of a file, or raise RagError."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise RagError(f"Cannot read {path}: {error}") from error


def load_search_results(path: str) -> StudentSearchResults:
    """Read a search results JSON file."""
    text = _read_text(path)
    try:
        return StudentSearchResults.model_validate_json(text)
    except ValidationError as error:
        raise RagError(f"{path} is not a valid search results file") from error


def load_dataset(path: str) -> RagDataset:
    """Read a dataset JSON file."""
    text = _read_text(path)
    try:
        return RagDataset.model_validate_json(text)
    except ValidationError as error:
        raise RagError(f"{path} is not a valid dataset file") from error
