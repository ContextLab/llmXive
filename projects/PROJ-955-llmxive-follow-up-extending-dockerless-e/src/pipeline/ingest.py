"""
src/pipeline/ingest.py
-----------------------

Data ingestion module for the static‑dynamic gap analysis pipeline.

This script performs the following steps:

1. **Download the raw datasets** (SWE‑Gym and Multi‑SWE‑RL) from the URLs
   provided via the CLI.  The files are saved under ``data/`` as
   ``raw_swe_gym.parquet`` and ``raw_multi_swe_rl.jsonl``.
2. **Verify SHA‑256 checksums** of the downloaded files against the
   expected values that are stored in ``plan.md``.
3. **Extract a unified patch table** (``patches.csv``) containing the
   columns ``patch_id,language,source_code,label``.
4. **Write execution logs** for every patch under ``data/execution_logs/``.
5. **Memory‑aware sampling fallback** – if the combined size of the raw
   dataset files exceeds 6 GB, the ingestion switches to a stratified
   10 % sample (per language‑and‑origin) using a fixed seed (42).

The module can be executed directly:
    python -m src.pipeline.ingest
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import requests
from tqdm import tqdm
import yaml

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------

def _sha256_of_file(path: Path) -> str:
    """Return the hex SHA‑256 digest of ``path``."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _extract_expected_checksums(plan_path: Path) -> Dict[str, str]:
    """
    Parse ``plan.md`` and return a mapping from filename to expected
    SHA‑256 checksum.
    """
    checksums: Dict[str, str] = {}
    content = plan_path.read_text(encoding="utf-8")
    
    if "checksums:" in content:
        try:
            yaml_part = content.split("checksums:")[1]
            yaml_text = "checksums:\n" + yaml_part
            data = yaml.safe_load(yaml_text)
            if isinstance(data, dict) and "checksums" in data:
                raw = data["checksums"]
                if isinstance(raw, dict):
                    checksums = {k: v.strip().lower() for k, v in raw.items()}
        except Exception as e:
            log.warning(f"Failed to parse YAML checksums block: {e}")

    if not checksums:
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith("|") and "SHA256" in line.upper():
                for row in lines[i + 1 :]:
                    if not row.strip().startswith("|"):
                        break
                    parts = [p.strip() for p in row.strip("|").split("|")]
                    if len(parts) >= 3:
                        filename = os.path.basename(parts[1])
                        checksum = parts[2].lower()
                        checksums[filename] = checksum
                break

    if not checksums:
        raise RuntimeError("Unable to locate expected SHA‑256 checksums in plan.md.")
    return checksums

def _download_file(url: str, dest: Path) -> None:
    """Download a remote file using ``requests`` with streaming."""
    log.info(f"Downloading {url} → {dest}")
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    with dest.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    log.info(f"Finished download: {dest}")

def _select_column(df: pd.DataFrame, candidates: List[str]) -> str | None:
    """Return the first column name from ``candidates`` that exists in ``df``."""
    for col in candidates:
        if col in df.columns:
            return col
    return None

# ----------------------------------------------------------------------
# Core ingestion logic
# ----------------------------------------------------------------------

def _norm_label(val):
    """Normalize label values to ``pass``/``fail``."""
    if isinstance(val, bool):
        return "pass" if val else "fail"
    if isinstance(val, str):
        val_low = val.lower()
        if any(x in val_low for x in {"pass", "true", "success", "passed"}):
            return "pass"
        if any(x in val_low for x in {"fail", "false", "error", "failed"}):
            return "fail"
    return "pass" if bool(val) else "fail"

def _process_swe_gym(parquet_path: Path) -> Tuple[pd.DataFrame, List[Tuple[str, str]]]:
    """
    Load the SWE‑Gym parquet file and extract the required columns.
    Expanded column candidates to handle diverse SWE-bench/Gym formats.
    """
    log.info(f"Reading SWE‑Gym parquet: {parquet_path}")
    df = pd.read_parquet(parquet_path, engine="fastparquet")

    # Expanded candidates for robustness
    pid_col = _select_column(df, ["instance_id", "patch_id", "id", "patchid"])
    lang_col = _select_column(df, ["language", "lang", "programming_language"])
    src_col = _select_column(df, ["patch", "source_code", "code", "patched_code", "original_code"])
    label_col = _select_column(df, ["test_results", "exec_result", "test_result", "result", "label"])

    if not pid_col or not src_col or not label_col:
        log.error(f"Columns found: {list(df.columns)}")
        missing = []
        if not pid_col: missing.append("patch_id")
        if not src_col: missing.append("source_code")
        if not label_col: missing.append("label")
        raise RuntimeError(f"SWE‑Gym parquet missing critical columns: {missing}")

    # Normalise columns
    patches = df.rename(columns={pid_col: "patch_id",
                                  src_col: "source_code",
                                  label_col: "label"}).copy()
    
    # Handle language (default to python if not found)
    if lang_col:
        patches = patches.rename(columns={lang_col: "language"})
    else:
        patches["language"] = "python"

    patches = patches[["patch_id", "language", "source_code", "label"]]
    patches["label"] = patches["label"].apply(_norm_label)

    # Extract logs
    logs = []
    log_col = _select_column(df, ["exec_log", "test_log", "log", "test_results"])
    if log_col:
        for pid, log_txt in zip(df[pid_col], df[log_col]):
            logs.append((pid, str(log_txt) if log_txt is not None else "MISSING_LOG"))
    else:
        for pid in df[pid_col]:
            logs.append((pid, "MISSING_LOG"))

    return patches, logs

