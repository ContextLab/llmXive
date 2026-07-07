# Implementation Plan: Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

**Branch**: `001-sentiment-drift` | **Date**: 2024-05-21 | **Spec**: `spec.md`

## Summary

This project implements a reproducible statistical pipeline to analyze the temporal relationship between social media sentiment and macroeconomic indicators (GDP, unemployment) during historical recessions. The approach involves ingesting time-series data from HuggingFace (sentiment) and FRED (economic), aligning them to a weekly frequency with specific interpolation rules, testing for stationarity (ADF) and cointegration (Johansen), and conducting Granger causality tests via Vector Autoregression (VAR) or Vector Error Correction Model (VECM). The system validates results using Moving Block Bootstrap (MBB) with data-driven block lengths and out-of-sample held-out recession periods, all constrained to run on CPU-only free-tier CI.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`, `huggingface_hub`, `pyyaml`, `fredapi`, `responses` (for mocking).  
**Storage**: Local filesystem (`data/`, `code/`, `artifacts/`); CSV/Parquet formats.  
**Testing**: `pytest` (unit tests for data alignment, statistical thresholds), `nbval` (notebook validation).  
**Target Platform**: Linux (GitHub Actions Free Runner: limited CPU, GB RAM).  
**Project Type**: Data Science / Statistical Analysis Pipeline.  
**Performance Goals**: Complete full pipeline (ingest -> model -> viz) in < 4 hours; Memory usage < 6GB.  
**Constraints**: No GPU; No external API calls during CI runs (data must be cached or mocked if credentials missing); Strict adherence to interpolation rules (forward-fill for GDP, linear for sentiment).  
**Scale/Scope**: Historical time-series analysis covering a multi-decade period; A substantial volume of weekly data points.

> Domain-specific empirical specifics (exact counts, dataset sizes) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. Dependencies pinned in `requirements.txt`. Data fetched from canonical sources (HF/FRED) with checksums recorded. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` will only use URLs from the verified datasets block. `Reference-Validator` will run on artifact write. **Note**: CI runs using synthetic/mock data are explicitly marked as 'Simulated' in metadata; 'Verified Accuracy' applies only to runs with real data. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/`. Derivations in `data/processed/`. Checksums recorded in state YAML. PII scan enforced. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats trace to `data/processed/merged_timeseries.csv`. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | `code/update_state.py` automatically updates the `state/projects/...yaml` file with content hashes of artifacts upon generation, ensuring the Advancement-Evaluator Agent functions correctly. |
| **VI. Time-Series Integrity** | **PASS** | ADF, Johansen Cointegration, and alignment logs documented before VAR/Granger. Lag adjustments explicitly recorded. |
| **VII. Sentiment Methodology** | **PASS** | NLP pipeline (model, tokenizer, thresholds) documented in `code/`. Validation on held-out sample required. |

## Project Structure

### Documentation (this feature)

```text
specs/001-sentiment-drift/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Schemas for validation)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data_ingestion.py        # Fetches FRED/HF data, handles alignment
├── preprocessing.py         # Interpolation, stationarity checks, lag logic
├── modeling.py              # ADF, Johansen, VAR/VECM, Granger Causality, MBB
├── validation.py            # Out-of-sample and sensitivity analysis
├── visualization.py         # Plots with NBER shading
├── update_state.py          # Updates state YAML with artifact hashes
├── analysis_notebook.ipynb  # Reproducible execution of full pipeline
└── requirements.txt         # Pinned dependencies

data/
├── raw/                     # Downloaded raw files (checksummed)
├── processed/               # Aligned, cleaned weekly CSVs
└── metadata/                # Checksums, alignment logs, imputation logs

