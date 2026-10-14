# Implementation Plan: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

**Branch**: `001-doomscrolling-anxiety` | **Date**: 2026-10-14 (rev. 3) | **Spec**: `specs/001-the-influence-of-social-media-doomscroll/spec.md`
**Input**: Feature specification from `/specs/001-the-influence-of-social-media-doomscroll/spec.md`

## Summary

The pipeline must (1) download **verified, programmatically-accessible parquet datasets** and test them against the required-variable schema, (2) clean via listwise deletion with a hard stop if N < 30, (3) fit an OLS regression of anxiety on negative-news exposure controlling for baseline anxiety, age, and gender, (4) compute the exposure–anxiety correlation, (5) run OLS assumption diagnostics, (6) run the conditional robustness check (only if `social_media_engagement` exists and correlates r > 0.3 with `news_exposure_freq`), and (7) generate a scatter plot with regression line and 95% CI.

**CRITICAL DATA-AVAILABILITY FINDING (blocking)**: The only datasets with **verified** URLs (three NLP text corpora on Hugging Face — mini-xlsum, 0-percent-human-dataset-og, and 100-percent-human-dataset; see research.md) do **NOT** contain any of the required variables (`news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`, `social_media_engagement`). The previously cited "Pew social_media_anxiety" Hugging Face dataset **does not exist as a verified source** and has been removed from this plan. **No verified open dataset containing the required schema is currently available.**

**Consequence**: The research question cannot be answered and SC-001–SC-004 cannot be measured with currently available data. The pipeline will still be built and executed for real against the three verified parquet files; the schema-validation stage will detect the variable mismatch and record a halt with an explicit, logged error (the FR-001 edge case). This executed halt record is **interim ingestion evidence only** — it is NOT a scientific deliverable and does NOT satisfy the spec's research intent.

## Advancement Criterion (operationalized)

This stage advances to statistical results ONLY when one of the following occurs:

1. **A verified dataset containing the required schema is supplied** (news-exposure frequency, anxiety score, baseline anxiety, age, gender; ideally social-media engagement), at which point FR-003–FR-008 and SC-001–SC-004 execute for real; OR
2. **The spec is formally re-scoped** to the data-availability finding (see "Required spec revision" below).

**Interim acceptance bar for this revision**: the executed pipeline produces `output/results/regression_results.json` with `data_status = "HALTED_NO_VALID_DATASET"`, containing real downloads, SHA-256 checksums, actual column inventories, and the missing-variable list. SC-001–SC-004 are reported as **BLOCKED-PENDING-DATA** (not satisfied, not "NOT-APPLICABLE-passed"); SC-005 (runtime) is measured for real. The halt is an honest engineering outcome, not a research result, and no statistical claim is advanced on its basis.

## Required spec revision (root cause — spec.md is not editable in this revision)

