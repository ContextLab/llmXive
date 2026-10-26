# Tasks: Predicting Plant Secondary Metabolite Profiles from Genomic Data

**Inputs**: `spec.md`, `plan.md`, existing code base, data‑model definitions, JSON contracts.  

---

## Phase 1 – Project scaffolding & reproducibility  

- [X] **T001** [ ] **Create core directory layout**  
  *Path(s):* `code/`, `code/data/`, `code/modeling/`, `code/utils/`, `code/cli/`, `data/raw/`, `data/interim/`, `data/processed/`, `tests/`  
  *Verification:* Run `tree` (or equivalent) at the repository root and confirm all listed directories exist.

- [ ] **T002** [ ] **Project linting, formatting, and environment‑variable management**
  *Path(s):* `.ruff.toml`, `.flake8`, `pyproject.toml` (Black section), `.env.example`, `code/config.py` (loads variables via `python‑dotenv`)  
  *Verification:*  
  1. `ruff --quiet .` and `black --check .` exit with code 0.  
  2. After sourcing `.env.example`, `config.get("NCBI_API_KEY")` and `config.get("PMDB_API_TOKEN")` return non‑empty strings.  

- [X] **T003** [ ] **Implement Pydantic schemas**  
  *Path:* `code/models/schemas.py` (Species, BGCFeature, Metabolite, ModelOutput)  
  *Verification:* Sample JSON objects validate against the models without errors.

- [X] **T004** [ ] **Configuration loader, seed manager & logging**  
  *Path(s):* `code/config.py` (loads `spec.yaml`, sets global random seed), `code/utils/logging.py` (file + console handlers)  
  *Verification:*  
  1. `config.seed` is reproducible across runs.  
  2. A run creates `logs/run.log` containing INFO‑level messages.  

- [ ] **T005** [ ] **Artifact hygiene: checksum computation, state tracking, and citation verification**  
  *Path(s):* `code/utils/artifact.py` (SHA‑256 computation, state‑file update), `code/utils/citation_validator.py` (invokes Reference‑Validator), `state/projects/PROJ-001-predict-plant-metabolite-pr.yaml` (records hashes)  
  *Verification:*  
  1. After writing `data/processed/aligned_matrix.csv` and `data/processed/model_metrics.json`, their SHA‑256 hashes appear in the state file.  
  2. Running `citation_validator.py` returns a pass report; any failing citation aborts the pipeline.

---

## Phase 2 – Data acquisition & preprocessing (User Story 1)  

- [ ] **T006** [ ] **Download genomes and metabolite tables; log missing species**   <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 -->
  *Path:* `code/data/download.py` (`download_genomes()`, `download_metabolites()`)  
  *Verification:* Using a test list of 5 species, the script creates files under `data/raw/` for all successfully fetched genomes and metabolites, and writes warnings for any species that could not be retrieved.  

- [ ] **T007** [ ] **Run antiSMASH 7.0 (Docker), parse JSON, and map BGC types to MIBiG ontology**   <!-- FAILED-IN-EXECUTION: code/data/antismash.py exit=2 -->
  *Path:* `code/data/antismash.py` (`run_antismash_wrapper()`, `parse_antismash_json()`, `map_bgc_to_mibig()`)  
  *Verification:* For a test genome the script produces `bgc_presence.csv` (binary matrix) and `bgc_counts.csv` (count matrix) with a column `metabolite_class`; unmapped BGC types are labelled `'unknown'`.  

- [ ] **T008** [ ] **Harmonize metabolite identifiers, add pseudo‑count, and log‑transform**  
  *Path:* `code/data/metabolite_preprocess.py` (`harmonize_metabolites()`)  
  *Verification:* The output `metabolite_harmonized.csv` contains only numeric `abundance_log` values (≈ 0 – 10) and uses InChIKeys as identifiers.  

- [ ] **T009** [ ] **Align BGC and metabolite matrices; retain zero‑BGC rows**  
  *Path:* `code/data/align.py` (`align_data()`)  
  *Verification:*  
  1. `aligned_matrix.csv` includes rows where `bgc_count == 0`.  
  2. Alignment retains all species with both data modalities; missing‑modality species are excluded with a logged warning.  

- [ ] **T018** [ ] **Verify alignment success rate meets concrete threshold**  
  *Path:* `code/data/align.py` (adds `calculate_alignment_success_rate()`)  
  *Verification:* `alignment_stats.json` reports the percentage of input species retained and asserts that it is **≥ 80 %**, satisfying SC‑004 with a measurable target.  

