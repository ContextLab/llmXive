# Feature Specification: Transferability of DFT‑D3 Dispersion to Ionic Liquids

**Feature Branch**: `PROJ-735-Transferability-DFT-D3-IL`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Does the DFT‑D3 empirical dispersion correction, calibrated on neutral organic molecules, accurately predict ion‑pair interaction energies in prototypical ionic liquids?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Benchmark DFT‑D3 Interaction Energies (Priority: P1)

A computational chemist wants to run an end‑to‑end benchmark that computes DFT‑D3 interaction energies for a set of ionic‑liquid ion‑pair complexes and compares them to high‑level CCSD(T)/CBS reference values, in order to assess the raw transferability of the dispersion model.

**Why this priority**: This story delivers the core scientific evidence needed to answer the research question; without it no downstream analysis is possible.

**Independent Test**: The pipeline can be executed on a fresh GitHub Actions runner and will produce a CSV of raw DFT‑D3 energies, reference energies, and error metrics without any scaling or correlation steps.

**Acceptance Scenarios**:

1. **Given** the IL‑Benchmark dataset is available and contains reference interaction energies, **when** the workflow runs the psi4 single‑point calculations, **then** a CSV file `raw_energies.csv` is created containing (i) ion‑pair identifier, (ii) reference energy, (iii) DFT‑D3 total energy, (iv) D3 dispersion contribution, (v) signed error, (vi) `error_signed` column (total‑energy error), and (vii) `dispersion_only_error` column (difference between D3 term and any available reference dispersion component).  
2. **Given** the calculations complete successfully, **when** the error‑analysis script runs, **then** it reports MAE, RMSE, and mean signed error (MSE) and the values are recorded in `benchmark_report.md`.

---

### User Story 2 – Derive a Simple Scaling Correction (Priority: P2)

A researcher wants to obtain a single scalar that, when applied to the D3 dispersion term, reduces systematic bias across the benchmark set, thereby providing a pragmatic correction that can be used in future high‑throughput screens.

**Why this priority**: A calibrated scaling factor directly addresses the "bias correction" component of the expected results and makes the method usable beyond the benchmark.

**Independent Test**: Running the "scaling" stage on the CSV from US‑1 produces a single numeric factor and a re‑computed error summary on a held‑out test subset.

**Acceptance Scenarios**:

1. **Given** `raw_energies.csv` exists, **when** the dataset is split ([deferred] training, [deferred] held‑out test) and the linear‑fit script is executed on the training portion, **then** it returns a positive scaling factor `s` (constrained `s > 0`) that minimizes the mean absolute error of the corrected interaction energies on the training data, and writes `scaling_factor.txt`.
2. **Given** the scaling factor `s` is applied to the D3 term of the **test** subset, **when** the corrected energies are recomputed, **then** the MAE on the test set is reported, a 95 % bootstrap confidence interval for `s` (1 000 replicates) is provided, and a two‑sided p‑value (α = 0.05) testing the null hypothesis `s = 1.0` is reported. The null hypothesis is rejected if the CI excludes 1.0 **and** the p‑value < 0.05.

---

### User Story 3 – Exploratory Correlation of Dispersion Terms with Bulk Properties (Priority: P3)

An analyst wishes to test whether the magnitude of the (raw or scaled) D3 dispersion contribution is associated with experimentally measured bulk properties (density and viscosity) of the corresponding ionic liquids, thereby probing the practical relevance of any systematic error.

**Why this priority**: This exploratory analysis is justified because it evaluates whether the D3 dispersion term captures physicochemical trends relevant to bulk properties, providing a practical relevance check for the transferability assessment while remaining ancillary to the core research question.

**Independent Test**: Executing the correlation stage on the **held‑out test** corrected CSV produces Pearson and Spearman coefficients, bootstrap confidence intervals, and Bonferroni‑adjusted p‑values.

**Acceptance Scenarios**:

