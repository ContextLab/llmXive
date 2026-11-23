import os
import sys
import json
import warnings
from pathlib import Path
from typing import Dict, Any, Optional

import config

def load_json_safe(filepath: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if the file does not exist."""
    if not filepath.exists():
        warnings.warn(f"File not found: {filepath}", UserWarning)
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        warnings.warn(f"Invalid JSON in {filepath}: {e}", UserWarning)
        return None

def check_data_gap_status() -> Dict[str, Any]:
    """
    Check the data gap status from data_gap_status.json.
    Returns a dict with 'status' and 'missing_sources' (if any).
    """
    status_path = config.PROJECT_ROOT / "data" / "gap_status" / "data_gap_status.json"
    data = load_json_safe(status_path)
    if data is None:
        return {"status": "UNKNOWN", "missing_sources": []}
    return {
        "status": data.get("status", "UNKNOWN"),
        "missing_sources": data.get("missing_sources", [])
    }

def generate_research_report(
    gap_status: Dict[str, Any],
    results_data: Optional[Dict[str, Any]],
    metrics_data: Optional[Dict[str, Any]],
    perm_results: Optional[Dict[str, Any]],
    threshold_data: Optional[Dict[str, Any]]
) -> str:
    """
    Generate the Markdown content for research.md based on the provided data sources.
    """
    lines = []
    lines.append("# Research Report: Predicting Coral Bleaching Susceptibility")
    lines.append("")
    lines.append("## 1. Data Gap Status")
    lines.append("")
    status = gap_status.get("status", "UNKNOWN")
    missing = gap_status.get("missing_sources", [])
    
    if status == "PASS":
        lines.append("**Status**: PASS - All required data sources were successfully verified and ingested.")
    elif status == "FAIL":
        lines.append(f"**Status**: FAIL - Data ingestion halted due to missing sources.")
        lines.append("")
        lines.append("### Missing Sources:")
        for source in missing:
            lines.append(f"- {source}")
    else:
        lines.append(f"**Status**: {status} - Unable to verify data gap status.")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Model Performance (Constitutional Gate)")
    lines.append("")
    
    if results_data:
        roc_auc = results_data.get("roc_auc")
        perf_status = results_data.get("performance_status", "N/A")
        
        if roc_auc is not None:
            lines.append(f"**ROC-AUC Score**: {roc_auc:.4f}")
            lines.append(f"**Constitutional Threshold**: 0.80")
            if perf_status == "PASS":
                lines.append(f"**Result**: PASS - Model meets the required performance threshold.")
            else:
                lines.append(f"**Result**: FAIL - Model did not meet the required performance threshold.")
        else:
            lines.append("**ROC-AUC Score**: Not Available (Model training failed or no score recorded)")
            lines.append(f"**Result**: {perf_status}")
    else:
        lines.append("**ROC-AUC Score**: Not Available (results.json missing)")
        lines.append("**Result**: N/A")
        
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Feature Stability and Importance")
    lines.append("")
    
    if metrics_data and metrics_data.get("independent_data_available"):
        auprc = metrics_data.get("auprc")
        if auprc is not None:
            lines.append(f"**AUPRC (Independent Validation)**: {auprc:.4f}")
        else:
            lines.append("**AUPRC**: Not Available")
    else:
        lines.append("**AUPRC**: Not Available (Independent validation data missing or not applicable)")
    
    lines.append("")
    lines.append("### Permutation Importance (FDR Corrected)")
    if perm_results:
        rankings = perm_results.get("ranking", [])
        corrected_pvalues = perm_results.get("corrected_pvalues", {})
        
        if rankings:
            lines.append("| Rank | Feature | Corrected P-Value |")
            lines.append("| :--- | :--- | :--- |")
            for i, feat in enumerate(rankings):
                p_val = corrected_pvalues.get(feat, "N/A")
                lines.append(f"| {i+1} | {feat} | {p_val} |")
        else:
            lines.append("No permutation importance results available.")
    else:
        lines.append("Permutation importance results not found.")
        
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. Threshold Sensitivity Analysis")
    lines.append("")
    
    if threshold_data:
        thresholds = threshold_data.get("thresholds", [])
        lines.append("| Threshold | False Positive Rate | False Negative Rate |")
        lines.append("| :--- | :--- | :--- |")
        for t in thresholds:
            fp = t.get("fp_rate", "N/A")
            fn = t.get("fn_rate", "N/A")
            lines.append(f"| {t.get('cutoff', 'N/A')} | {fp} | {fn} |")
        
        # Summary
        if len(thresholds) > 1:
            fps = [t.get("fp_rate") for t in thresholds if isinstance(t.get("fp_rate"), (int, float))]
            fns = [t.get("fn_rate") for t in thresholds if isinstance(t.get("fn_rate"), (int, float))]
            if fps:
                lines.append(f"**FP Rate Range**: {min(fps):.4f} - {max(fps):.4f}")
            if fns:
                lines.append(f"**FN Rate Range**: {min(fns):.4f} - {max(fns):.4f}")
    else:
        lines.append("Threshold sensitivity analysis results not found.")
        
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 5. Conclusion")
    lines.append("")
    lines.append("This report summarizes the findings from the coral bleaching susceptibility prediction pipeline.")
    lines.append("Key metrics include the ROC-AUC score against the constitutional threshold, feature stability via permutation importance,")
    lines.append("and the robustness of risk classification across different probability thresholds.")
    
    return "\n".join(lines)

def main():
    """
    Main entry point to generate the research.md report.
    """
    project_root = config.PROJECT_ROOT
    
    # Define paths based on config
    gap_status_path = project_root / "data" / "gap_status" / "data_gap_status.json"
    results_path = project_root / "results.json"
    metrics_path = project_root / "metrics.json"
    perm_results_path = project_root / "data" / "processed" / "permutation_results.json"
    threshold_path = project_root / "data" / "processed" / "threshold_sensitivity.json"
    output_path = project_root / "research.md"
    
    # Load data
    gap_status = check_data_gap_status()
    results_data = load_json_safe(results_path)
    metrics_data = load_json_safe(metrics_path)
    perm_results = load_json_safe(perm_results_path)
    threshold_data = load_json_safe(threshold_path)
    
    # Generate report content
    report_content = generate_research_report(
        gap_status, results_data, metrics_data, perm_results, threshold_data
    )
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"Research report generated successfully at: {output_path}")

if __name__ == "__main__":
    main()