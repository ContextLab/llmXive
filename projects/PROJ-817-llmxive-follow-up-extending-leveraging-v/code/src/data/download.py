"""Download the real InstructPix2Pix prompt source data (T001).

Streams the full ``timbrooks/instructpix2pix`` train split via
``datasets.load_dataset(..., streaming=True)`` (falling back to the
canonical HF parquet files at
https://huggingface.co/datasets/timbrooks/instructpix2pix), iterating in
chunks so the stream is scanned without loading it into RAM, and writes
the first N_PROMPTS real ``(image, edit_prompt)`` prompt texts with row
SHA-256 checksums to ``data/raw/prompts_sample.parquet``.

The loader fails loudly on any fetch error — there is NO synthetic/mock
fallback, ever.

Run:  python -m code.src.data.download
"""

from __future__ import annotations

import hashlib
import json
import sys

import pandas as pd

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

DATASET_ID = "timbrooks/instructpix2pix"
SPLIT = "train"
N_PROMPTS = 2000
CHUNK_SIZE = 500
PARQUET_URLS = [
    "https://huggingface.co/datasets/timbrooks/instructpix2pix/resolve/main/data/train-00000-of-00002-b9a5e2f7f2831e41.parquet",
    "https://huggingface.co/datasets/timbrooks/instructpix2pix/resolve/main/data/train-00001-of-00002-8f6b8f4b3a2f5b2f.parquet",
]

OUTPUT_PATH = paths.data("raw", "prompts_sample.parquet")
PROVENANCE_PATH = paths.data("raw", "prompts_sample_provenance.json")


def _row_checksum(row: dict) -> str:
    """Stable SHA-256 over the fields that identify a real source row."""
    payload = json.dumps(
        {
            "edit_prompt": row.get("edit_prompt"),
            "original_prompt": row.get("original_prompt"),
            "edit_type": row.get("edit_type"),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _iter_stream_hf():
    """Primary path: stream the full HF dataset without loading it in RAM."""
    from datasets import load_dataset

    log.info(
        "Streaming %s split=%s (full stream, chunked iteration)",
        DATASET_ID,
        SPLIT,
    )
    ds = load_dataset(DATASET_ID, split=SPLIT, streaming=True)
    for row in ds:
        yield row


def _iter_stream_parquet():
    """Fallback path: read the canonical HF parquet files chunk by chunk."""
    from datasets import load_dataset

    for url in PARQUET_URLS:
        log.info("Streaming canonical parquet shard: %s", url)
        ds = load_dataset(
            "parquet", data_files=url, split="train", streaming=True
        )
        for row in ds:
            yield row


def collect_prompt_sample(
    n_prompts: int = N_PROMPTS, chunk_size: int = CHUNK_SIZE
) -> pd.DataFrame:
    """Scan the real stream in chunks; keep the first n_prompts valid rows.

    Raises on any fetch error — no synthetic fallback.
    """
    try:
        row_iter = _iter_stream_hf()
        source = (
            f"datasets.load_dataset('{DATASET_ID}', split='{SPLIT}', streaming=True)"
        )
    except Exception as exc:  # noqa: BLE001 - fail loudly, then try fallback
        log.warning(
            "HF streaming loader failed (%s); trying canonical parquet shards",
            exc,
        )
        row_iter = _iter_stream_parquet()
        source = "canonical HF parquet shards (" + "; ".join(PARQUET_URLS) + ")"

    records: list[dict] = []
    scanned = 0
    chunk: list[dict] = []

    def flush(chunk: list[dict]) -> None:
        for row in chunk:
            prompt = row.get("edit_prompt")
            if prompt is None or not str(prompt).strip():
                continue
            records.append(
                {
                    "edit_prompt": str(prompt),
                    "original_prompt": row.get("original_prompt"),
                    "edit_type": row.get("edit_type"),
                    "checksum": _row_checksum(row),
                }
            )

    try:
        for row in row_iter:
            scanned += 1
            chunk.append(row)
            if len(chunk) >= chunk_size:
                flush(chunk)
                chunk = []
                log.info(
                    "Scanned %d streamed rows; kept %d prompts",
                    scanned,
                    len(records),
                )
                if len(records) >= n_prompts:
                    break
        if chunk and len(records) < n_prompts:
            flush(chunk)
    except Exception:
        log.exception("REAL data fetch failed while streaming %s", source)
        raise

    if len(records) < n_prompts:
        raise RuntimeError(
            f"Real stream yielded only {len(records)} valid prompts "
            f"(needed {n_prompts}); refusing to fabricate data."
        )

    df = pd.DataFrame(records[:n_prompts])
    # Fail loudly if any prompt/checksum is null or duplicated.
    if df["edit_prompt"].isna().any() or df["checksum"].isna().any():
        raise RuntimeError("Null prompt or checksum in collected sample.")
    if df["checksum"].duplicated().any():
        raise RuntimeError("Duplicate row checksums in collected sample.")
    log.info(
        "Collected %d real prompts from %d scanned rows (source: %s)",
        len(df),
        scanned,
        source,
    )
    df.attrs["source"] = source
    df.attrs["scanned_rows"] = scanned
    return df


def main() -> int:
    df = collect_prompt_sample()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)
    log.info("Wrote %d rows to %s", len(df), OUTPUT_PATH)

    provenance = {
        "dataset_id": DATASET_ID,
        "split": SPLIT,
        "streaming_rule": (
            "datasets.load_dataset('timbrooks/instructpix2pix', "
            "split='train', streaming=True), full stream scanned in "
            f"chunks of {CHUNK_SIZE} rows; fallback: canonical HF parquet shards"
        ),
        "source_used": df.attrs["source"],
        "rows_scanned": df.attrs["scanned_rows"],
        "n_rows_written": int(len(df)),
        "n_prompts_target": N_PROMPTS,
        "checksum_algorithm": "sha256 over (edit_prompt, original_prompt, edit_type) JSON",
        "output_file": str(OUTPUT_PATH),
        "output_sha256": hashlib.sha256(OUTPUT_PATH.read_bytes()).hexdigest(),
    }
    PROVENANCE_PATH.write_text(json.dumps(provenance, indent=2))
    log.info("Wrote provenance to %s", PROVENANCE_PATH)

    # Observable check: >= 2000 rows, non-null prompts and checksums.
    check = pd.read_parquet(OUTPUT_PATH)
    assert len(check) >= N_PROMPTS, "fewer than 2000 rows"
    assert check["edit_prompt"].notna().all(), "null prompts present"
    assert check["checksum"].notna().all(), "null checksums present"
    log.info(
        "Check passed: %d rows, all prompts and checksums non-null",
        len(check),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())