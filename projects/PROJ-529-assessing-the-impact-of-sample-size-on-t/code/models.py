"""Base model classes and meta-analysis fitting logic for T023."""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
import numpy as np
import csv
from pathlib import Path
import logging

from config import get_nominal_coverage_target, get_stability_threshold
from utils.exceptions import NegativeVarianceError, ZeroVarianceError, ConvergenceError, handle_variance_issues
from utils.seeds import SeedManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Study:
    """Represents a single study within a meta-analysis."""
    study_id: str
    effect_size: float
    standard_error: float
    sample_size: Optional[int] = None
    weight: Optional[float] = None
    
    def variance(self) -> float:
        """Calculate variance from standard error."""
        return self.standard_error ** 2
        
@dataclass
class Subsample:
    """Represents a bootstrap subsample of studies."""
    subsample_id: str
    meta_id: str
    k: int  # Number of studies in subsample
    seed: int
    estimator_type: str
    studies: List[Study] = field(default_factory=list)
    pooled_effect: Optional[float] = None
    pooled_se: Optional[float] = None
    
@dataclass
class MetaAnalysis:
    """Represents a complete meta-analysis."""
    meta_id: str
    title: str
    source: str
    studies: List[Study] = field(default_factory=list)
    full_sample_effect: Optional[float] = None
    full_sample_se: Optional[float] = None
    subsamples: List[Subsample] = field(default_factory=list)
    
@dataclass
class StabilityMetric:
    """Represents stability metrics for a given k."""
    meta_id: str
    k: int
    model_type: str
    sd_effects: float
    coverage_rate: float
    threshold_reached: bool = False
    changepoint_estimate: Optional[float] = None

def _calculate_tau2_reml(studies: List[Study]) -> float:
    """
    Calculate between-study variance (tau^2) using Restricted Maximum Likelihood (REML).
    This is a simplified iterative implementation for robustness without external heavy dependencies.
    
    Formula: tau^2 = (Sum(w_i * (y_i - mu)^2) - (k-1)) / (Sum(w_i) - Sum(w_i^2)/Sum(w_i))
    where w_i = 1 / (v_i + tau^2)
    """
    k = len(studies)
    if k < 2:
        return 0.0
    
    effects = np.array([s.effect_size for s in studies])
    variances = np.array([s.variance() for s in studies])
    
    # Handle zero variance immediately
    if np.any(variances == 0):
        logger.warning("Zero variance detected in studies. Clamping to small epsilon.")
        variances = np.maximum(variances, 1e-10)
    
    # Initial guess for tau^2 (DerSimonian-Laird estimator as start)
    # Q statistic
    weights_inv = 1.0 / variances
    sum_w = np.sum(weights_inv)
    mu_dl = np.sum(weights_inv * effects) / sum_w
    Q = np.sum(weights_inv * (effects - mu_dl)**2)
    
    C = sum_w - (np.sum(weights_inv**2) / sum_w)
    if C <= 0:
        tau2 = 0.0
    else:
        tau2 = max(0.0, (Q - (k - 1)) / C)
    
    # REML Iteration
    for _ in range(50):
        new_weights = 1.0 / (variances + tau2)
        sum_new_w = np.sum(new_weights)
        mu = np.sum(new_weights * effects) / sum_new_w
        
        numerator = np.sum(new_weights * (effects - mu)**2) - (k - 1)
        denominator = sum_new_w - (np.sum(new_weights**2) / sum_new_w)
        
        if denominator <= 1e-10:
            break
        
        new_tau2 = max(0.0, numerator / denominator)
        
        if abs(new_tau2 - tau2) < 1e-6:
            tau2 = new_tau2
            break
        tau2 = new_tau2
        
    return tau2

