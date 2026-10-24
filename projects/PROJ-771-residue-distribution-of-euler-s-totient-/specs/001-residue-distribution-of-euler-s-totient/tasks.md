# Tasks: Residue Distribution of Euler's Totient Function Modulo Small Primes  

**Inputs**: `specs/001-residue-distribution-of-euler-s-totient/spec.md`, `plan.md`, data‑model, contract schemas in `specs/001-residue-distribution-of-euler-s-totient/contracts/`, and reviewer feedback.

---  

## Phase 0 – Project‑wide infrastructure (setup, reproducibility, resource guards)

- [X] T001 Create core configuration and exception modules – implement `code/config.py` (loads `code/config.yaml` exposing `N`, `primes`, `seed`, `memory_limit_mb`) and `code/exceptions.py` defining `TotientError`, `MemoryLimitExceeded`, `InvalidPrimeError`. The configuration loader MUST reject any prime $p \notin \{3, 5, 7, 11\}$ with a clear error message as per the Spec Edge Cases.  
  *Verification*: `tests/unit/test_config.py` loads the sample config and asserts the parsed values; it also asserts that an `InvalidPrimeError` is raised when an unsupported prime is provided. `tests/unit/test_exceptions.py` raises each exception and checks the message string.

- [ ] T002 Implement deterministic seeding and memory guard – add `code/seed.py` (sets `random.seed`, `numpy.random.seed`, exposes `get_seed()`) and `code/memory_guard.py` (class `MemoryGuard` polls `psutil` every 10 000 sieve iterations and raises `MemoryLimitExceeded` if RSS ≥ 90 % of `memory_limit_mb`).  
  *Verification*: `tests/unit/test_seed_consistency.py` runs the full pipeline twice with identical config and confirms the generated `data/raw/residues_*.json` files are byte‑identical; `tests/unit/test_memory_guard.py` simulates rising memory usage and asserts the exception fires at the correct threshold.

- [X] T003 Benchmark instrumentation and dummy run – create `code/benchmark.py` providing a context manager `benchmark(name: str)` that records wall‑clock time, peak memory (via `MemoryGuard`), and writes a JSON report to `results/reports/benchmark_{name}.json`. Add `scripts/run_dummy.py` that executes `benchmark("dummy")` around a trivial loop to explicitly produce `results/reports/benchmark_dummy.json`.  
  *Verification*: After running `python scripts/run_dummy.py`, `results/reports/benchmark_dummy.json` must exist and contain numeric `wall_time_sec` and `peak_memory_mb` fields; `tests/integration/test_benchmark_dummy.py` checks for the file and validates its schema.

---  

## Phase 1 – Core computation (totient generation and residue aggregation)

- [ ] T004 Linear sieve and residue aggregation – implement `code/sieve.py` with two public functions:  
  1. `compute_phi_linear_sieve(N: int) -> List[int]` (returns φ values for `1…N` using Python’s arbitrary‑precision `int`). This function MUST halt execution and log the specific $n$ where any overflow or logic error occurs.  
  2. `compute_residues(phi_vals: List[int], prime: int) -> Dict[int, int]` (returns a frequency map `{residue: count}`).  
  The module must import and use `MemoryGuard` (poll every 10 000 iterations).  
  *Verification*: `tests/unit/test_sieve.py` checks exact φ values for `n=1…10`, correct residue counts for primes `3,5,7,11`, and proper exception raising/logging under a forced low memory limit.

- [X] T005 Documentation, static typing, and φ‑value correctness suite – add comprehensive docstrings and full type hints to all public callables in `code/sieve.py`; run `mypy` over the `code/` package with zero errors. Write `tests/unit/test_phi_correctness.py` that compares `compute_phi_linear_sieve` outputs for `n ≤ 100` against known tables.  
  *Verification*: `tests/unit/test_sieve_mypy.py` invokes `mypy` and asserts exit code 0; `tests/unit/test_phi_correctness.py` asserts exact matches for all reference values.

---  

## Phase 2 – Statistical analysis (goodness‑of‑fit testing, flagging, and contract validation)

- [ ] T006 Statistical engine conforming to schema – implement `code/stats.py` providing:  
  * `calculate_chi_squared_statistic(dataset: ResidueDataset) -> float` – computes the χ² statistic against the **uniform** expected counts ($E_i = N/p$).  
  * `run_chi_squared_test(dataset: ResidueDataset, M: int = 10_000) -> dict` – returns a JSON‑serialisable dict that **exactly matches** the `StatisticalResult` schema (fields `test_type`, `test_statistic`, `p_value`, `degrees_of_freedom`, `method`, `expected_counts`, `observed_counts`, `uniformity_hypothesis`, `metadata`).  
    - If any expected count < 5, invoke an exact multinomial tail‑probability routine (`exact_multinomial_test`).  
    - Otherwise compute the asymptotic χ² p‑value; if `method="monte_carlo"`, draw `M` multinomial samples with uniform probabilities and estimate the p‑value.  
  *Verification*: `tests/unit/test_stats.py` contains three sub‑tests: (a) uniform synthetic dataset → `p > 0.05`; (b) biased synthetic dataset → `p < 0.05`; (c) small‑N case with an expected count < 5 → exact test returns a valid p‑value and `test_type` = `"exact_multinomial"`.

- [ ] T007 Pass/Fail flag generation and unit test – add `code/flags.py` that reads a `StatisticalResult` JSON file and writes `results/reports/flag_{prime}_{N}.json` containing a boolean `alpha_pass` (`p > 0.05`) and `overall_pass` (matching `alpha_pass`). Implement `tests/unit/test_flags.py` that feeds the module high‑p and low‑p results and asserts the generated JSON flag file reflects the correct booleans.  
  *Verification*: Running the unit test must produce the flag files and verify their contents.

