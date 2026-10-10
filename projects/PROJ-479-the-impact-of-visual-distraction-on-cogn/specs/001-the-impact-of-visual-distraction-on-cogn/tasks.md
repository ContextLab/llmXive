---  
description: "Task list for feature 001‑visual‑distraction‑cognitive‑control"  
---  

# Tasks: The Impact of Visual Distraction on Cognitive Control in Remote Work Environments  

**Inputs**: `spec.md`, `plan.md`, existing artifacts in `code/`, `data/`, `results/`, `specs/…/contracts/`  

**Verification**: Every task must include a concrete verification step (unit‑/contract‑test, file‑existence check, schema validation, or runtime‑output check).  

---  

## Phase 1 – Setup & First End‑to‑End Analysis  

| ID | Parallel? | Description | Artifact(s) | Verification |
|----|-----------|-------------|-------------|--------------|
- [ ] T001 [P] **Create project skeleton** – Initialise directories `code/`, `data/`, `results/`, `tests/`, and `specs/001-visual-distraction-cognitive-control/`. | `.` | `ls -R` shows all directories. |
- [ ] T002 [P] **Add pinned dependencies** – Write `code/requirements.txt` with exact versions of `numpy`, `pandas`, `scikit-learn`, `scipy`, `opencv-python-headless`, `ultralytics>=8.0.0`, `matplotlib`, `seaborn`, `pillow`, `pytest`, `statsmodels`, `requests`, `openml`. | `code/requirements.txt` | `pip install -r requirements.txt` succeeds without version conflicts. |
- [ ] T003 [P] **Configure linting & formatting** – Add `ruff` and `black` configs; script `code/lint.sh` runs `ruff .` and `black --check .`. | `code/lint.sh` | `./code/lint.sh` exits with status 0. |
- [ ] T004 [P] **Create data‑folder hierarchy** – `data/raw/`, `data/processed/`, `data/processed/sanitized_images/`, `results/statistics/`, `results/plots/`, `results/sensitivity/`. | Directory tree | `tree data` shows expected sub‑folders. |
- [ ] T005 [P] **Implement logging utilities** – Functions `get_logger()` and `log_event()` in `code/utils.py`. | `code/utils.py` | Unit test `tests/unit/test_logging.py` passes. |
- [ ] T006 [P] **Implement SHA‑256 checksumming** – `compute_checksum(path)` in `code/utils.py`. | `code/utils.py` | Test `tests/unit/test_checksum.py` validates known checksum. |
- [ ] T007 [P] **Implement global random‑seed manager** – `set_global_seed(seed)` in `code/utils.py`. | `code/utils.py` | Test `tests/unit/test_seed.py` ensures reproducible RNG output. |
- [ ] T008 [P] **Implement structured error handler** – `log_error(key, message)` in `code/utils.py` for keys `unmatched_participant_ids`, `image_processing_failures`, `zero_variance_warning`. | `code/utils.py` | Contract test `tests/contract/test_error_logging.py` confirms JSON‑log entries. |
- [ ] T009 [P] **Create dataset schema** – `specs/001-visual-distraction-cognitive-control/contracts/dataset.schema.yaml`. | `specs/.../dataset.schema.yaml` | `jsonschema` validation against a tiny sample CSV passes. |
- [ ] T010 [P] **Create analysis‑output schema** – `specs/001-visual-distraction-cognitive-control/contracts/analysis_output.schema.yaml`. | `specs/.../analysis_output.schema.yaml` | Validation test `tests/contract/test_analysis_schema.py` passes. |
- [ ] T011 [P] **Implement PII‑sanitisation utility** – `sanitize_images(src_dir, dst_dir)` in `code/utils.py` (renames to `img_<sha256>.jpg`, strips EXIF, logs count). | `code/utils.py` | Integration test `tests/integration/test_sanitise.py` checks renamed files & EXIF removal. |
- [ ] T012 [P] **Create citations file** – `data/citations.yaml` with primary sources for Holm‑Bonferroni, OpenCV edge detection, Shannon entropy, YOLOv8, ASA p‑value statement. | `data/citations.yaml` | YAML lint passes; all required fields present. |

---  

## Phase 2 – Foundational (Blocks All User Stories)  

