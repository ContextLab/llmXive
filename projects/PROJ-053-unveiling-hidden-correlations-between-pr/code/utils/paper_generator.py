import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import (
    get_project_root,
    get_results_dir,
    get_figures_dir,
    get_processed_data_dir,
    get_raw_data_dir,
    get_logs_dir,
    get_docs_dir,
    ensure_directories
)
from utils.logger import setup_logging

def setup_paper_logger():
    """Setup logger for paper generation."""
    return setup_logging(
        name="paper_generator",
        log_dir=get_logs_dir(),
        filename="paper_generation.log"
    )

def load_metrics() -> Dict[str, Any]:
    """Load metrics from results/metrics.json."""
    metrics_path = os.path.join(get_results_dir(), "metrics.json")
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def load_normalization_bounds() -> Dict[str, Any]:
    """Load normalization bounds from data/processed/normalization_bounds.json."""
    bounds_path = os.path.join(get_processed_data_dir(), "normalization_bounds.json")
    if not os.path.exists(bounds_path):
        raise FileNotFoundError(f"Normalization bounds not found: {bounds_path}")
    
    with open(bounds_path, 'r') as f:
        return json.load(f)

def check_scope_reduction() -> Optional[str]:
    """Check preprocessing log for scope reduction entries."""
    log_path = os.path.join(get_processed_data_dir(), "preprocessing.log")
    if not os.path.exists(log_path):
        return None
    
    with open(log_path, 'r') as f:
        content = f.read()
    
    # Look for the specific scope reduction log entry from T016
    if "Reduced scope: fatigue_life missing" in content:
        return "fatigue_life was not present in the raw dataset; analysis restricted to yield_strength and ductility."
    
    return None

def get_data_provenance() -> str:
    """Construct data provenance statement."""
    raw_path = os.path.join(get_raw_data_dir(), "am_data.csv")
    processed_path = os.path.join(get_processed_data_dir(), "processed_data.csv")
    
    provenance = []
    provenance.append("### Data Provenance")
    provenance.append("")
    provenance.append("This analysis utilizes a manually provided dataset of additive manufacturing process parameters and mechanical properties.")
    provenance.append("")
    
    if os.path.exists(raw_path):
        raw_size = os.path.getsize(raw_path)
        provenance.append(f"- **Raw Data Source**: `{raw_path}` ({raw_size:,} bytes)")
    else:
        provenance.append(f"- **Raw Data Source**: `{raw_path}` (NOT FOUND)")
    
    if os.path.exists(processed_path):
        processed_size = os.path.getsize(processed_path)
        provenance.append(f"- **Processed Data**: `{processed_path}` ({processed_size:,} bytes)")
    else:
        provenance.append(f"- **Processed Data**: `{processed_path}` (NOT FOUND)")
    
    provenance.append("")
    provenance.append("The dataset contains the following columns:")
    provenance.append("- **Process Parameters**: laser_power, scan_speed, layer_thickness")
    provenance.append("- **Mechanical Properties**: yield_strength, ductility")
    provenance.append("- **Optional**: fatigue_life (if present in source)")
    provenance.append("")
    provenance.append("All data was manually placed in the `data/raw/` directory as per project constraints prohibiting automated downloads.")
    
    return "\n".join(provenance)

