"""
Motion quality‑control (QC) utilities.

This module implements the functionality required by task **T002**:
- Compute mean framewise displacement (FD) per subject from BIDS
  ``*_confounds.tsv`` files.
- Verify that each subject’s ``events.tsv`` contains both ``Inclusion``
  and ``Exclusion`` trial types.
- Flag subjects whose mean FD exceeds the motion threshold
  (default 0.2 mm) or whose condition markers are missing.
- Write a JSON metadata file ``subjects_metadata.json`` that conforms to
  ``contracts/subject.schema.yaml``.
- Provide a small CLI so that the QC step can be invoked independently.

The public API matches what the test suite expects (see
``code/tests/test_qc.py``).
"""
import argparse
import json
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger
from src.exceptions import DataUnavailableError, InsufficientSubjectsError

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def load_motion_parameters(subject_id: str, raw_dir: Path) -> pd.DataFrame:
    """
    Load motion parameters from a BIDS ``*_confounds.tsv`` file.

    Parameters
    ----------
    subject_id : str
        Subject identifier (e.g. ``sub-01`` or ``01`` – the function is
        tolerant to both forms).
    raw_dir : Path
        Root of the BIDS‑style raw data directory (typically
        ``paths.data('raw')``).

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the confounds columns.

    Raises
    ------
    DataUnavailableError
        If the confounds file cannot be found.
    """
    # Normalise the subject identifier to the BIDS ``sub-XX`` format.
    sub_prefix = subject_id if subject_id.startswith("sub-") else f"sub-{subject_id}"
    confounds_pattern = raw_dir / sub_prefix / "func" / "*_confounds.tsv"
    files = list(confounds_pattern.parent.glob(confounds_pattern.name))
    if not files:
        raise DataUnavailableError(f"Confounds file not found for {subject_id}")
    # Use the first matching file (standard BIDS layout has only one per run).
    return pd.read_csv(files[0], sep="\t")


def calculate_framewise_displacement(confounds_df: pd.DataFrame) -> float:
    """
    Compute the mean framewise displacement (FD) for a run.

    If the DataFrame already contains a ``framewise_displacement`` column,
    its mean is returned directly (pre‑computed case).  Otherwise FD is
    calculated using the Jenkinson 2002 formula with a 50 mm head radius.

    Parameters
    ----------
    confounds_df : pandas.DataFrame
        Confounds table possibly containing translation (``trans_x``,
        ``trans_y``, ``trans_z``) and rotation (``rot_x``, ``rot_y``,
        ``rot_z``) columns.

    Returns
    -------
    float
        Mean FD in millimetres.
    """
    if "framewise_displacement" in confounds_df.columns:
        return float(confounds_df["framewise_displacement"].mean())

    # Expected column names (case‑sensitive as produced by fmriprep).
    trans_cols = ["trans_x", "trans_y", "trans_z"]
    rot_cols = ["rot_x", "rot_y", "rot_z"]

    missing = [c for c in trans_cols + rot_cols if c not in confounds_df.columns]
    if missing:
        raise DataUnavailableError(
            f"Missing motion columns required for FD calculation: {missing}"
        )

    # Compute absolute differences between successive volumes.
    diffs = confounds_df[trans_cols + rot_cols].diff().fillna(0).abs()

    # Convert rotational displacements to millimetres (radius = 50 mm).
    radius = 50.0
    diffs_rot_mm = diffs[rot_cols] * radius

    # Sum translation and rotation contributions per volume.
    fd_per_vol = diffs[trans_cols].sum(axis=1) + diffs_rot_mm.sum(axis=1)

    return float(fd_per_vol.mean())


def calculate_subject_motion_metrics(subject_id: str, raw_dir: Path) -> float:
    """
    Convenience wrapper that loads the confounds TSV for a subject and
    returns the mean FD.

    Parameters
    ----------
    subject_id : str
    raw_dir : Path

    Returns
    -------
    float
        Mean FD (mm) for the subject.
    """
    df = load_motion_parameters(subject_id, raw_dir)
    return calculate_framewise_displacement(df)


