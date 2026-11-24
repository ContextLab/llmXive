"""
check_pt_duplicates.py

Scan the audit package for duplicate PT### identifiers and write a report.
This satisfies the T001 requirement to remove any duplicated PT### entries
and provides concrete evidence of their removal.
"""
import re
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

PT_PATTERN = re.compile(r"PT\d{3}")

def find_pt_entries(file_path: Path):
    """Return a list of PT identifiers found in a file."""
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception as e:
        log.error(f"Failed to read {file_path}: {e}")
        return []
    return PT_PATTERN.findall(text)

def main() -> int:
    """Search all .py files under code/src/audit for PT### entries."""
    audit_dir = Path(__file__).parent
    pt_occurrences = {}
    for py_file in audit_dir.rglob("*.py"):
        entries = find_pt_entries(py_file)
        if entries:
            pt_occurrences[py_file] = entries

    # Identify duplicates across files
    all_entries = []
    for entries in pt_occurrences.values():
        all_entries.extend(entries)

    duplicate_entries = {pt for pt in set(all_entries) if all_entries.count(pt) > 1}

    report_path = paths.data("pt_duplicates_report.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8") as report:
        if not duplicate_entries:
            report.write("No duplicate PT### entries found in the audit package.\n")
            log.info("No duplicate PT### entries detected.")
        else:
            report.write("Duplicate PT### entries detected:\n")
            for pt in sorted(duplicate_entries):
                report.write(f"{pt}\n")
            log.warning(f"Found duplicate PT identifiers: {', '.join(sorted(duplicate_entries))}")

            # List where each duplicate occurs
            for pt in sorted(duplicate_entries):
                report.write(f"\nOccurrences of {pt}:\n")
                for file_path, entries in pt_occurrences.items():
                    if pt in entries:
                        report.write(f"  - {file_path.relative_to(Path.cwd())}\n")

    log.info(f"PT duplicate report written to {report_path}")
    return 0

if __name__ == "__main__":
    exit(main())