`spec.md` still asserts "The system MUST download a specified public survey dataset … that contains the required variables" (US-1 scenario 1) and SC-001–SC-004 presuppose real regression outputs. Since no verified dataset with that schema exists, the spec must be revised to either (a) supply a verified dataset URL, or (b) mark US-1 scenario 1, FR-003–FR-008, and SC-001–SC-004 as **blocked-pending-verified-dataset**, with the data-availability finding (executed halt record) as the interim acceptance outcome. **This plan flags that re-scope for kickback to the spec stage; it does not itself modify spec.md.**

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas>=2.0.0`, `numpy>=1.24.0`, `statsmodels>=0.14.0`, `scikit-learn>=1.3.0`, `matplotlib>=3.7.0`, `pyarrow>=14.0.0`, `pyyaml>=6.0`, `jsonschema>=4.19.0` (pinned in `requirements.txt`)
- **Storage**: Local filesystem (`data/`, `output/`)
- **Testing**: `pytest` with contract validation against schemas in `contracts/`
- **Target Platform**: Linux (GitHub Actions free-tier, 2 cores, ~7 GB RAM, CPU-only)
- **Performance Goals**: Entire pipeline ≤ 60 seconds on the verified parquet files (SC-005)
- **Constraints**: No GPU; no imputation; hard stop if N < 30; all random seeds pinned; **no synthetic/simulated/hard-coded results** — every reported number must come from a real computation on real downloaded data.

## Constitution Check

| Principle | Status | Action / Justification |
|-----------|--------|------------------------|
| I. Reproducibility | PASS | Seeds pinned; the three verified parquet URLs are fetched deterministically on every run. |
| II. Verified Accuracy | PASS (rev. 2) | Only the three verified dataset URLs are cited. The fabricated "Pew social_media_anxiety" URL has been removed. |
| III. Data Hygiene | PASS | Raw parquet stored under `data/raw/` with SHA-256 checksums; derivations write new files. |
| IV. Single Source of Truth | PASS | All statistics trace to `data/processed/` and `code/`; no hand-typed numbers. |
| V. Versioning Discipline | PASS | Content hashes recorded; `requirements.txt` pinned. |
| VI. Ethical Human-Subjects Handling | PASS | Verified sources are public text corpora (no participant data). If a real survey dataset is later verified, its anonymization status will be documented before use. |
| VII. Psychometric Validity | **BLOCKED (documented)** | No verified dataset currently provides any validated anxiety instrument. The plan proceeds under this documented Principle-VII block pending a verified dataset (see Advancement Criterion); the proxy-flag machinery (FR-008) is implemented and will activate if/when a suitable verified dataset is added. |

## Project Structure

```
specs/001-the-influence-of-social-media-doomscroll/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md
```

```
projects/PROJ-540-the-influence-of-social-media-doomscroll/
├── code/
│   ├── __init__.py
│   ├── ingest.py          # download verified parquets, checksum, schema validation, cleaning
│   ├── model.py           # OLS fit, diagnostics, correlation, robustness logic
│   ├── viz.py             # scatter plot
│   ├── validate_sc.py     # SC-001..SC-005 validation script (writes real inspection report)
│   └── main.py            # orchestration
├── data/
│   ├── raw/               # downloaded parquet files (immutable)
│   └── processed/         # cleaned CSV (only if a dataset passes schema validation)
├── output/
│   ├── plots/
│   └── results/
│       └── regression_results.json   # SSoT for BOTH outcomes (OK or HALTED, incl. nested halt_report)
├── outputs/
│   ├── success_criteria_log.txt   # REAL output of validate_sc.py
│   └── signoff_report.json
├── tests/
│   ├── test_ingest.py
│   └── test_model.py
├── artifacts/project_artifact.zip
├── requirements.txt
└── README.md
```

## Complexity Tracking

One documented constitution block exists: **Principle VII (Psychometric Validity) is BLOCKED** pending a verified dataset containing a validated anxiety instrument (see Constitution Check and Advancement Criterion). This is the only open principle issue; no other constitution violations. The conditional robustness logic (FR-006) remains a dedicated sub-task.

## Methodological Rigor & FR/SC Coverage

Status legend: **CONDITIONAL-BLOCKED** = the plan element is fully implemented but cannot execute or be measured until a verified dataset with the required schema is supplied (see Advancement Criterion).

| Spec ID | Requirement | Plan Element | Status |
|---------|-------------|--------------|--------|
| FR-001 | Download public dataset & verify schema | `code/ingest.py` (T010) downloads each **verified** parquet URL, computes SHA-256, and validates columns against `contracts/dataset.schema.yaml`. Per the spec's edge case, a dataset lacking required variables triggers a logged error and halt — this is the **expected current outcome** with the verified sources. | EXECUTES (halt is the real current outcome) |
| FR-002 | Listwise deletion; hard stop if N < 30 | `code/ingest.py` (T012), applied only after a dataset passes schema validation. | CONDITIONAL-BLOCKED |
| FR-003 | Fit OLS; ensure distinct constructs | `code/model.py` (T018/T019a): metadata-based distinctness check; drops `baseline_anxiety` and sets `coupling_risk` if coupled. | CONDITIONAL-BLOCKED |
| FR-004 | Pearson/Spearman correlation | `code/model.py` (T020). | CONDITIONAL-BLOCKED |
| FR-005 | Scatter plot with CI | `code/viz.py` (T025). | CONDITIONAL-BLOCKED |
| FR-006 | Conditional robustness check (r > 0.3 gate) | `code/model.py` (T022): computes `r_engage`; runs top-quartile OLS only if r > 0.3 and the variable exists; otherwise logs warning and skips. | CONDITIONAL-BLOCKED |
| FR-007 | Assumption checks (linearity, homoscedasticity, normality) | Breusch-Pagan, Shapiro-Wilk, residual plots in `code/model.py`. | CONDITIONAL-BLOCKED |
| FR-008 | Proxy-anxiety flag | `proxy_flag` in cleaned data and `output.flags`. | CONDITIONAL-BLOCKED |
| SC-001 | p < 0.05 for `news_exposure_freq` | `code/validate_sc.py` reads the **real** `regression_results.json` and reports PASS/FAIL/**BLOCKED-PENDING-DATA**. | CONDITIONAL-BLOCKED |
| SC-002 | R² reported | Same validation script, from real output. | CONDITIONAL-BLOCKED |
| SC-003 | Robustness consistency | Compared in T022; recorded in `robustness_result`. | CONDITIONAL-BLOCKED |
| SC-004 | Assumption-check results | From real Shapiro-Wilk/BP outputs. | CONDITIONAL-BLOCKED |
| SC-005 | Runtime ≤ 60 s | Measured with `time.perf_counter()` around the real pipeline run; recorded in `runtime`. | EXECUTES |

**Multiple comparisons**: single primary hypothesis (β₁ on `news_exposure_freq`); no family-wise correction required. **Power**: the spec mandates the N ≥ 30 hard stop and the 30 ≤ N < 100 preliminary flag; no numeric a-priori N was specified in the spec, so none is invented here — the pipeline implements exactly the spec's thresholds. **Causal framing**: all outputs carry an explicit `associational_only: true` note; data are observational. **Collinearity**: VIF computed for all predictors; VIF > 10 flags instability per the spec's edge case.

## Compute Feasibility

All operations are O(N) on parquet files well under 1 GB; runs in seconds on the 2-core CPU runner. No GPU work anywhere.

## Data Availability (corrected)

| Candidate | Verified URL | Contains required variables? |
|-----------|--------------|------------------------------|
| mini-xlsum text corpus | `https://huggingface.co/datasets/gsstein/mini-xlsum/resolve/main/data/test-00000-of-00001.parquet` | **NO** — NLP text-summarization corpus, no survey variables |
| 0-percent-human text corpus | `https://huggingface.co/datasets/gsstein/0-percent-human-dataset-og/resolve/main/data/test-00000-of-00001.parquet` | **NO** — human-vs-AI text corpus |
| 100-percent-human text corpus | `https://huggingface.co/datasets/gsstein/100-percent-human-dataset/resolve/main/data/test-00000-of-00001.parquet` | **NO** — human-vs-AI text corpus |
| YouGov | — | **No verified source found** (not citable) |
| "Pew social_media_anxiety" | — | **Removed — was not a verified source; must not be cited or downloaded** |