def _process_multi_swe_rl(jsonl_path: Path) -> Tuple[pd.DataFrame, List[Tuple[str, str]]]:
    """Load the Multi‑SWE‑RL JSONL file and extract the required columns."""
    log.info(f"Reading Multi‑SWE‑RL JSONL: {jsonl_path}")
    records = []
    logs = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in tqdm(f, desc="Parsing JSONL", unit="lines"):
            if not line.strip(): continue
            obj = json.loads(line)
            pid = obj.get("patch_id")
            if pid is None: continue
            records.append({
                "patch_id": pid,
                "language": obj.get("language", "unknown"),
                "source_code": obj.get("source_code", ""),
                "label": _norm_label(obj.get("test_result", "fail")),
            })
            logs.append((pid, str(obj.get("test_log", "MISSING_LOG"))))
    
    patches = pd.DataFrame.from_records(records)
    return patches, logs

def ingest(
    swe_gym_url: str,
    multi_swe_rl_url: str,
    expected_checksums: Dict[str, str] | None = None,
) -> None:
    """Main entry point for the ingestion step."""
    raw_swe_gym_path = paths.data("raw_swe_gym.parquet")
    raw_multi_swe_rl_path = paths.data("raw_multi_swe_rl.jsonl")
    patches_csv_path = paths.data("patches.csv")
    patches_sample_path = paths.data("patches_sample.csv")
    logs_dir = paths.data("execution_logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    if not raw_swe_gym_path.is_file():
        _download_file(swe_gym_url, raw_swe_gym_path)
    if not raw_multi_swe_rl_path.is_file():
        _download_file(multi_swe_rl_url, raw_multi_swe_rl_path)

    if expected_checksums:
        for fp, expected in expected_checksums.items():
            actual = _sha256_of_file(paths.data(fp))
            if actual != expected.lower():
                raise RuntimeError(f"Checksum mismatch for {fp}: expected {expected}, got {actual}")

    total_raw_size = raw_swe_gym_path.stat().st_size + raw_multi_swe_rl_path.stat().st_size
    use_sampling = total_raw_size > 6 * 1024**3
    mode = "sampled" if use_sampling else "full"

    swe_patches, swe_logs = _process_swe_gym(raw_swe_gym_path)
    multi_patches, multi_logs = _process_multi_swe_rl(raw_multi_swe_rl_path)

    swe_patches = swe_patches.assign(origin="swe_gym")
    multi_patches = multi_patches.assign(origin="multi_swe_rl")
    all_patches = pd.concat([swe_patches, multi_patches], ignore_index=True)
    all_logs = {pid: txt for pid, txt in swe_logs + multi_logs}

    if use_sampling:
        sampled_df = (
            all_patches.groupby(["origin", "language"], group_keys=False)
            .apply(lambda grp: grp.sample(frac=0.1, random_state=42))
            .reset_index(drop=True)
        )
        sampled_df.drop(columns=["origin"]).to_csv(patches_sample_path, index=False)
        for pid in sampled_df["patch_id"]:
            (logs_dir / f"{pid}.log").write_text(all_logs.get(pid, "MISSING_LOG"), encoding="utf-8")
    else:
        all_patches.drop(columns=["origin"]).to_csv(patches_csv_path, index=False)
        for pid, log_text in tqdm(all_logs.items(), desc="Writing logs"):
            (logs_dir / f"{pid}.log").write_text(log_text, encoding="utf-8")

    mode_report = {"mode": mode}
    if use_sampling: mode_report.update({"sample_fraction": 0.1, "seed": 42})
    paths.reports("ingestion_mode.yaml").write_text(yaml.safe_dump(mode_report))

    label_counts = all_patches["label"].value_counts()
    total = len(all_patches)
    log.info(f"Ingestion complete. Total: {total}. Distribution: {label_counts.to_dict()}")

if __name__ == "__main__":
    plan_path = Path(__file__).resolve().parents[2] / "plan.md"
    if not plan_path.is_file():
        raise RuntimeError(f"Cannot locate plan.md: {plan_path}")

    swe_gym_url, multi_swe_rl_url = "", ""
    in_table = False
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and "Verified URL" in stripped:
            in_table = True; continue
        if in_table and stripped.startswith("|"):
            parts = [p.strip() for p in stripped.strip("|").split("|")]
            if len(parts) >= 2:
                if "swe‑gym" in parts[0].lower(): swe_gym_url = parts[1]
                elif "multi‑swe‑rl" in parts[0].lower(): multi_swe_rl_url = parts[1]
        else: in_table = False

    if not swe_gym_url or not multi_swe_rl_url:
        raise RuntimeError("Failed to extract URLs from plan.md")

    try: checksums = _extract_expected_checksums(plan_path)
    except RuntimeError as e:
        log.warning(str(e)); checksums = {}

    ingest(swe_gym_url, multi_swe_rl_url, expected_checksums=checksums)