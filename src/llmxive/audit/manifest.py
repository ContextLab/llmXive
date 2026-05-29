"""Shared audit manifest writer + reader (FR-007).

Manifests are JSON files at .audit/<auditor>/<ISO8601-utc>.json.
Schema: specs/009-quality-fixes-pass/contracts/audit-manifest.schema.json

We intentionally do NOT install a JSON Schema runtime as a hard dep here;
validation is done by the test suite using the published schema, and the
writer maintains the shape via dataclasses below. Constitution V (fail fast):
the writer validates required fields before writing.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from . import __version__ as AUDIT_VERSION

AUDITORS = {"personality_rubric", "template_vs_real", "pdf", "feedback_loop"}
CLASSIFICATIONS = {"real", "partial", "template", "passes", "fails"}


@dataclass
class RuleFired:
    rule_id: str
    evidence_snippet: str


@dataclass
class Defect:
    paper_id: str
    page: int
    defect_type: str
    evidence_snippet: str
    rule_id: str
    auto_fixable: bool = False


@dataclass
class ManifestItem:
    target: str
    rules_fired: list[RuleFired] = field(default_factory=list)
    classification: str | None = None
    defects: list[Defect] = field(default_factory=list)
    rubric_scores: dict[str, int] | None = None


def utcnow_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def new_manifest(auditor: str) -> dict:
    """Start a new manifest with required header fields."""
    if auditor not in AUDITORS:
        raise ValueError(
            f"Unknown auditor {auditor!r}; expected one of {sorted(AUDITORS)}"
        )
    return {
        "auditor": auditor,
        "started_at": utcnow_iso(),
        "ended_at": utcnow_iso(),
        "version": AUDIT_VERSION,
        "inputs_scanned": [],
        "items": [],
        "summary": {"total": 0, "by_classification": {}, "by_defect_type": {}},
    }


def add_item(manifest: dict, item: ManifestItem | dict) -> None:
    """Append a manifest item; updates summary counters."""
    if isinstance(item, ManifestItem):
        d = _to_dict(item)
    else:
        d = item
    manifest["items"].append(d)
    manifest["summary"]["total"] = len(manifest["items"])
    cls = d.get("classification")
    if cls:
        manifest["summary"]["by_classification"][cls] = (
            manifest["summary"]["by_classification"].get(cls, 0) + 1
        )
    for defect in d.get("defects", []):
        dt = defect["defect_type"]
        manifest["summary"]["by_defect_type"][dt] = (
            manifest["summary"]["by_defect_type"].get(dt, 0) + 1
        )


def _to_dict(item: ManifestItem) -> dict:
    out = asdict(item)
    # Strip None classification + empty defects/rules_fired? Keep fields for schema.
    if out.get("classification") is None:
        out.pop("classification")
    if not out.get("defects"):
        out.pop("defects", None)
    if not out.get("rubric_scores"):
        out.pop("rubric_scores", None)
    return out


def write_manifest(
    manifest: dict, repo_root: Path | str, *, also_markdown: bool = True
) -> Path:
    """Write manifest to .audit/<auditor>/<ts>.json. Returns the path written.

    Fail-fast: validates required keys before opening any file (Principle V).
    """
    required = {"auditor", "started_at", "ended_at", "version", "items", "summary"}
    missing = required - set(manifest)
    if missing:
        raise ValueError(f"manifest missing required keys: {sorted(missing)}")

    manifest["ended_at"] = utcnow_iso()
    repo_root = Path(repo_root)
    out_dir = repo_root / ".audit" / manifest["auditor"]
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = manifest["started_at"].replace(":", "-")
    out_path = out_dir / f"{ts}.json"
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    if also_markdown:
        _write_markdown_sibling(manifest, out_path.with_suffix(".md"))
    return out_path


def _write_markdown_sibling(manifest: dict, out_path: Path) -> None:
    lines = [
        f"# Audit Manifest — {manifest['auditor']} (v{manifest['version']})",
        "",
        f"- **Started**: {manifest['started_at']}",
        f"- **Ended**:   {manifest['ended_at']}",
        f"- **Inputs**:  {len(manifest['inputs_scanned'])}",
        f"- **Items**:   {manifest['summary']['total']}",
        "",
    ]
    by_cls = manifest["summary"].get("by_classification", {})
    if by_cls:
        lines.append("## By classification")
        lines.append("")
        lines.append("| Classification | Count |")
        lines.append("|-|-|")
        for k in sorted(by_cls):
            lines.append(f"| {k} | {by_cls[k]} |")
        lines.append("")
    by_def = manifest["summary"].get("by_defect_type", {})
    if by_def:
        lines.append("## By defect type")
        lines.append("")
        lines.append("| Defect type | Count |")
        lines.append("|-|-|")
        for k in sorted(by_def):
            lines.append(f"| {k} | {by_def[k]} |")
        lines.append("")
    if manifest["items"]:
        lines.append("## Items")
        lines.append("")
        for it in manifest["items"]:
            tag = it.get("classification") or (
                f"{len(it.get('defects', []))} defect(s)" if it.get("defects") else "—"
            )
            lines.append(f"- `{it['target']}` — **{tag}**")
            for rf in it.get("rules_fired", []):
                snippet = rf["evidence_snippet"].replace("\n", " ⏎ ")
                lines.append(f"  - rule `{rf['rule_id']}`: {snippet[:200]}")
    out_path.write_text("\n".join(lines))


def read_manifest(path: Path | str) -> dict:
    return json.loads(Path(path).read_text())


def iter_items(manifest: dict) -> Iterable[dict]:
    yield from manifest["items"]
