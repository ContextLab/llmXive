# Phase 0 Research: Paper Review Convergence

## Open questions deferred from /speckit-clarify (now resolved here)

### R1. Action-item ID generation strategy

**Decision**: `id = sha1(canonicalize(text))[:12]` where `canonicalize` lowercases, strips punctuation+whitespace runs, removes section/figure references (e.g., "in Section 3.2" → ""), and applies a small stop-word filter. The resulting 12-char hex is the stable ID.

**Rationale**:
- Stability across re-reviews depends on the SAME concern producing the SAME hash. Canonicalization absorbs cosmetic LLM variation (capitalization, "missing β_k value" vs "β_k value is missing", "in Section 4.1" vs "in Section 4.2 after the table was renumbered").
- 12 hex chars = 48 bits of ID space; collision probability across ≤200 action items per project is effectively zero (birthday bound: ~16M items needed for 50% collision chance).
- Deterministic + content-derived → no need for a stateful ID-allocator; new reviews can compute IDs locally without consulting prior reviews.
- Implementation: a single helper `action_item_id(text: str) -> str` in `src/llmxive/types.py` so callers don't reinvent canonicalization.

**Alternatives considered**:
- *Random UUIDs*: rejected — re-reviewer would mint a new UUID for the same concern, defeating SC-005 (stable IDs).
- *Sequential numbers per project*: rejected — requires a stateful counter, races between concurrent reviewers, and breaks the "compute locally" property.
- *Semantic embedding similarity*: rejected — depends on a model, expensive at re-review time, hard to make deterministic across model versions.

### R2. Auto-plan pipeline invocation mechanism

**Decision**: The 5-stage auto-plan runs as **a subprocess driver in a single Python process**, invoked by the advancement evaluator when it transitions a project to `paper_revision_in_progress`. The driver shells out to the speckit skill scripts (`.specify/scripts/bash/setup-plan.sh`, `.specify/scripts/bash/check-prerequisites.sh`, etc.) and to the speckit-skill-equivalent code paths under `src/llmxive/speckit/` (which already exist for Phase 3 / spec 011).

The driver is `revision_planner.py`:

```python
def run_revision_pipeline(project_id: str, action_items: list[ActionItem],
                          revision_kind: Literal["paper_writing", "paper_science"]) -> RevisionSpecResult:
    """Runs specify → clarify → plan → tasks → analyze.
    Returns a RevisionSpecResult dataclass with the new spec dir + status.
    Raises RevisionPlanningError if any stage fails.
    """
```

**Rationale**:
- Spec 011 already added `src/llmxive/speckit/slash_command.py` and `src/llmxive/speckit/_inspection.py` to drive Specifier + Clarifier programmatically with full inspection records. Reusing those keeps the single-source-of-truth principle intact.
- Subprocess (not asyncio task) lets each stage have its own working directory + env, mirroring how the human-driven pipeline works.
- Single process (not multi-machine queue) keeps it simple at current scale (~10s of papers in flight).
- Failure isolation: if stage 3 of 5 fails, the driver writes a `paper_revision_blocked` diagnostic and returns — no partial state corruption.

**Alternatives considered**:
- *GitHub Actions workflow_dispatch per stage*: rejected — adds 5 round-trips to GitHub per revision, slow + brittle.
- *In-process LLM calls (no shell-out)*: rejected — the speckit scripts already exist and are the canonical entry points; bypassing them duplicates logic.

### R3. Recovery path from `paper_revision_blocked`

**Decision**: `paper_revision_blocked` is **terminal until human intervention**. The state surfaces in the web dashboard's diagnostics tab with the analyzer's last report attached. A human can:

1. Manually edit the action items file under `state/revisions/<PROJ-ID>/<round-N>.yaml` to remove or rephrase items the analyzer can't resolve.
2. Manually transition the project back to `paper_minor_revision` (or whichever was the source) via a CLI command `llmxive project unblock <PROJ-ID>` — which validates the human did something AND resets the round counter.
3. Manually transition to `brainstormed` (reject) if the situation is genuinely unrecoverable.

**Rationale**:
- Auto-retry of a stuck analyzer is wasteful (same input → same stuck output).
- This matches the constitution's "fail fast → actionable exception" principle — the analyzer's findings ARE the actionable diagnostic.
- The `unblock` CLI command is small (a state-file rewrite + a history entry) and gives operators a clear escape valve without rewriting the gate logic.

**Alternatives considered**:
- *Auto-retry after N ticks*: rejected — analyzer is deterministic given inputs; retry without input change is pointless.
- *Auto-escalate to `paper_major_revision_science`*: rejected — masks the planning failure as a science failure; loses diagnostic signal.
- *Auto-transition to `HUMAN_INPUT_NEEDED`*: rejected — `paper_revision_blocked` is more specific and surfaces the diagnostic better. (Note: this is an intentional separate state; HUMAN_INPUT_NEEDED is the existing generic blocker.)

