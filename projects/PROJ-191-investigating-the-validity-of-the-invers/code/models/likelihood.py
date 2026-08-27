import numpy as np
from typing import Tuple, Optional
from pathlib import Path
import logging
from scipy.linalg import cholesky, cho_solve, LinAlgError
from models.physics import yukawa_force, newtonian_force

class NewtonianLikelihood:
    def __init__(self, covariance_matrix):
        self.covariance_matrix = covariance_matrix

    def log_likelihood(self, params, data):
        """
        Calculates the log-likelihood for a Newtonian force model given parameters and data.
        """
        force, separation, uncertainty = data[:, 0], data[:, 1], data[:, 2]
        predicted_force = newtonian_force(params[0], separation)  # params[0] is alpha
        diff = predicted_force - force
        try:
            precision_matrix = np.linalg.inv(self.covariance_matrix)
            log_likelihood = -0.5 * diff @ precision_matrix @ diff
        except LinAlgError as e:
            logging.error(f"Matrix inversion failed: {e}")
            return -np.inf  # Return negative infinity if matrix is singular

        return np.sum(log_likelihood)


class YukawaLikelihood:
    def __init__(self, covariance_matrix):
        self.covariance_matrix = covariance_matrix

    def log_likelihood(self, params, data):
        """
        Calculates the log-likelihood for a Yukawa force model given parameters and data.
        """
        force, separation, uncertainty = data[:, 0], data[:, 1], data[:, 2]
        predicted_force = yukawa_force(params[0], params[1], separation)  # params[0] is alpha, params[1] is lambda
        diff = predicted_force - force
        try:
            precision_matrix = np.linalg.inv(self.covariance_matrix)
            log_likelihood = -0.5 * diff @ precision_matrix @ diff
        except LinAlgError as e:
            logging.error(f"Matrix inversion failed: {e}")
            return -np.inf  # Return negative infinity if matrix is singular

        return np.sum(log_likelihood)


def load_covariance_matrix(file_path):
    """Loads the covariance matrix from a file."""
    try:
        return np.load(file_path)
    except FileNotFoundError:
        logging.error(f"Covariance matrix file not found at {file_path}")
        raise

def compute_cholesky_decomposition(covariance_matrix):
    """Computes the Cholesky decomposition of a covariance matrix."""
    try:
        return cholesky(covariance_matrix)
    except LinAlgError as e:
        logging.error(f"Cholesky decomposition failed: {e}")
        raise

def log_likelihood_newtonian(params, data, covariance_matrix):
  """Convenience wrapper for the Newtonian likelihood."""
  newtonian_likelihood = NewtonianLikelihood(covariance_matrix)
  return newtonian_likelihood.log_likelihood(params, data)

def log_likelihood_yukawa(params, data, covariance_matrix):
    """Convenience wrapper for the Yukawa likelihood."""
    yukawa_likelihood = YukawaLikelihood(covariance_matrix)
    return yukawa_likelihood.log_likelihood(params, data)

def main():
    # Example usage (can be removed/modified for actual pipeline integration)
    logging.basicConfig(level=logging.INFO)
    try:
        covariance_matrix = load_covariance_matrix("data/processed/covariance_matrix.npy")
        # Dummy data for demonstration
        dummy_data = np.array([[1.0, 2.0, 0.1], [2.5, 3.5, 0.2], [4.0, 5.0, 0.15]])

        # Example parameters (alpha) for Newtonian model
        newtonian_params = np.array([1.0])
        log_likelihood_n = log_likelihood_newtonian(newtonian_params, dummy_data, covariance_matrix)
        logging.info(f"Newtonian Log-Likelihood: {log_likelihood_n}")

        # Example parameters (alpha, lambda) for Yukawa model
        yukawa_params = np.array([1.0, 0.5])
        log_likelihood_y = log_likelihood_yukawa(yukawa_params, dummy_data, covariance_matrix)
        logging.info(f"Yukawa Log-Likelihood: {log_likelihood_y}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()