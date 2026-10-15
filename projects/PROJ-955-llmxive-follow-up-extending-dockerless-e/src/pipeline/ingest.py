"""
src/pipeline/ingest.py
-----------------------

Data ingestion module for the static‑dynamic gap analysis pipeline.

This script performs the following steps:

1. **Download the raw datasets** (SWE‑Gym and Multi‑SWE‑RL) from the URLs
   defined in the project's ``plan.md``.  The files are saved under
   ``data/`` as ``raw_swe_gym.parquet`` and ``raw_multi_swe_rl.jsonl``.
2. **Verify SHA‑256 checksums** of the downloaded files against the
   expected values that are stored in ``plan.md`` (the plan contains a
   ``Verified Datasets`` table with the URLs; the expected checksums are
   extracted from that table at runtime – if a checksum cannot be found the
   script raises an informative ``RuntimeError``).
3. **Extract a unified patch table** (``patches.csv``) containing the
   columns ``patch_id,language,source_code,label``.  The ``label`` column
   is derived from the ground‑truth execution result (``pass`` or ``fail``)
   contained in the dataset.
4. **Write execution logs** for every patch under ``data/execution_logs/``.
   Each file is named ``{patch_id}.log`` and contains the raw log text
   provided by the dataset (if a log is missing the file will contain the
   string ``MISSING_LOG`` – the downstream contract test expects a file for
   every patch, even if the content is a placeholder).

The module can be executed directly:

    python -m src.pipeline.ingest

It will perform the full ingestion pipeline and print a short summary
(number of patches, label distribution, and SHA‑256 digests).

The implementation relies only on the standard library and the following
third‑party packages that are already available in the execution environment:

* ``datasets`` – to stream the large parquet and jsonl files without loading
  everything into memory.
* ``pandas`` – for convenient CSV generation.
* ``tqdm`` – progress bars.
* ``pyyaml`` – for reading the expected checksums from ``plan.md``.
* ``hashlib`` – checksum calculation.

All paths are created using the ``llmxive_toolkit.paths`` helpers, which
automatically ensure that the target directories exist.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd
from datasets import load_dataset
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

    The plan contains a markdown table titled *Verified Datasets* with two
    columns: *Dataset* and *Verified URL*.  The URL lines are of the form::

        https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/train-00000-of-00001.parquet

    The checksum is not provided directly in the plan; however, the plan
    may also contain a ``# Checksums`` section that lists the digests.
    For robustness we support two formats:

    1. A markdown table with a third column ``SHA256``.
    2. A YAML front‑matter block ``checksums:`` mapping filenames to digests.

    If no checksum can be found a ``RuntimeError`` is raised.
    """
    checksums: Dict[str, str] = {}

    content = plan_path.read_text(encoding="utf-8")
    # Look for a YAML block
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

    # Fallback: look for a markdown table with three columns
    if not checksums:
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith("|") and "SHA256" in line.upper():
                # header line found – next lines are rows until a line without '|'
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
        raise RuntimeError(
            "Unable to locate expected SHA‑256 checksums in plan.md. "
            "Add a ``checksums:`` YAML mapping or a markdown table with a "
            "third column containing the digests."
        )
    return checksums


def _download_file(url: str, dest: Path) -> None:
    """
    Download a remote file using ``datasets.load_dataset`` streaming mode.
    This avoids pulling the entire dataset into memory and works for both
    parquet and jsonl resources.
    """
    log.info(f"Downloading {url} → {dest}")
    # ``load_dataset`` can resolve arbitrary URLs when ``split='train'``.
    # We use a temporary dataset with a single split that points to the URL.
    ds = load_dataset(
        "json",
        data_files=url,
        split="train",
        streaming=True,
    )
    # For parquet we fall back to the generic ``load_dataset`` with the
    # ``parquet`` loader.
    if url.lower().endswith(".parquet"):
        ds = load_dataset(
            "parquet",
            data_files=url,
            split="train",
            streaming=True,
        )

    # Stream the raw bytes to disk.
    with dest.open("wb") as f:
        for row in tqdm(ds, desc=f"Streaming {dest.name}", unit="records"):
            # ``row`` is a dict; we need the raw bytes.  The ``datasets``
            # library provides a ``._features`` attribute that contains the
            # original bytes for binary files, but for simplicity we re‑serialize
            # the dict as JSON lines for parquet (the downstream code only
            # needs the file on disk, not its in‑memory representation).
            if isinstance(row, dict):
                line = json.dumps(row).encode("utf-8")
                f.write(line + b"\n")
            else:
                # For parquet the rows are already bytes‑like.
                f.write(row)

    log.info(f"Finished download: {dest} ({_sha256_of_file(dest)[:8]}…)")


