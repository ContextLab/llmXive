# Reviewed Preprints — implementation handoff (2026-07-01)

**Spec:** `docs/superpowers/specs/2026-07-01-reviewed-preprints-design.md` (APPROVED).
**Branch:** `feat/reviewed-preprints` (NOT merged — feature branch off main).
**Ethics:** intake papers keep the ORIGINAL authors; llmXive had been MODIFYING them
without consent. Fix = never modify; review-only; credit authors+submitter+review-
models only; spawn a separate llmXive follow-up.

## DONE (ethics core — committed + tested on the branch)
1. `types.py` `Stage.REVIEWED_PREPRINT` (terminal); `scheduler._NEVER_PICK` + it;
   `lifecycle.ALLOWED_TRANSITIONS` PAPER_INGESTED→REVIEWED_PREPRINT (+ terminal).
   `paper_reprocess/preprint.py`: `write_preprint_manifest` / `load_preprint_manifest`
   / `is_reviewed_preprint` / `ingestion_statement`. Tests:
   `test_reviewed_preprint_manifest.py`.
2. `web_data._project_authors`: when `paper/preprint.json` present, credit ONLY
   original authors (metadata.json) + submitter + reviewer runs (by underlying
   `model_name`); modifier runs excluded. Tests: `test_reviewed_preprint_attribution.py`.
3. `paper_reprocess/reprocess.py::reprocess_ingested_paper`: NO branch_code/in-place
   transform — writes preprint.json, preserves paper bytes (byte-identical, tested),
   parks at REVIEWED_PREPRINT. Tests: `test_reviewed_preprint_routing.py`.
   (classify_paper/branch_code/branch_nocode kept for reuse below, not called by intake.)

## REMAINING (additive — do in order; TDD; real tests, no mocks)

### 3b. Spawn the separate follow-up brainstorm project
- Refactor `paper_reprocess/branch_nocode.py`: today `to_followup_idea` transforms
  the SAME project in place (→ brainstormed, drops byline). Extract a
  `spawn_followup_project(preprint_project, repo_root)` that CREATES A NEW project
  (new PROJ id via the project-id allocator — see `state/project_id_lock.py` /
  `project_store` create path used by brainstorm), writes the follow-up idea into the
  NEW project's `idea/` (reuse `_propose_extension` + `_write_followup_idea` +
  `build_bibtex_entry`), drops the byline on the NEW project (`_drop_original_authors`),
  sets it to `brainstormed`, and records its id back into the preprint's
  `preprint.json::followup_project_id`. Call it from `reprocess_ingested_paper` (and
  the migration). The ORIGINAL preprint keeps its authors.

### 4. Review-only runner
- `run_preprint_review(preprint_project, repo_root)`: run the 7 research reviewers
  ONCE (reuse `convergence/project_runner.py` / `agents/research_reviewer.py`) — NO
  convergence/revise loop, NO accept/reject. Write review records under
  `paper/reviews/` + a consolidated `paper/action_items.md` from the reviewers'
  concerns. Gate offline via the conftest reviewer stub pattern; real-call test with
  `LLMXIVE_REAL_TESTS=1`.

### 5. PDFs (prepend cover; review report)
- `original-llmxive.pdf` = a single `llmxive.cls`-themed cover page (title, authors,
  abstract, `ingestion_statement(...)`, llmXive blurb+link, link to review report,
  link to follow-up) PREPENDED to the untouched original PDF via `pypdf`
  (`PdfWriter`; append cover pages then original). Body byte-preserved — assert page
  count = 1 + original, and original pages unchanged.
- `peer-review-llmxive.pdf` = reviewer verdicts + feedback + action items rendered
  with `llmxive.cls` ("llmXive Peer Review of <title>"). Reuse
  `pipeline/pdf_pipeline/restyle.py`. Real-PDF test + open to eyeball.

### 6. Web UI — "Reviewed Preprints" tab
- `web_data.py`: build a `reviewed_preprints` collection (from `preprint.json` +
  metadata.json + action_items + the two pdf paths + followup id) into
  `web/data/projects.json` (see `_project_to_entry` / the payload builder).
- `web/index.html`: add `<button class="tab" data-tab="reviewedPreprints">…` beside
  Published/In Progress/Activity/Contributors (line ~71) + a count.
- `web/js/app.js` (+ `data.js`): a preprint card variant + modal — "Based on a
  preprint" badge, source link, `ingestion_statement`, credit list (original authors
  + submitter + review models, labeled), the two PDFs, the action-item list, link to
  the follow-up project. Follow-ups render normally in In Progress→Published.
- Build projects.json, render, screenshot card + modal to verify.

### 7. Migration of the 177 (dry-run FIRST — get maintainer approval before execute)
- `scripts/migrate_reviewed_preprints.py --dry-run` → report per intake project
  (those with `paper/metadata.json`): current stage, modifications that WOULD be
  discarded (backfilled specs/plan/tasks, in_progress code, revised paper), the
  follow-up it would spawn. `--execute` → revert to clean Reviewed Preprint (discard
  modifications; preserve `paper/source`, original `paper/pdf`, `metadata.json`), run
  3b+4+5, write preprint.json. **Do NOT run --execute without the maintainer eyeballing
  the dry-run.** ~177 projects; consider staging follow-up spawns if load is a concern.

## Verify before merge
- Full `pytest tests/unit tests/contract tests/integration -m "not slow"` green.
- Build both PDFs for one real intake (e.g. PROJ-601) and open them.
- Build projects.json + screenshot the new tab.
- Then merge `feat/reviewed-preprints` → main; run the dry-run migration; present it.
