# llmXive recovery audit — 2026-10-08

Production snapshot: `a3fc8073a968dbba1fe5fbae0014e6feb2c9b754`.
The audit uses repository state, every persisted run-log entry, sampled live
GitHub Actions logs/issues, the Dartmouth model catalog, and real model/code
calls. Counts below describe this frozen snapshot, not a claim about later runs.
Work is isolated from the user's unfinished `025-self-improvement-lane` branch.

## Current acceptance status — 2026-10-09 13:58 UTC

The repaired pipeline has autonomously crossed implementation and research review
in a fresh isolated run. **Full paper acceptance and production recovery are not
yet demonstrated.** The defects involve orchestration, scope, artifact boundaries,
and evidence verification; upgrading the model alone does not resolve them.

- The 13:29 production census (`c85a8b1306dc19dd0cc4c9011d51b040ae40c775`)
  contains 1,095 projects: 455 implementing, 103 planned, **zero authored projects
  at research-complete or later**, and 227 external preprint reviews. See
  `production-20261009-1329.json`. Scheduled workers are active, but a green worker
  can report zero forward progress. Run [37934499690](https://github.com/ContextLab/llmXive/actions/runs/37934499690)
  persisted two no-progress implementation attempts; another worker encountered
  Dartmouth connection timeouts. These are not authored-paper completions.
- The fresh bounded totient canary started at 12:49 UTC on platform
  `d366a5e6ee1d2120b23fc569fee081fd87bb2b3a`. It reached `research_complete` at
  13:10, `research_accepted` at 13:26, `paper_clarified` at 13:38 and `paper_planned` at 13:47. Paper task
  convergence is running. Neither scientific artifacts nor task/stage/replanning counters
  were hand-edited to obtain these transitions. Prior unsuccessful runs remain
  preserved; the successful research stages belong to this genuinely new run.
- Independent calculation checked all 12 residue-count tables, all 24 total-
  variation rows, population denominators, and 1,000 small-n gcd identities.
  Both primary JSON hashes were unchanged after research review. The plot was
  visually checked and the report correctly acknowledges the observed p=11
  conditional reversal instead of claiming monotonic convergence. This is useful
  numerical verification, not a new theorem or accepted paper. See
  `canary-20261009-1250-evidence.json`.
- GLM-5.3 is the free primary. All free models remain subject to service outages;
  the canary uses no paid fallback. PRs #1518/#1520/#1521 repair actual replanning,
  malformed-response recovery and task-authoring contracts. #1526 fixes explicit
  project-root script imports; #1528 keeps refused artifacts uncompleted and
  supplies exact refusal diagnostics to the next autonomous attempt.
- Merged #1531 corrects a remaining hidden GPT-OSS task-verifier default, explains trusted
  canonical-path/cwd evidence without rewriting task commands, accepts valid empty
  package markers for semantic review, and invalidates cached verdicts when model
  or verification policy changes. Six local real GLM cases passed, including
  negative controls; its hosted live job passed in 3m40s. All nine exact-head CI checks passed.
- #1525 reduced a measured aggregate real-call check from 18m07s to 7m35s. Offline
  and live checks run concurrently; docs/unit-only changes skip live calls, while
  runtime or unknown paths retain them. Free peer-model coverage and long tests
  run nightly. The primary-model contract asserts the actual returned model.
  PR #1534 preserves complete audited inputs and produces identical manifests
  on a case-sensitive filesystem. Its hosted audit checkouts took 4–11 seconds
  and complete audit jobs 47–84 seconds. External Zenodo timeouts independently
  blocked the live jobs on #1532/#1533/#1534; Dartmouth model checks passed.
  Separating external reference-service availability from unrelated model checks
  is in progress.
- #1523 restored project boundaries for 2,666 leaked files (390.83 MiB), preserving
  exact bytes and modes, with a committed recovery manifest and root-layout gates.
  #1530's project-local revision/cache follow-up is merged (1,356 files
  relocated with exact bytes/modes preserved). Case-colliding paths
  are separately inventoried; conflicting scientific files are not silently
  overwritten or assigned guessed ownership.
