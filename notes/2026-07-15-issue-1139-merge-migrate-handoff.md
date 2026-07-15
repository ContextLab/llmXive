# Issue #1139 — merge + migration DONE; handoff for the verification audit (2026-07-15)

## What just happened (all on `main`)

PR **#1145** (issue #1139: pipeline liveness anti-patterns + the AP1 state-reader guard) was
**merged to main**, then the three state migrations were **applied to the live corpus** and
pushed. The pipeline is running again with the new code + migrated state.

Commit trail on `main`:
- `4b4ef827dd` — Merge #1145 (all the code fixes + `llmxive.checks.state_readers` guard)
- `6b4f3aec7e` — migrate: classify **74** advance_errors → typed control records (53 permanent / 8 transient / 5 invariant / 4 deterministic_repair / 4 emitter_context)
- `6f1e4302ec` — migrate: archive **680** dead `resolved_datasets.yaml` (→ `state/_archive/resolved_datasets/`, reversible)
- `f3c2c6804b` — migrate: drain **7,197** stranded `[~]` across 428 projects (3,886 `[~]`→`[X]`, 1,172→`[ ]`, 2,139 residue)

Workflow state: `advance`/`maintenance`/`reprocess` were **disabled during migration and RE-ENABLED**
(verified none left disabled). `advance` now runs on the merged cadence `*/30`, width 6.

## Corpus BEFORE → AFTER (proof the drain landed)

| metric | audit baseline | now (post-migration) |
|-|-|-|
| in_progress task marks | X=3026 ` `=11046 ~=7021 | **X=6992 ` `=12659 ~=2139** |
| in_progress projects | 474 | 490 |
| projects total | 1084 | 1084 |
| dead `resolved_datasets.yaml` | 676 | 0 (archived) |
| advance_errors typed? | no (untyped `count`) | yes (class/fingerprint/retry_after/status) |

`python -m llmxive.checks.state_readers` → **0 dead-ends** (still green post-migration).

## The audit's job: verify the fixes work LIVE over the next cron cycles

The migrations un-stuck the *state*; the audit must confirm the *code* now keeps it moving. Watch these
over several `advance` ticks (every 30 min):

1. **Research wall (the headline goal):** does any in_progress project reach `research_complete` /
   `research_accepted`? At the audit, 0/810 had ever crossed. Watch:
   `git log --oneline origin/main | grep -iE "research_complete|research_accepted"` and the stage
   histogram (snapshot script below). The `[~]` count should keep **falling** (verifier drains it),
   not re-balloon back toward 7k — if it re-balloons, the deterministic-first verifier fix regressed.
2. **Error ledger controls routing (P0-1):** `state/advance_errors/*.json` should NOT re-grow toward
   733 recurrences. A permanently-failing project must be HELD (scheduler `is_on_hold`), not re-picked
   every tick. Check `jq -s 'map(.consecutive_count)|max' state/advance_errors/*.json` stays bounded.
3. **No invalid transitions (D3):** no NEW `invalid transition` fingerprints should appear
   (`grep -l invalid_transition state/advance_errors/*.json`). The 5 old ones are class=invariant/terminal.
4. **Paper gate (D1):** does any paper reach `paper_complete`? The gate now consumes `paper/pdf/main.pdf`.
5. **Failure classification (D4/D20):** `state/execution_status/*.json` on failures should carry a
   `failure_class`; execution-exhaustion should terminal at `AGENT_BLOCKED` (not `VALIDATOR_REJECTED`).
6. **CI stays green:** the per-PR gate now also runs `python -m llmxive.checks.state_readers`.

### Snapshot script (paste to get the live corpus state)
```
PYTHONPATH=src python - <<'PY'
from collections import Counter; from pathlib import Path
from llmxive.state import project as ps
from llmxive.pipeline.graph import _active_tasks_md, _task_marks
from llmxive.types import Stage
root=Path('.'); P=ps.list_all(repo_root=root)
print('stages', Counter(p.current_stage.value for p in P).most_common(8))
m=Counter(); n=0
for p in P:
    if p.current_stage!=Stage.IN_PROGRESS: continue
    n+=1; t=_active_tasks_md(root/'projects'/p.id,track='research')
    if t is not None: m.update(_task_marks(t.read_text(encoding='utf-8')))
print('in_progress',n,'marks',dict(m))
PY
```

## Env / how to run things
- `python` = `./.venv/bin/python`; always `PYTHONPATH=src`. Repo root override: `$LLMXIVE_REPO_ROOT`.
- Dartmouth key resolves via `llmxive.credentials.load_dartmouth_key()` (also in `~/.config/llmxive/credentials.toml`); real-call tests need `LLMXIVE_REAL_TESTS=1`.
- Offline suite: `LLMXIVE_ALLOW_LOCALHOST=1 PYTHONPATH=src pytest tests/unit tests/contract -m "not slow"`
  (6173 passed at merge). CI gate = `.github/workflows/llmxive-real-call-tests.yml` (checks.* + contract + real_call not-slow); it does NOT run tests/unit.

## Known caveats / do NOT redo
- **Migrations are already applied** — do not re-run `--apply`. The 2,139 residual `[~]` are the ones
  that need genuine semantic verification; the live verifier drains them over ticks.
- `tests/unit/test_dataset_sources.py::test_datacite_resolves_doi` fails ONLY when doi.org returns 503
  (external outage) — not a code bug; it does a live `requests.get`.
- 8 state artifacts are allow-listed in `checks/state_readers.py` with justifications (dashboard/Kaggle/
  glob/provenance consumers). Any NEW write-only state artifact will fail the guard.
- Operational levers if the pipeline overloads: cadence/width in `.github/workflows/advance.yml`;
  intake via `submission-intake.yml` / `hf-daily-papers.yml` (still active — not paused).
- Full per-defect evidence: issue #1139 comments (7 of them) + PR #1145.

## Deferred (documented on #1139, not done — candidate follow-ups)
Result-bundle-worker + serialized-merger rearchitecture (Phase 6 residual); canary/SLO suite (Phase 7);
per-catch narrowing for sec 3.2 (fail-open by design, cause threaded via FailureClass).
