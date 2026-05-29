"""Feedback-loop auditor (FR-034).

Walks runner dispatch records under projects/<id>/.audit/dispatches/*.jsonl
and validates each per FR-034:
    (a) input context contained the project's activity feed
    (b) output contained a valid comments-considered manifest
        referencing only real feed items

A dispatch passes iff both conditions hold.
"""

from __future__ import annotations

import json
from glob import glob
from pathlib import Path
from typing import Any

from . import register
from .manifest import ManifestItem, RuleFired, add_item, new_manifest


def _read_feed_ids(project_dir: Path) -> set[str]:
    feed = project_dir / "activity.jsonl"
    if not feed.exists():
        return set()
    ids: set[str] = set()
    for line in feed.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
            if "id" in item:
                ids.add(item["id"])
        except json.JSONDecodeError:
            continue
    return ids


def _validate_dispatch(record: dict[str, Any], feed_ids: set[str]) -> tuple[bool, list[RuleFired]]:
    """Returns (passes, rules_fired) for one dispatch record."""
    rules: list[RuleFired] = []
    # (a) feed delivery
    if not record.get("feed_delivered"):
        rules.append(RuleFired(
            rule_id="feed_not_delivered",
            evidence_snippet=f"dispatch_id={record.get('dispatch_id')}",
        ))
        return False, rules

    # (b) manifest validity
    manifest = record.get("manifest") or {}
    if not manifest:
        rules.append(RuleFired(rule_id="manifest_missing", evidence_snippet=""))
        return False, rules

    bogus_ids: list[str] = []
    for item in manifest.get("items", []):
        fid = item.get("feed_item_id")
        if fid and fid not in feed_ids:
            bogus_ids.append(fid)
    if bogus_ids:
        rules.append(RuleFired(
            rule_id="manifest_references_bogus_feed_ids",
            evidence_snippet=f"bogus={bogus_ids[:3]}",
        ))
        return False, rules

    rules.append(RuleFired(rule_id="dispatch_valid", evidence_snippet="all checks passed"))
    return True, rules


def audit(*, projects_dir: Path | str, repo_root: Path | str = ".", since: str | None = None, **_: Any) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    projects_dir = Path(projects_dir).resolve()
    if not projects_dir.exists():
        raise FileNotFoundError(f"projects_dir does not exist: {projects_dir}")

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(repo_root))
        except ValueError:
            return str(p)

    manifest = new_manifest("feedback_loop")
    dispatch_files = sorted(glob(str(projects_dir / "PROJ-*/.audit/dispatches/*.jsonl")))
    manifest["inputs_scanned"] = [_rel(Path(p)) for p in dispatch_files]

    for df in dispatch_files:
        project_dir = Path(df).parent.parent.parent  # .../PROJ-XXX/.audit/dispatches/X.jsonl -> .../PROJ-XXX
        feed_ids = _read_feed_ids(project_dir)
        for line in Path(df).read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if since and record.get("dispatched_at", "") < since:
                continue
            passes, rules = _validate_dispatch(record, feed_ids)
            add_item(manifest, ManifestItem(
                target=record.get("dispatch_id", "<unknown>"),
                rules_fired=rules,
                classification="passes" if passes else "fails",
            ))

    return manifest


register("feedback_loop", audit)
