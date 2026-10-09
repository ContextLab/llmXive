# Pages persistence profile — 2026-10-09

The Pages workflow copies `web/` and selected PDFs into `docs/`, then calls the shared cron commit helper. The October pipeline guard accepted and staged only research project, state, and dashboard-data paths, so a changed `docs/` tree was refused before publication. This is a deterministic code-path defect; recent Pages attempts were cancelled before completion, so this audit does not mislabel those cancellations as observed guard failures.

The trusted static Pages workflow now passes an explicit `pages` profile. A single fixed allowlist drives both validation and staging: Pages can publish only `docs/`, while the default `research` profile retains concrete project namespaces, `state/`, and `web/data/`. Arbitrary profiles are rejected. Completely deleted allowed roots are staged too. The checker runs with `python -B`, avoiding creation of its own bytecode files.

Two additional guard gaps are closed: index and working-tree differences are inspected separately so a worktree restoration cannot hide an unauthorized staged edit; rename detection is disabled so a protected source deletion cannot hide behind an allowed destination. Rejected trees and index contents are preserved for diagnosis.

The former workflow-persistence test only searched shell text for `git add -A`, including comments, and could not prove what the scoped helper actually staged. It now verifies guarded workflow delegation; real local Git push tests verify the resulting persisted paths instead of matching shell syntax.

Validation: **38 focused tests pass** in 7.73 seconds. Real temporary repositories and bare remotes establish that (1) default research commits reject docs changes, (2) Pages commits publish exact added/deleted docs paths, (3) mixed platform/project/state changes are refused before staging/push, (4) protected renames and staged/worktree cancellation are refused, (5) invalid profiles are refused, and (6) default research project/state/dashboard output still persists. Existing oversized-file and conflicting-worker protection tests also pass. Ruff, Actionlint, shell syntax, and diff checks pass. These tests establish code behavior, **not live GitHub Pages publication**.

The broad offline suite on this branch passed 3,357 tests with 20 skips and four deselections; its six failures are exactly the stale baseline assertions independently corrected in PR #1527 (whose full offline suite passes). No new broad-suite failures were introduced.

A separate audit finding remains outside this fix: convergence revision writers still use `specs/auto-revisions/<PROJ>/...`, which conflicts with the strict default guard. That path is not added to the allowlist. A separate project-local revision migration will retain legacy reads and provenance; the default research permission boundary is unchanged.
