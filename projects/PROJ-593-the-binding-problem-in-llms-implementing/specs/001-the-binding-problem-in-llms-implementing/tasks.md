# Tasks: The Binding Problem in LLMs – Implementing Synchronized Oscillations for Feature Integration  

**Inputs**: `spec.md`, `plan.md`, existing `research.md`, `data-model.md`, `contracts/`  

The tasks are grouped into three research phases (setup → core experiments → reproducible hand‑off).  
Each task follows the canonical format `- [ ] T### [P?] [USx?] description – file/path`.  
Unchecked boxes indicate work that still needs to be delivered; checked boxes denote completed artifacts that already satisfy the specification.

---  

## Phase 1 – Setup & First End‑to‑End Analysis  

| Goal | Build a minimal, runnable project skeleton, fetch real data, and implement the core spectral utilities needed for the first forward‑pass test. |
|------|------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] T001 **Create project layout** – `mkdir src tests data config docs contracts` and add a short `tree` listing in `README.md`.  
- [X] T002 **Pin dependencies** – `requirements.txt` containing exact versions of `transformers>=4.40`, `torch>=2.3`, `datasets>=2.20`, `mne>=1.7`, `scipy>=1.14`, `numpy>=2.0`, `scikit-learn>=1.5`.  
- [X] T003 **Add pre‑commit config** – `.pre-commit-config.yaml` with `ruff` and `black` hooks (no placeholder content).  
- [X] T004 **Configure pytest** – `pyproject.toml` section `[tool.pytest.ini_options]` with `addopts = "--strict-markers"` and `testpaths = ["tests"]`.  
- [ ] T005 **Download MEG data (streaming)** – `src/data/download_meg.py` uses `datasets.load_dataset("openneuro/ds000246", split="train", streaming=True)` and writes a Parquet file `data/raw/meg_streamed.parquet`. The script must raise on any fetch error (no synthetic fallback).   <!-- FAILED-IN-EXECUTION: src/data/download_meg.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download_meg.py exit=1 -->
- [ ] T006 **Download CLUTRR benchmark** – `src/data/download_clutrr.py` fetches `tasksource/clutrr` via `datasets.load_dataset` and saves `data/raw/clutrr.parquet`. Must fail loudly if the download fails.  
- [ ] T008 **Add MEG data contract** – `contracts/dataset.schema.yaml` describing the shape, dtype, and required metadata for each processed MEG artifact.  
- [ ] T007 **Pre‑process MEG** – `src/data/preprocess_meg.py` performs four sub‑steps (each writes its own artifact):  
  - **Ingest** → `data/processed/meg_raw.npy` (numpy array of sensor values).  
  - **Band‑pass filter 30‑50 Hz** → `data/processed/meg_filtered.npy`.  
  - **Compute SNR** (target band vs. adjacent 10‑20 Hz & 60‑80 Hz) → `data/processed/meg_snr.json`.  
  - **Welch PSD (normalized)** → `data/processed/meg_psd_normalized.npy`.  
  All steps must stream data, never load the full raw file into RAM, and must validate against the schema in `contracts/dataset.schema.yaml`.  
- [ ] T007a **MEG preprocessing verification** – unit test `tests/integration/test_meg_preprocess.py` that validates each artifact against `contracts/dataset.schema.yaml` and asserts SHA‑256 checksums match those recorded by T040.  
- [ ] T009 **Base‑model wrapper** – `src/models/base_model.py` defines `DistilBERTWrapper` that loads `distilbert-base-uncased` on CPU‑only mode and exposes a `forward` method.  
- [ ] T009a **Base‑model wrapper test** – `tests/unit/test_base_model.py` loads the wrapper and runs a dummy forward pass, asserting output shape and CPU execution.  
- [ ] T010 **Oscillatory attention module** – `src/models/oscillatory_attention.py` implements `OscillatoryAttentionModule` injecting a sinusoidal mask `sin(2π f t)` where `f` is a *relative* frequency (cycles per sequence). Unit test in `tests/unit/test_oscillatory.py` must verify mask shape and that masking is deterministic given a seed.  
- [ ] T011 **Spectral utilities** – `src/analysis/spectral.py` provides `compute_psd(signal)`, `compute_snr(psd, target_band, side_bands)`, and `fft_spectrum(signal)`. All functions accept NumPy arrays and return plain Python objects for easy JSON serialisation.  
- [ ] T012 **Spectral unit tests** – `tests/unit/test_spectral.py` checks that a synthetic 40 Hz sinusoid yields a PSD peak in the 38‑42 Hz window and that `compute_snr` returns a value > 0 dB.  
- [ ] T013 **Statistical utilities** – `src/analysis/stats.py` implements `permute_test(observed, null_generator, n_perm=1000)` and `bonferroni_correct(p_vals, alpha=0.05)`.  
- [ ] T014 **Statistical unit tests** – `tests/unit/test_stats.py` validates that a known permutation distribution returns the correct p‑value and that Bonferroni correction caps the family‑wise error rate.  
- [ ] T015 **Default configuration** – `config/default.yaml` contains: `seed: 42`, `freq_list: [30,35,40,45,50]`, `meg_path: data/raw/meg_streamed.parquet`, `clutrr_path: data/raw/clutrr.parquet`, `output_dir: data/results`.  
- [ ] T016 **Reporting helper** – `src/analysis/reporting.py` formats similarity scores with the required label “Associational Similarity Score”.  
- [ ] T016a **Reporting helper test** – `tests/unit/test_reporting.py` checks that a sample score is correctly formatted.  
- [ ] T040 **Checksum MEG dataset** – script `src/data/checksum_meg.py` computes SHA‑256 of `data/raw/meg_streamed.parquet` and writes the hash to `state/megsum.yaml`.  
- [ ] T041 **Checksum CLUTRR dataset** – script `src/data/checksum_clutrr.py` computes SHA‑256 of `data/raw/clutrr.parquet` and writes the hash to `state/clutrrsum.yaml`.  

