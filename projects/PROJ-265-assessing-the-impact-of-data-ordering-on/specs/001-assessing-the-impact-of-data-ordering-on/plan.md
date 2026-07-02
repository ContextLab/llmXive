# Implementation Plan: Assessing the Impact of Data Ordering on Bootstrapping Results

**Branch**: `001-assess-data-ordering-bootstrapping` | **Date**: 2024-05-22 | **Spec**: `specs/001-assessing-the-impact-of-data-ordering-on/spec.md`

## Summary

This feature implements a computational experiment to quantify how temporal autocorrelation violates the independence assumption of standard non-parametric bootstrapping. The system will generate synthetic AR time series with varying autoregressive coefficients ($\phi$), apply standard bootstrapping to ordered and shuffled versions, and measure the empirical coverage probability of the confidence interval against the theoretical mean (0). It will then validate these findings on segmented real-world data from the UCI Individual Household Electric Power Consumption dataset. The implementation prioritizes CPU-only feasibility on GitHub Actions free-tier runners, ensuring all simulations complete within 6 hours using `scikit-learn`, `statsmodels`, and `numpy`.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `statsmodels`, `pandas`, `scikit-learn`  
**Storage**: Local CSV/Parquet files in `data/`, results in `results/`  
**Testing**: `pytest` with `pytest-randomly` for reproducibility checks  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational research / CLI  
**Performance Goals**: Full simulation (multiple $\phi$ levels $\times$ multiple trials) $\le$ 6 hours on 2 CPU cores.  
**Constraints**: No GPU, no heavy deep learning, strict memory limits (~7GB), deterministic random seeds.  
**Scale/Scope**: A large set of synthetic time series; ~1 year of hourly UCI data segments.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action / Verification |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, fixed random seeds in `code/`, and canonical dataset fetching. |
| **II. Verified Accuracy** | **PASS** | Citations for McNemar's test and UCI dataset will be validated against primary sources before review. The UCI dataset URL is now verified via HuggingFace mirror. Checksums will be validated against the known hash of the verified source. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw UCI data; derivations (segments) written to new files. |
| **IV. Single Source of Truth** | **PASS** | All figures/statistics will trace to `results/coverage_metrics.csv` and specific code blocks. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes; state file updated on changes. |
| **VI. Temporal Autocorrelation** | **PASS** | Plan explicitly requires estimating $\phi$ for every synthetic and real segment; analysis rejects if $\phi$ is omitted. |
| **VII. Coverage Probability** | **PASS** | Plan mandates calculating coverage against theoretical mean (0) for synthetic data. For real data, it uses **CI Width Ratio** (Ordered/Shuffled) as the primary metric to avoid tautology. Comparison uses **Two-Proportion Z-Test** (Primary, per Constitution Principle VII) and **McNemar's Test** (Secondary, per Spec FR-005) to satisfy both requirements. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-data-ordering-bootstrapping/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Drafting target: coverage_metrics.schema.yaml)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-265-assessing-the-impact-of-data-ordering-on/
├── code/
│   ├── requirements.txt
│   ├── __init__.py
│   ├── main.py                  # Entry point for simulation
│   ├── generators.py            # AR(1) synthetic data generation
│   ├── bootstrap.py             # Non-parametric bootstrap & CI logic
│   ├── metrics.py               # Coverage calculation, Z-Test, McNemar's, CI Width Ratio
│   ├── loaders.py               # UCI dataset loading & segmentation
│   └── plots.py                 # Visualization generation
├── data/
│   ├── raw/                     # Raw UCI data (checksummed)
│   └── processed/               # Segmented hourly windows
├── results/
│   └── coverage_metrics.csv     # Primary output artifact
└── tests/
    ├── unit/
    │   ├── test_generators.py
    │   ├── test_bootstrap.py
    │   └── test_metrics.py
    └── integration/
        └── test_full_pipeline.py
