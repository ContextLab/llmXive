# Tasks: Investigating the Neural Response to Deviance in Auditory Perception

**Inputs**: Active `spec.md`, `plan.md`, `contracts/`, existing artifacts.
**Revision note**: Updated to resolve panel concerns (path consistency, schema selection, verification of statistical thresholds, variance reduction, per‑condition metrics, checksum recording, download method, ordering tags, and hard budget enforcement). Existing verified tasks retain IDs and status.

## Phase 0–5: Verified pipeline work (preserved, do not redo)

- [ ] T010 [P] [FR-001] Implement `code/download.py`: fetch OpenNeuro ds003645 via `wget` (or `curl`) with retry logic (3 attempts, 10 s backoff), writing raw files to `data/raw`. Verified: files present in `data/raw`.
- [ ] T011 [FR-001] Add checksum verification against the OpenNeuro manifest in `code/download.py`; raise on mismatch. **Note**: depends on T010 output. Verified.
- [ ] T016 [US1] [FR-001b] Channel subsampling to the standard montage (Fz, FCz, Cz, Pz, …) in `code/preprocess.py`. Verified.
- [ ] T017 [US1] [FR-002] Bandpass filter (1–30 Hz) and common‑average re‑reference in `code/preprocess.py`. Verified.
- [ ] T018 [US1] [FR-002] Epoching (−200 ms to 600 ms) into "standard"/"deviant" conditions → `data/processed/epo_raw.fif`. Verified.
- [x] T019/T020 [US1] [FR-003] ICA blink‑component detection (frontal correlation > 0.8) and removal, with removed‑component count logged → `data/processed/epo_clean.fif`. Verified.
- [ ] T021 [US1] [SC-001] Participant exclusion for >50 % rejected trials, IDs logged to `data/processed/rejected_participants.log`. Verified.
- [x] T022a/T022b [US2] [FR-004] Per‑participant standard/deviant ERPs and difference waves → `data/processed/diff_wave.fif`. Verified.
- [x] T023/T024/T025 [US2] [FR-004] [SC-005] Peak detection (primary 150–250 ms, fallback 100–300 ms, ≥2.0 µV threshold), `peak_detected` flagging, and SNR computation on difference waves at Fz/FCz. Verified.
- [ ] T026 [US2] [FR-004] `results/metrics.csv` generation with all schema fields (`amplitude`, `latency`, `peak_detected`, `snr`, nulls as JSON null). Verified.
- [x] T029–T035, T039, T039b [US3] [FR-005] [FR-006] Statistical analysis in `code/stats.py`: exclusion filtering, paired t‑tests (Wilcoxon fallback), FDR over 4 comparisons, mixed‑effects model, cluster‑based permutation test (1000 permutations), Cohen's d + 95 % CI, prevalence, latency‑window validation → `results/statistics.json`, `results/latency_validation.json`. Verified.
- [ ] T036–T038 [US3] [FR-007] Grand‑average ERP plots with CIs and topographic maps → `results/plots/erp_plot.png`, `results/plots/topomap.png`. Verified.
- [x] T050/T051/T052 Integration/unit tests for preprocessing, extraction, FDR, and visualization. Verified.

## Phase 6: Repairs for verifier‑rejected items (redo with real artifacts)

- [ ] T046 Create the concrete configuration artifacts previously missing as missing: (a) `.pre-commit-config.yaml` at repository root enabling `flake8` and `black` hooks for `code/` and `tests/`; (b) `tests/conftest.py` defining reusable pytest fixtures (paths to `data/raw`, `data/processed/epo_clean.fif`, `results/metrics.csv`, and a skip‑guard that skips integration tests when raw data is absent); (c) `code/env.example` documenting optional `OPENNEURO_API_KEY` and local data‑path environment variables, referenced from `code/download.py` via `os.environ.get` with no silent fallback to synthetic data. **Verify**: all three files exist and are non‑empty; `pytest tests/ -q --collect-only` collects fixtures without error.

- [ ] T047 Add edge‑case unit tests in `tests/unit/test_extract.py` and `tests/unit/test_stats.py`: (a) empty‑epochs input raises or returns an empty frame without fabricating rows; (b) a difference wave with no peak ≥ 2.0 µV in either window yields `peak_detected=false` with null amplitude/latency per the `mmn_metrics.schema.yaml` contract; (c) FDR correction on 4 p‑values reproduces expected corrected values. **Verify**: `pytest tests/unit -q` passes with ≥3 new tests, no synthetic input data written outside `tests/`.

