# Tasks: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

**Inputs**: Active `spec.md`, `plan.md`, data model, and contracts from `specs/001-neural-correlates-of-temporal-prediction/`.

This is the smallest complete study answering the research question: download real OpenNeuro ds004510 EEG data, preprocess it, compute MMN metrics for simple vs. complex auditory scene conditions, statistically compare them, and produce validated result tables and figures.

## Task format and paths

Use `- [ ] T### [P?] [USx?] description with exact artifact paths`. Paths are relative to the project directory. Code lives in `code/`, tests in `code/tests/`, results in `data/results/`.

**Authoritative output layout**: all result artifacts live under `data/results/` (`data/results/metrics_per_subject.csv`, `data/results/metrics.csv`, `data/results/stats.json`, `data/results/figures/`). Research tasks write only project-owned paths (`data/`, `code/`, `figures/`, `paper/`, this `specs/` dir) and never write to `state/` or `.github/`. NOTE: `plan.md`'s Project Structure places outputs at `results/`; that divergence is a plan-root inconsistency flagged for plan amendment — `data/results/` is authoritative for all tasks and downstream consumers.

## Documented inconsistencies flagged for upstream amendment (kickback)

These cannot be fixed in tasks.md alone and are flagged for the owning artifact:

1. **Constitution Principle VI** names "OpenNeuro ds000246 or PhysioNet" as the dataset instance; every task uses **ds004510** per spec FR-001. The constitution must be amended to ds004510.
2. **output.schema.yaml** has no `subject_id` field, sets `additionalProperties: false`, and requires cohort-level statistics on every row, while `data-model.md`'s MMN Metric is per-subject. Tasks below resolve this operationally via a two-tier layout (per-subject file + cohort-level schema-conformant table), but the schema/data-model should be reconciled (add a per-subject schema or a `subject_id`-bearing variant).
3. **output.schema.yaml's `snr_ratio` description** says "SEM of pre-stimulus baseline" while FR-011/SC-001 define the noise floor as the **standard deviation**. Tasks implement the FR-011 SD definition (spec constraint level governs); the schema description should be amended to SD.
4. **plan.md Task 5.2** references `contracts/stats.schema.yaml`, which does not exist. Tasks validate `stats.json` against `contracts/output.schema.yaml` (array of row objects); the plan should be amended (or the schema created).
5. **plan.md Task 2.1** says "low-frequency bandpass filtering (up to 40 Hz)", dropping the 1 Hz high-pass; FR-002 mandates the full **1–40 Hz** band, which tasks implement.
6. **plan.md Task 4.3** says "topography maps for the –250ms window"; the correct MMN window is **150–250 ms**, which tasks implement.
7. **plan.md Tasks 2.3 / Constraints** paraphrase the epoch window instead of stating the concrete **−200 ms to 500 ms** bounds of FR-003, which tasks implement.
8. **FR-013** requires artifact hashes in `state/projects/…yaml`; research scripts must not write to `state/` (platform-owned, derived at verification time). Tasks record checksums under `data/raw/checksums.json`; the spec should be amended to delegate `state/` hash recording to the platform.

## Phase 1: Setup and first end-to-end analysis

**Goal**: Run an executable analysis on a small subset of real ds004510 data early.

- [ ] T001 [P] [US1] Implement `code/download.py` to fetch the OpenNeuro ds004510 dataset via `openneuro-py` (`openneuro.download(dataset="ds004510", target_dir="data/raw")`) or the S3 HTTPS endpoint `[UNRESOLVED-CLAIM: https://openneuro.org/crn/datasets/ds004510/` — HTTP 404], processing subjects iteratively (never loading all subjects at once) to stay within ~7 GB RAM. The loader MUST fail loudly on fetch errors — no synthetic or mock fallbacks. Verify file integrity via SHA-256 checksums of downloaded files recorded in `data/raw/checksums.json`. Validate that the dataset contains both 'simple' and 'complex' `condition_label` values in `events.tsv` metadata (FR-001, FR-008); if 'complex' is missing, halt with the exact message "Dataset lacks required 'complex' condition; research question untestable with current data." Validate metadata against `specs/001-neural-correlates-of-temporal-prediction/contracts/dataset.schema.yaml`. For the first end-to-end pass, download only 2–3 subjects as the small real subset.
  - Check: `python code/download.py --subjects 2` exits 0, `data/raw/` contains BIDS files, `data/raw/checksums.json` exists, and both condition labels are present.
  - Note: dataset download, metadata validation, and condition verification (plan Tasks 1.1–1.3, 3.1, 3.2) are bundled here; the platform derives artifact hashes itself — do not write to `state/`.