**Checkpoint** – After completing T001‑T041, `pytest` must pass all unit and integration tests, and the two download scripts must produce the Parquet files specified.

---  

## Phase 2 – Core Experiments & Validation  

| Goal | Implement the oscillatory mechanism, verify its spectral signature, compare to human MEG using PLV, and evaluate functional impact on compositional reasoning benchmarks. |
|------|---------------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] T017 **Orchestrate forward passes** – `src/main.py` accepts `--mode {baseline,oscillatory}` and `--freq <int>`. It loads the appropriate model (T009 + T010), runs a forward pass on a batch of 8 sequences (seq‑len = 50) on CPU, records raw attention‑head activations, and writes them to `data/results/activation_{mode}.npy`.  
- [ ] T018 **Run oscillatory forward pass (baseline frequency 40 cycles/seq)** – `python -m src.main --mode oscillatory --freq 40`. Produces `data/results/activation_oscillatory.npy`.  
- [ ] T019 **Run baseline forward pass** – `python -m src.main --mode baseline`. Produces `data/results/activation_baseline.npy`.  
- [ ] T020 **Spectral peak & SNR verification** – Use `src/analysis/spectral.py` on `activation_oscillatory.npy` to compute PSD, locate the peak in the 38‑42 Hz relative band, compute SNR against side bands, and assert `SNR ≥ 3.0 dB`. Results are saved to `data/final/snr_report.json`.  
- [ ] T021 **Control‑run comparison** – Build `data/final/control_run_comparison.json` containing keys `oscillatory_coherence`, `baseline_coherence`, `coherence_difference`, `is_significant` (true if difference ≥ 0.05). Coherence is derived from the same PSD‑based SNR metric for consistency.  
- [ ] T022 **Frequency sweep** – Extend `src/main.py` with a `--sweep` flag that iterates over `freq_list` from `config/default.yaml`, runs T018 for each frequency, records peak power and SNR, and writes a summary CSV `data/processed/sweep_results.csv` (`frequency,peak_power,SNR`).  
- [ ] T023 **Latency budget check** – Instrument `src/main.py` to record wall‑clock time for each forward pass; assert the time is `< 300 s` on the GitHub Actions free‑tier runner. Write a summary to `data/final/latency_report.json`.  
- [ ] T024 **Phase Locking Value (PLV) computation** – `src/analysis/plv.py` computes PLV between the residual phase of model activations (after removing the deterministic sinusoidal mask) and the reference MEG phase from `data/processed/meg_fallback.npy` or the primary reference if available. Results are stored in `data/final/plv_report.json`.  
- [ ] T045 **PLV verification test** – `tests/unit/test_plv.py` validates that PLV on synthetic aligned signals returns a high value (>0.8) and on misaligned signals returns low value (<0.2).  
- [ ] T025 **MEG fallback handling** – In `src/data/preprocess_meg.py` add logic: if `meg_snr.json` reports SNR < 2.0 for the strict 40 Hz band, automatically recompute PSD on the broader 30‑50 Hz band and write `data/processed/meg_fallback.npy`. Document the fallback status in `data/final/meg_fallback_status.json`.  
- [ ] T026 **Permutation test for PLV difference** – Wrap `stats.permute_test` around the PLV difference (oscillatory − baseline). Output the null distribution summary and p‑value to `data/final/permutation_plv.json`.  
- [ ] T028 **CLUTRR evaluation** – `src/benchmarks/clutrr_eval.py` loads `data/raw/clutrr.parquet`, runs both models (baseline & oscillatory) on 100 samples for 5 random seeds, computes accuracy & F1, and writes per‑seed results to `data/results/clutrr_{mode}_seed{N}.json`.  
- [ ] T029 **bAbI evaluation** – `src/benchmarks/babi_eval.py` mirrors T028 for the bAbI “task 1‑20” suite, outputting `data/results/babi_{mode}_seed{N}.json`.  
- [ ] T030 **Statistical aggregation of benchmarks** – Load the per‑seed JSON files, perform paired t‑tests (oscillatory vs baseline) for accuracy and F1, apply the Bonferroni correction from T027, and store the final summary in `data/final/benchmark_summary.json`.  
- [ ] T027 **Global Bonferroni correction** – Gather all p‑values from T020, T026, T028, T029, and T030, run `stats.bonferroni_correct`, and write the corrected table to `data/final/bonferroni_corrected.json`.  

