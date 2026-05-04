# Phase 0 Research: Phase 1 (Idea Lifecycle) Diagnostic

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-05-04

This document records the small-scope repo introspection needed to translate the
spec's mechanism choices into concrete implementation tasks. The Technical
Context in `plan.md` had no `NEEDS CLARIFICATION` markers; what remained were
pure mechanical look-ups (CLI signatures, file schemas, citation formats).
Findings are recorded here so future-spec authors don't have to re-introspect.

## Decision 1: Orchestrator CLI signature

**Decision**: Use `python -m llmxive run --max-tasks N [--project <id>] [--stage <stage>]` for every agent invocation. Cohort growing for brainstorm uses a fresh `run --max-tasks 1` per seed (the scheduler picks a fresh project slot when no `--project` is given).

**Rationale**: Confirmed by reading `src/llmxive/cli.py` — the `_cmd_run` function loops over `--max-tasks` calls to `run_one_step`, with `--project` filtering to a specific project ID and `--stage` filtering to projects at a given lifecycle stage. The CLI usage string in the file's module docstring shows: `run --max-tasks N [--project X --stage S]`. There is also a separate `_cmd_brainstorm` subcommand that auto-seeds N brainstormed-stage state files; we do **not** use this — we want every agent run to go through the production `run` path so the diagnostic faithfully replicates production behavior.

**Alternatives considered**:
- `python -m llmxive brainstorm --count 8` (the dedicated subcommand) — rejected because it bypasses the scheduler / state-machine and isn't the production code path.
- Direct calls into `llmxive.agents.brainstorm.BrainstormAgent` — rejected because it bypasses the orchestrator entirely, defeating the point of the diagnostic.

## Decision 2: Idea-artifact filename convention

