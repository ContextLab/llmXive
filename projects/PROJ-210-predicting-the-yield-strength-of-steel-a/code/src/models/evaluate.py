import os
import logging
from typing import Dict, Any, Optional, Tuple, List, Callable
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, cross_val_score, cross_validate
import warnings

logger = logging.getLogger(__name__)

# Helper to generate associational framing text
def _generate_associational_framing(results: Dict[str, Any], 
                                    significant_interactions: List[str],
                                    p_values: Dict[str, float],
                                    fdr_threshold: float = 0.05) -> str:
    """
    Generates a text report explicitly framing the findings as associational.
    
    Args:
        results: Dictionary containing model performance metrics.
        significant_interactions: List of interaction terms identified as significant.
        p_values: Dictionary mapping interaction terms to their p-values.
        fdr_threshold: The FDR threshold used for significance.
        
    Returns:
        A formatted string report suitable for appending to logs or result files.
    """
    lines = []
    lines.append("=" * 80)
    lines.append("ASSOCIATIONAL FRAMING AND INTERPRETATION OF RESULTS")
    lines.append("=" * 80)
    lines.append("")
    lines.append("1. NATURE OF FINDINGS")
    lines.append("-" * 40)
    lines.append("The results presented in this report are strictly ASSOCIATIONAL.")
    lines.append("This analysis identifies statistical dependencies between input features")
    lines.append("(composition, heat treatment) and the target variable (yield strength).")
    lines.append("While the models (GAM, XGBoost, RF) detect non-linear patterns and")
    lines.append("interactions that correlate with yield strength, these findings do NOT")
    lines.append("establish causal mechanisms.")
    lines.append("")
    lines.append("2. INTERPRETATION OF INTERACTION TERMS")
    lines.append("-" * 40)
    if significant_interactions:
        lines.append(f"The following {len(significant_interactions)} interaction terms showed statistically significant")
        lines.append(f"associations with yield strength (after Benjamini-Hochberg FDR correction, alpha <= {fdr_threshold}):")
        lines.append("")
        for term in significant_interactions:
            p_val = p_values.get(term, "N/A")
            lines.append(f"  - {term}: p-value = {p_val}")
        lines.append("")
        lines.append("These interactions indicate that the effect of one variable on yield strength")
        lines.append("depends on the level of the other variable within the observed data distribution.")
        lines.append("They do not imply that manipulating one variable will causally change the other")
        lines.append("in a specific way outside the context of the training data distribution.")
    else:
        lines.append("No interaction terms passed the statistical significance threshold.")
        lines.append("This suggests that, within the noise of this dataset, main effects may dominate")
        lines.append("the predictive power, or that the sample size is insufficient to detect interactions.")
    lines.append("")
    lines.append("3. LIMITATIONS ON CAUSAL INFERENCE")
    lines.append("-" * 40)
    lines.append("- This study relies on observational data (NIST/Materials Project) and/or")
    lines.append("  literature-mined data without randomized controlled trials.")
    lines.append("- Unmeasured confounding variables (e.g., specific furnace calibration,")
    lines.append("  raw material batch variations) may influence both the input features")
    lines.append("  and the yield strength.")
    lines.append("- The 'orthogonalization' performed on interaction terms removes linear")
    lines.append("  dependence on main effects to improve model stability, but this is a")
    lines.append("  statistical adjustment, not a causal adjustment.")
    lines.append("")
    lines.append("4. RECOMMENDATIONS FOR FUTURE WORK")
    lines.append("-" * 40)
    lines.append("To move from association to causation, future work should:")
    lines.append("  1. Design controlled experiments (DOE) targeting the identified interactions.")
    lines.append("  2. Validate findings on independent datasets from different sources.")
    lines.append("  3. Incorporate domain knowledge (physics-based models) to constrain")
    lines.append("     the search space for causal mechanisms.")
    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF ASSOCIATIONAL FRAMING REPORT")
    lines.append("=" * 80)
    
    return "\n".join(lines)

