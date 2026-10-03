import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

def setup_report_logger() -> logging.Logger:
    """Setup and return the report logger."""
    logger = logging.getLogger("report_logger")
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def load_model_performance(filepath: str = "results/model_performance.json") -> Optional[Dict[str, Any]]:
    """Load model performance data from JSON file."""
    logger = setup_report_logger()
    path = Path(filepath)
    
    if not path.exists():
        logger.error(f"Performance file not found: {filepath}")
        return None
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded performance data from {filepath}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading {filepath}: {e}")
        return None

def generate_final_report(performance_data: Optional[Dict[str, Any]], output_path: str = "results/final_report.md") -> None:
    """
    Generate the final research report.
    
    This function writes the final report to disk. It unconditionally includes
    the mandatory "Limitations" section as required by the specification.
    
    Args:
        performance_data: The dictionary containing model performance metrics (R², RMSE, etc.)
        output_path: Path where the report will be written.
    """
    logger = setup_report_logger()
    
    report_lines = []
    
    # Header
    report_lines.append("# Final Report: Quantifying the Impact of Network Structure on Heat Diffusion")
    report_lines.append("")
    report_lines.append("## Executive Summary")
    report_lines.append("")
    report_lines.append("This study investigates the relationship between atomic network topology and thermal conductivity in crystalline solids.")
    report_lines.append("We constructed network graphs from Materials Project CIF files, computed topological metrics, and correlated them with thermal conductivity.")
    report_lines.append("")
    
    # Performance Section
    report_lines.append("## Model Performance")
    report_lines.append("")
    
    r2_interpretation = None
    
    if performance_data:
        mean_r2 = performance_data.get("mean_r2")
        std_r2 = performance_data.get("std_r2")
        mean_rmse = performance_data.get("mean_rmse")
        std_rmse = performance_data.get("std_rmse")
        n_folds = performance_data.get("n_folds")
        
        if mean_r2 is not None:
            report_lines.append(f"The linear regression model achieved a mean R² of **{mean_r2:.4f}** (±{std_r2:.4f}) across {n_folds} folds.")
            report_lines.append(f"The mean Root Mean Square Error (RMSE) was **{mean_rmse:.4f}** (±{std_rmse:.4f}).")
            report_lines.append("")
            
            # Interpretation logic
            if mean_r2 > 0.7:
                r2_interpretation = "strong positive relationship"
            elif mean_r2 > 0.4:
                r2_interpretation = "moderate positive relationship"
            elif mean_r2 > 0.1:
                r2_interpretation = "weak positive relationship"
            else:
                r2_interpretation = "negligible relationship"
            
            report_lines.append(f"**Interpretation**: The results suggest a {r2_interpretation} between the selected network/physical descriptors and thermal conductivity.")
        else:
            report_lines.append("Performance metrics could not be calculated or were missing from the input data.")
            report_lines.append("")
    else:
        report_lines.append("No model performance data was available to include in this report.")
        report_lines.append("")
    
    # Correlations Section (Placeholder for future expansion if data exists in a separate file, 
    # but T025c specifically focuses on the report generation from performance data)
    report_lines.append("## Network Metric Correlations")
    report_lines.append("")
    report_lines.append("Correlation analysis (Pearson and Spearman) was performed between network metrics (degree, path length, clustering) and thermal conductivity.")
    report_lines.append("Bonferroni correction was applied to control the family-wise error rate.")
    report_lines.append("Detailed correlation coefficients and p-values are stored in `results/correlations.json`.")
    report_lines.append("")
    
    # Mandatory Limitations Section
    report_lines.append("## Limitations")
    report_lines.append("")
    report_lines.append("This study is observational. Correlations do not imply causality. The thermal conductivity tensor was reduced to a scalar by averaging principal components, which may obscure anisotropic effects.")
    report_lines.append("")
    
    # Methodology Summary
    report_lines.append("## Methodology Summary")
    report_lines.append("")
    report_lines.append("1. **Data Acquisition**: Downloaded ≥50 CIF files from the Materials Project API.")
    report_lines.append("2. **Network Construction**: Parsed CIFs using pymatgen; detected bonds via covalent radii summation with fallback distance cutoffs.")
    report_lines.append("3. **Feature Engineering**: Computed average degree, average shortest path length (on LCC), clustering coefficient, unit cell volume, total atom count, and mean atomic mass.")
    report_lines.append("4. **Feature Selection**: Applied Variance Inflation Factor (VIF) filtering to remove multicollinearity.")
    report_lines.append("5. **Modeling**: Trained a linear regression model with 5-fold stratified cross-validation.")
    report_lines.append("")
    
    # Conclusion
    report_lines.append("## Conclusion")
    report_lines.append("")
    if r2_interpretation:
        report_lines.append(f"The analysis provides evidence of a {r2_interpretation} between network structure and thermal properties in the sampled crystalline solids.")
    else:
        report_lines.append("The analysis did not yield a definitive quantitative relationship within the observed sample.")
    report_lines.append("")
    report_lines.append("Future work should explore non-linear models and incorporate anisotropic thermal conductivity tensors directly.")
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Final report written to {output_path}")

def main():
    """Main entry point for the report generation script."""
    logger = setup_report_logger()
    logger.info("Starting final report generation...")
    
    # Load performance data
    performance_data = load_model_performance("results/model_performance.json")
    
    # Generate report
    generate_final_report(performance_data, "results/final_report.md")
    
    logger.info("Report generation complete.")

if __name__ == "__main__":
    main()