**Decision**: The idea artifact is **`projects/<id>/idea/<slug>.md`** (slug is the project's title-derived slug), NOT `projects/<id>/idea/idea.md`. The spec/contracts must use this convention.

**Rationale**: Confirmed by `ls projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/idea/` → `mechanistic-interpretability-of-ctcf-bin.md` (single file, slug-named). Same pattern in `PROJ-141-evaluating-the-impact-of-code-generation/idea/evaluating-the-impact-of-code-generation.md`. Phase 0's earlier draft references to `idea.md` and `seed.md` are **incorrect** — there is no separate `seed.md`; brainstorm writes the same slug-named file that flesh_out then expands in place.

**Implication for spec**: An update is needed — references to `idea/seed.md` and `idea/idea.md` in spec.md / plan.md / contracts must be canonicalized to `idea/<slug>.md`. (We'll fix this in the data-model.md and contracts and amend spec.md once /speckit-plan returns control.)

**Alternatives considered**: None — this is just observed reality.

## Decision 3: State YAML schema

**Decision**: Treat the following fields as canonical for `state/projects/<id>.yaml` (verified against existing entries):

```yaml
id: PROJ-NNN-<slug>                      # required
title: <human-readable title>            # required
field: <field name>                      # required (set by brainstorm)
current_stage: <stage name>              # required, drives advancement
last_run_id: <uuid> | null               # last run that touched this project
last_run_status: <"success"|"failure"> | null
assigned_agent: <agent name> | null      # set during a run
created_at: <ISO-8601 UTC>               # required
updated_at: <ISO-8601 UTC>               # required
failed_stage: <stage name> | null        # set on hard failures
human_escalation_reason: <str> | null    # set when human input needed
revision_round: <int>                    # 0 by default
points_paper: {}                         # review points by reviewer
points_research: {}                      # review points by reviewer
speckit_paper_dir: <path> | null         # set after Spec Kit init
speckit_research_dir: <path> | null      # set after Spec Kit init
artifact_hashes: {}                      # filename → sha256
```

A companion `state/projects/<id>.history.jsonl` may exist with one append-only line per stage transition (observed in PROJ-002, PROJ-003).

**Rationale**: Read 3 existing state YAMLs (PROJ-001, PROJ-141, PROJ-160) — all share the same field set. The `revision_round` field is interesting: the pipeline-status notes from 2026-05-04 say it's "set but never incremented" — this is a known issue tracked separately, not a Phase-1 concern.

**Alternatives considered**: We could synthesize our own state schema for sibling iterations, but that violates Constitutional Principle I (Single Source of Truth). We will reuse this schema verbatim for sibling projects.

## Decision 4: Run-log JSONL schema

**Decision**: Each run-log entry under `state/run-log/<YYYY-MM>/<run-id>.jsonl` has the following fields:

```json
{
  "run_id": "<uuid>",
  "entry_id": "<uuid>",
  "parent_entry_id": "<uuid>" | null,
  "task_id": "<uuid>",
  "agent_name": "<registry agent name>",
  "backend": "<registry backend name>",
  "model_name": "<model id>",
  "prompt_version": "<semver>",
  "project_id": "PROJ-NNN-<slug>",
  "started_at": "<ISO-8601 UTC>",
  "ended_at": "<ISO-8601 UTC>",
  "outcome": "success" | "failure",
  "failure_reason": "<str>" | null,
  "inputs": ["<path>", ...],
  "outputs": ["<path>", ...],
  "cost_estimate_usd": <float>
}
```

**Rationale**: Verified by `head -5` over multiple JSONL files in `state/run-log/2026-05/`. Multiple entries per run-id are possible (one per agent invocation within a single orchestrator step), distinguished by `entry_id` and chained via `parent_entry_id`. The diagnostic report will quote these blocks verbatim and reference them by `entry_id`.

**Alternatives considered**: None — schema is fixed by existing pipeline code.

## Decision 5: Sibling-spawn mechanics

**Decision**: To spawn `PROJ-NNN-<slug>-iterN` from canonical `PROJ-NNN-<slug>`:

1. Create directory `projects/PROJ-NNN-<slug>-iterN/idea/`.
2. Copy `projects/PROJ-NNN-<slug>/idea/<slug>.md` (the brainstormed seed) → `projects/PROJ-NNN-<slug>-iterN/idea/<slug>.md`. (For flesh_out / idea_selector iterations, the sibling starts at the **brainstorm output** — i.e., the seed before flesh_out's expansion. This guarantees every iteration has the same input and the diff is purely the agent's response to the prompt patch.)
3. Write `state/projects/PROJ-NNN-<slug>-iterN.yaml` with:
   - `id: PROJ-NNN-<slug>-iterN`
   - `title: <same as canonical>`
   - `field: <same as canonical>`
   - `current_stage: brainstormed` (so the orchestrator routes the next agent appropriately based on which stage we're testing)
   - `created_at: <now>`, `updated_at: <now>`, all other fields default
4. Do **not** copy the canonical's `state/projects/<id>.history.jsonl`.
5. Do **not** reuse the canonical's `last_run_id` — the sibling gets fresh run-log entries.

**Rationale**: Sibling project must be a fresh, replayable starting point. Copying the seed gives flesh_out / idea_selector the same input as the canonical iter1 had; resetting state to `brainstormed` lets the orchestrator pick `flesh_out` (or `idea_selector` after flesh_out finishes) as the next agent for that sibling.

**Alternatives considered**:
- Copy the canonical's full `idea/<slug>.md` (post-flesh_out expansion) instead of the seed — rejected because then flesh_out would refuse to re-run (state already at `flesh_out_complete`) and we'd be back to needing state surgery.
- Snapshot the canonical's full project directory — rejected because we don't want flesh_out's prior output to bias the new run; the sibling must start clean from the seed.

## Decision 6: Citation formats produced by `flesh_out`

**Decision**: The citation resolver MUST handle three citation formats observed in existing `idea/<slug>.md` files:

1. **Markdown link to arXiv abs page**: `[Title (year)](http://arxiv.org/abs/<id>v<n>)` or `[Title (year)](https://arxiv.org/abs/<id>)`. Resolution: extract arXiv ID, query arXiv API.
2. **Markdown link to DOI**: `[Title (year)](https://doi.org/<doi>)`. Resolution: HTTP HEAD on `https://doi.org/<doi>` (which redirects); accept any 2xx final status.
3. **Markdown link to raw URL**: `[Title or repo (year)](https://...)`. Resolution: HTTP HEAD on the URL; accept any 2xx final status.

Plus a fourth case for completeness:
4. **Inline raw URL** (no Markdown wrapper): `(GitHub https://github.com/...)`. Resolution: HTTP HEAD on extracted URL.

**Rationale**: Confirmed by reading `projects/PROJ-141-*/idea/<slug>.md` — all five citations in that file are Markdown-linked arXiv abs pages or DOIs. Raw URLs appear in the methodology section (not citations proper) but should still be resolved for completeness.

**Alternatives considered**:
- Limit to arXiv + DOI only — rejected because it would miss raw-URL citations entirely.
- Use a dedicated citation parser (e.g., `bibtexparser`) — rejected because flesh_out outputs Markdown, not BibTeX, and a 30-line regex extraction is sufficient.

## Decision 7: Failure-mode induction technique

**Decision**: For the FR-015 induced-failure run, the cleanest technique is to **temporarily set `DARTMOUTH_CHAT_API_KEY=invalid_<random>` in the shell environment for one orchestrator invocation**, run brainstorm, observe the resulting run-log entry records `outcome: failure` with a populated `failure_reason`, and confirm no sibling project's state YAML advances past `brainstormed`.

**Rationale**:
- Reversible (just `unset` after the test) — no permanent repo change.
- Exercises the same code path real backend outages would exercise.
- Doesn't require touching `agents/registry.yaml` (which would risk leaving production code in a broken state if the test crashes mid-run).
- Output is observable in run-log JSONL without any additional instrumentation.

**Alternatives considered**:
- Mis-name a model in `agents/registry.yaml` — rejected because it requires a registry edit (touches production config); also tests the model-resolution path rather than the backend-reachability path.
- Network-level firewall rule — rejected as way over-engineered for a one-shot induced failure.
- Use a project-local `.env` file with the wrong key — rejected because shell-level env-var override is simpler and doesn't leave a file behind.

## Decision 8: Spec corrections needed (filename canonicalization)

**Decision**: After Phase 1 design, amend spec.md to use `idea/<slug>.md` everywhere it currently says `idea/seed.md` or `idea/idea.md`. The conceptual distinction between "seed" (brainstorm output) and "expanded" (flesh_out output) is real, but it's not represented as separate files — flesh_out edits the same slug-named file in place.

**Rationale**: See Decision 2. Leaving the spec/plan as-written would mislead implementers into expecting two files where there's only one.

**Implementation**: This becomes a small task in `tasks.md` — a search-and-replace pass over `spec.md`, `plan.md`, the contracts, and the data model to canonicalize the filename references. Will land as an early task before any agent runs.

## Open items deferred to /speckit-tasks

None. All Phase 0 unknowns resolved. Phase 1 (data-model, contracts, quickstart) and Phase 2 (tasks.md) can proceed.