def compare_model_performance(model_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compares R² scores of models and returns a summary.
    """
    logger.info("Comparing model performance...")
    summary = {}
    for name, metrics in model_results.items():
        r2 = metrics.get('r2_score', 0.0)
        summary[name] = {'r2_score': r2}
    
    # Identify best model
    if summary:
        best_model = max(summary, key=lambda x: summary[x]['r2_score'])
        summary['best_model'] = best_model
        logger.info(f"Best model: {best_model} with R² = {summary[best_model]['r2_score']:.4f}")
    
    return summary

def benjamini_hochberg_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Applies Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level.
        
    Returns:
        Tuple of (boolean list of rejections, adjusted p-values).
    """
    logger.info(f"Applying Benjamini-Hochberg correction with alpha={alpha}...")
    n = len(p_values)
    if n == 0:
        return [], []
        
    sorted_indices = np.argsort(p_values)
    sorted_pvals = np.array(p_values)[sorted_indices]
    
    # Calculate adjusted p-values
    adjusted_pvals = np.zeros(n)
    for i, p in enumerate(sorted_pvals):
        # Rank i+1, total n
        adj_p = p * n / (i + 1)
        adjusted_pvals[sorted_indices[i]] = min(adj_p, 1.0)
    
    # Ensure monotonicity (cumulative min from right to left)
    for i in range(n - 2, -1, -1):
        adjusted_pvals[i] = min(adjusted_pvals[i], adjusted_pvals[i + 1])
        
    # Determine rejections
    rejections = adjusted_pvals <= alpha
    
    logger.info(f"Found {np.sum(rejections)} significant interactions after FDR correction.")
    return rejections.tolist(), adjusted_pvals.tolist()

def perform_nested_permutation_test(
    X: pd.DataFrame,
    y: pd.Series,
    interaction_terms: List[str],
    model: Callable,
    n_repeats: int = 100,
    cv_folds: int = 3
) -> Dict[str, Any]:
    """
    Performs nested permutation tests to validate interaction significance.
    Specifically shuffles the raw interaction term to generate a null distribution.
    """
    logger.info(f"Performing nested permutation tests on {len(interaction_terms)} interaction terms...")
    
    results = {}
    
    for term in interaction_terms:
        if term not in X.columns:
            logger.warning(f"Interaction term {term} not found in data. Skipping.")
            continue
        
        # 1. Calculate observed score (R²) using cross-validation
        # Using a simple baseline for the "observed" to compare against null
        # In a real pipeline, this would use the trained model's CV score
        cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
        observed_scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        observed_r2 = np.mean(observed_scores)
        
        # 2. Generate null distribution
        null_scores = []
        for _ in range(n_repeats):
            # Create a copy to avoid modifying original
            X_perm = X.copy()
            # Shuffle the specific interaction term relative to target
            # This breaks the association between this term and y
            X_perm[term] = np.random.permutation(X_perm[term].values)
            
            # Score on permuted data
            perm_scores = cross_val_score(model, X_perm, y, cv=cv, scoring='r2')
            null_scores.append(np.mean(perm_scores))
        
        null_scores = np.array(null_scores)
        
        # 3. Calculate p-value
        # p = P(null_score >= observed_score)
        # Since lower R² is better for null (no signal), we check if observed is significantly better
        # i.e., observed_r2 > null_r2. 
        # P-value is fraction of null scores that are >= observed (if we define score as R² where higher is better)
        # Actually, if observed is better (higher R²), we want to know how often null is that good.
        # p = (sum(null >= observed) + 1) / (n + 1)
        p_val = (np.sum(null_scores >= observed_r2) + 1) / (n_repeats + 1)
        
        results[term] = {
            'observed_r2': observed_r2,
            'null_mean': np.mean(null_scores),
            'null_std': np.std(null_scores),
            'p_value': p_val,
            'null_distribution': null_scores.tolist()
        }
        
        logger.debug(f"Term: {term}, Observed R²: {observed_r2:.4f}, P-value: {p_val:.4f}")
        
    return results

def run_evaluation_pipeline(
    X: pd.DataFrame,
    y: pd.Series,
    models: Dict[str, Any],
    interaction_terms: List[str],
    output_dir: str = "data/results",
    fdr_alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Runs the full evaluation pipeline including model comparison, permutation tests,
    FDR correction, and generates the explicit associational framing report.
    
    Args:
        X: Feature DataFrame.
        y: Target Series.
        models: Dictionary of model instances.
        interaction_terms: List of interaction term column names.
        output_dir: Directory to save results.
        fdr_alpha: FDR threshold.
        
    Returns:
        Dictionary containing all evaluation results and the framing report string.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Compare Models
    # We need to fit a simple version of each model to get R² scores for comparison
    # In a real pipeline, these would be the already trained models
    model_results = {}
    for name, model in models.items():
        # Simple CV score for comparison
        try:
            scores = cross_val_score(model, X, y, cv=3, scoring='r2')
            model_results[name] = {'r2_score': np.mean(scores), 'std': np.std(scores)}
        except Exception as e:
            logger.error(f"Error evaluating model {name}: {e}")
            model_results[name] = {'r2_score': np.nan, 'std': np.nan}
    
    comparison_summary = compare_model_performance(model_results)
    
    # 2. Perform Nested Permutation Tests
    # Use a generic model for the test (e.g., Random Forest) or the best performing one
    # For this task, we'll use a placeholder logic assuming 'XGBoost' or 'RF' is available
    test_model = None
    if 'XGBoost' in models:
        test_model = models['XGBoost']
    elif 'RandomForest' in models:
        test_model = models['RandomForest']
    else:
        # Fallback to a simple regressor if needed
        from sklearn.ensemble import RandomForestRegressor
        test_model = RandomForestRegressor(n_estimators=10, random_state=42)
        
    permutation_results = perform_nested_permutation_test(
        X, y, interaction_terms, test_model, n_repeats=50, cv_folds=3
    )
    
    # 3. Apply FDR Correction
    p_values = [res['p_value'] for res in permutation_results.values()]
    terms = list(permutation_results.keys())
    
    if p_values:
        rejections, adj_pvals = benjamini_hochberg_correction(p_values, alpha=fdr_alpha)
        
        # Map back to terms
        significant_terms = []
        final_p_values = {}
        for term, is_sig, adj_p in zip(terms, rejections, adj_pvals):
            final_p_values[term] = adj_p
            if is_sig:
                significant_terms.append(term)
    else:
        significant_terms = []
        final_p_values = {}
        
    # 4. Generate Associational Framing Report (FR-007)
    framing_report = _generate_associational_framing(
        model_results,
        significant_terms,
        final_p_values,
        fdr_alpha
    )
    
    # Save the framing report to a file
    report_path = os.path.join(output_dir, "associational_framing_report.txt")
    with open(report_path, "w") as f:
        f.write(framing_report)
    logger.info(f"Associational framing report saved to {report_path}")
    
    # 5. Compile Final Results
    final_results = {
        'model_comparison': comparison_summary,
        'permutation_tests': permutation_results,
        'fdr_corrected_p_values': final_p_values,
        'significant_interactions': significant_terms,
        'associational_framing_report_path': report_path,
        'associational_framing_text': framing_report
    }
    
    return final_results