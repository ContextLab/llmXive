"""Deterministic HOLLOW-RESULTS gate (sibling of :mod:`fabrication_guard`).

The execution gate's bar was ``bool(produced)`` — "did a file appear?". It never
looked INSIDE the file. So an analysis could run to completion, write every artifact
its run-book declared, and report NOTHING: PROJ-179 (a study of metacognitive
awareness, run on the IRIS FLOWER dataset) reached ``research_complete`` having
written ``{"correlation_coefficient": null, "p_value": null}`` as its primary result,
``d_prime: NaN`` as its headline metric, ``[]`` as its robustness analysis, and
``{"status": "PASS"}`` as its own validation report.

``fabrication_guard`` catches numbers that were FAKED. This catches numbers that were
never COMPUTED. Both are "the results are not real measurements", and both must be a
hard gate failure rather than something only the (non-deterministic) LLM review panel
might notice.

Design for HIGH PRECISION — honest work must never be blocked:
  * ``0.0`` and negative values are REAL measurements and are never flagged.
  * A non-numeric report (a dataset name, a status string) has no metric to be
    hollow about, so it is ignored.
  * Only RESULT artifacts are judged — raw inputs, figures, checksums and logs are
    not measurements.
  * A single populated metric is enough to clear a file; we flag only values that
    are affirmatively missing (``null`` / ``NaN`` / ``Infinity``) or containers with
    no data at all.
"""

from __future__ import annotations

import csv
import json
import math
from io import StringIO
from pathlib import Path

#: Path segments whose artifacts are RESULTS — the numbers a paper would report.
#: ``data/raw`` is an INPUT, not a result, so it is deliberately absent.
_RESULT_DIR_HINTS = ("results", "derived", "processed", "outputs", "output", "metrics")

#: Only these carry machine-readable measurements. A ``.png`` is a rendering of a
#: result, not the result; a ``.md``/``.txt`` is prose.
_RESULT_SUFFIXES = (".json", ".csv")

#: Keys that are bookkeeping, not measurements — a null here is not a hollow result.
_NON_METRIC_KEYS = frozenset({
    "status", "dataset", "source", "path", "file", "name", "version", "seed",
    "timestamp", "created_at", "updated_at", "notes", "description", "units",
    "generated_by", "commit", "sha", "checksum",
})


def _is_missing_number(v: object) -> bool:
    """A value that is affirmatively ABSENT where a number belongs.

    ``None`` (JSON null) and NaN/±Infinity are non-measurements. ``0.0`` and negative
    values are REAL and must never land here.
    """
    if v is None:
        return True
    if isinstance(v, bool):
        return False
    if isinstance(v, float):
        return math.isnan(v) or math.isinf(v)
    return False


