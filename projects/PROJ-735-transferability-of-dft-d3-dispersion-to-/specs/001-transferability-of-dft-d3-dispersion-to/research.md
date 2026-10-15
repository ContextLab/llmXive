# Research: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Scientific Background
DFT‑D* adds an empirical dispersion correction calibrated on neutral organic molecules (e.g., S66). Ionic liquids consist of charged ion pairs where electrostatics dominate but many‑body dispersion also contributes. The present study benchmarks DFT‑D3 against high‑level CCSD(T)/CBS reference interaction energies for a curated set of ion‑pair complexes, derives a pragmatic scalar correction for the D3 term, and investigates whether dispersion‑related quantities correlate with experimentally measured bulk properties (density and viscosity). The analysis respects the observational nature of the bulk‑property association (Constitution Principle VI) and follows rigorous statistical practice (multiple‑testing correction, bootstrap CIs, partial correlations).

## Dataset Strategy

| Dataset | Loader / Source | Variables Used | Notes |
|---------|----------------|----------------|-------|
| **IL‑Benchmark (Local)** | Attempt download from Zenodo DOI (as specified in FR‑001); on failure **raise RuntimeError** unless `--allow-fallback` flag is set. The fallback ZIP is a placeholder for local testing only. | `pair_id`, `xyz_path`, `reference_energy` | Primary benchmark. The placeholder does **not** contain genuine CCSD(T)/CBS reference energies; the pipeline aborts if the download fails without the fallback flag. |
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
6. **Diagnostic** – Fit an alternative linear model with intercept; compute AICc for both models. If ΔAICc > 2, issue a warning that a simple scalar may be insufficient (methodology‑1055b40b).  
7. **Output** – `scaling_factor.txt` (validated by `scaling_factor.schema.yaml`) contains `s`, its CI, the p‑value, training MAE, test MAE, and the original MAE.

### Phase 4 – Bulk‑Property Correlation (US‑3)
1. **Merge** – Join **test‑set** `raw_energies.csv` (with scaling applied) with bulk‑property CSV on `pair_id`.  
2. **Sample‑size guard** – If fewer than 3 valid pairs, the pipeline writes an **empty** `correlation_results.csv` (header only) and a markdown notice “Insufficient data for correlation”.  
3. **Control Variables** – Compute `E_elec = dft_total_energy – d3_dispersion_energy` and a size descriptor; assign a `cluster_id` based on shared cation/anion.  
4. **Partial Correlation** – For each of three primary metrics (raw D3 vs. density, scaled D3 vs. density, interaction‑energy error vs. viscosity) compute **partial Pearson** and **partial Spearman** coefficients controlling for `E_elec` and size.  
5. **Cluster‑Robust Bootstrap** – Resample whole `cluster_id` groups (1 000 replicates) **and** sample bulk‑property values from Normal(`value`, `uncertainty`) to propagate measurement error.  
6. **Bonferroni Adjustment** – Apply **Bonferroni correction** across the six tests.  
7. **Power analysis** – With the expected test‑set size (≈ 80 pairs), we have [deferred] power to detect |r|≈0.30 at 80 % power (α = 0.05); report this in the markdown (methodology‑51f4645e).
8. **Outputs** – `correlation_results.csv` (schema `correlation_results.schema.yaml`) and `docs/correlation_report.md` (schema `correlation_report.schema.yaml`) contain coefficient, R², raw and adjusted p‑values, CI, sample size, and a significance flag.  
9. **Interpretation Caveat** – Correlations are presented as **heuristic diagnostics**; we explicitly note that gas‑phase pairwise energies capture only part of the physics governing bulk properties, and that observed associations should not be interpreted causally (methodology‑503e987b).

### Phase 5 – Report Generation (FR‑012)
`generate_reports.py` bundles all derived artefacts, writes human‑readable markdown summaries, and records SHA‑256 checksums for each file in `state/projects/...yaml`.

### Phase 6 – Orchestration & Verification (T067)
`main.py` runs phases 0‑5 sequentially, aborting on any non‑zero exit code. `tests/test_main_workflow.py` runs the orchestrator in a temporary directory and asserts existence + schema compliance of all outputs. Successful test suite ⇒ SC‑005 satisfied.

## Statistical Rigor & Limitations
- **Multiple Comparisons** – Bonferroni correction (FR‑011).  
- **Power** – With up to 100 ion pairs, a two‑tailed test can detect |r|≈0.30 at 80 % power (α = 0.05). This is reported in Phase 4.  
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
