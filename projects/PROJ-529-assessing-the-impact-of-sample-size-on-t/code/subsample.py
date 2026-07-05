"""
Subsample generation module for meta-analysis stability assessment.

Implements bootstrap subsampling logic with seed management, chunked processing
support, and variance error handling. Generates up to 100 bootstrap subsamples
for each k (study count) from 3 to N.
"""

import os
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

# Import from project API surface
from utils.seeds import SeedManager
from utils.exceptions import handle_variance_issues, ZeroVarianceError, NegativeVarianceError
from utils.io import ChunkedDataReader, process_large_dataset
from models import Study, Subsample, MetaAnalysis
from config import is_real_mode, is_simulation_mode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_meta_analyses_from_disk() -> List[MetaAnalysis]:
    """
    Load meta-analyses from raw data directory.
    Handles both real downloaded data and simulation fallback data.
    """
    data_dir = Path("data/raw")
    if not data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {data_dir}")

    meta_analyses = []
    
    # Check for simulation data first (fallback)
    sim_files = list(data_dir.glob("simulation_*.csv"))
    real_files = list(data_dir.glob("cochrane_*.csv")) + list(data_dir.glob("campbell_*.csv"))
    
    files_to_process = sim_files if is_simulation_mode() else real_files
    
    if not files_to_process:
        if is_simulation_mode():
            logger.warning("No simulation data found. Running simulation fallback.")
            # Trigger simulation generation if not already done
            from download import run_simulation_fallback
            run_simulation_fallback()
            files_to_process = list(data_dir.glob("simulation_*.csv"))
        else:
            raise FileNotFoundError("No real meta-analysis data found and simulation mode not active.")

    for file_path in files_to_process:
        try:
            # Use chunked reading for large files
            studies = []
            chunk_iterator = ChunkedDataReader(file_path, chunk_size=1000)
            
            for chunk in chunk_iterator:
                # Convert chunk to Study objects
                for _, row in chunk.iterrows():
                    try:
                        study = Study(
                            meta_id=row.get('meta_id', 'unknown'),
                            effect_size=float(row['effect_size']),
                            se=float(row['se']),
                            n=int(row.get('n', 0))
                        )
                        # Validate variance
                        if study.se <= 0:
                            raise ZeroVarianceError(f"Zero or negative SE for study in meta {study.meta_id}")
                        studies.append(study)
                    except (KeyError, ValueError) as e:
                        logger.warning(f"Skipping invalid row: {e}")
                        continue
            
            if studies:
                meta_id = studies[0].meta_id
                meta_analysis = MetaAnalysis(
                    meta_id=meta_id,
                    studies=studies,
                    total_studies=len(studies)
                )
                meta_analyses.append(meta_analysis)
                logger.info(f"Loaded {len(studies)} studies from {file_path.name} for meta_id: {meta_id}")
            
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            continue

    logger.info(f"Total meta-analyses loaded: {len(meta_analyses)}")
    return meta_analyses

def generate_bootstrap_subsample(
    studies: List[Study],
    k: int,
    seed: int,
    estimator_type: str = "REML"
) -> Optional[Subsample]:
    """
    Generate a single bootstrap subsample of size k from the study list.
    
    Args:
        studies: List of Study objects
        k: Number of studies to sample
        seed: Random seed for reproducibility
        estimator_type: Type of estimator (REML or DL)
        
    Returns:
        Subsample object or None if generation fails
    """
    if k < 3:
        logger.warning(f"Skipping subsample generation for k={k} (minimum k=3)")
        return None
    
    if k > len(studies):
        logger.warning(f"Cannot generate subsample with k={k} from {len(studies)} studies")
        return None

    try:
        # Set seed for reproducibility
        np.random.seed(seed)
        
        # Bootstrap sampling with replacement
        sampled_indices = np.random.choice(len(studies), size=k, replace=True)
        sampled_studies = [studies[i] for i in sampled_indices]
        
        # Validate variance in sampled studies
        valid_studies = []
        for study in sampled_studies:
            try:
                handle_variance_issues(study.effect_size, study.se)
                valid_studies.append(study)
            except (ZeroVarianceError, NegativeVarianceError) as e:
                logger.debug(f"Excluding study with variance issue: {e}")
                continue
        
        if len(valid_studies) < 3:
            logger.warning(f"Not enough valid studies after variance filtering for k={k}")
            return None
        
        # Create Subsample object
        subsample = Subsample(
            meta_id=sampled_studies[0].meta_id,
            k=len(valid_studies),
            seed=seed,
            estimator_type=estimator_type,
            studies=valid_studies,
            effect_sizes=[s.effect_size for s in valid_studies],
            ses=[s.se for s in valid_studies]
        )
        
        return subsample
        
    except Exception as e:
        logger.error(f"Failed to generate subsample: {e}")
        return None

