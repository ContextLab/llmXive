# Research: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Scientific Background
DFT‑D* adds an empirical dispersion correction calibrated on neutral organic molecules (e.g., S66). Ionic liquids consist of charged ion‑pair combinations where electrostatics dominate but many‑body dispersion also contributes. This study benchmarks DFT‑D3 against high‑level CCSD(T)/CBS reference interaction energies for a curated set of ion‑pair complexes, derives a pragmatic scalar correction for the D3 term, and investigates whether dispersion‑related quantities correlate with experimentally measured bulk properties (density, viscosity). Correlations are presented as **associational** diagnostics (Constitution Principle VI) and follow rigorous statistical practice (multiple‑testing correction, bootstrap CIs, partial correlations).

## Dataset Strategy

| Dataset | Loader / Source | Variables Used | Notes |
|---------|----------------|----------------|-------|
| **IL‑Benchmark (placeholder)** | Attempt download from Zenodo DOI **(currently unspecified – empty placeholder)**; on failure **raise RuntimeError** unless `--allow-fallback` flag is set. Local fallback archive `data/raw/IL‑Benchmark‑local.zip` contains a minimal CSV with synthetic identifiers (development only). | `pair_id`, `xyz_path`, `reference_energy` | No open source with genuine CCSD(T)/CBS data exists; production run aborts if download fails (see FR‑001, Constitution VI). |
| **Experimental Bulk Properties (placeholder)** | Attempt NIST IL Thermophysical Database API call **(currently unspecified – empty placeholder)**; on failure **raise RuntimeError** unless `--allow-fallback` flag is set. Fallback CSV `data/raw/experimental_bulk_properties.csv` contains a subset of published bulk values (development only). | `pair_id`, `density`, `viscosity` | Same limitation as above; abort on failure (FR‑008). |

### Dataset Variable Fit
All required variables are present **in the fallback files** (pair identifier, reference energy, XYZ path, density, viscosity). The validation step (FR‑002) will drop any record missing `pair_id` or `reference_energy`. Bulk‑property gaps lead to exclusion from correlation (edge‑case handling). Because the fallback data are synthetic, the final report will clearly flag that the benchmark was performed on placeholder data; no scientific conclusions about real ionic liquids can be drawn until an open dataset becomes available.

## Methodology

### Phase 0 – Lint & Environment
Run `flake8` with minimal config (`.flake8`). Output → `code/lint_report.txt`; must end `Exit code: 0`. Failure aborts the pipeline (FR‑012, SC‑005).

### Phase 1 – Benchmark DFT‑D3 Interaction Energies (US‑1)
1. **Download attempt** – `requests.get(<ZENODO_URL>)`. If HTTP ≠ 200, raise `RuntimeError` (unless `--allow-fallback`).  
2. **Fallback** – If flag present, unzip `IL‑Benchmark‑local.zip` → `metadata.csv`.  
3. **Validation** – `load_data.py` checks for `pair_id` and `reference_energy`; missing fields logged in `validation.log` and omitted; clean table saved as `validated_metadata.csv`.  
4. **Psi4 calculations** – `run_psi4.py` processes the validated list in batches of 5, performing single‑point B3LYP/def2‑TZVP + D3(BJ) + Counterpoise on CPU. Up to 3 retries on SCF failure; persistent failures recorded as `"failed"` and excluded. Extract total energy, D3 contribution, BSSE correction; compute `error_signed` and `dispersion_only_error` (set to `NA` if no reference dispersion). Store in `raw_energies.csv` (schema `raw_energies.schema.yaml`). |
| **Outputs** | `raw_energies.csv`, `validation.log`, `validated_metadata.csv`. |

### Phase 2 – Raw Error Analysis (FR‑005, FR‑014, SC‑001)
`analyze_energies.py` computes MAE, RMSE, and mean signed error (MSE) between DFT‑D3 totals and reference energies. A bootstrap (1 000 replicates) samples reference energies from Normal(`ref`, 0.5 kcal/mol) to propagate measurement uncertainty, yielding a 95 % CI for MAE. Results written to `docs/benchmark_report.md`.

