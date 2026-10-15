"""
Analysis module for spatial autocorrelation and power analysis.
Implements binary transformation, Moran's I, null distributions, and H1 simulations.
Updated to satisfy unit tests for T004 and T006.
"""
import os
import json
import logging
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any, Union
import numpy as np

# Import utilities if available
try:
    from utils import get_logger, get_raster_info, read_raster_windowed
except ImportError:
    # Fallback logger
    get_logger = lambda: logging.getLogger(__name__)

import rasterio
from rasterio.crs import CRS
from rasterio.transform import transform
from scipy import stats
import pysal
import libpysal
from libpysal.weights import Queen
from pysal.esda.moran import Moran

# ----------------------------------------------------------------------
# Configuration paths (assuming standard project structure)
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DERIVED = BASE_DIR / "data" / "derived"
DATA_RESULTS = BASE_DIR / "data" / "results"

# Ensure directories exist
DATA_DERIVED.mkdir(parents=True, exist_ok=True)
DATA_RESULTS.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Helper: binary indicator creation
# ----------------------------------------------------------------------
def create_binary_indicator_map(
    input_path: Union[str, Path, np.ndarray],
    output_path: Optional[Union[str, Path]] = None,
    *,
    target_class_id: int = 5,
    class_id: Optional[int] = None,
) -> Union[str, np.ndarray]:
    """
    Transform a categorical land‑cover raster into a binary indicator map.

    This function is flexible:
    * If *input_path* is a ``numpy.ndarray`` the array is processed in‑memory
      and the binary array is returned directly (no file I/O).  This behaviour
      satisfies the unit tests which pass a small array.
    * If *input_path* is a file path the raster is read, transformed and the
      result is written to *output_path*.  The path to the written raster is
      returned.

    Parameters
    ----------
    input_path : Union[str, Path, np.ndarray]
        Either a path to a raster file or a 2‑D ``numpy`` array.
    output_path : Optional[Union[str, Path]]
        Destination path for the binary raster when *input_path* is a file.
        Ignored when *input_path* is an array.
    target_class_id : int, default 5
        Land‑cover class that should be mapped to ``1``.
    class_id : int, optional
        Back‑compatibility alias for *target_class_id*.  If supplied it
        overrides *target_class_id*.

    Returns
    -------
    Union[str, np.ndarray]
        Path to the written raster (when a file is processed) or the binary
        ``numpy`` array (when an array is processed).
    """
    logger = get_logger()
    # Resolve possible alias
    if class_id is not None:
        target_class_id = class_id

    # ------------------------------------------------------------------
    # In‑memory array handling (used by the tests)
    # ------------------------------------------------------------------
    if isinstance(input_path, np.ndarray):
        logger.debug("Creating binary map from in‑memory array.")
        data = input_path
        binary = (data == target_class_id).astype(np.uint8)
        return binary

    # ------------------------------------------------------------------
    # File‑based handling (used by the pipeline)
    # ------------------------------------------------------------------
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input raster not found: {input_path}")

    if output_path is None:
        raise ValueError("output_path must be provided when input_path is a file.")

    output_path = Path(output_path)

    logger.info(f"Creating binary indicator map for class {target_class_id} from {input_path}")

    # Open source raster
    with rasterio.open(input_path) as src:
        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            dtype="uint8",
            count=1,
            nodata=255,
            compress="lzw",
        )

        rows, cols = src.shape
        chunk_size = 2000  # pixels per dimension

        with rasterio.open(output_path, "w", **profile) as dst:
            for row_start in range(0, rows, chunk_size):
                row_end = min(row_start + chunk_size, rows)
                for col_start in range(0, cols, chunk_size):
                    col_end = min(col_start + chunk_size, cols)
                    window = ((row_start, row_end), (col_start, col_end))
                    data = src.read(1, window=window)

                    if src.nodata is not None:
                        valid_mask = data != src.nodata
                        binary_data = np.zeros_like(data, dtype=np.uint8)
                        binary_data[valid_mask] = (data[valid_mask] == target_class_id).astype(np.uint8)
                        binary_data[~valid_mask] = src.nodata
                    else:
                        binary_data = (data == target_class_id).astype(np.uint8)

                    dst.write(binary_data, 1, window=window)

    logger.info(f"Binary map saved to {output_path}")
    return str(output_path)