- [ ] T008 Synthetic dataset integration test – create `tests/integration/test_synthetic_stats.py` that:  
  1. Generates synthetic uniform and deliberately biased residue datasets for each supported prime.  
  2. Executes the full statistical pipeline (`stats.run_chi_squared_test` → `flags.generate_pass_fail`).  
  3. Asserts `alpha_pass` is `True` for uniform data and `False` for biased data.  
  *Verification*: The integration test must pass on the CI runner.

- [ ] T009 Contract validation utility at project root – implement the validator as a top‑level module `validate_contracts.py` (located at the project root) exposing `validate_all(artifact_path: str, schema_path: str) -> None`. The function loads a JSON artefact, validates it against the supplied JSON‑Schema, and raises `jsonschema.ValidationError` on failure. Provide `tests/unit/test_contracts.py` that imports `validate_all` via `from validate_contracts import validate_all`, testing both a valid and an intentionally malformed JSON file.  
  *Verification*: The unit test must succeed for the valid case and raise for the invalid case.

---  

## Phase 3 – Visualization, orchestration, and full‑pipeline verification

- [ ] T010 Visualization suite and integration test – implement `code/visualize.py` that, for a given prime and `N`, reads the corresponding `ResidueDataset` and `StatisticalResult` JSON files and produces:  
  * a high‑resolution bar plot (`results/plots/bar_{prime}_{N}.png`) showing observed frequencies with a horizontal reference line at the **uniform expectation** $N/p$;  
  * a QQ‑plot of the χ² residuals (`results/plots/qq_{prime}_{N}.png`).  
  Both plots must be saved as PNG at ≥ 300 DPI. Implement `tests/integration/test_visualization.py` that runs the visualizer on a tiny dataset (`N=100`) and asserts the two PNG files exist, are non‑empty, and have a resolution of at least 300 DPI.  
  *Verification*: The integration test must pass and the PNG files must meet the resolution requirement.

- [ ] T011 CLI orchestrator – create `code/run_analysis.py` (executable via `python -m code.run_analysis`) with command‑line options `--N`, `--primes`, `--seed`, `--memory-limit-mb`. The script must:  
  1. Load configuration via `code/config.py`.  
  2. Pin seeds using `code/seed.py`.  
  3. For each prime, invoke the sieve, write `data/raw/residues_{prime}_{N}.json` (conforms to `ResidueDataset`).  
  4. Run `code/stats.py` → write `data/processed/stats_{prime}_{N}.json`.  
  5. Validate each artefact with `validate_all`.  
  6. Generate flags (`code/flags.py`).  
  7. Produce visualizations (`code/visualize.py`).  
  8. Wrap the whole execution in `benchmark("fullrun")` to emit `results/reports/benchmark_fullrun.json`.  
  Provide `tests/integration/test_cli_small.py` that executes the CLI with `--N 200 --primes 3,5` and checks that all expected JSON and PNG files are created, each validates against its schema, and the benchmark file records reasonable resource usage.  
  *Verification*: The integration test must complete without error.

- [ ] T012 Quickstart documentation – update `specs/001-residue-distribution-of-euler-s-totient/quickstart.md` to include:  
  * Prerequisites (Python 3.11, virtual‑env, `pip install -r code/requirements.txt`).  
  * Example commands for a quick validation run (`python -m code.run_analysis --N 1000 --primes 3,5,7,11`) and a full‑scale run (`--N 5000000`).  
  * Description of output directories and naming conventions.  
  * Resource expectations (≤ 1 h wall‑clock, ≤ 90 % of 7 GB RAM).  
  * Instructions for reproducing the workflow from a fresh clone.  
  *Verification*: CI parses the markdown and confirms the two example command strings appear exactly as written.

- [ ] T013 Full‑pipeline integration test and checksum logging – add `tests/integration/test_full_pipeline.py` that runs `python -m code.run_analysis --N 5000000 --primes 3,5,7,11` (or, if the runner cannot afford the full size, runs with a reduced sample but still validates logic). The test must:  
  1. Validate every `ResidueDataset` and `StatisticalResult` JSON against their schemas.  
  2. Assert `results/reports/benchmark_fullrun.json` reports `wall_time_sec ≤ 3600` and `peak_memory_mb ≤ 0.9 * memory_limit_mb`.  
  3. Check that each `results/reports/flag_{prime}_{N}.json` contains `alpha_pass` and `overall_pass`.  
  4. Confirm that a summary markdown `results/reports/summary_{N}.md` exists and that its numeric table matches the JSON artefacts.  
  Implement `code/checksum.py` that computes SHA‑256 hashes of all files under `data/` after a successful run and writes a mapping to `state/projects/PROJ-771-residue-distribution-of-euler-s-totient-.yaml` under the key `artifact_hashes`.  
  *Verification*: `tests/unit/test_checksum.py` creates a temporary data directory, runs the utility, and asserts each file has a 64‑character hex hash entry in the YAML.

---  

## Dependency ordering

| Task | Depends on |
|------|------------|
| T001 | – |
| T002 | T001 |
| T003 | T001, T002 |
| T004 | T001, T002 |
| T005 | T004 |
| T006 | T004 |
| T007 | T006 |
| T008 | T006, T007 |
| T009 | – (stand‑alone utility) |
| T010 | T004, T006 |
| T011 | T001–T010, T009 |
| T012 | T011 |
| T013 | T011, T012, T009 |

All unchecked tasks must be completed and pass their respective verification steps before the project can advance to the next stage. Checked tasks have already satisfied their verification criteria and are retained.