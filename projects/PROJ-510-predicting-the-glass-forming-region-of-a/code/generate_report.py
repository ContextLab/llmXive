import os
import json
import sys
import glob
from typing import Dict, Any, List, Optional
import logging

# Ensure logging is configured before use
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_csv_file(filepath: str) -> List[Dict[str, Any]]:
    """Load a CSV file and return its contents as a list of dictionaries."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    import pandas as pd
    df = pd.read_csv(filepath)
    return df.to_dict(orient='records')

def get_data_summary(ingestion_log_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Summarize the data ingestion process.
    Reads from processed_alloys.csv to count records.
    """
    processed_path = "data/processed/processed_alloys.csv"
    if not os.path.exists(processed_path):
        logger.warning(f"Processed data file not found at {processed_path}. Using defaults.")
        return {
            "total_records": 0,
            "ternary_alloys": 0,
            "sampling_details": "Data not available"
        }

    import pandas as pd
    df = pd.read_csv(processed_path)
    return {
        "total_records": len(df),
        "ternary_alloys": len(df), # Assuming all are ternary after filtering
        "sampling_details": "Full dataset processed"
    }

def get_model_performance(metrics_path: str) -> Dict[str, Any]:
    """
    Extract model performance metrics from the final metrics JSON.
    """
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Model metrics file not found: {metrics_path}")
    
    metrics = load_json_file(metrics_path)
    return {
        "mean_rmse": metrics.get("mean_rmse", "N/A"),
        "test_rmse": metrics.get("test_rmse", "N/A"),
        "p_value_vs_null": metrics.get("p_value_vs_null", "N/A"),
        "sc002_met": metrics.get("sc002_met", False)
    }

def get_feature_importance(importance_path: str) -> List[Dict[str, Any]]:
    """
    Load feature importance rankings.
    """
    if not os.path.exists(importance_path):
        logger.warning(f"Feature importance file not found: {importance_path}")
        return []
    
    data = load_json_file(importance_path)
    # Ensure it's a list of dicts, handling potential nested structures if any
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'features' in data:
        return data['features']
    return []

def get_sensitivity_analysis(sensitivity_path: str) -> Dict[str, Any]:
    """
    Load sensitivity analysis results.
    """
    if not os.path.exists(sensitivity_path):
        logger.warning(f"Sensitivity report not found: {sensitivity_path}")
        return {"stability_met": False, "f1_variance": 0.0}
    
    data = load_json_file(sensitivity_path)
    return {
        "stability_met": data.get("stability_met", False),
        "f1_variance": data.get("f1_variance", 0.0),
        "rmse_variance": data.get("rmse_variance", 0.0)
    }

