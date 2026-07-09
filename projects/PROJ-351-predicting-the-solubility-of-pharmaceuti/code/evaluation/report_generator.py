"""
Report Generator for Solubility Prediction Project (US3).

Compiles RMSE, R², p-value, statistical power, and performance delta
from the baseline (RF) and GNN models into a final summary table.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from evaluation.compare_models import load_json_metrics
from evaluation.statistical_test import load_predictions
from config.seeds import get_seed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("report_generator")

RESULTS_DIR = project_root / "results"
REPORT_OUTPUT_PATH = RESULTS_DIR / "final_summary.json"
REPORT_TEXT_OUTPUT_PATH = RESULTS_DIR / "final_summary.txt"

def load_baseline_metrics() -> Dict[str, Any]:
    """Load baseline (Random Forest) metrics from results."""
    path = RESULTS_DIR / "baseline_metrics.json"
    if not path.exists():
        raise FileNotFoundError(f"Baseline metrics not found at {path}. "
                                "Ensure T014/T015 have been completed.")
    return load_json_metrics(path)

def load_gnn_metrics() -> Dict[str, Any]:
    """Load GNN metrics from results."""
    path = RESULTS_DIR / "gnn_metrics.json"
    if not path.exists():
        raise FileNotFoundError(f"GNN metrics not found at {path}. "
                                "Ensure T024 has been completed.")
    return load_json_metrics(path)

def load_statistical_results() -> Dict[str, Any]:
    """Load statistical test results (p-value, power) from results."""
    path = RESULTS_DIR / "statistical_test_results.json"
    if not path.exists():
        raise FileNotFoundError(f"Statistical results not found at {path}. "
                                "Ensure T028 has been completed.")
    return load_json_metrics(path)

def calculate_delta(rf_rmse: float, gnn_rmse: float) -> float:
    """Calculate the RMSE delta (RF - GNN). Positive means GNN is better."""
    return rf_rmse - gnn_rmse

def generate_summary_table(
    rf_metrics: Dict[str, Any],
    gnn_metrics: Dict[str, Any],
    stats_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compile all metrics into a structured summary dictionary.
    """
    rf_rmse = rf_metrics.get("rmse", 0.0)
    rf_r2 = rf_metrics.get("r2", 0.0)
    
    gnn_rmse = gnn_metrics.get("rmse", 0.0)
    gnn_r2 = gnn_metrics.get("r2", 0.0)
    
    p_value = stats_results.get("p_value", 0.0)
    power = stats_results.get("power", 0.0)
    
    rmse_delta = calculate_delta(rf_rmse, gnn_rmse)
    
    # Determine significance
    is_significant = p_value < 0.05
    
    # Determine winner
    if gnn_rmse < rf_rmse:
        winner = "GNN"
    elif rf_rmse < gnn_rmse:
        winner = "Random Forest"
    else:
        winner = "Tie"

    summary = {
        "project": "Predicting Solubility of Pharmaceutical Compounds (ESOL)",
        "model_comparison": {
            "baseline": {
                "model": "Random Forest",
                "rmse": rf_rmse,
                "r_squared": rf_r2
            },
            "advanced": {
                "model": "Message Passing Neural Network (MPNN)",
                "rmse": gnn_rmse,
                "r_squared": gnn_r2
            }
        },
        "statistical_analysis": {
            "p_value": p_value,
            "statistical_power": power,
            "alpha_threshold": 0.05,
            "is_significant": is_significant
        },
        "performance_delta": {
            "rmse_improvement": rmse_delta,
            "winner": winner,
            "interpretation": f"{'GNN outperforms' if is_significant and winner == 'GNN' else 'No significant improvement' if not is_significant else 'Winner determined'}"
        },
        "metadata": {
            "seed": get_seed(),
            "generated_by": "T031_ReportGenerator"
        }
    }
    
    return summary

def save_report_text(summary: Dict[str, Any]) -> None:
    """Save a human-readable text summary to results/."""
    lines = [
        "=" * 60,
        "FINAL SUMMARY REPORT: Solubility Prediction (ESOL)",
        "=" * 60,
        "",
        "MODEL PERFORMANCE:",
        f"  Baseline (Random Forest):",
        f"    RMSE: {summary['model_comparison']['baseline']['rmse']:.4f}",
        f"    R²:   {summary['model_comparison']['baseline']['r_squared']:.4f}",
        f"  Advanced (GNN MPNN):",
        f"    RMSE: {summary['model_comparison']['advanced']['rmse']:.4f}",
        f"    R²:   {summary['model_comparison']['advanced']['r_squared']:.4f}",
        "",
        "STATISTICAL SIGNIFICANCE:",
        f"  P-value: {summary['statistical_analysis']['p_value']:.6f}",
        f"  Power:   {summary['statistical_analysis']['statistical_power']:.4f}",
        f"  Significant (p < 0.05): {summary['statistical_analysis']['is_significant']}",
        "",
        "CONCLUSION:",
        f"  Winner: {summary['performance_delta']['winner']}",
        f"  RMSE Delta (RF - GNN): {summary['performance_delta']['rmse_improvement']:.4f}",
        f"  Interpretation: {summary['performance_delta']['interpretation']}",
        "",
        "=" * 60
    ]
    
    with open(REPORT_TEXT_OUTPUT_PATH, 'w') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Text report saved to {REPORT_TEXT_OUTPUT_PATH}")

def main(args: Optional[argparse.Namespace] = None) -> None:
    """Main entry point for report generation."""
    logger.info("Starting Report Generation (T031)...")
    
    try:
        # Ensure results directory exists
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load dependencies
        rf_metrics = load_baseline_metrics()
        gnn_metrics = load_gnn_metrics()
        stats_results = load_statistical_results()
        
        logger.info("All required metrics loaded successfully.")
        
        # Generate summary
        summary = generate_summary_table(rf_metrics, gnn_metrics, stats_results)
        
        # Save JSON report
        with open(REPORT_OUTPUT_PATH, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"JSON report saved to {REPORT_OUTPUT_PATH}")
        
        # Save human-readable report
        save_report_text(summary)
        
        logger.info("Report generation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during report generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate final summary report for US3.")
    parser.add_argument("--output-dir", type=str, default=str(RESULTS_DIR), 
                        help="Directory to save reports (default: results/)")
    args = parser.parse_args()
    
    if args.output_dir:
        # Update global path if overridden (though usually fixed per spec)
        pass 
        
    main(args)