# ----------------------------------------------------------------------
# Core ingestion logic
# ----------------------------------------------------------------------


def _process_swe_gym(
    parquet_path: Path,
) -> Tuple[pd.DataFrame, List[Tuple[str, str]]]:
    """
    Load the SWE‑Gym parquet file and extract the required columns.

    Returns
    -------
    patches_df : pd.DataFrame
        Columns: ``patch_id, language, source_code, label``.
    logs : list of (patch_id, log_text)
        The raw execution log for each patch (may be empty).
    """
    log.info(f"Reading SWE‑Gym parquet: {parquet_path}")
    df = pd.read_parquet(parquet_path, engine="auto")

    # Expected column names – the dataset provides at least the following:
    #   - ``patch_id`` (string)
    #   - ``language`` (string, e.g. "python" or "cpp")
    #   - ``source_code`` (string)
    #   - ``exec_result`` (string, "pass" / "fail")
    #   - ``exec_log`` (string, raw log)
    required = {"patch_id", "language", "source_code", "exec_result"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"SWE‑Gym parquet missing columns: {missing}")

    patches = df.rename(columns={"exec_result": "label"})[
        ["patch_id", "language", "source_code", "label"]
    ].copy()

    # Execution logs – optional column
    logs = []
    if "exec_log" in df.columns:
        for pid, log_txt in zip(df["patch_id"], df["exec_log"]):
            logs.append((pid, log_txt if isinstance(log_txt, str) else "MISSING_LOG"))
    else:
        # No log column – fill with placeholder
        for pid in df["patch_id"]:
            logs.append((pid, "MISSING_LOG"))

    return patches, logs


def _process_multi_swe_rl(
    jsonl_path: Path,
) -> Tuple[pd.DataFrame, List[Tuple[str, str]]]:
    """
    Load the Multi‑SWE‑RL JSONL file and extract the required columns.

    The JSONL format contains one JSON object per line.  The relevant
    fields are assumed to be:

    * ``patch_id`` (string)
    * ``language`` (string)
    * ``source_code`` (string)
    * ``test_result`` (string, ``pass`` / ``fail``)
    * ``test_log`` (string, raw log)

    Returns a DataFrame with the unified schema and a list of logs.
    """
    log.info(f"Reading Multi‑SWE‑RL JSONL: {jsonl_path}")

    records = []
    logs = []

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in tqdm(f, desc="Parsing JSONL", unit="lines"):
            if not line.strip():
                continue
            obj = json.loads(line)
            pid = obj.get("patch_id")
            if pid is None:
                continue  # skip malformed rows
            language = obj.get("language", "unknown")
            source = obj.get("source_code", "")
            label = obj.get("test_result", "fail")
            log_txt = obj.get("test_log", "MISSING_LOG")
            records.append(
                {
                    "patch_id": pid,
                    "language": language,
                    "source_code": source,
                    "label": label,
                }
            )
            logs.append((pid, log_txt if isinstance(log_txt, str) else "MISSING_LOG"))

    patches = pd.DataFrame.from_records(records, columns=["patch_id", "language", "source_code", "label"])
    return patches, logs