- [ ] T002 [US1] Implement `code/preprocess.py`: bandpass filter **1–40 Hz** (both cutoffs, per FR-002), ICA artifact rejection, average mastoid re-referencing, spherical-spline interpolation of <10% missing channels, and epoching at **-200 ms to 500 ms** with baseline correction (mean of -200 to 0 ms subtracted). ICA rejection criterion (US-1 acceptance scenario 2): fit ICA on filtered raw; reject components flagged by MNE's `find_bads_eog`/`find_bads_ecg` (correlation-based EOG/ECG detection) AND any components explaining >99% of variance; verify the reconstructed signal shows reduced blink/eye-movement contamination. Classify epochs as simple/complex from `condition_label` in `events.tsv` and standard/deviant from stimulus type (FR-002, FR-003, Edge Cases). Exclude subjects with >50% rejected epochs, logging exclusion counts to `data/processed/exclusions.csv`. Hard-stop if `np.isnan(epochs.get_data()).any()` is True. Save per-subject epochs to `data/processed/sub-XX_epo.fif`. Depends on T001's `data/raw/` output.
  - Check: run on the T001 subset; output epochs have the correct time window (-200 to 500 ms), sampling rate matching source, no NaNs, `data/processed/exclusions.csv` exists, and blink contamination is reduced post-ICA.

- [ ] T003 [US1][US2] Implement the per-subject computation in `code/analysis.py`: for each subject/electrode/condition, compute MMN amplitude (mean deviant-minus-standard difference, 150–250 ms window, fronto-central electrodes e.g. Fz, FCz, Cz) and latency (peak difference time in the same window), plus the noise floor — defined as the **standard deviation** of the -200 to 0 ms pre-stimulus baseline, per FR-011/SC-001 — and SNR = |amplitude_diff| / baseline SD, with `signal_validity = SNR >= 3.0` (FR-004, FR-011, SC-001). Run it on the T001/T002 subset and write real per-subject metric rows (subject_id, condition, electrode, amplitude_diff, latency_diff, snr_ratio, signal_validity — per-subject fields only; cohort-level statistical fields are produced later by T005) to `data/results/metrics_per_subject.csv`. Units: amplitude in µV, latency in ms.
  - Check: `data/results/metrics_per_subject.csv` exists with real measured values from the subset; no placeholder or random values; every row has a finite SD-based SNR.

**Checkpoint**: The documented command (`python code/main.py --subjects 2`) executes end-to-end on real data and its numerical outputs are checkable.

## Phase 2: Complete the study and validate its evidence

- [ ] T004 [US2] Extend the pipeline to the full ds004510 cohort: run download, preprocessing, and MMN quantification for all subjects iteratively (memory-mapped, one subject at a time), preserving all preprocessing parameters, exclusion rules, and condition constraints. Generate the canonical MMN topography template by averaging deviant-minus-standard topographies across all participants in the 'simple' condition, saving to `data/templates/canonical_mmn.npy`, with channel order matching the epochs montage; save the channel names in the same order to `data/templates/canonical_mmn_channels.json` so the template's channel order is verifiable (FR-009, SC-004). Update `data/results/metrics_per_subject.csv` with the full-cohort rows.
  - Check: `data/results/metrics_per_subject.csv` covers all non-excluded subjects and both conditions; `data/templates/canonical_mmn.npy` exists with one value per channel, and its length equals the number of entries in `canonical_mmn_channels.json`, which matches the epochs montage channel names in order.

