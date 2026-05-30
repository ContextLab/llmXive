"""Persistent full-text + verdict caches for claim grounding."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from llmxive.config import grounding_cache_dir

_FULLTEXT_TTL_S = 90 * 24 * 3600
_VERDICT_TTL_S = 30 * 24 * 3600


def _dir(repo_root: Path, sub: str) -> Path:
    d = grounding_cache_dir(repo_root) / sub
    d.mkdir(parents=True, exist_ok=True)
    return d


def _key(*parts: str) -> str:
    return hashlib.sha256(" ".join(parts).encode("utf-8")).hexdigest()


def _now() -> float:
    return time.time()


def _read(path: Path, *, max_age_s: float) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        rec: dict[str, Any] = json.loads(path.read_text())
    except (ValueError, OSError):
        return None
    if max_age_s < 0 or (_now() - float(rec.get("_ts", 0))) > max_age_s:
        return None
    data = rec.get("data")
    if not isinstance(data, dict):
        return None
    return data


def _write(path: Path, data: dict[str, Any]) -> None:
    payload = json.dumps({"_ts": _now(), "data": data})
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=path.suffix + ".tmp")
    try:
        os.write(fd, payload.encode("utf-8"))
        os.close(fd)
        os.replace(tmp, path)
    except Exception:
        os.close(fd)
        os.unlink(tmp)
        raise


def put_fulltext(repo_root: Path, kind: str, value: str, data: dict[str, Any]) -> None:
    _write(_dir(repo_root, "fulltext") / f"{_key(kind, value)}.json", data)


def get_fulltext(repo_root: Path, kind: str, value: str,
                 *, max_age_s: float = _FULLTEXT_TTL_S) -> dict[str, Any] | None:
    return _read(_dir(repo_root, "fulltext") / f"{_key(kind, value)}.json", max_age_s=max_age_s)


def put_verdict(repo_root: Path, *, source_id: str, claim: str, number: str | None,
                verdict: dict[str, Any]) -> None:
    k = _key(source_id, " ".join(claim.lower().split()), number or "")
    _write(_dir(repo_root, "verdict") / f"{k}.json", verdict)


def get_verdict(repo_root: Path, *, source_id: str, claim: str, number: str | None,
                max_age_s: float = _VERDICT_TTL_S) -> dict[str, Any] | None:
    k = _key(source_id, " ".join(claim.lower().split()), number or "")
    return _read(_dir(repo_root, "verdict") / f"{k}.json", max_age_s=max_age_s)
