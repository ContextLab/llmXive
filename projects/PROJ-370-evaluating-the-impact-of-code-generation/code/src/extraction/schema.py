"""
Schema definitions for PR extraction and data modeling.
Defines core dataclasses: PullRequest, BugDetection, AlignmentResult.
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

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Convert string to Severity enum."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid severity: {value}. Must be one of {[s.value for s in cls]}")


@dataclass
class PullRequest:
    """
    Represents a GitHub Pull Request with extracted metadata.
    
    Attributes:
        pr_id: Unique identifier (e.g., "microsoft/vscode#12345")
        repo: Repository name (e.g., "microsoft/vscode")
        number: PR number within the repo
        title: PR title
        body: PR description body
        author: Author username
        created_at: ISO 8601 timestamp of creation
        state: "open", "closed", or "merged"
        diff: The full diff content of the PR
        files_changed: List of file paths changed
        review_comments: List of review comment dictionaries
        linked_issue_ids: List of issue numbers linked in PR body/commits
        llm_code_flag: Boolean indicating if LLM-generated code was detected (optional)
    """
    pr_id: str
    repo: str
    number: int
    title: str
    body: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[str] = None
    state: Optional[str] = None
    diff: Optional[str] = None
    files_changed: List[str] = field(default_factory=list)
    review_comments: List[Dict[str, Any]] = field(default_factory=list)
    linked_issue_ids: List[int] = field(default_factory=list)
    llm_code_flag: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "pr_id": self.pr_id,
            "repo": self.repo,
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "author": self.author,
            "created_at": self.created_at,
            "state": self.state,
            "diff": self.diff,
            "files_changed": self.files_changed,
            "review_comments": self.review_comments,
            "linked_issue_ids": self.linked_issue_ids,
            "llm_code_flag": self.llm_code_flag
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PullRequest":
        """Create instance from dictionary."""
        return cls(
            pr_id=data.get("pr_id", ""),
            repo=data.get("repo", ""),
            number=data.get("number", 0),
            title=data.get("title", ""),
            body=data.get("body"),
            author=data.get("author"),
            created_at=data.get("created_at"),
            state=data.get("state"),
            diff=data.get("diff"),
            files_changed=data.get("files_changed", []),
            review_comments=data.get("review_comments", []),
            linked_issue_ids=data.get("linked_issue_ids", []),
            llm_code_flag=data.get("llm_code_flag")
        )


@dataclass
class BugDetection:
    """
    Represents a detected bug or issue in code.
    
    Attributes:
        pr_id: Reference to the PR containing the bug
        file_path: Path to the file containing the bug
        line_start: Starting line number (1-indexed)
        line_end: Ending line number (1-indexed)
        severity: Severity level of the bug
        description: Human-readable description of the bug
        source: Source of detection ("human", "llm", "triangulated")
        confidence: Optional confidence score (0.0-1.0) for LLM detections
        is_verified: Boolean indicating if bug is verified ground truth
        verification_method: Method used for verification (e.g., "strict_triangulation")
    """
    pr_id: str
    file_path: str
    line_start: int
    line_end: int
    severity: Severity
    description: str
    source: str
    confidence: Optional[float] = None
    is_verified: bool = False
    verification_method: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "pr_id": self.pr_id,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "severity": self.severity.value if isinstance(self.severity, Severity) else self.severity,
            "description": self.description,
            "source": self.source,
            "confidence": self.confidence,
            "is_verified": self.is_verified,
            "verification_method": self.verification_method
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BugDetection":
        """Create instance from dictionary."""
        severity_val = data.get("severity", "minor")
        if isinstance(severity_val, str):
            severity_val = Severity.from_string(severity_val)
        
        return cls(
            pr_id=data.get("pr_id", ""),
            file_path=data.get("file_path", ""),
            line_start=data.get("line_start", 0),
            line_end=data.get("line_end", 0),
            severity=severity_val,
            description=data.get("description", ""),
            source=data.get("source", "unknown"),
            confidence=data.get("confidence"),
            is_verified=data.get("is_verified", False),
            verification_method=data.get("verification_method")
        )


@dataclass
class AlignmentResult:
    """
    Represents the alignment between an LLM detection and a human-verified bug.
    
    Attributes:
        llm_detection_id: Unique identifier for the LLM detection
        human_detection_id: Unique identifier for the human detection (if matched)
        file_path: File path where alignment occurred
        line_start: Starting line of the aligned region
        line_end: Ending line of the aligned region
        jaccard_index: Jaccard similarity index for line overlap (0.0-1.0)
        cosine_similarity: Cosine similarity score between bug descriptions
        is_match: Boolean indicating if this is a valid match
        match_reason: Explanation of why the alignment was made/rejected
    """
    llm_detection_id: str
    human_detection_id: Optional[str]
    file_path: str
    line_start: int
    line_end: int
    jaccard_index: float
    cosine_similarity: float
    is_match: bool
    match_reason: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "llm_detection_id": self.llm_detection_id,
            "human_detection_id": self.human_detection_id,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "jaccard_index": self.jaccard_index,
            "cosine_similarity": self.cosine_similarity,
            "is_match": self.is_match,
            "match_reason": self.match_reason
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlignmentResult":
        """Create instance from dictionary."""
        return cls(
            llm_detection_id=data.get("llm_detection_id", ""),
            human_detection_id=data.get("human_detection_id"),
            file_path=data.get("file_path", ""),
            line_start=data.get("line_start", 0),
            line_end=data.get("line_end", 0),
            jaccard_index=data.get("jaccard_index", 0.0),
            cosine_similarity=data.get("cosine_similarity", 0.0),
            is_match=data.get("is_match", False),
            match_reason=data.get("match_reason", "")
        )
