# Tasks: Residue Distribution of Euler's Totient Function Modulo Small Primes  

**Inputs**: `specs/001-residue-distribution-of-euler-s-totient/spec.md`, `plan.md`, data‑model, contract schemas in `specs/001-residue-distribution-of-euler-s-totient/contracts/`, and reviewer feedback.

---  

## Phase 0 – Foundations (setup, reproducibility, resource guards)

- [ ] T001 Create configuration loader – implement `code/config.py` that reads a YAML file `code/config.yaml` (default location) exposing `N`, `primes`, `seed`, and `memory_limit_mb`.  
  *Verification*: `tests/unit/test_config.py` loads the sample config and asserts the parsed values match the file.  

- [ ] T002 Define custom exception hierarchy – add `code/exceptions.py` containing `TotientError`, `MemoryLimitExceeded`, and `InvalidPrimeError`, each with a clear error message.  
  *Verification*: `tests/unit/test_exceptions.py` imports the module, raises each exception, and checks that the message string matches the specification.  

- [ ] T003 Implement MemoryGuard – create `code/memory_guard.py` with class `MemoryGuard` that polls `psutil.Process().memory_info().rss` every **10 000** sieve iterations and raises `MemoryLimitExceeded` when usage exceeds **90 %** of the `memory_limit_mb` from the config.  
  *Verification*: `tests/unit/test_memory_guard.py` simulates increasing memory usage and confirms the exception is raised at the correct threshold.  

- [ ] T004 Pin deterministic seeds – write `code/seed.py` that sets `random.seed`, `numpy.random.seed`, and stores the seed in the config; expose `get_seed()` for downstream modules.  
  *Verification*: `tests/integration/test_seed_consistency.py` runs the full pipeline twice with the same config and asserts that the resulting `data/raw/residues_*.json` files are byte‑identical.  

- [ ] T005 Benchmark instrumentation – add `code/benchmark.py` providing a context manager `benchmark(name: str)` that records wall‑clock time, peak memory (via `MemoryGuard`), and writes a JSON record to `results/reports/benchmark_{name}.json`.  
  *Verification*: `scripts/run_dummy.py` uses the context manager; after execution `results/reports/benchmark_dummy.json` must exist and contain numeric `wall_time_sec` and `peak_memory_mb` fields.  

---  

## Phase 1 – Core computation (totient generation and residue aggregation)

- [ ] T006 Linear sieve and residue aggregation – implement `code/sieve.py` with two public functions:  
  1. `compute_phi_linear_sieve(N: int) -> List[int]` (returns φ values for `1…N` using Python’s arbitrary‑precision `int`).  
  2. `compute_residues(phi_vals: List[int], prime: int) -> Dict[int, int]` (returns a frequency map `{residue: count}`).  
  The module must import and use `MemoryGuard` (poll every 10 000 iterations) and raise `MemoryLimitExceeded` if the limit is hit.  
  *Verification*: `tests/unit/test_sieve.py` checks exact φ values for `n=1…10`, correct residue counts for primes `3,5,7,11`, and proper exception raising under a forced low memory limit.  

- [ ] T007 Docstrings and static typing for sieve – add comprehensive docstrings to all public callables in `code/sieve.py` and annotate with type hints. Run `mypy` over the `code/` package and ensure zero type‑checking errors.  
  *Verification*: `tests/unit/test_sieve_mypy.py` invokes `mypy` and asserts exit code 0; a docstring‑coverage test confirms every public function has a non‑empty docstring.  

- [ ] T016 φ‑value correctness validation – write unit tests (`tests/unit/test_phi_correctness.py`) that compare `compute_phi_linear_sieve` outputs for `n ≤ 100` against known mathematical tables. CI must fail on any discrepancy.  
  *Verification*: Tests assert exact match for all reference values.  

---  

## Phase 2 – Statistical analysis (goodness‑of‑fit testing)

