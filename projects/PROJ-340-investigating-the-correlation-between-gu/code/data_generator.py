import os
import json
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Constants for reproducibility
DEFAULT_SEED = 42
SYNTHETIC_DATA_DIR = Path("data/processed")
SYNTHETIC_MANIFEST_PATH = Path("data/metadata/synthetic_data_manifest.json")

def set_seeds(seed: int = DEFAULT_SEED) -> None:
    """
    Set random seeds for reproducibility across all libraries.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def generate_metagenomic_counts(
    n_subjects: int,
    n_taxa: int,
    zero_inflation_rate: float = 0.35,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic metagenomic count data.

    Args:
        n_subjects: Number of subjects (rows)
        n_taxa: Number of taxa (columns)
        zero_inflation_rate: Proportion of zeros in the data
        seed: Random seed for reproducibility

    Returns:
        DataFrame with taxa counts
    """
    if seed is not None:
        set_seeds(seed)

    # Generate base counts (negative binomial-like distribution)
    # Using a mixture of low and high abundance taxa
    base_abundance = np.random.lognormal(mean=1.0, sigma=1.5, size=n_taxa)
    counts = np.random.negative_binomial(n=2, p=0.3, size=(n_subjects, n_taxa))
    counts = counts * base_abundance

    # Apply zero inflation
    mask = np.random.random((n_subjects, n_taxa)) < zero_inflation_rate
    counts[mask] = 0

    # Ensure non-negative integers
    counts = np.maximum(counts, 0).astype(int)

    # Create DataFrame with taxon names
    taxon_names = [f"Taxon_{i}" for i in range(n_taxa)]
    df = pd.DataFrame(counts, columns=taxon_names)
    df['subject_id'] = range(n_subjects)
    df = df[['subject_id'] + taxon_names]

    return df

def generate_sleep_metrics(
    n_subjects: int,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic sleep architecture metrics.

    Args:
        n_subjects: Number of subjects
        seed: Random seed for reproducibility

    Returns:
        DataFrame with sleep metrics
    """
    if seed is not None:
        set_seeds(seed)

    data = {
        'subject_id': range(n_subjects),
        'total_sleep_time': np.random.normal(loc=420, scale=45, size=n_subjects),  # minutes
        'sleep_latency': np.random.normal(loc=15, scale=10, size=n_subjects),      # minutes
        'sws_duration': np.random.normal(loc=90, scale=20, size=n_subjects),       # minutes (Slow Wave Sleep)
        'rem_duration': np.random.normal(loc=100, scale=25, size=n_subjects),      # minutes (REM)
        'wake_after_sleep_onset': np.random.normal(loc=30, scale=15, size=n_subjects), # minutes
        'sleep_efficiency': np.random.normal(loc=0.85, scale=0.08, size=n_subjects)  # ratio
    }

    # Ensure positive values and reasonable bounds
    df = pd.DataFrame(data)
    df['total_sleep_time'] = np.clip(df['total_sleep_time'], 240, 540)
    df['sleep_latency'] = np.clip(df['sleep_latency'], 0, 60)
    df['sws_duration'] = np.clip(df['sws_duration'], 30, 150)
    df['rem_duration'] = np.clip(df['rem_duration'], 40, 180)
    df['wake_after_sleep_onset'] = np.clip(df['wake_after_sleep_onset'], 0, 90)
    df['sleep_efficiency'] = np.clip(df['sleep_efficiency'], 0.5, 1.0)

    return df

def generate_synthetic_dataset(
    n_subjects: int = 100,
    n_taxa: int = 50,
    seed: Optional[int] = None,
    output_dir: Optional[Path] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate a complete synthetic dataset with metagenomic and sleep data.

    Args:
        n_subjects: Number of subjects
        n_taxa: Number of taxa
        seed: Random seed
        output_dir: Directory to save the dataset (optional)

    Returns:
        Tuple of (microbiome_df, sleep_df)
    """
    if seed is not None:
        set_seeds(seed)

    # Generate data
    microbiome_df = generate_metagenomic_counts(n_subjects, n_taxa, seed=seed)
    sleep_df = generate_sleep_metrics(n_subjects, seed=seed)

    # Merge on subject_id
    merged_df = pd.merge(microbiome_df, sleep_df, on='subject_id')

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        microbiome_path = output_dir / "synthetic_microbiome.csv"
        sleep_path = output_dir / "synthetic_sleep.csv"
        merged_path = output_dir / "synthetic_merged.csv"

        microbiome_df.to_csv(microbiome_path, index=False)
        sleep_df.to_csv(sleep_path, index=False)
        merged_df.to_csv(merged_path, index=False)

    return microbiome_df, sleep_df

def generate_coc_log(
    n_subjects: int,
    seed: int,
    output_path: Optional[Path] = None
) -> Dict:
    """
    Generate a synthetic data manifest log (NOT a Chain-of-Custody log for biological samples).
    This artifact satisfies Constitution Principle I for synthetic data validation only.

    Args:
        n_subjects: Number of subjects in the dataset
        seed: Random seed used for generation
        output_path: Path to save the manifest (optional)

    Returns:
        Dictionary representing the manifest
    """
    set_seeds(seed)

    manifest = {
        "type": "synthetic_data_manifest",
        "schema_version": "1.0",
        "generation_parameters": {
            "n_subjects": n_subjects,
            "seed": seed,
            "zero_inflation_rate": 0.35,
            "distribution_type": "negative_binomial_lognormal_mixture"
        },
        "provenance": {
            "generator_module": "code.data_generator",
            "generator_function": "generate_synthetic_dataset",
            "timestamp": str(pd.Timestamp.now()),
            "note": "This is a synthetic dataset for pipeline validation. No biological samples exist."
        },
        "validation_status": "pending",
        # Explicitly excluding 'Chain-of-Custody' fields as per task T006d requirements
        "exclusions": [
            "biological_sample_id",
            "collection_date",
            "collection_site",
            "storage_conditions",
            "chain_of_custody_log"
        ]
    }

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)

    return manifest