- [ ] T005 [US2] Implement the statistical stage in `code/analysis.py`: paired t-tests comparing MMN amplitude/latency between simple and complex conditions across subjects, Benjamini-Hochberg FDR correction across electrodes, Cohen's d effect sizes, and comparison against the literature benchmark threshold d ≥ 0.5 loaded from `data/benchmarks/mmn_effect_sizes.json` (create this file citing the established medium-effect benchmark from Cohen, J. (1988), *Statistical Power Analysis for the Behavioral Sciences*, 2nd ed., which defines d ≥ 0.5 as a medium effect) (FR-005, FR-010, SC-002, SC-003). Compute topographic validation: Pearson r between each condition's observed MMN topography and the canonical template **loaded from `data/templates/canonical_mmn.npy` (produced by T004)**, using the channel order from `data/templates/canonical_mmn_channels.json`, tagged `validation_type` = "consistency_simple" or "validity_complex" (FR-009, SC-004, r ≥ 0.8 criterion recorded). Merge the cohort-level statistical fields (t_statistic, p_value, p_value_fdr, cohen_d, benchmark_reference, practical_significance, topographic_correlation, validation_type, significant) with the per-subject aggregates into the cohort-level result table `data/results/metrics.csv`, whose rows conform to `specs/001-neural-correlates-of-temporal-prediction/contracts/output.schema.yaml` (one row per electrode/condition). Write the same cohort-level rows to `data/results/stats.json` as a JSON array of objects, each conforming to `output.schema.yaml` (FR-015).
  - Check: `data/results/metrics.csv` rows and `data/results/stats.json` entries contain t-statistics, raw and FDR-corrected p-values, Cohen's d, `practical_significance`, `topographic_correlation`, and `significant` flags for every electrode/condition, and validate against `output.schema.yaml`.

