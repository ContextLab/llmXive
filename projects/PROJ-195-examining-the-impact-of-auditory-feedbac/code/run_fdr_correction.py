"""
T025: Apply voxel-wise FDR correction (q < 0.05) to the group-level
one-sample t-test results and extract significant clusters.

Method: Benjamini-Hochberg FDR correction on the 3D t-statistic map
(voxel-wise two-sided p-values derived from the t statistics and the
group degrees of freedom). This is the same procedure exposed by
nilearn.mass_univariate / statsmodels fdr_correction.

Edge case: if no voxels/clusters survive FDR, the uncorrected map is
saved to data/processed/uncorrected_map.nii.gz, a global t-statistic
p-value is computed, and "NULL RESULT: No clusters survived FDR" is
logged via utils.log_deviation.

Outputs:
  - data/processed/fdr_mask.nii.gz      (thresholded FDR mask)
  - data/processed/fdr_clusters.csv     (cluster table)
  - data/processed/uncorrected_map.nii.gz  (only in the null case)
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import nibabel as nib
import pandas as pd
from scipy import stats
from scipy import ndimage
import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from utils import log_deviation  # noqa: E402

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("fdr_correction")

TMAP_CANDIDATES = [
    "group_t_map.nii.gz",
    "group_ttest_t.nii.gz",
    "group_ttest_tmap.nii.gz",
    "group_level_t.nii.gz",
    "one_sample_t.nii.gz",
    "group_tstat.nii.gz",
    "t_map.nii.gz",
]


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}. "
            "stats_config.yaml is required (T004).")
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    if "fdr_threshold" not in cfg:
        raise KeyError("fdr_threshold missing from stats_config.yaml")
    return cfg


def find_group_t_map(processed_dir: Path,
                     explicit: Optional[str] = None) -> Path:
    """Locate the group-level t-statistic map produced by T024."""
    if explicit:
        p = Path(explicit)
        if not p.is_absolute():
            p = Path.cwd() / p
        if not p.exists():
            raise FileNotFoundError(f"Specified t-map not found: {p}")
        return p
    for name in TMAP_CANDIDATES:
        cand = processed_dir / name
        if cand.exists():
            return cand
    # last resort: any group-ish t map in processed dir
    matches = sorted(processed_dir.glob("*group*t*.nii.gz"))
    if matches:
        return matches[0]
    raise FileNotFoundError(
        "Could not locate the group-level t-statistic map in "
        f"{processed_dir}. Run code/glm_group.py (T024) first, or pass "
        "--tmap explicitly.")


def load_degrees_of_freedom(t_map_path: Path,
                            explicit_df: Optional[int] = None) -> int:
    """Determine group degrees of freedom (n_subjects - 1)."""
    if explicit_df is not None:
        return int(explicit_df)
    sidecar = t_map_path.with_suffix("").with_suffix(".json")
    for cand in [sidecar, t_map_path.parent / "group_ttest_info.json",
                 t_map_path.parent / "group_level_info.json"]:
        if cand.exists():
            with open(cand) as f:
                info = json.load(f)
            for key in ("df", "dof", "degrees_of_freedom", "n_subjects"):
                if key in info:
                    val = int(info[key])
                    return val if key != "n_subjects" else val - 1
    # derive from number of contrast maps on disk
    cm_dir = t_map_path.parent / "contrast_maps"
    if cm_dir.is_dir():
        n = len(list(cm_dir.glob("*.nii.gz")))
        if n > 1:
            LOGGER.info("Derived df=%d from %d contrast maps",
                        n - 1, n)
            return n - 1
    raise RuntimeError(
        "Could not determine degrees of freedom for the t map. "
        "Pass --df <n_subjects - 1> or provide a sidecar JSON with "
        "'df' or 'n_subjects'.")


def benjamini_hochberg(pvals: np.ndarray, q: float) -> np.ndarray:
    """Vectorized Benjamini-Hochberg FDR correction.

    Returns a boolean array marking p-values that survive FDR at level q.
    """
    pvals = np.asarray(pvals, dtype=float)
    n = pvals.size
    order = np.argsort(pvals, kind="mergesort")
    ranked = pvals[order]
    thresholds = (np.arange(1, n + 1) / n) * q
    # largest k such that p_(k) <= k*q/n
    below = ranked <= thresholds
    reject_sorted = np.zeros(n, dtype=bool)
    if np.any(below):
        k_max = np.max(np.nonzero(below)[0])
        reject_sorted[: k_max + 1] = True
    reject = np.zeros(n, dtype=bool)
    reject[order] = reject_sorted
    return reject


def fdr_correct_t_map(t_data: np.ndarray, df: int, q: float):
    """Compute two-sided p-values and FDR-correct them.

    Returns (pvals, fdr_mask) where pvals has the same shape as t_data
    (NaN outside the brain) and fdr_mask is the boolean surviving mask.
    """
    brain = np.isfinite(t_data) & (t_data != 0)
    pvals = np.full(t_data.shape, np.nan)
    tvals = t_data[brain]
    if tvals.size == 0:
        raise ValueError("t-statistic map contains no valid voxels")
    pvals[brain] = 2.0 * stats.t.sf(np.abs(tvals), df)
    reject = benjamini_hochberg(pvals[brain], q)
    fdr_mask = np.zeros(t_data.shape, dtype=bool)
    fdr_mask[brain] = reject
    LOGGER.info("FDR q=%.3f: %d / %d voxels survive (%.2f%%)",
                q, int(reject.sum()), int(tvals.size),
                100.0 * reject.mean() if tvals.size else 0.0)
    return pvals, fdr_mask, brain


def extract_clusters(t_data: np.ndarray, pvals: np.ndarray,
                     fdr_mask: np.ndarray,
                     affine: np.ndarray) -> pd.DataFrame:
    """Extract significant clusters from the FDR-thresholded mask.

    Each cluster is reported with its peak voxel coordinates (MNI mm),
    the t-statistic and FDR-corrected p-value at the peak, and the
    cluster size in voxels.
    """
    rows = []
    if not fdr_mask.any():
        return pd.DataFrame(columns=[
            "cluster_id", "x", "y", "z", "t", "p_val_fdr",
            "n_voxels", "peak_voxel_i", "peak_voxel_j", "peak_voxel_k",
            "description"])
    labeled, n_clusters = ndimage.label(fdr_mask)
    LOGGER.info("Found %d significant cluster(s)", n_clusters)
    for cid in range(1, n_clusters + 1):
        idx = np.array(np.nonzero(labeled == cid)).T  # (k, 3)
        t_vals_cluster = np.array([t_data[tuple(v)] for v in idx])
        peak_i = int(np.argmax(np.abs(t_vals_cluster)))
        peak_voxel = idx[peak_i]
        i, j, k = peak_voxel
        xyz_mm = nib.affines.apply_affine(affine, peak_voxel[[2, 1, 0]]
                                          if False else peak_voxel)
        # peak_voxel is in (i, j, k) array order; affine maps (i,j,k)
        xyz_mm = nib.affines.apply_affine(affine, peak_voxel)
        rows.append({
            "cluster_id": cid,
            "x": round(float(xyz_mm[0]), 2),
            "y": round(float(xyz_mm[1]), 2),
            "z": round(float(xyz_mm[2]), 2),
            "t": round(float(t_data[i, j, k]), 4),
            "p_val_fdr": round(float(pvals[i, j, k]), 6),
            "n_voxels": int(len(idx)),
            "peak_voxel_i": i,
            "peak_voxel_j": j,
            "peak_voxel_k": k,
            "description": (
                "significant cluster (perturbed > normal, FDR q<%.2f)"
                % 0.05),
        })
    return pd.DataFrame(rows)


def global_t_test(t_data: np.ndarray, brain: np.ndarray) -> dict:
    """Global one-sample t-test across intracerebral voxels (null case)."""
    tvals = t_data[brain]
    res = stats.ttest_1samp(tvals, 0.0)
    return {
        "global_t_statistic": float(res.statistic),
        "global_p_value": float(res.pvalue),
        "n_voxels": int(tvals.size),
        "mean_t": float(np.mean(tvals)),
    }


def main():
    parser = argparse.ArgumentParser(
        description="T025: voxel-wise FDR correction of the group "
                    "one-sample t-test map")
    parser.add_argument("--config", default="stats_config.yaml")
    parser.add_argument("--output-dir", default="data/processed")
    parser.add_argument("--tmap", default=None,
                        help="Explicit path to the group t map")
    parser.add_argument("--df", type=int, default=None,
                        help="Degrees of freedom (n_subjects - 1)")
    parser.add_argument("--q", type=float, default=None,
                        help="FDR level override")
    args = parser.parse_args()

    project_root = Path.cwd()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = project_root / config_path
    cfg = load_config(config_path)
    q = args.q if args.q is not None else float(cfg["fdr_threshold"])

    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = project_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    t_map_path = find_group_t_map(out_dir, args.tmap)
    LOGGER.info("Loading group t map: %s", t_map_path)
    t_img = nib.load(str(t_map_path))
    t_data = np.asanyarray(t_img.dataobj, dtype=float)

    df = load_degrees_of_freedom(t_map_path, args.df)
    LOGGER.info("Degrees of freedom: %d", df)

    pvals, fdr_mask, brain = fdr_correct_t_map(t_data, df, q)

    # Save the FDR-thresholded mask
    mask_img = nib.Nifti1Image(fdr_mask.astype(np.uint8),
                               t_img.affine, t_img.header)
    mask_path = out_dir / "fdr_mask.nii.gz"
    nib.save(mask_img, str(mask_path))
    LOGGER.info("Saved FDR mask: %s", mask_path)

    # Extract clusters and save the table
    clusters_df = extract_clusters(t_data, pvals, fdr_mask,
                                   t_img.affine)
    clusters_path = out_dir / "fdr_clusters.csv"
    clusters_df.to_csv(clusters_path, index=False)
    LOGGER.info("Saved cluster table: %s (%d clusters)",
                clusters_path, len(clusters_df))

    if len(clusters_df) == 0:
        # Edge case: null result. Save uncorrected map and global p.
        LOGGER.warning("NULL RESULT: No clusters survived FDR")
        uncorr_img = nib.Nifti1Image(t_data, t_img.affine, t_img.header)
        uncorr_path = out_dir / "uncorrected_map.nii.gz"
        nib.save(uncorr_img, str(uncorr_path))
        LOGGER.info("Saved uncorrected map: %s", uncorr_path)
        glob = global_t_test(t_data, brain)
        glob["fdr_threshold"] = q
        glob["df"] = df
        glob["result"] = "NULL RESULT: No clusters survived FDR"
        glob_path = out_dir / "fdr_null_result.json"
        with open(glob_path, "w") as f:
            json.dump(glob, f, indent=2)
        LOGGER.info("Global t-statistic: %.4f, p = %.6f",
                    glob["global_t_statistic"], glob["global_p_value"])
        try:
            log_deviation(
                "group",
                "null_result",
                ("NULL RESULT: No clusters survived FDR "
                 f"(q={q}, df={df}, global p="
                 f"{glob['global_p_value']:.6f})"))
        except Exception as exc:  # logging must not kill the analysis
            LOGGER.warning("log_deviation failed: %s", exc)
    else:
        LOGGER.info("FDR correction complete: %d significant clusters",
                    len(clusters_df))

    return 0


if __name__ == "__main__":
    sys.exit(main())