Note: these three sources are NLP corpora unrelated to the General Social Survey; they are used only to exercise the real ingestion path. **Conclusion**: no verified open dataset currently supports this analysis. See Advancement Criterion: advancing to statistical results requires a verified dataset with the required variables or a formal spec re-scope.

## Task Outline (high-level; `tasks.md` generated later)

| Phase | Task ID | Description | Dependencies | Notes |
|-------|---------|-------------|--------------|-------|
| 0 | T001 | Pin seeds; scaffold `code/`, `data/`, `output/` layout | – | Constitution I |
| 1 | T010 | Download the three **verified** parquet URLs; compute SHA-256; validate schema per file; log per-file column inventory | T001 | FR-001; expected outcome: mismatch logged, halt |
| 2 | T011 | Record checksums and column-inventory report under `data/` and `output/results/` | T010 | Constitution III |
| 3 | T012 | Listwise deletion + N ≥ 30 hard stop + low-power warning (executes only if a dataset passes validation) | T010 | FR-002; CONDITIONAL-BLOCKED |
| 4 | T013 | Write cleaned CSV (conditional on T012 success) | T012 | Constitution III; CONDITIONAL-BLOCKED |
| 5 | T019a | Construct-distinctness check; `coupling_risk` flag | T013 | FR-003 precondition; CONDITIONAL-BLOCKED |
| 6 | T018 | Fit OLS with covariates (conditional) | T019a | FR-003, FR-007; CONDITIONAL-BLOCKED |
| 7 | T020 | Pearson/Spearman correlation (conditional) | T018 | FR-004; CONDITIONAL-BLOCKED |
| 8 | T022 | Conditional robustness check with r > 0.3 gate | T018 | FR-006; CONDITIONAL-BLOCKED |
| 9 | T025 | Scatter plot + 95% CI (conditional) | T018 | FR-005; CONDITIONAL-BLOCKED |
| 10 | T030 | Assemble `output/results/regression_results.json` — the SSoT output file. When a dataset validates it holds the full regression results; when none validates it holds `data_status: "HALTED_NO_VALID_DATASET"` with the nested `halt_report` (sources, checksums, real column inventories, missing variables). **No standalone halt_report.json file is produced.** | T018–T025 | Real outputs only — **no placeholder values** |
| 11 | T041 | **REDO**: write `code/validate_sc.py`, EXECUTE it against the real pipeline outputs, and commit the generated `outputs/success_criteria_log.txt` with per-SC PASS/FAIL/BLOCKED-PENDING-DATA and the evidence line each verdict is based on | T030 | Rejected earlier for missing artifacts; must show executed script + report |
| 12 | T043 | **REDO**: update `README.md` with reproducibility instructions, dataset-availability finding, real results summary (or the documented halt), and limitations | T041 | Rejected earlier; actual file required |
| 13 | T044 | **REDO**: create `artifacts/project_artifact.zip` containing `data/processed/` (or the raw-data mismatch record), `outputs/`, and `code/`; record its SHA-256 | T043 | Rejected earlier; actual archive required |
| 14 | T045 | **REDO**: generate `outputs/signoff_report.json` referencing the archive hash, the success-criteria log, the ingestion evidence (downloaded files + checksums), and — if a dataset validated — the regression JSON and plots; commit all referenced artifacts | T041, T043, T044 | Rejected earlier; every referenced artifact must exist on disk |

Ordering: downloads precede consumption; model fitting precedes diagnostics/plots; validation, documentation, and archiving occur last. **Every task must produce real, inspectable artifacts; any task whose evidence consists of descriptions rather than executed output is incomplete.**

---