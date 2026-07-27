"""
Deterministic Synthetic Data Generator for Pipeline Validation.

This module generates synthetic metagenomic count data and sleep architecture metrics
strictly for pipeline logic validation. It does NOT simulate real biological distributions
for scientific claims.

Constitution Principle I (Reproducibility): All generation is seeded and deterministic.
The checksum of this script is recorded in the manifest to ensure the exact code
used for generation can be identified.
"""
import os
import sys
import json
import random
import hashlib
import argparse
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

# Ensure we can import from the project root if running as script
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def set_seeds(seed: int = 42):
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def calculate_script_checksum(script_path: str) -> str:
    """Calculate SHA-256 checksum of the generator script itself."""
    path = Path(script_path)
    if not path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    with open(path, "rb") as f:
        content = f.read()
    return hashlib.sha256(content).hexdigest()

def check_real_data_flag_and_fail(args: argparse.Namespace):
    """
    Enforce Constitution Principle: No synthetic fallback for real data runs.
    If --real-data is set, this function ensures we do NOT generate synthetic data.
    """
    if args.mode == "real" or args.real_data:
        # In a real run, we expect real data to be present.
        # If this generator is called in 'real' mode, it's a logic error.
        raise SystemExit(
            "CRITICAL: Synthetic data generator invoked in 'real-data' mode. "
            "This violates the 'No Synthetic Fallback' rule. "
            "Pipeline halted to prevent fabrication."
        )

def load_required_variables(config_path: str = None):
    """
    Load the required variables (taxa and sleep metrics) from the config.
    Used to ensure the synthetic data matches the schema expectations.
    """
    if config_path is None:
        config_path = PROJECT_ROOT / "data" / "config" / "required_variables.yaml"
    
    # Fallback if file doesn't exist (for pure unit testing of generator logic)
    if not os.path.exists(config_path):
        # Return a minimal set for validation if config is missing
        return {
            "predictors": ["Bacteroides", "Firmicutes", "Actinobacteria", "Proteobacteria"],
            "outcomes": ["SWS duration", "REM duration", "Sleep efficiency"]
        }
    
    # Real implementation would load YAML
    # For this generator, we simulate the structure if the file is missing or empty
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config.get("required_variables", config)
    except ImportError:
        # Fallback if yaml not installed (should be in T002)
        return {
            "predictors": ["Bacteroides", "Firmicutes", "Actinobacteria", "Proteobacteria"],
            "outcomes": ["SWS duration", "REM duration", "Sleep efficiency"]
        }
    except Exception:
        return {
            "predictors": ["Bacteroides", "Firmicutes", "Actinobacteria", "Proteobacteria"],
            "outcomes": ["SWS duration", "REM duration", "Sleep efficiency"]
        }

def generate_metagenomic_counts(n_subjects: int, taxa: list, seed: int) -> pd.DataFrame:
    """
    Generate synthetic metagenomic count data.
    Values are non-negative integers, simulating raw read counts.
    """
    set_seeds(seed)
    
    data = {}
    for taxon in taxa:
        # Simulate counts with a log-normal distribution (typical for microbiome)
        # Mean ~ 1000, Sigma ~ 1.5
        counts = np.random.lognormal(mean=6.9, sigma=1.5, size=n_subjects)
        # Add some zero-inflation (common in sparse data)
        zero_mask = np.random.random(n_subjects) < 0.15
        counts[zero_mask] = 0
        data[taxon] = np.round(counts).astype(int)
    
    df = pd.DataFrame(data)
    df["subject_id"] = [f"SUBJ_{i:04d}" for i in range(n_subjects)]
    return df

def generate_sleep_metrics(n_subjects: int, outcomes: list, seed: int) -> pd.DataFrame:
    """
    Generate synthetic sleep architecture metrics.
    Values are continuous, representing hours or percentages.
    """
    set_seeds(seed + 1) # Different seed offset to avoid perfect correlation
    
    data = {}
    for outcome in outcomes:
        if "duration" in outcome.lower():
            # Hours: Normal distribution, mean ~ 1.5-2.0, std ~ 0.5
            values = np.random.normal(loc=1.8, scale=0.4, size=n_subjects)
            # Clamp to positive
            values = np.clip(values, 0.1, 4.0)
        elif "efficiency" in outcome.lower():
            # Percentage: Normal distribution, mean ~ 85, std ~ 5
            values = np.random.normal(loc=85.0, scale=5.0, size=n_subjects)
            values = np.clip(values, 50.0, 100.0)
        else:
            # Generic
            values = np.random.normal(loc=50.0, scale=10.0, size=n_subjects)
        
        data[outcome] = values
    
    df = pd.DataFrame(data)
    df["subject_id"] = [f"SUBJ_{i:04d}" for i in range(n_subjects)]
    return df