- [ ] T008 Chi‑squared & exact multinomial testing – implement `code/stats.py` providing:  
  * `calculate_chi_squared_statistic(dataset: ResidueDataset) -> float` – computes the χ² statistic against the **biased** expected counts defined in the literature.  
  * `run_chi_squared_test(dataset: ResidueDataset, M: int = 10_000, seed: int = 0) -> dict` – returns a JSON‑serialisable dictionary that **exactly matches** the `StatisticalResult` schema (fields `test_type`, `test_statistic`, `p_value`, `degrees_of_freedom`, `method`, `expected_counts`, `observed_counts`, `uniformity_hypothesis`, `metadata`).  
    - If any expected count < 5, invoke an exact multinomial tail‑probability routine (`exact_multinomial_test`).  
    - Otherwise compute the asymptotic χ² p‑value; if `method="monte_carlo"` draw `M` multinomial samples with the biased probabilities and estimate the p‑value.  
  *Verification*: `tests/unit/test_stats.py` contains three sub‑tests: (a) uniform synthetic dataset → `p > 0.05`, (b) biased synthetic dataset → `p < 0.05`, (c) small‑N case where an expected count < 5 → exact test produces a valid p‑value.  

- [ ] T009 Pass/Fail flag generation – add `code/flags.py` that reads a `StatisticalResult` JSON file and writes `results/reports/flag_{prime}_{N}.json` containing three Boolean fields: `alpha_pass` (`p > 0.05`), `bonferroni_pass` (`p > 0.05/4`), and `overall_pass` (conjunction).  
  *Verification*: `tests/unit/test_flags.py` feeds the module high‑p and low‑p results and asserts that the generated JSON flag file reflects the correct booleans.  

- [ ] T017 Synthetic dataset statistical validation – create integration test `tests/integration/test_synthetic_stats.py` that:  
  1. Generates synthetic uniform and deliberately biased residue datasets for each supported prime.  
  2. Runs the full statistical pipeline (`stats.run_chi_squared_test` → `flags.generate_pass_fail`).  
  3. Asserts that `alpha_pass` is `True` for uniform data and `False` for biased data.  
  *Verification*: Test must pass on the CI runner.  

- [ ] T019 Contract validation utility – expose a top‑level importable function `validate_all(artifact_path: str, schema_path: str) -> None` in a module located at the project root named `validate_contracts.py`. The function loads a JSON artefact, validates it against the supplied JSON‑Schema, and raises a clear `jsonschema.ValidationError` on failure.  
  *Verification*: `tests/unit/test_contracts.py` imports `validate_all` via `from validate_contracts import validate_all`, feeds both valid and deliberately malformed JSON files, and checks that validation succeeds for the former and raises for the latter.  

- [ ] T018 Phase 8 timing verification – after the full run, read `results/reports/benchmark_fullrun.json` and assert `wall_time_sec ≤ 3600` and `peak_memory_mb ≤ 0.9 * memory_limit_mb`. CI fails if either constraint is violated.  
  *Verification*: Integrated into `tests/integration/test_full_pipeline.py`.  

---  

## Phase 3 – Visualization and end‑to‑end orchestration

- [ ] T010 Visualization suite & test – implement `code/visualize.py` that, for a given prime and `N`, reads the corresponding `ResidueDataset` and `StatisticalResult` JSON files and produces:  
  * a high‑resolution bar plot (`results/plots/bar_{prime}_{N}.png`) showing observed frequencies with a horizontal line at the biased expected count;  
  * a QQ‑plot of the χ² residuals (`results/plots/qq_{prime}_{N}.png`).  
  Both plots must overlay the theoretical error‑bound band `± φ·√N` (φ = golden ratio) and be saved as PNG at ≥ 300 DPI.  
  *Verification*: `tests/integration/test_visualization.py` runs the visualizer on a tiny dataset (`N=100`) and asserts that the two PNG files exist, are non‑empty, and have a resolution of at least 300 DPI.  