- [ ] T013 [P] **Add quick‑start guide** – `specs/001-visual-distraction-cognitive-control/quickstart.md` describing how to run the pipeline end‑to‑end. | `specs/.../quickstart.md` | Manual check: guide builds and runs `python -m code.run_pipeline`. |
- [ ] T014 [P] **Add PEP‑8 cleanup** – Run `ruff` and fix all reported issues. | `code/` | `ruff .` returns no violations. |
- [ ] T015 [P] **Add comprehensive unit tests** – Populate `tests/unit/` for edge‑density, color‑entropy, object‑count, bootstrap, Holm‑Bonferroni, power analysis. | `tests/unit/` | `pytest -q` reports 0 failures. |
- [ ] T016 [P] **Add integration test for full pipeline** – `tests/integration/test_full_pipeline.py` executes `python -m code.run_pipeline` on a tiny sampled dataset and checks that `results/report.md` is produced. | `tests/integration/` | Test passes on CI. |

---  

## User Story 1 – Data Acquisition & Pre‑processing (Priority P1)  

- [ ] T017 [US1] **Lookup real datasets** – `code/01_data_acquisition.py::lookup_real_datasets()` searches OpenML for Stroop/Flanker IDs, checks for `participant_id`, `reaction_time`, `accuracy`, `image_path`. Writes status JSON to `data/raw/lookup_status.json`. | `code/01_data_acquisition.py`, `data/raw/lookup_status.json` | Test `tests/unit/test_lookup.py` asserts correct JSON keys and boolean result. |
- [ ] T018 [US1] **Fetch real cognitive data** – If lookup fails, download OpenML dataset ID 4444 → `data/raw/cognitive_data.csv`. | `code/01_data_acquisition.py`, `data/raw/cognitive_data.csv` | Row‑count ≥ 100, ≤ 5 % missing values. |
- [ ] T019 [US1] **Fetch workspace images** – Query Unsplash API (`keywords: "home office", "desk", "workspace"`), download **N = 150** images to `data/raw/workspace_images/`. Save raw API response to `data/raw/unsplash_query_log.json`. | `code/01_data_acquisition.py`, `data/raw/workspace_images/`, `data/raw/unsplash_query_log.json` | Image count = 150; each file size > 10 KB. |
- [ ] T020 [US1] **Sanitise images** – Call `sanitize_images()` (T011) → sanitized images in `data/processed/sanitized_images/`. Update `data/raw/image_metadata.json` with new filenames. | `code/utils.py`, `data/processed/sanitized_images/`, `data/raw/image_metadata.json` | Log entry `sanitized_images: 150` appears in `logs/run.log`. |
- [ ] T021 [US1] **Proxy linkage** – `perform_proxy_linkage()` groups participants and images by `environment_tag`, assigns images to participants using a pinned seed, writes `data/processed/merged_data.csv` and seed file `data/processed/proxy_linkage_seed.txt`. | `code/01_data_acquisition.py`, `data/processed/merged_data.csv` | Merge file has ≥ 100 rows, no duplicate `participant_id`. |
- [ ] T022 [US1] **Synthetic fallback** – If after proxy linkage `merged_data.csv` has < 100 rows, generate synthetic dataset (N ≥ 100) with negative correlation between `visual_complexity` and `reaction_time` using Cholesky decomposition; write over `merged_data.csv`. | `code/01_data_acquisition.py` | Pearson r < ‑0.2, p < 0.05 on generated data. |
- [ ] T023 [US1] **Validate merged dataset** – `validate_and_mark()` checks ≤ 5 % missing per column, variance of `visual_complexity` > 0, writes marker file `data/processed/.ready`. | `code/01_data_acquisition.py`, `data/processed/.ready` | Marker exists; `cat data/processed/.ready` prints “READY”. |

---  

## User Story 2 – Visual‑Complexity Metric Extraction (Priority P1)  

- [ ] T024 [US2] **Edge‑density implementation** – `code/02_visual_metrics.py::compute_edge_density(img_path)` using OpenCV Canny, returns normalized value ∈ [0, 1]. | `code/02_visual_metrics.py` | Unit test `tests/unit/test_edge_density.py` passes for known image. |
- [ ] T025 [US2] **Color‑entropy implementation** – `compute_color_entropy(img_path)` using 256‑bin RGB histogram, Shannon entropy. | `code/02_visual_metrics.py` | Unit test `tests/unit/test_color_entropy.py` passes. |
- [ ] T026 [US2] **Object‑count implementation** – `compute_object_count(img_path)` runs YOLOv8‑nano (CPU) via `ultralytics`; returns integer count or `np.nan` on failure. | `code/02_visual_metrics.py` | Unit test `tests/unit/test_object_count.py` validates NaN handling. |
- [ ] T027 [US2] **Batch metric extraction** – Main block in `02_visual_metrics.py` waits for `data/processed/.ready`, iterates over `data/processed/sanitized_images/`, computes all three metrics, writes `data/processed/visual_metrics_intermediate.csv`. | `code/02_visual_metrics.py`, `data/processed/visual_metrics_intermediate.csv` | Row‑count matches image count; sample rows show non‑null values for edge & entropy, possible NaN for object count. |
- [ ] T028 [US2] **Merge metrics with participant data** – Inner join `visual_metrics_intermediate.csv` with `merged_data.csv` on `participant_id`; produce:  
  • `data/processed/final_analysis_data_all.csv` (keeps NaNs for object count)  
  • `data/processed/final_analysis_data_object_only.csv` (drops rows where object count = NaN). | `code/02_visual_metrics.py`, both CSVs | Log shows “All records: X, Object‑only records: Y”. |