```

**Structure Decision**: Single project structure selected. This is a self-contained computational experiment. Separating into frontend/backend is unnecessary. The `code/` directory contains pure Python modules for modularity and testing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The scope is strictly defined by the spec: synthetic generation, bootstrap application, and real-world validation. | A simpler alternative (e.g., only synthetic) would fail to meet the "practitioner" validation requirement in User Story 3. |

## Methodology Overview

### 1. Synthetic Data Generation (FR-001)
- Generate independent AR(1) time series for each $\phi \in \{0.0, 0.1, \dots, 0.9\}$.
- Length $N=100$.
- Error term $\epsilon \sim N(0, 1)$.
- **Validation**: Verify that the sample autocorrelation at lag 1 approximates $\phi$.

### 2. Bootstrap Procedure (FR-002)
- **Method**: Standard non-parametric bootstrap (resampling with replacement).
- **Resamples**: 1,000 per time series.
- **Statistic**: Sample mean.
- **CI Construction**: Percentile method (2.5th and 97.5th percentiles).

### 3. Coverage Calculation (FR-003)
- **Synthetic Data**:
  - **Ground Truth**: Theoretical mean = 0.
  - **Metric**: Binary indicator (1 if $0 \in [L, U]$, else 0).
  - **Aggregation**: Average of indicators across multiple trials for each $\phi$.
- **Real-World Data**:
  - **Challenge**: No known theoretical mean exists for UCI segments.
  - **Solution**: Use **CI Width Ratio** (Ordered Width / Shuffled Width) as the primary metric.
    - Rationale: If ordering inflates variance, the CI for ordered data should be wider than for shuffled data. This avoids the tautology of checking if the CI contains the sample mean.
    - Secondary Metric: "Self-Consistency" (does CI contain sample mean?) is noted but not used as primary evidence due to tautological nature.

### 4. Shuffling & Comparison (FR-004, FR-005)
- **Shuffle**: Random permutation of the time series array to break temporal dependence.
- **Comparison**:
  - **Primary Test**: **Two-Proportion Z-Test** comparing the coverage rates of Ordered vs. Shuffled across the [deferred] trials. This satisfies Constitution Principle VII.
  - **Secondary Test**: **McNemar's Test** applied to the **AGGREGATE** 2x2 contingency table of the [deferred] trials (counts of n11, n10, n01, n00), NOT per-trial.
    - *Clarification*: The test compares the proportion of covered intervals. The contingency table is constructed by iterating through all [deferred] trials and tallying:
      - n11: Covered in Ordered AND Covered in Shuffled
      - n10: Covered in Ordered AND Not Covered in Shuffled
      - n01: Not Covered in Ordered AND Covered in Shuffled
      - n00: Not Covered in Ordered AND Not Covered in Shuffled
    - This satisfies Spec FR-005 while avoiding the statistical error of applying McNemar's to per-trial data.

### 5. Real-World Segmentation (FR-006, FR-007)
- **Load**: Load UCI Power Consumption data from verified source.
- **Clean**: Drop/impute missing values.
- **Segment**: Non-overlapping hourly windows.
- **Filter**: Do NOT pre-filter for $\phi > 0.3$. Include ALL valid segments ($N \ge 30$).
- **Estimate**: Calculate $\hat{\phi}$ for each segment.
- **Stratify**: Bin segments by estimated $\hat{\phi}$ (e.g., 0.0-0.1, 0.1-0.2, etc.) to demonstrate the continuous relationship.
- **Analyze**: Compute CI Width Ratio for each bin to show degradation as a function of $\phi$.

### 6. Sensitivity Analysis on N (Addressing Sample Size Concerns)
- Run a subset of the synthetic simulation with $N \in \{50, 100, 200\}$ at $\phi=0.5$.
- **Goal**: Verify that the coverage drop is driven by autocorrelation, not small sample size artifacts or variance in $\hat{\phi}$ estimation.
- **Expected**: Coverage drop should persist across N, though magnitude may vary slightly.

## Statistical Rigor & Constraints

### Multiple Comparisons
- We perform hypothesis tests (one per $\phi$ level).
- **Correction**: Apply Bonferroni correction or False Discovery Rate (FDR) if testing significance of the *difference* at each level. However, the primary output is the *curve* of coverage vs. $\phi$, not just p-values. The visual trend is the primary evidence.

### Sample Size & Power
- **Trials**: [deferred] per $\phi$ level.
- **Power**: Sufficient to detect a drop in coverage from 0.95 to 0.80 with high power ($>0.99$) given the binary nature of the outcome.
- **Limitation**: $N=100$ per series is small, which may increase variance in $\hat{\phi}$ estimation, but is sufficient for the bootstrap exercise. Sensitivity analysis (N=50, 200) will address this.

### Causal Inference
- **Observational**: The synthetic data is generated with a known causal structure (AR(1)). The "cause" is the autocorrelation $\phi$. The "effect" is coverage degradation.
- **Identification**: The controlled generation allows for a direct causal claim within the simulation.
- **Real Data**: Observational. Claims will be framed as "associational" regarding the relationship between $\hat{\phi}$ and coverage drop/CI width inflation.

### Measurement Validity
- **Instruments**: `numpy` (AR generation), `statsmodels` (AR estimation), `scipy.stats` (Z-test, McNemar). All standard, validated libraries.
- **Collinearity**: Not applicable to the synthetic generation (controlled). In real data, if multiple lags are correlated, the AR(1) estimate is a simplification; we acknowledge this limitation.

## Compute Feasibility

- **Hardware**: GitHub Actions free-tier (2 CPU, 7GB RAM).
- **Memory**: trials $\times$ 100 points $\times$ 1,000 resamples = $10^8$ operations.
  - With vectorization (NumPy), this fits easily in memory.
  - No GPU required.
- **Runtime**: Estimated < 2 hours for full simulation.
- **Libraries**: `numpy`, `scipy`, `pandas`, `statsmodels` are all CPU-optimized and available in standard Python wheels.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Missing Real-World Dataset** | High (User Story 3 fails) | The plan now uses a verified URL with retry logic. If it fails, the step aborts with an error, preventing silent failure. |
| **McNemar's Test Assumptions** | Medium | Clarified that test is applied to aggregate counts, not per-trial. |
| **Short Time Series ($N<30$)** | Low | Filtered out as per FR-007. |
| **Runtime Exceeds h** | High | Vectorized NumPy operations and $N=100$ ensure the simulation is lightweight. |
| **Selection Bias in Real Data** | High | Removed pre-filtering for $\phi > 0.3$. All segments are analyzed and binned. |
| **Tautology in Real Data Coverage** | High | Replaced Coverage Probability with CI Width Ratio for real data. |