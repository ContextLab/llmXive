"""
Quality Control Module for Neural Avalanche Dynamics Pipeline.

This module implements quality control checks to exclude participants with:
1. Disconnected structural graphs (SC-004 adaptation).
2. Insufficient data quality, defined as channels with SNR < 5dB in simulated EEG data.

It calculates pipeline completeness and generates QC reports.
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import from sibling modules based on provided API surface
from data.models import Participant, StructuralConnectome, AvalancheRecord
from utils.logger import get_logger, ResearchError

logger = get_logger(__name__)

# Constants
SNR_THRESHOLD_DB: float = 5.0
MIN_SUBJECTS_REQUIRED: int = 10


def calculate_snr(signal: np.ndarray, noise_estimate: Optional[np.ndarray] = None) -> float:
    """
    Calculate the Signal-to-Noise Ratio (SNR) in decibels (dB).

    For simulated data, if no explicit noise vector is provided, noise is estimated
    as the high-frequency residual or a standard deviation of the baseline if available.
    In this simulation context, we estimate noise as the standard deviation of the
    signal itself (assuming the signal contains both 'neural' and 'noise' components,
    or using a proxy if the simulation output includes a noise term).

    However, for a robust simulation fidelity check as per T012, we assume the
    'signal' provided is the raw simulated EEG. If the simulation model (Wilson-Cowan)
    adds explicit noise, we can separate it. If not, we use a heuristic:
    SNR (dB) = 10 * log10(P_signal / P_noise)

    For this implementation, we assume the input `signal` is the raw time series.
    If `noise_estimate` is not provided, we estimate noise power as 10% of signal power
    (a conservative assumption for high-fidelity simulation) or use the standard
    deviation of the signal if the signal is dominated by noise (unlikely here).

    A more rigorous approach for simulated data:
    If the simulator outputs (state, noise), we use them.
    Since we only receive the final time series here, we calculate SNR based on
    the ratio of the signal variance to a baseline noise floor estimate.

    Args:
        signal: The EEG time series array.
        noise_estimate: Optional array of noise samples. If None, estimated.

    Returns:
        SNR in dB.
    """
    if signal.size == 0:
        return -np.inf

    signal_power = np.mean(signal ** 2)
    
    if noise_estimate is not None:
        if noise_estimate.size == 0:
            return np.inf
        noise_power = np.mean(noise_estimate ** 2)
    else:
        # Heuristic for simulated data without explicit noise separation:
        # Assume a baseline noise floor. If the simulation is high quality,
        # the 'noise' is small relative to the structured dynamics.
        # We estimate noise as the high-frequency component or a fixed fraction.
        # To be conservative and detect 'insufficient quality' (low SNR),
        # we assume a noise floor of 10% of the signal RMS if not provided.
        # This allows the function to detect if the signal is essentially flat or noisy.
        # A better approach for T012: The simulator should ideally output SNR.
        # If not, we check if the signal variance is too low (flat) or too erratic.
        # Let's use a standard deviation based estimate:
        # If the signal is purely random noise, SNR ~ 0dB.
        # If it has structure, SNR > 0dB.
        # We'll estimate noise as the standard deviation of the signal filtered by a high-pass.
        # For simplicity in this QC step, we assume the 'signal' passed here is the
        # raw output. We estimate noise as 10% of the signal's RMS power as a default
        # 'good' simulation floor, but if the calculated SNR (using this estimate)
        # is low, it implies the signal is weak or the noise assumption is wrong.
        
        # Actually, let's follow the prompt's definition: "channels with SNR < 5dB".
        # This implies we need a way to measure it.
        # If the simulation adds known noise, we should have access to it.
        # Since we don't, we will estimate noise power as the variance of the signal
        # after removing the mean and low-frequency trends, or simply assume a 
        # fixed noise floor if the signal is very strong.
        
        # Robust estimation: Use the median absolute deviation (MAD) to estimate noise.
        # Noise is often the high-frequency component.
        # Let's assume the signal has a mean of 0 (centered).
        # We estimate noise as the standard deviation of the signal.
        # If the signal is structured, this is an overestimate of noise, leading to lower SNR.
        # This is safe for QC: if the calculated SNR is < 5dB even with this conservative
        # noise estimate, the channel is definitely bad.
        
        # Alternative: If the simulation output includes a 'noise' parameter, use it.
        # Since we don't have it here, we assume the 'signal' is the clean output + noise.
        # We will estimate noise power as the variance of the signal multiplied by a small factor
        # representing the expected noise floor in a good simulation, or use a fixed value.
        # To be strictly compliant with "SNR < 5dB", we need a calculation.
        # Let's assume the 'signal' is the raw data. We estimate noise as the standard deviation
        # of the signal. This is a lower bound on SNR.
        
        # Correct approach for simulated data QC:
        # If the simulation is `x = dynamics + noise`, and we only have `x`.
        # We can't separate them perfectly without knowing the dynamics model state.
        # However, the task asks to exclude channels with SNR < 5dB.
        # We will calculate SNR as: 10 * log10(var(signal) / var(noise_estimate)).
        # If noise_estimate is None, we estimate it as 0.1 * var(signal) (assuming 10% noise floor).
        # If the resulting SNR is < 5dB, it means the signal is weak or the noise is high.
        
        # Let's use a standard heuristic: Noise is estimated as the high-frequency content.
        # We'll use a simple difference filter to estimate noise.
        noise_estimate = np.diff(signal)
        noise_power = np.mean(noise_estimate ** 2) / 2.0  # Approximate power of difference
        
        # If noise_power is 0 (flat signal), SNR is infinite (good) or undefined.
        # If signal_power is 0, SNR is -inf.
        if noise_power < 1e-12:
            noise_power = 1e-12
        
        # Re-calculate signal power to be safe
        signal_power = np.mean(signal ** 2)
        if signal_power < 1e-12:
            return -np.inf

    snr_linear = signal_power / noise_power
    snr_db = 10 * np.log10(snr_linear)
    return snr_db


def check_graph_connectivity(adjacency_matrix: np.ndarray) -> Tuple[bool, int]:
    """
    Check if the structural connectome graph is connected.

    Args:
        adjacency_matrix: N x N adjacency matrix (weighted or binary).

    Returns:
        Tuple of (is_connected, number_of_components).
    """
    if adjacency_matrix.size == 0:
        return False, 0

    # Convert to binary for connectivity check
    binary_adj = (adjacency_matrix > 0).astype(int)
    
    # Use networkx for connectivity check (imported in metrics.py, but we can import here too)
    # However, to avoid heavy imports in QC if possible, we can use scipy or simple BFS.
    # Let's use scipy.sparse.csgraph if available, or networkx.
    # Given the project uses networkx in metrics.py, we assume it's available.
    try:
        import networkx as nx
        G = nx.from_numpy_array(binary_adj)
        num_components = nx.number_connected_components(G)
        is_connected = (num_components == 1)
        return is_connected, num_components
    except ImportError:
        # Fallback to simple BFS if networkx is missing (unlikely given dependencies)
        # Or raise an error.
        raise ResearchError("NetworkX is required for connectivity check.")


def run_qc_for_subject(
    subject_id: str,
    adjacency_matrix: np.ndarray,
    eeg_data: np.ndarray,
    snr_threshold: float = SNR_THRESHOLD_DB
) -> Dict[str, any]:
    """
    Run quality control checks for a single subject.

    Checks:
    1. Graph Connectivity: Is the structural connectome connected?
    2. Channel SNR: Are there channels with SNR < 5dB?

    Args:
        subject_id: Unique identifier for the subject.
        adjacency_matrix: N x N structural connectivity matrix.
        eeg_data: M x T matrix of EEG time series (M channels, T time points).
        snr_threshold: Minimum SNR in dB required for a channel to be kept.

    Returns:
        Dictionary containing:
            - subject_id
            - passed_qc: bool (True if all checks pass)
            - graph_connected: bool
            - num_components: int
            - removed_channels: List[int] (indices of channels with low SNR)
            - snr_values: List[float] (SNR for each channel)
            - reason: str (if failed)
    """
    result = {
        "subject_id": subject_id,
        "passed_qc": True,
        "graph_connected": True,
        "num_components": 0,
        "removed_channels": [],
        "snr_values": [],
        "reason": ""
    }

    # 1. Check Graph Connectivity
    is_connected, num_components = check_graph_connectivity(adjacency_matrix)
    result["graph_connected"] = is_connected
    result["num_components"] = num_components

    if not is_connected:
        result["passed_qc"] = False
        result["reason"] = f"Graph is disconnected ({num_components} components)."
        # Even if graph is disconnected, we might still want to check EEG, 
        # but the task says "exclude participants with disconnected graphs".
        # So we can return early or continue to log. We'll mark as failed.

    # 2. Check Channel SNR
    num_channels = eeg_data.shape[0]
    snr_values = []
    removed_channels = []

    for ch_idx in range(num_channels):
        channel_signal = eeg_data[ch_idx, :]
        snr = calculate_snr(channel_signal)
        snr_values.append(snr)

        if snr < snr_threshold:
            removed_channels.append(ch_idx)

    result["snr_values"] = snr_values
    result["removed_channels"] = removed_channels

    if len(removed_channels) > 0:
        if not result["passed_qc"]:
            result["reason"] += f" Also, {len(removed_channels)} channels have SNR < {snr_threshold}dB."
        else:
            result["passed_qc"] = False
            result["reason"] = f"{len(removed_channels)} channels have SNR < {snr_threshold}dB."

    return result


def generate_qc_report(
    qc_results: List[Dict[str, any]],
    output_path: Path
) -> None:
    """
    Generate a JSON report of QC results for all subjects.

    Args:
        qc_results: List of dictionaries from run_qc_for_subject.
        output_path: Path to save the JSON report.
    """
    report = {
        "total_subjects": len(qc_results),
        "subjects_passed": sum(1 for r in qc_results if r["passed_qc"]),
        "subjects_failed": sum(1 for r in qc_results if not r["passed_qc"]),
        "details": qc_results
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"QC report generated at {output_path}")


def calculate_pipeline_completeness(
    qc_results: List[Dict[str, any]],
    total_subjects: int
) -> float:
    """
    Calculate the proportion of participants with complete pipelines.

    Args:
        qc_results: List of QC result dictionaries.
        total_subjects: Total number of subjects attempted.

    Returns:
        Proportion (0.0 to 1.0) of subjects that passed QC.
    """
    if total_subjects == 0:
        return 0.0
    passed_count = sum(1 for r in qc_results if r["passed_qc"])
    return passed_count / total_subjects


def main():
    """
    Main entry point for running QC on the dataset.
    Assumes data has been processed and stored by T010 and T011.
    """
    from config import get_data_root
    
    data_root = get_data_root()
    processed_dir = data_root / "processed"
    results_dir = data_root / "results"
    
    # Load subject list (assuming stored in a manifest or inferred from files)
    # For this implementation, we iterate over known subjects or a manifest.
    # Let's assume a manifest exists or we scan the directory.
    # Since T010/T011 might have generated files, we look for them.
    
    # Example: Scan for adjacency matrices and EEG files
    # Assuming files are named: sub-{id}_connectome.npy, sub-{id}_eeg.npy
    
    subject_ids = []
    # This is a placeholder for actual file discovery logic
    # In a real run, this would scan the directory
    import glob
    conn_files = list((processed_dir / "connectomes").glob("sub-*_connectome.npy"))
    for f in conn_files:
        sid = f.stem.replace("_connectome", "")
        subject_ids.append(sid)
    
    if not subject_ids:
        logger.warning("No subject data found for QC.")
        return

    qc_results = []
    
    for sid in subject_ids:
        logger.info(f"Running QC for subject {sid}")
        
        try:
            # Load data
            conn_path = processed_dir / "connectomes" / f"{sid}_connectome.npy"
            eeg_path = processed_dir / "eeg" / f"{sid}_eeg.npy"
            
            if not conn_path.exists() or not eeg_path.exists():
                logger.warning(f"Data missing for {sid}, skipping.")
                continue
                
            adj_mat = np.load(conn_path)
            eeg_data = np.load(eeg_path)
            
            # Run QC
            result = run_qc_for_subject(sid, adj_mat, eeg_data)
            qc_results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing {sid}: {e}")
            qc_results.append({
                "subject_id": sid,
                "passed_qc": False,
                "reason": f"Processing error: {str(e)}"
            })

    # Generate Report
    report_path = results_dir / "qc_report.json"
    generate_qc_report(qc_results, report_path)

    # Calculate completeness
    completeness = calculate_pipeline_completeness(qc_results, len(subject_ids))
    logger.info(f"Pipeline completeness: {completeness:.2%}")

    # Filter out failed subjects for downstream tasks (if needed)
    # This function is typically called by the main pipeline to decide which subjects to use.
    # We return the list of passed subjects here for demonstration.
    passed_subjects = [r["subject_id"] for r in qc_results if r["passed_qc"]]
    logger.info(f"Passed subjects: {passed_subjects}")
    
    return qc_results

if __name__ == "__main__":
    main()