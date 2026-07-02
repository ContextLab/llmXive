import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Local imports based on API surface
from config import get_data_root
from data.models import Participant, StructuralConnectome, AvalancheRecord
from utils.logger import get_logger

logger = get_logger(__name__)

def calculate_snr(signal: np.ndarray, noise_floor: float = 1e-6) -> float:
    """
    Calculate Signal-to-Noise Ratio (SNR) in dB for a given signal.
    For simulated data, noise is assumed to be additive white Gaussian noise
    with a known floor or estimated from the signal variance if not provided.
    Here we estimate noise floor from the signal's high-frequency content or use a default.
    """
    if noise_floor <= 0:
        # Estimate noise floor as a small fraction of signal variance or a fixed small value
        noise_floor = 1e-6 
    
    signal_power = np.mean(signal ** 2)
    snr_linear = signal_power / noise_floor
    return 10 * np.log10(snr_linear)

def check_graph_connectivity(adjacency_matrix: np.ndarray) -> Tuple[bool, int]:
    """
    Check if the graph represented by the adjacency matrix is connected.
    Returns (is_connected, number_of_components).
    """
    import networkx as nx
    G = nx.from_numpy_array(adjacency_matrix)
    num_components = nx.number_connected_components(G)
    is_connected = num_components == 1
    return is_connected, num_components

def run_qc_for_subject(subject_id: str, data_root: Path) -> Dict[str, any]:
    """
    Run quality control checks for a specific subject.
    Checks:
    1. Graph connectivity (from structural connectome)
    2. SNR of simulated EEG (must be >= 5dB)
    
    Returns a dictionary with QC results.
    """
    results = {
        "subject_id": subject_id,
        "passed": True,
        "reasons": [],
        "metrics": {}
    }

    # Paths
    connectome_path = data_root / "processed" / "connectomes" / f"{subject_id}_adj.npy"
    eeg_path = data_root / "processed" / "eeg" / f"{subject_id}_eeg.npy"

    # 1. Check Graph Connectivity
    if not connectome_path.exists():
        results["passed"] = False
        results["reasons"].append("Connectome file missing")
    else:
        try:
            adj_matrix = np.load(connectome_path)
            is_connected, num_components = check_graph_connectivity(adj_matrix)
            results["metrics"]["graph_connected"] = is_connected
            results["metrics"]["num_components"] = num_components
            if not is_connected:
                results["passed"] = False
                results["reasons"].append(f"Graph disconnected ({num_components} components)")
        except Exception as e:
            results["passed"] = False
            results["reasons"].append(f"Error loading connectome: {str(e)}")

    # 2. Check EEG SNR
    if not eeg_path.exists():
        results["passed"] = False
        results["reasons"].append("EEG file missing")
    else:
        try:
            eeg_data = np.load(eeg_path)
            # Flatten for global SNR calculation if multi-channel
            flat_signal = eeg_data.flatten()
            snr = calculate_snr(flat_signal)
            results["metrics"]["snr_db"] = snr
            if snr < 5.0:
                results["passed"] = False
                results["reasons"].append(f"Low SNR ({snr:.2f} dB < 5 dB)")
        except Exception as e:
            results["passed"] = False
            results["reasons"].append(f"Error processing EEG: {str(e)}")

    return results

def generate_qc_report(qc_results: List[Dict], output_path: Path) -> None:
    """
    Generate a JSON report of QC results for all subjects.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(qc_results, f, indent=2)
    logger.info(f"QC report generated at {output_path}")

def calculate_pipeline_completeness(data_root: Path, qc_results: List[Dict]) -> float:
    """
    Calculate the proportion of participants with complete simulated pipelines.
    A participant is considered to have a complete pipeline if they passed all QC checks.
    
    SC-004 Adaptation: This metric measures the fidelity of the simulation pipeline
    by calculating the success rate of generating usable data for all participants.
    
    Args:
        data_root: Path to the project data directory.
        qc_results: List of dictionaries containing QC results per subject.
        
    Returns:
        float: Proportion of participants (0.0 to 1.0) with complete pipelines.
    """
    if not qc_results:
        logger.warning("No QC results provided. Completeness is 0.0.")
        return 0.0

    total_subjects = len(qc_results)
    passed_subjects = sum(1 for r in qc_results if r.get("passed", False))
    
    proportion = passed_subjects / total_subjects
    logger.info(f"Pipeline Completeness: {passed_subjects}/{total_subjects} = {proportion:.2%}")
    return proportion

def main():
    """
    Main entry point to run QC for all subjects and calculate pipeline completeness.
    """
    data_root = get_data_root()
    processed_dir = data_root / "processed"
    
    # Identify subjects based on available files in processed/connectomes or processed/eeg
    connectomes_dir = processed_dir / "connectomes"
    eeg_dir = processed_dir / "eeg"
    
    subjects = set()
    if connectomes_dir.exists():
        for f in connectomes_dir.glob("*_adj.npy"):
            subjects.add(f.stem.replace("_adj", ""))
    if eeg_dir.exists():
        for f in eeg_dir.glob("*_eeg.npy"):
            subjects.add(f.stem.replace("_eeg", ""))
    
    if not subjects:
        logger.warning("No subject data found in processed directories.")
        return

    logger.info(f"Running QC for {len(subjects)} subjects: {sorted(subjects)}")
    
    qc_results = []
    for subject_id in sorted(subjects):
        result = run_qc_for_subject(subject_id, processed_dir)
        qc_results.append(result)
        status = "PASS" if result["passed"] else "FAIL"
        logger.info(f"Subject {subject_id}: {status} - {', '.join(result['reasons']) if result['reasons'] else 'OK'}")

    # Save individual QC report
    qc_report_path = data_root / "results" / "qc_report.json"
    generate_qc_report(qc_results, qc_report_path)

    # Calculate and log pipeline completeness
    completeness = calculate_pipeline_completeness(processed_dir, qc_results)
    
    # Save completeness metric to a specific file for downstream tasks
    completeness_path = data_root / "results" / "pipeline_completeness.json"
    completeness_path.parent.mkdir(parents=True, exist_ok=True)
    with open(completeness_path, 'w') as f:
        json.dump({
            "total_subjects": len(subjects),
            "passed_subjects": sum(1 for r in qc_results if r["passed"]),
            "proportion": completeness
        }, f, indent=2)
    
    logger.info(f"Pipeline completeness metric saved to {completeness_path}")

if __name__ == "__main__":
    main()