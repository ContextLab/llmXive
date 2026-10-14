# Tasks: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

**Input**: Design documents from `specs/001-assessing-the-validity-of-statistical-si/` (spec.md, plan.md, data-model.md, contracts/)
**Re-plan note**: This revision consolidates the prior task list into substantive, deterministically verifiable research tasks. Previously verified work (simulation engine, analysis methods, aggregation logic, and their passing tests) is preserved as checked. Tasks rejected for missing artifacts are folded into the consolidated tasks below, each naming a concrete file artifact on disk. Non‑substantive tasks (linting config, empty directory creation, contract re‑creation) are dropped as platform‑provided or already satisfied; their scientific content is absorbed where required.

## Path Conventions

All paths are relative to the project directory. Source in `code/`, tests in `code/tests/`, results in `data/processed/` and `data/results/`. Contracts under `specs/001-assessing-the-validity-of-statistical-si/contracts/` are read‑only inputs.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T101 Establish the real data‑loading and configuration foundation. Create `code/data_loader.py` that **downloads the following public RCT datasets from OpenML using the exact IDs**:
  * **42803** – treatment column `treat`, outcome column `outcome`, covariates `age`, `sex`.
  * **43844** – treatment column `treatment`, outcome column `outcome`, covariates `cov1`, `cov2`.
  * **43845** – treatment column `treatment`, outcome column `outcome`, covariates `age`, `gender`.

  The loader verifies each dataset contains a treatment column, an outcome column, and at least two covariates; **skips datasets with N < 100**, logs the skip, and records SHA256 checksums in `data/checksums/manifest.json`. It **must fail loudly** on any fetch error (no synthetic fallback).  

  **MNAR edge‑case handling**: if a dataset’s outcome variable is fully observed and MNAR cannot be simulated, the loader generates synthetic outcome values that preserve a correlation of **r ≈ 0.3 ± 0.05** with the covariates before missingness simulation, and logs this action. This behavior is documented here and flagged for spec clarification.  

  **Verification**: both `code/data_loader.py` and `code/config.py` exist; running `python -c "from code.data_loader import load_datasets; from code.config import load_config"` succeeds; a fetch failure raises an exception; `data/checksums/manifest.json` is created; synthetic‑outcome generation is recorded in logs.

- [ ] T102 Run a thin end‑to‑end analysis on real inputs. Implement **`code/main_us1.py`** (deterministic path) that executes ONE condition: <!-- FAILED-IN-EXECUTION: code/main_us1.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main_us1.py exit=1 -->
  * Dataset ID **42803**
  * Missingness mechanism **MAR** at **20 %** missingness (dependent on observed covariate `age`)
  * Treatment labels **permuted** to enforce a true null hypothesis
  * **500 Monte Carlo iterations**
  * Analysis method **Complete‑Case (CC)** only  

  The script writes results conforming to `specs/001-assessing-the-validity-of-statistical-si/contracts/p_value_distribution.schema.yaml` and `error_metric.schema.yaml` to `data/processed/us1_results.json`. Metadata includes the iteration count.  

  **Verification**: executing the script produces exactly 500 p‑values, an empirical error‑rate field, and the iteration count is recorded in the output JSON.

- [ ] T103 Write the focused correctness tests. Add `code/tests/unit/test_metrics.py` containing:
  1. **SC‑001 test** – verifies that CC under MCAR produces an empirical Type I error ≤ 0.06 (20 % relative increase) on a synthetic MCAR fixture.
  2. **SC‑003 test** – runs a uniformity test (e.g., Kolmogorov‑Smirnov vs. Uniform) on a set of p‑values, applies Benjamini‑Hochberg FDR correction, and asserts that the resulting q‑value is recorded (`uniformity_q` field).
  3. **SC‑004 / FR‑008 test** – checks the tipping‑point logic (>10 % relative increase, i.e., error > 0.055) and that FDR correction across the full 72‑condition family works.  

  **Verification**: `pytest code/tests/unit/test_metrics.py` passes using legitimate synthetic fixtures; no placeholder data is used.

## Phase 2: Complete the study and validate its evidence

- [ ] T104 Configure and execute the full sensitivity sweep. Create `code/configure_sweep_rates.py` that defines **exact missingness rates**: 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40. The script builds `SimulationConfig` objects for **8 rates × 3 mechanisms × 3 methods = 72 conditions per dataset** and validates the count.  

  Extend `code/main.py`’s `run_sensitivity_sweep` to consume these configs, using **500 Monte Carlo iterations per condition** (as mandated by FR‑003). The simulation MUST strictly adhere to **FR-002**, ensuring that for MNAR, the missingness probability depends on the permuted outcome values. Results are written to:
  * `data/processed/error_metrics.parquet` (granular iteration results)
  * `data/processed/comparison_results.json` (aggregated `ComparisonResult` records)  

  The file must contain **72 × n_datasets** records (one per condition per dataset). The Benjamini‑Hochberg FDR correction is applied across the entire family of 72 × n_datasets p‑values, satisfying FR‑008.  

  **Verification**: the sweep completes within the free‑tier CPU budget; `comparison_results.json` contains the expected number of records with all required schema fields populated.

