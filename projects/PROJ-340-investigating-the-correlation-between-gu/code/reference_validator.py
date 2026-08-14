import os
import sys
import json
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

# -----------------------------------------------------------------------------
# Reference-Validator Agent Implementation
# Addresses: Constitution Principle I & II
# -----------------------------------------------------------------------------

class VerificationStatus:
    """Enum-like class for verification outcomes."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    LOGIC_ONLY = "LOGIC_ONLY"  # Synthetic mode bypass

class CitationSchema:
    """Schema for expected citation structure."""
    REQUIRED_KEYS = {"doi", "title", "source", "url"}
    OPTIONAL_KEYS = {"authors", "year", "notes"}

    @staticmethod
    def validate(citation: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validates a citation dictionary against the schema.
        Returns (is_valid, list_of_missing_keys).
        """
        missing = []
        for key in CitationSchema.REQUIRED_KEYS:
            if key not in citation or not citation[key]:
                missing.append(key)
        return len(missing) == 0, missing

class VerificationResult:
    """Container for verification results."""
    def __init__(self, status: str, message: str, score: float = 1.0):
        self.status = status
        self.message = message
        self.score = score

class ReferenceValidator:
    """
    Implements Constitution Principle II:
    Strict enforcement of citation verification.
    If citations are missing or unreachable, the build MUST fail (score 0.0).
    EXCEPTION: If validation_mode_flag.json indicates synthetic mode,
    the agent skips verification and passes with 'LOGIC_ONLY' status.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.validation_mode_path = self.project_root / "data" / "metadata" / "validation_mode_flag.json"
        self.verified_dois_path = self.project_root / "data" / "citations" / "verified_dois.yaml"

    def _is_synthetic_mode(self) -> bool:
        """Checks if the project is running in synthetic validation mode."""
        if not self.validation_mode_path.exists():
            return False
        
        try:
            with open(self.validation_mode_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("active", False) is True
        except (json.JSONDecodeError, IOError):
            return False

    def _load_verified_dois(self) -> List[str]:
        """Loads the list of verified DOIs from the config file."""
        if not self.verified_dois_path.exists():
            return []
        
        try:
            with open(self.verified_dois_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            # Expecting structure: { "dois": ["10.xxxx/...", ...] } or just a list
            if isinstance(data, dict) and "dois" in data:
                return data["dois"]
            elif isinstance(data, list):
                return data
            return []
        except (yaml.YAMLError, IOError):
            return []

    def validate_citations(self) -> VerificationResult:
        """
        Main entry point for validation.
        
        Logic:
        1. Check synthetic mode flag. If active -> Return LOGIC_ONLY (Pass).
        2. If real mode:
           a. Check if verified_dois.yaml exists and is non-empty.
           b. If empty/missing -> FAIL (Score 0.0).
           c. (Future expansion: Network reachability check could go here).
        """
        
        # 1. Check Synthetic Mode
        if self._is_synthetic_mode():
            return VerificationResult(
                status=VerificationStatus.LOGIC_ONLY,
                message="Synthetic mode active. Citation verification skipped (Logic Only).",
                score=1.0
            )

        # 2. Real Mode: Enforce Constitution Principle II
        dois = self._load_verified_dois()
        
        if not dois:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                message="Real data mode active but no verified citations found in data/citations/verified_dois.yaml. "
                        "Constitution Principle II violation: Build aborted.",
                score=0.0
            )

        # Placeholder for future network reachability checks
        # For now, presence in the verified list is the gate.
        return VerificationResult(
            status=VerificationStatus.PASSED,
            message=f"Citation verification passed. {len(dois)} verified DOI(s) found.",
            score=1.0
        )

    def run_gate(self) -> int:
        """
        Runs the validation gate.
        Returns 0 on success (or logic_only), 1 on failure.
        This is designed to be called by CI or the main pipeline.
        """
        result = self.validate_citations()
        
        print(f"[ReferenceValidator] Status: {result.status}")
        print(f"[ReferenceValidator] Message: {result.message}")
        
        if result.status == VerificationStatus.FAILED:
            print(f"[ReferenceValidator] CRITICAL: Build failed with score {result.score}.")
            return 1
        
        return 0

def create_sample_schema() -> Dict[str, Any]:
    """Returns a sample schema for documentation purposes."""
    return {
        "citation": {
            "type": "object",
            "required": ["doi", "title", "source", "url"],
            "properties": {
                "doi": {"type": "string", "description": "Digital Object Identifier"},
                "title": {"type": "string", "description": "Title of the work"},
                "source": {"type": "string", "description": "Journal or repository name"},
                "url": {"type": "string", "format": "uri", "description": "Link to the work"}
            }
        }
    }

def main():
    """CLI entry point for the Reference Validator."""
    import argparse
    parser = argparse.ArgumentParser(description="Reference Validator Agent")
    parser.add_argument("--project-root", type=str, default=None, help="Path to project root")
    args = parser.parse_args()

    root = Path(args.project_root) if args.project_root else None
    validator = ReferenceValidator(project_root=root)
    exit_code = validator.run_gate()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
