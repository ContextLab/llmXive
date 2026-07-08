import sys
import os
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure the project root is in the path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ensure_directories, PROJECT_ROOT as CONFIG_ROOT
from src.data_loader import (
    fetch_dataset,
    load_manifest,
    get_cached_datasets,
    clear_cache
)
from src.preprocessing import (
    filter_zero_count_genes,
    stratify_samples,
    preprocess_dataset
)
from src.metrics import calculate_stability_metrics
from src.versioning import update_artifact_state, compute_sha256

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

R_SCRIPT_PATH = CONFIG_ROOT / "scripts" / "run_r_script.R"

def run_r_de_analysis(counts_path: Path, meta_path: Path, output_dir: Path, dataset_id: str, subset_idx: Optional[int] = None) -> Path:
    """
    Executes the R script (T014) for Differential Expression analysis.
    
    Args:
        counts_path: Path to the CSV file containing count matrix.
        meta_path: Path to the CSV file containing sample metadata.
        output_dir: Directory where R script should write results.
        dataset_id: Identifier for the dataset (used in output filenames).
        subset_idx: Optional index of the subset being processed.
        
    Returns:
        Path to the generated DE results file (e.g., results_subset_X.csv).
    """
    if not R_SCRIPT_PATH.exists():
        raise FileNotFoundError(f"R script not found at {R_SCRIPT_PATH}. Ensure T014 is complete.")
    
    output_file_name = f"{dataset_id}_de_results.csv"
    if subset_idx is not None:
        output_file_name = f"{dataset_id}_de_results_subset_{subset_idx}.csv"
        
    output_path = output_dir / output_file_name

    # Prepare arguments for the R script
    # Assuming the R script expects: counts_file, meta_file, output_file
    cmd = [
        "Rscript",
        str(R_SCRIPT_PATH),
        str(counts_path),
        str(meta_path),
        str(output_path)
    ]

    logger.info(f"Running DE analysis: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        if result.stdout:
            logger.debug(f"R stdout: {result.stdout}")
        if result.stderr:
            logger.debug(f"R stderr: {result.stderr}")
        
        if not output_path.exists():
            raise RuntimeError(f"R script finished but did not produce expected output at {output_path}")
            
        return output_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"R script failed with return code {e.returncode}")
        logger.error(f"R stderr: {e.stderr}")
        raise RuntimeError(f"DE analysis failed: {e.stderr}")

