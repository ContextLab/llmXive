"""
T031: Implement interpretation logic for User Story 3.

Reads model metrics from data/results/model_metrics.json.
Analyzes coefficients and p-values to determine direction/magnitude.
Frames null results as evidence for other factors.
Outputs a summary interpretation to data/results/interpretation.md.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Import logging utility from existing API
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_model_metrics(metrics_path: Path) -> Dict[str, Any]:
    """Load the model metrics JSON produced by T026."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Model metrics file not found at {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def analyze_ols_results(ols_results: Dict[str, Any]) -> List[str]:
    """
    Analyze OLS regression results to generate interpretation points.
    
    Args:
        ols_results: Dictionary containing 'coefficients', 'p_values', and 'feature_names'.
        
    Returns:
        List of interpretation strings describing direction and significance.
    """
    interpretations = []
    coefficients = ols_results.get('coefficients', {})
    p_values = ols_results.get('p_values', {})
    feature_names = ols_results.get('feature_names', list(coefficients.keys()))
    
    # Sort features by absolute coefficient magnitude for importance ordering
    sorted_features = sorted(
        coefficients.keys(),
        key=lambda x: abs(coefficients.get(x, 0)),
        reverse=True
    )
    
    significant_count = 0
    null_count = 0
    
    for feature in sorted_features:
        coef = coefficients.get(feature, 0)
        p_val = p_values.get(feature, 1.0)
        
        # Determine direction
        direction = "positive" if coef > 0 else "negative"
        magnitude = abs(coef)
        
        # Determine significance (using standard 0.05 threshold, assuming Bonferroni already applied)
        is_significant = p_val < 0.05
        
        if is_significant:
            significant_count += 1
            interpretations.append(
                f"- **{feature}**: Shows a statistically significant {direction} association "
                f"with perceived agency (β={coef:.4f}, p={p_val:.4f}). "
                f"Higher values of {feature} are associated with "
                f"{'higher' if direction == 'positive' else 'lower'} perceived agency."
            )
        else:
            null_count += 1
            interpretations.append(
                f"- **{feature}**: Did not show a statistically significant association "
                f"with perceived agency (β={coef:.4f}, p={p_val:.4f}). "
                f"This null result suggests that {feature} alone may not be a primary driver "
                f"of perceived agency in this synthetic dataset, or that the effect size is too small "
                f"to detect given the sample size."
            )
    
    if significant_count == 0:
        interpretations.append(
            "\n**Note**: No motion features showed a statistically significant association with perceived agency. "
            "This null finding suggests that other factors (e.g., contextual cues, avatar appearance, or interaction history) "
            "may play a more dominant role in determining perceived agency than the specific motion features measured here."
        )
    
    return interpretations

def analyze_rf_results(
    rf_importance: Dict[str, float], 
    rf_metrics: Dict[str, float]
) -> List[str]:
    """
    Analyze Random Forest results to generate interpretation points.
    
    Args:
        rf_importance: Dictionary of feature importance scores.
        rf_metrics: Dictionary of model performance metrics (R2, RMSE).
        
    Returns:
        List of interpretation strings describing feature importance and model fit.
    """
    interpretations = []
    
    # Sort features by importance
    sorted_features = sorted(
        rf_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    r2 = rf_metrics.get('r2', 0)
    rmse = rf_metrics.get('rmse', 0)
    
    interpretations.append(
        f"The Random Forest model explained approximately {r2*100:.1f}% of the variance in perceived agency "
        f"(R²={r2:.4f}, RMSE={rmse:.4f})."
    )
    
    if sorted_features:
        top_feature, top_importance = sorted_features[0]
        interpretations.append(
            f"Feature importance analysis identified **{top_feature}** as the most influential predictor "
            f"(importance={top_importance:.4f}), followed by {[f[0] for f in sorted_features[1:3]]}."
        )
        
        # Compare with OLS if possible (though we don't have direct access here, we can note consistency)
        interpretations.append(
            "Non-linear interactions captured by the Random Forest model may reveal relationships not detected "
            "by the linear OLS model, particularly for complex motion dynamics."
        )
    
    return interpretations

def generate_interpretation(metrics_data: Dict[str, Any]) -> str:
    """
    Generate the full interpretation text based on model metrics.
    
    Args:
        metrics_data: The full content of model_metrics.json.
        
    Returns:
        Markdown formatted interpretation string.
    """
    lines = [
        "# Interpretation of Results: Visual Motion and Perceived Agency",
        "",
        "## Overview",
        "This analysis examines the relationship between visual motion features (latency, smoothness, lead_time) "
        "and perceived agency in virtual interactions using synthetic data. All reported associations are "
        "strictly correlational and derived from a stress-test dataset.",
        "",
        "## Multiple Linear Regression (OLS) Findings",
        "",
        "The OLS model assessed the linear relationship between motion features and agency scores.",
        ""
    ]
    
    ols_results = metrics_data.get('ols_results', {})
    if ols_results:
        lines.extend(analyze_ols_results(ols_results))
    else:
        lines.append("- OLS results were not available.")
    
    lines.extend([
        "",
        "## Random Forest Model Findings",
        "",
        "The Random Forest model captured potential non-linear relationships and feature interactions.",
        ""
    ])
    
    rf_results = metrics_data.get('rf_results', {})
    if rf_results:
        importance = rf_results.get('feature_importance', {})
        metrics = rf_results.get('metrics', {})
        lines.extend(analyze_rf_results(importance, metrics))
    else:
        lines.append("- Random Forest results were not available.")
    
    lines.extend([
        "",
        "## Limitations and Context",
        "",
        "- **Synthetic Data**: These results are derived from synthetic data generated for pipeline stress-testing. "
        "They do not represent human perception validation.",
        "- **Correlational Nature**: Associations identified do not imply causation.",
        "- **Sample Size**: Results are constrained by the sample size of the generated dataset.",
        "- **Null Results**: Null findings should be interpreted as evidence for the need to explore other factors "
        "(e.g., contextual, visual, or auditory cues) rather than definitive proof of no effect."
    ])
    
    return "\n".join(lines)

def main():
    """Main entry point for T031."""
    logger.info("Starting T031: Interpretation Logic")
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    metrics_path = project_root / "data" / "results" / "model_metrics.json"
    output_path = project_root / "data" / "results" / "interpretation.md"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load metrics
        logger.info(f"Loading model metrics from {metrics_path}")
        metrics_data = load_model_metrics(metrics_path)
        
        # Generate interpretation
        logger.info("Generating interpretation text")
        interpretation_text = generate_interpretation(metrics_data)
        
        # Write output
        logger.info(f"Writing interpretation to {output_path}")
        with open(output_path, 'w') as f:
            f.write(interpretation_text)
        
        logger.info("T031 completed successfully")
        print(f"Interpretation written to {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"Error during interpretation generation: {e}")
        raise

if __name__ == "__main__":
    main()
