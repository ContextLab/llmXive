# Session 2026-10-10 — resuming the paused recovery

Entry point was `notes/HANDOFF-2026-10-09.md` →
`/Users/jmanning/llmxive-handoff-20261009/START_HERE.md` (private local dir).

## Live-state corrections to that handoff

- **#1557 is MERGED**, not open: squash `763615497ac`, merged by the user at
  2026-10-09T17:28:24Z — eight minutes AFTER the handoff was written. It merged
  WITHOUT the two uncommitted corrections in `actions-uncommitted.patch`.
- The squash contains more than the worktree head `6666382471c` (an extra
  `test_reviewed_task_integration_modules_keep_offline_and_dartmouth` block), so
  the PR branch had commits the local worktree never saw. `6666382471c` is NOT
  an ancestor of main.
- Crons have been driving main since; head at session start `edcd6d95fc5`
  (2026-10-10 19:14 UTC). Both disabled workflows (276410003 personality,
  379115107 repair) remain `disabled_manually` — untouched.

## Work landed this session (PRs open, CI green except offline in progress)

| PR | branch | content |
|-|-|-|
| #1558 | `fix/real-call-gate-20261010` | real-call gate by file path, not node id |
| #1559 | `fix/avoid-data-discovery-for-import-errors` | + terminal-error classification |
| #1560 | `fix/repair-context-followup-20261009` | bounded read-only context replacement |

### #1558 — the class behind the "sanitize one test parameter ID" note
`tests/conftest.py` gated real-call tests on `item.nodeid`, which embeds
parameter values, so ANY offline test parametrized with a `tests/real_call/...`
path was silently skipped. Reproduced on main before changing anything. Two
parametrize blocks in `test_ci_selection.py` already carried ad-hoc `ids=`
workarounds; the third was missed, so #1557's own offline regression never ran.
Fixed by `under_real_call()` (absolute path, files under `tests/real_call` only;
relative strings refused). Measured: trio 115 passed/1 skipped → 116/0;
`tests/real_call` still 126 collected/126 skipped; whole offline suite under
CI's exact sparse set **7838 passed, 11 skipped, 0 failed**.

**Local-environment trap:** a cone-mode sparse worktree of (.github .specify
agents notes scripts specs src tests) produces **34 spurious failures + 6
errors** (web/js/markdown.js, docs/, project templates absent). Replicate CI's
non-cone list from `.github/workflows/llmxive-real-call-tests.yml` lines 61-82
and then run `scripts/ci/prepare_test_checkout.py` (adds 3 PDFs + 4515 project
template files; 26M → 222M; suite grows 3735 → 7838 tests).

### #1559 — reviewer's "unconfirmed" edge case is REAL
`_CODE_SETUP_FAILURE_RE.search(f)` scanned the whole ~1200-char tail, so a
setup signature ANYWHERE suppressed data-source discovery. Confirmed in two
shapes: (a) a printed/handled `ImportError` notice above a terminal
`FileNotFoundError` on a `data/` input; (b) a chained `ModuleNotFoundError` →
terminal `RuntimeError` from the source host. `_terminal_error_line()` narrows
to the LAST traceback and takes that segment's last exception line (falling back
to the last non-empty line so `<python>: No module named <pkg>` stays
classified). Table-driven over 7 tail shapes.

## Interrupted-canary forensics (the most useful new evidence)

`canary-final-state.json`: 38 steps, 8171s, status `interrupted`. The shape is a
**re-plan cycle**, not a single stall:

```
 10-21 in_progress x12  -> 22 in_progress -> clarified     (kickback #1)
 23-27 specified(1062s) -> clarified -> planned -> tasked -> analyzed
 28-31 in_progress x4   -> 32 in_progress -> clarified     (kickback #2)
 33-36 planned -> tasked(1148s) -> analyzed -> in_progress
 37-38 in_progress x2   -> interrupted
```

Each cycle regenerates the whole doc chain (~2500-4000s), so a 10800s budget
affords ~3 cycles. Research never reached `research_complete`.

### Model-call accounting from the run's own trace log (665 ends parsed)

| model | successes | s/success | failures |
|-|-|-|-|
| `openai.gpt-oss-120b` | 327 | 11.9 | 0 (1 KeyboardInterrupt = the stop) |
| `zai-org.glm-5.3` | 42 | 65.3 | 273 instant `BackendUnavailable` + 5 deadline@360s |
| `google.gemma-4-31B-it` | 4 | 96.9 | 11 instant + 2 deadline@180s |

