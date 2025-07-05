"""Base classes for validation system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationCheck:
    """Result of a single validation check."""
    name: str
    passed: bool
    message: str
    severity: str = "error"  # error, warning, info
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __str__(self) -> str:
        """String representation."""
        status = "✓" if self.passed else "✗"
        severity_emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(self.severity, "")
        
        if self.passed:
            return f"{status} {self.name}: {self.message}"
        else:
            return f"{status} {severity_emoji} {self.name}: {self.message}"


@dataclass
class ValidationResult:
    """Collection of validation checks for a specific item."""
    item_type: str  # e.g., "technical_design", "github_issue"
    item_id: str    # e.g., "project-123", "issue-456"
    checks: List[ValidationCheck] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def passed(self) -> bool:
        """Check if all validations passed."""
        return all(check.passed for check in self.checks if check.severity == "error")
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return any(not check.passed and check.severity == "warning" for check in self.checks)
    
    @property
    def passed_count(self) -> int:
        """Count of passed checks."""
        return sum(1 for check in self.checks if check.passed)
    
    @property
    def failed_count(self) -> int:
        """Count of failed checks."""
        return sum(1 for check in self.checks if not check.passed)
    
    def add_check(self, name: str, passed: bool, message: str, 
                  severity: str = "error", details: Optional[Dict] = None) -> None:
        """Add a validation check."""
        self.checks.append(ValidationCheck(name, passed, message, severity, details))
    
    def get_errors(self) -> List[ValidationCheck]:
        """Get all error-level failed checks."""
        return [c for c in self.checks if not c.passed and c.severity == "error"]
    
    def get_warnings(self) -> List[ValidationCheck]:
        """Get all warning-level failed checks."""
        return [c for c in self.checks if not c.passed and c.severity == "warning"]
    
    def summary(self) -> str:
        """Get a summary of the validation."""
        status = "PASSED" if self.passed else "FAILED"
        warning_text = f" ({len(self.get_warnings())} warnings)" if self.has_warnings else ""
        
        return (f"{self.item_type} '{self.item_id}': {status} "
                f"({self.passed_count}/{len(self.checks)} checks passed){warning_text}")


class BaseValidator(ABC):
    """Abstract base class for validators."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize validator.
        
        Args:
            base_path: Base path for file operations
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
    
    @abstractmethod
    def validate(self, item_id: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate an item.
        
        Args:
            item_id: Identifier of the item to validate
            context: Optional context information
            
        Returns:
            ValidationResult with all checks
        """
        pass
    
    def check_file_exists(self, file_path: Path, result: ValidationResult, 
                         required: bool = True) -> bool:
        """Check if a file exists.
        
        Args:
            file_path: Path to check
            result: ValidationResult to add check to
            required: Whether the file is required (error) or optional (warning)
            
        Returns:
            True if file exists
        """
        exists = file_path.exists() and file_path.is_file()
        severity = "error" if required else "warning"
        
        result.add_check(
            name=f"file_exists_{file_path.name}",
            passed=exists,
            message=f"File {'exists' if exists else 'not found'}: {file_path}",
            severity=severity
        )
        
        return exists
    
    def check_directory_exists(self, dir_path: Path, result: ValidationResult,
                             required: bool = True) -> bool:
        """Check if a directory exists.
        
        Args:
            dir_path: Path to check
            result: ValidationResult to add check to
            required: Whether the directory is required
            
        Returns:
            True if directory exists
        """
        exists = dir_path.exists() and dir_path.is_dir()
        severity = "error" if required else "warning"
        
        result.add_check(
            name=f"directory_exists_{dir_path.name}",
            passed=exists,
            message=f"Directory {'exists' if exists else 'not found'}: {dir_path}",
            severity=severity
        )
        
        return exists
    
    def check_file_content(self, file_path: Path, required_patterns: List[str],
                          result: ValidationResult) -> bool:
        """Check if file contains required patterns.
        
        Args:
            file_path: Path to file
            required_patterns: Patterns that must be present
            result: ValidationResult to add checks to
            
        Returns:
            True if all patterns found
        """
        if not file_path.exists():
            result.add_check(
                name=f"content_check_{file_path.name}",
                passed=False,
                message=f"Cannot check content - file not found: {file_path}"
            )
            return False
        
        try:
            content = file_path.read_text()
            all_found = True
            
            for pattern in required_patterns:
                found = pattern in content
                all_found &= found
                
                result.add_check(
                    name=f"pattern_{pattern[:20]}",
                    passed=found,
                    message=f"Pattern {'found' if found else 'missing'}: {pattern}",
                    severity="error" if not found else "info"
                )
            
            return all_found
            
        except Exception as e:
            result.add_check(
                name=f"content_read_{file_path.name}",
                passed=False,
                message=f"Failed to read file: {e}"
            )
            return False