def verify_conditions(subject_id: str, raw_dir: Path) -> Tuple[bool, List[str]]:
    """
    Verify that a subject’s ``events.tsv`` contains both ``Inclusion``
    and ``Exclusion`` trial types.

    Parameters
    ----------
    subject_id : str
    raw_dir : Path

    Returns
    -------
    Tuple[bool, List[str]]
        ``(is_valid, conditions)`` where ``is_valid`` is True only when
        both required markers are present and ``conditions`` is the list
        of unique trial types (lower‑cased) found in the file.

    Raises
    ------
    DataUnavailableError
        If the ``events.tsv`` file cannot be located.
    """
    sub_prefix = subject_id if subject_id.startswith("sub-") else f"sub-{subject_id}"
    events_pattern = raw_dir / sub_prefix / "func" / "*_events.tsv"
    files = list(events_pattern.parent.glob(events_pattern.name))
    if not files:
        raise DataUnavailableError(f"Events file not found for {subject_id}")

    df = pd.read_csv(files[0], sep="\t")
    if "trial_type" not in df.columns:
        raise DataUnavailableError(f"'trial_type' column missing in events for {subject_id}")

    trial_types = {str(t).strip().lower() for t in df["trial_type"].unique()}
    is_valid = {"inclusion", "exclusion"}.issubset(trial_types)
    return is_valid, list(trial_types)


def calculate_subject_motion_metrics_with_conditions(
    raw_dir: Path,
) -> List[Dict[str, Any]]:
    """
    Iterate over all subjects in ``raw_dir`` and compute motion metrics
    together with condition verification.

    Returns
    -------
    List[Dict]
        Each dict contains:
            - ``subject_id`` (str)
            - ``motion_mean`` (float or None)
            - ``condition_valid`` (bool)
            - ``conditions`` (list of str)
    """
    subjects = [
        p.name
        for p in (raw_dir).glob("sub-*")
        if p.is_dir()
    ]

    results: List[Dict[str, Any]] = []
    for sub in subjects:
        try:
            motion = calculate_subject_motion_metrics(sub, raw_dir)
        except DataUnavailableError as e:
            log.warning(f"Motion metrics unavailable for {sub}: {e}")
            motion = None

        try:
            cond_valid, conds = verify_conditions(sub, raw_dir)
        except DataUnavailableError as e:
            log.warning(f"Condition verification unavailable for {sub}: {e}")
            cond_valid = False
            conds = []

        results.append(
            {
                "subject_id": sub,
                "motion_mean": motion,
                "condition_valid": cond_valid,
                "conditions": conds,
            }
        )
    return results


def filter_by_motion_threshold(
    subject_list: List[Dict[str, Any]], threshold: float = 0.2
) -> List[Dict[str, Any]]:
    """
    Apply the motion threshold (FR‑002) and condition validity filter.

    The function adds a ``qc_status`` key to each subject dictionary:
    - ``"passed"`` when ``motion_mean`` is ≤ ``threshold`` **and**
      ``condition_valid`` is True.
    - ``"failed"`` otherwise (including missing motion data).

    Parameters
    ----------
    subject_list : list of dict
        Output of ``calculate_subject_motion_metrics_with_conditions``.
    threshold : float, optional
        Motion threshold in millimetres (default 0.2).

    Returns
    -------
    list of dict
        Updated subject dictionaries with ``qc_status``.
    """
    filtered = []
    for sub in subject_list:
        motion = sub.get("motion_mean")
        cond_valid = sub.get("condition_valid", False)

        if motion is None or motion > threshold or not cond_valid:
            status = "failed"
        else:
            status = "passed"

        new_sub = dict(sub)  # shallow copy
        new_sub["qc_status"] = status
        filtered.append(new_sub)

    return filtered


