# Feature Specification: Exploring the Statistical Significance of Fine‑Structure Constant Variations

**Feature Branch**: `001-fine-structure-constant-variations`
**Created**: 2023-10-27
**Status**: Draft
**Input**: User description: "Exploring the Statistical Significance of Fine‑Structure Constant Variations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reproducible Data Ingestion and Preprocessing Pipeline (Priority: P1)

As a researcher, I want to automatically download publicly available quasar absorption-line spectra (e.g., from ESO UVES) and extract metal-absorption line lists (Fe II, Mg II, Si IV) with their measured wavelengths, so that I have a clean, standardized dataset ready for statistical analysis without manual data wrangling.

**Why this priority**: Without reliable data ingestion and line extraction, no subsequent statistical modeling or hypothesis testing is possible. This is the foundational step that enables the entire research workflow.

**Independent Test**: Can be fully tested by running the data pipeline script against a small subset of public spectra and verifying that the output CSV contains correctly identified absorption lines with wavelengths within expected error margins compared to manual inspection.

**Acceptance Scenarios**:

1. **Given** a list of quasar IDs from the ESO archive, **When** the pipeline executes, **Then** it downloads the corresponding FITS files and extracts at least 95% of known strong absorption lines (Fe II, Mg II) with wavelengths matching catalog values within 0.05 Å.
2. **Given** a corrupted or incomplete FITS file, **When** the pipeline attempts processing, **Then** it logs the error, skips the file, and continues processing remaining files without crashing.
3. **Given** a spectrum with low signal-to-noise ratio, **When** the pipeline runs, **Then** it flags lines with S/N < 5 for potential exclusion in downstream analysis.

---

### User Story 2 - Hierarchical Bayesian Inference for Δα/α Estimation (Priority: P2)

As a physicist, I want to run a hierarchical Bayesian model that estimates the fractional change in the fine-structure constant (Δα/α) for each absorber while accounting for systematic errors (wavelength calibration drift, intra-order distortions) as nuisance parameters, so that I obtain robust posterior distributions for potential variations.

**Why this priority**: This is the core scientific analysis that directly addresses the research question. It transforms raw measurements into statistically meaningful estimates of α variation while properly propagating uncertainties.

**Independent Test**: Can be fully tested by running the PyMC model on simulated data with known Δα/α values and systematic errors, then verifying that the posterior distributions correctly recover the injected parameters within 95% credible intervals. To validate frequentist coverage, the test MUST run 100 independent seeds with 4 chains each (2000 warmup, 4000 draws) on a validation subset (≤10 absorbers) and confirm that the 95% CI contains the true value in ≥95% of the 100 runs.

**Acceptance Scenarios**:

1. **Given** a dataset of 50 absorbers with injected systematic errors, **When** the hierarchical model runs with 4 chains (2000 warmup, 4000 draws each), **Then** the posterior mean for Δα/α is within 0.1σ of the true injected value for at least 90% of absorbers.
2. **Given** a null hypothesis scenario (no true variation), **When** the model is applied, **Then** the 95% credible interval for the global trend parameter includes zero in at least 95% of 100 repeated simulations (verified via the 100-seed coverage test).
3. **Given** varying prior widths on systematic error parameters, **When** the model is re-run, **Then** the posterior estimates for Δα/α remain stable (change < 0.05σ) across the sensitivity sweep.

---

### User Story 3 - Model Comparison and Spatial/Temporal Trend Validation (Priority: P3)

As a researcher, I want to compute Bayes factors comparing null models (no variation) against alternative models (spatial dipole, temporal trend) and correlate Δα/α estimates with large-scale structure data, so that I can quantify the evidence for new physics and assess potential spatial alignments.

**Why this priority**: This provides the final interpretive layer that determines whether observed variations are statistically significant and physically meaningful, completing the scientific inquiry.

**Independent Test**: Can be fully tested by running the model comparison on synthetic datasets with known ground truth (null vs. dipole) and verifying that Bayes factors correctly favor the true model in >90% of cases.

