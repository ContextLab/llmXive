# Feature Specification: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

**Feature Branch**: `001-t-violation-beta-decay`  
**Created**: 2026-08-11  
**Status**: Draft  
**Input**: User description: "Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay? (Physics)"

## User Scenarios & Testing

### User Story 1 - Archival Data Retrieval and Validation (Priority: P1)

The researcher MUST be able to retrieve *published* one‑sided upper limits on the T‑violation D‑coefficient, their confidence levels, reported uncertainties, and experimental conditions for specified nuclei (e.g., $^{6}$He, $^{19}$Ne) from dedicated beta‑decay T‑violation literature repositories (INSPIRE‑HEP, arXiv, and experiment‑specific reports such as emiT, nTRV, and recent neutron‑decay studies) and validate that the data format supports meta‑analysis.

**Why this priority**: This is the foundational step; without retrieving the fundamental observables (upper limits) required for the proposed meta‑analysis, no analysis can occur. This step also validates the feasibility of the approach by confirming the existence of sufficient published data.

**Independent Test**: Can be fully tested by executing the data extraction script against the literature repositories and verifying the output contains upper‑limit values with confidence levels for a target nucleus.

**Acceptance Scenarios**:

1. **Given** a target nucleus (e.g., $^{6}$He) exists in the literature with an upper‑limit entry, **When** the extraction script queries the repositories, **Then** the script retrieves the upper‑limit value, its confidence level (e.g., a conventional [deferred] CL), and associated metadata.
2. **Given** multiple published upper‑limit measurements for the same nucleus, **When** the validation process runs, **Then** the system confirms each dataset contains the necessary metadata (limit value, confidence level, source reference) to perform the meta‑analysis.
3. **Given** a target nucleus where no upper‑limit is reported in the literature, **When** the script processes it, **Then** the script flags the nucleus as "insufficient data" and excludes it from the analysis, reporting the limitation explicitly.

---

### User Story 2 - Rigorous Statistical Combination and Heterogeneity Assessment (Priority: P2)

The system MUST combine the retrieved upper limits **per nucleus** using a DerSimonian‑Laird random‑effects meta‑analysis after converting all limits to a common confidence level (90 % CL) via the standard normal approximation. The procedure must (a) weight each limit by the inverse of its variance, (b) assess heterogeneity with Cochran’s Q and I² statistics, and (c) select a random‑effects model when heterogeneity is statistically significant (p < 0.05). The combined bound is the pooled estimate of the D‑coefficient limit with its [deferred] CL.

**Why this priority**: This directly addresses the research question by providing a statistically sound, uncertainty‑aware aggregate bound rather than a naïve minimum, thereby preserving information from all studies.

**Independent Test**: Can be fully tested by providing a mock dataset containing upper limits at various confidence levels and known variances, then verifying that the system (i) normalises the limits, (ii) computes Q and I², (iii) selects the appropriate model, and (iv) returns the pooled limit with correct confidence interval.

**Acceptance Scenarios**:

1. **Given** a set of upper‑limit values with varying confidence levels and reported uncertainties, **When** the combination module runs, **Then** the system normalises all limits to [deferred] CL, computes Q and I², selects a random‑effects model if p < 0.05, and returns the pooled limit with its [deferred] CL.
2. **Given** identical limits from different experiments, **When** the combination runs, **Then** the system returns that common value (the pooled estimate equals the individual limits) and records all source references.
3. **Given** a situation where heterogeneity is low (p ≥ 0.05), **When** the aggregation completes, **Then** the system uses a fixed‑effect model and flags the result as “low heterogeneity”.

---

### User Story 3 - Sensitivity Validation and Independent Benchmark Comparison (Priority: P3)

The system MUST calculate the sensitivity of the combined upper bound for each nucleus and compare it against independent external constraints (e.g., the most stringent neutron‑EDM limits, atomic‑EDM limits, and dedicated beta‑decay T‑violation measurements) to validate the result.

**Why this priority**: This ensures scientific rigor by benchmarking the meta‑analysis bound against independent, physics‑relevant constraints, avoiding circular validation.

**Independent Test**: Can be fully tested by running the validation module on a processed dataset and verifying that the system correctly fetches the external benchmark values and reports whether the combined bound is tighter, comparable, or looser.

**Acceptance Scenarios**:

1. **Given** the combined upper bound for a nucleus, **When** the sensitivity analysis runs, **Then** the system reports the bound’s confidence level (90 % CL) and the corresponding standard error.
2. **Given** the combined bound, **When** the validation step runs, **Then** the system cross‑references the result with the latest neutron‑EDM limit (e.g., nEDM Collaboration 2023) and the strongest atomic‑EDM limit, flagging if the new bound is looser.
3. **Given** the combined bound and external benchmarks, **When** the comparison runs, **Then** the system produces a table summarising the two values, the percentage improvement (if any), and a concise interpretation.

