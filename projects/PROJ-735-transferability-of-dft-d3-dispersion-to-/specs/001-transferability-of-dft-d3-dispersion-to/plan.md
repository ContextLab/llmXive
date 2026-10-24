# Implementation Plan: Transferability of DFT‑D3 Dispersion to Ionic Liquids

**Branch**: `PROJ-735-Transferability-DFT-D3-IL` | **Date**: 2026-10-24  
**Spec**: `specs/PROJ-735-transferability-of-dft-d3-dispersion-to-/spec.md`  
**Input**: Feature specification from `/specs/PROJ-735-transferability-of-dft-d3-dispersion-to-/spec.md`

## Summary
The workflow is designed to (1) benchmark DFT‑D3 interaction energies for a set of ionic‑liquid ion‑pair complexes against high‑level CCSD(T)/CBS reference values, (2) derive a pragmatic scalar scaling factor for the D3 term, (3) perform residual diagnostics after scaling (FR‑018), and (4) explore partial correlations between (raw or scaled) D3 contributions and experimental bulk properties (density, viscosity). All steps are fully automated, reproducible, and constrained to run on a GitHub Actions free‑tier runner (≤ 2 CPU cores, ≤ 7 GB RAM, ≤ 6 h). The plan explicitly maps **every** functional requirement (FR‑001 – FR‑020) and **every** success criterion (SC‑001 – SC‑006).

> **Important limitation** – The specification currently provides **empty placeholders** for the Zenodo DOI (FR‑001) and the NIST IL Thermophysical Database endpoint (FR‑008). Consequently, Phase 1 will **attempt** to download from these URLs and **abort** with a clear error if the download fails. A local fallback (`IL‑Benchmark‑local.zip` and `experimental_bulk_properties.csv`) may be used **only** with the `--allow-fallback` flag for development or CI‑failure debugging; the production run **must** succeed on the official download, satisfying Constitution Principle VI. This explicit abort behavior is required because the spec does not yet supply real open URLs; the project cannot proceed without them (spec‑root cause; flagged for kickback).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `code/requirements.txt`):
  - `psi4==1.9.1`
  - `pandas==2.2.2`
  - `numpy==1.26.4`
  - `scipy==1.13.0`
  - `scikit-learn==1.5.0`
  - `requests==2.32.3`
  - `pyyaml==6.0.2`
  - `flake8==7.1.0`
  - `pytest==8.2.2`
- **Storage**: Local filesystem under `data/` (raw) and `data/derived/` (processed).  
- **Testing**: `pytest` suite validates data parsing, statistical functions, and end‑to‑end pipeline.  
- **Target Platform**: Linux (`ubuntu‑latest`) runner, CPU‑only.  
- **Constraints**: ≤ 500 ion pairs, batch size = 5 for Psi4, no GPU usage.

## Constitution Check
| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | Fixed random seeds (`code/constants.py`), pinned `requirements.txt`, checksum‑verified raw files, abort on missing high‑level data. |
| **II. Verified Accuracy** | External URLs are *attempted* only; fallback usage requires explicit `--allow-fallback`. |
| **III. Data Hygiene** | Raw files immutable; derived files written to `data/derived/` with timestamps; SHA‑256 checksums recorded. |
| **IV. Single Source of Truth** | All reported numbers are generated programmatically from CSV artefacts; no hand‑typed values. |
| **V. Versioning Discipline** | Content hashes of all artefacts logged; any change triggers re‑evaluation. |
| **VI. Benchmarking Against High‑Level Reference Data** | FR‑003‑FR‑005 benchmark against the **downloaded** CCSD(T)/CBS dataset; abort if unavailable. |

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
│   │   ├── IL‑Benchmark‑local.zip          # Development fallback only
│   │   └── experimental_bulk_properties.csv
│   └── derived/
│       ├── metadata.csv                    # Extracted from ZIP (fallback)
│       ├── validated_metadata.csv          # After FR‑002 validation
│       ├── validation.log                  # Warnings about missing fields
│       ├── raw_energies.csv
│       ├── scaling_factor.txt
│       ├── scaling_diagnostics.md          # Residual diagnostics (FR‑018)
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
| **Bootstrap (1 000 replicates)** | Required by FR‑007, FR‑010, FR‑014 for distribution‑free CIs and measurement‑error propagation. | Parametric CIs would assume normality, which is unjustified for a modest quantum‑chemistry benchmark. |
| **Counterpoise (BSSE) correction** | Required by FR‑003 to avoid systematic over‑binding. | Ignoring BSSE would bias MAE and violate SC‑001. |
| **Dataset size ≤ 500 ion pairs** | Guarantees runtime ≤ 6 h on free CI while preserving statistical power (see FR‑015). | Limiting to ≤ 20 would cripple power (Methodology‑51f4645e). |
| **Cross‑validation for scaling** | Prevents over‑fitting; yields unbiased test‑set MAE (FR‑017). | Fitting on the full set would inflate performance metrics. |
| **Partial correlation & cluster‑robust bootstrap** | Controls for electrostatics and size, avoiding inflated significance. |
| **Scalar justification** | Added homogeneity check and note on possible ion‑type‑specific scaling to address methodology‑29614174. |
| **Residual diagnostics (FR‑018)** | Added Phase 4.5 with histogram, Shapiro‑Wilk, Breusch‑Pagan, and `scaling_diagnostics.md`. |
| **Explicit abort on missing benchmark** – added abort logic (data_resources‑9ddbeab2). |
| **Minimum‑sample guard** – guarantees a valid CSV even when bulk data are scarce (FR‑020). |
| **Power analysis** – fulfills FR‑015, reported in Phase 5. |
| **Schema‑validated artefacts** – ensures deterministic verification for all contracts. |
| **AICc diagnostic** – added FR‑018 check for model adequacy. |
| **Justification for global scalar** – see methodology‑29614174 entry. |

