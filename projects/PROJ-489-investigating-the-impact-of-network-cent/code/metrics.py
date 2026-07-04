"""
Metrics computation module for network centrality and neural synchrony analysis.

This module provides functions to compute functional connectivity matrices,
network centrality metrics, Phase Lag Index (PLI), and Variance Inflation
Factors (VIF) for sleep study data.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import pandas as pd
import mne
from scipy.signal import welch, coherency
import networkx as nx
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Configure logger
logger = logging.getLogger(__name__)


def compute_waking_connectivity(
    raw: mne.io.BaseRaw,
    freq_bands: Optional[Dict[str, Tuple[float, float]]] = None
) -> np.ndarray:
    """
    Compute functional connectivity matrices from waking EEG data using coherence.

    Constructs connectivity matrices based on theta (4-8 Hz) and alpha (8-13 Hz)
    coherence between electrode pairs.

    Args:
        raw: MNE Raw object containing waking EEG data.
        freq_bands: Dictionary mapping band names to (low, high) frequency tuples.
                    Defaults to {'theta': (4, 8), 'alpha': (8, 13)}.

    Returns:
        np.ndarray: Symmetric connectivity matrix of shape (n_channels, n_channels).
                    Values represent mean coherence across specified bands.

    Raises:
        ValueError: If raw data is empty or has insufficient channels.
    """
    if freq_bands is None:
        freq_bands = {'theta': (4, 8), 'alpha': (8, 13)}

    if raw.n_channels < 2:
        raise ValueError("Insufficient channels for connectivity computation.")

    data = raw.get_data()
    sfreq = raw.info['sfreq']
    n_channels = data.shape[0]

    # Initialize connectivity matrix
    connectivity = np.zeros((n_channels, n_channels))

    for band_name, (fmin, fmax) in freq_bands.items():
        logger.info(f"Computing coherence for band: {band_name} ({fmin}-{fmax} Hz)")
        # Compute coherence for all channel pairs
        # Using MNE's cross-spectral density approach via coherency
        # Note: coherency returns (n_channels, n_channels, n_freqs)
        try:
            # Simplified approach: compute pairwise coherence
            for i in range(n_channels):
                for j in range(i + 1, n_channels):
                    f, Cxy = coherency(
                        data[i], data[j],
                        fs=sfreq,
                        nperseg=min(256, len(data[i]) // 4)
                    )
                    # Mask frequencies within band
                    mask = (f >= fmin) & (f <= fmax)
                    if np.any(mask):
                        coherence_val = np.mean(np.abs(Cxy[mask]))
                        connectivity[i, j] += coherence_val
                        connectivity[j, i] += coherence_val
        except Exception as e:
            logger.warning(f"Error computing coherence for pair ({i}, {j}): {e}")

    # Average across bands
    n_bands = len(freq_bands)
    connectivity /= n_bands

    # Set diagonal to 0 (no self-connection)
    np.fill_diagonal(connectivity, 0.0)

    return connectivity


def validate_connectivity_matrix(matrix: np.ndarray) -> Tuple[bool, List[str]]:
    """
    Validate that a connectivity matrix is symmetric and values are in [0, 1].

    Args:
        matrix: Numpy array representing a connectivity matrix.

    Returns:
        Tuple containing:
            - bool: True if validation passes, False otherwise.
            - List[str]: List of validation error messages.
    """
    errors = []

    if not isinstance(matrix, np.ndarray):
        errors.append("Input is not a numpy array.")
        return False, errors

    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        errors.append(f"Matrix must be square. Got shape {matrix.shape}.")
        return False, errors

    # Check symmetry
    if not np.allclose(matrix, matrix.T):
        max_diff = np.max(np.abs(matrix - matrix.T))
        errors.append(f"Matrix is not symmetric. Max difference: {max_diff:.6f}.")

    # Check value range
    min_val = np.min(matrix)
    max_val = np.max(matrix)

    if min_val < 0:
        errors.append(f"Matrix contains negative values. Min: {min_val:.6f}.")

    if max_val > 1:
        errors.append(f"Matrix contains values > 1. Max: {max_val:.6f}.")

    # Check for NaN/Inf
    if np.any(np.isnan(matrix)):
        errors.append("Matrix contains NaN values.")

    if np.any(np.isinf(matrix)):
        errors.append("Matrix contains Inf values.")

    is_valid = len(errors) == 0
    if is_valid:
        logger.info("Connectivity matrix validation passed.")
    else:
        logger.warning(f"Connectivity matrix validation failed: {errors}")

    return is_valid, errors


def compute_centralities(
    connectivity_matrix: np.ndarray,
    channel_names: Optional[List[str]] = None
) -> Dict[str, Union[np.ndarray, List[str]]]:
    """
    Compute network centrality metrics from a connectivity matrix.

    Calculates degree, betweenness, and eigenvector centrality using NetworkX.

    Args:
        connectivity_matrix: Symmetric connectivity matrix (n_channels, n_channels).
        channel_names: Optional list of channel names. If None, uses indices as names.

    Returns:
        Dictionary containing:
            - 'degree': np.ndarray of degree centrality values.
            - 'betweenness': np.ndarray of betweenness centrality values.
            - 'eigenvector': np.ndarray of eigenvector centrality values.
            - 'channel_names': List of channel names corresponding to indices.
    """
    n_channels = connectivity_matrix.shape[0]
    if channel_names is None:
        channel_names = [f"ch_{i}" for i in range(n_channels)]

    # Create weighted graph
    G = nx.Graph()
    for i in range(n_channels):
        G.add_node(i, name=channel_names[i])

    for i in range(n_channels):
        for j in range(i + 1, n_channels):
            weight = connectivity_matrix[i, j]
            if weight > 0:
                G.add_edge(i, j, weight=weight)

    # Compute centralities
    degree_cent = nx.degree_centrality(G)
    betweenness_cent = nx.betweenness_centrality(G, weight='weight')
    
    # Eigenvector centrality may fail for disconnected graphs; handle gracefully
    try:
        eigenvector_cent = nx.eigenvector_centrality(G, max_iter=1000)
    except nx.PowerIterationFailedConvergence:
        logger.warning("Eigenvector centrality did not converge. Using zeros.")
        eigenvector_cent = {node: 0.0 for node in G.nodes()}

    # Convert to arrays
    degree_array = np.array([degree_cent[i] for i in range(n_channels)])
    betweenness_array = np.array([betweenness_cent[i] for i in range(n_channels)])
    eigenvector_array = np.array([eigenvector_cent[i] for i in range(n_channels)])

    return {
        'degree': degree_array,
        'betweenness': betweenness_array,
        'eigenvector': eigenvector_array,
        'channel_names': channel_names
    }


def compute_pli(
    epochs: mne.Epochs,
    freq_band: Tuple[float, float] = (4, 8)
) -> np.ndarray:
    """
    Compute Phase Lag Index (PLI) across electrode pairs for each epoch.

    Args:
        epochs: MNE Epochs object containing epoched EEG data.
        freq_band: Tuple (fmin, fmax) defining the frequency band for PLI computation.
                   Default is theta band (4, 8) Hz.

    Returns:
        np.ndarray: Array of shape (n_epochs, n_channels, n_channels) containing PLI values.
                    Diagonal elements are zero.
    """
    fmin, fmax = freq_band
    n_epochs = len(epochs)
    data = epochs.get_data()  # Shape: (n_epochs, n_channels, n_times)
    sfreq = epochs.info['sfreq']
    n_channels = data.shape[1]
    n_times = data.shape[2]

    pli_matrix = np.zeros((n_epochs, n_channels, n_channels))

    for ep_idx in range(n_epochs):
        logger.debug(f"Computing PLI for epoch {ep_idx + 1}/{n_epochs}")
        ep_data = data[ep_idx]

        for i in range(n_channels):
            for j in range(i + 1, n_channels):
                # Compute phase difference
                # Using Hilbert transform to extract instantaneous phase
                try:
                    # Bandpass filter the epoch data for this pair
                    from scipy.signal import butter, filtfilt
                    b, a = butter(4, [fmin / (sfreq / 2), fmax / (sfreq / 2)], btype='band')
                    sig_i = filtfilt(b, a, ep_data[i])
                    sig_j = filtfilt(b, a, ep_data[j])

                    # Hilbert transform
                    from scipy.signal import hilbert
                    analytic_i = hilbert(sig_i)
                    analytic_j = hilbert(sig_j)

                    phase_i = np.angle(analytic_i)
                    phase_j = np.angle(analytic_j)

                    phase_diff = phase_i - phase_j

                    # PLI is the mean of the sign of the phase difference
                    pli_val = np.mean(np.sign(phase_diff))
                    pli_matrix[ep_idx, i, j] = pli_val
                    pli_matrix[ep_idx, j, i] = pli_val
                except Exception as e:
                    logger.warning(f"Error computing PLI for epoch {ep_idx}, pair ({i}, {j}): {e}")
                    continue

    return pli_matrix


def aggregate_pli_to_global(
    pli_matrix: np.ndarray,
    sleep_stages: List[str]
) -> Dict[str, float]:
    """
    Aggregate PLI values to mean global synchrony score per sleep stage.

    Args:
        pli_matrix: Array of shape (n_epochs, n_channels, n_channels) from compute_pli.
        sleep_stages: List of sleep stage labels corresponding to each epoch in pli_matrix.
                      Length must match pli_matrix.shape[0].

    Returns:
        Dictionary mapping sleep stage names to mean global PLI (synchrony) score.
    """
    if len(sleep_stages) != pli_matrix.shape[0]:
        raise ValueError(
            f"Length of sleep_stages ({len(sleep_stages)}) must match "
            f"number of epochs ({pli_matrix.shape[0]})."
        )

    unique_stages = list(set(sleep_stages))
    global_synchrony = {}

    for stage in unique_stages:
        # Identify epochs for this stage
        stage_indices = [i for i, s in enumerate(sleep_stages) if s == stage]
        
        if not stage_indices:
            continue

        # Aggregate PLI for these epochs
        stage_pli = pli_matrix[stage_indices]
        
        # Compute mean absolute PLI (ignoring sign, focusing on magnitude of lag)
        # Or use mean of absolute values to capture synchrony strength
        mean_pli = np.mean(np.abs(stage_pli))
        
        # Exclude diagonal (self-connections)
        n_channels = stage_pli.shape[1]
        n_pairs = n_channels * (n_channels - 1) / 2
        
        # Average across all electrode pairs and epochs
        global_synchrony[stage] = float(mean_pli)
        logger.info(f"Global synchrony for {stage}: {global_synchrony[stage]:.4f}")

    return global_synchrony


def calculate_vif(
    metrics_df: pd.DataFrame,
    feature_columns: Optional[List[str]] = None
) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for centrality metrics.

    Args:
        metrics_df: DataFrame containing centrality metrics as columns.
        feature_columns: List of column names to compute VIF for. If None, uses all numeric columns.

    Returns:
        Dictionary mapping feature names to their VIF values.
    """
    if feature_columns is None:
        feature_columns = metrics_df.select_dtypes(include=[np.number]).columns.tolist()

    if len(feature_columns) < 2:
        logger.warning("Insufficient features for VIF calculation. Returning empty dict.")
        return {}

    # Prepare feature matrix
    X = metrics_df[feature_columns].values

    # Add intercept column for VIF calculation (optional, but common practice)
    # However, statsmodels VIF usually expects centered data without intercept
    # We'll compute VIF for each feature regressed on others
    vif_results = {}

    for i, col in enumerate(feature_columns):
        # Design matrix for this feature: all other features
        other_features = [j for j in range(X.shape[1]) if j != i]
        X_other = X[:, other_features]
        y = X[:, i]

        # Add constant for intercept
        from statsmodels.regression.linear_model import OLS
        from statsmodels.tools import add_constant

        try:
            X_with_const = add_constant(X_other)
            model = OLS(y, X_with_const).fit()
            # VIF = 1 / (1 - R^2)
            r_squared = model.rsquared
            if r_squared >= 1.0:
                vif = np.inf
            else:
                vif = 1.0 / (1.0 - r_squared)
            vif_results[col] = float(vif)
        except Exception as e:
            logger.warning(f"Error computing VIF for {col}: {e}")
            vif_results[col] = float('nan')

    return vif_results


