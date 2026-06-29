# Feature Specification: The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

**Feature Branch**: `001-visual-salience-aDDM`  
**Created**: 2026-05-17  
**Status**: Draft  
**Input**: User description: "Research question: Does visual salience systematically modulate attentional drift patterns in computational models of moral decision-making, and can these modulations predict choice outcomes in existing moral dilemma datasets?"

## User Scenarios & Testing *(mandatory)*

### User Story US-001 - Data Ingestion and Salience Computation (Priority: P1)

The system MUST ingest the Moral Machine dataset and compute visual salience scores for each stimulus (image or text) to prepare the predictor variables for modeling.

**Why this priority**: Without accurate predictor variables (salience), the core hypothesis cannot be tested. This is the foundational data layer required for all downstream modeling.

**Independent Test**: This can be fully tested by running the data pipeline script on a local subset of scenarios and verifying that every row contains a computed salience score (numeric value 0.0–1.0) and that no rows are dropped due to missing stimulus data.

**Acceptance Scenarios**:

1. **Given** the raw Moral Machine dataset file, **When** the ingestion script runs, **Then** a processed CSV is produced with a `salience_score` column populated for all rows.
2. **Given** a scenario containing only text (no image), **When** the salience module processes it, **Then** a separate text-salience heuristic score is assigned rather than failing.

---

### User Story US-002 - aDDM Simulation and Parameter Fitting (Priority: P2)

The system MUST implement the attentional drift diffusion model (aDDM) and fit its parameters (drift rate, threshold, salience weight) to the observed choice data using grid search.

**Why this priority**: This implements the core computational mechanism (aDDM) to test if salience improves prediction over a baseline. It is the primary engine of the research.

**Independent Test**: This can be fully tested by running the fitting script on a held-out test set and verifying that the model converges (likelihood stabilizes) and outputs a log-likelihood metric without requiring GPU hardware.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset with salience scores, **When** the aDDM fitting script executes, **Then** the model converges within 30 minutes on a 2-core CPU runner.
2. **Given** a grid search over salience weights (0.0–1.0), **When** the search completes, **Then** the best-fitting weight is recorded in the output log.

---

### User Story US-003 - Model Comparison and Sensitivity Analysis (Priority: P3)

The system MUST compare the salience-augmented model against a baseline (no salience) model and perform a sensitivity analysis on decision thresholds to ensure robustness.

**Why this priority**: This validates the findings through statistical comparison (AIC/BIC, 5-fold cross-validation), ensuring the effect is not an artifact of arbitrary thresholds and framing the result as an association.

**Independent Test**: This can be fully tested by executing the comparison script and verifying that the output report includes AIC/BIC differences and a sensitivity table showing performance variation across threshold sweeps.

**Acceptance Scenarios**:

1. **Given** both baseline and salience-augmented model outputs, **When** the comparison script runs, **Then** it reports the AIC/BIC difference and significance (p-value) of the improvement.
2. **Given** a salience threshold cutoff, **When** the sensitivity analysis runs, **Then** it sweeps the cutoff over values {0.01, 0.05, 0.10} and reports the variation in log-likelihood and AIC.

---

### Edge Cases

- What happens when the Moral Machine dataset image URL is broken or inaccessible? (System MUST fallback to text-only heuristics for that specific scenario).
- How does system handle non-convergence of the aDDM optimizer? (System MUST log the failure, exclude that scenario from the final aggregate, and cap retries at 3).
- What happens if visual salience is highly correlated with actual culpability attributes? (System MUST compute Variance Inflation Factor (VIF) and flag collinearity > 5.0 in the report).
- What happens during threshold sensitivity analysis? (System MUST sweep cutoff over {0.01, 0.05, 0.10} and report log-likelihood and AIC variation, not false-positive rates).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and subset the Moral Machine dataset to ≤ 50,000 rows to fit within 7 GB RAM limits. (See US-001)
- **FR-002**: System MUST compute visual salience using ITTI/GBVS algorithms for images; for text-only stimuli, system MUST compute a separate text-salience score using word-frequency and position heuristics (distinct from visual salience). (See US-001)
- **FR-003**: System MUST implement the aDDM simulation using only NumPy/SciPy in default precision (float64) without CUDA or mixed-precision training. (See US-002)
- **FR-004**: System MUST perform grid search over salience weights (0.0 to 1.0 in steps of 0.1) to identify the maximum likelihood parameters. (See US-002)
- **FR-005**: System MUST perform a sensitivity analysis on the decision threshold, sweeping the cutoff over absolute differences {0.01, 0.05, 0.10} and reporting how the log-likelihood and AIC vary across them. (See US-003)
- **FR-006**: System MUST frame all reported findings as associational correlations between salience and choice outcomes, explicitly avoiding causal language regarding moral virtue. (See US-003)
- **FR-007**: System MUST apply multiple-comparison correction (e.g., Bonferroni) if more than a small number of hypothesis tests are conducted on the same dataset. (See US-003)
- **FR-008**: System MUST detect absence of explicit 'actual culpability' labels in the dataset and MUST use scenario attributes (number of lives saved/lost, species, social status, age, gender) as proxy control variables for confounding; the Moral Machine dataset does not contain explicit 'actual culpability' labels as it is a survey experiment measuring moral preferences, not real-world accident data (convention in computational ethics literature, see Awad et al. Nature). (See US-003)

### Key Entities *(include if feature involves data)*

- **Scenario**: A single moral dilemma instance containing binary choice outcome, stimulus attributes, and computed salience score.
- **Model Parameters**: A set of fitted values including drift rate, threshold, non-decision time, and salience weight.
- **Comparison Metric**: A statistical measure (AIC, BIC, Log-Likelihood) used to evaluate model performance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Salience computation time is measured against ≤ 30 minutes for [deferred] scenarios. (See US-001)
- **SC-002**: Model convergence rate is measured against ≥ 95% of 5-fold cross-validation splits converging within 30 minutes. (See US-002)
- **SC-003**: Sensitivity analysis reports variation in log-likelihood and AIC across threshold sweeps {0.01, 0.05, 0.10}. (See US-003)
- **SC-004**: Collinearity diagnostics (VIF) are measured against established thresholds to flag predictor redundancy. (See US-003)

## Assumptions

- The Moral Machine dataset is accessible via the public URL provided in the idea markdown without authentication barriers.
- The CI runner provides OpenCV, NumPy, and SciPy pre-installed in the environment.
- Text-based salience heuristics (word frequency/position) are a valid construct for measuring text prominence (distinct from visual salience).
- The analysis is strictly observational; no random assignment of stimuli to participants occurs, so causal claims are excluded.
- The standard CPU runner is sufficient for grid search optimization on the subsetted dataset within the allocated job limit.
- The dataset contains sufficient scenario attributes (e.g., number of lives saved/lost) to serve as control variables for 'actual role' if available.