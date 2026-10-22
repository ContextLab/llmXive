"""Acquire and validate the real primary dataset (FR-001, deviation #1).

Fetches the ``mmbench/ocean`` validation split from the Hugging Face Hub
via ``datasets.load_dataset(..., streaming=True)``, iterates ALL records,
normalizes them into per-video metadata records, validates each record
against ``specs/001-llmxive-follow-up-extending-perception-o/contracts/video_metadata.schema.yaml``,
and writes:

- ``data/raw/video_metadata.jsonl``  (one validated record per line)
- ``data/raw/checksums.json``       (SHA-256 checksums of written raw files)
- ``data/raw/dataset_stats.json``   (record count, field presence,
  missing-tag counts, sample-size/power limitation statement)

The loader FAILS LOUDLY on any fetch/parse/validation failure. There is
NO synthetic or mock fallback: every record written comes from the real
dataset stream.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import jsonschema
import yaml
from datasets import load_dataset

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

DATASET_ID = "mmbench/ocean"
SPLIT = "validation"
CHUNK_SIZE = 100

PROJECT_ROOT = paths.root
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-llmxive-follow-up-extending-perception-o" / "contracts" / "video_metadata.schema.yaml"
RAW_DIR = paths.data("raw")

VIDEO_ID_KEYS = ["video_id", "videoId", "videoID", "vid", "video", "id", "index", "sample_id"]
URL_KEYS = ["video_url", "videoUrl", "videoURL", "url", "video_path", "video", "video_path_url", "file"]
TRANSCRIPT_KEYS = ["transcript", "text", "caption", "subtitles", "subtitle", "speech", "dialogue", "description"]
SETTING_KEYS = ["setting", "scene", "situation", "context", "environment", "scenario", "occasion"]
CULTURE_KEYS = ["culture", "cultural_background", "country", "region", "ethnicity", "nationality"]
BEHAVIOR_KEYS = ["behavior_tags", "behaviors", "behavior", "tags", "actions", "behavioral_evidence", "evidence", "annotations"]
LABEL_KEYS = ["answer", "label", "gold", "gt", "ground_truth", "target", "expert_label"]
OCEAN_TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]

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
    # case-insensitive fallback
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
    for keys in (VIDEO_ID_KEYS, URL_KEYS, TRANSCRIPT_KEYS, SETTING_KEYS, CULTURE_KEYS, BEHAVIOR_KEYS):
        for key in keys:
            used.add(key)
            used.add(key.lower())
    extra = {k: v for k, v in record.items() if k not in used and not str(k).lower() in {t for t in OCEAN_TRAITS}}
    # keep only JSON-serializable extras
    clean_extra: Dict[str, Any] = {}
    for k, v in extra.items():
        try:
            json.dumps(v)
            clean_extra[k] = v
        except (TypeError, ValueError):
            clean_extra[k] = str(v)
    mapped["extra"] = clean_extra
    return mapped


def stream_records() -> Iterator[Dict[str, Any]]:
    """Stream the REAL validation split. Raises on any fetch failure."""
    log.info("Streaming %s split=%s", DATASET_ID, SPLIT)
    ds = load_dataset(DATASET_ID, split=SPLIT, streaming=True)
    for record in ds:
        yield dict(record)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    schema = load_schema()
    validator = jsonschema.Draft7Validator(schema)

    out_path = RAW_DIR / "video_metadata.jsonl"
    n_records = 0
    field_nonnull = {f: 0 for f in ("video_url", "transcript", "setting", "culture")}
    missing_tags = 0
    missing_labels = 0
    errors: List[str] = []

    tmp_path = RAW_DIR / "video_metadata.jsonl.tmp"
    with open(tmp_path, "w", encoding="utf-8") as out:
        buffer: List[Dict[str, Any]] = []
        for record in stream_records():
            normalized = normalize_record(record, n_records)
            errs = sorted(validator.iter_errors(normalized), key=lambda e: e.path)
            if errs:
                raise jsonschema.ValidationError(
                    f"Record {n_records} (video_id={normalized['video_id']}) violates "
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
    }
    with open(RAW_DIR / "dataset_stats.json", "w", encoding="utf-8") as fh:
        json.dump(stats, fh, indent=2)
    log.info("Wrote dataset_stats.json: %d records, %d missing behavior tags", n_records, missing_tags)


if __name__ == "__main__":
    main()
