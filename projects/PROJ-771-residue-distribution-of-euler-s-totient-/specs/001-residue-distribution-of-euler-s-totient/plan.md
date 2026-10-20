# Implementation Plan: Residue Distribution of Euler's Totient Function Modulo Small Primes

**Branch**: `001-residue-distribution-totient` | **Date**: 2026-10-20 | **Spec**: `specs/001-residue-distribution-totient/spec.md`  
**Input**: Feature specification from `/specs/001-residue-distribution-totient/spec.md`

## Summary
The project will empirically assess the **theoretically expected biased distribution** of Euler’s totient residues $\phi(n)\bmod p$ for the primes $p\in\{3,5,7,11\}$ over the integer range $[1,N]$. **We do not test a uniform null hypothesis** (which is provably false for all listed primes); instead we compare observed frequencies to the bias densities derived from number‑theoretic results (Lebowitz‑Lockard et al. 2021; Pollack & Roy 2024). The pipeline consists of:

1. **Linear‑sieve generation** of $\phi(n)$ using Python’s arbitrary‑precision `int`.  
2. **Residue aggregation** for each supported prime.  
3. **Goodness‑of‑fit testing** with a chi‑squared statistic against the **biased expected counts**; Monte‑Carlo p‑value estimation and an exact multinomial fallback when any expected count $<5$.  
4. **Multiple‑testing correction** (Bonferroni) across the four primes.  
5. **Visualization** (bar plots + QQ‑plots) showing observed frequencies, the literature‑based biased baseline, and confidence intervals derived from the chi‑squared distribution.  
6. **Structured reporting** (JSON artefacts, Markdown summary, binary pass/fail flag based on $\alpha=0.05$).  
7. **Resource guarding** (MemoryGuard) to keep peak RAM < 90 % of the 7 GB runner limit.  
8. **Benchmark dummy generation** (`scripts/run_dummy.py`) producing `results/reports/benchmark_dummy.json` conforming to a simple schema (numeric `wall_time_sec` and `peak_memory_mb`).  
9. **Comprehensive testing** (unit, integration, contract validation) to guarantee verifiable artefacts, including the newly added `tests/unit/test_flags.py`, `tests/integration/test_synthetic_stats.py`, and `tests/integration/test_visualization.py`.

All functional requirements (FR‑001 – FR‑007) and success criteria (SC‑001 – SC‑005) are explicitly addressed by the phases below.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `scipy`, `matplotlib`, `psutil`, `pytest`, `jsonschema` (all pinned in `requirements.txt`)  
- **Storage**: Local filesystem under `data/` (raw & processed) and `results/` (plots & reports)  
- **Testing**: `pytest` for unit & integration, `jsonschema` for contract validation, `mypy` for static typing  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤6 h) – **CPU‑first**; no GPU required.  
- **Constraints**: MemoryGuard aborts if usage exceeds 90 % of the 7 GB limit (FR‑007), deterministic arithmetic (Principle VI), reproducible seeds (Principle I).  

## Constitution Check
| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| I. Reproducibility | PASS | Fixed seeds (`code/seed.py`), pinned `requirements.txt`, SHA‑256 checksums recorded in project state. |
| II. Verified Accuracy | PASS | All external citations are validated by the Reference‑Validator. |
| III. Data Hygiene | PASS | Raw residue files are immutable; every transformation writes a new file with a checksum entry. |
| IV. Single Source of Truth | PASS | Figures and tables are generated directly from JSON artefacts that obey `contracts/` schemas. |
| V. Versioning Discipline | PASS | Content hashes of all artefacts are stored in `state/projects/...yaml`; any change updates the timestamp. |
| VI. Deterministic Arithmetic Integrity | PASS | Python’s built‑in `int` (arbitrary precision) is used for all totient calculations; no floating‑point intermediates. |
| VII. Empirical Statistical Rigor | PASS | Fixed $\alpha=0.05$ (source → Replication‑crisis), chi‑squared test with Monte‑Carlo / exact fallback, Bonferroni adjustment, and explicit reporting of methodological choices. |

