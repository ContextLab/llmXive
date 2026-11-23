import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from code.utils.logger import get_logger
from code.utils.config import load_config_from_env

logger = get_logger(__name__)


def get_disclaimer() -> str:
    """
    Return a specific text block stating the associational nature of findings.
    """
    return (
        "DISCLAIMER: All findings are associational, not causal. "
        "Code complexity is a mediator; controlling for it may introduce collider bias."
    )


def load_json_report(file_path: Path) -> Dict[str, Any]:
    """
    Safely load a JSON report file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Required report not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def aggregate_data() -> Dict[str, Any]:
    """
    Load VIF, Power, Stats, and Audit results from their respective JSON files.
    Output: Aggregated dictionary for report generation.
    """
    reports_dir = Path("docs/reports")

    vif_path = reports_dir / "vif_diagnostics.json"
    power_path = reports_dir / "power_analysis.json"
    stats_path = reports_dir / "statistical_analysis.json"
    audit_path = reports_dir / "audit_accuracy.json"

    data: Dict[str, Any] = {}

    try:
        data["vif"] = load_json_report(vif_path)
    except FileNotFoundError as e:
        logger.warning(str(e))
        data["vif"] = None

    try:
        data["power"] = load_json_report(power_path)
    except FileNotFoundError as e:
        logger.warning(str(e))
        data["power"] = None

    try:
        data["stats"] = load_json_report(stats_path)
    except FileNotFoundError as e:
        logger.warning(str(e))
        data["stats"] = None

    try:
        data["audit"] = load_json_report(audit_path)
    except FileNotFoundError as e:
        logger.warning(str(e))
        data["audit"] = None

    return data


def render_template(template_path: Path, data: Dict[str, Any]) -> str:
    """
    Load template and inject data.
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Simple injection: replace {{DATA}} with formatted JSON or specific keys
    # Assuming the template expects a JSON block or specific keys.
    # For robustness, we'll inject the JSON string of the data.
    import json
    data_json = json.dumps(data, indent=2)

    # If the template uses specific markers like {{VIF_RESULTS}}, we would replace those.
    # Since the spec says "inject report_data.json", we assume a placeholder or just appending.
    # Let's assume the template has a placeholder {{REPORT_DATA}}.
    if "{{REPORT_DATA}}" in template_content:
        return template_content.replace("{{REPORT_DATA}}", data_json)

    # Fallback: append at the end if no placeholder found (unlikely for a real template)
    logger.warning("Template placeholder {{REPORT_DATA}} not found. Appending data at end.")
    return template_content + "\n\n# Data\n" + data_json


def write_final_report(
    draft_path: Path,
    final_path: Path,
    disclaimer: Optional[str] = None
) -> None:
    """
    Read draft_report.md, append disclaimer, and write to final_report.md.
    """
    if not draft_path.exists():
        raise FileNotFoundError(f"Draft report not found: {draft_path}")

    with open(draft_path, "r", encoding="utf-8") as f:
        content = f.read()

    if disclaimer is None:
        disclaimer = get_disclaimer()

    final_content = content + "\n\n" + disclaimer

    with open(final_path, "w", encoding="utf-8") as f:
        f.write(final_content)

    logger.info(f"Final report written to {final_path}")


def add_limitations(final_report_path: Path, vif_data: Optional[Dict[str, Any]]) -> None:
    """
    Append a "Limitations" section to the final report.
    Discusses:
    1. Observational Nature of the study.
    2. Mediator Bias introduced by controlling for code complexity.
    Cites specific VIF results from T028 if available.
    """
    if not final_report_path.exists():
        raise FileNotFoundError(f"Final report not found: {final_report_path}")

    limitations_text = [
        "\n\n## Limitations",
        "",
        "### Observational Nature",
        "",
        "This study is based on observational data from GitHub pull requests. "
        "Consequently, all findings regarding the impact of LLM-generated code on review quality are associational "
        "and do not establish causality. Unobserved confounders (e.g., developer experience, project maturity, "
        "team dynamics) may influence both the likelihood of using LLM tools and the resulting review metrics.",
        "",
        "### Mediator Bias",
        ""
    ]

    # Add VIF context if available
    if vif_data:
        limitations_text.append(
            "The analysis controlled for code complexity as a potential confounder. "
            "However, code complexity acts as a mediator between the code generation method (LLM vs. Human) and "
            "review outcomes. Controlling for a mediator can introduce collider bias, potentially distorting the "
            "estimated effect of the generation method."
        )
        limitations_text.append("")
        limitations_text.append("**VIF Diagnostics:**")
        limitations_text.append("")
        
        # Format VIF results for the report
        if "predictors" in vif_data:
            for pred in vif_data["predictors"]:
                name = pred.get("predictor", "Unknown")
                score = pred.get("vif_score", "N/A")
                limitations_text.append(f"- **{name}**: VIF = {score}")
        else:
            # Fallback if structure is different
            limitations_text.append(f"- Raw VIF Data: {vif_data}")
    else:
        limitations_text.append(
            "The analysis controlled for code complexity as a potential confounder. "
            "However, code complexity acts as a mediator between the code generation method (LLM vs. Human) and "
            "review outcomes. Controlling for a mediator can introduce collider bias, potentially distorting the "
            "estimated effect of the generation method."
        )
        limitations_text.append("")
        limitations_text.append(
            "**Note:** VIF diagnostic results were not available for inclusion in this section."
        )

    limitations_text.append("")
    limitations_text.append(
        "Future work should consider instrumental variable approaches or randomized controlled trials "
        "to better isolate the causal impact of LLM code generation tools."
    )

    limitations_section = "\n".join(limitations_text)

    # Read existing content
    with open(final_report_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Append limitations
    new_content = content + limitations_section

    # Write back
    with open(final_report_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    logger.info(f"Limitations section appended to {final_report_path}")


def main() -> None:
    """
    Main entry point for report generation and limitations addition.
    """
    logger.info("Starting report generation pipeline...")

    # 1. Aggregate Data
    reports_dir = Path("docs/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    data = aggregate_data()

    # 2. Render Template (Assuming template exists, otherwise skip to final report generation logic)
    # The task T035b handles the actual template rendering to draft_report.md.
    # This task T043 focuses on the limitations section which runs after T035c.
    # We assume the final_report.md exists from T035c.

    final_report_path = reports_dir / "final_report.md"
    vif_path = reports_dir / "vif_diagnostics.json"

    # Load VIF data specifically for the limitations section
    vif_data = None
    if vif_path.exists():
        try:
            vif_data = load_json_report(vif_path)
        except Exception as e:
            logger.error(f"Failed to load VIF data for limitations: {e}")
            vif_data = None

    # Add Limitations
    if final_report_path.exists():
        add_limitations(final_report_path, vif_data)
    else:
        logger.warning(f"Final report {final_report_path} not found. Skipping limitations append.")
        # In a real pipeline, this might be an error if T035c is supposed to run first.
        # But we proceed gracefully as per task scope.

    logger.info("Report generation and limitations addition complete.")


if __name__ == "__main__":
    main()