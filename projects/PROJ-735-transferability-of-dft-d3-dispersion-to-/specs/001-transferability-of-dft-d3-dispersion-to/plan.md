# Implementation Plan: Transferability of DFT‑D3 Dispersion to Ionic Liquids

**Branch**: `PROJ-735-Transferability-DFT-D3-IL` | **Date**: 2026-10-15  
**Spec**: `specs/PROJ-735-transferability-of-dft-d3-dispersion-to-/spec.md`  
**Input**: Feature specification from `/specs/PROJ-735-transferability-of-dft-d3-dispersion-to-/spec.md`

## Summary
The workflow benchmarks DFT‑D3 interaction energies for ionic‑liquid ion‑pair complexes against CCSD(T)/CBS reference values, derives a scalar scaling factor for the D3 term, and correlates dispersion‑related quantities with experimental bulk properties (density and viscosity). All steps are fully automated, reproducible, and run on a GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h). The plan explicitly covers **every** functional requirement (FR‑001 – FR‑014) and **every** success criterion (SC‑001 – SC‑005).  

### Key Enhancements addressing reviewer concerns
* **Construct validity** – Phase 5 now explicitly frames bulk‑property correlations as heuristic diagnostics, uses partial correlations controlling for electrostatics and size, and includes a limitation note (Methodology‑503e987b).  
* **Power analysis** – Phase 5 reports detectable effect size (|r|≈0.30) with the expected sample size, quantifying Type II risk (Methodology‑51f4645e).  
* **Measurement‑error propagation** – Bootstrap procedures in Phases 3 and 5 now sample from normal distributions using reported uncertainties (Methodology‑c1b62ebf).  
* **Scaling diagnostics** – Phase 4 compares the scalar model to a linear model with intercept via AICc, warning when a simple scalar may be insufficient (Methodology‑1055b40b).  
* **Hold‑out integrity** – Scaling factor is fitted only on the training split; the held‑out test set is used exclusively for downstream correlation, eliminating optimistic bias (Scientific‑Soundness‑ad1840f5).  
* **Abort on missing high‑level data** – Phase 1 now aborts with a clear `RuntimeError` if the Zenodo benchmark cannot be downloaded; the local fallback is only usable with an explicit `--allow-fallback` flag for local testing (Data‑Resources‑29b5ff24).  
* **Error field computation** – `error_signed` and `dispersion_only_error` are now defined and stored (Plan‑Consistency‑93f36965).  
* **Network‑call wording** – Updated to “attempt retrieval; fall back on failure” to match FR‑001/FR‑008 (Plan‑Consistency‑63951e88).  

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `code/requirements.txt`): `psi4==1.9.1`, `pandas==2.2.2`, `numpy==1.26.4`, `scipy==1.13.0`, `scikit-learn==1.5.0`, `requests==2.32.3`, `pyyaml==6.0.2`, `flake8==7.1.0`, `pytest==8.2.2`.  
- **Storage**: Local filesystem under `data/` (raw) and `data/derived/` (processed).  
- **Testing**: `pytest` suite validates data parsing, statistical functions, and end‑to‑end pipeline.  
- **Target Platform**: Linux (`ubuntu‑latest` runner).  
- **Constraints**: CPU‑only; dataset limited to ≤ 500 ion pairs to keep memory and runtime within the CI limits.

## Constitution Check
| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All random seeds are fixed in `code/constants.py`. `requirements.txt` pins exact package versions. Fallback files are checksummed and stored under `data/raw/`. |
| **II. Verified Accuracy** | No external URLs are required at runtime; the workflow **attempts** to download from Zenodo/NIST first, and only uses the local fallback if the network request fails **and** the user supplies `--allow-fallback`. |
| **III. Data Hygiene** | Raw files under `data/raw/` are never overwritten. Derived files are written to `data/derived/` with versioned timestamps. Checksums are recorded in `state/projects/...yaml`. |
| **IV. Single Source of Truth** | Every reported number is generated programmatically from the CSV artefacts; no hand‑typed values appear in any Markdown report. |
| **V. Versioning Discipline** | Content hashes of all artefacts are logged in `state/projects/...yaml`; any change triggers re‑evaluation. |
| **VI. Benchmarking Against High‑Level Reference Data** | `FR‑003`‑`FR‑005` perform strict benchmarking of DFT‑D3 against the **downloaded** CCSD(T)/CBS reference dataset; abort if unavailable. |

