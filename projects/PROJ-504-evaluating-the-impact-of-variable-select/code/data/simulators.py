from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Generator

import numpy as np
import pandas as pd

from config import get_config
from data.downloader import DatasetMetadata
from models import SimulatedDataset
from utils.logger import get_logger
from utils.config_limits import get_memory_limit_gb, get_resource_monitor

logger = get_logger(__name__)


@dataclass
class SimulatorConfig:
    """Configuration for the simulation loop."""
    snr_levels: List[float] = field(default_factory=list)
    sparsity_levels: List[float] = field(default_factory=list)
    seed: int = 42
    output_path: str = "data/processed"
    chunk_size: int = 1000  # Number of simulations per chunk to manage memory
    max_retries: int = 3

def get_default_snr_levels() -> List[float]:
    """Return default SNR levels for the study."""
    return [0.1, 1.0, 10.0, 100.0]

def get_default_sparsity_levels() -> List[float]:
    """Return default sparsity levels (proportion of non-zero coefficients)."""
    return [0.1, 0.3, 0.5, 0.7]

def get_simulator_config() -> SimulatorConfig:
    """Load simulator configuration from the global config."""
    cfg = get_config()
    return SimulatorConfig(
        snr_levels=cfg.get("snr_levels", get_default_snr_levels()),
        sparsity_levels=cfg.get("sparsity_levels", get_default_sparsity_levels()),
        seed=cfg.get("seed", 42),
        output_path=cfg.get("output_path", "data/processed"),
        chunk_size=cfg.get("chunk_size", 1000),
    )

def _calculate_noise_scale(X: np.ndarray, true_beta: np.ndarray, snr: float) -> float:
    """
    Calculate the noise standard deviation (sigma) to achieve the target SNR.
    SNR = Var(X @ beta) / Var(epsilon)
    """
    signal = X @ true_beta
    signal_var = np.var(signal)
    if signal_var < 1e-8:
        return 1.0  # Fallback to avoid division by zero if signal is flat
    sigma = np.sqrt(signal_var / snr)
    return sigma

def generate_synthetic_outcomes(
    dataset_meta: DatasetMetadata,
    snr: float,
    sparsity: float,
    seed: int,
    n_simulations: int = 100
) -> Generator[SimulatedDataset, None, None]:
    """
    Generate synthetic outcome vectors Y for a given dataset configuration.
    
    This generator yields SimulatedDataset objects containing:
    - The original X matrix (from the real dataset)
    - The generated Y vector
    - The ground-truth coefficients used
    - Metadata (SNR, sparsity, seed, dataset_id)
    
    Args:
        dataset_meta: Metadata and X matrix from the downloader.
        snr: Signal-to-Noise ratio.
        sparsity: Proportion of non-zero coefficients.
        seed: Random seed for this specific simulation run.
        n_simulations: Number of Y vectors to generate for this config.
        
    Yields:
        SimulatedDataset objects.
    """
    rng = np.random.default_rng(seed)
    X = dataset_meta.X
    n_samples, n_features = X.shape
    
    # Determine number of non-zero coefficients
    n_nonzero = max(1, int(n_features * sparsity))
    
    # Pre-allocate arrays for efficiency if needed, but we yield per simulation
    for i in range(n_simulations):
        # Set seed for this specific simulation to ensure reproducibility
        sim_seed = seed + i
        sim_rng = np.random.default_rng(sim_seed)
        
        # 1. Generate ground-truth coefficients
        # Randomly select indices for non-zero coefficients
        nonzero_indices = sim_rng.choice(n_features, size=n_nonzero, replace=False)
        true_beta = np.zeros(n_features)
        
        # Assign random values to non-zero coefficients (standard normal)
        true_beta[nonzero_indices] = sim_rng.standard_normal(n_nonzero)
        
        # 2. Calculate signal variance and noise scale
        signal = X @ true_beta
        signal_var = np.var(signal)
        
        if signal_var < 1e-9:
            # If signal is essentially zero, skip to avoid NaN/Inf
            logger.warning(f"Signal variance too low for dataset {dataset_meta.id}, SNR {snr}, Sparsity {sparsity}. Skipping.")
            continue
            
        sigma = np.sqrt(signal_var / snr)
        
        # 3. Generate noise and Y
        epsilon = sim_rng.normal(0, sigma, size=n_samples)
        Y = signal + epsilon
        
        yield SimulatedDataset(
            X=X,
            Y=Y,
            true_coefficients=true_beta,
            snr=snr,
            sparsity=sparsity,
            seed=sim_seed,
            dataset_id=dataset_meta.id,
            simulation_index=i
        )