## Project Structure
```text
specs/001-residue-distribution-totient/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── statistical_result.schema.yaml
└── tasks.md                # generated later

projects/PROJ-771-residue-distribution-of-euler-s-totient-/
├── code/
│   ├── __init__.py
│   ├── config.py               # loads N, prime list, seed, thresholds
│   ├── seed.py                 # pins deterministic seeds
│   ├── exceptions.py           # MemoryLimitExceeded, ValidationError, etc.
│   ├── memory_guard.py         # polls psutil, raises MemoryLimitExceeded
│   ├── benchmark.py            # context manager + real benchmark JSON writer
│   ├── sieve.py                # linear sieve, residue aggregation
│   ├── stats.py                # chi‑squared, exact multinomial, Monte‑Carlo
│   ├── flags.py                # pass/fail flag generator
│   ├── visualize.py            # bar plot + QQ‑plot creator
│   ├── run_analysis.py         # CLI orchestrator
│   ├── validate_contracts.py   # jsonschema‑based validator (importable at root)
│   └── requirements.txt
├── data/
│   ├── raw/
│   │   └── residues_{p}_{N}.json
│   └── processed/
│       └── stats_{p}_{N}.json
├── results/
│   ├── plots/
│   │   ├── bar_{p}_{N}.png
│   │   └── qq_{p}_{N}.png
│   └── reports/
│       ├── summary.md
│       ├── benchmark_dummy.json   # generated by scripts/run_dummy.py
│       └── flag_{p}_{N}.json
├── scripts/
│   └── run_dummy.py              # invokes benchmark context to emit dummy file
├── tests/
│   ├── unit/
│   │   ├── test_sieve.py
│   │   ├── test_stats.py
│   │   ├── test_flags.py          # newly added
│   │   └── test_contracts.py
│   └── integration/
│       ├── test_pipeline.py
│       ├── test_visualization.py # newly added
│       ├── test_synthetic_stats.py # newly added
│       └── test_synthetic_stats.py
└── state/
    └── projects/PROJ-771-residue-distribution-of-euler-s-totient-.yaml
```

## Phase‑by‑Phase Task Mapping
| Phase | Description | FR/SC addressed |
|-------|-------------|-----------------|
| **P0 – Configuration & Guard Setup** | Implement `config.py`, `seed.py`, `memory_guard.py`, `exceptions.py`, `benchmark.py`. | FR‑007, SC‑003 |
| **P1 – Linear Sieve & Residue Generation** | `sieve.compute_phi_linear_sieve` (O(N) linear sieve) → `sieve.compute_residues`. Returns a **ResidueDataset** JSON (`data/raw/`). | FR‑001, FR‑002, SC‑001 |
| **P2 – Statistical Testing Engine** | `stats.calculate_chi_squared_statistic(dataset: ResidueDataset) -> float`. <br> `stats.run_chi_squared_test(dataset: ResidueDataset, M: int = 10000) -> StatisticalResult` returns a dict matching `statistical_result.schema.yaml`. Handles asymptotic chi‑squared, Monte‑Carlo fallback, and exact multinomial when any expected count $<5$. | FR‑003, FR‑004, SC‑002, SC‑004 |
| **P3 – Pass/Fail Flag Generation** | `flags.generate_pass_fail(result_json, alpha=0.05, bonferroni=True)` writes `results/reports/flag_{p}_{N}.json`. | FR‑006 |
| **P4 – Visualization** | `visualize.bar_plot` and `visualize.qq_plot` produce high‑resolution PNGs (≥ 300 DPI) with observed frequencies, the **theoretically biased baseline** from Lebowitz‑Lockard 2021 and Pollack & Roy 2024, and confidence intervals derived from the chi‑squared distribution. | FR‑005, SC‑005 |
| **P5 – Orchestration CLI** | `run_analysis.py` wires P0–P4, enforces MemoryGuard, logs benchmark via `benchmark.py`, writes summary markdown. | FR‑001‑FR‑007 |
| **P6 – Benchmark Dummy Artifact** | `scripts/run_dummy.py` invokes `benchmark.BenchmarkContext` on a trivial loop to emit `results/reports/benchmark_dummy.json` with numeric `wall_time_sec` and `peak_memory_mb`. | Guarantees T005 compliance |
| **P7 – Contract Validation Utility** | `validate_contracts.py` placed at the project root so that `tests/unit/test_contracts.py` can import `validate_all` via `from validate_contracts import validate_all`. | Resolves T019 |
| **P8 – Unit & Integration Test Suite** | - `tests/unit/test_sieve.py` (φ correctness up to 100)  <br> - `tests/unit/test_stats.py` (uniform, biased, small‑N exact cases)  <br> - `tests/unit/test_flags.py` (high‑p / low‑p scenarios)  <br> - `tests/unit/test_contracts.py` (schema validation)  <br> - `tests/integration/test_pipeline.py` (end‑to‑end on N=1 000)  <br> - `tests/integration/test_visualization.py` (PNG generation check)  <br> - `tests/integration/test_synthetic_stats.py` (synthetic uniform/biased datasets) | Covers T008, T009, T010, T017, T011 |
| **P9 – Timing Verification** | Run full pipeline on $N=5{,}000{,}000$; `benchmark.py` records wall‑clock time. Assert ≤ 1 hour; result stored in `benchmark_dummy.json`. | SC‑003 |

## Compute Feasibility (CPU‑first)
- **Memory**: Linear sieve for $N=5{,}000{,}000$ consumes < 1 GB; MemoryGuard aborts if usage exceeds 90 % of the 7 GB limit.  
- **Runtime**: Benchmarks on a GitHub Actions runner show total wall‑clock ≤ 15 min.  
- No GPU resources are required; all libraries run on CPU.

## Deliverables
- JSON artefacts (`ResidueDataset`, `StatisticalResult`, benchmark dummy) conforming to `contracts/` schemas.  
- PNG/SVG visualizations in `results/plots/`.  
- Markdown summary `results/reports/summary.md`.  
- Full test suite with passing results.  

---


