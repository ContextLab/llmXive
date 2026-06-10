# Orchestration-harness pilot — results + decision (issue #295, scope item 1)

**Decision: KEEP THE BESPOKE PIPELINE.** The pilot does not meet the
audit's adoption threshold ("adopt only if a one-lane pilot reduces
orchestration LOC and passes the same eval/real-call gates").

## What was run (2026-06-10, real Dartmouth calls)

`smolagents_pilot.py`: the representative implementer micro-lane (read
tasks.md → implement artifact → write file → validate by executing →
mark checkbox → report) through a smolagents 1.26.0 `CodeAgent` whose
`RouterModel` adapter delegates every model call to llmXive's
`chat_with_fallback` (free-model guard, per-model breakers, peer
fallback all active). Model: `qwen.qwen3.5-122b` (the pipeline's free
default). The bespoke lane's gate for the same shape of work is the
nightly-green `tests/real_call/test_implementer_e2e.py`.

| Run | Config | Outcome |
|-|-|-|
| 1 | max_steps=6, default sandbox | **FAILED** — wrote a correct `fib.py` but the sandbox blocked importing/executing the just-written file (its own report: "direct imports and exec/compile are restricted in this environment"); burned steps working around it; hit the step cap before the checkbox + final_answer protocol. 7 LLM calls, 73.4 s. |
| 2 | max_steps=8, `subprocess` authorized, explicit final_answer instruction | **PASSED** — full protocol (file correct, validated via subprocess, checkbox marked, `T001 COMPLETE`). 7 LLM calls, 62.4 s. |

## Findings against the threshold

1. **Orchestration LOC: net INCREASE, not reduction.** The
   router-delegating adapter is ~55 LOC and pilot glue ~100 LOC;
   production wiring (flag at `graph.py:439`, verdict mapping,
   checkpoint bridging) would add ~150–250 LOC. What it could replace
   is only the pure step/retry loop of `speckit/implement_cmd.py`
   (~60–80 of its ~222 LOC) — the rest is llmXive *semantics*
   (completed/failed/atomize/skipped verdict taxonomy, tasks.md
   checkbox checkpointing, FAILED-IN-EXECUTION gating) that smolagents
   does not provide and which would be reimplemented as tools/callbacks
   around `CodeAgent`. Stage-level orchestration (~580 LOC:
   run_one_step, kickback cap, scheduler, locks) and the convergence
   protocol stay in-house regardless (Constitution I).

2. **The audit's headline benefit for this lane — the sandboxed
   CodeAgent — evaporates in practice.** The implementer's core
   validation pattern is "execute the file you just wrote"; the default
   sandbox blocks exactly that (run 1's failure). Making the lane work
   required authorizing `subprocess` (run 2), i.e. forfeiting the
   sandbox guarantee that motivated smolagents for this lane.

3. **Gate parity is doubtful:** 1/2 runs completed the protocol; the
   failure mode (step-cap + sandbox friction) is inherent to the
   harness's interaction with this lane, not a transient.

4. **What DOES carry forward:** the `RouterModel` adapter pattern is
   proven — a harness can run entirely inside llmXive's router (guard,
   breakers, peer fallback intact, honest token/cost accounting). If a
   future lane genuinely suits a harness (e.g. a long-horizon planning
   lane on LangGraph), this adapter is the template, and the MCP server
   (scope item 2) exposes the librarian/claim tools to any such harness
   without router coupling.

## Dependency hygiene outcomes

- `smolagents` is NOT added to pyproject (pilot-only; installed
  transiently, uninstalled after the pilot).
- As-you-go finding: `langgraph>=0.2` had been a *declared but entirely
  unused* dependency since the original bootstrap commit (`e9814dfc`) —
  zero imports anywhere in src/ or tests/. Removed (same spirit as the
  audit's Phase-0 legacy cleanup); if a planning-lane pilot is ever
  attempted, it should re-add the dependency alongside actual usage.

## Reproduce

```bash
.venv/bin/pip install smolagents
.venv/bin/python specs/022-audit-phase3-followup/pilot/smolagents_pilot.py
.venv/bin/pip uninstall -y smolagents
```