---  

## User Story 3 – Statistical Analysis & Reporting (Priority P2)  

- [ ] T029 [US3] **VIF calculation** – `code/03_analysis.py::compute_vif()` reads `final_analysis_data_all.csv`, computes VIF for edge, entropy, object count (excludes NaNs as needed), writes `results/statistics/vif_report.json`. | `code/03_analysis.py`, `results/statistics/vif_report.json` | JSON contains keys `edge_density`, `color_entropy`, `object_count`. |
- [ ] T030 [US3] **PCA fallback** – `perform_pca_fallback()` runs if any VIF ≥ 5; PCA on the three metrics, stores first component as `pc1` in dataframe, writes `results/statistics/pca_report.json` (variance explained). | `code/03_analysis.py`, `results/statistics/pca_report.json` | JSON field `explained_variance[0]` ≥ 0.5. |
- [ ] T031 [US3] **Correlation analysis** – `run_correlation()` computes Pearson r & p for each predictor‑outcome pair (using `pc1` if PCA triggered, else raw metrics). Writes `results/statistics/correlation_results.json`. | `code/03_analysis.py`, `results/statistics/correlation_results.json` | JSON array length = 6, each entry has `predictor`, `outcome`, `r_value`, `p_value`. |
- [ ] T032 [US3] **Linear regression** – `run_regression()` fits OLS for each pair (or PCA path), outputs `results/statistics/regression_results.json` with β, 95 % CI, VIF, `pca_applied` flag. | `code/03_analysis.py`, `results/statistics/regression_results.json` | JSON entries contain required fields. |
- [ ] T033 [US3] **Holm‑Bonferroni correction (core implementation)** – `apply_holm_bonferroni()` calls `scipy.stats.multitest.multipletests(method='holm')` on all raw p‑values, writes corrected p‑values back into `correlation_results.json` and also creates `results/statistics/multiplicity_table.csv` (columns: `test_name`, `raw_p`, `adjusted_p`, `metric_pair`). | `code/03_analysis.py`, `results/statistics/multiplicity_table.csv` | CSV contains 6 rows; adjusted p‑values ≤ 1. |
- [ ] T034 [US3] **Bootstrap confidence intervals** – `run_bootstrap()` performs ≥ 1000 resamples of each correlation, stores mean r, 95 % CI in `results/sensitivity/bootstrap_results.json`. | `code/03_analysis.py`, `results/sensitivity/bootstrap_results.json` | JSON includes keys `mean_r`, `ci_lower`, `ci_upper` for each pair. |
- [ ] T035 [US3] **Generate scatter plots** – `generate_scatter_plots()` creates PNGs for every *significant* (Holm‑adjusted p < 0.05) pair, saved as `results/plots/plot_{predictor}_{outcome}.png`. | `code/03_analysis.py`, `results/plots/` | At least one PNG exists; file name matches pattern. |
- [ ] T036 [US3] **Assemble final statistics JSON** – `save_final_statistics()` consolidates correlations, regressions, VIF, PCA (if any), bootstrap CIs, Holm‑adjusted p‑values into `results/statistics/statistics.json` adhering to `statistics_output.schema.yaml`. | `code/03_analysis.py`, `results/statistics/statistics.json` | Schema validation passes. |
- [ ] T037 [US3] **Generate alpha‑threshold justification** – Reads `data/citations.yaml`, writes a ≥ 150‑word markdown file `results/statistics/alpha_threshold_justification.md` citing the ASA statement, and creates `results/statistics/word_count.json` with word count. | `code/03_analysis.py`, `results/statistics/alpha_threshold_justification.md`, `results/statistics/word_count.json` | Word count ≥ 150; citation present. |
- [ ] T038 [US3] **Generate methods citations markdown** – Extracts OpenCV, entropy, YOLO citations from `data/citations.yaml`, writes `results/statistics/methods_citations.md`. | `code/03_analysis.py`, `results/statistics/methods_citations.md` | All three primary sources appear. |
- [ ] T039 [US3] **Power analysis (a‑priori)** – `power_analysis_a_priori()` uses `statsmodels.stats.power.FTestPower` with effect size r = 0.3, α = 0.05, solves for N; writes markdown `results/statistics/power_analysis_a_priori.md` containing N, power, rationale. | `code/03_analysis.py`, `results/statistics/power_analysis_a_priori.md` | File reports N ≥ 100 and power ≥ 0.8 (or explains shortfall). |
- [ ] T040 [US3] **Power analysis (post‑hoc)** – `power_analysis_post_hoc()` computes achieved power from observed r, writes `results/statistics/power_analysis_post_hoc.md`. | `code/03_analysis.py`, `results/statistics/power_analysis_post_hoc.md` | File contains numeric power and brief interpretation. |
- [ ] T041 [US3] **Generate associational report (markdown)** – `generate_associational_report()` assembles sections (Methods, Results, Multiplicity, Power, Alpha justification, Methods citations) into `results/report.md`, enforces no causal language via a simple keyword filter, embeds random‑seed JSON block. | `code/03_analysis.py`, `results/report.md` | Manual spot‑check confirms absence of “cause”, “effect”, “impact”. |

