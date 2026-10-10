# Tasks: Predicting Plant Secondary Metabolite Profiles from Genomic Data

**Inputs**: `spec.md`, `plan.md`, existing code base, data‑model definitions, JSON contracts.  
**Goal**: End‑to‑end pipeline that (1) downloads real genomic and metabolomic data, (2) extracts BGC features with antiSMASH, (3) aligns datasets, (4) trains and validates regression models (including PGLS), (5) performs a mandated sensitivity analysis, and (6) produces a reproducible report while meeting all functional requirements and success criteria.

---  

## Phase 1 – Project scaffolding & reproducibility  

- [X] **T001** [P] **Create core directory layout**  
  *Path(s):* `code/`, `code/data/`, `code/modeling/`, `code/utils/`, `code/cli/`, `data/raw/`, `data/interim/`, `data/processed/`, `tests/`  
  *Verification:* Run `tree` (or equivalent) at the repository root and confirm all listed directories exist.

- [ ] **T002** [P] **Add linting & formatting configuration**  
  *Path(s):* `.ruff.toml`, `.flake8`, `pyproject.toml` (Black section) at repository root  
  *Verification:* `ruff --quiet .` and `black --check .` complete with exit‑code 0.

- [ ] **T003** [P] **Add environment‑variable management**  
  *Path(s):* `.env.example` (template), `code/config.py` (loads variables via `python‑dotenv`)  
  *Verification:* After sourcing `.env.example`, `config.get("NCBI_API_KEY")` and `config.get("PMDB_API_TOKEN")` return non‑empty strings.

---  

## Phase 2 – Core scientific foundations  

- [ ] **T004** [ ] **Implement Pydantic schemas**  
  *Path:* `code/models/schemas.py` (Species, BGCFeature, Metabolite, ModelOutput)  
  *Verification:* Sample JSON objects validate against the models without errors.

- [ ] **T005** [ ] **Configuration loader, seed manager & logging**  
  *Path(s):* `code/config.py` (loads `spec.yaml`, sets global random seed), `code/utils/logging.py` (file + console handlers)  
  *Verification:* `config.seed` is reproducible, and a run creates `logs/run.log` containing INFO‑level messages.

- [ ] **T006** [ ] **Checksum & artifact tracking**  
  *Path(s):* `code/utils/artifact.py` (SHA‑256 computation, state‑file update), `state/projects/PROJ-198-predicting-plant-secondary-metabolite-pr.yaml` (records hashes)  
  *Verification:* After writing `data/processed/aligned_matrix.csv` and `data/processed/model_metrics.json`, their hashes appear in the state file.

- [ ] **T017** [ ] **Citation verification using Reference‑Validator Agent**  
  *Path:* `code/utils/citation_validator.py` (invokes the Reference‑Validator on all citation artifacts)  
  *Verification:* Running the validator returns a pass/fail report; the pipeline aborts if any citation fails verification, ensuring Constitution Principle II compliance.

---  

## Phase 3 – Data acquisition & preprocessing (User Story 1)  

- [ ] **T007** [ ] **Download real data – genomes from NCBI RefSeq (no size filter) and metabolite tables from PMDB; log warnings for species that cannot be retrieved**  
  *Path:* `code/data/download.py` (`download_genomes()`, `download_metabolites()`)  
  *Verification:* Using a test list of 5 species, the script creates files under `data/raw/` for all successfully fetched species and writes a warning for any missing ones. All genome assemblies listed are attempted regardless of size.

- [ ] **T008** [ ] **Run antiSMASH 7.0 and parse output – execute via Docker, extract a binary presence matrix and a count matrix per species**  
  *Path:* `code/data/preprocess.py` (`run_antiSMASH_wrapper()`)  
  *Verification:* For a test genome, the script produces `bgc_presence.csv` and `bgc_counts.csv` with columns `species_id`, `bgc_type`, `presence` / `count`.

- [ ] **T018** [ ] **Map BGC types to metabolite classes using MIBiG 3.0 ontology**  
  *Path:* `code/data/preprocess.py` (`map_bgc_to_metabolite_class()`)  
  *Verification:* The resulting CSV (`bgc_metabolite_mapping.csv`) contains a column `metabolite_class` for each BGC type; unmapped types are labelled `'unknown'` per FR‑009.

- [ ] **T009** [ ] **Harmonize metabolite data – map identifiers to InChIKeys, add pseudo‑count = 1, apply `log(x+1)` transformation**  
  *Path:* `code/data/preprocess.py` (`harmonize_metabolites()`)  
  *Verification:* The resulting CSV (`metabolite_harmonized.csv`) contains only numeric `abundance_log` values within a realistic range (≈ 0 – 10).

