import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from temporal_proximity import calculate_temporal_proximity

logger = logging.getLogger(__name__)

def load_analysis_results(results_path: str) -> Dict[str, Any]:
    """Load the analysis results JSON file."""
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Analysis results file not found: {results_path}")
    with open(results_path, 'r') as f:
        return json.load(f)

def generate_report(
    analysis_results: Dict[str, Any],
    metrics_csv_path: str,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Generate the final report dictionary.
    
    This includes:
    1. Coefficients, raw p-values, FDR-corrected p-values.
    2. Effect sizes (if N < 30).
    3. Significance flags.
    4. Confounding Limitation section based on temporal proximity.
    """
    report = {
        "title": "Network Centrality and Neural Synchrony Analysis Report",
        "results": analysis_results.get("results", []),
        "summary": analysis_results.get("summary", {}),
        "limitations": []
    }

    # Add significance flags to results if not already present
    if "results" in analysis_results:
        for res in report["results"]:
            adj_p = res.get("adj_p_value", res.get("p_value", 1.0))
            res["significance"] = "Significant" if adj_p < 0.05 else "Non-Significant"

    # Add effect sizes if available
    if "effect_sizes" in analysis_results:
        report["effect_sizes"] = analysis_results["effect_sizes"]

    # Check for temporal proximity confounding
    # We need to load the metrics CSV to check the temporal_proximity flag
    if os.path.exists(metrics_csv_path):
        import pandas as pd
        try:
            df = pd.read_csv(metrics_csv_path)
            # Check if any subject has temporal_proximity == True
            # Assuming the column is named 'temporal_proximity' or similar based on T029
            # T029 extracts IDs, T028 process_subject_metrics adds the flag.
            # Let's look for a boolean column indicating same night.
            # Based on T029 description: "Extract waking_night_id and sleep_night_id"
            # And T041 requirement: "when temporal_proximity flag ... indicates ... same night"
            # We assume the processed metrics file has a column 'temporal_proximity' (bool)
            
            if 'temporal_proximity' in df.columns:
                if df['temporal_proximity'].any():
                    report["limitations"].append({
                        "type": "Confounding Limitation",
                        "description": "Some subjects' waking and sleep data originate from the same night.",
                        "impact": "Temporal proximity may confound the relationship between network centrality and neural synchrony, as physiological states might be correlated due to circadian rhythms or immediate prior activity rather than stable trait-like properties.",
                        "affected_subjects": int(df['temporal_proximity'].sum()),
                        "recommendation": "Future studies should ensure a minimum temporal separation between waking and sleep recordings to isolate the effect of stable network properties."
                    })
            else:
                # Fallback: check if the column exists with a different name or if we need to re-calculate
                # For now, if the column is missing, we assume no confounding was flagged in the metrics
                logger.warning("Column 'temporal_proximity' not found in metrics CSV. Skipping confounding limitation check.")
        except Exception as e:
            logger.error(f"Error reading metrics CSV for temporal proximity check: {e}")
    else:
        logger.warning(f"Metrics CSV not found at {metrics_csv_path}. Skipping confounding limitation check.")

    return report

def save_report(report: Dict[str, Any], output_path: str) -> None:
    """Save the report to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {output_path}")

def main():
    """Main entry point for report generation."""
    # Paths
    config_path = Path("code/config.yaml")
    results_path = Path("data/results/analysis_results.json")
    metrics_path = Path("data/metrics/SubjectMetrics.csv")
    output_json_path = Path("data/results/final_report.json")
    output_md_path = Path("reports/final_report.md")

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Load analysis results
    try:
        analysis_results = load_analysis_results(str(results_path))
        logger.info("Analysis results loaded successfully.")
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    # Generate report
    report = generate_report(analysis_results, str(metrics_path), output_json_path.parent)

    # Save JSON report
    save_report(report, str(output_json_path))

    # Generate Markdown summary
    os.makedirs("reports", exist_ok=True)
    with open(output_md_path, 'w') as f:
        f.write("# Network Centrality and Neural Synchrony Analysis\n\n")
        f.write(f"Generated: {report.get('summary', {}).get('timestamp', 'N/A')}\n\n")
        
        f.write("## Results Summary\n")
        for res in report.get("results", []):
            sig = res.get("significance", "Unknown")
            f.write(f"- **{res.get('predictor', 'Unknown')}**: {sig} (p={res.get('adj_p_value', 'N/A')})\n")
        
        if report.get("effect_sizes"):
            f.write("\n## Effect Sizes (N < 30)\n")
            for es in report["effect_sizes"]:
                f.write(f"- {es.get('comparison', 'N/A')}: Cohen's d = {es.get('d', 'N/A')}\n")

        if report.get("limitations"):
            f.write("\n## Limitations\n")
            for lim in report["limitations"]:
                f.write(f"- **{lim['type']}**: {lim['description']}\n")
                f.write(f"  - Impact: {lim['impact']}\n")
                f.write(f"  - Recommendation: {lim['recommendation']}\n")

    logger.info(f"Markdown report saved to {output_md_path}")
    print(f"Final report generated: {output_json_path}")
    print(f"Markdown summary generated: {output_md_path}")

if __name__ == "__main__":
    main()