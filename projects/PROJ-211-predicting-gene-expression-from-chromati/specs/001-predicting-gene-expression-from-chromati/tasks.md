# Tasks: Predicting Gene Expression from Chromatin Accessibility in Human Cells

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas in `specs/001-predicting-gene-expression-from-chromati/contracts/`, and existing verified artifacts.

The pipeline must use **real ENCODE data** for the scientific results; synthetic data is generated only for CI validation of pipeline logic and never substitutes for real results. All artifacts are written under project-owned directories (`code/`, `data/`, `interpretation/`, `docs/`, `logs/`). Tasks rejected by the independent verifier (T005a, T005b, T011, T015, T016c, T023, T026, T027) have been consolidated into the tasks below — each carries its prior acceptance criteria forward. The reviewer's causation-vs-correlation and bulk-averaging concerns are addressed in T012 (limitations master file) and the report caveat in T010.

---

## Phase 1 – Setup and first end-to-end analysis

- [ ] T001 [US1] Implement a complete, runnable synthetic data generator `code/generate_data.py` (fixing the previously truncated file) that (a) seeds `numpy.random` with `42`, (b) writes `data/raw/synthetic_counts.csv` and `data/raw/synthetic_peaks.bed` for the five cell lines (GM12878, K562, HMEC, IMR90, HepG2), (c) validates the outputs against `specs/001-predicting-gene-expression-from-chromati/contracts/dataset_schema.schema.yaml` using `jsonschema`/`yaml` loading, and (d) raises an exception on any schema mismatch — no silent fallback, no truncated stub. The schema file must be present and referenced by relative path from the repo root.
  - **Verification**: `python -m code.generate_data` exits 0; both files exist, are non-empty, contain rows for all five cell lines; `pytest tests/unit/test_generate_data.py` loads the schema and asserts conformity. (Repairs rejected T005a/T005b.)