- [ ] **T010** [ ] **Align genomic and metabolomic matrices – inner‑join on species, **preserve rows with zero BGC counts**, compute alignment success rate, write `aligned_matrix.csv` and `alignment_stats.json`.**  
  *Path:* `code/data/align.py` (`align_data()`, `calculate_alignment_success_rate()`)  
  *Verification:* `alignment_stats.json` reports the percentage of input species retained; `aligned_matrix.csv` includes rows where `bgc_count == 0`.

---  

## Phase 4 – Modeling & validation (User Story 2)  

- [ ] **T011** [ ] **Load phylogeny & build covariance matrix** – read Newick tree (`data/raw/phylogeny/tree.nwk`) and construct a phylogenetic covariance matrix for PGLS.  
  *Path:* `code/modeling/phylo.py` (`load_phylogeny()`, `construct_covariance_matrix()`)  
  *Verification:* Covariance matrix dimensions equal the number of species in the aligned dataset.

- [ ] **T012** [ ] **Conditional PCA & conventional model training – if `num_features > N/2` apply PCA (save `pca_features.csv`), then train Random Forest, Elastic Net, Gradient Boosting with k‑fold cross‑validation **stratified by phylogenetic clade** (`LOO` when N < 20, else `5‑Fold`). Record `cross_val_scores` and `cv_method` in `model_metrics.json`.**  
  *Path:* `code/modeling/train.py` (`apply_pca()`, `train_models()`)  
  *Verification:* `model_metrics.json` contains a `cv_method` field (`"LOO"` or `"5Fold"`), a non‑empty `cross_val_scores` list, and model‑type identifiers.

- [ ] **T013** [ ] **Model evaluation & phylogenetic permutation baseline – for **all** trained models (Random Forest, Elastic Net, Gradient Boosting, PGLS) compute R², Pearson r on the hold‑out test set, run the permutation baseline (shuffle metabolite labels, keep features & tree fixed), calculate p‑value, and store results in `model_metrics.json`.**  
  *Path:* `code/modeling/eval.py` (`run_permutation_baseline()`, `calculate_significance()`)  
  *Verification:* `model_metrics.json` includes entries for each model type with `r_squared`, `pearson_r`, `p_value` ≤ 0.05, and baseline statistics.

- [ ] **T014** [ ] **Sweep BGC detection thresholds – iterate over thresholds {0.1, 0.3, 0.5, 0.7}, retrain the full modeling pipeline for each, write `sensitivity_results.csv` (threshold → R²). Compute the maximum absolute ΔR²; if > 0.05 raise a `VerificationError` to abort the run.**  
  *Path:* `code/modeling/eval.py` (`run_sensitivity_sweep()`, `calculate_variation()`, `handle_sensitivity_failure()`)  
  *Verification:* When the variation exceeds 0.05 the script exits with a non‑zero status and an informative error message.

---  

## Phase 5 – Runtime enforcement  

- [ ] **T016** [ ] **Record total pipeline runtime and enforce ≤ 6 h limit**  
  *Path:* `code/utils/runtime_monitor.py` (captures start/end timestamps, computes elapsed time, asserts limit)  
  *Verification:* Pipeline logs `total_runtime_seconds`; if runtime > 21600 s the process exits with an error and CI fails, satisfying SC‑003.

---  

## Phase 6 – Reporting, documentation & CI hand‑off  

- [ ] **T015** [ ] **Generate final report & project documentation**  
  *Sub‑tasks (all part of T015):*  
  - Write `data/processed/final_report.md` containing model performance tables, feature‑importance plots, sensitivity‑analysis summary, threshold justification (citing antiSMASH default confidence), and a “Data Availability” section listing numbers of genomes/metabolites retrieved and excluded.  
  - Update `README.md` with clear installation steps, antiSMASH Docker usage, environment‑variable setup, and a quick‑start command (`python -m code.cli.main run_all`).  
  - Add GitHub Actions workflow `.github/workflows/ci.yml` that (1) installs dependencies, (2) runs the quick‑start pipeline, (3) executes linting, (4) runs the full test suite, and (5) enforces a ≤ 6 h runtime on the free‑tier runner.  
  *Verification:* A fresh clone of the repository triggers the CI workflow, which completes with all jobs green; the generated `final_report.md` contains the required sections and matches the numbers stored in `model_metrics.json`.

---  

### Dependency & Execution Order Summary  

| Task | Depends on |
|------|------------|
| T001‑T003 | – (initial scaffolding) |
| T004‑T006 | T001‑T003 |
| T017 | T004‑T006 |
| T007 | T004‑T006 |
| T008 | T007 |
| T018 | T008 |
| T009 | T018 |
| T010 | T009 |
| T011 | T010 |
| T012 | T011 |
| T013 | T012 |
| T014 | T013 |
| T016 | T014 |
| T015 | T016 (report uses final metrics and runtime info) |

All tasks marked **[P]** can run in parallel where their file locations do not overlap. The pipeline respects the data‑flow ordering required by the specification and the Constitution (no verification step runs before its prerequisite data is produced).  
