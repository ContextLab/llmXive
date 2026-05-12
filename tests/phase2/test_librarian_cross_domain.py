"""Cross-domain coverage tests for the librarian (spec 005 / T027-T031 / US4).

Per ``contracts/cross-domain-coverage.md``: invokes the librarian on
the most-recently-brainstormed project per default field (8 fields
total). Each invocation must produce ``outcome ∈ {success,
success_after_expansion, exhausted}`` (NOT failed for non-transient
reasons) and ``len(verified_citations) >= 1``.

Per Constitution Principle III: real Semantic Scholar + arXiv + PDF
downloads. Per FR-002: deterministic (cache-backed) — re-running this
suite within the cache TTL window is a fast no-op.

Each test writes a CrossDomainTestRow record to
``/tmp/cross-domain-results-<field>.json`` for inclusion in the
diagnostic report's § 4 table.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import pytest
import yaml

from llmxive.agents import registry
from llmxive.agents.librarian import LibrarianAgent
from llmxive.credentials import load_dartmouth_key, load_semantic_scholar_key

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_PROJECTS = REPO_ROOT / "state" / "projects"

HAS_DM_KEY = bool(load_dartmouth_key(prompt_if_missing=False))
HAS_SS_KEY = bool(load_semantic_scholar_key(prompt_if_missing=False))

both_keys_required = pytest.mark.skipif(
    not (HAS_DM_KEY and HAS_SS_KEY),
    reason="Cross-domain US4 needs DARTMOUTH_CHAT_API_KEY + SEMANTIC_SCHOLAR_API_KEY",
)

DEFAULT_FIELDS = [
    "biology",
    "chemistry",
    "computer science",
    "materials science",
    "neuroscience",
    "physics",
    "psychology",
    "statistics",
]

TARGET_N = 5  # spec.md SC-002


def _pick_most_recent_per_field(field: str) -> str | None:
    """Return project_id of the most-recently-brainstormed project in
    ``field`` (per research.md Decision 8). Excludes iter siblings.
    """
    candidates: list[tuple[str, str]] = []
    for yf in STATE_PROJECTS.glob("PROJ-*.yaml"):
        if "iter" in yf.name:
            continue
        try:
            data = yaml.safe_load(yf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        if (data.get("field") or "").lower() != field.lower():
            continue
        stage = (data.get("current_stage") or "").lower()
        if stage not in {
            "brainstormed",
            "flesh_out_in_progress",
            "flesh_out_complete",
            "validated",
            "project_initialized",
        }:
            continue
        candidates.append((data["id"], data.get("created_at") or ""))
    if not candidates:
        return None
    candidates.sort(key=lambda r: r[1], reverse=True)
    return candidates[0][0]


_RESEARCH_QUESTION_HEADER_RE = re.compile(
    r"^##\s*Research\s*question\s*$", re.MULTILINE | re.IGNORECASE
)
_NEXT_HEADER_RE = re.compile(r"^##\s+", re.MULTILINE)


def _derive_sample_term(project_id: str) -> tuple[str, str | None]:
    """Extract the sample search term + idea-body excerpt from a project's
    idea/<slug>.md.

    Returns (sample_term, idea_body_excerpt). The sample term is the
    first sentence of the ``## Research question`` section, or the
    project title if that section is absent.
    """
    project_dir = REPO_ROOT / "projects" / project_id
    idea_dir = project_dir / "idea"
    if not idea_dir.is_dir():
        return (project_id, None)
    # Idea files are slug-named .md (per spec 003 convention).
    md_files = [
        p for p in idea_dir.glob("*.md")
        if p.name not in {"research_question_validation.md", "citation_resolution.json"}
    ]
    if not md_files:
        return (project_id, None)
    text = md_files[0].read_text(encoding="utf-8")

    body_excerpt = text[:1000] if text else None

    m = _RESEARCH_QUESTION_HEADER_RE.search(text)
    if m:
        rest = text[m.end():]
        next_m = _NEXT_HEADER_RE.search(rest)
        rq_section = rest[: next_m.start()] if next_m else rest
        rq_section = rq_section.strip()
        if rq_section:
            # First sentence (split on . ! ? followed by whitespace).
            first = re.split(r"(?<=[.!?])\s+", rq_section, maxsplit=1)[0]
            first = first.strip().strip("?!.")
            if first:
                return (first[:500], body_excerpt)

    # Fallback: project title from state YAML.
    state_path = STATE_PROJECTS / f"{project_id}.yaml"
    if state_path.is_file():
        data = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
        return (str(data.get("title") or project_id), body_excerpt)
    return (project_id, body_excerpt)


@pytest.fixture(scope="module")
def shared_arxiv_client():
    """Module-scoped ArxivClient so its rate-limiting state persists
    across all 8 cross-domain test invocations, preventing the burst-
    load 429 cascade we saw in the first US4 run."""
    from llmxive.librarian.search import ArxivClient
    return ArxivClient(min_interval_seconds=5.0)


@pytest.fixture(scope="module")
def shared_ss_client():
    from llmxive.librarian.search import SemanticScholarClient
    return SemanticScholarClient()


@both_keys_required
@pytest.mark.parametrize("field", DEFAULT_FIELDS)
def test_librarian_field_coverage(field: str, shared_arxiv_client, shared_ss_client):
    """Per US4: librarian works on the most-recently-brainstormed project
    in each default field. Outcome != "failed"; len(verified) >= 1.
    """
    project_id = _pick_most_recent_per_field(field)
    if project_id is None:
        pytest.skip(f"no brainstormed projects found for field={field}")

    sample_term, idea_body_excerpt = _derive_sample_term(project_id)
    librarian = LibrarianAgent(registry.get("librarian"))

    result = librarian.invoke(
        term=sample_term,
        field=field,
        idea_body_excerpt=idea_body_excerpt,
        target_n=TARGET_N,
        repo_root=REPO_ROOT,
        ss_client=shared_ss_client,
        arxiv_client=shared_arxiv_client,
    )
    d = result.to_dict()

    # Persist a CrossDomainTestRow record for the diagnostic report.
    out_path = Path(tempfile.gettempdir()) / f"cross-domain-results-{field.replace(' ', '_')}.json"
    row = {
        "field": field,
        "project_id": project_id,
        "sample_term": sample_term,
        "outcome": d["outcome"],
        "verified_count": len(d["verified_citations"]),
        "expansion_fired": (
            d["expansion"] is not None
            or d["outcome"] in {"success_after_expansion", "exhausted"}
        ),
        "pdf_sample_size": d["pdf_sample"]["sampled_count"],
        "first_verified_pointer": (
            d["verified_citations"][0]["primary_pointer"]
            if d["verified_citations"]
            else None
        ),
        "first_verified_title": (
            d["verified_citations"][0]["bibliographic_info"]["title"]
            if d["verified_citations"]
            else None
        ),
        "duration_seconds": d["duration_seconds"],
        "cache_status": d["cache_status"],
    }
    out_path.write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding="utf-8")

    # Assertions per US4 acceptance scenario 1.
    assert d["outcome"] != "failed", (
        f"field={field}: librarian outcome was 'failed' (non-transient). "
        f"sample_term={sample_term!r}; failure_reason={d.get('failure_reason')}"
    )
    assert d["outcome"] in {"success", "success_after_expansion", "exhausted"}
    assert len(d["verified_citations"]) >= 1, (
        f"field={field}: zero verified citations returned. "
        f"sample_term={sample_term!r}; outcome={d['outcome']}"
    )
