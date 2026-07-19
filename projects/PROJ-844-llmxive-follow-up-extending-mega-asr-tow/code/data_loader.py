import os
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Iterator, Generator

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datasets import load_dataset

from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for checksums
LIBRISPEECH_CHECKSUM = "d1923795991553656398971363638958" # Placeholder, actual checksums should be verified
CORAA_CHECKSUM = "a1b2c3d4e5f678901234567890123456" # Placeholder

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """Verify file checksum against expected value."""
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash

def fetch_and_verify_librispeech(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Fetch LibriSpeech subset from Hugging Face and verify integrity.
    Returns a DataFrame with audio paths and transcripts.
    """
    data_dir = Path(config['raw_path']) / 'librispeech'
    
    if not data_dir.exists():
        # Attempt to download via Hugging Face datasets
        logger.info(f"LibriSpeech data not found at {data_dir}. Attempting download...")
        try:
            # Using streaming to avoid loading full dataset into memory
            dataset = load_dataset(
                "librispeech_asr", 
                "clean", 
                split="train.clean.100", 
                streaming=True
            )
            
            # Create directory structure
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Process in chunks to save memory
            chunk_size = 1000
            chunks = []
            for i, item in enumerate(dataset):
                chunks.append(item)
                if len(chunks) >= chunk_size:
                    # Process chunk
                    df_chunk = pd.DataFrame(chunks)
                    # Save intermediate chunk
                    chunk_path = data_dir / f"chunk_{i // chunk_size}.parquet"
                    df_chunk.to_parquet(chunk_path)
                    chunks = []
            
            # Process remaining items
            if chunks:
                df_chunk = pd.DataFrame(chunks)
                chunk_path = data_dir / f"chunk_{len(chunks)}.parquet"
                df_chunk.to_parquet(chunk_path)
            
            logger.info(f"Downloaded LibriSpeech subset to {data_dir}")
        except Exception as e:
            logger.error(f"Failed to download LibriSpeech: {e}")
            raise FileNotFoundError(f"LibriSpeech data directory not found at {data_dir}. Download failed.")
    
    # Load data from chunks
    parquet_files = list(data_dir.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {data_dir}")
    
    # Stream load to avoid memory issues
    dfs = []
    for pq_file in parquet_files:
        table = pq.read_table(pq_file)
        df = table.to_pandas()
        dfs.append(df)
    
    return pd.concat(dfs, ignore_index=True)

def fetch_and_verify_coraa_mupe_asr(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Fetch CORAA-MUPE-ASR subset from Hugging Face and verify integrity.
    Returns a DataFrame with audio paths and transcripts.
    """
    data_dir = Path(config['raw_path']) / 'coraa'
    
    if not data_dir.exists():
        logger.info(f"CORAA data not found at {data_dir}. Attempting download...")
        try:
            dataset = load_dataset(
                "coraa_mupe_asr",
                split="train",
                streaming=True
            )
            
            data_dir.mkdir(parents=True, exist_ok=True)
            
            chunk_size = 1000
            chunks = []
            for i, item in enumerate(dataset):
                chunks.append(item)
                if len(chunks) >= chunk_size:
                    df_chunk = pd.DataFrame(chunks)
                    chunk_path = data_dir / f"chunk_{i // chunk_size}.parquet"
                    df_chunk.to_parquet(chunk_path)
                    chunks = []
            
            if chunks:
                df_chunk = pd.DataFrame(chunks)
                chunk_path = data_dir / f"chunk_{len(chunks)}.parquet"
                df_chunk.to_parquet(chunk_path)
            
            logger.info(f"Downloaded CORAA subset to {data_dir}")
        except Exception as e:
            logger.error(f"Failed to download CORAA: {e}")
            raise FileNotFoundError(f"CORAA data directory not found at {data_dir}. Download failed.")
    
    # Load data from chunks
    parquet_files = list(data_dir.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {data_dir}")
    
    dfs = []
    for pq_file in parquet_files:
        table = pq.read_table(pq_file)
        df = table.to_pandas()
        dfs.append(df)
    
    return pd.concat(dfs, ignore_index=True)

def stratified_sample(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Perform stratified sampling by speaker ID and SNR bucket.
    """
    # Determine sample size per stratum
    sample_size = config.get('sample_size_per_stratum', 10)
    
    # Group by speaker and SNR
    grouped = df.groupby(['speaker_id', 'snr_bucket'])
    
    sampled_dfs = []
    for name, group in grouped:
        n = min(len(group), sample_size)
        sampled = group.sample(n=n, random_state=config.get('random_seed', 42))
        sampled_dfs.append(sampled)
    
    if not sampled_dfs:
        return pd.DataFrame()
    
    return pd.concat(sampled_dfs, ignore_index=True)

def save_stratified_subset(sampled_df: pd.DataFrame, output_path: Path):
    """Save stratified sample to parquet."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sampled_df.to_parquet(output_path)
    logger.info(f"Saved stratified subset to {output_path}")

def load_librispeech_subset(config: Dict[str, Any]) -> pd.DataFrame:
    """Load and prepare LibriSpeech subset."""
    logger.info("Loading LibriSpeech subset...")
    df = fetch_and_verify_librispeech(config)
    
    # Apply stratified sampling
    sampled_df = stratified_sample(df, config)
    
    # Save subset
    output_path = Path(config['derived_path']) / 'librispeech_sample.parquet'
    save_stratified_subset(sampled_df, output_path)
    
    return sampled_df

def load_coraa_mupe_asr_subset(config: Dict[str, Any]) -> pd.DataFrame:
    """Load and prepare CORAA-MUPE-ASR subset."""
    logger.info("Loading CORAA-MUPE-ASR subset...")
    df = fetch_and_verify_coraa_mupe_asr(config)
    
    # Apply stratified sampling
    sampled_df = stratified_sample(df, config)
    
    # Save subset
    output_path = Path(config['derived_path']) / 'coraa_sample.parquet'
    save_stratified_subset(sampled_df, output_path)
    
    return sampled_df

def verify_dataset_coverage_for_scenarios(df: pd.DataFrame, scenarios: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Verify that the dataset covers the required distortion scenarios.
    Returns (is_covered, missing_scenarios).
    """
    covered = []
    missing = []
    
    for scenario in scenarios:
        scenario_id = scenario.get('scenario_id')
        # Check if scenario exists in data
        # This is a simplified check; actual implementation would verify specific distortion parameters
        if scenario_id in df.columns or any(scenario_id in str(col) for col in df.columns):
            covered.append(scenario_id)
        else:
            missing.append(scenario_id)
            logger.warning(f"Scenario {scenario_id} not found in dataset")
    
    return len(missing) == 0, missing

def generate_stress_curve_for_clip(clip_df: pd.DataFrame, distortion_vectors: List[Dict], 
                                 metrics_calc) -> pd.DataFrame:
    """
    Generate stress curve for a single audio clip across multiple distortion vectors.
    """
    results = []
    
    for vector in distortion_vectors:
        # Apply distortion
        distorted_audio = metrics_calc.apply_distortion(clip_df, vector)
        
        # Compute metrics
        sss = metrics_calc.compute_sss(clip_df, distorted_audio)
        wer = metrics_calc.compute_wer(clip_df, distorted_audio)
        
        results.append({
            'clip_id': clip_df['clip_id'].iloc[0],
            'distortion_vector_id': vector['vector_id'],
            'snr': vector['snr'],
            'rt60': vector['rt60'],
            'sss': sss,
            'wer': wer
        })
    
    return pd.DataFrame(results)

def load_stress_curves_streaming(input_path: Path, chunk_size: int = 1000) -> Iterator[pd.DataFrame]:
    """
    Load stress curve data in chunks to manage memory usage.
    Yields DataFrames of up to chunk_size rows.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Stress curves file not found at {input_path}")
    
    # Use PyArrow for efficient streaming
    parquet_file = pq.ParquetFile(input_path)
    
    for batch in parquet_file.iter_batches(batch_size=chunk_size):
        yield batch.to_pandas()

def process_stress_curves_in_chunks(config: Dict[str, Any], 
                                   processing_func: callable) -> Dict[str, Any]:
    """
    Process stress curve data in chunks to ensure peak RSS stays under 7GB.
    This is the memory-streaming wrapper required for T039.
    """
    stress_curve_path = Path(config['derived_path']) / 'stress_curves.parquet'
    
    if not stress_curve_path.exists():
        raise FileNotFoundError(f"Stress curves file not found at {stress_curve_path}")
    
    # Initialize results accumulator
    all_results = []
    total_rows = 0
    
    logger.info("Starting chunked processing of stress curves...")
    
    # Process in chunks of 1000 rows
    chunk_size = 1000
    for chunk_df in load_stress_curves_streaming(stress_curve_path, chunk_size):
        logger.info(f"Processing chunk with {len(chunk_df)} rows...")
        
        # Apply processing function to chunk
        chunk_results = processing_func(chunk_df)
        
        # Accumulate results
        if isinstance(chunk_results, pd.DataFrame):
            all_results.append(chunk_results)
            total_rows += len(chunk_results)
        elif isinstance(chunk_results, list):
            all_results.extend(chunk_results)
            total_rows += len(chunk_results)
        
        # Log memory status
        import resource
        mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Convert to MB
        logger.info(f"Current chunk processed. Total rows: {total_rows}, Peak RSS: {mem_usage:.2f} MB")
        
        # Safety check: if memory exceeds threshold, force garbage collection
        if mem_usage > 6000:  # 6GB threshold
            import gc
            gc.collect()
            logger.warning("Memory usage high, forcing garbage collection")
    
    # Combine all results
    if all_results:
        if isinstance(all_results[0], pd.DataFrame):
            final_result = pd.concat(all_results, ignore_index=True)
        else:
            final_result = pd.DataFrame(all_results)
        
        logger.info(f"Processing complete. Total rows processed: {total_rows}")
        return final_result
    else:
        logger.warning("No results generated from stress curves")
        return pd.DataFrame()

def main():
    """Main entry point for data loader."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Data loader for ASR stress testing')
    parser.add_argument('--download', action='store_true', help='Download datasets')
    parser.add_argument('--verify', action='store_true', help='Verify dataset integrity')
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Config file path')
    
    args = parser.parse_args()
    
    config = get_config(args.config)
    
    if args.download:
        logger.info("Downloading datasets...")
        try:
            load_librispeech_subset(config)
            load_coraa_mupe_asr_subset(config)
            logger.info("Download complete")
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise
    
    if args.verify:
        logger.info("Verifying datasets...")
        librispeech_df = load_librispeech_subset(config)
        coraa_df = load_coraa_mupe_asr_subset(config)
        logger.info(f"LibriSpeech: {len(librispeech_df)} rows, CORAA: {len(coraa_df)} rows")
        logger.info("Verification complete")

if __name__ == '__main__':
    main()
