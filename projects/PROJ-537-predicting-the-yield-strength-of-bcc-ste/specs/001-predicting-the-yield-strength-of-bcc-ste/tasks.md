# Tasks: Predicting the Yield Strength of BCC Steels from Compositional Data and Density Functional Theory

**Inputs**: `specs/001-predict-yield-strength-bcc/spec.md`, `plan.md`, original idea, prior `tasks.md` with reviewer feedback.  
**Re-plan note**: Previously rejected tasks fell into two classes: (a) unverifiable scaffolding (directory listings, lint config, git hooks, README polish, code cleanup, profiling) that the template forbids as standalone tasks — these are dropped or folded into the scientific tasks that produce them as by‑products; (b) missing real data artifacts (`merged.csv`, `output.json`, plots) — these are re‑tasked as concrete, deterministically verifiable pipeline executions. Verified implementation tasks (ingestion, modeling, interpretability code with passing unit/integration tests) are preserved as checked. The platform manages `state/*.yaml`; research scripts must not write it, so T020 is dropped and checksums remain in `data/provenance/checksums.txt`.

## Phase 1: Setup and first end‑to‑end analysis

**Goal**: Produce a real merged dataset and a first end‑to‑end model run on real inputs.

- [ ] T048 [US1] Execute the existing ingestion pipeline end‑to‑end to produce the real merged dataset: run `code/main.py` (ingestion stage) which invokes `code/ingestion/fetch_experimental.py` (MatNavi/NIST source URL from `code/config.py`), `code/ingestion/fetch_dft.py` (Materials Project API via `mp-api`, exponential backoff, provenance logged to `data/provenance/dft_queries.jsonl`), and `code/ingestion/merge_and_filter.py` (join on formula, BCC space‑group‑229 filter, range‑midpoint handling with uncertainty flag). The loader must **FAIL LOUDLY** on fetch errors — no synthetic/mock fallback is permitted. Deliverables, verifiable as real files: `data/intermediate/merged.csv` with ≥20 rows having non‑null `yield_strength_MPa` and `shear_modulus_GPa` (halt with `ERR_INSUFFICIENT_DATA` if <20, per FR‑001/FR‑002/FR‑003/SC‑006), and refreshed `data/provenance/checksums.txt` (SHA‑256 of raw and intermediate files, Constitution III).  
    - Verification: `python -c "import pandas as pd; df=pd.read_csv('data/intermediate/merged.csv'); assert len(df[df.yield_strength_MPa.notna() & df.shear_modulus_GPa.notna()])>=20"` exits 0.

- [ ] T049 [US2] Run a thin end‑to‑end first analysis on the real merged dataset: execute `code/modeling/features.py` (composition one‑hot/fractions, DFT scaling, VIF report) and `code/modeling/train.py` with the Random Forest (both DFT‑enhanced and composition‑only) under **5‑fold cross‑validation**, seeded (seed 42). Produce a first real results file `data/results/output.json` containing, at minimum:
  - row count of merged dataset (SC‑006)
  - Pearson correlation between shear modulus and yield strength (SC‑001, FR‑005)
  - per‑fold **R²** and **MAE** for both models (FR‑004, SC‑002)
  - **95 % bootstrap confidence intervals** for the aggregated R² and MAE across folds (`r2_ci`, `mae_ci` fields)
  The analysis must be capable of returning a null result.  
    - Verification: `data/results/output.json` exists, parses as JSON, and contains non‑placeholder numeric values for `pearson_r`, `mae_dft`, `mae_baseline`, `row_count`, `r2_ci`, and `mae_ci`.

## Phase 2: Complete the study and validate its evidence

- [ ] T050 [US2] Complete the statistical comparison: extend `code/modeling/evaluate.py` execution to compute the **paired t‑test** on fold‑wise errors between the DFT‑enhanced and composition‑only models (p‑value, SC‑003, FR‑005), the MAE difference (SC‑007), and the **statistical power** using `statsmodels.stats.power.TTestPower` with Cohen’s d derived from the paired errors, α = 0.05, n = 5 folds. Write these into `data/results/output.json` as `p_value`, `mae_difference`, `power`, and boolean `power_below_0_8` if power < 0.8.  
    - Verification: `output.json` contains numeric `p_value`, `mae_difference`, `power`, and boolean `power_below_0_8` computed from the real fold‑wise errors.

- [ ] T051 [US3] Execute the interpretability analysis on the real merged dataset and trained DFT‑enhanced model: run `code/interpretability/shap_analysis.py` to produce **TreeSHAP** values and **permutation importance** rankings (top‑5 features with scores, highlighting DFT descriptors, FR‑006). **Partial Dependence Plots are omitted** as they are not required by the spec. Write results to `data/results/output.json` and figures `data/results/shap_summary.png` and `data/results/permutation_importance.png`.  
    - Verification: both PNG files exist with non‑trivial size and `output.json` contains a `top5_features` list including importance scores.

