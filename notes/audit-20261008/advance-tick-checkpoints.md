# Durable checkpoints between advance ticks — 2026-10-09

## Observed failure and evidence boundary

Production worker 0 was interrupted in
[run 37941378791](https://github.com/ContextLab/llmXive/actions/runs/37941378791)
at 14:28:15 UTC and again in
[run 37948763455, job 113881791403](https://github.com/ContextLab/llmXive/actions/runs/37948763455/job/113881791403)
at 15:19:05 UTC. Both exited 143; subsequent state publication and failure
artifact steps did not execute. The latter log explicitly reports a runner
shutdown signal. It does **not** establish what caused that shutdown.

The latter log records PROJ-728 implementation making no progress at 15:13:21,
then shutdown. Buffered CLI output does not establish that any complete graph
step returned. These observations therefore do not prove that a between-step
checkpoint would have saved this particular interrupted attempt.

The independently reproducible persistence defect is that `advance.yml` ran
up to ten graph steps before publishing any of their results. A later runner
interruption could discard every earlier completed step and its diagnostics.
The `always()` final step cannot guarantee execution after runner shutdown.

## Bounded change

The advance workflow explicitly invokes `python -u -m llmxive run --checkpoint`.
This flag commits and **pushes** through the existing research-profile CI guard;
it is off by default for local runs. The same single process selects its worker
project once, retains the original maximum of ten scheduler ticks and checks
one original 2,400-second admission budget. Checkpoint time counts toward that
budget. As before, this is a between-step admission limit, not a hard timeout
for an already running graph step.

Each completed graph step is published before another begins. Recorded project
exceptions and implementation no-progress ledgers are also published before the
pass exits. Publication is synchronous; it never runs concurrently with an
artifact writer. It uses the existing output allowlist, rebase conflict refusal,
recovery patch and verified remote push. A failed checkpoint stops the pass
nonzero. The final workflow `always()` publication remains a fallback.

The checkpoint validates writes using code imported before agent execution,
refusing modified platform/guard files before executing the repository commit
script. After a successful rebase, any change outside project/state/dashboard
outputs or the derived `docs/` tree stops the pass, so a running Python process
cannot continue against newly fetched platform code, configuration or prompts.

Unbuffered CLI output improves future interruption diagnosis. This change does
not preserve an in-flight graph step, diagnose runner termination, bypass any
scientific gate, or establish production scientific acceptance.

## Validation

- Two regressions fail with the base CLI: a subsequent step observes the old
  remote stage rather than the preceding completed step; recorded failure
  diagnostics are absent from the remote.
- Eleven new cases use local Git repositories and bare remotes, including an
  actual guarded push before a simulated subsequent `KeyboardInterrupt`, a
  rejected push, conflicting remote project progress, preserved recovery patch,
  tampered commit-script refusal, platform-changing rebase, explicit opt-in,
  failure/no-progress ledgers, original worker selection, ten-tick ceiling and
  checkpoint time consuming the original wall budget.
- 43 related checkpoint, wall-budget, error-ledger, worker-scheduler, write-profile
  and workflow-persistence tests pass in 22.31 seconds. Ruff, actionlint and
  `git diff --check` pass.

Hosted checks and actual scheduled checkpoint publication remain separate from
these local regression results.