- #1529's docs-only write profile passed a real Pages deployment. Public
  `data/projects.json` returned HTTP 200, 15,693,905 bytes, Git blob
  `9a55471c265a021f34354a549a950675d9cb4686`, exactly matching deployed commit
  `c95996fa5e106216da756a75746eaab6e9a370e7`. The preceding deployment produced
  52 changed paths, all under `docs/`.
- Self-improvement fixes #1519/#1522 are merged. Fresh bounded trial
  [37937595531](https://github.com/ContextLab/llmXive/actions/runs/37937595531)
  failed on `ed81d772fad69a25b0ace248978ce06d79a6b960`. Attempts included
  a regression that failed only because its proposed helper did not yet exist,
  malformed Python and unsafe deletion of an existing backup. No candidate
  reached preservation review or publication. **Self-improvement has not yet
  delivered an accepted useful repair.** Follow-ups target meaningful baseline
  failures, syntax diagnostics and backup-preservation tests. PR #1533 also fixes
  a separately reproduced runner/publisher evidence-digest mismatch without
  weakening the publisher integrity check.
- PR #1535 addresses a new observed paper-planning defect: prefixed model file
  markers produced nested feature directories while the canonical plan initially
  remained a template. It reuses complete-set guards, confined writes, rollback
  and corrective retries; eight before/after regressions and 106 related tests
  pass. The real captured-response corrective replay is pending. An isolated
  two-step production snapshot probe of PROJ-549 is also running on merged
  `9e93570fcc8d66af5d0413868e970989f926be1d`; it is not a production mutation or
  evidence of full-pipeline acceptance.
- The HF `llmxive` resource group and private storage pilot are configured with
  a shared $20 monthly cap. Real private-file roundtrip, a bounded CPU job and
  one stronger-model call passed; credentials are in macOS Keychain. #1524 adds
  the explicit pilot helper and receipts. This is not automatic paid escalation
  or production artifact offloading; existing Git blobs remain preserved.
- Issue cleanup consolidated 203 dispositions into eight recurring/actionable
  issues (195 closed). The Claude web/mobile health-check task and all its
  triggers are paused; it was not deleted.

Live acceptance and remaining blockers are tracked in
[#1139](https://github.com/ContextLab/llmXive/issues/1139), reviewer protocol in
[#1474](https://github.com/ContextLab/llmXive/issues/1474), provider evidence in
[#1475](https://github.com/ContextLab/llmXive/issues/1475), and autonomous repair in
[#1242](https://github.com/ContextLab/llmXive/issues/1242). Later issue updates
supersede this timestamped snapshot.

## What the baseline data shows

| Measure | Observed |
|---|---:|
| Project state files | 1,095 |
| In implementation | 464 |
| Authored projects at research-complete or any later research/paper stage | 0 |
| Reviewed external preprints, a separate review-only track | 227 |
| Active research task lists | 723 |
| Tasks across those lists | 40,199 |
| Median / maximum tasks per project | 52 / 175 |
| Open tasks invisible to the original implementation regex | 1,941 across 200 projects |
| Persisted run-log records | 190,552 |
| Implementation invocations marked successful since October 1 | 12,100 |
| Implementation records without output paths since October 1 | 6,286 |
| Stored execution-status records | 321 |
| Successful execution-status records | 7, all imported projects; not authored-paper completions |

The original advancement metric counted successful agent calls, including
no-output calls, rather than actual stage advancement. A green worker or an
external preprint review therefore did not establish progress toward an authored
paper. `baseline.json` preserves the census, failure classes, sample task lines,
and model/outcome counts; `progress-metrics.json` uses persisted stage history.

## Causes and repairs

1. **Task identities disagreed across components.** The implementer accepted
   `T001` but missed dotted, suffixed, uppercase, indented, bold, and other real
   variants. The verifier could truncate IDs and conflate different tasks.
   PROJ-591 repeatedly had only `T003.5` left, producing empty successful runs.
   Both implementers and the verifier now share identity parsing. Completion
   considers every checkbox; ambiguous/duplicate identities are sent back to the
   tasker with feedback, not silently ignored. The wider corpus scan initially
   left 219 unmatched open lines; expanded support reduced this to 13 malformed
   lines that require regeneration (`parser-after.json`).
2. **Success was often activity rather than progress.** No-output and no-task
   invocations now log as skipped. The CLI stops and records a no-progress
   implementation tick instead of clearing its failure history and repeating.
   The advancement metric now counts forward authored-project stage transitions
   from history, separately from successful calls and external-paper intake.
3. **The implementation/review contract had holes.** A nonempty stub or two-row
   CSV could be accepted as task completion without checking its meaning. File
   presence now supplies evidence, not approval. Missing required artifacts still
   fail deterministically; existing ones need independent content verification.
   Evidence lookup now finds the active `plan.md`/`spec.md`; cached verdicts depend
   on the task, specification, and full artifact hashes. Malformed reviewer
   responses receive one constrained repair attempt; a non-accept verdict with
   no actionable concerns cannot become an automatic acceptance. Truncated model
   responses are rejected before partial content can be treated as complete.
4. **Execution could pollute the platform.** Commit
   `f555b75c41fb91bb1a6cee88aa365ce95e1ebc13` (August 6) replaced the platform README
   and MIT license with an unrelated fluid-flow dataset's README and CC-BY
   license. Discovery executed generated snippets in the repository root, and
   the worker used `git add -A`. The platform files are restored. Discovery now
   runs in temporary working directories with a credential-free environment;
   research subprocesses also receive an allowlisted environment. Cron commits
   reject writes outside canonical output roots and stage only those roots.
   These cwd/environment protections are not an OS filesystem security boundary.
   Repair-candidate tests, separately, run in Docker with no network,
   credentials, Docker socket, or writable host checkout.
5. **Concurrent persistence could overwrite newer results.** The commit helper
   used `git rebase -X theirs`, silently choosing the stale worker's version on
   conflict. It now refuses a conflicting push and preserves a patch for recovery.
   The two advancement workflows upload that patch on failure. A real bare-Git
   regression proves the newer remote results survive.
6. **Dashboard regeneration dominated worker time.** It repeatedly reread the
   complete log corpus for each project. One worker spent roughly an hour on
   this after a seconds-long no-op implementation pass. Per-project entries are
   now indexed once per build. On the real corpus the revised build took 44.1 s
   and emitted 868 authored-project entries plus 227 external preprints.
7. **Fabrication detection confused prohibitions with permission or evidence.**
   Negative text such as “synthetic data is strictly prohibited” could trigger a
   fabrication finding; “No synthetic data” in an idea could authorize synthetic
   data. Both directions are fixed and regression tested. Actual fabricated
   substitutes remain disallowed.
8. **Scoping and scientific assumptions need attention as well as machinery.**
   The median 52-task plan often builds an application framework around a small
   scientific question. Planner/tasker prompts now target a small complete
   study, typically 8–15 substantive tasks, with real execution early and no
   weakening of scientific requirements. In sampled PROJ-771, the proposed
   uniformity test conflated all totient residue classes with the coprime-only
   population in the cited theorem. The [source paper](https://arxiv.org/abs/2105.12850)
   explicitly distinguishes these. A bounded, correctly framed replication is
   now the full-pipeline canary; its scope is illustrative, not a new theorem.
9. **Discovery imposed unnecessary work on exact computations.** The live canary
   searched for unrelated downloaded data even though its original study design
   explicitly needed no external dataset. Procurement now honors that declaration
   in the original idea; execution, fabrication checks and scientific review still
   apply. Studies without such a declaration retain normal data discovery.

10. **Claim cleanup altered the experiment itself.** With production scientific
    guards enabled, the canary's planned `p ∈ {5, 7, 11}` became incomplete sets
    such as `{, 7, 11}`. The planning extractor was even instructed to treat
    runtime budgets and acceptance targets as empirical findings. The extractor
    now distinguishes chosen parameters/targets from measured findings, and the
    deterministic guards preserve enumerated parameter domains. An unrelated
    observed quantity on the same line still goes through claim handling.
    Sixty-four regression checks passed; a real GLM claim-processing call
    preserved both domains and the five-minute runtime target verbatim
    (`design-preservation-live.json`).

11. **Task verification could prevent its own prerequisites from running.**
    The production-guarded canary generated exporter code but no data files;
    verification reopened the output tasks, while the dedicated execution gate
    waited for every task to be checked off. A bounded run-book preview now runs
    before each implementation batch's verification, supplies real output and
    traceback evidence, and leaves final execution acceptance/fix budgets alone.
    Real subprocess regressions prove outputs are computed with tasks still open
    and a failed computation supplies feedback without accepting the project.
    Evidence parsing also preserves `paper/figures/...` and multi-dot schema
    filenames instead of looking for nonexistent shortened paths.
12. **A checkbox was mistaken for a saved review.** A batch interrupted before
    verification could resume with unverified tasks treated as previously
    accepted. Later tasks could also overwrite accepted code without invalidating
    its checkbox. Acceptance reuse now requires a matching cached review of the
    current task/spec/evidence; pending review is persisted before backend calls.
13. **The template audit confused task tags with unfilled fields.** Remote CI
    flagged six existing files. Five were substantive task lists with labels such
    as `[Write Script]` or bold `[Phase Timer]`; these are now recognized in task
    metadata positions, while explicit fill-in directives remain detectable.
    PROJ-434 also contained actual `Insert Research Question`/`Insert Reference`
    placeholders and a validation instruction conflicting with its FR-004. That
    paragraph now states the question and defers to the active specification's
    held-out-species validation requirement, without inventing a citation.
14. **Execution results and tests could become stale or invisible.** Successful
    execution records now bind to the analysis source, run-book and output bytes;
    editing or removing evidence invalidates acceptance. Run-book `pytest`
    commands are executed instead of silently discarded. A real failing pytest
    subprocess blocks acceptance even when the preceding analysis creates a CSV.
    The implementer prompt now documents the existing `execute: true` capability,
    which its previous output contract omitted entirely. Scientific-output tasks
    can request their producer run immediately, as well as wiring the run-book.
15. **Multiline task requirements were dropped.** Replanning emitted task headers
    followed by indented output paths and constraints. Implementation context and
    verification had retained only the first line. Both now retain the full
    indented task body; an absent CSV named on a continuation line fails the
    deterministic check. `canary-diagnostic-tasks.md` and the diagnostic trail
    preserve the failed trial. That process was stopped to test the corrected
    pipeline from the same initial idea; its recorded running status is a
    pre-interruption snapshot, not a claim of an ongoing or accepted run.

16. **Valid source layouts escaped execution and evidence checks.** The clean
    canary planned a `src/` package, while preview execution, code context,
    dependency discovery, fabrication checks, and execution fingerprints assumed
    `code/`. These now share discovery across `code/`, `src/`, and `scripts/`.
    An existing root requirements manifest is reused. A real subprocess regression
    executes a nested `src/` module, validates its computed CSV, then proves a
    fabricated replacement invalidates its execution approval. Failed `src/`
    module commands now reopen their owning task and retain the correct repair
    path. Relative project paths also work for direct output-producer execution.
17. **Copied concern labels triggered a false planning kickback.** The clean
    canary's plan panel accepted all three corrections, but the reviser returned
    IDs prefixed with `concern`, copied from the prompt's labels. Exact matching
    padded these as missing and sent the project back to specification. The
    recorded trail is `canary-plan-response-failure.jsonl`. Response IDs now
    tolerate that explicit wrapper only when the remaining literal ID is a
    supplied concern. Unknown IDs and duplicate answers still fail closed; the
    independent panel still decides whether the correction resolves the concern.
18. **An unavailable model server was classified as a permanent engine bug.**
    The issue census found three `no available server` failures filed separately
    for different projects. That explicit availability signal now fast-fails to
    the existing peer-model fallback instead of opening a permanent engine
    failure. A regression exercises the backend's actual classification entry
    point and verifies that budget-exceeded errors remain hard limits.
19. **Failure deduplication was scoped to each project, multiplying tickets.**
    The live issue census found 185 reviewer-schema reports and five provider
    reports among 199 open issues. Those observed signatures now route to shared
    tracking issues [#1474](https://github.com/ContextLab/llmXive/issues/1474) and
    [#1475](https://github.com/ContextLab/llmXive/issues/1475), before consulting
    legacy per-project ledgers. The state ledger retains the latest 20 project/
    stage examples with run IDs and diagnostic excerpts. Repeated occurrences
    emit no new tickets or comments. A closed tracking issue is reopened when
    recurrence is detected, with status checks bounded to once per UTC day per
    checkout. Unknown signatures retain their distinct issue tracking. The
    regression covers thirty different projects sharing one issue and recurrence
    after closure; it does not claim an exact global occurrence counter across
    concurrent workers.

### Independent scientific acceptance reference

`totient-independent-oracle.py` computes the full twelve `(N, p)` combinations
using per-integer trial factorization, with a separate GCD count check for
`n = 1..500`. Its exact counts and rational TV distances are saved alongside it.
This is an external acceptance reference, explicitly **not pipeline-generated
research output** and not evidence that the canary passed. Unconditional TV uses
uniform mass `1/p`; conditional TV excludes zero residues and uses `1/(p-1)`.
For the four specified sizes, conditional TV falls throughout for primes 5 and
7, while prime 11 rises from about 0.02667 to 0.02905 before falling. The eventual
pipeline artifacts must reproduce these observations and preserve their
finite-range interpretation. The live planning reviewers independently flagged
the plan's incorrect use of `1/p` for conditional TV; its correction is pending.

## Models: verified, not inferred from names

Dartmouth's authenticated catalog exposed `zai-org.glm-5.3` with zero input and
output prices. A real backend call returned valid JSON in 3.26 s. All 53
registry agent defaults and the central default now use GLM-5.3. Free GPT-OSS
and Gemma 4 are fallback peers; existing paid fallbacks retain their prior
explicit opt-in and budget guards. Independent task verification still uses
GPT-OSS. Vision-specific code is not blindly switched to a text-only model.

A real GLM implementer invocation completed PROJ-591's previously invisible
T003.5 in 49.4 s. An independent GPT-OSS call examined the actual plan/spec and
accepted the correction in 4.57 s (`real-implementer-result.json`,
`independent-verification.json`). This demonstrates a recovered task, not full
project completion or proof that GLM alone solves the pipeline.

## Self-improvement: a concrete product

The consolidated backlog exposed another repair-input defect: title filtering
omitted the new reviewer umbrella, and slicing the combined evidence JSON
hid later issue identities and retry diagnostics. Recurring issues are now
eligible. Long string fields are bounded individually while retaining their
beginning/end; all selected records remain in valid JSON and the complete raw
evidence stays on disk. A probe using the actual consolidated inventory
reproduced invalid JSON against the prior runner and retained all five issue
identities afterward (45,811 raw characters → 7,229 prompt characters).
Twelve focused checks and lint passed. This is a verified input correction,
not another claim of a model-generated repair; see `repair-evidence-bounds.json`.

The elaborate prototype on branch 025 was not present in production. The new
production repair runner takes either repeated structured failures or open
platform issues, selects one bounded defect, and proposes at most five files.
It cannot change workflows, itself, existing tests, or research artifacts.
Candidates must add a regression that fails against baseline production code,
pass that same regression and related existing tests with the fix, and pass
independent review by a different model. Validation runs without credentials or
network in Docker. Publication happens in a separate job, verifies unchanged
baseline hashes, and opens a PR; it never auto-merges. Only one repair PR may
be outstanding. Failed attempts keep diagnostics and feed them into at most
three attempts. No health-check notification is its output.

The first live trial reproduced `run_pytest` raising `FileNotFoundError` for a
relative project path. The initial candidate had an invalid test and was
rejected. A subsequent live trial produced a valid patch: two new regressions
failed before the fix; five new/related checks passed afterward in Docker;
GPT-OSS accepted the fix. The reviewed patch is applied to this recovery branch.
Evidence is under `repair-trial/`. This is evidence of one useful repair, not a
claim that unattended production repairs have already accumulated a track record.

## Health-check removal

The Claude cloud routine was actually hourly, despite notifications appearing
roughly weekly. Its prompt explicitly prohibited code changes, pushes, and test
execution; it could diagnose or file issues but could not repair the pipeline.
The `llmXive #1139 migration health check (hourly)` routine is paused in Claude,
with “All triggers are paused” verified in the UI. No replacement health-check
notification was created.

## Acceptance and deployment boundaries

Deployment inspection found the advance matrix still capped the entire job at
90 minutes, below the observed 94-minute planning attempt. Its 2,400-second CLI
budget is checked between stages and cannot cap one long stage. The matrix now
uses a 330-minute job cap with a separate 300-minute advance-step cap, and
always attempts to persist state after a failed step. The single-worker
pipeline also reserves a persistence window with a 300-minute step cap.
Existing per-worker concurrency remains in place. These changes preserve
diagnostics/partial work; they do not claim that slow convergence is resolved.

The [issue consolidation report](issue-consolidation/report.md) records the
completed backlog review: 199 initially open issues, two new recurring-cause
umbrellas and two new incident reports yielded 203 tracked dispositions.
195 were closed with evidence and continuing-work links; eight remain open.
Complex unresolved work is retained with acceptance criteria. Production can
still emit duplicates until the shared-routing change is deployed.

The next live planning attempt took 5,655.9 seconds and kicked back from
`clarified` to `specified`. Its preserved trail
(`canary-plan-hash-response-failure.jsonl`) records two rounds with no parsed
per-concern responses, then four answers using complete concern hashes without
their reviewer prefixes. The engine treated those four identities as missing.
The response mapper now accepts a complete eight-digit hash only if it maps
uniquely to a current reviewer-prefixed concern. Unknown, shortened, colliding,
and duplicate answers remain unresolved. Forty-four focused checks passed;
the live scientific correction and accepted paper remain pending.

Later, the same run reached `planned` after eleven total recorded steps. The
resulting plan and research notes now explicitly use `1/(p−1)` for conditional
TV and retain the finite-range interpretation. The runner then failed its
budget check (12,242.9 seconds in that resumed run); this is not acceptance.
The status and log are saved as `canary-planned-budget-exhausted.*`. It resumed
from the saved `planned` stage with the hash-identity fix loaded, without
editing research artifacts or forcing a stage transition.

The latest PR real-call job ([37826932550](https://github.com/ContextLab/llmXive/actions/runs/37826932550))
was cancelled at its 60-minute job limit. Its contract suite and 7,053 unit
tests passed; real-call output stopped after the liveness checks, immediately
before the 15-persona sequential rotation in collection order. That rotation
now joins the existing nightly-only heavy tests. Collection checks confirm it
remains selected by the nightly suite and is excluded from the fast PR gate.
This change does not establish that the remaining real-call gate passes; a
fresh run is required.

The follow-up run [37835730308](https://github.com/ContextLab/llmXive/actions/runs/37835730308)
passed in 17m12s on commit `8cb06dc8602`; all six PR checks passed on that
revision. The subsequent hash-identity change still requires its own remote CI.

The old “full pipeline” test only invoked one step and could pass when the
project was rejected or needed human input. Its description is corrected. A new
opt-in real acceptance test traverses both research and paper gates, with the
same claim/grounding flags as the production CLI, and requires actual paper
source and a compiled PDF. It fails on rejection or exhausted budgets and stops
before publication/sign-off. The nightly workflow now enables that test and
retains artifacts on failure as well as success.

**Full-pipeline acceptance and deployment are still being verified.** A model
probe, thousands of unit tests, a successful repair, or the canary reaching
planning does not establish that a useful paper has finished the pipeline.
Final verification results and remote deployment references will be recorded
in `verification.json` after they are observed.
