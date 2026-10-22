# Tasks: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, verifier rejections, and reviewer feedback.

This checklist implements FR‑001–FR‑014 and SC‑001–SC‑005 under a conditional scope: T014 attempts real external acquisition from OpenML/UCI (fail‑loud, no synthetic fallback); if — as the librarian search trail indicates — no schema‑matching public dataset exists, T013's spec amendments authorize the bundled‑verification + synthetic‑validation scope and the conditional skip of mediation as the delivered outcomes. T013 (spec amendment) runs BEFORE T002 so the spec and implementing code never disagree. Tasks rejected by the independent verifier (T001–T005) are reopened with corrected, concrete instructions. All tasks respect data‑flow ordering, write only project‑owned paths, and never fabricate data or fall back to synthetic stand‑ins for real fetches.

---

## Phase 0 – Spec precondition (must land before implementation)

- [ ] T013 [P] **Amend the spec BEFORE implementation: non‑linear proxy, conditional external‑ingestion scope, and conditional mediation semantics**
  *Files*: `specs/001-predicting-the-impact-of-residual-stress/spec.md`, `code/tests/test_spec_update.py`
  *Actions* (this task is a PRECONDITION for T002/T004/T008/T009 — run it first so no implementer following spec.md verbatim builds the wrong formula or the wrong gating):
  - **Amend FR‑003** to adopt the non‑linear proxy `σ_res = k·log(heat_input+1)·sqrt(cooling_rate)` (same k values: 0.8 steel, 0.6 aluminum), replacing the linear form flagged as a deterministic linear function of Set‑A features. Add a discussion acknowledging the proxy remains a deterministic function of Set‑A predictors, so Set‑B/C gains from estimated stress must be interpreted with caution, and that the coefficients k are heuristic, not literature‑derived.
  - **Amend FR‑001** to re‑scope the MUST‑ingest clause conditionally: external NIST/UCI/OpenML ingestion is delivered when T014's acquisition attempt finds a schema‑matching dataset (process parameters + measured residual stress + fatigue life + material class); if the attempt verifies that no such dataset exists (per the librarian search trail), the bundled verification CSV + deterministic synthetic validation dataset constitute the authorized delivered scope, and the gap is recorded in the spec with the verification date. Keep the parsing/standardisation/imputation clauses unchanged. This amendment — not a mere limitation note — authorizes the delivered scope.
  - **Amend FR‑006/FR‑007/SC‑001/SC‑003** to conditional semantics: bootstrap mediation (10 000 resamples, proportion mediated, 95 % CIs) executes when a real (non‑synthetic, non‑validation) source with ≥50 measured‑stress rows is available from T014; otherwise the skip outcome (with power analysis, FR‑013, and an explicit limitation) is the spec‑authorized delivered result. Synthetic/validation sources are never eligible for mediation regardless of row count.
  - **Note for US‑1 Acceptance Scenario 2**: the nested‑JSON parsing requirement is exercised against the real OpenML API in T014 when a dataset is found; the repo‑bundled fixture is unit‑test‑only. If no OpenML dataset matches, the FR‑001 amendment above also covers this scenario's source aspect.
  *Verification*: `pytest code/tests/test_spec_update.py` confirms all three amended clauses are present, the non‑linear formula text matches `k·log(heat_input+1)·sqrt(cooling_rate)`, and the spec still aligns with `contracts/dataset_schema.yaml`.

## Phase 1 – Environment, data acquisition, and inputs

