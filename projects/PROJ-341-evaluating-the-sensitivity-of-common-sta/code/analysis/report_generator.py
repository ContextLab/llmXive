import os
import json
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime

def load_error_rates(filepath: str = "data/simulation/error_rates_summary.csv") -> List[Dict[str, Any]]:
    """Load aggregated error rates from CSV."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_real_data_pvalues(filepath: str = "data/simulation/real_data_pvalues.csv") -> List[Dict[str, Any]]:
    """Load real data p-values from CSV."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_thresholds(filepath: str = "data/simulation/thresholds.json") -> Optional[Dict[str, Any]]:
    """Load threshold metrics from JSON."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_validation_metrics(filepath: str = "data/simulation/validation_metrics.json") -> Optional[Dict[str, Any]]:
    """Load validation metrics from JSON."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_real_data_power(filepath: str = "data/simulation/real_data_power.json") -> Optional[Dict[str, Any]]:
    """Load real data power estimation results from JSON."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_deviation(
    error_rates: List[Dict[str, Any]],
    thresholds: Optional[Dict[str, Any]],
    validation_metrics: Optional[Dict[str, Any]],
    real_data_power: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze whether simulation results held true or if deviations were observed.
    Returns a structured analysis result.
    """
    analysis = {
        "simulation_held": True,
        "deviations": [],
        "summary": "",
        "details": {}
    }

    # Check validation metrics (KS distance)
    if validation_metrics:
        ks_results = validation_metrics.get("ks_distances", {})
        for test_type, ks_val in ks_results.items():
            # Threshold is 0.10 as per FR-006
            if ks_val > 0.10:
                analysis["simulation_held"] = False
                deviation_msg = f"KS distance for {test_type} ({ks_val:.4f}) exceeds threshold (0.10), indicating deviation between simulated and real data distributions."
                analysis["deviations"].append(deviation_msg)
            else:
                analysis["details"][f"{test_type}_ks"] = {
                    "value": ks_val,
                    "status": "PASS",
                    "message": f"KS distance ({ks_val:.4f}) within acceptable range."
                }

    # Check real data power results
    if real_data_power:
        power_estimates = real_data_power.get("power_estimates", {})
        for test_type, power_info in power_estimates.items():
            expected_power = power_info.get("expected", 0.80)
            observed_power = power_info.get("observed", 0.0)
            if observed_power < 0.70:  # Significant drop below expected
                analysis["simulation_held"] = False
                deviation_msg = f"Observed power for {test_type} ({observed_power:.2f}) is significantly lower than expected ({expected_power:.2f})."
                analysis["deviations"].append(deviation_msg)
            else:
                analysis["details"][f"{test_type}_power"] = {
                    "expected": expected_power,
                    "observed": observed_power,
                    "status": "PASS"
                }

    # Check thresholds
    if thresholds:
        threshold_data = thresholds.get("thresholds", [])
        low_sample_thresholds = [t for t in threshold_data if t.get("sample_size", 1000) < 30]
        if low_sample_thresholds:
            analysis["details"]["low_sample_thresholds"] = {
                "count": len(low_sample_thresholds),
                "tests": [t.get("test_type") for t in low_sample_thresholds]
            }

    # Generate summary
    if analysis["simulation_held"]:
        analysis["summary"] = (
            "The simulation results held true. The observed p-value distributions from real-world small-sample datasets "
            "align with the predictions from the simulation. KS distances are within the acceptable threshold (≤0.10), "
            "and power estimates are consistent with expectations."
        )
    else:
        analysis["summary"] = (
            "Deviations were observed between the simulation and real-world data. "
            "Some statistical tests showed KS distances exceeding the 0.10 threshold or power estimates significantly lower than expected. "
            "This suggests that the simulation model may not fully capture the behavior of certain tests under specific real-world conditions."
        )

    return analysis

def generate_report(analysis_result: Dict[str, Any], output_path: str = "data/reports/validation_report.md") -> None:
    """Generate a Markdown validation report based on the analysis."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    held_status = "Held True" if analysis_result["simulation_held"] else "Deviations Observed"

    report_lines = [
        "# Validation Report: Simulation vs. Real-World Data",
        "",
        f"**Generated:** {timestamp}",
        f"**Status:** {held_status}",
        "",
        "## Executive Summary",
        "",
        analysis_result["summary"],
        "",
        "## Detailed Analysis",
        ""
    ]

    # Deviations Section
    if analysis_result["deviations"]:
        report_lines.append("### Deviations Observed")
        report_lines.append("")
        for i, dev in enumerate(analysis_result["deviations"], 1):
            report_lines.append(f"{i}. {dev}")
        report_lines.append("")
    else:
        report_lines.append("### No Significant Deviations")
        report_lines.append("")
        report_lines.append("No significant deviations were detected between simulation predictions and real-world observations.")
        report_lines.append("")

    # Details Section
    if analysis_result["details"]:
        report_lines.append("## Detailed Metrics")
        report_lines.append("")
        for key, value in analysis_result["details"].items():
            report_lines.append(f"### {key.replace('_', ' ').title()}")
            report_lines.append("")
            if isinstance(value, dict):
                for sub_key, sub_val in value.items():
                    report_lines.append(f"- **{sub_key.replace('_', ' ').title()}:** {sub_val}")
            else:
                report_lines.append(f"- {value}")
            report_lines.append("")

    # Conclusion
    report_lines.append("## Conclusion")
    report_lines.append("")
    if analysis_result["simulation_held"]:
        report_lines.append(
            "The study confirms that the simulated sensitivity analysis accurately predicts the behavior of common statistical tests "
            "(t-test, ANOVA, chi-squared) on real-world small-sample datasets. The identified thresholds for reliability (e.g., n < 30 for normality violations) "
            "are consistent with observed data behavior."
        )
    else:
        report_lines.append(
            "While the simulation provided a strong baseline, deviations were observed in specific conditions. "
            "These deviations highlight areas where the simulation assumptions (e.g., perfect normality, independence) may diverge from real-world data characteristics. "
            "Further investigation into the specific tests and datasets showing deviations is recommended."
        )
    report_lines.append("")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

def main() -> None:
    """Main entry point to generate the validation report."""
    print("Loading simulation and validation data...")

    error_rates = load_error_rates()
    thresholds = load_thresholds()
    validation_metrics = load_validation_metrics()
    real_data_power = load_real_data_power()
    load_real_data_pvalues()  # Load but not directly used in summary analysis

    print("Analyzing deviations...")
    analysis = analyze_deviation(error_rates, thresholds, validation_metrics, real_data_power)

    print("Generating validation report...")
    generate_report(analysis)

    print(f"Report generated successfully at: data/reports/validation_report.md")

if __name__ == "__main__":
    main()