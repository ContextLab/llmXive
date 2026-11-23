import argparse
import json
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

def load_validation_report(report_path: Path) -> Dict[str, Any]:
    """Load the item source log or validation report JSON."""
    if not report_path.exists():
        raise FileNotFoundError(f"Validation report not found at {report_path}")
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_scale_items_from_spec(spec_path: Path) -> List[str]:
    """
    Extract the list of trust scale items from the generated markdown file.
    Expects a JSON array embedded in the file or a specific format.
    Based on T010b-auto, docs/trust_scale_items.md contains the verified items.
    """
    if not spec_path.exists():
        raise FileNotFoundError(f"Scale items file not found at {spec_path}")
    
    with open(spec_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Attempt to find a JSON array block within the markdown
    # Pattern looks for [...] possibly surrounded by markdown code blocks
    json_match = re.search(r'```json\s*(\[.*?\])\s*```', content, re.DOTALL)
    if json_match:
        try:
            items = json.loads(json_match.group(1))
            if isinstance(items, list):
                return items
        except json.JSONDecodeError:
            pass

    # Fallback: Try to parse the whole file as JSON if it's just the array
    try:
        items = json.loads(content)
        if isinstance(items, list):
            return items
    except json.JSONDecodeError:
        pass

    raise ValueError(f"Could not extract valid JSON array of items from {spec_path}")

def compare_items(source_items: List[str], spec_items: List[str]) -> bool:
    """
    Compare two lists of items for exact match.
    Normalizes whitespace but preserves text content.
    """
    if len(source_items) != len(spec_items):
        return False

    for s, p in zip(source_items, spec_items):
        # Normalize whitespace (strip, collapse internal spaces)
        norm_s = " ".join(s.split())
        norm_p = " ".join(p.split())
        if norm_s != norm_p:
            return False
    return True

def write_validation_report(report_path: Path, status: str, details: Dict[str, Any]) -> None:
    """Write the verification report to the specified path."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_data = {
        "verification_status": status,
        "timestamp": details.get("timestamp", ""),
        "source_file": details.get("source_file", ""),
        "spec_file": details.get("spec_file", ""),
        "item_count": details.get("item_count", 0),
        "match_result": details.get("match_result", False),
        "message": details.get("message", "")
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

def main() -> None:
    """
    Main entry point for T007g: Generate trust_scale_verification_report.md.
    
    Logic:
    1. Read research/item_source_log.json (from T000/T010c).
    2. Extract items from docs/trust_scale_items.md (from T010b-auto).
    3. Confirm exact match.
    4. Write research/trust_scale_verification_report.md.
    """
    parser = argparse.ArgumentParser(description="Verify Trust Scale Items")
    parser.add_argument("--source-log", type=str, default="research/item_source_log.json",
                        help="Path to the item source log JSON")
    parser.add_argument("--spec-file", type=str, default="docs/trust_scale_items.md",
                        help="Path to the trust scale items markdown file")
    parser.add_argument("--output-report", type=str, default="research/trust_scale_verification_report.md",
                        help="Path to write the verification report")
    args = parser.parse_args()

    source_log_path = Path(args.source_log)
    spec_path = Path(args.spec_file)
    output_path = Path(args.output_report)

    try:
        # 1. Load source log
        source_data = load_validation_report(source_log_path)
        source_items = source_data.get("items", [])
        
        if not source_items:
            raise ValueError("Source log contains no items.")

        # 2. Fetch items from spec
        spec_items = fetch_scale_items_from_spec(spec_path)

        # 3. Compare
        is_match = compare_items(source_items, spec_items)
        
        # 4. Write Report (Markdown format as requested by task description)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        status_text = "VERIFIED" if is_match else "MISMATCH"
        message = "All items match exactly." if is_match else "Item mismatch detected."
        
        report_md = f"""# Trust Scale Verification Report

**Status**: {status_text}
**Source**: {source_log_path}
**Spec**: {spec_path}
**Item Count**: {len(source_items)}

## Details
- **Match Result**: {'Pass' if is_match else 'Fail'}
- **Message**: {message}

## Items Verified
The following {len(source_items)} items from the Lee & See (2004) scale were verified:

"""
        for i, item in enumerate(source_items, 1):
            report_md += f"{i}. {item}\n"

        report_md += "\n## Conclusion\n"
        if is_match:
            report_md += "The items in `docs/trust_scale_items.md` are identical to the verified source.\n"
        else:
            report_md += "WARNING: The items do not match the verified source. Do not proceed with data collection.\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_md)

        print(f"Verification complete. Report written to {output_path}")
        if not is_match:
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Validation Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()