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

1. **Given** the IL‑Benchmark dataset is available and contains reference interaction energies, **when** the workflow runs the psi4 single‑point calculations, **then** a CSV file `raw_energies.csv` is created containing (i) ion‑pair identifier, (ii) reference energy, (iii) DFT‑D3 total energy, (iv) D3 dispersion contribution, and (v) signed error.
2. **Given** the calculations complete successfully, **when** the error‑analysis script runs, **then** it reports MAE, RMSE, and mean signed error (MSE) and the values are recorded in `benchmark_report.md`.

---

### User Story 2 – Derive a Simple Scaling Correction (Priority: P2)

A researcher wants to obtain a single scalar that, when applied to the D3 dispersion term, reduces systematic bias across the benchmark set, thereby providing a pragmatic correction that can be used in future high‑throughput screens.

**Why this priority**: A calibrated scaling factor directly addresses the "bias correction" component of the expected results and makes the method usable beyond the benchmark.

**Independent Test**: Running the "scaling" stage on the CSV from US‑1 produces a single numeric factor and a re‑computed error summary.

**Acceptance Scenarios**:

1. **Given** `raw_energies.csv` exists, **when** the linear‑fit script is executed, **then** it returns a positive scaling factor `s` (constrained `s > 0`) that minimizes the mean absolute error of the corrected interaction energies, and writes `scaling_factor.txt`.
2. **Given** the scaling factor is applied, **when** the corrected energies are recomputed, **then** the new MAE is reported and the statistical test shows whether `s` differs significantly from 1.0 (p < 0.05).

---

### User Story 3 – Correlate Dispersion Terms with Bulk Properties (Priority: P3)

An analyst wishes to test whether the magnitude of the (raw or scaled) D3 dispersion contribution is associated with experimentally measured bulk properties (density and viscosity) of the corresponding ionic liquids, thereby probing the practical relevance of any systematic error.

**Why this priority**: This story links the quantum‑chemical benchmark to experimentally observable macroscopic behavior. While the primary transferability question is answered by the benchmark in US-1, this correlation serves as a **heuristic diagnostic** to check if the dispersion physics captured by D3 aligns with macroscopic trends. This analysis is explicitly limited to assessing statistical association; it does not claim causal influence, acknowledging that bulk properties emerge from many-body interactions and collective dynamics.

**Independent Test**: Executing the correlation stage on the corrected CSV produces Pearson and Spearman coefficients, bootstrap confidence intervals, and Bonferroni‑adjusted p‑values.

**Acceptance Scenarios**:

1. **Given** the corrected interaction‑energy CSV and a CSV of experimental densities & viscosities (retrieved from the NIST IL Thermophysical Database or the static fallback file), **when** the correlation script runs, **then** it outputs `correlation_report.md` containing (a) Pearson |R|, R², and p‑value for D3 term vs density, (b) Pearson |R|, R², and p‑value for interaction‑energy error vs viscosity, and (c) 95 % bootstrap confidence intervals for each coefficient.
2. **Given** the correlation results, **when** the Bonferroni correction is applied to the set of p‑values, **then** the adjusted p‑values are reported and the significance thresholds are evaluated.

---

### Edge Cases

