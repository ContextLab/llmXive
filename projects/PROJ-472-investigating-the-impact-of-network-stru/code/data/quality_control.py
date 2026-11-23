"""
Quality Control Module for Neural Avalanche Dynamics Pipeline.

This module implements rigorous quality control checks for both real and simulated
data pipelines. It ensures data integrity, graph connectivity, and pipeline completeness.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import networkx as nx

from config import get_data_root
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants
CHANNEL_REMOVAL_THRESH = 0.30  # 30% threshold for real EEG
CONNECTIVITY_MIN_NODES = 5     # Minimum nodes for a valid graph (simulated)

def calculate_snr(eeg_signal: np.ndarray, noise_window: Tuple[int, int] = (0, 100)) -> float:
    """
    Calculate Signal-to-Noise Ratio for EEG data.
    
    Args:
        eeg_signal: 1D or 2D numpy array of EEG data.
        noise_window: Tuple (start, end) indices for noise estimation.
        
    Returns:
        SNR value as float.
    """
    if eeg_signal.ndim == 2:
        eeg_signal = eeg_signal.mean(axis=0)  # Average over channels if 2D
        
    signal_power = np.var(eeg_signal)
    noise_segment = eeg_signal[noise_window[0]:noise_window[1]]
    noise_power = np.var(noise_segment)
    
    if noise_power == 0:
        return float('inf')
        
    return float(signal_power / noise_power)

def check_graph_connectivity(connectome_path: Path) -> Tuple[bool, int]:
    """
    Check if a structural connectome graph is fully connected.
    
    Args:
        connectome_path: Path to the connectome TSV file.
        
    Returns:
        Tuple of (is_connected, num_components).
    """
    if not connectome_path.exists():
        logger.error(f"Connectome file not found: {connectome_path}")
        return False, 0
        
    try:
        # Load connectome
        df = pd.read_csv(connectome_path, sep='\t', header=None)
        # Assuming format: source, target, weight
        # Create graph
        G = nx.from_pandas_edgelist(
            df, 
            source=0, 
            target=1, 
            edge_attr=2,
            create_using=nx.Graph()
        )
        
        num_components = nx.number_connected_components(G)
        is_connected = (num_components == 1)
        
        return is_connected, num_components
        
    except Exception as e:
        logger.error(f"Error checking connectivity for {connectome_path}: {e}")
        return False, 0

def check_real_eeg_quality(eeg_path: Path) -> Dict[str, Any]:
    """
    Check quality metrics for real EEG data.
    
    Args:
        eeg_path: Path to cleaned EEG file (.fif).
        
    Returns:
        Dictionary with quality metrics.
    """
    try:
        import mne
        raw = mne.io.read_raw_fif(eeg_path, preload=True)
        info = raw.info
        
        # Count channels
        total_channels = len(info['ch_names'])
        
        # Check for bad channels
        bad_channels = info['bads']
        n_bad = len(bad_channels)
        removal_ratio = n_bad / total_channels if total_channels > 0 else 1.0
        
        # Calculate SNR
        data = raw.get_data()
        snr = calculate_snr(data)
        
        is_valid = removal_ratio <= CHANNEL_REMOVAL_THRESH
        
        return {
            'is_valid': is_valid,
            'total_channels': total_channels,
            'bad_channels': n_bad,
            'removal_ratio': removal_ratio,
            'snr': snr,
            'reason': 'Too many channels removed' if not is_valid else 'Pass'
        }
        
    except Exception as e:
        logger.error(f"Error processing real EEG {eeg_path}: {e}")
        return {
            'is_valid': False,
            'total_channels': 0,
            'bad_channels': 0,
            'removal_ratio': 1.0,
            'snr': 0.0,
            'reason': f'Error: {str(e)}'
        }

def check_simulated_eeg_quality(
    connectome_path: Path, 
    eeg_path: Path
) -> Dict[str, Any]:
    """
    Check quality metrics for simulated EEG data.
    
    Args:
        connectome_path: Path to structural connectome.
        eeg_path: Path to simulated EEG file.
        
    Returns:
        Dictionary with quality metrics.
    """
    # Check graph connectivity
    is_connected, n_components = check_graph_connectivity(connectome_path)
    
    # Check if EEG file exists
    eeg_exists = eeg_path.exists()
    
    is_valid = is_connected and eeg_exists
    
    return {
        'is_valid': is_valid,
        'is_connected': is_connected,
        'n_components': n_components,
        'eeg_exists': eeg_exists,
        'reason': (
            'Disconnected graph' if not is_connected and not eeg_exists else
            'Disconnected graph' if not is_connected else
            'Missing EEG file' if not eeg_exists else
            'Pass'
        )
    }

def run_qc_for_subject(
    subject_id: str, 
    data_type: str = 'simulated'
) -> Dict[str, Any]:
    """
    Run quality control checks for a single subject.
    
    Args:
        subject_id: Subject identifier.
        data_type: 'real' or 'simulated'.
        
    Returns:
        QC results dictionary.
    """
    data_root = get_data_root()
    results = {
        'subject_id': subject_id,
        'data_type': data_type,
        'passed': False
    }
    
    if data_type == 'real':
        eeg_path = data_root / 'processed' / 'eeg' / f'sub-{subject_id}' / 'eeg_cleaned.fif'
        if eeg_path.exists():
            qc_result = check_real_eeg_quality(eeg_path)
            results.update(qc_result)
            results['passed'] = qc_result['is_valid']
        else:
            results['passed'] = False
            results['reason'] = 'EEG file not found'
            
    elif data_type == 'simulated':
        connectome_path = data_root / 'processed' / 'connectomes' / f'sub-{subject_id}' / 'connectome.tsv'
        eeg_path = data_root / 'processed' / 'eeg' / f'sub-{subject_id}' / 'eeg_simulated.fif'
        
        if connectome_path.exists() and eeg_path.exists():
            qc_result = check_simulated_eeg_quality(connectome_path, eeg_path)
            results.update(qc_result)
            results['passed'] = qc_result['is_valid']
        else:
            results['passed'] = False
            results['reason'] = 'Missing files'
            
    else:
        logger.error(f"Unknown data type: {data_type}")
        results['passed'] = False
        results['reason'] = 'Invalid data type'
        
    return results

def calculate_pipeline_completeness(
    routing_state_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Calculate the proportion of participants with complete pipelines.
    
    This implements SC-004: Measures the ratio of usable subjects to total
    subjects attempted, treating simulation generation as a valid pipeline.
    
    Args:
        routing_state_path: Optional path to routing_state.json.
        
    Returns:
        Dictionary with completeness metrics.
    """
    if routing_state_path is None:
        routing_state_path = get_data_root() / 'processed' / 'routing_state.json'
        
    if not routing_state_path.exists():
        logger.warning(f"Routing state not found: {routing_state_path}")
        return {
            'total_subjects': 0,
            'usable_subjects': 0,
            'completeness_ratio': 0.0,
            'status': 'error'
        }
        
    try:
        with open(routing_state_path, 'r') as f:
            routing_state = json.load(f)
            
        data_root = get_data_root()
        eeg_dir = data_root / 'processed' / 'eeg'
        connectomes_dir = data_root / 'processed' / 'connectomes'
        
        # Get all subject directories
        all_subjects = []
        if eeg_dir.exists():
            all_subjects = [
                d.name for d in eeg_dir.iterdir() 
                if d.is_dir() and d.name.startswith('sub-')
            ]
            
        total_subjects = len(all_subjects)
        usable_subjects = []
        
        for subj in all_subjects:
            # Determine data type from routing state
            is_simulated = routing_state.get('simulation_required', False)
            
            # Run QC for this subject
            qc_result = run_qc_for_subject(
                subj.replace('sub-', ''), 
                'simulated' if is_simulated else 'real'
            )
            
            if qc_result['passed']:
                usable_subjects.append(subj)
                
        usable_count = len(usable_subjects)
        completeness_ratio = usable_count / total_subjects if total_subjects > 0 else 0.0
        
        # Save usable subjects list
        usable_path = data_root / 'processed' / 'usable_subjects.json'
        with open(usable_path, 'w') as f:
            json.dump({
                'subject_ids': [s.replace('sub-', '') for s in usable_subjects],
                'total_subjects': total_subjects,
                'usable_subjects': usable_count,
                'completeness_ratio': completeness_ratio
            }, f, indent=2)
            
        logger.info(f"Pipeline completeness: {usable_count}/{total_subjects} ({completeness_ratio:.2%})")
        
        return {
            'total_subjects': total_subjects,
            'usable_subjects': usable_count,
            'completeness_ratio': completeness_ratio,
            'status': 'complete' if total_subjects > 0 else 'no_data'
        }
        
    except Exception as e:
        logger.error(f"Error calculating pipeline completeness: {e}")
        return {
            'total_subjects': 0,
            'usable_subjects': 0,
            'completeness_ratio': 0.0,
            'status': 'error',
            'error': str(e)
        }

