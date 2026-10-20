# Tasks: How does attention sparsity affect geometric coherence in dense scenes?

**Inputs**: `spec.md`, `plan.md`, existing repository layout, and the contract `inference_results.schema.yaml`.

The study follows three research phases. Tasks are expressed as checklist items; unchecked items indicate pending work. Each task lists the functional requirement(s) it satisfies, the concrete artifact paths it creates or modifies, and the verification step(s) required.

---

## Phase 0 – Data Acquisition & Checksum

- [ ] T000 **Download verified datasets (VRSBench, COCO 2017, RefCOCO+ subset) and verify checksums**   <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/run_download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/run_download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/run_download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/run_download.py exit=1 -->
  - **Path**: `code/data/download.py` → `data/raw/vrsbench.parquet`, `data/raw/coco_val.parquet`, `data/raw/refcoco_plus.parquet`  
  - **Verification**: SHA‑256 hash comparison against published checksums (unit test `tests/unit/test_download.py`); file existence check.  

## Phase 1 – Setup and first end‑to‑end analysis

- [ ] T001 **Download verified datasets and verify checksums**  
  - **Path**: `code/data/download.py` → `data/raw/vrsbench.parquet`, `data/raw/coco_val.parquet`  
  - **Verification**: SHA‑256 hash comparison (unit test `tests/unit/test_download.py`); file existence check.

- [ ] T002 [FR-003, FR‑007, FR‑008] **Pre‑process raw data → dense / non‑dense subsets & exclusion log**  
  - **Path**: `code/data/preprocess.py` → `data/processed/dense_subset.parquet`, `data/processed/non_dense.parquet`, `data/processed/exclusion_log.json`  
  - **Verification**:  
    1. Count of excluded images ≤ 5 % of total (asserted in `tests/unit/test_preprocess.py`).  
    2. Dense‑scene definition (> 5 overlapping boxes, pairwise IoU > 0.10) verified by spot‑check script.

- [ ] T003 [FR-001] **Implement sparsity configuration and masking utility**  
  - **Path**: `code/model/sparsity.py` (class `SparsityConfig(window_size)`)  
  - **Verification**: Unit test `tests/unit/test_sparsity.py` confirms that for a given `window_size` the generated mask covers exactly the specified patch region and that `window_size=0` yields a global mask.

- [ ] T004 [FR-001, FR‑006] **Model wrapper that applies sparsity knob and records per‑image metrics**  
  - **Path**: `code/model/locateany.py` (class `LocateAnythingSparsityWrapper`)  
  - **Verification**: Integration test `tests/unit/test_model_wrapper.py` runs a forward pass on a single image with `window_size=32` and checks that output dictionary contains keys `prediction`, `latency_ms`, and that `torch.get_num_threads()` equals 2.

- [ ] T005 **End‑to‑end sanity run on a tiny sample (5 images) with global attention**  
  - **Path**: `code/cli/run_experiment.py --config global --sample 5` → `data/results/test_run.parquet` and `data/predictions/sample_global.json`  
  - **Verification**:  
    1. All rows conform to `inference_results.schema.yaml` (pytest contract `tests/contract/test_contracts.py`).  
    2. Mean‑IoU value is a number between 0 and 1 (asserted in the same test).  

*Checkpoint*: The command above executes without error, produces real prediction files, and passes schema validation.

---

## Phase 2 – Complete the study and validate its evidence

- [ ] T006 [FR‑002, FR‑009] **Run full inference across the sparsity grid** (global, 64, 32, 16, optional 1) on both dense and non‑dense subsets**  
  - **Path**: `code/cli/run_experiment.py --grid global,64,32,16,1` → `data/results/inference_0.parquet`, `data/results/inference_64.parquet`, `data/results/inference_32.parquet`, `data/results/inference_16.parquet`, `data/results/inference_1.parquet` and corresponding `data/predictions/*.json`  
  - **Verification**: Each parquet file passes the contract schema; aggregate latency per image recorded; total wall‑clock time ≤ 6 h (checked by CI log parser).

- [ ] T014 [FR‑006] **Verify memory consumption stays within 7 GB RAM limit**  
  - **Path**: `code/analysis/memory_check.py` → logs memory usage to `data/analysis/memory_usage.log`  
  - **Verification**: Unit test `tests/unit/test_memory_check.py` asserts that peak RSS ≤ 7 GB; CI fails if the limit is exceeded.

- [ ] T007 [FR‑004, SC‑002, SC‑003] **Statistical analysis (mixed ANOVA / Friedman fallback, correlations)**  
  - **Path**: `code/analysis/stats.py` → `data/analysis/anova_results.json`, `data/analysis/correlation.csv`  
  - **Verification**: Script prints p‑value; unit test `tests/unit/test_stats.py` asserts that the JSON contains keys `f_value`, `p_value`, `method` and that correlation CSV contains columns `density`, `pearson_r`, `spearman_r`.

