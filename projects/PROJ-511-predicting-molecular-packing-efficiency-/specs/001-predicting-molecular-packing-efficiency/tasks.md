# Tasks: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, all contract schemas, and any existing code artifacts.  

The tasks below implement every functional requirement, success‑criterion and reviewer‑driven correction.  Tasks are ordered to respect data flow; each task produces the inputs needed by later tasks.  Checked boxes (`- [x]`) are retained only for tasks that have already been verified as complete in the repository.  All other tasks are unchecked and ready for implementation.

---

## Phase 1 – Data acquisition, preprocessing & validation  

- [ ] **T001** [US1] **Add a verified COD source URL**  
  *Create `code/constants.py` containing `COD_BASE_URL = "<verified COD mirror URL>"` and update the README with the exact version tag.*  
  *Write `data/source_verification.json` (fields: `url`, `version_tag`, `retrieval_date`, `sha256_hashes`).*  
  *Verification*: `source_verification.json` validates against a tiny inline schema and the URL is reachable (HTTP 200).  

- [ ] **T002** [US1] **Download organic CIF files (≤ 50 non‑H atoms) and log statistics**  
  *Implement `code/download_cod.py` that reads the verified URL, streams CIF identifiers, downloads each CIF into `data/raw_cif/`, records download success/failure, and stops when ≥ 500 valid entries have been saved.*  
  *Generate `data/raw_cif/download_log.json` with counts and timestamps.*  
  *Verification*: `data/raw_cif/` contains ≥ 500 `.cif` files; `download_log.json` reports ≥ 500 successful downloads.  

- [ ] **T003** [US1] **Parse CIFs → SMILES, compute Packing Coefficient & 3‑D descriptors**  
  *Script `code/generate_smiles_and_descriptors.py` reads each CIF, extracts a SMILES tag when present, otherwise generates a canonical SMILES with RDKit (flagging `extracted`/`generated`).*  
  *Compute `pc_raw` per FR‑003, radius of gyration, asphericity, principal moments, lattice system, temperature_K, has_solvent, atom_count, atom_type_counts.*  
  *Write `data/dataset_raw.csv` with **all** columns required by `dataset.schema.yaml` (including a placeholder `fingerprint_vector` column).*  
  *Verification*: CSV contains the full column set, SMILES strings are valid (RDKit can parse them), and every `pc_raw` lies in (0, 1).  

- [ ] **T004** [US1] **Filter and clean the raw dataset**  
  *Implement `code/filter_dataset.py` (full, non‑truncated) that loads `data/dataset_raw.csv`, removes rows with missing SMILES, `pc_raw` ≤ 0 or ≥ 1, `atom_count` > 50, or implausible unit‑cell volumes, and logs reasons for each drop.*  
  *Output cleaned file `data/dataset_filtered.csv`.  Abort with a clear error if fewer than 500 rows remain (SC‑001).*  
  *Verification*: `data/dataset_filtered.csv` contains ≥ 500 rows; `filter_log.json` lists counts and exclusion reasons.  

- [ ] **T005** [US1] **Pre‑encoding validation of the filtered CSV**  
  *Create `code/validate_preencoding.py` that checks column presence, non‑nullness (except `fingerprint_vector`), correct data types, and that every SMILES parses with RDKit.*  
  *Exit code 0 only if all checks pass; otherwise print a detailed error summary.*  
  *Verification*: script returns 0 and prints “Pre‑encoding validation passed”.  

- [ ] **T006** [US2] **Encode SMILES with frozen SMILES‑Transformer (CPU‑only)**  
  *Script `code/encode_smiles.py` loads the transformer model (`seyonec/ChemBERTa-zinc-base-v1`) on `device="cpu"`, processes SMILES from `data/dataset_filtered.csv` in streaming batches (initial batch = 64, auto‑downgrade to 32/16 on OOM), computes mean‑pooled fingerprint vectors, and writes `data/processed/full_feature_matrix.csv` (adds `fingerprint_vector` column).*  
  *Verification*: output CSV validates against `dataset.schema.yaml`; all fingerprint entries are finite numbers.  

- [ ] **T007** [US2] **Full dataset schema validation**  
  *Implement `code/validate_dataset.py` that loads `data/processed/full_feature_matrix.csv` and validates every record against `contracts/dataset.schema.yaml` (including correct JSON‑encoded strings).*  
  *Verification*: script exits 0; any schema violation is reported with line number.  

- [ ] **T008** **Train the primary 2‑layer MLP regression model**  
  *Script `code/train_model.py` reads `data/processed/full_feature_matrix.csv`, splits 80/20 (random seed = 42), builds a 2‑layer MLP (≤ 100 k trainable parameters, dropout = 0.1), trains with Adam (lr = 1e‑3, batch = 32, epochs ≤ 30).*  
  *Save checkpoint `data/artifacts/model_primary.pt` and metadata `data/artifacts/model_primary.json` that conforms to `contracts/model.schema.yaml`.*  
  *Verification*: `model_primary.json` validates; `total_parameters` ≤ 100 000.  