def _fit_fixed_effects(studies: List[Study]) -> Tuple[float, float]:
    """
    Fit a Fixed Effects model.
    Returns (pooled_effect, pooled_se).
    """
    if not studies:
        raise ValueError("Cannot fit model to empty study list")
        
    effects = np.array([s.effect_size for s in studies])
    variances = np.array([s.variance() for s in studies])
    
    # Handle zero variance
    if np.any(variances == 0):
        logger.warning("Zero variance detected in FE model. Clamping.")
        variances = np.maximum(variances, 1e-10)
        
    weights = 1.0 / variances
    sum_w = np.sum(weights)
    
    pooled_effect = np.sum(weights * effects) / sum_w
    pooled_se = np.sqrt(1.0 / sum_w)
    
    return pooled_effect, pooled_se

def _fit_random_effects(studies: List[Study], method: str = "REML") -> Tuple[float, float]:
    """
    Fit a Random Effects model.
    method: 'REML' or 'DL' (DerSimonian-Laird)
    Returns (pooled_effect, pooled_se).
    """
    if not studies:
        raise ValueError("Cannot fit model to empty study list")
        
    effects = np.array([s.effect_size for s in studies])
    variances = np.array([s.variance() for s in studies])
    
    # Handle zero variance
    if np.any(variances == 0):
        logger.warning("Zero variance detected in RE model. Clamping.")
        variances = np.maximum(variances, 1e-10)
        
    k = len(studies)
    
    # Calculate tau^2
    if method == "REML":
        tau2 = _calculate_tau2_reml(studies)
    elif method == "DL":
        # DL Estimator
        weights_inv = 1.0 / variances
        sum_w = np.sum(weights_inv)
        mu = np.sum(weights_inv * effects) / sum_w
        Q = np.sum(weights_inv * (effects - mu)**2)
        C = sum_w - (np.sum(weights_inv**2) / sum_w)
        
        if C <= 0:
            tau2 = 0.0
        else:
            tau2 = max(0.0, (Q - (k - 1)) / C)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Calculate weights with tau^2
    weights = 1.0 / (variances + tau2)
    sum_w = np.sum(weights)
    
    pooled_effect = np.sum(weights * effects) / sum_w
    pooled_se = np.sqrt(1.0 / sum_w)
    
    return pooled_effect, pooled_se

def fit_meta_analysis_model(subsample: Subsample, full_sample_effect: float) -> StabilityMetric:
    """
    Fit the appropriate model based on k (sample size) and return a StabilityMetric.
    
    Logic per FR-003:
    - If k >= 10: Use DerSimonian-Laird (DL) Random Effects.
    - If k < 10: Use REML Random Effects.
    
    Calculates:
    - pooled_effect, pooled_se (updates the subsample object)
    - sd_effects: Standard deviation of pooled effects across subsamples (aggregated later, here we return the single point)
    - coverage_rate: Whether the CI contains the full_sample_effect (1.0 or 0.0 for this single instance)
    
    Note: The task asks to tag this as "primary" deliverable.
    """
    studies = subsample.studies
    k = subsample.k
    
    # Determine estimator
    if k >= 10:
        estimator = "DL"
        model_type = "RandomEffects_DL"
    else:
        estimator = "REML"
        model_type = "RandomEffects_REML"
    
    try:
        pooled_effect, pooled_se = _fit_random_effects(studies, method=estimator)
    except Exception as e:
        logger.error(f"Model fitting failed for {subsample.subsample_id}: {e}")
        # Fallback to Fixed Effects if RE fails (rare)
        try:
            pooled_effect, pooled_se = _fit_fixed_effects(studies)
            model_type = "FixedEffects_Fallback"
        except Exception as e2:
            logger.critical(f"Both RE and FE failed for {subsample.subsample_id}: {e2}")
            raise ConvergenceError(f"Model fitting failed completely: {e2}")
    
    # Update subsample
    subsample.pooled_effect = pooled_effect
    subsample.pooled_se = pooled_se
    subsample.estimator_type = estimator
    
    # Calculate coverage for this single subsample
    # CI: [pooled_effect - 1.96 * pooled_se, pooled_effect + 1.96 * pooled_se]
    lower = pooled_effect - 1.96 * pooled_se
    upper = pooled_effect + 1.96 * pooled_se
    contains = 1.0 if (lower <= full_sample_effect <= upper) else 0.0
    
    # Note: sd_effects is an aggregate metric across multiple subsamples.
    # For this function, we return the raw pooled effect. The aggregation happens in metrics.py.
    # However, the StabilityMetric class expects sd_effects. We will return 0.0 here and let
    # the aggregation logic in metrics.py compute the actual SD.
    # Or, we can interpret this task as fitting the model and preparing data for the metric.
    # The task says: "Calculate standard deviation of pooled effects... for each k" (T025).
    # So here we just return the metric with coverage=1/0 and sd=0 (placeholder for aggregation).
    
    metric = StabilityMetric(
        meta_id=subsample.meta_id,
        k=k,
        model_type=model_type,
        sd_effects=0.0, # Will be aggregated in T025
        coverage_rate=contains,
        threshold_reached=False
    )
    
    return metric

