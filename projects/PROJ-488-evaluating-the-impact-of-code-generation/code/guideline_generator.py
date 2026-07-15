"""
Guideline Generator Module for PROJ-488.

Generates review guideline recommendations based on statistical analysis results.
Specifically looks for metrics with adjusted p < 0.05 AND |Cliff's delta| >= 0.1.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Import from local project modules
from data_model import MetricResult
from state_tracker import load_state_file, save_state_file, update_state_with_artifact
from logging_config import get_logger

# Constants
SIGNIFICANCE_THRESHOLD = 0.05
EFFECT_SIZE_THRESHOLD = 0.1
RESULTS_DIR = Path("results")
GUIDELINES_FILE = RESULTS_DIR / "guidelines.md"
STATE_FILE = Path("state") / "projects" / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def setup_guideline_logger() -> logging.Logger:
    """Setup a dedicated logger for guideline generation."""
    logger = get_logger("guideline_generator")
    return logger

def load_statistical_results(metrics_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load statistical results from the metrics and statistical analysis output files.
    
    Expected files:
    - data/metrics/<metric_type>_comparison.csv (raw comparisons)
    - data/metrics/mann_whitney_results.csv (p-values)
    - data/metrics/cliffs_delta_results.csv (effect sizes)
    - data/metrics/bh_corrected_results.csv (adjusted p-values)
    
    Returns a dictionary keyed by metric type with p-values and effect sizes.
    """
    logger = setup_guideline_logger()
    results = {}
    
    if metrics_dir is None:
        metrics_dir = Path("data") / "metrics"
    
    if not metrics_dir.exists():
        logger.error(f"Metrics directory not found: {metrics_dir}")
        return results

    # Load Mann-Whitney U results (raw p-values)
    mw_file = metrics_dir / "mann_whitney_results.csv"
    if mw_file.exists():
        import pandas as pd
        try:
            df_mw = pd.read_csv(mw_file)
            for _, row in df_mw.iterrows():
                metric_name = row.get('metric_name', row.get('metric', 'unknown'))
                if metric_name not in results:
                    results[metric_name] = {}
                results[metric_name]['raw_p_value'] = row.get('p_value', None)
        except Exception as e:
            logger.warning(f"Could not load Mann-Whitney results: {e}")

    # Load Benjamini-Hochberg corrected results (adjusted p-values)
    bh_file = metrics_dir / "bh_corrected_results.csv"
    if bh_file.exists():
        import pandas as pd
        try:
            df_bh = pd.read_csv(bh_file)
            for _, row in df_bh.iterrows():
                metric_name = row.get('metric_name', row.get('metric', 'unknown'))
                if metric_name not in results:
                    results[metric_name] = {}
                results[metric_name]['adjusted_p_value'] = row.get('adjusted_p_value', None)
        except Exception as e:
            logger.warning(f"Could not load BH corrected results: {e}")

    # Load Cliff's Delta results
    cd_file = metrics_dir / "cliffs_delta_results.csv"
    if cd_file.exists():
        import pandas as pd
        try:
            df_cd = pd.read_csv(cd_file)
            for _, row in df_cd.iterrows():
                metric_name = row.get('metric_name', row.get('metric', 'unknown'))
                if metric_name not in results:
                    results[metric_name] = {}
                results[metric_name]['cliffs_delta'] = row.get('cliffs_delta', None)
                results[metric_name]['magnitude'] = row.get('magnitude', 'unknown')
        except Exception as e:
            logger.warning(f"Could not load Cliff's Delta results: {e}")

    logger.info(f"Loaded statistical results for {len(results)} metrics")
    return results

def determine_recommendation(metric_name: str, stats: Dict[str, Any]) -> Optional[str]:
    """
    Determine if a guideline recommendation is needed for a metric.
    
    Criteria:
    - adjusted p-value < 0.05
    - |Cliff's delta| >= 0.1
    
    Returns a recommendation string if criteria met, None otherwise.
    """
    adj_p = stats.get('adjusted_p_value')
    delta = stats.get('cliffs_delta')
    magnitude = stats.get('magnitude', 'unknown')

    if adj_p is None or delta is None:
        return None

    try:
        adj_p_val = float(adj_p)
        delta_val = float(delta)
    except (ValueError, TypeError):
        return None

    # Check criteria
    if adj_p_val < SIGNIFICANCE_THRESHOLD and abs(delta_val) >= EFFECT_SIZE_THRESHOLD:
        direction = "higher" if delta_val > 0 else "lower"
        mag_label = magnitude if magnitude != 'unknown' else "medium"
        
        recommendation = (
            f"**{metric_name}**: Significant difference detected (adj. p={adj_p_val:.4f}, "
            f"|Cliff's δ|={abs(delta_val):.4f}, {mag_label} effect). "
            f"LLM-generated code shows {direction} values compared to human-written code. "
            f"Recommendation: Review {metric_name} thresholds in code quality gates; "
            f"consider adjusting expectations for LLM-generated snippets."
        )
        return recommendation
    
    return None

