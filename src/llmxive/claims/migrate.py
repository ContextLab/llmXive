"""T040 (spec 016, FR-019) — one-time migration: F-18 ``[UNVERIFIED: ...]``
markers → the unified ``[UNRESOLVED-CLAIM: ...]`` marker.

The claim-verification layer uses a single unified claim-marker that REPLACES
the F-18 ``[UNVERIFIED:`` marker (no backward-compat shim — early-stage, sole
developer; see ``clean-over-backcompat`` memory). This module performs the
single pass over existing projects' tracked artifacts that the cutover needs:

  * every residual ``[UNVERIFIED: <body>]`` in a tracked ``.md`` / ``.tex``
    document is rewritten to ``[UNRESOLVED-CLAIM: <body>]``; and
  * a registry entry is seeded for each, with status NOT_ENOUGH_INFO, so the
    claim layer re-resolves it on the next pass rather than silently dropping
    the (previously unverified) reference.

Run once::

    python -m llmxive.claims.migrate            # apply
    python -m llmxive.claims.migrate --dry-run  # list files that WOULD change
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from llmxive.claims.classify import classify
from llmxive.claims.gate import CLAIM_MARKER_PREFIX
from llmxive.claims.models import Claim, ClaimStatus, compute_claim_id
from llmxive.config import repo_root as _default_repo_root
from llmxive.state import claims as _claim_store

# Match a whole F-18 marker, capturing its body. Kept local (not imported from
# citation_guard) so the migration is self-contained and stable even after the
# F-18 marker constant is retired.
_F18_MARKER_RE = re.compile(r"\[UNVERIFIED:\s*(?P<body>[^\]]*?)\s*\]")

# Document trees that may carry persisted markers.
_DOC_DIRS = (
    "projects",
    "papers",
    "technical_design_documents",
    "implementation_plans",
    "reviews",
    "specs",
)
_DOC_SUFFIXES = (".md", ".tex")


def _extract_project_id(path: Path, repo_root: Path) -> str | None:
    """Best-effort project id from a repo-relative path (``PROJ-...`` segment)."""
    rel = path.relative_to(repo_root).as_posix()
    m = re.search(r"(PROJ-[A-Za-z0-9_-]+)", rel)
    return m.group(1) if m else None


def _iter_doc_files(repo_root: Path):
    for d in _DOC_DIRS:
        base = repo_root / d
        if not base.is_dir():
            continue
        for suffix in _DOC_SUFFIXES:
            yield from base.rglob(f"*{suffix}")


def migrate_unverified_markers(
    *, repo_root: Path | None = None, dry_run: bool = False
) -> list[Path]:
    """Rewrite ``[UNVERIFIED: ...]`` → ``[UNRESOLVED-CLAIM: ...]`` across tracked
    docs and seed a NOT_ENOUGH_INFO registry entry per migrated marker.

    Returns the list of files that changed (or, with ``dry_run=True``, that
    WOULD change — no file or registry is written).
    """
    root = repo_root or _default_repo_root()
    changed: list[Path] = []

    for path in _iter_doc_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        markers = list(_F18_MARKER_RE.finditer(text))
        if not markers:
            continue
        changed.append(path)
        if dry_run:
            continue

        new_text = _F18_MARKER_RE.sub(
            lambda m: f"{CLAIM_MARKER_PREFIX} {m.group('body').strip()}]", text
        )
        path.write_text(new_text, encoding="utf-8")

        project_id = _extract_project_id(path, root)
        if not project_id:
            continue
        rel = path.relative_to(root).as_posix()
        for m in markers:
            body = m.group("body").strip()
            kind = classify(body, body)
            claim = Claim(
                claim_id=compute_claim_id(kind, body, rel),
                kind=kind,
                raw_text=body,
                canonical=body,
                context=f"migrated from [UNVERIFIED] in {rel}",
                artifact_path=rel,
                source_type="external",
                status=ClaimStatus.NOT_ENOUGH_INFO,
                resolved_value=None,
                evidence={"note": "seeded by one-time F-18→unified marker migration"},
                resolver=None,
                attempts=0,
                updated_at="",
            )
            _claim_store.upsert(project_id, claim, repo_root=root)

    return changed


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    dry_run = "--dry-run" in argv
    changed = migrate_unverified_markers(dry_run=dry_run)
    verb = "would change" if dry_run else "migrated"
    print(f"{verb} {len(changed)} file(s):")
    for p in changed:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
