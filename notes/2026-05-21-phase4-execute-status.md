# Phase 4 (/speckit-execute spec 014) — status 2026-05-21

Branch: 014-phase4-plan-tasks-testing. Running LOCALLY (background validate_phase4.py → python -m llmxive run, real Dartmouth). NOT in CI.

## Pipeline stages (Stages 1-3 done)
- Plan/Tasks/Analyze (clean after 1 remediation). Spec 014: 22 FR / 11 SC, 28 tasks.
- Code committed: _research_guard.py (FR-005/006/007 planner gates), plan_cmd wiring, _inspection.py rounds[],
  slash_command per-round hook, tasks_cmd per-round capture, scripts/validate_phase4.py driver,
  tests/integration/test_phase4_plan_tasks.py.

## REAL BUGS FOUND + FIXED during real runs (each committed w/ regression tests)
1. audit/template_vs_real._body_density: stripped fenced/mermaid blocks + counted parent headings as empty
   → rejected real table/diagram data-model.md. FIXED.
2. _research_guard FR-007: demanded 1:1 entity↔schema name match; planner contract is ">=1 schema" w/ differing
   names. RELAXED to robust structural check (entities exist; schemas valid YAML).
3. audit: learned structural task labels [US1]/[Story] as template placeholders → rejected every valid tasks.md.
   FIXED (STRUCTURAL_LABEL_RE excluded from learned set).
4. audit Rule 2 (unfilled_bracket_density): counted fenced ASCII/mermaid flowchart node labels
   ([Dataset Download] etc.) as placeholders. FIXED (_placeholder_scan_text strips fences/links/comments;
   Rule 1 still uses full text so templates still caught).
5. Driver budget: Tasker advances across TWO runner steps (planned->tasked, tasked->analyzed) per
   STAGE_AFTER_AGENT; fixed --max-tasks 2 left it stuck at 'tasked'. _run_pipeline now steps 1 agent at a
   time until terminal Phase-4 stage, STOPS at 'analyzed' (never runs implementer). Added --force rollback
   (planned/tasked -> clarified) for reproducible re-validation.

## DECISION (user, 2026-05-21): analyze-loop cap-hit = BEST-EFFORT ADVANCE
- Cap-hit WITHOUT convergence -> accept tasks.md best-effort, advance to 'analyzed', record converged:false.
  human_input_needed ONLY on explicit Mode-B verdict:escalate or backend failure. Code already did this;
  aligned spec FR-013/Background/US1/US2/US3/edge-case/data-model + added best-effort regression test.
- KNOWN: /speckit.analyze (LLM) rarely returns literal CLEAN (always finds a MEDIUM nitpick) -> non-convergence
  is expected (issue #107). PROJ-261 ran all 5 rounds, converged:false. Best-effort advance handles it.

## IN FLIGHT
- attempt 7 (bg bdn9j5fqe): PROJ-261 --force, stepping planner + tasker x2 to 'analyzed' (~45 min).

## REMAINING
- Confirm PROJ-261 reaches 'analyzed'. Then PROJ-262 (--force). Then T014/T015 (inspection verify),
  T024 (carry-forward.yaml + phase-report.md via --all or --emit-carry-forward), mark tasks [X].
- Stage 5 verify: re-walk FR/SC, full pytest, edge cases, open artifacts. Then completion report.

## PRE-EXISTING failures (out of scope, NOT caused by spec 014; do NOT fix here)
- test_revision_in_progress_idempotency.py x2 (scheduler _NEVER_PICK missing READY_FOR_IMPLEMENTATION; spec-012/013).
- test_librarian_default_fields.py, test_theoremsearch.py (real-network flaky).
- Verified: spec-014 src changes are confined to speckit/{_research_guard,plan_cmd,_inspection,slash_command,tasks_cmd}.py
  + audit/template_vs_real.py + scripts/validate_phase4.py; none touch those failing tests' sources.
