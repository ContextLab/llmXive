# GitHub Actions timing and scheduling audit — 2026-10-09

The observed avoidable cost is setup for empty work, followed by checkout. Keep
the production advance width, useful research lanes, scientific checks and
20-minute reprocess cadence. Skip heavy reprocess setup only when a conservative
state probe proves there is no applicable stage; stop fetching all history in
four lanes that operate on current files.

## Evidence window and limitations

Snapshot: approximately 16:40 UTC, source `7185be8dbe39c08884e498cc2506d8f64d17eb78`.
The audit fetched up to 100 latest runs for each of 15 workflows, then job/step
records for 132 runs (25 six-worker advance runs; usually eight completed runs
per other lane; three nightly runs). Detailed logs cover 36 recent advance jobs,
eight reprocess jobs and selected other lanes. This mixes recently improved and
older workflow versions: it is an observational baseline, not a controlled trial.

Raw run/job JSON, selected logs, analysis scripts and the frozen 1,095-project
state census are retained locally at
`/private/tmp/llmxive-actions-audit-20261009/`. Reproduce the source records with
`gh api repos/ContextLab/llmXive/actions/workflows/<workflow>/runs?per_page=100`,
`gh api repos/ContextLab/llmXive/actions/runs/<id>/jobs`, and the linked job logs.
Job duration is `completed_at - started_at`; checkout excludes the post-job
cleanup step. Runner queue delay is job `started_at - created_at`, not time
spent waiting for an upstream job. Skipped jobs are excluded from medians.

| Lane | Current trigger (UTC) | Sampled jobs | Median job / checkout minutes | Decision |
|---|---|---:|---:|---|
| Advance | hourly :00, six workers | 150 | 21.68 / 5.27 | Retain width/cadence |
| Maintenance | hourly :05 | 8 | 9.21 / 6.46 | Shallow checkout |
| General pipeline | every 3 hours :00 | 8 | 26.42 / 5.32 | Retain useful additional advancement |
| Reprocess | hourly :07, :27, :47 | 8 | 9.99 / 6.39 | Sparse empty-queue probe; unchanged cadence |
| Submission intake | hourly :00 | 8 | 8.97 / 6.93 | Shallow checkout |
| Personality | every 2 hours :00 | 8 | 15.10 / 8.11 | Separate incremental-value review; no change here |
| Signoff poll | every 2 hours :25 | 8 | 8.91 / 4.94 | Preserve human approval lane |
| Paper compile | every 30 minutes + paths/manual | 8 | 23.42 / 6.68 | Shallow checkout; preserve backfill/audit |
| Pages | paths + explicit dispatch | 8 | 9.32 / 6.52 | Shallow checkout; retain coalescing |
| Repair | 07:00 errors / 19:00 issues + manual | 8 | 20.08 / 6.00 | Retain bounds and independent acceptance gates |
| Prompt evaluation | relevant PR paths + manual | 8 | 6.76 / 1.28 | Recent sparse improvement already present |
| Full real-call nightly | 06:00 daily | 3 | 21.53 / 4.85 | Preserve full tests; latest run was 96.5 minutes |
| PR tests | relevant PRs | 33 | 1.50 / 0.18 | Heterogeneous jobs; recent split/sparse setup already present |
| HF daily intake | 08:00 daily | 8 | 5.63 / 4.72 | No cadence change |
| Static audits | PRs | 40 | 1.00 / 0.08 | Separate owner; no change here |

