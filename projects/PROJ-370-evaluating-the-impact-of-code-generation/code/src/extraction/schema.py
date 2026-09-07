"""
Schema definitions for PR data extraction.
Defines dataclasses for PullRequest, BugDetection, and AlignmentResult.
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
    Dataclass representing a GitHub Pull Request.
    Contains PR metadata, diff content, and associated comments/issues.
    """
    pr_id: int
    repo_name: str
    title: str
    body: Optional[str]
    state: str
    created_at: str
    updated_at: str
    user_login: str
    diff_url: str
    html_url: str
    # Extracted content
    diff_text: str
    comments: List[Dict[str, Any]] = field(default_factory=list)
    linked_issue_ids: List[int] = field(default_factory=list)
    # Processing metadata
    is_truncated: bool = False
    token_count: int = 0
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pr_id": self.pr_id,
            "repo_name": self.repo_name,
            "title": self.title,
            "body": self.body,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user_login": self.user_login,
            "diff_url": self.diff_url,
            "html_url": self.html_url,
            "diff_text": self.diff_text,
            "comments": self.comments,
            "linked_issue_ids": self.linked_issue_ids,
            "is_truncated": self.is_truncated,
            "token_count": self.token_count,
            "checksum": self.checksum
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
            user_login=data["user_login"],
            diff_url=data["diff_url"],
            html_url=data["html_url"],
            diff_text=data["diff_text"],
            comments=data.get("comments", []),
            linked_issue_ids=data.get("linked_issue_ids", []),
            is_truncated=data.get("is_truncated", False),
            token_count=data.get("token_count", 0),
            checksum=data.get("checksum")
        )


@dataclass
class BugDetection:
    """
    Dataclass representing a detected bug or issue in code.
    Used for both human-verified and LLM-detected bugs.
    """
    pr_id: int
    file_path: str
    line_start: int
    line_end: int
    severity: Severity
    description: str
    # Detection source
    detection_source: str  # "human" or "llm"
    # Additional metadata
    confidence: Optional[float] = None
    is_verified: bool = False
    verification_method: Optional[str] = None
    llm_error_flag: bool = False
    raw_context: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pr_id": self.pr_id,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "severity": self.severity.value,
            "description": self.description,
            "detection_source": self.detection_source,
            "confidence": self.confidence,
            "is_verified": self.is_verified,
            "verification_method": self.verification_method,
            "llm_error_flag": self.llm_error_flag,
            "raw_context": self.raw_context
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
        elif isinstance(severity, Severity):
            pass
        else:
            raise ValueError(f"Invalid severity type: {type(severity)}")

        return cls(
            pr_id=data["pr_id"],
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            severity=severity,
            description=data["description"],
            detection_source=data["detection_source"],
            confidence=data.get("confidence"),
            is_verified=data.get("is_verified", False),
            verification_method=data.get("verification_method"),
            llm_error_flag=data.get("llm_error_flag", False),
            raw_context=data.get("raw_context")
        )


@dataclass
class AlignmentResult:
    """
    Dataclass representing the alignment between a human-verified bug
    and an LLM-detected bug.
    """
    human_bug: BugDetection
    llm_bug: BugDetection
    match_score: float
    jaccard_index: float
    cosine_similarity: float
    is_match: bool
    match_criteria: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "human_bug": self.human_bug.to_dict(),
            "llm_bug": self.llm_bug.to_dict(),
            "match_score": self.match_score,
            "jaccard_index": self.jaccard_index,
            "cosine_similarity": self.cosine_similarity,
            "is_match": self.is_match,
            "match_criteria": self.match_criteria
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
            match_score=data["match_score"],
            jaccard_index=data["jaccard_index"],
            cosine_similarity=data["cosine_similarity"],
            is_match=data["is_match"],
            match_criteria=data.get("match_criteria", {})
        )