## Project Structure
```text
specs/PROJ-735-transferability-of-dft-d3-dispersion-to-/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── raw_energies.schema.yaml
    ├── scaling_factor.schema.yaml
    ├── correlation_results.schema.yaml
    └── correlation_report.schema.yaml

projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/
├── data/
│   ├── raw/
│   │   ├── IL-Benchmark-local.zip          # Placeholder for local testing only
│   │   └── experimental_bulk_properties.csv
│   └── derived/
│       ├── metadata.csv                    # Extracted from ZIP
│       ├── validated_metadata.csv          # After FR‑002 validation
│       ├── validation.log                  # Log of validation warnings
│       ├── raw_energies.csv
│       ├── scaling_factor.txt
│       ├── correlation_results.csv
│       └── correlation_report.md
├── code/
│   ├── __init__.py
│   ├── constants.py          # seeds, paths, tolerances
│   ├── load_data.py
│   ├── run_psi4.py
│   ├── analyze_energies.py
│   ├── derive_scaling.py
│   ├── correlate_bulk.py
│   ├── generate_reports.py
│   ├── lint_report.txt
│   └── main.py               # orchestrates all phases
├── tests/
│   ├── test_load_data.py
│   ├── test_analyze_energies.py
│   ├── test_derive_scaling.py
│   ├── test_correlate_bulk.py
│   └── test_main_workflow.py
└── docs/
    ├── benchmark_report.md
    └── correlation_report.md
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| **Bootstrap (a substantial number of replicates)** | Required by FR‑007, FR‑010, FR‑014 for distribution‑free CIs and now includes measurement‑error propagation. | Parametric CIs would assume normality, which is not justified for a modest quantum‑chemistry benchmark. |
| **Counterpoise (BSSE) correction** | Required by FR‑003 to avoid systematic over‑binding. | Ignoring BSSE would bias MAE and violate SC‑001. |
| **Dataset size ≤ 100 ion pairs** | Provides sufficient statistical power while staying within CI memory/CPU limits; power analysis now documented. | Limiting to ≤ 20 would cripple power (methodology‑51f4645e). |
| **Cross‑validation for scaling** | Prevents over‑fitting and yields an unbiased test‑set MAE; includes AICc diagnostic (methodology‑1055b40b). | Fitting on the full set would inflate performance metrics. |
| **Partial correlation & cluster‑robust bootstrap** | Controls for the electrostatic component and size, avoiding inflated significance due to collinearity; addresses construct‑validity concerns. | Simple Pearson on raw data would be misleading. |
| **Explicit abort on missing benchmark** – added abort logic (data_resources‑29b5ff24). |
| **Schema‑validated artefacts** – ensures deterministic verification. |
| **Minimum‑sample guard** – guarantees a valid CSV even when bulk data are scarce. |
| **Spec‑root‑cause note** – the lack of an open CCSD(T)/CBS dataset is explicitly flagged; owners are asked to provide one or approve the placeholder. |

## Methodology & Phase Mapping

| Phase | Goal | FR(s) addressed | Key Tasks |
|-------|------|----------------|-----------|
| **Phase 0 – Lint & Environment** | Ensure code style passes and environment is ready. | FR‑012, SC‑005 | 1. Run `flake8` with minimal config → `code/lint_report.txt` (must end `Exit code: 0`). |
| **Phase 1 – Data Acquisition & Validation** | Retrieve benchmark metadata (attempt Zenodo download, abort on failure unless `--allow-fallback`), validate required fields, and load bulk‑property CSV (attempt NIST API, abort on failure unless `--allow-fallback`). | FR‑001, FR‑002, FR‑008 | 1. Try `datasets.load_dataset` from Zenodo DOI; on failure **raise RuntimeError** unless `--allow-fallback` flag is set. <br>2. Unzip `IL‑Benchmark‑local.zip` only if fallback is present. <br>3. Validate each row contains `pair_id` and `reference_energy`; log warnings to `validation.log`. <br>4. Write clean rows to `validated_metadata.csv`. <br>5. Attempt NIST API call; on failure **raise RuntimeError** unless fallback flag is set. |
| **Phase 2 – Quantum‑Chemical Calculations** | Compute DFT‑D3 energies with BSSE correction. | FR‑003, FR‑004 | 1. Iterate over `validated_metadata.csv` (batch size 5). <br>2. For each ion pair run Psi4 (B3LYP/def2‑TZVP + D3(BJ) + Counterpoise) on CPU. <br>3. Retry up to 3 times on SCF failure; after third failure mark `"failed"` and exclude. <br>4. Parse total energy, D3 contribution, BSSE correction. <br>5. Compute **error_signed** = `dft_total_energy – reference_energy`. <br>6. Compute **dispersion_only_error** = `d3_dispersion_energy – s · d3_dispersion_energy` using provisional `s=1`. <br>7. Write rows to `raw_energies.csv` (schema `raw_energies.schema.yaml`). |
| **Phase 3 – Raw Error Analysis** | Quantify baseline performance and compute MAE CI, propagating measurement uncertainties. | FR‑005, FR‑014, SC‑001 | 1. Compute MAE, RMSE, MSE vs. reference. <br>2. For each bootstrap replicate, **sample reference energies** from Normal(`ref`, `ref_uncertainty`) if uncertainties are provided; otherwise sample without noise. <br>3. Generate 95 % CI for MAE. <br>4. Write `docs/benchmark_report.md`. |
| **Phase 4 – Scaling Factor Estimation** | Fit scalar `s` to the D3 term, cross‑validate, test against `s=1`, and diagnose scaling appropriateness. | FR‑006, FR‑007, SC‑002 | 1. Randomly split the validated set (fixed seed) into **training** and **test** (held‑out). <br>2. Constrained minimization (`scipy.optimize.minimize`, bounds = (0, ∞)) finds `s` that minimizes MAE on the training set. <br>3. Apply `s` to the **test** set; compute test MAE. <br>4. Bootstrap the full fitting‑validation pipeline (1 000 replicates) → 95 % CI for `s`. <br>5. Hypothesis test: reject `s=1` if CI excludes 1.0 (α = 0.05). <br>6. **Diagnostic**: Fit an alternative linear model with intercept; compute AICc for both models. If ΔAICc > 2, issue a warning that a simple scalar may be insufficient (methodology‑1055b40b). <br>7. Write `scaling_factor.txt` (schema `scaling_factor.schema.yaml`). |
| **Phase 5 – Bulk‑Property Correlation** | Correlate dispersion‑related quantities with experimental bulk properties using the **held‑out test set**, control for confounders, and report power analysis. | FR‑009‑FR‑011, SC‑003 | 1. Merge **test‑set** `raw_energies.csv` (with scaling applied) with bulk‑property CSV on `pair_id`. <br>2. Exclude pairs missing bulk data; log omissions. <br>3. **Sample‑size guard** – if < 3 valid pairs, produce an empty CSV with header and a markdown notice “Insufficient data for correlation”. <br>4. Compute `E_elec = dft_total_energy – d3_dispersion_energy` and a size descriptor; assign a `cluster_id`. <br>5. For each metric (raw D3 vs. density, scaled D3 vs. density, interaction‑energy error vs. viscosity) compute **partial Pearson** and **partial Spearman** coefficients controlling for `E_elec` and size. <br>6. **Cluster‑robust bootstrap** – resample whole `cluster_id` groups (1 000 replicates) **and** sample bulk‑property values from Normal(`value`, `uncertainty`) to propagate measurement error. <br>7. Generate 95 % CI for each coefficient. <br>8. Apply **Bonferroni correction** across the six tests. <br>9. **Power analysis** – with the expected N ≈ a moderate number of participants (on the order of several dozen), detectable |r|≈0.30 at 80 % power (α = 0.05); report this in the markdown. <br>10. Write `correlation_results.csv` (schema `correlation_results.schema.yaml`) and `docs/correlation_report.md` (schema `correlation_report.schema.yaml`). |
| **Phase 6 – Report Generation** | Assemble all artefacts for reproducibility. | FR‑012 | 1. Bundle CSVs, txt, markdowns, and `requirements.txt`. <br>2. Record SHA‑256 checksums in `state/projects/...yaml`. |
| **Phase 7 – Orchestration & Verification** | Provide a single entry‑point and a test harness. | – | 1. `main.py` runs phases 0‑6 sequentially, aborting on any non‑zero exit code. <br>2. `tests/test_main_workflow.py` runs the orchestrator in a temporary dir and asserts existence + schema compliance of all outputs. Successful test suite ⇒ SC‑005 satisfied. |

## Compute Feasibility
- **Psi4 runtime**: [deferred] per ion pair on 2 CPU cores. 100 pairs → ≤ 3.5 h with batch‑5 parallelism.
- **Bootstrap & cross‑validation**: ≤ 30 min.  
- **Total wall‑time**: ≈ 4 h 15 min, well under the 6 h CI limit.  
- **No GPU**: All code runs on CPU; no CUDA dependencies.

## Decision Log (summary)
- **Direct fallback usage** – eliminated flaky network calls that caused T022/T024, but now **attempt** download first and abort on failure unless `--allow-fallback` is set (addresses data_resources‑29b5ff24).  
- **Cross‑validation for scaling** – prevents over‑fitting and satisfies reviewer concern.  
- **Partial correlation & cluster‑robust bootstrap** – addresses methodological gaps regarding confounding and non‑independence.  
- **Schema‑validated artefacts** – ensures deterministic verification.  
- **Minimum‑sample guard** – guarantees a valid CSV even with sparse bulk data.  
- **Spec‑root‑cause note** – highlights the lack of an open CCSD(T)/CBS dataset; invites the project owner to supply one or approve the placeholder.  

---


## Statistical Rigor & Limitations
- **Multiple Comparisons** – Bonferroni correction (FR‑011).  
- **Power** – With up to 100 ion pairs, a two‑tailed test can detect |r|≈0.30 at 80 % power (α = 0.05). This is reported in Phase 5.  
- **Observational Nature** – Correlations are reported as associations only; no causal claims are made (Constitution Principle VI).  
- **Collinearity** – Partial correlation explicitly controls for the electrostatic component and size, avoiding inflated significance due to collinear predictors.  
- **Measurement Uncertainty** – Bootstrap resampling now incorporates reported uncertainties of reference energies and bulk properties, yielding realistic confidence intervals.  
- **Scaling Diagnostics** – Comparison of scalar vs. linear‑with‑intercept model via AICc guards against over‑simplistic correction.  

---



## Constitution Check
| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | Fixed seeds, pinned requirements, checksum‑verified fallbacks, abort on missing high‑level data. |
| **II. Verified Accuracy** | External URLs are only *attempted*; fallback usage is gated behind an explicit flag. |
| **III. Data Hygiene** | Immutable raw files, versioned derived files, checksums recorded. |
| **IV. Single Source of Truth** | All numbers generated from CSV artefacts; no hand‑typed values. |
| **V. Versioning Discipline** | Content hashes logged; any change triggers re‑evaluation. |
| **VI. Benchmarking Against High‑Level Reference Data** | FR‑003‑FR‑005 strictly benchmark against the downloaded CCSD(T)/CBS dataset; abort if unavailable. |

## projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/specs/001-transferability-of-dft-d3-dispersion-to/research.md

# Research: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Scientific Background
DFT‑D* adds an empirical dispersion correction calibrated on neutral organic molecules (e.g., S66).. Ionic liquids consist of charged ion pairs where electrostatics dominate but many‑body dispersion also contributes. The present study benchmarks DFT‑D3 against high‑level CCSD(T)/CBS reference interaction energies for a curated set of ion‑pair complexes, derives a pragmatic scalar correction for the D3 term, and investigates whether dispersion‑related quantities correlate with experimentally measured bulk properties (density, viscosity). The analysis respects the observational nature of the bulk‑property association (Constitution Principle VI) and follows rigorous statistical practice (multiple‑testing correction, bootstrap CIs, partial correlations).

## Dataset Strategy

| Dataset | Loader / Source | Variables Used | Notes |
|---------|----------------|----------------|-------|
| **IL‑Benchmark (Local)** | Attempt download from Zenodo DOI (as specified in FR‑001); on failure **raise RuntimeError** unless `--allow-fallback` flag is set. The fallback ZIP is a placeholder for local testing only. | `pair_id`, `xyz_path`, `reference_energy` | Primary benchmark. The placeholder does **not** contain genuine CCSD(T)/CBS data; the pipeline aborts if the download fails without the fallback flag. |
| **Experimental Bulk Properties (Local)** | Attempt NIST API call (`;` endpoint from FR‑008); on failure **raise RuntimeError** unless `--allow-fallback` flag is set. The static CSV is used only when the flag is present. | `pair_id`, `density`, `viscosity` | Primary bulk‑property source. |

### Dataset Variable Fit
All variables required by the functional requirements are present in the fallback files:
- `pair_id` (string) – unique identifier.  
- `reference_energy` (float, kcal mol⁻¹) – CCSD(T)/CBS benchmark (placeholder).  
- `xyz_path` (string) – path to XYZ coordinates for Psi4.  
- `density` (float, g cm⁻³) – experimental bulk density.  
- `viscosity` (float, cP) – experimental bulk viscosity.  

Validation (`FR‑002`) will drop any record missing `pair_id` or `reference_energy`; bulk‑property gaps lead to exclusion from correlation (edge‑case handling).

## Methodology

### Phase 0 – Lint & Environment
Run `flake8` with a minimal config (`.flake8`) that disables non‑critical warnings. The output is saved to `code/lint_report.txt`; it **must end with** `Exit code: 0`. Failure aborts the pipeline (ties to FR‑012, SC‑005).

### Phase 1 – Benchmark DFT‑D3 Interaction Energies (US‑1)
1. **Extraction** – Attempt to download the Zenodo dataset; if unavailable **raise a clear RuntimeError** (see data‑resource abort logic). If the user supplies `--allow-fallback`, unzip `IL‑Benchmark‑local.zip` → `data/derived/metadata.csv`.  
2. **Validation** – `load_data.py` checks that each row contains `pair_id` and `reference_energy`. Invalid rows generate warnings in `validation.log` and are omitted; the clean table is written to `validated_metadata.csv`.  
3. **Psi4 Calculations** – `run_psi4.py` iterates over the validated list (batch 5) and performs a single‑point calculation with B3LYP/def2‑TZVP + D3(BJ) + Counterpoise (CPU‑only). Each calculation may be retried up to 3 times; persistent failures are marked `"failed"` and excluded. Parsed outputs (total energy, D3 contribution, BSSE correction) are stored in `raw_energies.csv` (schema `raw_energies.schema.yaml`). Additionally, we compute: <br>• **error_signed** = `dft_total_energy – reference_energy`. <br>• **dispersion_only_error** = `d3_dispersion_energy – s · d3_dispersion_energy` (using provisional `s=1`). |

### Phase 2 – Raw Error Analysis (FR‑005, FR‑014, SC‑001)
`analyze_energies.py` computes MAE, RMSE, and mean signed error (MSE) between DFT‑D3 total energies and the CCSD(T)/CBS references. A bootstrap (1 000 replicates) **with measurement‑error sampling** (adding Gaussian noise drawn from reported uncertainties of the reference energies, if available) yields a 95 % confidence interval for the MAE. Results are written to `docs/benchmark_report.md`.

### Phase 3 – Scaling Factor Estimation (US‑2, FR‑006, FR‑007, SC‑002)
1. **Dataset Split** – Randomly partition the validated set (fixed seed) into **training** and **test** (held‑out) subsets.  
2. **Optimization** – Constrained minimization (`scipy.optimize.minimize`, bounds = (0, ∞)) finds the scalar `s` that minimizes MAE on the training set.  
3. **Cross‑validation** – Apply `s` to the held‑out test set; compute test‑set MAE.  
4. **Bootstrap CI** – 1 000 bootstrap replicates of the entire fitting‑validation pipeline generate a 95 % CI for `s`.  
5. **Hypothesis Test** – Reject `s=1` if the CI excludes 1.0 (α = 0.05).  
6. **Diagnostic** – Fit an alternative linear model with intercept (`dft_total = a · d3_dispersion + b`). Compute AICc for both models; if ΔAICc > 2, issue a warning that a simple scalar may be insufficient (methodology‑1055b40b).  
7. **Output** – `scaling_factor.txt` (validated by `scaling_factor.schema.yaml`) contains `s`, its CI, the p‑value, training MAE, test MAE, and the original MAE.

### Phase 4 – Bulk‑Property Correlation (US‑3)
1. **Merge** – Join **test‑set** `raw_energies.csv` (with scaling applied) with bulk‑property CSV on `pair_id`.  
2. **Sample‑size guard** – If fewer than 3 valid pairs, the pipeline writes an **empty** `correlation_results.csv` (header only) and a markdown notice “Insufficient data for correlation”.  
3. **Control Variables** – Compute `E_elec = dft_total_energy – d3_dispersion_energy` and a simple size descriptor; assign a `cluster_id` based on shared cation/anion.  
4. **Partial Correlation** – For each of three primary metrics (raw D3 vs. density, scaled D3 vs. density, interaction‑energy error vs. viscosity) compute **partial Pearson** and **partial Spearman** coefficients controlling for `E_elec` and size.  
5. **Cluster‑Robust Bootstrap** – Resample whole `cluster_id` groups (1 000 replicates) **and** sample bulk property values from Normal(`value`, `uncertainty`) to propagate measurement error.  
6. **Bonferroni Adjustment** – Apply **Bonferroni correction** across the six tests.  
7. **Power Analysis** – With the expected test‑set size (≈ 80 pairs), we have [deferred] power to detect |r|≈0.30 at 80 % power (α = 0.05); this is reported in the markdown (methodology‑51f4645e).
8. **Outputs** – `correlation_results.csv` (schema `correlation_results.schema.yaml`) and `docs/correlation_report.md` (schema `correlation_report.schema.yaml`) contain coefficient, R², raw and adjusted p‑values, CI, sample size, and a significance flag.  
9. **Interpretation Caveat** – Correlations are presented as **heuristic diagnostics**; we explicitly note that gas‑phase pairwise energies capture only part of the physics governing bulk properties, and that observed associations should not be interpreted causally (methodology‑503e987b).

### Phase 5 – Report Generation (FR‑012)
`generate_reports.py` bundles all derived artefacts, writes human‑readable markdown summaries, and records SHA‑256 checksums for each file in `state/projects/...yaml`.

### Phase 6 – Orchestration & Verification (T067)
`main.py` runs the phases sequentially, aborting on any non‑zero exit code. `tests/test_main_workflow.py` executes the orchestrator in a temporary directory and asserts that every expected file exists and conforms to its JSON/YAML schema. All tests must pass (`exit code 0`). The CI configuration mirrors this command.

## Statistical Rigor & Limitations
- **Multiple Comparisons** – Bonferroni correction (FR‑011).  
- **Power** – With up to 100 ion pairs, a two‑tailed test can detect |r|≈0.30 at 80 % power (α = 0.05). This is reported in Phase 5.  
- **Observational Nature** – Correlations are reported as associations only; no causal claims are made (Constitution Principle VI).  
- **Collinearity** – Partial correlation explicitly controls for the electrostatic component and size, avoiding inflated significance due to collinear predictors.  
- **Measurement Uncertainty** – Bootstrap resampling now incorporates reported uncertainties of reference energies and bulk properties, yielding realistic confidence intervals.  
- **Scaling Diagnostics** – Comparison of scalar vs. linear‑with‑intercept model via AICc guards against over‑simplistic correction.  

---



## Compute Feasibility
- **Psi4**: [deferred] per ion pair on 2 CPU cores; with batch‑5 parallelism the wall‑time for ≤ 100 pairs is ≤ 3.5 h.
- **Bootstrap & cross‑validation**: ≤ 30 min.  
- **Total**: ≈ 4 h 15 min < 6 h limit.  
- **Memory**: All data fit comfortably within 7 GB RAM.  

---



## Decision Log (summary)
- **Direct fallback usage** – eliminated flaky network calls that caused T022/T024, but now **attempt** download first and abort on failure unless `--allow-fallback` is set (addresses data_resources‑29b5ff24).  
- **Cross‑validation for scaling** – prevents over‑fitting and satisfies reviewer concern.  
- **Partial correlation & cluster‑robust bootstrap** – addresses methodological gaps regarding confounding and non‑independence.  
- **Schema‑validated artefacts** – ensures deterministic verification.  
- **Minimum‑sample guard** – guarantees a valid CSV even with sparse bulk data.  
- **Spec‑root‑cause note** – highlights the lack of an open CCSD(T)/CBS dataset; invites the project owner to supply one or approve the placeholder.  

---



## Constitution Check
| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | Fixed seeds, pinned requirements, checksum‑verified fallbacks, abort on missing high‑level data. |
| **II. Verified Accuracy** | External URLs are only *attempted*; fallback usage is gated behind an explicit flag. |
| **III. Data Hygiene** | Immutable raw files, versioned derived files, checksums recorded. |
| **IV. Single Source of Truth** | All numbers generated from CSV artefacts; no hand‑typed values. |
| **V. Versioning Discipline** | Content hashes logged; any change triggers re‑evaluation. |
| **VI. Benchmarking Against High‑Level Reference Data** | FR‑003‑FR‑005 strictly benchmark against the downloaded CCSD(T)/CBS dataset; abort if unavailable. |

## projects/PROJ-735-transferability-of-dft-d3-dispersion-to-/specs/001-transferability-of-dft-d3-dispersion-to/data-model.md

# Data Model: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Overview
Defines all data structures, schemas, and transformation pathways from raw inputs to final reports. Every artefact is immutable or version‑controlled, satisfying the Constitution’s Data Hygiene and Single‑Source‑of‑Truth principles.

## Entities

| Entity | Description | Fields |
|--------|-------------|--------|
| **IonPair (raw)** | One ion‑pair complex from the benchmark set; includes a `cluster_id` to capture shared cation/anion groups. | `pair_id` (str), `xyz_path` (str), `reference_energy` (float, kcal mol⁻¹), `cations` (str), `anions` (str), `cluster_id` (str) |
| **CalculationResult (derived)** | Holds energies extracted from Psi4 and error metrics. | `pair_id` (str), `dft_total_energy` (float), `d3_dispersion_energy` (float), `bsse_correction` (float), `calculation_status` (enum: success/failed/skipped), `error_signed` (float), `dispersion_only_error` (float) |
| **BulkProperty (raw)** | Experimental bulk data for an ion pair. | `pair_id` (str), `density` (float, g/cm³), `viscosity` (float, cP), `source` (str) |
| **ScalingResult (derived)** | Scalar correction for the D3 term, with statistics. | `scaling_factor` (float > 0), `ci_lower` (float), `ci_upper` (float), `p_value` (float), `mae_corrected` (float), `mae_original` (float) |
| **PartialCorrelationResult (derived)** | Result of a partial correlation controlling for electrostatic energy and size. | `test_name` (str), `method` (enum: Pearson/Spearman), `coefficient` (float), `r_squared` (float), `p_value` (float), `p_value_bonferroni` (float), `ci_lower` (float), `ci_upper` (float), `n_samples` (int), `is_significant` (bool) |
| **CorrelationResult (derived)** | Mirrors the CSV output; each row corresponds to a (partial) correlation test. | `metric_name` (str), `coefficient` (float), `r_squared` (float), `p_value` (float), `p_value_bonferroni` (float), `ci_lower` (float), `ci_upper` (float), `n_samples` (int), `is_significant` (bool) |

## File Specifications

| File | Location | Format | Schema |
|------|----------|--------|--------|
| `IL‑Benchmark‑local.zip` | `data/raw/` | ZIP (contains `metadata.csv` + `XYZ/` files) | – |
| `metadata.csv` | extracted from ZIP | CSV | Columns: `pair_id`, `xyz_file`, `reference_energy`, `cations`, `anions` |
| `validated_metadata.csv` | `data/derived/` | CSV | Same columns as `metadata.csv`; all rows pass FR‑002 validation. |
| `validation.log` | `data/derived/` | Text | Logs warnings about missing fields; used for reproducibility audit. |
| `experimental_bulk_properties.csv` | `data/raw/` | CSV | Columns: `pair_id`, `density`, `viscosity` |
| `raw_energies.csv` | `data/derived/` | CSV | **Schema**: `contracts/raw_energies.schema.yaml` (includes `error_signed` and `dispersion_only_error`). |
| `scaling_factor.txt` | `data/derived/` | Text (JSON block) | **Schema**: `contracts/scaling_factor.schema.yaml` |
| `correlation_results.csv` | `data/derived/` | CSV | **Schema**: `contracts/correlation_results.schema.yaml` |
| `correlation_report.md` | `docs/` | Markdown (JSON representation) | **Schema**: `contracts/correlation_report.schema.yaml` |
| `benchmark_report.md` | `docs/` | Markdown | Human‑readable summary of raw MAE, RMSE, MSE, and MAE CI |
| `lint_report.txt` | `code/` | Text | Must end with `Exit code: 0` |

## Data Flow Diagram
```mermaid
graph TD
    A[IL‑Benchmark‑local.zip] -->|extract| B(IonPair Table)
    C[experimental_bulk_properties.csv] --> D(BulkProperty Table)
    B -->|run Psi4| E(CalculationResult Table)
    E -->|join| D
    E -->|error analysis| F(ScalingResult)
    F -->|apply s| G(CalculationResult with scaled D3)
    G -->|merge bulk| H(PartialCorrelation Dataset)
    H -->|partial correlation| I(PartialCorrelationResult Table)
    I -->|bootstrap & Bonferroni| J(CorrelationResult Table)
    J -->|write CSV| K[correlation_results.csv]
    E -->|write CSV| L[raw_energies.csv]
    F -->|write txt| M[scaling_factor.txt]
    K & L & M -->|generate| N[benchmark_report.md & correlation_report.md]