- [ ] T006 [P] [US2] Implement `code/tests/test_contracts.py` (pytest) validating: (a) each row of the cohort-level `data/results/metrics.csv` against `specs/001-neural-correlates-of-temporal-prediction/contracts/output.schema.yaml`, (b) each entry of the `data/results/stats.json` JSON array against the same `output.schema.yaml` (note: plan Task 5.2's `contracts/stats.schema.yaml` does not exist; `output.schema.yaml` is the authoritative target — plan flagged for amendment), and (c) dataset metadata against `contracts/dataset.schema.yaml` (FR-014, FR-015). Include focused correctness tests for the MMN window computation (e.g., a synthetic analytic waveform with known amplitude difference verifies the windowed mean code — test fixture only, never a result), the SD-based SNR computation, and the FDR correction.
  - Check: `pytest code/tests/ -v` passes on the real outputs; tests fail if schema fields are missing or out of range.

- [ ] T007 [US3] Implement `code/visualize.py` generating publication-quality figures directly from `data/results/metrics_per_subject.csv`, `data/results/metrics.csv`, and `data/results/stats.json` (FR-006): (a) ERP waveforms for standard and deviant trials per condition with the 150–250 ms MMN window highlighted, (b) scalp topography maps of the MMN difference for the **150–250 ms** window for both conditions (not "–250ms" as plan Task 4.3 mistakenly says), (c) statistical significance plots (FDR-corrected p-values and effect sizes per electrode). Save PNG and SVG to `data/results/figures/`.
  - Check: all figure files exist and render without errors; waveforms reflect actual computed ERPs, not invented curves.

## Phase 3: Reproducible results, verification gates, and paper handoff

- [ ] T008 [US2] Write `code/main.py` orchestration and document the full runnable command in the feature's `quickstart.md`: `python code/main.py` (download → preprocess → analyze → visualize), with pinned dependencies in `code/requirements.txt` (mne>=1.7.0, numpy, pandas, scipy, statsmodels, matplotlib, jsonschema) and random seeds pinned for ICA. Re-run the documented workflow from its declared inputs and confirm all tests and artifact checks pass.
  - Check: fresh re-run reproduces `data/results/metrics_per_subject.csv`, `data/results/metrics.csv`, and `data/results/stats.json` consistently; `pytest code/tests/` passes.

- [ ] T009 [US2][US3] Write a concise methods/results account in `specs/001-neural-correlates-of-temporal-prediction/research.md` linked to the actual output rows in `data/results/metrics.csv`, entries in `data/results/stats.json`, and figure files in `data/results/figures/`. Report honestly: whether the SNR ≥ 3.0, FDR p < 0.05, d ≥ 0.5, and r ≥ 0.8 criteria were met per condition; subject exclusion counts; any negative findings (e.g., no significant complexity effect) and limitations (sample size, electrode coverage, single dataset). Document the paper-stage handoff: the paper pipeline receives `data/results/metrics.csv`, `data/results/stats.json`, and the figures, with the requirement to present MMN amplitude/latency/topography comparisons between simple and complex conditions with uncertainty.
  - Check: every numerical claim in `research.md` traces to a row in the result artifacts; no expected or invented values.

- [ ] T010 [US1][US2][US3] Implement the three FR-012 verification points as concrete, failing-loud code checks in `code/verify_references.py`, invoked from `code/main.py`: (1) before dataset download, verify the dataset ID and URL against the canonical OpenNeuro source (resolve `[UNRESOLVED-CLAIM: https://openneuro.org/crn/datasets/ds004510/` — HTTP 404] and confirm the dataset ID and BIDS structure; halt on mismatch); (2) before analysis, verify the presence of the required 'simple' and 'complex' conditions in the downloaded events metadata (halt with the FR-008 message if absent); (3) before reporting, verify every citation used in `research.md` and `data/benchmarks/mmn_effect_sizes.json` against its named primary source, recording verification status (verified/unreachable) in `data/results/citation_verification.json`. FR-013's artifact-hash recording is satisfied within project-owned paths via `data/raw/checksums.json` (T001); the `state/projects/…yaml` hash map is platform-owned and derived at verification time — the spec's FR-013 path is flagged for amendment to delegate that to the platform (see kickback list).
  - Check: `python code/verify_references.py --stage all` exits 0 on the real dataset; each of the three checks fails loudly (non-zero exit, clear message) when given a wrong dataset ID, a missing condition, or an unreachable citation.

## Dependencies and requirement coverage

| Requirement | Task(s) | Order |
|---|---|---|
| FR-001 (download + checksums) | T001 | first |
| FR-002/FR-003 (preprocessing, epochs) | T002 | after T001 |
| FR-004, FR-011 (MMN metrics, SD-based SNR) | T003, T004 | after T002 |
| FR-008 (complex-condition halt) | T001, T010 | at download / pre-analysis |
| FR-005, FR-010 (stats, FDR, Cohen's d, benchmark) | T005 | after T004 |
| FR-009 (canonical template, topographic r) | T004, T005 | T004 before T005 |
| FR-006 (visualizations) | T007 | after T005 |
| FR-012 (verification at three points) | T010 | gates at download, analysis, reporting |
| FR-013 (hashes; state/ path platform-owned) | T001 (data/raw/checksums.json) | at download |
| FR-014, FR-015 (contract tests) | T006 | after T005 (metrics/stats exist) |
| Edge cases (exclusions, interpolation) | T002 | with preprocessing |
| SC-001–SC-004 | T003, T004, T005, T009 | as above |

Execution order: T001 → T002 → T003 → T004 → T005 → (T006, T007) → T008 → T009, with T010's three checks gating T001 (dataset ID), T005 (condition presence), and T009 (citations). T001 is the only parallel-safe task (`[P]`); T002 consumes T001's `data/raw/` output and is strictly sequential after it, as are T006/T007's `[P]` tags (parallel with each other, after T005).

## Revision behavior

Preserve working artifacts and verified requirements. Repair specific failing commands from verifier feedback rather than regenerating the task list. A narrow failure in one script is not a reason to rebuild the project skeleton.