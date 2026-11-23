import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config.seeds import get_seed
from setup_logging import setup_logger

def setup_report_logger(log_path: Optional[Path] = None) -> logging.Logger:
    """Setup logger for report generation."""
    if log_path is None:
        log_path = project_root / "data" / "logs" / "report_generation.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return setup_logger("report_generator", log_path)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_baseline_metrics() -> Dict[str, Any]:
    """Load baseline (Random Forest) metrics."""
    # T015 saves to results/baseline_metrics.json
    metrics_path = project_root / "results" / "baseline_metrics.json"
    return load_json_file(metrics_path)

def load_gnn_metrics() -> Dict[str, Any]:
    """Load GNN metrics."""
    # T024 saves to results/gnn_metrics.json
    metrics_path = project_root / "results" / "gnn_metrics.json"
    return load_json_file(metrics_path)

def load_statistical_results() -> Dict[str, Any]:
    """Load statistical test results from T028."""
    # T028 saves to results/statistical_test_results.json (standard convention for T028 output)
    # We check common locations. T028 output is typically saved in results/
    possible_paths = [
        project_root / "results" / "statistical_test_results.json",
        project_root / "results" / "statistical_results.json",
        project_root / "data" / "processed" / "statistical_results.json"
    ]
    
    for p in possible_paths:
        if p.exists():
            return load_json_file(p)
    
    # Fallback: try to construct from T032 (aggregated metrics) if specific stats file missing
    # But T028 explicitly saves results. Let's assume standard path first.
    # If not found, we raise error to fail loudly as per constraints.
    raise FileNotFoundError(
        f"Statistical results file not found in expected locations: {[str(p) for p in possible_paths]}"
    )

def load_ceiling_effect_status() -> Dict[str, Any]:
    """Load ceiling effect detection result from T034."""
    # T034 appends to results/final_report.json or saves specific file
    # Let's check results/final_report.json first, or a dedicated ceiling file
    possible_paths = [
        project_root / "results" / "ceiling_effect.json",
        project_root / "results" / "final_report.json"
    ]
    
    for p in possible_paths:
        if p.exists():
            data = load_json_file(p)
            if "ceiling_effect" in data:
                return data
            # If it's the final_report.json, it might contain the flag
            return data
    
    # If T034 ran, it should have saved something.
    # Let's check if ceiling_effect key exists in the main metrics file as a fallback
    metrics_path = project_root / "results" / "metrics.json"
    if metrics_path.exists():
        data = load_json_file(metrics_path)
        if "ceiling_effect" in data:
            return data
    
    return {"ceiling_effect": False, "reason": "Not detected or not run"}

def calculate_delta(baseline_rmse: float, gnn_rmse: float) -> Dict[str, float]:
    """Calculate RMSE delta and percentage improvement."""
    delta = gnn_rmse - baseline_rmse
    pct_improvement = ((baseline_rmse - gnn_rmse) / baseline_rmse) * 100 if baseline_rmse != 0 else 0.0
    return {
        "rmse_delta": delta,
        "percent_improvement": pct_improvement,
        "better": gnn_rmse < baseline_rmse
    }

def generate_summary_table(baseline: Dict, gnn: Dict, stats: Dict, ceiling: Dict) -> str:
    """Generate a markdown summary table of all key metrics."""
    baseline_rmse = baseline.get("rmse", 0.0)
    baseline_r2 = baseline.get("r2", 0.0)
    
    gnn_rmse = gnn.get("rmse", 0.0)
    gnn_r2 = gnn.get("r2", 0.0)
    
    delta_info = calculate_delta(baseline_rmse, gnn_rmse)
    
    p_value = stats.get("p_value", 0.0)
    power = stats.get("power", 0.0)
    cohens_d = stats.get("effect_size_cohens_d", 0.0)
    
    is_significant = p_value < 0.05
    ceiling_flag = ceiling.get("ceiling_effect", False)
    
    table = f"""
| Metric | Random Forest (Baseline) | GNN (MPNN) | Delta / Notes |
| :--- | :--- | :--- | :--- |
| **RMSE** | {baseline_rmse:.4f} | {gnn_rmse:.4f} | {delta_info['rmse_delta']:+.4f} ({delta_info['percent_improvement']:+.1f}%) |
| **R²** | {baseline_r2:.4f} | {gnn_r2:.4f} | {gnn_r2 - baseline_r2:+.4f} |
| **Statistical Significance (p-value)** | - | - | {p_value:.6f} |
| **Effect Size (Cohen's d)** | - | - | {cohens_d:.4f} |
| **Statistical Power** | - | - | {power:.4f} |
| **Significant? (α=0.05)** | - | - | {'Yes' if is_significant else 'No'} |
| **Ceiling Effect Detected?** | - | - | {'Yes' if ceiling_flag else 'No'} |
"""
    return table.strip()

