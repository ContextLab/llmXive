import os
import json
import hashlib
import datetime
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import existing utilities to maintain API surface
from src.utils.logger import get_logger
from src.utils.config import get_config, get_housekeeping_genes, get_seed
from src.utils.schemas import ManifestEntry, ProvenanceInfo

logger = get_logger(__name__)

def _calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _get_tool_versions() -> Dict[str, str]:
    """Get versions of relevant tools for provenance."""
    return {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "numpy": np.__version__,
        "pandas": pd.__version__,
    }

def generate_synthetic_counts(
    n_genes: int = 2000,
    n_samples: int = 50,
    n_studies: int = 3,
    output_dir: Optional[str] = None,
    seed: Optional[int] = None,
) -> Tuple[Dict[str, pd.DataFrame], str]:
    """
    Generate structurally valid synthetic TPM count matrices.

    This function creates synthetic expression data that mimics real RNA-seq
    TPM matrices. It generates multiple "studies" (simulating batch effects)
    with varying sample sizes and gene expression patterns.

    Args:
        n_genes: Number of genes to generate
        n_samples: Total number of samples across all studies
        n_studies: Number of distinct studies (batches) to simulate
        output_dir: Directory to save the generated CSV files
        seed: Random seed for reproducibility

    Returns:
        Tuple of (dict of DataFrames keyed by study name, path to manifest file)
    """
    if seed is None:
        seed = get_seed()
    
    np.random.seed(seed)
    logger.info(f"Generating synthetic counts with seed={seed}")
    logger.info(f"Parameters: n_genes={n_genes}, n_samples={n_samples}, n_studies={n_studies}")

    # Create output directory if specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        # Default to project's synthetic data directory
        config = get_config()
        output_path = Path(config.data_dir) / "synthetic"
        output_path.mkdir(parents=True, exist_ok=True)

    # Housekeeping genes from config
    housekeeping_genes = get_housekeeping_genes()
    n_hk = len(housekeeping_genes)
    
    # Ensure we have enough genes for housekeeping set
    if n_genes < n_hk:
        logger.warning(f"n_genes ({n_genes}) < housekeeping genes ({n_hk}), adjusting n_genes")
        n_genes = n_hk + 500

    # Gene names
    gene_names = [f"GENE_{i:05d}" for i in range(n_genes)]
    # Insert housekeeping genes at specific positions for realism
    hk_indices = np.random.choice(n_genes, size=min(n_hk, n_genes), replace=False)
    for i, gene in enumerate(housekeeping_genes[:len(hk_indices)]):
        gene_names[hk_indices[i]] = gene

    # Study assignments and sample sizes
    samples_per_study = np.random.randint(10, 30, size=n_studies)
    total_samples = samples_per_study.sum()
    if total_samples < n_samples:
        # Adjust to meet minimum
        samples_per_study[-1] += (n_samples - total_samples)
    elif total_samples > n_samples:
        samples_per_study = samples_per_study[:n_samples]
    
    study_names = [f"Study_{i:03d}" for i in range(n_studies)]
    sample_assignments = []
    for study, count in zip(study_names, samples_per_study):
        sample_assignments.extend([study] * count)

    # Generate expression matrix
    # Base expression levels (log-normal distribution)
    base_expression = np.random.lognormal(mean=5, sigma=1.5, size=n_genes)
    
    # Housekeeping genes have lower variance
    hk_mask = np.array([g in housekeeping_genes for g in gene_names])
    hk_base = base_expression[hk_mask] * 1.5  # Slightly higher expression
    
    data_dict = {}
    manifest_entries = []
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    tool_versions = _get_tool_versions()

    for study_name, samples in zip(study_names, samples_per_study):
        # Create study-specific expression matrix
        study_matrix = np.zeros((n_genes, samples))
        
        for i in range(n_genes):
            gene_name = gene_names[i]
            if gene_name in housekeeping_genes:
                # Housekeeping: stable expression with small batch effect
                batch_effect = np.random.normal(0, 0.2)
                study_matrix[i, :] = np.random.lognormal(
                    mean=np.log(hk_base[list(housekeeping_genes).index(gene_name)]) + batch_effect,
                    sigma=0.1
                )
            else:
                # Variable genes: higher variance, some batch effect
                batch_effect = np.random.normal(0, 0.5)
                study_matrix[i, :] = np.random.lognormal(
                    mean=np.log(base_expression[i]) + batch_effect,
                    sigma=1.0
                )
        
        # Ensure non-negative and add small epsilon to avoid zeros
        study_matrix = np.maximum(study_matrix, 1e-6)
        
        # Create DataFrame
        df = pd.DataFrame(
            study_matrix.T,
            columns=gene_names,
            index=[f"{study_name}_Sample_{j:03d}" for j in range(samples)]
        )
        
        # Add metadata columns (simulating tissue/condition info)
        tissues = ["Leaf", "Root", "Stem", "Flower"]
        df["tissue"] = np.random.choice(tissues, size=samples)
        df["condition"] = np.random.choice(["Control", "Herbivory"], size=samples)
        
        # Save to CSV
        file_name = f"synthetic_{study_name.lower()}.csv"
        file_path = output_path / file_name
        df.to_csv(file_path, index=True)
        
        logger.info(f"Saved synthetic data for {study_name} to {file_path}")
        
        # Calculate checksum
        checksum = _calculate_sha256(str(file_path))
        
        # Create manifest entry
        entry = {
            "file_name": file_name,
            "checksum": checksum,
            "source_type": "synthetic",
            "provenance": {
                "generated_at": timestamp,
                "tool_versions": tool_versions,
                "parameters": {
                    "n_genes": n_genes,
                    "n_samples": samples,
                    "n_studies": n_studies,
                    "seed": seed
                }
            }
        }
        manifest_entries.append(entry)
        data_dict[study_name] = df

    # Write manifest
    manifest_path = output_path / "synthetic_manifest.json"
    manifest_data = {
        "manifest_version": "1.0",
        "generated_at": timestamp,
        "source_type": "synthetic",
        "entries": manifest_entries
    }
    
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)
    
    logger.info(f"Saved manifest to {manifest_path}")
    
    return data_dict, str(manifest_path)