tests/
├── unit/                    # Test interpolation logic, alignment
├── contract/                # Validate schema compliance
└── integration/             # Run full pipeline on sample data
```

**Structure Decision**: Single-project structure selected to minimize overhead for a statistical analysis pipeline. All logic resides in `code/` with clear separation between ingestion, processing, and modeling.

## Implementation Phases

### Phase 0: Data Ingestion & Alignment
- **Goal**: Fetch real data (or mock if CI) and align to weekly frequency.
- **Tasks**:
  - Fetch GDP (GDP), Unemployment (UNRATE), VIX (VIXCLS) from FRED.
  - Fetch sentiment data from HuggingFace (`cardiffnlp/twitter-2020` or similar).
  - Apply **Forward-Fill with Lag Awareness** for GDP/Unemployment.
  - Apply **Linear Interpolation** for Sentiment.
  - Generate `data/processed/merged_timeseries.csv` and `data/processed/imputation_log.json`.
- **Output**: `merged_timeseries.csv`, `imputation_log.json`.

### Phase 1: Preprocessing & Stationarity
- **Goal**: Ensure data meets VAR/VECM assumptions.
- **Tasks**:
  - Perform ADF tests on all series.
  - Perform **Johansen Cointegration Test**.
    - If cointegrated: Proceed to VECM.
    - If not: Differencing (1st diff) and re-test.
  - **De-trending**: Remove step-function bias from quarterly forward-fill using release dummies.
  - Calculate **Minimum Detectable Effect (MDE)** based on N (~800).
- **Output**: `data/processed/stationarity_log.csv`, `data/processed/model_spec.json` (VAR vs VECM).

### Phase 2: Modeling & Granger Causality
- **Goal**: Estimate relationships and test predictive precedence.
- **Tasks**:
  - Fit VAR (or VECM) model.
  - Select optimal lag via AIC.
  - Run Granger Causality tests (F-test) for Sentiment <-> GDP/Unemployment.
  - Run Granger tests with control variables (VIX, News Volume).
- **Output**: `data/processed/model_results.json`.

### Phase 3: Robustness & Sensitivity
- **Goal**: Validate results against artifacts and noise.
- **Tasks**:
 - **MBB**: Calculate optimal block length (Politis & White) and run [deferred] iterations.
  - **Sensitivity Analysis**: Mask a small proportion of data, re-interpolate, re-run Granger, record p-value shifts.
  - **Collinearity Check**: VIF for GDP vs. Unemployment.
- **Output**: `data/processed/robustness_report.json`.

### Phase 4: Out-of-Sample Validation
- **Goal**: Verify predictive validity on unseen data.
- **Tasks**:
  - Split data: Train (early period), Test (recent period).
  - Re-run Granger Causality test on the **Test** set only.
  - Compare results with Train set.
- **Output**: `data/processed/holdout_validation.json`.

### Phase 5: Visualization & Reporting
- **Goal**: Generate final artifacts.
- **Tasks**:
  - Generate time-series plots with NBER shading.
  - Generate impulse response functions.
  - Update `state/projects/...yaml` via `update_state.py`.
- **Output**: `artifacts/figures/`, `analysis_notebook.ipynb`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Johansen Cointegration Test** | Required to avoid 'cointegration trap' (Scientific Soundness). | Differencing without cointegration check loses long-run equilibrium info. |
| **VECM Fallback** | Required if cointegration is found. | Standard VAR is invalid for cointegrated series. |
| **Data-Driven Block Length** | Required for valid MBB (Methodology). | Fixed block duration is arbitrary and may bias CI

Research Question: Does the choice of block duration affect the coverage probability of confidence intervals?
Method: Simulation study comparing coverage probabilities across varying block lengths.
References: [Insert DOI/arXiv/author-year here]. |
| **Out-of-Sample Validation** | Required to distinguish Precision (MBB) from Validity (Science). | MBB on training data is tautological for causal claims. |
| **Control Variables** | Required to address Omitted Variable Bias. | Sentiment alone is confounded by market volatility. |

## Data Resource Strategy

- **Real Data**: FRED Series `GDP`, `UNRATE`, `VIXCLS`; HF Dataset `cardiffnlp/twitter-2020`.
- **CI Fallback**: If API keys missing, `data_ingestion.py` uses `responses` library to mock FRED API responses and generates synthetic data that strictly mimics the schema of the real sources.
- **Verification**: The `imputation_log.json` and `model_results.json` will include a `data_source` flag (`real` or `synthetic`) to ensure 'Verified Accuracy' is only claimed for `real` runs.