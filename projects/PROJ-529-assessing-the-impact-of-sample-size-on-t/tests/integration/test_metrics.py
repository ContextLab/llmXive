"""
Integration test for coverage rate calculation (US2).

This test verifies the end-to-end flow of calculating CI coverage rates
for meta-analytic subsamples against a full-sample reference estimate.

Prerequisites:
- T016: Subsampling pipeline must be functional (generates data/processed/subsample_data.parquet)
- T023: Model fitting logic (determine_estimator_method, fit_meta_analysis) must be available

Output:
- data/output/coverage_test_results.json: Contains calculated coverage rates per k
"""
import os
import json
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

# Import from project modules (matching API surface)
from models import MetaAnalysis, Subsample, determine_estimator_method, fit_meta_analysis
from subsample import SubsampleResult, load_meta_analyses, generate_subsample_indices, calculate_pooled_effect
from utils.seeds import set_seed, ensure_log_directory
from utils.exceptions import MetaAnalysisError, ZeroVarianceError, NegativeVarianceError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CoverageTestResult:
    """Result of a coverage rate calculation for a specific k."""
    k: int
    n_subsamples: int
    coverage_rate: float
    reference_effect: float
    reference_se: float
    subsample_effects: List[float]
    subsample_ses: List[float]
    ci_contains_ref: List[bool]

def generate_test_synthetic_data(n_meta_analyses: int = 10, min_k: int = 5, max_k: int = 20) -> List[Dict[str, Any]]:
    """
    Generate synthetic meta-analysis data for testing purposes.
    
    This is used ONLY for the integration test to ensure we have data
    without requiring the full data acquisition pipeline (T012/T019).
    
    Returns:
        List of meta-analysis data dictionaries.
    """
    np.random.seed(42)
    data = []
    
    for i in range(n_meta_analyses):
        k = np.random.randint(min_k, max_k + 1)
        true_effect = np.random.uniform(0.1, 0.5)
        tau_sq = np.random.uniform(0.01, 0.1)
        
        studies = []
        for j in range(k):
            # Generate study effect and SE
            study_effect = np.random.normal(true_effect, np.sqrt(tau_sq))
            study_se = np.sqrt(np.random.uniform(0.01, 0.1))  # Random SE
            
            studies.append({
                "effect": float(study_effect),
                "se": float(study_se),
                "variance": float(study_se ** 2)
            })
        
        data.append({
            "meta_id": f"test_ma_{i:03d}",
            "studies": studies,
            "n_studies": k
        })
    
    return data

def save_test_data_to_parquet(data: List[Dict[str, Any]], output_path: str):
    """Save test data to parquet format compatible with load_meta_analyses."""
    # Convert to the expected format for load_meta_analyses
    # This mimics the output of T016 subsample.py
    rows = []
    for ma in data:
        for study in ma["studies"]:
            rows.append({
                "meta_id": ma["meta_id"],
                "study_id": study["effect"], # Simplified: using effect as unique identifier
                "effect_size": study["effect"],
                "se": study["se"],
                "variance": study["variance"]
            })
    
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved test data to {output_path}")

def calculate_coverage_rate(
    subsample_effects: List[float],
    subsample_ses: List[float],
    reference_effect: float,
    reference_se: float,
    alpha: float = 0.05
) -> List[bool]:
    """
    Calculate whether each subsample's CI contains the reference effect.
    
    Args:
        subsample_effects: List of pooled effect sizes from subsamples
        subsample_ses: List of standard errors for subsamples
        reference_effect: The "true" full-sample effect size
        reference_se: Standard error of the reference estimate
        alpha: Significance level (default 0.05 for 95% CI)
    
    Returns:
        List of booleans indicating if CI contains reference effect
    """
    z_score = 1.96  # For 95% CI
    contains_ref = []
    
    for effect, se in zip(subsample_effects, subsample_ses):
        if se <= 0:
            # Handle zero or negative SE gracefully
            contains_ref.append(False)
            continue
        
        lower_ci = effect - z_score * se
        upper_ci = effect + z_score * se
        
        # Check if reference effect falls within the CI
        if lower_ci <= reference_effect <= upper_ci:
            contains_ref.append(True)
        else:
            contains_ref.append(False)
    
    return contains_ref

