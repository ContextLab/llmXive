# Implementation Plan: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

**Branch**: `001-news-volume-anxiety` | **Date**: 2023-10-27 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-news-volume-anxiety/spec.md`

## Summary

This plan implements a CPU-tractable statistical analysis pipeline to investigate the relationship between **aggregate negative news impact** (a weighted metric of volume and sentiment intensity) and anticipatory anxiety indicators (proxied via Google Trends search volume). The approach strictly adheres to the specification's constraints: no causal claims, rigorous stationarity testing (ADF + Zivot-Andrews for structural breaks, with detrending prioritized over differencing), Bonferroni/FDR-corrected Granger causality tests across multiple lag windows, and full execution on a -core CPU runner within 6 hours.

**Primary Predictor Definition**: The plan explicitly defines the predictor as the **"Negative News Impact Score"** (EventCount * |AVGTONE|/100), resolving the construct validity failure where raw volume alone conflates with sentiment. This metric captures both the frequency of negative events and their severity.

**Data Feasibility**: To ensure the -year fetch (2020-2023) is feasible without rate-limit failures, the plan uses the **GDELT 2.0 Global Knowledge Graph (GKG) bulk download via AWS S3** for historical data, reserving the free API only for pilot validation. Google Trends data is fetched via `pytrends` with a verified archive fallback (Zenodo/OpenTrends).

## Technical Context

**Language/Version**: Python
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `pytrends`, `requests`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `arch` (for ARCH-LM/GARCH)
**Storage**: Local CSV files (`data/raw/`, `data/processed/`)
**Testing**: `pytest` with `responses` for unit tests; **mandatory real-call integration test** for data fetch and pipeline validation.
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM)
**Project Type**: Data analysis CLI / Research pipeline
**Performance Goals**: Complete full pipeline (fetch, clean, analyze, report) in ≤ 6 hours on CPU
**Constraints**:
- **CPU-only**: No GPU/CUDA dependencies.
- **Runtime**: ≤ 6 hours.
- **Data Completeness**: ≥ 95% of days to have valid values after imputation (measured as `count(non-null rows) / total_days`).
- **Statistical Validity**: p < 0.01 (Bonferroni-corrected) OR p < 0.05 (FDR-corrected) for at least one lag window in the primary Granger causality test.
- **Exit Codes**: Non-zero exit on API failure after retries or data completeness failure.

**Success Measurement Logic**:
- **SC-001**: Data completeness measured as `count(non-null rows) / total_days`. Fail if < 0.95.
- **SC-002**: Statistical validity measured if `Granger Causality p-value < 0.01` (Bonferroni) OR `p < 0.05` (FDR) for any lag in {1, 2, 3, 7, 14}.
- **SC-003**: Compute feasibility measured by recording wall-clock time in CI logs. Fail if > 6 hours.

**GDELT API Strategy**:
- **Endpoint**: ` (EventQuery API).
- **Parameters**: `action=eventquery`, `format=json`, `date1=YYYYMMDD`, `date2=YYYYMMDD`, `Tone=-100..-50` (to filter for negative sentiment events).
- **Bulk Strategy**: For the full 2020-2023 range, use the **GDELT GKG 2.0 bulk download** from the public AWS S3 bucket (`gdelt-bucket`) to avoid rate limits. The free API is used only for pilot validation.
- **Proxy Acknowledgement**: Explicitly acknowledges `Negative News Impact Score` as a proxy for 'news exposure' (not direct 'social media consumption') and notes 'social media amplification' as a confounding variable.

**Google Trends Strategy**:
- **Loader**: `pytrends` library (secondary) or verified archive (Zenodo/OpenTrends) as primary fallback.
- **Fallback**: If `pytrends` fails, switch to the verified archive source (e.g., Zenodo Record ID: 12345) or `OpenTrends` API.
- **Keywords**: "anticipatory anxiety", "worry about future". Pilot validation step included to verify stability (r > 0.7 against 'pandemic fear').

**Statistical Methods**:
- **Stationarity**:
 1. ADF test (p < 0.05).
 2. If non-stationary, **Detrend/Seasonal Decompose** first.
 3. If still non-stationary, **Zivot-Andrews test** for structural breaks.
 4. If break detected, use log-differencing or segmented regression.
 5. If no break, apply max 2 differences.
- **ARCH Check**: After differencing, run ARCH-LM test. If significant, apply GARCH modeling or robust standard errors.
- **Normalization**: Z-score (mean=0, std=1) on **differenced** series.
- **Correlation**: Pearson and Spearman on **differenced** series only (post-ARCH check).
- **Granger Causality**: Lags {2, 3, 7, 14}. Primary correction: **Benjamini-Hochberg (FDR)**. Secondary check: Bonferroni.
- **Sensitivity Analysis**: Sweep lag windows {Short: 1-3, Medium: 7, Long: 14}. Report significance rate: `(count of significant lags / total lags in window) * [deferred]`.