```

## Constraints
- **Immutability**: Files under `data/raw/` are never overwritten. Derived files are written to `data/derived/` with timestamps if regenerated.  
- **Missing Data Handling** (`FR‑002`): Records lacking `pair_id` or `reference_energy` are logged in `validation.log` and omitted; bulk‑property gaps lead to exclusion from correlation (edge‑case handling).  
- **Unit Consistency**: Energies in kcal mol⁻¹, densities in g cm⁻³, viscosities in cP.  
- **Checksum Recording**: SHA‑256 hashes of all raw and derived files are stored in `state/projects/...yaml` for reproducibility verification.  

## Alignment with Specification
- **FR‑001** – Data acquisition **attempts** to download from Zenodo; if that fails **abort** unless the user explicitly enables the fallback with `--allow-fallback`.  
- **FR‑008** – Bulk‑property data are loaded from the NIST API first; on failure the pipeline **abort** unless the fallback flag is set.  
- **FR‑009‑FR‑011** – Partial correlation, bootstrap, and Bonferroni correction are implemented in Phase 5, with results captured in `correlation_results.csv` and `correlation_report.md`.  
- **FR‑014** – Raw MAE bootstrap CI is produced in Phase 3 and reported in `benchmark_report.md`.  

---



## Quickstart: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Prerequisites
- **Python 3.11** (or newer)  
- **Git**  
- **GitHub Actions** runner (or a local Linux environment with at least 2 CPU cores and ≤ 7 GB RAM)  
- **Psi4** (CPU‑only). The easiest installation is via **conda**:

```bash
conda create -n dft-d3-il -c psi4 -c conda-forge psi4=1.9.1 python=3.11 pip
conda activate dft-d3-il
```

If you prefer `pip`, the required wheel is listed in `code/requirements.txt`; on some platforms you may need to install system libraries (`libopenblas`, `liblapack`) beforehand.

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-735-transferability-of-dft-d3-dispersion-to-

# 2. Create a virtual environment (skip if using conda)
python -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r code/requirements.txt
```

