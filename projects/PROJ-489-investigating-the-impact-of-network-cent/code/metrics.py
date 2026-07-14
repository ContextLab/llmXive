"""
Network Centrality and Neural Synchrony Metrics Module.

This module provides functions to compute functional connectivity matrices,
network centrality metrics, and neural synchrony scores (Phase Lag Index)
from EEG data. It also handles validation and aggregation of these metrics.

Functions:
    compute_waking_connectivity: Compute coherence-based connectivity matrix.
    validate_connectivity_matrix: Check matrix symmetry and value range.
    compute_centralities: Calculate degree, betweenness, and eigenvector centrality.
    compute_pli: Calculate Phase Lag Index for signal pairs.
    aggregate_pli_to_global: Average PLI scores across epochs and pairs.
    calculate_vif: Compute Variance Inflation Factor for centrality metrics.
    generate_subject_metrics_csv: Compile metrics into a DataFrame and save to CSV.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import pandas as pd
import mne
from scipy.signal import welch, coherency
import networkx as nx
from statsmodels.stats.outliers_influence import variance_inflation_factor

logger = logging.getLogger(__name__)


def compute_waking_connectivity(
    raw: mne.io.BaseRaw,
    band: Tuple[float, float] = (4.0, 13.0),
    fmin: float = 1.0,
    fmax: float = 40.0
) -> np.ndarray:
    """
    Compute functional connectivity matrix using coherence for waking data.

    Extracts EEG channels, computes coherence in specified frequency bands
    (theta and alpha), and returns a symmetric connectivity matrix.

    Args:
        raw: MNE Raw object containing EEG data.
        band: Frequency band tuple (f_min, f_max) for coherence calculation.
            Defaults to (4.0, 13.0) covering theta and alpha.
        fmin: Minimum frequency for spectral estimation (Hz).
        fmax: Maximum frequency for spectral estimation (Hz).

    Returns:
        np.ndarray: Symmetric connectivity matrix of shape (n_channels, n_channels).
                    Values represent coherence (0.0 to 1.0).
    """
    # Extract EEG channels
    eeg_channels = raw.copy().pick_types(eeg=True)
    data = eeg_channels.get_data()
    sfreq = eeg_channels.info['sfreq']
    ch_names = eeg_channels.ch_names
    n_channels = len(ch_names)

    logger.info(f"Computing connectivity for {n_channels} channels.")

    # Initialize connectivity matrix
    conn_matrix = np.zeros((n_channels, n_channels))

    # Compute coherence for each pair
    for i in range(n_channels):
        for j in range(i, n_channels):
            if i == j:
                conn_matrix[i, j] = 1.0
                continue

            try:
                # Use MNE's coherence function
                f, Cxy = coherency(
                    data[i], data[j],
                    fs=sfreq,
                    nperseg=int(2 * sfreq),  # 2-second windows
                    noverlap=int(sfreq),       # 50% overlap
                    fmin=band[0],
                    fmax=band[1]
                )
                # Average coherence across frequencies in band
                coherence_val = np.mean(np.abs(Cxy))
                conn_matrix[i, j] = coherence_val
                conn_matrix[j, i] = coherence_val
            except Exception as e:
                logger.warning(f"Coherence calculation failed for pair ({i}, {j}): {e}")
                conn_matrix[i, j] = 0.0
                conn_matrix[j, i] = 0.0

    return conn_matrix


def validate_connectivity_matrix(matrix: np.ndarray) -> Tuple[bool, str]:
    """
    Validate that a connectivity matrix is symmetric and values are in [0, 1].

    Args:
        matrix: 2D numpy array representing the connectivity matrix.

    Returns:
        Tuple[bool, str]: (is_valid, message).
            is_valid: True if matrix is symmetric and values are in [0, 1].
            message: Description of validation result or error.
    """
    if not isinstance(matrix, np.ndarray) or matrix.ndim != 2:
        return False, "Matrix must be a 2D numpy array."

    n, m = matrix.shape
    if n != m:
        return False, f"Matrix must be square. Got shape {matrix.shape}."

    # Check symmetry
    if not np.allclose(matrix, matrix.T):
        return False, "Matrix is not symmetric."

    # Check value range
    if np.any(matrix < 0) or np.any(matrix > 1):
        return False, "Matrix values must be between 0 and 1."

    return True, "Matrix validation passed."


def compute_centralities(matrix: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Compute network centrality metrics from a connectivity matrix.

    Converts the connectivity matrix to a NetworkX graph and calculates
    degree, betweenness, and eigenvector centrality.

    Args:
        matrix: Symmetric connectivity matrix (n_nodes, n_nodes).

    Returns:
        Dict[str, np.ndarray]: Dictionary containing:
            - 'degree': Degree centrality for each node.
            - 'betweenness': Betweenness centrality for each node.
            - 'eigenvector': Eigenvector centrality for each node.
    """
    # Create graph from matrix
    G = nx.from_numpy_array(matrix)

    # Compute centralities
    degree_cent = nx.degree_centrality(G)
    betweenness_cent = nx.betweenness_centrality(G)
    try:
        eigenvector_cent = nx.eigenvector_centrality(G, max_iter=1000)
    except nx.PowerIterationFailedConvergence:
        logger.warning("Eigenvector centrality did not converge. Using zeros.")
        eigenvector_cent = {node: 0.0 for node in G.nodes()}

    # Convert to arrays
    n = len(G.nodes())
    degree_arr = np.array([degree_cent[i] for i in range(n)])
    betweenness_arr = np.array([betweenness_cent[i] for i in range(n)])
    eigenvector_arr = np.array([eigenvector_cent[i] for i in range(n)])

    return {
        'degree': degree_arr,
        'betweenness': betweenness_arr,
        'eigenvector': eigenvector_arr
    }


