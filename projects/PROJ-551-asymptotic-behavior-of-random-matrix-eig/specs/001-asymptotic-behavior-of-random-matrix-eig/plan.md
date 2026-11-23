# Implementation Plan: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

**Branch**: `feature/asymptotic-random-matrix` | **Date**: 2026-10-17 (re‑plan) | **Spec**: [spec.md](../spec.md)
**Input**: Feature specification from `/specs/feature/asymptotic-random-matrix/spec.md`

> **Re‑plan note**: This is a targeted repair of the previously rejected tasks T001, T003, T006, T007. Working artifacts (schema files, single‑run eigenvalue computation producing a top eigenvalue of the expected order of magnitude for the reference configuration) are preserved. The failures were all *verifiability* failures, not scientific ones: (a) promised artifacts (results JSON, matrix checksum, validation output) were never written to disk; (b) contract tests skipped instead of validating the real files in `data/processed/`; (c) `threshold_fit.py` and `aggregate_thresholds.py` exited 1. The fix is a **write‑then‑verify discipline**: every analysis step must (1) write a real file with a schema‑conformant top‑level structure and (2) pass a contract test that loads that exact file and validates it against the matching schema — no catch‑all "non‑empty" branches, no skipped tests.

## Summary
Empirically verify the BBP phase‑transition threshold for large Wigner matrices perturbed by deterministic sparse matrices. Generate synthetic Wigner ensembles (scaled by \(1/\sqrt N\)), construct sparse perturbations of configurable rank \(k\) and support density \(p\), compute top eigenvalues with ARPACK (`scipy.sparse.linalg.eigsh`), detect outliers using the theoretical semicircle edge (2, per arXiv:0812.2602) plus a tolerance that scales with matrix size, and sweep perturbation norms (\(\theta\)) and sparsity density to estimate the critical threshold \(\theta_c\). All steps are deterministic via pinned seeds; every output is a real, checksummed, schema‑validated file.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `numpy`, `scipy`, `pandas`, `pyarrow`, `pydantic`, `matplotlib`, `jsonschema` (pinned in `code/requirements.txt`)
- **Storage**: File‑system (JSON + Parquet under `data/processed/`); SHA‑256 checksums in `data/checksums.yaml`
- **Testing**: `pytest` with contract tests that load and validate the actual `data/processed/` artifacts
- **Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU, ~7 GB RAM, ~14 GB disk, no GPU) — CPU‑first
- **Constraints**:
  - **SC-001** – Memory ≤ 7 GB.
  - **SC-002** – CPU‑only; iterative solvers (ARPACK).
  - **SC-003** – Full reproducibility via fixed seeds, checksums, and artifact‑level verification.
  - **SC-004** – ARPACK tolerance 1e‑10, maxiter 1000.
  - **SC-005** – Every output file conforms to a contract in `contracts/` and is validated by a passing (non‑skipped) test.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | Fixed seeds recorded in `SimulationRun`; every run writes real artifacts with SHA‑256 checksums; `code/requirements.txt` pins all packages; integration test re‑runs a configuration and compares against the stored reference value. |
| II. Verified Accuracy | Only citation used: semicircle edge = 2 (arXiv:0812.2602, verified). |
| III. Data Hygiene | Raw matrix checksums written to `data/checksums.yaml`; derivations write new files; no PII (synthetic data only). |
| IV. Single Source of Truth | Every figure/table/statistic is generated programmatically from `data/processed/` files; no hand‑typed numbers. |
| V. Versioning Discipline | All artifacts content‑hashed; state file `updated_at` maintained by the platform. |
| VI. Spectral Numerical Stability | ARPACK with `tol=1e-10`, `maxiter=1000`; bulk edge validated against theoretical 2 (verified value, arXiv:0812.2602). |
| VII. Sparse Perturbation Structural Fidelity | Perturbation rank, pattern, and support density recorded in every `SimulationRun` record; spectral norm enforced by explicit scaling and verified post‑construction. |

## Project Structure
```text
code/
├── main.py                  # CLI entry point (python -m code.main ...)
├── requirements.txt         # Pinned dependencies
├── simulation/
│   ├── wigner.py            # Wigner matrix generator (preserved)
│   ├── perturbation.py      # Sparse deterministic perturbations (preserved)
│   └── eigen_solver.py      # ARPACK wrapper + outlier detection (preserved)
├── analysis/
│   ├── sweep.py             # Parameter sweep driver
│   ├── sensitivity.py       # Sparsity density sweep
│   ├── finite_size.py       # N‑sweep analysis
│   ├── aggregate_thresholds.py  # REPAIRED — writes `aggregated_thresholds.json` (no theta_c fields)
│   └── threshold_fit.py     # REPAIRED — writes `threshold_fit.json` (validated against `threshold_fit.schema.yaml`)
├── utils/
│   ├── checksum.py          # SHA‑256 utilities (REPAIRED — always invoked by run modes)
│   └── artifacts.py         # NEW: canonical artifact writer (top‑level keys match contracts exactly)
└── tests/
    ├── contract/
    │   └── test_schemas.py  # REPAIRED: per‑file, per‑schema validation; FAILS on missing files
    └── integration/
        └── test_t001.py     # Reproducibility test against stored reference

data/
├── processed/               # All JSON/Parquet outputs (schema‑valid, checksummed)
└── checksums.yaml           # SHA‑256 map, updated on every write

contracts/
├── simulation_run.schema.yaml
├── eigenvalue_result.schema.yaml
├── aggregated_threshold.schema.yaml   # Updated: theta minimum 0.5, no theta_c fields
├── convergence_report.schema.yaml
└── threshold_fit.schema.yaml         # NEW: schema for sigmoid‑fit results
```

