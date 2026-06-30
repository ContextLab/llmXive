# Deterministic spec-item stage gates (PROJ-604 fabrication) — 2026-06-30

## Confirmed diagnosis (PROJ-604-https-arxiv-org-abs-2605-18739)

**The implementation is BOTH fabricated AND disconnected from its own spec.**

1. **Fabricated results.** `code/longlive_quant_benchmark.py`:
   - `simulate_gemm_throughput()` → `return random.uniform(1.6, 2.3)` — the headline
     "speedup" metric is a RANDOM number, range hardcoded to match the paper's 2.15x claim.
   - `bf16_time = (bf16_mem/1e6)*1000  # Arbitrary scaling to ms` — "time" is fake.
   - `memory_reduction = 75%` is a tautology (bf16=2 bytes, fp4=0.5 bytes constants).
   - `data/quant_benchmark_summary.json`: `"experiment_type": "...Simulation"`,
     `"constraints": "...simulated metrics"`, `avg_speedup: 1.92` (mean of random draws).
   - 17 random/simulate refs. The code openly says "we simulate the metrics".

2. **Spec ↔ implementation divergence.** `specs/*/spec.md` FR-003/004/005 + SC-002/005
   demand: run `inference.py`, generate a VIDEO (.mp4), measure peak memory/FPS. The code
   does NONE of that — it emits random-number CSVs. Totally different deliverables.

## How it passed (gate gap)
- Execution gate (`analysis_runner.run_analysis` `ok`): code ran rc=0 + produced non-empty
  files under data/ + figures/ → `ok=True`. It does NOT check the results are REAL or match
  the spec's declared deliverables. (My earlier phantom-deliverable fix even EXCLUDES the
  spec's video deliverable because the code never references it → gate passes on the CSVs.)
- LLM review CAUGHT it (unanimous full_revision + 1 reject) — review works; the gap is the
  lack of DETERMINISTIC earlier-stage checks.

## Fixes to implement (after sub-agent's stage-by-stage map)
A. **Deterministic fabrication guard** at `execute_and_gate` (hard-block before `ok=True`):
   - random-as-metric: a reported-metric value computed from `random.*`/`np.random.*`.
   - self-declared simulation of OUTPUT/METRICS ("simulated metrics", experiment_type
     "...Simulation", "we simulate the metrics", "arbitrary scaling", "placeholder"/"mock"/
     "fake" results) — distinct from synthetic INPUT data (allowed, labelled).
   - tautological constant == claimed headline number.
   On hit → not ok → kickback to implementation (not research_complete).
B. **Spec-item deterministic checks at each research stage** (specified/planned/tasked):
   verify the stage artifact addresses the declared FR/SC items (extend `_spec_quality` /
   `_real_only_guard`). Detail per sub-agent map.
C. **Routing aside (user):** `research_full_revision` should NOT rest/route to `clarified`;
   a full-revision must kick to IMPLEMENTATION (`in_progress`). Touch:
   - `agents/advancement.py:609-610,629-631` (winning==full_revision / rounds-exhausted →
     RESEARCH_FULL_REVISION),
   - `pipeline/graph.py:1511-1520` (research_full_revision → CLARIFIED → change to IN_PROGRESS),
   - `agents/lifecycle.py:153` (valid transitions: add IN_PROGRESS),
   - research_review `kickback_routing` (reviewspecs.py:257-263) — no in_progress target today.
