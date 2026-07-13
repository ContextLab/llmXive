"""
Base data models for the llmXive research pipeline.

Defines Pydantic models for PullRequest and CodeSnippet entities
used throughout the data acquisition, feature extraction, and analysis phases.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class PullRequest:
    """
    Represents a GitHub Pull Request and its associated metadata.
    
    Fields:
        pr_id: Unique identifier for the PR (e.g., 'owner/repo#number')
        repo_id: Repository identifier (e.g., 'owner/repo')
        author_type: Type of author ('human' or 'llm')
        review_duration: Time in seconds from PR open to first comment/merge
        file_size: Size of the changed files in bytes
        complexity_score: Calculated complexity score (e.g., cyclomatic complexity)
    """
    pr_id: str
    repo_id: str
    author_type: str
    review_duration: float
    file_size: int
    complexity_score: float
    created_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    labels: List[str] = field(default_factory=list)
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary for serialization."""
        return {
            "pr_id": self.pr_id,
            "repo_id": self.repo_id,
            "author_type": self.author_type,
            "review_duration": self.review_duration,
            "file_size": self.file_size,
            "complexity_score": self.complexity_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "merged_at": self.merged_at.isoformat() if self.merged_at else None,
            "labels": self.labels,
            "extra_metadata": self.extra_metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PullRequest":
        """Create a PullRequest instance from a dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        merged_at = data.get("merged_at")
        if isinstance(merged_at, str):
            merged_at = datetime.fromisoformat(merged_at)

        return cls(
            pr_id=data["pr_id"],
            repo_id=data["repo_id"],
            author_type=data["author_type"],
            review_duration=data["review_duration"],
            file_size=data["file_size"],
            complexity_score=data["complexity_score"],
            created_at=created_at,
            merged_at=merged_at,
            labels=data.get("labels", []),
            extra_metadata=data.get("extra_metadata", {})
        )


@dataclass
class CodeSnippet:
    """
    Represents a code snippet extracted from a commit or generated synthetically.
    
    Fields:
        snippet_id: Unique identifier for the snippet
        source_commit: Commit hash or ID where the snippet originated
        generation_source: Source of the snippet ('human', 'llm-generated', 'synthetic')
        complexity_metrics: Dictionary of complexity metrics (LOC, cyclomatic, etc.)
        semantic_similarity_score: Float score indicating semantic similarity to reference
        content: The actual code content
    """
    snippet_id: str
    source_commit: str
    generation_source: str
    complexity_metrics: Dict[str, float]
    semantic_similarity_score: float
    content: str
    language: Optional[str] = None
    file_path: Optional[str] = None
    generated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary for serialization."""
        return {
            "snippet_id": self.snippet_id,
            "source_commit": self.source_commit,
            "generation_source": self.generation_source,
            "complexity_metrics": self.complexity_metrics,
            "semantic_similarity_score": self.semantic_similarity_score,
            "content": self.content,
            "language": self.language,
            "file_path": self.file_path,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeSnippet":
        """Create a CodeSnippet instance from a dictionary."""
        generated_at = data.get("generated_at")
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at)

        return cls(
            snippet_id=data["snippet_id"],
            source_commit=data["source_commit"],
            generation_source=data["generation_source"],
            complexity_metrics=data["complexity_metrics"],
            semantic_similarity_score=data["semantic_similarity_score"],
            content=data["content"],
            language=data.get("language"),
            file_path=data.get("file_path"),
            generated_at=generated_at
        )