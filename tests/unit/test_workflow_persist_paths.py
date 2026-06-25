"""Guard: every scheduled lane that runs pipeline passes persists ALL
artifact roots (FR-003, spec 023).

Live failure this prevents (issue #303 / research.md R2): revision
work-specs are written under ``specs/auto-revisions/...`` but the lanes'
persist steps enumerated only ``state/ projects/ web/data/`` — so even a
correctly-persisted advancement decision would commit the project pointer
while silently LOSING the work-spec body it points at.

The test parses each workflow's shell steps textually (the persist steps
are multi-line ``run:`` strings; full YAML parsing adds nothing) and
asserts that any workflow invoking ``python -m llmxive run`` stages paths
covering each required root — or stages everything via ``git add -A``, or
delegates to the SSoT ``scripts/ci/commit-and-push.sh`` (which stages
``git add -A`` — verified here so the guard still bites if that ever changes).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WORKFLOWS_DIR = Path(__file__).resolve().parents[2] / ".github" / "workflows"
COMMIT_SCRIPT = (
    Path(__file__).resolve().parents[2] / "scripts" / "ci" / "commit-and-push.sh"
)

REQUIRED_ROOTS = ("specs", "state", "projects")

# ``git add <args>`` with args split on whitespace; quotes stripped.
_GIT_ADD_RE = re.compile(r"git add\s+(.+?)(?:\s*(?:\|\||2>|$))", re.MULTILINE)


def _pass_running_workflows() -> list[Path]:
    found = [
        path
        for path in sorted(WORKFLOWS_DIR.glob("*.yml"))
        if "-m llmxive run" in path.read_text(encoding="utf-8")
    ]
    assert found, f"no pass-running workflows found under {WORKFLOWS_DIR}"
    return found


def _staged_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for match in _GIT_ADD_RE.finditer(text):
        for raw in match.group(1).split():
            tokens.append(raw.strip("'\""))
    return tokens


def _commit_script_stages_everything() -> bool:
    """The SSoT commit+push script must stage all artifact roots (``git add -A``)
    so a lane delegating to it persists everything (FR-003). Verified here so the
    guard still fails loudly if the script is ever narrowed."""
    if not COMMIT_SCRIPT.is_file():
        return False
    return "-A" in _staged_tokens(COMMIT_SCRIPT.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "workflow", _pass_running_workflows(), ids=lambda p: p.name
)
def test_pass_running_lane_persists_all_artifact_roots(workflow: Path) -> None:
    text = workflow.read_text(encoding="utf-8")
    # A lane may persist inline (``git add <roots>``) OR delegate to the SSoT
    # ``scripts/ci/commit-and-push.sh`` (which stages ``git add -A``).
    if "commit-and-push.sh" in text:
        assert _commit_script_stages_everything(), (
            f"{workflow.name} delegates persistence to commit-and-push.sh, but "
            "that script does not `git add -A` — artifact roots could be lost "
            "(FR-003)"
        )
        return
    tokens = _staged_tokens(text)
    assert tokens, (
        f"{workflow.name} runs pipeline passes but has no `git add` persist "
        "step at all — generated artifacts would never be committed (FR-003)"
    )
    if "-A" in tokens:
        return  # stages everything
    for root in REQUIRED_ROOTS:
        covered = any(
            token == root or token.startswith(f"{root}/") for token in tokens
        )
        assert covered, (
            f"{workflow.name} persist step stages {tokens} but nothing under "
            f"`{root}/` — artifacts written there during a pass would be "
            "silently lost (FR-003; see specs/023 research.md R2)"
        )