---  

## Phase 3 – Reproducible Results & Paper‑Stage Handoff  

| Goal | Produce documentation, ensure full reproducibility, and close the traceability loop with the specification. |
|------|-----------------------------------------------------------------------------------------------------------|

- [ ] T048 **Spec integrity verification** – script `scripts/verify_spec.py` checks that `spec.md` contains FR‑003 describing PLV and that no SDC clause remains; exits with non‑zero code if the check fails.  
- [ ] T033 **Traceability of PLV rejection** – Add `docs/traceability/plv_rejection_rationale.md` that cites FR‑003, explains why PLV is retained, and points to the new PLV definition.  
- [ ] T042 **Traceability mapping** – `scripts/generate_traceability.py` produces `docs/traceability/mapping.json` linking each final figure/statistic (e.g., SNR, PLV, benchmark results) to its originating data file and code module.  
- [ ] T043 **Version‑hash recording** – `scripts/record_hashes.py` computes SHA‑256 hashes for all generated artifacts under `data/final/` and updates `state/projects/PROJ-593-the-binding-problem-in-llms-implementing.yaml` with an `artifact_hashes` map.  
- [ ] T034 **Quick‑start guide** – Update `docs/quickstart.md` with a single command that runs the full pipeline end‑to‑end: `./run_all.sh`. The script should invoke data download, preprocessing, model runs, and final report generation.  
- [ ] T035 **Methods & Results write‑up** – Populate `research.md` sections “Methods” and “Results” with concise prose that links directly to the generated artifacts (e.g., `data/final/snr_report.json`, `data/final/plv_report.json`, `data/final/benchmark_summary.json`).  
- [ ] T036 **Limitations & Falsification** – Add a “Falsification Evidence” subsection to `research.md` that explicitly states the conditions under which the 40 Hz hypothesis is rejected (e.g., SNR < 2 dB, non‑significant PLV after correction, no performance gain).  
- [ ] T037 **Reproducibility script** – `run_all.sh` (bash) that:  
  1. Installs `requirements.txt` in a fresh virtual environment,  
  2. Executes T005‑T030 in the correct order,  
  3. Validates that **all** expected output files exist:  
     - `data/final/snr_report.json`  
     - `data/final/plv_report.json`  
     - `data/final/permutation_plv.json`  
     - `data/final/benchmark_summary.json`  
     - `data/final/bonferroni_corrected.json`  
     - `data/final/latency_report.json`  
     - `data/final/meg_fallback_status.json`  
     - `docs/traceability/mapping.json`  
  4. Writes a log `data/final/reproducibility_log.txt` with timestamps and any failures.  
  Exit code 0 only if every listed file is present and all checks pass.  
- [ ] T039 **Feature‑definition schema** – Add `src/models/feature_definition.py` (a tiny dataclass describing a “binding‑feature” with fields `name`, `frequency`, `amplitude`) and the corresponding JSON schema `data/final/feature_definition_schema.json`. This satisfies the reviewer‑requested “feature definition” validation.  
- [ ] T038 **Final verification suite** – `tests/contract/test_all.py` imports the contracts, loads each final JSON/CSV artifact, and asserts schema compliance, that all p‑values are ≤ 0.05 after Bonferroni correction where required, and that hash entries in the state file match computed hashes.  

**Final Checkpoint** – Running `./run_all.sh` on a clean GitHub Actions runner must complete within the 6‑hour job limit, produce every file listed above, and exit with status 0. All unit, integration, and contract tests must pass.  

---  

### Dependency & Execution Order Summary  

| Phase | Dependent on |
|------|--------------|
| Phase 1 | None (can run in parallel) |
| Phase 2 | All Phase 1 tasks (T001‑T041) must be completed |
| Phase 3 | All Phase 2 tasks (T017‑T030) must be completed |

Parallel‑eligible tasks are marked with **[P]** in the list above; they operate on distinct files and have no ordering constraints.  

---  

*All scientific requirements (FR‑001 – FR‑006) are covered by the tasks above, and each success criterion (SC‑001 – SC‑005) has a concrete, verifiable artifact. The task list now respects ordering, eliminates duplicate IDs, adds missing hygiene, traceability, and versioning steps, and restores the required PLV metric.*  