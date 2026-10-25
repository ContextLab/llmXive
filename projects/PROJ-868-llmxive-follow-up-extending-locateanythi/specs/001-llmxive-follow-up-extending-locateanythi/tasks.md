# Tasks: How does attention sparsity affect geometric coherence in dense scenes?

**Inputs**: `spec.md`, `plan.md`, existing repository layout, and the contract `inference_results.schema.yaml`.

The study follows three research phases. Tasks are expressed as checklist items; unchecked items indicate pending work. Each task lists the functional requirement(s) it satisfies, the concrete artifact paths it creates or modifies, and the verification step(s) required.

---

## Phase 0 – Data acquisition & checksum

- [ ] **T001** [FR‑001 · FR‑006] **Download verified datasets (VRSBench, COCO 2017, RefCOCO+ subset) and verify checksums**   <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 -->
  - **Path**: `code/data/download.py` → `data/raw/vrsbench.parquet`, `data/raw/coco_val.parquet`, `data/raw/refcoco_plus.parquet`  
  - **Verification**: Unit test `tests/unit/test_download.py` checks that each file exists and that its SHA‑256 hash matches the published checksum; the script must exit with status 0.

---

## Phase 1 – Setup and first end‑to‑end analysis

- [ ] **T002** [FR‑003 · FR‑007 · FR‑008] **Pre‑process raw data → dense / non‑dense subsets & exclusion log**   <!-- FAILED-IN-EXECUTION: code/data/preprocess.py exit=1 -->
  - **Path**: `code/data/preprocess.py` → `data/processed/dense_subset.parquet`, `data/processed/non_dense.parquet`, `data/processed/exclusion_log.json`  
  - **Verification**:  
    1. `tests/unit/test_preprocess.py` asserts that the proportion of excluded images ≤ 5 % of the total.  
    2. Spot‑check script confirms that dense‑scene images contain > 5 overlapping boxes (pairwise IoU > 0.10).  

- [ ] **T003** [FR‑001] **Implement sparsity configuration and masking utility**  
  - **Path**: `code/model/sparsity.py` (class `SparsityConfig(window_size)`)  
  - **Verification**: `tests/unit/test_sparsity.py` validates that for each supported `window_size` (0, 64, 32, 16, 1) the generated mask covers exactly the intended patch region and that `window_size=0` yields a global mask.

- [ ] **T004** [FR‑001 · FR‑006] **Model wrapper that applies the sparsity knob and records per‑image metrics**  
  - **Path**: `code/model/locateany.py` (class `LocateAnythingSparsityWrapper`)  
  - **Verification**: Integration test `tests/unit/test_model_wrapper.py` runs a forward pass on a single image with `window_size=32` and checks that the output dict contains keys `prediction`, `latency_ms`, and that `torch.get_num_threads()` equals 2.

- [ ] **T005** [FR‑002 · FR‑009] **End‑to‑end sanity run on a tiny sample (5 images) with global attention**  
  - **Path**: `code/cli/run_experiment.py --config global --sample 5` → `data/results/sanity_global.parquet`, `data/predictions/sample_global.json`  
  - **Verification**:  
    1. All rows in the parquet file pass `inference_results.schema.yaml` (contract test `tests/contract/test_contracts.py`).  
    2. The mean mIoU column contains a numeric value between 0 and 1.  

*Checkpoint*: The command executes without error, produces real prediction files, and passes schema validation.

---

## Phase 2 – Complete the study and validate its evidence

- [ ] **T006** [FR‑002 · FR‑009] **Run full inference across the sparsity grid (global, 64, 32, 16, optional 1) on both dense and non‑dense subsets**  
  - **Path**: `code/cli/run_experiment.py --grid global,64,32,16,1` → `data/results/inference_0.parquet`, `data/results/inference_64.parquet`, `data/results/inference_32.parquet`, `data/results/inference_16.parquet`, `data/results/inference_1.parquet` and corresponding JSON predictions under `data/predictions/`.  
  - **Verification**: Each parquet file conforms to the contract schema; total wall‑clock time ≤ 6 h (checked by CI log parser).

- [ ] **T007** [FR‑006] **Verify memory consumption stays within the 7 GB RAM limit**  
  - **Path**: `code/analysis/memory_check.py` → logs written to `data/analysis/memory_usage.log`  
  - **Verification**: Unit test `tests/unit/test_memory_check.py` asserts that peak RSS ≤ 7 GB; CI fails otherwise.

- [ ] **T008** [FR‑004 · SC‑002 · SC‑003] **Statistical analysis (mixed ANOVA with Friedman fallback, plus correlation analysis)**  
  - **Path**: `code/analysis/stats.py` → `data/analysis/anova_results.json`, `data/analysis/correlation.csv`  
  - **Verification**: Script prints the p‑value; `tests/unit/test_stats.py` checks that the JSON contains keys `method`, `f_value`, `p_value` and that the CSV has columns `scene_density`, `pearson_r`, `pearson_p`, `spearman_r`, `spearman_p`.