### Phase 3 – Scaling Factor Estimation (US‑2, FR‑006, FR‑007, SC‑002)
1. **Justification** – Prior to fitting we examine residual homogeneity across ion‑type clusters. If residual variance is comparable across clusters, a single global scalar is justified; otherwise we note the limitation and suggest ion‑type‑specific scaling as future work (methodology‑29614174).  
2. **Split** – Randomly partition the validated set (fixed seed) into training ([deferred]) and held‑out test ([deferred]).  
3. **Optimization** – Constrained minimization (`scipy.optimize.minimize`, bounds > 0) finds scalar *s* that minimizes MAE on the training set.  
4. **Cross‑validation** – Apply *s* to the test set; compute out‑of‑sample MAE.  
5. **Bootstrap CI** – 1 000 replicates of the full fitting pipeline generate a 95 % CI for *s*.  
6. **Hypothesis Test** – Reject *s = 1* only if the CI excludes 1.0 **and** the two‑sided p‑value < 0.05.  
7. **Diagnostic** – Fit an alternative linear model with intercept; compute AICc for both models; if ΔAICc > 2, issue a warning that a simple scalar may be insufficient.  
8. **Output** – `scaling_factor.txt` (schema `scaling_factor.schema.yaml`) records *s*, CI, p‑value, training MAE, test MAE, and original MAE. |

### Phase 4 – Bulk‑Property Correlation (US‑3)
1. **Merge** – Join held‑out test set (with scaled D3 term) with bulk‑property CSV on `pair_id`.  
2. **Sample‑size guard** – If < 3 valid pairs, write an empty `correlation_results.csv` (header only) and a markdown notice “Insufficient data for correlation”.  
3. **Control variables** – Compute `E_elec = dft_total_energy – d3_dispersion_energy` and a simple size descriptor; assign `cluster_id` based on shared cation/anion.  
4. **Partial correlation** – For each of three metrics (raw D3 vs density, scaled D3 vs density, interaction‑energy error vs viscosity) compute partial Pearson and partial Spearman coefficients controlling for `E_elec` and size.  
5. **Cluster‑robust bootstrap** – Resample whole `cluster_id` groups (1 000 replicates) **and** sample bulk values from Normal(`value`, `uncertainty`) to propagate measurement error (FR‑016).  
6. **Bonferroni correction** – Apply across the six tests (FR‑011).  
7. **Power analysis** – Using the actual test‑set size, compute achieved power for detecting |r| ≥ 0.3 at 80 % (α = 0.05); report required N and achieved power (FR‑015).  
8. **Outputs** – `correlation_results.csv` (schema `correlation_results.schema.yaml`) and `docs/correlation_report.md` (schema `correlation_report.schema.yaml`) containing coefficients, R², raw & adjusted p‑values, CI, sample size, significance flag, and power analysis.  
9. **Interpretation Caveat** – Correlations are exploratory diagnostics; bulk properties emerge from many‑body effects, so any association is reported as *associational* only (Constitution VI).

### Phase 5 – Report Generation (FR‑012)
`generate_reports.py` bundles all derived artefacts, writes human‑readable markdown summaries, and records SHA‑256 checksums for each file in `state/projects/...yaml`.

### Phase 6 – Orchestration & Verification (T067)
`main.py` runs Phases 0‑5 sequentially, aborting on any non‑zero exit code. `tests/test_main_workflow.py` executes the orchestrator in a temporary directory and asserts existence + schema compliance of all outputs. Passing the test suite satisfies SC‑005.

## Statistical Rigor & Limitations
- **Multiple Comparisons** – Bonferroni correction (FR‑011).  
- **Power** – With up to 100 ion pairs, a two‑tailed test can detect |r|≈0.30 at 80 % power (α = 0.05); reported in Phase 4.  
- **Observational Nature** – Correlations are reported as associations only; no causal claims (Constitution VI).  
- **Collinearity** – Partial correlation controls for electrostatic energy and size, mitigating inflated significance.  
- **Measurement Uncertainty** – Bootstrap resampling incorporates ±0.5 kcal/mol uncertainty on reference energies and reported bulk‑property uncertainties (FR‑016).  
- **Scaling Diagnostics** – AICc comparison guards against over‑simplistic scalar correction (FR‑018).  

---


## Compute Feasibility
- **Psi4**: ≤ 3.5 h for ≤ 100 ion pairs (batch 5, 2 CPU cores).  
- **Bootstrap / cross‑validation**: ≤ 30 min.  
- **Total**: ≈ 4 h 15 min < 6 h limit.  
- **Memory**: ≤ 6 GB RAM.  

---


## Constitution Check
| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | Fixed seeds, pinned dependencies, checksum‑verified fallbacks, abort on missing high‑level data. |
| **II. Verified Accuracy** | External URLs are *attempted* only; fallback usage requires explicit `--allow-fallback`. |
| **III. Data Hygiene** | Raw files immutable; derived files versioned; checksums recorded. |
| **IV. Single Source of Truth** | All numbers derived programmatically from CSV artefacts; no hand‑typed values. |
| **V. Versioning Discipline** | Content hashes logged; any change triggers re‑evaluation. |
| **VI. Benchmarking Against High‑Level Reference Data** | FR‑003‑FR‑005 benchmark against the **downloaded** CCSD(T)/CBS dataset; abort if unavailable. |

---


