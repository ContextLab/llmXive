"""Spec 020 follow-up — per-project speckit templates must match the shared ones.

speckit treats each project as a mini-repo with its own ``.specify/templates/``;
those per-project copies are a forked duplication of the shared
``.specify/templates/`` (Principle I). Rather than re-architect the scaffold's
mini-repo model, this test ENFORCES the invariant: every per-project
``*-template.md`` that also exists at the repo root MUST be byte-identical to the
shared template. So an edit to a shared template (e.g. the FR-006 deferral
guidance) that isn't propagated to the per-project copies fails the gate instead
of silently drifting.

Deterministic / offline.
"""

from __future__ import annotations

import pytest

from llmxive.config import repo_root as _repo_root

REPO = _repo_root()
_SHARED = REPO / ".specify" / "templates"


def _pairs() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    proj_root = REPO / "projects"
    if not proj_root.is_dir():
        return out
    for proj in sorted(proj_root.iterdir()):
        tdir = proj / ".specify" / "templates"
        if not tdir.is_dir():
            continue
        for shared in sorted(_SHARED.glob("*-template.md")):
            copy = tdir / shared.name
            if copy.exists():
                out.append((str(copy.relative_to(REPO)), shared.name))
    return out


_PAIRS = _pairs()


@pytest.mark.skipif(not _PAIRS, reason="no per-project template copies present")
@pytest.mark.parametrize("rel_copy,shared_name", _PAIRS, ids=[p[0] for p in _PAIRS])
def test_per_project_template_matches_shared(rel_copy: str, shared_name: str) -> None:
    copy_text = (REPO / rel_copy).read_text(encoding="utf-8")
    shared_text = (_SHARED / shared_name).read_text(encoding="utf-8")
    assert copy_text == shared_text, (
        f"{rel_copy} drifted from .specify/templates/{shared_name} — re-sync it "
        f"(per-project copies must mirror the shared template; Principle I / FR-006)"
    )