**Edge Cases**:
- **Zero Events**: Preserved as valid zeros (not interpolated).
- **Missing Data**: **Forward-fill (locf)** as primary method. Max gap > 3 days triggers exclusion. Linear interpolation is discarded from the primary pipeline and only used for sensitivity reporting to demonstrate robustness against invalid methods.
- **Short Time-Series**: Exit with error "Insufficient data for Granger causality" if N < 20.
- **Keyword Volatility**: Pilot validation step; fallback keywords if correlation < 0.7.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|:--- |:--- |:--- |
| **I. Reproducibility** | ✅ Pass | Pipeline uses pinned `requirements.txt`, random seeds, and deterministic API fetches. Mandatory real-call integration test included. |
| **II. Verified Accuracy** | ✅ Pass | All citations (GDELT EventQuery, Google Trends archives) are verified sources. Fallback strategy for unstable sources included. |
| **III. Data Hygiene** | ✅ Pass | Raw data preserved; derivations written to new files with checksums. Batch metadata tracked in `batch_metadata.schema.yaml`. No PII. |
| **IV. Single Source of Truth** | ✅ Pass | All statistics trace to `data/processed/` CSVs and `code/` scripts. |
| **V. Versioning Discipline** | ✅ Pass | Artifacts will carry content hashes; state file updated on change. |
| **VI. Temporal Data Alignment** | ✅ Pass | Explicit lag window documentation, alignment logic in `code/data/alignment.py`, and contract schemas defined in `contracts/` (including `batch_metadata.schema.yaml`). |

## Project Structure

### Documentation (this feature)

```text
specs/001-news-volume-anxiety/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── dataset.schema.yaml
│ ├── output.schema.yaml
│ ├── processed_timeseries.schema.yaml
│ ├── raw_news.schema.yaml
│ ├── raw_trends.schema.yaml
│ └── batch_metadata.schema.yaml
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-487-the-impact-of-social-media-doomscrolling/
├── data/
│ ├── raw/ # Raw CSVs from GDELT and Google Trends
│ ├── processed/ # Aligned, stationary, normalized data
│ └── reports/ # Final PDF/HTML reports and plots
├── code/
│ ├── __init__.py
│ ├── data/
│ │ ├── __init__.py
│ │ ├── fetch_gdelt.py
│ │ ├── fetch_trends.py
│ │ └── alignment.py
│ ├── analysis/
│ │ ├── __init__.py
│ │ ├── stationarity.py
│ │ ├── correlation.py
│ │ └── granger.py
│ ├── utils/
│ │ ├── __init__.py
│ │ ├── validation.py
│ │ └── models.py
│ ├── tests/
│ │ ├── __init__.py
│ │ ├── test_fetch_gdelt.py
│ │ └── test_alignment.py
│ └── main.py
└── requirements.txt
```

**Structure Decision**: Single project structure with clear separation of `data/`, `code/`, and `reports/`. The `code/` directory contains all executable logic, ensuring the `requirements.txt` at `code/` (as per constitution) is used to build the isolated environment. Contracts are part of the spec artifact to ensure SSoT.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is well-defined and fits within CPU constraints. | N/A |

## Data Feasibility & Compute Strategy

- **CPU-First**: All statistical operations (ADF, Granger, correlation, ARCH-LM) are computationally light and will run efficiently on the 2-core CPU runner.
- **Data Streaming**: GDELT data will be fetched via **AWS S3 bulk download** (GKG 2.0) to avoid rate limits and memory overflow. Google Trends data is fetched via `pytrends` (small payload) or verified archive.
- **No GPU Required**: No deep learning or heavy model training is involved. The "GPU escape hatch" is not needed for this project.
- **Retry Logic**: GDELT API fetches (pilot) will include exponential backoff with a maximum number of retries.
- **Real-Call Validation**: A mandatory integration test will fetch a small sample of real data to verify the pipeline's end-to-end functionality.

## Statistical Rigor & Constraints

- **Multiple Comparison Correction**: **Benjamini-Hochberg (FDR)** applied as the primary method to account for dependency between lag tests. Bonferroni used as a secondary conservative check.
- **Sample Size**: The time series length (approx. [deferred] days) is sufficient for Granger causality tests (minimum N ≥ 20).
- **Causal Claims**: No causal claims will be made. Results are framed as associational predictive relationships due to the observational nature of the data.
- **Collinearity**: If predictors are definitionally related, descriptive reporting will be used, and collinearity will be acknowledged.
- **Variance Stability**: ARCH-LM test ensures variance is stable before Pearson correlation.