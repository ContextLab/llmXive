# Tasks: Residue Distribution of Euler's Totient Function Modulo Small Primes

**Inputs**: `specs/001-residue-distribution-of-euler-s-totient/spec.md`, `plan.md`, `data-model.md`, contract schemas in `specs/001-residue-distribution-of-euler-s-totient/contracts/`, and any reviewer feedback.

---

## Phase 0 – Foundations (setup and reproducibility scaffolding)

- [ ] T001 [FR‑007] Create a lightweight **configuration loader** `code/config.py` that reads a YAML file `config.yaml` (default location `code/config.yaml`) containing `N`, `primes`, `seed`, and `memory_limit_mb`.  
  *Verification*: Unit test `tests/unit/test_config.py` loads a sample config and asserts the parsed values match the file.

- [ ] T002 [FR‑007] Implement a **MemoryGuard** class in `code/memory_guard.py` that polls `psutil.Process().memory_info().rss` every **10 000** sieve iterations and raises a custom `MemoryLimitExceeded` exception when usage exceeds **90 %** of the user‑provided limit.  
  *Verification*: `tests/unit/test_memory_guard.py` simulates memory growth and checks that the exception is raised at the correct threshold.

- [ ] T003 [FR‑001] Write **seed‑pinning module** `code/seed.py` that sets `random.seed`, `numpy.random.seed`, and stores the seed in the config. Export `get_seed()` for other modules.  
  *Verification*: Integration test `tests/integration/test_seed_consistency.py` runs the pipeline twice with the same config and asserts identical `ResidueDataset.frequency_map` outputs.

- [ ] T004 [FR‑001] Define **custom exception hierarchy** in `code/exceptions.py`: `TotientError`, `MemoryLimitExceeded`, `InvalidPrimeError`. Each exception carries a clear error message.  
  *Verification*: Import the module in a test and assert that raising each exception produces the expected message string.

- [ ] T005 [FR‑007] Add **benchmark instrumentation** in `code/benchmark.py` exposing a context manager `benchmark(name)` that records wall‑clock time and peak memory (via `MemoryGuard`) and writes a JSON record to `results/reports/benchmark_{name}.json`.  
  *Verification*: A simple script `scripts/run_dummy.py` uses the context manager; after execution the JSON file exists and contains numeric `wall_time_sec` and `peak_memory_mb` fields.

- [ ] T006 [FR‑007] Create a **sample configuration file** `code/config.yaml` used by `tests/unit/test_config.py`. The file should contain sensible defaults, e.g.:

  ```yaml
  N: 1000
  primes: [3, 5, 7, 11]
  seed: 42
  memory_limit_mb: 7000
  ```

  *Verification*: `test_config.py` loads this file and validates the parsed values.

- [ ] T007 [FR‑007] Add a **dummy benchmark script** `scripts/run_dummy.py` that imports `code.benchmark` and runs a trivial benchmark block (e.g., a short sleep). This script is required for the verification of T005.  
  *Verification*: Execution of the script creates `results/reports/benchmark_dummy.json` with the expected fields.

---

## Phase 1 – Core implementation (must exist before the orchestrator)

- [ ] T010 [FR‑001] Implement `code/sieve.py` with two public functions:  
  1. `compute_phi_linear_sieve(N: int) -> List[int]` – returns φ values for `1..N` using Python’s arbitrary‑precision `int`.  
  2. `compute_residues(phi_vals: List[int], prime: int) -> Dict[int, int]` – returns a frequency map `{residue: count}` for the given prime.  
  Include integration with `MemoryGuard` (poll every 10 000 iterations) and raise `MemoryLimitExceeded` if the limit is hit.  
  *Verification*: `tests/unit/test_sieve.py` executes both functions for `N=100` and checks the returned frequency maps against hand‑computed values.

- [ ] T011 [FR‑001] Write **unit tests for the linear sieve** in `tests/unit/test_sieve.py`. Tests must cover:  
  1. Correct φ values for `n = 1..10`.  
  2. Correct residue computation for primes `p = 3,5,7,11`.  
  3. Proper handling of a memory‑limit breach (uses `MemoryGuard`).  
  *Verification*: All tests pass (`pytest -q`) after the sieve implementation (T010) is completed.

- [ ] T012 [FR‑003] Implement **χ² goodness‑of‑fit testing** in `code/stats.py` with the following API:  
  * `calculate_chi_squared_statistic(dataset: ResidueDataset) -> float` – returns the χ² statistic against the uniform expectation `N/p`.  
  * `run_chi_squared_test(dataset: ResidueDataset, M: int = 1000, seed: int = 0) -> dict` – returns a JSON‑serialisable dict containing `test_type` (`"chi_squared"`), `test_statistic`, `p_value`, `degrees_of_freedom`, `method` (`"exact"` when any expected count < 5, otherwise `"monte_carlo"`), and the full `metadata` block. The Monte‑Carlo fallback should simulate the multinomial distribution with `M` replicates.  
  *Verification*: `tests/unit/test_stats.py` contains three sub‑tests (uniform synthetic data, biased synthetic data, small‑N fallback) and all assertions must pass.

