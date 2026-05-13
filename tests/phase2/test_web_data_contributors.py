"""Real-fixture regression tests for the Contributors list (FR-007, FR-008).

Builds the website payload from the actual repo state (no mocks — Constitution
III) and asserts the contributor rows are models / GitHub usernames /
"unattributed", never pipeline-agent role names, with correct counts.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from llmxive.web_data import build_payload

REPO_ROOT = Path(__file__).resolve().parents[2]

# A non-exhaustive set of known pipeline agent/prompt role names. A
# contributor row's `name` must never be one of these.
KNOWN_ROLE_NAMES = {
    "brainstorm", "flesh_out", "research_question_validator", "idea_selector",
    "project_initializer", "librarian", "specifier", "clarifier", "planner",
    "tasker", "implementer", "research_reviewer", "reference_validator",
    "paper_initializer", "paper_specifier", "paper_clarifier", "paper_planner",
    "paper_tasker", "paper_implementer", "paper_writing", "paper_figure_generation",
    "paper_statistics", "proofreader", "latex_build", "latex_fix", "paper_reviewer",
    "status_reporter", "repository_hygiene", "task_atomizer", "task_joiner",
    "citation_validator", "submission_intake", "reviewer", "agent",
    "figure_generation", "statistician",
}
ROLE_PREFIXES = ("research_reviewer", "paper_reviewer", "paper_", "latex_")


@pytest.fixture(scope="module")
def payload() -> dict:
    return build_payload(REPO_ROOT)


def _looks_like_role(name: str) -> bool:
    n = (name or "").strip()
    if n in KNOWN_ROLE_NAMES:
        return True
    nl = n.lower()
    return any(nl.startswith(p) for p in ROLE_PREFIXES)


def test_contributors_present(payload):
    assert isinstance(payload.get("contributors"), list)
    assert payload["contributors"], "expected at least one contributor in the repo"


def test_no_contributor_is_a_prompt_or_agent_name(payload):
    bad = [c["name"] for c in payload["contributors"]
           if c.get("kind") in ("llm", "human") and _looks_like_role(c["name"])]
    assert not bad, f"contributor rows must be models/usernames, not roles: {bad}"


def test_every_contributor_has_a_valid_kind(payload):
    for c in payload["contributors"]:
        assert c.get("kind") in ("llm", "human", "unattributed"), c


def test_unattributed_is_a_single_bucket(payload):
    unattr = [c for c in payload["contributors"] if c.get("kind") == "unattributed"]
    assert len(unattr) <= 1, "there should be at most one 'unattributed' row"
    for c in unattr:
        assert c["name"] == "unattributed"


def test_contribution_counts_are_positive_ints(payload):
    for c in payload["contributors"]:
        n = c.get("contribution_count")
        assert isinstance(n, int) and n >= 1, c


def test_aggregates_match_contributor_list(payload):
    contribs = payload["contributors"]
    agg = payload["aggregates"]
    assert agg["total_contributors"] == len(contribs)
    assert agg["total_contributions"] == sum(c["contribution_count"] for c in contribs)
    assert agg["human_contributors"] == sum(1 for c in contribs if c["kind"] == "human")
    assert agg["ai_contributors"] == sum(1 for c in contribs if c["kind"] == "llm")


def test_at_least_one_contributor_count_is_independently_reproducible(payload):
    """For the top contributor, recount run-log success entries for that model
    and assert the contributor count is at least that many (it also includes
    review + submitter contributions, so it can only be ≥)."""
    import json

    from llmxive.web_data import _normalize_model_name

    contribs = sorted(payload["contributors"], key=lambda c: -c["contribution_count"])
    assert contribs
    top = contribs[0]
    if top["kind"] != "llm":
        pytest.skip("top contributor is not an LLM model")
    runlog_root = REPO_ROOT / "state" / "run-log"
    if not runlog_root.is_dir():
        pytest.skip("no run-log in repo")
    n = 0
    for month_dir in runlog_root.iterdir():
        if not month_dir.is_dir() or month_dir.name.startswith("."):
            continue
        for jsonl in month_dir.glob("*.jsonl"):
            for line in jsonl.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if e.get("outcome") != "success":
                    continue
                model = (e.get("model_name") or "").strip()
                if model and _normalize_model_name(model) == top["name"]:
                    n += 1
    assert top["contribution_count"] >= n, (top, n)
