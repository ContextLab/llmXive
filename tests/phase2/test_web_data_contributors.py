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


def test_contribution_counts_are_distinct_artifacts_not_runlog_lines(payload):
    """FR-008: `contribution_count` MUST equal the count of *distinct artifacts*
    a contributor produced, not the number of run-log lines (a model that
    re-ran an agent N times on a project produced one logical contribution, not
    N). For the top LLM contributor, independently recount:
      distinct (model, project_id, agent_name) run-log tuples
      + distinct review files with model_name == this model
      + distinct project ideas submitted by this model (idea front-matter)
    and assert the contributor count equals that — and is strictly less than
    the raw run-log line count (which proves dedup actually happened)."""
    import json

    import yaml

    from llmxive.web_data import _normalize_model_name

    contribs = sorted(payload["contributors"], key=lambda c: -c["contribution_count"])
    assert contribs
    top = contribs[0]
    if top["kind"] != "llm":
        pytest.skip("top contributor is not an LLM model")
    name = top["name"]

    # 1. distinct (model, project, agent) run-log tuples + raw line count.
    runlog_root = REPO_ROOT / "state" / "run-log"
    distinct_runlog: set[tuple[str, str, str]] = set()
    raw_lines = 0
    if runlog_root.is_dir():
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
                    m = (e.get("model_name") or "").strip()
                    if not m or _normalize_model_name(m) != name:
                        continue
                    raw_lines += 1
                    distinct_runlog.add((name, e.get("project_id") or "", (e.get("agent_name") or "").strip()))

    # 2. distinct review files attributing this model.
    review_files = 0
    proj_root = REPO_ROOT / "projects"
    if proj_root.is_dir():
        for pdir in proj_root.glob("PROJ-*"):
            for sub in ("reviews/research", "paper/reviews", "reviews/paper"):
                rdir = pdir / sub
                if not rdir.is_dir():
                    continue
                for md in rdir.rglob("*.md"):
                    text = md.read_text(encoding="utf-8", errors="ignore")
                    if not text.startswith("---"):
                        continue
                    try:
                        fm = yaml.safe_load(text[3:text.index("---", 3)]) or {}
                    except (ValueError, yaml.YAMLError):
                        continue
                    rm = str(fm.get("model_name", "")).strip()
                    rk = str(fm.get("reviewer_kind", "")).strip()
                    if rk != "human" and rm and _normalize_model_name(rm) == name:
                        review_files += 1

    # 3. distinct project ideas submitted by this model (idea front-matter).
    submitted_ideas = 0
    if proj_root.is_dir():
        for pdir in proj_root.glob("PROJ-*"):
            for md in (pdir / "idea").glob("*.md") if (pdir / "idea").is_dir() else []:
                text = md.read_text(encoding="utf-8", errors="replace")
                if not text.startswith("---"):
                    continue
                try:
                    fm = yaml.safe_load(text[3:text.index("---", 3)]) or {}
                except (ValueError, yaml.YAMLError):
                    continue
                sub = str(fm.get("submitter") or fm.get("submitted_by") or fm.get("author") or "").strip()
                if sub and _normalize_model_name(sub) == name:
                    submitted_ideas += 1

    expected = len(distinct_runlog) + review_files + submitted_ideas
    assert top["contribution_count"] == expected, (name, top["contribution_count"], expected,
                                                   len(distinct_runlog), review_files, submitted_ideas)
    # And: the displayed count must be < the raw run-log line count when there
    # were repeated invocations — proves we deduped (this is the #115-item-4 bug).
    if raw_lines > len(distinct_runlog):
        assert top["contribution_count"] < raw_lines, (top["contribution_count"], raw_lines)
