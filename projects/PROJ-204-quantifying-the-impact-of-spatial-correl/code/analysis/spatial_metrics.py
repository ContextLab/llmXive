import numpy as np
from scipy import ndimage
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import logging
from typing import Tuple, Dict, Any, Optional, Union, List

__all__ = [
    "gaussian_decay",
    "exponential_decay",
    "power_law_decay",
    "compute_autocorrelation",
    "compute_radial_distances",
    "extract_radial_profile",
    "fit_decay_model",
    "compute_spatial_metrics_for_sample",
    "process_dataset_and_write_metrics",
]

def gaussian_decay(r: np.ndarray, a: float, sigma: float, c: float) -> np.ndarray:
    """
    Gaussian decay model: ``a * exp(-(r**2)/(2*sigma**2)) + c``.

    Parameters
    ----------
    r: np.ndarray
        Radial distances.
    a, sigma, c: float
        Model parameters.

    Returns
    -------
    np.ndarray
        Model values.
    """
    return a * np.exp(-(r ** 2) / (2 * sigma ** 2)) + c

def exponential_decay(r: np.ndarray, a: float, tau: float, c: float) -> np.ndarray:
    """
    Exponential decay model: ``a * exp(-r / tau) + c``.

    Parameters
    ----------
    r: np.ndarray
        Radial distances.
    a, tau, c: float
        Model parameters.

    Returns
    -------
    np.ndarray
        Model values.
    """
    return a * np.exp(-r / tau) + c

def power_law_decay(r: np.ndarray, a: float, beta: float, c: float) -> np.ndarray:
    """
    Power‑law decay model: ``a * r**(-beta) + c``.

    Parameters
    ----------
    r: np.ndarray
        Radial distances.
    a, beta, c: float
        Model parameters.

    Returns
    -------
    np.ndarray
        Model values.
    """
    # avoid division by zero
    r = np.where(r == 0, 1e-12, r)
    return a * r ** (-beta) + c

def compute_autocorrelation(image: np.ndarray) -> np.ndarray:
    """
    Compute the 2‑D autocorrelation of an image using FFT.

    Parameters
    ----------
    image: np.ndarray
        Input image.

    Returns
    -------
    np.ndarray
        Autocorrelation image (real, normalized).
    """
    f = np.fft.fft2(image)
    ac = np.fft.ifft2(f * np.conj(f)).real
    ac /= ac.max()
    return ac

def compute_radial_distances(shape: Tuple[int, int]) -> np.ndarray:
    """
    Generate an array of radial distances from the centre of an image.

    Parameters
    ----------
    shape: Tuple[int, int]
        (height, width) of the image.

    Returns
    -------
    np.ndarray
        2‑D array where each element holds its radial distance.
    """
    y, x = np.indices(shape)
    centre = np.array([(shape[0] - 1) / 2.0, (shape[1] - 1) / 2.0])
    r = np.sqrt((x - centre[1]) ** 2 + (y - centre[0]) ** 2)
    return r

