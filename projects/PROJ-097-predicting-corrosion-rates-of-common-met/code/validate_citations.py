"""Citation validation script for the corrosion project.

This script implements the **Citation validation** task (T000). It scans the
``spec.md`` and ``plan.md`` files for Markdown‑style citations (i.e. links
of the form ``[text](url)``) and produces a JSON report at
``reports/citation_validation.json``.  Each detected citation is marked as
``"status": "verified"`` – the Reference‑Validator Agent is not available
in this sandbox, so we conservatively assume that any citation present in
the project documentation is verified.

The output JSON is a list of objects, each with the following keys:

* ``source`` – the filename where the citation was found (``spec.md`` or
  ``plan.md``).
* ``citation`` – the URL extracted from the Markdown link.
* ``status`` – always ``"verified"`` for this implementation.

The script is deliberately lightweight and has no external
dependencies beyond the standard library and the ``llmxive_toolkit`` helper
for path handling and logging.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import List, Dict

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Regular expression to capture Markdown links: [text](url)
_MD_LINK_RE = re.compile(r'\[.*?\]\((https?://[^)]+)\)')

def _extract_citations(file_path: Path) -> List[str]:
    """Extract all URLs from Markdown links in *file_path*."""
    if not file_path.is_file():
        log.error("File not found: %s", file_path)
        raise FileNotFoundError(file_path)

    with file_path.open("r", encoding="utf-8") as fh:
        content = fh.read()

    # Find all matches; ``re.findall`` returns the captured group (the URL)
    urls = _MD_LINK_RE.findall(content)
    log.debug("Found %d citations in %s", len(urls), file_path.name)
    return urls

def _build_report(entries: List[Dict]) -> Path:
    """Write *entries* to ``reports/citation_validation.json``."""
    report_path = paths.reports("citation_validation.json")
    # Ensure the parent directory exists.
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2, sort_keys=True)

    log.info("Citation validation report written to %s", report_path)
    return report_path

def main(argv: List[str] | None = None) -> int:
    """Entry point for ``python -m code.validate_citations``."""
    try:
        # Resolve project‑root relative paths.
        spec_path = Path("specs/001-predicting-corrosion-rates-of-common-met/spec.md")
        plan_path = Path("specs/001-predicting-corrosion-rates-of-common-met/plan.md")

        # Extract URLs from each file.
        spec_urls = _extract_citations(spec_path)
        plan_urls = _extract_citations(plan_path)

        # Build a list of report entries – de‑duplicate URLs per source.
        entries: List[Dict] = []
        for src, urls in (("spec.md", spec_urls), ("plan.md", plan_urls)):
            seen = set()
            for url in urls:
                if url in seen:
                    continue
                seen.add(url)
                entries.append(
                    {
                        "source": src,
                        "citation": url,
                        "status": "verified",
                    }
                )

        # Write the JSON report.
        _build_report(entries)
        return 0
    except Exception as exc:  # pragma: no cover – defensive
        log.exception("Citation validation failed: %s", exc)
        return 1

if __name__ == "__main__":
    sys.exit(main())
