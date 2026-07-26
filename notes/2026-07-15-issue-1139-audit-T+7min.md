# Issue #1139 verification audit — T+7min snapshot (2026-07-15 13:22 UTC)

Resumed the audit from `notes/2026-07-15-issue-1139-merge-migrate-handoff.md`. **Critical timing
context:** the merge + migrations landed at 13:09–13:15 UTC; it is now 13:22 UTC. Exactly **ONE**
`advance` tick (`f5a229ffc9`, worker 7, 13:19:56 UTC) has run since. The "verify over the next cron
cycles" audit therefore **cannot be completed yet** — this is a regression/baseline check, not the
crossings verdict. That needs hours of cron cycles.

## Verdict per audit question (at HEAD `f5a229ffc9`)

| # | Question | Verdict | Evidence |
|-|-|-|-|
| 1 | Research wall crossing? | **PENDING** (0 crossings — expected @T+7min) | `research_complete`=0, `research_accepted`=0 |
| 2 | `[~]` keeps falling, not re-ballooning? | **HELD** (2139, unchanged — NOT toward 7k) ✓; "falling" not yet demonstrable | in_progress marks X=6992 ` `=12659 ~=2139 x=1 (identical to handoff baseline) |
| 3 | Error ledger holds (no re-pick of drained permanents)? | **CONFIRMED ✓** | top permanent counts frozen pre-migration + `rerouted` (dormant) |
| 4 | No new invalid transitions? | **CONFIRMED ✓** | `invalid_transition`=5, unchanged, all class=invariant/terminal |
| 5 | Paper reaches `paper_complete`? | **PENDING** (0) | paper_status: 171 restyled_unaudited, 11 fallback_original, 0 complete |
| 6 | AGENT_BLOCKED vs VALIDATOR_REJECTED terminal? | **N/A yet** (both 0) | no project has terminaled either way |

**Overall: migrations held through the first post-merge tick; no regressions. Pipeline is LIVE and
doing real work** — the one tick actively iterated `data_ingestion.py`/`metric_extraction.py` in the
execution fix-loop of the code-generation project (not a no-op). All goal-state crossings remain
PENDING and are genuinely unobservable 7 min after migration.

## Two handoff-note items corrected (so the next session doesn't re-investigate)

1. **The `consecutive_count=365` "concern" is a NON-issue.** It's **PROJ-077** (permanent /
   `unreachable_reference` / status=`rerouted`), `last_seen=2026-07-14T18:38:23Z` — **frozen ~19h
   BEFORE the migration**. It is NOT climbing. Ranked list:
   - 365 PROJ-077 permanent/rerouted last_seen 07-14 (dormant)
   - 100 PROJ-770 **deterministic_repair/retry_scheduled** last_seen 07-15 12:43 (legitimately retrying — this class is *supposed* to retry)
   - 84 PROJ-047 permanent/rerouted last_seen 07-14 (dormant)
   The P0-1 control is working: permanent failures are held/rerouted (not re-picked); only
   deterministic_repair records have recent `last_seen`. Watch that PROJ-770's 100 doesn't run away.
2. **`failure_class` absence is a MERGE-BOUNDARY ARTIFACT, not a code gap.** `execution_status.record()`
   (`state/execution_status.py:263-264`) *unconditionally* persists `failure_class` + `evidence` on every
   call (both set from `stage.py:396-407` via `FailureClass.from_signals`). But **all 45 live records have
   `updated_at ≤ 2026-07-15T13:09:34Z`** (= the merge commit time) — i.e. every one was written by
   **pre-merge** code; 0 post-merge writes exist yet; 0 carry the key. Proof: the post-merge tick f5a229's
   own PROJ-488 write is stamped `13:09:34Z` (worker checked out pre-merge code at the merge boundary).
   **→ Verification item (needs 1 post-merge failure write):** the NEXT time any project executes-and-fails
   under post-merge code, its record MUST gain `failure_class` (∈ compute_env/data_unreachable/fabrication/
   execution_bug/hollow/unknown) + `evidence`. If a post-merge `ok=false` record still lacks it → real bug.
   The terminal AGENT_BLOCKED vs VALIDATOR_REJECTED choice lives in `graph.py:1428/1715`, branching on this class.
   - Escalation ladder IS active: model_tier 0=33, tier 1=12 (12 projects escalated to gpt-oss-120b).
   - Fabrication guard IS firing: e.g. PROJ-018 `ok=false`, "20 fabricated/simulated-result signal(s)",
     14 attempts, tier 1 — correctly refusing to advance a synthetic-data project.
   - PROJ-488 (the ONE project the post-merge tick worked) is a dependency-churner: `radon.mi` +
     `datasets` ModuleNotFoundError, fix_rounds 7→10 (cap 12), tier 0 — implementer editing requirements.txt.
     Watch it escalate to tier 1 / re-plan rather than churn to the cap.