- [ ] T052 [US3] Execute the bootstrap stability analyses on the REAL dataset via `code/interpretability/bootstrap_stability.py`:
  (a) **Sample‑size sweep** n = 10 → 50 reporting the standard deviation of feature importance for key DFT descriptors (FR‑007, SC‑004).  
  (b) **10‑bootstrapped full‑dataset resamples** reporting the standard deviation of permutation importance for key DFT descriptors and the boolean `is_stable` (std < 0.05) (FR‑008, SC‑005).  
  The script already implements the required calculations; this task only orchestrates its execution and records the outputs `data/results/stability_distribution.png` and the corresponding fields in `output.json`.  
    - Verification: `output.json` contains `bootstrap_sweep_std` (per n), `permutation_importance_std_10boot`, and `is_stable` boolean; the PNG exists.

- [ ] T053 [US1] Create the contract schemas and validate all artifacts against them: write `specs/001-predict-yield-strength-bcc/contracts/dataset.schema.yaml` (columns, types, units for `merged.csv`) and `contracts/output.schema.yaml` (all SC‑001 – SC‑008 fields, including the newly added CI and power fields), then run the existing `tests/contract/test_merged_schema.py` extended to validate the REAL `data/intermediate/merged.csv` and `data/results/output.json` against these schemas.  
    - Verification: `pytest tests/contract/ -q` passes against the real files; both schema files exist and are non‑empty.

- [ ] T054 Run the complete pipeline end‑to‑end from declared inputs and record actual outcomes: execute `python code/main.py` (full orchestration: ingestion → features → modeling → interpretability → output), confirm all unit/integration/contract tests pass (`pytest tests/ -q`), and confirm `data/results/output.json` contains **every** success criterion SC‑001 – SC‑008 **with real measured values**, including confidence intervals and power.  
    - Verification: full pytest run exits 0; a checklist mapping each SC‑ID to its value in `output.json` is recorded in `data/results/verification.md`.

- [ ] T058 [US3] Verify that every numeric claim in `specs/001-predict-yield-strength-of-bcc-ste/research.md` traces to a field in `output.json`. Implement `tests/verification/test_numeric_trace.py` that extracts numeric literals from the results section and asserts presence (and equality within tolerance) in `output.json`. This script is run as part of T054 verification.  
    - Verification: pytest includes `test_numeric_trace.py` and passes.

- [ ] T059 [US2] Verify reproducibility of the full pipeline: after a fresh runner executes `python code/main.py`, compare the newly generated `data/results/output.json` byte‑for‑byte with the committed baseline (`baseline/output.json`). The check is performed in `tests/reproducibility/test_output_consistency.py` and is included in T054 verification.  
    - Verification: pytest includes `test_output_consistency.py` and passes, confirming exact reproducibility under the pinned seed.

## Phase 3: Reproducible results and paper handoff

- [ ] T055 Write a concise methods/results account in `specs/001-predict-yield-strength-of-bcc-ste/research.md` (results section) linked to the actual values in `data/results/output.json` and the figure files, describing the study design (5‑fold CV, paired t‑test, power analysis, bootstrap stability), negative or null findings honestly (including low power or an insignificant p‑value if the real data yields one), data provenance (MatNavi/NIST URL, Materials Project API queries from `data/provenance/dft_queries.jsonl`), and limitations (associational not causal, sample size, VIF/multicollinearity findings).  
    - Verification: every numeric claim in the results section traces to a field in `output.json`; no invented values.

- [ ] T056 Re‑run the documented workflow from its declared inputs and document the paper‑stage handoff: update `specs/001-predict-yield-strength-of-bcc-ste/quickstart.md` with the exact runnable commands (`python code/main.py`, pytest invocations), pinned seeds, and data‑source citations; record in `data/results/handoff.md` the figures, tables, and claims (with their `output.json` keys) that the paper stage should use, plus open limitations. Paper layout, PDF compilation, and publication remain with the subsequent paper pipeline.  
    - Verification: a fresh runner following `quickstart.md` reproduces `output.json` (byte‑identical, as checked by T059) and `handoff.md` lists each figure file and its source metric key.

## Dependencies and requirement coverage

- **FR‑001/FR‑002/FR‑003/SC‑006** (real data ingestion, ≥20 rows, halt on insufficiency): T048.  
- **FR‑004/SC‑002** (RF with composition + DFT, 5‑fold CV, R²/MAE): T049.  
- **FR‑005/SC‑001/SC‑003/SC‑007** (paired t‑test, p‑value, Pearson correlation, MAE difference): T049, T050.  
- **FR‑009/SC‑008** (statistical power): T050.  
- **FR‑006** (TreeSHAP, permutation importance): T051.  
- **FR‑007/SC‑004** (bootstrap sweep n = 10 → 50): T052.  
- **FR‑008/SC‑005** (10‑bootstraps permutation importance std, `is_stable`): T052.  
- **Constitution VI** (confidence intervals): addressed in T049.  
- **Contracts**: T053. **End‑to‑end validation**: T054. **Reporting/handoff**: T055, T056.  
- **Additional verification**: T058, T059.

Execution order: T048 → T049 → (T050, T051, T052) → T053 → T054 → T058 → T059 → T055 → T056. Previously verified implementation tasks (T002, T005–T007, T009–T016, T018–T019, T021–T030, T033–T038, T043) are complete and preserved; this re‑plan only re‑tasks the artifact‑producing executions and adds the missing verification and CI requirements.