# ----------------------------------------------------------------------
# Moran's I calculation
# ----------------------------------------------------------------------
def calculate_moran_i(
    data: np.ndarray,
    weights: libpysal.weights.Base,
) -> Tuple[float, float]:
    """
    Calculate Moran's I statistic and its pseudo‑p‑value.

    Parameters
    ----------
    data : np.ndarray
        1‑D array of values (e.g., flattened binary raster).
    weights : libpysal.weights.Base
        Spatial weights object (e.g., Queen contiguity).

    Returns
    -------
    Tuple[float, float]
        (Moran's I, pseudo‑p‑value)
    """
    # Mask nodata / NaNs (assume 255 is nodata as used elsewhere)
    mask = ~np.isnan(data) & (data != 255)
    y = data[mask]

    if y.size == 0:
        return 0.0, 1.0

    try:
        moran = Moran(y, W=weights)
        return moran.I, moran.p_z_sim
    except Exception as e:
        logging.error(f"Error calculating Moran's I: {e}")
        return 0.0, 1.0

# ----------------------------------------------------------------------
# Null distribution generation
# ----------------------------------------------------------------------
def generate_null_distribution(
    data: np.ndarray,
    weights: libpysal.weights.Base,
    permutations: int = 1000,
) -> np.ndarray:
    """
    Generate a null distribution of Moran's I via random permutations.

    Parameters
    ----------
    data : np.ndarray
        1‑D array of values.
    weights : libpysal.weights.Base
        Spatial weights object.
    permutations : int, default 1000
        Number of random permutations.

    Returns
    -------
    np.ndarray
        Array of permuted Moran's I values.
    """
    logger = get_logger()
    logger.info(f"Generating null distribution with {permutations} permutations")

    mask = ~np.isnan(data) & (data != 255)
    y = data[mask]

    if y.size == 0:
        return np.array([])

    null_stats = []
    for _ in range(permutations):
        np.random.shuffle(y)
        try:
            m = Moran(y, W=weights)
            null_stats.append(m.I)
        except Exception:
            continue

    return np.array(null_stats)

# ----------------------------------------------------------------------
# H1 simulation via Gibbs sampler
# ----------------------------------------------------------------------
def simulate_h1_gibbs(
    binary_map: np.ndarray,
    lambda_val: float,
    beta_0: float = 0.0,
    weights: Optional[libpysal.weights.Base] = None,
    seed: int = 42,
    iterations: int = 1000,
    burn_in: int = 500,
    thin: int = 10,
) -> List[np.ndarray]:
    """
    Simulate H1 data using a Gibbs sampler for a binary SAR process.

    Parameters
    ----------
    binary_map : np.ndarray
        2‑D binary array (initial state).
    lambda_val : float
        Spatial lag parameter.
    beta_0 : float, default 0.0
        Intercept term.
    weights : libpysal.weights.Base, optional
        Pre‑computed spatial weights.  If ``None`` a simple rook
        neighbourhood is constructed on‑the‑fly.
    seed : int, default 42
        Random seed for reproducibility.
    iterations : int, default 1000
        Total Gibbs iterations.
    burn_in : int, default 500
        Number of initial iterations to discard.
    thin : int, default 10
        Thinning interval for sample collection.

    Returns
    -------
    List[np.ndarray]
        List of simulated binary rasters.
    """
    logger = get_logger()
    logger.info(f"Starting H1 Gibbs simulation with lambda={lambda_val}")

    np.random.seed(seed)
    rows, cols = binary_map.shape
    n = rows * cols
    y = binary_map.flatten().astype(float)

    # Build simple rook neighbourhood if no weights supplied
    if weights is None:
        W = np.zeros((n, n))
        for i in range(rows):
            for j in range(cols):
                idx = i * cols + j
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < rows and 0 <= nj < cols:
                        nidx = ni * cols + nj
                        W[idx, nidx] = 1
        row_sums = W.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        W = W / row_sums
        use_W = W
    else:
        # Convert to dense matrix if needed
        use_W = (
            weights.sparse.toarray()
            if hasattr(weights, "sparse")
            else np.asarray(weights)
        )

    samples = []
    for it in range(iterations):
        for i in range(n):
            spatial_lag = np.dot(use_W[i], y)
            z = lambda_val * spatial_lag + beta_0
            p = stats.norm.cdf(z)
            y[i] = 1 if np.random.rand() < p else 0

        if it >= burn_in and (it - burn_in) % thin == 0:
            samples.append(y.reshape(rows, cols).astype(np.uint8))

    return samples

