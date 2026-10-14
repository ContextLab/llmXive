# Tasks: Mindfulness Components and Delivery Formats in ASD Social Skills

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/cleaned_study.schema.yaml`, `contracts/effect_size.schema.yaml`.

**Layout authority**: All source code lives under `code/` (per the constitution's Reproducibility Requirements, which pin `pyproject.toml` at `projects/PROJ-008-psychology-research/code/`). The `src/` tree shown in plan.md's Project Structure section is superseded; every `src/...` path in the plan maps to the corresponding `code/...` path here. (Plan-root cause; flagged for kickback.)

**Spec discrepancies flagged for kickback** (plan-root causes; tasks follow the methodologically correct plan behavior and the spec must be amended to match):
- FR-008/US1 specify proportional control splitting; the plan (and T004 below) instead select a single primary control group per treatment arm to avoid double-counting participants and unit-of-analysis error. Spec FR-008 must be amended to record this override.
- FR-003 specifies regex-pattern extraction; the plan (and T004 below) use a structured keyword-based pipeline with confidence scoring and manual-verification flags. Spec FR-003 must be amended to record this override.
- `contracts/effect_size.schema.yaml` omits `unknown` from `format_tag` while `cleaned_study.schema.yaml` permits `delivery_format: unknown`. T005 handles this by excluding unknown-format studies from `effect_sizes.csv` (logged in `data/raw/excluded_studies.log`) pending a contract amendment adding `unknown` to the `format_tag` enum.
- Prior reviewer records referencing a 33-task `specs/001-psychology-research/tasks.md` are stale relative to the current `specs/002` artifacts and must be reconciled by the platform per Constitution Principle V before review points are awarded.

## Task ordering

- T001 and T003 are parallel-safe setup tasks.
- T002 depends on T001. T004 depends on T001–T003. T005 depends on T004. T006 depends on T005. T007 depends on T006. T008 depends on T006. T009 depends on T007 and T008. T012 depends on T004–T008.
- T011 (checksum baseline) depends on T002, T004–T009, and T012 — it must run AFTER all data/raw/, data/processed/, and data/results/ files exist.
- T010 (CI workflow) depends on T001–T009, T011, and T012 and must run LAST.

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish the environment and run a "thin slice" of the pipeline to prove the data flow from API retrieval to a basic effect size result.

- [ ] T001 [P] Establish project layout under `code/` (the authoritative layout; see header note), install pinned dependencies from `code/pyproject.toml`, and document the execution flow in `quickstart.md`. <!-- FAILED-IN-EXECUTION: code/setup_project.py exit=1 -->
    - Verify: `mkdir -p code/{data,analysis,viz,lib} data/{raw,processed,results} docs contracts tests/{unit,integration,contract}` executes without error.
- [ ] T002 [US1, US2] Implement a thin-slice pipeline in `code/data/collector.py`, `code/data/cleaner.py`, and `code/analysis/effect_sizes.py` that fetches one real record from ClinicalTrials.gov, cleans it, and calculates a Hedges' $g$ effect size. <!-- FAILED-IN-EXECUTION: code/data/thin_slice.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/thin_slice.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/thin_slice.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/thin_slice.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/thin_slice.py exit=1 -->
    - Output: `data/results/thin_slice_result.json` containing `study_id` and `hedges_g`.
    - Verify: The script executes end-to-end on a real API record without fabrication.
- [ ] T003 [P] Implement the schema validation utility in `code/lib/validation.py` to enforce the contracts defined in `contracts/cleaned_study.schema.yaml` and `contracts/effect_size.schema.yaml`.
    - Verify: A test script in `tests/contract/test_schemas.py` confirms that a valid record passes and a record with an invalid `age_min` (e.g., 5) fails.

**Checkpoint**: The plumbing is verified. A single real record can move from the registry to a calculated metric.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 [US1] Implement the full data collection and cleaning pipeline in `code/data/collector.py` and `code/data/cleaner.py`.
    - Requirements:
        - Fetch from ClinicalTrials.gov and OSF only (Constitution Principle VI), with rate-limiting and exponential backoff on all API calls (FR-002); log every retry.
        - Filter for ASD diagnosis, age 6-12, and social skill outcomes.
        - Handle multi-arm studies by selecting a single primary control group per treatment arm to avoid double-counting participants and unit-of-analysis error (documented override of spec FR-008; see header).
        - Extract intervention components (breathing, body_scan, mindful_movement, combined) using a structured keyword-based pipeline with confidence scoring; entries with low confidence are flagged for manual verification (documented override of spec FR-003; see header).
        - Extract `delivery_format` (caregiver_mediated, child_led, hybrid, unknown) and `social_skill_domain` (FR-010).
        - Implement abstract-only text extraction fallback when full text is unavailable; no full-text OCR (FR-009).
        - Log the search query strings and retrieval timestamps for every study in the retrieval log (Constitution Principle VI).
    - Outputs: `data/raw/verified_snapshot_2026.json` (canonical baseline), `data/processed/cleaned_studies.csv`, `data/raw/excluded_studies.log` (exclusion audit trail with reasons, per US1), and `data/raw/search_retrieval_log.json` (query strings + retrieval timestamps per included study).
    - Verify: `data/processed/cleaned_studies.csv` validates against `cleaned_study.schema.yaml`; `data/raw/excluded_studies.log` lists every excluded study with a reason; `data/raw/search_retrieval_log.json` contains a query string and timestamp for every included study; retrieval logs show only ClinicalTrials.gov and OSF endpoints.
- [ ] T005 [US2] Implement the effect size engine in `code/analysis/effect_sizes.py` to compute Hedges' $g$ with small-sample correction for all included studies (FR-004, FR-013).
    - Requirements: Studies with `delivery_format = "unknown"` are excluded from `effect_sizes.csv` and recorded in `data/raw/excluded_studies.log` (schema contradiction handling; see header) — they remain in `cleaned_studies.csv` and are excluded only from subgroup analysis per Principle VII.
    - Output: `data/processed/effect_sizes.csv`.
    - Verify: `data/processed/effect_sizes.csv` validates against `effect_size.schema.yaml` and values match a manual calculation for a sample row (unit test in `tests/unit/test_effect_sizes.py`).
- [ ] T006 [US2] Implement the meta-analysis core in `code/analysis/meta_analysis.py` to calculate pooled effect sizes and heterogeneity.
    - Requirements:
        - Use random-effects model if $I^2 > 50\%$, otherwise fixed-effects (reported as sensitivity check).
        - Calculate $I^2$ and Cochran's $Q$ statistic with p-value.
        - Pin all random seeds (e.g., `random.seed(42)`, `numpy.random.seed(42)`) in `code/` per Constitution Principle I.
    - Output: `data/results/meta_analysis_summary.json`.
    - Verify: A unit test in `tests/unit/test_meta_analysis.py` reproduces the pooled $g$, $I^2$, and $Q$ from a fixed two-study fixture within tolerance.
- [ ] T007 [US2] Implement subgroup analysis and conditional meta-regression in `code/analysis/meta_analysis.py`.
    - Requirements:
        - Compare mindfulness components (breathing, body_scan, mindful_movement, combined) — data produced by T004.
        - Compare delivery formats (caregiver_mediated vs child_led): the PRIMARY subgroup/meta-regression comparison MUST exclude `delivery_format = "unknown"` entries per Constitution Principle VII.
        - Compare social skill domains (FR-011).
        - Compare follow-up duration (3-month vs others) (FR-012).
        - Apply Bonferroni correction to all subgroup p-values (plan Risk Mitigation).
        - FR-014 conditional: if $N < 10$ studies, suppress meta-regression entirely and record a descriptive-synthesis flag in the output; if $N \ge 10$, run delivery-format meta-regression (Hedges' $g$ as effect metric, per Principle VII).
    - Output: `data/results/subgroup_analysis.json` (including a `meta_regression` block or an explicit `suppressed_reason` when $N < 10$).
    - Verify: A test in `tests/unit/test_subgroups.py` confirms (a) unknown-format entries are absent from the delivery-format subgroup, (b) Bonferroni-corrected p-values are reported, and (c) the meta-regression block is suppressed when the fixture has fewer than 10 studies.
- [ ] T008 [US3] Implement visualization and bias assessment in `code/viz/plotting.py` and `code/analysis/bias.py`.
    - Requirements:
        - Generate forest plots (study CIs + pooled diamond) (FR-006).
        - Generate funnel plots and run Egger's test ONLY if $N \ge 10$ (US3 / FR-006 gating; distinct from FR-014's meta-regression suppression, which is handled in T007).
    - Output: `data/results/forest_plot.png` and `data/results/funnel_plot.png` (only if $N \ge 10$).
    - Verify: A test in `tests/unit/test_plotting.py` asserts the funnel plot file is absent when $N < 10$ and present when $N \ge 10$.
- [ ] T012 [P] Implement the report generator module `code/reporting/generate_report.py` that renders `docs/results.md` from the JSON artifacts in `data/results/` (single source of truth; no hand-typed numbers, Constitution Principle IV).
    - Verify: A test in `tests/integration/test_report.py` confirms every number in a generated report matches the corresponding JSON value.

**Checkpoint**: All scientific computations are complete. Results are stored in `data/results/` and figures are generated.

## Phase 3: Reproducible results and paper handoff

- [ ] T009 [US3] Generate the final research report in `docs/results.md` using the T012 generator, synthesizing all findings.
    - Requirements:
        - If $N = 0$: state "No studies found" and stop (plan Task 12).
        - If $N < 10$: provide a descriptive narrative synthesis and explicitly state that meta-regression, funnel plots, and Egger's test were suppressed.
        - If $N \ge 10$: include the pooled effect size table, subgroup tables, and embedded figures.
        - Link every result to the specific file in `data/results/`.
    - Verify: `tests/integration/test_report.py` covers the $N=0$, $N<10$, and $N\ge10$ branches with fixture inputs.
- [ ] T011 Record the checksum baseline for all data artifacts (Constitution Principle III).
    - Requirements: Generate `data/checksums.sha256` (SHA-256, `sha256sum` format) covering all files under `data/raw/`, `data/processed/`, and `data/results/`. This task MUST run after T002, T004–T009, and T012 so the hashed files exist; raw data is never modified in place afterwards.
    - Output: `data/checksums.sha256`.
    - Verify: `sha256sum -c data/checksums.sha256` passes against the current tree.
- [ ] T010 Implement the CI reproducibility workflow in `.github/workflows/ci.yml`.
    - Requirements:
        - The workflow must load `data/raw/verified_snapshot_2026.json` to ensure the analysis is deterministic.
        - Execute all tests in `tests/` and the full analysis pipeline (T002–T009).
        - After the pipeline run, re-compute `data/checksums.sha256` via `code/lib/verify_ci.py` and compare against the committed baseline from T011; the run fails on any mismatch.
    - Verify: A successful CI run produces artifacts whose SHA-256 hashes match the committed `data/checksums.sha256` baseline (mechanism: `code/lib/verify_ci.py --baseline data/checksums.sha256` exits 0).

## Dependencies and requirement coverage

Every functional requirement, user story, and constitutional principle in `spec.md` maps to exactly one row below, pointing at the implementing task and its verification artifact.

| Requirement | Task | Verification |
|-------------|------|--------------|
| US1 (Collection) | T002, T004 | `data/processed/cleaned_studies.csv` exists and is schema-valid; `data/raw/excluded_studies.log` exists |
| US2 (Analysis) | T002, T005, T006, T007 | `data/results/meta_analysis_summary.json` contains $I^2$ and pooled $g$ |
| US3 (Visualization) | T008, T009 | `data/results/forest_plot.png` exists; `docs/results.md` contains synthesis |
| FR-001 (API sources) | T004 | `data/raw/search_retrieval_log.json` shows only ClinicalTrials.gov and OSF |
| FR-002 (Backoff/rate-limit) | T004 | Retry log entries present in `data/raw/search_retrieval_log.json` |
| FR-003 (Component extraction) | T004 | `component_tag` values in `cleaned_studies.csv` (keyword pipeline; spec override flagged) |
| FR-004 (Hedges' g small-sample correction) | T002, T005 | Unit tests in `tests/unit/test_effect_sizes.py` |
| FR-005 (Random-effects + heterogeneity) | T006 | `meta_analysis_summary.json` contains model_used, $I^2$, $Q$ |
| FR-006 (Forest/funnel plots) | T008 | Plot files present; funnel gated on $N \ge 10$ |
| FR-007 (Schema validation) | T003 | `tests/contract/test_schemas.py` passes |
| FR-008 (Multi-arm handling) | T004 | Single primary control per arm (spec override flagged in header) |
| FR-009 (Abstract-only fallback) | T004 | Fallback path exercised in `tests/unit/test_cleaner.py` |
| FR-010 (Domain extraction) | T004 | `social_skill_domain` column populated in `cleaned_studies.csv` |
| FR-011 (Domain subgroups) | T007 | `subgroup_analysis.json` domain blocks |
| FR-012 (Follow-up subgroups) | T007 | `subgroup_analysis.json` follow-up block |
| FR-013 (Effect sizes from summary statistics) | T002, T005 | Unit tests in `tests/unit/test_effect_sizes.py`; `effect_sizes.csv` schema-valid |
| FR-014 (Suppress meta-regression if N<10) | T007 | `subgroup_analysis.json` `suppressed_reason` when N<10; `meta_regression` block when N≥10 |
| Const. Principle I (Seeds) | T006 | Pinned seeds in `code/analysis/meta_analysis.py` |
| Const. Principle III (Checksums) | T011 | `sha256sum -c data/checksums.sha256` passes |
| Const. Principle VI (Retrieval log) | T004 | `data/raw/search_retrieval_log.json` per-study queries + timestamps |
| Const. Principle VII (Delivery) | T004, T007 | `delivery_format` column present; unknown-format entries excluded from primary subgroup analysis |
| SC-005 (Reproducibility) | T010, T011 | CI run matches committed `data/checksums.sha256` baseline |