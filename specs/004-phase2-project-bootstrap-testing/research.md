# Phase 0 Research: Phase 2 (Project Bootstrap) End-to-End Testing & Diagnostics

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-05-05

## Purpose

The Technical Context in `plan.md` has zero `NEEDS CLARIFICATION` markers — every unknown was resolved during `/speckit-clarify` (Q1-Q4). Phase 0 research therefore **(a)** consolidates the mechanism choices that the clarifications committed to into concrete code-level decisions, **(b)** does the small amount of repo-introspection needed to verify the existing pipeline code already supports those choices (or names the precise file:line where it doesn't), and **(c)** documents three known-quirks-of-the-substrate that will affect the diagnostic without requiring changes.

## Decision 1 — Sibling start-stage extension

**Decision**: Extend `tests/phase1/sibling_project.py`'s `ALLOWED_START_STAGES` set to include `validated`. This is the single line at `tests/phase1/sibling_project.py:36` (currently `{"brainstormed", "flesh_out_in_progress", "flesh_out_complete"}`). No other change needed in the spawner — the rest of the spawner is stage-agnostic (it copies the canonical `idea/<slug>.md`, writes a fresh state YAML at the chosen `start_stage`, and never touches the canonical's state).

**Rationale**: spec 003 introduced the `validated` stage (D10 architecture decision) AFTER the sibling spawner was written, so the spawner's allowlist is simply out-of-date. Phase 2 testing requires staging siblings at `validated` because the orchestrator's `STAGE_TO_AGENT[VALIDATED] = "project_initializer"` mapping is the only way to route the sibling to the agent under test without manually invoking the agent class.

**Alternatives considered**:

- **Drop the allowlist entirely** — rejected because it would let the spawner produce siblings at `project_initialized`, `specified`, etc., which are downstream of the agent under test and would silently skip Phase 2.
- **Add a CLI flag like `--bypass-allowlist`** — rejected because it's a flexibility that this spec doesn't need; the simplest fix is a one-line set extension.
- **Refactor the allowlist to be derived from `agents/registry.yaml`** — rejected as out-of-scope; correct long-term direction but not needed for spec 004 and would touch many more lines than the one-line fix.

