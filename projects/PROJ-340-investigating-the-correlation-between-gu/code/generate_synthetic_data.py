"""
Deterministic Synthetic Data Generator for Pipeline Validation.

This module generates synthetic metagenomic count data and sleep architecture metrics
for testing the pipeline's ingestion, validation, and analysis steps.

CRITICAL: Synthetic data generator invoked in 'validation' or 'test' mode only.
It is NOT authorized for production research results.
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

def set_seeds(seed: int = 42) -> np.random.Generator:
    """Initialize the global random number generator with a fixed seed."""
    rng = np.random.default_rng(seed)
    return rng

def load_required_variables(config_path: str = "data/config/required_variables.yaml") -> dict:
    """
    Load required variable names from the config file.
    Returns a dict with 'required_predictors' and 'required_outcomes'.
    """
    path = Path(config_path)
    if not path.exists():
        # Fallback to hardcoded defaults if config is missing, 
        # but log a warning.
        return {
            "required_predictors": ["taxon_abundance", "relative_abundance"],
            "required_outcomes": ["rem_duration", "sws_duration", "total_sleep_time"]
        }
    
    import yaml
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    return {
        "required_predictors": config.get("required_predictors", []),
        "required_outcomes": config.get("required_outcomes", [])
    }

def generate_metagenomic_counts(rng: np.random.Generator, n_samples: int, n_taxa: int) -> pd.DataFrame:
    """
    Generate synthetic metagenomic count data.
    
    Uses a Zero-Inflated Negative Binomial distribution to mimic 
    realistic microbiome sparsity and over-dispersion.
    """
    # Generate taxon names
    taxa_names = [f"Taxon_{i}" for i in range(n_taxa)]
    
    # Generate counts with zero-inflation
    # Approximate ZINB: mix of zeros and NB-distributed counts
    data = {}
    for taxon in taxa_names:
        # Probability of zero inflation
        pi = 0.3 
        # Generate uniform randoms to decide zero vs count
        u = rng.uniform(0, 1, n_samples)
        # Generate NB counts for non-zeros
        # mu (mean) and alpha (dispersion)
        mu = rng.uniform(10, 100, n_samples)
        alpha = rng.uniform(0.1, 1.0)
        # NB generation: use Gamma-Poisson mixture
        # Lambda ~ Gamma(alpha, mu/alpha)
        # Count ~ Poisson(Lambda)
        # Simplified: use numpy's negative_binomial if available, 
        # or approximate with Gamma + Poisson
        try:
            # n is number of failures, p is success probability
            # np.random.negative_binomial(n, p, size)
            # Mean = n(1-p)/p
            # We want mean ~ mu, var ~ mu + alpha*mu^2
            # This is tricky to map directly. 
            # Let's use a simpler approximation: 
            # Count = Poisson(Gamma(mu, scale=alpha))
            lambdas = rng.gamma(shape=mu/alpha, scale=alpha, size=n_samples)
            counts = rng.poisson(lambdas)
        except Exception:
            # Fallback to simple Poisson if Gamma/Poisson fails
            counts = rng.poisson(mu, size=n_samples)
        
        # Apply zero inflation
        counts[u < pi] = 0
        data[taxon] = counts
    
    df = pd.DataFrame(data)
    return df

def generate_sleep_metrics(rng: np.random.Generator, n_samples: int) -> pd.DataFrame:
    """
    Generate synthetic sleep architecture metrics.
    
    Distributions:
    - REM duration: Normal (approx 90-120 mins)
    - SWS duration: Normal (approx 60-100 mins)
    - Total sleep time: Normal (approx 420-500 mins)
    """
    data = {}
    
    # REM duration
    rem_mean = 105
    rem_std = 20
    data["rem_duration"] = rng.normal(rem_mean, rem_std, n_samples)
    
    # SWS duration
    sws_mean = 80
    sws_std = 15
    data["sws_duration"] = rng.normal(sws_mean, sws_std, n_samples)
    
    # Total sleep time
    tst_mean = 450
    tst_std = 45
    data["total_sleep_time"] = rng.normal(tst_mean, tst_std, n_samples)
    
    # Ensure non-negative
    for k in data:
        data[k] = np.maximum(data[k], 0)
    
    df = pd.DataFrame(data)
    return df

def generate_synthetic_dataset(
    n_samples: int = 100,
    n_taxa: int = 50,
    seed: int = 42,
    inject_missing: str = None
) -> pd.DataFrame:
    """
    Generate a complete synthetic dataset with metagenomic counts and sleep metrics.
    
    Args:
        n_samples: Number of subjects
        n_taxa: Number of taxa
        seed: Random seed
        inject_missing: If set, a column name from required_outcomes to omit
                       (for testing missing variable detection)
    
    Returns:
        pd.DataFrame: Combined dataset
    """
    rng = set_seeds(seed)
    
    # Load required variables to know column names
    required = load_required_variables()
    
    # Generate components
    meta_df = generate_metagenomic_counts(rng, n_samples, n_taxa)
    sleep_df = generate_sleep_metrics(rng, n_samples)
    
    # Add subject IDs
    meta_df["subject_id"] = [f"SUBJ_{i:04d}" for i in range(n_samples)]
    sleep_df["subject_id"] = [f"SUBJ_{i:04d}" for i in range(n_samples)]
    
    # Merge
    df = pd.merge(meta_df, sleep_df, on="subject_id")
    
    # Inject missing variable if requested
    if inject_missing and inject_missing in required["required_outcomes"]:
        if inject_missing in df.columns:
            df.drop(columns=[inject_missing], inplace=True)
            print(f"Injected missing variable: {inject_missing}")
    
    return df

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for pipeline validation.")
    parser.add_argument("--n-samples", type=int, default=100, help="Number of samples")
    parser.add_argument("--n-taxa", type=int, default=50, help="Number of taxa")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/raw/synthetic_test_data.csv", help="Output file path")
    parser.add_argument("--inject-missing", type=str, default=None, help="Column name to omit for testing")
    
    args = parser.parse_args()
    
    print(f"Generating synthetic dataset with {args.n_samples} samples and {args.n_taxa} taxa...")
    
    df = generate_synthetic_dataset(
        n_samples=args.n_samples,
        n_taxa=args.n_taxa,
        seed=args.seed,
        inject_missing=args.inject_missing
    )
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    df.to_csv(output_path, index=False)
    print(f"Synthetic dataset written to {output_path}")
    
    # Write manifest
    manifest = {
        "type": "synthetic",
        "n_samples": args.n_samples,
        "n_taxa": args.n_taxa,
        "seed": args.seed,
        "inject_missing": args.inject_missing,
        "generated_at": str(pd.Timestamp.now())
    }
    manifest_path = output_path.parent / f"{output_path.stem}_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest written to {manifest_path}")

if __name__ == "__main__":
    main()