---

### User Story 4 - Robustness via Monte‑Carlo Permutation Testing (Priority: P4)

The system MUST generate Monte‑Carlo simulations of underlying polarization‑vs‑momentum distributions consistent with each published upper limit, then perform permutation testing by randomly shuffling polarization values across momentum bins (**5,000 permutations per simulated dataset**). The permutation p‑value is the fraction of permutations yielding a combined bound equal to or more stringent than the observed pooled estimate. This satisfies Constitution Principle VII.

**Why this priority**: Constitution Principle VII mandates permutation testing on raw polarization‑momentum data; because raw data are unavailable, we approximate the required structure via simulation, preserving methodological integrity.

**Independent Test**: Can be fully tested by providing a synthetic set of simulated raw datasets (with known underlying D‑coefficient), running the permutation module, and confirming that the empirical p‑value matches the expected distribution.

**Acceptance Scenarios**:

1. **Given** a set of simulated raw datasets derived from the published limits, **When** the permutation test runs, **Then** the system generates [deferred] random shuffles per dataset, recomputes the pooled bound for each, and calculates the empirical p‑value.
2. **Given** a p‑value < 0.05, **When** the robustness check completes, **Then** the system flags the result as “potentially sensitive to underlying polarization‑momentum structure” and records the p‑value in the provenance log.
3. **Given** a p‑value ≥ 0.05, **When** the robustness check completes, **Then** the system records the result as “robust under permutation” and proceeds without flagging.

---

### Edge Cases

- **Data source unavailable**: If a literature repository (e.g., INSPIRE) is temporarily unavailable or returns an HTTP “not found” error for a specific query, the system retries a limited number of times with exponential backoff (increasing delays) before logging the failure and proceeding with the remaining nuclei.
- **Limit reported as a range**: When an upper limit is given as a range, the system uses the most conservative (lowest) endpoint for aggregation and propagates the range width as an additional systematic uncertainty. If the range width exceeds a substantial proportion of the nominal limit, the dataset is excluded and flagged.
- **Numerical precision extremes**: If a permutation p‑value evaluates to exactly **0** or **1** due to floating‑point limits, The system clamps the value to a safe interval bounded away from zero and the upper limit, logs a warning, and marks the result with the flag “inconclusive due to numerical precision”.
- **Binned aggregate without per‑study uncertainty**: Datasets lacking per‑study uncertainties are flagged as “invalid for meta‑analysis” and excluded, preventing the generation of a spurious pooled estimate.

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve *published* one‑sided upper limits on the T‑violation D‑coefficient, their confidence levels, reported uncertainties, and experimental conditions for specified nuclei (e.g., $^{6}$He, $^{19}$Ne) from dedicated beta‑decay T‑violation literature repositories (INSPIRE‑HEP, arXiv, experiment‑specific reports). The system MUST NOT attempt to derive D‑coefficients from raw momentum spectra or polarization asymmetries that are unavailable in the public archival format. (See US-1)
- **FR-002**: System MUST convert all retrieved limits to a common confidence level (90 % CL) using the standard normal approximation, then combine them per nucleus with a DerSimonian‑Laird random‑effects meta‑analysis (inverse‑variance weighting). (See US-2)
- **FR-003**: System MUST calculate and record the confidence‑level conversion factors and individual variances applied to each upper limit, preserving full provenance for reproducibility. (See US-2)
- **FR-004**: System MUST validate the feasibility of the combination by checking for the presence of upper‑limit entries with associated uncertainties; if a nucleus lacks such entries, the system MUST flag the dataset as "insufficient data" and exclude it from further analysis. (See US-1)
- **FR-005**: System MUST report the pooled upper bound together with its [deferred] CL and a clear statement that the result represents an *associational limit* derived from archival data, not a direct detection. (See US-2)
- **FR-006**: System MUST cross‑reference the pooled bound with independent external constraints (latest neutron‑EDM limits, atomic‑EDM limits, and dedicated beta‑decay T‑violation measurements) and flag any result that is looser than the most stringent external benchmark. (See US-3)
- **FR-007**: System MUST perform a leave‑one‑out influence analysis on the random‑effects pooled estimate; a study is flagged as “high influence” if its removal changes the pooled limit by more than **[deferred]** in relative terms (i.e., absolute change > 0.05 × pooled limit). (See US-4)
- **FR-008**: System MUST log the source URL, extraction timestamp, confidence‑level conversion factor, and variance for every data point used in the final calculation. Numerical‑stability adjustments (e.g., p‑value clamping) are permitted only if logged and flagged as "inconclusive" when they affect the final conclusion. (See US-2)
- **FR-009**: System MUST generate Monte‑Carlo simulations of raw polarization‑vs‑momentum data consistent with each published limit, then perform permutation testing by shuffling polarization values across momentum bins (**5,000 permutations per simulated dataset**). The empirical p‑value is reported and logged. (See US-4, satisfies Constitution Principle VII)
- **FR-010**: System MUST assess heterogeneity among the retrieved limits using Cochran’s Q and I² statistics; if the heterogeneity p‑value is **< 0.05**, the system MUST adopt a random‑effects model (DerSimonian‑Laird) and report Q, I², and the heterogeneity p‑value. (See US-2)
- **FR-011**: System MUST NOT rely on a deterministic minimum‑limit rule; all aggregation must follow the statistical combination described in FR‑002. (See US-2)
- **FR-012**: System MUST produce output artifacts that conform to all contract schemas in the `contracts/` directory (d_measurement.schema.yaml, dataset.schema.yaml, fusion_result.schema.yaml, meta_analysis_result.schema.yaml, output.schema.yaml, raw_observable.schema.yaml) and validate them during the plan execution. (See US-4)