- [ ] T008 [FR‑010, FR‑011, SC‑001] **Detect tipping point and execute ±8‑patch sensitivity sweep**  
  - **Path**: `code/analysis/tipping_point.py` → `data/analysis/tipping_point.json`, `data/analysis/sweep_results.parquet` (if sweep executed)  
  - **Verification**:  
    1. JSON field `status` is either `"found"` or `"none"` and `window_size` matches the smallest window where dense‑scene mean mIoU < 0.80.  
    2. When a sweep is performed, the sweep parquet contains exactly the expected window sizes (clamped to 1‑64).

- [ ] T013 **Create hold‑out set for attribution analysis**  
  - **Path**: `code/data/create_holdout.py` → `data/holdout/holdout_set.parquet` (fixed‑seed random 200‑image sample, balanced dense/non‑dense)  
  - **Verification**: Unit test `tests/unit/test_holdout.py` checks that the file exists, contains exactly 200 rows, and respects the seed.

- [ ] T009 [FR‑005, SC‑004] **Attribution on failure vs. success cases** (Grad‑CAM or attention rollout)  
  - **Path**: `code/analysis/attribution.py` → heatmaps under `figures/attribution/failure_<id>.png`, `figures/attribution/success_<id>.png`; summary `data/analysis/attribution_summary.json`  
  - **Verification**:  
    1. Attribution script runs only on the hold‑out set created by T013.  
    2. Summary JSON contains keys `global_context_activation_diff`, `failure_mean`, `success_mean`; values are floats in [0,1].  
    3. Unit test `tests/unit/test_attribution.py` checks that at least one heatmap file is created and that the proportion column is populated for those rows.

- [ ] T010 [SC‑001, SC‑002, SC‑003, SC‑004, SC‑005, SC‑006, SC‑007] **Generate all result tables and figures**  
  - **Path**: `code/analysis/reporting.py` →  
    - `data/analysis/degradation_curve.csv`  
    - `figures/degradation_curve.png`  
    - `figures/anova_summary.png`  
    - `figures/correlation_plot.png`  
    - `figures/latency_bar.png`  
    - `figures/attribution_collage.png`  
    - `data/analysis/exclusion_log.json` (re‑used)  
  - **Verification**:  
    1. Each CSV/JSON file can be loaded without error.  
    2. Each PNG is a non‑empty image file (checked by `tests/unit/test_reporting.py`).  
    3. All SC metrics (p‑value, correlation coefficients, latency budget, exclusion proportion, “N/A” flag for low‑density) are present in the generated artifacts.

- [ ] T015 **Verify Single Source of Truth for all generated artifacts**  
  - **Path**: `code/analysis/ssv_check.py` → `data/analysis/ssv_report.json`  
  - **Verification**: Unit test `tests/unit/test_ssv_check.py` asserts that every figure/table references exactly one CSV/Parquet source and reports any violations; CI fails on any breach.

---

## Phase 3 – Reproducible results and paper handoff

- [ ] T011 **Write concise methods & results markdown linked to concrete artifacts**  
  - **Path**: `docs/results.md` – contains sections *Dataset*, *Sparsity Configurations*, *Degradation Curve*, *Statistical Findings*, *Attribution Insights*, each referencing the exact CSV/PNG files produced above.  
  - **Verification**: Manual review step (recorded in CI log) confirms that every figure/table cited in `results.md` exists at the path referenced; a sanity script `scripts/verify_results_md.py` fails if any link is broken.

- [ ] T012 **Full reproducibility run‑through** (re‑execute the entire pipeline from raw download to final report)  
  - **Path**: Single command `bash run_full_pipeline.sh` (provided in the repo root) which orchestrates the tasks in the order T000 → T011.  
  - **Verification**: CI job `reproducibility.yml` runs the script on a fresh runner; the job passes only if all intermediate artifacts are regenerated and the final `docs/results.md` matches the one committed (hash comparison).  

*Checkpoint*: After T012 the pipeline can be started from an empty `data/` directory and will produce the exact same set of validated artifacts, satisfying all success criteria (SC‑001 – SC‑007).

--- 

### Dependency & Requirement Mapping (summary)

| Requirement | Satisfied by Task(s) |
|-------------|----------------------|
| FR‑001 | T003, T004 |
| FR‑002 | T006 |
| FR‑003 | T002, T009 |
| FR‑004 | T007 |
| FR‑005 | T009 |
| FR‑006 | T004, T014 |
| FR‑007 | T002 |
| FR‑008 | T002 (low‑density handling) |
| FR‑009 | T006 (optional 1‑patch) |
| FR‑010 | T008 |
| FR‑011 | T008 |
| SC‑001 | T006, T008, T010 |
| SC‑002 | T007 |
| SC‑003 | T007 |
| SC‑004 | T009 |
| SC‑005 | T006 |
| SC‑006 | T002 |
| SC‑007 | T002 (N/A flag) |

--- 

*All tasks remain unchecked until their implementation and verification succeed. Once a task is checked, the CI will lock its artifact hashes, ensuring reproducibility.*  