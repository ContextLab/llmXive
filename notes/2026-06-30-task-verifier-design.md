# Session notes — deterministic gates + task-completion verifier (2026-06-30)

## DONE this session (all pushed to origin)
- **Fabrication gate** (caf4d9fa1): `execution/fabrication_guard.py` — deterministic
  scan; `run_analysis` hard `ok=False`; `_fabrication_concerns` backstop in
  `convergence/engine.py` at spec/plan/tasks/research_review. + routing
  research_full_revision → in_progress (graph.py/lifecycle.py).
- **Scheduler drain** (b235ba49e): `_PRIORITY_DRAIN_STAGES` floated to front of
  `pick_for_worker` — fixes PROJ-604 stranded at research_full_revision (sparse
  transient stage never picked by the top-N worker rotation).
- **Synthetic-data rule** (a951df2e5): synthetic/fake/dummy/mock INPUT data is
  flagged at the exec gate UNLESS `idea/` (NON-circular; not the back-filled spec)
  authorizes it. Only PROJ-552/579 of the 10 crossings are genuine real-data;
  the other 8 used the code_adapter synthetic CPU fallback → now caught.
  code_adapter prompt updated: REAL data only, degrade on deps never on data.

## NEXT: Task-completion verifier (the user's task #3) — spec-contract consistency
**User's spec:** an LLM call OUTSIDE the implementer's session evaluates whether a
task's ARTIFACTS + EVIDENCE actually satisfy the task REQUIREMENTS. Only if that
checker accepts is the task checked off complete; otherwise it's "under review".
On reject, NOTES are updated and the NEXT implementer captures them as context.

### Design
1. **New agent `task_verifier`** (registry.yaml + agents/prompts/task_verifier.md):
   free model, separate session. Input: the task text/requirements + the evidence
   (the files the task claims to produce + their head/summary + the project's
   spec/FR context). Output (structured): `accept: bool` + `reason` +
   `missing: [..]`. It judges: do the real artifacts match what the task required?
2. **Three task states in tasks.md**: `- [ ]` not done, `- [~]` UNDER REVIEW
   (implementer claims done, awaiting verification), `- [X]` VERIFIED complete.
   - `graph._all_tasks_done` must require NO `[ ]` AND NO `[~]` (don't advance with
     unverified tasks). `_incomplete_task_count` should count `[ ]` + `[~]`.
   - The implement-batch checks off `[ ]` → `[X]` today; intercept: a verify pass
     converts each newly-claimed task to `[X]` (accept) or `[ ]` (reject) — and
     marks pending ones `[~]` if the verify can't run this tick.
3. **Flow (run_one_step implement-batch, graph.py ~660-710):** after the
   implementer marks a task done, run `task_verifier` on it. accept → `[X]`;
   reject → revert to `[ ]` + append the reason to the implementer feedback note
   (`.specify/memory/<feedback>.md`) so the NEXT implementer session reads it as
   context. Keep it bounded (verify the tasks changed THIS tick; cap calls).
4. **Notes channel:** reuse the execution-feedback file the implementer already
   reads, OR a dedicated `.specify/memory/verifier_notes.md`. The implementer
   prompt/context must include it.

### Hook points / files
- `agents/registry.yaml` (+ `agents/prompts/task_verifier.md`) — new agent.
- `src/llmxive/pipeline/graph.py` — implement-batch loop (`_incomplete_task_count`,
  the per-task implementer dispatch ~674-706); `_all_tasks_done`/`_incomplete_task_count`
  treat `[~]` as not-done.
- A new `src/llmxive/agents/task_verifier.py` (or reuse the reviewer harness) that
  loads the task + evidence and calls the model via the same backend router.
- Tests: `[~]`-aware gate; verifier accept→[X]/reject→[ ]+notes (stub the LLM).

### STATUS (built + tested + committed; NOT yet wired)
- `src/llmxive/agents/task_verifier.py` — `verify_task()` (separate LLM judge via
  `chat_with_fallback`, temp 0, COMPLETE/INCOMPLETE, DEFERS on failure — fail
  CLOSED), `gather_evidence()` (reads the task's referenced code/data/figures
  artifacts), `TaskVerdict(complete: bool|None)`. tests/unit/test_task_verifier.py.
- `graph.py` gates are `[~]`-aware: `_all_tasks_done` requires no `[ ]` AND no
  `[~]`; `_incomplete_task_count` counts both. `UNDER_REVIEW_MARK = "- [~]"`.

### REMAINING: wire the verification pass into run_one_step (the integration)
In the implement-batch block (graph.py ~625-753, the `elif agent_name in
_SPECKIT_AGENTS:` branch), for `_is_implement_batch` runs only:
1. PRE-batch: read the active tasks.md (`_active_tasks_md`); snapshot the set of
   task descriptions currently `[X]` = `already_verified` (these were accepted in a
   prior tick — never re-verify).
2. POST-batch (after the `while` loop, ~749): run a bounded verify pass:
   - For each task line now `[X]` whose desc ∉ `already_verified` (claimed THIS
     tick), up to a cap (e.g. 6 LLM calls/tick): `verify_task(task_text=line,
     evidence=gather_evidence(project_dir,line), spec_context=<spec.md FR/SC
     excerpt>, model=entry.default_model, default_backend/fallback from entry)`.
     - COMPLETE → keep `[X]`.
     - INCOMPLETE → set the line `- [ ]` (implementer REDOES it) + append
       `(task, reason)` to the notes; bump a per-task reject count in
       `.specify/memory/task_verify.yaml`; if count ≥ 3 → keep `[X]` + log (avoid
       an infinite redo loop; the LLM review panel is the final backstop).
     - DEFER (None: backend outage or over-cap) → set the line `- [~]` (under
       review; re-verified next tick; NOT redone by the implementer).
   - Also re-verify existing `- [~]` tasks (deferred earlier) up to the remaining
     cap: COMPLETE→`[X]`, INCOMPLETE→`[ ]`+notes, still-defer→stay `[~]`.
3. NOTES channel: append rejections to a file the implementer already injects —
   reuse `_write_doc_kickback_feedback`'s ingestion (`.specify/memory/
   kickback_feedback.md` is read via `_comments_context.render_recent_comments_block`)
   OR a dedicated `.specify/memory/task_verifier_notes.md` added to that injection.
   The NEXT implementer session MUST see "tasks the verifier rejected + why".
4. Registry: add a `task_verifier` entry (free model, paid_opt_in:false) so the
   model/backend are config-driven, OR just pass entry.default_model (qwen) —
   prefer a registry entry for SSoT + to make it a DISTINCT agent (the user's
   "outside the implementer's session" requirement).
5. Tests: a stubbed-LLM run_one_step that (a) accepts → task stays `[X]` →
   advances; (b) rejects → task `[ ]` + notes file written; (c) defer → `[~]`,
   project not advanced. Mirror tests/unit/test_implement_batching.py fixtures.

### Watch-outs
- The verifier is a REAL LLM call (free model, Dartmouth/local) — bound the count
  per tick + cache by (task, artifact-hash) to avoid re-verifying unchanged work.
- Must be OUTSIDE the implementer prompt/session (distinct agent + prompt).
- Real-call test path: `LLMXIVE_REAL_TESTS=1` + Dartmouth/local backend.