---  

## User Story 4 – Sensitivity & Robustness Checks (Priority P3)  

- [ ] T042 [US4] **Bootstrap unit test** – `tests/unit/test_bootstrap.py` verifies ≥ 1000 iterations, deterministic seed, CI width reasonable. | `tests/unit/` | Test passes. |
- [ ] T043 [US4] **Alternative binning strategies** – `run_binning_sensitivity()` evaluates quartile and decile binning for each predictor‑outcome pair, writes `results/sensitivity/binning_results.csv` (columns: `binning_strategy`, `predictor`, `outcome`, `pearson_r`, `p_value`). | `code/03_analysis.py`, `results/sensitivity/binning_results.csv` | CSV contains 12 rows (6 pairs × 2 strategies). |
- [ ] T044 [US4] **Validate sensitivity outputs** – Contract test `tests/contract/test_sensitivity_schema.py` validates both bootstrap JSON and binning CSV against schemas. | `tests/contract/` | Test passes. |
- [ ] T045 [US4] **Final report integration** – `results/report.md` (from T041) is updated to include a “Sensitivity Analysis” section that renders the binning table (markdown) and summarizes bootstrap CI stability (directional consistency, Δr < 0.1). | `results/report.md` | Section header `## Sensitivity Analysis` present; tables rendered correctly. |

---  

## Phase N – Polish & Cross‑Cutting Concerns  

- [ ] T046 [P] **Update quick‑start with data‑source selection** – Add “Data Source Selection” and “Interpretation of Results” sections (real vs synthetic) to `quickstart.md`. | `specs/.../quickstart.md` | Sections appear with correct headings. |
- [ ] T047 [P] **PEP‑8 compliance sweep** – Run `ruff` again after all code changes. | `code/` | No violations reported. |
- [ ] T048 [P] **Edge‑case unit tests** – Add tests for image‑load failure and zero‑variance predictors (`tests/unit/test_edge_cases.py`). | `tests/unit/` | All new tests pass. |
- [ ] T049 [P] **End‑to‑end validation** – Execute `./run_all.sh` (calls `python -m code.run_pipeline`) on the full dataset; assert that `results/report.md` exists and contains at least one significant scatter plot. | `run_all.sh` | Script exits 0, report present. |
- [ ] T050 [P] **Record random seed in report** – `generate_associational_report()` appends `{"seed": <value>}` JSON block to Methods section (already covered in T041). | `results/report.md` | JSON block visible. |
- [ ] T051 [P] **Contract test for merged‑data schema** – `tests/contract/test_dataset_schema.py` validates `final_analysis_data_all.csv` against `dataset.schema.yaml`. | `tests/contract/` | Test passes. |
- [ ] T052 [P] **Document version & timestamps** – `code/utils.py` adds `record_metadata()` that writes `results/statistics/metadata.json` with software versions, git commit hash, timestamp. | `code/utils.py`, `results/statistics/metadata.json` | File contains required fields. |

---  

### Dependency Flow (high‑level)

1. **Phase 1 → Phase 2** – foundational utilities become available.  
2. **User Story 1** (T017‑T023) produces `data/processed/.ready`.  
3. **User Story 2** (T024‑T028) consumes the ready marker and outputs final analysis data.  
4. **User Story 3** (T029‑T041) consumes the final data, performs VIF/PCA, correlation, regression, Holm‑Bonferroni, bootstrap, plots, power analyses, and writes the full report.  
5. **User Story 4** (T042‑T045) consumes outputs from 3 to produce robustness tables and extend the report.  
6. **Phase N** runs linting, documentation, and final validation.  

---  

*All tasks above follow the canonical `- [ ] T### [P?] [USx?] description …` format, reference exact file paths, and include a concrete verification step.*