**Acceptance Scenarios**:

1. **Given** a dataset where a true dipole pattern exists, **When** Bayes factors are computed between null and dipole models, **Then** the dipole model is favored with ln(BF) > 5 in at least 85% of simulation trials.
2. **Given** Δα/α posterior estimates and celestial coordinates (RA, Dec), **When** a spatial dipole fit is computed, **Then** the dipole amplitude and direction are reported with 95% credible intervals.
3. **Given** a sensitivity analysis where prior widths are varied by ±20%, **When** model comparison is re-run, **Then** the qualitative conclusion (null vs. alternative favored) remains unchanged in at least 90% of cases.

---

### User Story 4 - Separation of Method Validation from Research Findings (Priority: P2)

As a reviewer of the research output, I want every reported research result (posterior Δα/α estimates, trend/dipole parameters, Bayes factors, Spearman correlations, summary tables, and figures) to be derived exclusively from the real observed spectra downloaded in US-1, with all simulation-based validation runs clearly labeled and quarantined into a distinct validation section, so that no simulated, synthetic, placeholder, or hardcoded number can be mistaken for — or contaminate — a genuine research finding.

**Why this priority**: A prior review cycle flagged the research output for self-declared fabricated metrics. The trustworthiness of the entire study depends on an auditable separation between (a) methodological validation on synthetic data with known ground truth (US-2, US-3 validation tests) and (b) the actual scientific conclusions drawn from real ESO/NIST/SDSS data. This story makes that separation a first-class, testable deliverable.

**Independent Test**: Can be fully tested by inspecting the provenance of every number in the final research report: each result must trace to a recorded run on real downloaded data (with the ESO program ID, e.g. 094.C-0462, and input file checksums logged), and every synthetic-data artifact must appear only under an explicitly labeled "Method Validation (synthetic data)" section with no cross-references from the conclusions.

**Acceptance Scenarios**:

1. **Given** the final research report, **When** any headline quantity (e.g., global Δα/α posterior mean, dipole amplitude, Bayes factor) is inspected, **Then** its provenance record identifies the real-data run (input FITS checksums, absorber count, sampler configuration) that produced it, and it is never sourced from a synthetic-data or placeholder run.
2. **Given** the validation suite (100-seed coverage test, ground-truth model-comparison trials), **When** its outputs are written, **Then** they are stored under a separate, explicitly labeled validation directory/section and are never cited in the research conclusions as measurements of the physical world.
3. **Given** the analysis codebase, **When** the production pipeline executes, **Then** it contains no code path that injects simulated wavelengths, hardcoded Δα/α values, or `random.*`-generated measurements into the real-data results; any random number generation is confined to (a) MCMC sampling of the posterior over real data and (b) the quarantined validation suite.

---

### Edge Cases