- [ ] **T010** [ ] **Load phylogenetic tree and construct covariance matrix for PGLS**   <!-- FAILED-IN-EXECUTION: code/modeling/phylo_compute.py exit=1 -->
  *Path:* `code/modeling/phylo.py` (`load_phylogeny()`, `construct_covariance_matrix()`)  
  *Verification:* The resulting covariance matrix dimensions equal the number of species in `aligned_matrix.csv`.  

---

## Phase 3 – Modeling & validation (User Story 2)  

- [ ] **T011** [ ] **Conditional PCA (if needed) and train regression models with phylogenetically‑stratified CV**  
  *Path:* `code/modeling/train.py` (`apply_pca_if_needed()`, `train_random_forest()`, `train_elastic_net()`, `train_gradient_boosting()`)  
  *Verification:*  
  1. `model_metrics.json` contains a `cv_method` field (`"LOO"` when N < 20, else `"5Fold"`).  
  2. `cross_val_scores` list is non‑empty and matches the chosen CV strategy.  

- [ ] **T012** [ ] **Model evaluation, hold‑out test set, and phylogenetic permutation baseline**  
  *Path:* `code/modeling/eval.py` (`evaluate_models()`, `run_permutation_baseline()`, `calculate_significance()`)  
  *Verification:*  
  1. A separate hold‑out test set (stratified by clade) is used; metrics for this set are recorded.  
  2. `model_metrics.json` includes, for each model type, `r_squared`, `pearson_r`, and `p_value` ≤ 0.05, as well as baseline statistics (`r2_perm_mean`).  

- [ ] **T017** [ ] **Bootstrap R² variability check**  
  *Path:* `code/modeling/bootstrap.py` (`run_bootstrap_resamples(num_resamples=5)`)  
  *Verification:* The script computes R² for each of 5 bootstrap resamples, stores them in `bootstrap_r2.json`, and asserts that the standard deviation ≤ 0.1.  

- [ ] **T016** [ ] **Train and evaluate Phylogenetic Generalized Least Squares (PGLS) model**  
  *Path:* `code/modeling/pgls.py` (`train_pgls()`, `evaluate_pgls()`)  
  *Verification:* `model_metrics.json` contains an entry with `model_type: "PGLS"` and includes all required fields per `model_output.schema.yaml`.  

- [ ] **T013** [ ] **Sensitivity analysis: sweep BGC detection thresholds and enforce ΔR² ≤ 0.05**  
  *Path:* `code/modeling/sensitivity.py` (`run_sensitivity_sweep()`, `calculate_variation()`)  
  *Verification:* `sensitivity_results.csv` lists thresholds and corresponding R²; the script exits with an error if `max(|ΔR²|) > 0.05`, otherwise completes with exit 0.  

- [ ] **T014** [ ] **Runtime monitoring and enforcement of ≤ 6 h total pipeline time**  
  *Path:* `code/utils/runtime_monitor.py` (captures start/end timestamps, asserts limit)  
  *Verification:* Pipeline logs `total_runtime_seconds`; if > 21600 s the process aborts with a clear error message, satisfying SC‑003.  

- [ ] **T015a** [ ] **Generate final report (`final_report.md`)**  
  *Path:* `data/processed/final_report.md`  
  *Verification:* The report contains model performance tables, feature‑importance plots, sensitivity‑analysis summary, threshold justification (citing antiSMASH default confidence), and a “Data Availability” section. Numbers match those in `model_metrics.json`.  

- [ ] **T015b** [ ] **Update `README.md` with installation, antiSMASH Docker usage, and quick‑start command**  
  *Path:* `README.md`  
  *Verification:* A fresh clone’s CI runs `python -m code.cli.main run_all` successfully and the README instructions are accurate.  

- [ ] **T015c** [ ] **Add CI workflow (`.github/workflows/ci.yml`) and verify CI passes**  
  *Path:* `.github/workflows/ci.yml`  
  *Verification:* CI workflow installs dependencies, runs the quick‑start pipeline, executes linting, runs the full test suite, and enforces the ≤ 6 h runtime; all jobs complete green on a fresh runner.  

---  

### Dependency & Execution Order Summary  

| Task | Depends on |
|------|------------|
| T001 | – |
| T002 | – |
| T003 | T001 |
| T004 | T001 |
| T005 | T001‑T004 |
| T006 | T005 |
| T007 | T006 |
| T008 | T007 |
| T009 | T008 |
| T018 | T009 |
| T010 | T009 |
| T011 | T010 |
| T012 | T011 |
| T017 | T012 |
| T016 | T010 |
| T013 | T012 |
| T014 | T013 |
| T015a | T014 |
| T015b | T015a |
| T015c | T015b |
| T016 | T010 |
| T017 | T012 |
| T018 | T009 |

All tasks now respect data flow, cover every functional requirement, and provide concrete, measurable verification steps.  