1. **Given** the corrected interaction‑energy CSV for the held‑out test subset and a CSV of experimental densities & viscosities (retrieved from the NIST IL Thermophysical Database via the endpoint ` No address associated with hostname)"))] or, if the API fails, the static file `data/experimental_bulk_properties.csv`), **when** the correlation script runs, **then** it outputs `correlation_report.md` containing (a) Pearson |R|, R², and p‑value for D3 term vs density, (b) Pearson |R|, R², and p‑value for interaction‑energy error vs viscosity, (c) 95 % bootstrap confidence intervals for each coefficient, and (d) Bonferroni‑adjusted p‑values evaluated against α = 0.05.  
2. **Given** the correlation results, **when** the Bonferroni correction is applied to the set of p‑values, **then** the adjusted p‑values are reported and any coefficient with an adjusted p‑value < 0.05 is flagged as statistically significant.

---

### Edge Cases

- **Missing reference energy**: If an ion‑pair entry lacks a CCSD(T)/CBS reference, the pipeline must log a warning, skip that entry, and continue without aborting.  
- **Psi4 calculation failure**: If a single‑point job fails (e.g., SCF convergence), the workflow retries up to **3** times; after the third failure the entry is recorded as "failed" and excluded from downstream analysis.  
- **Absent bulk‑property data**: If the NIST API does not return density or viscosity for a given ion pair, the correlation step excludes that pair and notes the omission in the final report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve the IL‑Benchmark interaction‑energy dataset (including CCSD(T)/CBS reference values and structural coordinates) from the Zenodo DOI ``. If the network request fails, the system MUST load the local fallback file `data/IL‑Benchmark‑local.zip` **only for development**; the final analysis MUST use the Zenodo data to satisfy Constitution Principle VI. (See US‑1)  
- **FR-002**: System MUST validate that each record contains **both** a reference interaction energy **and** a unique ion‑pair identifier; records missing either field MUST be flagged and omitted from analysis (See US‑1).  
- **FR-003**: System MUST perform a single‑point energy calculation for each ion pair using **psi4** with the B3LYP functional, the **def2‑TZVP** basis set, the D3 (Becke‑Johnson damping) dispersion correction, and the **Counterpoise correction** for Basis Set Superposition Error (BSSE), executing on **CPU only** (no GPU) (See US‑1).  
- **FR-004**: System MUST extract from psi4 output the total interaction energy and the separate D3 dispersion contribution, compute `error_signed = dft_total_energy – reference_energy`, compute `dispersion_only_error = d3_dispersion_energy – reference_dispersion` (if a reference dispersion component is available; otherwise set to NA), and store all fields in a structured CSV with columns `pair_id, reference_energy, dft_total_energy, d3_dispersion_energy, error_signed, dispersion_only_error` (See US‑1).  
- **FR-005**: System MUST compute error metrics (MAE, RMSE, mean signed error) between DFT‑D3 total energies and the CCSD(T)/CBS references (See US‑1).  
- **FR-006**: System MUST fit a linear scaling factor *s* (constrained *s > 0*) to the D3 dispersion term on the **training** subset to minimize the MAE of the corrected interaction energies (See US‑2).  
- **FR-007**: System MUST test the null hypothesis *s = 1.0* by (a) constructing a **95 % bootstrap confidence interval** on *s* using **1 000** replicates and (b) performing a two‑sided hypothesis test yielding a p‑value (α = 0.05). The null is rejected only if **both** the CI excludes 1.0 **and** p < 0.05 (See US‑2).  
- **FR-008**: System MUST retrieve experimental bulk‑property data (density, viscosity) for each ion pair from the NIST IL Thermophysical Database via the endpoint ` No address associated with hostname)"))]; if the API fails, the system MUST load the static CSV file `data/experimental_bulk_properties.csv` (See US‑3).  
- **FR-009**: System MUST compute Pearson and Spearman correlation coefficients between (a) **raw D3 term** and density, (b) **scaled D3 term** and density, (c) **interaction‑energy error** and viscosity, together with associated p‑values and **R²** (See US‑3).  
- **FR-010**: System MUST perform bootstrap resampling with **1 000** replicates to generate 95 % confidence intervals for each correlation coefficient (See US‑3).  
- **FR-011**: System MUST apply a Bonferroni correction to the family of correlation tests to control the family‑wise error rate (See US‑3).  
- **FR-012**: System MUST generate a reproducible, version‑controlled report package containing (i) raw energies CSV, (ii) scaling factor file, (iii) correlation report, and (iv) a `requirements.txt` that pins all Python dependencies (See US‑1‑US‑3).  
- **FR-014**: System MUST compute the **95 % confidence interval for the raw MAE** (from FR‑005) using **bootstrap resampling with 1 000 replicates** (See US‑1).  
- **FR-015**: System MUST perform an a priori power analysis to determine the minimum sample size required to detect a Pearson correlation of |r| ≥ 0.3 with 80 % power at α = 0.05, and must report the required N and the achieved power given the actual dataset size (See US‑3).  
- **FR-016**: System MUST propagate measurement uncertainties of the CCSD(T)/CBS reference energies (assumed ±0.5 kcal/mol) and of the experimental bulk‑property values (as provided in the NIST dataset) by sampling from normal distributions during bootstrap, thereby producing uncertainty‑aware confidence intervals (See FR‑014, FR‑010).  
- **FR-017**: System MUST split the benchmark dataset into an [deferred] training set and a [deferred] held‑out test set **before** fitting the scaling factor; the training set is used for FR‑006‑FR‑007, and the test set is used to report an out‑of‑sample MAE (See US‑2).  
- **FR-018**: System MUST perform residual diagnostics after applying the scaling factor: (a) compute per‑pair residuals, (b) generate a histogram, (c) conduct a Shapiro‑Wilk test for normality, and (d) assess heteroscedasticity using the Breusch‑Pagan test; results are included in `scaling_diagnostics.md` (See US‑2).  
- **FR-019**: System MUST ensure that any use of the local fallback `IL‑Benchmark‑local.zip` is restricted to development or CI‑failure scenarios; the production run must verify that the Zenodo dataset was successfully downloaded, otherwise abort with an error (ensuring compliance with Constitution Principle VI).  
- **FR-020**: System MUST perform the correlation analysis (FR‑009‑FR‑011) **exclusively on the held‑out test subset** obtained after fitting the scaling factor, to avoid optimistic bias from using training data (See US‑3).

