"""
Visualization module for eigenstate analysis and quantitative physical summaries.

Implements finite-size scaling visualization, decay length analysis, and
generation of quantitative physical summaries as requested by Feynman's review.
"""

import os
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from scipy import linalg
from scipy.sparse.linalg import eigsh
from scipy.optimize import curve_fit

from code.config import get_config
from code.generate_hamiltonian import generate_hamiltonian
from code.logger import get_logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def exponential_decay(x: np.ndarray, amplitude: float, decay_length: float, offset: float) -> np.ndarray:
    """Model for exponential decay of eigenstate probability density."""
    return amplitude * np.exp(-np.abs(x) / decay_length) + offset

def compute_decay_length(psi_squared: np.ndarray, site_center: int) -> Tuple[float, float, Dict[str, Any]]:
    """
    Compute decay length from probability density using log-linear fit.
    
    Args:
        psi_squared: Probability density array |ψ_i|^2
        site_center: Center site index for fitting
        
    Returns:
        Tuple of (decay_length, r_squared, fit_params)
    """
    # Select sites around the center for fitting
    half_window = min(site_center, len(psi_squared) - site_center - 1)
    window_size = max(10, half_window)  # At least 10 points for fitting
    
    sites = np.arange(site_center - window_size, site_center + window_size + 1)
    probs = psi_squared[sites]
    
    # Filter out very small values to avoid log(0)
    valid_mask = probs > 1e-15
    if np.sum(valid_mask) < 5:
        logger.warning("Not enough valid points for decay fit")
        return np.nan, 0.0, {}
    
    x_fit = np.abs(sites[valid_mask] - site_center)
    y_fit = np.log(probs[valid_mask])
    
    # Linear fit to log(probability)
    try:
        coeffs = np.polyfit(x_fit, y_fit, 1)
        decay_length = -1.0 / coeffs[0] if coeffs[0] != 0 else np.nan
        
        # Calculate R-squared
        y_pred = np.polyval(coeffs, x_fit)
        ss_res = np.sum((y_fit - y_pred) ** 2)
        ss_tot = np.sum((y_fit - np.mean(y_fit)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        fit_params = {
            'slope': float(coeffs[0]),
            'intercept': float(coeffs[1]),
            'decay_length': float(decay_length),
            'r_squared': float(r_squared)
        }
        
        return float(decay_length), float(r_squared), fit_params
    except Exception as e:
        logger.warning(f"Fit failed: {e}")
        return np.nan, 0.0, {}

def find_half_amplitude_site(psi_squared: np.ndarray, site_center: int) -> Optional[int]:
    """
    Find the site index where amplitude drops to half of the peak.
    
    Args:
        psi_squared: Probability density array
        site_center: Center site index
        
    Returns:
        Site index where amplitude drops to half, or None if not found
    """
    peak_value = psi_squared[site_center]
    half_value = peak_value / 2.0
    
    # Search outward from center
    for offset in range(1, min(site_center, len(psi_squared) - site_center)):
        left_site = site_center - offset
        right_site = site_center + offset
        
        if psi_squared[left_site] <= half_value:
            return int(left_site)
        if psi_squared[right_site] <= half_value:
            return int(right_site)
    
    return None

def generate_worked_example(W: float, L: int, realization_index: int, seed: int) -> Dict[str, Any]:
    """
    Generate a quantitative physical summary for a specific disorder realization.
    
    This implements the "worked example" requested by Feynman's review,
    identifying specific sites and decay lengths without qualitative analogies.
    
    Args:
        W: Disorder strength
        L: System size
        realization_index: Index of the realization
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing quantitative metrics
    """
    config = get_config()
    
    # Generate Hamiltonian with real random numbers
    np.random.seed(seed)
    H = generate_hamiltonian(L, W, seed=seed)
    
    # Diagonalize
    try:
        # Use dense solver for moderate L
        if L <= 2000:
            eigenvalues, eigenvectors = linalg.eigh(H.toarray() if hasattr(H, 'toarray') else H)
        else:
            # Sparse solver for larger systems
            eigenvalues, eigenvectors = eigsh(H, k=min(100, L-1), which='LM')
            # Sort by eigenvalue
            idx = np.argsort(np.abs(eigenvalues))
            eigenvalues = eigenvalues[idx]
            eigenvectors = eigenvectors[:, idx]
    except Exception as e:
        logger.error(f"Diagonalization failed: {e}")
        return {}
    
    # Find eigenstate near E=0
    zero_idx = np.argmin(np.abs(eigenvalues))
    psi = eigenvectors[:, zero_idx]
    psi_squared = np.abs(psi) ** 2
    
    # Find center site (peak probability)
    site_center = int(np.argmax(psi_squared))
    
    # Compute decay length
    decay_length, r_squared, fit_params = compute_decay_length(psi_squared, site_center)
    
    # Find half-amplitude site
    half_site = find_half_amplitude_site(psi_squared, site_center)
    half_value = psi_squared[half_site] if half_site is not None else None
    
    # Compile quantitative summary
    summary = {
        'W': float(W),
        'L': int(L),
        'realization_index': int(realization_index),
        'seed': int(seed),
        'eigenvalue': float(eigenvalues[zero_idx]),
        'site_center': int(site_center),
        'peak_amplitude': float(psi_squared[site_center]),
        'decay_length': float(decay_length) if not np.isnan(decay_length) else None,
        'r_squared': float(r_squared),
        'half_amplitude_site': int(half_site) if half_site is not None else None,
        'half_amplitude_value': float(half_value) if half_value is not None else None,
        'fit_params': fit_params
    }
    
    return summary

def write_physical_summary(summary: Dict[str, Any], output_path: str) -> None:
    """
    Write quantitative physical summary to markdown file.
    
    Args:
        summary: Dictionary of quantitative metrics
        output_path: Path to output markdown file
    """
    docs_dir = Path(output_path).parent
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("# Physical Interpretation of Localized Eigenstates\n\n")
        f.write("## Worked Example: W=2.0\n\n")
        f.write("Quantitative metrics derived from eigenstate probability density analysis.\n\n")
        
        # Check if fit quality is sufficient
        if summary.get('r_squared', 0) < 0.95:
            f.write("**Note**: Fit quality R² = {:.4f} < 0.95. Results may be unreliable.\n\n".format(summary['r_squared']))
        
        f.write("### System Parameters\n")
        f.write(f"- Disorder strength: W = {summary['W']:.2f}\n")
        f.write(f"- System size: L = {summary['L']}\n")
        f.write(f"- Realization index: {summary['realization_index']}\n")
        f.write(f"- Seed: {summary['seed']}\n")
        f.write(f"- Eigenvalue: E = {summary['eigenvalue']:.6f}\n\n")
        
        f.write("### Localization Metrics\n")
        f.write(f"- Center site: {summary['site_center']}\n")
        f.write(f"- Peak probability: |ψ|² = {summary['peak_amplitude']:.6f}\n")
        
        if summary['decay_length'] is not None:
            f.write(f"- Decay length: ξ = {summary['decay_length']:.2f} sites\n")
        else:
            f.write("- Decay length: Unable to compute (fit failed)\n")
        
        f.write(f"- Fit quality: R² = {summary['r_squared']:.4f}\n\n")
        
        if summary['half_amplitude_site'] is not None:
            f.write("### Half-Amplitude Point\n")
            f.write(f"At site {summary['half_amplitude_site']}, probability drops to {summary['half_amplitude_value']:.6f} (50% of peak)\n")
            f.write(f"Distance from center: {abs(summary['half_amplitude_site'] - summary['site_center'])} sites\n")
        else:
            f.write("### Half-Amplitude Point\n")
            f.write("Half-amplitude point not found within system bounds.\n")
        
        if summary.get('fit_params'):
            f.write("\n### Fit Parameters\n")
            for key, value in summary['fit_params'].items():
                if isinstance(value, float):
                    f.write(f"- {key}: {value:.6f}\n")
                else:
                    f.write(f"- {key}: {value}\n")

def plot_eigenstate_decay(psi_squared: np.ndarray, site_center: int, decay_length: float, 
                          output_path: str, title: str = "Eigenstate Probability Density") -> None:
    """
    Plot eigenstate probability density with exponential fit overlay.
    
    Args:
        psi_squared: Probability density array
        site_center: Center site index
        decay_length: Computed decay length
        output_path: Path to save the plot
        title: Plot title
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sites = np.arange(len(psi_squared))
    ax.plot(sites, psi_squared, 'b.', label='|ψ|²', markersize=4)
    
    # Overlay exponential fit
    x_fit = np.abs(sites - site_center)
    y_fit = psi_squared[site_center] * np.exp(-x_fit / decay_length) if decay_length > 0 else psi_squared[site_center]
    ax.plot(sites, y_fit, 'r-', label=f'Exp. fit (ξ={decay_length:.2f})', linewidth=2)
    
    ax.set_xlabel('Site Index')
    ax.set_ylabel('Probability Density |ψ|²')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Plot saved to {output_path}")

def main():
    """Main entry point for visualization and summary generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate eigenstate visualizations and physical summaries')
    parser.add_argument('--L', type=int, default=200, help='System size')
    parser.add_argument('--W', type=float, default=2.0, help='Disorder strength')
    parser.add_argument('--realization', type=int, default=5, help='Realization index')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output-plot', type=str, default='data/processed/visualizations/eigenstate_decay.png',
                      help='Output path for plot')
    parser.add_argument('--output-summary', type=str, default='docs/physical_interpretation.md',
                      help='Output path for physical summary')
    
    args = parser.parse_args()
    
    # Generate worked example
    summary = generate_worked_example(
        W=args.W,
        L=args.L,
        realization_index=args.realization,
        seed=args.seed
    )
    
    if not summary:
        logger.error("Failed to generate worked example")
        return 1
    
    # Write physical summary
    write_physical_summary(summary, args.output_summary)
    logger.info(f"Physical summary written to {args.output_summary}")
    
    # Generate plot
    psi_squared = np.zeros(args.L)
    # Re-compute for plotting (could be optimized to reuse from summary)
    np.random.seed(args.seed)
    H = generate_hamiltonian(args.L, args.W, seed=args.seed)
    try:
        if args.L <= 2000:
            eigenvalues, eigenvectors = linalg.eigh(H.toarray() if hasattr(H, 'toarray') else H)
        else:
            eigenvalues, eigenvectors = eigsh(H, k=min(100, args.L-1), which='LM')
            idx = np.argsort(np.abs(eigenvalues))
            eigenvalues = eigenvalues[idx]
            eigenvectors = eigenvectors[:, idx]
        
        zero_idx = np.argmin(np.abs(eigenvalues))
        psi = eigenvectors[:, zero_idx]
        psi_squared = np.abs(psi) ** 2
        site_center = int(np.argmax(psi_squared))
        decay_length = summary.get('decay_length', 1.0) or 1.0
        
        plot_eigenstate_decay(
            psi_squared,
            site_center,
            decay_length,
            args.output_plot,
            title=f"Eigenstate Decay (W={args.W}, L={args.L})"
        )
    except Exception as e:
        logger.error(f"Plot generation failed: {e}")
    
    return 0

if __name__ == '__main__':
    exit(main())