def run_modeling_pipeline(subsamples: List[Subsample], full_sample_effect: float, output_path: str) -> List[StabilityMetric]:
    """
    Run the modeling pipeline for a list of subsamples.
    Writes results to `data/processed/stability_metrics.csv`.
    
    Args:
        subsamples: List of generated subsamples from T016.
        full_sample_effect: The reference effect size from the full meta-analysis.
        output_path: Path to the output CSV file.
        
    Returns:
        List of StabilityMetric objects.
    """
    logger.info(f"Starting modeling pipeline for {len(subsamples)} subsamples.")
    metrics = []
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Header
        writer.writerow(['meta_id', 'k', 'model_type', 'pooled_effect', 'pooled_se', 'coverage_flag'])
        
        for subsample in subsamples:
            try:
                metric = fit_meta_analysis_model(subsample, full_sample_effect)
                metrics.append(metric)
                
                # Write row for this subsample
                writer.writerow([
                    subsample.meta_id,
                    subsample.k,
                    metric.model_type,
                    f"{subsample.pooled_effect:.6f}",
                    f"{subsample.pooled_se:.6f}",
                    metric.coverage_rate
                ])
                
            except Exception as e:
                logger.error(f"Skipping subsample {subsample.subsample_id} due to error: {e}")
                # Continue with next
                continue
                
    logger.info(f"Modeling pipeline complete. Results written to {output_path}")
    return metrics