### Key Entities

- **Ion‑Pair**: Represents a specific cation–anion combination; attributes include `pair_id`, `reference_energy (kcal/mol)`, `experimental_density (g/cm³)`, `experimental_viscosity (cP)`.  
- **CalculationResult**: Holds `pair_id`, `dft_total_energy`, `d3_dispersion_energy`, `error_signed`, `scaled_d3_energy`, `dispersion_only_error`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The system MUST report the Mean Absolute Error (MAE) of raw DFT‑D3 interaction energies versus CCSD(T)/CBS references, along with a **95 % confidence interval generated via bootstrap resampling (1 000 replicates)** that incorporates propagated measurement uncertainties (See US‑1).  
- **SC-002**: The system MUST report the fitted scaling factor *s*, its **95 % bootstrap confidence interval**, the p‑value from the hypothesis test, and the **out‑of‑sample MAE** on the held‑out test set (See US‑2).  
- **SC-003**: The system MUST report the Pearson and Spearman correlation coefficients, p‑values, **R² values**, and 95 % bootstrap confidence intervals for the correlations between D3 terms and bulk properties (See US‑3).  
- **SC-004**: The system MUST report the result of the power analysis (required N, achieved power) and confirm that the actual dataset meets or exceeds the required sample size (See US‑3).  
- **SC-005**: The entire workflow completes on a GitHub Actions free‑tier runner within **6 hours** and uses **≤ 7 GB RAM** (See US‑1).  
- **SC-006**: The correlation analysis reported in SC‑003 is performed **only on the held‑out test subset** after scaling factor determination (See US‑3).

## Assumptions

- The IL‑Benchmark dataset released on Zenodo (``) contains **≥ 100** ion‑pair complexes with high‑level CCSD(T)/CBS reference interaction energies and **structural coordinates (XYZ files)** required for calculations.  
- Experimental bulk‑property values (density, viscosity) are available for **≥ 80 %** of the ion pairs via the NIST IL Thermophysical Database; if the API is unavailable, the system falls back to the static CSV `data/experimental_bulk_properties.csv`.  
- B3LYP/def2‑TZVP + D3 + Counterpoise correction is a **validated** quantum‑chemical setup for charged systems; we assume its implementation in psi4 is reliable.  
- All statistical tests assume **independence of observations**; each ion pair is distinct, making this reasonable.  
- The analysis is **observational/associational**: conclusions are limited to correlations, not causal claims about dispersion affecting bulk properties.  
- No GPU or CUDA libraries are used; psi4 runs in CPU‑only mode, fulfilling the free‑tier CI constraints.  
- The benchmark set size is limited to **≤ 500** ion pairs to keep memory and runtime within the CI limits.  
- The correlation between single‑ion‑pair interaction energies and bulk properties is treated as a **heuristic diagnostic**, acknowledging that bulk properties emerge from many‑body interactions and collective dynamics; any observed correlation is exploratory and not interpreted as causal.  
- Network retrieval is attempted for both benchmark and bulk‑property data; if both network and fallback fail, the run aborts (ensuring reproducibility).  

---

