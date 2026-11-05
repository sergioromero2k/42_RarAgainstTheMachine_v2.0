"""
Data models for the RAG against the machine project.
These models ensure type safety and data integrity using Pydantic.
"""

from pydantic import BaseModel, Field
from typing import List
import uuid


class MinimalSource(BaseModel):
    """
    Represents a specific fragment of a file in the repository.
    Includes the file path and the exact character boundaries.
    The fragment is content[first_character_index:last_character_index], so
    the last index is exclusive.
    """

    file_path: str
    first_character_index: int
    last_character_index: int


class UnansweredQuestion(BaseModel):
    """
    Rerpresents a question that has not yet been processed by the RAG system.
    Includes a unique identifier and the question text.
    """

    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str


class AnsweredQuestion(UnansweredQuestion):
    """
    Represents a question with its ground truth answer and source citations.
    Inherits from UnansweredQuestion.
    """

    sources: List[MinimalSource]
    answer: str


class RagDataset(BaseModel):
    """
    A collection of questions, which can be either answered or unanswered.
    Used for loading datasets from JSON files.
    """

    rag_questions: List[AnsweredQuestion | UnansweredQuestion]


class MinimalSearchResults(BaseModel):
    """
    Contains the retrieval results for a specific question.
    Lists the top-k sources found by the search system.
    """

    question_id: str
    question: str
    retrieved_sources: List[MinimalSource]


class MinimalAnswer(MinimalSearchResults):
    """
    Represents the final output for a question, including the generated answer.
    Inherits from MinimalSearchResults to keep citation context.
    """

    answer: str


class StudentSearchResults(BaseModel):
    """
    The standardized output for search operations on a dataset.
    Includes a list of results and the k parameter used.
    """

    search_results: List[MinimalSearchResults]
    k: int


class StudentSearchResultsAndAnswer(BaseModel):
    """
    The final output containing both retrieved sources and generated answers.
    Used for the 'answer_dataset' command.
    """
    search_results: List[MinimalAnswer]
