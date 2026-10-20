# Tasks: Residue Distribution of Euler's Totient Function Modulo Small Primes

**Inputs**: `specs/001-residue-distribution-of-euler-s-totient/spec.md`, `plan.md`, `data-model.md`, contract schemas in `specs/001-residue-distribution-of-euler-s-totient/contracts/`, and any reviewer feedback.

---

## Phase 0 – Foundations (setup, reproducibility, and resource guards)

- [ ] T001  **Create configuration loader** – implement `code/config.py` that reads a YAML file `code/config.yaml` (default location) exposing `N`, `primes`, `seed`, and `memory_limit_mb`.  
  *Verification*: `tests/unit/test_config.py` loads the sample config and asserts the parsed values match the file.

- [ ] T002 [FR‑007] **Define custom exception hierarchy** – add `code/exceptions.py` containing `TotientError`, `MemoryLimitExceeded`, and `InvalidPrimeError`, each with a clear error message.  
  *Verification*: `tests/unit/test_exceptions.py` imports the module, raises each exception, and checks that the message string matches the specification.

- [ ] T003 [FR‑007] **Implement MemoryGuard** – create `code/memory_guard.py` with class `MemoryGuard` that polls `psutil.Process().memory_info().rss` every **10 000** sieve iterations and raises `MemoryLimitExceeded` when usage exceeds **90 %** of the `memory_limit_mb` from the config.  
  *Verification*: `tests/unit/test_memory_guard.py` simulates increasing memory usage and confirms the exception is raised at the correct threshold.

- [ ] T004 [FR‑001] **Pin deterministic seeds** – write `code/seed.py` that sets `random.seed`, `numpy.random.seed`, and stores the seed in the config; expose `get_seed()` for downstream modules.  
  *Verification*: `tests/integration/test_seed_consistency.py` runs the full pipeline twice with the same config and asserts that the resulting `ResidueDataset.frequency_map` files are byte‑identical.

- [ ] T005  **Benchmark instrumentation** – add `code/benchmark.py` providing a context manager `benchmark(name: str)` that records wall‑clock time, peak memory (via `MemoryGuard`), and writes a JSON record to `results/reports/benchmark_{name}.json`.  
  *Verification*: a tiny script `scripts/run_dummy.py` uses the context manager; after execution `results/reports/benchmark_dummy.json` exists and contains numeric `wall_time_sec` and `peak_memory_mb` fields.

---

## Phase 1 – Core computation (totient generation and residue aggregation)

- [ ] T006 [FR‑001][FR‑002] **Linear sieve and residue aggregation** – implement `code/sieve.py` with two public functions:  
  1. `compute_phi_linear_sieve(N: int) -> List[int]` – returns the list of φ values for `1 … N` using Python’s arbitrary‑precision `int`.  
  2. `compute_residues(phi_vals: List[int], prime: int) -> Dict[int, int]` – returns a frequency map `{residue: count}` for the supplied prime.  
  The module must import and use `MemoryGuard` (poll every 10 000 iterations) and raise `MemoryLimitExceeded` if the limit is hit.  
  *Verification*: `tests/unit/test_sieve.py` checks (a) exact φ values for `n = 1 … 10`, (b) correct residue counts for primes `3, 5, 7, 11`, and (c) proper exception raising when a forced low memory limit is supplied.

- [ ] T007 [FR‑001] **Docstrings and static typing** – add comprehensive docstrings to all public callables in `code/sieve.py` and annotate with type hints. Run `mypy` over the `code/` package and ensure zero type‑checking errors.  
  *Verification*: `tests/unit/test_sieve_mypy.py` invokes `mypy` and asserts exit code 0; a docstring‑coverage test confirms every public function has a non‑empty docstring.

- [ ] T016 [SC‑001] **φ‑value correctness validation** – write unit tests (e.g., `tests/unit/test_phi_correctness.py`) that compare `compute_phi_linear_sieve` outputs for `n ≤ 100` against known mathematical tables. The CI must fail if any discrepancy is found.  
  *Verification*: Tests assert exact match for all reference values.

