"""
Report generation module.
Ensures findings are framed as associational (ROC-001) by filtering causal language.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Forbidden causal terms
CAUSAL_TERMS = [
    "cause", "causes", "causing", "caused",
    "effect", "effects", "affect", "affects", "affecting", "affected",
    "determine", "determines", "determining", "determined",
    "impact", "impacts", "impacting", "impacted",
    "influence", "influences", "influencing", "influenced",
    "drive", "drives", "driving", "driven",
    "result in", "leads to", "results in", "leads to"
]

def filter_causal_language(text: str) -> str:
    """
    Scan text for forbidden causal terms and replace with associational equivalents.
    
    Args:
        text: Input text
        
    Returns:
        Text with causal language replaced
    """
    result = text
    for term in CAUSAL_TERMS:
        # Case insensitive replacement
        import re
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        # Simple replacement strategy
        if term.lower() in ["cause", "causes", "causing", "caused"]:
            result = pattern.sub("is associated with", result)
        elif term.lower() in ["effect", "effects", "affect", "affects", "affecting", "affected"]:
            result = pattern.sub("is correlated with", result)
        elif term.lower() in ["determine", "determines", "determining", "determined"]:
            result = pattern.sub("is related to", result)
        elif term.lower() in ["impact", "impacts", "impacting", "impacted"]:
            result = pattern.sub("is associated with", result)
        elif term.lower() in ["influence", "influences", "influencing", "influenced"]:
            result = pattern.sub("is correlated with", result)
        elif term.lower() in ["drive", "drives", "driving", "driven"]:
            result = pattern.sub("is associated with", result)
        elif term.lower() in ["result in", "leads to", "results in", "leads to"]:
            result = pattern.sub("is associated with", result)
            
    return result

def generate_report(regression_results: Dict, anova_results: Dict, sensitivity_results: List, output_path: str) -> Dict[str, Any]:
    """
    Generate a textual report from analysis results.
    Ensures all language is associational per ROC-001.
    """
    # Build draft report
    draft = []
    draft.append("## Network Topology and Energy Transfer Analysis Report")
    draft.append("")
    draft.append("### Summary")
    draft.append("This study investigates the relationship between network topology metrics and energy diffusion rates.")
    draft.append("All findings are presented as associational correlations, not causal claims.")
    draft.append("")
    
    # Regression section
    draft.append("### Regression Analysis")
    lin_res = regression_results.get("linear", {})
    if lin_res.get("status") != "skipped":
        r_sq = lin_res.get("r_squared", 0)
        slope = lin_res.get("slope", 0)
        draft.append(f"Linear regression yielded R² = {r_sq:.4f} with slope = {slope:.4f}.")
        draft.append("Clustering coefficient is associated with diffusion rate.")
    else:
        draft.append("Regression analysis was skipped due to insufficient data.")
    draft.append("")
    
    # ANOVA section
    draft.append("### ANOVA Analysis")
    if anova_results.get("status") != "skipped":
        f_stat = anova_results.get("f_statistic", 0)
        p_val = anova_results.get("p_value", 1)
        draft.append(f"ANOVA F-statistic = {f_stat:.4f}, p-value = {p_val:.4f}.")
        if p_val < 0.05:
            draft.append("Significant differences in diffusion rates are associated with topology class.")
        else:
            draft.append("No significant differences in diffusion rates were detected across topology classes.")
    else:
        draft.append("ANOVA analysis was skipped.")
    draft.append("")
    
    # Sensitivity section
    draft.append("### Sensitivity Analysis")
    if sensitivity_results:
        draft.append(f"Sensitivity sweep tested {len(sensitivity_results)} clustering thresholds.")
        draft.append("Diffusion rates vary across different clustering coefficient thresholds.")
    else:
        draft.append("Sensitivity analysis was not performed.")
    draft.append("")
    
    # Disclaimer
    draft.append("### Limitations")
    draft.append("This study identifies correlational patterns. No causal inferences should be drawn.")
    draft.append("The phrase 'associational' is explicitly used to frame all findings.")
    
    raw_text = "\n".join(draft)
    filtered_text = filter_causal_language(raw_text)
    
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "title": "Network Topology Energy Transfer Study",
        "content": filtered_text,
        "roc_001_compliant": True
    }
    
    # Save report
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w') as f:
        json.dump(report_data, f, indent=2)
        
    logger.info(f"Report generated and saved to {output_path}")
    return report_data

def main():
    """Main entry point for report generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate analysis report")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    output_path = Path(args.output)
    stats_path = output_path / "analysis" / "statistical_outputs.json"
    sensitivity_path = output_path / "analysis" / "sensitivity_sweep.json"
    report_path = output_path / "analysis" / "report.json"
    
    # Load data
    stats_data = None
    if stats_path.exists():
        with open(stats_path, 'r') as f:
            stats_data = json.load(f)
            
    sens_data = []
    if sensitivity_path.exists():
        with open(sensitivity_path, 'r') as f:
            sens_json = json.load(f)
            sens_data = sens_json.get("results", [])
    
    report = generate_report(
        regression_results=stats_data.get("regression", {}) if stats_data else {},
        anova_results=stats_data.get("anova", {}) if stats_data else {},
        sensitivity_results=sens_data,
        output_path=str(report_path)
    )

if __name__ == "__main__":
    main()