## Corpus snapshot (T+7min baseline for next comparison)

- Stages: in_progress 490 · reviewed_preprint 222 · brainstormed 79 · tasked 70 · validated 66 ·
  flesh_out_in_progress 65 · flesh_out_complete 50 · planned 13 · specified 12 · project_initialized 11 · clarified 6
- advance_errors: 74 files — permanent 53 · transient 8 · invariant 5 · deterministic_repair 4 · emitter_context 4
- state_readers guard: **0 dead-ends** (44 artifacts, 8 allow-listed) — green
- Goal/terminal states ALL 0: research_complete, research_accepted, paper_complete, published, agent_blocked, validator_rejected

## What to re-check next cycle (deltas to watch, vs this baseline)
- `[~]` from 2139 → should trend **down** (task-completion verifier drains residue). Alarm if it climbs.
- research_complete/research_accepted: any non-zero = the headline win.
- PROJ-770 deterministic_repair count 100 → should resolve or cap, not run to 733.
- New `invalid_transition` fingerprints (currently 5) → should stay 5.
- paper_complete: any non-zero (from the 171 restyled_unaudited pool).

Re-run the handoff snapshot script + `sort advance_errors by consecutive_count` + terminal-state count
after several `advance` ticks (realistically a few hours; note CI queue thrash → ~1 tick landed in 13 min).

## Monitoring loop (session cron `3658f4fa`, `7,37 * * * *` ≈ every 30 min, rounded from 45m)
Re-snapshots + checks the 5 deltas + the post-merge failure_class check each cycle; auto-appends here;
stops on a research-wall crossing, a real bug, or ~6 healthy cycles. Session-only (dies on exit).

### Cycle log
- **Cycle 1 (2026-07-15 ~13:26 UTC, HEAD `570b1ded48`, +1 advance tick since baseline):** all HELD —
  goal/terminal states still 0 (expected); max_consecutive 365 (frozen); PROJ-770 still 100 (not
  incrementing); invalid_transition 5; guard 0 dead-ends; **0 post-merge execution_status writes yet**
  so the failure_class new-code check remains PENDING. ONE watch item: `[~]` 2139 → **2166 (+27)** —
  NOT a re-balloon (nowhere near 7k); caused by the tick's +268-line `tasks.md` (a tasker generating a
  fresh task list ADDS `[~]`; the verifier that DRAINS `[~]` didn't run this tick). Watch the trend: a
  single +27 with a known cause is noise; sustained creep would mean task-gen is outpacing verifier drainage.
- **Cycle 2 (2026-07-15 ~13:40 UTC, HEAD `b289d5f229`, +2 advance ticks):** all HELD — goal/terminal
  states still 0; max_consecutive 365; PROJ-770 100; invalid_transition 5; guard 0 dead-ends; 0 post-merge
  execution_status writes yet (failure_class check still PENDING). `[~]` **2166 → 2160 (−6)** — the C1
  blip is receding, trend now 2139→2166→2160, nowhere near 7k. The 2 ticks did non-execution stage work
  (no execution_status writes). in_progress 490→491. Corpus healthy-but-throughput-bound; continuing.
- **Cycle 3 (2026-07-15 ~14:10 UTC, HEAD `0b096b53d0`, +3 advance ticks):** all HELD — goal/terminal 0;
  max_consec 365; PROJ-770 100; invalid_transition 5; guard 0 dead-ends; still 0 post-merge execution_status
  writes (failure_class check untestable by passive observation — already code-verified). `[~]` 2160→**2167**
  (band 2160–2167, +1.3% over base, far from 7k). in_progress 491→493, ` `=12764 (+73): new projects
  entering in_progress + taskers adding lists. HONEST NOTE: `[~]` is HOVERING, not draining — the verifier
  drains only on research *implement* batches (cron-slot-limited) while task-gen adds; matches the known
  in-progress throughput wall. Not a regression; the science gates are intact. Continuing (3 of ~6).