def generate_qc_report(
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a comprehensive QC report for all subjects.
    
    Args:
        output_path: Optional output path for the report.
        
    Returns:
        Path to the generated report.
    """
    if output_path is None:
        output_path = get_data_root() / 'processed' / 'qc_report.json'
        
    data_root = get_data_root()
    routing_state_path = data_root / 'processed' / 'routing_state.json'
    
    # Get all subjects
    all_subjects = []
    eeg_dir = data_root / 'processed' / 'eeg'
    if eeg_dir.exists():
        all_subjects = [
            d.name for d in eeg_dir.iterdir() 
            if d.is_dir() and d.name.startswith('sub-')
        ]
        
    results = []
    for subj in all_subjects:
        # Determine data type
        is_simulated = False
        if routing_state_path.exists():
            try:
                with open(routing_state_path, 'r') as f:
                    state = json.load(f)
                    is_simulated = state.get('simulation_required', False)
            except:
                pass
                
        qc_result = run_qc_for_subject(
            subj.replace('sub-', ''), 
            'simulated' if is_simulated else 'real'
        )
        results.append(qc_result)
        
    report = {
        'total_subjects': len(results),
        'passed_subjects': sum(1 for r in results if r['passed']),
        'failed_subjects': sum(1 for r in results if not r['passed']),
        'subjects': results
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"QC report generated: {output_path}")
    return output_path

def main():
    """Main entry point for quality control pipeline."""
    logger.info("Starting quality control pipeline...")
    
    # Calculate completeness
    completeness = calculate_pipeline_completeness()
    logger.info(f"Pipeline completeness: {completeness}")
    
    # Generate report
    report_path = generate_qc_report()
    logger.info(f"QC report saved to: {report_path}")
    
    # Output usable subjects count
    usable_path = get_data_root() / 'processed' / 'usable_subjects.json'
    if usable_path.exists():
        with open(usable_path, 'r') as f:
            usable_data = json.load(f)
            logger.info(f"Usable subjects: {usable_data['usable_subjects']} / {usable_data['total_subjects']}")
    
    logger.info("Quality control pipeline completed.")
    return completeness

if __name__ == '__main__':
    main()