**Do not read the 43.9% failure rate as broken fallback.** 226 of 284 breaker
rejections are followed by a success within 4 events, i.e. the router escapes to
a healthy peer at ~0.01s cost. The breaker also already opens immediately on
`ModelDownError` (`dartmouth.py` `Breaker.call`).

The real loss is **wall clock**: 7 deadline hangs = **2160s of the 8171s run
(26%)**. The breaker's cooldown recovery probe is a FULL-budget real call, so
each probe of a hung model costs another 360s — ~4 of the 7 hangs are probes.
A cheap-liveness probe (short deadline) instead of a full-budget probe would
recover ~1440s (~18%). NOT implemented this session: it changes a shared
mechanism, and the next canary should supply fresh evidence first.

### Live model catalog re-verified 2026-10-10 (real calls, trivial prompt)

All five candidate free ids answer and are fast: `openai.gpt-oss-120b` 2.62s,
`zai-org.glm-5.3` 1.85s, `google.gemma-4-31B-it` 1.12s, `qwen.qwen3.5-122b`
0.85s, `google.gemma-3-27b-it` 5.98s. So the canary's glm/gemma failures were
NOT dead ids — they are load/length dependent hangs on real prompts.
`qwen.qwen3.5-122b` made ZERO calls in that canary despite being the documented
default; worth checking what the registry actually routes.

## Canary prerequisites verified (ready to launch on merge)

- `load_dartmouth_key()` and `load_signing_key()` both resolve locally.
- fixture `tests/real_call/fixtures/PROJ-9999-totient-canary` = ONE file,
  `idea/fleshed_out.md` (the spec/plan/tasks are platform-generated).
- The idea file EXPLICITLY specifies "half the sum of absolute frequency
  differences" and "the unconditional denominator is N, the conditional
  denominator excludes all zero residues". So the handoff's "scientific contract
  drift" is a platform deviation from a correctly specified idea, not a flawed
  fixture: the generated spec mixed denominators (stratum mass vs residue
  probability) and the plan then dropped the 0.5. Fix belongs in the platform /
  review gates — never in the canary.
- Runner `llmxive-canary-run-observed-20261009.py` needs COPY_ROOTS (src,
  eval/promptfoo, tests, agents, specs, .specify, scripts, web/about.html,
  pyproject.toml, README.md, LICENSE) + `papers/.style` in the frozen source.

## Repository-weight question (user asked; subagent measured)

`projects/` is not the weight: tracked `projects/` = 7.89 GB of which
`projects/*/paper/` = 7840 MB and everything else = 238.7 MB. 93/279
`src/llmxive` modules touch project paths, so migrating would be a ~33% package
rewrite to save 239 MB. Two findings that matter more:

1. `docs/papers` = **2114.3 MB** (my own `git ls-tree` measurement), and the
   subagent found 655/655 blobs byte-identical to `projects/*/paper/pdf`,
   committed by `pages.yml`. The deployed `github-pages` artifact of run
   38079995168 is **1916 MB**, while `pages.yml:53-56` states Pages caps a site
   at 1 GB and claims the 15 MB/file filter keeps docs/ "comfortably under 1 GB".
   Deploys still report success, so the cap is not hard-failing — but the
   guard's stated premise is false.
2. 4.39 GB is third-party arXiv intake (`original.pdf`, `original-llmxive.pdf`)
   in a PUBLIC repo, and all 227 `preprint.json` lack a license field.
   Rights/publishing question → user's decision, NOT filed as a public issue.

## Next

1. Merge #1558/#1559/#1560 when the offline job finishes (everything else is
   already SUCCESS, including Dartmouth live and, on #1558, external references).
2. Freeze merged main into a new isolated dir; launch
   `llmxive-canary-run-observed-20261009.py` (50 steps / 10800s, paid opt-in
   false, no GitHub writes). Preserve the previous interrupted run untouched.
3. While it runs: personality redesign (approved design, implementation not
   begun) and the spec→plan denominator-drift class.

---

## Session continued — what landed

| PR | merged as | content |
|-|-|-|
| #1558 | `d760891dc6d` | real-call gate by FILE PATH, not node id |
| #1559 | `b55f0cb1f38` | execution failure classified by the error it DIED of |
| #1560 | `db01419a459` | bounded read-only repair context replacement |
| #1561 | `17c7bce552c` | cross-document scientific-contract drift gate |
| #1562 | `a19b1e6e8f8` | cheap breaker recovery probe |
| #1563 | `5c76e4ebe71` | README stage→agent recipe (SC-008) restored |
| #1564 | open | preprint intake digests (prerequisite for dropping the arXiv PDFs) |