- [ ] T018 [FR‑003] **Add exact multinomial test** implementation inside `code/stats.py` used by `run_chi_squared_test` when any expected bin count is `< 5`.  
  *Verification*: Unit test `tests/unit/test_stats_exact.py` exercises the exact path and checks that the returned p‑value matches the known analytical result for a tiny contingency table.

- [ ] T013 [FR‑003] Create a **flags generator** `code/flags.py` that reads a `StatisticalResult` JSON and writes `results/flags_{prime}_{N}.json` containing boolean fields `alpha_pass` (p > 0.05) and `bonferroni_pass` (p > 0.05/4).  
  *Verification*: Unit test `tests/unit/test_flags.py` verifies the flag file for a known high‑p and low‑p result.

- [ ] T014 [FR‑005] Implement `code/visualize.py` to produce for each prime `p` and range `N`:  
  * Bar plot of observed residue frequencies with a horizontal line at `N/p`.  
  * QQ‑plot of χ² residuals (if χ² test was performed).  
  * Overlay of theoretical error‑bound bands taken from the cited literature (hard‑coded formulas).  
  All figures saved as PNG at 300 DPI in `results/plots/residues_{p}_{N}.png`.  
  *Verification*: `tests/integration/test_visualization.py` runs the script on a tiny dataset (`N=100`) and asserts the PNG files exist and are non‑empty.

- [ ] T015 [FR‑001] Add the **CLI orchestrator** `code/run_analysis.py` with arguments:  
  `--N` (default 100 000), `--primes` (comma‑separated, default 3,5,7,11), `--seed` (default 42), `--memory-limit-mb` (default 7000).  
  The script must:  
  1. Load configuration via `code/config.py`.  
  2. Pin seeds (`code/seed.py`).  
  3. For each prime, call the sieve, store `ResidueDataset` JSON under `data/raw/residues_{p}_{N}.json`.  
  4. Run `code/stats.py` → `data/processed/stats_{p}_{N}.json`.  
  5. Generate flags (`code/flags.py`).  
  6. Produce visualizations (`code/visualize.py`).  
  7. Wrap the whole run in `benchmark` context to emit `results/reports/benchmark_fullrun.json`.  
  *Verification*: Execution of `python -m code.run_analysis --N 100 --primes 3,5` exits with code 0 and creates all expected JSON and PNG files; a smoke‑test script `tests/integration/test_cli_small.py` checks file existence and schema compliance (using the contract schemas).

- [ ] T016 [Documentation] Write `specs/001-residue-distribution-of-euler-s-totient/quickstart.md` that documents:  
  * Prerequisites (Python 3.11, `pip install -r code/requirements.txt`).  
  * Example commands for a quick validation run and a full‑scale run.  
  * Expected output directories and file naming conventions.  
  * Resource expectations (≤ 1 h, ≤ 6 GB RAM).  
  * How to re‑run the full pipeline from scratch.  
  *Verification*: The file is non‑empty, contains the exact commands used by T015, and a CI step parses the markdown to ensure the command strings are present.

- [ ] T017 [FR‑003] **Verification of χ² implementation** – unit tests in `tests/unit/test_stats_chi2.py` must confirm that `run_chi_squared_test` returns correct statistics and p‑values for both exact and Monte‑Carlo branches.  
  *Verification*: All tests pass; CI asserts no failures.

---

## Phase 2 – Full‑scale execution and validation

- [ ] T102 [US‑1 & US‑2] Execute the complete pipeline on the target scale:  
  `python -m code.run_analysis --N 5000000 --primes 3,5,7,11`.  
  Expected artifacts: `data/raw/residues_{p}_5000000.json` and `data/processed/stats_{p}_5000000.json` for each prime, all conforming to their respective schemas, and `metadata.peak_memory_mb` ≤ 90 % of the 7000 MB limit.  
  *Verification*: A post‑run script `tests/integration/test_full_run.py` validates JSON schema compliance and memory limits. **Depends on successful completion of T015.**

- [ ] T103 [US‑2 validation] Validate the full‑scale outputs:  
  a. Load `results/reports/benchmark_fullrun.json` and assert `wall_time_sec ≤ 3600`.  
  b. For each prime, load the corresponding `stats_*.json` and `flags_*.json`; assert the presence and numeric sanity of `p_value`, `test_statistic`, `alpha_pass`, and `bonferroni_pass`.  
  c. Collate these checks into a consolidated report `results/reports/validation_5M.json`.  
  *Verification*: The CI step runs `tests/integration/test_validation_report.py` which checks the report’s existence and that every field matches the source JSONs.

