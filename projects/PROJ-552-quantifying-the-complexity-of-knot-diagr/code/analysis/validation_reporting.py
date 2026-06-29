"""
Hyperbolic Volume Validation Reporting Module.

This module handles the generation of human-readable reports (Markdown)
and JSON summaries for the hyperbolic volume validation results.
It was refactored from hyperbolic_volume_validation.py to separate
reporting logic from core validation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from reproducibility.logs import get_logger, log_operation
from .validation import ValidationResult, ValidationEntry

logger = get_logger(__name__)

def generate_validation_summary(result: ValidationResult) -> dict:
    """
    Generate a summary dictionary for the validation result.
    
    Args:
        result: The ValidationResult object.
        
    Returns:
        A dictionary containing summary statistics.
    """
    return {
        "timestamp": result.timestamp,
        "total_records": result.total_records,
        "successful_lookups": result.successful_lookups,
        "failed_lookups": result.failed_lookups,
        "matches_within_tolerance": result.matches_within_tolerance,
        "matches_percentage": result.matches_percentage,
        "tolerance": result.tolerance,
        "status": "PASS" if result.matches_percentage >= 90.0 else "FAIL"
    }

def write_validation_report_md(result: ValidationResult, output_path: Path) -> None:
    """
    Write a Markdown report of the validation results.
    
    Args:
        result: The ValidationResult object.
        output_path: Path to save the Markdown file.
    """
    summary = generate_validation_summary(result)
    
    lines = [
        "# Hyperbolic Volume Validation Report",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**Source:** Knot Atlas vs. KnotInfo",
        f"**Tolerance:** {result.tolerance}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"| :--- | :--- |",
        f"| Total Records | {summary['total_records']} |",
        f"| Successful Lookups | {summary['successful_lookups']} |",
        f"| Failed Lookups | {summary['failed_lookups']} |",
        f"| Matches (within tolerance) | {summary['matches_within_tolerance']} |",
        f"| Match Percentage | {summary['matches_percentage']:.2f}% |",
        f"| Status | {summary['status']} |",
        "",
        "## Interpretation",
        "",
    ]
    
    if summary['matches_percentage'] >= 90.0:
        lines.append(f"The dataset meets the FR-013 requirement of ≥ 90% match.")
    else:
        lines.append(f"**Warning:** The dataset does NOT meet the FR-013 requirement of ≥ 90% match.")
        lines.append(f"Only {summary['matches_percentage']:.2f}% of records matched within tolerance.")
        lines.append("Review `docs/reproducibility/hyperbolic_volume_validation.md` for details on failures.")
        
    lines.extend([
        "",
        "## Mismatch Details",
        "",
        "The following knots had volumes that differed from KnotInfo by more than the tolerance:",
        "",
    ])
    
    mismatches = [e for e in result.entries if not e.match and e.error_message is None]
    # Actually, if match is False, error_message might be set or it's just a mismatch
    # Let's list entries where match is False
    mismatches = [e for e in result.entries if not e.match]
    
    if not mismatches:
        lines.append("No mismatches found among successful lookups.")
    else:
        lines.append("| Knot ID | Atlas Volume | KnotInfo Volume | Difference |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for entry in mismatches[:50]: # Limit to first 50 for readability
            diff = abs(entry.atlas_volume - entry.knotinfo_volume) if entry.knotinfo_volume else 0
            lines.append(
                f"| {entry.knot_id} | {entry.atlas_volume} | {entry.knotinfo_volume} | {diff:.6f} |"
            )
        if len(mismatches) > 50:
            lines.append(f"... and {len(mismatches) - 50} more.")

    lines.extend([
        "",
        "## Lookup Failures",
        "",
        "The following knots could not be validated (missing data or API error):",
        "",
    ])
    
    failures = [e for e in result.entries if e.error_message is not None]
    if not failures:
        lines.append("No lookup failures.")
    else:
        lines.append("| Knot ID | Error Message |")
        lines.append("| :--- | :--- |")
        for entry in failures[:50]:
            lines.append(f"| {entry.knot_id} | {entry.error_message} |")
        if len(failures) > 50:
            lines.append(f"... and {len(failures) - 50} more.")

    content = "\n".join(lines)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    logger.info(f"Validation report written to {output_path}")

def save_validation_results_json(result: ValidationResult, output_path: Path) -> None:
    """
    Save detailed validation entries to a JSON file.
    
    Args:
        result: The ValidationResult object.
        output_path: Path to save the JSON file.
    """
    from dataclasses import asdict
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump([asdict(e) for e in result.entries], f, indent=2)
    logger.info(f"Validation details written to {output_path}")

def generate_full_report(
    result: ValidationResult,
    md_path: Path,
    json_path: Optional[Path] = None
) -> None:
    """
    Generate both Markdown and JSON reports.
    
    Args:
        result: The ValidationResult object.
        md_path: Path for the Markdown report.
        json_path: Optional path for the JSON details.
    """
    log_operation("report_generation", "Hyperbolic Volume Report", {
        "md_path": str(md_path),
        "json_path": str(json_path) if json_path else "None"
    })
    
    write_validation_report_md(result, md_path)
    if json_path:
        save_validation_results_json(result, json_path)
    
    log_operation("report_generation_complete", "Hyperbolic Volume Report", {"status": "success"})

def main():
    """CLI entry point for reporting only (requires pre-computed results)."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Generate validation reports from JSON results.")
    parser.add_argument("--input-json", type=Path, required=True,
                        help="Path to the JSON results file from validation.py.")
    parser.add_argument("--output-md", type=Path, default=Path("docs/reproducibility/hyperbolic_volume_validation.md"),
                        help="Path to output Markdown report.")
    parser.add_argument("--output-json", type=Path, default=None,
                        help="Path to copy output JSON (optional).")
                        
    args = parser.parse_args()
    
    if not args.input_json.exists():
        logger.error(f"Input file not found: {args.input_json}")
        return
        
    with open(args.input_json, 'r') as f:
        data = json.load(f)
        
    # Reconstruct ValidationResult
    # Note: This is a simplified reconstruction. Ideally, we'd have a full serialization format.
    # We assume the JSON contains the list of entries and we can infer stats.
    entries = [ValidationEntry(**item) for item in data]
    
    total = len(entries)
    successful = sum(1 for e in entries if e.error_message is None)
    failed = total - successful
    matches = sum(1 for e in entries if e.match)
    pct = (matches / successful * 100) if successful > 0 else 0.0
    
    result = ValidationResult(
        total_records=total,
        successful_lookups=successful,
        failed_lookups=failed,
        matches_within_tolerance=matches,
        matches_percentage=pct,
        tolerance=1e-6,
        entries=entries
    )
    
    generate_full_report(result, args.output_md, args.output_json)
    print(f"Reports generated successfully.")

if __name__ == "__main__":
    main()