def generate_subject_metrics_csv(
    subject_id: str,
    centralities: Dict[str, np.ndarray],
    synchrony_scores: Dict[str, float],
    vif_flags: Dict[str, float],
    output_path: str
) -> None:
    """
    Generate a CSV file containing subject metrics.

    Args:
        subject_id: Unique identifier for the subject.
        centralities: Dictionary from compute_centralities containing 'degree', 'betweenness', 'eigenvector'.
        synchrony_scores: Dictionary from aggregate_pli_to_global mapping sleep stages to scores.
        vif_flags: Dictionary from calculate_vif mapping feature names to VIF values.
        output_path: Path to the output CSV file.
    """
    rows = []

    # Flatten centralities: one row per channel
    channels = centralities.get('channel_names', [f"ch_{i}" for i in range(len(centralities['degree']))])
    for idx, ch_name in enumerate(channels):
        row = {
            'subject_id': subject_id,
            'channel': ch_name,
            'degree_centrality': centralities['degree'][idx],
            'betweenness_centrality': centralities['betweenness'][idx],
            'eigenvector_centrality': centralities['eigenvector'][idx]
        }
        rows.append(row)

    # Create DataFrame
    df = pd.DataFrame(rows)

    # Add synchrony scores as columns (broadcasted)
    for stage, score in synchrony_scores.items():
        col_name = f"synchrony_{stage}"
        df[col_name] = score

    # Add VIF flags (broadcasted)
    for feat, vif_val in vif_flags.items():
        col_name = f"vif_{feat}"
        df[col_name] = vif_val

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved subject metrics to {output_path}")


def main() -> None:
    """
    Main entry point for metrics module.

    This function demonstrates the usage of metrics computation functions
    with sample data. In a real pipeline, it would load data from files
    and orchestrate the full metrics computation workflow.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Metrics module initialized.")
    
    # Placeholder for actual pipeline integration
    # In production, this would be called from a pipeline orchestrator
    logger.info("To use this module, import functions and pass MNE objects or DataFrames.")


if __name__ == "__main__":
    main()