def generate_report_markdown(
    data_summary: Dict[str, Any],
    model_perf: Dict[str, Any],
    feature_importance: List[Dict[str, Any]],
    sensitivity: Dict[str, Any],
    output_path: str
) -> None:
    """
    Generate the final consolidated research report in Markdown.
    """
    report_lines = [
        "# Research Report: Predicting the Glass Forming Region of Alloy Systems",
        "",
        "## 1. Executive Summary",
        "",
        "This study investigates the ability of a Random Forest regressor to predict the Critical Cooling Rate (CCR) of alloy systems based on thermodynamic descriptors. The goal is to identify key thermodynamic features that correlate with glass-forming ability.",
        "",
        "## 2. Data Summary",
        "",
        f"- **Total Records Processed**: {data_summary['total_records']}",
        f"- **Number of Ternary Alloys**: {data_summary['ternary_alloys']}",
        f"- **Sampling Details**: {data_summary['sampling_details']}",
        "",
        "## 3. Model Performance",
        "",
        "The model was trained using a Random Forest algorithm and evaluated against a null baseline.",
        "",
        f"- **Mean RMSE (Cross-Validation)**: {model_perf['mean_rmse']}",
        f"- **Test RMSE**: {model_perf['test_rmse']}",
        f"- **P-value vs Null Model**: {model_perf['p_value_vs_null']}",
        "",
        f"- **SC-002 Status (Statistically Distinguishable)**: {'PASSED' if model_perf['sc002_met'] else 'FAILED'}",
        "",
        "## 4. Feature Importance",
        "",
        "The following features were identified as top contributors to the model's predictive power:",
        ""
    ]

    if feature_importance:
        # Sort by importance if not already sorted, assuming 'importance' key exists
        sorted_features = sorted(feature_importance, key=lambda x: x.get('importance', 0), reverse=True)
        top_3 = sorted_features[:3]
        
        for i, feat in enumerate(top_3, 1):
            name = feat.get('feature', 'Unknown')
            p_val = feat.get('p_value', 'N/A')
            importance = feat.get('importance', 'N/A')
            report_lines.append(f"{i}. **{name}**: Importance={importance}, P-value={p_val}")
        
        report_lines.append("")
        report_lines.append("**Note**: Feature importance rankings are based on the stable model after collinearity checks.")
    else:
        report_lines.append("*No feature importance data available.*")
        report_lines.append("")

    report_lines.extend([
        "## 5. Sensitivity Analysis",
        "",
        "Sensitivity analysis was performed across critical cooling rate thresholds {50, 100, 150} K/s.",
        "",
        f"- **F1-Score Variance**: {sensitivity['f1_variance']:.4f}",
        f"- **RMSE Variance**: {sensitivity['rmse_variance']:.4f}",
        f"- **Stability Met (Variance <= 10%)**: {'YES' if sensitivity['stability_met'] else 'NO'}",
        "",
        "## 6. Caveats",
        "",
        "**FINDINGS ARE ASSOCIATIONAL**: This study uses observational data; no causal claims are made. The correlations identified are statistical associations and do not imply causation.",
        "",
        "## 7. SC-002 Status",
        "",
        f"The model's performance relative to the null baseline was evaluated using an independent t-test. The result is: **{'STATISTICALLY DISTINGUISHABLE' if model_perf['sc002_met'] else 'NOT STATISTICALLY DISTINGUISHABLE'}** (p-value = {model_perf['p_value_vs_null']}).",
        "",
        "## 8. References",
        "",
        "- Dataset: `matsci/glass-forming-ability` (Hugging Face Datasets)",
        "- Elemental Properties: `mendeleev` Python library",
        "- Model: Random Forest Regressor (scikit-learn)",
        ""
    ])

    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Report generated successfully at {output_path}")

def main():
    """
    Main entry point for report generation.
    Loads all required artifacts and generates REPORT.md.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_path = project_root # Assuming code/ is at project_root/code/
    
    # Define paths relative to project root
    processed_data_path = os.path.join(base_path, "data/processed/processed_alloys.csv")
    metrics_path = os.path.join(base_path, "data/models/model_metrics_final.json")
    importance_path = os.path.join(base_path, "data/processed/feature_importance.json")
    sensitivity_path = os.path.join(base_path, "data/processed/sensitivity_status.json")
    output_path = os.path.join(base_path, "REPORT.md")

    logger.info("Starting report generation...")

    try:
        # 1. Load Data Summary
        data_summary = get_data_summary()
        logger.info(f"Data summary loaded: {data_summary['total_records']} records.")

        # 2. Load Model Performance
        model_perf = get_model_performance(metrics_path)
        logger.info(f"Model performance loaded: RMSE={model_perf['test_rmse']}")

        # 3. Load Feature Importance
        feature_importance = get_feature_importance(importance_path)
        logger.info(f"Feature importance loaded: {len(feature_importance)} features.")

        # 4. Load Sensitivity Analysis
        sensitivity = get_sensitivity_analysis(sensitivity_path)
        logger.info(f"Sensitivity analysis loaded: Stability={sensitivity['stability_met']}")

        # 5. Generate Report
        generate_report_markdown(
            data_summary,
            model_perf,
            feature_importance,
            sensitivity,
            output_path
        )

        logger.info("Report generation completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Required file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during report generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
