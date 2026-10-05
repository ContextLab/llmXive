"""
Schema definitions for the extraction module.

Defines data classes for PullRequest, BugDetection, and AlignmentResult
to structure data flowing through the extraction pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class Severity(Enum):
    """Severity levels for bug detection."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    STYLE = "style"
    INFO = "info"

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Convert string to Severity enum, case-insensitive."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid severity level: {value}")

    def __str__(self) -> str:
        return self.value


@dataclass
class PullRequest:
    """
    Represents a GitHub Pull Request with associated metadata.
    
    Attributes:
        pr_id: Unique identifier for the PR (e.g., "12345")
        repo_name: Repository name in "owner/repo" format
        title: PR title
        body: PR description body
        state: PR state (open, closed, merged)
        created_at: ISO 8601 timestamp of creation
        updated_at: ISO 8601 timestamp of last update
        merged_at: ISO 8601 timestamp if merged, else None
        author: Username of the PR author
        diff: The full diff content of the PR
        linked_issue_ids: List of issue IDs linked to this PR
        comments: List of comment dictionaries associated with the PR
        llm_code_flag: Boolean indicating if LLM-generated code was detected
        truncation_flag: Boolean indicating if the diff was truncated
        raw_json: Original raw JSON from GitHub API (for reference)
    """
    pr_id: str
    repo_name: str
    title: str
    body: Optional[str]
    state: str
    created_at: str
    updated_at: str
    merged_at: Optional[str]
    author: str
    diff: str
    linked_issue_ids: List[int] = field(default_factory=list)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    llm_code_flag: bool = False
    truncation_flag: bool = False
    raw_json: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert PullRequest to a dictionary for JSON serialization."""
        return {
            "pr_id": self.pr_id,
            "repo_name": self.repo_name,
            "title": self.title,
            "body": self.body,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "merged_at": self.merged_at,
            "author": self.author,
            "diff": self.diff,
            "linked_issue_ids": self.linked_issue_ids,
            "comments": self.comments,
            "llm_code_flag": self.llm_code_flag,
            "truncation_flag": self.truncation_flag,
            "raw_json": self.raw_json,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PullRequest":
        """Create a PullRequest instance from a dictionary."""
        return cls(
            pr_id=str(data.get("pr_id", "")),
            repo_name=data.get("repo_name", ""),
            title=data.get("title", ""),
            body=data.get("body"),
            state=data.get("state", "open"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            merged_at=data.get("merged_at"),
            author=data.get("author", ""),
            diff=data.get("diff", ""),
            linked_issue_ids=data.get("linked_issue_ids", []),
            comments=data.get("comments", []),
            llm_code_flag=data.get("llm_code_flag", False),
            truncation_flag=data.get("truncation_flag", False),
            raw_json=data.get("raw_json"),
        )

    def to_json(self) -> str:
        """Serialize PullRequest to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "PullRequest":
        """Deserialize PullRequest from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class BugDetection:
    """
    Represents a detected bug within a PR diff.
    
    Attributes:
        pr_id: ID of the PR where the bug was found
        file_path: Path to the file containing the bug
        line_start: Starting line number of the bug
        line_end: Ending line number of the bug
        severity: Severity level of the bug
        description: Text description of the bug
        detection_method: Method used to detect (e.g., "llm", "heuristic", "human")
        confidence: Confidence score (0.0 to 1.0)
        is_confirmed: Whether the bug has been confirmed by human review
    """
    pr_id: str
    file_path: str
    line_start: int
    line_end: int
    severity: Severity
    description: str
    detection_method: str
    confidence: float = 0.0
    is_confirmed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert BugDetection to a dictionary for JSON serialization."""
        return {
            "pr_id": self.pr_id,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "severity": str(self.severity),
            "description": self.description,
            "detection_method": self.detection_method,
            "confidence": self.confidence,
            "is_confirmed": self.is_confirmed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BugDetection":
        """Create a BugDetection instance from a dictionary."""
        severity_str = data.get("severity", "info")
        if isinstance(severity_str, str):
            severity = Severity.from_string(severity_str)
        else:
            severity = severity_str

        return cls(
            pr_id=data.get("pr_id", ""),
            file_path=data.get("file_path", ""),
            line_start=data.get("line_start", 0),
            line_end=data.get("line_end", 0),
            severity=severity,
            description=data.get("description", ""),
            detection_method=data.get("detection_method", "unknown"),
            confidence=data.get("confidence", 0.0),
            is_confirmed=data.get("is_confirmed", False),
        )

    def to_json(self) -> str:
        """Serialize BugDetection to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "BugDetection":
        """Deserialize BugDetection from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class AlignmentResult:
    """
    Represents the result of aligning LLM-detected bugs with human-confirmed bugs.
    
    Attributes:
        pr_id: ID of the PR being analyzed
        llm_bug_id: Identifier for the LLM-detected bug
        human_bug_id: Identifier for the human-confirmed bug (or None if unmatched)
        file_path: File path where alignment occurred
        line_start_llm: Start line from LLM detection
        line_end_llm: End line from LLM detection
        line_start_human: Start line from human confirmation (or None)
        line_end_human: End line from human confirmation (or None)
        jaccard_index: Jaccard similarity index for line overlap
        similarity_score: Cosine similarity score for alignment
        is_aligned: Boolean indicating if alignment was successful
        alignment_method: Method used for alignment (e.g., "jaccard", "cosine")
    """
    pr_id: str
    llm_bug_id: str
    human_bug_id: Optional[str]
    file_path: str
    line_start_llm: int
    line_end_llm: int
    line_start_human: Optional[int]
    line_end_human: Optional[int]
    jaccard_index: float
    similarity_score: float
    is_aligned: bool
    alignment_method: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert AlignmentResult to a dictionary for JSON serialization."""
        return {
            "pr_id": self.pr_id,
            "llm_bug_id": self.llm_bug_id,
            "human_bug_id": self.human_bug_id,
            "file_path": self.file_path,
            "line_start_llm": self.line_start_llm,
            "line_end_llm": self.line_end_llm,
            "line_start_human": self.line_start_human,
            "line_end_human": self.line_end_human,
            "jaccard_index": self.jaccard_index,
            "similarity_score": self.similarity_score,
            "is_aligned": self.is_aligned,
            "alignment_method": self.alignment_method,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlignmentResult":
        """Create an AlignmentResult instance from a dictionary."""
        return cls(
            pr_id=data.get("pr_id", ""),
            llm_bug_id=data.get("llm_bug_id", ""),
            human_bug_id=data.get("human_bug_id"),
            file_path=data.get("file_path", ""),
            line_start_llm=data.get("line_start_llm", 0),
            line_end_llm=data.get("line_end_llm", 0),
            line_start_human=data.get("line_start_human"),
            line_end_human=data.get("line_end_human"),
            jaccard_index=data.get("jaccard_index", 0.0),
            similarity_score=data.get("similarity_score", 0.0),
            is_aligned=data.get("is_aligned", False),
            alignment_method=data.get("alignment_method", "unknown"),
        )

    def to_json(self) -> str:
        """Serialize AlignmentResult to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "AlignmentResult":
        """Deserialize AlignmentResult from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