def generate_paper_content(metrics: Dict[str, Any], bounds: Dict[str, Any], scope_note: Optional[str]) -> str:
    """Generate the full paper.md content."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    paper = []
    
    # Title and Header
    paper.append("# Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys")
    paper.append("")
    paper.append(f"**Draft Version** | Generated: {timestamp}")
    paper.append("")
    paper.append("---")
    paper.append("")
    
    # Abstract
    paper.append("## Abstract")
    paper.append("")
    paper.append("This study investigates the correlations between additive manufacturing process parameters (laser power, scan speed, layer thickness) and resulting mechanical properties (yield strength, ductility) in metal alloys. Using Gaussian Process Regression (GPR) models, we quantify predictive performance and uncertainty across the parameter space. We also perform a comparative analysis against a linear regression baseline and assess feature importance through permutation analysis. The findings aim to identify optimal processing regimes and regions requiring further experimental validation.")
    paper.append("")
    
    # Introduction
    paper.append("## 1. Introduction")
    paper.append("")
    paper.append("Additive manufacturing (AM) offers unprecedented flexibility in designing and fabricating complex metal components. However, the relationship between processing parameters and final mechanical properties remains complex and often non-linear. This work leverages machine learning, specifically Gaussian Process Regression, to model these relationships and provide uncertainty estimates that can guide experimental design.")
    paper.append("")
    
    # Scope Note
    if scope_note:
        paper.append("### Scope Limitation")
        paper.append("")
        paper.append(f"**Note**: {scope_note}")
        paper.append("")
    
    # Methodology
    paper.append("## 2. Methodology")
    paper.append("")
    paper.append("### 2.1 Data Preprocessing")
    paper.append("")
    paper.append("- **Missing Value Imputation**: Median imputation applied to numeric features.")
    paper.append("- **Categorical Encoding**: One-hot encoding for alloy type.")
    paper.append("- **Normalization**: Min-Max scaling fit on training set only.")
    paper.append("- **Derived Feature Filtering**: Columns corresponding to derived energy metrics (e.g., energy_density, line_energy) were excluded to maintain source independence.")
    paper.append("- **Zero-Variance Detection**: Columns with zero variance were dropped to prevent singularity.")
    paper.append("")
    
    paper.append("### 2.2 Model Training")
    paper.append("")
    paper.append("- **Primary Model**: Gaussian Process Regression with Radial Basis Function (RBF) kernel.")
    paper.append("- **Hyperparameter Optimization**: K-fold cross-validation maximizing log marginal likelihood.")
    paper.append("- **Baseline Model**: Linear Regression for comparative analysis (Simple Case 001).")
    paper.append("")
    
    paper.append("### 2.3 Evaluation Metrics")
    paper.append("")
    paper.append("- **R² (Coefficient of Determination)**")
    paper.append("- **RMSE (Root Mean Square Error)**")
    paper.append("- **MAE (Mean Absolute Error)**")
    paper.append("- **RMSE as Percentage of Range**: Normalized error metric.")
    paper.append("")
    
    paper.append("### 2.4 Uncertainty Quantification")
    paper.append("")
    paper.append("- **Permutation Importance**: Used to rank feature influence.")
    paper.append("- **Uncertainty Heatmaps**: Regions with standard deviation > 2× median highlighted.")
    paper.append("")
    
    # Results
    paper.append("## 3. Results")
    paper.append("")
    
    # Model Performance
    paper.append("### 3.1 Model Performance Metrics")
    paper.append("")
    
    gpr_metrics = metrics.get("gpr_metrics", {})
    baseline_metrics = metrics.get("baseline_metrics", {})
    comparison = metrics.get("gpr_vs_baseline_delta", {})
    
    paper.append("| Metric | GPR Model | Baseline (Linear) | Delta (GPR - Baseline) |")
    paper.append("|--------|-----------|-------------------|------------------------|")
    paper.append(f"| R² | {gpr_metrics.get('r2', 'N/A'):.4f} | {baseline_metrics.get('r2', 'N/A'):.4f} | {comparison.get('delta_r2', 'N/A'):.4f} |")
    paper.append(f"| RMSE | {gpr_metrics.get('rmse', 'N/A'):.4f} | {baseline_metrics.get('rmse', 'N/A'):.4f} | {comparison.get('delta_rmse', 'N/A'):.4f} |")
    paper.append(f"| MAE | {gpr_metrics.get('mae', 'N/A'):.4f} | {baseline_metrics.get('mae', 'N/A'):.4f} | {comparison.get('delta_mae', 'N/A'):.4f} |")
    paper.append(f"| RMSE % Range | {gpr_metrics.get('rmse_percentage_of_range', 'N/A'):.2f}% | {baseline_metrics.get('rmse_percentage_of_range', 'N/A'):.2f}% | - |")
    paper.append("")
    
    # Feasibility Status
    if "feasibility_status" in metrics:
        status = metrics["feasibility_status"]
        runtime = metrics.get("runtime_seconds", "N/A")
        paper.append(f"**Feasibility Check**: {status} (Runtime: {runtime} seconds)")
        paper.append("")
    
    # High Uncertainty Analysis
    if "high_uncertainty_percentage" in metrics:
        paper.append("### 3.2 Uncertainty Analysis")
        paper.append("")
        paper.append(f"- **High Uncertainty Sample Percentage**: {metrics['high_uncertainty_percentage']:.2f}%")
        paper.append("- **Definition**: Samples where predicted standard deviation (σ) > 2× median σ.")
        paper.append("")
    
    # Visualizations
    paper.append("### 3.3 Visualizations")
    paper.append("")
    paper.append("The following figures were generated as part of this analysis:")
    paper.append("")
    paper.append("1. **Contour Plots**: Yield Strength vs. Laser Power and Scan Speed (with physical unit annotations).")
    paper.append("2. **Uncertainty Heatmaps**: Regions of high prediction uncertainty (σ > 2× median) highlighted in red.")
    paper.append("3. **Partial Dependence Plots (PDPs)**: Top 3 influential parameters.")
    paper.append("")
    
    figures_dir = get_figures_dir()
    figures_found = []
    if os.path.exists(figures_dir):
        for f in os.listdir(figures_dir):
            if f.endswith('.png'):
                figures_found.append(f)
    
    if figures_found:
        paper.append("**Generated Figures:**")
        paper.append("")
        for fig in sorted(figures_found):
            paper.append(f"- `figures/{fig}`")
        paper.append("")
    
    # Discussion
    paper.append("## 4. Discussion")
    paper.append("")
    paper.append("The GPR model demonstrates [INSERT INTERPRETATION BASED ON R²] predictive capability compared to the linear baseline. The uncertainty quantification reveals specific regions in the parameter space where model confidence is low, suggesting these regimes may require additional experimental data.")
    paper.append("")
    paper.append("The exclusion of derived energy metrics (e.g., energy_density) ensures that the model learns directly from the fundamental process parameters, maintaining source independence as required by the study design.")
    paper.append("")
    
    # Data Provenance
    paper.append(get_data_provenance())
    paper.append("")
    
    # Conclusion
    paper.append("## 5. Conclusion")
    paper.append("")
    paper.append("This study successfully implemented a Gaussian Process Regression pipeline to model the relationship between additive manufacturing parameters and mechanical properties. The integration of uncertainty quantification provides actionable insights for experimental design. Future work will focus on expanding the dataset to include fatigue life data and exploring multi-fidelity modeling approaches.")
    paper.append("")
    
    # References
    paper.append("## References")
    paper.append("")
    paper.append("- Rasmussen, C. E., & Williams, C. K. I. (2006). Gaussian Processes for Machine Learning. MIT Press.")
    paper.append("- Pedregosa, F., et al. (2011). Scikit-learn: Machine Learning in Python. JMLR.")
    paper.append("")
    
    return "\n".join(paper)

def save_paper(content: str):
    """Save the generated paper to docs/paper.md."""
    docs_dir = get_docs_dir()
    ensure_directories(docs_dir)
    
    output_path = os.path.join(docs_dir, "paper.md")
    with open(output_path, 'w') as f:
        f.write(content)
    
    return output_path

def main():
    """Main entry point for paper generation."""
    logger = setup_paper_logger()
    logger.info("Starting paper generation (T044)...")
    
    try:
        # Load required artifacts
        logger.info("Loading metrics...")
        metrics = load_metrics()
        
        logger.info("Loading normalization bounds...")
        bounds = load_normalization_bounds()
        
        logger.info("Checking scope reduction...")
        scope_note = check_scope_reduction()
        if scope_note:
            logger.info(f"Scope reduction detected: {scope_note}")
        else:
            logger.info("No scope reduction detected.")
        
        # Generate paper content
        logger.info("Generating paper content...")
        content = generate_paper_content(metrics, bounds, scope_note)
        
        # Save paper
        logger.info("Saving paper to docs/paper.md...")
        output_path = save_paper(content)
        
        logger.info(f"Paper successfully generated at: {output_path}")
        print(f"Paper generated: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required artifact: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating paper: {e}")
        raise

if __name__ == "__main__":
    main()