def run_subsampling_pipeline(
    meta_analyses: List[MetaAnalysis],
    max_subsamples_per_k: int = 100,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Run the full subsampling pipeline for all meta-analyses.
    
    Generates bootstrap subsamples for each k from 3 to N (max studies in meta-analysis),
    up to max_subsamples_per_k iterations per k.
    
    Args:
        meta_analyses: List of MetaAnalysis objects
        max_subsamples_per_k: Maximum number of bootstrap subsamples per k value
        output_path: Path to save the output parquet file
        
    Returns:
        DataFrame containing all subsample data
    """
    if output_path is None:
        output_path = "data/processed/subsample_data.parquet"
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_subsamples = []
    seed_manager = SeedManager()
    
    logger.info(f"Starting subsampling pipeline for {len(meta_analyses)} meta-analyses")
    logger.info(f"Max subsamples per k: {max_subsamples_per_k}")
    
    for meta_analysis in meta_analyses:
        meta_id = meta_analysis.meta_id
        n_studies = len(meta_analysis.studies)
        
        logger.info(f"Processing meta_id: {meta_id} with {n_studies} studies")
        
        # Determine k range: 3 to n_studies
        k_values = range(3, n_studies + 1)
        
        for k in k_values:
            # Reset seed for each k to ensure reproducibility
            seed_manager.reset_seed(base_seed=hash(f"{meta_id}_k{k}"))
            
            subsamples_generated = 0
            attempts = 0
            max_attempts = max_subsamples_per_k * 5  # Allow some retries for failed samples
            
            while subsamples_generated < max_subsamples_per_k and attempts < max_attempts:
                seed = seed_manager.get_next_seed()
                attempts += 1
                
                # Determine estimator type based on k (REML for k<10, DL for k>=10)
                estimator_type = "REML" if k < 10 else "DL"
                
                subsample = generate_bootstrap_subsample(
                    studies=meta_analysis.studies,
                    k=k,
                    seed=seed,
                    estimator_type=estimator_type
                )
                
                if subsample is not None:
                    # Log iteration details
                    logger.debug(f"Generated subsample: meta_id={meta_id}, k={k}, seed={seed}, estimator={estimator_type}")
                    
                    # Store subsample data
                    subsample_data = {
                        'meta_id': meta_id,
                        'k': k,
                        'seed': seed,
                        'estimator_type': estimator_type,
                        'n_studies_original': n_studies,
                        'n_studies_sampled': len(subsample.studies),
                        'effect_sizes': [s.effect_size for s in subsample.studies],
                        'ses': [s.se for s in subsample.studies],
                        'mean_effect': np.mean([s.effect_size for s in subsample.studies]),
                        'variance_effect': np.var([s.effect_size for s in subsample.studies]),
                    }
                    
                    all_subsamples.append(subsample_data)
                    subsamples_generated += 1
            
            logger.info(f"  k={k}: Generated {subsamples_generated}/{max_subsamples_per_k} subsamples")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_subsamples)
    
    if not df.empty:
        # Save to parquet
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved {len(df)} subsamples to {output_path}")
        
        # Also save a summary CSV for quick inspection
        summary_path = output_path.replace('.parquet', '_summary.csv')
        summary_df = df.groupby(['meta_id', 'k', 'estimator_type']).agg({
            'seed': 'count',
            'mean_effect': ['mean', 'std']
        }).reset_index()
        summary_df.columns = ['meta_id', 'k', 'estimator_type', 'count', 'mean_effect', 'std_effect']
        summary_df.to_csv(summary_path, index=False)
        logger.info(f"Saved summary to {summary_path}")
    else:
        logger.warning("No subsamples were generated. Creating empty output file.")
        # Create empty file with correct schema
        empty_df = pd.DataFrame(columns=[
            'meta_id', 'k', 'seed', 'estimator_type', 'n_studies_original',
            'n_studies_sampled', 'effect_sizes', 'ses', 'mean_effect', 'variance_effect'
        ])
        empty_df.to_parquet(output_path, index=False)
    
    return df

def main():
    """Main entry point for the subsampling pipeline."""
    logger.info("Starting subsampling pipeline...")
    
    try:
        # Load meta-analyses from disk
        meta_analyses = load_meta_analyses_from_disk()
        
        if not meta_analyses:
            logger.error("No meta-analyses loaded. Cannot proceed with subsampling.")
            return 1
        
        # Run subsampling pipeline
        output_df = run_subsampling_pipeline(
            meta_analyses=meta_analyses,
            max_subsamples_per_k=100,
            output_path="data/processed/subsample_data.parquet"
        )
        
        if output_df.empty:
            logger.error("Subsampling pipeline completed but no data was generated.")
            return 1
        
        logger.info(f"Subsampling pipeline completed successfully. Generated {len(output_df)} subsamples.")
        return 0
        
    except Exception as e:
        logger.exception(f"Subsampling pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
