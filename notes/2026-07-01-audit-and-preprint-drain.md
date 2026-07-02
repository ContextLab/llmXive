# Deep audit + Reviewed-Preprints drain — session notes (2026-07-01/02)

## What landed (all pushed to origin/main unless noted)

1. **Review-quality tuning** (commit 1d5dbbc60): vision figure reviewer
   (`paper_reprocess/preprint_figures.py`, qwen3.5-122b multimodal — needs a
   REAL token budget + thinking off, else empty replies; one figure per call
   with ALL captions passed for cross-reference), curated 9-lens preprint panel
   (dropped generic holistic + code_quality/data_quality/text_formatting),
   strengthened third-party-paper preamble (no LaTeX/typography nitpicks, external
   code links are sufficient, can't-see-figures rule), `_YAML_REMINDER` retry.
2. **21 preprints regenerated** with the final reviewer (ffc8f9503): 21/21 ok,
   9 lenses × 21 projects, all records schema-valid, PDFs + action_items rebuilt,
   `web/data/projects.json` rebuilt (reviewed_preprints=21).
3. **Audit fixes** (ec3fc83e4): reprocess.py docstring (was describing the
   retired modify flow), dialog.js follow-up link now opens the project modal,
   submit-a-paper disclosure (auto-reviewed, never modified/republished),
   About-tab "Reviewed Preprints — we review, never rewrite" section.
4. **CI gaps** (in ffc8f9503): reprocess.yml installs poppler-utils (vision
   figure lens needs it; silently skipped in CI without), header rewritten;
   Paper Compile workflow now runs `scripts/build_missing_preprint_pdfs.py
   --max 10` per tick (drain runner has no TeX Live → preprints arrive without
   themed PDFs; the sweep fills them in).

## Audit findings (evidence-based)

- **#1 systemic: brainstorm→posted throughput wall.** Census (837 projects):
  ZERO brainstorm-origin projects have ever reached research_accepted / paper_*
  / posted. 660 brainstorm-origin: 183 project_initialized, 101 validated
  (median 16 days stale), 95 flesh_out_in_progress, 95 specified, 74
  in_progress; furthest = ONE project at research_review. NOT a stranding bug —
  `validated` is schedulable, the scheduler load-balances correctly; there is
  simply ~837 projects vs a few advance ticks/hour on free CI. Fix directions
  (not implemented; needs owner decision): more advance workers/cadence, stage
  batching (like implement-stage batching), or capping brainstorm intake until
  WIP drains.
- **Security: SOUND** on the highest-risk surfaces: lualatex runs WITHOUT
  shell-escape on untrusted arXiv source; tarball extraction uses
  `filter="data"` (no zip-slip); workflow inputs are env-quoted + digit-sanitized.
- **Repo bloat: .git = 4.1 GB.** Every CI tick clones/checks out this. PDFs and
  binary artifacts accrue per preprint (~2 PDFs each × 177). Mitigations to
  consider: git-lfs for `projects/**/paper/pdf/*.pdf`, shallow/partial clones in
  workflows (`fetch-depth: 1` + sparse checkout), artifact storage outside git.
- **Push race:** any local bulk push (~200MB) loses to cron commit cadence
  (~1/min). Procedure that works: disable the committing workflows
  (llmXive Pipeline 268086210, Submission Intake 275994767, Personality
  276410003, Paper Compile 276480098, HF Daily 276460428, Advance 303787277,
  Maintenance 303787278, Reprocess 304403248), cancel in-flight runs, push,
  re-enable. CI's own commit-and-push.sh is fine for small deltas.
- **Old-code failed run 28555012459 was protective**: pre-push sha, its final
  push lost the race 8× and nothing landed (no old-path modifications leaked).

## Current state / in flight

- 156 intakes at paper_ingested; drained by reprocess cron (3/tick every 20min,
  dispatchable with drain_tasks=N) via `python -m llmxive run --stage
  paper_ingested` → finalize_reviewed_preprint (VERIFIED the cron path uses the
  new handler). Dispatched an accelerator run with drain_tasks=8.
- Preprint PDFs for cron-drained intakes appear on the NEXT Paper Compile tick
  (sweep). Vision figure lens active in CI only after poppler commit lands.
- Reviewed Preprints tab live with 21 fully-reviewed preprints.

## Verification recipe (quality spot-check of a drained preprint)

- reviews dir has 9 lenses (no paper_reviewer/code_quality/data_quality/
  text_formatting records); figure_critic record exists (vision) once poppler
  is in; verdicts parse via llmxive.state.reviews.read; action_items.md +
  preprint.json + followup_project_id present; follow-up project exists at
  brainstormed WITHOUT paper_authors byline.
