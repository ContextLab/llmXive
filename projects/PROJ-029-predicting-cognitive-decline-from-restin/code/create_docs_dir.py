"""T001c: Create the `docs/` directory at the repository root.

Creates `docs/` and seeds it with an index file so the directory is
tracked by version control and its presence is verifiable on disk.
"""
from pathlib import Path

from llmxive_toolkit import paths

def main() -> int:
    docs_dir = paths.docs()
    docs_dir.mkdir(parents=True, exist_ok=True)

    index_file = docs_dir / "index.md"
    if not index_file.exists():
        index_file.write_text(
            "# Project Documentation\n\n"
            "This directory holds project-level documentation for\n"
            "PROJ-029: Predicting Cognitive Decline from Resting-State fMRI\n"
            "Network Topology.\n\n"
            "## Contents\n\n"
            "- Pipeline run-book: see `quickstart.md` at the repository root.\n"
            "- Feature specification: `specs/001-predicting-cognitive-decline-from-restin/spec.md`\n"
            "- Implementation plan: `specs/001-predicting-cognitive-decline-from-restin/plan.md`\n"
            "- Final analysis report (generated): `data/artifacts/final_report.md`\n",
            encoding="utf-8",
        )

    print(f"docs/ directory ready at: {docs_dir}")
    print(f"index file: {index_file} (exists={index_file.is_file()})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())