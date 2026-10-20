# Tasks: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

**Inputs**: `spec.md`, `plan.md` (from `specs/001-the-impact-of-musical-training-on-functi/`)

**Mode note**: No verified open dataset currently provides adolescent rs-fMRI plus a musical-training variable; per the plan's re-plan trigger, the default run is **synthetic verification mode** (machinery validation, no injected group effect). FR-001's real-data clause and FR-011's real-data validation clause remain **deferred/unmet** until the re-plan trigger fires; the real-data ingestion path is a graceful stub that reports data-source unavailability and exits 0 — it must NEVER fall back to synthetic data silently. The dropped "musical aptitude" term from the validated research question is a spec-level gap flagged for kickback (no verified dataset provides an aptitude measure); it is recorded in `research.md` rather than fabricated.

## Phase 1 — Repair entry points and run a first end-to-end analysis

- [ ] T001 [P] [US-1] Repair the four failing entry points and document the runnable command in `specs/001-the-impact-of-musical-training-on-functi/quickstart.md` <!-- FAILED-IN-EXECUTION: code/main.py exit=1; code/data/run_synthetic_generator.py exit=1; code/run_quickstart_test.py exit=5 --> <!-- FAILED-IN-EXECUTION: code/run_quickstart_test.py exit=5 --> <!-- FAILED-IN-EXECUTION: code/data/run_synthetic_generator.py exit=1; code/run_quickstart_test.py exit=5 --> <!-- FAILED-IN-EXECUTION: code/run_quickstart_test.py exit=5 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1; code/data/run_synthetic_generator.py exit=1; code/run_quickstart_test.py exit=5 -->
  - Fix `code/main.py` (verifier: exit=2): correct argparse so `python code/main.py --mode synthetic --n-subjects 100 --seed 42` runs end-to-end; add `--n-permutations` and `--seed` flags. Verify only argparse parsing, `--help` output, and that `code/data/real_ingest.py` stub exits cleanly with a status JSON when no dataset is supplied.
  - Fix `code/data/run_synthetic_generator.py` (exit=1): standalone executable with `if __name__ == "__main__"` and importable-from-repo-root relative imports.
  - Fix `code/data/real_ingest.py` (exit=1): when no verified dataset path is supplied, print a clear "data source unavailable" message, write a JSON status file, and exit 0 — never an unhandled exception, never a synthetic fallback (spec edge case: unavailable data source).
  - Fix `code/run_quickstart_test.py` (exit=5): subprocess‑invoke the **quickstart smoke test** (see T009) after the synthetic pipeline has produced artifacts; assert exit 0 and schema‑valid outputs.
  - *Verification*: `python code/run_quickstart_test.py` exits 0 **after** T002‑T004 have succeeded; `python code/main.py --mode synthetic --n-subjects 100 --seed 42` completes without error; `python code/data/real_ingest.py` exits 0 with the unavailability status JSON.

- [ ] T002 [P] [US-1] Synthetic verification cohort with controlled quality defects — `code/data/synthetic_generator.py` (invoked via `code/data/run_synthetic_generator.py`) <!-- FAILED-IN-EXECUTION: code/data/run_synthetic_generator.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/run_synthetic_generator.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/run_synthetic_generator.py exit=1 -->
  - Balanced cohort, default 100 subjects, capped at 75/group; `years_of_training ~ Uniform(1,10)` for musicians, 0 otherwise; age ~ N(15,1); sex 50/50; motion ~ N(0.15,0.05); SES ~ N(0,1); mock 64³ Gaussian‑noise NIfTI per subject. **No systematic group effect by default** (null‑first false‑positive verification). Optional `--inject-effect` (d≈0.4) exists only for the T007 power simulation.
  - Inject a small seeded rate of missing training‑history values and corrupted NIfTI files (logged) so preprocessing exclusions and the SC‑005 audit have a real failure mode.
  - *Outputs*: `data/raw/mock_nifti/`, `data/processed/subjects.parquet`.
  - *Verification*: `pytest code/test_synthetic_generator.py` confirms `subject.schema.yaml` compliance and every musician has `years_of_training ≥ 1`.