def run_stability_analysis(dataset_id: str, num_subsets: int = 5) -> dict:
    """
    Orchestrates the stability analysis for a single dataset.
    1. Loads data.
    2. Preprocesses (filters, stratifies).
    3. Runs DE analysis on full set and subsets via R script (T014).
    4. Calculates stability metrics (Pearson correlation of log2FC).
    """
    ensure_directories()
    
    logger.info(f"Starting stability analysis for dataset: {dataset_id}")
    
    # 1. Load Data
    try:
        dataset = fetch_dataset(dataset_id)
        if dataset is None:
            logger.error(f"Dataset {dataset_id} not found or failed to download.")
            return {"status": "failed", "reason": "Dataset not found"}
        
        counts_df = dataset['counts']
        meta_df = dataset['meta']
        
        # Filter for minimum sample size (T017 requirement)
        if counts_df.shape[1] < 20:
            logger.warning(f"Dataset {dataset_id} has only {counts_df.shape[1]} samples (< 20). Skipping.")
            return {"status": "skipped", "reason": "Insufficient samples (< 20)"}
            
        logger.info(f"Loaded dataset {dataset_id}: {counts_df.shape[0]} genes, {counts_df.shape[1]} samples")
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {e}")
        return {"status": "failed", "reason": str(e)}

    # 2. Preprocess: Filter Zero Counts
    logger.info("Filtering zero-count genes...")
    filtered_counts = filter_zero_count_genes(counts_df)
    
    # Check for minimum genes (T018 requirement)
    if filtered_counts.shape[0] < 5:
        logger.warning(f"Dataset {dataset_id} has only {filtered_counts.shape[0]} genes after filtering (< 5). Skipping.")
        return {"status": "skipped", "reason": "Insufficient genes (< 5)"}
        
    logger.info(f"After filtering: {filtered_counts.shape[0]} genes")

    # 3. Preprocess: Stratify into Subsets
    logger.info(f"Stratifying data into {num_subsets} subsets...")
    try:
        subsets = stratify_samples(filtered_counts, meta_df, n_splits=num_subsets)
        logger.info(f"Created {len(subsets)} subsets.")
        for i, sub in enumerate(subsets):
            logger.info(f"  Subset {i}: {sub.shape[1]} samples")
    except Exception as e:
        logger.error(f"Stratification failed: {e}")
        return {"status": "failed", "reason": f"Stratification error: {str(e)}"}

    # 4. Run DE Analysis (T015 Core Logic)
    # Create a temporary directory for intermediate R inputs/outputs
    temp_dir = CONFIG_ROOT / "data" / "intermediates" / dataset_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    full_log2fc_path = None
    
    try:
        # 4a. Run DE on FULL dataset first
        full_counts_path = temp_dir / f"{dataset_id}_full_counts.csv"
        full_meta_path = temp_dir / f"{dataset_id}_full_meta.csv"
        filtered_counts.to_csv(full_counts_path)
        meta_df.to_csv(full_meta_path)
        
        logger.info("Running DE analysis on FULL dataset...")
        full_log2fc_path = run_r_de_analysis(
            full_counts_path, 
            full_meta_path, 
            temp_dir, 
            dataset_id, 
            subset_idx=None
        )
        
        # Read full log2FC results
        full_results_df = pd.read_csv(full_log2fc_path)
        # Expect columns: 'gene', 'log2FoldChange' (standard DESeq2/edgeR output)
        if 'log2FoldChange' not in full_results_df.columns:
            # Fallback if column name differs, though spec implies standard
            cols = [c for c in full_results_df.columns if 'log2' in c.lower()]
            if cols:
                full_log2fc_col = cols[0]
            else:
                raise ValueError(f"Could not find log2FC column in {full_log2fc_path}. Columns: {list(full_results_df.columns)}")
        else:
            full_log2fc_col = 'log2FoldChange'
            
        full_log2fc_series = full_results_df.set_index('gene')[full_log2fc_col]
        
        # 4b. Run DE on each SUBSET and collect log2FC
        subset_log2fc_series_list = []
        
        for i, sub_counts in enumerate(subsets):
            logger.info(f"Running DE analysis on Subset {i}...")
            
            sub_counts_path = temp_dir / f"{dataset_id}_subset_{i}_counts.csv"
            # Metadata is the same for all subsets in this stratification approach
            # (we are splitting samples, so meta needs to be filtered too? 
            #  stratify_samples returns counts only. We need to filter meta to match samples)
            #  Assuming stratify_samples returns counts where columns are sample IDs.
            #  We need to filter meta_df to keep only samples present in sub_counts.columns
            
            sub_samples = sub_counts.columns.tolist()
            sub_meta = meta_df[meta_df['sample_id'].isin(sub_samples)]
            
            sub_meta_path = temp_dir / f"{dataset_id}_subset_{i}_meta.csv"
            
            sub_counts.to_csv(sub_counts_path)
            sub_meta.to_csv(sub_meta_path)
            
            sub_log2fc_path = run_r_de_analysis(
                sub_counts_path, 
                sub_meta_path, 
                temp_dir, 
                dataset_id, 
                subset_idx=i
            )
            
            sub_results_df = pd.read_csv(sub_log2fc_path)
            # Find log2FC column
            if 'log2FoldChange' in sub_results_df.columns:
                col_name = 'log2FoldChange'
            else:
                cols = [c for c in sub_results_df.columns if 'log2' in c.lower()]
                col_name = cols[0] if cols else sub_results_df.columns[1] # Fallback
                
            sub_log2fc_series = sub_results_df.set_index('gene')[col_name]
            subset_log2fc_series_list.append(sub_log2fc_series)
            
    except Exception as e:
        logger.error(f"DE analysis loop failed: {e}")
        return {"status": "failed", "reason": f"DE analysis error: {str(e)}"}

    # 5. Calculate Stability Metrics
    # Calculate Pearson correlation between Full and each Subset
    correlations = []
    for i, sub_log2fc in enumerate(subset_log2fc_series_list):
        # Align indices (genes)
        common_genes = full_log2fc_series.index.intersection(sub_log2fc.index)
        if len(common_genes) < 10:
            logger.warning(f"Subset {i} has insufficient overlapping genes ({len(common_genes)}). Skipping correlation.")
            continue
        
        r_val, p_val = pearsonr(
            full_log2fc_series.loc[common_genes], 
            sub_log2fc.loc[common_genes]
        )
        correlations.append(r_val)
        logger.info(f"Subset {i} vs Full: r = {r_val:.4f}, p = {p_val:.4e}")
    
    if not correlations:
        logger.error("No valid correlations calculated.")
        return {"status": "failed", "reason": "No valid correlations calculated"}
    
    stability_result = {
        "dataset_id": dataset_id,
        "num_subsets": num_subsets,
        "correlations": correlations,
        "mean_correlation": float(np.mean(correlations)),
        "std_correlation": float(np.std(correlations)),
        "status": "completed",
        "artifacts": [str(p) for p in temp_dir.glob(f"{dataset_id}_de_results*.csv")]
    }
    
    # Save final stability result
    final_output_dir = CONFIG_ROOT / "data" / "results"
    final_output_dir.mkdir(parents=True, exist_ok=True)
    result_path = final_output_dir / f"{dataset_id}_stability.json"
    
    import json
    with open(result_path, 'w') as f:
        json.dump(stability_result, f, indent=2)
        
    update_artifact_state("stability_analysis", compute_sha256(final_output_dir))
    
    return stability_result

def main():
    """
    Entry point for the stability analysis pipeline.
    Orchestrates the loop over subsets and R script calls.
    """
    ensure_directories()
    
    # Load manifest to find available datasets
    manifest = load_manifest()
    
    if not manifest:
        logger.critical("No manifest found. Run setup or create a manifest.")
        sys.exit(1)
    
    # Select a dataset for demonstration (e.g., the first one in the manifest)
    # In a real run, this could be an argument
    target_dataset = manifest.get('datasets', [{}])[0].get('id')
    
    if not target_dataset:
        logger.warning("No datasets found in manifest. Exiting.")
        sys.exit(0)
    
    logger.info(f"Target dataset selected: {target_dataset}")
    
    result = run_stability_analysis(target_dataset, num_subsets=5)
    
    if result['status'] == 'failed':
        logger.error(f"Analysis failed: {result.get('reason')}")
        sys.exit(1)
    elif result['status'] == 'skipped':
        logger.warning(f"Analysis skipped: {result.get('reason')}")
        sys.exit(0)
    
    logger.info(f"Analysis completed successfully: {result}")
    print(f"Result: {result}")

if __name__ == "__main__":
    main()