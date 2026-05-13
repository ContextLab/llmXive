"""Tests for the submission_intake maintenance agent (FR-020, FR-021).

Offline (always):
  - parsing of feedback / new-paper issue bodies
  - subtype detection (malformed labels → None)
  - process_submission_issue on a malformed-labels issue → `failed`, no close,
    a comment posted (using a fake `gh`)
  - an unparseable LLM verdict → `failed`, no close (using a fake `gh` + a
    monkeypatched chat_with_fallback)
  - idempotency: a closed issue → `skipped`
  - the registry entry validates

Gated:
  - real GitHub API (LLMXIVE_REAL_TESTS=1 + `gh` authed): create a real
    feedback / new-paper issue, run the agent, assert comment + close, clean up
  - real-LLM triage smoke (LLMXIVE_REAL_TESTS=1 + DARTMOUTH_CHAT_API_KEY): the
    verdict shape for a few representative feedback messages
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from llmxive.agents import registry as registry_loader
from llmxive.agents.submission_intake import (
    IntakeResult,
    _parse_feedback_body,
    _parse_new_paper_body,
    _subtype,
    process_submission_issue,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL = os.environ.get("LLMXIVE_REAL_TESTS") == "1" and shutil.which("gh") is not None
REAL_LLM = os.environ.get("LLMXIVE_REAL_TESTS") == "1" and bool(os.environ.get("DARTMOUTH_CHAT_API_KEY"))


# ── a recording fake `gh` ──────────────────────────────────────────────────

class FakeGh:
    """Records calls; returns canned JSON for the few endpoints we touch."""

    def __init__(self):
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, *args: str) -> tuple[int, str, str]:
        self.calls.append(args)
        # POST a comment → return a fake comment object.
        if len(args) >= 2 and args[0] == "api" and "/comments" in args[1] and "-X" in args and args[args.index("-X") + 1] == "POST":
            return 0, json.dumps({"html_url": "https://github.com/x/y/issues/1#issuecomment-99"}), ""
        # PATCH (close) → empty success.
        if len(args) >= 2 and args[0] == "api" and "-X" in args and args[args.index("-X") + 1] == "PATCH":
            return 0, "{}", ""
        # default: success, empty.
        return 0, "{}", ""

    def commented(self) -> bool:
        return any(("/comments" in c[1] if len(c) > 1 else False) for c in self.calls)

    def closed(self) -> bool:
        return any(("-X" in c and c[c.index("-X") + 1] == "PATCH" and "state=closed" in c) for c in self.calls)


# ── offline: parsing + subtype ─────────────────────────────────────────────

def test_subtype_detection():
    assert _subtype({"labels": [{"name": "human-submission"}, {"name": "feedback"}]}) == "feedback"
    assert _subtype({"labels": [{"name": "human-submission"}, {"name": "new-paper"}]}) == "new-paper"
    # malformed: missing human-submission
    assert _subtype({"labels": [{"name": "feedback"}]}) is None
    # malformed: both sub-types
    assert _subtype({"labels": [{"name": "human-submission"}, {"name": "feedback"}, {"name": "new-paper"}]}) is None
    # malformed: neither sub-type
    assert _subtype({"labels": [{"name": "human-submission"}]}) is None


def test_parse_feedback_body():
    body = (
        "> the spec is missing an edge case\n\n"
        "## Feedback\n\nthe spec for PROJ-X is missing an edge case about empty inputs\n\n"
        "## Target\n\n"
        "- **Project / artifact:** PROJ-001-x\n"
        "- **Artifact kind:** spec\n"
        "- **Stage:** specified\n"
        "- **Submitter:** octocat\n\n"
        "---\n*footer*\n"
    )
    p = _parse_feedback_body(body)
    assert p["target_id"] == "PROJ-001-x"
    assert p["target_kind"] == "spec"
    assert p["target_stage"] == "specified"
    assert p["submitter"] == "octocat"
    assert "empty inputs" in p["content"]


def test_parse_new_paper_body_url_and_staged():
    burl = "## Submitted paper\n\n- **URL:** https://arxiv.org/abs/1234.5678\n- **Submitter:** octocat\n"
    pu = _parse_new_paper_body(burl)
    assert pu["url"] == "https://arxiv.org/abs/1234.5678"
    assert pu["staged_file"] == ""
    bstaged = "## Submitted paper\n\n- **Staged file:** `submissions/inbox/2026-05-13T00-00-00-000Z-paper.pdf`\n- **Submitter:** octocat\n"
    ps = _parse_new_paper_body(bstaged)
    assert ps["staged_file"] == "submissions/inbox/2026-05-13T00-00-00-000Z-paper.pdf"
    assert ps["url"] == ""


# ── offline: process_submission_issue edge cases ───────────────────────────

def test_malformed_labels_fails_without_closing():
    gh = FakeGh()
    issue = {"number": 42, "state": "open", "labels": [{"name": "human-submission"}], "body": "x", "user": {"login": "octocat"}}
    res = process_submission_issue(issue, repo_root=REPO_ROOT, gh=gh)
    assert isinstance(res, IntakeResult)
    assert res.status == "failed"
    assert gh.commented()       # an explanatory comment was posted
    assert not gh.closed()      # the issue stays open


def test_closed_issue_is_skipped():
    gh = FakeGh()
    issue = {"number": 7, "state": "closed", "labels": [{"name": "human-submission"}, {"name": "feedback"}], "body": "x"}
    res = process_submission_issue(issue, repo_root=REPO_ROOT, gh=gh)
    assert res.status == "skipped"
    assert not gh.calls         # no API calls for an already-closed issue


def test_unparseable_llm_verdict_fails_without_closing(monkeypatch, tmp_path):
    # Make the LLM return junk → the agent's _triage_feedback_llm raises → failed.
    from llmxive.agents import submission_intake as si

    class _Resp:
        text = "I'm not going to give you JSON, sorry."
        model = "x"
        backend = "x"

    monkeypatch.setattr(si, "chat_with_fallback", lambda *a, **k: _Resp())
    # Build an isolated repo so _project_exists / project creation don't touch
    # the real state tree. The feedback names no target, so target_context is
    # "(no target named)" and the LLM is still called.
    (tmp_path / "projects").mkdir()
    (tmp_path / "state" / "projects").mkdir(parents=True)
    gh = FakeGh()
    issue = {
        "number": 99, "state": "open",
        "labels": [{"name": "human-submission"}, {"name": "feedback"}],
        "body": "> hi\n\n## Feedback\n\nyou should look into something\n\n## Target\n\n- **Project / artifact:** (unspecified)\n- **Submitter:** octocat\n",
        "user": {"login": "octocat"},
    }
    res = process_submission_issue(issue, repo_root=tmp_path, gh=gh)
    assert res.status == "failed"
    assert gh.commented()
    assert not gh.closed()


def test_create_project_via_acknowledge_path_fallback(monkeypatch, tmp_path):
    # An LLM verdict of "acknowledge" → the agent comments + closes, returns ok.
    from llmxive.agents import submission_intake as si

    class _Resp:
        text = '{"target": null, "action": "acknowledge", "rationale": "a non-actionable remark"}'
        model = "x"
        backend = "x"

    monkeypatch.setattr(si, "chat_with_fallback", lambda *a, **k: _Resp())
    (tmp_path / "projects").mkdir()
    (tmp_path / "state" / "projects").mkdir(parents=True)
    gh = FakeGh()
    issue = {
        "number": 100, "state": "open",
        "labels": [{"name": "human-submission"}, {"name": "feedback"}],
        "body": "> nice\n\n## Feedback\n\nnice work!\n\n## Target\n\n- **Submitter:** octocat\n",
        "user": {"login": "octocat"},
    }
    res = process_submission_issue(issue, repo_root=tmp_path, gh=gh)
    assert res.status == "ok"
    assert res.action == "acknowledged"
    assert gh.commented() and gh.closed()


# ── offline: registry entry ────────────────────────────────────────────────

def test_registry_entry_validates():
    registry_loader.load(repo_root=REPO_ROOT)  # validates the schema
    e = registry_loader.get("submission_intake", repo_root=REPO_ROOT)
    assert e.name == "submission_intake"
    assert e.prompt_version == "1.0.0"
    assert (REPO_ROOT / e.prompt_path).exists()
    assert e.wall_clock_budget_seconds == 300
    assert e.paid_opt_in is False


# ── gated: real GitHub API roundtrip ───────────────────────────────────────

@pytest.mark.skipif(not REAL, reason="needs `gh` authed + LLMXIVE_REAL_TESTS=1")
def test_real_acknowledge_roundtrip(monkeypatch):
    """Create a real feedback issue, run the agent with a stubbed LLM verdict
    of 'acknowledge', assert it commented + closed, then delete the issue."""
    from llmxive.agents import submission_intake as si

    class _Resp:
        text = '{"target": null, "action": "acknowledge", "rationale": "automated test"}'
        model = "x"
        backend = "x"

    monkeypatch.setattr(si, "chat_with_fallback", lambda *a, **k: _Resp())

    import subprocess
    def _gh(*args: str) -> tuple[int, str, str]:
        p = subprocess.run(["gh", *args], capture_output=True, text=True)
        return p.returncode, p.stdout, p.stderr

    REPO = "ContextLab/llmXive"
    body = ("> automated test — please ignore\n\n## Feedback\n\n[automated test] checking intake\n\n"
            "## Target\n\n- **Project / artifact:** (unspecified)\n- **Submitter:** test\n")
    rc, out, err = _gh("api", f"repos/{REPO}/issues", "-X", "POST",
                       "-f", "title=[test] spec-007 intake roundtrip",
                       "-f", f"body={body}",
                       "-f", "labels[]=human-submission", "-f", "labels[]=feedback")
    assert rc == 0, err
    num = json.loads(out)["number"]
    try:
        # Refetch (need the full issue object the agent expects).
        _, out2, _ = _gh("api", f"repos/{REPO}/issues/{num}")
        issue = json.loads(out2)
        res = process_submission_issue(issue, repo_root=REPO_ROOT, gh=_gh)
        assert res.status == "ok" and res.action == "acknowledged"
        # confirm it's closed
        _, out3, _ = _gh("api", f"repos/{REPO}/issues/{num}")
        assert json.loads(out3)["state"] == "closed"
    finally:
        _gh("api", f"repos/{REPO}/issues/{num}", "-X", "DELETE")  # best-effort


# ── gated: real-LLM triage smoke ───────────────────────────────────────────

@pytest.mark.skipif(not REAL_LLM, reason="needs DARTMOUTH_CHAT_API_KEY + LLMXIVE_REAL_TESTS=1")
@pytest.mark.parametrize("feedback,expect_action_prefix", [
    ("the spec for PROJ-X is missing an edge case about empty inputs", "route-to-"),
    ("you should look into using diffusion models for protein structure prediction", "create-project"),
    ("nice work on the dashboard, looks great!", "acknowledge"),
])
def test_real_llm_triage_smoke(feedback, expect_action_prefix):
    from llmxive.agents import submission_intake as si
    entry = registry_loader.get("submission_intake", repo_root=REPO_ROOT)
    target_context = ("Project PROJ-X — “Test project” — current stage: specified."
                      if "PROJ-X" in feedback else "(no target named)")
    verdict = si._triage_feedback_llm(entry, feedback=feedback, target_context=target_context, repo_root=REPO_ROOT)
    assert verdict["action"].startswith(expect_action_prefix) or verdict["action"] == expect_action_prefix