## Phase 7: Full‑cohort run, validation, and reproducibility

- [ ] T048 [SC-004] Run the full pipeline over all downloaded participants (not just `sub-01`) on CPU (2 cores, ~7 GB RAM), recording per‑stage wall‑clock timings and peak memory (via `resource`/`time`) logged to `results/runtime_report.json`. **Assert** total runtime ≤ 6 h **and** peak RAM < 7 GB; the task fails if either bound is exceeded.

- [ ] T049 Re‑run the documented end‑to‑end workflow from `data/raw` using the command recorded in `specs/001-investigating-the-neural-correlates-of-p/quickstart.md` (download → preprocess → extract → stats → viz), and capture the execution log to `results/e2e_run.log`. Confirm `results/metrics.csv`, `results/statistics.json`, `results/latency_validation.json`, and `results/plots/*.png` are regenerated with consistent content (e.g., `analyzed_n` in `statistics.json` matches non‑excluded rows in `metrics.csv`). **Verify**: log exists, all artifacts exist and cross‑check pass; any failure is reported honestly, not masked.

- [ ] T050b Perform a focused cleanup of `code/` limited to the analysis drivers actually used by the verified pipeline: remove dead/unused modules, ensure `code/config.yaml` parameters match the executed run (filter 1–30 Hz, epoch −200–600 ms, ICA corr > 0.8), and record the change summary in `code/CHANGELOG.md`. **Verify**: `code/CHANGELOG.md` exists listing concrete changes; the end‑to‑end command from T049 still runs after cleanup. **Note**: must run after T049.

- [ ] T051b Write `README.md` at the project root documenting: dataset provenance (OpenNeuro ds003645, canonical programmatic fetch via wget), pipeline stages with the exact runnable command from `quickstart.md`, key parameters, output artifact inventory (`results/metrics.csv`, `results/statistics.json`, `results/plots/`), and the associational (non‑causal) framing of findings per the spec's assumptions. **Verify**: `README.md` exists, references only real artifact paths that exist on disk, and contains no expected/invented numerical results.

- [ ] T052b Methods/results handoff: write `specs/001-investigating-the-neural-correlates-of-p/research_summary.md` linking each reported statistic to its actual source cell in `results/statistics.json` and each figure to its PNG file, including: FDR‑corrected p‑values and Cohen's d for all 4 comparisons, cluster‑permutation and mixed‑effects results, prevalence of `peak_detected`, excluded‑participant count, and honest reporting of negative findings or participants without detectable peaks. **Verify**: every number in the summary appears verbatim in the JSON/CSV artifacts; no value is hand‑typed or projected.

## New verification and compliance tasks

- [ ] T053 Record dataset checksum: compute SHA‑256 checksums for all files downloaded into `data/raw` and write them to `data/checksums.txt`. **Verify**: file exists and contains a line for each raw file; checksum verification step (T011) reads this file.

- [ ] T054 Verify ICA variance reduction: after ICA cleaning, compute variance of frontal channels (Fz, FCz) in the pre‑ICA data and post‑ICA data; assert ≥ 10 % reduction. **Verify**: task fails if reduction < 10 %.

- [ ] T055 Verify latency prevalence: compute proportion of valid participants whose peak latency falls within the primary window (150–250 ms) or fallback (100–300 ms). Assert proportion ≥ 0.80. **Verify**: task fails if proportion < 0.80.

- [ ] T056 Per‑condition metric extraction: extend `code/extract.py` to also compute peak amplitude and latency for the **standard** and **deviant** conditions separately (in addition to the difference wave). Append these columns (`standard_amplitude`, `standard_latency`, `deviant_amplitude`, `deviant_latency`) to `results/metrics.csv` while retaining the existing difference‑wave fields. **Verify**: CSV contains all required columns and conforms to a new schema `mmn_metrics_per_condition.schema.yaml`.

- [ ] T057 Statistical significance gate: add a verification step after `code/stats.py` that checks the FDR‑corrected p‑value for the amplitude comparison at Fz (or the most significant comparison) is < 0.05. The pipeline fails if this condition is not met, satisfying SC‑002.

- [ ] T058 Schema selection clarification: add a comment in `code/stats.py` and update documentation to state that `results/statistics.json` must conform to `contracts/results.schema.yaml`; the alternative `stats_report.schema.yaml` is deprecated. **Verify**: test validates JSON against the chosen schema.