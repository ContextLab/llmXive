"""Classify an ingested paper as code-included vs no-code (spec 024).

The decision discriminator is **runnable code** (the user's rule: "if code IS
included … back-fill spec/plan/tasks; if NO code is included … convert into a
brainstormed idea"). Intake already parses the paper's .tex for repo links into
``paper/metadata.json::code`` (``submission_intake._parse_tex_external_resources``);
we read that — the single source of truth — and decide whether at least one is a
plausibly clonable git repository.

Liveness of the repo is NOT verified here: :mod:`branch_code` attempts the real
``git submodule add`` and falls back to the no-code branch if the clone fails, so
classification stays cheap and deterministic (no network) and "code" means
"there is a repo URL worth trying".
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# Hosts whose URLs are git-clonable repositories. A bare ``huggingface.co/<org>/<repo>``
# is clonable too, but a HF *dataset*/*paper* page is not code — excluded below.
_REPO_HOST_RE = re.compile(
    r"^https?://(?:www\.)?(github\.com|gitlab\.com|bitbucket\.org|codeberg\.org)/"
    r"([^/\s]+)/([^/\s#?]+)",
    re.IGNORECASE,
)
# Trailing path noise that points INTO a repo rather than at its clone root.
_REPO_SUBPATH_RE = re.compile(r"/(?:blob|tree|commit|releases|issues|pull|raw|wiki)/.*$", re.IGNORECASE)


def normalize_repo_url(url: str) -> str | None:
    """Return the clone-root ``https://host/owner/repo`` for a code-host URL,
    or ``None`` if ``url`` is not a recognizable git repository link.

    Strips ``/blob/…``, ``/tree/…`` sub-paths and a trailing ``.git`` / slash so
    the same repo linked three different ways normalizes to one clone target.
    """
    if not url:
        return None
    url = url.strip().rstrip(").,;>\"'")
    m = _REPO_HOST_RE.match(url)
    if not m:
        return None
    host, owner, repo = m.group(1), m.group(2), m.group(3)
    repo = re.sub(r"\.git$", "", repo)
    # First-segment values that are GitHub site sections, not a repo owner.
    if not owner or not repo or owner.lower() in {
        "orgs", "sponsors", "marketplace", "about", "settings",
        "features", "topics", "collections", "apps", "notifications",
    }:
        return None
    return f"https://{host}/{owner}/{repo}"


def code_repos(metadata: dict) -> list[str]:
    """De-duplicated, normalized clone-root URLs from ``metadata['code']``."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in metadata.get("code", []) or []:
        norm = normalize_repo_url(str(raw))
        if norm and norm.lower() not in seen:
            seen.add(norm.lower())
            out.append(norm)
    return out


def load_metadata(project_dir: Path) -> dict:
    """Read ``paper/metadata.json``; ``{}`` when absent/unparseable."""
    meta = project_dir / "paper" / "metadata.json"
    if not meta.is_file():
        return {}
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def classify_paper(project_dir: Path) -> str:
    """Return ``"code"`` if the ingested paper ships a clonable code repo, else
    ``"nocode"``. Pure + deterministic (reads only ``paper/metadata.json``)."""
    return "code" if code_repos(load_metadata(project_dir)) else "nocode"
