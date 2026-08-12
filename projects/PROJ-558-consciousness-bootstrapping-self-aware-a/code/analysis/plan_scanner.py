import os
import json
import re
from typing import List, Dict, Any
from pathlib import Path

# Search patterns as defined in T003a
TARGET_PATTERNS = [
    "Teacher-Student Distillation",
    "Pre-computed Teacher Labels",
    "external truth"
]

def scan_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Scans a file for specific target phrases and returns their locations and context.

    Args:
        file_path: Path to the file to scan.

    Returns:
        A list of dictionaries containing line number, context, and matched phrase.
    """
    findings = []
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        raise ValueError(f"Could not decode file {file_path} as UTF-8")

    for line_num, line in enumerate(lines, start=1):
        for pattern in TARGET_PATTERNS:
            # Case-insensitive search
            if pattern.lower() in line.lower():
                # Get context: 1 line before and 1 line after if available
                context_start = max(0, line_num - 2)
                context_end = min(len(lines), line_num + 1)
                context_lines = lines[context_start:context_end]
                context_text = "".join(context_lines).strip().replace('\n', ' ')

                findings.append({
                    "line_number": line_num,
                    "matched_phrase": pattern,
                    "line_content": line.strip(),
                    "context": context_text
                })

    return findings

def main():
    """
    Main entry point for scanning plan.md.
    Outputs JSON to stdout.
    """
    # Determine project root relative to this script
    # Assuming script is at code/analysis/plan_scanner.py
    # Project root is ../../
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    plan_path = project_root / "plan.md"

    if not plan_path.exists():
        print(f"Error: plan.md not found at {plan_path}", file=os.sys.stderr)
        os.sys.exit(1)

    try:
        findings = scan_file(str(plan_path))
        if not findings:
            print("No occurrences of target phrases found in plan.md.")
            return

        # Sort by line number
        findings.sort(key=lambda x: x['line_number'])

        # Output as JSON
        print(json.dumps(findings, indent=2))

    except Exception as e:
        print(f"Error scanning file: {e}", file=os.sys.stderr)
        os.sys.exit(1)

if __name__ == "__main__":
    main()
