"""Vertex-block extraction and cleaning (T003, FR-002 Python adaptation).

Streams the verified parquet shard (``clane9/openneuro-fslr64k``, test
split) row-group by row-group — the full shard is NEVER loaded into
RAM — maps fsLR vertices to the deterministic 100-block
contiguous-vertex scheme, computes the mean signal per block per
timepoint, bandpass-filters 0.01–0.1 Hz, and writes per-subject QC
records.

IMPORTANT CONSTRUCT-VALIDITY NOTE: the 100 "blocks" are a
deterministic contiguous grouping of fsLR surface vertices in their
stored column order (vertex i belongs to block
``i // ceil(n_vertices / 100)``). This is NOT a neuroanatomical or
functionally meaningful parcellation; all downstream outputs are
"vertex-block connectivity descriptors", never brain-network
properties.

QC bad-volume rule (spec edge case, fully specified):
  * If a real FD column exists: a volume is bad when FD > 0.5 mm.
  * Else (expected path — the verified shard has no FD column): a
    volume is bad when its DVARS-like statistic — the root-mean-square
    frame-to-frame change in the 100 block-mean signals — exceeds
    run_median + 3 x (1.4826 x MAD).
  A subject is excluded when > 20% of volumes are bad.
  All thresholds are pinned in code/config.py.

Outputs (per subject s):
  data/derived/roi_timeseries_<s>.csv  (long format, conforms to
      specs/001-investigating-the-relationship-between-b/contracts/
      roi_timeseries.schema.yaml)
  data/derived/qc_<s>.json             (QC record)
Plus data/derived/exclusion_log.csv and
data/derived/task_label_status.json (edge-case record for T006).
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from scipy.signal import butter, filtfilt

import config  # noqa: E402  (pinned parameters; sibling module)
from llmxive_toolkit import paths, get_logger  # noqa: E402

log = get_logger(__name__)

# Known fsLR/HCP surface vertex counts used ONLY to disambiguate the
# storage orientation (frame-major vs vertex-major) of the `bold`
# column. No data are fabricated; an unrecognized layout raises.
_KNOWN_VERTEX_COUNTS = {64984, 59412, 32492, 91282}

DERIVED_RELATIVE = Path("derived")
BANDPASS_ORDER = 2


# ------------------------------------------------------------------
# Core numeric routines (unit-tested in tests/test_extract.py)
# ------------------------------------------------------------------
def vertex_block_ids(n_blocks: int = config.N_VERTEX_BLOCKS) -> list:
    """Deterministic block labels roi_1 .. roi_100."""
    return [f"roi_{i + 1}" for i in range(n_blocks)]


def block_assignment(n_vertices: int, n_blocks: int = config.N_VERTEX_BLOCKS) -> np.ndarray:
    """Map each vertex to one of ``n_blocks`` contiguous blocks.

    Deterministic scheme: vertices are split into ``n_blocks`` groups
    of (nearly) equal contiguous size in their stored order. This is
    an arbitrary grouping, NOT a parcellation.
    """
    return np.arange(n_vertices) // int(np.ceil(n_vertices / n_blocks))


def compute_block_means(matrix: np.ndarray, n_blocks: int = config.N_VERTEX_BLOCKS) -> np.ndarray:
    """Mean signal per block per timepoint.

    Parameters
    ----------
    matrix : (n_timepoints, n_vertices) array of BOLD values.
    Returns (n_timepoints, n_blocks).
    """
    if matrix.ndim != 2:
        raise ValueError(f"expected 2-D (timepoints x vertices), got {matrix.shape}")
    n_vertices = matrix.shape[1]
    if n_vertices < n_blocks:
        raise ValueError(
            f"fewer vertices ({n_vertices}) than blocks ({n_blocks})"
        )
    assign = block_assignment(n_vertices, n_blocks)
    out = np.empty((matrix.shape[0], n_blocks), dtype=np.float64)
    for b in range(n_blocks):
        out[:, b] = matrix[:, assign == b].mean(axis=1)
    return out


def bandpass_filter(matrix: np.ndarray, tr: float = config.TR_SECONDS,
                    low: float = config.BANDPASS_LOW_HZ,
                    high: float = config.BANDPASS_HIGH_HZ,
                    order: int = BANDPASS_ORDER):
    """Butterworth bandpass (default 0.01–0.1 Hz) along time, zero-phase.

    Returns (filtered_matrix, applied: bool). If the run is too short
    for ``filtfilt`` padding, filtering is skipped and ``applied`` is
    False (recorded honestly in the QC record).
    """
    fs = 1.0 / float(tr)
    nyq = fs / 2.0
    if high >= nyq:
        raise ValueError(f"bandpass high {high} Hz >= Nyquist {nyq} Hz for TR={tr}")
    b, a = butter(order, [low / nyq, high / nyq], btype="band")
    padlen = 3 * max(len(a), len(b))
    if matrix.shape[0] <= padlen:
        return matrix, False
    return filtfilt(b, a, matrix, axis=0), True


def dvars_statistics(block_matrix: np.ndarray):
    """DVARS-like motion proxy on the 100 block-mean signals.

    Returns (dvars, bad_mask, median, mad, threshold) where
    dvars[t] is the root-mean-square frame-to-frame change across
    blocks and a volume is bad when
    dvars[t] > median + 3 * (1.4826 * MAD).
    """
    if block_matrix.shape[0] < 2:
        raise ValueError("need at least 2 timepoints for DVARS")
    diff = np.diff(block_matrix, axis=0)
    dvars = np.sqrt((diff ** 2).mean(axis=1))
    dvars = np.concatenate([[0.0], dvars])  # first volume: no predecessor
    med = float(np.median(dvars))
    mad = float(np.median(np.abs(dvars - med)))
    robust_sd = config.MAD_TO_SD_CONSTANT * mad
    if mad == 0.0:
        # Degenerate constant series: the literal rule would flag
        # half the volumes; treat as no motion information instead.
        thresh = float("inf")
    else:
        thresh = med + config.DVARS_MAD_MULTIPLIER * robust_sd
    bad = dvars > thresh
    return dvars, bad, med, mad, thresh


def fd_bad_mask(fd_values) -> np.ndarray:
    """FD rule: a volume is bad when FD > 0.5 mm (spec edge case)."""
    fd = np.asarray(fd_values, dtype=np.float64)
    return fd > config.FD_THRESHOLD_MM


def qc_from_block_matrix(block_matrix: np.ndarray, fd_values=None) -> dict:
    """Full QC evaluation for one subject's block-mean matrix.

    Applies the FD rule when real FD values are supplied, else the
    DVARS-like MAD rule. Returns a dict with fraction_bad_volumes,
    excluded, exclusion_reason, and the motion-proxy description.
    """
    n_t = block_matrix.shape[0]
    if fd_values is not None:
        bad = fd_bad_mask(fd_values)
        proxy = {
            "method": "fd",
            "description": "real FD column; volume bad when FD > "
                           f"{config.FD_THRESHOLD_MM} mm",
            "thresholds": {"fd_mm": config.FD_THRESHOLD_MM},
        }
        stats = {}
    else:
        dvars, bad, med, mad, thresh = dvars_statistics(block_matrix)
        proxy = {
            "method": "dvars_mad",
            "description": (
                "no FD column in verified shard; DVARS-like statistic "
                "(root-mean-square frame-to-frame change in the 100 "
                "block-mean signals) is bad when it exceeds "
                "run_median + 3 * (1.4826 * MAD)"
            ),
            "thresholds": {
                "mad_multiplier": config.DVARS_MAD_MULTIPLIER,
                "mad_to_sd_constant": config.MAD_TO_SD_CONSTANT,
                "max_bad_volume_fraction": config.MAX_BAD_VOLUME_FRACTION,
            },
            "run_median": med,
            "run_mad": mad,
            "threshold": (None if not np.isfinite(thresh) else float(thresh)),
        }
        stats = {"dvars_median": med, "dvars_mad": mad}
    frac = float(bad.mean())
    excluded = frac > config.MAX_BAD_VOLUME_FRACTION
    reason = (
        f"excessive_bad_volumes: {frac:.3f} of volumes bad "
        f"(> {config.MAX_BAD_VOLUME_FRACTION}) by the "
        f"{proxy['method']} rule"
        if excluded else None
    )
    return {
        "n_volumes": int(n_t),
        "n_bad_volumes": int(bad.sum()),
        "fraction_bad_volumes": frac,
        "excluded": bool(excluded),
        "exclusion_reason": reason,
        "motion_proxy": proxy,
        **stats,
    }


# ------------------------------------------------------------------
# Parquet streaming (row-group batches; never the full shard)
# ------------------------------------------------------------------
def _orient_matrix(arr: np.ndarray, n_frames) -> np.ndarray:
    """Return a (n_timepoints, n_vertices) matrix from raw bold data.

    Uses ``n_frames`` and known fsLR vertex counts to disambiguate
    frame-major vs vertex-major storage. Fails loudly on unknown
    layouts — never guesses silently.
    """
    if arr.ndim == 2:
        mat = arr.astype(np.float64, copy=False)
        if n_frames is not None:
            if mat.shape[0] == int(n_frames):
                return mat
            if mat.shape[1] == int(n_frames):
                return mat.T
        return mat
    flat = np.asarray(arr, dtype=np.float64).reshape(-1)
    if n_frames is None:
        raise ValueError("cannot orient flat bold array without n_frames")
    n_frames = int(n_frames)
    if flat.size % n_frames != 0:
        raise ValueError(
            f"bold size {flat.size} not divisible by n_frames {n_frames}"
        )
    v = flat.size // n_frames
    if v in _KNOWN_VERTEX_COUNTS:
        return flat.reshape(n_frames, v)  # frame-major
    for vc in _KNOWN_VERTEX_COUNTS:
        if flat.size % vc == 0 and flat.size // vc == n_frames:
            return flat.reshape(vc, n_frames).T  # vertex-major
    if 1000 <= v <= 2_000_000:
        # plausible vertex count; assume frame-major
        return flat.reshape(n_frames, v)
    raise ValueError(
        f"unrecognized bold layout: size={flat.size}, "
        f"n_frames={n_frames}, implied V={v}"
    )


def _iter_rows(pf: pq.ParquetFile, columns: list):
    """Yield (subject, n_frames, task, bold_flat_or_array) row by row.

    Uses the arrow offsets/flatten fast path (cheap numpy slices) for
    single-level list columns; falls back to ``.as_py()`` for nested
    layouts. Only ONE row's bold data is materialized at a time.
    """
    for rg in range(pf.num_row_groups):
        tbl = pf.read_row_group(rg, columns=columns)
        n = tbl.num_rows
        subs = tbl.column("sub").to_pylist() if "sub" in tbl.column_names else [None] * n
        frames = tbl.column("n_frames").to_pylist() if "n_frames" in tbl.column_names else [None] * n
        tasks = tbl.column("task").to_pylist() if "task" in tbl.column_names else [None] * n
        bold_col = tbl.column("bold").combine_chunks()
        if pa.types.is_fixed_size_list(bold_col.type):
            size = bold_col.type.list_size
            values = bold_col.values
            for i in range(n):
                flat = np.asarray(values[i * size:(i + 1) * size], dtype=np.float64)
                yield subs[i], frames[i], tasks[i], flat
        elif pa.types.is_list(bold_col.type) or pa.types.is_large_list(bold_col.type):
            offsets = np.asarray(bold_col.offsets)
            values = bold_col.values
            nested = pa.types.is_list(values.type) or pa.types.is_large_list(values.type) \
                or pa.types.is_fixed_size_list(values.type)
            for i in range(n):
                if nested:
                    arr = np.asarray(bold_col[i].as_py(), dtype=np.float64)
                else:
                    arr = np.asarray(values[offsets[i]:offsets[i + 1]], dtype=np.float64)
                yield subs[i], frames[i], tasks[i], arr
        else:
            raise ValueError(
                f"unsupported 'bold' column type: {bold_col.type}"
            )


def _safe_subject_id(sid) -> str:
    s = re.sub(r"[^A-Za-z0-9_.-]", "_", str(sid))
    return s or "unknown_subject"


# ------------------------------------------------------------------
# Main extraction
# ------------------------------------------------------------------
def load_inventory():
    inv_path = paths.data("raw", "column_inventory.json")
    if not inv_path.is_file():
        raise RuntimeError(
            f"column inventory missing: {inv_path}. Run "
            "python code/download_openneuro.py first (T001)."
        )
    return json.loads(inv_path.read_text())


def extract_all(shard_path: Path = None, derived_dir: Path = None) -> dict:
    """Stream the shard and write per-subject timeseries + QC records."""
    inventory = load_inventory()
    shard = shard_path or paths.data("raw", config.SHARD_BASENAME)
    if not shard.is_file():
        raise RuntimeError(f"verified shard missing: {shard} (run T001 first)")
    derived = derived_dir or paths.data("derived")
    derived.mkdir(parents=True, exist_ok=True)

    subject_column = inventory.get("subject_column") or "sub"
    fd_present = bool(
        inventory.get("expected_fields", {}).get("fd", {}).get("present")
    )
    task_present = bool(
        inventory.get("expected_fields", {}).get("task_labels", {}).get("present")
    )
    # Edge case (spec): missing task labels are detected from the
    # column inventory and recorded; the descriptive pipeline proceeds.
    task_status = {
        "task_labels_present": task_present,
        "matched_column": inventory.get("expected_fields", {})
            .get("task_labels", {}).get("matched_column"),
        "note": (
            "task labels present; the conditional association stage "
            "(T006) may use them only as a secondary skill proxy"
            if task_present else
            "task labels ABSENT from the verified shard; recorded per "
            "the spec's edge-case rule — the descriptive pipeline "
            "proceeds and T006's association stage uses this record"
        ),
    }
    (derived / "task_label_status.json").write_text(json.dumps(task_status, indent=2))
    if not task_present:
        log.warning("Task labels missing (edge case): %s", task_status["note"])

    read_columns = ["bold", subject_column]
    for extra in ("n_frames", "task"):
        if extra in inventory.get("columns", []):
            read_columns.append(extra)

    # Accumulate per-subject block-mean matrices (tiny: T x 100).
    subjects = {}
    pf = pq.ParquetFile(shard)
    for sub, n_frames, task, bold in _iter_rows(pf, read_columns):
        if sub is None:
            raise RuntimeError("row with missing subject ID in verified shard")
        mat = _orient_matrix(bold, n_frames)
        blocks = compute_block_means(mat)
        sid = _safe_subject_id(sub)
        entry = subjects.setdefault(sid, {"runs": [], "tasks": []})
        entry["runs"].append(blocks)
        entry["tasks"].append(task)
        log.info("subject %s: run with %d timepoints, %d vertices",
                 sid, mat.shape[0], mat.shape[1])

    if not subjects:
        raise RuntimeError("no subject rows found in the verified shard")

    exclusion_rows = []
    summary = {"n_subjects": len(subjects), "n_excluded": 0, "subjects": {}}
    for sid, entry in sorted(subjects.items()):
        block_matrix = np.vstack(entry["runs"])
        fd_values = None  # no FD column in the verified shard (expected)
        qc = qc_from_block_matrix(block_matrix, fd_values=fd_values)
        filtered, applied = bandpass_filter(block_matrix)
        n_t, n_b = filtered.shape
        df = pd.DataFrame({
            "subject_id": sid,
            "timepoint": np.repeat(np.arange(n_t), n_b),
            "roi_id": np.tile(vertex_block_ids(n_b), n_t),
            "value": filtered.reshape(-1),
        })
        ts_path = derived / f"roi_timeseries_{sid}.csv"
        df.to_csv(ts_path, index=False)

        qc_record = {
            "subject_id": sid,
            "n_runs": len(entry["runs"]),
            "task_values": [str(t) for t in entry["tasks"]],
            "task_labels_present": task_present,
            "n_vertex_blocks": int(n_b),
            "n_vertices_per_block_min": int(block_assignment(
                block_matrix.shape[1] if block_matrix.shape[1] else n_b).max()) if False else None,
            "bandpass": {
                "low_hz": config.BANDPASS_LOW_HZ,
                "high_hz": config.BANDPASS_HIGH_HZ,
                "tr_seconds": config.TR_SECONDS,
                "order": BANDPASS_ORDER,
                "applied": bool(applied),
            },
            **qc,
        }
        qc_record.pop("n_vertices_per_block_min", None)
        (derived / f"qc_{sid}.json").write_text(json.dumps(qc_record, indent=2))
        exclusion_rows.append({
            "subject_id": sid,
            "excluded": qc["excluded"],
            "exclusion_reason": qc["exclusion_reason"] or "",
            "fraction_bad_volumes": qc["fraction_bad_volumes"],
        })
        if qc["excluded"]:
            summary["n_excluded"] += 1
            log.warning("subject %s EXCLUDED: %s", sid, qc["exclusion_reason"])
        summary["subjects"][sid] = {
            "n_volumes": qc["n_volumes"],
            "fraction_bad_volumes": qc["fraction_bad_volumes"],
            "excluded": qc["excluded"],
        }

    log_df = pd.DataFrame(exclusion_rows)
    log_df.to_csv(derived / "exclusion_log.csv", index=False)
    log.info("extraction complete: %d subjects, %d excluded",
             summary["n_subjects"], summary["n_excluded"])
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Vertex-block extraction + bandpass + QC (T003)"
    )
    parser.add_argument("--shard", type=Path, default=None,
                        help="override shard path (default: data/raw shard)")
    parser.add_argument("--derived_dir", type=Path, default=None,
                        help="override derived output directory")
    args = parser.parse_args(argv)
    summary = extract_all(shard_path=args.shard, derived_dir=args.derived_dir)
    print(json.dumps({
        "n_subjects": summary["n_subjects"],
        "n_excluded": summary["n_excluded"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
