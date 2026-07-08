# Feature Specification: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

**Feature Branch**: `001-investigate-inverse-square-law`  
**Created**: 2026-06-16  
**Status**: Draft  
**Input**: User description: "Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Harmonization (Priority: P1)

The researcher must be able to download raw force-vs-separation data from the specified arXiv supplementary materials, convert all measurements to SI units, and align them onto a common separation grid with a fully propagated covariance matrix representing both statistical and systematic uncertainties.

**Why this priority**: Without a unified, uncertainty-aware dataset, no statistical inference can be performed. This is the foundational step that enables all subsequent modeling and is the primary bottleneck for reproducibility.

**Independent Test**: Can be fully tested by executing the data pipeline script against the provided arXiv URLs and verifying that the output is a single CSV/JSON file containing aligned force data, separation distances, and a valid positive-definite covariance matrix, with no missing values in the 10⁻⁵–10⁻⁴ m range.

**Acceptance Scenarios**:

1. **Given** the arXiv supplementary data files are accessible, **When** the pipeline script runs, **Then** it outputs a harmonized dataset where all force values are in Newtons and distances in meters, with a covariance matrix dimension matching the data length.
2. **Given** datasets with different original units (e.g., dynes, micrometers), **When** the conversion logic is applied, **Then** the resulting values match the expected SI equivalents within a tolerance of a negligible relative error.
3. **Given** a dataset with reported systematic uncertainties, **When** the propagation step runs, **Then** the resulting covariance matrix diagonal includes the sum of squared statistical and systematic errors.

---

### User Story 2 - Bayesian Model Inference (Priority: P2)

The researcher must be able to run the affine-invariant MCMC sampler (`emcee`) to estimate the posterior distributions of the Yukawa strength (α) and length scale (λ), and compute the Bayesian evidence for both the Newtonian-only and Yukawa-extended models using nested sampling (`dynesty`).

**Why this priority**: This step directly addresses the research question by quantifying the probability of deviations from the inverse-square law. It is the core analytical engine of the project.

**Independent Test**: Can be fully tested by running the inference script on the harmonized dataset and verifying that the output includes posterior samples for α and λ, a Bayes factor value, and that the MCMC chains show convergence (e.g., Gelman-Rubin statistic < 1.01) within the 6-hour CPU limit.

**Acceptance Scenarios**:

1. **Given** the harmonized dataset and defined priors, **When** the MCMC sampler executes, **Then** it produces [deferred] total samples (a set of walkers × 5000 steps) that converge to a stable posterior distribution for α and λ (Gelman-Rubin < 1.01).
2. **Given** the Newtonian and Yukawa models, **When** the nested sampler runs, **Then** it outputs a log-evidence value for each model, allowing the calculation of the Bayes factor K.
3. **Given** a standard 2-core CPU runner, **When** the full inference pipeline runs, **Then** it completes within the 6-hour job limit.

---

### User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

The researcher must be able to perform leave-one-experiment-out cross-validation and systematic uncertainty inflation tests to ensure the derived constraints on α are not driven by a single dataset or specific error assumptions.

**Why this priority**: Scientific claims regarding new physics or tightened constraints require robustness against dataset-specific artifacts. This step validates the reliability of the primary results.

**Independent Test**: Can be fully tested by running the robustness script, which iteratively removes one dataset and inflates covariance, and verifying that the resulting Bayes factors and 95% credible intervals for α remain stable (e.g., shifts < 10% in the upper limit) across all iterations.

**Acceptance Scenarios**:

1. **Given** the full combined dataset (containing ≥3 independent runs), **When** the leave-one-out loop executes, **Then** the resulting credible upper limits on α vary by a small margin across all iterations.
2. **Given** the baseline covariance matrix, **When** the uncertainty inflation test runs (increasing covariance by [deferred]), **Then** the resulting Bayes factor changes by a negligible amount in log-units, indicating robustness.
3. **Given** a specific outlier dataset, **When** it is excluded, **Then** the system reports whether the primary conclusion (null constraint vs. deviation) changes, flagging if the result is dataset-dependent.

---

### Edge Cases

