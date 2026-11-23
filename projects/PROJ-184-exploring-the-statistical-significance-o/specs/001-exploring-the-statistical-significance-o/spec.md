# Feature Specification: Exploring the Statistical Significance of Fine‑Structure Constant Variations  

**Feature Branch**: `001-exploring-the-statistical-significance-o`  
**Created**: 2026-10-22  
**Status**: Draft  
**Input**: User description: “Exploring the Statistical Significance of Fine‑Structure Constant Variations”  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Reproducible Data Ingestion and Pre‑processing (Priority: P1)  

As a researcher, I want to automatically download publicly available VLT/UVES quasar absorption‑line spectra and extract metal‑absorption line lists with measured wavelengths, so that I obtain a clean, standardized dataset ready for statistical analysis without manual wrangling.  

**Why this priority**: Reliable ingestion is the prerequisite for any downstream inference; without it the scientific question cannot be addressed.  

**Independent Test**: Run the ingestion script on a curated test set of three public spectra and verify that the resulting CSV contains at least 95 % of the catalogued strong lines (Fe II, Mg II) with wavelengths within 0.05 Å of the reference values.  

**Acceptance Scenarios**  

1. **Given** a list of quasar IDs, **When** the pipeline executes, **Then** it downloads the FITS files, extracts the line list, and writes a CSV that meets the [deferred] completeness and 0.05 Å tolerance criteria.
2. **Given** a corrupted FITS file, **When** the pipeline processes it, **Then** it logs an error, skips the file, and continues without terminating the whole run.  

---

### User Story 2 – Hierarchical Bayesian Inference for Δα/α (Priority: P2)  

As a physicist, I want to run a hierarchical Bayesian model that estimates the fractional change Δα/α for each absorber while explicitly modelling known systematic effects, so that I obtain robust posterior distributions that reflect all sources of uncertainty.  

**Why this priority**: This analysis directly yields the scientific estimates needed to answer the research question.  

**Independent Test**: Apply the PyMC model to 100 simulated datasets (each with known Δα/α and injected systematics). Verify that ≥ 95 % of the 95 % credible intervals contain the true injected value.  

**Acceptance Scenarios**  

1. **Given** a simulated dataset of 50 absorbers with injected systematics, **When** the model runs (4 chains, 2 000 warm‑up, 4 000 draws), **Then** the posterior mean for each absorber’s Δα/α lies within 0.1 σ of the true value for ≥ 90 % of absorbers.  
2. **Given** a null‑variation simulation (true Δα/α = 0), **When** the model runs, **Then** the global‑trend 95 % credible interval includes zero in ≥ 95 % of 100 repetitions (coverage test).  

---

### User Story 3 – Model Comparison and Spatial/Temporal Trend Validation (Priority: P3)  

As a researcher, I want to compute Bayes factors for competing global hypotheses (constant α, linear redshift trend, dipole spatial pattern) and correlate Δα/α estimates with an external large‑scale‑structure field, so that I can quantify the evidence for or against variation.  

**Why this priority**: Quantitative model comparison determines whether the data support any variation beyond noise.  

**Independent Test**: Run the comparison on synthetic datasets where the true underlying model is known (null vs. dipole). Verify that the correct model obtains a Bayes factor > 5 (strong evidence) in ≥ 85 % of trials.  

**Acceptance Scenarios**  

1. **Given** a synthetic dipole dataset, **When** Bayes factors are computed, **Then** the dipole model is favored with ln(BF) > 5 in at least 85 % of trials.  
2. **Given** real‑data posterior Δα/α estimates and sky coordinates, **When** a dipole fit is performed, **Then** the amplitude and direction are reported with 95 % credible intervals.  

---

### User Story 4 – Provenance‑Enforced Separation of Validation from Scientific Results (Priority: P2)  

As a reviewer, I need assurance that every numeric result in the final research report originates from real data runs and that synthetic‑data validation outputs are kept strictly separate, so that the scientific conclusions are based solely on observed measurements.  

**Why this priority**: Prior feedback highlighted the risk of inadvertent inclusion of fabricated or placeholder numbers; explicit provenance enforcement eliminates this risk.  

**Independent Test**: Inspect the generated report and run the automated provenance audit. The audit must confirm that every headline numeric value maps to an entry in the provenance manifest derived from real data; any reference to a validation‑only artifact causes the audit to fail.  

**Acceptance Scenarios**  

1. **Given** the final report, **When** the provenance audit is executed, **Then** it finds a matching manifest entry for every reported Δα/α estimate, trend parameter, dipole amplitude, Bayes factor, and Spearman statistic.  
2. **Given** the validation suite outputs, **When** the report‑generation step assembles the manuscript, **Then** those outputs appear only under a section titled “Method Validation (synthetic data)” and are not cited in the conclusions.  