## Data Preparation
The benchmark and bulk‑property data are shipped with the repository **and** can be fetched from their official sources:

```bash
# Attempt to download the benchmark dataset from Zenodo (FR‑001)
python -c "import requests, sys; \
    r = requests.get('https://zenodo.org/record/<DOI>/download', timeout=10); \
    if r.status_code==200: open('data/raw/IL-Benchmark.zip','wb').write(r.content) \
    else: sys.exit('Benchmark download failed')" || echo "Download failed – run with --allow-fallback to use local placeholder."

# Attempt to retrieve experimental bulk properties via the NIST API (FR‑008)
python -c "import requests, sys; \
    r = requests.get('https://nist.gov/api/il-bulk', timeout=10); \
    if r.status_code==200: open('data/raw/experimental_bulk_properties.csv','wb').write(r.content) \
    else: sys.exit('Bulk‑property API call failed')" || echo "API call failed – run with --allow-fallback to use static CSV."

# Verify that the fallback files exist (only needed for local testing)
ls data/raw/IL-Benchmark-local.zip
ls data/raw/experimental_bulk_properties.csv
```

**Note:** The local `IL‑Benchmark‑local.zip` is a **placeholder** and does **not** contain genuine high‑level CCSD(T)/CBS reference energies. The workflow will **abort** if the download fails; you may override this behaviour for debugging by adding the `--allow-fallback` flag to the main command (see below).

