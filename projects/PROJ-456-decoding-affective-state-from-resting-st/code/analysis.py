"""Analysis module for PROJ-456: dataset-variable fit verification (T023A).

Implements verify_dataset_variable_fit(), which checks that the project's
OpenNeuro datasets contain BOTH raw EEG recordings AND affective
questionnaire data from validated instruments (PANAS / SAM), and that
questionnaire response rates meet the >=80% per-subject requirement
(FR-012). The result is written to a project‑owned location
`data/results/dataset_fit_status.json` with status 'ready' or 'skipped'.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from llmxive_toolkit import paths, get_logger

# Import the manifest generation helper to create the manifest on‑the‑fly
# if it does not already exist.
from code.utils import generate_manifest

log = get_logger(__name__)

# Citable validation literature for the accepted instruments (FR-012).
VALIDATED_INSTRUMENTS: Dict[str, Dict[str, str]] = {
    "PANAS": {
        "full_name": "Positive and Negative Affect Schedule",
        "validation_reference": (
            "Watson, D., Clark, L. A., & Tellegen, A. (1988). "
            "Development and validation of brief measures of positive and "
            "negative affect: The PANAS scales. Journal of Personality and "
            "Social Psychology, 54(6), 1063-1070."
        ),
    },
    "SAM": {
        "full_name": "Self-Assessment Manikin",
        "validation_reference": (
            "Bradley, M. M., & Lang, P. J. (1994). Measuring emotion: The "
            "Self-Assessment Manikin and the Semantic Differential. "
            "Journal of Behavior Therapy and Experimental Psychiatry, "
            "25(1), 49-59."
        ),
    },
}

MIN_RESPONSE_RATE = 0.80

EEG_EXTENSIONS = {".set", ".edf", ".bdf", ".vhdr", ".fif", ".eeg", ".cnt", ".gdf"}
QUESTIONNAIRE_KEYWORDS = (
    "panas",
    "sam",
    "questionnaire",
    "affect",
    "affective",
    "valence",
    "arousal",
    "phenotype",
)
INSTRUMENT_KEYWORDS = {"panas": "PANAS", "sam": "SAM"}

# ----------------------------------------------------------------------
# Helper functions (unchanged from the original implementation)
# ----------------------------------------------------------------------
def _iter_dataset_entries(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize manifest entries into a list of per‑dataset dicts."""
    entries: List[Dict[str, Any]] = []
    if isinstance(manifest, dict):
        datasets = manifest.get("datasets", manifest.get("entries"))
        if isinstance(datasets, dict):
            for ds_id, info in datasets.items():
                entry = dict(info) if isinstance(info, dict) else {"info": info}
                entry.setdefault("dataset_id", ds_id)
                entries.append(entry)
        elif isinstance(datasets, list):
            entries = [dict(e) for e in datasets if isinstance(e, dict)]
        else:
            if "dataset_id" in manifest or "files" in manifest:
                entries.append(dict(manifest))
    elif isinstance(manifest, list):
        entries = [dict(e) for e in manifest if isinstance(e, dict)]
    return entries


def _collect_files(entry: Dict[str, Any], raw_dir: Path) -> List[Path]:
    """Collect file paths recorded in a manifest entry plus real files on disk."""
    found: set = set()
    for key in ("files", "file_paths", "eeg_files", "paths"):
        val = entry.get(key)
        if isinstance(val, list):
            for f in val:
                if isinstance(f, str):
                    p = Path(f)
                    if not p.is_absolute():
                        p = raw_dir / p
                    found.add(p)
    ds_dir = raw_dir / str(entry.get("dataset_id", ""))
    if entry.get("dataset_id") and ds_dir.is_dir():
        for p in ds_dir.rglob("*"):
            if p.is_file():
                found.add(p)
    return sorted(found)


def _find_questionnaire_files(files: List[Path]) -> List[Path]:
    """Return tabular files whose names suggest affective questionnaire data."""
    hits = []
    for p in files:
        name = p.name.lower()
        if p.suffix.lower() in {".tsv", ".csv", ".txt"} and any(
            k in name for k in QUESTIONNAIRE_KEYWORDS
        ):
            hits.append(p)
    return hits


def _detect_instruments(files: List[Path], entry: Dict[str, Any]) -> List[str]:
    """Detect PANAS/SAM instrument mentions in file names and metadata text."""
    text_blobs: List[str] = [str(p.name) for p in files]
    for key in ("description", "name", "title", "summary", "modalities"):
        val = entry.get(key)
        if val is not None:
            text_blobs.append(str(val))
    blob = " ".join(text_blobs).lower()
    detected = []
    for keyword, instrument in INSTRUMENT_KEYWORDS.items():
        if keyword in blob:
            detected.append(instrument)
    return sorted(set(detected))


def _compute_response_rates(questionnaire_files: List[Path]) -> Dict[str, float]:
    """Compute per‑subject completion rate from real questionnaire tables."""
    rates: Dict[str, float] = {}
    for qf in questionnaire_files:
        try:
            sep = "\t" if qf.suffix.lower() == ".tsv" else None
            df = pd.read_csv(qf, sep=sep, index_col=0 if sep else None)
        except Exception as exc:  # unparseable file: skip, do not fabricate
            log.warning("Could not parse questionnaire file %s: %s", qf, exc)
            continue
        if df.empty:
            continue
        id_col = None
        for cand in ("participant_id", "subject_id", "sub", "id", "subject"):
            if cand in df.columns:
                id_col = cand
                break
        item_cols = [c for c in df.columns if c != id_col]
        if not item_cols:
            continue
        for _, row in df.iterrows():
            sub_id = str(row[id_col]) if id_col is not None else str(row.name)
            values = [row[c] for c in item_cols]
            answered = sum(
                1
                for v in values
                if pd.notna(v) and str(v).strip() not in ("", "n/a", "N/A")
            )
            rates[sub_id] = answered / len(item_cols)
    return rates

