"""
Synthetic Data Generator for Prototype Validation.

Generates structurally valid synthetic TPM count matrices for Arabidopsis thaliana
and associated metadata. This data is used strictly for structural validation
of the pipeline when real data is unavailable or for local development testing.

Constraints:
- NEVER writes to data/raw/
- Generates a manifest satisfying Constitution Principle VI
- Generates the metadata verification report required by T011a
"""
import os
import json
import hashlib
import datetime
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, List

# Import existing configuration
try:
    from src.utils.config import get_housekeeping_genes, get_seed
except ImportError:
    # Fallback if config is not yet imported in this context (should be handled by main)
    get_housekeeping_genes = lambda: []
    get_seed = lambda: 42

def calculate_sha256(data: str) -> str:
    """Calculate SHA256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def generate_synthetic_tpm_matrix(
    n_samples: int = 20,
    n_genes: int = 15000,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate a synthetic TPM count matrix.

    Uses a log-normal distribution to mimic real gene expression data.
    Housekeeping genes are injected with lower variance.

    Args:
        n_samples: Number of synthetic samples (studies/replicates)
        n_genes: Number of genes in the matrix
        seed: Random seed for reproducibility

    Returns:
        pd.DataFrame: TPM matrix with genes as rows and samples as columns.
    """
    np.random.seed(seed)

    # Generate gene names
    gene_ids = [f"AT{np.random.randint(1, 6):01d}G{np.random.randint(10000, 50000):05d}" for _ in range(n_genes)]

    # Generate TPM values using log-normal distribution
    # s=1.5 (shape), scale=10 (median-like center)
    tpm_values = scipy_stats_lognorm.rvs(s=1.5, scale=10, size=(n_samples, n_genes))

    # Inject housekeeping genes with lower variance (more stable)
    hk_genes = get_housekeeping_genes()
    if hk_genes:
        # Find or create indices for housekeeping genes
        # For synthetic data, we might just pick random rows to represent HK genes
        # to ensure the structure is correct for downstream batch correction
        hk_indices = np.random.choice(n_genes, size=min(len(hk_genes), n_genes), replace=False)
        # Reduce variance for HK genes (scale by 0.5, closer to mean)
        hk_means = np.mean(tpm_values, axis=1)
        tpm_values[:, hk_indices] = hk_means[:, np.newaxis] * (1 + 0.1 * np.random.randn(n_samples, len(hk_indices)))

    # Ensure non-negative
    tpm_values = np.maximum(tpm_values, 0)

    df = pd.DataFrame(
        tpm_values,
        index=gene_ids,
        columns=[f"Sample_{i:03d}" for i in range(n_samples)]
    )

    return df

def calculate_manifest_entry(
    file_path: str,
    accession_id: str,
    seed: int,
    n_samples: int,
    n_genes: int
) -> Dict[str, Any]:
    """
    Generate a manifest entry for the generated synthetic data.

    Args:
        file_path: Path to the saved CSV file
        accession_id: Synthetic accession ID
        seed: Random seed used
        n_samples: Number of samples
        n_genes: Number of genes

    Returns:
        Dict: Manifest entry dictionary.
    """
    # Calculate checksum of the file content
    with open(file_path, 'rb') as f:
        content = f.read()
        checksum = hashlib.sha256(content).hexdigest()

    # Get tool versions
    import scipy
    import pandas

    return {
        "file_name": os.path.basename(file_path),
        "checksum": checksum,
        "source_type": "synthetic",
        "provenance": {
            "generated_at": datetime.datetime.now().isoformat(),
            "tool_versions": {
                "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "numpy": np.__version__,
                "scipy": scipy.__version__,
                "pandas": pandas.__version__
            },
            "accession_id": accession_id,
            "organism": "Arabidopsis thaliana",
            "parameters": {
                "seed": seed,
                "distribution": "log-normal",
                "n_samples": n_samples,
                "n_genes": n_genes
            }
        }
    }

def save_synthetic_manifest(manifest_entry: Dict[str, Any], output_path: str) -> None:
    """Save the synthetic manifest to JSON."""
    with open(output_path, 'w') as f:
        json.dump(manifest_entry, f, indent=2)

def generate_synthetic_metadata_report(accession_id: str, output_path: str) -> None:
    """
    Generate the metadata verification report required by T011a.
    This report explicitly states mode="synthetic" and real_data_available=false.

    Args:
        accession_id: The synthetic accession ID.
        output_path: Path to write the JSON report.
    """
    report = {
        "mode": "synthetic",
        "real_data_available": False,
        "verification_results": [
            {
                "accession_id": accession_id,
                "status": "valid",
                "tissue_metadata": "leaf_root_germ", # Synthetic valid tissue
                "replicates": 3, # Synthetic valid replicates
                "herbivore_type": "generalist_chewing",
                "exclusion_reason": None
            }
        ],
        "summary": {
            "total_studies": 1,
            "valid_studies": 1,
            "excluded_studies": 0
        },
        "generated_at": datetime.datetime.now().isoformat()
    }

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

def main():
    """
    Main entry point for generating synthetic data.
    Writes outputs to data/synthetic/ and data/processed/.
    """
    import sys
    from pathlib import Path

    # Set seed from config or default
    try:
        from src.utils.config import set_seed, get_seed
        set_seed(42)
        seed = get_seed()
    except ImportError:
        seed = 42

    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    synthetic_dir = project_root / "data" / "synthetic"
    processed_dir = project_root / "data" / "processed"
    manifests_dir = project_root / "data" / "manifests"

    synthetic_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)

    # Parameters
    n_samples = 20
    n_genes = 15000
    accession_id = "SYNTH_001"
    file_name = f"{accession_id}_tpm_matrix.csv"
    manifest_file = manifests_dir / "synthetic_manifest.json"
    verification_report_file = processed_dir / "metadata_verification_report.json"

    print(f"Generating synthetic TPM matrix: {n_samples} samples x {n_genes} genes...")
    df = generate_synthetic_tpm_matrix(n_samples, n_genes, seed)

    # Save TPM matrix
    tpm_file_path = synthetic_dir / file_name
    df.to_csv(tpm_file_path)
    print(f"Saved TPM matrix to {tpm_file_path}")

    # Generate and save manifest
    manifest_entry = calculate_manifest_entry(
        str(tpm_file_path),
        accession_id,
        seed,
        n_samples,
        n_genes
    )
    save_synthetic_manifest(manifest_entry, str(manifest_file))
    print(f"Saved synthetic manifest to {manifest_file}")

    # Generate and save verification report (required for T011a)
    generate_synthetic_metadata_report(accession_id, str(verification_report_file))
    print(f"Saved metadata verification report to {verification_report_file}")

    print("Synthetic data generation complete.")

if __name__ == "__main__":
    # Import scipy inside main to avoid import errors if not needed
    import scipy.stats
    global scipy_stats_lognorm
    scipy_stats_lognorm = scipy.stats.lognorm
    main()