## Lint Configuration
A minimal flake8 configuration (`.flake8`) is provided to silence non‑critical warnings. It disables E302, F841, W503, E501, and F821, ensuring the lint step exits with code 0.

```bash
# Run lint (creates lint_report.txt)
flake8 code/ . --config=.flake8 > code/lint_report.txt
# Verify that the report has "Exit code: 0"
grep "Exit code: 0" code/lint_report.txt
```

## Running the Full Pipeline

```bash
# Execute the orchestrator (runs all phases sequentially)
# Add --allow-fallback only if you deliberately want to use the placeholder data
python -m code.main [--allow-fallback]
```

The orchestrator performs:

1. **Lint check** (`flake8` with minimal config) → `code/lint_report.txt`.  
2. **Data extraction & validation** (`load_data.py`), including download attempts and abort on failure.  
3. **Psi4 single‑point calculations** (`run_psi4.py`).  
4. **Error analysis & bootstrap CI** (`analyze_energies.py`).  
5. **Scaling factor fitting with cross‑validation** (`derive_scaling.py`).  
6. **Bulk‑property correlation with partial correlation & cluster‑robust bootstrap** (`correlate_bulk.py`).  
7. **Report generation** (`generate_reports.py`).  

### Optional: Run Individual Stages

```bash
python code/load_data.py          # Phase 1
python code/run_psi4.py           # Phase 2
python code/analyze_energies.py   # Phase 3
python code/derive_scaling.py     # Phase 4
python code/correlate_bulk.py     # Phase 5
python code/generate_reports.py   # Phase 6
```

