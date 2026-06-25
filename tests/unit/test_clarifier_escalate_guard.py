"""The clarifier must NOT escalate when there is nothing left to clarify.

Live failure (PROJ-492): a re-generated spec had ZERO open
``[NEEDS CLARIFICATION]`` markers, yet the clarifier LLM emitted
``verdict=escalate`` — which the CLI turns into a fail-and-retry / human ask
over a no-op, blocking the project at `specified`. Guard: honor ``escalate``
ONLY when something is genuinely unresolved.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from llmxive.backends.base import ChatResponse
from llmxive.speckit.clarify_cmd import ClarifierAgent
from llmxive.speckit.slash_command import SlashCommandContext
from llmxive.types import BackendName

_REAL_SPEC = """# Feature Specification: A/B test validity

## User Scenarios & Testing

- **US-1** (P1): A reviewer submits a list of A/B-test summary URLs and receives
  a per-summary consistency verdict with the reconstructed p-value.

### Edge Cases
- Empty input list returns an empty report, not an error.

## Requirements
- **FR-001**: System MUST accept a list of URLs pointing to A/B-test summaries.
- **FR-002**: System MUST reconstruct the expected p-value via a two-proportion
  Z-test for binary conversion metrics.
- **FR-003**: System MUST flag a summary inconsistent when the reported and
  reconstructed p-values differ by more than 0.05.

### Success Criteria
- **SC-001**: Reconstruction matches a hand-computed reference on 10 worked
  examples to within 1e-6.

## Assumptions
- Summaries report sample size and conversion counts per variant.
"""


def _ctx(project_dir: Path) -> SlashCommandContext:
    return SlashCommandContext(
        project_id="PROJ-700-clarify-guard",
        project_dir=project_dir,
        run_id="r", task_id="t",
        inputs=[], expected_outputs=[],
        prompt_template_path=Path("agents/prompts/clarifier.md"),
        default_backend=BackendName.LOCAL,  # no LLM in unit test → panel skips
        fallback_backends=[], default_model="m", prompt_version="1.0.0",
        agent_name="clarifier",
    )


def _setup(tmp_path: Path):
    proj = tmp_path / "projects" / "PROJ-700-clarify-guard"
    feat = proj / "specs" / "001-x"
    mem = proj / ".specify" / "memory"
    feat.mkdir(parents=True)
    mem.mkdir(parents=True)
    spec = feat / "spec.md"
    spec.write_text(_REAL_SPEC, encoding="utf-8")
    return proj, spec, mem


def test_escalate_with_nothing_unresolved_does_not_block(tmp_path, monkeypatch) -> None:
    proj, spec, mem = _setup(tmp_path)
    # Scope out the separate spec-panel concern (offline already skips it, but be
    # explicit — it is not the unit under test).
    monkeypatch.setattr(ClarifierAgent, "_run_spec_panel", lambda *a, **k: None)
    agent = ClarifierAgent()
    mech = {"spec_path": str(spec), "spec_text": _REAL_SPEC, "markers": [], "memory_dir": str(mem)}
    resp = ChatResponse(text='{"verdict": "escalate", "patches": []}', model="m", backend="local")
    # 0 markers + escalate → must NOT raise (advances; the panel decides quality).
    out = agent.write_artifacts(_ctx(proj), mech, resp)
    assert out  # produced the spec output path


def test_escalate_with_real_unresolved_markers_still_escalates(tmp_path, monkeypatch) -> None:
    proj, spec, mem = _setup(tmp_path)
    monkeypatch.setattr(ClarifierAgent, "_run_spec_panel", lambda *a, **k: None)
    agent = ClarifierAgent()
    # One genuine open marker, no patch → escalate is HONORED (raises).
    mech = {
        "spec_path": str(spec), "spec_text": _REAL_SPEC,
        "markers": [{"question": "Which test for revenue lift?"}],
        "memory_dir": str(mem),
    }
    resp = ChatResponse(text='{"verdict": "escalate", "patches": []}', model="m", backend="local")
    with pytest.raises(RuntimeError):
        agent.write_artifacts(_ctx(proj), mech, resp)
