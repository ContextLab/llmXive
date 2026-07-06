"""
Data models and entities for the codebase age impact analysis.

This module defines the core data structures used throughout the pipeline:
- Snippet: Represents a code snippet extracted from a repository.
- Repository: Metadata about a source code repository.
- InferenceResult: Results from running an LLM on a snippet.
- FileMetric: Aggregated metrics at the file level.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Snippet:
    """
    Represents a function-level code snippet extracted from a repository.

    Attributes:
        snippet_id: Unique identifier for the snippet.
        repo_url: URL of the source repository.
        file_path: Path to the file within the repository.
        median_commit_age: Median age of commits touching this file (in days).
        snippet_content: The actual source code content of the snippet.
        token_count: Number of tokens in the snippet.
        complexity: Cyclomatic complexity or similar metric.
    """
    snippet_id: str
    repo_url: str
    file_path: str
    median_commit_age: float
    snippet_content: str
    token_count: int
    complexity: float


@dataclass
class Repository:
    """
    Represents metadata about a source code repository.

    Attributes:
        repo_url: URL of the repository.
        commit_count: Total number of commits in the repository.
        median_age: Median age of all commits in the repository (in days).
    """
    repo_url: str
    commit_count: int
    median_age: float


@dataclass
class InferenceResult:
    """
    Represents the result of running an LLM inference on a snippet.

    Attributes:
        snippet_id: Reference to the snippet being evaluated.
        perplexity: Perplexity score from the language model.
        functional_correctness_rate: Rate of functional correctness (0.0 to 1.0).
        status: Status of the inference run (e.g., 'success', 'timeout', 'error').
    """
    snippet_id: str
    perplexity: Optional[float]
    functional_correctness_rate: Optional[float]
    status: str


@dataclass
class FileMetric:
    """
    Represents aggregated metrics for a specific file.

    Attributes:
        file_path: Path to the file.
        mean_perplexity: Mean perplexity of all snippets in the file.
        mean_correctness: Mean functional correctness rate of snippets in the file.
        mean_complexity: Mean complexity of snippets in the file.
        mean_length: Mean token length of snippets in the file.
        median_age: Median commit age for the file.
    """
    file_path: str
    mean_perplexity: float
    mean_correctness: float
    mean_complexity: float
    mean_length: float
    median_age: float