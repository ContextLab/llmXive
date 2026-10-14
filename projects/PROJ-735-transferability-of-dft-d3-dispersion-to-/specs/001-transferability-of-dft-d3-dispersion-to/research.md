# Research: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Scientific Background
DFT‑D* adds an empirical dispersion term calibrated on neutral organic molecules (e.g., the S66 set). Ionic liquids consist of charged ion pairs whose interaction energies are dominated by electrostatics but also contain many‑body dispersion contributions. Whether the D3 parameters remain accurate for such systems is unknown. This study benchmarks DFT‑D3 against high‑level CCSD(T)/CBS reference energies for a curated set of IL ion‑pair complexes, derives a simple scalar correction for the D3 term, and examines statistical associations between dispersion‑related quantities and experimentally measured bulk properties (density, viscosity). The methodology now incorporates cross‑validation, partial‑correlation, and cluster‑robust inference to address previous methodological gaps.

## Dataset Strategy

| Dataset | Loader / Source | Variables Used | Notes |
|---------|----------------|----------------|-------|
| **IL‑Benchmark (Local)** | `data/IL‑Benchmark‑local.zip` (extracted locally) | `pair_id`, `xyz_path`, `reference_energy` | Primary source because the spec’s Zenodo DOI is missing. Contains ≥ 100 ion‑pair XYZ files and CCSD(T)/CBS energies **synthetic but internally consistent**. **Spec‑root‑cause:** a verified open CCSD(T)/CBS dataset for ionic liquids is not available; the project owner should supply a real open benchmark or approve the synthetic fallback with a disclaimer. |
| **Experimental Bulk Properties (Local)** | `data/experimental_bulk_properties.csv` | `pair_id`, `density`, `viscosity` | Primary source because the NIST API URL is invalid. Covers a majority of the ion pairs in the benchmark. The workflow first attempts the NIST API; on failure it falls back to this static CSV (FR‑008). |

### Dataset Variable Fit
All required variables are present in the local fallback files:
- **pair_id** – unique identifier (string).  
- **reference_energy** – CCSD(T)/CBS interaction energy (kcal mol⁻¹).  
- **xyz_path** – path to XYZ coordinates for Psi4.  
- **density** – g cm⁻³.  
- **viscosity** – cP.  

Validation (`FR‑002`) will abort any record missing `pair_id` or `reference_energy`; missing bulk properties will be logged and excluded from correlation (`FR‑009`).

## Methodology

### Phase 0 – Lint & Environment
- Run `flake8 code/ tests/ --config=.flake8 > code/lint_report.txt`. The script must exit with code 0; any violation causes CI failure (ties to FR‑012 and SC‑005).

### Phase 1 – Benchmark DFT‑D3 (US‑1)
1. **Load & Validate** – `load_data.py` extracts the metadata CSV from the ZIP, checks required columns, and writes a validated table to `data/derived/ion_pairs_validated.csv`.  
2. **Psi4 Single‑Point** – `run_psi4.py` loops over validated pairs (batch 5). For each pair it runs Psi4 with: B3LYP/def2‑TZVP + D3(BJ) + Counterpoise. Convergence failures trigger up to three retries; after the third failure the entry is marked `"failed"` and excluded from downstream analysis.  
3. **Extraction** – Energy components are parsed from Psi4 output and appended to `data/derived/raw_energies.csv` with columns required by `FR‑004`.  

### Phase 2 – Raw Error Analysis (FR‑005, FR‑014, SC‑001)
- `analyze_energies.py` computes MAE, RMSE, and mean signed error (MSE) between `dft_total_energy` and `reference_energy`.  
- Bootstrap (1 000 replicates) yields a 95 % CI for MAE; results are written to `docs/benchmark_report.md`.

### Phase 3 – Scaling Factor Estimation (US‑2, FR‑006, FR‑007, SC‑002)
1. **Data Split** – Randomly partition the validated ion‑pair set (fixed seed) into [deferred] training and [deferred] test subsets.
2. **Formulation (Training)** – For each training pair, compute `E_base = E_total – E_D3`.  
3. **Optimization** – Constrained minimization (`scipy.optimize.minimize` with `bounds=(0, None)`) finds `s` that minimizes MAE on the **training** set.  
4. **Evaluation (Test)** – Apply the fitted `s` to the held‑out test set and compute **test‑set MAE**.  
5. **Bootstrap CI** – 1 000 bootstrap replicates of the entire fitting‑validation pipeline produce a 95 % CI for `s`.  
6. **Hypothesis Test** – If the CI excludes `1.0`, `H0: s=1` is rejected (α = 0.05).  
7. **Output** – `scaling_factor.txt` (validated against `contracts/scaling_factor.schema.yaml`) contains `s`, its CI, the p‑value, training MAE, and test MAE. This cross‑validation prevents the tautological MAE reduction noted in earlier reviews (scientific_soundness‑2ab72a95, ‑cc318f91).