def compute_pli(
    epoch_data: np.ndarray,
    sfreq: float,
    band: Tuple[float, float] = (4.0, 8.0)
) -> np.ndarray:
    """
    Calculate Phase Lag Index (PLI) for pairs of EEG signals.

    PLI measures the asymmetry of the distribution of phase differences,
    indicating true functional connectivity while suppressing volume conduction.

    Args:
        epoch_data: 3D array (n_epochs, n_channels, n_times).
        sfreq: Sampling frequency in Hz.
        band: Frequency band (f_min, f_max) for PLI calculation.

    Returns:
        np.ndarray: Symmetric PLI matrix of shape (n_channels, n_channels).
    """
    n_epochs, n_channels, n_times = epoch_data.shape
    pli_matrix = np.zeros((n_channels, n_channels))

    # Filter parameters
    nyq = sfreq * 0.5
    if band[0] >= nyq or band[1] >= nyq:
        logger.error(f"Band {band} exceeds Nyquist frequency {nyq}.")
        return pli_matrix

    # Compute PLI for each pair
    for i in range(n_channels):
        for j in range(i, n_channels):
            if i == j:
                pli_matrix[i, j] = 1.0
                continue

            phase_diffs = []
            for ep in range(n_epochs):
                # Extract signals
                sig1 = epoch_data[ep, i, :]
                sig2 = epoch_data[ep, j, :]

                # Bandpass filter
                from scipy.signal import butter, filtfilt
                b, a = butter(4, [band[0] / nyq, band[1] / nyq], btype='band')
                sig1_f = filtfilt(b, a, sig1)
                sig2_f = filtfilt(b, a, sig2)

                # Compute instantaneous phase via Hilbert transform
                from scipy.signal import hilbert
                phase1 = np.angle(hilbert(sig1_f))
                phase2 = np.angle(hilbert(sig2_f))

                # Phase difference
                diff = phase1 - phase2
                phase_diffs.append(diff)

            # Stack and compute mean sign of phase difference
            phase_diffs = np.array(phase_diffs)
            # Average over epochs
            mean_sign = np.mean(np.sign(phase_diffs))
            pli_val = np.abs(mean_sign)

            pli_matrix[i, j] = pli_val
            pli_matrix[j, i] = pli_val

    return pli_matrix