def generate_synthetic_dataset(n_subjects: int = 100, seed: int = 42) -> dict:
    """
    Generate a complete synthetic dataset with metagenomic counts and sleep metrics.
    Returns a dictionary with the two DataFrames.
    """
    config = load_required_variables()
    predictors = config.get("predictors", [])
    outcomes = config.get("outcomes", [])
    
    if not predictors or not outcomes:
        raise ValueError("Required variables not found in config. Cannot generate synthetic data.")
    
    metagenomic_df = generate_metagenomic_counts(n_subjects, predictors, seed)
    sleep_df = generate_sleep_metrics(n_subjects, outcomes, seed)
    
    # Merge on subject_id
    merged_df = pd.merge(metagenomic_df, sleep_df, on="subject_id")
    
    return {
        "metagenomic": metagenomic_df,
        "sleep": sleep_df,
        "merged": merged_df,
        "predictors": predictors,
        "outcomes": outcomes
    }

def generate_synthetic_manifest(project_id: str, output_path: str, 
                                script_path: str, seed: int, 
                                artifacts: list = None):
    """
    Generate a synthetic data manifest log (NOT a Chain of Custody log).
    This satisfies Constitution Principle I for synthetic data validation only.
    
    Args:
        project_id: Project identifier
        output_path: Path to write the manifest JSON
        script_path: Path to the generator script (to checksum)
        seed: The seed used
        artifacts: List of dicts with 'path' and 'checksum' for generated files
    """
    checksum = calculate_script_checksum(script_path)
    
    # Determine schema version based on mode
    if mode == 'synthetic':
        schema_version = 'schema_v1_synthetic'
        coc_log = None
        dataset_type = 'synthetic'
    else:
        # If someone tries to call this for real data, it's a logic error in this generator
        raise ValueError("This generator cannot produce real data manifests.")

    manifest = {
        "project_id": project_id,
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "generator_script": script_path,
        "generator_checksum": checksum,
        "random_seed": seed,
        "schema_type": "schema_v1_synthetic",
        "chain_of_custody_log": None, # Explicitly null for synthetic
        "notes": "This is a synthetic dataset for pipeline validation. "
                 "No biological samples were used. Results are for engine verification only.",
        "data_artifacts": artifacts or []
    }
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Manifest written to {output_path}")
    return manifest

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data for pipeline validation.")
    parser.add_argument("--mode", type=str, default="synthetic", 
                        choices=["synthetic", "real"], 
                        help="Mode of operation. 'real' will fail if this script is called.")
    parser.add_argument("--real-data", action="store_true", 
                        help="Flag indicating real data is expected (triggers failure if synthetic gen is used).")
    parser.add_argument("--output-dir", type=str, default="data/raw",
                        help="Directory to output generated files.")
    parser.add_argument("--n-subjects", type=int, default=100,
                        help="Number of synthetic subjects.")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility.")
    
    args = parser.parse_args()
    
    # Safety check: Fail loudly if real data mode is requested
    check_real_data_flag_and_fail(args)
    
    # Setup paths
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    print(f"Generating synthetic data with N={args.n_subjects}, seed={args.seed}...")
    data = generate_synthetic_dataset(n_subjects=args.n_subjects, seed=args.seed)
    
    # Save artifacts
    csv_path = output_dir / "synthetic_data.csv"
    data["merged"].to_csv(csv_path, index=False)
    
    # Calculate checksums for artifacts
    artifact_list = []
    if csv_path.exists():
        with open(csv_path, "rb") as f:
            checksum = hashlib.sha256(f.read()).hexdigest()
        artifact_list.append({
            "path": str(csv_path.relative_to(PROJECT_ROOT)),
            "checksum": checksum,
            "size_bytes": csv_path.stat().st_size
        })
    
    # Generate Manifest (T006d requirement)
    manifest_path = PROJECT_ROOT / "data" / "metadata" / "synthetic_data_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    generator_script_path = os.path.abspath(__file__)
    manifest = generate_synthetic_manifest(
        project_id="PROJ-340-investigating-the-correlation-between-gu",
        output_path=str(manifest_path),
        script_path=generator_script_path,
        seed=args.seed,
        artifacts=artifact_list
    )
    
    print(f"Synthetic data written to: {csv_path}")
    print(f"Manifest written to: {manifest_path}")
    print(f"Script Checksum: {manifest['generator_checksum']}")

if __name__ == "__main__":
    main()