# Exhausted fresh canary: source-layout shadowing — October 9, 12:32 UTC

Read-only evidence comes from `/private/tmp/llmxive-canary-rescoped-20261009`
(PROJ-9999-totient-canary), run against platform `22048a64fb6`.
The project reached `agent_blocked` at 12:32:12, not research acceptance.

## Why the planner-routing fix did not run

The project history records implementation-to-`planned` recoveries at 06:34,
07:14, and 08:20, before the corrected #1518 route was loaded. Its persisted
`replan_rounds` is already 3, the existing cap. The final exhausted model ladder
therefore correctly takes the earlier `AGENT_BLOCKED` branch; it never reaches
the new `CLARIFIED` return. The latest planner inspection is 07:52, following a
07:38 tasks-panel kickback. This run does not validate #1518's live planner
recovery. Counters and scientific state were not reset.

## Two demonstrated platform defects

1. `code/.tasks/T006.src_cli.py.log` records execution of root `src/cli.py`, but
   its import resolves to `code/src/phi_sieve.py`, a 93-byte deprecated stub.
   The real root `src/phi_sieve.py` is 2,309 bytes. `run_in_venv` always prepended
   `code/` to PYTHONPATH even for an explicitly selected root-package script.
   The fix prioritizes the containing regular package's import root for explicit
   project-local Python entry files. Existing code-workspace precedence and
   generic/module invocations retain their behavior.
2. All six captured T004 responses include `tests/test_plot_verification.py`,
   yet the final file is absent. Replaying only the static import guard against
   the 12:31:04 response (1,960-character proposed test; no writes/execution)
   returns `('src.plot_tv', 'make_plot', '')`. The guard exclusively inspected
   deprecated `code/src/plot_tv.py` (87 bytes), ignoring the real root
   `src/plot_tv.py` (2,786 bytes) which defines `make_plot`. The fix checks a root
   artifact's own workspace first, while code artifacts retain code-first
   lookup. Truly missing imported names are still refused.

The three new behavioral regressions fail on the original source: one actual
subprocess raises ImportError, another silently imports the wrong same-named
module, and the real artifact writer refuses a valid root-source test. With the
fixes, 54 distinct focused checks pass across sandbox execution, implementation
contracts/previews, import/binding validation, and import context. Tests create
isolated synthetic projects; no scientific canary files are repaired or run.

## Other blockers remain

T004 explicitly requires deleting obsolete wrappers. The artifact protocol
supports file writes/execution but has no explicit delete operation; captured
responses replace wrappers with comments claiming removal, leaving the package
on disk. Adding a bounded, auditable deletion contract merits separate work.

T005's latest saved test execution passes CLI flags to a unittest runner:
`tests/test_cli_success_and_log.py --max-n 1000 --moduli 5`; argparse correctly
returns exit 2. The final run-book test failure also includes an old test using
N=10 while the revised CLI restricts N to the four required scales. These are
unresolved generated-code/test consistency problems, not reasons to weaken the
execution gate. No useful full-pipeline artifact acceptance is claimed.