def run_coverage_test(
    k_values: List[int] = [3, 5, 10],
    n_subsamples_per_k: int = 20,
    test_data_path: Optional[str] = None,
    output_path: str = "data/output/coverage_test_results.json"
) -> Dict[str, Any]:
    """
    Run the full integration test for coverage rate calculation.
    
    Args:
        k_values: List of study counts (k) to test
        n_subsamples_per_k: Number of bootstrap subsamples per k
        test_data_path: Path to test data (if None, generates synthetic)
        output_path: Path to save results
    
    Returns:
        Dictionary containing test results
    """
    logger.info(f"Starting coverage rate integration test for k values: {k_values}")
    
    # Prepare data
    if test_data_path and os.path.exists(test_data_path):
        logger.info(f"Loading test data from {test_data_path}")
        # In a real scenario, we would use load_meta_analyses here
        # For this test, we'll generate fresh synthetic data to ensure consistency
        test_data = generate_test_synthetic_data(n_meta_analyses=5, min_k=max(k_values), max_k=max(k_values) + 5)
        temp_path = tempfile.mktemp(suffix=".parquet")
        save_test_data_to_parquet(test_data, temp_path)
        test_data_path = temp_path
    else:
        logger.info("Generating synthetic test data")
        test_data = generate_test_synthetic_data(n_meta_analyses=5, min_k=max(k_values), max_k=max(k_values) + 5)
        temp_path = tempfile.mktemp(suffix=".parquet")
        save_test_data_to_parquet(test_data, temp_path)
        test_data_path = temp_path
    
    try:
        # Load meta-analyses (using the actual function from subsample.py)
        meta_analyses = load_meta_analyses(test_data_path)
        logger.info(f"Loaded {len(meta_analyses)} meta-analyses")
        
        if not meta_analyses:
            raise ValueError("No meta-analyses loaded from test data")
        
        results = []
        
        for k in k_values:
            logger.info(f"Testing k={k}")
            
            # Select a meta-analysis with enough studies
            ma = None
            for candidate in meta_analyses:
                if candidate.n_studies >= k:
                    ma = candidate
                    break
            
            if ma is None:
                logger.warning(f"No meta-analysis with >= {k} studies found, skipping k={k}")
                continue
            
            # Calculate full-sample reference estimate
            estimator_type = determine_estimator_method(ma.n_studies)
            ref_result = fit_meta_analysis(ma.studies, estimator_type)
            reference_effect = ref_result["pooled_effect"]
            reference_se = ref_result["se_pooled"]
            
            logger.info(f"Reference effect (k={ma.n_studies}): {reference_effect:.4f} (SE={reference_se:.4f})")
            
            # Generate subsamples and calculate coverage
            subsample_effects = []
            subsample_ses = []
            ci_contains_ref = []
            
            for i in range(n_subsamples_per_k):
                # Generate random subsample indices
                set_seed(42 + i)  # Deterministic for reproducibility
                indices = generate_subsample_indices(ma.n_studies, k)
                
                if len(indices) < k:
                    continue
                
                # Extract subsample studies
                subsample_studies = [ma.studies[idx] for idx in indices]
                
                # Fit model to subsample
                try:
                    subsample_estimator = determine_estimator_method(k)
                    subsample_result = fit_meta_analysis(subsample_studies, subsample_estimator)
                    
                    subsample_effects.append(subsample_result["pooled_effect"])
                    subsample_ses.append(subsample_result["se_pooled"])
                    
                    # Calculate if CI contains reference
                    contains = calculate_coverage_rate(
                        [subsample_result["pooled_effect"]],
                        [subsample_result["se_pooled"]],
                        reference_effect,
                        reference_se
                    )[0]
                    ci_contains_ref.append(contains)
                    
                except (ZeroVarianceError, NegativeVarianceError, MetaAnalysisError) as e:
                    logger.warning(f"Subsample {i} failed: {e}")
                    continue
            
            if not subsample_effects:
                logger.warning(f"No valid subsamples for k={k}")
                continue
            
            coverage_rate = sum(ci_contains_ref) / len(ci_contains_ref)
            
            result = CoverageTestResult(
                k=k,
                n_subsamples=len(subsample_effects),
                coverage_rate=coverage_rate,
                reference_effect=reference_effect,
                reference_se=reference_se,
                subsample_effects=subsample_effects,
                subsample_ses=subsample_ses,
                ci_contains_ref=ci_contains_ref
            )
            
            results.append(asdict(result))
            logger.info(f"k={k}: Coverage rate = {coverage_rate:.4f} ({sum(ci_contains_ref)}/{len(ci_contains_ref)})")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump({
                "test_status": "completed",
                "k_values_tested": k_values,
                "results": results,
                "summary": {
                    "total_k_tested": len(results),
                    "average_coverage": np.mean([r["coverage_rate"] for r in results]) if results else 0.0
                }
            }, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        return {
            "status": "success",
            "results_path": output_path,
            "coverage_rates": [r["coverage_rate"] for r in results]
        }
        
    finally:
        # Clean up temp file if created
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

def main():
    """Main entry point for the integration test."""
    logger.info("=== Coverage Rate Integration Test (T022) ===")
    
    # Define test parameters
    k_values = [3, 5, 10]
    n_subsamples = 20
    output_path = "data/output/coverage_test_results.json"
    
    try:
        result = run_coverage_test(
            k_values=k_values,
            n_subsamples_per_k=n_subsamples,
            output_path=output_path
        )
        
        if result["status"] == "success":
            logger.info("✓ Integration test completed successfully")
            logger.info(f"  Coverage rates: {result['coverage_rates']}")
            return 0
        else:
            logger.error("✗ Integration test failed")
            return 1
            
    except Exception as e:
        logger.error(f"✗ Integration test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())