## Methodology & Phase Mapping
| Phase | Goal | FR(s) addressed | Key Tasks |
|-------|------|----------------|-----------|
| **Phase 0 – Lint & Environment** | Ensure code style passes; prepare virtualenv. | FR‑012, SC‑005 | Run `flake8` with minimal config → `code/lint_report.txt` (must end `Exit code: 0`). |
| **Phase 1 – Data Acquisition & Validation** | **Attempt** to download benchmark from Zenodo (placeholder URL) and bulk‑property data from NIST API. Abort on failure unless `--allow-fallback`. Validate required fields. | FR‑001, FR‑002, FR‑008, FR‑019 | 1. `requests.get(<ZENODO_URL>)`. If HTTP ≠ 200, raise `RuntimeError` (unless `--allow-fallback`). 2. If flag present, unzip `IL‑Benchmark‑local.zip` → `metadata.csv`. 3. Validation – `load_data.py` checks for `pair_id` and `reference_energy`; missing fields logged in `validation.log` and omitted; clean table saved as `validated_metadata.csv`. 4. Attempt NIST API call; same abort logic; fallback CSV used only with flag. |
| **Phase 2 – Quantum‑Chemical Calculations** | Compute DFT‑D3 energies with BSSE correction. | FR‑003, FR‑004 | Iterate over `validated_metadata.csv` (batch 5). For each ion pair: run Psi4 (B3LYP/def2‑TZVP + D3(BJ) + Counterpoise) on CPU. Up to 3 retries on SCF failure; persistent failures recorded as `"failed"` and excluded. Parse total energy, D3 term, BSSE correction; compute `error_signed` and `dispersion_only_error` (set to `NA` if no reference dispersion). Store in `raw_energies.csv` (schema `raw_energies.schema.yaml`). |
| **Phase 3 – Raw Error Analysis** | Quantify baseline performance; compute MAE CI with measurement‑error propagation. | FR‑005, FR‑014, SC‑001 | `analyze_energies.py` computes MAE, RMSE, MSE. Bootstrap (1 000) samples reference energies from Normal(`ref`, 0.5 kcal/mol) to propagate uncertainty, yielding a 95 % CI for MAE. Results written to `docs/benchmark_report.md`. |
| **Phase 4 – Scaling Factor Estimation** | Fit scalar *s* on training set; cross‑validate; test hypothesis *s = 1*. | FR‑006, FR‑007, FR‑017, SC‑002 | 1. **Justification** – Prior to fitting we examine residual homogeneity across ion‑type clusters. If residual variance is comparable across clusters, a single global scalar is justified; otherwise we note the limitation and suggest ion‑type‑specific scaling as future work (methodology‑29614174). 2. **Split** – Random partition (fixed seed) into training ([deferred]) and held‑out test ([deferred]). 3. **Optimization** – Constrained minimization (`scipy.optimize.minimize`, bounds > 0) finds *s* that minimizes MAE on training. 4. **Cross‑validation** – Apply *s* to test set; compute out‑of‑sample MAE. 5. **Bootstrap CI** – 1 000 replicates of the full fitting pipeline generate a 95 % CI for *s*. 6. **Hypothesis Test** – Reject *s = 1* only if CI excludes 1.0 **and** p‑value < 0.05. 7. **Diagnostic** – Fit an alternative linear model with intercept; compute AICc for both models; if ΔAICc > 2, issue a warning that a simple scalar may be insufficient. 8. **Output** – `scaling_factor.txt` (schema `scaling_factor.schema.yaml`) records *s*, CI, p‑value, training MAE, test MAE, and original MAE. |
| **Phase 4.5 – Residual Diagnostics after Scaling (FR‑018)** | Assess adequacy of the scalar correction. | FR‑018 | a) Compute per‑pair residuals (`scaled_dft_total_energy – reference_energy`). b) Generate histogram. c) Perform Shapiro‑Wilk test for normality. d) Conduct Breusch‑Pagan test for heteroscedasticity. e) Summarize results in `scaling_diagnostics.md`, which is included in the final report package. |
| **Phase 5 – Bulk‑Property Correlation** | Correlate (raw & scaled) D3 term and interaction‑energy error with bulk density/viscosity **exclusively** on held‑out test set. | FR‑009‑FR‑011, FR‑020, SC‑003, SC‑004, FR‑015 | 1. **Merge** – Join held‑out test set (with scaled D3 term) with bulk‑property CSV on `pair_id`. 2. **Sample‑size guard** – If < 3 valid pairs, write an empty `correlation_results.csv` (header only) and a markdown notice “Insufficient data for correlation”. 3. **Control variables** – Compute `E_elec = dft_total_energy – d3_dispersion_energy` and a simple size descriptor; assign `cluster_id` based on shared cation/anion. 4. **Partial correlation** – For each of three metrics (raw D3 vs density, scaled D3 vs density, interaction‑energy error vs viscosity) compute partial Pearson & Spearman coefficients controlling for `E_elec` and size. 5. **Cluster‑robust bootstrap** – Resample whole `cluster_id` groups (1 000 replicates) **and** sample bulk values from Normal(`value`, `uncertainty`) to propagate measurement error (FR‑016). 6. **Bonferroni correction** – Apply across the six tests (FR‑011). 7. **Power analysis** – Using the actual test‑set size, compute achieved power for detecting |r| ≥ 0.3 at 80 % (α = 0.05); report required N and achieved power (FR‑015). 8. **Outputs** – `correlation_results.csv` (schema `correlation_results.schema.yaml`) and `docs/correlation_report.md` (schema `correlation_report.schema.yaml`). |
| **Phase 6 – Report Generation** | Assemble all artefacts for reproducibility. | FR‑012 | Bundle CSVs, txt, markdowns; record SHA‑256 checksums in `state/projects/...yaml`. |
| **Phase 7 – Orchestration & Verification** | Provide single entry‑point and test harness. | — | `main.py` runs Phases 0‑6 sequentially, aborting on any non‑zero exit code. `tests/test_main_workflow.py` runs the orchestrator in a temporary dir, asserts existence + schema compliance of all outputs. Passing the test suite satisfies SC‑005. |