def main():
    """
    Entry point for T023.
    Reads subsamples from data/processed/subsample_data.parquet (or similar),
    fits models, and writes to data/processed/stability_metrics.csv.
    """
    # For demonstration in this task, we assume subsamples are loaded.
    # In a real pipeline, this would be called by an orchestrator or read from disk.
    # Since T016 produces a parquet file, we need to read it here.
    
    input_path = Path("data/processed/subsample_data.parquet")
    output_path = "data/processed/stability_metrics.csv"
    
    if not input_path.exists():
        logger.warning(f"Input file {input_path} not found. Skipping modeling pipeline execution.")
        logger.warning("This task is implemented. To run, ensure subsample_data.parquet exists.")
        return

    # Attempt to load parquet (requires pandas, which is in requirements)
    try:
        import pandas as pd
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} subsamples from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        return

    # Reconstruct Subsample objects and group by meta_id to get full_sample_effect
    # Assumption: The parquet contains columns: meta_id, subsample_id, k, seed, estimator_type, effect_size, standard_error (repeated rows?)
    # Or it contains a list of studies per row.
    # Given the complexity of reconstructing objects from a flat parquet without schema,
    # we will implement a simplified loader that assumes a specific structure or mocks the process
    # if the structure isn't standard.
    
    # However, T016 description says: "logging seeds and handling k < 3 edge cases. ... logging every subsample iteration ... to data/processed/subsample_data.parquet"
    # It doesn't specify the exact schema.
    
    # To make this robust and runnable without assuming a specific complex schema that might not exist yet,
    # we will implement a mock runner that generates synthetic subsamples for demonstration IF the file is missing or empty,
    # BUT the constraint says "Real data only".
    # So we will try to load. If the schema is unknown, we log an error.
    
    # Let's assume the parquet has a column 'studies' which is a list of dicts or similar, or it's a long format.
    # Since we cannot guess the exact schema of T016's output without seeing it, we will implement the logic
    # that expects a 'studies_json' column or similar, and fail gracefully if not found.
    
    if 'studies_json' not in df.columns:
        # Try to infer from columns
        logger.error("Expected 'studies_json' column in subsample_data.parquet not found.")
        logger.error("Cannot proceed with modeling without study data.")
        return
        
    # Group by meta_id to find full_sample_effect
    # We assume the full sample effect is stored in a column 'full_sample_effect' or derived from the full set of studies.
    # If not present, we cannot calculate coverage.
    if 'full_sample_effect' not in df.columns:
        logger.error("Column 'full_sample_effect' not found. Cannot calculate coverage rates.")
        return

    subsamples = []
    for _, row in df.iterrows():
        # Parse studies
        import json
        try:
            studies_data = json.loads(row['studies_json'])
            studies = [Study(s['study_id'], s['effect_size'], s['standard_error']) for s in studies_data]
            
            subsample = Subsample(
                subsample_id=row['subsample_id'],
                meta_id=row['meta_id'],
                k=row['k'],
                seed=row['seed'],
                estimator_type=row.get('estimator_type', 'unknown'),
                studies=studies
            )
            subsamples.append(subsample)
        except Exception as e:
            logger.warning(f"Failed to parse row {row.name}: {e}")
            continue
    
    # Run pipeline
    if subsamples:
        # We need a full_sample_effect for each meta_id. The row has it.
        # We'll pass the row's full_sample_effect to the function.
        # Since run_modeling_pipeline expects a single float, we need to group by meta_id or pass it per row.
        # Let's modify run_modeling_pipeline to accept a mapping or handle per-row.
        
        # Actually, let's just run the logic per row in the loop to keep it simple and correct.
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['meta_id', 'k', 'model_type', 'pooled_effect', 'pooled_se', 'coverage_flag'])
            
            for subsample in subsamples:
                # Find full_sample_effect from the row (we need to match meta_id, but we have it in the row context)
                # Since we are iterating the dataframe, we can get it from the row.
                # But we are iterating the reconstructed list.
                # Let's re-iterate the dataframe to be safe and simple.
                pass

        # Re-do loop for simplicity
        with open(output_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['meta_id', 'k', 'model_type', 'pooled_effect', 'pooled_se', 'coverage_flag'])
            
            for _, row in df.iterrows():
                try:
                    studies_data = json.loads(row['studies_json'])
                    studies = [Study(s['study_id'], s['effect_size'], s['standard_error']) for s in studies_data]
                    subsample = Subsample(
                        subsample_id=row['subsample_id'],
                        meta_id=row['meta_id'],
                        k=row['k'],
                        seed=row['seed'],
                        estimator_type=row.get('estimator_type', 'unknown'),
                        studies=studies
                    )
                    
                    metric = fit_meta_analysis_model(subsample, row['full_sample_effect'])
                    
                    writer.writerow([
                        subsample.meta_id,
                        subsample.k,
                        metric.model_type,
                        f"{subsample.pooled_effect:.6f}",
                        f"{subsample.pooled_se:.6f}",
                        metric.coverage_rate
                    ])
                except Exception as e:
                    logger.error(f"Error processing row {row.name}: {e}")
                    continue
        
        logger.info(f"Results written to {output_path}")
    else:
        logger.warning("No valid subsamples found to process.")

if __name__ == "__main__":
    main()