- [ ] T001 [P] **Establish runnable environment, global config, pinned dependencies, and input checksums** *(REDO — previous execution failed: `code/src/env_check.py` exit=1)*
  *Files*: `quickstart.md`, `code/src/env_check.py`, `code/src/config.py`, `code/src/timing.py`, `requirements.txt`, `data/raw/checksums.json`, `code/tests/test_env_check.py`
  *Actions*
  - Implement `code/src/env_check.py` that imports the full scientific stack (`pandas`, `numpy`, `scikit-learn`, `torch` CPU‑only, `statsmodels`, `pyyaml`, `pytest`, `jsonschema`, `psutil`) and exits 0 only if all imports succeed. The previous failure (exit=1) must be diagnosed and fixed — likely a missing pinned dependency (`psutil`) or an import of a not‑yet‑created module; the script must import only what `requirements.txt` pins.
  - Create `code/src/config.py` centrally defining `SEED = 42`, the non‑linear proxy coefficients (`K_STEEL = 0.8`, `K_ALUMINUM = 0.6`), the psi→MPa factor (`0.00689476`), and path constants.
  - Write `requirements.txt` pinning every downstream package (`pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `torch==2.3.*+cpu`, `statsmodels==0.14.*`, `pyyaml==6.0.*`, `pytest==8.2.*`, `jsonschema==4.23.*`, `psutil==6.*`, `openml==0.14.*`, `ucimlrepo==0.0.7`).
  - After T015 has produced `data/raw/synthetic_fatigue.csv`, compute SHA‑256 checksums of the two bundled raw inputs (`data/raw/pipeline_verification.csv`, `data/raw/synthetic_fatigue.csv`) and store them in `data/raw/checksums.json`. The T002 loader must verify these hashes and **raise** on mismatch — never fall back to generated data.
  - Provide the `phase_timer` context manager (wall‑clock via `time.perf_counter`, peak‑RSS via `psutil`) in `code/src/timing.py`; each pipeline phase appends `phase, wall_clock_s, peak_rss_mb` to `data/results/runtime_summary.csv`.
  - Document the single command `python -m code.src.run_e2e` in `quickstart.md`.
  *Verification*: `pytest code/tests/test_env_check.py` asserts the script exits 0, `config.py` defines `SEED`, and recorded checksums match files on disk.

- [ ] T014 **Attempt real external dataset acquisition from OpenML and UCI (FR‑001 delivery attempt; fail‑loud, no synthetic fallback)**
  *Files*: `code/src/acquire_external.py`, `data/external/acquisition_log.json`, `code/tests/test_acquire.py`
  *Actions*
  - Query OpenML via the `openml` Python package (`openml.datasets.list_datasets` with tag/filter searches for fatigue, residual stress, steel, aluminum) and UCI via `ucimlrepo` (`list_datasets` + keyword search) for datasets containing process parameters, residual stress (measured), fatigue life, and material class.
  - For any candidate, fetch the REAL dataset (`openml.datasets.get_dataset(...).get_data()` / `ucimlrepo.fetch_ucirepo(...)`), including its nested/JSON‑structured metadata (exercising the US‑1 scenario‑2 nested parsing against the real API response), and evaluate schema fit against `contracts/dataset_schema.yaml` requirements.
  - If a schema‑matching dataset exists: write it under `data/raw/external_<name>.csv` with a `source` column naming the repository, record its SHA‑256 in `data/raw/checksums.json`, and record `acquired: true` in `data/external/acquisition_log.json` — T002 then ingests it alongside the bundled files.
  - If NO schema‑matching dataset exists: record `acquired: false` with the full query trail (repositories queried, search terms, candidate datasets examined, rejection reasons) in `acquisition_log.json`. A failed real fetch MUST raise during the fetch itself; the "no match" outcome is a documented, verified negative result, NEVER a substitution of synthetic data.
  *Verification*: `pytest code/tests/test_acquire.py` asserts `acquisition_log.json` exists with a complete query trail, and that any `acquired: true` entry points to a real file on disk whose checksum matches `checksums.json`.

- [ ] T015 **Implement and run the deterministic synthetic‑data generator (pipeline validation input)**
  *Files*: `code/src/data/gen_synthetic.py`, `data/raw/synthetic_fatigue.csv`, `code/tests/test_gen_synthetic.py`
  *Actions*
  - Implement `gen_synthetic.py` exactly as plan Phase 1 specifies: deterministic, seed 42, generating 10 000 rows conforming to `contracts/dataset_schema.yaml` (material classes steel/aluminum, heat input, cooling rate, material properties, measured residual stress for a subset, fatigue life). The dataset is for PIPELINE VALIDATION ONLY and is explicitly labeled `source="synthetic"`; it is never eligible for mediation (T008) and never substitutes for a real fetch (T014).
  - Run the generator to produce `data/raw/synthetic_fatigue.csv`; the script must be byte‑reproducible (same seed ⇒ identical file) so T001's checksum and T011's reproducibility check are stable.
  *Verification*: `pytest code/tests/test_gen_synthetic.py` asserts the file exists with 10 000 rows, conforms to the schema, and that a re‑run with the same seed produces a byte‑identical file.

## Phase 2 – Ingestion, preprocessing, and early end‑to‑end run

- [ ] T002 **Implement data ingestion, harmonisation, and non‑linear proxy computation** *(REDO — test missing, artifacts missing, heuristic unit conversion, clamp logging absent; runs AFTER T013 so the amended non‑linear FR‑003 is in force)*
  *Files*: `code/src/ingest.py`, `code/tests/test_ingest.py`, `code/tests/fixtures/openml_style_nested.json`, `data/processed/unified_fatigue.csv`, `data/processed/missing_flags.json`
  *Actions*
  - Load the two bundled raw files PLUS any file T014 acquired (`acquired: true`); on any read error or checksum mismatch, raise immediately (no synthetic fallback). This implements the CSV + nested‑JSON parsing, unit standardisation, and median imputation of FR‑001 (as amended by T013) within the verified scope. The repo‑bundled `openml_style_nested.json` fixture is used for unit‑level parsing tests only; real OpenML nested structures are parsed in T014 when a dataset is found.
  - Parse CSV rows and flatten nested‑JSON structures into the unified schema of `contracts/dataset_schema.yaml`. **Unit conversion MUST use the explicit `stress_unit` column** (values with `stress_unit == "psi"` are multiplied by 0.00689476; `MPa` values pass through) — the previous magnitude‑heuristic (>1000 ⇒ psi) is prohibited.
  - Median‑impute missing numeric values; record original missingness in `data/processed/missing_flags.json`.
  - Compute the proxy for **all** rows using the amended non‑linear form `σ_res = k·log(heat_input+1)·sqrt(cooling_rate)` with `k=0.8` (steel), `k=0.6` (aluminum). Populate `residual_stress_proxy` and `is_proxy` (true only when a measured value is missing); the proxy column is never set equal to a measured value. Clamp negative proxies to `0.01 MPa` and **log the adjustment count** to `logs/proxy_clamp.log`.
  - Compute a per‑row SHA‑256 `checksum` column, validate the result against `contracts/dataset_schema.yaml` with `jsonschema` (abort on failure), and write `data/processed/unified_fatigue.csv` plus `missing_flags.json`.
  *Verification*: `pytest code/tests/test_ingest.py` runs on a slice of the bundled CSV and the nested‑JSON fixture, asserting: output CSV exists, checksum column present, psi rows converted via the unit column (not magnitude), median imputation applied, proxy values match the amended formula, `is_proxy` flags correct, clamp‑log entry count equals the number of negative proxies, and schema validation passes.

- [ ] T003 **Compute proxy–measured agreement (FR‑014) and run a thin end‑to‑end pipeline** *(REDO — `code/src/run_e2e.py` exit=1)*
  *Files*: `code/src/proxy_agreement.py`, `code/src/run_e2e.py`, `data/results/proxy_agreement.csv`, `data/results/e2e_summary.json`, `code/tests/test_e2e.py`
  *Actions*
  - For rows where both `residual_stress_measured` and `residual_stress_proxy` exist, compute Pearson r and R²; write `proxy_agreement.csv` with a `caveat` column stating the proxy is a deterministic (non‑linear) function of Set‑A predictors, so agreement is descriptive only.
  - `run_e2e.py` orchestrates ingest → proxy agreement, wraps each phase in `timing.phase_timer`, and emits `e2e_summary.json` (row counts, % proxy rows, agreement metrics). Fix the prior exit‑1 failure (root cause: missing downstream modules referenced before they existed — the thin run must import only T001–T003 modules).
  *Verification*: `pytest code/tests/test_e2e.py` checks `e2e_summary.json` exists with finite agreement metrics when applicable and `runtime_summary.csv` has a non‑null timing row per phase.

## Phase 3 – Feature construction, model training, and predictive comparison

- [ ] T004 **Build feature sets A, B (balanced), B‑full, and C on identical row indices where paired** *(REDO — A/B length mismatch 8 vs 4)*
  *Files*: `code/src/build_features.py`, `code/tests/test_features.py`
  *Actions*
  - Load `unified_fatigue.csv`. **Feature Set A (balanced)** and **Feature Set B (balanced)** must both be restricted to the identical measured‑stress subset (`is_proxy=False`) with the same `sample_id` order and length — the prior bug built A on the full dataset; fix the construction, not the test.
  - **Balanced‑subset rule (deterministic, resolving the plan's contradictory wording — the plan should be updated to match)**: within the measured‑stress subset, down‑sample the MAJORITY material class with seed 42 so steel and aluminum row counts are EQUAL; if already equal, no down‑sampling. Record the resulting per‑class counts in `data/processed/balanced_measured.csv` metadata. (The plan's "maintain the original proportion" clause is incompatible with "balanced number" and is superseded by this explicit equal‑counts rule; flagged for plan kickback.)
  - **Feature Set B‑full**: process + stress (measured where available, proxy otherwise) on the full dataset. **Feature Set C**: process + material‑property attributes + proxy, full dataset.
  - Standardise numeric features (zero mean, unit variance); persist the scalers under `code/models/`.
  *Verification*: `pytest code/tests/test_features.py` asserts (i) balanced A and B share identical row indices and length, (ii) balanced B contains no proxy rows, (iii) steel and aluminum counts in the balanced subset are equal, (iv) B‑full and C span the full dataset and use the proxy only where measured stress is missing.

- [ ] T005 **Train RF, GBM, and shallow NN with 5‑fold CV, hyper‑parameter search, and held‑out evaluation** *(REDO — `code/src/train.py` exit=1)*
  *Files*: `code/src/train.py`, `code/tests/test_train.py`, `data/results/model_performance.csv`, `code/models/`
  *Actions*
  - Define a fixed grid of 10 hyper‑parameter combinations per algorithm (RF, GBM, shallow NN with one hidden layer, ≤500 epochs, early stopping).
  - 5‑fold CV stratified by `material_class` on the balanced subset for Sets A and B; on the full dataset for B‑full and C. Record per‑fold MAPE and R². All randomness from `config.SEED`.
  - Select the lowest mean CV‑MAPE combo, retrain on the training split, save models under `code/models/<feature_set>/<algorithm>`.
  - 80/20 stratified train/test split (seed 42) of the balanced subset; compute test MAPE & R² per model and per material class; write `data/results/model_performance.csv` including `train_time_s` per model. Fix the prior exit‑1 (import of missing modules / path constants); enforce NN training ≤ 3600 s with a clear error otherwise.
  *Verification*: `pytest code/tests/test_train.py` asserts model files exist, CV‑MAPE values are finite, NN `train_time_s` ≤ 3600, and test metrics are written.

- [ ] T006 **Statistical comparison of Set A vs Set B per material class, enforcing the Constitution VII improvement‑claim gate**
  *Files*: `code/src/wilcoxon_compare.py`, `data/results/wilcoxon_results.csv`, `code/tests/test_wilcoxon.py`
  *Actions*
  - Compute absolute errors for each algorithm's A‑model and B‑model on the **same measured‑stress test rows**, stratified by `material_class`.
  - Per material class: Wilcoxon signed‑rank test (primary, Bonferroni α = 0.05/3) and **paired t‑test on absolute errors (mandatory component of the improvement‑claim gate below, per Constitution VII — not merely supplementary)**.
  - **Constitution VII improvement‑claim gate (MUST be enforced)**: any statement claiming improved predictive value from stress‑mediated features (i.e., any claim that Set B achieves ≥10 % lower MAPE than Set A) MUST demonstrate that improvement (a) consistently across the held‑out test set — both per material class AND overall — and (b) via the paired t‑test on absolute errors. The gate output is a boolean column `improvement_claim_supported` in `wilcoxon_results.csv`. If the gate fails, the MAPE reduction is reported descriptively with an explicit "no improvement claim supported" statement; the reduction percentage is never reported as a claim without passing the gate.
  - Write `wilcoxon_results.csv` with `material_class, algorithm, statistic, p_uncorrected, p_corrected, ttest_statistic, ttest_p, mape_reduction_pct, improvement_claim_supported`.
  *Verification*: `pytest code/tests/test_wilcoxon.py` checks per‑class reporting, p‑values in [0,1], that a fixture with known error pairs yields the expected significance outcomes, and that a fixture with ≥10 % MAPE reduction but inconsistent per‑class results yields `improvement_claim_supported = false`.

- [ ] T007 **Cross‑material transfer evaluation with permutation testing (FR‑009, FR‑011)**
  *Files*: `code/src/cross_material.py`, `data/results/cross_material.csv`, `code/tests/test_cross_material.py`
  *Actions*
  - For each algorithm/feature set: train on steel‑only, test on aluminium‑only, and vice‑versa; compute ΔMAPE vs the within‑material baseline.
  - Permutation test (10 000 permutations, seed 42) with Holm‑Bonferroni correction across the two transfer directions.
  - Write `cross_material.csv` with `train_material, test_material, mape_same, mape_other, delta_mape, perm_p, p_corrected`.
  *Verification*: `pytest code/tests/test_cross_material.py` asserts both direction rows exist, ΔMAPE finite, p‑values in [0,1].

## Phase 4 – Conditional mediation analysis

- [ ] T008 **Power‑analysis eligibility gate and proxy‑dependency flag (FR‑013)**
  *Files*: `code/src/power_analysis.py`, `data/results/mediation_eligibility.json`, `code/tests/test_power.py`
  *Actions*
  - A‑priori power analysis for mediation (f² = 0.15, α = 0.05, power = 0.80); document required n (≈45) and the conservative ≥50 operational threshold.
  - Count measured‑stress rows (`is_proxy=False`) from real (non‑synthetic, non‑validation) sources only — i.e., rows whose `source` traces to a T014 acquisition; synthetic/validation sources are **never** eligible for mediation regardless of row count. Emit `mediation_eligibility.json` with `n_measured`, `eligible`, `under_power_band`, `skip_mediation`, `proxy_dependent`. Under the verified scope (T014 `acquired: false`), `skip_mediation: true` is the spec‑authorized outcome per the T013 amendment of FR‑006/FR‑007.
  *Verification*: `pytest code/tests/test_power.py` confirms the JSON matches recomputed counts and a zero‑measured‑row fixture yields `proxy_dependent: true`, `skip_mediation: true`.

- [ ] T009 **Bootstrap mediation analysis on the measured‑stress subset, conditional on eligibility (FR‑006, FR‑007, FR‑012 as amended by T013)**
  *Files*: `code/src/boot_mediation.py`, `data/results/mediation_summary.csv`, `figures/`, `code/tests/test_mediation.py`
  *Actions*
  - Proceed only if `eligible == true` (a real T014 source with ≥50 measured rows); if under‑powered, add a warning flag; if skipped, write an explicit "skipped" row citing the T013 spec amendment — under the verified scope this skip is the honest, spec‑authorized outcome.
  - Exclude all proxy‑only rows. Exposure `P = z(heat_input)·z(cooling_rate)`; a‑path OLS `residual_stress_measured ~ P + elastic_modulus + yield_strength + C(material_class)`; b‑path OLS `fatigue_life_cycles ~ residual_stress_measured + P + elastic_modulus + yield_strength + C(material_class)`.
  - Indirect effect a·b, direct effect c′, proportion mediated, VIF (flag > 5); 10 000 bootstrap resamples (seed 42), 95 % CI, Holm‑Bonferroni across material classes.
  - Label all outputs "associational — no causal identification"; if the underlying data is synthetic/validation‑only, also "pipeline validation only — synthetic data, not an external scientific claim".
  *Verification*: `pytest code/tests/test_mediation.py` checks that eligibility met ⇒ non‑null CI bounds and required labels; eligibility not met ⇒ skip row written citing the amended spec.

## Phase 5 – Reporting, reproducibility, and handoff

- [ ] T010 **Generate consolidated results report and figures**
  *Files*: `code/src/generate_report.py`, `paper/results_report.md`, `figures/`, `code/tests/test_report.py`
  *Actions*
  - Aggregate all result CSV/JSON artifacts (model performance, Wilcoxon incl. `improvement_claim_supported`, cross‑material, proxy agreement, mediation summary/eligibility, acquisition log, runtime summary).
  - Produce PNG figures: (i) MAPE per feature set & algorithm, (ii) mediation forest plot (if present), (iii) cross‑material ΔMAPE bar chart, (iv) proxy‑agreement scatter.
  - Write `paper/results_report.md` linking each table/figure, interpreting SC‑001–SC‑004 (with the conditional semantics authorized by T013), stating the deterministic‑proxy circularity caveat, the associational framing of mediation, the Constitution‑VII improvement‑claim gate outcome, the T014 acquisition result (acquired or verified gap), and any under‑power warnings.
  *Verification*: `pytest code/tests/test_report.py` asserts the markdown exists, references ≥3 figures, all referenced paths resolve, and a `proxy_dependent: true` case produces the corresponding statement.

- [ ] T011 **End‑to‑end reproducibility verification (FR‑010, SC‑005)**
  *Files*: `code/src/repro_check.py`, `data/results/reproducibility_report.txt`, `code/tests/test_repro.py`
  *Actions*
  - Re‑compute raw‑file SHA‑256 checksums and compare against `checksums.json` and the `checksum` column of `unified_fatigue.csv`; verify the synthetic generator (T015) reproduces a byte‑identical file.
  - Confirm `config.SEED` is used across splits, model initialisation, and bootstrap; verify total wall‑clock ≤ 6 h and peak RAM ≤ 7 GB from `runtime_summary.csv`; verify NN `train_time_s` ≤ 3600.
  - Re‑run the workflow exactly as documented in `quickstart.md`; verify final artifacts are byte‑stable. Write the pass/fail report.
  *Verification*: `pytest code/tests/test_repro.py` checks the report contains "ALL CHECKS PASSED" when constraints are met and that the NN time check is enforced.

- [ ] T012 **Paper‑stage handoff documentation**
  *File*: `paper/paper_handoff.md`, `code/tests/test_handoff.py`
  *Actions*
  - List exact locations of every artifact required for manuscript preparation; state the scope limitation (measured‑stress results are synthetic validation only unless T014 acquired a real source; FR‑001's external clause delivered per the T013 amendment); preserve manuscript‑layout/PDF items as handoff notes only.
  *Verification*: `pytest code/tests/test_handoff.py` asserts the file exists and each listed path resolves.

---

### Dependency & requirement coverage

| Requirement | Satisfying Task(s) |
|-------------|--------------------|
| FR‑001 (conditional scope per T013 amendment) | T013, T014, T002 |
| FR‑002 | T002 |
| FR‑003 (non‑linear proxy, amended) | T013, T002, T004 |
| FR‑004 / FR‑005 | T005 |
| FR‑006 / FR‑007 (conditional per T013 amendment) | T013, T008, T009 |
| FR‑008 + Constitution VII improvement‑claim gate | T006 |
| FR‑009 / FR‑011 | T007 |
| FR‑010 | T001, T005, T009, T011 |
| FR‑012 | T004, T009 |
| FR‑013 | T008 |
| FR‑014 | T003 |
| SC‑001–SC‑005 | T005–T011 |
| Synthetic‑input generation (plan Phase 1) | T015 |
| Reviewer proxy‑determinism concern | T013 (spec revision), T003/T010 (descriptive caveat) |

**Execution order** (data flow; only T001 and T013 are parallel‑safe, and only with each other): (T001 ∥ T013) → T014 → T015 → T002 → T003 → T004 → T005 → (T006 → T007) → T008 → T009 → T010 → T011 → T012. T013 MUST precede T002/T004/T008/T009 so the amended spec is in force before implementation; T015 MUST precede T001's checksum step and T002; T014 MUST precede T002 so any acquired dataset is ingested.

**Plan‑root defects flagged for kickback** (not fixable in tasks.md): (1) plan Phase 4 step 2's contradictory "balanced … while maintaining the original proportion" wording — T004 supersedes it with the explicit equal‑counts seed‑42 rule; (2) plan Phase 1's `src/data/gen_synthetic.py` path differs from the implemented `code/src/data/gen_synthetic.py` (T015); (3) plan Phase 8's eligibility wording should reference the T013 spec amendment for FR‑006/FR‑007 conditional semantics.

All tasks are unchecked; they will be marked complete only after their verification scripts pass against real artifacts.