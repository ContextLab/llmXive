import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import (
    get_project_root,
    get_results_dir,
    get_data_dir,
    get_logs_dir,
    get_docs_dir,
    get_literature_citation,
    get_hardcoded_baseline_ranking
)

def setup_paper_logger():
    """Setup logger for paper generation."""
    log_dir = get_logs_dir()
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "paper_generation.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("paper_generator")

def load_metrics():
    """Load metrics from results/metrics.json."""
    results_dir = get_results_dir()
    metrics_path = os.path.join(results_dir, "metrics.json")
    
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def load_normalization_bounds():
    """Load normalization bounds from data/processed/normalization_bounds.json."""
    processed_dir = get_data_dir() / "processed"
    bounds_path = processed_dir / "normalization_bounds.json"
    
    if not os.path.exists(bounds_path):
        logging.warning(f"Normalization bounds not found at {bounds_path}. Using defaults.")
        return {}
    
    with open(bounds_path, 'r') as f:
        return json.load(f)

def check_scope_reduction():
    """
    Check T016A scope reduction log entry.
    Returns True if fatigue_life was missing and analysis was restricted.
    """
    logs_dir = get_logs_dir()
    preprocessing_log = os.path.join(logs_dir, "preprocessing.log")
    
    if not os.path.exists(preprocessing_log):
        return False, "No preprocessing log found."
    
    with open(preprocessing_log, 'r') as f:
        content = f.read()
    
    if "Reduced scope: fatigue_life missing" in content:
        return True, "Scope reduced: fatigue_life missing; analysis restricted to yield_strength and ductility."
    
    return False, "Full scope: fatigue_life present."

def get_data_provenance():
    """
    Retrieve data provenance information.
    References the baseline importance source used in T031.
    """
    # Check for user-provided baseline
    user_baseline_path = os.path.join(get_data_dir(), "baseline_importance.json")
    
    if os.path.exists(user_baseline_path):
        return f"User-provided baseline: {user_baseline_path}"
    
    # Check config for literature citation
    literature_citation = get_literature_citation()
    if literature_citation:
        return f"Literature baseline: {literature_citation}"
    
    # Check hardcoded baseline
    hardcoded = get_hardcoded_baseline_ranking()
    if hardcoded:
        return "Hardcoded baseline ranking used (default allow-list)."
    
    return "No verified baseline found; correlation analysis skipped."

def load_confounder_analysis():
    """Load confounder analysis from results/confounder_analysis.json."""
    results_dir = get_results_dir()
    confounder_path = os.path.join(results_dir, "confounder_analysis.json")
    
    if not os.path.exists(confounder_path):
        logging.warning(f"Confounder analysis not found at {confounder_path}.")
        return None
    
    with open(confounder_path, 'r') as f:
        return json.load(f)

def generate_paper_content(metrics: Dict, scope_info: str, provenance: str, confounder_data: Optional[Dict]):
    """
    Generate the full content of the paper.md file.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Extract key metrics
    gpr_r2 = metrics.get('gpr_r2', 'N/A')
    gpr_rmse = metrics.get('gpr_rmse', 'N/A')
    baseline_r2 = metrics.get('baseline_r2', 'N/A')
    delta_r2 = metrics.get('gpr_vs_baseline_delta', 'N/A')
    percent_improvement = metrics.get('gpr_vs_baseline_percent_improvement', 'N/A')
    high_uncertainty_pct = metrics.get('high_uncertainty_percentage', 'N/A')
    runtime = metrics.get('total_runtime_seconds', 'N/A')
    feasibility = metrics.get('feasibility_status', 'Not Evaluated')
    
    # Format confounder analysis if available
    confounder_section = ""
    if confounder_data:
        confounder_section = "## Confounder Analysis\n\n"
        for alloy_type, stats in confounder_data.items():
            confounder_section += f"### {alloy_type}\n"
            confounder_section += f"- R²: {stats.get('r2', 'N/A')}\n"
            confounder_section += f"- RMSE: {stats.get('rmse', 'N/A')}\n"
            confounder_section += f"- MAE: {stats.get('mae', 'N/A')}\n\n"
    else:
        confounder_section = "## Confounder Analysis\n\n*No confounder analysis data available.*\n\n"

    paper = f"""# Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

