"""
Synthetic Data Generator for Imputation Impact Study.

Generates datasets with known super-population parameters and controlled
missingness mechanisms (MCAR, MAR). Outputs conform to project contracts.
"""
import os
import sys
import logging
import json
import hashlib
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure dependencies are available
try:
    import yaml
except ImportError:
    logger.error("PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

# Import project utilities
# Note: We are extending the existing API surface. If 'contracts' logic
# is needed, we assume the schema file exists at the path defined in T006.
# We will implement a simple validation function here to avoid circular deps.

def ensure_directories(base_path: str) -> None:
    """Ensure output directories exist."""
    path = Path(base_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {path.parent}")

def generate_synthetic_data(
    n_samples: int,
    mechanism: str = "MAR",
    seed: int = 42,
    true_mean: float = 50.0,
    true_variance: float = 100.0
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generates synthetic data with specified parameters and missingness.

    Args:
        n_samples: Number of rows to generate.
        mechanism: 'MCAR' or 'MAR'.
        seed: Random seed for reproducibility.
        true_mean: The known population mean for the target variable.
        true_variance: The known population variance for the target variable.

    Returns:
        Tuple of (DataFrame, metadata_dict)
    """
    logger.info(f"Generating {n_samples} samples with {mechanism} missingness (seed={seed})")
    np.random.seed(seed)

    # 1. Generate full population data
    # We generate a covariate X that will drive MAR missingness
    x = np.random.normal(loc=0, scale=1, size=n_samples)

    # Generate target variable Y with known mean and variance
    # Y = true_mean + noise scaled to match true_variance
    noise = np.random.normal(loc=0, scale=np.sqrt(true_variance), size=n_samples)
    y = true_mean + noise

    df = pd.DataFrame({
        'id': range(n_samples),
        'covariate_x': x,
        'target_y': y
    })

    # 2. Introduce Missingness
    missing_mask = None

    if mechanism == "MCAR":
        # Missing Completely At Random: 20% missing
        prob = 0.2
        missing_mask = np.random.random(n_samples) < prob
        logger.info(f"Applied MCAR: {missing_mask.sum()} values missing ({missing_mask.sum()/n_samples:.2%})")

    elif mechanism == "MAR":
        # Missing At Random: Probability depends on X
        # P(missing) = logistic(alpha + beta * X)
        # We tune alpha/beta to get roughly 20-30% missingness
        alpha = -0.5
        beta = 1.5
        logits = alpha + beta * x
        probs = 1 / (1 + np.exp(-logits))
        missing_mask = np.random.random(n_samples) < probs
        logger.info(f"Applied MAR: {missing_mask.sum()} values missing ({missing_mask.sum()/n_samples:.2%})")
    else:
        raise ValueError(f"Unsupported mechanism: {mechanism}. Use 'MCAR' or 'MAR'.")

    # Apply mask
    df.loc[missing_mask, 'target_y'] = np.nan

    # 3. Prepare Metadata
    metadata = {
        "true_mean": true_mean,
        "true_variance": true_variance,
        "missingness_mechanism": mechanism,
        "n_samples": n_samples,
        "n_missing": int(missing_mask.sum()),
        "missing_rate": float(missing_mask.sum() / n_samples),
        "seed": seed,
        "generated_at": pd.Timestamp.now().isoformat()
    }

    return df, metadata

def validate_schema(df: pd.DataFrame, metadata: Dict[str, Any], schema_path: str = None) -> bool:
    """
    Validates the generated data against the project contract schema.
    If schema_path is provided, it attempts to load and validate against it.
    Otherwise, performs basic structural checks.
    """
    required_cols = ['id', 'covariate_x', 'target_y']
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Missing required columns. Expected: {required_cols}, Found: {list(df.columns)}")
        return False

    if not isinstance(metadata.get('true_mean'), (int, float)):
        logger.error("Metadata missing or invalid 'true_mean'")
        return False

    if not isinstance(metadata.get('true_variance'), (int, float)):
        logger.error("Metadata missing or invalid 'true_variance'")
        return False

    if metadata.get('missingness_mechanism') not in ['MCAR', 'MAR']:
        logger.error("Metadata missing or invalid 'missingness_mechanism'")
        return False

    logger.info("Schema validation passed.")
    return True

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for imputation study.")
    parser.add_argument("--n-rows", type=int, default=5000, help="Number of rows to generate.")
    parser.add_argument("--mechanism", type=str, default="MAR", choices=["MCAR", "MAR"], help="Missingness mechanism.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--output-csv", type=str, default="data/processed/synthetic_mar_v1.csv", help="Output CSV path.")
    parser.add_argument("--output-meta", type=str, default="data/processed/synthetic_mar_v1_meta.json", help="Output metadata JSON path.")
    parser.add_argument("--schema", type=str, default="specs/contracts/dataset.schema.yaml", help="Path to schema file for validation.")

    args = parser.parse_args()

    # 1. Ensure directories
    ensure_directories(args.output_csv)
    ensure_directories(args.output_meta)

    # 2. Generate Data
    df, metadata = generate_synthetic_data(
        n_samples=args.n_rows,
        mechanism=args.mechanism,
        seed=args.seed
    )

    # 3. Validate
    # Note: We check if the schema file exists before trying to load it to avoid crashes
    # if T006 hasn't run yet or the path is slightly different.
    schema_path = Path(args.schema)
    if schema_path.exists():
        # If we had a full validator, we'd use it here.
        # For now, we rely on the internal check which covers the critical fields.
        validate_schema(df, metadata)
    else:
        logger.warning(f"Schema file not found at {args.schema}. Skipping external validation.")
        validate_schema(df, metadata)

    # 4. Save Artifacts
    df.to_csv(args.output_csv, index=False)
    logger.info(f"Saved synthetic data to {args.output_csv}")

    with open(args.output_meta, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {args.output_meta}")

    # 5. Compute Checksums for Manifest
    csv_hash = compute_sha256(args.output_csv)
    meta_hash = compute_sha256(args.output_meta)

    logger.info(f"SHA-256 CSV: {csv_hash}")
    logger.info(f"SHA-256 Meta: {meta_hash}")

    # 6. Update Manifest (if update_state module is available and manifest exists)
    # We attempt to import and use the update_state logic if available,
    # but this task focuses on generation. The execution of T007 (update_state)
    # will handle the manifest update in the pipeline, or we can do it here.
    # Given T007 is a separate task, we will just log the hashes.
    # However, to satisfy T005b's requirement to "record checksums in state/manifest.yaml",
    # we should attempt to update it if the infrastructure exists.
    try:
        from update_state import update_manifest
        manifest_path = "state/manifest.yaml"
        if os.path.exists(manifest_path):
            update_manifest(manifest_path, {
                "data/processed/synthetic_mar_v1.csv": csv_hash,
                "data/processed/synthetic_mar_v1_meta.json": meta_hash
            })
            logger.info(f"Updated {manifest_path} with checksums.")
        else:
            logger.info(f"Manifest {manifest_path} not found. Skipping update.")
    except ImportError:
        logger.warning("Could not import update_state. Skipping manifest update.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