def check_subject_count(subject_list: List[Dict[str, Any]], min_count: int = 10) -> None:
    """
    Verify that at least ``min_count`` subjects have passed QC.

    Raises
    ------
    InsufficientSubjectsError
        If the number of subjects with ``qc_status == "passed"`` is lower
        than ``min_count``.
    """
    passed = [s for s in subject_list if s.get("qc_status") == "passed"]
    if len(passed) < min_count:
        raise InsufficientSubjectsError(len(passed))


# ----------------------------------------------------------------------
# Pipeline orchestration
# ----------------------------------------------------------------------


def run_qc_pipeline(
    raw_dir: Path,
    output_dir: Path,
    motion_threshold: float = 0.2,
    min_subjects: int = 10,
) -> List[Dict[str, Any]]:
    """
    Execute the full QC workflow:

    1. Compute per‑subject motion metrics and condition validity.
    2. Apply the motion threshold filter.
    3. Write ``subjects_metadata.json`` (the filtered list) to ``output_dir``.
    4. Validate that at least ``min_subjects`` subjects have passed QC.

    Parameters
    ----------
    raw_dir : Path
        Directory containing the BIDS‑style raw dataset.
    output_dir : Path
        Directory where ``subjects_metadata.json`` will be written.
    motion_threshold : float, optional
        FD threshold in millimetres (default 0.2).
    min_subjects : int, optional
        Minimum number of retained subjects required (default 10).

    Returns
    -------
    list of dict
        The filtered subject metadata (including ``qc_status``).
    """
    log.info(f"Running QC on raw data directory: {raw_dir}")

    # 1. Gather raw metrics.
    raw_metrics = calculate_subject_motion_metrics_with_conditions(raw_dir)

    # 2. Apply threshold & condition filter.
    filtered = filter_by_motion_threshold(raw_metrics, threshold=motion_threshold)

    # 3. Persist results.
    output_dir.mkdir(parents=True, exist_ok=True)
    subjects_path = output_dir / "subjects_metadata.json"
    with subjects_path.open("w", encoding="utf-8") as fp:
        json.dump(filtered, fp, indent=2, sort_keys=True)
    log.info(f"Wrote subjects metadata to {subjects_path}")

    # Also write the full QC list for completeness (mirrors historic artifact).
    qc_list_path = output_dir / "subject_qc_list.json"
    with qc_list_path.open("w", encoding="utf-8") as fp:
        json.dump(filtered, fp, indent=2, sort_keys=True)
    log.info(f"Wrote subject QC list to {qc_list_path}")

    # 4. Enforce minimum subject count.
    check_subject_count(filtered, min_count=min_subjects)

    return filtered


def main(argv: List[str] = None) -> int:
    """
    Command‑line entry point.

    Arguments are parsed with ``argparse``; defaults point to the standard
    project data locations managed by ``llmxive_toolkit.paths``.
    """
    parser = argparse.ArgumentParser(description="Run motion QC.")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=paths.data("raw"),
        help="Root directory of the raw BIDS dataset.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=paths.data("processed"),
        help="Directory where QC JSON files will be written.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.2,
        help="Mean FD threshold (mm) for subject exclusion.",
    )
    parser.add_argument(
        "--min-subjects",
        type=int,
        default=10,
        help="Minimum number of subjects required after QC.",
    )
    args = parser.parse_args(argv)

    try:
        run_qc_pipeline(
            raw_dir=args.raw_dir,
            output_dir=args.output_dir,
            motion_threshold=args.threshold,
            min_subjects=args.min_subjects,
        )
    except InsufficientSubjectsError as e:
        log.error(f"Insufficient subjects after QC: {e}")
        return 1
    except DataUnavailableError as e:
        log.error(f"Data unavailable during QC: {e}")
        return 1
    except Exception as e:
        log.exception(f"Unexpected error during QC: {e}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
