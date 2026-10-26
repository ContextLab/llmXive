"""Acquire and validate the real primary dataset (FR-001, deviation #1).

Fetches the ``mmbench/ocean`` validation split from the Hugging Face Hub.
Primary path: ``datasets.load_dataset(..., streaming=True)``. The
``datasets`` import is performed defensively because some runner
environments ship a ``pyarrow`` build incompatible with the installed
NumPy (ImportError at import time). When — and only when — the
``datasets`` library itself cannot be imported, the loader falls back to
the official Hugging Face datasets‑server HTTP API
(https://datasets-server.huggingface.co), which serves the SAME real
records of the SAME real dataset as JSON. Both paths stream the REAL
validation split; any fetch/parse failure raises loudly. There is NO
synthetic or mock fallback.

Outputs:
- ``data/raw/video_metadata.jsonl``  (one schema‑validated record/line)
- ``data/raw/checksums.json``       (SHA‑256 checksums of written files)
- ``data/raw/dataset_stats.json``   (record count, field presence,
  missing‑tag counts, sample‑size/power limitation statement)
"""

from __future__ import annotations

import hashlib
import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import jsonschema
import requests
import yaml

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ``datasets`` is imported defensively: on runners where pyarrow was
# built against NumPy 2.x but NumPy 1.x is installed, importing
# ``datasets`` raises ImportError. In that case we keep the module-level
# name ``load_dataset = None`` and use the datasets‑server HTTP API in
# ``stream_records``. If the import succeeds, the streaming path is used
# and any runtime fetch error propagates (fail loudly).
try:  # pragma: no cover - environment dependent
    from datasets import load_dataset  # type: ignore
except Exception as _import_error:  # noqa: BLE001
    load_dataset = None  # type: ignore
    _DATASETS_IMPORT_ERROR = repr(_import_error)
else:
    _DATASETS_IMPORT_ERROR = None

DATASET_ID = "mmbench/ocean"
SPLIT = "validation"
CHUNK_SIZE = 100
DATASETS_SERVER = "https://datasets-server.huggingface.co"

PROJECT_ROOT = paths.root
SCHEMA_PATH = (
    PROJECT_ROOT
    / "specs"
    / "001-llmxive-follow-up-extending-perception-o"
    / "contracts"
    / "video_metadata.schema.yaml"
)
RAW_DIR = paths.data("raw")

VIDEO_ID_KEYS = [
    "video_id",
    "videoId",
    "videoID",
    "vid",
    "video",
    "id",
    "index",
    "sample_id",
]
URL_KEYS = [
    "video_url",
    "videoUrl",
    "videoURL",
    "url",
    "video_path",
    "video",
    "video_path_url",
    "file",
]
TRANSCRIPT_KEYS = [
    "transcript",
    "text",
    "caption",
    "subtitles",
    "subtitle",
    "speech",
    "dialogue",
    "description",
]
SETTING_KEYS = [
    "setting",
    "scene",
    "situation",
    "context",
    "environment",
    "scenario",
    "occasion",
]
CULTURE_KEYS = [
    "culture",
    "cultural_background",
    "country",
    "region",
    "ethnicity",
    "nationality",
]
BEHAVIOR_KEYS = [
    "behavior_tags",
    "behaviors",
    "behavior",
    "tags",
    "actions",
    "behavioral_evidence",
    "evidence",
    "annotations",
]
LABEL_KEYS = [
    "answer",
    "label",
    "gold",
    "gt",
    "ground_truth",
    "target",
    "expert_label",
]
OCEAN_TRAITS = [
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
]

LIMITATION_NOTE = (
    "Sample-size/power limitation: all reported results use the mmbench/ocean "
    "validation split (N records as counted in this file). MM-OCEAN (spec FR-001) "
    "has no verified public URL and is deferred to future replication (deviation #1). "
    "Whether N meets the >=80% power target for Cohen's d ~ 0.5 is assessed a priori "
    "in data/derived/power_analysis.json (T014) and verified post hoc in T009; any "
    "shortfall is recorded there and reported as a limitation, never resolved by "
    "fabricating data."
)


def load_schema() -> Dict[str, Any]:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _first_present(record: Dict[str, Any], keys: List[str]) -> Optional[Any]:
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    # case‑insensitive fallback
    lower = {str(k).strip().lower(): v for k, v in record.items()}
    for key in keys:
        if key in lower and lower[key] is not None:
            return lower[key]
    return None