- What happens if the arXiv supplementary data files are missing or the URL redirects? (System must fail gracefully with a clear error message and not proceed to inference).
- How does the system handle datasets where the separation range does not fully overlap with the 10⁻⁵–10⁻⁴ m target window? (System must interpolate or exclude non-overlapping regions and log a warning).
- How does the system behave if the MCMC chains fail to converge within the step limit? (System must detect non-convergence, log a warning, and optionally extend steps or flag the result as unreliable).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse raw force-vs-separation data from the supplementary section of the referenced arXiv preprint and the recent review calibration curves, converting all units to SI (Newtons, meters) before processing. The harmonized dataset MUST contain at least 3 independent experimental runs to support valid leave-one-out cross-validation; if fewer are available, the system MUST fallback to bootstrap resampling. (See US-1)
- **FR-002**: System MUST construct a full covariance matrix for the harmonized dataset by propagating both statistical uncertainties and systematic error budgets provided in the source files. (See US-1)
- **FR-003**: System MUST implement the Yukawa-modified force model \(F(r)=F_N(r)\,[1+\alpha\,\exp(-r/\lambda)]\) and perform Bayesian inference using `emcee` with exactly 100 walkers and 5000 steps, OR until the Gelman-Rubin statistic < 1.01, whichever requires more steps, to sample the posterior of α and λ. (See US-2)
- **FR-004**: System MUST compute the Bayesian evidence for both the Newtonian-only and Yukawa-extended models using `dynesty` nested sampling to derive the Bayes factor K. (See US-2)
- **FR-005**: System MUST execute a leave-one-experiment-out cross-validation loop and a systematic uncertainty inflation test ([deferred] increase in covariance) to assess the stability of the derived constraints. (See US-3)
- **FR-006**: System MUST enforce a strict runtime limit of ≤6 hours and memory limit of ≤7 GB RAM on the inference pipeline, automatically sampling data if necessary to fit constraints. (See US-2)
- **FR-007**: System MUST output the credible upper limits on α for length scales λ in the micrometer range, formatted for direct comparison with literature values. (See US-2)
- **FR-008**: System MUST perform an injection-recovery test where a known non-zero α is injected into simulated data with realistic noise, and the pipeline MUST recover the injected value within the credible interval. (See US-2)
- **FR-009**: System MUST perform a null-simulation test where α=0 is the true value but systematic errors are present, to establish a baseline false-positive rate for the Bayes factor K. (See US-2)

### Key Entities

- **HarmonizedDataset**: Represents the unified force-distance data with aligned grids and a full covariance matrix.
- **ModelPosterior**: Represents the sampled distribution of parameters (α, λ, scale factor) from the MCMC run.
- **BayesianEvidence**: Represents the computed log-evidence values for the Newtonian and Yukawa models.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The tightness of the 95% credible upper limits on α is measured against the constraints reported in the 2023 review (arXiv:2305.06325) for the same specific experimental subset to verify consistency or improvement. (See FR-007)
- **SC-002**: The statistical significance of the model preference is measured by the Bayes factor K against the Kass–Raftery scale (K > 3 indicates substantial evidence) AND against the null-simulation baseline established in FR-009 to ensure the result is not a systematic artifact. (See FR-004, FR-009)
- **SC-003**: The robustness of the results is measured by the variation in the [deferred] credible upper limits across the leave-one-out cross-validation iterations (must be < 15%). (See FR-005)
- **SC-004**: The computational feasibility is measured by the total runtime of the inference pipeline against the GitHub Actions job limit. (See FR-006)
- **SC-005**: The validity of the inference pipeline is measured by the injection-recovery test (FR-008), requiring the recovered α to fall within the 95% credible interval of the injected value. (See FR-008)

## Assumptions

- The arXiv supplementary data files for the 2021 experiment (2106.08611) and the calibration curves for the 2023 review (2305.06325) are publicly accessible and remain stable in their current format throughout the project duration.
- The `emcee` and `dynesty` Python libraries are compatible with the default Python version on the GitHub Actions runner and do not require GPU acceleration or CUDA dependencies.
- The dataset size after harmonization will fit within the available RAM limit of the free-tier runner; if not, a random subsample of the force-distance points will be used for the MCMC run.
- The systematic uncertainty budgets provided in the source papers are sufficient to construct a valid covariance matrix without requiring additional external data or estimation.
- The inference time for the fixed 5000-step MCMC run is expected to be measurable against the 6-hour limit, and the system will flag if it exceeds this bound.