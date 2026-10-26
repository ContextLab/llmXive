# Tasks: Predicting Plant Secondary Metabolite Profiles from Genomic Data

**Inputs**: `spec.md`, `plan.md`, existing code base, data‑model definitions, JSON contracts.  

---

## Phase 1 – Project scaffolding & reproducibility  

- [X] **T001** [ ] **Create core directory layout**  
  *Path(s):* `code/`, `code/data/`, `code/modeling/`, `code/utils/`, `code/cli/`, `data/raw/`, `data/interim/`, `data/processed/`, `tests/`  
  *Verification:* Run `tree` (or equivalent) at the repository root and confirm all listed directories exist.

- [ ] **T002** [ ] **Add linting, formatting, and env‑variable templates**  
  *Path(s):* `.ruff.toml`, `.flake8`, `pyproject.toml` (Black section), `.env.example` (with placeholder but non‑empty `NCBI_API_KEY=FAKE_KEY` and `PMDB_API_TOKEN=FAKE_TOKEN`)  
  *Verification:*  
  1. `ruff --quiet .` and `black --check .` exit with code 0.  
  2. `flake8 .` exits with code 0.  
  3. Loading `.env.example` via `python -c "from dotenv import load_dotenv; load_dotenv('.env.example'); import os; assert os.getenv('NCBI_API_KEY')" ` succeeds, confirming the variables are present.

- [X] **T003** [ ] **Implement Pydantic schemas**  
  *Path:* `code/models/schemas.py` (Species, BGCFeature, Metabolite, ModelOutput)  
  *Verification:* Sample JSON objects validate against the models without errors.

- [X] **T004** [ ] **Configuration loader, seed manager & logging**  
  *Path(s):* `code/config.py` (loads `spec.yaml`, sets global random seed), `code/utils/logging.py` (file + console handlers)  
  *Verification:*  
  1. `config.seed` is reproducible across runs.  
  2. A run creates `logs/run.log` containing INFO‑level messages.

- [ ] **T005** [ ] **Artifact hygiene limited to project‑owned paths**  
  *Path(s):* `code/utils/artifact.py` (SHA‑256 computation, writes `data/metadata/checksums.json`), `code/utils/citation_validator.py` (invokes Reference‑Validator)  
  *Verification:*  
  1. After writing any `data/processed/*` file (e.g., `aligned_matrix.csv`, `model_metrics.json`), its SHA‑256 hash appears in `data/metadata/checksums.json`.  
  2. Running `python -m code.utils.citation_validator` returns a pass report; any failing citation aborts the pipeline.  
  3. No files are written under the platform‑owned `state/` directory.

## Phase 2 – Data acquisition & preprocessing (User Story 1)

- [ ] **T006** [ ] **Download genomes and metabolite tables; log missing species**  
  *Path:* `code/data/download.py` (`download_genomes()`, `download_metabolites()`)  
  *Verification:*  
  1. Using a test list of 5 species, the script creates files under `data/raw/genomes/` and `data/raw/metabolites/` for all successfully fetched items.  
  2. For each species that cannot be retrieved, a warning is written to `logs/download.log`.  
  3. After each successful download a SHA‑256 checksum is recorded in `data/metadata/checksums.json`.  
  4. The script exits with code 0 on complete success; permanent failures raise an exception and abort the pipeline.

- [ ] **T007** [ ] **Run antiSMASH 7.0 (Docker), parse JSON, and map BGC types to MIBiG ontology**  
  *Path:* `code/data/antismash.py` (`run_antismash_wrapper()`, `parse_antismash_json()`, `map_bgc_to_mibig()`)  
  *Verification:*  
  1. For a test genome the Dockerized antiSMASH run completes without error and produces a JSON file.  
  2. `parse_antismash_json()` creates `data/interim/bgc_presence.csv` (binary matrix) and `data/interim/bgc_counts.csv` (count matrix).  
  3. Unmapped BGC types are labelled `'unknown'`.  
  4. Both CSVs validate against `contracts/feature_matrix.schema.yaml`.  
  5. All steps log summary information to `logs/antismash.log` and exit with code 0.

- [ ] **T008** [ ] **Harmonize metabolite identifiers, add pseudo‑count, and log‑transform**  
  *Path:* `code/data/metabolite_preprocess.py` (`harmonize_metabolites()`)  
  *Verification:*  
  1. Output `data/interim/metabolite_harmonized.csv` contains only numeric `abundance_log` values (typically 0 – 10) and uses InChIKeys as identifiers.  
  2. A pseudo‑count of 1 is added before log‑transformation; the transformation is verified to produce finite numbers.  
  3. The file validates against `contracts/dataset.schema.yaml`.  
  4. The script exits with code 0 and writes a concise summary to `logs/metabolite_preprocess.log`.

- [ ] **T009** [ ] **Align BGC and metabolite matrices; retain zero‑BGC rows**  
  *Path:* `code/data/align.py` (`align_data()`)  
  *Verification:*  
  1. `data/processed/aligned_matrix.csv` is created and includes rows where `bgc_count == 0`.  
  2. Species lacking either genome or metabolite data are excluded; each exclusion generates a **warning** in `logs/align.log`.  
  3. The aligned matrix validates against `contracts/aligned_dataset.schema.yaml`.  
  4. The script exits with code 0.

- [ ] **T018** [ ] **Calculate alignment success rate and enforce user‑defined retention target**  
  *Path:* `code/data/align.py` (adds `calculate_alignment_success_rate()` and writes `data/processed/alignment_stats.json`)  
  *Verification:*  
  1. `alignment_stats.json` contains fields `input_species_count`, `retained_species_count`, and `retention_percent`.  
  2. The task reads `config.alignment_retention_target` (a percentage supplied by the user) and asserts `retention_percent >= config.alignment_retention_target`.  
  3. If the assertion fails, the script exits with a non‑zero code and prints a clear error message.  
  4. The configuration is loaded via `code/config.py` before any calculation.