- What happens when the ESO archive is temporarily unavailable or returns rate-limited responses?
- How does the system handle spectra with overlapping absorption lines from multiple redshifts?
- What occurs if the NIST database lacks laboratory reference frequencies for a detected transition?
- How are outliers in Δα/α estimates (e.g., >5σ from mean) handled in the hierarchical model?
- What happens if the NUTS sampler fails to converge (R-hat > 1.01) for certain chains?
- What happens if a validation-suite artifact (synthetic-data output) is accidentally referenced in the research conclusions? The report generation step MUST fail loudly (a provenance check that rejects any conclusion citing a validation-only artifact) rather than silently publish the contamination.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download UVES quasar spectra from the ESO Science Archive and parse FITS headers to extract observation metadata (redshift, exposure time, instrument setup) (See US-1)
- **FR-002**: System MUST identify and extract absorption line wavelengths for at least 5 common metal species (Fe II, Mg II, Si IV, C IV, Al III) using `specutils` with automated line-list matching (See US-1)
- **FR-003**: System MUST implement a hierarchical Bayesian model in PyMC v5 with Level 1 (individual absorbers) and Level 2 (global trend/dipole) structure, including nuisance parameters for systematic errors (See US-2)
- **FR-004**: System MUST derive wavelength-calibration drift and intra-order distortion parameters from per-spectrum calibration residuals (ThAr lamp lines or laser frequency comb data) found in FITS headers or linked logs. If such data is unavailable, the system MUST model these as a hyper-parameter with a Half-Cauchy prior (scale=0.1 Å) as a mandatory fallback, prioritizing informative priors based on the engineering study (2023) if data is available (See US-2)
- **FR-005**: System MUST compute Bayes factors between null and alternative models using bridge sampling, with ln(BF) > 3 considered moderate evidence and ln(BF) > 5 strong evidence (See US-3)
- **FR-006**: System MUST fit a spatial dipole model (Δα/α = A cos(θ) + B) to the celestial coordinates (RA, Dec) of the absorbers. "Sightline groups" are defined as spatial clusters of absorbers within 10 degrees angular separation or redshift bins of Δz < 0.1, used solely as input for the dipole model. The system MUST report the dipole amplitude and direction with 95% credible intervals (See US-3)
- **FR-007**: System MUST run NUTS sampling with a minimum of 4 chains, 2000 warmup steps, and 4000 posterior draws per chain for production runs. The system MUST use the `arviz.rhat` function with a convergence threshold of R-hat < 1.01 to verify convergence, and report the maximum R-hat value in the output log (See US-2)
- **FR-008**: System MUST generate corner plots and summary tables using `arviz` showing posterior distributions for Δα/α, trend slope, and dipole amplitude (See US-3)
- **FR-009**: System MUST perform a Spearman rank test to correlate Δα/α estimates with galaxy density fields from the SDSS DR catalog to assess large-scale structure alignment (See US-3)
- **FR-010**: System MUST derive all final research results from actual data ingestion (FR-001) and real model execution. The system MUST NOT use simulated, synthetic, placeholder, or hardcoded values for final research conclusions; simulation is used strictly for method validation (US-2, US-3 validation tests) only (See US-2, US-3)
- **FR-011**: System MUST maintain a provenance manifest for every production run, recording: the ESO program ID (e.g., 094.C-0462), checksums of all input FITS files, the NIST reference-line version used, the absorber count, and the sampler configuration. Every headline quantity in the research report MUST be traceable to an entry in this manifest (See US-4)
- **FR-012**: System MUST write all synthetic-data validation outputs (100-seed coverage runs, ground-truth model-comparison trials) to a dedicated, explicitly labeled validation directory, and the final report MUST place these results only under a section titled "Method Validation (synthetic data)". The report-generation step MUST include an automated provenance check that fails the build if any research conclusion cites a validation-only artifact or any value lacking a real-data provenance entry (See US-4)
- **FR-013**: System MUST confine random number generation to two audited uses: (a) MCMC posterior sampling over the real observed data, and (b) the quarantined validation suite. The production analysis path MUST contain no code branch that generates simulated wavelengths, synthetic Δα/α measurements, or placeholder metric values feeding into research results; this MUST be verified by an automated check (e.g., static scan of the production pipeline for synthetic-data constructors plus a runtime provenance assertion) that runs as part of the pipeline (See US-4)

### Key Entities *(include if feature involves data)*

