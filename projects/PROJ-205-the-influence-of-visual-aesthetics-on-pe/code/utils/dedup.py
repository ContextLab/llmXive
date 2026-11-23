"""
Deduplication utility for survey submissions.
"""
import os
import sys
import csv
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.helpers import get_project_root, get_submissions_csv_path

def load_submissions_data() -> list[dict]:
    """Load submissions data."""
    path = get_submissions_csv_path()
    if not path.exists():
        return []
    with open(path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def detect_duplicates(data: list[dict]) -> list[dict]:
    """Detect duplicate participant_ids."""
    seen = {}
    duplicates = []
    for row in data:
        pid = row.get("participant_id")
        if pid in seen:
            duplicates.append(row)
        else:
            seen[pid] = row
    return duplicates

def write_dedup_report(duplicates: list[dict], output_path: Path) -> None:
    """Write deduplication report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        if not duplicates:
            f.write("participant_id,timestamp,reason\n")
            f.write(",,No duplicates found\n")
            return
        
        writer = csv.DictWriter(f, fieldnames=duplicates[0].keys() | {"reason"})
        writer.writeheader()
        for d in duplicates:
            d["reason"] = "duplicate_participant_id"
            writer.writerow(d)

def run_deduplication() -> dict:
    """Run deduplication and return stats."""
    data = load_submissions_data()
    duplicates = detect_duplicates(data)
    
    unique_data = []
    seen = set()
    for row in data:
        pid = row.get("participant_id")
        if pid not in seen:
            unique_data.append(row)
            seen.add(pid)
    
    return {
        "total_rows": len(data),
        "unique_rows": len(unique_data),
        "duplicates_removed": len(duplicates),
        "duplicates": duplicates
    }

def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Deduplicate submissions")
    parser.add_argument("--output", default=None, help="Output path for report")
    args = parser.parse_args()

    project_root = get_project_root()
    output_path = Path(args.output) if args.output else project_root / "data" / "processed" / "dedup_report.csv"

    stats = run_deduplication()
    write_dedup_report(stats["duplicates"], output_path)

    print(f"Deduplication complete. Removed {stats['duplicates_removed']} duplicates.")
    print(f"Report saved to {output_path}")

if __name__ == "__main__":
    main()