- [ ] **T020** [ ] **Validate all major outputs against their JSON schemas**  
  *Path:* `code/validation/run_schema_validation.py`  
  *Verification:*  
  1. The script loads each contract (`aligned_dataset`, `dataset`, `feature_matrix`, `model_output`, `model_results`) and validates the corresponding file (`data/processed/aligned_matrix.csv`, `data/processed/dataset.json`, etc.) using Pydantic/JSON‑Schema.  
  2. Any validation error aborts the pipeline with a descriptive message.  
  3. Successful validation is logged to `logs/validation.log`.

- [ ] **T021** [ ] **Run block‑permutation baseline and compare to phylogenetic baseline**  
  *Path:* `code/modeling/block_permutation.py` (`run_block_permutation_baseline()`)  
  *Verification:*  
  1. Generates `data/processed/block_permutation_baseline.json` containing R² scores for each block‑permuted iteration.  
  2. `evaluate_models.py` must read both `permutation_baseline.json` (phylogenetic) and `block_permutation_baseline.json` and compute two separate p‑values; both must be < 0.05 for the model to be accepted.  
  3. The script exits with code 0 only if both significance criteria are met; otherwise it aborts with a clear error.

- [ ] **T010** [ ] **Load phylogenetic tree and construct covariance matrix for PGLS**  
  *Path:* `code/modeling/phylo.py` (`load_phylogeny()`, `construct_covariance_matrix()`)  
  *Verification:*  
  1. The phylogenetic tree file (`data/raw/phylogeny.nwk`) is read without error.  
  2. The resulting covariance matrix is saved as `data/processed/phylo_covariance.npy` with dimensions matching the number of species in `aligned_matrix.csv`.  
  3. The script exits with code 0 and logs the matrix shape to `logs/phylo.log`.

## Phase 3 – Modeling & validation (User Story 2)

- [ ] **T011** [ ] **Conditional PCA (if needed) and train regression models with phylogenetically‑stratified CV**  
  *Path:* `code/modeling/train.py` (`apply_pca_if_needed()`, `train_random_forest()`, `train_elastic_net()`, `train_gradient_boosting()`)  
  *Verification:*  
  1. The training script uses a CV splitter that is instantiated as `StratifiedKFold` (or equivalent) on the `clade` column to ensure phylogenetic stratification.  
  2. `data/processed/model_metrics.json` contains a `cv_method` field (`"LOO"` when N < 20, else `"5Fold"`).  
  3. `cross_val_scores` list is non‑empty and matches the chosen CV strategy.  
  4. The splitter type (`StratifiedKFold`) is recorded in the metrics file for auditability.

- [ ] **T012** [ ] **Model evaluation, hold‑out test set, and phylogenetic permutation baseline**  
  *Path:* `code/modeling/eval.py` (`evaluate_models()`, `run_permutation_baseline()`, `calculate_significance()`)  
  *Verification:*  
  1. A stratified hold‑out test set (respecting clade distribution) is used; metrics for this set are recorded in `model_metrics.json`.  
  2. The phylogenetic permutation baseline is executed, producing `data/processed/permutation_baseline.json` with a distribution of R² scores.  
  3. `calculate_significance()` computes a p‑value by comparing the model’s test‑set R² to the baseline distribution; the p‑value must be < 0.05.  
  4. Both the baseline mean R² (`r2_perm_mean`) and the p‑value are stored in `model_metrics.json`.  
  5. The script exits with code 0 only if the significance condition is satisfied.

- [ ] **T016** [ ] **Train and evaluate Phylogenetic Generalized Least Squares (PGLS) model**  
  *Path:* `code/modeling/pgls.py` (`train_pgls()`, `evaluate_pgls()`)  
  *Verification:* `model_metrics.json` contains an entry with `model_type: "PGLS"` and includes all required fields per `model_output.schema.yaml`.  

- [ ] **T013** [ ] **Sensitivity analysis: sweep BGC detection thresholds and enforce ΔR² ≤ 0.05**  
  *Path:* `code/modeling/sensitivity.py` (`run_sensitivity_sweep()`, `calculate_variation()`)  
  *Verification:* `data/processed/sensitivity_results.csv` lists thresholds and corresponding R²; the script exits with an error if `max(|ΔR²|) > 0.05`, otherwise completes with exit 0.  

- [ ] **T014** [ ] **Runtime monitoring and enforcement of ≤ 6 h total pipeline time**  
  *Path:* `code/utils/runtime_monitor.py` (captures start/end timestamps, asserts limit)  
  *Verification:* Pipeline logs `total_runtime_seconds`; if > 21600 s the process aborts with a clear error message, satisfying SC‑003.  

- [ ] **T017** [ ] **Bootstrap R² variability check**  
  *Path:* `code/modeling/bootstrap.py` (`run_bootstrap_resamples(num_resamples=5)`)  
  *Verification:* The script computes R² for each of 5 bootstrap resamples, stores them in `data/processed/bootstrap_r2.json`, and asserts that the standard deviation ≤ 0.1.  

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
| T016 | T010 |
| T013 | T012 |
| T014 | T013 |
| T017 | T012 |
| T015a | T014 |
| T015b | T015a |
| T015c | T015b |
| T020 | T009, T011, T012, T016, T018 |
| T021 | T012 |

All tasks now respect data flow, satisfy every functional requirement, and provide concrete, measurable verification steps. No task writes outside project‑owned directories, and all schema‑validation, stratified CV, permutation‑baseline significance, and user‑defined alignment‑retention criteria are explicitly enforced.  
