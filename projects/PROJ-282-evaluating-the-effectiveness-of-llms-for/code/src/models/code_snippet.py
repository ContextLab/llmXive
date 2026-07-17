from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class CodeSnippet:
    """
    Represents a single code snippet extracted from a security vulnerability dataset.
    
    Attributes:
        id: Unique identifier for the snippet (UUID v4).
        language: Programming language of the snippet (e.g., 'c', 'java', 'python').
        source_code: The actual source code content.
        ground_truth_label: Binary label indicating vulnerability status (1=vulnerable, 0=safe).
        ground_truth_category: Specific category of vulnerability (e.g., 'SQL Injection', 'Buffer Overflow').
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    language: str = ""
    source_code: str = ""
    ground_truth_label: int = 0
    ground_truth_category: Optional[str] = None

    def __post_init__(self):
        """Validate required fields after initialization."""
        if not self.language:
            raise ValueError("language cannot be empty")
        if not self.source_code:
            raise ValueError("source_code cannot be empty")
        if self.ground_truth_label not in (0, 1):
            raise ValueError("ground_truth_label must be 0 (safe) or 1 (vulnerable)")

    def to_dict(self) -> dict:
        """Convert the dataclass to a dictionary for serialization."""
        return {
            "id": self.id,
            "language": self.language,
            "source_code": self.source_code,
            "ground_truth_label": self.ground_truth_label,
            "ground_truth_category": self.ground_truth_category
        }


def create_snippet(
    language: str,
    source_code: str,
    ground_truth_label: int,
    ground_truth_category: Optional[str] = None,
    snippet_id: Optional[str] = None
) -> CodeSnippet:
    """
    Factory function to create a CodeSnippet instance with validation.
    
    Args:
        language: Programming language code.
        source_code: The code content.
        ground_truth_label: 1 for vulnerable, 0 for safe.
        ground_truth_category: Optional vulnerability category string.
        snippet_id: Optional custom ID; if None, a UUID is generated.
        
    Returns:
        A validated CodeSnippet instance.
        
    Raises:
        ValueError: If validation constraints are violated.
    """
    if snippet_id is None:
        snippet_id = str(uuid.uuid4())
        
    return CodeSnippet(
        id=snippet_id,
        language=language,
        source_code=source_code,
        ground_truth_label=ground_truth_label,
        ground_truth_category=ground_truth_category
    )
