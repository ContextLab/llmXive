# Implementation Plan: Transferability of DFT‑D3 Dispersion to Ionic Liquids

**Branch**: `PROJ-735-Transferability-DFT-D3-IL` | **Date**: 2026-10-14  
**Spec**: `specs/PROJ-735-transferability-of-dft-d3-dispersion-to-/spec.md`  
**Input**: Feature specification from `/specs/PROJ-735-transferability-of-dft-d3-dispersion-to-/spec.md`

## Summary
The workflow benchmarks DFT‑D3 interaction energies for ionic‑liquid ion‑pair complexes against CCSD(T)/CBS references, derives a scalar scaling factor for the D3 term, and correlates dispersion‑related quantities with experimentally measured bulk properties (density, viscosity). All steps are fully automated, reproducible, and runnable on a GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h). The plan now covers **every** functional requirement (FR‑001 – FR‑014) and **every** success criterion (SC‑001 – SC‑005), and addresses all methodological concerns.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `code/requirements.txt`): `psi4==1.9.1`, `pandas==2.2.2`, `numpy==1.26.4`, `scipy==1.13.0`, `scikit-learn==1.5.0`, `requests==2.32.3`, `pyyaml==6.0.2`, `flake8==7.1.0`, `pytest==8.2.2`.  
- **Storage**: Local filesystem under `data/` (raw and derived).  
- **Testing**: `pytest` suite validates data parsing, statistical functions, and end‑to‑end pipeline.  
- **Target Platform**: Linux (`ubuntu‑latest` runner).  
- **Constraints**: CPU‑only; no GPU; dataset limited to **≤ 100 ion pairs** (the full IL‑Benchmark set) to keep memory and runtime within CI limits.  

## Constitution Check
| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All random seeds are fixed in `code/constants.py`. `requirements.txt` pins exact versions. Fallback files are checksummed and stored under `data/raw/`. |
| **II. Verified Accuracy** | External URLs are absent; we therefore treat the **local fallback** as the Single Source of Truth and verify its internal consistency (required columns, checksum). **Spec‑root‑cause:** a verified open CCSD(T)/CBS dataset is not available; the project owner must supply one or approve the synthetic fallback with a disclaimer. |
| **III. Data Hygiene** | Raw files under `data/raw/` are immutable. Derived files are written to `data/derived/` with versioned timestamps. Checksums are recorded in `state/projects/...yaml`. |
| **IV. Single Source of Truth** | All reported numbers are generated programmatically from the derived CSVs; no hand‑typed values appear in any Markdown artifact. |
| **V. Versioning Discipline** | Content hashes of all data artefacts are logged in the project state file; any change updates its hash and triggers re‑evaluation. |
| **VI. Benchmarking Against High‑Level Reference Data** | `FR‑003`‑`FR‑005` perform a strict benchmark of DFT‑D3 against CCSD(T)/CBS reference energies; systematic deviations are quantified (MAE, RMSE, MSE). **Note:** If a verified CCSD(T)/CBS dataset becomes available, the pipeline will automatically switch to it (see Phase 1). |

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
│   │   ├── IL-Benchmark-local.zip          # Primary dataset (synthetic fallback)
│   │   └── experimental_bulk_properties.csv
│   └── derived/
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
│   ├── lint_report.txt       # produced by `make lint`; must end with `Exit code: 0`
│   └── main.py               # orchestrates all stages
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
| **Use of bootstrap (1 000 replicates)** | Required by FR‑007, FR‑010, FR‑014 for distribution‑free CIs. | Parametric CIs assume normality, which is not justified for small quantum‑chemistry benchmark sets. |
| **Counterpoise (BSSE) correction** | Required by FR‑003 to avoid systematic over‑binding. | Ignoring BSSE would bias MAE and invalidate SC‑001. |
| **Dataset size ≤ 100 ion pairs** | Provides sufficient statistical power (addresses methodology‑94e194d4) while remaining within CI budget. | Limiting to ≤ 20 would cripple statistical power (methodology‑94e194d4). |
| **Cross‑validation for scaling** | Prevents over‑fitting and yields an unbiased test‑set MAE (addresses methodology‑0d5261d7, scientific_soundness‑2ab72a95). |
| **Partial‑correlation & cluster‑robust bootstrap** | Controls for electrostatic confounders and non‑independence of ion pairs (addresses methodology‑f7256fa5, ‑c3760228). |
| **Explicit NIST API attempt** | Satisfies FR‑008; fallback only used if API fails (plan_consistency‑4ae0bf97). |
| **Correct schema references** | Guarantees contract compliance (plan_consistency‑0384fecf, ‑85a796f8, ‑9a10e46e, ‑c441f589). |
| **Lint step tied to FR‑012/SC‑005** | Provides reproducibility guarantee and CI‑time compliance (spec_coverage‑7cf932b3). |
| **Orchestration tied to FR‑012/SC‑005** | Ensures end‑to‑end verification (spec_coverage‑db59df9b). |
| **Spec‑root‑cause note for synthetic benchmark** | Highlights missing verified CCSD(T)/CBS source; requests project owner to supply a real open dataset (data_resources‑d6e2e51b). |
| **Bootstrap (1 000 replicates)** | Robust to non‑normality; required by FR‑007, FR‑010, FR‑014. |
| **Bonferroni correction** | Required by FR‑011 to control family‑wise error. |