- [ ] T011 CLI orchestrator – create `code/run_analysis.py` (executable via `python -m code.run_analysis`) with command‑line options `--N`, `--primes`, `--seed`, `--memory-limit-mb`. The script must:  
  1. Load configuration via `code/config.py`.  
  2. Pin seeds using `code/seed.py`.  
  3. For each prime, invoke the sieve, write `data/raw/residues_{prime}_{N}.json` (conforming to `ResidueDataset` schema).  
  4. Run `code/stats.py` → write `data/processed/stats_{prime}_{N}.json`.  
  5. Run contract validation (`validate_all`).  
  6. Generate flags (`code/flags.py`).  
  7. Produce visualizations (`code/visualize.py`).  
  8. Wrap the whole execution in `benchmark("fullrun")` to emit `results/reports/benchmark_fullrun.json`.  
  *Verification*: `tests/integration/test_cli_small.py` executes the CLI with `--N 200 --primes 3,5` and checks that all expected JSON and PNG files are created, each validates against its schema, and the benchmark file records reasonable resource usage.  

- [ ] T012 Quickstart guide – update `specs/001-residue-distribution-of-euler-s-totient/quickstart.md` to include:  
  * Prerequisites (Python 3.11, virtual‑env activation, `pip install -r code/requirements.txt`).  
  * Example commands for a quick validation run (`python -m code.run_analysis --N 1000 --primes 3,5,7,11`) and a full‑scale run (`--N 5000000`).  
  * Description of output directories and file‑naming conventions.  
  * Resource expectations (≤ 1 h wall‑clock, ≤ 90 % of 7 GB RAM).  
  * Instructions for reproducing the entire workflow from a fresh clone.  
  *Verification*: CI parses the markdown and confirms that the two example command strings appear exactly as written.  

- [ ] T013 Full‑scale integration test – add `tests/integration/test_full_pipeline.py` that runs `python -m code.run_analysis --N 5000000 --primes 3,5,7,11` (or a reduced sample if the runner cannot afford the full size, but the test must still verify logic). The test must:  
  1. Validate every `ResidueDataset` and `StatisticalResult` JSON against their schemas.  
  2. Assert `benchmark_fullrun.json` reports `wall_time_sec ≤ 3600` and `peak_memory_mb ≤ 0.9 * memory_limit_mb`.  
  3. Check that each `flag_{prime}_{N}.json` contains `alpha_pass`, `bonferroni_pass`, and `overall_pass`.  
  4. Confirm that a summary markdown `results/reports/summary_5000000.md` exists and that the numeric table inside matches the JSON artefacts.  
  *Verification*: CI runs this test; any mismatch causes a failure.  

- [ ] T014 Checksum logging for data hygiene – implement `code/checksum.py` that computes SHA‑256 hashes of all files under `data/` after a successful run and writes a mapping to `state/projects/PROJ-771-residue-distribution-of-euler-s-totient-.yaml` under the key `artifact_hashes`.  
  *Verification*: `tests/unit/test_checksum.py` creates a temporary data directory with known files, runs the utility, and asserts that the YAML contains a 64‑character hex string for each file.  

---  

## Dependency ordering

| Task | Depends on |
|------|------------|
| T001–T004 | none |
| T005 | T001–T004 |
| T006 | T001–T004 |
| T007 | T006 |
| T016 | T006 |
| T008 | T006, T001–T004 |
| T009 | T008 |
| T017 | T008, T009 |
| T019 | none (top‑level import) |
| T010 | T006, T008 |
| T011 | T001–T010, T019 |
| T012 | T011 |
| T013 | T011, T012 |
| T014 | T011 |
| T018 | T011 |
| T018 is verified within T013 |

All unchecked tasks must be completed and pass their respective verification steps before the project can advance to the next stage. Checked tasks have already satisfied their verification criteria.