def generate_synthetic_fastq_study(
    study_id: str = "synthetic_001",
    n_samples: int = 10,
    read_length: int = 150,
    output_dir: Optional[str] = None,
    seed: Optional[int] = None,
) -> str:
    """
    Generate synthetic FASTQ files for testing download pipeline.
    
    Note: This is for structural validation only. Real FASTQ generation
    is not feasible; this creates minimal valid FASTQ structures.
    
    Args:
        study_id: Identifier for the study
        n_samples: Number of samples to generate
        read_length: Length of reads
        output_dir: Directory to save FASTQ files
        seed: Random seed

    Returns:
        Path to the study directory
    """
    if seed is None:
        seed = get_seed()
    
    np.random.seed(seed)
    
    if output_dir:
        output_path = Path(output_dir)
    else:
        config = get_config()
        output_path = Path(config.data_dir) / "synthetic"
    
    output_path.mkdir(parents=True, exist_ok=True)
    study_dir = output_path / study_id
    study_dir.mkdir(exist_ok=True)

    logger.info(f"Generating synthetic FASTQ study: {study_id}")

    for i in range(n_samples):
        sample_name = f"{study_id}_Sample_{i:03d}"
        fastq_path = study_dir / f"{sample_name}.fastq"
        
        # Generate minimal valid FASTQ (4 lines per read)
        with open(fastq_path, "w") as f:
            for read_num in range(100):  # 100 reads per sample
                read_id = f"@{sample_name}_read_{read_num}"
                sequence = "".join(np.random.choice(list("ACGT"), size=read_length))
                plus_line = f"+{sample_name}_read_{read_num}"
                quality = "".join(np.random.choice(list("!'+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"), size=read_length))
                
                f.write(f"{read_id}\n{sequence}\n{plus_line}\n{quality}\n")
        
        logger.info(f"Generated synthetic FASTQ: {fastq_path}")

    return str(study_dir)

def calculate_tpm_from_counts(
    counts_df: pd.DataFrame,
    gene_lengths: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """
    Convert raw counts to TPM values.
    
    Args:
        counts_df: DataFrame with counts (rows=samples, cols=genes)
        gene_lengths: Dict mapping gene names to lengths in bp.
                     If None, uses random lengths.
    
    Returns:
        DataFrame with TPM values
    """
    if gene_lengths is None:
        # Generate random lengths between 500 and 5000 bp
        gene_lengths = {
            gene: np.random.uniform(500, 5000) 
            for gene in counts_df.columns
        }
    
    # Convert to RPK (Reads Per Kilobase)
    rpk = counts_df.div([gene_lengths[gene] / 1000.0 for gene in counts_df.columns], axis=1)
    
    # Calculate scaling factor (per sample)
    scaling_factors = rpk.sum(axis=1) / 1e6
    
    # TPM = RPK / scaling factor
    tpm = rpk.div(scaling_factors, axis=0)
    
    return tpm

def main():
    """Main entry point for synthetic data generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic TPM count matrices")
    parser.add_argument("--n-genes", type=int, default=2000, help="Number of genes")
    parser.add_argument("--n-samples", type=int, default=50, help="Total number of samples")
    parser.add_argument("--n-studies", type=int, default=3, help="Number of studies")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    
    args = parser.parse_args()
    
    data_dict, manifest_path = generate_synthetic_counts(
        n_genes=args.n_genes,
        n_samples=args.n_samples,
        n_studies=args.n_studies,
        output_dir=args.output_dir,
        seed=args.seed,
    )
    
    print(f"Synthetic data generation complete.")
    print(f"Generated {len(data_dict)} study matrices.")
    print(f"Manifest saved to: {manifest_path}")
    
    # Verify manifest content
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    print(f"Manifest contains {len(manifest['entries'])} entries.")
    for entry in manifest['entries']:
        print(f"  - {entry['file_name']}: {entry['checksum'][:16]}...")

if __name__ == "__main__":
    main()