- [ ] T003 [US-1] Preprocessing, confound matching, and inclusion audit — `code/data/preprocess.py`
  - Applies the strict ≥1‑year threshold (0 years + "some experience" → non‑musician); drops missing training history with a logged exclusion count; skips+logs corrupted NIfTI files; propensity matching (nearest‑neighbor, caliper 0.2 SD) on age/sex/motion/SES, then edge‑wise linear residualization of the matched sample; halts with "Sample Size Insufficient" (also logging "Insufficient Data for Power" for traceability) if either group < 50.
  - *Outputs*: `data/processed/subjects_cleaned.csv`, `data/processed/dataset_validity_report.csv` (with `valid_subjects_percentage ≥ 90`, SC‑005), `data/processed/matching_balance_report.csv`, exclusion log under `data/logs/`.
  - *Verification*: `pytest code/test_ingestion.py` checks columns, ≥90 % validity, musician/non‑musician label consistency, and the <50‑per‑group halt.

- [ ] T004 [US-2] Connectivity matrices and network metrics — `code/analysis/connectivity.py`, `code/analysis/atlas.py`, `code/analysis/network_metrics.py`
  - Bundled Schaefer‑200 atlas CSV (no download); per‑subject Pearson correlation + Fisher r‑to‑z; per‑subject connectivity JSON (`data/processed/connectivity/<subject_id>.json`, `connectivity.schema.yaml`‑valid) and per‑subject network‑mean connectivity for auditory/motor/executive networks (`data/processed/network_metrics/<subject_id>.json`, `network_metric.schema.yaml`‑valid).
  - *Verification*: `pytest code/test_connectivity.py` asserts symmetric z‑matrices with zero diagonal and a spot‑check reproduces `numpy.corrcoef`; `pytest code/test_network_metrics.py` asserts networks ⊆ {auditory, motor, executive} and rows = subjects × 3.

- [ ] T012 [P] Memory‑usage enforcement implementation and testing — `code/utils/memory_monitor.py` (enhanced)
  - Implements adaptive fallback: monitors peak RAM; if a step exceeds 7 GB it first attempts streaming (chunked processing); if still over, applies deterministic seeded subsetting (recorded in logs); if unable to reduce below limit, aborts with clear error. Includes unit tests (`code/tests/test_memory_monitor.py`) verifying enforcement on synthetic large‑matrix workloads.
  - *Verification*: `pytest code/tests/test_memory_monitor.py` asserts that for a synthetic matrix >7 GB the monitor triggers subsetting and that final peak RAM ≤7 GB; also checks that a normal run records peak RAM without abort.

- [ ] T009 [P] Phase‑1 checkpoint – end‑to‑end quickstart validation
  - Runs the full synthetic pipeline (`code/main.py --mode synthetic …`) after T002‑T004 have produced valid artifacts, then executes `code/run_quickstart_test.py` to verify that all schema‑valid outputs are generated and exit codes are correct.
  - *Verification*: `python code/run_quickstart_test.py` exits 0 and all output files pass JSON‑schema validation.

## Phase 2 — Complete statistical analysis

- [ ] T005 [US-2] Edge‑wise group comparison and NBS — `code/analysis/stats.py`
  - Welch's t‑test per edge within auditory/motor/executive networks on residualized connectivity; Benjamini‑Hochberg FDR (FR‑003); Cohen's d and bootstrap 95 % CIs (FR‑007); permutation‑based NBS (default 1000 permutations, thresholds t ∈ {1.8, 2.0, 2.5}) with largest‑component size and FWER‑corrected p (FR‑008, SC‑001).
  - *Outputs*: `data/results/statistical_results.csv` (`statistical_result.schema.yaml` fields), `data/results/nbs_components.json` (`network_component.schema.yaml`‑valid).
  - *Verification*: spot‑check reproduces `scipy.stats.ttest_ind(..., equal_var=False)` to ≤1e‑6; `pytest code/test_stats.py` validates columns and BH q‑values; no edge is required to survive threshold.

- [ ] T006 [US-3] Training‑duration correlation and sensitivity analysis — `code/analysis/correlation.py`, `code/analysis/sensitivity.py`
  - Musicians‑only Pearson (Spearman on non‑normality) between `years_of_training` and connectivity strength (FR‑004, SC‑002); BH FDR; r, p, q, effect size, 95 % CI. Sensitivity sweep **p‑value** thresholds {0.01, 0.05, 0.10} with significant‑connection counts, percentage reduction 0.05→0.01, and "low stability" flag when the 95 % CI includes zero at the stricter threshold (FR‑005, SC‑003).
  - Runtime assertion: the correlation stage must complete within 5 minutes; duration recorded in `data/results/verification_run_summary.csv`.
  - *Outputs*: `data/results/correlation_results.csv`, `data/results/sensitivity_analysis.csv`.
  - *Verification*: `pytest code/test_correlation.py` checks musician‑only rows, runtime ≤5 min, and stability‑flag logic; `pytest code/test_sensitivity.py` recomputes counts from `statistical_results.csv`.

## Phase 3 — Validation, aggregation, and figures