def _save_simulation_chunk(
    results: List[SimulatedDataset],
    chunk_id: int,
    config: SimulatorConfig
) -> str:
    """
    Save a chunk of simulation results to disk.
    Records true coefficients and metadata for every run as required by T017.
    """
    os.makedirs(config.output_path, exist_ok=True)
    
    # Flatten the data for CSV/Parquet storage
    records = []
    for ds in results:
        # Convert coefficients to a JSON-serializable string or list
        # Storing as a list of floats in a single column is often best for Parquet
        coeff_list = ds.true_coefficients.tolist()
        
        records.append({
            "dataset_id": ds.dataset_id,
            "snr": ds.snr,
            "sparsity": ds.sparsity,
            "seed": ds.seed,
            "simulation_index": ds.simulation_index,
            "n_samples": ds.X.shape[0],
            "n_features": ds.X.shape[1],
            "true_coefficients": coeff_list,
            "true_nonzero_count": int(np.count_nonzero(ds.true_coefficients)),
            "true_nonzero_indices": np.where(ds.true_coefficients != 0)[0].tolist(),
            # We do NOT store the full X and Y matrices here to save space.
            # They are regenerated or stored separately if needed for downstream analysis.
            # T017 specifically asks to record true coefficients and metadata.
        })
    
    df = pd.DataFrame(records)
    filename = f"simulations_chunk_{chunk_id}.parquet"
    filepath = os.path.join(config.output_path, filename)
    
    # Use Snappy compression for efficiency
    df.to_parquet(filepath, compression='snappy', index=False)
    logger.info(f"Saved simulation chunk {chunk_id} to {filepath} ({len(records)} records)")
    
    return filepath

def main() -> None:
    """
    Main entry point for the simulation pipeline.
    Iterates over loaded datasets, SNR, and Sparsity levels.
    Generates synthetic Y vectors and records true coefficients/metadata.
    """
    config = get_simulator_config()
    logger.info(f"Starting simulation with config: SNR={config.snr_levels}, Sparsity={config.sparsity_levels}")
    
    # Ensure output directory exists
    os.makedirs(config.output_path, exist_ok=True)
    
    # Load datasets (assuming downloader has populated data/raw or similar)
    # In a real pipeline, we might load from a manifest or re-fetch
    # For this task, we assume fetch_datasets is available and returns valid metadata
    from data.downloader import fetch_datasets
    
    # Fetch datasets (this might be cached or re-run depending on implementation)
    # We filter for those already downloaded if possible, but fetch_datasets handles logic
    datasets = fetch_datasets()
    
    if not datasets:
        logger.error("No datasets found. Cannot proceed with simulation.")
        return

    logger.info(f"Found {len(datasets)} datasets to process.")
    
    total_simulations = 0
    chunk_buffer: List[SimulatedDataset] = []
    chunk_id = 0
    
    # Monitor memory
    memory_limit_gb = get_memory_limit_gb()
    monitor = get_resource_monitor()
    
    for ds_meta in datasets:
        logger.info(f"Processing dataset: {ds_meta.id} (rows={ds_meta.n_rows}, features={ds_meta.n_features})")
        
        for snr in config.snr_levels:
            for sparsity in config.sparsity_levels:
                # Define number of simulations per condition
                # For a full study, this might be 100-1000. 
                # We use a reasonable default for the pipeline.
                sims_per_condition = 50 
                
                logger.debug(f"Running {sims_per_condition} simulations for SNR={snr}, Sparsity={sparsity}")
                
                gen = generate_synthetic_outcomes(
                    dataset_meta=ds_meta,
                    snr=snr,
                    sparsity=sparsity,
                    seed=config.seed,
                    n_simulations=sims_per_condition
                )
                
                for sim_data in gen:
                    chunk_buffer.append(sim_data)
                    total_simulations += 1
                    
                    # Check memory pressure
                    current_mem_gb = monitor.get_memory_usage_gb()
                    if current_mem_gb > memory_limit_gb * 0.8:
                        logger.warning(f"Memory usage high ({current_mem_gb:.2f}GB). Flushing buffer.")
                        if chunk_buffer:
                            _save_simulation_chunk(chunk_buffer, chunk_id, config)
                            chunk_buffer = []
                            chunk_id += 1
                    
                    # Flush buffer if it reaches chunk size
                    if len(chunk_buffer) >= config.chunk_size:
                        _save_simulation_chunk(chunk_buffer, chunk_id, config)
                        chunk_buffer = []
                        chunk_id += 1
    
    # Save any remaining buffer
    if chunk_buffer:
        _save_simulation_chunk(chunk_buffer, chunk_id, config)
        chunk_id += 1
        
    logger.info(f"Simulation complete. Total records generated: {total_simulations}.")
    logger.info(f"Output files saved to: {config.output_path}")

if __name__ == "__main__":
    main()