# ----------------------------------------------------------------------
# Core verification function
# ----------------------------------------------------------------------
def verify_dataset_variable_fit(
    manifest_path: Optional[str] = None,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify dataset‑variable fit (FR‑012, SC‑008).

    Checks that datasets contain both raw EEG and affective questionnaire
    data (PANAS/SAM) and that questionnaire response rates are >=80% per
    subject.

    Args:
        manifest_path: Path to ``data/raw/dataset_manifest.json``.
        output_path: Path for the JSON status file (project‑owned).

    Returns:
        The status dict that was written to ``output_path``.

    Raises:
        FileNotFoundError: If the dataset manifest does not exist and
            automatic generation fails.
    """
    # ------------------------------------------------------------------
    # Resolve paths – default to project‑owned locations.
    # ------------------------------------------------------------------
    if manifest_path is None:
        manifest_path = str(paths.data("raw", "dataset_manifest.json"))
    if output_path is None:
        # Use a project‑owned location; ``data/results`` is safe.
        output_path = str(paths.data("results", "dataset_fit_status.json"))

    manifest_file = Path(manifest_path)

    # ------------------------------------------------------------------
    # If the manifest is missing, attempt to create it using the utility
    # that performs a real OpenNeuro download.  This respects the
    # “real‑data‑only” rule – the download will fail loudly if the remote
    # source is unavailable.
    # ------------------------------------------------------------------
    if not manifest_file.is_file():
        log.info(
            "Dataset manifest not found at %s – attempting automatic generation.",
            manifest_file,
        )
        try:
            # The two OpenNeuro datasets referenced in the spec.
            dataset_ids = ["ds003501", "ds004137"]
            generate_manifest(
                dataset_ids,
                target_dir=str(paths.data("raw")),
                manifest_path=manifest_path,
            )
        except Exception as exc:
            raise FileNotFoundError(
                f"Failed to generate dataset manifest automatically: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Load the (now‑present) manifest.
    # ------------------------------------------------------------------
    with open(manifest_file, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    raw_dir = paths.data("raw")
    dataset_reports: List[Dict[str, Any]] = []
    any_ready = False

    for entry in _iter_dataset_entries(manifest):
        ds_id = str(entry.get("dataset_id", entry.get("id", "unknown")))
        files = _collect_files(entry, raw_dir)
        eeg_files = [p for p in files if p.suffix.lower() in EEG_EXTENSIONS]
        questionnaire_files = _find_questionnaire_files(files)
        instruments = _detect_instruments(files, entry)
        response_rates = _compute_response_rates(questionnaire_files)

        subjects_meeting_rate = {
            s: r for s, r in response_rates.items() if r >= MIN_RESPONSE_RATE
        }
        eeg_ok = len(eeg_files) > 0
        questionnaire_ok = (
            len(questionnaire_files) > 0
            and len(instruments) > 0
            and len(subjects_meeting_rate) > 0
        )
        dataset_ready = eeg_ok and questionnaire_ok
        any_ready = any_ready or dataset_ready

        dataset_reports.append(
            {
                "dataset_id": ds_id,
                "eeg_present": eeg_ok,
                "eeg_file_count": len(eeg_files),
                "questionnaire_present": len(questionnaire_files) > 0,
                "questionnaire_files": [str(p) for p in questionnaire_files],
                "instruments_detected": instruments,
                "n_subjects_with_questionnaire": len(response_rates),
                "n_subjects_meeting_response_rate": len(subjects_meeting_rate),
                "min_response_rate": (
                    min(response_rates.values()) if response_rates else None
                ),
                "mean_response_rate": (
                    sum(response_rates.values()) / len(response_rates)
                    if response_rates
                    else None
                ),
                "response_rate_threshold": MIN_RESPONSE_RATE,
                "dataset_status": "ready" if dataset_ready else "skipped",
                "skip_reason": None
                if dataset_ready
                else ("no_eeg_data" if not eeg_ok else "no_linked_affective_data"),
            }
        )

    # ------------------------------------------------------------------
    # Overall status
    # ------------------------------------------------------------------
    if any_ready:
        status = "ready"
        reason = None
    else:
        status = "skipped"
        reason = "no_linked_data"

    result: Dict[str, Any] = {
        "status": status,
        "reason": reason,
        "task": "T023A",
        "requirement": "FR-012",
        "min_response_rate": MIN_RESPONSE_RATE,
        "instrument_validation_literature": VALIDATED_INSTRUMENTS,
        "datasets": dataset_reports,
        "manifest_path": str(manifest_file),
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    log.info("Dataset fit status '%s' written to %s", status, out)
    print(json.dumps({"status": status, "reason": reason, "output": str(out)}))
    return result

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Entry point: run the dataset‑variable fit verification."""
    verify_dataset_variable_fit()

if __name__ == "__main__":
    main()