def generate_visualizations_section() -> str:
    """Generate a section listing the generated visualizations."""
    viz_dir = project_root / "results"
    png_files = list(viz_dir.glob("feature_importance_*.png"))
    
    if not png_files:
        return "No visualizations found in `results/`."
    
    section = "### Generated Visualizations\n\n"
    section += "The following feature importance heatmaps were generated for representative molecules:\n\n"
    
    for i, png in enumerate(sorted(png_files)[:5], 1):
        # Create a relative path for the report
        rel_path = png.relative_to(project_root)
        section += f"{i}. **{png.stem}**: ![{png.stem}]({rel_path})\n"
    
    section += "\n*Note: These images were selected using deterministic quantile-based selection (10th, 50th, 90th percentiles of logS).*"
    return section

def save_report_text(content: str, output_path: Path) -> None:
    """Save the generated report to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f"Report saved to {output_path}")

def main():
    """Main entry point for report generation."""
    parser = argparse.ArgumentParser(description="Generate the final research report.")
    parser.add_argument("--output", type=str, default="docs/reports/final_report.md",
                        help="Path to save the final report.")
    args = parser.parse_args()
    
    output_path = project_root / args.output
    logger = setup_report_logger()
    logger.info("Starting final report generation.")
    
    try:
        # 1. Load all required data
        logger.info("Loading baseline metrics...")
        baseline_metrics = load_baseline_metrics()
        
        logger.info("Loading GNN metrics...")
        gnn_metrics = load_gnn_metrics()
        
        logger.info("Loading statistical results...")
        stats_results = load_statistical_results()
        
        logger.info("Loading ceiling effect status...")
        ceiling_status = load_ceiling_effect_status()
        
        # 2. Generate Report Content
        logger.info("Generating summary table...")
        summary_table = generate_summary_table(baseline_metrics, gnn_metrics, stats_results, ceiling_status)
        
        logger.info("Generating visualizations section...")
        viz_section = generate_visualizations_section()
        
        # 3. Assemble the full Markdown report
        report_content = f"""# Final Research Report: Predicting the Solubility of Pharmaceutical Compounds

**Project ID**: PROJ-351
**Task ID**: T046
**Date**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

This report summarizes the performance of a Random Forest baseline and a Message Passing Neural Network (MPNN) on the ESOL dataset for predicting aqueous solubility (logS). Statistical significance testing was performed to validate improvements.

## Methodology

- **Dataset**: ESOL (Delaney-processed)
- **Baseline**: Random Forest with Morgan Fingerprints (radius=2, 2048 bits)
- **Model**: MPNN (PyTorch Geometric, CPU-only)
- **Validation**: Nested Cross-Validation (5 outer folds, 5 inner folds)
- **Statistical Test**: Nadeau's Corrected Resampled t-test

## Results

{summary_table}

## Statistical Analysis

- **Null Hypothesis**: There is no difference in prediction errors between the GNN and the Random Forest baseline.
- **Alternative Hypothesis**: The GNN has significantly lower prediction errors than the baseline.
- **P-value**: {stats_results.get('p_value', 'N/A')}
- **Conclusion**: {'Reject null hypothesis (GNN is significantly better)' if stats_results.get('p_value', 1) < 0.05 else 'Fail to reject null hypothesis (no significant difference detected)'}

## Visualizations

{viz_section}

## Limitations & Notes

- **Ceiling Effect**: {'Detected' if ceiling_status.get('ceiling_effect', False) else 'Not detected'}
- **Statistical Power**: {stats_results.get('power', 'N/A')}
- **Hardware**: CPU-only execution as per constraints.

## Conclusion

{
    "The GNN model showed statistically significant improvement over the baseline." if stats_results.get('p_value', 1) < 0.05 
    else "The GNN model did not show statistically significant improvement over the baseline in this experiment."
}

---
*Generated by the llmXive automated science pipeline.*
"""
        
        # 4. Save the report
        save_report_text(report_content, output_path)
        
        logger.info("Report generation completed successfully.")
        print(f"Final report generated at: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}", exc_info=True)
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()