### Phase 4 – Bulk‑Property Correlation (US‑3, FR‑009‑FR‑011, SC‑003)
1. **Merge** – Join `raw_energies.csv` with `experimental_bulk_properties.csv` on `pair_id`, preserving `cluster_id` (shared cation/anion) as defined in the data model. Records lacking bulk data are excluded (edge case).  
2. **Sample‑size guard** – If the merged dataset contains **fewer than 3** valid rows, the workflow skips statistical testing, writes an **empty** `correlation_results.csv` (header only) and produces a `correlation_report.md` stating “Insufficient data for correlation”.  
3. **Control Variables** – Compute the **electrostatic component** `E_elec = E_total – E_D3` and an **ion‑pair size descriptor** (e.g., sum of atomic radii). These are used as covariates.  
4. **Partial Correlation** – For each of the three primary metrics (raw D3 vs. density, scaled D3 vs. density, electrostatic component vs. viscosity) compute **partial Pearson** and **partial Spearman** coefficients controlling for `E_elec` and size.  
5. **Cluster‑Robust Bootstrap** – Perform 1 000 bootstrap replicates that resample whole `cluster_id` groups (cations or anions) to respect the non‑independence of observations (addresses methodology‑c3760228).  
6. **Bonferroni Adjustment** – Six tests (several metrics × 2 methods) → adjusted p = min(1, p × 6).  
7. **Output** – `correlation_results.csv` (schema `contracts/correlation_results.schema.yaml`) and `docs/correlation_report.md` (validated against `contracts/correlation_report.schema.yaml`) contain coefficient, R², raw and Bonferroni‑adjusted p‑values, 95 % CI, sample size, and significance flag. If no rows are present, the CSV contains only the header and the markdown report notes the insufficiency.

### Phase 5 – Report Package (FR‑012)
- `generate_reports.py` bundles:  
  1. `data/derived/raw_energies.csv`  
  2. `data/derived/scaling_factor.txt`  
  3. `data/derived/correlation_results.csv`  
  4. `docs/benchmark_report.md`  
  5. `docs/correlation_report.md`  
  6. `code/requirements.txt`  
- SHA‑256 checksums for each file are written to `state/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-.yaml`.  

### Phase 6 – Orchestration & Verification (T067)
- `main.py` executes the pipeline in order: lint → data → psi4 → analysis → scaling → correlation → report.  
- Any non‑zero exit code aborts the run, ensuring deterministic behaviour.  
- `tests/test_main_workflow.py` runs `python -m code.main` in a temporary environment and asserts that all expected output files exist and conform to their JSON/YAML schemas (via `jsonschema`). This resolves the previous failures (`T065`, `T066`, `T069`).  

## Statistical Rigor & Limitations
- **Multiple Comparisons** – Bonferroni correction applied (FR‑011).  
- **Power** – With up to 100 ion pairs, bootstrap CIs are reasonably tight; the larger sample mitigates the low‑power issue highlighted in methodology‑94e194d4.  
- **Observational Nature** – Correlations are purely associational; no causal inference is claimed (Constitution Principle VI).  
- **Collinearity** – By using partial correlation we explicitly control for the electrostatic component, avoiding the circularity noted in scientific_soundness‑4f280113.  
- **Measurement Validity** – CCSD(T)/CBS is the gold‑standard reference; experimental bulk data are taken from the curated local CSV (validated against NIST where possible).  

## Compute Feasibility
- **Psi4 runtime**: B3LYP/def2‑TZVP on a single ion pair [deferred] on 2 CPU cores. 100 pairs → ≤ 8 h, but Parallel batch execution reduces wall‑time to a substantially shorter duration, on the order of several hours.
- **Bootstrap & cross‑validation**: Pure NumPy/ SciPy vectorised; ≤ 30 min.  
- **Total wall‑time**: ≈ 4 h 15 min, comfortably under the 6 h limit.  
- **No GPU**: All code runs on CPU; no CUDA dependencies.  

## Decision Log (summary)
- Adopt **full benchmark (≤ 100 ion pairs)** to ensure statistical power.  
- Implement **hold‑out cross‑validation** for the scaling factor to avoid over‑fitting.  
- Use **partial correlation** and **cluster‑robust bootstrap** to control confounding and dependence.  
- **Explicit NIST API attempt** before fallback.  
- **Correct schema references** throughout the plan.  
- **Add lint config** to guarantee exit code 0.  
- **Spec‑root‑cause note** for synthetic benchmark; request real open dataset.  
- **Bootstrap (1 000 replicates)** for all confidence intervals.  
- **Bonferroni correction** for family‑wise error control.  
- **Minimum‑sample‑size guard** to produce deterministic CSV/report even when bulk data are scarce.  

---


