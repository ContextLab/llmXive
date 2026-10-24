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

1. **Given** the IL‑Benchmark dataset is available and contains reference interaction energies, **when** the workflow runs the psi4 single‑point calculations, **then** a CSV file `raw_energies.csv` is created containing (i) ion‑pair identifier, (ii) reference energy, (iii) DFT‑D3 total energy, (iv) D3 dispersion contribution, (v) signed error (`error_signed` = dft_total_energy – reference_energy), and (vi) `dispersion_only_error` column (difference between D3 term and any available reference dispersion component; set to NA if unavailable).  
2. **Given** the calculations complete successfully, **when** the error‑analysis script runs, **then** it reports MAE, RMSE, and mean signed error (MSE) and the values are recorded in `benchmark_report.md`.

---

### Edge Cases

- **Missing reference energy**: If an ion‑pair entry lacks a CCSD(T)/CBS reference, the pipeline must log a warning, skip that entry, and continue without aborting.  
- **Psi4 calculation failure**: If a single‑point job fails (e.g., SCF convergence), the workflow retries up to **3** times; after the third failure the entry is recorded as "failed" and excluded from downstream analysis.  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve the IL‑Benchmark interaction‑energy dataset (including CCSD(T)/CBS reference values and structural coordinates) from the Zenodo DOI `10.5281/zenodo.7890123`. If the network request fails, the system MUST load the local fallback file `data/IL‑Benchmark‑local.zip` **only for development**; the final analysis MUST use the Zenodo data to satisfy Constitution Principle VI. (See US‑1)  
- **FR-002**: System MUST validate that each record contains **both** a reference interaction energy **and** a unique ion‑pair identifier; records missing either field MUST be flagged and omitted from analysis (See US‑1).  
- **FR-003**: System MUST perform a single‑point energy calculation for each ion pair using **psi4** with the B3LYP functional, the **def2‑TZVP** basis set, the D3 (Becke‑Johnson damping) dispersion correction, and the **Counterpoise correction** for Basis Set Superposition Error (BSSE), executing on **CPU only** (no GPU) (See US‑1).  
- **FR-004**: System MUST extract from psi4 output the total interaction energy and the separate D3 dispersion contribution, compute `error_signed = dft_total_energy – reference_energy`, compute `dispersion_only_error = d3_dispersion_energy – reference_dispersion` (if a reference dispersion component is available; otherwise set to NA), and store all fields in a structured CSV with columns `pair_id, reference_energy, dft_total_energy, d3_dispersion_energy, error_signed, dispersion_only_error` (See US‑1).  
- **FR-005**: System MUST compute error metrics (MAE, RMSE, mean signed error) between DFT‑D3 total energies and the CCSD(T)/CBS references (See US‑1).  
- **FR-014**: System MUST compute the **95 % confidence interval for the raw MAE** (from FR‑005) using **bootstrap resampling with 1 000 replicates**, propagating measurement uncertainties of the CCSD(T)/CBS references (assumed ±0.5 kcal/mol). (See US‑1)  
- **FR-019**: System MUST ensure that any use of the local fallback `IL‑Benchmark‑local.zip` is restricted to development or CI‑failure scenarios; the production run must verify that the Zenodo dataset was successfully downloaded, otherwise abort with an error (ensuring compliance with Constitution Principle VI). (See US‑1)  
- **FR-020**: System MUST complete the entire workflow on a GitHub Actions free‑tier runner within **6 hours** and consume **≤ 7 GB RAM** (See US‑1).

### Key Entities

- **Ion‑Pair**: Represents a specific cation–anion combination; attributes include `pair_id`, `reference_energy (kcal/mol)`, `experimental_density (g/cm³)`, `experimental_viscosity (cP)`.  
- **CalculationResult**: Holds `pair_id`, `dft_total_energy`, `d3_dispersion_energy`, `error_signed`, `dispersion_only_error`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The system MUST report the Mean Absolute Error (MAE) of raw DFT‑D3 interaction energies versus CCSD(T)/CBS references, along with a **95 % confidence interval generated via bootstrap resampling (1 000 replicates)** that incorporates propagated measurement uncertainties (See US‑1).  
- **SC-005**: The entire workflow completes on a GitHub Actions free‑tier runner within **6 hours** and uses **≤ 7 GB RAM** (See US‑1).

## Assumptions

- The IL‑Benchmark dataset released on Zenodo (`10.5281/zenodo.7890123`) contains **≥ 100** ion‑pair complexes with high‑level CCSD(T)/CBS reference interaction energies and **structural coordinates (XYZ files)** required for calculations.  
- All statistical tests assume **independence of observations**; each ion pair is distinct, making this reasonable.  
- The analysis is **observational/associational**: conclusions are limited to the accuracy of DFT‑D3 predictions, not causal claims about bulk properties.  
- No GPU or CUDA libraries are used; psi4 runs in CPU‑only mode, fulfilling the free‑tier CI constraints.  
- The benchmark set size is limited to **≤ 500** ion pairs to keep memory and runtime within the CI limits.  
- Network retrieval is attempted for the benchmark dataset; if both network and fallback fail, the run aborts (ensuring reproducibility).  
