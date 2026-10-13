# Tasks: Evaluating the Impact of Code Generation on Code Review Quality Using LLMs

**Input**: Design documents from `/specs/001-evaluating-llm-code-review-impact/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/

**Re-plan note**: The prior task list failed verification because the data pipeline never produced its promised artifacts (`prs_labeled.csv`, `complexity_scores.csv`, `prs_metrics.csv`, `results.json`). This revision restructures the remaining work around an executable end-to-end pipeline: one runnable driver that fetches real PR data, labels it, scores complexity, extracts metrics, and writes all declared CSV/JSON artifacts. Verified infrastructure tasks are preserved as completed; rejected tasks are re-opened and consolidated. No synthetic fallback data is permitted anywhere.

## Phase 1: Setup and first end-to-end analysis

Completed infrastructure (preserved from prior rounds; do not redo):

- [ ] T002 Initialize Python 3.11 project with `requirements.txt` pinning `requests`, `pandas`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `statsmodels`, `pytest`, `pydantic`.
- [ ] T004 Create `code/utils/seeds.py` for pinned random seeds.
- [ ] T005 Create `code/utils/config.py` defining repo list (`psf/requests`, `microsoft/vscode`, `numpy/numpy`), thresholds, and API settings.
- [ ] T007 Create `code/data/fetch_github.py` with `fetch_batch(repo, limit, max_retries=3)` implementing batch processing, exponential backoff, and SHA-256 checksums of raw JSON in `data/raw/`.
- [ ] T008 Implement checksum utility in `code/utils/checksum.py`.
- [ ] T009 Create `code/audit/manual_validation.py` sample-size calculation `calculate_sample_size(N_llm, min_threshold=10, scaling_factor=0.1)`.
- [ ] T013 [US1] Fetch up to 200 PRs from the prioritized repo list with pagination, backoff, and raw JSON + checksums (FR-001).
- [ ] T014 [US1] Primary signature classification (`llm`/`human`) with `confidence_score` per PR and `flagged` boolean for confidence < 0.6 (FR-002).
- [X] T015a/T015c [US1] Secondary detector (entropy + n-gram anomaly on hardcoded Python token baseline) emitting `detector_score` (FR-007).
- [ ] T018 [US1] Repository fallback logic when LLM count < 10.
- [ ] T019a [US1] Manual audit checklist template `code/audit/manual_audit_checklist.csv` (SC-004).
- [ ] T024b [US2] Mann-Whitney U sensitivity-test implementation.
- [ ] T025 [US2] Effect sizes (Cohen's d) and α = 0.05 significance determination.
- [ ] T026 [US2] `code/analysis/sensitivity_analysis.py` for the detector-only cohort (FR-008).
- [ ] T035 [US2] Correlation analysis between complexity and review metrics (SC-003).
- [ ] T036c [US3] Rule-based narrative synthesis for Discussion/Limitations.
- [X] T047/T053 [US2] Effect-size interpretation and sensitivity-comparison reporting in the results aggregation.
- [ ] T042 PII filter and scan (`code/utils/pii_scan.py`).

Remaining executable work:

- [ ] T060 [US1] [FR-001] [FR-002] [FR-007] Build a single end-to-end data pipeline driver `code/data/run_pipeline.py` that executes, in order: (1) fetch real PRs via `code/data/fetch_github.py` with strict fail-loudly behavior — on unrecoverable API error after max retries raise `RuntimeError`, NEVER fall back to synthetic/mock data (T044 concern); (2) classify via `code/data/classify_prs.py` producing `source_type`, `confidence_score` (weighted combination of signature strength and detector score, signature weighted higher — T048), `flagged_for_audit`, `detector_score` with a deterministic seed (T050); (3) write `data/processed/prs_labeled.csv` conforming to `specs/.../contracts/pr_schema.schema.yaml` (pr_id, repo, source_type, confidence_score, flagged_for_audit, comment_count, time_to_merge_minutes, review_cycles, complexity_score, loc, entropy_score, hour_of_day, day_of_week), validated row-by-row with pydantic (`LabeledPR` model; raise `ValueError` on malformed rows — T051).
    - **Verification**: `python code/data/run_pipeline.py` exits 0 and `data/processed/prs_labeled.csv` exists, is non-empty, has all schema columns, every row has `source_type ∈ {llm, human}` and `confidence_score ∈ [0,1]`. This repairs rejected T017 (missing CSV) by making the driver itself the artifact producer.
    - **Dependencies**: T013, T014, T015a (all complete).

## Phase 2: Complete the study and validate its evidence

- [ ] T061 [US1] [FR-005] Extend `code/analysis/complexity.py` to read `data/processed/prs_labeled.csv`, fetch each PR's diff (from raw JSON in `data/raw/`), and compute cyclomatic complexity (AST-based decision-point counting, exposed as a graph traversal consistent with the plan's networkx dependency) and LOC per PR, processing diffs in chunks (fixed-size line blocks) to stay within RAM (T045/T041 concern). Write `data/processed/complexity_scores.csv` with columns `pr_id` (int), `complexity_score` (float), `loc` (int), joined on `pr_id` from `prs_labeled.csv`. No memory-fallback model is needed since only standard metrics are used (spec FR-005 permits standard metrics directly).
    - **Verification**: file exists, non-empty, one row per PR in `prs_labeled.csv`, all values ≥ 0. Repairs rejected T033a/T033b.
    - **Dependencies**: T060.

- [ ] T062 [US2] [FR-003] Complete `code/data/extract_metrics.py` to compute `comment_count`, `time_to_merge_minutes` (created_at → merged_at; unmerged PRs excluded and count logged), `review_cycles` (heuristic: commits_count or comments_count/2 per data model), plus temporal covariates `hour_of_day`/`day_of_week`, joining `prs_labeled.csv` with `complexity_scores.csv` on `pr_id`. Write `data/processed/prs_metrics.csv` with the full pr_schema columns. Fail loudly (raise) if either input CSV is missing — never fabricate rows.
    - **Verification**: `data/processed/prs_metrics.csv` exists, non-empty, schema-valid per `pr_schema.schema.yaml`. Repairs rejected T022/T023.
    - **Dependencies**: T061.

- [ ] T063 [US2] [FR-004] [SC-001] [SC-002] Complete `code/analysis/statistical_tests.py` as the primary analysis: Shapiro-Wilk normality check per metric per group (log warning "Data non-normal, but t-test forced per FR-004" when p < 0.05, do not switch tests), outlier check on `time_to_merge_minutes` (> 3 IQR → log warning, no exclusion — T052), then independent two-sample t-tests (primary) and Mann-Whitney U (sensitivity) for comment density and time-to-merge between `llm` and `human` groups, with Cohen's d, rank-biserial correlation, and α = 0.05 significance flags. Write `data/processed/results.json` conforming to `statistical_result.schema.yaml` (both `t_test` and `mann_whitney_u` blocks per metric), including effect-size interpretation and the sensitivity-comparison section from T047/T053. If N_LLM < 10, still write results but mark the output `exploratory: true`.
    - **Verification**: `data/processed/results.json` exists, contains t-statistics, p-values, effect sizes for comment density and time-to-merge, and sample sizes matching `prs_metrics.csv` group counts. Repairs rejected T024a.
    - **Dependencies**: T062.

- [ ] T064 [US1] [SC-004] Complete `code/audit/manual_validation.py` as a full CLI audit runner (repairing truncated T019b): load `prs_labeled.csv`, select a stratified sample (size from `calculate_sample_size`, min 10, 10% of N_LLM), emit `data/audit/audit_input.jsonl` with PR diff summaries and the checklist items from T019a, then run an interactive CLI loop (with file-polling fallback, max 60 s) collecting `human_label` per PR, logging each decision with timestamp to `data/audit/audit_log.jsonl` (T054). Compute the error rate of the automated signature label against the human ground truth (checklist + detector score per SC-004) and write `data/audit/manual_audit_results.json` and `data/audit/error_rate.json`.
    - **Verification**: all three audit artifacts exist and are non-empty; `error_rate.json` contains a numeric `error_rate` field. If no human input is available in the run environment, the script must exit with a clear non-zero status and message (not silently pass) — the gate task T065 then records `human_input_needed`.
    - **Dependencies**: T060.

- [ ] T065 [US2] [FR-004] Implement the results gate in `code/analysis/generate_results_report.py`: read `data/audit/error_rate.json` and write `data/processed/gate_status.json` with schema `{"status": "blocked" | "passed" | "exploratory"}` — `blocked` if error rate > 0.05, `exploratory` if N_LLM < 10, else `passed`. If `error_rate.json` is missing, write status `human_input_needed` and exit non-zero with message "Manual audit (T064) must complete before aggregation" (replacing the prior hard FileNotFoundError so the pipeline state is observable). Aggregate all findings into `data/processed/results.json` (extending T063's output with `complexity_correlation` read from the correlation analysis and the gate status).
    - **Verification**: `data/processed/gate_status.json` exists with a valid status value; `results.json` contains the complete aggregated schema.
    - **Dependencies**: T063, T064.

## Phase 3: Reproducible results and paper handoff

- [ ] T066 [US3] [FR-006] Implement `code/analysis/visualizations.py` to generate publication-quality (consistent font, palette, labeled axes — T049) side-by-side boxplots and histograms for comment density and time-to-merge by group, reading `data/processed/prs_metrics.csv`. Write `reports/figures/boxplots.pdf` and `reports/figures/histograms.pdf` (each > 50 KB, ≥ 2 vector paths, verified with pdfplumber in `tests/integration/test_visualizations.py`).
    - **Verification**: both PDFs exist and pass the size/vector-path checks.
    - **Dependencies**: T062.

- [ ] T067 [US3] [FR-006] Implement `code/analysis/generate_report_narrative.py` to inject results from `data/processed/results.json`, `gate_status.json`, and the correlation output into `docs/report_template.md`, synthesizing Discussion/Limitations via the completed T036c logic (including the N_LLM < 10 power limitation and the associational-not-causal framing from the spec's assumptions). Produce `reports/figures/final_report.pdf` with sections Executive Summary, Methodology, Results (embedding the T066 plots), Discussion, Limitations. If gate status is `blocked`, raise `ValueError("Pipeline blocked: error rate exceeded threshold")`; if `exploratory`, include the note but do not abort.
    - **Verification**: `reports/figures/final_report.pdf` exists, contains all five section headings, and embeds the boxplot/histogram figures.
    - **Dependencies**: T065, T066.

- [ ] T068 Re-run the documented workflow end-to-end from its declared inputs (`python code/data/run_pipeline.py` → T061 → T062 → T063 → T064 → T065 → T066 → T067), confirm every declared artifact exists with the expected schema (`prs_labeled.csv`, `complexity_scores.csv`, `prs_metrics.csv`, `results.json`, `gate_status.json`, audit artifacts, figure PDFs), update `quickstart.md` with the exact runnable command sequence, and document the paper-stage handoff: the final report must state the primary t-test findings (SC-001, SC-002), the complexity correlation (SC-003), the audit error rate (SC-004), the FR-008 sensitivity comparison, and the associational framing and multiple-comparison limitation honestly, including any negative or underpowered (N_LLM < 10) outcomes.
    - **Verification**: a fresh clone following `quickstart.md` reproduces all artifacts; no hand-typed numbers appear outside `data/processed/results.json`-derived content.
    - **Dependencies**: T067.

## Dependencies and requirement coverage

- **FR-001** (fetch 200 PRs): T013 (done) + T060 (fail-loudly enforcement).
- **FR-002** (classification + confidence): T014 (done) + T060 (calibrated confidence, pydantic validation).
- **FR-003** (metrics): T062.
- **FR-004** (t-tests primary, effect sizes): T063, T065.
- **FR-005** (complexity): T061.
- **FR-006** (visualizations/report): T066, T067.
- **FR-007** (secondary detector): T015a (done) + T060 (deterministic seed).
- **FR-008** (sensitivity analysis): T026 (done) + T063/T065 (reporting).
- **SC-001/SC-002**: T063. **SC-003**: T035 (done) + T065. **SC-004**: T064, T065.
- Execution order: T060 → T061 → T062 → {T063, T066} → {T064} → T065 → T067 → T068. T064 depends only on T060 and can run in parallel with T061–T063.

## Revision behavior

Completed tasks above are preserved verbatim with their identities. Rejected tasks T017, T019b, T033a, T033b, T022, T023, T024a are superseded by T060–T063, which consolidate the missing-artifact root cause (no runnable driver producing the CSVs) into pipeline tasks whose outputs are deterministically verifiable files. Redundant polish tasks (T040, T041, T049, T055) are folded into T060/T061/T066 where scientifically relevant; pure refactoring with no scientific requirement is dropped. No synthetic or mock data is permitted at any stage; a failed real fetch must raise.

## Notes

- Independent two-sample t-tests are PRIMARY per FR-004; Mann-Whitney U is sensitivity analysis (documented deviation in `docs/statistical_protocol_deviation.md`, preserved).
- The secondary detector uses local heuristics (documented deviation in `docs/statistical_detector_deviation.md`, preserved).
- Manual audit (T064) requires human input; if unavailable, the pipeline surfaces `human_input_needed` rather than fabricating an audit result.