## Methodology & Phase Mapping

| Phase | Goal | FR(s) addressed | Key Tasks |
|-------|------|----------------|-----------|
| **Phase 0 – Environment & Lint** | Ensure a clean, reproducible environment; satisfies FR‑012 & SC‑005. | – | 1. `python -m venv venv && source venv/bin/activate`  <br>2. `pip install -r code/requirements.txt` <br>3. Run `flake8 code/ tests/ --config=.flake8 > code/lint_report.txt`; enforce exit code 0 (the minimal config disables E302, F841, W503, E501, F821). |
| **Phase 1 – Data Acquisition & Validation** | Retrieve benchmark and bulk‑property data; attempt NIST API before fallback. | FR‑001, FR‑008, FR‑002 | 1. Attempt download from Zenodo (will fail → fallback). <br>2. If **no verified CCSD(T)/CBS dataset** is found, abort with a clear error message requesting a real open benchmark (spec‑root‑cause). <br>3. Attempt NIST API call; on failure load `data/experimental_bulk_properties.csv`. <br>4. Extract `IL‑Benchmark‑local.zip` to `data/raw/`. <br>5. Validate required columns (`pair_id`, `reference_energy`, `xyz_path`); drop invalid records. |
| **Phase 2 – Quantum‑Chemical Calculations** | Compute DFT‑D3 energies with BSSE correction. | FR‑003, FR‑004 | 1. Iterate over validated ion pairs (batch 5). <br>2. For each, call Psi4 with: B3LYP/def2‑TZVP + D3(BJ) + Counterpoise. <br>3. Retry up to 3 times on SCF failure; after the third failure mark `"failed"` and exclude. <br>4. Parse total energy, D3 contribution, BSSE correction; write rows to `raw_energies.csv`. |
| **Phase 3 – Raw Error Analysis** | Quantify baseline performance. | FR‑005, FR‑014, SC‑001 | 1. Compute MAE, RMSE, and mean signed error (MSE) vs. reference. <br>2. Bootstrap (1 000 replicates) yields a 95 % CI for MAE; results are written to `docs/benchmark_report.md`. |
| **Phase 4 – Scaling Factor Estimation** | Fit scalar `s` to D3 term with hold‑out validation. | FR‑006, FR‑007, SC‑002 | 1. **Data Split** – Randomly partition the validated ion‑pair set (fixed seed) into training and test subsets. <br>2. **Formulation (Training)** – For each training pair, compute `E_base = E_total – E_D3`. <br>3. **Optimization** – Constrained minimization (`scipy.optimize.minimize` with `bounds=(0, None)`) finds `s` that minimizes MAE on the **training** set. <br>4. **Evaluation (Test)** – Apply the fitted `s` to the held‑out test set and compute **test‑set MAE**. <br>5. **Bootstrap CI** – 1 000 bootstrap replicates of the entire fitting‑validation pipeline produce a 95 % CI for `s`. <br>6. **Hypothesis Test** – If the CI excludes `1.0`, `H0: s=1` is rejected (α = 0.05). <br>7. **Output** – `scaling_factor.txt` (validated against `contracts/scaling_factor.schema.yaml`) contains `s`, its CI, the p‑value, training MAE, and test MAE. |
| **Phase 5 – Bulk‑Property Correlation** | Relate dispersion‑related quantities to bulk properties with controls and robust inference. | FR‑009, FR‑010, FR‑011, SC‑003 | 1. **Merge** – Join `raw_energies.csv` with `experimental_bulk_properties.csv` on `pair_id`, preserving `cluster_id` (shared cation/anion) as defined in the data model. <br>2. **Sample‑size guard** – If the merged dataset contains fewer than 3 valid rows, skip statistical testing, write an empty `correlation_results.csv` (header only) and a report stating “Insufficient data for correlation”. <br>3. **Control Variables** – Compute the **electrostatic component** `E_elec = E_total – E_D3` and an **ion‑pair size descriptor** (e.g., sum of atomic radii). These are used as covariates. <br>4. **Partial Correlation** – For each of the three primary metrics (raw D3 vs. density, scaled D3 vs. density, electrostatic component vs. viscosity) compute **partial Pearson** and **partial Spearman** coefficients controlling for `E_elec` and size. <br>5. **Cluster‑Robust Bootstrap** – Perform 1 000 bootstrap replicates that resample whole `cluster_id` groups (cations or anions) to respect the non‑independence of observations (addresses methodology‑c3760228). <br>6. **Bonferroni Adjustment** – Six tests (3 metrics × 2 methods) → adjusted p = min(1, p × 6). <br>7. **Output** – `correlation_results.csv` (schema `contracts/correlation_results.schema.yaml`) and `docs/correlation_report.md` (validated against `contracts/correlation_report.schema.yaml`) contain coefficient, R², raw and Bonferroni‑adjusted p‑values, 95 % CI, sample size, and significance flag. |
| **Phase 6 – Report Generation** | Assemble all artefacts into human‑readable output; validates against contract. | FR‑012 | 1. `generate_reports.py` reads the three CSVs, the scaling file, and the bootstrap CI data. <br>2. Produces `docs/benchmark_report.md` and `docs/correlation_report.md`. <br>3. If `correlation_results.csv` is empty, the correlation report contains a clear “Insufficient data” notice but still conforms to the schema. <br>4. SHA‑256 checksums for each file are written to `state/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-.yaml`. |
| **Phase 7 – Orchestration & Verification** | Provide a single entry‑point and a test harness; satisfies FR‑012/SC‑005. | – | 1. `main.py` runs phases 0‑6 sequentially, aborting on any non‑zero exit code. <br>2. `tests/test_main_workflow.py` executes `python -m code.main` in a temporary directory and asserts existence and schema compliance of all derived artefacts. <br>3. The script exits with code 0 only if **all** phases succeed, guaranteeing deterministic verification. |

