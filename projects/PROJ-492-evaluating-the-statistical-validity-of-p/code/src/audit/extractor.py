"""
extractor.py
--------------

Implements the extraction phase of the audit pipeline.

* Reads HTML files produced by ``src.audit.fetcher`` (stored under ``data/raw``).
* Attempts to extract the key fields required for an ``ABTestSummary`` model.
* Handles missing or malformed fields by logging a structured error code
  (``ERR-001`` – ``ERR-099``) as defined in the project constitution (FR‑007).
* Writes a JSON array of extracted ``ABTestSummary`` objects to
  ``data/extracted/ab_summaries.json``.
* The module can be executed directly: ``python -m src.audit.extractor``.
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any

from bs4 import BeautifulSoup

# Project imports – must match the declared API surface
from src.models.data_models import ABTestSummary
from src.utils.logger import get_default_logger, validate_error_code

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
RAW_HTML_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/extracted")
OUTPUT_FILE = OUTPUT_DIR / "ab_summaries.json"

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _log_error(code: str, message: str) -> None:
    """
    Log an error using the project's logger.  The ``code`` must be a valid
    ``ERR-###`` identifier – ``validate_error_code`` raises if the format is
    incorrect, ensuring we stay within the FR‑007 contract.
    """
    # Validate that the error code follows the required pattern
    validate_error_code(code)

    logger = get_default_logger()
    # The logger is configured to include timestamps etc.; we just
    # prepend the code for downstream parsing.
    logger.error(f"{code}: {message}")

def _extract_numeric(text: str) -> float | None:
    """
    Extract the first numeric value (int or float) from a string.
    Returns ``None`` if no number can be found.
    """
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None

# ---------------------------------------------------------------------------
# Core extraction logic
# ---------------------------------------------------------------------------

def extract_summary_from_html(html_content: str, source_path: Path) -> ABTestSummary | None:
    """
    Parse a single HTML document and build an ``ABTestSummary`` instance.

    Parameters
    ----------
    html_content: str
        Raw HTML source.
    source_path: Path
        Path to the file – used only for error reporting.

    Returns
    -------
    ABTestSummary | None
        The populated model, or ``None`` if critical fields are missing.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # The extraction heuristics are deliberately simple – they look for
    # elements whose ``id`` or ``class`` name contains a known keyword.
    # Real‑world implementations would be far more sophisticated.
    def _find_text(keywords: List[str]) -> str | None:
        for kw in keywords:
            # Try id first
            el = soup.find(attrs={"id": re.compile(kw, re.I)})
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
            # Then class
            el = soup.find(class_=re.compile(kw, re.I))
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        return None

    # -------------------------------------------------------------------
    # Extract individual fields – missing fields trigger an error log.
    # -------------------------------------------------------------------
    # 1. Test name / identifier
    test_name = _find_text(["test-name", "title", "heading"])
    if not test_name:
        _log_error("ERR-001", f"Missing test name in {source_path}")
        test_name = "unknown"

    # 2. Baseline conversion rate (or metric)
    baseline_raw = _find_text(["baseline", "control-rate", "control"])
    baseline = _extract_numeric(baseline_raw) if baseline_raw else None
    if baseline is None:
        _log_error("ERR-002", f"Missing or unparsable baseline in {source_path}")

    # 3. Variant conversion rate (or metric)
    variant_raw = _find_text(["variant", "treatment-rate", "treatment"])
    variant = _extract_numeric(variant_raw) if variant_raw else None
    if variant is None:
        _log_error("ERR-003", f"Missing or unparsable variant in {source_path}")

    # 4. Sample size – may be a single number or two numbers (control/variant)
    sample_raw = _find_text(["sample-size", "participants", "n"])
    # Accept formats like "N=1234", "1234", or "Control: 600, Variant: 634"
    sample_n = None
    if sample_raw:
        nums = re.findall(r"\d+", sample_raw)
        if len(nums) == 1:
            sample_n = int(nums[0])
        elif len(nums) >= 2:
            # If two numbers are present we store the total.
            sample_n = sum(int(n) for n in nums[:2])
    if sample_n is None:
        _log_error("ERR-004", f"Missing or unparsable sample size in {source_path}")

    # 5. Reported p‑value (may be an inequality)
    pvalue_raw = _find_text(["p-value", "pvalue", "pvalue"])
    pvalue = None
    if pvalue_raw:
        # Handle inequality forms like "< 0.05"
        if "<" in pvalue_raw or ">" in pvalue_raw:
            pvalue = pvalue_raw.strip()
        else:
            pvalue = _extract_numeric(pvalue_raw)
    if pvalue is None:
        _log_error("ERR-005", f"Missing or unparsable p‑value in {source_path}")

    # 6. Effect size (optional – many A/B reports omit it)
    effect_raw = _find_text(["effect-size", "lift", "relative-change"])
    effect_size = _extract_numeric(effect_raw) if effect_raw else None
    # No error code for optional fields; we simply store ``None`` if absent.

    # -------------------------------------------------------------------
    # Build the Pydantic model – any validation errors will be raised
    # by the model itself, which we also capture and log.
    # -------------------------------------------------------------------
    try:
        summary = ABTestSummary(
            test_name=test_name,
            baseline=baseline,
            variant=variant,
            sample_size=sample_n,
            p_value=pvalue,
            effect_size=effect_size,
            source_url=str(source_path),  # traceability
        )
    except Exception as exc:
        # Log a generic extraction failure – assign a code in the 090‑099
        # range to keep the namespace tidy.
        _log_error("ERR-090", f"Pydantic validation error for {source_path}: {exc}")
        return None

    return summary

def extract_all() -> List[ABTestSummary]:
    """
    Walk ``RAW_HTML_DIR`` and extract an ``ABTestSummary`` from each HTML file.
    Returns a list of successfully extracted summaries.
    """
    if not RAW_HTML_DIR.is_dir():
        _log_error("ERR-010", f"Raw HTML directory does not exist: {RAW_HTML_DIR}")
        return []

    summaries: List[ABTestSummary] = []
    for html_path in RAW_HTML_DIR.glob("*.html"):
        try:
            html_text = html_path.read_text(encoding="utf-8")
        except Exception as exc:
            _log_error("ERR-011", f"Unable to read {html_path}: {exc}")
            continue

        summary = extract_summary_from_html(html_text, html_path)
        if summary:
            summaries.append(summary)

    return summaries

def write_summaries_to_json(summaries: List[ABTestSummary]) -> None:
    """
    Serialize the list of ``ABTestSummary`` objects to JSON.
    The output directory is created if it does not exist.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Use ``model.dict()`` to get a plain‑dict representation.
    data = [s.dict() for s in summaries]
    OUTPUT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    logger = get_default_logger()
    logger.info(f"Wrote {len(summaries)} ABTestSummary records to {OUTPUT_FILE}")

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Entry point used by the CI pipeline and by developers.
    """
    logger = get_default_logger()
    logger.info("Starting extraction phase...")
    summaries = extract_all()
    write_summaries_to_json(summaries)
    logger.info("Extraction phase completed.")

if __name__ == "__main__":
    main()