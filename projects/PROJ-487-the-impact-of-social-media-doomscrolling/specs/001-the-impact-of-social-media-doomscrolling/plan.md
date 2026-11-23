# Implementation Plan: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

**Branch**: `001-news-volume-anxiety` | **Date**: 2026-10-27 | **Spec**: `specs/001-news-volume-anxiety/spec.md`
**Input**: Feature specification from `/specs/001-news-volume-anxiety/spec.md`

## Summary

This feature implements a time-series analysis pipeline to quantify the relationship between aggregate negative news publication volume (GDELT EventCount) and anticipatory anxiety indicators (Google Trends search volume). The technical approach involves fetching raw daily time-series data via AWS S3 bulk download (GDELT) and robust session-based fetching (Google Trends), preprocessing for stationarity (Seasonal Differencing -> STL Decomposition -> Cointegration Check), and performing statistical analysis including Pearson/Spearman correlation, Granger causality tests across multiple lags (with Holm-Bonferroni correction), and sensitivity analysis. The pipeline is designed to run entirely on CPU within 6 hours on a standard CI runner.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `requests`, `pytrends`, `pyyaml`, `matplotlib`, `scikit-learn`, `arch` (for ARCH-LM)
**Storage**: Local CSV files (raw and processed) and JSON reports
**Testing**: `pytest` with `unittest` fixtures for data validation
**Target Platform**: Linux (GitHub Actions runner)
**Project Type**: Data Science Pipeline / CLI
**Performance Goals**: < 6 hours total runtime; < 7 GB RAM usage
**Constraints**: CPU-only execution; no external API keys required for GDELT (public S3 access); Google Trends data must be fetched via `pytrends` with robust retry logic; strict adherence to stationarity checks and cointegration logic before analysis.
**Scale/Scope**: Daily time-series data for a multi-year period (approximately four years of daily observations); analysis of multiple lag windows.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `random_state` pinning in all sampling/analysis steps. External datasets (GDELT S3, Google Trends) are fetched via deterministic API calls with caching. `requirements.txt` will pin versions. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` reference verified literature (Salathé et al., 2012). The pipeline includes Task T015b to validate keyword stability and volume before analysis. Data checksums are recorded. |
| **III. Data Hygiene** | **PASS** | Raw data (`data/raw/`) will be preserved. Processed data (`data/processed/`) will be new files with derivation logs. PII is not applicable to aggregate time-series. |
| **IV. Single Source of Truth** | **PASS** | All figures and statistics in the final report will be generated directly from the `data/processed/` files via scripts, not hand-typed. |
| **V. Versioning Discipline** | **PASS** | The plan includes a step to generate content hashes for all artifacts in `data/` and `code/`. |
| **VI. Temporal Data Alignment** | **PASS** | Task T019 explicitly includes seasonal differencing, STL decomposition, ARCH-LM test, and cointegration checks. The `processed_timeseries.schema.yaml` contract is aligned with these steps. |

## Project Structure

### Documentation (this feature)

```text
specs/001-news-volume-anxiety/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Static Design Artifacts)
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   ├── processed_timeseries.schema.yaml
│   ├── raw_news.schema.yaml
│   └── raw_trends.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-487-the-impact-of-social-media-doomscrolling/
├── data/
│   ├── raw/             # Raw CSVs from GDELT and Google Trends
│   ├── processed/       # Aligned, stationary, normalized time-series
│   └── reports/         # Generated PDF/HTML reports and plots
├── code/
│   ├── fetch/           # Scripts for data acquisition (T010, T015a, T015b)
│   ├── preprocess/      # Scripts for cleaning, STL, Cointegration (T019)
│   ├── analyze/         # Statistical analysis scripts (T029)
│   ├── utils/           # Shared utilities, validation, Pydantic models
│   │   └── models.py    # Pydantic models generated from contracts/
│   ├── tests/           # Unit and integration tests
│   ├── contracts/       # (Symlink or copy of static YAML schemas for runtime validation)
│   └── main.py          # Pipeline orchestration
└── requirements.txt
```

**Structure Decision**: Single project structure chosen. The pipeline is linear (Fetch -> Preprocess -> Analyze -> Report), making a monolithic `code/` directory with functional sub-packages the most maintainable approach.
**Contracts Clarification**: The `contracts/` directory in the documentation contains **static YAML schema definitions** (design artifacts). The `code/utils/models.py` contains **generated Pydantic models** derived from these YAML files for runtime validation. This resolves the ambiguity between design docs and generated code.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Seasonal Decomposition (STL)** | Time-series with weekly news cycles (e.g., weekend dips) require seasonal differencing or STL to avoid spurious regression. Simple first-order differencing fails for weekly seasonality. | Simple regression without seasonal adjustment would violate statistical rigor and produce invalid p-values. |
| **Cointegration & ECM** | If the relationship is driven by long-run levels (sustained high news volume -> sustained anxiety), differencing destroys this signal. Cointegration tests preserve level relationships. | Blind differencing risks a 'null result' that is an artifact of the methodology rather than a true absence of correlation. |
| **Holm-Bonferroni Correction** | Granger causality tests at different lags are dependent (nested models). Bonferroni is overly conservative and statistically inappropriate. | Bonferroni would likely suppress true predictive signals due to dependency structure. |
| **AWS S3 Bulk Download** | GDELT EventQuery API is rate-limited and unsuitable for 4 years of daily aggregates. | The API approach would fail or require unrealistic retry logic for the full dataset. |

## Implementation Phases

### Phase 0: Data Acquisition & Validation (T010, T012, T015a, T015b)

**Objective**: Fetch raw data and validate keyword stability.

*   **T010**: Initialize project structure (`data/`, `code/`, `contracts/`).
*   **T012**: **Fetch GDELT Data via AWS S3 Bulk Download**.
    *   Download the GDELT GKG bulk files for a multi-year period from the public AWS S3 bucket.
    *   Filter for `EventCount` with `AvgTone < 0` (negative sentiment).
    *   Aggregate to daily frequency.
    *   *Constraint*: Use `s3fs` or direct `wget` for bulk retrieval to avoid API rate limits.
*   **T015a**: **Fetch Google Trends Data**.
    *   Use `pytrends` to fetch daily search volume for primary keywords: "anticipatory anxiety", "worry about future".
    *   Implement exponential backoff and retry logic with a bounded maximum number of attempts for anti-scraping measures..
*   **T015b**: **Validate Keyword Stability (New)**.
    *   Check if fetched time-series have sufficient volume (non-zero for >5% of days).
    *   If a keyword fails, switch to fallback keywords: "stress about future", "pandemic fear".
    *   *Action*: If all keywords fail, exit with error "Insufficient data for anxiety proxy".
    *   *Output*: `data/raw/anxiety_trends.csv` with metadata on which keyword was used.

### Phase 1: Preprocessing & Stationarity (T019)

**Objective**: Clean, align, and ensure stationarity.

*   **T019**: **Preprocess Data**.
    *   **Alignment**: Merge GDELT and Trends on date (intersection). Preserve zero-event days.
    *   **Missing Data**: Linear interpolation for nulls. Preserve explicit zeros.
    *   **Stationarity Protocol**:
        1.  **Seasonal Differencing**: Apply first-order differencing with lag=7 (weekly cycle) to both series.
        2.  **ADF Test**: Test for stationarity.
        3.  **STL Decomposition**: If still non-stationary, apply STL (Seasonal-Trend decomposition using Loess) to remove trend and seasonality.
        4.  **Simple Differencing**: If STL fails, apply simple first-order differencing.
    *   **Cointegration Check**: Test if original (non-differenced) series are cointegrated (Engle-Granger or Johansen).
        *   *If Cointegrated*: Proceed to Error Correction Model (ECM) analysis.
        *   *If Not Cointegrated*: Proceed with differenced series for Granger Causality.
    *   **Variance Stability**: Perform ARCH-LM test on residuals.
    *   **Normalization**: Z-score normalization (mean=0, std=1) of the final series.
    *   *Output*: `data/processed/aligned_timeseries.csv` and `data/processed/stationarity_check.csv`.

### Phase 2: Statistical Analysis (T029)

**Objective**: Compute correlations, causality, and sensitivity.

*   **T029a**: **Correlation Analysis**.
    *   Compute Pearson and Spearman correlation coefficients.
    *   Report p-values.
*   **T029b**: **Granger Causality**.
    *   Test at multiple short-to-medium lags and a short-term lag.
    *   Apply **Holm-Bonferroni correction** for multiple comparisons (5 tests).
    *   *Output*: p-values, F-statistics, significance flags.
*   **T029c**: **Sensitivity Analysis**.
    *   Sweep lag windows and report significance rate.
    *   *Output*: `data/reports/analysis_results.json`.

### Phase 3: Reporting (T030)

**Objective**: Generate visualizations and final report.

*   **T030a**: **Generate Plots** (Lag plots, correlation heatmaps).
*   **T030b**: **Assemble Report** (HTML/PDF).
*   **T030c**: **Validate Outputs** against `contracts/` schemas.

## Task Dependencies

*   T015b depends on T015a (data fetch).
*   T019 depends on T012 and T015b (raw data).
*   T029 depends on T019 (processed data).
*   T030 depends on T029 (results).

## Compute Feasibility

*   **CPU-First**: All operations (pandas, statsmodels, arch) are CPU-bound.
*   **Memory**: Dataset (sufficiently sized) fits easily in RAM.
*   **Time**: Estimated runtime < 1 hour on a 2-core CPU.
*   **GPU**: Not required.

## Risk Mitigation

*   **Google Trends Fragility**: `pytrends` is unofficial. Mitigation: Local caching of fetched data, retry logic, and fallback keywords.
*   **GDELT Bulk Size**: S3 bulk download is large but manageable via streaming or chunked processing.
*   **Stationarity Failure**: If STL fails, the pipeline logs a warning and proceeds with simple differencing, noting the limitation.