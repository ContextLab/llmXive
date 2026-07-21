from dataclasses import dataclass
from typing import Optional

@dataclass
class PullRequest:
    """
    Represents a Pull Request with its metadata and classification.
    
    Attributes:
        repo_id: Repository identifier (e.g., 'owner/repo')
        pr_number: Pull request number within the repository
        author: Username of the PR author
        code_lines_changed: Number of lines changed in the PR
        origin_label: Classification label ('Disclosing' or 'Non-Disclosing')
    """
    repo_id: str
    pr_number: int
    author: str
    code_lines_changed: int
    origin_label: str

@dataclass
class ReviewMetrics:
    """
    Statistical metrics for review duration.
    
    Attributes:
        median_time: Median review time (minutes)
        mean_time: Mean review time (minutes)
        std_dev: Standard deviation of review time (minutes)
        sample_size: Number of samples used for calculation
    """
    median_time: float
    mean_time: float
    std_dev: float
    sample_size: int