# Tasks: Residue Distribution of Euler's Totient Function Modulo Small Primes

**Input**: Design documents from `/specs/001-residue-distribution-of-euler-s-totient/`  
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/

## Phase 0: Foundations (already verified)

- [ ] T005/T004/T007/T008/T009 – config loader, `MemoryGuard`, seed pinning, sieve unit tests, custom exceptions, benchmark instrumentation (preserved as verified).

## Phase 1: Implementation of core modules (must exist before orchestrator)

- [ ] T010 [FR‑001] Implement `code/sieve.py` with `compute_phi_linear_sieve(N)` using Python `int` (arbitrary‑precision) and `compute_residues(phi_vals, prime)`. Includes `MemoryGuard` polling every 10 000 iterations and raises `MemoryLimitExceeded` at **≥ 90 %** of the user‑provided memory limit. Unit tests in `tests/unit/test_sieve.py` assert correct residues for `n=1..5` (p=5) and verify memory‑limit behavior.

- [ ] T011 [FR‑001] Add comprehensive docstrings and type hints to `code/sieve.py`. Verification via static analysis (mypy) passes.

- [ ] T012 [FR‑003] Implement `code/stats.py`:
  * `calculate_chi_squared_statistic(dataset)` – χ² statistic for uniformity.
  * `run_chi_squared_test(dataset, M=1000, seed=…)` – Monte‑Carlo p‑value estimation with exact fallback when any expected count < 5.
  * `block_bootstrap_residues(dataset, block_size, M, seed)` – contiguous‑block resampling for deviation‑magnitude test.
  * `run_deviation_test(dataset, ...)` – block‑bootstrap deviation metric with small‑N fallback (if `N < 100` report raw `D` and set `p_value = null`).
  Verification via `tests/unit/test_stats.py` covering uniform synthetic data, biased synthetic data, and small‑N path.

- [X] T017 [FR‑003] Extend `code/stats.py` to provide an **exact multinomial test** used when any expected bin count < 5, invoked automatically by `run_chi_squared_test`.

- [ ] T018 [FR‑004] Ensure `run_chi_squared_test` records the method used (`"chi_squared_monte_carlo"` or `"chi_squared_exact"`) in the output JSON for traceability.

- [ ] T013 [FR‑003] Extend `code/stats.py` to expose **α‑pass** and **Bonferroni‑pass** boolean flags in a separate JSON file `results/flags_{prime}_{N}.json`.

- [ ] T014 [FR‑005] Implement `code/visualize.py` to generate:
  * Bar plot of observed residues with horizontal line at `N/p`.
  * QQ‑plot of χ² residuals.
  * Annotated error‑bound bands from Lebowitz‑Lockard & Pollack‑Roy.
  All figures saved as PNG ≥ 300 DPI in `results/plots/`.

- [ ] T015 [FR‑006] Add `code/run_analysis.py` (the CLI orchestrator):
  * Argparse: `--N` (default 100 000), `--primes` (default 3,5,7,11), `--seed` (default 42), `--memory-limit-mb` (default 7000).
  * Pins `random.seed` and `numpy.random.seed`.
  * Calls `code.sieve`, `code.stats`, `code.visualize`.
  * Writes outputs via `llmxive_toolkit.paths`.
  * Verification: `python -m code.run_analysis --N 100 --primes 3,5` exits 0 and produces `data/raw/residues_3_100.json` and `data/raw/residues_5_100.json` conforming to `contracts/dataset.schema.yaml`.

- [ ] T016 [Documentation] Write `quickstart.md` at repository root (`specs/001-residue-distribution-of-euler-s-totient/quickstart.md`) containing:
  * Prerequisites (Python 3.11, `code/requirements.txt`).
  * Commands:
    - Small validation run: `python -m code.run_analysis --N 100 --primes 3,5`.
    - Full run: `python -m code.run_analysis --N 5000000 --primes 3,5,7,11`.
  * Expected output paths.
  * Expected wall‑clock (< 1 h) and memory (< 6 GB) envelopes.
  Verification: file exists, non‑empty, and listed commands match those executed by T015 and T104.

## Phase 2: Full‑scale execution and validation

- [ ] T102 [US‑1 & US‑2] Execute full pipeline:
  `python -m code.run_analysis --N 5000000 --primes 3,5,7,11`.
  Produces `data/raw/residues_{p}_5000000.json` and `data/processed/stats_{p}_5000000.json` (χ² results) for each prime, all conforming to their contracts and with `metadata.peak_memory_mb` ≤ 90 % of limit. Edge‑case check: running with `--primes 13` exits non‑zero with clear error (verified by unit test T110).

- [ ] T103 [US‑2 validation] Validate outputs:
  * (a) Read `results/reports/benchmark_5M.json` (produced by T109) and assert `wall_time_sec ≤ 3600`.
  * (b) For each prime, load `data/processed/stats_{p}_5000000.json` and the corresponding `results/flags_{p}_5000000.json`; assert that `p_value`, `test_statistic`, `α‑pass`, and `Bonferroni‑pass` are present, finite, and correctly derived.
  * (c) Write a consolidated validation report `results/reports/validation_5M.json`.
  Verification: report exists, non‑empty, and references real artifact filenames.

- [ ] T104 [US‑3] Generate final figures and summary:
  * Bar plots, QQ‑plots, and error‑bound annotations for each prime (via `code.visualize.py`).
  * Consolidated markdown report `results/reports/summary_5000000.md` quoting numbers directly from the JSON stats and flag files.
  Verification: report numbers match the source JSONs (checked in `tests/integration/test_pipeline.py`).

## Phase 3: Additional compliance tasks

- [ ] T107 [Data Hygiene] After each `run_analysis` execution, compute SHA‑256 checksums of every file under `data/` and update `state/projects/PROJ-771-residue-distribution-of-euler-s-totient-.yaml` `artifact_hashes` map. Verification: checksum script runs without error and state file contains entries for all generated data files.

- [ ] T108 [Statistical Rigor] Synthetic dataset validation:
  * Create a perfectly uniform synthetic residue dataset for each prime and run the χ² test – expect `p_value > 0.05`.
  * Create a biased synthetic dataset (e.g., inflate residue class 0 by 10 %) and run the χ² test – expect `p_value < 0.05`.
  * Record outcomes in `results/reports/synthetic_validation.json`.
  Verification: test script `tests/unit/test_synthetic_stats.py` asserts the expected inequality directions.

- [ ] T109 [Benchmark Report] During T102, capture wall‑clock time, peak RAM, and write `results/reports/benchmark_5M.json` containing:
  ```json
  {"wall_time_sec": <float>, "peak_memory_mb": <float>, "limit_reached": false}
  ```
  Verification: file exists and fields are numeric.

- [ ] T110 [CLI Edge‑Case Test] Add unit test `tests/unit/test_cli_errors.py` that runs `python -m code.run_analysis --primes 13` and asserts a non‑zero exit code and error message containing “only {3,5,7,11} are supported”.

## Phase 4: Research write‑up and reproducibility handoff

- [ ] T105 [Research Report] Write `specs/001-residue-distribution-totient/research.md` summarizing methods, χ² and block‑bootstrap results, synthetic validation, and interpretation against theoretical error bounds. All numeric claims cite values from the generated JSON artifacts.

- [ ] T106 [Reproducibility Log] Re‑run the workflow from `quickstart.md` on a fresh runner, capture logs, and produce `results/reports/rerun_validation.md` showing identical `frequency_map` outputs and passing all `pytest` suites.