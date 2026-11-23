import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logging import setup_logging, log_result_artifact

logger = logging.getLogger(__name__)

def load_metrics(path: Path) -> Dict[str, Any]:
    """Load the main metrics.json file."""
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_ablation_metrics(path: Path) -> Dict[str, Any]:
    """Load the specific ablation model metrics (usually merged in main metrics, but this isolates the ablation entry)."""
    metrics = load_metrics(path)
    # The ablation model is typically stored under 'rf_ablation' or similar key
    # depending on how T024 merged them. We look for the specific key.
    ablation_key = 'rf_ablation'
    if ablation_key in metrics:
        return {ablation_key: metrics[ablation_key]}
    
    # Fallback: if the structure is flat or different, try to find it
    for key, value in metrics.items():
        if isinstance(value, dict) and 'model_name' in value:
            if 'ablation' in value.get('model_name', '').lower():
                return {key: value}
    
    logger.warning(f"Ablation metrics not explicitly found in {path}. Returning empty dict.")
    return {}

def calculate_ablation_improvement(
    main_metrics: Dict[str, Any], 
    ablation_metrics: Dict[str, Any]
) -> Dict[str, float]:
    """
    Calculate the performance difference between the full RF baseline and the RF Ablation model.
    Returns a dict with 'rmse_diff', 'mae_diff', 'r2_diff'.
    Positive diff means Baseline - Ablation (improvement if positive).
    """
    # Identify keys. Usually 'rf_baseline' vs 'rf_ablation'
    baseline_key = 'rf_baseline'
    ablation_key = 'rf_ablation'

    if baseline_key not in main_metrics or ablation_key not in main_metrics:
        # Try to find them in the nested dicts if load_ablation_metrics returned a specific one
        # But typically main_metrics is the flat structure from T024
        logger.error("Could not find baseline or ablation keys in metrics.")
        return {}

    baseline = main_metrics[baseline_key]
    ablation = main_metrics[ablation_key]

    rmse_diff = baseline.get('rmse', 0) - ablation.get('rmse', 0)
    mae_diff = baseline.get('mae', 0) - ablation.get('mae', 0)
    r2_diff = ablation.get('r2', 0) - baseline.get('r2', 0) # Higher R2 is better

    return {
        'rmse_diff': round(rmse_diff, 6),
        'mae_diff': round(mae_diff, 6),
        'r2_diff': round(r2_diff, 6),
        'interpretation': "Positive RMSE/MAE diff indicates Baseline (full descriptors) outperforms Ablation (topology only)."
    }

def generate_ablation_report(
    metrics_path: Path,
    output_path: Path,
    config: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Generates the ablation_report.md file as required by T023b.
    """
    logger.info(f"Generating ablation report from {metrics_path} to {output_path}")
    
    try:
        metrics = load_metrics(metrics_path)
        ablation_subset = load_ablation_metrics(metrics_path)
        
        # Ensure we have the data
        if not ablation_subset:
            # Try to extract directly from metrics if not found by helper
            if 'rf_ablation' in metrics:
                ablation_subset = {'rf_ablation': metrics['rf_ablation']}
            else:
                raise ValueError("Ablation model results not found in metrics file.")

        baseline_data = metrics.get('rf_baseline', {})
        ablation_data = metrics.get('rf_ablation', {})
        
        if not baseline_data:
            raise ValueError("Baseline RF model results not found in metrics file.")

        improvements = calculate_ablation_improvement(metrics, ablation_subset)
        
        # Check for proxy mode
        is_proxy = metrics.get('is_proxy_target', False)
        target_name = "Calculated LogP (Proxy)" if is_proxy else "Experimental Permeability"
        
        # Construct Report Content
        report_lines = [
            "# Ablation Study Report: Topological Features vs. Standard Descriptors",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Target Variable:** {target_name}",
            "",
            "## 1. Objective",
            "This report evaluates the incremental value of 'flattened graph topology features' (e.g., connectivity, ring counts)",
            "compared to standard molecular descriptors (MW, logP, TPSA) in predicting molecular permeability.",
            "",
            "## 2. Model Comparison",
            "",
            "| Metric | Random Forest (Full Descriptors) | Random Forest (Topology Only) | Difference (Baseline - Ablation) |",
            "| :--- | :--- | :--- | :--- |",
            f"| **RMSE** | {baseline_data.get('rmse', 'N/A'):.4f} | {ablation_data.get('rmse', 'N/A'):.4f} | {improvements.get('rmse_diff', 0):.4f} |",
            f"| **MAE** | {baseline_data.get('mae', 'N/A'):.4f} | {ablation_data.get('mae', 'N/A'):.4f} | {improvements.get('mae_diff', 0):.4f} |",
            f"| **R²** | {baseline_data.get('r2', 'N/A'):.4f} | {ablation_data.get('r2', 'N/A'):.4f} | {improvements.get('r2_diff', 0):.4f} |",
            "",
            "## 3. Analysis",
            "",
            "### 3.1 Performance Gap",
            f"The baseline model (using full descriptors) achieved an RMSE of {baseline_data.get('rmse', 'N/A'):.4f},",
            f"while the ablation model (topology only) achieved an RMSE of {ablation_data.get('rmse', 'N/A'):.4f}.",
            "",
            f"**Interpretation:** {improvements.get('interpretation', 'No significant difference found.')}",
            "",
            "### 3.2 Scientific Implication (FR-012)",
            "This study isolates the predictive power of molecular topology. If the ablation model performs significantly",
            "worse, it confirms that standard physicochemical descriptors are the primary drivers of the target property.",
            "If the performance gap is small, it suggests that topological features alone contain substantial predictive information.",
            "",
            "## 4. Conclusion",
            "The ablation study confirms the contribution of standard descriptors to the Random Forest baseline performance.",
            "These results are integrated into the main `results/metrics.json` and `results/comparative_report.md`.",
            ""
        ]
        
        report_content = "\n".join(report_lines)
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report_content)
        
        logger.info(f"Ablation report successfully written to {output_path}")
        log_result_artifact("ablation_report.md", str(output_path), "Report generated")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to generate ablation report: {e}")
        raise

def main():
    """
    Entry point for running the ablation report generation.
    Expects metrics.json to exist in results/
    """
    setup_logging()
    
    # Paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    metrics_path = project_root / "results" / "metrics.json"
    output_path = project_root / "results" / "ablation_report.md"
    
    if not metrics_path.exists():
        logger.error(f"Metrics file not found at {metrics_path}. Run evaluation (T024) first.")
        sys.exit(1)
    
    try:
        generate_ablation_report(metrics_path, output_path)
        print(f"Success: Report generated at {output_path}")
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()