### Edge Cases  

- ESO archive temporarily unavailable or returns HTTP 429 rate‑limit responses.  
- Spectra contain overlapping absorption features from multiple redshifts.  
- NIST database lacks laboratory wavelengths for a detected transition.  
- NUTS sampler fails to converge (R̂ > 1.01) for a subset of parameters.  
- An outlier Δα/α estimate exceeds 5 σ from the ensemble mean.  

## Requirements *(mandatory)*  

### Functional Requirements  

- **FR-001**: System MUST download UVES quasar spectra from the ESO Science Archive and record observation metadata (redshift, exposure time, instrument setup) (See US‑1).  
- **FR-002**: System MUST identify and extract wavelengths for at least five metal species (Fe II, Mg II, Si IV, C IV, Al III) using `specutils`, outputting a standardized CSV (See US‑1).  
- **FR-003**: System MUST implement a hierarchical Bayesian model in PyMC v5 with Level 1 (per‑absorber Δα/α) and Level 2 (global trend/dipole) structures, incorporating nuisance parameters for wavelength‑calibration drift, intra‑order distortion, and continuum placement (See US‑2).  
- **FR-004**: If per‑spectrum calibration data are unavailable, the system MUST model calibration systematics with a Half‑Cauchy prior (scale = 0.1 Å) as a mandatory fallback (See US‑2).  
- **FR-005**: System MUST compute Bayes factors between the constant‑α, linear‑trend, and dipole models using bridge sampling; ln(BF) > 3 denotes moderate evidence, ln(BF) > 5 denotes strong evidence (See US‑3).  
- **FR-006**: System MUST fit the spatial dipole model Δα/α = A cos θ + B, reporting amplitude A and direction with 95 % credible intervals (See US‑3).  
- **FR-007**: System MUST run NUTS sampling with **≥ 4 chains**, 2 000 warm‑up steps, and 4 000 posterior draws per chain; convergence is verified via R̂ < 1.01 and reported in the log (See US‑2).  
- **FR-008**: System MUST generate corner plots and summary tables for all posterior parameters using `arviz` (See US‑3).  
- **FR-009**: System MUST perform a Spearman rank correlation between Δα/α estimates and the SDSS DR12 galaxy‑density field, reporting the coefficient and p‑value (See US‑3).  
- **FR-010**: System MUST enforce that every final research result is derived from real data ingestion (FR‑001) and model execution; synthetic data are used only within a clearly labeled validation suite (See US‑4).  
- **FR-011**: System MUST produce a provenance manifest for each production run, recording ESO program ID, input FITS checksums, NIST reference version, absorber count, and sampler configuration; every headline numeric in the final report must be traceable to this manifest (See US‑4).  
- **FR-012**: System MUST write all validation‑suite artifacts to a dedicated `validation/` directory and ensure the manuscript places these results only under a “Method Validation (synthetic data)” section; an automated check must fail the build if any validation‑only artifact is cited in the conclusions (See US‑4).  
- **FR-013**: System MUST restrict random‑number generation to (a) MCMC sampling over real data and (b) the quarantined validation suite; no other code path may generate synthetic measurements for the scientific conclusions (See US‑4).  
- **FR-014**: System MUST implement a retry policy for ESO archive requests: up to **3** attempts with exponential back‑off (initial 5 s, max 60 s); after exhausting retries, the failure is logged and processing continues with remaining targets (See US‑1).  
- **FR-015**: System MUST detect overlapping lines (centroid separation < 0.1 Å) and attempt de‑blending via multi‑component Gaussian fitting; if de‑blending fails, the line is flagged for manual review (See US‑1).  
- **FR-016**: System MUST handle missing laboratory frequencies by excluding the transition, logging a warning, and proceeding with remaining lines (See US‑1).  
- **FR-017**: System MUST identify Δα/α outliers > 5 σ from the posterior mean and either down‑weight them using a Student‑t prior (ν = 4) or list them in an “Outliers” section of the report (See US‑2).  
- **FR-018**: If NUTS fails to converge (R̂ > 1.01), the system first increases posterior draws to **8 000** per chain; if convergence still fails, the pipeline aborts with an error and records the offending parameters (See US‑2).  
- **FR-019**: System MUST compute completeness weights based on quasar magnitude and redshift distributions versus the survey selection function, and incorporate these weights into the hierarchical model as a scaling factor (See US‑2).  
- **FR-020**: System MUST guarantee that **no hard‑coded numeric values** appear in the final research report; every numeric result must be generated by the pipeline and linked to the provenance manifest (See US‑4).  
- **FR-021**: Synthetic validation datasets MUST be generated by an independent forward‑modeling process that uses known true parameters and a noise model distinct from the inference priors, ensuring that validation is not circular (See US‑2).  

### Key Entities  

