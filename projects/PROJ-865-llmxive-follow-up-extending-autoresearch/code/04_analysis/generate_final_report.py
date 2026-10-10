"""
generate_final_report.py

This script compiles the final research report for the llmXive follow‑up project.
It reads a markdown template (docs/research_report_template.md) and injects
results extracted from the full experiment artifacts:

  * data/derived/full_regression_results.json
  * data/derived/error_taxonomy.json

If any of the required data files are missing, the script inserts a
placeholder notice so that the report can still be generated without
fabricating values.

The generated report is written to:
  docs/research_report.md
"""
import json
import sys
from pathlib import Path

# Project‑relative imports
from utils.logging import get_logger, log_stage_start, log_stage_end

logger = get_logger(__name__)

def _load_json(file_path: Path):
    """Load a JSON file; raise if unreadable."""
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _read_template(template_path: Path) -> str:
    """Return the template contents, falling back to a minimal built‑in template."""
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    # Minimal built‑in template with explicit placeholders
    return (
        "# Research Report\\n\\n"
        "## Methodology\\n"
        "(details omitted for brevity)\\n\\n"
        "## Results\\n\\n"
        "### Interaction Term Significance\\n"
        "{{interaction_term}}\\n\\n"
        "### Error Taxonomy\\n"
        "{{error_taxonomy}}\\n\\n"
        "## Discussion\\n"
        "(interpretation of the above results)\\n"
    )

def _format_interaction(regression_data: dict) -> str:
    """
    Produce a human‑readable summary of the interaction term.
    Expected keys (based on T026c) are:
      - interaction_coefficient
      - interaction_p_value
    If those keys are absent, the whole JSON blob is pretty‑printed.
    """
    coeff = regression_data.get("interaction_coefficient")
    p_val = regression_data.get("interaction_p_value")
    if coeff is not None and p_val is not None:
        return f"Interaction coefficient: {coeff}, p‑value: {p_val}"
    # Fallback – show the raw JSON (still real data, no fabrication)
    return json.dumps(regression_data, indent=2)

def _format_taxonomy(taxonomy_data: dict) -> str:
    """Pretty‑print the error taxonomy JSON."""
    return json.dumps(taxonomy_data, indent=2)

def main() -> int:
    log_stage_start("generate_final_report")
    # Resolve project‑root relative paths
    project_root = Path(__file__).resolve().parents[2]  # code/04_analysis/../..
    template_path = project_root / "docs" / "research_report_template.md"
    output_path = project_root / "docs" / "research_report.md"

    # Load template
    template = _read_template(template_path)

    # ------------------------------------------------------------------
    # 1️⃣ Interaction‑term section
    # ------------------------------------------------------------------
    regression_path = project_root / "data" / "derived" / "full_regression_results.json"
    if regression_path.exists():
        try:
            regression_json = _load_json(regression_path)
            interaction_section = _format_interaction(regression_json)
        except Exception as exc:
            logger.error(f"Failed to parse regression results: {exc}")
            interaction_section = "Error loading regression results."
    else:
        interaction_section = "Regression results not available (file missing)."

    # ------------------------------------------------------------------
    # 2️⃣ Error‑taxonomy section
    # ------------------------------------------------------------------
    taxonomy_path = project_root / "data" / "derived" / "error_taxonomy.json"
    if taxonomy_path.exists():
        try:
            taxonomy_json = _load_json(taxonomy_path)
            taxonomy_section = _format_taxonomy(taxonomy_json)
        except Exception as exc:
            logger.error(f"Failed to parse error taxonomy: {exc}")
            taxonomy_section = "Error loading error taxonomy."
    else:
        taxonomy_section = "Error taxonomy not available (file missing)."

    # ------------------------------------------------------------------
    # 3️⃣ Populate template
    # ------------------------------------------------------------------
    report_contents = (
        template.replace("{{interaction_term}}", interaction_section)
                .replace("{{error_taxonomy}}", taxonomy_section)
    )

    # Write the final markdown file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_contents, encoding="utf-8")
    logger.info(f"Research report written to {output_path}")

    log_stage_end("generate_final_report", status="PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
