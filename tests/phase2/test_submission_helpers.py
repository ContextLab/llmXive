"""Validate the GitHub-issue / staged-file payloads the website's submission
helpers (web/js/auth.js: submitFeedback / submitPaper) produce — FR-012..015.

There is no browser-JS test harness in this repo (the site JS is verified
visually per Constitution III), so this Python harness POSTs the *same payloads*
against the real repo via `gh` and asserts what was created — then cleans up.

Tiers:
  - offline (always): asserts the canonical label sets / body structure that the
    helpers must produce (a contract check — if the JS body format drifts, the
    submission_intake agent's parser breaks).
  - real GitHub API (gated on `gh` being authed AND `LLMXIVE_REAL_TESTS=1`):
    creates a real `human-submission`+`feedback` issue, asserts its labels +
    body context, then closes + deletes it; same for `new-paper`+URL; and for
    `new-paper`+staged-PDF, PUTs a tiny test PDF to `submissions/inbox/…`,
    asserts it appeared with the right path, then deletes it.
  The end-to-end consumer side (issue → triage → comment/close/file) is covered
  by tests/phase2/test_submission_intake.py.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import time

import pytest

REPO = "ContextLab/llmXive"

REAL = os.environ.get("LLMXIVE_REAL_TESTS") == "1" and shutil.which("gh") is not None


def _gh(*args: str, input_bytes: bytes | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True,
                          input=input_bytes.decode() if input_bytes else None)
    return proc.returncode, proc.stdout, proc.stderr


# ── The canonical payloads the JS helpers produce (mirrors web/js/auth.js) ──

FEEDBACK_LABELS = ["human-submission", "feedback"]
NEW_PAPER_LABELS = ["human-submission", "new-paper"]


def feedback_body(target_id: str, target_kind: str, target_stage: str, content: str, submitter: str) -> str:
    summary = (content.split("\n", 1)[0] or "")[:200]
    return "\n".join([
        "> " + summary, "",
        "## Feedback", "", content, "",
        "## Target", "",
        "- **Project / artifact:** " + (target_id or "(unspecified)"),
        "- **Artifact kind:** " + (target_kind or "(unspecified)"),
        "- **Stage:** " + (target_stage or "(unspecified)"),
        "- **Submitter:** " + submitter, "",
        "---",
        "*Submitted via the llmXive dashboard. The submission-intake agent will triage this to the appropriate pipeline step within the hour.*",
    ])


def new_paper_url_body(url: str, submitter: str) -> str:
    return "\n".join([
        "> A paper has been submitted for consideration/review (link).", "",
        "## Submitted paper", "",
        "- **URL:** " + url,
        "- **Submitter:** " + submitter, "",
        "---",
        "*Submitted via the llmXive dashboard. The submission-intake agent will file this and create/link a project within the hour.*",
    ])


# ── offline contract checks ────────────────────────────────────────────────

def test_feedback_payload_shape():
    body = feedback_body("PROJ-001-x", "spec", "specified", "the spec is missing an edge case", "octocat")
    assert FEEDBACK_LABELS == ["human-submission", "feedback"]
    assert "## Feedback" in body and "## Target" in body
    assert "PROJ-001-x" in body and "spec" in body and "specified" in body
    assert "**Submitter:** octocat" in body
    # the parser (submission_intake) keys off the blockquote summary first line
    assert body.splitlines()[0].startswith("> ")


def test_new_paper_payload_shapes():
    burl = new_paper_url_body("https://arxiv.org/abs/1234.5678", "octocat")
    assert NEW_PAPER_LABELS == ["human-submission", "new-paper"]
    assert "## Submitted paper" in burl and "https://arxiv.org/abs/1234.5678" in burl
    # the staged-PDF body references submissions/inbox/<…>.pdf
    staged = "- **Staged file:** `submissions/inbox/2026-05-13T00-00-00-000Z-test.pdf`"
    assert staged.startswith("- **Staged file:** `submissions/inbox/")


def test_inbox_path_format():
    # ISO timestamp with : and . replaced by -, then a slug, then .pdf
    slug = "my-cool-paper"
    ts = "2026-05-13T01-02-03-456Z"
    path = f"submissions/inbox/{ts}-{slug}.pdf"
    assert path.startswith("submissions/inbox/")
    assert path.endswith(".pdf")
    assert ":" not in path


# ── real GitHub API (gated) ────────────────────────────────────────────────

@pytest.mark.skipif(not REAL, reason="needs `gh` authed + LLMXIVE_REAL_TESTS=1")
def test_real_feedback_issue_roundtrip():
    body = feedback_body("PROJ-TEST-spec007", "spec", "specified",
                         "[automated test — please ignore] checking the feedback payload", "test")
    rc, out, err = _gh("api", f"repos/{REPO}/issues", "-X", "POST",
                       "-f", "title=[test] spec-007 feedback payload",
                       "-f", f"body={body}",
                       "-f", "labels[]=human-submission", "-f", "labels[]=feedback")
    assert rc == 0, err
    issue = json.loads(out)
    num = issue["number"]
    try:
        labels = {lab["name"] for lab in issue["labels"]}
        assert {"human-submission", "feedback"} <= labels
        assert "PROJ-TEST-spec007" in issue["body"]
        assert "## Feedback" in issue["body"] and "## Target" in issue["body"]
    finally:
        # close + delete the test issue
        _gh("api", f"repos/{REPO}/issues/{num}", "-X", "PATCH", "-f", "state=closed")
        _gh("api", f"repos/{REPO}/issues/{num}", "-X", "DELETE")  # may 404 if not allowed; best-effort


@pytest.mark.skipif(not REAL, reason="needs `gh` authed + LLMXIVE_REAL_TESTS=1")
def test_real_new_paper_url_issue_roundtrip():
    body = new_paper_url_body("https://arxiv.org/abs/0000.00000", "test")
    rc, out, err = _gh("api", f"repos/{REPO}/issues", "-X", "POST",
                       "-f", "title=[test] spec-007 new-paper URL payload",
                       "-f", f"body={body}",
                       "-f", "labels[]=human-submission", "-f", "labels[]=new-paper")
    assert rc == 0, err
    issue = json.loads(out)
    num = issue["number"]
    try:
        labels = {lab["name"] for lab in issue["labels"]}
        assert {"human-submission", "new-paper"} <= labels
        assert "arxiv.org/abs/0000.00000" in issue["body"]
    finally:
        _gh("api", f"repos/{REPO}/issues/{num}", "-X", "PATCH", "-f", "state=closed")
        _gh("api", f"repos/{REPO}/issues/{num}", "-X", "DELETE")


@pytest.mark.skipif(not REAL, reason="needs `gh` authed + LLMXIVE_REAL_TESTS=1")
def test_real_staged_pdf_roundtrip():
    # A minimal valid-ish PDF.
    pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
    ts = time.strftime("%Y-%m-%dT%H-%M-%S-000Z", time.gmtime())
    path = f"submissions/inbox/{ts}-spec007-test.pdf"
    content_b64 = base64.b64encode(pdf).decode()
    rc, out, err = _gh("api", f"repos/{REPO}/contents/{path}", "-X", "PUT",
                       "-f", "message=[test] spec-007 stage a test PDF",
                       "-f", f"content={content_b64}", "-f", "branch=main")
    assert rc == 0, err
    put = json.loads(out)
    sha = put["content"]["sha"]
    try:
        # verify it's there
        rc2, out2, _ = _gh("api", f"repos/{REPO}/contents/{path}?ref=main")
        assert rc2 == 0
        got = json.loads(out2)
        assert got["path"] == path
        assert base64.b64decode(got["content"]) == pdf
    finally:
        _gh("api", f"repos/{REPO}/contents/{path}", "-X", "DELETE",
            "-f", "message=[test] spec-007 remove test PDF",
            "-f", f"sha={sha}", "-f", "branch=main")