- [ ] **T009** [FR‑010 · FR‑011 · SC‑001] **Detect tipping point and, if applicable, execute ±8‑patch sensitivity sweep**  
  - **Path**: `code/analysis/tipping_point.py` → `data/analysis/tipping_point.json`, `data/analysis/sweep_results.parquet` (only when a sweep is performed)  
  - **Verification**:  
    1. JSON field `status` is `"found"` or `"none"` and, when `"found"`, `window_size` matches the smallest sparsity window where dense‑scene mean mIoU < 0.80.  
    2. When a sweep runs, the sweep parquet contains exactly the clamped window sizes (±8 patches, limited to 1‑64).

- [ ] **T010** [FR‑003] **Create a fixed‑seed hold‑out set for attribution analysis**  
  - **Path**: `code/data/create_holdout.py` → `data/holdout/holdout_set.parquet` (200‑image sample, balanced dense / non‑dense)  
  - **Verification**: `tests/unit/test_holdout.py` confirms file existence, exactly 200 rows, and reproducibility with the same random seed.

- [ ] **T011** [FR‑005 · SC‑004] **Attribution on failure vs. success cases (Grad‑CAM or attention rollout)**  
  - **Path**: `code/analysis/attribution.py` → heatmaps under `figures/attribution/failure_<id>.png` and `figures/attribution/success_<id>.png`; summary `data/analysis/attribution_summary.json`  
  - **Verification**:  
    1. Script runs only on the hold‑out set from T010.  
    2. Summary JSON contains keys `global_context_activation_diff`, `failure_mean`, `success_mean` with values in [0, 1].  
    3. `tests/unit/test_attribution.py` checks that at least one heatmap file is created and that the proportion column is populated for those rows.

- [ ] **T012** [SC‑001 · SC‑002 · SC‑003 · SC‑004 · SC‑005 · SC‑006 · SC‑007] **Generate all result tables and figures**  
  - **Path**: `code/analysis/reporting.py` →  
    - `data/analysis/degradation_curve.csv` & `figures/degradation_curve.png`  
    - `figures/anova_summary.png`  
    - `figures/correlation_plot.png`  
    - `figures/latency_bar.png`  
    - `figures/attribution_collage.png`  
    - `data/analysis/exclusion_log.json` (re‑used)  
  - **Verification**:  
    1. Each CSV/JSON loads without error.  
    2. Each PNG is a non‑empty image file (`tests/unit/test_reporting.py`).  
    3. All SC metrics (p‑value, correlation coefficients, latency budget, exclusion proportion, “N/A” flag for low‑density images) are present in the generated artifacts.

- [ ] **T013** [SC‑001] **Verify Single Source of Truth (SSoT) for all generated artifacts**  
  - **Path**: `code/analysis/ssv_check.py` → `data/analysis/ssv_report.json`  
  - **Verification**: `tests/unit/test_ssv_check.py` asserts that every figure/table references exactly one CSV/Parquet source and reports any violations; CI fails on breach.

---

## Phase 3 – Reproducible results and paper handoff

- [ ] **T014** [SC‑001 · SC‑006] **Write concise methods & results markdown linked to concrete artifacts**  
  - **Path**: `docs/results.md` – sections *Dataset*, *Sparsity Configurations*, *Degradation Curve*, *Statistical Findings*, *Attribution Insights*, each citing the exact CSV/PNG files produced above.  
  - **Verification**: Script `scripts/verify_results_md.py` checks that every referenced file exists; CI logs a manual‑review step confirming the links.

- [ ] **T015** [SC‑001 · SC‑005] **Full reproducibility run‑through (raw download → final report)**  
  - **Path**: `bash run_full_pipeline.sh` (or `make full`) orchestrates tasks in order T001 → T015.  
  - **Verification**: CI job `reproducibility.yml` executes the script on a fresh runner; it passes only if all intermediate artifacts are regenerated and the final `docs/results.md` matches the committed version (hash comparison).

--- 

### Dependency & Requirement Mapping (summary)

| Requirement | Satisfied by Task(s) |
|-------------|----------------------|
| FR‑001 | T003, T004 |
| FR‑002 | T006 |
| FR‑003 | T002, T011 |
| FR‑004 | T008 |
| FR‑005 | T011 |
| FR‑006 | T004, T007 |
| FR‑007 | T002 |
| FR‑008 | T002 (low‑density handling) |
| FR‑009 | T006 (optional 1‑patch) |
| FR‑010 | T009 |
| FR‑011 | T009 |
| SC‑001 | T006, T009, T012 |
| SC‑002 | T008 |
| SC‑003 | T008 |
| SC‑004 | T011 |
| SC‑005 | T006 |
| SC‑006 | T002 |
| SC‑007 | T002 (N/A flag) |

--- 

*All tasks remain unchecked until their implementation and verification succeed. Once a task is checked, the CI will lock its artifact hashes, ensuring reproducibility.*