- **Cycle 4 (2026-07-15 ~14:40 UTC, HEAD `b9c57d63cf`, +4 advance ticks):** all HELD, byte-identical
  aggregates to C3 (in_progress 493, [~]=2167, X=6989, ` `=12764). VERIFIED not a measurement artifact:
  the 4 ticks changed 30 `projects/` + 32 `state/` files and rebuilt `web/data/projects.json`, but **no
  `tasks.md` changed** → marks legitimately unchanged; work was reviews/run-logs/.specify-memory/dashboard,
  no stage crossings. max_consec 365, PROJ-770 100, invalid_transition 5, guard 0 dead-ends. Still 0
  post-merge execution_status writes (10 ticks in, none hit the execution stage — failure_class check
  remains code-verified-only). Throughput-bound in sharp relief: real churn, no counted advancement.
  Continuing (4 of ~6).
- **Cycle 5 (2026-07-15 ~15:10 UTC, HEAD `e8a2f747ae`, +5 advance ticks):** all HELD — goal/terminal 0;
  max_consec 365; PROJ-770 100; invalid_transition 5; guard 0 dead-ends; 0 post-merge execution_status (15
  ticks in, none hit execution stage). `[~]`=**2167** (flat for C3/C4/C5 — stable). X=6989→**7008 (+19)**,
  ` `=12796 (+32): implementers ARE completing tasks while task-gen adds; `[~]` holds as verifier-drain and
  tasker-add balance. in_progress 493→494. No regression, no crossing. Continuing (5 of ~6).
- **Cycle 6 (2026-07-15 ~15:40 UTC, HEAD `ad1adc82e6`, +1 advance tick):** all HELD, identical to C5
  (in_progress 494, [~]=2167, X=7008, ` `=12796). goal/terminal 0; max_consec 365; PROJ-770 100;
  invalid_transition 5; guard 0 dead-ends; 0 post-merge execution_status. Sixth consecutive healthy cycle.

## LOOP CONCLUDED — 2026-07-15 ~15:40 UTC (6 cycles over ~2h15m, HEAD 3cccd510cc → ad1adc82e6, ~16 ticks)
**Verdict: REGRESSION CHECK PASSED, no crossings.** Every #1139 invariant held across all 6 cycles:
- `[~]` 2139→2166→2160→2167→2167→2167→2167 — a tiny early blip (fresh task-list gen) that receded and
  settled FLAT at 2167 (+1.3% of base). NEVER trended toward 7k → the deterministic-first verifier did NOT regress.
- advance_errors max consecutive_count **365** (frozen, PROJ-077 pre-migration) all 6 cycles; PROJ-770
  **100** (never incremented). Ledger control (P0-1) HOLDING — no permanent-failure re-picking.
- invalid_transition fingerprints **5** (no new ones); state_readers guard **0 dead-ends** every cycle.
- X (completed research tasks) climbed 6980→**7008** — implementers ARE completing work; `[~]` holds flat
  as verifier-drain and tasker-add balance. in_progress 490→494 (projects still entering). This is the
  known throughput wall, not a #1139 regression.

**Not yet demonstrable (needs far more cron time — NOT a code problem):**
- Zero research_complete/research_accepted/paper_complete/published crossings across ~16 ticks. Expected:
  the pipeline is throughput-bound (verifier + execution run only on cron-limited implement batches).
- **`failure_class` persistence remains observation-untested**: all ~16 post-merge ticks worked
  non-execution stages, so NO post-merge `ok=false` execution_status write occurred. The invariant is
  CODE-verified (`execution_status.record()` L263-264 always persists it); it just hasn't been exercised
  live yet. → Handed to the durable hourly cloud routine `trig_01GswTZGsiGXT1sPTj2KuwE6` to catch when it fires.

**Handoff:** durable monitoring continues via the hourly cloud routine (opens `[pipeline-health]` GitHub
issues on any real problem). Local session loop `3658f4fa` CronDeleted at conclusion.