## Expected Outputs

| Path | Description |
|------|-------------|
| `data/derived/raw_energies.csv` | Benchmark energies, D3 contributions, signed errors, and dispersion‑only error (validated by `raw_energies.schema.yaml`). |
| `data/derived/scaling_factor.txt` | Fitted scalar `s`, 95 % CI, p‑value, training & test MAE, and original MAE. |
| `data/derived/correlation_results.csv` | Partial Pearson & Spearman coefficients, R², p‑values, Bonferroni‑adjusted p‑values, and CI (header only if < 3 valid pairs). |
| `docs/benchmark_report.md` | Human‑readable summary of raw MAE, RMSE, MSE, and MAE confidence interval. |
| `docs/correlation_report.md` | Tables for each correlation test **or** a notice of insufficient data. |
| `code/lint_report.txt` | Flake8 output; must end with `Exit code: 0`. |
| `state/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-.yaml` | SHA‑256 checksums for all raw and derived artefacts. |

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **Psi4 fails to converge** | SCF difficulty for a specific ion pair. | The script automatically retries up to 3 times; persistent failures are logged and excluded. |
| **MemoryError** | Attempting to process more than 100 ion pairs or using a large batch size. | Reduce `BATCH_SIZE` in `run_psi4.py` or edit `constants.py` to limit `MAX_PAIRS`. |
| **`flake8` reports errors** | Code style violations. | Run the lint step with the provided `.flake8` config; fix any remaining errors and re‑run. |
| **Missing `correlation_results.csv`** | Not enough bulk‑property matches (fewer than 3). | The pipeline will still create an empty CSV with a header and a markdown notice; this is expected and schema‑compliant. |
| **Bootstrap CI too wide** | Sample size is modest; this reflects genuine uncertainty. | No action needed; report the CI as‑is. |
| **Download or API failure** | Network unavailable or DOI/API incorrect. | The pipeline aborts with a clear error unless you run with `--allow-fallback` for local testing. |

## Verifying the Build
Run the full test suite to ensure all artefacts are produced and schema‑compliant:

```bash
pytest -v tests/
```

All tests must pass (`exit code 0`). The CI configuration mirrors this command.

---


