"""
Module: 06_generate_report.py
Purpose: Generate the final interpretation report JSON with disclaimers and FDR values.

This module aggregates results from previous analysis steps (permutation importance,
Benjamini-Hochberg correction, overlap statistics) and generates a comprehensive
interpretation report.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.hashing import compute_file_hash


def load_json_file(file_path: str) -> dict:
    """
    Load a JSON file and return its contents as a dictionary.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary containing the JSON data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_feature_importance_data() -> dict:
    """
    Load feature importance data from the FDR-corrected p-values file.
    
    Returns:
        Dictionary containing feature importance data with corrected p-values
    """
    # Path to the FDR-corrected p-values file (output of T030)
    fdr_file = Path("data/results/feature_importance_pvalues.json")
    
    if not fdr_file.exists():
        raise FileNotFoundError(
            f"Feature importance data not found at {fdr_file}. "
            "Please ensure T030 (Benjamini-Hochberg correction) has been completed."
        )
    
    return load_json_file(str(fdr_file))


def load_overlap_report() -> dict:
    """
    Load the overlap statistics report from the overlap analysis.
    
    Returns:
        Dictionary containing overlap statistics and analysis results
    """
    overlap_file = Path("data/results/overlap_report.json")
    
    if not overlap_file.exists():
        raise FileNotFoundError(
            f"Overlap report not found at {overlap_file}. "
            "Please ensure T031 (overlap statistics calculation) has been completed."
        )
    
    return load_json_file(str(overlap_file))


def load_model_metrics() -> dict:
    """
    Load model performance metrics from the training step.
    
    Returns:
        Dictionary containing model metrics (R², RMSE, etc.)
    """
    metrics_file = Path("data/results/model_metrics.json")
    
    if not metrics_file.exists():
        raise FileNotFoundError(
            f"Model metrics not found at {metrics_file}. "
            "Please ensure T023 (model metrics calculation) has been completed."
        )
    
    return load_json_file(str(metrics_file))


def generate_interpretation_report() -> dict:
    """
    Generate the final interpretation report by aggregating all analysis results.
    
    This function:
    1. Loads feature importance data with FDR-corrected p-values
    2. Loads overlap statistics with known terpene synthase families
    3. Loads model performance metrics
    4. Aggregates disclaimers and metadata
    5. Returns a comprehensive report dictionary
    
    Returns:
        Dictionary containing the complete interpretation report
    """
    # Load all required data sources
    feature_data = load_feature_importance_data()
    overlap_data = load_overlap_report()
    model_metrics = load_model_metrics()
    
    # Build the report structure
    report = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "report_version": "1.0",
            "pipeline_stage": "interpretation",
            "task_id": "T032"
        },
        "model_performance": {
            "r_squared": model_metrics.get("r_squared", None),
            "rmse": model_metrics.get("rmse", None),
            "cross_validation": model_metrics.get("cross_validation", {}),
            "disclaimer": model_metrics.get("disclaimer", 
                "Findings are associational due to observational data. "
                "Correlation does not imply causation.")
        },
        "feature_importance": {
            "method": "permutation_importance",
            "fdr_correction": "benjamini_hochberg",
            "significant_features": feature_data.get("significant_features", []),
            "all_features": feature_data.get("all_features", []),
            "p_value_threshold": feature_data.get("p_value_threshold", 0.05),
            "fdr_threshold": feature_data.get("fdr_threshold", 0.05)
        },
        "biological_interpretation": {
            "overlap_analysis": overlap_data,
            "key_findings": [],
            "terpene_synthase_families": overlap_data.get("terpene_synthase_families", [])
        },
        "disclaimers": [
            "Findings are associational due to observational data.",
            "Correlation does not imply causation.",
            "Results should be validated with experimental follow-up.",
            "Feature importance reflects predictive power, not necessarily biological causality.",
            "The model was trained on CPU-only infrastructure without GPU acceleration."
        ],
        "limitations": [
            "Observational data limits causal inference.",
            "Feature importance may be affected by multicollinearity.",
            "Model performance may vary on external datasets.",
            "Biological interpretation is limited to known terpene synthase families."
        ]
    }
    
    # Add key findings based on analysis results
    key_findings = []
    
    # Add findings from overlap analysis
    if overlap_data.get("significant_overlap", False):
        key_findings.append(
            f"Significant overlap detected between top predictive features and "
            f"known terpene synthase families (p-value: {overlap_data.get('overlap_p_value', 'N/A')})."
        )
    
    # Add findings from feature importance
    significant_count = len(feature_data.get("significant_features", []))
    if significant_count > 0:
        key_findings.append(
            f"Identified {significant_count} features with FDR-corrected p-values < 0.05."
        )
    
    # Add model performance context
    r_squared = model_metrics.get("r_squared")
    if r_squared is not None:
        if r_squared > 0.7:
            key_findings.append("Model demonstrates strong predictive performance (R² > 0.7).")
        elif r_squared > 0.5:
            key_findings.append("Model demonstrates moderate predictive performance (0.5 < R² ≤ 0.7).")
        else:
            key_findings.append("Model demonstrates limited predictive performance (R² ≤ 0.5).")
    
    report["biological_interpretation"]["key_findings"] = key_findings
    
    return report


def save_report(report: dict, output_path: str) -> str:
    """
    Save the interpretation report to a JSON file.
    
    Args:
        report: Dictionary containing the report data
        output_path: Path where the report should be saved
        
    Returns:
        Path to the saved file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Compute and store hash for verification
    file_hash = compute_file_hash(str(output_file))
    return str(output_file)


def main():
    """
    Main entry point for generating the interpretation report.
    
    This function:
    1. Loads all required analysis results
    2. Generates the comprehensive interpretation report
    3. Saves the report to data/results/interpretation_report.json
    4. Prints summary information
    """
    print("=" * 60)
    print("T032: Generating Final Interpretation Report")
    print("=" * 60)
    
    try:
        # Generate the report
        print("Loading analysis results...")
        report = generate_interpretation_report()
        
        # Save the report
        output_path = "data/results/interpretation_report.json"
        print(f"Saving report to {output_path}...")
        saved_path = save_report(report, output_path)
        
        # Print summary
        print("\nReport Summary:")
        print(f"  - Generated at: {report['metadata']['generated_at']}")
        print(f"  - Model R²: {report['model_performance']['r_squared']}")
        print(f"  - Model RMSE: {report['model_performance']['rmse']}")
        print(f"  - Significant features (FDR < 0.05): {len(report['feature_importance']['significant_features'])}")
        print(f"  - Key findings: {len(report['biological_interpretation']['key_findings'])}")
        print(f"  - Disclaimers: {len(report['disclaimers'])}")
        print(f"\nReport saved to: {saved_path}")
        print("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Please ensure all prerequisite tasks have been completed:")
        print("  - T030: Benjamini-Hochberg correction")
        print("  - T031: Overlap statistics calculation")
        print("  - T023: Model metrics calculation")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error generating report: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())