def extract_radial_profile(
    autocorr: np.ndarray, radial_dist: np.ndarray, nbins: int = 100
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert a 2‑D autocorrelation image into a 1‑D radial profile.

    Parameters
    ----------
    autocorr: np.ndarray
        Autocorrelation image.
    radial_dist: np.ndarray
        Radial distance map (same shape as ``autocorr``).
    nbins: int, optional
        Number of radial bins (default 100).

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        (bin_centers, mean_autocorr_per_bin)
    """
    max_r = radial_dist.max()
    bins = np.linspace(0, max_r, nbins + 1)
    digitized = np.digitize(radial_dist.ravel(), bins)
    bin_means = [
        autocorr.ravel()[digitized == i].mean() if np.any(digitized == i) else np.nan
        for i in range(1, nbins + 1)
    ]
    bin_centers = (bins[:-1] + bins[1:]) / 2
    return bin_centers, np.array(bin_means)

def fit_decay_model(
    r: np.ndarray, profile: np.ndarray
) -> Tuple[str, Dict[str, float], float]:
    """
    Fit exponential, Gaussian and power‑law decay models and select the best
    one based on Akaike Information Criterion (AIC).

    Parameters
    ----------
    r: np.ndarray
        Radial distances (bin centres).
    profile: np.ndarray
        Autocorrelation values at those distances.

    Returns
    -------
    Tuple[str, Dict[str, float], float]
        (best_model_name, best_parameters, best_aic)
    """
    models = {
        "exponential": (exponential_decay, 3),
        "gaussian": (gaussian_decay, 3),
        "power_law": (power_law_decay, 3),
    }
    best_aic = np.inf
    best_name = None
    best_params = {}
    for name, (func, k) in models.items():
        try:
            popt, _ = curve_fit(func, r, profile, maxfev=10000)
            residuals = profile - func(r, *popt)
            ss_res = np.sum(residuals ** 2)
            n = len(r)
            aic = n * np.log(ss_res / n) + 2 * k
            if aic < best_aic:
                best_aic = aic
                best_name = name
                best_params = dict(zip(func.__code__.co_varnames[1:], popt))
        except Exception as e:
            logging.debug("Fit failed for %s: %s", name, e)
    return best_name, best_params, best_aic

def compute_spatial_metrics_for_sample(
    sample_id: str, element_map: np.ndarray
) -> List[Dict[str, Any]]:
    """
    Compute spatial metrics for a single elemental map.

    The function returns a list of dictionaries, each containing the
    ``sample_id``, ``element`` name, computed ``correlation_length``,
    selected ``model_type`` and the associated ``AIC`` value.

    Parameters
    ----------
    sample_id: str
        Identifier of the sample.
    element_map: np.ndarray
        2‑D array of the elemental intensity.

    Returns
    -------
    List[Dict[str, Any]]
        List with a single dictionary of results.
    """
    ac = compute_autocorrelation(element_map)
    rad = compute_radial_distances(ac.shape)
    r_bins, profile = extract_radial_profile(ac, rad)
    # remove NaNs for fitting
    mask = ~np.isnan(profile)
    if np.sum(mask) < 5:
        logging.warning("Insufficient data to fit decay model for %s", sample_id)
        return []
    best_name, best_params, best_aic = fit_decay_model(r_bins[mask], profile[mask])
    # correlation length definition: distance where model drops to 1/e of its max
    if best_name == "exponential":
        tau = best_params.get("tau")
        corr_len = tau
    elif best_name == "gaussian":
        sigma = best_params.get("sigma")
        corr_len = sigma
    else:
        # power‑law does not have a characteristic length; use a proxy
        corr_len = np.nan
    return [
        {
            "sample_id": sample_id,
            "element": "unknown",  # placeholder – real code would know element name
            "correlation_length": corr_len,
            "model_type": best_name,
            "AIC": best_aic,
        }
    ]

def process_dataset_and_write_metrics(
    input_csv: str,
    output_csv: str,
    element_column: str = "element_map_path",
) -> None:
    """
    Process a dataset of sample IDs and elemental map file paths, compute
    spatial metrics for each, and write the results to a CSV.

    Parameters
    ----------
    input_csv: str
        CSV with columns ``sample_id`` and a column pointing to a NumPy ``.npy``
        file containing the elemental map.
    output_csv: str
        Destination CSV for the computed metrics.
    element_column: str, optional
        Name of the column containing the path to the elemental map file.
    """
    import pandas as pd

    df = pd.read_csv(input_csv)
    all_metrics = []
    for _, row in df.iterrows():
        sample_id = row["sample_id"]
        map_path = row[element_column]
        try:
            element_map = np.load(map_path)
        except Exception as e:
            logging.error("Failed to load map for %s: %s", sample_id, e)
            continue
        metrics = compute_spatial_metrics_for_sample(sample_id, element_map)
        all_metrics.extend(metrics)
    result_df = pd.DataFrame(all_metrics)
    result_df.to_csv(output_csv, index=False)
    logging.info("Spatial metrics written to %s", output_csv)