Runner queue medians were approximately 2–3 seconds. That does **not** measure
cron lateness or pending concurrency wait. For example, the daily 06:00 nightly
was created at 06:34, and a maintenance :05 tick was created at 16:22. GitHub
documents delayed or dropped scheduled runs during load, especially at the top
of an hour. Moving all offsets would not establish a performance improvement:
already-offset lanes also arrived late. See [GitHub schedule semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

## Findings and causal boundaries

**Reprocess spends setup on an empty queue.** All eight inspected completed
reprocess runs migrated zero papers, found no project ready and completed zero
steps: approximately 80 observed runner-minutes without draining work. Example:
[run 37958846442](https://github.com/ContextLab/llmXive/actions/runs/37958846442).
The frozen state census has zero `paper_ingested` and zero `paper_review` records.
`migrate_unprocessed_external_papers` only considers `paper_review`; the normal
drain explicitly selects `paper_ingested`. A probe that treats **every** record
in either stage as potential work safely includes legacy external-paper
migration without duplicating its artifact classifier. Authored review papers
may produce false positives, which simply run the original job.

**Advance and the general lane perform real stage work, but success is not
scientific acceptance.** The 36 recent advance job logs recorded 51 completed
steps; 18 jobs also reported no implementation progress, and two reported model
deadline/outage failures. Two general-lane logs recorded three completed steps,
including a clarified-to-planned transition in
[run 37950071003](https://github.com/ContextLab/llmXive/actions/runs/37950071003).
The same run later encountered a circuit-open GPT endpoint, GLM's 360-second
deadline, a Gemma timeout and a fail-closed paid-credit lookup timeout. The
inspected logs contain no explicit HTTP 429/rate-limit evidence. Six workers plus
general/nightly/review lanes can overlap, but these logs do not establish that
our concurrency caused the provider outage. Reducing width or removing the
general lane would sacrifice observed work without a measured causal benefit.

The advance job cap is 330 minutes, its step cap 300 minutes, and its wall budget
2,400 seconds is an admission check **between** steps. A single long step can
exceed 40 minutes. In the 102 sampled October 9 worker jobs, median duration was
22.85 minutes, the empirical 90th percentile was 50.23 minutes, eight exceeded
an hour, and the longest was 84.4 minutes. Per-worker serialization accommodates
that tail. Preserve checkpoint/always-commit/failure evidence and this
headroom; do not interpret median duration as a safe hard timeout.

**Pages cancellations mostly represent queued demand, not 80 failed deploys.**
The 24-hour snapshot contains 80 cancelled, 13 successful, one failed and one
active Pages run. Several cancellations coincide with newer requests before
13:30; [cancelled run 37936926165](https://github.com/ContextLab/llmXive/actions/runs/37936926165)
has zero jobs. This is consistent with the default one-running/one-pending
concurrency behavior, where newer pending work replaces older pending work.
The specific failure [37937097751](https://github.com/ContextLab/llmXive/actions/runs/37937097751)
was a guarded commit conflict after a 6m28s checkout; it refused to overwrite
newer work. Keep coalescing rather than building an obsolete deployment backlog.
See [GitHub concurrency semantics](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).

**History fetching can consume an entire short job.** Personality
[run 37957247536](https://github.com/ContextLab/llmXive/actions/runs/37957247536)
spent its full 15-minute limit fetching all branches/tags; its annotation says
the job exceeded 15m0s and no model step began. This is a checkout finding, not
evidence against personality reviewers' incremental scientific value. That
comparison and workflow are owned separately; neither is altered here.

**Other apparent duplication is not sufficient grounds to remove a lane.**
Maintenance and dedicated submission intake both ran the same empty intake in
their latest two logs. Maintenance swallows precondition errors, while dedicated
intake reports them as failures. Removing the dedicated schedule would change
error visibility. Both remain. The latest two paper-compile logs said no papers
to compile, but then spent about 5.8 minutes backfilling preprint PDFs and 7.8
minutes auditing PDFs: the entire job is not a no-op. Two signoff polls found no
awaiting projects; the human approval gate remains unchanged.

**Nightly failed because checks found defects, not because its budget expired.**
[Run 37894209975](https://github.com/ContextLab/llmXive/actions/runs/37894209975)
ran real-call tests for 87m58s: 93 passed, seven failed, six skipped. Failures
included incorrect factual corrections, grounding, a tasker producing zero task
IDs and publication held for manual signoff. Artifacts were preserved. These
failures require their own remediation, not shorter/less frequent checks. Repair
trials similarly require causal reproduction, preservation and independent
acceptance; wiring success does not justify increasing trial cadence.

## Changes and validation

1. Reprocess first checks out only `state/projects`, its probe script and the
   stage contract. It installs PyYAML and checks the conservative stage superset.
   Missing/empty/unreadable YAML, unknown stages, missing schema or a failed
   probe enable the normal full job. Manual dispatch also enables it.
   "Malformed" here means YAML/stage uncertainty, not full project-schema
   validation; the original full job still owns that validation. Explicit
   workflow cancellation remains respected. The full drain uses the probed
   commit (or main if checkout failed), preserving the same snapshot and every
   original preflight, migration, vision, TeX, model and persistence step.
2. Maintenance, submission intake, paper compile and Pages now use depth one.
   Their invoked scripts operate on current files; the guarded persistence
   helper explicitly fetches newer main before rebasing and verifies the push.
   No full project data or PDF inputs are removed. Full-tree transfer still
   costs time, so hosted savings from this change remain unmeasured.

Local validation: 35 targeted tests passed, including real `file://` depth-one
clones for research and Pages persistence under a concurrent disjoint update
and a same-file conflict. New tests cover current/legacy queue stages, authored
review false positives, malformed/unknown/missing/empty state, missing stage
vocabulary, read-only probing and workflow fallback/pinning. Actionlint and
Ruff passed. Running the actual probe against all 1,095 YAML records extracted
from the frozen Git snapshot returned `needed=false`. No production run was cancelled and no extra model call was made
for this audit.

## Hosted verification after review and merge

Observe the first three scheduled reprocess ticks at the new SHA. For an empty
queue require a successful probe, `needed=false`, a skipped full drain, and no
lost pending eligible state. Compare total runner-minutes and checkout duration
with the 9.99/6.39-minute baseline. When real work appears, require the original
drain and preservation steps on the pinned SHA; do not dispatch synthetic paid
work simply to produce timing evidence. Observe three ordinary runs of each
shallow lane, including push verification/deployment completion. Retain actual
new timings and any conflicts. A local test is not proof of hosted speedup or
scientific acceptance.

The 100-run windows for PR CI and static audits cover only 05:40–16:40 and
12:56–16:40 respectively, so their counts cannot be compared with full-day
production counts. Other lanes' sampled outcomes also reflect active platform
repair and should not be extrapolated into stable failure rates.