### R4. Re-review prompt structure

**Decision**: The shared `agents/prompts/_shared/rereview_block.md` snippet contains:

```
## Re-Review Protocol (prior action items present)

You have reviewed this paper before. Your prior review's action items are listed
below with their stable IDs. For this re-review, your job is REDUCED to two
questions:

(a) For each prior action item: has it been ADEQUATELY ADDRESSED in the current
    revision?
(b) Has the revision INTRODUCED ANY NEW ISSUES?

Output rules:
- If (a) = YES for ALL prior items AND (b) = NO new issues → verdict: accept.
  Your `action_items` list MUST be empty.
- If (a) = NO for one or more prior items → verdict: minor_revision (or
  major_revision_writing if the unaddressed items are writing-class, or
  major_revision_science if science-class, or fundamental_flaws if fatal-class).
  Your `action_items` list MUST contain the unaddressed items with their
  ORIGINAL IDs preserved (do NOT mint new IDs for re-flags of the same
  concern). Append any NEW issues (with newly-generated IDs) AFTER the
  re-flagged items.
- DO NOT generate fresh independent critique. This is a diff-check, not a
  full review.

Prior action items (most recent prior review for THIS specialist):
{prior_action_items_yaml}
```

**Rationale**:
- Putting it in `_shared/` and templating-in via `{prior_action_items_yaml}` keeps the protocol identical across all 12 specialists (single source of truth).
- Explicit "ADEQUATELY ADDRESSED" + "REDUCED to two questions" + "DO NOT generate fresh independent critique" is the load-bearing language — without all three, models drift back into full critique on the next round.
- Only the latest prior review (per specialist) is shown — older rounds are stale and inflating the prompt with them just confuses the diff-check.

**Alternatives considered**:
- *Single round-trip with system-message-only instructions*: rejected — the model needs the prior items in-prompt to actually compare against them.
- *Include ALL prior rounds*: rejected — token-budget pressure + the most recent round is what defines "what was supposed to be fixed in this iteration".

### R5. Severity classification responsibility

**Decision**: The reviewer LLM assigns severity at emission time, per action item. The LLM prompt provides explicit definitions:

- `writing` — the issue can be fixed by editing the manuscript text alone (typos, clarity, missing citation, unclear caption, terminology drift, jargon).
- `science` — the issue requires re-running an experiment, re-analyzing data, adding a control condition, or otherwise touching the underlying research artifact. Cannot be fixed by text edits.
- `fatal` — the central claim is unsupportable, the data is unrecoverable, the design has no scientific merit. The paper cannot be salvaged by any revision; the underlying idea should return to the backlog.

The advancement evaluator trusts this classification and routes accordingly (writing → paper_minor_revision; science → paper_major_revision_science; fatal in ANY item → reject to BRAINSTORMED).

**Rationale**:
- The LLM is the only entity with semantic context about what the issue is. Post-hoc reclassification is brittle.
- Trust matches the existing pattern of trusting the LLM's `verdict` field.
- For the rare case where a `writing` item is mis-classified, the worst outcome is a writing-revision pipeline gets kicked off — which is cheaper than under-routing.

**Alternatives considered**:
- *Post-hoc keyword classifier*: rejected — adds a parallel classifier (constitution violation: single source of truth) and ML drift over time.
- *Per-specialist defaults (jargon_police always writing, scientific_evidence always science)*: rejected — wrong for cross-cutting issues; jargon_police occasionally finds a term that hides a substantive claim.

## Existing-codebase reuse audit

Per Constitution I (single source of truth), before adding new modules we verified:

| New module | Existing equivalent? | Decision |
|-|-|-|
| `revision_planner.py` | `src/llmxive/speckit/slash_command.py` (Phase 3) handles individual stage runs | NEW module reuses slash_command.py as its building block; no parallel implementation. |
| `upstream_feedback.py` | none — annotation file is feature-new | NEW (small, ~50 LOC). |
| `_shared/rereview_block.md` | none — no shared snippet pattern exists yet | NEW (~20 LOC); introduces an `_shared/` convention so future shared snippets follow it. |
| Action item ID helper | none | Added to existing `src/llmxive/types.py` (where the schema lives). |
| `paper_revision_in_progress` stage | `Stage` enum in `src/llmxive/types.py` | EXTEND enum; no parallel state machine. |
| Three-way routing | `advancement.py` already has paper_review handler | MODIFY existing handler; no parallel `advancement_v2.py`. |

## Out-of-scope (per spec Assumptions)

- The implementation-agent that consumes `ready_for_implementation` flags. The spec contract is "we set the flag"; the consumer is a separate workstream.
- Real-call hallucination detection on specialist reviews (covered elsewhere).
- Web dashboard UI changes for `paper_revision_in_progress` / `paper_revision_blocked` states (data is regenerated; UI rendering of new states is a follow-up if dashboard breaks).