- [ ] T007 [P] Machinery validation: null false‑positive control and power simulation
  - Null synthetic cohort (no injected effect) yields FDR/NBS false‑positive rates at nominal levels – validates statistical machinery only (does **not** satisfy FR‑011). Separate effect‑injected runs (d≈0.4) estimate detection rate (power limitation). Also verifies corrupted‑NIfTI skipping and the <50‑per‑group halt behavior.
  - *Outputs*: `data/results/validation_checks.csv`, `data/results/power_simulation.csv`.
  - *Verification*: `pytest code/test_validation_checks.py` confirms null‑control, detection‑rate, corruption‑handling, and halt behaviours.

- [ ] T007a [P] Edge‑case behaviours (corrupted files & sample‑size halt)
  - Explicitly tests that corrupted NIfTI files are logged and skipped, and that the pipeline aborts with the exact message "Sample Size Insufficient" when either group falls below 50 subjects.
  - *Verification*: `pytest code/test_edge_cases.py` checks log entries and exit messages.

- [ ] T008 [P] Aggregate SSoT results
  - Builder that reads all previous result files and writes `data/results/results_summary.csv` (FR‑010) aggregating group stats, network metrics, correlations, sensitivity table, and NBS summary – the sole downstream reference.
  - *Verification*: `pytest code/test_summary.py` reads the summary back and confirms consistency with source CSV/JSON files.

- [ ] T008a [P] Connectivity heatmap figure
  - `code/analysis/plot_connectivity.py` generates group‑mean z‑matrix heatmaps (`data/results/fig_connectivity_heatmap.png`).
  - *Verification*: `pytest code/test_visuals.py` re‑runs the plot and checks pixel‑hash stability.

- [ ] T008b [P] NBS component figure
  - `code/analysis/plot_nbs.py` visualises the largest NBS component graph (`data/results/fig_nbs_component.png`).
  - *Verification*: same `pytest code/test_visuals.py` validates reproducibility of the figure.

- [ ] T010 [P] Runtime & memory recording
  - `code/utils/memory_monitor.py` records peak RAM usage and total runtime for the entire pipeline; results appended to `data/results/verification_run_summary.csv` (supports SC‑004).
  - *Verification*: `pytest code/test_memory_monitor.py` asserts recorded peak ≤7 GB for synthetic runs.

## Phase 4 — Documentation and paper‑stage handoff

- [ ] T011 [P] Methods/results account and handoff — `specs/001-the-impact-of-musical-training-on-functi/research.md`, `quickstart.md`
  - Document each pipeline stage, the null‑first verification results, the power‑simulation estimate, the distribution of `years_of_training` within musicians (addressing the ≥1‑year cutoff concern), and the dropped "musical aptitude" term (spec‑level gap). State explicitly that FR‑001's real‑data clause and FR‑011 are **deferred/unmet** pending a verified dataset. Include exact reproducible commands from a clean checkout and the paper‑stage handoff (tables/figures above, limitations, deferred real‑data path).
  - *Verification*: `pytest code/test_documentation.py` confirms every referenced artifact path exists and the deferred‑status disclaimer is present.

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|------------|---------|-----------------------|
| FR-001 (synthetic clause; real clause DEFERRED) | T002, T003 | `python code/data/run_synthetic_generator.py --n-subjects 100` |
| FR-002 | T004 | `pytest code/test_connectivity.py` |
| FR-003, FR-007, FR-008, SC-001 | T005 | `pytest code/test_stats.py` |
| FR-004, SC-002 | T006 | `pytest code/test_correlation.py` |
| FR-005, SC-003 | T006 | `pytest code/test_sensitivity.py` |
| FR-006, SC-004 | T012, T010 | `python code/main.py --mode synthetic …` (memory/runtime log) |
| FR-009 | T003 | `pytest code/test_ingestion.py` |
| FR-010 | T008 | read‑back of `data/results/results_summary.csv` |
| FR-011 | **UNMET/DEFERRED** — T007 validates machinery only | re‑plan trigger in plan.md |
| SC-005 | T003 | `dataset_validity_report.csv` ≥ 90 % |
| Edge cases (corruption, <50/group, unavailable source) | T001, T003, T007a | `pytest code/test_edge_cases.py` |
| Documentation handoff | T011 | `pytest code/test_documentation.py` |

**Execution order**: T001 → T002 → T003 → T004 → T012 → T009 → T005 → T006 → T007 → T007a → T008 → T008a → T008b → T010 → T011. All tasks write only project‑owned paths under `data/`, `code/`, and the feature’s `specs/` directory. 
