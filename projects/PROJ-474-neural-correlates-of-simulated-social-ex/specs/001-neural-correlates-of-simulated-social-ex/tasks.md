# Tasks: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

**Inputs**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, contracts, and existing artifacts.
All paths are relative to the project directory. All computation is CPU-only (2 cores, ~7 GB RAM, ~14 GB disk, ≤6 h); no synthetic or placeholder data are ever generated — every metric derives from the real OpenNeuro `ds000030` recordings and event timings.

**Metric definition (spec-authoritative)**: Per spec FR-005, the **primary** outcome is the **sign-preserving mean Pearson correlation** averaged across all unique ROI-pair edges; the primary contrast is the difference (Exclusion − Inclusion). The **mean absolute correlation** is additionally reported as a secondary, Constitution-Principle-VII-derived metric. *Kickback flag:* spec FR-005 (signed primary) and Constitution VII (absolute correlation) conflict; this task list follows the spec's MUST-level FR-005 and does not weaken it — the spec/constitution reconciliation must be recorded spec-side before paper stage.

**ROI configuration (spec-authoritative)**: FR-003 defines four DMN ROIs (PCC, mPFC, L_ANG, R_ANG), yielding a 4×4 correlation matrix and **six** unique ROI-pair edges. The plan's three-ROI/three-edge description is stale; task T014 updates the contracts and data model to the four-ROI configuration. *Kickback flag:* plan.md Summary step 3 and FR-003 mapping row must be corrected.

**Storage-format note**: Tabular processed artifacts (per-subject strength table, dynamic series, dynamic summary) are written as **Parquet** under `data/processed/` and `data/results/`, per plan.md Technical Context and data-model.md Data Flow. Single schema-validated records (connectivity, statistical result) remain JSON because the JSON-Schema contracts validate JSON documents. *Kickback flag:* plan/data-model wording should acknowledge this JSON-for-schema-records exception.

**Dataset-paradigm verification**: `ds000030` is assumed (spec Assumptions) to contain Cyberball Inclusion/Exclusion event markers. T001/T012 verify this against the actual `events.tsv` contents and abort loudly (error 101897695) if the paradigm is absent — the pipeline never substitutes a different dataset or synthetic stand-in. *Kickback flag:* reviewers note ds000030 is the UCLA Neuropsychiatric Phenomics dataset; if the paradigm check fails at runtime, the failure is surfaced for scope revision, not worked around.

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [US1] Implement the dataset download module `code/data_loader.py` that downloads the verified dataset `ds000030` from `https://openneuro.org/datasets/ds000030` using the OpenNeuro API (e.g. the `openneuro` Python package / `[UNRESOLVED-CLAIM: https://openneuro.org/crn/datasets/ds000030/subjects/{sub}?type=func` — HTTP 404] endpoints), streaming files one subject at a time so peak disk stays within ~14 GB and RAM within ~7 GB.
  - Implement retry with exponential backoff (1 s → 2 s → 4 s, 3 attempts) per FR-013; on final failure raise `DataUnavailableError` (`ERR_DATA_UNAVAILABLE`). The loader must FAIL LOUDLY on fetch failure — never fall back to synthetic, mock, or bundled data.
  - Verify file integrity per FR-001: downloaded NIfTI files open with `nibabel` and have size > 0; a corrupt or empty download raises rather than silently continuing.
  - Write the BIDS tree to `data/raw/ds000030/`.
  - Single verifiable deliverable: `data/raw/ds000030/` contains downloadable subject files that pass the integrity check.