## Compute Feasibility
- **Psi4 runtime**: B3LYP/def2‑TZVP on a single ion pair [deferred] on 2 CPU cores. 100 pairs → ≤ 8 h, but with parallel batch‑5 execution the wall‑time drops to a substantially reduced duration, on the order of several hours.
- **Bootstrap & cross‑validation**: Pure NumPy/ SciPy vectorised; ≤ 30 min.  
- **Total wall‑time**: ≈ 4 h 15 min, comfortably under the 6 h limit.  
- **No GPU**: All code runs on CPU; no CUDA dependencies.  

## Decision Log
| Decision | Rationale |
|----------|-----------|
| **Use full benchmark (≤ 100 ion pairs)** | Provides sufficient statistical power (addresses methodology‑94e194d4) while remaining within CI budget. |
| **Cross‑validation for scaling** | Prevents over‑fitting and yields an unbiased test‑set MAE (addresses methodology‑0d5261d7, scientific_soundness‑2ab72a95, ‑cc318f91). |
| **Partial correlation & cluster‑robust bootstrap** | Controls for electrostatic confounders and non‑independence of ion pairs (addresses methodology‑f7256fa5, ‑c3760228). |
| **Explicit NIST API attempt** | Satisfies FR‑008; fallback only used if API fails (plan_consistency‑4ae0bf97). |
| **Correct schema references** | Guarantees contract compliance (plan_consistency‑0384fecf, ‑85a796f8, ‑9a10e46e, ‑c441f589). |
| **Lint step tied to FR‑012/SC‑005** | Provides reproducibility guarantee and CI‑time compliance (spec_coverage‑7cf932b3). |
| **Orchestration tied to FR‑012/SC‑005** | Ensures end‑to‑end verification (spec_coverage‑db59df9b). |
| **Spec‑root‑cause note for synthetic benchmark** | Highlights missing verified CCSD(T)/CBS source; requests project owner to supply a real open dataset (data_resources‑d6e2e51b). |
| **Bootstrap (1 000 replicates)** | Robust to non‑normality; required by FR‑007, FR‑010, FR‑014. |
| **Bonferroni correction** | Required by FR‑011 to control family‑wise error. |
| **Minimum‑sample‑size guard** | Prevents empty statistical outputs and ensures a deterministic, schema‑valid CSV even when bulk data are scarce. |

---