- **Absorber**: Represents a single quasar absorption system with attributes: redshift, measured wavelengths for each transition, signal-to-noise ratio, and associated systematic error estimates.
- **Δα/α Estimate**: The fractional change in the fine-structure constant for an absorber, represented as a posterior distribution with mean, standard deviation, and 95% credible interval.
- **Global Trend Model**: Represents the redshift-dependent variation hypothesis with parameters: slope (temporal trend), dipole amplitude, and intrinsic scatter.
- **Provenance Manifest**: A machine-readable record (per production run) linking each reported research result to its real-data inputs: ESO program ID, input FITS checksums, NIST reference version, absorber count, and sampler configuration. Validation-suite artifacts are excluded from this manifest and tagged as synthetic.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Posterior recovery accuracy is measured against simulated datasets with known ground-truth Δα/α values, where 95% credible intervals should contain the true value in ≥95% of 100 independent runs (See US-2)
- **SC-002**: Model comparison performance is measured against synthetic data with known null/alternative ground truth, where Bayes factors should correctly identify the true model in ≥90% of trials (See US-3)
- **SC-003**: Computational efficiency is measured against the GitHub Actions free-tier constraint (a limited number of CPU cores, 7 GB RAM, 6-hour limit). For the benchmark dataset (20 simulated absorbers), the full analysis (4 chains, 2000 warmup, 4000 draws) MUST complete within 4 hours with ≤5 GB memory usage. For production runs (≥30 absorbers), the system MUST complete successfully within 6 hours and using ≤7 GB RAM (See US-2)
- **SC-004**: Systematic error propagation is measured by comparing the posterior mean bias and coverage probability of Δα/α in the 'with-systematics' model against the 'without-systematics' model. Success is defined as the 'with-systematics' model showing reduced bias and improved coverage probability (See US-2)
- **SC-005**: Sensitivity analysis coverage is measured by the number of prior-width variations tested (minimum 3 values: nominal, ±20%), with stable conclusions across all variations indicating robustness (See US-3)
- **SC-006**: Research-result authenticity is measured by a full provenance audit of the final report: [deferred] of headline quantities (posterior Δα/α estimates, trend/dipole parameters, Bayes factors, Spearman statistics, and all figures/tables in the conclusions) MUST resolve to a provenance-manifest entry from a real-data run, and [deferred] may originate from the synthetic-data validation suite. The automated provenance check (FR-012) MUST pass on the delivered report (See US-4)

## Assumptions

- The ESO Science Archive provides programmatic access to UVES Large Programme spectra without requiring manual authentication beyond API key configuration.
- Laboratory transition frequencies from the NIST Atomic Spectra Database are accurate to within 0.001 cm⁻¹ for all relevant metal transitions (Fe II, Mg II, Si IV, etc.).
- The GitHub Actions free-tier runner has sufficient disk space to store downloaded spectra, intermediate data files, and model outputs without requiring external storage.
- PyMC v5 and related packages (arviz, specutils, astropy) are compatible with the Python version available on the GitHub Actions runner and can be installed via pip without compilation issues.
- Systematic errors in high-resolution spectroscopy are typically characterized per observation using calibration lamps (ThAr) or laser combs; if such data is unavailable, the system MUST use broad hyper-priors (Half-Cauchy scale=0.1 Å) as a mandatory fallback.
- The SDSS DR galaxy density catalog is publicly accessible and provides sufficient spatial coverage to correlate with the quasar sightlines in the analysis (for auxiliary checks, though the primary test is the dipole fit).
- The sample of available quasar spectra contains at least 30 absorbers with sufficient signal-to-noise ratio to enable meaningful hierarchical Bayesian inference.
- The NUTS sampler will converge (R-hat < 1.01) for all model parameters when run with the specified chain configuration (4 chains, 2000 warmup, 4000 draws) on the GitHub Actions hardware.
- The 100-seed validation suite (SC-001) is a methodological calibration of the estimator on synthetic data and is budgeted separately from the ≤6-hour production-run constraint; if the full 100-seed sweep threatens the runner time limit, it MAY be reduced to ≥50 seeds on a ≤10-absorber subset, with the reduction documented in the validation section — this affects only the validation suite, never the real-data research results.
- The findings of this study are associational/inferential statements about Δα/α in the observed absorber sample; a null result (95% credible interval including zero) is a valid, publishable scientific outcome and is treated as equally successful to a detection.

### Paper-stage handoff

The research deliverables of this feature are: the provenance-audited research report with posterior estimates, Bayes factors, sensitivity analyses, validation-suite results, summary tables, and figures. Manuscript formatting, LaTeX PDF compilation, and publication preparation are owned by the subsequent paper pipeline and are NOT completion criteria for this research stage.
