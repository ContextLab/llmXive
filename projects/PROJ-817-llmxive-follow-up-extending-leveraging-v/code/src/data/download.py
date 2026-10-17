"""Download the real InstructPix2Pix prompt source data (T001).

Streams the full ``timbrooks/instructpix2pix`` train split via
``datasets.load_dataset(..., streaming=True)``. Because the Hub-side
dataset loader can be unavailable on some runners (renamed repos,
removed loading scripts, ``datasets>=3`` incompatibilities), the module
falls back to REAL, canonical sources of the SAME dataset, in order:

1. ``datasets.load_dataset("timbrooks/instructpix2pix", split="train",
   streaming=True)`` (primary, per spec).
2. Loading the full dataset non‑streaming (fallback when streaming fails).
3. The dataset's auto‑converted parquet shards listed by the official
   HF datasets‑server API
   (``https://datasets-server.huggingface.co/parquet?dataset=...``),
   streamed one shard at a time with
   ``load_dataset("parquet", data_files=<url>, streaming=True)``.
4. The parquet URLs published by the Hub API endpoint
   ``https://huggingface.co/api/datasets/timbrooks/instructpix2pix/parquet/default/train``.
5. The datasets‑server ``/rows`` API (paginated real rows).

Every fallback serves REAL rows of the SAME dataset; there is NO
synthetic/mock fallback, ever, and any fetch error raises loudly.

Run:  python -m code.src.data.download
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import requests
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

DATASET_ID = "timbrooks/instructpix2pix"
SPLIT = "train"
N_PROMPTS = 2000
CHUNK_SIZE = 500

DATASETS_SERVER_PARQUET = (
    "https://datasets-server.huggingface.co/parquet"
)
HUB_API_PARQUET = (
    "https://huggingface.co/api/datasets/timbrooks/instructpix2pix/"
    "parquet/default/train"
)
DATASETS_SERVER_ROWS = "https://datasets-server.huggingface.co/rows"

OUTPUT_PATH = paths.data("raw", "prompts_sample.parquet")
PROVENANCE_PATH = paths.data("raw", "prompts_sample_provenance.json")


def _row_checksum(row: dict) -> str:
    """Stable SHA‑256 over the fields that identify a real source row."""
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


def _load_full_dataset():
    """Fallback: load the entire split into memory (still real data)."""
    from datasets import load_dataset

    log.info(
        "Loading full %s split=%s into memory as fallback",
        DATASET_ID,
        SPLIT,
    )
    ds = load_dataset(DATASET_ID, split=SPLIT)  # returns a Dataset object
    for row in ds:
        yield row


def _parquet_urls_from_datasets_server() -> list[str]:
    """Real parquet shard URLs from the official HF datasets‑server API."""
    resp = requests.get(
        DATASETS_SERVER_PARQUET,
        params={"dataset": DATASET_ID},
        timeout=60,
    )
    resp.raise_for_status()
    files = resp.json().get("parquet_files", [])
    urls = [f["url"] for f in files if f.get("split") == SPLIT]
    if not urls:
        raise RuntimeError(
            f"datasets‑server returned no train parquet files for {DATASET_ID}"
        )
    return sorted(urls)


def _parquet_urls_from_hub_api() -> list[str]:
    """Real parquet shard URLs from the Hub parquet API endpoint."""
    resp = requests.get(HUB_API_PARQUET, timeout=60)
    resp.raise_for_status()
    urls = list(resp.json())
    if not urls:
        raise RuntimeError(
            f"Hub parquet API returned no train files for {DATASET_ID}"
        )
    return sorted(urls)


def _iter_parquet_shards(urls: list[str]):
    """Fallback path: stream real canonical parquet shards one by one."""
    from datasets import load_dataset

    for url in urls:
        log.info("Streaming canonical parquet shard: %s", url)
        ds = load_dataset(
            "parquet", data_files=url, split="train", streaming=True
        )
        for row in ds:
            yield row


def _iter_stream_parquet():
    """Fallback path: real parquet shards, server‑listed then Hub‑listed."""
    try:
        urls = _parquet_urls_from_datasets_server()
    except Exception as exc:  # noqa: BLE001 - try the other real source
        log.warning(
            "datasets‑server parquet listing failed (%s); trying Hub API",
            exc,
        )
        urls = _parquet_urls_from_hub_api()
    yield from _iter_parquet_shards(urls)


def _iter_rows_api():
    """Last real fallback: paginated real rows from the datasets‑server."""
    offset = 0
    page = 100
    while True:
        resp = requests.get(
            DATASETS_SERVER_ROWS,
            params={
                "dataset": DATASET_ID,
                "config": "default",
                "split": SPLIT,
                "offset": offset,
                "length": page,
            },
            timeout=120,
        )
        # Some environments may reject unauthenticated access; propagate error.
        resp.raise_for_status()
        rows = resp.json().get("rows", [])
        if not rows:
            return
        for wrapped in rows:
            row = wrapped.get("row", {})
            # Normalise possible dict‑encoded prompts.
            if isinstance(row.get("edit_prompt"), dict):
                row["edit_prompt"] = row["edit_prompt"].get("text")
            if isinstance(row.get("original_prompt"), dict):
                row["original_prompt"] = row["original_prompt"].get("text")
            yield row
        offset += len(rows)


def collect_prompt_sample(
    n_prompts: int = N_PROMPTS, chunk_size: int = CHUNK_SIZE
) -> pd.DataFrame:
    """Scan the real stream in chunks; keep the first n_prompts valid rows.

    Raises on any fetch error — no synthetic fallback.
    """
    attempts = [
        (
            "datasets.load_dataset streaming",
            _iter_stream_hf,
        ),
        (
            "datasets.load_dataset full (non‑streaming) fallback",
            _load_full_dataset,
        ),
        (
            "canonical HF parquet shards via datasets‑server/Hub API",
            _iter_stream_parquet,
        ),
        (
            "datasets‑server /rows API (paginated real rows)",
            _iter_rows_api,
        ),
    ]

    records: list[dict] = []
    scanned = 0
    source = None

    for source, stream_factory in attempts:
        records = []
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
            row_iter = stream_factory()
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
            log.exception(
                "REAL data fetch failed while streaming (source: %s)",
                source,
            )
            if stream_factory is attempts[-1][1]:
                raise
            log.warning("Falling back to the next REAL source")
            continue

        if len(records) >= n_prompts:
            break
        log.warning(
            "Source %s yielded only %d valid prompts (< %d); "
            "trying the next REAL source",
            source,
            len(records),
            n_prompts,
        )

    if len(records) < n_prompts:
        raise RuntimeError(
            f"All REAL sources yielded only {len(records)} valid prompts "
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
            f"chunks of {CHUNK_SIZE} rows; fallbacks: full non‑streaming "
            "load, canonical parquet shards (datasets‑server / Hub API), "
            "and datasets‑server /rows API — all serving the same real dataset"
        ),
        "source_used": df.attrs["source"],
        "rows_scanned": df.attrs["scanned_rows"],
        "n_rows_written": int(len(df)),
        "n_prompts_target": N_PROMPTS,
        "checksum_algorithm": (
            "sha256 over (edit_prompt, original_prompt, edit_type) JSON"
        ),
        "output_file": str(OUTPUT_PATH),
        "output_sha256": hashlib.sha256(OUTPUT_PATH.read_bytes()).hexdigest(),
    }
    PROVENANCE_PATH.write_text(json.dumps(provenance, indent=2))
    log.info("Wrote provenance to %s", PROVENANCE_PATH)

    # Observable check: >= 2000 rows, non‑null prompts and checksums.
    check = pd.read_parquet(OUTPUT_PATH)
    assert len(check) >= N_PROMPTS, "fewer than 2000 rows"
    assert check["edit_prompt"].notna().all(), "null prompts present"
    assert check["checksum"].notna().all(), "null checksums present"
    log.info(
        "Check passed: %d rows, all prompts and checksums non‑null",
        len(check),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