- [ ] T012 [US1] Implement event parsing and dataset manifest in `code/data_loader.py` (extends T001's module):
  - Parse each subject's `events.tsv` and `*_confounds.tsv`; verify both "Inclusion" and "Exclusion" trial types exist, else abort with error code `101897695` per FR-010. This is the dataset-paradigm verification step: if the Cyberball markers are absent, the run fails loudly for scope revision.
  - Write `data/processed/dataset_manifest.json` listing subject IDs, run IDs, TR (from BIDS JSON side-cars), and available conditions.
  - Update `specs/001-neural-correlates-of-simulated-social-ex/quickstart.md` with the exact runnable command (`python code/data_loader.py --dataset ds000030 --output data/raw`).
  - Tests in `code/tests/test_data_loader.py`: a missing-marker events file triggers 101897695; a corrupt download raises.
  - Single verifiable deliverable: manifest exists and tests pass.

- [ ] T002 [US1] Implement motion QC in `code/qc.py`: compute mean framewise displacement per subject from the BIDS `*_confounds.tsv` (Power FD definition using motion derivatives; use the precomputed `framewise_displacement` column when present) and flag subjects with mean FD > 0.2 mm (FR-002).
  - Output initial `data/processed/subjects_metadata.json` (fields per `contracts/subject.schema.yaml`: `subject_id`, `motion_mean`, `qc_status`, `conditions`).
  - Tests in `code/tests/test_qc.py`: a subject with mean FD > 0.2 mm is flagged `failed`; boundary FD = 0.2 mm retains the subject.
  - Single verifiable deliverable: `subjects_metadata.json` with per-subject QC status.

- [ ] T003 [US1] Implement raw ROI extraction and condition segmentation in `code/roi_extractor.py` for each subject passing motion QC (FR-003):
  - Load the 4-D BOLD NIfTI with `nibabel` (`mmap=True`, streaming) and extract the mean BOLD time-series for the four Harvard-Oxford DMN ROIs (PCC, mPFC, L_ANG, R_ANG) **before any nuisance regression** — the spec (FR-004) mandates raw time-series for connectivity. No confound-regression deliverable is included (the FR-019 reference in the prior revision cited a nonexistent requirement and has been removed).
  - Segment the raw time-series into Inclusion and Exclusion conditions using the verified `events.tsv` onsets/durations aligned to TR.
  - Save per subject/condition to `data/processed/raw_timeseries_{subject_id}_{condition}.parquet` (columns: `timepoint`, `PCC`, `mPFC`, `L_ANG`, `R_ANG`).
  - Validate each record against `contracts/timeseries.schema.yaml` (via a JSON side-record per subject/condition); subjects missing any required ROI column or with zero-variance ROI are flagged for exclusion per FR-014.
  - Test in `code/tests/test_roi_extractor.py`: on one real retained subject, four ROI columns of equal length matching the condition's TR count; zero-variance ROI triggers exclusion.
  - Single verifiable deliverable: raw per-subject/condition ROI time-series files.

- [ ] T013 [US1] Implement final cohort validation in `code/qc.py` (cohort stage):
  - **FR-011 (explicit):** exclude any subject lacking valid time-series for **either the Inclusion or the Exclusion condition** from the paired analysis.
  - **FR-014:** exclude any subject whose extraction failed for any required DMN ROI.
  - Update `data/processed/subjects_metadata.json` and write `data/processed/qc_report.json` containing the final retention rate (SC-001).
  - **Pipeline Guard:** halt with error `101897696` if the final retained N < 10 (FR-009).
  - Single verifiable deliverable: `qc_report.json` with retention rate and final retained-subject list.
  - *Kickback flag:* plan.md's FR-011 mapping row mislabels FR-011 as FR-014's ROI-failure rule; the plan row must be corrected.

- [ ] T014 Update the project contracts and data model to the spec-authoritative four-ROI configuration BEFORE any connectivity computation (resolves the contract/tasks contradiction):
  - Edit `specs/001-neural-correlates-of-simulated-social-ex/contracts/connectivity.schema.yaml`: `strength_absolute` description becomes "mean absolute correlation across the **six** ROI edges (secondary metric)"; add `strength_signed` as a required field described as "PRIMARY metric — sign-preserving mean Pearson correlation across the six ROI edges (FR-005)"; nodes become `["PCC","mPFC","L_ANG","R_ANG"]` with a 4×4 matrix.
  - Edit `specs/001-neural-correlates-of-simulated-social-ex/data-model.md`: TimeSeries `roi` enum becomes `PCC, mPFC, L_ANG, R_ANG`; ConnectivityMatrix nodes `["PCC","mPFC","L_ANG","R_ANG"]`, 4×4 matrix, six unique edges; `strength_signed` marked primary and `strength_absolute` secondary; DynamicSeries strength fields annotated accordingly.
  - Single verifiable deliverable: both files updated and internally consistent with FR-003/FR-005.

- [ ] T004 [US2] Implement static connectivity computation in `code/connectivity.py` and run it end-to-end on the final retained cohort:
  - Per subject and condition, compute the 4 × 4 Pearson correlation matrix directly from the raw ROI time-series produced by T003 (FR-004), across the six unique ROI-pair edges.
  - Derive `strength_signed` — the **sign-preserving mean Pearson correlation across the six edges — the PRIMARY metric per FR-005** — and `strength_absolute` (mean absolute correlation, Constitution-VII secondary metric), plus per-edge signed values.
  - Write `data/processed/connectivity_{subject_id}_{condition}.json` validated against the UPDATED `contracts/connectivity.schema.yaml` (T014), and a cohort table `data/results/strength_per_subject.parquet` with columns `subject_id, inclusion_signed, exclusion_signed, difference_signed, inclusion_absolute, exclusion_absolute, difference_absolute` (SC-004; primary difference is `difference_signed`).
  - Tests in `code/tests/test_connectivity.py`: correlation of a real ROI pair recomputed with `numpy.corrcoef` matches; strength difference = exclusion − inclusion; signed and absolute metrics computed per their definitions.
  - **Checkpoint (direct module invocation — the orchestrator does not exist yet):** `python code/connectivity.py --input data/processed --output data/results --seed 42` runs on real data and produces the per-subject Parquet with N ≥ 10 rows.
  - Single verifiable deliverable: per-subject connectivity records + cohort strength table.

- [ ] T015 [US2] Implement dynamic (sliding-window) connectivity in `code/connectivity.py` (dynamic stage), separate from the static computation:
  - Sliding-window (30 s window, 5 s step, converted via TR) Pearson correlations producing a time-resolved strength series per condition (FR-018); report both signed and absolute windowed strength.
  - Write `data/processed/dynamic_{subject_id}_{condition}.parquet` (`window_center_sec`, `strength_signed`, `strength_absolute`).
  - Test in `code/tests/test_connectivity.py` (dynamic cases): window count equals `floor((T − 30s)/5s) + 1` for a series of length T.
  - Single verifiable deliverable: per-subject/condition dynamic series files.

## Phase 2: Complete the study and validate its evidence

- [ ] T016 Reconcile the duplicate statistical-result contracts BEFORE results are emitted: delete the superseded `specs/001-neural-correlates-of-simulated-social-ex/contracts/result.schema.yaml` and confirm `contracts/result_schema.schema.yaml` as the single authoritative result contract (fields: `metric`, `condition_comparison`, `p_value`, `effect_size`, `confidence_interval`, `is_associational`, `edge_p_values`, `edge_p_values_fdr`, `n_subjects`, `motion_threshold`). Update any code or docs referencing the deleted file.
  - Single verifiable deliverable: exactly one result contract remains, referenced consistently.

- [ ] T005 [US3] Implement the statistical testing module `code/stats.py`: non-parametric paired permutation test (exactly 10 000 permutations, per FR-006) on per-subject **signed** strength differences (Exclusion − Inclusion, the FR-005 primary outcome), reporting a two-tailed empirical p-value, Cohen's d, and a 95 % CI from the permutation distribution.
  - Accept an explicit `--seed` argument (FR-016); run edge-wise paired permutation tests for each of the six unique ROI edges with Benjamini–Hochberg FDR correction across edges.
  - Write `data/results/statistical_result.json` validating against `contracts/result_schema.schema.yaml` (the single authoritative contract after T016). Pin: `metric` = `"mean_signed_correlation"`, `condition_comparison` = `"Exclusion vs Inclusion"`, `is_associational: true`. Include `p_value`, `effect_size`, `confidence_interval`, `edge_p_values`, `edge_p_values_fdr`, `n_subjects`, `motion_threshold`. Additionally report the secondary absolute-metric test in the same JSON where the schema allows, or in a companion `data/results/statistical_result_absolute.json` using the same schema.
  - **Plan-derived note (not a spec SC):** with N ≈ 10–30 the test reliably detects only large effects (Cohen's d ≈ 0.8) at α = 0.05; this power limitation is reported honestly. *Kickback flag:* if SC-007 is desired as a spec success criterion it must be added to spec.md.
  - Tests in `code/tests/test_stats.py`: permutation count is exactly 10 000; p-value on swapped-sign differences is symmetric; identical seed reproduces identical p-value.

- [ ] T006 [US3] Implement visualization in `code/viz.py`, generating from the validated result artifacts (FR-015, FR-017):
  - `data/results/figures/null_distribution.png` — histogram of the permutation null distribution with the observed statistic marked;
  - `data/results/figures/strength_difference_bar.png` — bar plot of the observed mean signed difference with 95 % CI error bars;
  - `data/results/figures/heatmap_inclusion.png` and `heatmap_exclusion.png` — group-mean ROI correlation-matrix heatmaps with colorbars and axis labels (SC-003, SC-005);
  - `data/results/figures/dynamic_series.png` — group-mean sliding-window strength series per condition with ± SEM bands.
  - Test in `code/tests/test_viz.py`: all PNGs exist, are non-empty, and matplotlib figures contain titles, axis labels, and colorbars.

- [ ] T007 [US2] Complete the dynamic-connectivity summary — **descriptive only, per plan.md Summary step 6 (no multiple-comparison correction across windows)**:
  - Aggregate per-subject sliding-window series into `data/results/dynamic_summary.parquet` (per subject and condition: mean and SD of windowed signed and absolute strength, SC-006).
  - The window-wise FDR analysis and `dynamic_fdr.csv` from the prior revision have been REMOVED: the plan explicitly states sliding-window series are reported descriptively with no formal correction across time points. *Kickback flag:* if window-wise correction is desired, plan.md and spec.md must be amended to authorize it first.
  - Test in `code/tests/test_dynamic_summary.py`: row count = 2 × N_retained; mean/SD columns present and finite.
  - Single verifiable deliverable: dynamic summary table.

- [ ] T008 **Plan-derived supplementary analysis (authorized by no FR or SC in spec.md — flagged for spec kickback; retained because plan.md Summary step 9 requires it):** implement the motion-threshold sensitivity analysis in `code/sensitivity_analysis.py`: re-apply the QC filter at thresholds [0.2, 0.3, 0.4, 0.5] mm (reusing already-extracted time-series, no re-download), recompute the primary permutation test at each threshold (10 000 permutations, fixed seed), and record `{threshold, n_retained, p_value, effect_size}` rows in `data/results/sensitivity_curve.csv` plus a line plot `data/results/figures/sensitivity_curve.png` (p-value vs. threshold).
  - Halt any threshold arm whose retained N < 10 and record it as `insufficient_n` in the CSV rather than fabricating a result.
  - Test in `code/tests/test_sensitivity.py`: CSV has four threshold rows in ascending order; each row's n_retained is non-decreasing with threshold.

- [ ] T009 [US3] Implement the full orchestrator `code/main.py` wiring download → QC → ROI extraction → cohort validation → static + dynamic connectivity → statistics → figures, with `--seed` propagated end-to-end and error codes (`101897695`, `101897696`, `ERR_DATA_UNAVAILABLE`) surfaced as non-zero exits. Run the complete pipeline on the full retained cohort; all artifacts land under `data/processed/`, `data/results/`, and `data/results/figures/`.
  - Integration test in `code/tests/test_integration.py` — reproducibility with a DEFINED canonicalization procedure: re-run the stats stage with the same seed, load both `statistical_result.json` files with `json.load`, remove the `generated_at` key from each (the only permitted timestamp field), and assert `json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)`.
  - Seed-stability check per SC-002, with its limitation documented: re-running with 5 different seeds must yield p-value SD ≤ 0.01. **Documented limitation:** with N ≈ 10 the number of distinct paired permutations is only 2^10 = 1024, so p-values are nearly deterministic across seeds; the criterion is trivially satisfied at small N and does not by itself demonstrate inference stability — the test report states this explicitly rather than overclaiming.

## Phase 3: Reproducible results and paper handoff

- [ ] T010 Write `data/results/report.md`: a concise methods-and-results account generated from the actual result artifacts, stating the exact retained N, retention rate, motion threshold, primary (signed-metric) p-value, Cohen's d, 95 % CI, FDR-corrected edge-wise p-values, the secondary absolute-metric result, dynamic-series summary, sensitivity curve, and the power limitation (N-dependent detectable effect size). Frame all findings as **associational** and report negative/null results honestly. Link every figure and table to its file under `data/results/`.
  - Verification: implement `code/verify_report.py` that extracts numeric literals from `report.md` and asserts they match the values in `statistical_result.json`, `sensitivity_curve.csv`, or `dynamic_summary.parquet`.

- [ ] T011 Re-run the documented workflow from its declared inputs (`python code/main.py --seed 42` per `quickstart.md`), confirm all unit and integration tests pass (`pytest code/tests/`), confirm every contract-validating check passes against the schemas in `specs/001-neural-correlates-of-simulated-social-ex/contracts/` (as updated by T014/T016), and document the paper-stage handoff: the tables (`strength_per_subject.parquet`, `dynamic_summary.parquet`, `sensitivity_curve.csv`), figures (all PNGs under `data/results/figures/`), statistical summary (`statistical_result.json`), and report (`report.md`) are packaged for downstream manuscript preparation — formatting, references, and submission belong to the paper pipeline.

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR-001, FR-013 (ingest, retry, integrity) | T001 | `python code/data_loader.py --dataset ds000030 --output data/raw` |
| FR-010 (event markers / paradigm verification) | T012 | `pytest code/tests/test_data_loader.py` |
| FR-002 (motion QC) | T002 | `pytest code/tests/test_qc.py` |
| FR-003 (four-ROI extraction, raw series) | T003 | `pytest code/tests/test_roi_extractor.py` |
| FR-011 (both conditions present), FR-014 (ROI failure), FR-009 (N ≥ 10) | T013 | `python code/qc.py --stage cohort` |
| FR-004, FR-005 (static connectivity, signed primary metric) | T004 | `python code/connectivity.py --input data/processed --output data/results --seed 42` |
| FR-018 (dynamic connectivity) | T015, T007 | `pytest code/tests/test_connectivity.py` |
| FR-006, FR-016 (permutation test, seed) | T005, T009 | `python code/main.py --seed 42` |
| FR-015, FR-017 (figures) | T006 | `pytest code/tests/test_viz.py` |
| SC-001–SC-006 (spec success criteria) | T002, T013, T004, T005, T006, T007, T009 | integration tests + artifact checks |
| Plan-derived criteria (power note, descriptive dynamic reporting, sensitivity analysis — pending spec amendment) | T005, T007, T008 | report.md + kickback flags above |
| Contract consistency (connectivity schema, data model, result contract) | T014, T016 | schema files updated and referenced consistently |
| Paper handoff | T010, T011 | `data/results/report.md` exists and validates |

Execution order: T001 → T012 → T002 → T003 → T013 → T014 → T004 → T015 → T016 → T005 → T006 → T007 → T008 → T009 → T010 → T011. No task writes to `state/` or `.github/`; the platform derives artifact hashes at verification time.

**Outstanding kickbacks (plan/spec-rooted, not resolvable in tasks.md):**
1. plan.md must adopt the four-ROI/six-edge configuration (Summary step 3, FR-003 mapping row) — T014 fixes the contracts, but the plan text remains stale.
2. The spec FR-005 (signed primary) vs Constitution VII (absolute correlation) conflict must be reconciled spec-side; tasks follow FR-005 without weakening it.
3. plan.md's FR-006 Summary wording ("sufficiently large number") must restore "exactly 10 000"; its FR-011 mapping row must be corrected to the condition-availability definition.
4. SC-007/SC-008 and the sensitivity analysis need spec-level authorization (add to spec.md or formally mark supplementary).
5. plan.md/data-model.md Parquet wording should acknowledge the JSON-for-schema-records exception.
6. The ds000030 Cyberball-paradigm assumption needs verification at runtime (T012) and possible scope revision if the dataset lacks the required task markers.