### Contract-drift gate (#1561) — the measurement that shaped it

`scan_contract_drift` fires only when the SAME name is defined in >= 2 documents,
BOTH definitions parse under the existing restricted sympy evaluator, their
difference does not simplify to zero, AND the difference is STRUCTURAL. Measured
over all 745 live feature dirs: first cut 8 findings (4 prose parsed as
arithmetic) → tightened 1, genuine (PROJ-468 `Dissipation` = `Abs(dKE+dPE)` in
plan vs `(dKE+dPE)` in spec). The canary's `stratum_TV` factor-of-two is caught.
NOT caught (semantic, needs a reviewer): that the canary's "stratum TV" is not a
residue-distribution TV at all.

### Breaker probe (#1562)

Breaker + router fallback were NOT broken — 226/284 instant rejections recover
within 4 events. The waste was the probe's price: a full-budget real request per
cooldown window on a model whose circuit a deadline hang had opened.
`_liveness_ok` now answers in ~1s. **The real-call suite caught two defects in
the first version**: `max_tokens=16` makes gpt-oss-120b AND gemma-4 return EMPTY
content (the EmptyReplyError flap) — a liveness check would have stranded two
healthy models permanently; and an unlisted id returns None, not False, because
the free/paid classifier cannot tell a retired id from a paid one.

### arXiv PDFs — maintainer chose "drop original*.pdf from HEAD"

Blocking discovery: **an arXiv id does not pin the bytes.** Re-downloading a
random 12 of 226: **5 differ** (2605.22878 committed 906,089 → now 9,751,359).
Our reviews were written against the committed bytes. So recovery is via GIT
HISTORY, not arXiv, and #1564 records sha256+bytes per paper first (4.28 GiB
hashed from the object store in 9s). Corrects the subagent's "zero license
field": that was `preprint.json`; `paper/metadata.json` has `arxiv_id`,
`arxiv_url`, `license`, `license_url` for all 227 — all the arXiv Non-exclusive
Distribution License, which reads "I grant arXiv.org a perpetual, non-exclusive
license to distribute this article" (fetched 2026-10-10): arXiv.org only.

`llmxive.checks.state_readers` caught MY defect in that PR: the first version
wrote `original-version-mismatch.json`, read by no source module — a
persist-and-forget artifact. Now a logged warning + returned verdict; the
structured record lands with its consumer.

Maintainer approved for the follow-up PR: the site links arXiv and NAMES the
licence instead of serving a mirror (also drops ~2.1 GB from a published site
measured at 1916 MB against Pages' 1 GB cap).

### Still-open CI gaps (reported, not fixed)

- **`tests/integration` is run by no workflow.** That is why the SC-008 README
  regression from #1545 sat undetected. Turning it on needs `/.claude/` and
  `/projects/*/specs/` added to the offline job's sparse list — i.e. it enlarges
  the checkout #1557 just trimmed. State that cost when proposing it.
- **No workflow runs ruff.** `ruff check src tests` = 96 errors on main (23
  RUF001, 20 E702, 18 I001, 9 F401, ...). Agents have been linting only their
  own changed files by hand.
- Local full-suite runs in a sparse worktree produce 34 false failures; see the
  recorded lesson `sparse-worktree-ci-parity`.

### Canary run 2 (in flight)

PID 26604's successor: PID 28266, source `b55f0cb1f381af9121cf79d3a8ad5d905e0154c1`,
runner sha256 `710dab872f0437010b1724c4e9bba2bc0c6b8aff421426879068edb89f4b32a3`,
data `/private/tmp/llmxive-canary-fresh-20261010-1957`. At 62 min: step 11,
`in_progress`, **76 calls, ZERO failures** (the interrupted run had failures by
this point). Wrote code/, data/, figures/ incl. `totient_tv_results.csv`,
`tv_vs_N.png`, 5 of 10 tasks marked done. Acceptance still UNPROVEN — it has not
reached research_complete, and the previous run kicked back to `clarified` after
12 in_progress ticks.

### Prompt-log gap found via history-surfer

`surfer` logged only 2 prompts for 2026-10-10 and captures NO mid-turn prompts.
The session transcript does, as `type: queue-operation` records:
`~/.claude/projects/-Users-jmanning-llmXive/<session>.jsonl`. One genuine user
prompt had been skipped this session: `/compound` at 19:32:23.
