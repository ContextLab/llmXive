# Specification: Neural Correlates of Anticipatory Reward Processing in Vocal Learning

## Overview
This project investigates the neural correlates of anticipatory reward processing in vocal learning systems, specifically analyzing spike train data in relation to reward magnitude and cue timing.

## User Stories

### US1: Data Ingestion and Pre-processing Pipeline
**Goal**: Load pre-processed spike train data and trial metadata from public repositories (or synthetic source) and align them by trial ID into a unified DataFrame.

**Acceptance Criteria**:
- Data loaded from CSV or Neurodata files in `data/raw/`
- Spike counts calculated in [-500ms, 0ms] window relative to reward
- Validation checks for minimum trials per reward level (>=30)
- Handling of zero-reward trials and silent neurons
- Cue-reward delay validation (flag if <500ms)
- Output: Unified Pandas DataFrame with required columns

### US2: Statistical Modeling and Significance Testing
**Goal**: Fit a Generalized Linear Model (GLM) regressing firing rates on reward magnitude and run a permutation test to validate the coefficient.

**Acceptance Criteria**:
- Dispersion check to select appropriate model family (Poisson vs Negative Binomial)
- GLM fitting with firing_rate ~ reward_magnitude
- Power analysis with MDES calculation
- Permutation test for significance validation
- Robustness checks (categorical GLM, LRT)
- Cross-validation for predictive performance
- Multiple comparisons correction if needed

### US3: Visualization and Reporting
**Goal**: Generate scatter plots of firing rate vs. reward magnitude with confidence intervals and a summary statistics report.

**Acceptance Criteria**:
- Scatter plot with regression line and 95% CI
- Summary report with coefficient, p-value, MDES, CV scores
- Data loss metrics documentation
- Selection bias impact analysis

## Data Model

### Input Schema (contracts/dataset.schema.yaml)
- trial_id: Unique identifier for each trial
- neuron_id: Identifier for recorded neuron
- spike_timestamps: Array of spike times
- reward_magnitude: Magnitude of reward delivered
- cue_timestamps: Array of cue presentation times
- spike_sorting_metadata: SNR, isolation distance metrics

### Output Schema (contracts/output.schema.yaml)
- Unified DataFrame with: trial_id, neuron_id, spike_count, reward_magnitude, timestamp_relative_to_reward
- Validation report (JSON)
- Spike sorting validation report (Markdown)
- Summary statistics report (Text)
- Visualization figures (PNG)

## Functional Requirements

- FR-001: Load data from CSV/Neurodata files
- FR-002: Calculate spike counts in [-500ms, 0ms] window
- FR-003: Select model family based on dispersion
- FR-004: Run permutation test for significance
- FR-005: Generate scatter plot with 95% CI
- FR-006: Generate summary report with all metrics
- FR-007: Validate minimum 30 trials per reward level
- FR-008: Perform k-fold cross-validation
- FR-009: Flag trials with cue-reward delay <500ms

## Security & Compliance

- SC-001: Permutation test iterations >= 1000
- SC-002: MDES calculation with power=0.80, alpha=0.05
- SC-003: 95% confidence intervals on plots
- SC-004: Log data loss metrics (ingestion_rows_total, valid, dropped)
- SC-005: Bonferroni correction for multiple comparisons

## Constraints

- CPU-only execution (no GPU requirements)
- Use only scipy, statsmodels, scikit-learn, pandas, numpy
- Real data from verified sources (OpenNeuro/Zenodo)
- No synthetic data for final results (only for CI validation)
- Python 3.10+