### Key Entities

- **Nucleus**: Represents a specific atomic nucleus (e.g., $^{6}$He) with attributes: `name`, `mass_number`, `experimental_conditions`.
- **PublishedUpperLimit**: Represents a published upper‑limit measurement, with attributes: `limit_value`, `confidence_level`, `uncertainty`, `source_experiment`, `reference_id`, `publication_year`, `source_url`, `extraction_timestamp`, `conversion_factor`.
- **AggregationResult**: Represents the statistical output of the meta‑analysis, with attributes: `nucleus_id`, `pooled_limit`, `pooled_confidence_level`, `heterogeneity_Q`, `heterogeneity_I2`, `heterogeneity_p`, `permutation_p_value`, `high_influence_flags`, `model_type` (e.g., "random‑effects"), `validation_status`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The pooled upper bound on $|D|$ for each nucleus is measured against the independent neutron‑EDM, atomic‑EDM, and dedicated beta‑decay T‑violation limits (e.g., nEDM Collaboration 2023). The system reports whether the bound is tighter, equal, or looser, and flags any looser result. (See US-3)
- **SC-002**: The permutation p‑value from FR‑009 is measured against the significance threshold **α = 0.05**. If p < 0.05, the system flags the result as “potentially sensitive to underlying polarization‑momentum structure”. (See US-4)
- **SC-003**: The leave‑one‑out influence metric from FR‑007 is measured as the relative percent change in the pooled limit. Experiments causing **> 5 %** change are flagged as “high influence”. (See US-4)
- **SC-004**: The data retrieval coverage is measured against the total number of requested nuclei in the target list {6He, 19Ne}, requiring retrieval of all available upper limits (flagging those where data is missing). (See US-1)
- **SC-005**: The provenance log maps every result to a specific literature reference ID and source URL, ensuring no simulated or hard‑coded values are used. (See US-2)
- **SC-006**: Heterogeneity assessment (FR‑010) yields a Q statistic, I² value, and heterogeneity p‑value; if **p < 0.05**, the system must have used a random‑effects model and report this decision. (See US-2)
- **SC-007**: Monte‑Carlo simulation convergence is verified by confirming that the standard error of the mean of pooled limits falls within an acceptable tolerance relative to the pooled limit across a sufficiently large set of permutations. (See US-4)

## Assumptions

- Dedicated beta‑decay T‑violation literature repositories (INSPIRE‑HEP, arXiv, experiment‑specific reports) are publicly accessible for the duration of the analysis, and the data format remains stable.
- The archival upper limits include reported uncertainties and confidence levels sufficient for inverse‑variance weighting.
- Reported upper limits are approximately independent; any residual common systematic bias is accounted for by the random‑effects variance component in the meta‑analysis.
- The Standard Model prediction for the T‑violation D‑coefficient is effectively zero, serving as the null hypothesis baseline.
- If no upper limit is reported for a nucleus in the literature, the aggregation method is invalid for that dataset, and the system will correctly identify and flag this limitation.
- The aggregation approach (random‑effects meta‑analysis) is computationally feasible within the allocated runtime for the expected dataset size (≤ 50 studies per nucleus).
- Monte‑Carlo simulations of polarization‑vs‑momentum data can be generated under reasonable physics‑motivated models consistent with the published limits; these simulations are used solely for permutation testing required by Constitution Principle VII.
- All numerical values used in the final analysis are strictly derived from the cited literature sources; no synthetic data, random sampling from theoretical distributions, or hard‑coded constants are used to generate the final pooled bounds, except for the controlled Monte‑Carlo simulations required for the permutation test, which are explicitly logged.