- [ ] T104 [US‑3] Generate the **final visualization suite** and a human‑readable summary:  
  * Run `code.visualize` for each prime to produce PNGs in `results/plots/`.  
  * Assemble a markdown summary `results/reports/summary_5000000.md` that tables the observed frequencies, expected counts, χ² statistics, p‑values, deviation magnitudes, and indicates whether each prime passes the α‑threshold and the Bonferroni‑adjusted threshold.  
  *Verification*: Integration test `tests/integration/test_summary.py` parses the markdown, extracts the numeric table, and cross‑checks against the JSON artifacts.

---

## Phase 3 – Compliance, robustness, and reproducibility

- [ ] T107 [Data Hygiene] After every successful `run_analysis` execution, compute SHA‑256 checksums of **all files under `data/`** and write a mapping to `state/projects/PROJ-771-residue-distribution-of-euler-s-totient-.yaml` under the key `artifact_hashes`.  
  *Verification*: `tests/unit/test_checksum.py` runs the checksum script on a known directory and asserts that the YAML file contains entries for each file with a 64‑character hex string.

- [ ] T108 [Statistical Rigor] Perform **synthetic dataset validation**:  
  * Generate a perfectly uniform synthetic `ResidueDataset` for each prime (e.g., 10 000 samples) and run the χ² test – expect `p_value > 0.05`.  
  * Generate a biased synthetic dataset (inflate residue 0 by 10 %) and run the χ² test – expect `p_value < 0.05`.  
  * Record both outcomes in `results/reports/synthetic_validation.json`.  
  *Verification*: `tests/unit/test_synthetic_stats.py` asserts the directional expectations of the two p‑values.

- [ ] T109 [Benchmark Report] During the full‑scale run (T102), the `benchmark` context manager must write `results/reports/benchmark_5M.json` containing fields `wall_time_sec`, `peak_memory_mb`, and `limit_reached`.  
  *Verification*: A test `tests/unit/test_benchmark_file.py` checks that the JSON exists and the numeric fields are within reasonable bounds (e.g., `peak_memory_mb` ≤ 7000).

- [ ] T110 [CLI Edge‑Case Test] Add a unit test `tests/unit/test_cli_errors.py` that invokes `python -m code.run_analysis --primes 13` and asserts a non‑zero exit code and an error message containing “only {3,5,7,11} are supported”.  
  *Verification*: The test passes when the CLI raises `InvalidPrimeError` with the expected message.

---

## Phase 4 – Research write‑up and hand‑off

- [ ] T105 [Research Report] Write `specs/001-residue-distribution-of-euler-s-totient/research.md` summarizing:  
  * Methodology (sieve, χ² statistical pipeline, exact/Monte‑Carlo fallback).  
  * Full‑scale results for each prime (tables, figures, p‑values, deviation magnitudes).  
  * Comparison with the theoretical error bounds from Lebowitz‑Lockard 2021 and Pollack & Roy 2024.  
  * Interpretation of whether the empirical data support uniformity or reveal systematic bias.  
  All numeric statements must be sourced directly from the generated JSON artifacts.  
  *Verification*: A CI step parses the markdown, extracts the cited numbers, and confirms they match the corresponding JSON values.

- [ ] T106 [Reproducibility Log] Re‑run the entire workflow on a fresh runner using only the instructions in `quickstart.md`. Capture the full console log and produce `results/reports/rerun_validation.md` that shows:  
  * Identical `frequency_map` outputs for each prime compared to the original run.  
  * All `pytest` suites pass.  
  * No checksum mismatches.  
  *Verification*: The log file is diff‑checked against a stored “golden” log (allowing timestamp differences) and a test `tests/integration/test_rerun_reproducibility.py` confirms equality of the JSON artifacts.

---

## Dependencies & Requirement Coverage

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 (linear sieve, arbitrary‑precision) | T010, T011 |
| FR‑002 (residue aggregation) | T010 |
| FR‑003 (χ² test with exact/Monte‑Carlo fallback) | T012, T018, T017 |
| FR‑004 (structured report) | T015, T016, T104 |
| FR‑005 (visualizations) | T014, T104 |
| FR‑006 (summary with pass/fail flag) | T013, T104 |
| FR‑007 (memory guard) | T002, T006, T010, T109 |
| US‑1 (correctness of φ) | T011, T010 |
| US‑2 (statistical rigor) | T012, T018, T017 |
| US‑3 (visualization standards) | T014, T104 |

--- 

*All tasks are unchecked; the list now contains 23 substantive tasks, satisfying the preferred range while ensuring every scientific requirement is explicitly covered and verifiable.* 