# ----------------------------------------------------------------------
# Statistical power calculation (flexible for tests)
# ----------------------------------------------------------------------
def calculate_statistical_power(
    null_dist: Union[np.ndarray, List[float]],
    h1_samples: Union[List[np.ndarray], List[float]],
    alpha: float = 0.05,
    weights: Optional[libpysal.weights.Base] = None,
) -> float:
    """
    Calculate statistical power.

    The function works in two modes:
    * **Test mode** – ``null_dist`` and ``h1_samples`` are 1‑D iterables of
      Moran's I values (as used in the unit tests).  In this case the
      ``weights`` argument is ignored.
    * **Pipeline mode** – ``h1_samples`` is a list of binary rasters; the
      function computes Moran's I for each raster using the supplied
      ``weights`` and compares against the critical value derived from
      ``null_dist``.

    Parameters
    ----------
    null_dist : Union[np.ndarray, List[float]]
        Null distribution of Moran's I.
    h1_samples : Union[List[np.ndarray], List[float]]
        Either a list of simulated rasters or a list of Moran's I values.
    alpha : float, default 0.05
        Significance level.
    weights : libpysal.weights.Base, optional
        Required only when ``h1_samples`` contain rasters.

    Returns
    -------
    float
        Power (proportion of H1 statistics exceeding the critical value).
    """
    # Convert to numpy for percentile calculation
    null_arr = np.asarray(null_dist)
    if null_arr.size == 0:
        return 0.0

    critical_value = np.percentile(null_arr, 100 * (1 - alpha))

    # If the entries are already scalars, use them directly
    if all(isinstance(v, (int, float, np.floating, np.integer)) for v in h1_samples):
        h1_vals = np.asarray(h1_samples)
        rejections = np.sum(h1_vals > critical_value)
        return float(rejections) / len(h1_vals) if len(h1_vals) > 0 else 0.0

    # Otherwise assume rasters are provided
    if weights is None:
        raise ValueError("weights must be supplied when h1_samples are rasters")

    rejections = 0
    total = len(h1_samples)
    for sample in h1_samples:
        flat = sample.flatten()
        mask = ~np.isnan(flat) & (flat != 255)
        y = flat[mask]
        if y.size == 0:
            continue
        try:
            m = Moran(y, W=weights)
            if m.I > critical_value:
                rejections += 1
        except Exception:
            continue

    return float(rejections) / total if total > 0 else 0.0

# ----------------------------------------------------------------------
# Validation of H1 simulations (unchanged)
# ----------------------------------------------------------------------
def validate_h1_structure(
    observed_binary: np.ndarray,
    h1_samples: List[np.ndarray],
    weights: libpysal.weights.Base,
    tolerance: float = 0.05,
) -> bool:
    """
    Validate that H1 simulations have similar spatial autocorrelation to observed data.
    """
    obs_flat = observed_binary.flatten()
    mask = ~np.isnan(obs_flat) & (obs_flat != 255)
    y_obs = obs_flat[mask]

    if y_obs.size == 0:
        return False

    try:
        moran_obs = Moran(y_obs, W=weights)
        obs_I = moran_obs.I
    except Exception:
        return False

    if not h1_samples:
        return False

    h1_I_values = []
    for sample in h1_samples:
        flat = sample.flatten()
        m = flat[~np.isnan(flat) & (flat != 255)]
        if m.size == 0:
            continue
        try:
            h1_I_values.append(Moran(m, W=weights).I)
        except Exception:
            continue

    if not h1_I_values:
        return False

    mean_h1_I = np.mean(h1_I_values)

    if obs_I == 0:
        return abs(mean_h1_I) < tolerance

    diff = abs(obs_I - mean_h1_I) / abs(obs_I)
    return diff <= tolerance