- [ ] T105 Execute the power analysis. After `configure_sweep_rates.py` has defined the rates/mechanisms, run `code/main_power_analysis.py` which **imports the rate/mechanism list from that module** (ensuring the dependency order). It performs the alternative‑hypothesis sweep (Cohen’s d = 0.5) using the same **500 iterations** per condition and writes `data/processed/power_results.json`.  

  **Verification**: the file is non‑empty, contains power estimates for every condition, and uses the identical rate list as T104.

- [ ] T106 Validate the method‑comparison evidence. Run the CC vs MI vs IPW comparison across the full sweep (using the configs from T104). Verify and record:
  * `cc_mi_ratio` and `validated_tipping_point` per the `simulation_output` schema (covers SC‑005).  

  **Verification**: `comparison_results.json` includes these fields and passes consistency checks.

- [ ] T106b Validate synthetic covariate correlations. For all MAR simulations, implement the check mandated by **FR-009** to verify that the correlation with the outcome (r ≈ 0.3 ± 0.05) is preserved before missingness is applied. Record the result in the `validation_status` field of each record in `comparison_results.json`.

  **Verification**: `comparison_results.json` contains `validation_status` for all MAR conditions, and `code/tests/unit/test_analysis.py` confirms the correlation check logic.

- [ ] T106c Perform p-value distribution analysis. For each condition in the sweep, execute the uniformity deviation test (e.g., Binomial test or KS test) against the theoretical uniform distribution (SC-003). Store the resulting FDR-corrected q-value in the `uniformity_q` field of `comparison_results.json`.

  **Verification**: `comparison_results.json` includes the `uniformity_q` field for all conditions; results are non-null and within [0, 1].

- [ ] T107 Generate the specified figures and tables. Extend `code/visualize.py` to produce:
  * Type I error rate vs. missingness rate curves for each mechanism, with tipping‑point markers.
  * Overlaid CC/MI/IPW error curves.
  * Summary table `data/processed/tipping_points.csv` derived from `comparison_results.json`.  
  All outputs are saved under `figures/`.  

  **Verification**: each figure file exists and is generated programmatically from validated result artifacts.

## Phase 3: Reproducible results and paper handoff

- [ ] T108 Document the runnable workflow. Update `README.md` (project root) and `specs/001-assessing-the-validity-of-statistical-si/quickstart.md` with:
  * Exact command‑line invocations for each entry point (`main_us1.py`, `configure_sweep_rates.py` + sweep, `main_power_analysis.py`, `visualize.py`).
  * Dataset provenance (OpenML IDs and checksums).
  * Seed handling and expected output locations.  

  **Verification**: both files contain the sections; the quickstart command reproduces the T102 result.

- [ ] T109 Re‑run the documented workflow and confirm reproducibility. Execute the full pipeline on a fresh runner:
  * Download datasets, run the sweep, power analysis, comparison, and visualization.
  * Ensure all pytest suites pass.
  * Verify checksums match recorded values.
  * **Tolerance check**: each numeric result (e.g., empirical Type I error rates) must be within **±0.005** of the values recorded in `final_results.json` when using the fixed seeds.  
  * Confirm all result artifacts conform to their contracts.  

  **Verification**: a single fresh run produces `final_results.json` identical to the recorded version within the stated tolerance and all other checks succeed.

- [ ] T110 Write the concise methods/results account and paper‑stage handoff. Create `specs/001-assessing-the-validity-of-statistical-si/research.md` that:
  * Links every reported statistic to its source artifact path.
  * Describes MNAR edge‑case handling (synthetic outcomes when needed).
  * Lists dataset skips (N < 100) and limitations.
  * Provides a handoff section enumerating tables, figures, and result files for the paper stage.  

  **Verification**: every claim cites an existing artifact; no invented numbers appear; the handoff section lists concrete file paths.

## Dependencies and requirement coverage

| Requirement | Task(s) | Command / artifact |
| :-- | :-- | :-- |
| FR-001 (real RCT data, fail‑loud loader) | T101 | `code/data_loader.py`, `data/checksums/manifest.json` |
| FR-002, FR-003 (permute‑then‑mask null, 500 iterations) | T102, T104 | `data/processed/us1_results.json`, `comparison_results.json` |
| FR-004, FR-008, SC-002 (sweep + tipping points + FDR) | T104, T106 | `data/processed/comparison_results.json`, `tipping_points.csv` |
| FR-005, FR-007, SC-001, SC-003, SC-005 (CC/MI/IPW comparison) | T106, T106c | `data/processed/comparison_results.json` |
| FR-006 (Binomial test) | T103 | `pytest code/tests/unit/test_metrics.py` |
| FR-009 (covariate correlation validation) | T106b | `validation_status` fields |
| SC-004 (power, d = 0.5) | T105 | `data/processed/power_results.json` |
| Figures/tables | T107 | `figures/`, `tipping_points.csv` |
| Reproducibility + docs | T108, T109 | `README.md`, `quickstart.md`, `final_results.json` |
| Results account + handoff | T110 | `specs/001-.../research.md` |

**Execution order**: T101 → T102 → T103 → T104 → T105 → T106 → T106b → T106c → T107 → T108 → T109 → T110. T105 explicitly imports the rate list from T104, ensuring correct ordering.