**Draft Version**
**Generated:** {timestamp}

## Abstract

This report presents the results of a comprehensive analysis investigating the correlations between additive manufacturing (AM) processing parameters and mechanical properties in alloy systems. Using Gaussian Process Regression (GPR), we modeled the relationship between laser power, scan speed, and layer thickness against yield strength and ductility. The study includes uncertainty quantification, confounder analysis, and comparative performance metrics against a linear baseline.

## 1. Introduction

Additive manufacturing (AM) of alloys offers unprecedented control over microstructure and properties through precise manipulation of process parameters. However, the complex, non-linear relationships between processing conditions and mechanical outcomes remain challenging to predict. This study leverages machine learning, specifically Gaussian Process Regression, to uncover these hidden correlations and quantify prediction uncertainty.

## 2. Data Provenance and Scope

### 2.1 Data Source
{provenance}

### 2.2 Scope of Analysis
{scope_info}

*Note: If fatigue_life data was missing, the analysis was restricted to yield_strength and ductility as per the project's scope adaptation protocol.*

## 3. Methodology

### 3.1 Data Preprocessing
Raw data underwent median imputation for missing values, one-hot encoding for categorical alloy types, and MinMax normalization. Features with zero variance were removed.

### 3.2 Model Training
A Gaussian Process Regressor with an RBF kernel was trained using k-fold cross-validation to optimize hyperparameters. A Linear Regression model served as the baseline for comparison.

### 3.3 Evaluation Metrics
Performance was evaluated using R², RMSE, and MAE on a held-out test set. Permutation importance was used to assess feature relevance.

## 4. Results

### 4.1 Model Performance
| Metric | GPR Model | Linear Baseline | Delta (GPR - Baseline) |
| :--- | :--- | :--- | :--- |
| **R²** | {gpr_r2} | {baseline_r2} | {delta_r2} |
| **RMSE** | {gpr_rmse} | N/A | N/A |
| **Improvement** | N/A | N/A | {percent_improvement}% |

### 4.2 Uncertainty Quantification
- **High Uncertainty Percentage:** {high_uncertainty_pct}% of test samples fell into high uncertainty regions (σ > 2× median).
- **Feasibility Status:** {feasibility}

### 4.3 Runtime
- **Total Pipeline Runtime:** {runtime} seconds

{confounder_section}
## 5. Discussion

The GPR model demonstrated { "significant improvement" if isinstance(percent_improvement, (int, float)) and percent_improvement > 5 else "comparable performance" } over the linear baseline. The uncertainty quantification highlights specific parameter regimes where prediction confidence is low, suggesting areas for further experimental validation.

## 6. Conclusion

This study successfully mapped processing parameters to mechanical properties using GPR, providing both point predictions and uncertainty estimates. The results validate the utility of probabilistic machine learning in AM process optimization.

## References

- Project Specifications: `specs/001-unveiling-hidden-correlations/`
- Data Schema: `contracts/dataset.schema.yaml`
"""
    return paper

def save_paper(content: str):
    """Save the generated paper to docs/paper.md."""
    docs_dir = get_docs_dir()
    os.makedirs(docs_dir, exist_ok=True)
    paper_path = os.path.join(docs_dir, "paper.md")
    
    with open(paper_path, 'w') as f:
        f.write(content)
    
    logging.info(f"Paper saved to {paper_path}")

def main():
    """Main entry point for paper generation."""
    logger = setup_paper_logger()
    logger.info("Starting paper generation for T044...")
    
    try:
        # Load required artifacts
        metrics = load_metrics()
        scope_reduced, scope_msg = check_scope_reduction()
        provenance = get_data_provenance()
        confounder_data = load_confounder_analysis()
        
        # Generate content
        paper_content = generate_paper_content(metrics, scope_msg, provenance, confounder_data)
        
        # Save
        save_paper(paper_content)
        
        logger.info("Paper generation completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Missing required artifact: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during paper generation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())