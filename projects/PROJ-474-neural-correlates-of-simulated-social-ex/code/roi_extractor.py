"""
Raw ROI extraction and condition segmentation (T003).

Implements FR-003 (extract raw BOLD time-series for the four Harvard-Oxford
DMN ROIs: PCC, mPFC, L_ANG, R_ANG), FR-004 (extraction happens on the RAW
signal, before any confound regression), FR-011 / FR-014 (subjects missing
an ROI or a condition are excluded) and FR-009 (abort with error code
101897696 if fewer than 10 subjects are retained).

The module operates on the real BIDS data downloaded under ``data/raw/``
and writes per-subject/condition Parquet files plus validation
side-records conforming to ``contracts/timeseries.schema.yaml``.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import nibabel as nib
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ROIS = ["PCC", "mPFC", "L_ANG", "R_ANG"]

# Harvard-Oxford cortical atlas label names (cort-maxprob-thr25-2mm).
# The Harvard-Oxford atlas does not split the angular gyrus by hemisphere,
# so L_ANG / R_ANG are derived by splitting the "Angular Gyrus" label at
# the mid-sagittal plane (MNI x = 0).
HO_LABELS = {
    "PCC": "Cingulate Gyrus, posterior division",
    "mPFC": "Frontal Medial Cortex",
    "ANG": "Angular Gyrus",
}

CONDITIONS = ["Inclusion", "Exclusion"]
MIN_SUBJECTS = 10
ERROR_INSUFFICIENT_SUBJECTS = 101897696


class ROIExtractionError(RuntimeError):
    """Raised when ROI extraction fails for a subject (FR-014)."""


class InsufficientSubjectsError(RuntimeError):
    """Raised when fewer than MIN_SUBJECTS subjects are retained (FR-009)."""


# ---------------------------------------------------------------------------
# Atlas handling
# ---------------------------------------------------------------------------
def get_harvard_oxford_atlas() -> Tuple[nib.spatialimages.SpatialImage, List[str]]:
    """
    Fetch the real Harvard-Oxford cortical atlas via nilearn.

    Returns:
        (atlas_image, labels) where labels[i] is the name of label value i
        (labels[0] is "Background").
    """
    from nilearn import datasets

    atlas = datasets.fetch_atlas_harvard_oxford("cort-maxprob-thr25-2mm")
    return nib.load(atlas.maps), list(atlas.labels)


def build_roi_masks(atlas_img, labels: List[str]) -> Dict[str, np.ndarray]:
    """
    Build boolean masks for the four DMN ROIs in the atlas' voxel space.

    The angular gyrus label is split into left (MNI x < 0) and right
    (MNI x >= 0) halves using the atlas affine.
    """
    data = np.asarray(atlas_img.dataobj)
    affine = atlas_img.affine

    def label_index(name: str) -> int:
        if name not in labels:
            raise ROIExtractionError(
                f"Harvard-Oxford atlas does not contain label '{name}'"
            )
        return labels.index(name)

    masks: Dict[str, np.ndarray] = {}

    pcc_sel = data == label_index(HO_LABELS["PCC"])
    masks["PCC"] = pcc_sel

    mpfc_sel = data == label_index(HO_LABELS["mPFC"])
    masks["mPFC"] = mpfc_sel

    ang_sel = data == label_index(HO_LABELS["ANG"])
    # MNI x coordinate of every voxel (vectorised via the affine's first row)
    xx, xy, xz = affine[0, 0], affine[0, 1], affine[0, 2]
    i_idx, j_idx, k_idx = np.meshgrid(
        np.arange(data.shape[0]),
        np.arange(data.shape[1]),
        np.arange(data.shape[2]),
        indexing="ij",
    )
    mni_x = xx * i_idx + xy * j_idx + xz * k_idx + affine[0, 3]
    masks["L_ANG"] = ang_sel & (mni_x < 0)
    masks["R_ANG"] = ang_sel & (mni_x >= 0)

    return masks


# ---------------------------------------------------------------------------
# BIDS file discovery
# ---------------------------------------------------------------------------
def find_bold_file(subject_dir: Path) -> Path:
    """Locate the 4-D preprocessed BOLD NIfTI for a subject."""
    func_dir = subject_dir / "func"
    if not func_dir.is_dir():
        raise ROIExtractionError(f"No func/ directory for {subject_dir.name}")
    candidates = sorted(
        list(func_dir.glob("*task-*bold*.nii.gz"))
        + list(func_dir.glob("*task-*bold*.nii"))
    )
    # Prefer preprocessed files when both raw and preprocessed exist.
    preproc = [c for c in candidates if "preproc" in c.name or "desc-preproc" in c.name]
    chosen = preproc[0] if preproc else (candidates[0] if candidates else None)
    if chosen is None:
        raise ROIExtractionError(f"No BOLD NIfTI found for {subject_dir.name}")
    return chosen


def find_events_file(subject_dir: Path) -> Path:
    """Locate the events.tsv for a subject."""
    func_dir = subject_dir / "func"
    candidates = sorted(func_dir.glob("*events.tsv")) if func_dir.is_dir() else []
    if not candidates:
        raise ROIExtractionError(f"No events.tsv found for {subject_dir.name}")
    return candidates[0]


def get_tr(bold_img) -> float:
    """Repetition time in seconds from the NIfTI header."""
    zooms = bold_img.header.get_zooms()
    tr = float(zooms[3]) if len(zooms) > 3 else 0.0
    if not tr or tr <= 0 or not np.isfinite(tr):
        raise ROIExtractionError("Invalid or missing TR in BOLD header")
    return tr


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------
def segment_conditions(events_df: pd.DataFrame, n_vol: int, tr: float) -> Dict[str, np.ndarray]:
    """
    Map each volume to Inclusion / Exclusion using the verified events.tsv.

    Returns a dict of boolean arrays (length n_vol) per condition.
    """
    if "onset" not in events_df.columns or "trial_type" not in events_df.columns:
        raise ROIExtractionError("events.tsv must contain 'onset' and 'trial_type'")

    cond_mask = {c: np.zeros(n_vol, dtype=bool) for c in CONDITIONS}
    for _, ev in events_df.iterrows():
        trial_type = str(ev["trial_type"])
        if "Inclusion" in trial_type:
            cond = "Inclusion"
        elif "Exclusion" in trial_type:
            cond = "Exclusion"
        else:
            continue
        onset = float(ev["onset"])
        duration = float(ev["duration"]) if "duration" in events_df.columns else tr
        start = int(np.floor(onset / tr))
        end = int(np.ceil((onset + max(duration, tr)) / tr))
        cond_mask[cond][max(start, 0):min(end, n_vol)] = True
    return cond_mask


def extract_subject(
    subject_id: str,
    bold_path: Path,
    events_path: Path,
    atlas_img,
    atlas_labels: List[str],
    output_dir: Path,
) -> Dict[str, pd.DataFrame]:
    """
    Extract raw mean BOLD time-series for the four DMN ROIs of one subject,
    segmented into Inclusion and Exclusion conditions.

    Returns a dict condition -> DataFrame with columns
    [timepoint, PCC, mPFC, L_ANG, R_ANG]. Also writes the per-condition
    Parquet files and the validation side-records.
    """
    from nilearn import image as nimg

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # mmap=True keeps memory low on large 4-D files (FR: streaming).
    bold = nib.load(str(bold_path), mmap=True)
    if len(bold.shape) != 4:
        raise ROIExtractionError(f"{bold_path.name} is not a 4-D BOLD image")
    tr = get_tr(bold)
    n_vol = bold.shape[3]

    # Resample ROI masks into the BOLD image's grid (nearest neighbour).
    atlas_masks = build_roi_masks(atlas_img, atlas_labels)
    masks = {}
    for roi, sel in atlas_masks.items():
        mimg = nib.Nifti1Image(sel.astype(np.uint8), atlas_img.affine)
        resampled = nimg.resample_to_img(mimg, bold, interpolation="nearest")
        masks[roi] = np.asarray(resampled.dataobj) > 0
        if masks[roi].sum() == 0:
            raise ROIExtractionError(
                f"ROI {roi} is empty in the BOLD grid for {subject_id} (FR-014)"
            )

    # Raw mean signal per ROI per volume — NO confound regression (FR-004).
    dataobj = bold.dataobj
    ts = {roi: np.empty(n_vol, dtype=float) for roi in ROIS}
    for t in range(n_vol):
        vol = np.asarray(dataobj[..., t], dtype=np.float64)
        for roi in ROIS:
            ts[roi][t] = float(vol[masks[roi]].mean())

    # Condition segmentation from the verified events.tsv.
    events_df = pd.read_csv(events_path, sep="\t")
    cond_mask = segment_conditions(events_df, n_vol, tr)

    result: Dict[str, pd.DataFrame] = {}
    for cond in CONDITIONS:
        sel = cond_mask[cond]
        if sel.sum() == 0:
            raise ROIExtractionError(
                f"{subject_id} has no {cond} volumes (FR-011)"
            )
        df = pd.DataFrame({"timepoint": np.arange(n_vol)[sel]})
        for roi in ROIS:
            series = ts[roi][sel]
            if np.allclose(series, series[0]):
                raise ROIExtractionError(
                    f"Zero-variance ROI {roi} during {cond} for {subject_id} (FR-014)"
                )
            df[roi] = series
        result[cond] = df

        # Per-subject/condition Parquet (raw time-series).
        parquet_path = output_dir / f"raw_timeseries_{subject_id}_{cond}.parquet"
        df.to_parquet(parquet_path, index=False)

        # Validation side-records conforming to contracts/timeseries.schema.yaml.
        for roi in ROIS:
            record = {
                "subject_id": subject_id,
                "roi": roi,
                "condition": cond,
                "data": [float(v) for v in df[roi].tolist()],
                "tr": float(tr),
            }
            side = output_dir / f"timeseries_validation_{subject_id}_{cond}_{roi}.json"
            with open(side, "w") as f:
                json.dump(record, f)

    return result


# ---------------------------------------------------------------------------
# Cohort-level pipeline
# ---------------------------------------------------------------------------
def run(
    raw_dir: Path,
    processed_dir: Path,
    metadata_path: Path,
    min_subjects: int = MIN_SUBJECTS,
) -> Dict:
    """
    Run ROI extraction for every QC-passed subject in subjects_metadata.json.

    Updates subjects_metadata.json with extraction status, writes
    qc_report.json with the retention rate, and raises
    InsufficientSubjectsError (error code 101897696) if N < min_subjects.
    """
    raw_dir = Path(raw_dir)
    processed_dir = Path(processed_dir)
    metadata_path = Path(metadata_path)
    processed_dir.mkdir(parents=True, exist_ok=True)

    if not metadata_path.exists():
        raise ROIExtractionError(f"subjects metadata not found: {metadata_path}")
    with open(metadata_path) as f:
        metadata = json.load(f)
    if not isinstance(metadata, list) or not metadata:
        raise ROIExtractionError("subjects_metadata.json is empty or malformed")

    atlas_img, atlas_labels = get_harvard_oxford_atlas()

    total = len(metadata)
    for entry in metadata:
        entry.setdefault("subject_id", "")
        if entry.get("qc_status") != "passed":
            entry["roi_extraction"] = "skipped"
            continue
        subject_id = entry["subject_id"]
        subject_dir = raw_dir / subject_id
        try:
            bold_path = find_bold_file(subject_dir)
            events_path = find_events_file(subject_dir)
            extract_subject(
                subject_id, bold_path, events_path, atlas_img, atlas_labels,
                processed_dir,
            )
            entry["roi_extraction"] = "passed"
            entry["qc_status"] = "passed"
        except ROIExtractionError as exc:
            entry["roi_extraction"] = "failed"
            entry["roi_extraction_reason"] = str(exc)
            entry["qc_status"] = "failed"

    # Persist the updated metadata (FR-011 / FR-014).
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    retained = sum(1 for e in metadata if e.get("qc_status") == "passed")
    retention_rate = retained / total if total else 0.0

    qc_report = {
        "total_subjects": total,
        "retained_subjects": retained,
        "retention_rate": retention_rate,
        "motion_threshold_mm": 0.2,
        "rois": ROIS,
        "min_subjects_required": min_subjects,
    }
    with open(processed_dir / "qc_report.json", "w") as f:
        json.dump(qc_report, f, indent=2)

    if retained < min_subjects:
        raise InsufficientSubjectsError(
            f"Only {retained} subjects retained after ROI extraction; "
            f"minimum is {min_subjects} (error code {ERROR_INSUFFICIENT_SUBJECTS})"
        )
    return qc_report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Raw DMN ROI extraction and condition segmentation (T003)."
    )
    parser.add_argument("--raw", default="data/raw/ds000030",
                        help="BIDS raw data directory")
    parser.add_argument("--processed", default="data/processed",
                        help="Output directory for processed artifacts")
    parser.add_argument("--metadata", default="data/processed/subjects_metadata.json",
                        help="Path to subjects_metadata.json from motion QC")
    args = parser.parse_args(argv)

    try:
        report = run(Path(args.raw), Path(args.processed), Path(args.metadata))
    except InsufficientSubjectsError as exc:
        print(f"ERROR {ERROR_INSUFFICIENT_SUBJECTS}: {exc}", file=sys.stderr)
        return ERROR_INSUFFICIENT_SUBJECTS
    except ROIExtractionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
