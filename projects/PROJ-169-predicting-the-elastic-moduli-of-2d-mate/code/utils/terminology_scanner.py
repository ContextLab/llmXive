"""
Terminology Scanner for llmXive PROJ-169.

Scans source code and documentation for forbidden terms related to
"First-Principles" or "Schrödinger" when referring to the ML model.
Replaces them with "Surrogate" or "Interpolation" and logs changes.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Forbidden terms and their replacements
# We look for these terms in contexts that imply the ML model is doing physics
FORBIDDEN_PATTERNS = [
    # Pattern: (First-Principles|First Principles) [model/solution/calculation]
    (re.compile(r'\b(First-Principles|First Principles)\s*(model|calculation|solution|method|approach)?\b', re.IGNORECASE), "Surrogate"),
    # Pattern: (Schrödinger|Schrodinger) [equation]
    (re.compile(r'\b(Schrödinger|Schrodinger)\s*(equation)?\b', re.IGNORECASE), "Schrödinger equation (referenced only for exclusion)"),
    # Pattern: Hamiltonian [in ML context]
    (re.compile(r'\b(Hamiltonian)\b', re.IGNORECASE), "Hamiltonian (referenced only for exclusion)"),
    # Specific forbidden phrases
    (re.compile(r'\bFirst-Principles\s+Calculations\b', re.IGNORECASE), "Surrogate Model Interpolation"),
    (re.compile(r'\bsolving the Schrödinger\b', re.IGNORECASE), "interpolating pre-computed DFT data"),
]

# Direct replacements for simple swaps
DIRECT_REPLACEMENTS = {
    "First-Principles": "Surrogate",
    "First Principles": "Surrogate",
    "First-principles": "Surrogate",
    "first-principles": "surrogate",
}

# Directories to scan (relative to project root)
SCAN_DIRS = ["code", "docs"]
# Directories to exclude
EXCLUDE_DIRS = ["data", "data/results", "data/raw", "data/processed", "__pycache__", ".git", "venv", ".venv"]
# File extensions to scan
SCAN_EXTENSIONS = {".py", ".md", ".txt", ".yaml", ".yml", ".rst", ".json", ".toml"}

class Violation:
    """Represents a single terminology violation found."""
    def __init__(self, file_path: str, line_number: int, original: str, replacement: str, context: str):
        self.file_path = file_path
        self.line_number = line_number
        self.original = original
        self.replacement = replacement
        self.context = context.strip()[:100] + "..." if len(context.strip()) > 100 else context.strip()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file_path,
            "line": self.line_number,
            "original": self.original,
            "replacement": self.replacement,
            "context": self.context
        }

class AuditReport:
    """Aggregates all violations found."""
    def __init__(self):
        self.violations: List[Violation] = []
        self.files_scanned = 0
        self.files_modified = 0

    def add_violation(self, violation: Violation):
        self.violations.append(violation)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "files_scanned": self.files_scanned,
                "files_modified": self.files_modified,
                "total_violations": len(self.violations)
            },
            "violations": [v.to_dict() for v in self.violations]
        }

def is_acceptable_context(line: str, match_str: str) -> bool:
    """
    Checks if the term appears in an acceptable context (e.g., a disclaimer or citation).
    Acceptable contexts:
    - "NOT a first-principles calculation"
    - "does NOT solve the Schrödinger equation"
    - "interpolating pre-computed DFT data"
    """
    acceptable_keywords = [
        "not", "does not", "does NOT", "is not", "is NOT",
        "referenced", "citing", "unlike", "distinct from",
        "surrogate", "interpolation", "ML model"
    ]
    line_lower = line.lower()
    for kw in acceptable_keywords:
        if kw in line_lower:
            # Check if the forbidden term is near the negative keyword
            # Simple heuristic: if both are in the same sentence (or close proximity)
            if abs(line_lower.find(kw) - line_lower.find(match_str.lower())) < 50:
                return True
    return False

def scan_file(file_path: Path, report: AuditReport) -> bool:
    """
    Scans a single file for forbidden terminology.
    Returns True if the file was modified.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.warning(f"Could not read file {file_path}: {e}")
        return False

    modified = False
    new_lines = []

    for i, line in enumerate(lines):
        original_line = line
        line_modified = False

        for pattern, replacement in FORBIDDEN_PATTERNS:
            # Check for matches
            matches = list(pattern.finditer(line))
            for match in matches:
                match_str = match.group()
                # Skip if in acceptable context (e.g., a disclaimer)
                if is_acceptable_context(line, match_str):
                    continue

                # Log violation
                violation = Violation(
                    file_path=str(file_path),
                    line_number=i + 1,
                    original=match_str,
                    replacement=replacement,
                    context=line
                )
                report.add_violation(violation)
                logger.warning(f"Found violation in {file_path}:{i+1}: '{match_str}' -> '{replacement}'")

                # Perform replacement
                line = line[:match.start()] + replacement + line[match.end():]
                line_modified = True

        if line_modified:
            modified = True
        new_lines.append(line)

    if modified:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            report.files_modified += 1
            logger.info(f"Modified file: {file_path}")
        except Exception as e:
            logger.error(f"Could not write to file {file_path}: {e}")
            return False

    return modified

def run_audit(project_root: Path) -> AuditReport:
    """
    Runs the terminology audit over the project structure.
    """
    report = AuditReport()

    for dir_name in SCAN_DIRS:
        target_dir = project_root / dir_name
        if not target_dir.exists():
            logger.warning(f"Directory not found: {target_dir}")
            continue

        for root, dirs, files in os.walk(target_dir):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file_name in files:
                file_path = Path(root) / file_name
                if file_path.suffix in SCAN_EXTENSIONS:
                    report.files_scanned += 1
                    scan_file(file_path, report)

    return report

def save_audit_report(report: AuditReport, output_path: Path):
    """Saves the audit report to a JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2)
        logger.info(f"Audit report saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save audit report: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Scan code and docs for forbidden terminology.")
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Path to the project root directory."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/terminology_audit.json",
        help="Path to save the audit report JSON."
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    output_path = Path(args.output).resolve()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting terminology audit for project at: {project_root}")
    report = run_audit(project_root)

    save_audit_report(report, output_path)

    if report.violations:
        logger.warning(f"Audit complete. Found {len(report.violations)} violations in {report.files_modified} files.")
        sys.exit(0) # Success, but with warnings found
    else:
        logger.info("Audit complete. No violations found.")
        sys.exit(0)

if __name__ == "__main__":
    main()
