# Tasks: Investigating the Impact of Simulated Sensory Deprivation on Resting‑State Brain Network Dynamics

**Input**: Design documents from `/specs/001-sensory-deprivation-network-dynamics/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

---

## Phase 1 – Project scaffolding (foundation)

- [ ] **T001** [P] Create the required project directories (`src/`, `tests/`, `data/`, `results/`).  
  *Creates*: empty folders at the repository root.  
  *Verification*: run `tree -L 2` and confirm the four directories exist; CI test `tests/integration/test_structure.py` checks for their presence.

- [ ] **T002** [ ] Initialize a Python 3.11 project with a pinned `requirements.txt` containing the exact versions needed for the pipeline (e.g., `nibabel==5.1.0`, `numpy==1.26.2`, `pandas==2.2.0`, `networkx==3.2`, `scikit-learn==1.4.0`, `scipy==1.12.0`, `matplotlib==3.8.2`, `seaborn==0.13.2`, `bids-validator==1.14.0`, `requests==2.31.0`).  
  *Verification*: `pip install -r requirements.txt` completes without version conflicts; `tests/unit/test_requirements.py` parses the file and asserts the presence of all required packages.

- [ ] **T003** [ ] Add a `quickstart.md` that documents a single‑command end‑to‑end run (`python -m src.main --sample 1`) and lists required environment variables.  
  *Verification*: CI runs `python -m src.main --dry-run` and checks that the command exits with status 0.

---

## Phase 2 – Core configuration & utilities (blocking)

- [ ] **T004** [ ] Create `src/config.py` defining:  
  * `DATA_ROOT = Path("data")`  
  * `RAW_DIR = DATA_ROOT / "raw"`  
  * `PREPROC_DIR = DATA_ROOT / "preprocessed"`  
  * `QUALITY_DIR = DATA_ROOT / "quality"`  
  * `CONNECTIVITY_DIR = DATA_ROOT / "connectivity"`  
  * `RESULTS_DIR = Path("results")`  
  * `FD_THRESHOLD = 0.5` (mm) and `FD_VOLUME_PCT = 0.10`  
  * `DATASET_IDS = ["ds001770", "ds003820"]`  
  * `ATLAS_URL = "https://github.com/..."` (pinned release)  
  * `MAX_SUBJECTS = 24`  
  * `PERMUTATIONS = 1000`  
  * `RANDOM_SEED = 42`  
  *All paths are created on demand via `llmxive_toolkit.paths.ensure_dir`.  
  *Verification*: Importing `src.config` does not raise; a unit test `tests/unit/test_config.py` asserts each constant exists and has the expected type/value.

- [ ] **T005** [ ] Implement `src/utils/atlas.py` that:  
  1. Downloads the Schaefer‑400 or AAL‑200 atlas from the pinned GitHub URL in `config.py`.  
  2. Caches the zip file under `data/atlas/` and extracts a `.nii.gz` and a lookup CSV.  
  3. Provides `load_atlas(name: str) -> Tuple[nibabel.Nifti1Image, pd.DataFrame]`.  
  *Verification*: Running `python -c "from src.utils.atlas import load_atlas; img, df = load_atlas('Schaefer400'); print(img.shape, df.shape)"` prints a shape matching the number of ROIs; a test `tests/unit/test_atlas.py` checks that the returned ROI count is within 200‑400.

- [ ] **T006** [ ] Create `src/data/quality_check.py` that:  
  1. Reads motion parameter JSON side‑cars for each run.  
  2. Computes Framewise Displacement (FD) per volume using the Power et al. formula.  
  3. Calculates `mean_fd`, `max_fd`, and the proportion of volumes > `FD_THRESHOLD`.  
  4. Marks a subject `excluded = True` if the proportion exceeds `FD_VOLUME_PCT`.  
  5. Writes an exclusion manifest `data/quality/exclusion_manifest.json` with one entry per subject (subject_id, excluded, mean_fd, max_fd).  
  6. Logs the total number of excluded subjects; raises `RuntimeError` if remaining subjects < 20.  
  *Verification*: Unit test `tests/unit/test_quality_check.py` feeds a synthetic motion JSON and asserts correct FD computation and exclusion flag; integration test `tests/integration/test_quality_pipeline.py` runs the script on a tiny real subject and checks that the manifest file exists and matches expectations.

- [ ] **T007** [ ] Create `src/main.py` (entry point) that:  
  1. Parses command‑line arguments (`--download`, `--preprocess`, `--metrics`, `--stats`, `--sample N`).  
  2. Orchestrates the pipeline stages in order: download → quality_check → preprocess → connectivity → metrics → stats → viz.  
  3. After each subject finishes, writes a checkpoint file `data/.checkpoint.json` recording the last completed stage and subject ID.  
  4. On start, checks for an existing checkpoint and resumes from the next stage automatically.  
  *Verification*: Running `python -m src.main --dry-run` prints the ordered stages; a test `tests/unit/test_main_checkpoint.py` simulates an interrupted run and confirms that a second invocation resumes correctly.

- [ ] **T008** [ ] Extend `src/main.py` (or a helper `src/utils/disk.py`) to enforce the **14 GB disk quota** and **7 GB RAM limit**:  
  1. After each major output (raw NIfTI, preprocessed NIfTI, connectivity matrix) the script checks `du -sh data/` and aborts with a clear error if > 13 GB.  
  2. Uses `numpy.float32` for all intermediate arrays and writes them compressed (`np.savez_compressed`).  
  3. Provides a `--cleanup` flag that deletes raw NIfTI files once preprocessing succeeds, preserving only the checksum file.  
  *Verification*: CI runs the pipeline on a synthetic mini‑dataset with `--sample 2`; after stage 2 the disk‑usage check is asserted via `tests/integration/test_disk_quota.py`.

---

## Phase 3 – User Story 1: Acquire & preprocess resting‑state fMRI (Priority P1)

- [ ] **T011** [ ] Implement `src/data/download.py` to:  
  1. Query OpenNeuro for `ds001770`; if unavailable, fallback to `ds003820`.  
  2. Verify the BIDS hierarchy contains `sub-*/ses-*/func/*_task-rest_*_deprivation-{pre,post}*.nii.gz`.  
  3. Download only the first **20 subjects** (deterministic seed) into `data/raw/`.  
  4. Compute and store SHA‑256 checksums in `data/raw/checksums.txt`.  
  5. Raise `ValueError` with a clear message if deprivation labels are missing.  
  *Verification*: Integration test `tests/integration/test_download.py` runs the script with `--sample 1` and asserts that exactly two NIfTI files (pre & post) exist for a subject and that the checksum file is non‑empty.

- [ ] **T012** [ ] Implement `src/data/preprocess.py` (CPU‑only) that:  
  1. Calls FSL’s `mcflirt` for motion correction, `flirt` for MNI normalization, and `fslmaths` for band‑pass filtering (0.01‑0.1 Hz).  
  2. Operates on each raw NIfTI file, writes the preprocessed BOLD time series to `data/preprocessed/{subject}_{condition}_bold.npy`.  
  3. Preserves the original raw NIfTI files (no in‑place modification).  
  *Verification*: Unit test `tests/unit/test_preprocess.py` runs the script on a tiny dummy NIfTI (generated with `nibabel`) and checks that the output `.npy` exists, has shape `(T, R)` and that the raw file remains untouched.

- [ ] **T013** [ ] Add logging (via `llmxive_toolkit.get_logger`) to both download and preprocess modules, capturing start/end timestamps, number of subjects processed, and any exclusion warnings.  
  *Verification*: After a dry run, `logs/pipeline.log` contains entries matching regex `^INFO.*downloaded.*` and `^WARN.*excluded.*`.

- [ ] **T014a** [ ] In `src/data/download.py`, raise `ValueError("Dataset lacks required deprivation condition labels")` if the BIDS check in step 2 fails.  
  *Verification*: Unit test `tests/unit/test_download_labels.py` feeds a dataset lacking the labels and asserts that the exception and message are raised.

- [ ] **T014b** [ ] In `src/data/download.py`, raise `ValueError("Motion covariates missing in side‑car JSON")` if any required motion parameter (`trans_x`, `rot_y`, …) is absent.  
  *Verification*: Test `tests/unit/test_download_motion.py` confirms the exception.

- [ ] **T015** [ ] Validate dataset variable fit (SC-001): after download, parse the BIDS side‑cars and metadata to confirm that all required predictors (deprivation condition), outcomes (modularity, global efficiency, node strength), and covariates (motion FD metrics) are present for each subject.  
  *Verification*: Unit test `tests/unit/test_dataset_schema.py` loads the generated `data-model` JSON for each subject and asserts conformity to `specs/001-investigating-the-impact-of-simulated-se/contracts/dataset_schema.schema.yaml`. Missing variables cause the script to abort with a clear error.

- [ ] **T016** [ ] Document absence of questionnaire‑based measures (SC-006): run a check that scans the project for any questionnaire files (e.g., `*_questionnaire*.csv`); if none are found, write a compliance report `results/questionnaire_compliance.md` stating “No questionnaire data present; SC‑006 satisfied by omission.”  
  *Verification*: Test `tests/unit/test_questionnaire_absence.py` confirms the report is generated and contains the required statement.

- [ ] **T014c** [ ] (renamed from previous T014) Ensure that `src/data/download.py` raises a clear error if the dataset lacks required deprivation labels, as already covered by T014a.

---

## Phase 4 – User Story 2: Compute connectivity & network metrics (Priority P2)

- [ ] **T018** [ ] Implement `src/analysis/connectivity.py` to:  
  1. Load preprocessed BOLD `.npy` for a subject/condition.  
  2. Load the ROI mask from `src/utils/atlas.py`.  
  3. Extract mean time series per ROI, compute a Pearson correlation matrix (`float32`).  
  4. Save the symmetric matrix to `data/connectivity/{subject}_{condition}_conn.npy`.  
  *Verification*: Unit test `tests/unit/test_connectivity.py` creates a synthetic 5‑ROI time series, runs the function, and asserts that the output matrix is symmetric and diagonal = 1.0.

- [ ] **T019** [ ] Implement `src/analysis/metrics.py` function `compute_modularity(matrix, atlas_name)` using the Louvain algorithm from `networkx.algorithms.community`.  
  *Verification*: Test `tests/unit/test_modularity.py` feeds a known modular graph and checks that the returned modularity matches the reference value within 1e‑4.

- [ ] **T020** [ ] Add to `metrics.py` the functions `global_efficiency(matrix)` (networkx) and `node_strength(matrix)` (sum of absolute edge weights per node).  
  *Verification*: Unit tests `tests/unit/test_efficiency.py` and `tests/unit/test_node_strength.py` validate against hand‑computed examples.

- [ ] **T021** [ ] Create `src/analysis/aggregate.py` that reads all per‑subject metric CSV rows, pairs pre/post entries, and writes `results/paired_metrics.csv` with columns: `subject_id, modularity_pre, modularity_post, global_eff_pre, global_eff_post, strength_pre, strength_post`.  
  *Verification*: Integration test `tests/integration/test_aggregate.py` runs the whole connectivity+metrics pipeline on two synthetic subjects and checks that the CSV contains exactly two rows with correctly paired values.

- [ ] **T022** [ ] Ensure all numeric outputs are saved with **≥ 4 decimal places** (use `np.format_float_positional(..., precision=4)`) and compressed (`np.savez_compressed`).  
  *Verification*: A CI step reads a saved `.npy` file and asserts `np.max(np.abs(arr - np.round(arr, 4))) < 1e‑4`.

---

## Phase 5 – User Story 3: Statistical comparison & visualizations (Priority P3)

- [ ] **T026** [ ] Implement `src/analysis/stats.py` to perform paired **t‑tests** for each metric across subjects, apply **Benjamini‑Hochberg FDR** correction (α = 0.05), and compute **Cohen’s d**.  
  *Verification*: Unit test `tests/unit/test_stats_ttest.py` uses a small synthetic paired dataset where the true p‑value is known and checks that the corrected p‑value and effect size match expectations.

- [ ] **T027** [ ] Add to `stats.py` a **permutation test** (sign‑flip) with `config.PERMUTATIONS` iterations, returning an empirical p‑value per metric.  
  *Verification*: Integration test `tests/integration/test_permutation.py` runs the permutation on a tiny dataset and asserts that the empirical p‑value lies between 0 and 1 and differs from the parametric p‑value.

- [ ] **T028** [ ] Implement a **sensitivity analysis** routine that re‑runs the statistical tests over a grid of thresholds:  
  - Motion exclusion thresholds: 0.3, 0.5, 0.7 mm  
  - Effect‑size thresholds: 0.3, 0.5, 0.8  
  - FDR q‑values: 0.01, 0.05, 0.1  
  Results are written to `results/sensitivity_report.csv`.  
  *Verification*: Test `tests/unit/test_sensitivity.py` confirms the CSV contains `len(threshold_grid)` rows and that each row includes the three threshold values used.

- [ ] **T029** [ ] Create `src/viz/plot_networks.py` that:  
  1. Loads a connectivity matrix, thresholds at the top 10 % strongest edges,  
  2. Plots degree distribution histograms for pre & post conditions side‑by‑side,  
  3. Saves PNGs to `figures/degree_{subject}_{condition}.png`.  
  *Verification*: CI runs the script on a synthetic matrix and asserts that the PNG files exist and have non‑zero file size.

- [ ] **T030** [ ] Create `src/viz/plot_metrics.py` that:  
  1. Reads `results/paired_metrics.csv`,  
  2. Generates bar plots with error bars for each metric (pre vs. post),  
  3. Overlays significance stars based on FDR‑corrected p‑values,  
  4. Saves to `figures/metrics_comparison.png`.  
  *Verification*: Visual test `tests/integration/test_plot_metrics.py` checks that the PNG is created and that the figure contains at least three bars (one per metric).

- [ ] **T031** [ ] Write `results/stats.csv` containing for each metric: `t_statistic, p_uncorrected, p_fdr, cohen_d, permutation_p`.  
  *Verification*: After running `src.main --stats`, a CI step loads the CSV and asserts that all columns are present and that `p_fdr ≤ 0.05` for at least one metric (or records the failure for later review).

---

## Phase 6 – polish & cross‑cutting concerns

- [ ] **T032** [ ] Update `README.md` and `quickstart.md` with the final command sequence, required environment variables, and a reproducibility checklist.  
  *Verification*: CI runs `bash -c "grep -q 'python -m src.main' README.md"`.

- [ ] **T033** [ ] Generate `results/statistical_framing.md` that programmatically inspects the dataset metadata for randomization flags; if absent, the document declares the inference as **associational** (per SC‑002).  
  *Verification*: Unit test `tests/unit/test_framing.py` feeds a metadata JSON without randomization and checks that the generated markdown contains the phrase “associational”.

- [ ] **T034** [ ] Produce `results/sensitivity_report.md` summarizing the CSV from **T028**, including a one‑line rationale for each threshold sweep (e.g., “0.5 mm chosen as community‑standard motion cutoff”).  
  *Verification*: Test `tests/unit/test_sensitivity_md.py` parses the markdown and confirms that each threshold appears with an accompanying rationale line.

- [ ] **T035** [ ] Create `results/power_analysis.md` documenting the sample‑size justification (n ≥ 20) and the method used (e.g., G*Power simulation) along with any acknowledged power limitations (SC‑004).  
  *Verification*: Manual reviewer check; CI ensures the file exists and contains the phrase “n ≥ 20”.

- [ ] **T036** [ ] Refactor code for memory efficiency: use generators when streaming BOLD time series, delete intermediate variables after use, and confirm peak RAM < 7 GB via a runtime monitor (`psutil`).  
  *Verification*: CI runs the full pipeline on the sample subset with `--monitor-memory` and asserts `max_ram_mb < 7000`.

- [ ] **T037** [ ] Parallelise subject‑wise processing where possible (download, quality check, preprocessing, connectivity) using `concurrent.futures.ThreadPoolExecutor` while respecting the 6‑hour wall‑time limit.  
  *Verification*: CI measures total runtime on the sample set; it must be ≤ 3600 seconds and the log must contain “Parallel workers: X”.

- [ ] **T038** [ ] Add edge‑case unit tests (`tests/unit/test_edge_cases.py`) covering: missing BIDS side‑cars, empty subject list, and corrupted NIfTI files (should raise informative errors).  
  *Verification*: CI runs the test suite; all edge‑case tests must pass.

- [ ] **T039** [ ] Run `quickstart.md` validation on a fresh runner (`actions/checkout` + `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && bash quickstart.sh`) and confirm the end‑to‑end pipeline produces `results/stats.csv` without manual intervention.  
  *Verification*: CI step asserts exit code 0 and existence of the final CSV.

--- 

### Dependencies & Execution Order

1. **Phase 1** tasks must complete before any other task (they provide the folder layout and dependency list).  
2. **Phase 2** tasks (`T004–T008`) are **blocking**; all downstream user‑story tasks depend on a valid `config.py`, atlas utility, quality‑check script, and orchestrator.  
3. **User Story 1** (`T011–T016`) can start once Phase 2 is done.  
4. **User Story 2** (`T018–T022`) depends on the outputs of US 1 (`preprocessed` BOLD files).  
5. **User Story 3** (`T026–T031`) depends on US 2’s `paired_metrics.csv`.  
6. **Phase 6** tasks run after the three user stories have produced their primary artifacts; they may be executed in parallel where marked `[P]`.

--- 

*All tasks are unchecked (`[ ]`) until their corresponding artifact is produced and verified by the automated test suite. Checked tasks from previous iterations that remain valid have been omitted to avoid duplication; they will be re‑added automatically once their artifacts pass verification.* 