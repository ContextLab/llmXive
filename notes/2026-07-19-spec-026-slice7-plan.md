# spec 026 Slice 7 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Retire every remaining model-id pin outside the canonical policy/catalog layer by migrating `AgentRegistryEntry` and all compatibility consumers onto named capability profiles, and land US5's deferred acceptance criteria (AC1, AC3, AC4).

**Architecture:** `AgentRegistryEntry` drops `default_model`/`default_backend`/`fallback_backends` for a single `profile` field; the tier-1 escalation rung's model-id exclusion becomes a two-pass pure translation in `route_chat`; the canonical `ChatMessage`/backend path is extended to carry multimodal content so the figure-review call can route through `select()`/`execute()` instead of its own urllib request.

**Tech Stack:** Python ≥3.11, Pydantic v2 (`llmxive.types`), frozen dataclasses (`llmxive.model_selection.*`), pytest.

**Design doc:** [2026-07-19-issue-1242-slice7-design.md](2026-07-19-issue-1242-slice7-design.md) (rev 3) · **Tracking:** [#1285](https://github.com/ContextLab/llmXive/issues/1285) · **Spec:** `specs/026-model-selection-consolidation/spec.md`

## Global Constraints

- **Behavior-preserving against the fixed migration snapshot**: `qwen.qwen3.5-122b` remains every LLM agent's chain leader; `google.gemma-4-31B-it` stays. Only the deltas recorded in Task 11 are sanctioned.
- **No model-id literals in production code** outside `model_selection/policy.py` and the live catalog layer. Fixtures and tests may contain them.
- **Regenerate the manifest after every pin-moving task**: `.venv/bin/python -m llmxive.model_selection.inventory`. The frozen-drift test `tests/unit/test_model_selection_inventory.py` enforces json+md match the live scan.
- **Every commit**: `PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit …` with trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`. Verify HEAD moved. **NEVER push** — local `main` lags ~785 commits; rebase onto `origin/main` only at PR time.
- **Constitution III**: real tests, no mocks as the primary path. The autouse `_offline_model_selection_snapshot` fixture in `tests/conftest.py` makes routing deterministic offline — **do not remove it**.
- **Do NOT touch `agents/prompts/**`** — that fires the promptfoo eval gate; this slice is schema/routing only.
- **Import discipline**: `model_selection` types into `backends`/`agents` under `TYPE_CHECKING` + `from __future__ import annotations`. `llmxive/types.py` must NOT import `llmxive.model_selection` at runtime (cycle — see Task 5).
- **Offline suite green after every task**: `.venv/bin/python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q`.

## File Structure

|file|responsibility in this slice|
|-|-|
|`src/llmxive/model_selection/types.py`|`RequirementOverrides.exclude_leader` (T1); `ContentPart`/`TextPart`/`ImagePart` live in `backends/base.py` instead (they are a message concern, not a selection concern)|
|`src/llmxive/model_selection/route.py`|two-pass `exclude_leader` translation (T1); `deterministic-no-llm` guard re-keyed to `profile` (T2)|
|`src/llmxive/state/execution_status.py`|`TierConstraint.exclude_leader`; `to_overrides()`/`tier_overrides()` lose `default_model` (T1)|
|`src/llmxive/pipeline/graph.py`|stop reading `entry.default_model`; pass `entry.profile` (T1, T6)|
|`src/llmxive/backends/base.py`|`ContentPart` union + `ImagePart` validation; `UnsupportedFeatureError` (T3)|
|`src/llmxive/backends/router.py`|`disposition_of` SKIP branch for `UnsupportedFeatureError` (T3); `profile` param on all four wrappers (T7)|
|`src/llmxive/backends/dartmouth.py`|serialize `ContentPart` into the OpenAI content array (T3)|
|`src/llmxive/backends/local.py`|reject multimodal with `UnsupportedFeatureError` (T3)|
|`src/llmxive/model_selection/tokens.py`|image-inclusive conservative estimator with a documented upper bound (T3)|
|`src/llmxive/model_selection/policy.py`|`qwen3.5` gains `vision`; `SELECTION_POLICY_VERSION` → 2 (T4)|
|`src/llmxive/types.py`|`ProfileName` Literal; `AgentRegistryEntry.profile`; `RunLogEntry` nullable attribution (T5, T9)|
|`agents/registry.yaml`|54 entries rewritten to `profile:` (T5)|
|`src/llmxive/paper_reprocess/preprint_figures.py`|delete `_VISION_MODEL` + the urllib path; route via `profile="vision"` (T4)|
|`specs/026-model-selection-consolidation/spec.md`|record the sanctioned Slice-7 deltas (T11)|

---

### Task 1: `exclude_leader` — two-pass translation

**Files:**
- Modify: `src/llmxive/model_selection/types.py:186-189` (add field to `RequirementOverrides`)
- Modify: `src/llmxive/model_selection/route.py:208-217` (two-pass translation)
- Modify: `src/llmxive/state/execution_status.py:79-110` (`TierConstraint`), `:177-183` (`tier_overrides`)
- Modify: `src/llmxive/pipeline/graph.py:767`, `:772-774`
- Test: `tests/unit/test_exclude_leader.py` (new), `tests/unit/test_execution_exhaustion_flow.py:159-172` (update)

**Interfaces:**
- Consumes: `select(requirement, snapshot) -> ModelChain` (unchanged, pure); `RequirementOverrides(allow_paid, require_paid, exclude_models, max_credits)`.
- Produces: `RequirementOverrides.exclude_leader: bool = False`; `TierConstraint.exclude_leader: bool = False`; `TierConstraint.to_overrides()` **with no arguments**; `execution_status.tier_overrides(project_id, *, repo_root=None)` **with no `default_model`**.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_exclude_leader.py`. Reuse the snapshot helper pattern from `tests/unit/test_model_selection_select.py` (read `_snapshot()` there and mirror it — it builds a `RuntimeSnapshot` with qwen3.5/gemma-4/gpt-oss free + a paid claude candidate).

```python
"""exclude_leader: the tier-1 'free second opinion' rung without a model id."""
from __future__ import annotations

from dataclasses import replace

import pytest

from llmxive.model_selection.profiles import build_requirement
from llmxive.model_selection.select import select
from llmxive.model_selection.types import CallBudget, ModelUnavailable, RequirementOverrides
from llmxive.state import execution_status as es

# Import the existing fixed-snapshot helper rather than rebuilding one.
from tests.unit.test_model_selection_select import _snapshot  # noqa: E402

_CB = CallBudget(max_input_tokens=1000, max_output_tokens=500)


def _leader(chain):
    return chain.candidates[0].model_ref.model_id


def test_exclude_leader_drops_rank_one_only():
    snap = _snapshot()
    base = build_requirement("standard_generation", _CB)
    full = select(base, snap)
    assert _leader(full) == "qwen.qwen3.5-122b"

    narrowed = replace(base, exclude_models=base.exclude_models | {_leader(full)})
    second = select(narrowed, snap)
    assert _leader(second) == "google.gemma-4-31B-it"
    # every OTHER candidate from the full chain survives, in order
    assert [c.model_ref.model_id for c in second.candidates] == [
        c.model_ref.model_id for c in full.candidates if c.model_ref.model_id != _leader(full)
    ]


def test_tier_constraint_carries_exclude_leader_not_a_model_id():
    rung = es.TierConstraint(allow_paid=False, exclude_leader=True)
    ov = rung.to_overrides()          # NO default_model argument
    assert ov.exclude_leader is True
    assert ov.exclude_models == frozenset()   # no model id smuggled in


def test_tier_overrides_needs_no_default_model(tmp_path):
    pid = "PROJ-001-x"
    ov0 = es.tier_overrides(pid, repo_root=tmp_path)   # tier 0
    assert ov0.exclude_leader is False
    es.bump_model_tier(pid, repo_root=tmp_path)
    ov1 = es.tier_overrides(pid, repo_root=tmp_path)   # tier 1
    assert ov1.exclude_leader is True
    assert ov1.exclude_models == frozenset()


def test_exclude_leader_composes_with_existing_exclusions():
    snap = _snapshot()
    base = build_requirement("standard_generation", _CB,
                             exclude_models=frozenset({"google.gemma-4-31B-it"}))
    full = select(base, snap)
    assert _leader(full) == "qwen.qwen3.5-122b"
    narrowed = replace(base, exclude_models=base.exclude_models | {_leader(full)})
    assert _leader(select(narrowed, snap)) == "openai.gpt-oss-120b"


def test_pass_one_model_unavailable_propagates_immediately():
    """When pass 1 finds nothing eligible, ModelUnavailable propagates and pass 2
    is NEVER invoked (there is no leader to exclude)."""
    snap = _snapshot()
    impossible = build_requirement(
        "standard_generation", _CB,
        exclude_models=frozenset({
            "qwen.qwen3.5-122b", "google.gemma-4-31B-it", "openai.gpt-oss-120b",
            "anthropic.claude-haiku-4-5-20251001", "Qwen/Qwen2.5-3B-Instruct",
        }),
    )
    with pytest.raises(ModelUnavailable):
        select(impossible, snap)
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
.venv/bin/python -m pytest tests/unit/test_exclude_leader.py -q
```
Expected: FAIL — `TypeError: TierConstraint.__init__() got an unexpected keyword argument 'exclude_leader'`.

- [ ] **Step 3: Add the field to `RequirementOverrides`**

In `src/llmxive/model_selection/types.py`, after line 189 (`max_credits`):

```python
    #: Routing-only escalation constraint (spec 026 slice 7): drop whatever
    #: ``select`` ranks FIRST, so the "free second opinion" rung needs no model
    #: id. Applied by ``route_chat`` as a two-pass translation (pass 1 resolves
    #: the leader, pass 2 excludes it), NOT inside ``select`` — ``select``
    #: receives a ``ModelRequirement`` and stays pure.
    exclude_leader: bool = False
```

- [ ] **Step 4: Implement the two-pass translation in `route_chat`**

In `src/llmxive/model_selection/route.py`, replace the `if overrides is None:` block (currently lines 208-217) with:

```python
    if overrides is None:
        requirement = base
    else:
        requirement = replace(
            base,
            require_paid=base.require_paid or overrides.require_paid,
            exclude_models=base.exclude_models | overrides.exclude_models,
            max_credits=_tighter_credits(base.max_credits, overrides.max_credits),
        )
        if overrides.exclude_leader:
            # PASS 1 (pure, no I/O): resolve who would lead, then exclude exactly
            # that model. If pass 1 raises ModelUnavailable it propagates
            # immediately — there is no leader to exclude and pass 2 never runs.
            leader = select(requirement, snap).candidates[0].model_ref.model_id
            requirement = replace(
                requirement, exclude_models=requirement.exclude_models | {leader}
            )
    chain = select(requirement, snap)   # PASS 2 — THE decision
```

- [ ] **Step 5: De-parameterize `TierConstraint` / `tier_overrides`**

In `src/llmxive/state/execution_status.py`, replace `exclude_registered_default` with `exclude_leader` and drop the `default_model` argument:

```python
@dataclass(frozen=True)
class TierConstraint:
    """One escalation rung as REQUIREMENT overrides — never a model id (spec 026
    slice 6; slice 7 removed the last model-id argument)."""

    allow_paid: bool = False
    exclude_leader: bool = False
    require_paid: bool = False
    max_credits: int | None = None

    @property
    def is_paid(self) -> bool:
        return self.allow_paid or self.require_paid

    def to_overrides(self) -> RequirementOverrides:
        return RequirementOverrides(
            allow_paid=self.allow_paid,  # ALWAYS explicit (incl. False)
            require_paid=self.require_paid,
            exclude_leader=self.exclude_leader,
            max_credits=self.max_credits,
        )
```

Update `_FREE_RUNGS` to `TierConstraint(allow_paid=False, exclude_leader=True)` for tier 1, and:

```python
def tier_overrides(project_id: str, *, repo_root: Path | None = None) -> RequirementOverrides:
    """The RequirementOverrides for the project's CURRENT model tier."""
    return tier_constraint(model_tier(project_id, repo_root=repo_root)).to_overrides()
```

- [ ] **Step 6: Update the `graph.py` call site**

In `src/llmxive/pipeline/graph.py`, delete line 767 (`_model_for_run = entry.default_model`) and change lines 772-774 to:

```python
            _req_overrides = execution_status.tier_overrides(project.id, repo_root=repo)
```

Leave `default_model=_model_for_run` on `SlashCommandContext` for now — Task 6 replaces the whole context field set. To keep this task green in isolation, temporarily pass `default_model=entry.default_model` directly at the `SlashCommandContext(...)` construction site.

- [ ] **Step 7: Update the existing exhaustion test**

In `tests/unit/test_execution_exhaustion_flow.py:159-172`, remove the `default_model="REGISTERED-DEFAULT"` arguments from both `es.tier_overrides(...)` calls and assert `exclude_leader` instead of `exclude_models`.

- [ ] **Step 8: Run the full offline suite**

```bash
.venv/bin/python -m pytest tests/unit/test_exclude_leader.py tests/unit/test_execution_exhaustion_flow.py tests/unit/test_slice6_override_propagation.py -q
.venv/bin/python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q
```
Expected: all PASS. `test_slice6_override_propagation.py:412-464` references `tier_overrides(..., default_model=…)` — update those call sites too.

- [ ] **Step 9: Commit**

```bash
git add -A
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(026 Slice-7): exclude_leader replaces the tier-1 model-id exclusion

Tier 1 ('free second opinion') expressed exclude_models={registered default},
which required threading a model id from the registry into dispatch. Slice 7
deletes that registry field, so the rung becomes exclude_leader: route_chat
resolves the leader with a first PURE select() pass and excludes exactly it in
the second. select() is untouched and the returned chain remains its direct
output, so FR-003 needs no amendment.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 2: `deterministic-no-llm` — two-layer bypass (US5 AC3)

**Files:**
- Modify: `src/llmxive/model_selection/route.py:64` (constant docstring), `:168-172` (guard)
- Modify: `src/llmxive/pipeline/graph.py` (registry dispatch bypass — locate the agent-dispatch branch that builds `SlashCommandContext`)
- Test: `tests/unit/test_deterministic_no_llm.py` (new)

**Interfaces:**
- Consumes: `route.DETERMINISTIC_NO_LLM = "deterministic-no-llm"` (unchanged value).
- Produces: `route_chat(profile="deterministic-no-llm", …)` raises `ValueError` **before** snapshot acquisition; registry dispatch never reaches `route_chat` for a no-LLM agent.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_deterministic_no_llm.py`:

```python
"""US5 AC3 — a no-LLM agent bypasses selection at BOTH layers."""
from __future__ import annotations

import pytest

from llmxive.backends.base import ChatMessage
from llmxive.model_selection.route import DETERMINISTIC_NO_LLM, route_chat


def test_route_chat_rejects_the_sentinel_profile_before_any_snapshot(monkeypatch):
    """Layer 2 (defense in depth): reaching the model layer with the sentinel is a
    programming error and must fail BEFORE snapshot/ledger work."""
    import llmxive.model_selection.route as route_mod

    def _boom(*_a, **_k):  # pragma: no cover - must never be called
        raise AssertionError("snapshot acquired before the sentinel guard fired")

    monkeypatch.setattr(route_mod, "runtime_snapshot", _boom)
    monkeypatch.setattr(route_mod, "_SNAPSHOT_CACHE", None)

    with pytest.raises(ValueError, match="deterministic-no-llm"):
        route_chat(
            [ChatMessage(role="user", content="hi")],
            profile=DETERMINISTIC_NO_LLM,
            max_tokens=100,
        )


def test_route_chat_still_rejects_the_sentinel_via_caller_model():
    """The pre-existing caller_model spelling must keep failing closed until
    Task 7 removes the last caller_model pins."""
    with pytest.raises(ValueError, match="deterministic-no-llm"):
        route_chat(
            [ChatMessage(role="user", content="hi")],
            caller_model=DETERMINISTIC_NO_LLM,
            max_tokens=100,
        )
```

**Layer 1 (registry dispatch) is tested in Task 5**, where `entry.profile` exists. Do NOT write an
`xfail` placeholder here: a test marked `xfail(strict=False)` asserts nothing and passes whether or
not the behavior is correct. Task 5 Step 6 adds the layer-1 test to `test_profile_schema.py`.

- [ ] **Step 2: Run it to verify it fails**

```bash
.venv/bin/python -m pytest tests/unit/test_deterministic_no_llm.py -q
```
Expected: FAIL — `route_chat` currently keys the guard off `caller_model`, so the sentinel profile reaches `build_requirement` and raises `KeyError`, not `ValueError`.

- [ ] **Step 3: Re-key the guard to `profile`**

In `src/llmxive/model_selection/route.py`, replace the guard at lines 168-172:

```python
    # deterministic-no-llm bypasses snapshot / select / execute ENTIRELY: a no-llm
    # agent that reached the model layer is a programming error → fail fast before
    # touching the mechanism (US5 AC3, layer 2). Registry dispatch (graph.py) is
    # layer 1 and must never let such an agent get here in the first place.
    if profile == DETERMINISTIC_NO_LLM or caller_model == DETERMINISTIC_NO_LLM:
        raise ValueError(
            "route_chat called with the 'deterministic-no-llm' sentinel — a no-LLM "
            "agent must never reach model selection/execution"
        )
```

Keep the `caller_model` arm: Task 7 removes the last `caller_model` pins, and until then both spellings must fail closed.

- [ ] **Step 4: Add the registry-dispatch bypass**

In `src/llmxive/pipeline/graph.py`, immediately before the agent's LLM dispatch (the block that constructs `SlashCommandContext` around line 783), add:

```python
        # US5 AC3, layer 1: a no-LLM agent NEVER enters model selection.
        if entry.profile == DETERMINISTIC_NO_LLM:
            logger.info("agent %s is deterministic-no-llm — bypassing model selection", entry.name)
            return _run_deterministic_agent(agent_name, project, repo=repo, run_id=run_id)
```

Locate the existing deterministic path for `paper_publisher` first (`grep -rn "paper_publisher" src/llmxive/pipeline/graph.py`) and call THAT, rather than inventing `_run_deterministic_agent`. If dispatch already routes `paper_publisher` deterministically, this step is an assertion that the branch is keyed on `entry.profile` rather than on the agent's name.

- [ ] **Step 5: Run tests**

```bash
.venv/bin/python -m pytest tests/unit/test_deterministic_no_llm.py -q
.venv/bin/python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q
```
Expected: the layer-2 test PASSES; the layer-1 test XFAILs until Task 5.

- [ ] **Step 6: Commit**

```bash
git add -A
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(026 Slice-7): deterministic-no-llm bypass at both layers (US5 AC3)

route.py detected the sentinel only via caller_model. Once the registry carries
a profile instead of a model, profile='deterministic-no-llm' would have reached
build_requirement() and died as an unknown-profile KeyError, possibly after
snapshot/ledger preparation. The guard now fires on either spelling before any
snapshot work, and registry dispatch bypasses no-LLM agents outright.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 3: multimodal canonical path

**Files:**
- Modify: `src/llmxive/backends/base.py:21-25` (`ContentPart`), after `:99` (`UnsupportedFeatureError`)
- Modify: `src/llmxive/backends/router.py:205-213` (`disposition_of`)
- Modify: `src/llmxive/backends/dartmouth.py:790-799` (langchain serialization)
- Modify: `src/llmxive/backends/local.py:39` (`chat` — reject multimodal)
- Modify: `src/llmxive/model_selection/tokens.py` (image-inclusive estimator)
- Test: `tests/unit/test_multimodal_content.py` (new)

**Interfaces:**
- Produces: `TextPart(text: str)`; `ImagePart(mime: str, data: bytes, width: int, height: int)`;
  `ContentPart = TextPart | ImagePart`; `ChatMessage.content: str | tuple[ContentPart, ...]`;
  `UnsupportedFeatureError(PermanentBackendError)` classified `CandidateDisposition.SKIP`;
  `tokens.MAX_IMAGE_DIMENSION_PX = 1536`, `tokens.MAX_IMAGE_BYTES = 8 * 1024 * 1024`,
  `tokens.TOKENS_PER_IMAGE = 2048`.
- Consumes: `disposition_of(exc) -> CandidateDisposition` (`router.py:199`).

**Why `ContentPart` lives in `backends/base.py`:** it is a property of a *message*, which `backends`
owns. Defining it in `model_selection` would force `backends` to import `model_selection` at runtime —
the same cycle Task 5 avoids.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_multimodal_content.py`:

```python
"""Canonical multimodal path (spec 026 slice 7): content parts, skip-class
rejection, and a DEMONSTRABLE token upper bound."""
from __future__ import annotations

import pytest

from llmxive.backends.base import (
    ChatMessage, ImagePart, PermanentBackendError, TextPart, UnsupportedFeatureError,
)
from llmxive.backends.router import CandidateDisposition, disposition_of
from llmxive.model_selection import tokens

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 512


def _img(w=1536, h=1536, data=_PNG):
    return ImagePart(mime="image/png", data=data, width=w, height=h)


def test_string_content_still_valid_and_unchanged():
    assert ChatMessage(role="user", content="plain text").content == "plain text"


def test_parts_content_is_an_immutable_tuple():
    import dataclasses

    m = ChatMessage(role="user", content=(TextPart("look:"), _img()))
    assert isinstance(m.content, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.content = "mutated"          # frozen dataclass


def test_image_part_rejects_oversize_dimensions():
    with pytest.raises(ValueError, match="dimension"):
        _img(w=tokens.MAX_IMAGE_DIMENSION_PX + 1)


def test_image_part_rejects_oversize_payload():
    with pytest.raises(ValueError, match="bytes"):
        _img(data=b"x" * (tokens.MAX_IMAGE_BYTES + 1))


def test_image_part_rejects_unknown_mime():
    with pytest.raises(ValueError, match="mime"):
        ImagePart(mime="application/pdf", data=_PNG, width=10, height=10)


def test_unsupported_feature_is_SKIP_not_ABORT():
    """A text-only backend refusing an image must SKIP the candidate. A plain
    PermanentBackendError would ABORT the whole chain (router.py:211)."""
    assert disposition_of(UnsupportedFeatureError("no vision")) is CandidateDisposition.SKIP
    assert disposition_of(PermanentBackendError("hard refusal")) is CandidateDisposition.ABORT
    assert isinstance(UnsupportedFeatureError("x"), PermanentBackendError)


def test_estimator_is_at_least_the_documented_maximum_at_boundary():
    """UPPER-bound proof: a max-dimension image must price AT OR ABOVE the
    documented per-image worst case — not merely above an average-looking floor."""
    msgs = [ChatMessage(role="user", content=(TextPart("hi"), _img()))]
    assert tokens.max_input_tokens_upper_bound(msgs) >= tokens.TOKENS_PER_IMAGE


def test_estimator_scales_with_image_count():
    one = tokens.max_input_tokens_upper_bound([ChatMessage(role="user", content=(_img(),))])
    three = tokens.max_input_tokens_upper_bound(
        [ChatMessage(role="user", content=(_img(), _img(), _img()))]
    )
    assert three >= one + 2 * tokens.TOKENS_PER_IMAGE


def test_mixed_text_and_image_accounting():
    text_only = tokens.max_input_tokens_upper_bound(
        [ChatMessage(role="user", content="a" * 4000)]
    )
    mixed = tokens.max_input_tokens_upper_bound(
        [ChatMessage(role="user", content=(TextPart("a" * 4000), _img()))]
    )
    assert mixed >= text_only + tokens.TOKENS_PER_IMAGE


def test_local_backend_rejects_multimodal_with_the_skip_class():
    from llmxive.backends.local import LocalBackend

    with pytest.raises(UnsupportedFeatureError):
        LocalBackend().chat(
            [ChatMessage(role="user", content=(_img(),))],
            model="Qwen/Qwen2.5-3B-Instruct",
        )
```

- [ ] **Step 2: Run it to verify it fails**

```bash
.venv/bin/python -m pytest tests/unit/test_multimodal_content.py -q
```
Expected: FAIL — `ImportError: cannot import name 'ImagePart' from 'llmxive.backends.base'`.

- [ ] **Step 3: Add the content parts + the skip-class exception**

In `src/llmxive/backends/base.py`, replace the `ChatMessage` definition (lines 21-24), adding the
parts above it:

```python
#: Allowed image MIME types (Dartmouth's OpenAI-compatible vision endpoint).
_IMAGE_MIMES = frozenset({"image/png", "image/jpeg", "image/webp"})


@dataclass(frozen=True)
class TextPart:
    """A text span inside a multimodal message."""

    text: str


@dataclass(frozen=True)
class ImagePart:
    """An image inside a multimodal message.

    Dimensions and payload size are BOUNDED and validated here so the token
    estimator's per-image charge is a true UPPER bound (FR-003/FR-010): an
    unbounded payload priced at a fixed constant would invalidate the cost bound
    ``select()`` reserves against.
    """

    mime: str
    data: bytes
    width: int
    height: int

    def __post_init__(self) -> None:
        # Function-local: backends.base must not import model_selection at module scope.
        from llmxive.model_selection.tokens import MAX_IMAGE_BYTES, MAX_IMAGE_DIMENSION_PX

        if self.mime not in _IMAGE_MIMES:
            raise ValueError(
                f"ImagePart: unsupported mime {self.mime!r} (allowed: {sorted(_IMAGE_MIMES)})"
            )
        if self.width <= 0 or self.height <= 0:
            raise ValueError("ImagePart: dimension must be positive")
        if self.width > MAX_IMAGE_DIMENSION_PX or self.height > MAX_IMAGE_DIMENSION_PX:
            raise ValueError(
                f"ImagePart: dimension {self.width}x{self.height} exceeds the estimator's "
                f"supported maximum {MAX_IMAGE_DIMENSION_PX}px — downscale before selection "
                f"(the token upper bound is derived from it)"
            )
        if len(self.data) > MAX_IMAGE_BYTES:
            raise ValueError(
                f"ImagePart: {len(self.data)} bytes exceeds MAX_IMAGE_BYTES={MAX_IMAGE_BYTES}"
            )


ContentPart = TextPart | ImagePart


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str | tuple[ContentPart, ...]
```

After `PaidGuardDenied` (line 99), add:

```python
class UnsupportedFeatureError(PermanentBackendError):
    """This backend/model cannot serve a feature THIS request needs (e.g. image
    content on a text-only local checkpoint). Like ``PaidGuardDenied`` this is a
    CANDIDATE-ineligibility signal, not a request-level refusal: it says nothing
    about other candidates, so the chain walker SKIPS to the next one
    (``CandidateDisposition.SKIP``) instead of aborting. Without this dedicated
    type it would land on the generic ``PermanentBackendError`` branch and ABORT
    the chain (``router.disposition_of``, line 211).
    """
```

- [ ] **Step 4: Classify it as SKIP**

In `src/llmxive/backends/router.py`, in `disposition_of`, immediately after the `PaidGuardDenied`
branch (line 206):

```python
    if isinstance(exc, UnsupportedFeatureError):
        return CandidateDisposition.SKIP  # candidate can't serve this feature → advance
```

Add `UnsupportedFeatureError` to the existing `from llmxive.backends.base import …` block.

- [ ] **Step 5: Add the bounded image estimator**

In `src/llmxive/model_selection/tokens.py`, add the constants with their derivation:

```python
#: Images are bounded BEFORE selection so the per-image charge below is a true
#: upper bound. Callers downscale to fit; an oversize ImagePart is REJECTED.
MAX_IMAGE_DIMENSION_PX = 1536
MAX_IMAGE_BYTES = 8 * 1024 * 1024

#: Documented worst case for ONE image at MAX_IMAGE_DIMENSION_PX in high-detail
#: mode. Derivation (OpenAI-compatible vision tiling, which Dartmouth serves):
#: 1536x1536 = 3x3 = 9 tiles of 512px; cost = 85 base + 9 * 170 per tile = 1615
#: tokens. Rounded UP to 2048 for provider-serialization overhead and future
#: tiling changes — deliberately over-estimating, matching this module's stated
#: conservative philosophy. NEVER lower this without re-deriving it: selection
#: prices worst_case_credits against it (FR-003).
TOKENS_PER_IMAGE = 2048
```

In `max_input_tokens_upper_bound`, make the per-message accumulation content-aware: a `tuple`
content sums each `TextPart.text` through the **existing** char÷4 path and adds `TOKENS_PER_IMAGE`
per `ImagePart`; a `str` content keeps its existing path **byte-for-byte unchanged** (the existing
estimator tests plus `test_string_content_still_valid_and_unchanged` prove this).

- [ ] **Step 6: Serialize parts in the Dartmouth backend**

`DartmouthBackend.chat` builds **langchain_core** message objects (not a raw OpenAI array), so the
change goes in the conversion loop at lines 790-799. Add a module-level helper:

```python
def _lc_content(content):
    """Serialize canonical ChatMessage content for langchain_core. A plain ``str``
    passes through unchanged (byte-identical payloads for every existing caller);
    a parts tuple becomes langchain's content-block list, which the
    OpenAI-compatible endpoint renders as the multimodal content array."""
    from llmxive.backends.base import ImagePart, TextPart

    if isinstance(content, str):
        return content
    blocks: list[dict] = []
    for part in content:
        if isinstance(part, TextPart):
            blocks.append({"type": "text", "text": part.text})
        elif isinstance(part, ImagePart):
            import base64

            b64 = base64.b64encode(part.data).decode()
            blocks.append({
                "type": "image_url",
                "image_url": {"url": f"data:{part.mime};base64,{b64}"},
            })
        else:  # pragma: no cover - the union is closed
            raise PermanentBackendError(f"unknown content part {type(part).__name__}")
    return blocks
```

Then replace every `content=m.content` in that loop with `content=_lc_content(m.content)`.

- [ ] **Step 7: Reject multimodal in the local backend**

In `src/llmxive/backends/local.py`, at the top of `chat` (line 39) — materializing `messages` into
a list first if it is currently consumed lazily:

```python
        messages_list = list(messages)
        if any(not isinstance(m.content, str) for m in messages_list):
            raise UnsupportedFeatureError(
                "local backend serves a text-only checkpoint and cannot accept image "
                "content — skip this candidate"
            )
```

- [ ] **Step 8: Repo-wide `.content` audit**

```bash
grep -rn "\.content" --include="*.py" src/llmxive/ | grep -v "response\.content"
```

For EVERY hit confirm it either (a) only ever receives `str` content, or (b) handles parts.
Particular attention to `speckit/_inspection.py` (audit serialization **must** record image
metadata — mime, dimensions, byte length — and **never** raw image bytes into audit logs),
`tools/summarize.py`, and any `len()`/slicing/regex over `.content`. Record the audit outcome in
the commit message.

- [ ] **Step 9: Run tests**

```bash
.venv/bin/python -m pytest tests/unit/test_multimodal_content.py -q
.venv/bin/python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q
```
Expected: all PASS.

- [ ] **Step 10: Commit**

```bash
git add -A
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(026 Slice-7): canonical multimodal path (ContentPart + SKIP class + bounded pricing)

ChatMessage.content was typed str, so the figure-review payload could not be
expressed as a ChatMessage at all — which is why that call bypassed the backend
layer with its own urllib request (no breaker, retry, classification or credit
guard). content becomes str | tuple[ContentPart, ...]; str is unchanged for every
existing caller.

Two load-bearing contract details:
- UnsupportedFeatureError is classified SKIP, mirroring PaidGuardDenied. A plain
  PermanentBackendError would ABORT the chain (router.py:211), so a text-only
  local candidate would kill a vision chain instead of yielding to its peer.
- Image pricing is a DEMONSTRABLE upper bound, not a floor: ImagePart rejects
  oversize dimensions/payloads, and TOKENS_PER_IMAGE is derived from the bounded
  maximum (1536px -> 9 tiles -> 85 + 9*170 = 1615, rounded up to 2048). Tests
  assert the estimator is >= the documented maximum at boundary images.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 4: vision verification (2 real calls) → policy v2 → migrate the figure call

**⚠ HARD GATE — STOP AND ESCALATE.** If real call #1 fails, do NOT proceed and do NOT substitute a
different model on your own authority. Report the failure and stop; the maintainer decides whether
to migrate to `qwen3-vl` as a sanctioned delta instead.

**Files:**
- Modify: `src/llmxive/model_selection/policy.py:42` (version), `:113-118` (`qwen3.5` entry)
- Modify: `src/llmxive/paper_reprocess/preprint_figures.py:34`, `:191-249`
- Test: `tests/real_call/test_vision_real.py` (new); update `tests/unit/test_model_selection_policy.py:20`, `tests/unit/test_model_selection_select.py:271`, `:488`

**Interfaces:**
- Consumes: `route_chat(profile="vision", …)`, `TextPart`/`ImagePart` (Task 3),
  `RequirementOverrides.exclude_leader` (Task 1).
- Produces: `SELECTION_POLICY_VERSION = 2`; `qwen3.5` attributed `vision`.

- [ ] **Step 1: Write the real-call verification**

Create `tests/real_call/test_vision_real.py` (needs `DARTMOUTH_CHAT_API_KEY`; runs only under
`LLMXIVE_REAL_TESTS=1`):

```python
"""SC-008 vision verification (Constitution II): real image UNDERSTANDING, not
merely payload acceptance."""
from __future__ import annotations

import io

from llmxive.backends.base import ChatMessage, ImagePart, TextPart
from llmxive.model_selection.route import route_chat
from llmxive.model_selection.types import RequirementOverrides


def _red_square_png() -> tuple[bytes, int, int]:
    """A 256x256 PURE RED png. A model that ignores the image cannot name red."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (256, 256), (255, 0, 0)).save(buf, format="PNG")
    return buf.getvalue(), 256, 256


def _asks_for_the_colour() -> list[ChatMessage]:
    png, w, h = _red_square_png()
    return [
        ChatMessage(role="system", content="Answer with ONE word."),
        ChatMessage(role="user", content=(
            TextPart("What is the dominant colour of this image? One word."),
            ImagePart(mime="image/png", data=png, width=w, height=h),
        )),
    ]


def test_qwen35_actually_understands_images():
    """THE GATE for the policy attribution: qwen3.5-122b must READ the image."""
    resp = route_chat(_asks_for_the_colour(), profile="vision", max_tokens=64)
    assert resp.model == "qwen.qwen3.5-122b"
    assert "red" in resp.text.lower(), f"no image understanding; got {resp.text!r}"


def test_qwen3_vl_serves_the_canonical_multimodal_representation():
    """SC-008 names qwen.qwen3-vl:32b as the vision tier INDEPENDENTLY of the
    qwen3.5 attribution; it must also consume the new ContentPart form."""
    resp = route_chat(
        _asks_for_the_colour(), profile="vision", max_tokens=64,
        overrides=RequirementOverrides(exclude_leader=True),
    )
    assert resp.model == "qwen.qwen3-vl:32b"
    assert "red" in resp.text.lower(), f"no image understanding; got {resp.text!r}"
```

- [ ] **Step 2: Run the gate**

```bash
LLMXIVE_REAL_TESTS=1 .venv/bin/python -m pytest tests/real_call/test_vision_real.py -v
```
Expected: both PASS. If `test_qwen35_actually_understands_images` FAILS → **STOP. ESCALATE.** Do
not edit the policy.

- [ ] **Step 3: Attribute vision + bump the policy version**

In `src/llmxive/model_selection/policy.py`: `SELECTION_POLICY_VERSION = 2`, and:

```python
        "qwen3.5": PolicyEntry(
            capabilities=frozenset({"cheap", "standard", "deep", "vision"}),
            features=frozenset({"reasoning", "structured", "vision"}),
            quality_tier=3,
            max_context_tokens=256_000,
        ),
```

Add to the module docstring: ``qwen3.5`` is attributed ``vision`` (real-call verified 2026-07-19,
`tests/real_call/test_vision_real.py`); ``qwen3-vl`` remains the vision peer.

- [ ] **Step 4: Update the three affected assertions**

- `tests/unit/test_model_selection_policy.py:20` → `== SELECTION_POLICY_VERSION == 2`
- `tests/unit/test_model_selection_select.py:488` → `chain.selection_policy_version == 2`
- `tests/unit/test_model_selection_select.py:271` → the `vision` chain leads with
  `qwen.qwen3.5-122b`, keeping `qwen.qwen3-vl:32b` as the peer

Do NOT touch `test_model_selection_policy.py:47-48` or `test_model_selection_select.py:264` —
`qwen3-vl`'s own attribution is unchanged by this.

- [ ] **Step 5: Migrate the figure call**

In `src/llmxive/paper_reprocess/preprint_figures.py`: delete `_VISION_MODEL` (line 34) and the
entire private-HTTP block in `_review_one_figure` (`body = {...}` → `urllib.request.Request` →
`urlopen` → response parsing, ~lines 226-249), replacing it with:

```python
    resp = route_chat(
        [
            ChatMessage(role="system", content=_SYSTEM),
            ChatMessage(role="user", content=(
                TextPart(prompt_text),
                ImagePart(mime="image/png", data=png, width=width, height=height),
            )),
        ],
        profile="vision",
        max_tokens=2000,
        temperature=0,
    )
    return resp.text, resp.model
```

`_render_png` must also return the rendered dimensions (or measure them with PIL) and
**downscale to `MAX_IMAGE_DIMENSION_PX`** rather than letting `ImagePart` raise. Drop
`_review_one_figure`'s `model` and `key` parameters, and delete `_endpoint()` if nothing else uses
it. The `enable_thinking=False` handling is already backend-level SSoT — do not re-add it here.

- [ ] **Step 6: Run everything + regenerate the manifest**

```bash
.venv/bin/python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q
LLMXIVE_REAL_TESTS=1 .venv/bin/python -m pytest tests/real_call/test_vision_real.py -v
.venv/bin/python -m llmxive.model_selection.inventory
git diff --stat specs/026-model-selection-consolidation/
```
Expected: suites PASS; the manifest loses the `_VISION_MODEL` row.

- [ ] **Step 7: Commit**

```bash
git add -A
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(026 Slice-7): vision real-call verified; policy v2; figure review routes through execute()

Real-call verified (Constitution II) that qwen.qwen3.5-122b genuinely UNDERSTANDS
image input — the code comment asserting it was not evidence. A second real call
exercises qwen.qwen3-vl:32b through execute(), which SC-008 requires independently
and which proves the fallback consumes the new ContentPart representation.

qwen3.5 therefore gains the vision capability (SELECTION_POLICY_VERSION 1 -> 2),
and the figure-review call drops its private urllib request for
route_chat(profile='vision'), gaining the breaker/retry/classification/credit-guard
semantics it never had. Same model as before, so behavior is preserved.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 5: the registry schema (`ProfileName` + `profile`) — clears 161 + 3 manifest rows

**Files:**
- Modify: `src/llmxive/types.py:689-706` (`AgentRegistryEntry`), plus a new `ProfileName` Literal
- Modify: `agents/registry.yaml` (all 54 entries)
- Modify: `src/llmxive/speckit/slash_command.py` (`SlashCommandContext` fields)
- Test: `tests/unit/test_profile_schema.py` (new); un-xfail `tests/unit/test_deterministic_no_llm.py`

**Interfaces:**
- Produces: `types.ProfileName` (a `Literal`); `AgentRegistryEntry.profile: ProfileName`;
  `SlashCommandContext.profile: str` replacing `default_backend`/`fallback_backends`/`default_model`.
- Consumes: `model_selection.profiles.PROFILES` (test-time only — never a runtime import from `types`).

**Import-cycle constraint (non-negotiable):** `llmxive/types.py` must NOT import
`llmxive.model_selection` at runtime. Importing any `model_selection` submodule executes
`model_selection/__init__.py:21` → `execute` → `backends.router` → back into a partially-initialized
`llmxive.types`. The `Literal` + a drift test is what keeps the two in sync without the import.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_profile_schema.py`:

```python
"""Registry entries express a capability PROFILE, never a model id (spec 026 US5)."""
from __future__ import annotations

from typing import get_args

import pytest
import yaml

from llmxive.agents.registry import load_registry
from llmxive.config import repo_root
from llmxive.model_selection.profiles import PROFILES
from llmxive.types import AgentRegistryEntry, ProfileName

NO_LLM = "deterministic-no-llm"


def test_profile_name_literal_matches_the_canonical_profiles():
    """The schema layer declares the names WITHOUT importing model_selection
    (that would cycle). This test is what prevents the two drifting apart."""
    assert set(get_args(ProfileName)) - {NO_LLM} == set(PROFILES)


def test_registry_has_no_model_ids_at_all():
    raw = yaml.safe_load((repo_root() / "agents" / "registry.yaml").read_text())
    for agent in raw["agents"]:
        assert "default_model" not in agent, agent["name"]
        assert "default_backend" not in agent, agent["name"]
        assert "fallback_backends" not in agent, agent["name"]
        assert agent["profile"] in get_args(ProfileName), agent["name"]


def test_every_agent_loads_with_a_canonical_profile():
    agents = load_registry().agents
    assert len(agents) == 54
    assert sum(a.profile == NO_LLM for a in agents) == 1


def test_unknown_profile_is_a_load_time_failure():
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="profile"):
        AgentRegistryEntry(
            name="bogus_agent", purpose="x" * 20, prompt_path="agents/prompts/x.md",
            prompt_version="1.0.0", profile="not_a_real_profile",
            wall_clock_budget_seconds=60,
        )


def test_no_llm_agent_is_bypassed_by_registry_dispatch():
    """US5 AC3 layer 1 (deferred here from Task 2, where entry.profile did not
    yet exist): the no-LLM agent is identified by its PROFILE, so dispatch can
    bypass it before any routing."""
    entries = {a.name: a for a in load_registry().agents}
    assert entries["paper_publisher"].profile == NO_LLM
    assert [n for n, e in entries.items() if e.profile == NO_LLM] == ["paper_publisher"]


def test_paid_opt_in_is_retained_and_defaults_false():
    """D7: the field stays (permission to configure a paid-PREFERRING default);
    it is NOT threaded into routing and does NOT gate the guarded paid tail."""
    assert all(a.paid_opt_in is False for a in load_registry().agents)
```

- [ ] **Step 2: Run it to verify it fails**

```bash
.venv/bin/python -m pytest tests/unit/test_profile_schema.py -q
```
Expected: FAIL — `ImportError: cannot import name 'ProfileName' from 'llmxive.types'`.

- [ ] **Step 3: Add `ProfileName` + migrate the entry schema**

In `src/llmxive/types.py`, above `AgentRegistryEntry`:

```python
#: The canonical requirement-profile names (spec 026 FR-012) plus the no-LLM
#: sentinel. Declared as a Literal HERE rather than imported from
#: llmxive.model_selection.profiles, because a runtime import would cycle
#: (model_selection/__init__ -> execute -> backends.router -> llmxive.types).
#: tests/unit/test_profile_schema.py asserts this stays in sync with PROFILES.
ProfileName = Literal[
    "cheap_structured",
    "standard_generation",
    "deep_review",
    "deep_code",
    "vision",
    "independent_review",
    "deterministic-no-llm",
]
```

Then replace lines 696-698 of `AgentRegistryEntry`:

```python
    profile: ProfileName
```

and narrow the `paid_opt_in` comment (D7 — it is NOT a routing ceiling):

```python
    # Default False (Constitution Principle IV free-first). True permits this
    # agent to configure a paid-PREFERRING default/profile, and is sanctioned
    # ONLY via the credit-managed Dartmouth daily-budget path (issue #295;
    # runtime-gated by LLMXIVE_PAID_OPT_IN + the live credit cap in
    # backends/credits.py), requiring written justification in the introducing
    # PR. It does NOT gate the platform's guarded paid FALLBACK: that tail is
    # governed process-wide by the credit guard (spec 026 SC-007(b)), exactly as
    # the legacy MODEL_FALLBACKS chain was.
    paid_opt_in: bool = False
```

- [ ] **Step 4: Rewrite all 54 registry entries**

For each agent in `agents/registry.yaml`, delete the `default_backend`, `fallback_backends` and
`default_model` keys and add `profile:` per this assignment (54 total):

```
deep_review (26):
  research_reviewer, paper_reviewer,
  paper_reviewer_writing_quality, paper_reviewer_logical_consistency,
  paper_reviewer_claim_accuracy, paper_reviewer_overreach,
  paper_reviewer_safety_ethics, paper_reviewer_scientific_evidence,
  paper_reviewer_statistical_analysis, paper_reviewer_code_quality_paper,
  paper_reviewer_data_quality_paper, paper_reviewer_text_formatting,
  paper_reviewer_figure_critic, paper_reviewer_jargon_police,
  research_reviewer_idea_quality, research_reviewer_creativity,
  research_reviewer_implementation_correctness,
  research_reviewer_implementation_completeness,
  research_reviewer_code_quality_research, research_reviewer_data_quality_research,
  research_reviewer_filesystem_hygiene,
  research_question_validator, reference_validator, proofreader,
  repository_hygiene, idea_selector

standard_generation (16):
  brainstorm, flesh_out, project_initializer, librarian, specifier, clarifier,
  planner, tasker, paper_initializer, paper_specifier, paper_clarifier,
  paper_planner, paper_tasker, paper_writing, task_atomizer, personality

deep_code (7):
  implementer, paper_implementer, llmxive_implementer, code_adapter,
  paper_figure_generation, latex_fix, paper_statistics

cheap_structured (4):
  latex_build, status_reporter, task_joiner, submission_intake

deterministic-no-llm (1):
  paper_publisher
```

`paper_reviewer_figure_critic` is `deep_review`, NOT `vision` (D5): the agent class does text
review; the vision call lives in `preprint_figures` (Task 4). Giving it `vision` would drop
`gemma-4`/`gpt-oss` from its fallback tail for no benefit.

Verify the counts before committing:

```bash
.venv/bin/python -c "
import yaml, collections
ags = yaml.safe_load(open('agents/registry.yaml'))['agents']
c = collections.Counter(a['profile'] for a in ags)
print(dict(c)); assert sum(c.values()) == 54, c
assert c['deep_review'] == 26 and c['standard_generation'] == 16
assert c['deep_code'] == 7 and c['cheap_structured'] == 4
assert c['deterministic-no-llm'] == 1
print('assignment OK')
"
```

- [ ] **Step 5: Migrate `SlashCommandContext`**

In `src/llmxive/speckit/slash_command.py`, replace the `default_backend` / `fallback_backends` /
`default_model` fields with a single `profile: str`. Task 6 updates its consumers; this task only
needs the dataclass plus the construction site in `graph.py` (which Task 1 left passing
`entry.default_model` directly — replace that with `profile=entry.profile`).

- [ ] **Step 6: Un-xfail the Task-2 test**

Remove the `@pytest.mark.xfail` marker from
`tests/unit/test_deterministic_no_llm.py::test_registry_dispatch_bypasses_no_llm_agents`.

- [ ] **Step 7: Run tests + regenerate the manifest**

```bash
.venv/bin/python -m pytest tests/unit/test_profile_schema.py tests/unit/test_deterministic_no_llm.py -q
.venv/bin/python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q
.venv/bin/python -m llmxive.model_selection.inventory
.venv/bin/python -c "
import json, collections
rows = json.load(open('specs/026-model-selection-consolidation/migration_manifest.json'))['entries']
s7 = [r for r in rows if r.get('owning_slice') == 7]
print(collections.Counter(r['category'] for r in s7))
assert not [r for r in s7 if r['category'] in ('registry', 'schema')], 'registry/schema rows remain'
print('161 registry + 3 schema rows CLEARED')
"
```

Expect a large test fallout here: every test double constructing `AgentRegistryEntry` with the old
fields now fails **loudly** at load time (the 267 `test_double` manifest rows are the inventory).
Fix them all — do not weaken the schema.

- [ ] **Step 8: Commit**

```bash
git add -A
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(026 Slice-7): AgentRegistryEntry expresses a capability profile (US5)

Clears all 161 registry + 3 schema manifest rows in one rewrite. default_backend
and fallback_backends were already IGNORED by route_chat (backend fallback has
been first-class in the selected chain since Slice 5) and every agent carried
identical values, so no per-agent information is lost.

ProfileName is a Literal declared in the schema layer rather than imported from
model_selection.profiles: a runtime import there would cycle through
model_selection/__init__ -> execute -> backends.router -> llmxive.types. A drift
test asserts the Literal and PROFILES stay in sync.

paid_opt_in is RETAINED with a narrowed docstring (D7): it permits a
paid-preferring default, and does NOT gate the guarded paid fallback, which stays
process-governed per SC-007(b).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 6: the 91 `field_consumer` sites

**Files (from the manifest — regenerate to get current line numbers):**
`agents/base.py` (5) · `agents/implementer.py` (12) · `agents/librarian.py` (12) ·
`agents/paper_reviewer.py` (3) · `agents/personality.py` (3) · `agents/submission_intake.py` (3) ·
`cli.py` (6) · `pipeline/graph.py` (4) · `paper_reprocess/{branch_code,branch_nocode,code_adapter}.py` (9) ·
`speckit/{tasks_cmd,slash_command,paper_tasks_cmd,plan_cmd,clarify_cmd,paper_clarify_cmd,paper_implement_cmd,paper_plan_cmd}.py` (34)

**Interfaces:**
- Consumes: `AgentRegistryEntry.profile` (Task 5), `SlashCommandContext.profile` (Task 5).
- Produces: no new API — every consumer stops reading the deleted fields.

**Granularity note:** this task is 91 instances of ONE mechanical transformation. The plan gives the
rule plus a worked exemplar rather than 91 code blocks; per-site blocks would be less reliable than
the rule (line numbers shift as you edit) and would not tell the implementer anything the rule does
not. The manifest is the checklist and the suite is the gate.

- [ ] **Step 1: Get the current work-list**

```bash
.venv/bin/python -c "
import json
rows = json.load(open('specs/026-model-selection-consolidation/migration_manifest.json'))['entries']
for r in sorted((r for r in rows if r.get('owning_slice')==7 and r['kind']=='field_consumer'),
                key=lambda r: (r['file'], r['line'])):
    print(f\"{r['file']}:{r['line']}  {r['symbol']}\")
" | tee /tmp/slice7_field_consumers.txt | wc -l
```

- [ ] **Step 2: Apply the transformation**

The rule: an argument triple becomes a single `profile`. Worked exemplar — `agents/base.py:152-159`
becomes:

```python
                response = chat_with_fallback(
                    attempt_messages,
                    profile=self.entry.profile,
                    temperature=self.chat_temperature,
                    max_tokens=self.chat_max_tokens,
                )
```

(`default_backend=`, `fallback_backends=` and `model=` are deleted, not renamed — `route_chat`
already ignored the first two, and the third is what the migration exists to remove.)

For a site holding the value on an object (e.g. a reviser storing `self._model`), rename the
attribute to `self._profile` and seed it from `entry.profile` — Task 7 covers the remaining
object-state cases, but fix any you touch here.

`agents/base.py:137-138` (the run-log seed) is Task 9's — leave it for now.

- [ ] **Step 3: Run the suite after each file**

```bash
.venv/bin/python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q
```

- [ ] **Step 4: Verify zero field consumers remain**

```bash
grep -rn "default_model\|fallback_backends\|entry\.default_backend" --include="*.py" src/llmxive/ || echo "CLEAN"
.venv/bin/python -m llmxive.model_selection.inventory
```

- [ ] **Step 5: Commit**

```bash
git add -A
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "refactor(026 Slice-7): 91 field consumers read entry.profile

Every default_backend=/fallback_backends=/model= argument triple collapses to a
single profile=. The first two were already ignored by route_chat; the third is
the pin this spec exists to remove.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 7: wrapper `profile` parameter + the 43 direct pins

**Files:**
- Modify: `src/llmxive/backends/router.py` — `_walker_route` (~:290-330), `chat_with_model_fallback` (:334), `reasoning_chat` (:361), `chat_with_fallback` (:387-396, :433-437)
- Modify: the 35 `model_id_literal` + 8 `module_constant` sites (see Step 2)

**Interfaces:**
- Produces: all four wrappers accept `profile: str = "standard_generation"`;
  `chat_with_fallback` **loses** `default_backend`, `fallback_backends`, `model`.
- Consumes: `route_chat(profile=…)`.

- [ ] **Step 1: Thread `profile` through all four wrappers**

Add `profile: str = "standard_generation"` to `_walker_route`, `chat_with_model_fallback`,
`reasoning_chat` and `chat_with_fallback`, forwarding it to `route_chat` in place of the two
hardcoded `profile="standard_generation"` literals at `router.py:320` and `:435`. The default keeps
every not-yet-migrated caller behaviourally identical. Once Step 2 lands, delete
`default_backend` / `fallback_backends` / `model` from `chat_with_fallback`'s signature.

- [ ] **Step 2: Migrate the pins by intent**

|profile|sites|
|-|-|
|`cheap_structured`|`claims/extract.py:26`, `claims/resolve.py:37`, `fill/extract.py:247`, `fill/service.py:98`, `librarian/query_extractor.py:141`, `librarian/math_classifier.py:223`, `librarian/data_source_discovery.py:52`, `execution/data_source.py:118`, `tools/summarize.py:248`|
|`deep_review`|`grounding/entailment.py:18`, `agents/grounding_guard.py:92`, `convergence/triage.py:198`, `convergence/engine.py:400`, `librarian/relevance_judge.py:234,347`, `agents/task_verifier.py:246,434`, `agents/living_document.py:81,514`|
|`deep_code`|`convergence/revisers/`: `implementer_reviser.py:214,222,230,307`, `paper_implement_reviser.py:167,178,189,197,249`, `spec_reviser.py:232,244`, `paper_spec_reviser.py:125,137`, `plan_reviser.py:216,227`, `tasks_reviser.py:139,150,161,172`, `flesh_out_reviser.py:139`|
|`standard_generation`|`agents/personality.py:68` (`MODEL_NAME`)|

Delete each `_DEFAULT_MODEL` / `_MODEL` / `MODEL_NAME` constant outright; replace `model=<pin>` with
`profile="<profile>"` at the call.

- [ ] **Step 3: Migrate object state and secondary call paths (NOT manifest-visible)**

The manifest finds model-id *literals*; it cannot see an interface that merely *permits* a pin.
Enumerate and fix:

```bash
grep -rn "model=\|_model\b\|model:" --include="*.py" src/llmxive/convergence/ src/llmxive/agents/ | grep -v "model_selection\|model_ref\|model_name\|model_tier"
```

Specifically: reviser/reviewer objects storing `self._model` → `self._profile`; the
self-consistency passes in `convergence/revisers/*`; the malformed-response retry loop
(`agents/base.py:151-159`) — it must reuse the same `profile`, not re-pin; and any helper still
exposing an optional `model=` parameter, which should be deleted rather than defaulted.

- [ ] **Step 4: Run + regenerate**

```bash
.venv/bin/python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q
.venv/bin/python -m llmxive.model_selection.inventory
```

- [ ] **Step 5: Commit**

```bash
git add -A
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "refactor(026 Slice-7): all four wrappers take profile; 43 direct pins migrated

chat_with_fallback — the PRIMARY registry path — hardcoded standard_generation at
router.py:435 and was missed by the original scope. All four wrappers now accept
profile, and chat_with_fallback drops its obsolete backend/model arguments.

Object state and secondary call paths are migrated too (reviser self-consistency,
the malformed-response retry loop, optional model= helper parameters): the
manifest scans for literals and cannot see an interface that merely permits a pin,
so the zero-row gate alone would not have caught these.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 8: `_MODEL_BUDGETS` → policy; `local.py` reclassification

**Files:**
- Modify: `src/llmxive/tools/summarize.py:45` (delete `_MODEL_BUDGETS`)
- Modify: `src/llmxive/model_selection/inventory.py` (classify `backends/local.py:37` as `canonical_layer`)
- Test: `tests/unit/test_summarize_budget_from_policy.py` (new)

- [ ] **Step 1: Write the failing test**

```python
"""_MODEL_BUDGETS was a second, drifting copy of per-model context limits."""
from __future__ import annotations

from llmxive.model_selection.policy import CAPABILITY_POLICY
from llmxive.tools.summarize import usable_budget_for


def test_budget_comes_from_the_capability_policy():
    assert usable_budget_for("openai.gpt-oss-120b") <= CAPABILITY_POLICY.max_context_tokens("gpt-oss")
    assert usable_budget_for("qwen.qwen3.5-122b") <= CAPABILITY_POLICY.max_context_tokens("qwen3.5")


def test_unknown_model_falls_back_conservatively():
    assert usable_budget_for("not.a-real-model") > 0
```

- [ ] **Step 2: Implement**

Delete `_MODEL_BUDGETS` and derive the budget from `policy.max_context_tokens(family)`, resolving
the family with `snapshot._family_of`. Preserve the existing safety margin (read `_usable_budget`
first and keep its ratio). **Assert the resolved budgets match the old table** for the two models
it covered before deleting it — this is the one §5 change with real behavior surface.

- [ ] **Step 3: Reclassify `local.py:37` in `inventory.py`**

`backends/local.py:37 list_models` declares the local backend's OWN inventory — a snapshot *input*,
not a selection pin. Deleting it would blind the composite snapshot (SC-010). Add it to the
`canonical_layer` classification beside `dartmouth.py:86 _REASONING_MODELS`, with that reason as a
comment.

- [ ] **Step 4: Run + regenerate + commit**

```bash
.venv/bin/python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q
.venv/bin/python -m llmxive.model_selection.inventory
git add -A
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "refactor(026 Slice-7): summarize budgets read the policy; local inventory is canonical

_MODEL_BUDGETS was a second copy of per-model context limits that could drift from
the capability policy (Constitution I). backends/local.py's list_models is
reclassified canonical_layer: it declares the local backend's own inventory, so
deleting it would blind the composite snapshot (SC-010).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 9: run-log attribution becomes nullable (D4)

**Files:**
- Modify: `src/llmxive/types.py` (`RunLogEntry.backend`, `.model_name` + a validator)
- Modify: `src/llmxive/agents/base.py:137-138`
- Test: `tests/unit/test_runlog_attribution.py` (new)

**Interfaces:**
- Produces: `RunLogEntry.backend: BackendName | None = None`, `model_name: str | None = None`, with
  a `model_validator` requiring BOTH when `outcome is Outcome.SUCCESS`.

- [ ] **Step 1: Write the failing test**

```python
"""A run log records the model that ANSWERED — never one invented before the call."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from llmxive.types import BackendName, Outcome, RunLogEntry


def _entry(**kw):
    now = datetime.now(UTC)
    base = dict(
        run_id="r1", entry_id="e1", agent_name="brainstorm", project_id="PROJ-001-x",
        task_id="t1", inputs=[], outputs=[], prompt_version="1.0.0",
        started_at=now, ended_at=now, outcome=Outcome.SUCCESS,
        backend=BackendName.DARTMOUTH, model_name="qwen.qwen3.5-122b",
        cost_estimate_usd=0.0,
    )
    base.update(kw)
    return RunLogEntry(**base)


def test_failure_before_any_call_records_no_attribution():
    e = _entry(outcome=Outcome.FAILURE, backend=None, model_name=None,
               failure_reason="BackendUnavailable")
    assert e.backend is None and e.model_name is None


def test_success_requires_both_fields():
    with pytest.raises(ValueError):
        _entry(backend=None)
    with pytest.raises(ValueError):
        _entry(model_name=None)


def test_success_with_both_is_valid():
    assert _entry().model_name == "qwen.qwen3.5-122b"
```

- [ ] **Step 2: Run it — expect FAIL** (`backend=None` currently violates the non-optional type).

- [ ] **Step 3: Implement**

```python
    backend: BackendName | None = None
    model_name: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _attribution_on_success(self) -> RunLogEntry:
        # A SUCCESSFUL run must name the model that actually answered; a run that
        # failed before any ChatResponse has nothing truthful to record. Seeding
        # from a registry default (pre-spec-026) invented a model for a call that
        # may never have happened — and this field feeds paper authorship.
        if self.outcome is Outcome.SUCCESS and (self.backend is None or not self.model_name):
            raise ValueError("a SUCCESS run-log entry must record backend and model_name")
        return self
```

In `src/llmxive/agents/base.py`, replace lines 137-138 with `backend_used: BackendName | None = None`
/ `model_used: str | None = None`. The success path already overwrites both from
`response.backend`/`response.model` at lines 162-163.

- [ ] **Step 4: Verify the downstream consumers**

```bash
.venv/bin/python -m pytest tests/unit/test_authors.py tests/unit/test_runlog_producer.py tests/unit/test_web_data_recent_activity.py -q
```
`state/runlog.py:237` already filters non-SUCCESS before building paper authorship and
`pipeline/authors.py:207-213` already null-guards both fields, so no consumer change is expected —
confirm rather than assume.

- [ ] **Step 5: Run all + commit**

```bash
.venv/bin/python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q
git add -A
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "feat(026 Slice-7): run-log attribution is nullable, required on SUCCESS

base.py seeded backend/model from the registry default before the call. With the
registry no longer naming a model there is nothing truthful to seed, and inventing
one would write a model that never ran into a field feeding paper authorship. Both
fields become optional with a validator requiring BOTH on SUCCESS (rejecting
half-populated successful entries). Mirrors the existing ReviewRecord idiom
(types.py:618).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 10: US5 AC1 + per-profile projections + AC4 + README

**Files:**
- Test: `tests/unit/test_us5_ac1_primary_preservation.py` (new), `tests/unit/test_profile_projections.py` (new)
- Modify: `tests/unit/test_config_consistency.py` (AC4 rewrite), `README.md`

- [ ] **Step 1: Write AC1 — all 53 LLM agents preserve their leader**

```python
"""US5 AC1 (BINDING): under the fixed migration snapshot every LLM agent's chain
leader equals its pre-migration default."""
from __future__ import annotations

import pytest

from llmxive.agents.registry import load_registry
from llmxive.model_selection.profiles import build_requirement
from llmxive.model_selection.select import select
from llmxive.model_selection.types import CallBudget
from tests.unit.test_model_selection_select import _snapshot

LEGACY_DEFAULT = "qwen.qwen3.5-122b"
NO_LLM = "deterministic-no-llm"
_CB = CallBudget(max_input_tokens=1000, max_output_tokens=500)

_LLM_AGENTS = [a for a in load_registry().agents if a.profile != NO_LLM]


def test_there_are_53_llm_agents_and_one_exempt():
    assert len(_LLM_AGENTS) == 53
    assert [a.name for a in load_registry().agents if a.profile == NO_LLM] == ["paper_publisher"]


@pytest.mark.parametrize("agent", _LLM_AGENTS, ids=lambda a: a.name)
def test_every_llm_agent_preserves_its_primary(agent):
    chain = select(build_requirement(agent.profile, _CB), _snapshot())
    assert chain.candidates[0].model_ref.model_id == LEGACY_DEFAULT


def test_no_llm_agent_never_reaches_selection():
    from llmxive.model_selection.route import DETERMINISTIC_NO_LLM, route_chat
    from llmxive.backends.base import ChatMessage

    with pytest.raises(ValueError):
        route_chat([ChatMessage(role="user", content="x")],
                   profile=DETERMINISTIC_NO_LLM, max_tokens=10)
```

- [ ] **Step 2: Write the per-profile composite projections (§2.1)**

Against a **composite** snapshot (the 3 free Dartmouth models **plus** the local `qwen2.5` candidate
**plus** the paid `claude-haiku` tail, opt-in ON with headroom) assert each profile's exact chain,
so candidate caps express intent and are verified rather than homogenized:

```python
def test_standard_generation_keeps_the_free_chain_plus_the_guarded_paid_tail():
    ids = [c.model_ref.model_id for c in select(
        build_requirement("standard_generation", _CB, allow_paid=True), _composite())
    .candidates]
    assert ids[:3] == ["qwen.qwen3.5-122b", "google.gemma-4-31B-it", "openai.gpt-oss-120b"]
    assert "anthropic.claude-haiku-4-5-20251001" in ids, "paid tail truncated by max_candidates"
```

Write the same explicit assertion for each remaining profile — do not collapse them into a loop or
leave them as "repeat for the others"; each profile's intended chain is a separate reviewed claim:

```python
def test_deep_review_keeps_the_free_chain_plus_the_guarded_paid_tail():
    ids = _ids(select(build_requirement("deep_review", _CB, allow_paid=True), _composite()))
    assert ids[:3] == ["qwen.qwen3.5-122b", "google.gemma-4-31B-it", "openai.gpt-oss-120b"]
    assert "anthropic.claude-haiku-4-5-20251001" in ids


def test_deep_code_keeps_the_free_chain_plus_the_guarded_paid_tail():
    ids = _ids(select(build_requirement("deep_code", _CB, allow_paid=True), _composite()))
    assert ids[:3] == ["qwen.qwen3.5-122b", "google.gemma-4-31B-it", "openai.gpt-oss-120b"]
    assert "anthropic.claude-haiku-4-5-20251001" in ids


def test_cheap_structured_keeps_the_free_chain_plus_the_guarded_paid_tail():
    ids = _ids(select(build_requirement("cheap_structured", _CB, allow_paid=True), _composite()))
    assert ids[:3] == ["qwen.qwen3.5-122b", "google.gemma-4-31B-it", "openai.gpt-oss-120b"]
    assert "anthropic.claude-haiku-4-5-20251001" in ids


def test_vision_leads_with_qwen35_and_keeps_the_vl_peer():
    ids = _ids(select(build_requirement("vision", _CB), _composite()))
    assert ids[0] == "qwen.qwen3.5-122b"
    assert "qwen.qwen3-vl:32b" in ids
    # gemma-4/gpt-oss have no vision attribution and must NOT appear
    assert "google.gemma-4-31B-it" not in ids and "openai.gpt-oss-120b" not in ids


def test_independent_review_requires_a_different_family():
    from llmxive.model_selection.types import IndependenceBaseline

    ids = _ids(select(build_requirement(
        "independent_review", _CB,
        independence_against=IndependenceBaseline(families=frozenset({"qwen3.5"})),
    ), _composite()))
    assert "qwen.qwen3.5-122b" not in ids, "required family independence not honored"
```

**Raise `max_candidates` to 8 on `cheap_structured`, `deep_review`, `deep_code` and `vision` in
`profiles.py`** so the guarded paid tail stays reachable — the as-built behavior, since every caller currently routes through
`standard_generation` (cap 8). If a profile is deliberately given a narrower surface, record it in
the commit message as an intentional delta with its rationale.

- [ ] **Step 3: Rewrite `test_config_consistency.py` (AC4)**

Delete the imports at lines 25-26 (`KNOWN_FREE_MODELS`, `MODEL_FALLBACKS`) and rewrite:

- `test_registry_models_are_free_unless_paid_opt_in` → every agent's `profile` is canonical; under a
  paid-opt-in-**OFF** snapshot every profile's chain is free-only; with opt-in **ON and headroom**
  the guarded paid tail appears — **independent of `entry.paid_opt_in`** (SC-007(b), D7).
- `test_model_fallback_chains_are_free` → the **policy** admits no paid family except the sanctioned
  `claude-haiku-4-5`.
- `test_every_llm_registry_model_has_a_fallback_chain` → every profile resolves to ≥2 candidates.
- `test_readme_model_names_match_registry` → re-point at `CAPABILITY_POLICY`; the registry no longer
  names models.

- [ ] **Step 4: Update `README.md`**

Update the "Models & cost" section so its model prose matches the policy table (the rewritten test
enforces this). Do not leave `default_model` prose describing the registry.

- [ ] **Step 5: Run + commit**

```bash
.venv/bin/python -m pytest tests/unit/test_us5_ac1_primary_preservation.py tests/unit/test_profile_projections.py tests/unit/test_config_consistency.py -q
.venv/bin/python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q
git add -A
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "test(026 Slice-7): US5 AC1 + AC4 + per-profile projections (BINDING)

AC1: all 53 LLM agents keep qwen.qwen3.5-122b as their leader under the fixed
migration snapshot; paper_publisher is exempt. Holds by construction (qwen3.5 is
tier 3 across cheap/standard/deep and now vision), but the test keeps it a real
guard if the policy shifts.

AC4: test_config_consistency validates capability profiles instead of the
KNOWN_FREE_MODELS/MODEL_FALLBACKS allowlists. The paid assertion follows the
PRODUCTION routing path: the guarded tail appears iff the process snapshot is
opted in with headroom, independent of entry.paid_opt_in (SC-007(b)).

Per-profile composite projections verify each candidate cap against a composite
snapshot rather than homogenizing them; caps rise to 8 on the text profiles to
preserve as-built breadth (every caller routes through standard_generation, cap 8,
today).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 11: record the sanctioned deltas in `spec.md`

**Files:** Modify `specs/026-model-selection-consolidation/spec.md`

Two Slice-7 semantics currently exist only in the design doc, while the spec says the only general
migration delta is Gemma-3→Gemma-4 and US6's sanctioned text says tier 1 excludes **the registered
default**. Unrecorded, a future review would correctly flag the implementation as drift.

- [ ] **Step 1: Amend US6's "Sanctioned migration delta" paragraph**

Tier 1 changes from "exclude the registered default" to **"exclude whatever `select()` ranks
first"** — necessarily, since the registered default ceases to exist in Slice 7. Note that behavior
is identical under the fixed migration snapshot (the leader *is* the former registered default), and
that it is implemented as a two-pass pure translation in `route_chat`, leaving `select()` untouched.

- [ ] **Step 2: Add a sanctioned Slice-7 delta beside the Gemma correction (Assumptions)**

`qwen3.5` gains the `vision` capability, widening vision eligibility and incrementing
`SELECTION_POLICY_VERSION` to 2. Record that it was **real-call verified 2026-07-19** (image
understanding, not payload acceptance) per Constitution II, and cite
`tests/real_call/test_vision_real.py`.

- [ ] **Step 3: Amend SC-007**

Add: the vision projection's leader is `qwen.qwen3.5-122b` with `qwen.qwen3-vl:32b` as its peer.

- [ ] **Step 4: Commit**

```bash
git add -A
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "docs(026): record the sanctioned Slice-7 deltas in the binding spec

Two new semantics lived only in the design doc while spec.md still said the only
general delta was Gemma-3->Gemma-4 and US6 said tier 1 excludes 'the registered
default'. Recording them as explicit sanctioned deltas (with the real-call
evidence for the vision attribution) so a future review reads them as approved
rather than as drift.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

### Task 12: manifest regeneration + full-suite gate

- [ ] **Step 1: Regenerate and prove zero surviving rows**

```bash
.venv/bin/python -m llmxive.model_selection.inventory
.venv/bin/python -c "
import json, collections
rows = json.load(open('specs/026-model-selection-consolidation/migration_manifest.json'))['entries']
s7 = [r for r in rows if r.get('owning_slice') == 7]
print('owning_slice==7:', len(s7), dict(collections.Counter(r['category'] for r in s7)))
assert not s7, f'Slice 7 INCOMPLETE — {len(s7)} rows remain: {s7[:5]}'
print('SLICE 7 WORK-LIST FULLY RESOLVED')
"
```

- [ ] **Step 2: Full non-slow suite + lint**

```bash
.venv/bin/python -m pytest tests/unit tests/contract tests/integration -m "not slow" -q
.venv/bin/ruff check src tests
git diff --check
```

- [ ] **Step 3: Real-call verification (needs `DARTMOUTH_CHAT_API_KEY`)**

```bash
LLMXIVE_REAL_TESTS=1 .venv/bin/python -m pytest tests/real_call/test_vision_real.py -v
```

- [ ] **Step 4: Confirm no push happened**

```bash
git log --oneline origin/main..HEAD | wc -l   # local commits, unpushed — expected
git status -sb | head -1
```

- [ ] **Step 5: Commit the regenerated manifest**

```bash
git add -A
PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit -m "chore(026 Slice-7): regenerate migration manifest — zero owning_slice==7 rows

All 300 Slice-7 contract rows resolved (136 migration_target + 161 registry +
3 schema). Full non-slow suite green; vision real calls verified.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git log --oneline -1
```

---

## Plan self-review

**Spec coverage.** US5 AC1 → T10; AC2/AC3 → T2 + T10; AC4 → T10. US7 direct pins → T7, T8.
FR-012 (6 named profiles at every call site) → T5, T6, T7. FR-013 (registry/tier-ladder resolve
through the mechanism) → T1, T5, T6. FR-010 (execute safeguards preserved) → T3's
`UnsupportedFeatureError` SKIP class. FR-003 (cost bound) → T3's image upper bound. SC-007 →
T10's projections. SC-008 vision tier → T4's second real call. SC-010 (no hidden second
selection path) → T8's `local.py` reclassification. Slice-8 items (`enforcement.py`,
`DEFAULT_MODEL`/`MODEL_FALLBACKS`/`KNOWN_FREE_MODELS` deletion) are deliberately **out of scope**.

**Type consistency.** `profile` is a `str`-valued `ProfileName` everywhere (T5 defines, T6/T7
consume). `RequirementOverrides.exclude_leader` (T1) is consumed by T4's real-call test.
`TierConstraint.to_overrides()` takes no arguments after T1 — T1 Step 7 updates the two existing
call sites. `ImagePart`/`TextPart` (T3) are consumed by T4. `tokens.MAX_IMAGE_DIMENSION_PX` is
defined in T3 and referenced by T3's `ImagePart.__post_init__` and T4's `_render_png` downscale.

**Known granularity exception.** Tasks 6 and 7 give a transformation rule plus a worked exemplar
rather than 91 and 43 individual code blocks. This is deliberate: the edits are instances of one
mechanical change, line numbers shift as you work, and the manifest + suite are the real gate. Every
*contract-defining* change in this plan (new types, exceptions, validators, tests) is given as
complete code.

**Ordering constraint.** T3 must precede T4 (the vision call needs `ImagePart`). T5 must precede
T6 (consumers need `entry.profile`). T1 must precede T4 (the real-call test uses `exclude_leader`).
T2's layer-1 test xfails until T5.