---

## Phase 2 – Statistical analysis (goodness‑of‑fit testing)

- [ ] T008 [FR‑003] **Chi‑squared & exact multinomial testing** – implement `code/stats.py` providing:  
  * `calculate_chi_squared_statistic(dataset: ResidueDataset) -> float` – computes the χ² statistic against the uniform expectation `N/p`.  
  * `run_chi_squared_test(dataset: ResidueDataset, M: int = 10_000, seed: int = 0) -> dict` – returns a JSON‑serialisable dictionary matching the `StatisticalResult` schema.  
    - If any expected count `< 5`, invoke an exact multinomial tail‑probability routine (`exact_multinomial_test`).  
    - Otherwise compute the asymptotic χ² p‑value; if the user requests Monte‑Carlo (`method="monte_carlo"`), draw `M` multinomial samples with the uniform probabilities and estimate the p‑value.  
    - Include fields `test_type`, `test_statistic`, `p_value`, `degrees_of_freedom`, `method`, `expected_counts`, `observed_counts`, `uniformity_hypothesis`, and the `metadata` block.  
  *Verification*: `tests/unit/test_stats.py` contains three sub‑tests: (a) uniform synthetic dataset → p > 0.05, (b) biased synthetic dataset → p < 0.05, (c) small‑N case where expected count < 5 → exact test produces a valid p‑value (compared to a hand‑computed reference).

- [ ] T009 [FR‑006] **Pass/Fail flag generation** – add `code/flags.py` that reads a `StatisticalResult` JSON file and writes `results/reports/flag_{prime}_{N}.json` containing three Boolean fields: `alpha_pass` (p > 0.05), `bonferroni_pass` (p > 0.05/4), and `overall_pass` (true if both pass).  
  *Verification*: `tests/unit/test_flags.py` feeds the module high‑p and low‑p results and asserts that the JSON flag file reflects the correct booleans.

- [ ] T017 [SC‑002] **Synthetic dataset statistical validation** – generate synthetic uniform and deliberately biased residue datasets, run the full statistical pipeline on them, and assert that the resulting `alpha_pass` flags behave as expected (true for uniform, false for biased).  
  *Verification*: Integration test `tests/integration/test_synthetic_stats.py` automates this check.

- [ ] T019 [FR‑030] **Contract validation** – implement a utility (e.g., `code/validate_contracts.py`) that loads each JSON artefact produced by the pipeline and validates it against the corresponding schema in `specs/001-residue-distribution-of-euler-s-totient/contracts/`. The pipeline must abort with a clear error if any artefact fails validation.  
  *Verification*: Unit test `tests/unit/test_contracts.py` feeds both valid and deliberately malformed JSON files and checks that validation succeeds or raises as appropriate.

---

## Phase 3 – Visualization and end‑to‑end orchestration

- [ ] T010 [FR‑005] **Visualization suite** – implement `code/visualize.py` that, for a given prime and `N`, reads the corresponding `ResidueDataset` and `StatisticalResult` JSON files and produces:  
  * a high‑resolution bar plot (`results/plots/bar_{prime}_{N}.png`) showing observed frequencies with a horizontal line at the uniform expectation `N/p`;  
  * a QQ‑plot of the χ² residuals (`results/plots/qq_{prime}_{N}.png`).  
  Both plots must overlay the theoretical error‑bound band `± φ·√N` where `φ = 1.618033988749895` (golden ratio) and be saved as PNG at ≥ 300 DPI.  
  *Verification*: `tests/integration/test_visualization.py` runs the visualizer on a tiny dataset (`N=100`) and asserts that the two PNG files exist and have non‑zero file size.

