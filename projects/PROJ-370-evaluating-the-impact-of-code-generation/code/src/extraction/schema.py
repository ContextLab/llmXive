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

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Convert string to Severity enum."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid severity: {value}. Must be one of {list(cls)}")


@dataclass
class PullRequest:
    """Data class representing a GitHub Pull Request and its metadata."""
    pr_id: str
    repo_name: str
    title: str
    body: Optional[str]
    state: str
    created_at: str
    updated_at: str
    author: str
    base_branch: str
    head_branch: str
    diff: str
    linked_issue_ids: List[str] = field(default_factory=list)
    review_comments: List[Dict[str, Any]] = field(default_factory=list)
    is_verified_bug: bool = False
    verification_method: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "pr_id": self.pr_id,
            "repo_name": self.repo_name,
            "title": self.title,
            "body": self.body,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
            "base_branch": self.base_branch,
            "head_branch": self.head_branch,
            "diff": self.diff,
            "linked_issue_ids": self.linked_issue_ids,
            "review_comments": self.review_comments,
            "is_verified_bug": self.is_verified_bug,
            "verification_method": self.verification_method,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PullRequest":
        """Create instance from dictionary."""
        return cls(
            pr_id=data["pr_id"],
            repo_name=data["repo_name"],
            title=data["title"],
            body=data.get("body"),
            state=data["state"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            author=data["author"],
            base_branch=data["base_branch"],
            head_branch=data["head_branch"],
            diff=data["diff"],
            linked_issue_ids=data.get("linked_issue_ids", []),
            review_comments=data.get("review_comments", []),
            is_verified_bug=data.get("is_verified_bug", False),
            verification_method=data.get("verification_method"),
        )


@dataclass
class BugDetection:
    """Data class representing a detected bug in a code change."""
    pr_id: str
    file_path: str
    line_start: int
    line_end: int
    severity: Severity
    description: str
    source: str  # "human" or "llm"
    confidence: Optional[float] = None
    llm_error_flag: bool = False
    
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
            "llm_error_flag": self.llm_error_flag,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BugDetection":
        """Create instance from dictionary."""
        severity = data["severity"]
        if isinstance(severity, str):
            severity = Severity.from_string(severity)
        
        return cls(
            pr_id=data["pr_id"],
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            severity=severity,
            description=data["description"],
            source=data["source"],
            confidence=data.get("confidence"),
            llm_error_flag=data.get("llm_error_flag", False),
        )


@dataclass
class AlignmentResult:
    """Data class representing the alignment between human and LLM bug detections."""
    human_bug: BugDetection
    llm_bug: BugDetection
    alignment_score: float
    jaccard_index: float
    is_match: bool
    match_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "human_bug": self.human_bug.to_dict(),
            "llm_bug": self.llm_bug.to_dict(),
            "alignment_score": self.alignment_score,
            "jaccard_index": self.jaccard_index,
            "is_match": self.is_match,
            "match_reason": self.match_reason,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlignmentResult":
        """Create instance from dictionary."""
        human_bug = BugDetection.from_dict(data["human_bug"])
        llm_bug = BugDetection.from_dict(data["llm_bug"])
        
        return cls(
            human_bug=human_bug,
            llm_bug=llm_bug,
            alignment_score=data["alignment_score"],
            jaccard_index=data["jaccard_index"],
            is_match=data["is_match"],
            match_reason=data.get("match_reason"),
        )
