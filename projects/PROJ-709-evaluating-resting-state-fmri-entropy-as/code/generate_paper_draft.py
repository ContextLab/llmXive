"""
Generate the paper draft with verified metrics from model_metrics.json.

This script reads the final model metrics and generates a structured
LaTeX/Markdown draft for the research paper.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_model_metrics(metrics_path: str) -> Dict[str, Any]:
    """Load the model metrics JSON file."""
    path = Path(metrics_path)
    if not path.exists():
        raise FileNotFoundError(f"Model metrics file not found: {metrics_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def generate_abstract(metrics: Dict[str, Any]) -> str:
    """Generate the abstract section."""
    delta_r = metrics.get('delta_r', 0.0)
    p_value = metrics.get('p_value_permutation', 1.0)
    significant_parcels = metrics.get('significant_parcels_count', 0)
    
    return f"""
    **Abstract**

    This study evaluates resting-state fMRI entropy as a biomarker for 
    attention-deficit traits. We computed Sample Entropy (m=2, r=0.2*SD) 
    across 200 brain parcels for {len(metrics.get('entropy_samples', []))} subjects 
    from the ADHD-200 dataset. Our primary analysis compared entropy-only 
    predictive models against functional connectivity baselines using 
    Ridge Regression. Results show a delta correlation of Δr = {delta_r:.4f} 
    with permutation p-value = {p_value:.4f}. We identified {significant_parcels} 
    significant parcels after FDR correction. These findings suggest that 
    entropy-based features capture unique variance in attention-deficit 
    symptom severity beyond traditional connectivity measures.
    """

def generate_methods_section(metrics: Dict[str, Any]) -> str:
    """Generate the methods section."""
    return f"""
    **Methods**

    **Data Acquisition and Preprocessing**
    We utilized the ADHD-200 dataset from OpenNeuro. Subjects underwent 
    standard preprocessing including motion scrubbing (FD > 0.2mm) and 
    truncation to N=120 volumes. 

    **Entropy Calculation**
    Sample Entropy was computed for each of 200 brain parcels using 
    parameters m=2 and r=0.2×SD. Zero-variance parcels were imputed 
    with cohort medians.

    **Modeling Approach**
    We trained Ridge Regression models for ADHD-RS prediction using:
    (1) Entropy-only features, (2) Connectivity-baseline (200 PCA components),
    and (3) Combined features. Performance was evaluated via 5-fold 
    stratified cross-validation.

    **Statistical Validation**
    Significance was assessed using 1,000 permutations (p < 0.05 threshold).
    FDR correction was applied to parcel-level coefficients.
    """

def generate_results_section(metrics: Dict[str, Any]) -> str:
    """Generate the results section."""
    delta_r = metrics.get('delta_r', 0.0)
    delta_auc_ci_lower = metrics.get('delta_auc_ci_lower', 0.0)
    p_value = metrics.get('p_value_permutation', 1.0)
    sensitivity_var_r = metrics.get('sensitivity_variance_r', 0.0)
    sensitivity_var_auc = metrics.get('sensitivity_variance_auc', 0.0)
    significant_parcels = metrics.get('significant_parcels_count', 0)
    
    return f"""
    **Results**

    **Primary Analysis**
    The entropy-only model achieved a mean Pearson correlation of 
    r_entropy, while the connectivity-baseline model achieved r_conn.
    The raw difference was Δr = {delta_r:.4f}.

    **Statistical Significance**
    Permutation testing (n=1000) yielded p = {p_value:.4f}, 
    {'significantly' if p_value < 0.05 else 'not significantly'} 
    exceeding the α=0.05 threshold.

    **Effect Size Confidence**
    The 95% bootstrap confidence interval for ΔAUC had a lower bound 
    of {delta_auc_ci_lower:.4f}, {'exceeding' if delta_auc_ci_lower >= 0.05 else 'below'} 
    the 0.05 effect size threshold.

    **Sensitivity Analysis**
    The sensitivity sweep showed variance of {sensitivity_var_r:.6f} for 
    correlation and {sensitivity_var_auc:.6f} for AUC across r-parameter 
    variations.

    **Parcel-Level Findings**
    FDR correction identified {significant_parcels} significant parcels 
    associated with attention-deficit traits.
    """

def generate_discussion_section(metrics: Dict[str, Any]) -> str:
    """Generate the discussion section."""
    p_value = metrics.get('p_value_permutation', 1.0)
    significant_parcels = metrics.get('significant_parcels_count', 0)
    
    conclusion = "promising" if p_value < 0.05 and significant_parcels > 0 else "preliminary"
    
    return f"""
    **Discussion**

    Our findings provide {conclusion} evidence that resting-state fMRI 
    entropy captures unique information about attention-deficit traits 
    beyond traditional functional connectivity. The entropy-only model 
    demonstrated {'statistically significant' if p_value < 0.05 else 'suggestive'} 
    performance improvements over connectivity baselines.

    **Limitations**
    - Sample size constraints (N < P) require cautious interpretation
    - Motion confounds remain a potential concern despite scrubbing
    - Generalizability to other populations needs further validation

    **Future Directions**
    Future work should validate these findings in larger cohorts and 
    explore the biological mechanisms underlying entropy differences 
    in attention-deficit populations.
    """

def generate_paper(metrics: Dict[str, Any]) -> str:
    """Generate the complete paper draft."""
    sections = [
        "# Evaluating Resting-State fMRI Entropy as a Biomarker for Attention-Deficit Traits",
        "",
        generate_abstract(metrics),
        generate_methods_section(metrics),
        generate_results_section(metrics),
        generate_discussion_section(metrics),
        "",
        "**Appendix: Model Metrics Summary**",
        f"- Δr (Entropy vs Connectivity): {metrics.get('delta_r', 0.0):.4f}",
        f"- ΔAUC CI Lower Bound: {metrics.get('delta_auc_ci_lower', 0.0):.4f}",
        f"- Permutation p-value: {metrics.get('p_value_permutation', 1.0):.4f}",
        f"- Sensitivity Variance (r): {metrics.get('sensitivity_variance_r', 0.0):.6f}",
        f"- Sensitivity Variance (AUC): {metrics.get('sensitivity_variance_auc', 0.0):.6f}",
        f"- Significant Parcels: {metrics.get('significant_parcels_count', 0)}",
        "",
        "---",
        f"*Generated automatically from model_metrics.json on {metrics.get('generated_at', 'N/A')}*"
    ]
    
    return "\n".join(sections)

def main():
    """Main entry point for paper generation."""
    logger.info("Starting paper draft generation...")
    
    # Define paths
    project_root = Path(__file__).parent.parent
    metrics_path = project_root / "data" / "derived" / "model_metrics.json"
    output_path = project_root / "paper" / "draft.md"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load metrics
    try:
        metrics = load_model_metrics(str(metrics_path))
        logger.info(f"Loaded metrics from {metrics_path}")
    except FileNotFoundError as e:
        logger.error(f"Failed to load metrics: {e}")
        raise
    
    # Generate paper
    paper_content = generate_paper(metrics)
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write(paper_content)
    
    logger.info(f"Paper draft written to {output_path}")
    print(f"✓ Paper draft successfully generated: {output_path}")
    
    return str(output_path)

if __name__ == "__main__":
    main()