def generate_guidelines_content(results: Dict[str, Any]) -> str:
    """
    Generate the full markdown content for the guidelines file.
    """
    logger = setup_guideline_logger()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content_lines = [
        "# Code Review Guidelines: LLM-Generated vs Human-Written Code",
        "",
        f"**Generated**: {timestamp}",
        f"**Project**: PROJ-488 - Evaluating the Impact of Code Generation",
        "",
        "## Summary",
        "",
        "This document provides review guidelines based on statistical comparisons between "
        "human-written (CodeSearchNet) and LLM-generated (CodeParrot/CodeGen) code snippets. "
        "Guidelines are generated for metrics showing statistically significant differences "
        f"(adjusted p < {SIGNIFICANCE_THRESHOLD}) with meaningful effect sizes "
        f"(|Cliff's δ| >= {EFFECT_SIZE_THRESHOLD}).",
        "",
        "## Statistical Criteria",
        "",
        "- **Significance Level**: Adjusted p-value < 0.05 (Benjamini-Hochberg corrected)",
        "- **Effect Size Threshold**: |Cliff's Delta| >= 0.1",
        "",
        "## Recommendations",
        ""
    ]

    recommendations = []
    for metric_name, stats in sorted(results.items()):
        rec = determine_recommendation(metric_name, stats)
        if rec:
            recommendations.append(rec)
            logger.info(f"Generated recommendation for metric: {metric_name}")

    if not recommendations:
        content_lines.append(
            "No metrics met the criteria for significant difference with meaningful effect size. "
            "Current review guidelines may be applied uniformly to both human-written and "
            "LLM-generated code without specific adjustments."
        )
    else:
        content_lines.append(f"Found {len(recommendations)} metric(s) requiring guideline adjustment:")
        content_lines.append("")
        for i, rec in enumerate(recommendations, 1):
            content_lines.append(f"{i}. {rec}")
            content_lines.append("")

    content_lines.extend([
        "## Methodology",
        "",
        "1. **Data Sources**: Human-written code from CodeSearchNet, LLM-generated code from CodeParrot/CodeGen",
        "2. **Preprocessing**: Filtered to Python functions, matched by length distribution",
        "3. **Metrics**: Cyclomatic complexity, maintainability index, bug indicators (radon/pylint)",
        "4. **Statistical Tests**: Mann-Whitney U test with Benjamini-Hochberg correction",
        "5. **Effect Size**: Cliff's Delta with magnitude interpretation",
        "",
        "## Next Steps",
        "",
        "- Integrate these guidelines into the code review workflow",
        "- Monitor for drift as LLM models evolve",
        "- Re-run analysis periodically with updated datasets",
        "",
        "---",
        f"*Generated by llmXive Pipeline - Task T032*"
    ])

    return "\n".join(content_lines)

def write_guidelines_to_file(content: str, output_path: Optional[Path] = None) -> Path:
    """
    Write the generated guidelines content to a markdown file.
    """
    if output_path is None:
        output_path = GUIDELINES_FILE
    
    logger = setup_guideline_logger()
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Guidelines written to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to write guidelines: {e}")
        raise

def update_state_with_guidelines(output_path: Path) -> None:
    """
    Update the project state file to record the guidelines artifact.
    """
    logger = setup_guideline_logger()
    
    try:
        state = load_state_file(STATE_FILE)
        update_state_with_artifact(
            state,
            artifact_type="guidelines",
            artifact_path=str(output_path),
            description="Review guideline recommendations based on statistical analysis"
        )
        save_state_file(state, STATE_FILE)
        logger.info(f"State updated with guidelines artifact: {output_path}")
    except Exception as e:
        logger.warning(f"Could not update state with guidelines: {e}")
        # Non-fatal, continue

def run_guideline_generation(
    metrics_dir: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Main entry point for guideline generation.
    
    1. Load statistical results from data/metrics/
    2. Determine recommendations for each metric
    3. Generate markdown content
    4. Write to results/guidelines.md
    5. Update state tracker
    
    Returns the path to the generated file.
    """
    logger = setup_guideline_logger()
    logger.info("Starting guideline generation pipeline")
    
    # Load results
    results = load_statistical_results(metrics_dir)
    if not results:
        logger.warning("No statistical results found. Generating empty guidelines.")
    
    # Generate content
    content = generate_guidelines_content(results)
    
    # Write file
    if output_path is None:
        output_path = GUIDELINES_FILE
    written_path = write_guidelines_to_file(content, output_path)
    
    # Update state
    update_state_with_guidelines(written_path)
    
    logger.info("Guideline generation completed successfully")
    return written_path

def main() -> int:
    """
    CLI entry point for guideline generation.
    """
    logger = setup_guideline_logger()
    logger.info("Running guideline generator via CLI")
    
    try:
        output_path = run_guideline_generation()
        logger.info(f"Guidelines generated at: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Guideline generation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