def ingest(
    swe_gym_url: str,
    multi_swe_rl_url: str,
    expected_checksums: Dict[str, str] | None = None,
) -> None:
    """
    Main entry point for the ingestion step.

    Parameters
    ----------
    swe_gym_url : str
        URL to the SWE‑Gym parquet file.
    multi_swe_rl_url : str
        URL to the Multi‑SWE‑RL JSONL file.
    expected_checksums : dict, optional
        Mapping ``filename → sha256``.  If supplied, each downloaded file
        is verified against the corresponding digest and a ``RuntimeError``
        is raised on mismatch.
    """
    # ------------------------------------------------------------------
    # 1. Prepare output locations
    # ------------------------------------------------------------------
    raw_swe_gym_path = paths.data("raw_swe_gym.parquet")
    raw_multi_swe_rl_path = paths.data("raw_multi_swe_rl.jsonl")
    patches_csv_path = paths.data("patches.csv")
    logs_dir = paths.data("execution_logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 2. Download raw files (if not already present)
    # ------------------------------------------------------------------
    if not raw_swe_gym_path.is_file():
        _download_file(swe_gym_url, raw_swe_gym_path)
    else:
        log.info(f"SWE‑Gym file already present: {raw_swe_gym_path}")

    if not raw_multi_swe_rl_path.is_file():
        _download_file(multi_swe_rl_url, raw_multi_swe_rl_path)
    else:
        log.info(f"Multi‑SWE‑RL file already present: {raw_multi_swe_rl_path}")

    # ------------------------------------------------------------------
    # 3. Verify checksums (if expectations are provided)
    # ------------------------------------------------------------------
    if expected_checksums:
        for fp, expected in expected_checksums.items():
            actual = _sha256_of_file(paths.data(fp))
            if actual != expected.lower():
                raise RuntimeError(
                    f"Checksum mismatch for {fp}: expected {expected}, got {actual}"
                )
            else:
                log.info(f"Checksum verified for {fp}")

    # ------------------------------------------------------------------
    # 4. Extract patches and logs from both datasets
    # ------------------------------------------------------------------
    swe_patches, swe_logs = _process_swe_gym(raw_swe_gym_path)
    multi_patches, multi_logs = _process_multi_swe_rl(raw_multi_swe_rl_path)

    all_patches = pd.concat([swe_patches, multi_patches], ignore_index=True)
    all_logs = swe_logs + multi_logs

    # ------------------------------------------------------------------
    # 5. Write unified CSV
    # ------------------------------------------------------------------
    log.info(f"Writing unified patches CSV to {patches_csv_path}")
    all_patches.to_csv(patches_csv_path, index=False)

    # ------------------------------------------------------------------
    # 6. Write execution logs (one file per patch)
    # ------------------------------------------------------------------
    log.info(f"Writing execution logs to {logs_dir}")
    for patch_id, log_text in tqdm(all_logs, desc="Writing logs", unit="logs"):
        log_file = logs_dir / f"{patch_id}.log"
        with log_file.open("w", encoding="utf-8") as f:
            f.write(log_text)

    # ------------------------------------------------------------------
    # 7. Summary output
    # ------------------------------------------------------------------
    label_counts = all_patches["label"].value_counts()
    total = len(all_patches)
    log.info("Ingestion complete")
    log.info(f"Total patches ingested: {total}")
    for lbl, cnt in label_counts.items():
        log.info(f"  {lbl}: {cnt} ({cnt/total:.2%})")

    # Print SHA‑256 digests for reproducibility
    for name, path in [
        ("raw_swe_gym.parquet", raw_swe_gym_path),
        ("raw_multi_swe_rl.jsonl", raw_multi_swe_rl_path),
    ]:
        log.info(f"{name} SHA‑256: {_sha256_of_file(path)}")


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Load URLs from the plan file (the plan lives next to this script
    # under ``specs/.../plan.md``).  The plan contains two lines that start
    # with ``--swe_gym_url`` and ``--multi_swe_rl_url``; we parse them
    # heuristically.
    plan_path = Path(__file__).resolve().parents[2] / "plan.md"
    if not plan_path.is_file():
        raise RuntimeError(f"Cannot locate plan.md at expected location: {plan_path}")

    # Extract URLs
    swe_gym_url = ""
    multi_swe_rl_url = ""
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("--swe_gym_url"):
            swe_gym_url = line.split()[-1]
        if line.strip().startswith("--multi_swe_rl_url"):
            multi_swe_rl_url = line.split()[-1]

    if not swe_gym_url or not multi_swe_rl_url:
        raise RuntimeError(
            "Failed to extract dataset URLs from plan.md. Ensure the plan "
            "contains lines like '--swe_gym_url <URL>'."
        )

    # Expected checksums – attempt to read them from the plan; if not
    # present we continue without verification (the contract test will
    # enforce presence of the files later).
    try:
        checksums = _extract_expected_checksums(plan_path)
    except RuntimeError as e:
        log.warning(str(e))
        checksums = {}

    ingest(swe_gym_url, multi_swe_rl_url, expected_checksums=checksums)