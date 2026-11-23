"""
Laplacian Eigenvalue Validation for Ring Graphs.

This module validates the Laplacian eigenvalues of a ring graph against
the analytical solution. The analytical eigenvalues for a ring graph with N nodes
are given by: λ_k = 2 - 2 * cos(2 * π * k / N) for k = 0, ..., N-1.

This task (T025) ensures that the numerical computation of the Laplacian matrix
and its eigenvalues matches the theoretical expectation within a tight tolerance.
"""
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import logging
import os
import sys

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.utils.diagnostics import generate_ring_analytical_eigenvalues

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_ring_graph(N: int) -> nx.Graph:
    """
    Generate a ring graph with N nodes.

    Args:
        N (int): Number of nodes in the ring.

    Returns:
        nx.Graph: A ring graph.
    """
    G = nx.cycle_graph(N)
    return G


def compute_numerical_eigenvalues(G: nx.Graph) -> np.ndarray:
    """
    Compute the eigenvalues of the Laplacian matrix of a graph.

    Args:
        G (nx.Graph): The input graph.

    Returns:
        np.ndarray: Sorted eigenvalues of the Laplacian matrix.
    """
    L = nx.laplacian_matrix(G).toarray()
    eigenvalues = np.linalg.eigvalsh(L)
    return np.sort(eigenvalues)


def validate_eigenvalues(N: int, tolerance: float = 1e-6) -> dict:
    """
    Validate the eigenvalues of a ring graph against the analytical solution.

    Args:
        N (int): Number of nodes in the ring.
        tolerance (float): Tolerance for comparison.

    Returns:
        dict: Validation results including numerical eigenvalues, analytical eigenvalues,
              max error, and pass/fail status.
    """
    logger.info(f"Generating ring graph with N={N} nodes...")
    G = generate_ring_graph(N)

    logger.info("Computing numerical Laplacian eigenvalues...")
    numerical_eigs = compute_numerical_eigenvalues(G)

    logger.info("Computing analytical Laplacian eigenvalues...")
    analytical_eigs = generate_ring_analytical_eigenvalues(N)

    # Ensure both arrays are sorted for comparison
    numerical_eigs = np.sort(numerical_eigs)
    analytical_eigs = np.sort(analytical_eigs)

    logger.debug(f"Numerical eigenvalues: {numerical_eigs}")
    logger.debug(f"Analytical eigenvalues: {analytical_eigs}")

    # Calculate error
    error = np.abs(numerical_eigs - analytical_eigs)
    max_error = np.max(error)
    mean_error = np.mean(error)

    passed = max_error < tolerance

    result = {
        "N": N,
        "numerical_eigenvalues": numerical_eigs.tolist(),
        "analytical_eigenvalues": analytical_eigs.tolist(),
        "max_error": float(max_error),
        "mean_error": float(mean_error),
        "tolerance": tolerance,
        "passed": passed
    }

    return result


def plot_eigenvalue_comparison(result: dict, output_path: str) -> None:
    """
    Plot the comparison between numerical and analytical eigenvalues.

    Args:
        result (dict): Validation results from validate_eigenvalues.
        output_path (str): Path to save the plot.
    """
    N = result["N"]
    numerical = np.array(result["numerical_eigenvalues"])
    analytical = np.array(result["analytical_eigenvalues"])
    k = np.arange(N)

    plt.figure(figsize=(10, 6))
    plt.plot(k, numerical, 'o-', label='Numerical (Computed)', markersize=4)
    plt.plot(k, analytical, 's--', label='Analytical (Theoretical)', markersize=4)
    
    plt.xlabel('Mode Index k')
    plt.ylabel('Eigenvalue λ')
    plt.title(f'Laplacian Eigenvalues for Ring Graph (N={N})')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Add annotation for max error
    max_err = result["max_error"]
    plt.annotate(f'Max Error: {max_err:.2e}', 
                xy=(0.05, 0.95), xycoords='axes fraction',
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Eigenvalue comparison plot saved to {output_path}")


def main():
    """
    Main function to run the Laplacian eigenvalue validation.
    """
    logger.info("Starting Laplacian Eigenvalue Validation (Task T025)...")
    
    # Use a standard size for validation, e.g., N=100
    N = 100
    tolerance = 1e-6
    
    # Ensure output directory exists
    output_dir = "data/analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    result = validate_eigenvalues(N, tolerance)
    
    # Save results to JSON
    import json
    output_json_path = os.path.join(output_dir, "ring_eigenvalue_validation.json")
    with open(output_json_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Validation results saved to {output_json_path}")
    
    # Generate plot
    output_plot_path = os.path.join(output_dir, "ring_eigenvalue_validation.png")
    plot_eigenvalue_comparison(result, output_plot_path)
    
    if result["passed"]:
        logger.info(f"Validation PASSED: Max error {result['max_error']:.2e} < tolerance {tolerance}")
    else:
        logger.error(f"Validation FAILED: Max error {result['max_error']:.2e} >= tolerance {tolerance}")
        sys.exit(1)

    # Generate checksum for the output file
    from code.utils.checksums import generate_checksum
    generate_checksum(output_json_path)
    logger.info(f"Checksum generated for {output_json_path}")

    logger.info("Task T025 completed successfully.")


if __name__ == "__main__":
    main()