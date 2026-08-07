import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class FailureClassification:
    issue_id: str
    classification: str  # "missing_context" | "reasoning_error" | "other"
    confidence: float
    reason: str

def extract_file_references_from_context(log_text: str) -> List[str]:
    """Extract file paths mentioned in logs."""
    pattern = r'(?:file|path):\s*(?:[\'"])([^\'"]+\.(?:py|js|ts))'
    return re.findall(pattern, log_text, re.IGNORECASE)

def check_file_exists_in_context(file_path: str, context_files: List[str]) -> bool:
    return any(file_path in cf for cf in context_files)

def classify_failure(
    log_text: str,
    context_files: List[str],
    issue_id: str
) -> FailureClassification:
    """
    Classify failure based on sandbox log parsing.
    Rules:
    - "missing_context": logs contain "file not found" or "cannot locate"
    - "reasoning_error": file exists but logic fails
    """
    log_lower = log_text.lower()
    
    if "file not found" in log_lower or "cannot locate" in log_lower:
        return FailureClassification(
            issue_id=issue_id,
            classification="missing_context",
            confidence=0.9,
            reason="Log indicates file not found/cannot locate"
        )
    
    # Check if referenced files exist in context
    refs = extract_file_references_from_context(log_text)
    missing_refs = [r for r in refs if not check_file_exists_in_context(r, context_files)]
    
    if missing_refs:
        return FailureClassification(
            issue_id=issue_id,
            classification="missing_context",
            confidence=0.8,
            reason=f"Referenced files missing in context: {missing_refs}"
        )
    
    return FailureClassification(
        issue_id=issue_id,
        classification="reasoning_error",
        confidence=0.7,
        reason="File exists but execution failed (logic error)"
    )

def process_execution_results(
    results: List[Dict[str, Any]]
) -> List[FailureClassification]:
    """Process a list of execution results."""
    classifications = []
    for res in results:
        log = res.get("sandbox_log", "")
        context = res.get("context_files", [])
        issue_id = res.get("issue_id", "unknown")
        if res.get("pass_status") is False:
            classifications.append(classify_failure(log, context, issue_id))
    return classifications

def main():
    # Demo
    sample = {
        "issue_id": "123",
        "pass_status": False,
        "sandbox_log": "File not found: src/main.py",
        "context_files": ["src/utils.py"]
    }
    res = process_execution_results([sample])
    for r in res:
        print(asdict(r))

if __name__ == "__main__":
    main()