- [ ] **T009** **Evaluate the trained model and produce a validation report**  
  *Script `code/evaluate_model.py` loads the model and validation set, computes MAE, Spearman ρ, runs Shapiro‑Wilk on residuals, conditionally computes Pearson r, executes a **full 10 000‑shuffle permutation test** (seed = 42, parallelized via `joblib`).*  
  *Incorporates confounder metadata (lattice_system, temperature_K, has_solvent) as covariates in a multivariate regression diagnostic to satisfy FR‑009.*  
  *Write `data/artifacts/validation_report.json` adhering to `contracts/validation_report.schema.yaml` and also emit a concise `results/validation_report.md` summarising the permutation test.*  
  *Verification*: JSON validates; `actual_shuffles` = 10 000; `mae` ≤ 0.05 flagged as `mae_pass`; SC‑003 condition (`Spearman ρ < 0.2 ⇒ p ≥ 0.05`) is logged.  

- [ ] **T015** **Generate a mini sampled dataset for US‑2 independent testing**  
  *Script `code/create_mini_dataset.py` randomly samples 50 rows from `data/dataset_filtered.csv` (fixed seed = 123) and writes `data/mini_dataset.csv`.*  
  *All downstream US‑2 scripts can be pointed at this mini‑dataset for fast CI‑only validation.*  
  *Verification*: `data/mini_dataset.csv` contains exactly 50 rows and passes `validate_preencoding.py`.  

## Phase 2 – Modeling, evaluation & diagnostics  

- [ ] **T011** **Generate a reproducible HTML report**  
  *Script `code/report_generator.py` uses Jinja2 to assemble `data/artifacts/report.html`.  The report must embed:*  
  • Dataset provenance (COD URL, version, SHA‑256 hashes)  
  • Pre‑processing description, model architecture & hyper‑parameters  
  • All metrics from `validation_report.json` (MAE, Spearman ρ, Pearson r, Shapiro‑Wilk, permutation p‑value, confounder‑covariate diagnostics)  
  • Figures generated programmatically (predicted vs observed scatter, residual histogram, PC distribution)  
  • Git commit hash of the source tree.  
  *Verification*: HTML renders in a browser; every numeric value matches the JSON source (no hand‑typed numbers).  

## Phase 3 – Full pipeline execution, runtime tracking & hand‑off  

- [ ] **T012** **Run the complete end‑to‑end workflow on a fresh CI runner**  
  *Create a top‑level driver script `code/run_full_pipeline.py` that sequentially invokes T001–T011 (using subprocess calls), measures wall‑clock time for each stage, and writes `data/artifacts/runtime_log.txt` with timestamps and total elapsed time.*  
  *The CI job must fail if total runtime exceeds **6 hours** (SC‑005).*  
  *Verification*: `runtime_log.txt` shows total ≤ 6 h; all intermediate artifacts exist.  

- [ ] **T013** **Write the methods & results summary**  
  *Create `data/results/summary.md` that briefly describes the methodology, links to `data/dataset_filtered.csv`, `data/artifacts/model_primary.pt`, `data/artifacts/validation_report.json`, and `data/artifacts/report.html`.*  
  *All reported numeric values (MAE, Spearman ρ, permutation p‑value, SC‑003 outcome, etc.) are copied programmatically from `validation_report.json` to avoid transcription errors.*  
  *Verification*: file exists; a quick script confirms that every number in the markdown matches the JSON counterpart.  

- [ ] **T014** **Add unit‑ and integration‑tests for all new scripts**  
  *Populate `tests/unit/` with pytest files for each script (`test_download_cod.py`, `test_generate_smiles_and_descriptors.py`, …) that use small, real‑data fixtures (e.g., a handful of publicly available CIFs).  Place integration test `tests/integration/test_full_pipeline.py` that runs `run_full_pipeline.py` on the mini‑dataset (`data/mini_dataset.csv`) and checks that the final `validation_report.json` contains the required keys.*  
  *Verification*: `pytest -q` passes with 0 failures on the CI runner.  

---

### Dependency map (summary)

| Task | Produces | Consumes |
|------|----------|----------|
| T001 | `code/constants.py`, `data/source_verification.json` | – |
| T002 | `data/raw_cif/`, `data/raw_cif/download_log.json` | `code/constants.py` |
| T003 | `data/dataset_raw.csv` | `data/raw_cif/` |
| T004 | `data/dataset_filtered.csv`, `filter_log.json` | `data/dataset_raw.csv` |
| T005 | – | `data/dataset_filtered.csv` |
| T006 | `data/processed/full_feature_matrix.csv` | `data/dataset_filtered.csv` |
| T007 | – | `data/processed/full_feature_matrix.csv` |
| T008 | `data/artifacts/model_primary.pt`, `model_primary.json` | `data/processed/full_feature_matrix.csv` |
| T009 | `data/artifacts/validation_report.json`, `results/validation_report.md` | `model_primary.pt`, `data/processed/full_feature_matrix.csv` |
| T015 | `data/mini_dataset.csv` | `data/dataset_filtered.csv` |
| T011 | `data/artifacts/report.html` | `validation_report.json`, model & dataset files |
| T012 | `data/artifacts/runtime_log.txt` | All previous artifacts |
| T013 | `data/results/summary.md` | `validation_report.json`, `report.html`, model & dataset files |
| T014 | Test suite | All code modules |

All tasks together satisfy **FR‑001 – FR‑013**, **SC‑001 – SC‑005**, and the reviewer‑driven corrections. The pipeline is now fully specified, reproducible, and ready for execution.  