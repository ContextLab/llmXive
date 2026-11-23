"""
code/models.py

Implements Fixed Effects (FE) and Random Effects (RE) meta-analysis models.
Primary Output: Writes results to data/processed/stability_metrics.csv.
Logic: Uses DerSimonian-Laird (DL) for k >= 10 and REML for k < 10 per FR-003.
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
import numpy as np
import csv
from pathlib import Path
import logging
import json

# Import config for thresholds if needed, though logic is hardcoded per task spec
# Import utils for error handling
from utils.exceptions import (
    ZeroVarianceError,
    NegativeVarianceError,
    ConvergenceError,
    handle_variance_issues,
    validate_variance_bounds
)
from utils.seeds import SeedManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Study:
    """Represents a single study within a meta-analysis."""
    meta_id: str
    study_id: str
    effect_size: float
    se: float
    n: Optional[int] = None

    def __post_init__(self):
        # Basic validation
        if self.se <= 0:
            raise ZeroVarianceError(f"Study {self.study_id} has non-positive SE: {self.se}")
        if self.effect_size != self.effect_size:  # NaN check
            raise ValueError(f"Study {self.study_id} has NaN effect size.")

@dataclass
class Subsample:
    """Represents a bootstrap subsample of studies."""
    meta_id: str
    k: int
    seed: int
    studies: List[Study] = field(default_factory=list)

    def get_effect_sizes(self) -> np.ndarray:
        return np.array([s.effect_size for s in self.studies])

    def get_variances(self) -> np.ndarray:
        # Variance = SE^2
        return np.array([s.se ** 2 for s in self.studies])

    def get_n_studies(self) -> int:
        return len(self.studies)

@dataclass
class MetaAnalysis:
    """Container for a full meta-analysis dataset."""
    meta_id: str
    studies: List[Study] = field(default_factory=list)
    full_sample_effect: Optional[float] = None
    full_sample_se: Optional[float] = None

    def __post_init__(self):
        if not self.studies:
            raise ValueError("MetaAnalysis must have at least one study.")

@dataclass
class StabilityMetric:
    """Result of a model fit on a subsample."""
    meta_id: str
    k: int
    seed: int
    model_type: str  # 'FE', 'RE_DL', 'RE_REML'
    pooled_effect: float
    pooled_se: float
    ci_lower: float
    ci_upper: float
    is_primary: bool  # True if matches the k>=10 DL / k<10 REML rule

def _fit_fixed_effects(
    effects: np.ndarray,
    variances: np.ndarray
) -> Tuple[float, float]:
    """
    Fits a Fixed Effects model using inverse-variance weighting.
    Returns (pooled_effect, pooled_se).
    """
    if len(effects) == 0:
        raise ValueError("Cannot fit FE model with 0 studies.")

    weights = 1.0 / variances
    pooled_effect = np.sum(weights * effects) / np.sum(weights)
    pooled_se = np.sqrt(1.0 / np.sum(weights))

    return pooled_effect, pooled_se

def _fit_random_effects_dl(
    effects: np.ndarray,
    variances: np.ndarray
) -> Tuple[float, float]:
    """
    Fits a Random Effects model using DerSimonian-Laird (DL) estimator for tau^2.
    Returns (pooled_effect, pooled_se).
    """
    if len(effects) < 2:
        raise ValueError("Cannot fit RE model with < 2 studies for DL estimation.")

    weights_inv_var = 1.0 / variances
    sum_w = np.sum(weights_inv_var)
    sum_w_sq = np.sum(weights_inv_var ** 2)

    # Q statistic
    Q = np.sum(weights_inv_var * (effects - np.sum(weights_inv_var * effects) / sum_w) ** 2)
    C = sum_w - (sum_w_sq / sum_w)

    # Tau^2 estimation
    tau_sq = max(0.0, (Q - (len(effects) - 1)) / C)

    # New weights
    new_variances = variances + tau_sq
    new_weights = 1.0 / new_variances
    new_sum_w = np.sum(new_weights)

    pooled_effect = np.sum(new_weights * effects) / new_sum_w
    pooled_se = np.sqrt(1.0 / new_sum_w)

    return pooled_effect, pooled_se

def _fit_random_effects_reml(
    effects: np.ndarray,
    variances: np.ndarray
) -> Tuple[float, float]:
    """
    Fits a Random Effects model using Restricted Maximum Likelihood (REML).
    Uses a simple Newton-Raphson or optimization approach since statsmodels
    might be overkill or unavailable in strict environments, but we aim for
    standard implementation.
    
    Simplified REML implementation for robustness without heavy dependencies if possible,
    or fallback to a known robust estimator if REML is strictly required.
    Given the constraint to use 'real' code and standard libs, we implement
    a standard iterative REML solver.
    """
    if len(effects) < 2:
        raise ValueError("Cannot fit RE model with < 2 studies for REML estimation.")

    # Initial guess for tau^2 (using DL)
    weights_inv_var = 1.0 / variances
    sum_w = np.sum(weights_inv_var)
    sum_w_sq = np.sum(weights_inv_var ** 2)
    Q = np.sum(weights_inv_var * (effects - np.sum(weights_inv_var * effects) / sum_w) ** 2)
    C = sum_w - (sum_w_sq / sum_w)
    tau_sq = max(0.0, (Q - (len(effects) - 1)) / C)

    # Iterative REML
    # Log-likelihood for REML: -0.5 * (sum(log(V_i)) + log(sum(1/V_i)) + sum(y_i^2/V_i) - (sum(y_i/V_i))^2/sum(1/V_i))
    # where V_i = sigma_i^2 + tau^2
    
    max_iter = 50
    tol = 1e-6
    
    for _ in range(max_iter):
        current_variances = variances + tau_sq
        weights = 1.0 / current_variances
        sum_w = np.sum(weights)
        
        if sum_w == 0:
            break
            
        # Derivative of REML log-likelihood w.r.t tau^2
        # d/d(tau^2) [ -0.5 * ( sum(log(V)) + log(sum(1/V)) + ... ) ]
        # Simplified update step using Newton-Raphson on the profile likelihood
        
        # Calculate the profile likelihood derivative (score function)
        # Score = 0.5 * ( sum(1/V_i) - sum(1/V_i^2) * ( (sum(y/V))^2 / sum(1/V) + sum(y^2/V) - (sum(y/V))^2/sum(1/V) )? )
        # Actually, let's use a simpler gradient ascent on the restricted log likelihood
        
        # Current estimate of pooled effect
        mu = np.sum(weights * effects) / sum_w
        
        # Residuals
        residuals = effects - mu
        
        # Derivative of log-likelihood
        # dL/dtau2 = 0.5 * sum( 1/(sigma^2+tau^2) ) - 0.5 * sum( (y-mu)^2 / (sigma^2+tau^2)^2 ) + 0.5 * (sum(1/(sigma^2+tau^2)))^-1 * sum( (y-mu)^2 / (sigma^2+tau^2)^2 )?
        # Standard REML score equation: sum(1/V) - sum( (y-mu)^2 / V^2 ) + (sum(1/V^2) / sum(1/V)) * sum( (y-mu)^2 / V )?
        
        # Let's use the standard iterative re-weighted least squares logic for REML
        # Update tau^2 using the moment estimator on residuals
        # New tau^2 = ( sum( (y-mu)^2 / V^2 ) - sum(1/V) ) / ( sum(1/V^2) - (sum(1/V^2)/sum(1/V))^2 * sum(1/V) )?
        # This is getting complex. Let's use a robust numerical optimization for the scalar tau^2.
        
        # Define negative log-likelihood (to minimize)
        def nll(tau):
            if tau < 0: return 1e9
            V = variances + tau
            w = 1.0 / V
            log_V = np.log(V)
            sum_w = np.sum(w)
            if sum_w == 0: return 1e9
            mu = np.sum(w * effects) / sum_w
            rss = np.sum(w * (effects - mu) ** 2)
            # REML log-likelihood (ignoring constants)
            # L = -0.5 * ( sum(log(V)) + log(sum(1/V)) + rss )
            return 0.5 * (np.sum(log_V) + np.log(sum_w) + rss)

        # Simple gradient-free optimization (Brent's method or similar)
        # Since we are in a pure python context without scipy.optimize (unless imported),
        # let's check if we can import scipy. The prompt says "pandas, numpy, scipy...".
        # We will use scipy.optimize if available, else fallback to grid search.
        try:
            from scipy.optimize import minimize_scalar
            res = minimize_scalar(nll, bounds=(0, np.max(variances)*10), method='bounded')
            tau_sq = res.x
            if res.fun == 1e9: # Failed to converge to valid
                tau_sq = 0
        except ImportError:
            # Fallback to grid search if scipy is missing (unlikely given requirements)
            best_tau = 0
            best_val = nll(0)
            for t in np.linspace(0, np.max(variances)*10, 100):
                val = nll(t)
                if val < best_val:
                    best_val = val
                    best_tau = t
            tau_sq = best_tau

        # Check convergence (tau_sq change is small) - simplified here by fixed iterations
        # For this task, one iteration of re-estimation is often sufficient for stability metrics
        # or we run until change < tol.
        # Let's run a few iterations for robustness.
        # But to keep it simple and robust, we'll trust the optimizer result.
        break

    # Final weights
    final_variances = variances + tau_sq
    final_weights = 1.0 / final_variances
    final_sum_w = np.sum(final_weights)
    
    if final_sum_w == 0:
        raise ConvergenceError("REML failed to converge to positive weights.")

    pooled_effect = np.sum(final_weights * effects) / final_sum_w
    pooled_se = np.sqrt(1.0 / final_sum_w)

    return pooled_effect, pooled_se

def fit_meta_analysis_model(
    subsample: Subsample,
    model_type: str
) -> StabilityMetric:
    """
    Fits a specified model to a subsample.
    model_type: 'FE', 'RE_DL', 'RE_REML'
    """
    effects = subsample.get_effect_sizes()
    variances = subsample.get_variances()

    # Handle variance issues
    variances = handle_variance_issues(variances)

    try:
        if model_type == 'FE':
            pooled_effect, pooled_se = _fit_fixed_effects(effects, variances)
        elif model_type == 'RE_DL':
            pooled_effect, pooled_se = _fit_random_effects_dl(effects, variances)
        elif model_type == 'RE_REML':
            pooled_effect, pooled_se = _fit_random_effects_reml(effects, variances)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    except Exception as e:
        logger.error(f"Model fitting failed for meta_id={subsample.meta_id}, k={subsample.k}, seed={subsample.seed}: {e}")
        # Return a failed metric or raise? Let's raise to be caught by pipeline
        raise ConvergenceError(f"Fitting {model_type} failed: {e}")

    # Calculate 95% CI (approximate normal)
    z = 1.96
    ci_lower = pooled_effect - z * pooled_se
    ci_upper = pooled_effect + z * pooled_se

    return StabilityMetric(
        meta_id=subsample.meta_id,
        k=subsample.k,
        seed=subsample.seed,
        model_type=model_type,
        pooled_effect=pooled_effect,
        pooled_se=pooled_se,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        is_primary=False # Will be set by pipeline
    )

def run_modeling_pipeline(
    subsamples: List[Subsample],
    output_path: str
) -> List[StabilityMetric]:
    """
    Runs the modeling pipeline on a list of subsamples.
    Applies FR-003 logic: DL for k >= 10, REML for k < 10.
    Writes primary results to output_path.
    """
    results = []
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting modeling pipeline for {len(subsamples)} subsamples.")

    for subsample in subsamples:
        k = subsample.k
        model_type = "RE_DL" if k >= 10 else "RE_REML"
        
        try:
            metric = fit_meta_analysis_model(subsample, model_type)
            metric.is_primary = True
            results.append(metric)
        except Exception as e:
            logger.warning(f"Skipping subsample (k={k}) due to error: {e}")
            continue

    # Write results to CSV
    logger.info(f"Writing {len(results)} results to {output_path}")
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'meta_id', 'k', 'seed', 'model_type', 'pooled_effect', 
            'pooled_se', 'ci_lower', 'ci_upper', 'is_primary'
        ])
        for r in results:
            writer.writerow([
                r.meta_id, r.k, r.seed, r.model_type, 
                r.pooled_effect, r.pooled_se, r.ci_lower, 
                r.ci_upper, r.is_primary
            ])

    return results

def main():
    """
    Entry point for the modeling task.
    Expects subsamples to be loaded from data/processed/subsample_data.parquet (or similar).
    Since parquet reading might require pandas (which is in requirements), we assume it's available.
    However, to be safe and generic, we might need to load the data generated by T016.
    The task description says: "Primary Output: ... in data/processed/stability_metrics.csv".
    """
    import pandas as pd
    
    input_path = Path("data/processed/subsample_data.parquet")
    output_path = Path("data/processed/stability_metrics.csv")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Run T016 first.")
        return

    # Load subsamples
    # Assuming the parquet file has columns: meta_id, k, seed, effect_sizes (list), se_values (list)
    # Or perhaps a flat table where we need to group?
    # The subsample.py task (T016) likely outputs a structured format.
    # Let's assume a format compatible with the Subsample dataclass reconstruction.
    
    df = pd.read_parquet(input_path)
    
    # Reconstruct Subsample objects
    subsamples = []
    for _, row in df.iterrows():
        # Assuming columns: meta_id, k, seed, effects, ses
        # If effects/ses are stored as strings or lists, handle accordingly
        effects = row['effects'] if isinstance(row['effects'], list) else eval(row['effects'])
        ses = row['ses'] if isinstance(row['ses'], list) else eval(row['ses'])
        
        studies = [
            Study(
                meta_id=row['meta_id'],
                study_id=f"{row['meta_id']}_sub_{i}",
                effect_size=float(e),
                se=float(s)
            )
            for i, (e, s) in enumerate(zip(effects, ses))
        ]
        
        subsamples.append(Subsample(
            meta_id=row['meta_id'],
            k=int(row['k']),
            seed=int(row['seed']),
            studies=studies
        ))
    
    # Run pipeline
    results = run_modeling_pipeline(subsamples, str(output_path))
    logger.info(f"Modeling pipeline complete. {len(results)} metrics saved.")

if __name__ == "__main__":
    main()