- [ ] T011 [FR‑001 – FR‑007] **CLI orchestrator** – create `code/run_analysis.py` (executable via `python -m code.run_analysis`) with command‑line options `--N`, `--primes`, `--seed`, `--memory-limit-mb`. The script must:  
  1. Load configuration via `code/config.py`.  
  2. Pin seeds using `code/seed.py`.  
  3. For each prime, invoke the sieve, write `data/raw/residues_{prime}_{N}.json` (conforming to `ResidueDataset` schema).  
  4. Run `code/stats.py` → write `data/processed/stats_{prime}_{N}.json`.  
  5. Run contract validation (T019).  
  6. Generate flags (`code/flags.py`).  
  7. Produce visualizations (`code/visualize.py`).  
  8. Wrap the whole execution in `benchmark("fullrun")` to emit `results/reports/benchmark_fullrun.json`.  
  *Verification*: `tests/integration/test_cli_small.py` executes the CLI with `--N 200 --primes 3,5` and checks that all expected JSON and PNG files are created and that each JSON validates against its contract schema.

- [ ] T018 [SC‑003] **Phase 8 timing verification** – after the full run, assert that `benchmark_fullrun.json` reports `wall_time_sec ≤ 3600` and `peak_memory_mb ≤ 0.9 * memory_limit_mb`. The CI test fails if the constraint is violated.  
  *Verification*: Integrated into `tests/integration/test_full_pipeline.py`.

---

## Phase 4 – Documentation, reproducibility, and full‑scale validation

- [ ] T012 [FR‑001] **Quickstart guide** – update `specs/001-residue-distribution-of-euler-s-totient/quickstart.md` to include:  
  * prerequisites (Python 3.11, virtual‑env activation, `pip install -r code/requirements.txt`),  
  * example commands for a quick validation run (`python -m code.run_analysis --N 1000 --primes 3,5,7,11`) and a full‑scale run (`--N 5000000`),  
  * description of output directories and file naming conventions,  
  * resource expectations (≤ 1 h wall‑clock, ≤ 90 % of 7 GB RAM),  
  * instructions for reproducing the entire workflow from a fresh clone.  
  *Verification*: CI parses the markdown and confirms that the two example command strings appear exactly as written.

- [ ] T013 [SC‑003 & SC‑004] **Full‑scale integration test** – add `tests/integration/test_full_pipeline.py` that runs `python -m code.run_analysis --N 5000000 --primes 3,5,7,11` on the CI runner (using a reduced sample if the runner cannot afford the full size; the test must still verify logic). The test must:  
  1. Validate every `ResidueDataset` and `StatisticalResult` JSON against their respective schemas.  
  2. Assert `results/reports/benchmark_fullrun.json` reports `wall_time_sec ≤ 3600` and `peak_memory_mb ≤ 0.9 * memory_limit_mb`.  
  3. Check that each `flag_{prime}_{N}.json` contains `alpha_pass`, `bonferroni_pass`, and `overall_pass` booleans.  
  4. Confirm that the summary markdown `results/reports/summary_5000000.md` exists and that the numeric table inside matches the JSON artifacts.  
  *Verification*: The CI runs this test; any mismatch causes a failure, ensuring the end‑to‑end pipeline is sound.

- [ ] T014 [FR‑007] **Checksum logging for data hygiene** – implement a small utility `code/checksum.py` that computes SHA‑256 hashes of all files under `data/` after a successful run and writes a mapping to `state/projects/PROJ-771-residue-distribution-of-euler-s-totient-.yaml` under the key `artifact_hashes`.  
  *Verification*: `tests/unit/test_checksum.py` creates a temporary data directory with known files, runs the utility, and asserts that the YAML contains a 64‑character hex string for each file.

---

### Dependency ordering

| Task | Depends on |
|------|------------|
| T001 – T005 | none |
| T006 | T001, T002, T003, T004 |
| T007 | T006 |
| T008 | T006, T002 |
| T009 | T008 |
| T010 | T006, T008 |
| T011 | T001–T010 |
| T012 | T011 |
| T013 | T011, T012 |
| T014 | T011 |
| T016 | T006 |
| T017 | T008 |
| T018 | T011 |
| T019 | T008 |
All tasks are unchecked; they will be marked complete by the verification pipeline once the corresponding artifacts satisfy the listed checks.  