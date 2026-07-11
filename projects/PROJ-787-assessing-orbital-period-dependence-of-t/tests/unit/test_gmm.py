"""
Unit test for GMM fitting on synthetic bimodal data.

This test generates a synthetic bimodal dataset with a known gap location
and verifies that the Gaussian Mixture Model (GMM) fitting logic correctly
identifies the valley between the peaks within a defined tolerance.

Dependencies:
    - numpy
    - scipy
    - sklearn.mixture
"""
import numpy as np
from scipy.stats import norm
from sklearn.mixture import GaussianMixture
from sklearn.metrics import bic


def generate_synthetic_bimodal_data(
    n_samples: int = 1000,
    mean1: float = 1.5,
    std1: float = 0.2,
    mean2: float = 2.5,
    std2: float = 0.2,
    fraction1: float = 0.5,
    seed: int = 42
) -> np.ndarray:
    """
    Generate a synthetic bimodal dataset representing planet radii.

    Args:
        n_samples: Total number of data points to generate.
        mean1: Mean of the first Gaussian component (super-Earths).
        std1: Standard deviation of the first component.
        mean2: Mean of the second Gaussian component (sub-Neptunes).
        std2: Standard deviation of the second component.
        fraction1: Fraction of samples belonging to the first component.
        seed: Random seed for reproducibility.

    Returns:
        A 1D numpy array of generated radii.
    """
    np.random.seed(seed)
    n1 = int(n_samples * fraction1)
    n2 = n_samples - n1

    data1 = np.random.normal(mean1, std1, n1)
    data2 = np.random.normal(mean2, std2, n2)

    data = np.concatenate([data1, data2])
    # Reshape for sklearn
    return data.reshape(-1, 1)


def fit_gmm_and_find_gap(
    data: np.ndarray,
    n_components: int = 2,
    random_state: int = 42
) -> float:
    """
    Fit a 2-component GMM to the data and calculate the gap location.

    The gap location is defined as the point between the two component means
    where the probability density is minimized (the valley). For two Gaussians
    with equal variance, this is simply the midpoint, but for unequal variance,
    it requires solving for the intersection or the minimum of the sum.
    Here, we approximate the gap as the weighted average of the means based
    on the mixture weights, or more simply, the midpoint between the sorted means
    for this specific test case where variances are similar.

    For the purpose of this unit test, we use the midpoint between the two
    fitted means as the proxy for the "gap location" since the true minimum
    of the sum of two Gaussians is analytically complex and the midpoint
    is sufficient to verify the model has separated the peaks correctly.

    Args:
        data: 2D array of shape (n_samples, 1).
        n_components: Number of Gaussian components.
        random_state: Random state for KMeans++ initialization.

    Returns:
        The estimated gap location (float).
    """
    gmm = GaussianMixture(
        n_components=n_components,
        covariance_type='full',
        init_params='k-means++',
        n_init=10,
        random_state=random_state
    )
    gmm.fit(data)

    means = gmm.means_.flatten()
    # Sort means to ensure consistent ordering (smaller mean first)
    sorted_means = np.sort(means)

    # The gap is located between the two means.
    # A robust estimate for the valley in a bimodal distribution is the midpoint
    # if variances are similar, or the point where PDFs cross.
    # We use the midpoint for this unit test as the ground truth comparison.
    gap_location = (sorted_means[0] + sorted_means[1]) / 2.0

    return gap_location


def test_gmm_fitting_synthetic_bimodal():
    """
    Test that GMM correctly identifies the gap location in synthetic bimodal data.

    Ground truth:
        Mean1 = 1.5, Mean2 = 2.5
        True Gap (midpoint) = 2.0
    """
    # Configuration
    true_mean1 = 1.5
    true_mean2 = 2.5
    true_gap = (true_mean1 + true_mean2) / 2.0
    tolerance = 0.15  # Allow for some statistical fluctuation

    # Generate data
    data = generate_synthetic_bimodal_data(
        n_samples=2000,
        mean1=true_mean1,
        mean2=true_mean2,
        std1=0.2,
        std2=0.2,
        fraction1=0.5,
        seed=42
    )

    # Fit GMM
    estimated_gap = fit_gmm_and_find_gap(data)

    # Assertions
    assert estimated_gap is not None, "GMM fitting failed to return a gap location"
    assert isinstance(estimated_gap, float), "Gap location must be a float"

    error = abs(estimated_gap - true_gap)
    assert error < tolerance, (
        f"Gap location {estimated_gap:.4f} deviates from true gap {true_gap:.4f} "
        f"by {error:.4f}, which exceeds tolerance {tolerance}."
    )

    # Additional check: Ensure the model found two distinct components
    # by verifying the means are not identical
    gmm = GaussianMixture(n_components=2, random_state=42)
    gmm.fit(data)
    means = np.sort(gmm.means_.flatten())
    assert means[1] - means[0] > 0.5, "GMM failed to separate the two modes sufficiently"

if __name__ == "__main__":
    test_gmm_fitting_synthetic_bimodal()
    print("Test passed: GMM correctly identified the gap location.")