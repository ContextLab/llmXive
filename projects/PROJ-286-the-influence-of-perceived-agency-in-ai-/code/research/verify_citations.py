"""
Task T000c: Verify citation validation results.

Parses research/validation_report.json and verifies all citations are valid
(status="valid", overlap >= 0.7). Halts with an error if any fail.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Validation report not found at {path}. Run T000b first.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

def verify_citations(validation_data: Dict[str, Any]) -> None:
    """
    Verify that all citations in the validation report are valid.

    Criteria:
    - status must be "valid"
    - overlap must be >= 0.7

    Raises SystemExit with an error message if verification fails.
    """
    citations = validation_data.get("citations", [])
    
    if not citations:
        print("No citations found in validation report.")
        sys.exit(1)

    failed_citations: List[Dict[str, Any]] = []

    for citation in citations:
        citation_text = citation.get("citation", "Unknown")
        status = citation.get("status", "")
        overlap = citation.get("overlap", 0.0)

        is_valid = (status == "valid") and (overlap >= 0.7)

        if not is_valid:
            failed_citations.append({
                "citation": citation_text,
                "status": status,
                "overlap": overlap,
                "reason": f"status={status}, overlap={overlap} (threshold 0.7)"
            })

    if failed_citations:
        error_msg = f"Citation verification FAILED for {len(failed_citations)} citation(s):\n"
        for fc in failed_citations:
            error_msg += f"  - {fc['citation']}: {fc['reason']}\n"
        error_msg += "\nHalt: Cannot proceed to implementation until all citations are valid."
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    print(f"Success: All {len(citations)} citation(s) verified as valid (status='valid', overlap >= 0.7).")

def main() -> None:
    """Main entry point for T000c."""
    parser = argparse.ArgumentParser(
        description="Verify citation validation results from T000b."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="research/validation_report.json",
        help="Path to the validation report JSON file (default: research/validation_report.json)"
    )
    
    args = parser.parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found. Ensure T000b has been run.", file=sys.stderr)
        sys.exit(1)

    try:
        data = load_json_file(input_path)
        verify_citations(data)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