- **Absorber** – a quasar absorption system with attributes: redshift, measured line wavelengths, signal‑to‑noise ratios, and systematic‑error estimates.  
- **Δα/α Estimate** – posterior distribution for the fractional change in the fine‑structure constant for an absorber (mean, std, 95 % credible interval).  
- **Global Trend Model** – encapsulates the redshift‑dependent and dipole hypotheses with parameters: slope, dipole amplitude, dipole direction, and intrinsic scatter.  
- **Provenance Manifest** – machine‑readable record linking each reported numeric result to its real‑data inputs (ESO program ID, FITS checksums, NIST version, absorber count, sampler configuration).  

## Success Criteria *(mandatory)*  

### Measurable Outcomes  

- **SC-001**: On 100 simulated datasets with known Δα/α, the hierarchical model’s 95 % credible intervals contain the true value in ≥ 95 % of cases (coverage). *(See US‑2)*  
- **SC-002**: Model‑comparison on synthetic data correctly identifies the true underlying model (null, trend, or dipole) in ≥ 90 % of trials (Bayes factor criteria). *(See US‑3)*  
- **SC-003**: Full analysis on a benchmark set of 20 absorbers completes within 4 hours and ≤ 5 GB RAM on the GitHub Actions free‑tier runner; production runs with ≥ 30 absorbers complete within 6 hours and ≤ 7 GB RAM. *(See US‑2)*  
- **SC-004**: Incorporating systematic‑error nuisance parameters reduces posterior‑mean bias of Δα/α by ≥ 20 % and improves coverage probability by ≥ 5 percentage points relative to a model that omits systematics. *(See US‑2)*  
- **SC-005**: Sensitivity analysis over three prior‑width settings (nominal, ±20 %) yields posterior‑mean changes < 0.05 σ for all key parameters, demonstrating robustness. *(See US‑3)*  
- **SC-006**: Provenance audit of the final report finds zero violations: every headline numeric quantity maps to a real‑data manifest entry, and no validation‑only artifact is cited. *(See US‑4)*  
- **SC-007**: Data‑ingestion completeness reaches ≥ 95 % of the target quasar list; missing files are logged and accounted for in the manifest. *(See US‑1)*  
- **SC-008**: Retry/back‑off handling succeeds within the 3‑attempt limit for ≥ 90 % of transient ESO archive failures; remaining failures are recorded without halting the pipeline. *(See FR‑014)*  
- **SC-009**: Applying completeness weights changes the weighted global Δα/α estimate by ≤ 0.02 relative to the unweighted estimate, confirming that bias correction has a measurable but modest impact. *(See FR‑019)*  
- **SC-010**: Automated static analysis confirms that no hard‑coded numeric literals appear in the conclusions section; any violation causes the pipeline to fail. *(See FR‑020)*  

## Assumptions  

- The ESO Science Archive provides programmatic access to UVES Large Programme spectra via an API key without manual authentication steps.  
- Laboratory transition frequencies from the NIST Atomic Spectra Database are accurate to ≤ 0.001 cm⁻¹ for all metal transitions used.  
- The GitHub Actions free‑tier runner offers sufficient disk space (~14 GB) to store all downloaded spectra, intermediate files, and model outputs.  
- PyMC v5, `arviz`, `specutils`, and `astropy` are installable via `pip` on the runner’s Python 3.11 environment without requiring compiled extensions.  
- If per‑observation calibration data (ThAr or laser‑comb) are missing, the fallback Half‑Cauchy prior (scale = 0.1 Å) adequately captures plausible calibration uncertainty.  
- The SDSS DR12 galaxy‑density catalog is publicly accessible and provides coverage for the majority of quasar sightlines; it is used only for the ancillary Spearman correlation.  
- The available quasar sample contains at least 30 absorbers with S/N ≥ 5, ensuring meaningful hierarchical inference.  
- The NUTS sampler will converge (R̂ < 1.01) under the specified configuration on the runner; if not, the remedial procedure in FR‑018 will be invoked.  
- The 100‑seed validation suite is executed separately from the production time budget; the runner’s resources are sufficient to complete it within the allotted CI window.  
- Findings are reported as **associational** statements about Δα/α; a null result (credible interval including zero) is treated as a successful, publishable outcome.  
- All numeric results in the final manuscript are generated by the pipeline and have corresponding provenance entries; no fabricated or placeholder numbers are permitted.  

### Paper‑stage handoff  

The deliverables of this feature are:  

1. A provenance‑audited research report containing posterior summaries, Bayes factors, dipole fit results, sensitivity analyses, validation‑suite outcomes, tables, and figures.  
2. All code, environment specifications, and data‑access scripts committed to the repository.  

Manuscript formatting, PDF compilation, and journal submission are owned by the downstream paper pipeline and are **not** required for completion of this research stage.