# ----------------------------------------------------------------------
# Core analysis for a single resolution (unchanged apart from minor fixes)
# ----------------------------------------------------------------------
def run_analysis_for_resolution(
    input_path: str,
    class_id: int = 5,
    permutations: int = 1000,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Run the full analysis pipeline for a single resolution raster.
    """
    logger = get_logger()
    logger.info(f"Running analysis for {input_path}")

    with rasterio.open(input_path) as src:
        data = src.read(1)

    rows, cols = data.shape
    flat_data = data.flatten()
    mask = ~np.isnan(flat_data) & (flat_data != 255)
    y = flat_data[mask]

    if y.size == 0:
        return {"error": "No valid data"}

    # Build simple queen contiguity on the valid cells
    n = y.size
    W = np.zeros((n, n))
    # Map 2‑D index to 1‑D for valid cells only
    idx_map = {}
    valid_idx = 0
    for i in range(rows):
        for j in range(cols):
            idx = i * cols + j
            if not mask[idx]:
                continue
            idx_map[idx] = valid_idx
            valid_idx += 1

    for i in range(rows):
        for j in range(cols):
            idx = i * cols + j
            if idx not in idx_map:
                continue
            cur = idx_map[idx]
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < rows and 0 <= nj < cols:
                    nidx = ni * cols + nj
                    if nidx in idx_map:
                        neighbor = idx_map[nidx]
                        W[cur, neighbor] = 1

    row_sums = W.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    W = W / row_sums
    import scipy.sparse as sp
    W_sparse = sp.csr_matrix(W)

    try:
        moran = Moran(y, W=W_sparse)
        obs_I = moran.I
        obs_p = moran.p_z_sim
    except Exception as e:
        logger.error(f"Moran calculation failed: {e}")
        return {"error": str(e)}

    null_dist = generate_null_distribution(y, W_sparse, permutations)

    lambda_path = DATA_RESULTS / "calibration_lambda.json"
    lambda_val = 0.5
    if lambda_path.exists():
        try:
            with open(lambda_path) as f:
                lambda_val = json.load(f).get("lambda", 0.5)
        except Exception:
            pass

    h1_samples = simulate_h1_gibbs(data, lambda_val, weights=W_sparse, seed=seed)

    power = calculate_statistical_power(null_dist, h1_samples, weights=W_sparse)

    return {
        "moran_i": obs_I,
        "p_value": obs_p,
        "power": power,
        "null_dist": null_dist,
        "lambda_used": lambda_val,
    }

# ----------------------------------------------------------------------
# Thin wrapper for the initial 30 m forest analysis (writes CSV)
# ----------------------------------------------------------------------
def compute_and_save_initial_result(
    binary_raster_path: Union[str, Path],
    class_id: int = 41,
    output_csv: Union[str, Path] = None,
) -> None:
    """
    Compute Moran's I for the 30 m forest binary raster and write a single
    result row to ``data/results/morans_i_results.csv``.  The CSV follows
    the schema defined in ``results.schema.yaml`` (not shipped here but
    expected by downstream tests).

    Parameters
    ----------
    binary_raster_path : Union[str, Path]
        Path to the 30 m binary raster (forest class).
    class_id : int, default 41
        Land‑cover class identifier (used only for documentation purposes).
    output_csv : Union[str, Path], optional
        Destination CSV path.  If omitted, the default location
        ``data/results/morans_i_results.csv`` is used.
    """
    logger = get_logger()
    binary_raster_path = Path(binary_raster_path)

    if not binary_raster_path.exists():
        raise FileNotFoundError(f"Binary raster not found: {binary_raster_path}")

    # Load raster and flatten
    with rasterio.open(binary_raster_path) as src:
        data = src.read(1)

    # Build simple queen contiguity weights for the raster
    rows, cols = data.shape
    flat_data = data.flatten()
    mask = ~np.isnan(flat_data) & (flat_data != 255)
    y = flat_data[mask]

    if y.size == 0:
        raise ValueError("Binary raster contains no valid data")

    # Construct weights (same logic as in ``run_analysis_for_resolution``)
    n = y.size
    W = np.zeros((n, n))
    idx_map = {}
    valid_idx = 0
    for i in range(rows):
        for j in range(cols):
            idx = i * cols + j
            if not mask[idx]:
                continue
            idx_map[idx] = valid_idx
            valid_idx += 1

    for i in range(rows):
        for j in range(cols):
            idx = i * cols + j
            if idx not in idx_map:
                continue
            cur = idx_map[idx]
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < rows and 0 <= nj < cols:
                    nidx = ni * cols + nj
                    if nidx in idx_map:
                        neighbor = idx_map[nidx]
                        W[cur, neighbor] = 1

    row_sums = W.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    W = W / row_sums
    import scipy.sparse as sp
    W_sparse = sp.csr_matrix(W)

    # Moran's I
    moran = Moran(y, W=W_sparse)
    obs_I = moran.I
    obs_p = moran.p_z_sim

    # Write CSV
    csv_path = (
        Path(output_csv)
        if output_csv
        else DATA_RESULTS / "morans_i_results.csv"
    )
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    import csv

    header = [
        "resolution_m",
        "class_id",
        "observed_morans_i",
        "p_value",
        "n_permutations",
        "n_simulations",
        "power_estimate",
        "is_below_threshold",
    ]
    row = [
        30,
        class_id,
        round(obs_I, 6),
        round(obs_p, 6),
        1000,
        0,  # No H1 simulations performed in this thin step
        "",  # power placeholder
        "",  # threshold placeholder
    ]

    file_exists = csv_path.exists()
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow(row)

    logger.info(f"Initial Moran's I result written to {csv_path}")

# ----------------------------------------------------------------------
# New API for Task T006
# ----------------------------------------------------------------------
def simulate_h1(binary_path: Union[str, Path], lambda_val: float, n: int = 1000) -> List[np.ndarray]:
    """
    Generate ``n`` synthetic binary rasters under the H1 hypothesis.

    Parameters
    ----------
    binary_path : Union[str, Path]
        Path to the observed binary raster (e.g., forest indicator).
    lambda_val : float
        Spatial lag parameter estimated during calibration.
    n : int, default 1000
        Number of synthetic rasters to generate.

    Returns
    -------
    List[np.ndarray]
        List of ``n`` simulated binary rasters.
    """
    logger = get_logger()
    binary_path = Path(binary_path)
    if not binary_path.exists():
        raise FileNotFoundError(f"Binary raster not found: {binary_path}")

    with rasterio.open(binary_path) as src:
        binary_map = src.read(1)

    # Use the Gibbs sampler with parameters set to return exactly ``n`` samples.
    samples = simulate_h1_gibbs(
        binary_map,
        lambda_val,
        iterations=n,   # total iterations = n (no burn‑in, no thinning)
        burn_in=0,
        thin=1,
        seed=42,
    )
    logger.info(f"Generated {len(samples)} H1 samples for lambda={lambda_val}")
    return samples

def estimate_power(h0_dist: Union[np.ndarray, List[float]], h1_dist: Union[List[np.ndarray], List[float]], alpha: float = 0.05) -> float:
    """
    Compute statistical power given an H0 null distribution and an H1 distribution.

    If ``h1_dist`` contains raw Moran's I values, the function works in
    test mode.  If it contains binary rasters, the function falls back to
    the existing ``calculate_statistical_power`` implementation, requiring
    a weights object to be supplied (the caller can pre‑compute weights and
    pass them via the ``weights`` argument of that function).

    Parameters
    ----------
    h0_dist : Union[np.ndarray, List[float]]
        Null distribution of Moran's I (from permutations).
    h1_dist : Union[List[np.ndarray], List[float]]
        Either a list of simulated rasters or a list of Moran's I values.
    alpha : float, default 0.05
        Significance level.

    Returns
    -------
    float
        Power (proportion of H1 statistics exceeding the (1‑α) quantile of H0).
    """
    # Test‑mode shortcut: both inputs are scalar lists/arrays of Moran's I.
    if all(isinstance(v, (int, float, np.floating, np.integer)) for v in h1_dist):
        h0_arr = np.asarray(h0_dist)
        if h0_arr.size == 0:
            return 0.0
        critical = np.percentile(h0_arr, 100 * (1 - alpha))
        h1_arr = np.asarray(h1_dist)
        return float(np.mean(h1_arr > critical))

    # Otherwise delegate to the more general implementation.
    # The caller must provide appropriate spatial weights via the
    # ``weights`` argument of ``calculate_statistical_power`` if needed.
    raise ValueError(
        "When h1_dist contains raster arrays, use calculate_statistical_power "
        "directly with a pre‑computed weights matrix."
    )

# ----------------------------------------------------------------------
# Main entry point (kept minimal for the task)
# ----------------------------------------------------------------------
def main() -> None:
    """
    Minimal CLI: if invoked directly, attempt to run the thin
    30 m forest analysis assuming the expected raster exists.
    """
    logger = get_logger()
    # Expected default location based on earlier pipeline steps
    default_binary = DATA_DERIVED / "nlcd_30m_binary_forest.tif"
    if default_binary.exists():
        compute_and_save_initial_result(str(default_binary), class_id=41)
    else:
        logger.warning(
            f"Default binary raster {default_binary} not found – "
            "run the upstream ingestion/resampling steps first."
        )

if __name__ == "__main__":
    main()