def check_real_data_flag_and_fail(real_data_mode: bool) -> None:
    """
    Assert that if real_data_mode is True, we are not generating synthetic data.
    This function raises SystemExit if real data is required but the generator is invoked.

    Args:
        real_data_mode: Boolean flag indicating if the pipeline is running in real-data mode.

    Raises:
        SystemExit: If real_data_mode is True (indicating a violation of the no-synthetic-fallback rule).
    """
    if real_data_mode:
        raise SystemExit("FABRICATION PREVENTED: Real data required but missing. The data generator should not be called in real-data mode.")

def main():
    """
    Main entry point for generating synthetic data.
    Parses command line arguments to determine mode.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic microbiome and sleep data.")
    parser.add_argument('--n-subjects', type=int, default=100, help='Number of subjects')
    parser.add_argument('--n-taxon', type=int, default=50, help='Number of taxa')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output-dir', type=str, default='data/processed', help='Output directory')
    parser.add_argument('--real-data', action='store_true', help='Flag indicating real-data mode (should not generate synthetic)')

    args = parser.parse_args()

    # T062: Enforce No-Synthetic-Fallback
    # If the --real-data flag is set, we must NOT generate synthetic data.
    # The presence of this flag implies the caller expects real data.
    # If we are in this function, we are about to generate synthetic data, which is forbidden.
    if args.real_data:
        print("ERROR: FABRICATION PREVENTED: Real data required but missing.")
        print("The data generator was invoked with --real-data flag, which is a violation of the no-synthetic-fallback rule.")
        raise SystemExit("FABRICATION PREVENTED: Real data required but missing.")

    print(f"Generating synthetic dataset with {args.n_subjects} subjects and {args.n_taxon} taxa...")
    microbiome_df, sleep_df = generate_synthetic_dataset(
        n_subjects=args.n_subjects,
        n_taxa=args.n_n_taxon,
        seed=args.seed,
        output_dir=args.output_dir
    )

    # Generate manifest
    manifest_path = Path(args.output_dir).parent / "metadata" / "synthetic_data_manifest.json"
    generate_coc_log(n_subjects=args.n_subjects, seed=args.seed, output_path=manifest_path)

    print(f"Synthetic data generated and saved to {args.output_dir}")
    print(f"Manifest saved to {manifest_path}")

if __name__ == "__main__":
    main()