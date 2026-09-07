"""
Generate the final paper draft from meta-analysis results.

This script renders a Markdown paper draft using Jinja2 templates,
incorporating results from the meta-analysis, bias tests, and
Bonferroni correction status.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Attempt to import Jinja2, but handle the case where it's missing
try:
    from jinja2 import Environment, FileSystemLoader, TemplateNotFound
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logging.warning("Jinja2 not available. Falling back to minimal text generation.")

from utils.config import get_project_root, ensure_directory
from utils.logger import get_logger

logger = get_logger(__name__)


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return None


def get_results_dict() -> Dict[str, Any]:
    """
    Aggregate all relevant result files into a single dictionary.
    
    This function loads:
    - meta_results.json (meta-analysis results)
    - bonferroni_status.json (correction status)
    - egger_test.json (bias test results)
    - heterogeneity_results.json (I² and Q statistics)
    - gate_result.json (quantitative/narrative mode)
    """
    project_root = get_project_root()
    derived_path = project_root / "data" / "derived"
    
    results = {
        "meta_analysis": None,
        "bonferroni": None,
        "egger": None,
        "heterogeneity": None,
        "gate": None,
        "timestamp": datetime.now().isoformat()
    }
    
    # Load meta-analysis results
    meta_path = derived_path / "meta_results.json"
    results["meta_analysis"] = load_json_file(meta_path)
    if results["meta_analysis"]:
        logger.info(f"Loaded meta-analysis results from {meta_path}")
    
    # Load Bonferroni status
    bonf_path = derived_path / "bonferroni_status.json"
    results["bonferroni"] = load_json_file(bonf_path)
    if results["bonferroni"]:
        logger.info(f"Loaded Bonferroni status from {bonf_path}")
    
    # Load Egger's test results
    egger_path = derived_path / "egger_test.json"
    results["egger"] = load_json_file(egger_path)
    if results["egger"]:
        logger.info(f"Loaded Egger's test results from {egger_path}")
    
    # Load heterogeneity results
    het_path = derived_path / "heterogeneity_results.json"
    results["heterogeneity"] = load_json_file(het_path)
    if results["heterogeneity"]:
        logger.info(f"Loaded heterogeneity results from {het_path}")
    
    # Load gate result
    gate_path = derived_path / "gate_result.json"
    results["gate"] = load_json_file(gate_path)
    if results["gate"]:
        logger.info(f"Loaded gate result from {gate_path}")
    
    return results


def generate_minimal_draft(results: Dict[str, Any]) -> str:
    """
    Generate a minimal text-based draft when Jinja2 is unavailable.
    
    This provides a fallback that still produces a readable document
    with the key findings.
    """
    lines = [
        "# Correlation Between Structural Brain Connectivity and Music Preferences",
        "",
        f"**Generated:** {results['timestamp']}",
        "",
        "## Executive Summary",
        "",
    ]
    
    # Gate status
    if results["gate"]:
        status = results["gate"].get("status", "unknown")
        lines.append(f"**Analysis Mode:** {status}")
        if status == "narrative_required":
            reason = results["gate"].get("reason", "Insufficient data")
            lines.append(f"**Reason:** {reason}")
        lines.append("")
    
    # Meta-analysis results
    if results["meta_analysis"]:
        lines.append("## Meta-Analysis Results")
        lines.append("")
        pooled_r = results["meta_analysis"].get("pooled_effect_size")
        if pooled_r is not None:
            lines.append(f"**Pooled Effect Size (r):** {pooled_r:.4f}")
            ci = results["meta_analysis"].get("confidence_interval")
            if ci:
                lines.append(f"**95% CI:** [{ci[0]:.4f}, {ci[1]:.4f}]")
        lines.append("")
    else:
        lines.append("## Meta-Analysis Results")
        lines.append("")
        lines.append("*Meta-analysis results not available.*")
        lines.append("")
    
    # Bonferroni correction
    if results["bonferroni"] and results["bonferroni"].get("bonferroni_applied"):
        lines.append("## Multiple Comparisons Correction")
        lines.append("")
        lines.append("**Bonferroni correction was applied.**")
        alpha_adj = results["bonferroni"].get("alpha_adj")
        if alpha_adj:
            lines.append(f"**Adjusted Alpha:** {alpha_adj:.6f}")
        lines.append("")
        lines.append("*Note: The Bonferroni correction is a conservative method that reduces the risk of Type I errors but may increase the risk of Type II errors (false negatives).*")
        lines.append("")
    
    # Heterogeneity
    if results["heterogeneity"] and not results["heterogeneity"].get("skipped"):
        lines.append("## Heterogeneity Analysis")
        lines.append("")
        i_squared = results["heterogeneity"].get("i_squared")
        if i_squared is not None:
            lines.append(f"**I² Statistic:** {i_squared:.2f}%")
            interpretation = results["heterogeneity"].get("interpretation")
            if interpretation:
                lines.append(f"**Interpretation:** {interpretation}")
        lines.append("")
    
    # Bias assessment
    if results["egger"] and not results["egger"].get("skipped"):
        lines.append("## Publication Bias Assessment")
        lines.append("")
        p_value = results["egger"].get("p_value")
        if p_value is not None:
            lines.append(f"**Egger's Test p-value:** {p_value:.4f}")
            if p_value < 0.05:
                lines.append("*Significant evidence of publication bias detected.*")
            else:
                lines.append("*No significant evidence of publication bias.*")
        lines.append("")
    
    lines.append("---")
    lines.append("*This report was generated automatically by the llmXive automated science pipeline.*")
    
    return "\n".join(lines)


def render_with_jinja2(results: Dict[str, Any], template_path: Path) -> str:
    """
    Render the paper draft using Jinja2 templating.
    
    Args:
        results: Dictionary containing all analysis results
        template_path: Path to the Jinja2 template file
        
    Returns:
        Rendered Markdown string
    """
    project_root = get_project_root()
    
    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(project_root),
        autoescape=False  # We're generating Markdown, not HTML
    )
    
    try:
        template = env.get_template(str(template_path.relative_to(project_root)))
    except TemplateNotFound:
        logger.warning(f"Template not found at {template_path}. Using minimal draft.")
        return generate_minimal_draft(results)
    
    # Render the template
    return template.render(
        results=results,
        timestamp=results["timestamp"],
        bonferroni_applied=results["bonferroni"] and results["bonferroni"].get("bonferroni_applied", False)
    )


def generate_paper_draft(output_path: Path) -> None:
    """
    Generate the final paper draft.
    
    This function:
    1. Loads all relevant result files
    2. Determines the template path
    3. Renders the draft using Jinja2 (or falls back to minimal text)
    4. Writes the output to the specified path
    
    Args:
        output_path: Path where the draft will be written
    """
    logger.info("Starting paper draft generation...")
    
    # Load all results
    results = get_results_dict()
    
    # Determine template path
    project_root = get_project_root()
    template_path = project_root / "docs" / "paper_draft.md"
    
    # Check if template exists
    if not template_path.exists():
        logger.warning(f"Template not found at {template_path}. Using minimal draft.")
        content = generate_minimal_draft(results)
    elif not JINJA2_AVAILABLE:
        logger.warning("Jinja2 not available. Using minimal draft.")
        content = generate_minimal_draft(results)
    else:
        try:
            content = render_with_jinja2(results, template_path)
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            logger.warning("Falling back to minimal draft.")
            content = generate_minimal_draft(results)
    
    # Ensure output directory exists
    ensure_directory(output_path.parent)
    
    # Write the output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Paper draft generated successfully at {output_path}")


def main() -> int:
    """Main entry point for the paper generation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate the final paper draft from meta-analysis results.")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to the output file (default: data/derived/paper_draft.md)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        project_root = get_project_root()
        output_path = project_root / "data" / "derived" / "paper_draft.md"
    
    try:
        generate_paper_draft(output_path)
        return 0
    except Exception as e:
        logger.error(f"Failed to generate paper draft: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())