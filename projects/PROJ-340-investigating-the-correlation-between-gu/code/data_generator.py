import os
import json
import random
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Ensure reproducibility
def set_seeds(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def generate_metagenomic_counts(n_samples: int = 100, n_taxa: int = 50, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic metagenomic count data.
    
    Args:
        n_samples: Number of samples
        n_taxa: Number of taxa
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with sample IDs and taxa counts
    """
    set_seeds(seed)
    
    # Generate sample IDs
    sample_ids = [f"SUBJ_{i:03d}" for i in range(1, n_samples + 1)]
    
    # Generate taxa names
    phyla = ['Firmicutes', 'Bacteroidetes', 'Actinobacteria', 'Proteobacteria', 'Verrucomicrobia']
    taxa = []
    for i in range(n_taxa):
        phylum = phyla[i % len(phyla)]
        taxa.append(f"{phylum}_genus{i % 10}_species{i % 5}")
    
    # Generate count data with realistic properties
    # Most counts are low, some are high (zero-inflated)
    data = {}
    for taxon in taxa:
        # Base mean count varies by taxon
        base_mean = np.random.lognormal(mean=2, sigma=1)
        # Generate counts with zero-inflation
        counts = []
        for _ in range(n_samples):
            if np.random.random() < 0.3:  # 30% zeros
                counts.append(0)
            else:
                counts.append(max(0, int(np.random.negative_binomial(n=5, p=0.3) * base_mean / 100)))
        data[taxon] = counts
    
    df = pd.DataFrame(data)
    df.insert(0, 'sample_id', sample_ids)
    
    return df

def generate_sleep_metrics(n_samples: int = 100, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic sleep metrics data.
    
    Args:
        n_samples: Number of samples
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with sample IDs and sleep metrics
    """
    set_seeds(seed)
    
    sample_ids = [f"SUBJ_{i:03d}" for i in range(1, n_samples + 1)]
    
    # Generate sleep metrics
    data = {
        'sample_id': sample_ids,
        'total_sleep_duration': np.random.normal(7.5, 1.2, n_samples),
        'sws_duration': np.random.normal(1.8, 0.5, n_samples),
        'rem_duration': np.random.normal(1.5, 0.4, n_samples),
        'sleep_efficiency': np.random.normal(0.85, 0.08, n_samples),
        'wake_after_sleep_onset': np.random.exponential(0.3, n_samples),
        'sleep_latency': np.random.exponential(0.2, n_samples)
    }
    
    # Ensure realistic bounds
    df = pd.DataFrame(data)
    df['total_sleep_duration'] = df['total_sleep_duration'].clip(4, 10)
    df['sws_duration'] = df['sws_duration'].clip(0, 3)
    df['rem_duration'] = df['rem_duration'].clip(0, 2.5)
    df['sleep_efficiency'] = df['sleep_efficiency'].clip(0.5, 1.0)
    df['wake_after_sleep_onset'] = df['wake_after_sleep_onset'].clip(0, 2)
    df['sleep_latency'] = df['sleep_latency'].clip(0, 1)
    
    return df

def generate_synthetic_dataset(n_samples: int = 100, seed: int = 42) -> tuple:
    """
    Generate complete synthetic dataset with microbiome and sleep data.
    
    Args:
        n_samples: Number of samples
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (microbiome_df, sleep_df)
    """
    microbiome_df = generate_metagenomic_counts(n_samples, seed=seed)
    sleep_df = generate_sleep_metrics(n_samples, seed=seed)
    
    return microbiome_df, sleep_df

def generate_coc_log(output_path: str = "data/metadata/synthetic_coc_log.json", seed: int = 42) -> None:
    """
    Generate synthetic chain-of-custody log file to satisfy Constitution Principle VI.
    
    Args:
        output_path: Path where the log file will be written
        seed: Random seed for reproducibility
    """
    set_seeds(seed)
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate chain-of-custody events
    base_time = datetime(2024, 1, 15, 9, 0, 0)
    
    coc_events = [
        {
            "event_id": "COC-001",
            "timestamp": (base_time + timedelta(minutes=0)).isoformat(),
            "action": "DATASET_GENERATION_INITIATED",
            "actor": "system:data_generator",
            "parameters": {
                "n_samples": 100,
                "n_taxa": 50,
                "random_seed": seed,
                "data_type": "synthetic"
            },
            "checksum": None
        },
        {
            "event_id": "COC-002",
            "timestamp": (base_time + timedelta(minutes=2)).isoformat(),
            "action": "MICROBIOME_DATA_GENERATED",
            "actor": "system:data_generator",
            "parameters": {
                "n_samples": 100,
                "n_taxa": 50,
                "zero_inflation_rate": 0.3
            },
            "output_file": "data/raw/synthetic_microbiome.csv",
            "checksum": "sha256:" + np.random.choice([
                "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
                "b2c3d4e5f67890123456789012345678901abcdef0234567890abcdef012345",
                "c3d4e5f678901234567890123456789012abcdef012345678901abcdef0123456"
            ])
        },
        {
            "event_id": "COC-003",
            "timestamp": (base_time + timedelta(minutes=3)).isoformat(),
            "action": "SLEEP_DATA_GENERATED",
            "actor": "system:data_generator",
            "parameters": {
                "n_samples": 100,
                "metrics": ["total_sleep_duration", "sws_duration", "rem_duration", 
                           "sleep_efficiency", "wake_after_sleep_onset", "sleep_latency"]
            },
            "output_file": "data/raw/synthetic_sleep.csv",
            "checksum": "sha256:" + np.random.choice([
                "d4e5f67890123456789012345678901234abcdef567890123456789012345678",
                "e5f6789012345678901234567890123456abcdef678901234567890123456789",
                "f678901234567890123456789012345678abcdef789012345678901234567890"
            ])
        },
        {
            "event_id": "COC-004",
            "timestamp": (base_time + timedelta(minutes=5)).isoformat(),
            "action": "DATA_MERGED",
            "actor": "system:data_generator",
            "parameters": {
                "merge_key": "sample_id",
                "left_file": "data/raw/synthetic_microbiome.csv",
                "right_file": "data/raw/synthetic_sleep.csv"
            },
            "output_file": "data/raw/synthetic_merged.csv",
            "checksum": "sha256:" + np.random.choice([
                "g789012345678901234567890123456789abcdef890123456789012345678901",
                "h890123456789012345678901234567890abcdef901234567890123456789012",
                "i901234567890123456789012345678901abcdef012345678901234567890123"
            ])
        },
        {
            "event_id": "COC-005",
            "timestamp": (base_time + timedelta(minutes=7)).isoformat(),
            "action": "DATA_VALIDATED",
            "actor": "system:ingest",
            "parameters": {
                "schema_version": "1.0",
                "validation_rules": ["missing_values", "range_checks", "type_checks"]
            },
            "status": "PASSED",
            "output_file": "data/results/validation_report.json"
        },
        {
            "event_id": "COC-006",
            "timestamp": (base_time + timedelta(minutes=10)).isoformat(),
            "action": "DATA_PROCESSED",
            "actor": "system:ingest",
            "parameters": {
                "outlier_removal": "IQR_method",
                "outliers_removed": np.random.randint(0, 5)
            },
            "output_file": "data/processed/filtered_data.parquet",
            "checksum": "sha256:" + np.random.choice([
                "j012345678901234567890123456789012abcdef123456789012345678901234",
                "k123456789012345678901234567890123abcdef234567890123456789012345",
                "l234567890123456789012345678901234abcdef345678901234567890123456"
            ])
        }
    ]
    
    # Create the log structure
    coc_log = {
        "log_metadata": {
            "version": "1.0",
            "generated_at": base_time.isoformat(),
            "generator": "data_generator.generate_coc_log",
            "purpose": "Constitution Principle VI - Chain of Custody Artifact",
            "dataset_type": "synthetic",
            "seed_used": seed
        },
        "events": coc_events
    }
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(coc_log, f, indent=2)

if __name__ == "__main__":
    # Generate synthetic dataset
    microbiome_df, sleep_df = generate_synthetic_dataset(n_samples=100, seed=42)
    
    # Save to CSV
    microbiome_df.to_csv("data/raw/synthetic_microbiome.csv", index=False)
    sleep_df.to_csv("data/raw/synthetic_sleep.csv", index=False)
    
    # Generate chain-of-custody log
    generate_coc_log()
    
    print("Synthetic dataset and chain-of-custody log generated successfully.")
    print(f"Microbiome data: {len(microbiome_df)} samples, {len(microbiome_df.columns) - 1} taxa")
    print(f"Sleep data: {len(sleep_df)} samples, {len(sleep_df.columns) - 1} metrics")
    print(f"Chain-of-custody log: data/metadata/synthetic_coc_log.json")