def aggregate_pli_to_global(
    pli_matrices: List[np.ndarray],
    epochs_per_stage: Optional[Dict[str, int]] = None
) -> Dict[str, float]:
    """
    Aggregate PLI matrices into a mean global synchrony score per sleep stage.

    Args:
        pli_matrices: List of PLI matrices, one per epoch.
        epochs_per_stage: Optional dict mapping stage name to count (for weighting).

    Returns:
        Dict[str, float]: Mean global synchrony score (average of all off-diagonal PLI values).
    """
    if not pli_matrices:
        logger.warning("No PLI matrices provided for aggregation.")
        return {}

    # Average all PLI matrices
    avg_matrix = np.mean(pli_matrices, axis=0)

    # Compute mean of off-diagonal elements
    n = avg_matrix.shape[0]
    off_diag = avg_matrix[np.ones((n, n), dtype=bool) - np.eye(n, dtype=bool)]
    global_score = np.mean(off_diag)

    return {'global_synchrony': float(global_score)}


def calculate_vif(
    metrics_df: pd.DataFrame,
    features: Optional[List[str]] = None
) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for centrality metrics.

    VIF measures multicollinearity among predictor variables. A VIF > 5.0
    indicates high collinearity.

    Args:
        metrics_df: DataFrame containing metric columns.
        features: List of column names to calculate VIF for. Defaults to all numeric cols.

    Returns:
        Dict[str, float]: VIF values for each feature.
    """
    if features is None:
        features = metrics_df.select_dtypes(include=[np.number]).columns.tolist()
        # Exclude target variable if present (e.g., 'pli', 'synchrony')
        exclude = ['pli', 'synchrony', 'global_synchrony']
        features = [f for f in features if f not in exclude]

    if len(features) < 2:
        logger.warning("Need at least 2 features to calculate VIF.")
        return {}

    X = metrics_df[features].dropna()
    if X.empty:
        return {}

    # Add constant for intercept
    X_with_const = sm.add_constant(X)

    vif_results = {}
    for col in features:
        try:
            vif_val = variance_inflation_factor(X_with_const.values, X_with_const.columns.get_loc(col))
            vif_results[col] = float(vif_val)
        except Exception as e:
            logger.warning(f"VIF calculation failed for {col}: {e}")
            vif_results[col] = float('inf')

    return vif_results


def generate_subject_metrics_csv(
    subject_id: str,
    centralities: Dict[str, np.ndarray],
    synchrony_scores: Dict[str, float],
    vif_flags: Dict[str, float],
    night_ids: Tuple[str, str],
    output_path: str
) -> None:
    """
    Compile centrality, synchrony, and VIF metrics into a CSV file.

    Args:
        subject_id: Unique identifier for the subject.
        centralities: Dict of centrality metrics (degree, betweenness, eigenvector).
        synchrony_scores: Dict of synchrony scores per sleep stage.
        vif_flags: Dict of VIF values for each centrality metric.
        night_ids: Tuple (waking_night_id, sleep_night_id).
        output_path: Path to save the CSV file.
    """
    data = {
        'subject_id': [subject_id],
        'waking_night_id': [night_ids[0]],
        'sleep_night_id': [night_ids[1]]
    }

    # Flatten centralities
    for metric_name, values in centralities.items():
        data[f'{metric_name}_mean'] = [np.mean(values)]
        data[f'{metric_name}_std'] = [np.std(values)]

    # Flatten synchrony
    for stage, score in synchrony_scores.items():
        data[f'synchrony_{stage}'] = [score]

    # Add VIF flags
    for metric, vif_val in vif_flags.items():
        data[f'vif_{metric}'] = [vif_val]
        data[f'vif_flag_{metric}'] = ['High' if vif_val > 5.0 else 'Low']

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved subject metrics to {output_path}")


def main() -> None:
    """
    Main entry point for the metrics module.
    Currently serves as a placeholder for future CLI integration.
    """
    logger.info("Metrics module loaded. Use specific functions for calculations.")