import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import setup_logging, get_logger
from utils.seed import set_seed
from data.ingest import fetch_zinc15_data, process_smiles_file
from data.preprocess import process_molecule_chunk, load_conformer_config
from data.add_molecular_weight import calculate_molecular_weight, add_molecular_weight_column
from data.split import stratified_split_by_mw, save_indices_to_csv
from data.logging_stats import DatasetStatistics, log_dataset_statistics
from utils.checksum import calculate_file_checksum

def setup_dry_run_logger(log_path: Path) -> logging.Logger:
    """Setup a specific logger for the dry-run execution."""
    setup_logging(log_level=logging.INFO)
    logger = get_logger("dry_run")
    
    # Add file handler for dry-run specific logs
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def run_dry_run_pipeline(
    logger: logging.Logger, 
    sample_size: int = 100,
    output_dir: Path = None
) -> Dict[str, Any]:
    """
    Execute a dry-run of the entire pipeline on a fixed sample of molecules.
    
    This function:
    1. Fetches a small sample from the real ZINC15 dataset.
    2. Processes 2D and 3D features for exactly `sample_size` molecules.
    3. Calculates Molecular Weight.
    4. Performs a stratified split.
    5. Validates the outputs and error handling.
    
    Args:
        logger: The dry-run logger instance.
        sample_size: Number of molecules to process (default 100).
        output_dir: Directory to write dry-run artifacts.
        
    Returns:
        A dictionary containing the dry-run results and statistics.
    """
    if output_dir is None:
        output_dir = project_root / "data" / "processed" / "dry_run"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "sample_size": sample_size,
        "status": "pending",
        "errors": [],
        "stats": {},
        "output_files": []
    }

    logger.info(f"Starting dry-run pipeline on {sample_size} molecules.")
    logger.info(f"Output directory: {output_dir}")

    # 1. Ingest: Fetch real data with streaming
    logger.info("Step 1: Fetching real ZINC15 data (streaming)...")
    try:
        # We fetch the dataset in streaming mode and take the first `sample_size` items
        # to simulate the chunked processing without loading the full 7GB.
        # The actual ingest.py logic uses datasets.load_dataset(..., streaming=True)
        # Here we replicate that logic for the dry-run scope.
        
        # Note: We assume the 'datasets' library is installed as per T002
        from datasets import load_dataset
        
        # Using a known subset that is accessible. 
        # ZINC15 filtered drug-like is the target.
        # If the specific subset ID changes, this might need adjustment, 
        # but we adhere to the spec's requirement for a real source.
        # We use 'zinc15' if available, otherwise a fallback to a small known subset
        # to ensure the dry-run completes in the time budget if the full ZINC15 is slow.
        # However, per strict constraints, we must try the real source first.
        
        dataset_name = "zinc15" 
        # Attempt to load a small subset or the main one. 
        # If 'zinc15' is not a direct HF dataset name, we might need to use a specific path.
        # Based on T012, we target "https://zinc15.docking.org/subsets/filtered/drug_like/"
        # often mirrored as 'zinc15' or similar in HF.
        # Let's try to load 'zinc15' or a known small mirror.
        # If this fails, the pipeline MUST fail loudly (T043).
        
        # Fallback strategy for dry-run stability if the full ZINC15 is not directly 
        # available as a simple 'zinc15' dataset name in HF:
        # We will try to load 'zinc15' first. If it raises, we fail.
        # To ensure the dry-run is robust against network issues for the FULL dataset
        # but still uses REAL data, we limit the take.
        
        try:
            ds = load_dataset("zinc15", split="train", streaming=True)
        except Exception as e:
            # If 'zinc15' is not found, try a known alternative that represents the data
            # e.g., 'molecule_net' or similar if zinc15 isn't a direct HF dataset name.
            # However, T012 specifically mentions ZINC15. 
            # If the HF mirror is not 'zinc15', we might need to fetch from URL.
            # Let's assume 'zinc15' is the intended HF name. If not, we fail loudly.
            logger.error(f"Failed to load 'zinc15' dataset from HuggingFace: {e}")
            raise RuntimeError("Real data source 'zinc15' not found. Dry-run cannot proceed with synthetic data.")

        # Take exactly sample_size
        sample_data = []
        count = 0
        for item in ds:
            sample_data.append(item)
            count += 1
            if count >= sample_size:
                break
        
        if len(sample_data) < sample_size:
            logger.warning(f"Only retrieved {len(sample_data)} molecules from real source, expected {sample_size}.")
            sample_size = len(sample_data)
            
        logger.info(f"Successfully retrieved {len(sample_data)} real molecules from ZINC15.")
        
    except Exception as e:
        logger.error(f"CRITICAL: Failed to fetch real ZINC15 data: {e}")
        results["status"] = "failed"
        results["errors"].append(f"Ingest failed: {str(e)}")
        return results

    # 2. Preprocess: 2D and 3D features
    logger.info("Step 2: Processing 2D/3D features for sample...")
    processed_molecules = []
    failed_count = 0
    
    # Load conformer config (generated by T006b/T014)
    try:
        conformer_config = load_conformer_config()
    except Exception as e:
        # If config doesn't exist, generate a default one for the dry-run
        logger.warning("Conformer config not found, generating default for dry-run.")
        from utils.conformer_config import generate_conformer_config
        conformer_config = generate_conformer_config()
        # Save it for the pipeline
        config_path = output_dir / "conformer_config.json"
        with open(config_path, 'w') as f:
            json.dump(conformer_config, f)
        
    for idx, item in enumerate(sample_data):
        smiles = item.get("smiles")
        if not smiles:
            failed_count += 1
            continue
        
        try:
            # Replicate logic from process_molecule_chunk
            mol_data = process_molecule_chunk([{"smiles": smiles}], conformer_config)
            if mol_data and len(mol_data) > 0:
                processed_molecules.append(mol_data[0])
            else:
                failed_count += 1
        except Exception as e:
            logger.debug(f"Molecule {idx} failed processing: {e}")
            failed_count += 1

    if len(processed_molecules) == 0:
        logger.error("CRITICAL: No molecules processed successfully.")
        results["status"] = "failed"
        results["errors"].append("Preprocessing failed for all molecules.")
        return results

    failure_rate = failed_count / len(sample_data)
    logger.info(f"Preprocessing complete. Success: {len(processed_molecules)}, Failed: {failed_count} ({failure_rate:.2%})")
    
    if failure_rate > 0.10:
        logger.error(f"CRITICAL: Failure rate {failure_rate:.2%} exceeds 10% threshold.")
        results["status"] = "failed"
        results["errors"].append("Conformer generation failure rate > 10%.")
        return results

    # 3. Add Molecular Weight
    logger.info("Step 3: Calculating Molecular Weight...")
    for mol in processed_molecules:
        mol["molecular_weight"] = calculate_molecular_weight(mol.get("smiles"))
    
    # 4. Save to Parquet/CSV
    output_file = output_dir / "dry_run_graphs.parquet"
    import pandas as pd
    df = pd.DataFrame(processed_molecules)
    df.to_parquet(output_file)
    logger.info(f"Saved processed data to {output_file}")
    results["output_files"].append(str(output_file))
    
    # 5. Split
    logger.info("Step 4: Performing stratified split...")
    try:
        train_indices, test_indices = stratified_split_by_mw(df, test_size=0.2, random_state=42)
        
        save_indices_to_csv(train_indices, output_dir / "dry_run_train_indices.csv")
        save_indices_to_csv(test_indices, output_dir / "dry_run_test_indices.csv")
        
        logger.info(f"Split complete. Train: {len(train_indices)}, Test: {len(test_indices)}")
        results["output_files"].append(str(output_dir / "dry_run_train_indices.csv"))
        results["output_files"].append(str(output_dir / "dry_run_test_indices.csv"))
    except Exception as e:
        logger.error(f"Split failed: {e}")
        results["errors"].append(f"Split failed: {str(e)}")
        # Don't fail the whole pipeline if split is the only issue, but log it.

    # 6. Checksum
    checksum = calculate_file_checksum(output_file)
    logger.info(f"Output file checksum: {checksum}")
    results["checksum"] = checksum

    # Final Stats
    results["stats"] = {
        "total_input": len(sample_data),
        "processed_success": len(processed_molecules),
        "failed": failed_count,
        "failure_rate": failure_rate,
        "train_count": len(train_indices) if 'train_indices' in locals() else 0,
        "test_count": len(test_indices) if 'test_indices' in locals() else 0
    }
    
    results["status"] = "success"
    return results

def main():
    parser = argparse.ArgumentParser(description="Dry-run pipeline for ZINC15 SASA prediction.")
    parser.add_argument("--sample-size", type=int, default=100, help="Number of molecules to process.")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for dry-run artifacts.")
    args = parser.parse_args()

    # Setup logging
    log_dir = Path("results") / "reports"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "dry_run_execution.log"
    
    logger = setup_dry_run_logger(log_file)
    
    # Set seed
    set_seed(42)
    
    # Run pipeline
    results = run_dry_run_pipeline(
        logger=logger, 
        sample_size=args.sample_size,
        output_dir=Path(args.output_dir) if args.output_dir else None
    )
    
    # Save results report
    report_path = Path("results") / "reports" / "dry_run_report.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Dry-run report saved to {report_path}")
    
    if results["status"] == "success":
        logger.info("Dry-run completed successfully.")
        sys.exit(0)
    else:
        logger.error("Dry-run failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()