def _walk(obj: object, path: str = "") -> list[tuple[str, object]]:
    """Flatten a JSON document to (dotted-key, leaf-value) pairs."""
    out: list[tuple[str, object]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.extend(_walk(v, f"{path}.{k}" if path else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(_walk(v, f"{path}[{i}]"))
    else:
        out.append((path, obj))
    return out


def _scan_json(rel: str, text: str) -> list[str]:
    try:
        # NaN/Infinity are not legal JSON but json.loads accepts them by default,
        # and analysis code writes them all the time — which is the whole point.
        doc = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return []  # unparseable is a different defect; not ours to claim

    if doc in ({}, []):
        return [f"{rel}: results file is EMPTY ({text.strip() or '<0 bytes>'}) — "
                f"the analysis produced no values"]

    leaves = _walk(doc)
    missing = [
        k for k, v in leaves
        if _is_missing_number(v) and k.rsplit(".", 1)[-1].lower() not in _NON_METRIC_KEYS
    ]
    if not missing:
        return []
    finite = [
        k for k, v in leaves
        if isinstance(v, int | float) and not isinstance(v, bool) and not _is_missing_number(v)
    ]
    detail = ", ".join(missing[:4]) + ("…" if len(missing) > 4 else "")
    if not finite:
        return [f"{rel}: EVERY metric is null/NaN ({detail}) — nothing was computed"]
    return [f"{rel}: metric is null/NaN ({detail}) — not a real measurement"]


def _scan_csv(rel: str, text: str) -> list[str]:
    rows = list(csv.reader(StringIO(text)))
    rows = [r for r in rows if r and any(c.strip() for c in r)]
    if not rows:
        return [f"{rel}: results file is EMPTY — the analysis produced no rows"]
    header, data = rows[0], rows[1:]
    if not data:
        return [f"{rel}: header only, ZERO data rows — the analysis produced no rows"]
    blank = [
        col for i, col in enumerate(header)
        if col.strip() and all(i >= len(r) or not r[i].strip() for r in data)
    ]
    if blank:
        return [
            f"{rel}: column(s) {', '.join(blank[:4])} are EMPTY in every one of "
            f"{len(data)} rows — that measure was never recorded"
        ]
    return []


def find_hollow_results(project_dir: Path, produced: list[str]) -> list[str]:
    """Findings for produced RESULT artifacts that contain no real measurement.

    ``produced`` is the execution run's artifact list (repo-relative to
    ``project_dir``). Returns one human-readable finding per defect; empty list means
    the results are populated. Never raises — an unreadable artifact is a different
    failure and is left to the caller's other checks.
    """
    findings: list[str] = []
    for rel in produced:
        p = Path(rel)
        if p.suffix.lower() not in _RESULT_SUFFIXES:
            continue
        parts = {seg.lower() for seg in p.parts}
        if not (parts & set(_RESULT_DIR_HINTS)):
            continue
        if "raw" in parts:  # an input, not a result
            continue
        f = project_dir / rel
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if p.suffix.lower() == ".json":
            findings.extend(_scan_json(rel, text))
        else:
            findings.extend(_scan_csv(rel, text))
    return findings


def find_no_durable_evidence(
    project_dir: Path, produced: list[str], *, repo_root: Path
) -> list[str]:
    """Flag a run whose every artifact is GITIGNORED — nothing survives the commit.

    ``projects/*/data/raw/*`` and ``projects/*/data/processed/*`` are gitignored by
    design (datasets are large and reproducible from the download scripts). But that
    means a run whose ONLY outputs land there leaves NOTHING behind: no committed
    result, no figure, nothing a reviewer can open and nothing a paper can cite. It is
    unverifiable by construction.

    PROJ-256 passed the gate and advanced to research_review on exactly one artifact —
    ``data/processed/null_fpr_metrics.json`` — which is gitignored and no longer
    exists. Its entire empirical contribution had already evaporated.

    Durability is decided by git itself (the .gitignore is the SSoT — never re-encode
    its patterns here). If git cannot answer (not a repo, git missing) we do NOT flag:
    this is a secondary property and must never block honest work on a bad probe.
    """
    import subprocess

    candidates = [rel for rel in produced if Path(rel).suffix.lower() != ""]
    if not candidates:
        return []
    try:
        paths = "\n".join(str((project_dir / rel).resolve()) for rel in candidates)
        proc = subprocess.run(
            ["git", "check-ignore", "--stdin"],
            input=paths, capture_output=True, text=True,
            cwd=str(repo_root), timeout=30, check=False,
        )
        # rc 0 = some ignored (listed on stdout); 1 = none ignored; >1 = error.
        if proc.returncode > 1:
            return []
    except (OSError, subprocess.SubprocessError):
        return []
    ignored = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    durable = [
        rel for rel in candidates
        if str((project_dir / rel).resolve()) not in ignored
    ]
    if durable:
        return []
    return [
        f"every produced artifact is gitignored ({', '.join(candidates[:3])}) — the "
        f"run left NO durable evidence: nothing is committed for a reviewer to inspect "
        f"or a paper to cite. Write the results a reader needs (e.g. data/results/*, "
        f"figures/*) outside the ignored data/raw + data/processed dataset caches."
    ]


__all__ = ["find_hollow_results", "find_no_durable_evidence"]