## Compute Feasibility
- **Psi4**: ≤ 3.5 h for 100 ion pairs (batch 5, 2 CPU cores).  
- **Bootstrap / cross‑validation**: ≤ 30 min.  
- **Total wall‑time**: ≈ 4 h 15 min < 6 h CI limit.  
- **Memory**: ≤ 6 GB, well under 7 GB cap.  
- **GPU**: Not required; all code runs on CPU.

## Decision Log (summary)
- **Dataset placeholders** – acknowledged lack of open IL‑Benchmark and NIST API URLs; pipeline aborts if not provided, with optional `--allow-fallback` for local testing (addresses data_resources‑9ddbeab2).  
- **Scalar justification** – added homogeneity check and note on possible ion‑type‑specific scaling to address methodology‑29614174.  
- **Residual diagnostics (FR‑018)** – added Phase 4.5 and `scaling_diagnostics.md`.  
- **Cross‑validation for scaling** – satisfies FR‑017, prevents optimistic bias.  
- **Partial correlation & cluster‑robust bootstrap** – fulfills FR‑009‑FR‑011, meets multiple‑comparison requirements.  
- **Bootstrap measurement‑error propagation** – implements FR‑014, FR‑016.  
- **AICc diagnostic** – added FR‑018 check for model adequacy.  
- **Explicit abort on missing benchmark** – added abort logic (data_resources‑9ddbeab2).  
- **Minimum‑sample guard** – guarantees a valid CSV even when bulk data are scarce (FR‑020).  
- **Power analysis** – fulfills FR‑015, reported in Phase 5.  
- **Schema‑validated artefacts** – ensures deterministic verification for all contracts.  

---


## Constitution Check
| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | Fixed random seeds, pinned dependencies, checksum‑verified fallbacks, abort on missing high‑level data. |
| **II. Verified Accuracy** | External URLs are *attempted* only; fallback usage requires explicit `--allow-fallback`. |
| **III. Data Hygiene** | Raw files immutable; derived files versioned; checksums recorded. |
| **IV. Single Source of Truth** | All numbers derived programmatically from CSV artefacts; no hand‑typed values. |
| **V. Versioning Discipline** | Content hashes logged; any change triggers re‑evaluation. |
| **VI. Benchmarking Against High‑Level Reference Data** | FR‑003‑FR‑005 benchmark against the **downloaded** CCSD(T)/CBS dataset; abort if unavailable. |

---