## Complexity Tracking
No constitution violations require justification.

## Phases & Tasks

| Phase | Description | FR/SC addressed |
|-------|-------------|-----------------|
| **0 – Artifact‑writing discipline (REPAIR)** | Add `utils/artifacts.py`: a single `write_artifact(path, data, schema_name)` function that (a) validates `data` against the named contract BEFORE writing, (b) writes JSON with top‑level keys exactly matching the contract, (c) appends the SHA‑256 to `data/checksums.yaml`, (d) prints the written path + checksum to stdout. Every analysis entry point must route all output through this function. | SC‑003, SC‑005 |
| **1 – Core generators (preserved)** | `wigner.py` (FR‑001), `perturbation.py` (FR‑002) — already working; unchanged. | FR‑001, FR‑002, SC‑004 |
| **2 – Eigenvalue engine (preserved)** | `eigen_solver.py` with ARPACK (FR‑003) — already working (reference top eigenvalue (a representative high eigenvalue)). | FR‑003, SC‑002, SC‑004 |
| **3 – Single‑run artifact (REPAIR of T003)** | `python -m code.main --mode single ...` must, on every invocation: write `data/processed/single_run_results.json` (structure: a `SimulationRun` record plus an `eigenvalue_results` array of `EigenvalueResult` records — key names fixed by `artifacts.py`), write the SHA‑256 of the raw Wigner matrix bytes to `data/checksums.yaml`, and write `data/processed/convergence_report.json` (per `convergence_report.schema.yaml`) recording ARPACK convergence status, tolerance, maxiter, and the validation result. stdout must echo each artifact path and checksum. Verification = the files exist, parse, and pass contract tests. | FR‑004, SC‑003, SC‑005 |
| **4 – Parameter sweep** | `sweep.py` loops over the \(\theta\) grid \([0.5,3.0]\) for each pattern/rank, writing `data/processed/sweep_runs.parquet` (raw run/eigenvalue records) via `artifacts.py`‑equivalent Parquet path. **All** theta values, including sub‑threshold \(\theta<1\), are retained in the raw Parquet. Aggregated statistics (Phase 7) operate on this full set. | FR‑005, SC‑001 |
| **5 – Sparsity sensitivity** | `sensitivity.py` varies support density \(p\) (FR‑006). | FR‑006 |
| **6 – Finite‑size analysis** | `finite_size.py` sweeps \(N\in\{500,1000,1500,2000\}\) for representative configurations; quantifies finite‑size shifts in bulk edge and outlier probability. | FR‑006, Constitution VI |
| **7 – Aggregation (REPAIR of T007)** | `aggregate_thresholds.py` reads the sweep Parquet, groups by configuration **excluding** any theta‑c fields, and writes `data/processed/aggregated_thresholds.json` — an array of `AggregatedThreshold` records **without** `theta_c_estimate` or `theta_c_confidence`. Failure mode fixed: empty input raises a clear error before exit (no silent exit 1). | FR‑007, SC‑005 |
| **8 – Threshold fit (REPAIR of T006)** | `threshold_fit.py` reads the **raw** run records (including \(\theta<1\)) and fits a sigmoid \(f(\theta)=1/(1+\exp[-a(\theta-\theta_c)])\). It writes `data/processed/threshold_fit.json` validated against the new `threshold_fit.schema.yaml`. Non‑convergent fits are recorded with `fit_status: "failed"` and `theta_c_estimate`/`theta_c_confidence` set to `null` (per schema). | FR‑007, SC‑005 |
| **9 – Contract tests (REPAIR of T001)** | Rewrite `tests/contract/test_schemas.py`: one test per expected artifact file (`single_run_results.json`, `convergence_report.json`, `sweep_runs.parquet`, `aggregated_thresholds.json`, `threshold_fit.json`, sensitivity/finite‑size outputs). Each test loads the REAL file and validates against the matching schema. Missing files cause **FAIL**, never SKIP. No catch‑all branches: each file maps to exactly one schema and one validator. `pytest tests/contract/ -v` must show all tests as PASSED. | SC‑005 |
| **10 – Integration test** | `test_t001.py` re‑runs the reference single‑run configuration and asserts the top eigenvalue matches the stored reference within 1e‑6 and that the artifact files are regenerated identically (checksum match on the deterministic parts). | SC‑003 |
| **11 – Figures & evidence summary** | Generate figures (outlier probability vs \(\theta\); \(\theta_c\) vs density; finite‑size plots) from the processed files; write evidence summary table. | All FR |

Execution order: data‑producing phases (1–8) run before validation (9–10) and figures (11); aggregation (7) runs only after sweep (4); threshold fit (8) runs only after aggregation (7).

---