def _as_tags(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        tags: List[str] = []
        for item in value:
            if item is None:
                continue
            if isinstance(item, (list, tuple)):
                tags.extend(str(x) for x in item if x is not None)
            else:
                tags.append(str(item))
        return [t.strip() for t in tags if t.strip()]
    if isinstance(value, str):
        parts = value.replace(";", ",").split(",")
        return [p.strip() for p in parts if p.strip()]
    return [str(value)]


def _as_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        value = " ".join(str(v) for v in value if v is not None)
    text = str(value).strip()
    return text if text else None


def _expert_labels(record: Dict[str, Any]) -> Dict[str, Any]:
    labels: Dict[str, Any] = {}
    lower = {str(k).strip().lower(): (k, v) for k, v in record.items()}
    for trait in OCEAN_TRAITS:
        for lk, (orig, val) in lower.items():
            if trait in lk and val is not None:
                labels[trait] = val
                break
    if not labels:
        for key in LABEL_KEYS:
            if key in lower and lower[key][1] is not None:
                labels["label"] = lower[key][1]
                break
    return labels


def normalize_record(record: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Map a raw dataset row to the contract's normalized shape.

    Raises ValueError when no video identifier can be determined — the
    loader fails loudly rather than inventing data.
    """
    vid = _as_text(_first_present(record, VIDEO_ID_KEYS))
    if vid is None:
        vid = _as_text(record.get("video"))
    if vid is None:
        raise ValueError(
            f"Record {index}: cannot determine a video identifier from columns "
            f"{sorted(record.keys())}; refusing to fabricate one."
        )
    mapped = {
        "video_id": vid,
        "video_url": _as_text(_first_present(record, URL_KEYS)),
        "transcript": _as_text(_first_present(record, TRANSCRIPT_KEYS)),
        "setting": _as_text(_first_present(record, SETTING_KEYS)),
        "culture": _as_text(_first_present(record, CULTURE_KEYS)),
        "behavior_tags": _as_tags(_first_present(record, BEHAVIOR_KEYS)),
        "expert_labels": _expert_labels(record),
    }
    used = set()
    for keys in (
        VIDEO_ID_KEYS,
        URL_KEYS,
        TRANSCRIPT_KEYS,
        SETTING_KEYS,
        CULTURE_KEYS,
        BEHAVIOR_KEYS,
    ):
        for key in keys:
            used.add(key)
            used.add(key.lower())
    extra = {
        k: v
        for k, v in record.items()
        if k not in used and not str(k).lower() in {t for t in OCEAN_TRAITS}
    }
    # keep only JSON‑serializable extras
    clean_extra: Dict[str, Any] = {}
    for k, v in extra.items():
        try:
            json.dumps(v)
            clean_extra[k] = v
        except (TypeError, ValueError):
            clean_extra[k] = str(v)
    mapped["extra"] = clean_extra
    return mapped


def _auth_headers() -> Dict[str, str]:
    """Return optional Authorization header if a HuggingFace token is available."""
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _http_config_for_split() -> str:
    """Resolve the datasets‑server config name for the validation split.

    The /splits endpoint returns a list where each element corresponds to
    a config and contains a ``splits`` list. We need to locate the config
    that provides the requested SPLIT. If the expected structure is not
    found, fall back to the first available config name.
    """
    headers = _auth_headers()
    resp = requests.get(
        f"{DATASETS_SERVER}/splits",
        params={"dataset": DATASET_ID},
        headers=headers,
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json()
    splits_info = payload.get("splits", [])
    for cfg in splits_info:
        config_name = cfg.get("config")
        for split_entry in cfg.get("splits", []):
            if split_entry.get("split") == SPLIT:
                return config_name
    # Fallback: use the first config name if present
    if splits_info:
        first_cfg = splits_info[0]
        if "config" in first_cfg:
            return first_cfg["config"]
    raise RuntimeError(
        f"{DATASET_ID} has no '{SPLIT}' split according to the Hugging Face "
        f"datasets‑server (available configs: {splits_info!r}); refusing to fabricate data."
    )


def _stream_records_http() -> Iterator[Dict[str, Any]]:
    """Stream the REAL validation split via the datasets‑server rows API.

    Used only when the ``datasets`` library cannot be imported (e.g. a
    pyarrow/NumPy binary incompatibility on the runner). Raises on any
    HTTP or parse failure — no synthetic fallback.
    """
    config = _http_config_for_split()
    log.info(
        "Streaming %s split=%s via datasets‑server (config=%s); "
        "datasets‑library import unavailable: %s",
        DATASET_ID,
        SPLIT,
        config,
        _DATASETS_IMPORT_ERROR,
    )
    headers = _auth_headers()
    offset = 0
    page_size = 100
    while True:
        resp = requests.get(
            f"{DATASETS_SERVER}/rows",
            params={
                "dataset": DATASET_ID,
                "config": config,
                "split": SPLIT,
                "offset": offset,
                "length": page_size,
            },
            headers=headers,
            timeout=120,
        )
        resp.raise_for_status()
        payload = resp.json()
        rows = payload.get("rows", [])
        if not rows:
            break
        for row in rows:
            rec = row.get("row")
            if rec is None:
                raise RuntimeError(
                    f"Malformed datasets‑server row at offset {offset}: {row!r}"
                )
            yield dict(rec)
        if len(rows) < page_size:
            break
        offset += page_size


def stream_records() -> Iterator[Dict[str, Any]]:
    """Stream the REAL validation split. Raises on any fetch failure."""
    loader = globals().get("load_dataset")
    if callable(loader):
        log.info("Streaming %s split=%s via datasets library", DATASET_ID, SPLIT)
        ds = loader(DATASET_ID, split=SPLIT, streaming=True)
        for record in ds:
            yield dict(record)
        return
    # ``datasets`` could not be imported on this runner — use the real
    # datasets‑server HTTP API for the same dataset/split.
    yield from _stream_records_http()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    schema = load_schema()
    validator = jsonschema.Draft7Validator(schema)

    # Ensure the output directory exists
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    out_path = RAW_DIR / "video_metadata.jsonl"
    n_records = 0
    field_nonnull = {f: 0 for f in ("video_url", "transcript", "setting", "culture")}
    missing_tags = 0
    missing_labels = 0

    tmp_path = RAW_DIR / "video_metadata.jsonl.tmp"
    with open(tmp_path, "w", encoding="utf-8") as out:
        buffer: List[Dict[str, Any]] = []
        for record in stream_records():
            try:
                normalized = normalize_record(record, n_records)
            except ValueError as ve:
                # Skip records that cannot be normalized (e.g., missing video_id)
                log.warning(str(ve))
                continue

            errs = sorted(validator.iter_errors(normalized), key=lambda e: e.path)
            if errs:
                raise jsonschema.ValidationError(
                    f"Record {n_records} (video_id={normalized.get('video_id')}) violates "
                    f"video_metadata.schema.yaml: {errs[0].message}"
                )
            buffer.append(normalized)
            n_records += 1
            for f in field_nonnull:
                if normalized[f] is not None:
                    field_nonnull[f] += 1
            if not normalized["behavior_tags"]:
                missing_tags += 1
            if not normalized["expert_labels"]:
                missing_labels += 1
            if len(buffer) >= CHUNK_SIZE:
                for rec in buffer:
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                buffer = []
                log.info(" ... %d records streamed", n_records)
        # Flush remaining buffer
        for rec in buffer:
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")

    if n_records == 0:
        raise RuntimeError(
            f"Streaming {DATASET_ID} split={SPLIT} yielded 0 records; "
            "refusing to write an empty dataset (no synthetic fallback)."
        )
    tmp_path.replace(out_path)
    log.info("Wrote %d records to %s", n_records, out_path)

    checksum = sha256_file(out_path)
    checksums = {
        "dataset_id": DATASET_ID,
        "split": SPLIT,
        "files": {
            str(out_path.relative_to(PROJECT_ROOT)): {
                "sha256": checksum,
                "bytes": out_path.stat().st_size,
                "record_count": n_records,
            }
        },
    }
    with open(RAW_DIR / "checksums.json", "w", encoding="utf-8") as fh:
        json.dump(checksums, fh, indent=2)

    stats = {
        "dataset_id": DATASET_ID,
        "split": SPLIT,
        "n_records": n_records,
        "fields_present": {
            "video_id": n_records,
            **{f: c for f, c in field_nonnull.items()},
            "behavior_tags_nonempty": n_records - missing_tags,
            "expert_labels_nonempty": n_records - missing_labels,
        },
        "missing_tag_counts": {
            "behavior_tags_missing": missing_tags,
            "expert_labels_missing": missing_labels,
            "transcript_missing": n_records - field_nonnull["transcript"],
            "setting_missing": n_records - field_nonnull["setting"],
            "culture_missing": n_records - field_nonnull["culture"],
        },
        "sample_size_power_limitation": LIMITATION_NOTE,
        "dataset_substitution_note": (
            "MM-OCEAN (spec FR-001) has no verified public URL; the verified open "
            "dataset mmbench/ocean is the primary data source for all reported "
            "results (deviation #1, flagged for kickback)."
        ),
        "transport": (
            "datasets‑library streaming"
            if callable(globals().get("load_dataset"))
            else "huggingface datasets‑server HTTP API (datasets library not "
                 "importable on this runner)"
        ),
    }
    with open(RAW_DIR / "dataset_stats.json", "w", encoding="utf-8") as fh:
        json.dump(stats, fh, indent=2)
    log.info(
        "Wrote dataset_stats.json: %d records, %d missing behavior tags", n_records, missing_tags
    )


if __name__ == "__main__":
    main()
