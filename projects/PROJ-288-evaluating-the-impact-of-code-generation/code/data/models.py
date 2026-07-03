"""
Data models and entities for the code generation impact study.

Defines core data structures for Pull Requests and Review Metrics
used throughout the pipeline.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PullRequest:
    """
    Represents a GitHub Pull Request with classification metadata.
    
    Attributes:
        repo_id: Unique identifier for the repository (e.g., 'owner/repo')
        pr_number: The PR number within the repository
        author: GitHub username of the PR author
        code_lines_changed: Total number of lines changed in the PR
        origin_label: Classification label indicating origin source
                      Expected values: 'Disclosing', 'Non-Disclosing', or None
    """
    repo_id: str
    pr_number: int
    author: str
    code_lines_changed: int
    origin_label: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert the PullRequest instance to a dictionary."""
        return {
            "repo_id": self.repo_id,
            "pr_number": self.pr_number,
            "author": self.author,
            "code_lines_changed": self.code_lines_changed,
            "origin_label": self.origin_label
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PullRequest":
        """Create a PullRequest instance from a dictionary."""
        return cls(
            repo_id=data["repo_id"],
            pr_number=data["pr_number"],
            author=data["author"],
            code_lines_changed=data["code_lines_changed"],
            origin_label=data.get("origin_label")
        )


@dataclass
class ReviewMetrics:
    """
    Statistical metrics derived from review time data.
    
    Attributes:
        median_time: Median review time in minutes
        mean_time: Mean review time in minutes
        std_dev: Standard deviation of review times in minutes
        sample_size: Number of observations in the sample
    """
    median_time: float
    mean_time: float
    std_dev: float
    sample_size: int

    def to_dict(self) -> dict:
        """Convert the ReviewMetrics instance to a dictionary."""
        return {
            "median_time": self.median_time,
            "mean_time": self.mean_time,
            "std_dev": self.std_dev,
            "sample_size": self.sample_size
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReviewMetrics":
        """Create a ReviewMetrics instance from a dictionary."""
        return cls(
            median_time=float(data["median_time"]),
            mean_time=float(data["mean_time"]),
            std_dev=float(data["std_dev"]),
            sample_size=int(data["sample_size"])
        )