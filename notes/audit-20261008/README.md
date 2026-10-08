# llmXive recovery audit — 2026-10-08

Production snapshot: `a3fc8073a968dbba1fe5fbae0014e6feb2c9b754`.
The audit uses repository state, every persisted run-log entry, sampled live
GitHub Actions logs/issues, the Dartmouth model catalog, and real model/code
calls. Counts below describe this frozen snapshot, not a claim about later runs.
Work is isolated from the user's unfinished `025-self-improvement-lane` branch.

## What the data shows

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