- **Missing reference energy**: If an ion‑pair entry lacks a CCSD(T)/CBS reference, the pipeline must log a warning, skip that entry, and continue without aborting.
- **Psi4 calculation failure**: If a single‑point job fails (e.g., SCF convergence), the workflow retries up to **3** times; after the third failure the entry is recorded as "failed" and excluded from downstream analysis.
- **Absent bulk‑property data**: If the NIST API does not return density or viscosity for a given ion pair, the correlation step excludes that pair and notes the omission in the final report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve the IL‑Benchmark interaction‑energy dataset (including CCSD(T)/CBS reference values and structural coordinates) from the Zenodo DOI ``. If the network request fails, the system MUST load the local fallback file `data/IL-Benchmark-local.zip` (See US-1).
- **FR-002**: System MUST validate that each record contains **both** a reference interaction energy **and** a unique ion‑pair identifier; records missing either field MUST be flagged and omitted from analysis (See US-1).
- **FR-003**: System MUST perform a single‑point energy calculation for each ion pair using **psi4** with the B3LYP functional, the **def2-TZVP** basis set, the D3 (Becke‑Johnson damping) dispersion correction, and the **Counterpoise correction** for Basis Set Superposition Error (BSSE), executing on **CPU only** (no GPU) (See US-1).
- **FR-004**: System MUST extract from psi4 output the total interaction energy and the separate D3 dispersion contribution, and store them in a structured CSV (See US-1).
- **FR-005**: System MUST compute error metrics (MAE, RMSE, mean signed error) between DFT‑D3 total energies and the CCSD(T)/CBS references (See US-1).
- **FR-006**: System MUST fit a linear scaling factor *s* (constrained *s > 0*) to the D3 dispersion term that minimizes the **Mean Absolute Error (MAE)** of the corrected interaction energies (See US-2).
- **FR-007**: System MUST test the null hypothesis *s = 1.0* by constructing a **95% bootstrap confidence interval** on the parameter *s* using **1,000** replicates; if the interval excludes 1.0, the null hypothesis is rejected (See US-2).
- **FR-008**: System MUST retrieve experimental bulk‑property data (density, viscosity) for each ion pair from the NIST IL Thermophysical Database via the endpoint `; if the API fails, the system MUST load the static CSV file `data/experimental_bulk_properties.csv` provided with the benchmark set (See US-3).
- **FR-009**: System MUST compute Pearson and Spearman correlation coefficients between (a) **raw D3 term** and density, (b) **scaled D3 term** and density, (c) **interaction‑energy error** and viscosity, together with associated p‑values and **R² (coefficient of determination)** (See US-3).
- **FR-010**: System MUST perform bootstrap resampling with **1 000** replicates to generate 95 % confidence intervals for each correlation coefficient (See US-3).
- **FR-011**: System MUST apply a Bonferroni correction to the family of correlation tests to control the family‑wise error rate (See US-3).
- **FR-012**: System MUST generate a reproducible, version‑controlled report package containing (i) raw energies CSV, (ii) scaling factor file, (iii) correlation report, and (iv) a `requirements.txt` that pins all Python dependencies (See US-1‑US‑3).
- **FR-014**: System MUST compute the **95% confidence interval for the raw MAE** (from FR-005) using **bootstrap resampling with 1,000 replicates** (See US-1).

### Key Entities

- **Ion‑Pair**: Represents a specific cation–anion combination; attributes include `pair_id`, `reference_energy (kcal/mol)`, `experimental_density (g/cm³)`, `experimental_viscosity (cP)`.
- **CalculationResult**: Holds `pair_id`, `dft_total_energy`, `d3_dispersion_energy`, `error_signed`, `scaled_d3_energy`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The system MUST report the Mean Absolute Error (MAE) of raw DFT‑D3 interaction energies versus CCSD(T)/CBS references, along with a **95% confidence interval generated via bootstrap resampling (1,000 replicates)** (See US-1).
- **SC-002**: The system MUST report the fitted scaling factor *s*, its **95% bootstrap confidence interval**, and the result of the hypothesis test (whether the interval excludes 1.0) (See US-2).
- **SC-003**: The system MUST report the Pearson and Spearman correlation coefficients, p-values, **R² values**, and 95% bootstrap confidence intervals for the correlations between D3 terms and bulk properties (See US-3).
- **SC-005**: The entire workflow completes on a GitHub Actions free‑tier runner within **6 hours** and uses **≤ 7 GB RAM**.

## Assumptions

- The IL‑Benchmark dataset released on Zenodo (``) contains **≥ 100** ion‑pair complexes with high‑level CCSD(T)/CBS reference interaction energies and **structural coordinates (XYZ files)** required for calculations.
- Experimental bulk‑property values (density, viscosity) are available for **≥ 80 %** of the ion pairs via the NIST IL Thermophysical Database; if the API is unavailable, the system falls back to the static CSV `data/experimental_bulk_properties.csv`.
- B3LYP/def2‑TZVP + D3 + Counterpoise correction is a **validated** quantum‑chemical setup for charged systems; we assume its implementation in psi4 is reliable.
- All statistical tests assume **independence of observations**; given each ion pair is distinct, this is reasonable.
- The analysis is **observational/associational**: conclusions are limited to correlations, not causal claims about dispersion affecting bulk properties.
- **Methodological Limitation (US-3)**: The correlation between single-ion-pair interaction energies (2-body, gas-phase) and bulk properties (many-body, condensed phase) is treated as a **heuristic diagnostic**. We acknowledge that viscosity and density are emergent properties dominated by collective dynamics and many-body effects; thus, any observed correlation is not expected to be perfect and should not be interpreted as a direct causal link.
- No GPU or CUDA libraries are used; psi4 is run in its default CPU mode, fulfilling the free‑tier CI constraints.
- The benchmark set size is limited to **≤ 500** ion pairs to keep memory and runtime within the CI limits.
- The correlation between single-ion-pair interaction energies and bulk properties is treated as a heuristic diagnostic, acknowledging that bulk properties emerge from many-body interactions and collective dynamics.

---