- [ ] T002 [US1] Implement robust ENCODE download script `code/download_encode.py` that streams real resources and records SHA-256 checksums in `data/raw/checksums.csv` (project-owned; the platform derives its own state hashes):
  - RNA-seq gene quantification TSVs per cell line (query the ENCODE REST API `https://www.encodeproject.org/search/?type=Experiment&assay_title=total+RNA-seq&biosample_ontology.term_name={cell_line}&status=released&format=json`, then fetch the `gene quantifications` file via `requests` with `stream=True`, parsing in chunks) → `data/raw/encode_counts_{cell_line}.csv`
  - DNase-seq narrowPeak files per cell line (same API pattern with `assay_title=DNase-seq`, output type `peaks`) → `data/raw/encode_peaks_{cell_line}.bed`
  - GENCODE hg38 gene coordinates from `https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_44/gencode.v44.basic.annotation.gtf.gz`, streamed and reduced to TSS BED rows → `data/raw/gene_coords.bed`
  The script must raise on any HTTP error or empty response; no synthetic fallback is permitted. Process files one at a time and free memory between downloads to stay under 7 GB RAM.
  - **Verification**: Each file exists, is non-empty, checksum matches the recorded value; `pytest tests/integration/test_download.py` checks file headers (CSV columns per `dataset.schema.yaml`; BED ≥ 5 columns with `start < end`) and schema compliance. (Repairs rejected T011's real-data half.)

- [ ] T003 [US1] Implement preprocessing script `code/preprocess.py` that for each cell line:
  1. **Bin aggregation** (FR-002) — split the ±50 kb window around each TSS into 200 fixed-width bins, excluding the promoter region (TSS ± 2 kb, zeroed per the plan's circularity check), summing peak scores per bin → `data/processed/{cell_line}_binned_features.csv`
  2. **Gene filtering** (FR-003) — remove genes with zero expression across all five cell lines → `data/processed/filtered_expression.csv`
  3. **Log-pseudocount** (FR-004) — `log(count + 1)` → `data/processed/log_expression.csv`
  4. **Median imputation** (FR-005) — per-bin median across genes → `data/processed/imputed_binned_features.csv` (imputation applies to the binned feature matrix, not expression, per the data model)
  5. **Merge** — joint matrix concatenating the 200-bin features with the log-expression target → `data/processed/merged_matrix_{cell_line}.csv`
  - **Verification**: Each CSV has exactly 200 bin columns plus identifiers, contains no NaNs, passes schema validation against `dataset.schema.yaml`, and `pytest tests/unit/test_preprocess.py` succeeds on both synthetic and a small real-data slice. (Repairs rejected T015/T016c's missing-matrix half.)

- [ ] T004 [US1] Extend `code/preprocess.py` to compute gene-category metrics: coefficient of variation (CV) of log-expression across cell lines, writing `data/processed/housekeeping_genes.csv` (CV < 0.2), `data/processed/cell_type_specific_genes.csv` (CV > 0.5), and `data/processed/housekeeping_matrix.csv` (merged feature+target matrix restricted to housekeeping genes).
  - **Verification**: Both category files obey their CV bounds, are disjoint, and the matrix file contains exactly the rows listed in `housekeeping_genes.csv`; `pytest tests/unit/test_gene_categorization.py` passes.

**Checkpoint**: `python -m code.generate_data && python -m code.download_encode && python -m code.preprocess` executes end-to-end on real ENCODE inputs, and the binned matrices can be inspected numerically. No report writing from expected or invented results.

## Phase 2 – Complete the study and validate its evidence

- [ ] T005 [US2] Implement Elastic Net training script `code/train.py` that, per cell line (skipping lines with N < 4 samples per the plan's Sample Size Gate), trains Elastic Net (`l1_ratio=0.5`) with `alpha` selected by LOOCV over the 200-bin features: serialize models to `data/models/elastic_net_{cell_line}.pkl`, record chosen `alpha` in `data/models/lambda_optimal_{cell_line}.json`, and write per-fold CV metrics (`fold`, `r2`, `pearson_r`, `p_value`) to `data/processed/cv_scores_{cell_line}.json`. Log wall-time and peak RAM per cell line to `logs/profiling.log` (created by this run — the previously missing artifact), enforcing ≤ 6 h total and ≤ 7 GB RAM. CPU-only, serial execution.
  - **Verification**: All model files exist; `cv_scores_*.json` conforms to `model_output.schema.yaml`; `logs/profiling.log` exists with real measured timings/memory; `pytest tests/integration/test_training_loop.py` passes. (Repairs rejected T027.)

- [ ] T006 [US2] Implement a complete `code/evaluate.py` (fixing the truncated file) that consumes CV scores and model predictions to compute: (1) Pearson correlations and raw p-values per cell line → `data/processed/correlations.csv`; (2) Bonferroni-corrected p-values (m = 5 cell lines) as a `p_value_corrected` column (FR-006); (3) housekeeping-gene R² → `data/processed/housekeeping_r2.csv` (FR-009); (4) cell-type-specific R² → `data/processed/cell_type_specific_r2.csv`; (5) external validation (SC-006): train on four cell lines, test on the held-out fifth, rotating, → `data/processed/external_validation_r2.csv` (columns: `held_out_cell_line`, `r2`).
  - **Verification**: All CSVs exist with finite numeric values, adhere to the schemas, and `pytest tests/integration/test_evaluation.py` succeeds. (Repairs rejected T023/T026.)

- [ ] T007 [US3] Implement interpretation script `code/analyze.py` producing: (1) **Feature importance** (FR-007) — non-zero coefficients ranked by absolute magnitude → `interpretation/feature_importance.csv` (`gene_id`, `bin_id`, `coefficient`, `distance_to_tss`, `within_10kb`); (2) **TSS proximity stats** (FR-008, SC-003) — percentage of top-100 coefficients within ±10 kb of TSS, reported in `interpretation/tss_proximity_stats.json` (report the measured value; if the 80 % biological prior is not met, record the actual percentage and flag it as a finding, not a failure); (3) **Performance gap** (FR-010) — ΔR² = R²(housekeeping) − R²(cell-type-specific) per cell line → `interpretation/performance_gap.csv`.
  - **Verification**: Files exist; `feature_importance.csv` matches `model_output.schema.yaml` fields; `tss_proximity_stats.json` parses; `pytest tests/unit/test_interpretation.py` passes.

- [ ] T008 [US3] Generate figures and tables directly from validated outputs: `figures/r2_by_cell_line.png`, `figures/predicted_vs_observed_{cell_line}.png`, and `data/results/summary_table.csv` (per cell line: R², Pearson r, corrected p-value, external-validation R², ΔR²), all produced programmatically from `data/processed/` and `interpretation/` artifacts — no hand-typed numbers.
  - **Verification**: Each figure file exists and is regenerated by a documented command; every value in `summary_table.csv` traces to a row in the source CSVs.

- [ ] T009 [US3] Perform a **full end-to-end re-run** on the real ENCODE inputs (no synthetic data) via the documented workflow, capturing `logs/profiling.log` and confirming runtime/memory constraints are met. All artifacts are regenerated from the real data in one pass.
  - **Verification**: The profiling log shows ≤ 6 h total and ≤ 7 GB peak; all prior verification tests still pass on the regenerated artifacts. (Repairs rejected T011's execution half.)

## Phase 3 – Reproducible results and paper handoff

- [ ] T010 [US3] Draft the regulatory-insights summary `interpretation/regulatory_insights_report.md` (FR-011) including, per cell line: overall R² and Pearson r, external-validation R², top-10 features with distances and within-10 kb flags, and performance-gap values — every numeric token traceable to a CSV/JSON row. Include a caveat paragraph, in plain prose, referencing `docs/LIMITATIONS_MASTER.md` and explicitly stating that the models identify statistical associations between accessibility and expression, not causal regulatory links, and that bulk profiles average over single-cell heterogeneity (addressing the reviewer's concern directly).
  - **Verification**: `pytest tests/integration/test_report_consistency.py` asserts every number in the report matches its source artifact and that the caveat paragraph is present.

- [ ] T011 [US3] Consolidate all limitation statements into `docs/LIMITATIONS_MASTER.md` (bulk-profile averaging, correlation ≠ causation, ±50 kb window / distal-enhancer exclusion, small-N statistical validity with N = 3–5 per line, promoter-exclusion design choice) and update any legacy limitation references (e.g., `docs/regulatory_context.md`) to point to this master file.
  - **Verification**: The master file exists with all required sections; a repository search for "Limitations" returns only this file as the canonical source.

- [ ] T012 [US3] Write the reproducible workflow guide `quickstart.md` listing exact commands for the full pipeline (download → preprocess → train → evaluate → interpret), stating the Python version, that dependencies are in `requirements.txt`, and a clean-run command clearing `data/processed/*`, `data/models/*`, and `interpretation/*`. Then re-run the documented workflow from its declared inputs and confirm all tests and artifact checks pass.
  - **Verification**: Executing the guide's commands in a fresh clone reproduces all artifacts; the verification suite exits 0.

- [ ] T013 [US3] Create the paper-stage handoff manifest `docs/paper_handoff.yaml` enumerating versioned data files (paths and SHA-256 checksums) for processed matrices, model artifacts, and evaluation results; locations of figures/tables for the downstream paper pipeline; and a brief Methods block referencing task IDs. Paper layout, PDF compilation, and publication remain the paper pipeline's responsibility and are only named here.
  - **Verification**: The YAML validates against `docs/paper_handoff_schema.yaml` and `python -m code.verify_handoff` exits 0.

---

## Dependencies and requirement coverage

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR-001 (ENCODE download) | T002 |
| FR-002 (±50 kb aggregation) | T003 |
| FR-003 (zero-expression filter) | T003 |
| FR-004 (log pseudocount) | T003 |
| FR-005 (median imputation) | T003 |
| FR-006 (Bonferroni) | T006 |
| FR-007 (feature ranking) | T007 |
| FR-008 (TSS mapping) | T007 |
| FR-009 (housekeeping R²) | T006 |
| FR-010 (performance gap) | T007 |
| FR-011 (insights report) | T010 |
| SC-001 (interpretable models) | T005 |
| SC-002 (CPU-only) | T003, T005 |
| SC-003 (≥80 % within ±10 kb) | T007 |
| SC-004 (reproducible gap analysis) | T008, T010 |
| SC-005 (resource limits) | T002, T005, T009 |
| SC-006 (external validation) | T006 |
| US1 / US2 / US3 | T001–T004 / T005–T006 / T007–T013 |

Execution order is strictly data-flow respecting: T001–T002 (inputs) → T003–T004 (features/targets/categories) → T005 (models) → T006–T008 (evaluation, interpretation, figures) → T009 (full re-run) → T010–T013 (report, limitations, workflow, handoff). No evaluation task runs before the artifacts it consumes exist.
