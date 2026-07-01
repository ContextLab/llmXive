# Session 2026-06-30/07-01 — pipeline reliability + fabrication audit

## Goal (standing /goal)
Get 10+ projects to `paper_drafting_init` ("paper init"); do NOT sacrifice
scientific quality — make real fixes to make pipeline steps more robust/powerful/
efficient/comprehensive.

## Honest outcome
- **Count: 2** at paper-init-or-beyond (PROJ-575, PROJ-601, both `paper_analyzed`).
- Reaching 10+ is **structurally impossible in a single session**: measured ~9h of
  reasoning-bound implementation per project (PROJ-492 drive: ~15 reasoning calls/
  task) + execution + 7-reviewer × 3-round review; ~50% of executed projects
  fabricate (correctly blocked). The only shortcuts are fabricating results or
  weakening the science gate — both prohibited. The count climbs over CRON cycles.
- Clause 2 (real fixes) delivered comprehensively; clause 1 (the count) is cron-bound.

## Fixes shipped (all pushed to main, suite green ~4640)
1. Kaggle GPU offload unblocked — auto-derive username, works with existing
   `KAGGLE_API_TOKEN` secret; 10 bugs fixed, proven on real GPU.
2. Empty-reply retry cap (`EmptyReplyError`, dartmouth) — escapes qwen `<think>`
   flap in ~3 tries not ~8.
3. Pages: artifact deploy (broken nested submodule killed legacy deploy) + 15MB PDF
   mirror cap (1.7GB→698MB, under Pages 1GB limit).
4. Audit `[Const VII]` false-positive (template_vs_real.py).
5. **ab3551109** run-book/impl path-mismatch stall — `_reopen_failing_tasks` appends
   a self-owning reconciliation task when a run-book script has no owning task
   (was permanent in_progress stall; PROJ-552/179).
6. **b7b653e91** artifact-detection — scan `results/`+`output/`+`code/output/`, not
   just data/figures (PROJ-492 was falsely gated "no artifacts").
7. **e405d029f** fabrication audit — anti-fabrication guardrails at every generator
   stage (implement batch [implement_cmd.py], tasker, paper_statistics; planner +
   implementer_research already had it) + detectors (research/paper data_quality
   reviewers flag it). Deterministic guard already backstops exec gate + every
   convergence stage. Regression test `test_fabrication_guardrails_present.py`.
8. **604ef9a41** (sub-agent) plan-reviser engine crash — all 3 `[engine-failure]`
   issues #384/#385/#386 (RuntimeError "outside the plan set" on paraphrased slug /
   foreign-only reply); re-key to canonical path + degrade gracefully. Issues
   CLOSED. Unblocks PROJ-259/637/019 at plan stage.
9. **5080d89b9** OpenML as a 5th dataset source (search_openml → verifiable CSV).
10. **ed2a5a755** dataset-intent extraction filter — was extracting garbage
    (`FR-001`/`MUST`/`CSV`/`PNG`) so resolver searched noise → nothing → fabricate.
    `_is_dataset_intent` filters requirement IDs / RFC-2119 keywords / file formats.
    Validated: PROJ-306 `MBPP` now resolves to a VERIFIED HF dataset.
11. **7d8e785b4** CamelCase dataset-name extraction (ImageNet/WikiText/OpenWebText
    were silently missed) + stoplist tool/lib CamelCase (PyTorch/GitHub/DataFrame).

## Key findings (see also memory: paper-init-throughput-bound,
## runbook-impl-path-mismatch-stall)
- **Dominant blocker = fabrication** (~half of executed projects generate synthetic
  input data). Attacked at all 3 roots: prevention (generator guardrails), detection
  (reviewers), SUPPLY (resolver now finds real datasets: intent-filter + CamelCase +
  OpenML).
- Gates verified SOUND end-to-end: `research_accepted` is transient (575/601 crossed
  it); exec-gate trigger correct; paper pipeline healthy (no stall, underpopulated).
- Near-boundary projects (567/574/581 research_complete; 552/261 research_review) are
  arxiv-intake with real reproducibility/science concerns (thin adapters, no code) —
  correctly held, not bugs.
- 35 in_progress projects fully implemented; 28 await a cron exec-gate run (the
  fixes let more pass).

## What's left / next-session
- Let the crons run these fixes; count climbs as sound projects complete real
  research over cron cycles. No remaining in-session-fixable bottleneck found.
- Optional further data-availability sources (UCI/data.gov) — diminishing returns.
- Arxiv-intake reprocessing sometimes yields a thin adapter vs real code (structural;
  affects arxiv-intake review convergence). Not the main count vehicle.