**Verification**: Read [tests/phase1/sibling_project.py:35-36](tests/phase1/sibling_project.py#L35-L36) directly. Confirmed the allowlist is at line 36. Confirmed the only consumer is line 65-67 (validation in `spawn_sibling`); no other code references it.

## Decision 2 — Constitution-write skip-if-exists fix

**Decision**: Patch `src/llmxive/agents/project_initializer.py` so the `handle_response` method (lines 84-104) checks for an existing `.specify/memory/constitution.md` BEFORE writing. If the file exists, the method returns early with a no-op (still re-running `init_speckit_in` since that operation is already idempotent on directories). The patch must preserve the defensive fallback that catches malformed LLM output and substitutes the template — that fallback only applies on first-write, not on skip.

**Rationale**: Per Q3 clarification, re-rendering a governance document with a possibly-different LLM output silently mutates downstream Constitution Checks (because `/speckit-plan` and `/speckit-tasks` inside the project read this file at every invocation). True idempotency requires the constitution to be written once and only once per project. The pattern matches the existing skip-if-dir-exists guard at [src/llmxive/speckit/runner.py:114](src/llmxive/speckit/runner.py#L114) (`if dst.is_dir(): continue`), so the fix is consistent with how the same module already handles idempotency.

**Alternatives considered**:

- **Hash-and-skip** (re-render to a temp, compare sha256, skip if identical, error if differs) — rejected as too strict for the LLM's natural variance; would force every re-run to be a hard failure even when the new constitution is acceptably similar to the old.
- **Always re-render with `temperature=0` and assert equality** — rejected because `temperature=0` doesn't guarantee determinism on the Dartmouth Chat backend (the underlying vLLM cluster has `seed`-handling quirks that produce non-deterministic outputs even at temperature=0); this would make the spec brittle to backend variance.
- **Document overwrite as accepted behavior, mark as known issue** — rejected per Q3: the user explicitly chose option B (skip-if-exists) so this option is off the table.

**Verification**: Read [src/llmxive/agents/project_initializer.py:84-104](src/llmxive/agents/project_initializer.py#L84-L104). Confirmed the agent unconditionally writes `constitution_path.write_text(constitution_text + "\n")` at line 102. Confirmed the only callers are `runner.run_one_task` via the `STAGE_TO_AGENT` dispatch table (per [src/llmxive/pipeline/graph.py:70](src/llmxive/pipeline/graph.py#L70)), so the patch surface is contained.

**Scope of patch (concrete diff sketch)**:

```python
# Before any of the LLM-rendering or init_speckit_in work, guard:
constitution_path = project_dir / ".specify" / "memory" / "constitution.md"
if constitution_path.is_file():
    init_speckit_in(project_dir)  # still idempotent; safe to re-call
    return [str(constitution_path.relative_to(repo))]

# ...rest of existing handle_response...
```

## Decision 3 — Transient-backend retry policy is satisfied by existing router

**Decision**: No code change is required for FR-002's retry budget. The existing backend router at `src/llmxive/backends/router.py:96-100` already implements 3 attempts on the primary model + 1 attempt on each model in `MODEL_FALLBACKS[primary_model]`, then falls through to the next backend in `fallback_backends`. For `project_initializer` (default model `qwen.qwen3.5-122b`, fallbacks `[huggingface, local]`), the worst-case retry tree is:

- Dartmouth + qwen3.5-122b: 3 attempts
- Dartmouth + gpt-oss-120b (peer per `MODEL_FALLBACKS`): 1 attempt
- Dartmouth + gemma-3-27b-it (peer): 1 attempt
- HuggingFace + qwen3.5-122b: 3 attempts
- HuggingFace + (any peers): 1 each
- Local + qwen3.5-122b: 3 attempts
- ... etc.

This is **strictly more retry-tolerant** than Q4's "2 retries / 3 total attempts" minimum, so FR-002 is satisfied "by inheritance" from the production router. The spec's responsibility is to **verify** this empirically (induce a transient failure on the primary model — e.g., temporarily blackhole `api.dartmouth.edu` — and confirm the run-log entry shows the retry attempts before the eventual `TransientBackendError`).

**Rationale**: Per Constitution Principle I (Single Source of Truth), the spec must NOT fork the retry policy into its own implementation. The router is the canonical retry mechanism for the whole project; spec 004 inherits it.

**Alternatives considered**:

- **Add a Phase 2-specific retry wrapper** — rejected as a Constitution Principle I violation.
- **Tighten the router's existing 3-attempt policy to Q4's exact 2-retry policy** — rejected because the existing policy is more permissive (good for production reliability) and Q4 specified 2 retries as a *minimum*, not a maximum.

**Verification**: Read [src/llmxive/backends/router.py:96-100](src/llmxive/backends/router.py#L96-L100). Confirmed `attempts = 3 if model_idx == 0 else 1`. Read [src/llmxive/backends/router.py:44-50](src/llmxive/backends/router.py#L44-L50) confirmed `MODEL_FALLBACKS["qwen.qwen3.5-122b"] = ["openai.gpt-oss-120b", "google.gemma-3-27b-it"]`. Read [src/llmxive/backends/dartmouth.py:163-180](src/llmxive/backends/dartmouth.py#L163-L180) confirmed transient classification covers rate-limit / 5xx / connection / DNS errors.

## Decision 4 — Idempotency-check harness location & invocation pattern

**Decision**: Place the idempotency-check pytest harness at `tests/phase1/test_idempotency.py`. It uses pytest's `tmp_path` fixture to clone an existing iter2 sibling's `.specify/` tree into a temp dir, then runs `init_speckit_in` directly twice in sequence and asserts sha256-equality of every file. For US3 acceptance scenario 2 (constitution skip-if-exists), the harness instantiates `ProjectInitializerAgent` directly (bypassing the orchestrator) and asserts the constitution file's sha256 is unchanged after a second `handle_response` call with a different LLM response.

**Rationale**: Live-running the orchestrator on a sibling at `project_initialized` would route to `specifier` (Phase 3), not re-run Phase 2. Direct agent invocation in a Python harness is the only way to test re-entry. Pytest is already in the project's dev dependencies (per spec 003's test_citation_resolver.py).

**Alternatives considered**:

- **Bash script + `sha256sum`** — rejected as less integrated with CI than pytest; adds shell-script-vs-python skill split.
- **Add `--force-stage <stage>` to the orchestrator** — rejected as a feature creep that violates the simplicity principle for spec 004; only useful for one test scenario.

**Verification**: Confirmed pytest is set up via `pyproject.toml` (project uses pytest for spec 003's tests). Confirmed `init_speckit_in` is importable from `llmxive.speckit.runner`. Confirmed `ProjectInitializerAgent` accepts a registry entry constructor argument and exposes `build_messages` + `handle_response` as the canonical lifecycle methods.

## Decision 5 — Induced-failure scenario implementation

**Decision**: Each of the three induced-failure scenarios from Q2 is implemented as a maintainer-driven runbook step (not as automated test code), captured in `quickstart.md` and `contracts/induced-failure-runs.md`:

1. **Backend unreachable** (`-iterFAIL-backend` sibling): `LLMXIVE_BACKEND_BASE_URL` is temporarily exported to `https://invalid.example.com` for the duration of one orchestrator invocation. Expected outcome: router walks the entire backend chain, every backend's instantiation either fails immediately (Dartmouth: `PermanentBackendError` from missing endpoint) or hits transient errors and retries; eventually surfaces `TransientBackendError` to the orchestrator, which writes an `outcome: failure` run-log entry and leaves `current_stage: validated` unchanged. Diagnostic confirms no `.specify/memory/constitution.md` is created.
2. **Idea file missing** (`-iterFAIL-idea` sibling): Maintainer manually deletes `projects/<sibling-id>/idea/<slug>.md` after spawning the sibling (via `tests/phase1/sibling_project.py`) but before invoking the orchestrator. Expected outcome: `ProjectInitializerAgent.build_messages` reads `ctx.inputs[0]` (the idea path) at line 58; if the file doesn't exist, the read returns empty string (defensive fallback at line 60: `if idea_path.exists():`). Currently this means the agent silently builds a prompt with `idea_summary=""`. **This is a Constitution Principle V (Fail Fast) violation we will surface as a HIGH defect**: the agent should raise `FileNotFoundError` if the idea seed is missing, not produce a constitution untethered from any idea. Fix lands as part of FR-014 / FR-018.
3. **Template file missing** (`-iterFAIL-template` sibling): Maintainer renames `agents/templates/research_project_constitution.md` to `…research_project_constitution.md.bak` for the duration of one orchestrator invocation. Expected outcome: `render_prompt(CONSTITUTION_TEMPLATE_PATH, …)` at line 44 of `project_initializer.py` raises `FileNotFoundError` immediately; the orchestrator records `outcome: failure` with the exception's repr in `failure_reason`; state remains `validated`.

**Rationale**: Each scenario validates one distinct precondition (network reachability, idea-file presence, template-file presence). Per Q2, all three are required, and each runs on its own dedicated sibling so the failures don't contaminate each other. Scenario 2's expected fix-on-discovery is itself a finding — Phase 2 testing surfacing a real Phase 2 defect is exactly the kind of value spec 003 demonstrated.

**Alternatives considered**:

- **Mock the backend / filesystem to induce failures** — rejected per Constitution Principle III (real-world testing).
- **Use `pytest.raises` to assert the exception path** — rejected because the failure path goes through the orchestrator's run-log writer, which is what we're auditing; we need to read the actual run-log JSONL after the fact, not just assert that a Python exception was raised.

**Verification**: Read [src/llmxive/agents/project_initializer.py:55-61](src/llmxive/agents/project_initializer.py#L55-L61) — confirmed the `if idea_path.exists()` defensive check that masks the missing-idea-file scenario. This is exactly the kind of silent fallback Constitution Principle V prohibits.

## Decision 6 — Carry-forward forward-compatibility

**Decision**: The carry-forward manifest at `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml` uses the same schema as spec 003's `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml`, with an additional `agents_run` entry recording `project_initializer` and an additional metadata field `phase2_iter2_id` capturing which iter2 sibling produced the carried-forward `.specify/memory/constitution.md`. Spec 005 (Phase 3) will read this manifest to know which iter2 sibling to pick up.

**Rationale**: Schema continuity across spec-NNN/carry-forward.yaml files makes future-phase specs (005-007 etc.) trivial to author — they just `cat` the previous spec's manifest and pick a project ID. Adding a new field rather than replacing an existing one preserves backward compatibility with spec 003's parser at `tests/phase1/validate_carry_forward.py`.

**Alternatives considered**:

- **New schema for spec 004's manifest** — rejected as a Constitution Principle I violation (would force two parsers).
- **Embed the iter2 ID inside the existing `agents_run` entry** — rejected because spec 003's schema treats `agents_run` as an unstructured list of name+iteration counts; adding a sibling-iter pointer there would couple two different concerns.

**Verification**: Read `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml` and `tests/phase1/validate_carry_forward.py`. Confirmed the schema is `{spec, generated_at, final_commit, projects: [{project_id, final_state, final_commit, agents_run: [{name, iterations, final_iter_id}], justification}]}`. Adding a new top-level field to each project entry is non-breaking.

## Substrate quirks (no fix, just documented)

- **PROJ-261 and PROJ-262 are already at `project_initialized` on `main`**: spec 003 ran `project_initializer` on them as part of its end-state. Phase 2 testing therefore operates on iter2 siblings, not on the canonicals. Confirmed by inspecting `find projects/PROJ-26{1,2}-…/ -maxdepth 4 -type f` which shows `.specify/memory/constitution.md`, `.specify/templates/{constitution,plan,spec,tasks,checklist}-template.md`, `.specify/scripts/bash/{common,setup-plan,check-prerequisites,create-new-feature}.sh` already present.
- **Cron-driven commits land on `main` continuously**: e.g., recent commits `df3537d pipeline(brainstorm): hourly tick`, `19ce86a pipeline(flesh-out): 2h tick`. These don't affect spec 004's correctness (the cron jobs operate on different projects in a separate `cron/` workflow) but the maintainer should `git pull` before starting each diagnostic session to avoid merge conflicts on `state/run-log/`.
- **`templates/{spec,plan,tasks,checklist}-template.md` exist at repo root**: `init_speckit_in` copies these (4 files) plus `templates/constitution-template.md` (1 file) into the project's `.specify/templates/` (5 files total). Audit US1 acceptance scenario 3 must list all 5 names, not just 4 like the spec draft mistakenly suggested. (The spec text already names all 5 correctly: `templates/{constitution,plan,spec,tasks,checklist}-template.md`.)

## Summary of code changes required by this plan

| File | Change | Severity | Source |
|-|-|-|-|
| [tests/phase1/sibling_project.py](tests/phase1/sibling_project.py) | Add `validated` to `ALLOWED_START_STAGES` (line 36) | Prerequisite | FR-003a |
| [src/llmxive/agents/project_initializer.py](src/llmxive/agents/project_initializer.py) | Skip-if-exists guard before constitution write (line 84-104) | HIGH defect fix | FR-011, Q3 |
| [src/llmxive/agents/project_initializer.py](src/llmxive/agents/project_initializer.py) | Replace `if idea_path.exists():` with `raise FileNotFoundError` if missing (line 60) | HIGH defect fix | Decision 5 / FR-012 finding |
| `tests/phase1/test_idempotency.py` | New pytest harness for US3 sha256-tree check | New code | Decision 4 |

No edits required to `src/llmxive/backends/router.py` (Q4 satisfied), `src/llmxive/speckit/runner.py` (already idempotent on dirs), or `agents/registry.yaml` (Phase 2 entry already correct).
