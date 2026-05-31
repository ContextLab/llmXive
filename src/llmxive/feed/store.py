"""FeedStore — single canonical reader/writer for project activity feeds.

Spec 009: FR-025 (append-only), FR-030 (audit_status=live filtering),
FR-031 (truncate-from-oldest packing with [truncated N] marker),
FR-032 (edit + retract), FR-033 (concurrent dispatches via flock).

Constitution V (Fail Fast): every public method validates inputs before any
filesystem mutation. Constitution III (Real testing): uses real filesystem,
real flock; tests under tests/unit/test_feed_store.py exercise this directly.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from ulid import ULID  # python-ulid package

    def _new_ulid() -> str:
        return str(ULID())
except ImportError:  # pragma: no cover — handled in T004 dependency add
    import secrets

    def _new_ulid() -> str:
        # 26-char Crockford-base32-ish fallback; not strictly ULID but length-correct
        alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
        return "".join(secrets.choice(alphabet) for _ in range(26))


def utcnow_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# Trivial item kinds (per spec FR-027 clarification): may be omitted from manifest
TRIVIAL_KINDS = {"manifest", "dispatch_failure", "edit", "speckit_emission", "paper_emission"}
NON_TRIVIAL_KINDS = {"personality_tick", "review", "human_comment", "revision"}


@dataclass
class PackedFeed:
    """Result of packing a feed for an agent dispatch context."""

    items: list[dict[str, Any]]             # delivered items (chronological)
    truncated: int                           # count of older items omitted
    feed_snapshot_at: str                    # ISO timestamp
    truncation_marker: str | None = None     # human-readable marker text

    def to_context_block(self) -> str:
        """Render as a markdown block for inclusion in agent input context."""
        out: list[str] = ["## Project Activity Feed", ""]
        if self.truncated > 0:
            out.append(f"_[truncated {self.truncated} earlier items]_")
            out.append("")
        for it in self.items:
            ts = it.get("created_at", "")[:19]
            author = (it.get("author") or {}).get("display_name") or (it.get("author") or {}).get("name") or "anon"
            kind = it.get("kind", "?")
            edited = " *[edited]*" if it.get("edited_at") else ""
            summary = it.get("summary", "")
            out.append(f"- `{it.get('id', '?')}` ({ts}, **{author}**, _{kind}_{edited}): {summary}")
            body = it.get("body")
            if body:
                # Trim very long bodies in the rendered block
                out.append("")
                for line in body.splitlines():
                    out.append(f"  > {line}")
                out.append("")
        out.append("")
        out.append(f"_Feed snapshot at {self.feed_snapshot_at}._")
        return "\n".join(out)


class FeedStore:
    """One-per-process accessor for project activity feeds."""

    def __init__(self, repo_root: Path | str):
        self.repo_root = Path(repo_root)

    # ----- Path helpers -----

    def project_dir(self, project_id: str) -> Path:
        if not project_id:
            raise ValueError("project_id is required")
        # locate the directory: projects/PROJ-XXX-...
        d = self.repo_root / "projects" / project_id
        if not d.exists():
            # Some callers pass the directory leaf already
            matches = list((self.repo_root / "projects").glob(f"{project_id}*"))
            if matches:
                return matches[0]
        return d

    def feed_path(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "activity.jsonl"

    def audit_dir(self, project_id: str) -> Path:
        return self.project_dir(project_id) / ".audit"

    # ----- Locking -----

    @contextlib.contextmanager
    def _locked(self, path: Path, mode: str, lock_type: int) -> Any:
        """Open `path` with an fcntl lock. mode='r' uses LOCK_SH, 'a'/'w' uses LOCK_EX.

        Creates parent dirs and the file itself (with shared/exclusive lock as appropriate).
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        if mode == "r" and not path.exists():
            yield None  # no file to read; caller handles None
            return
        # 'a' creates if needed; 'r' won't
        if mode == "a":
            path.touch(exist_ok=True)
        f = open(path, mode)
        try:
            fcntl.flock(f.fileno(), lock_type)
            yield f
        finally:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            finally:
                f.close()

    # ----- Read -----

    def read(self, project_id: str, *, include_audit_statuses: set[str] | None = None) -> list[dict[str, Any]]:
        """Return all feed items for a project.

        By default, returns only items whose `audit_status == 'live'`
        (FR-030). Pass `include_audit_statuses={'live','rejected','superseded'}`
        for maintainer/admin use.
        """
        path = self.feed_path(project_id)
        if not path.exists():
            return []
        allowed = include_audit_statuses or {"live"}
        items: list[dict[str, Any]] = []
        with self._locked(path, "r", fcntl.LOCK_SH) as f:
            if f is None:
                return []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if item.get("audit_status", "live") in allowed:
                    items.append(item)
        # Resolve edits: collapse {original, edit, edit...} chains so caller sees current body
        return self._resolve_edits(items)

    @staticmethod
    def _resolve_edits(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """For each item with later kind=edit children, replace body with newest edit's body."""
        by_id: dict[str, dict[str, Any]] = {it["id"]: it for it in items if "id" in it}
        edits_by_parent: dict[str, list[dict[str, Any]]] = {}
        for it in items:
            if it.get("kind") == "edit" and it.get("parent_id"):
                edits_by_parent.setdefault(it["parent_id"], []).append(it)
        # newest edit wins
        for parent_id, edits in edits_by_parent.items():
            edits.sort(key=lambda e: e.get("created_at", ""))
            newest = edits[-1]
            parent = by_id.get(parent_id)
            if parent:
                parent["body"] = newest.get("body", parent.get("body", ""))
                parent["edited_at"] = newest.get("created_at")
        # Filter out kind=edit items from the visible feed (they were merged into parents)
        return [it for it in items if it.get("kind") != "edit"]

    # ----- Append -----

    def append(self, project_id: str, item: dict[str, Any]) -> dict[str, Any]:
        """Append a feed item; fills in id/created_at/audit_status if missing."""
        item = dict(item)
        item.setdefault("id", _new_ulid())
        item.setdefault("created_at", utcnow_iso())
        item.setdefault("audit_status", "live")
        if "summary" not in item and "body" in item:
            item["summary"] = (item["body"] or "").splitlines()[0][:280] if item["body"] else ""
        # Required fields enforced at write time (fail-fast)
        for required in ("id", "kind", "author", "summary", "created_at", "audit_status"):
            if required not in item:
                raise ValueError(f"feed item missing required field: {required!r}")
        path = self.feed_path(project_id)
        with self._locked(path, "a", fcntl.LOCK_EX) as f:
            f.write(json.dumps(item) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return item

    # ----- Edit / retract (T072a, FR-032) -----

    def edit(self, project_id: str, item_id: str, new_body: str, editor: dict[str, Any]) -> dict[str, Any]:
        """Edit a feed item by appending a `kind=edit` item; preserve original in audit log."""
        items = self.read(project_id, include_audit_statuses={"live", "rejected", "superseded"})
        original = next((it for it in items if it.get("id") == item_id), None)
        if not original:
            raise KeyError(f"feed item {item_id!r} not found in project {project_id!r}")
        # write original body to .audit/edit-history.jsonl
        audit_path = self.audit_dir(project_id) / "edit-history.jsonl"
        with self._locked(audit_path, "a", fcntl.LOCK_EX) as f:
            f.write(json.dumps({
                "original_id": item_id,
                "original_body": original.get("body", ""),
                "edited_at": utcnow_iso(),
                "editor": editor,
            }) + "\n")
            f.flush()
            os.fsync(f.fileno())
        # append new kind=edit item
        edit_item: dict[str, Any] = {
            "kind": "edit",
            "author": editor,
            "summary": new_body.splitlines()[0][:280] if new_body else "",
            "body": new_body,
            "parent_id": item_id,
        }
        return self.append(project_id, edit_item)

    def retract(self, project_id: str, item_id: str, reason: str, editor: dict[str, Any]) -> None:
        """Mark a feed item as `audit_status=superseded` and log the reason."""
        path = self.feed_path(project_id)
        # Rewrite the JSONL with the targeted item flipped (atomic via tmp + rename, under lock)
        with self._locked(path, "a", fcntl.LOCK_EX) as _f:
            # Re-read under the exclusive lock for atomicity
            text = path.read_text()
            new_lines: list[str] = []
            found = False
            for line in text.splitlines():
                if not line.strip():
                    new_lines.append(line)
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    new_lines.append(line)
                    continue
                if obj.get("id") == item_id:
                    obj["audit_status"] = "superseded"
                    found = True
                new_lines.append(json.dumps(obj))
            if not found:
                raise KeyError(f"feed item {item_id!r} not found in project {project_id!r}")
            tmp = path.with_suffix(".tmp")
            tmp.write_text("\n".join(new_lines) + "\n")
            tmp.replace(path)
        # log
        audit_path = self.audit_dir(project_id) / "edit-history.jsonl"
        with self._locked(audit_path, "a", fcntl.LOCK_EX) as f:
            f.write(json.dumps({
                "retracted_id": item_id,
                "retracted_at": utcnow_iso(),
                "editor": editor,
                "reason": reason,
            }) + "\n")
            f.flush()
            os.fsync(f.fileno())

    # ----- Pack for dispatch (FR-026, FR-031) -----

    def pack_for_dispatch(self, project_id: str, *, budget_chars: int = 20000) -> PackedFeed:
        """Pack the feed into an agent's input context budget.

        Per research.md §1 packing rule:
            * walk newest-first, including full `body` per item until budget/2 used
            * then switch to summary-only
            * then truncate from the oldest end with a marker
        """
        snapshot_at = utcnow_iso()
        items = self.read(project_id)
        # newest first
        items_rev = list(reversed(items))

        included: list[dict[str, Any]] = []
        used = 0
        body_budget = budget_chars // 2
        for it in items_rev:
            body_cost = len(it.get("body") or "") + 200  # overhead per item
            summary_cost = len(it.get("summary") or "") + 200
            if used + body_cost <= body_budget:
                included.append(it)
                used += body_cost
            elif used + summary_cost <= budget_chars:
                shallow = dict(it)
                shallow.pop("body", None)
                included.append(shallow)
                used += summary_cost
            else:
                break

        # restore chronological order
        included.reverse()
        truncated = len(items) - len(included)
        marker = f"[truncated {truncated} earlier items]" if truncated > 0 else None
        return PackedFeed(
            items=included,
            truncated=truncated,
            feed_snapshot_at=snapshot_at,
            truncation_marker=marker,
        )

    # ----- Dispatch metadata ledger (FR-034 inputs) -----

    def record_dispatch(self, project_id: str, record: dict[str, Any]) -> None:
        """Append a dispatch metadata record to .audit/dispatches/<date>.jsonl."""
        date = time.strftime("%Y-%m-%d", time.gmtime())
        path = self.audit_dir(project_id) / "dispatches" / f"{date}.jsonl"
        record = dict(record)
        record.setdefault("dispatched_at", utcnow_iso())
        with self._locked(path, "a", fcntl.LOCK_EX) as f:
            f.write(json.dumps(record) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def record_rejected(self, project_id: str, contribution: dict[str, Any]) -> None:
        """Append a rubric-rejected contribution to .audit/rejected-contributions.jsonl."""
        path = self.audit_dir(project_id) / "rejected-contributions.jsonl"
        with self._locked(path, "a", fcntl.LOCK_EX) as f:
            f.write(json.dumps(contribution) + "\n")
            f.flush()
            os.fsync(f.fileno())
