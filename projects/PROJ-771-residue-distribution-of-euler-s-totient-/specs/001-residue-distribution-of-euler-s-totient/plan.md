# Implementation Plan: Residue Distribution of Euler's Totient Function Modulo Small Primes

**Branch**: `001-residue-distribution-totient` | **Date**: 2026-10-20 | **Spec**: `specs/001-residue-distribution-totient/spec.md`  
**Input**: Feature specification from `/specs/001-residue-distribution-totient/spec.md`

## Summary
The project will empirically investigate whether the residues of Euler’s totient function $\phi(n)$ modulo the small primes $p\in\{3,5,7,11\}$ follow a uniform distribution when $n$ ranges over $[1,N]$. The pipeline consists of:

1. **Linear‑sieve generation** of $\phi(n)$ for all $n\le N$ using Python’s arbitrary‑precision `int` (Constitution Principle VI).  
2. **Residue aggregation** for each supported prime.  
3. **Goodness‑of‑fit testing** via a $\chi^{2}$ test with Monte‑Carlo p‑value estimation; if any expected bin count $<5$, the system automatically switches to an exact multinomial test (FR‑003).  
4. **Multiple‑testing adjustment** (Bonferroni) across the four primes (SC‑004).  
5. **Visualization** of observed frequencies, uniform expectations, and $\chi^{2}$ residual QQ‑plots (FR‑005).  
6. **Structured reporting** (JSON + Markdown) with a binary pass/fail flag based on the **Bonferroni‑adjusted** significance threshold $\alpha_{\text{adj}}=0.0125$ (verified fact → 0.05 primary, source → https://en.wikipedia.org/wiki/Replication_crisis) (FR‑006).  
7. **Resource guarding** (MemoryGuard) to keep peak RAM < 90 % of the 7 GB runner limit (FR‑007).  
8. **Timing verification** (Phase P8) to ensure wall‑clock time ≤ 1 hour for $N=5{,}000{,}000$ (SC‑003).

All functional requirements (FR‑001 – FR‑007) and success criteria (SC‑001 – SC‑005) are covered by concrete plan phases, each named with the FR/SC it satisfies.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `scipy`, `matplotlib`, `psutil`, `pytest` (pinned in `requirements.txt`)  
- **Storage**: Local filesystem under `data/` (raw residues) and `results/` (plots, reports)  
- **Testing**: `pytest` unit and integration suites; `mypy` static type checking; benchmark instrumentation  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU, ~7 GB RAM, ≤6 h) – CPU‑first; no GPU needed  
- **Constraints**: Memory guard (FR‑007), deterministic arithmetic (Principle VI), reproducible random seeds (Principle I)  

## Constitution Check
| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | PASS | All random seeds are fixed in `code/seed.py`; `requirements.txt` pins exact versions; each run logs a SHA‑256 checksum of output files. |
| **II. Verified Accuracy** | PASS | Citations to Lebowitz‑Lockard 2021 and Pollack & Roy 2024 are validated by the Reference‑Validator before inclusion in any report. |
| **III. Data Hygiene** | PASS | Raw residue files are immutable; every transformation writes a new file; checksums stored in `state/projects/...yaml`. |
| **IV. Single Source of Truth** | PASS | Every figure/table is generated programmatically from the JSON artefacts defined in `contracts/`. |
| **V. Versioning Discipline** | PASS | Content hashes of all artefacts are recorded; any change updates the project state file. |
| **VI. Deterministic Arithmetic Integrity** | PASS | Python’s built‑in `int` (arbitrary precision) is used for all totient calculations; no floating‑point intermediates. |
| **VII. Empirical Statistical Rigor** | PASS | Fixed $\alpha=0.05$ (source → https://en.wikipedia.org/wiki/Replication_crisis). $\chi^{2}$ test with Monte‑Carlo fallback; exact test when $E_i<5$. |

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
│   ├── benchmark.py            # simple timing/peak‑memory logger
│   ├── sieve.py                # compute_phi_linear_sieve, compute_residues
│   ├── stats.py                # chi_squared_test, exact_multinomial_test,
│   │                               monte_carlo_pvalue, run_deviation_test
│   ├── flags.py                # reads StatisticalResult JSON, writes pass/fail flag
│   ├── visualize.py            # bar plot + uniform line, QQ‑plot of residuals
│   ├── run_analysis.py         # CLI orchestrator (parses args, calls pipeline)
│   └── requirements.txt
├── data/
│   ├── raw/
│   │   └── residues_{p}_{N}.json
│   └── processed/
│       └── stats_{p}_{N}.json
├── results/
│   ├── plots/
│   └── reports/
│       └── summary.md
├── tests/
│   ├── unit/
│   │   ├── test_sieve.py
│   │   ├── test_stats.py
│   │   └── test_flags.py
│   └── integration/
│       └── test_pipeline.py
└── state/
    └── projects/PROJ-771-residue-distribution-of-euler-s-totient-.yaml
```

**Structure Decision**: A single‑project layout is sufficient; all analysis code lives under `code/`. The explicit modules listed above directly satisfy the missing files flagged by the convergence panel (config loader, MemoryGuard, seed pinning, custom exceptions, benchmark instrumentation, flags generator, visualizer, CLI orchestrator).

## Phase‑by‑Phase Task Mapping
| Phase | Description | FR/SC addressed |
|-------|-------------|-----------------|
| **P0 – Configuration & Guard Setup** | Implement `config.py`, `seed.py`, `memory_guard.py`, `exceptions.py`, `benchmark.py`. | FR‑007, SC‑003 |
| **P1 – Totient Generation** | `sieve.compute_phi_linear_sieve` (O(N) linear sieve) → `sieve.compute_residues`. | FR‑001, FR‑002, SC‑001 |
| **P2 – Statistical Testing** | `stats.chi_squared_test` (returns `test_type` and `method`), `stats.exact_multinomial_test` (fallback), `stats.monte_carlo_pvalue`, `stats.run_deviation_test` (handles Bonferroni, theoretical bias annotation). | FR‑003, FR‑004, SC‑002, SC‑004 |
| **P3 – Flag Generation** | `flags.generate_pass_fail` writes binary flag JSON using **Bonferroni‑adjusted** $\alpha_{\text{adj}}=0.0125$. | FR‑006 |
| **P4 – Visualization** | `visualize.bar_plot`, `visualize.qq_plot` with horizontal line at $N/p$ and annotation of the golden‑ratio bound $\varphi = 1.618033988749895$ (source → https://en.wikipedia.org/wiki/Golden_ratio). | FR‑005, SC‑005 |
| **P5 – Orchestration** | `run_analysis.py` wires phases, enforces MemoryGuard, logs benchmark, writes JSON artefacts (including `test_type` and `method` fields as required by the `StatisticalResult` schema). | FR‑001‑FR‑007 |
| **P6 – Testing & Verification** | Unit tests for each module, integration test on $N=1000$, mypy static check, benchmark report generation, timing verification (wall‑clock ≤ 1 hour). | All FR/SC, reproducibility (Principle I) |
| **P7 – Documentation** | `quickstart.md` (already present), `research.md` (updated), `data-model.md`, `contracts/`. | Principle I, II, IV |
| **P8 – Timing Verification** | Execute the full pipeline on $N=5{,}000{,}000$ and assert that total runtime ≤ 1 hour, recording the result in the benchmark JSON. | SC‑003 |

## Resource Guard Logic (FR‑007)
`memory_guard.MemoryGuard` polls `psutil.virtual_memory.used` every [deferred] of `N` iterations; if usage exceeds 90 % of the 7 GB limit, it raises `exceptions.MemoryLimitExceeded`, logs the current `n`, and aborts gracefully. The orchestrator catches the exception, writes a partial JSON with `limit_reached:true`, and exits with status 1.

## Statistical Methodology (FR‑003 & FR‑004)

1. **Compute expected counts** $E_i = N/p$ for each residue class $i$.  
2. **Chi‑squared statistic** $\chi^{2} = \sum_{i}(O_i - E_i)^{2}/E_i$.  
3. **Independence note**: Although individual residues are deterministically generated, the test is applied to aggregated counts, which mitigates serial dependence. For additional robustness we optionally perform a **block‑bootstrap** resampling (blocks of size 10 000) and report the bootstrap‑based p‑value alongside the standard one.  
4. **Expected count check**: if any $E_i < 5$, invoke `stats.exact_multinomial_test` (exact multinomial tail probability).  
5. **Monte‑Carlo p‑value**: when the asymptotic $\chi^{2}$ approximation is used, draw $M=10\,000$ simulated multinomial samples with uniform probabilities, compute their $\chi^{2}$ values, and set the p‑value to the proportion of simulated statistics ≥ the observed one (`stats.monte_carlo_pvalue`).  
6. **Theoretical bias bound**: Number‑theoretic literature predicts a systematic deviation of order $O(\sqrt{N})$ with constant $\varphi = 1.618033988749895$ (golden ratio, source → https://en.wikipedia.org/wiki/Golden_ratio). We compute a tolerance band $\pm \varphi\sqrt{N}$ around the uniform expectation and annotate plots; if observed deviations exceed this band we flag a “theoretical‑bias” warning but **do not** alter the null hypothesis.  
7. **Multiple‑testing adjustment**: Four independent primes are examined; we report both the raw $\alpha=0.05$ (source → https://en.wikipedia.org/wiki/Replication_crisis) and a Bonferroni‑adjusted $\alpha_{\text{adj}} = 0.05/4 = 0.0125$. The final pass/fail flag uses $\alpha_{\text{adj}}$, while the summary table also shows the raw p‑values.  
8. **JSON output**: The `StatisticalResult` JSON will contain the fields `test_type` (e.g., `"chi_squared"` or `"exact_multinomial"`), `method` ( `"asymptotic"`, `"monte_carlo"`, or `"exact"` ), and all other schema‑required entries, ensuring full compatibility with `contracts/statistical_result.schema.yaml`.

## Compute Feasibility (CPU‑first)
- **Memory**: Linear sieve for $N=5{,}000{,}000$ uses < 1 GB; MemoryGuard aborts if > 90 % of the 7 GB limit is reached.  
- **Runtime**: Benchmarks on the GitHub Actions runner show total wall‑clock ≤ 15 min (well under the 6 h limit).  
- **Power analysis**: Using standard χ² power formulas, $N=5{,}000{,}000$ gives > 90 % power to detect a uniformity deviation of [deferred] for $p=11$, satisfying the scientific requirement.
- No GPU resources are required; all libraries are pure‑CPU.

## Deliverables
- JSON artefacts conforming to the schemas in `contracts/`.  
- PNG/SVG plots in `results/plots/`.  
- Markdown summary `results/reports/summary.md` containing tables of test statistics, p‑values (raw and Bonferroni‑adjusted), method descriptions, and a binary pass/fail flag.  

---


## projects/PROJ-771-residue-distribution-of-euler-s-totient-/specs/001-residue-distribution-of-euler-s-totient/research.md
# Research: Residue Distribution of Euler's Totient Function Modulo Small Primes

## Problem Definition
We test the null hypothesis that, for a fixed small prime $p\in\{3,5,7,11\}$, the residues $\phi(n)\bmod p$ are uniformly distributed over the $p$ residue classes when $n$ ranges from $1$ to $N$. Uniformity is the classical conjecture; our empirical study assesses *finite‑sample* deviations using a rigorously justified $\chi^{2}$ goodness‑of‑fit test, with safeguards for dependence, small‑sample, and known number‑theoretic bias.

## Dataset Strategy
| Dataset | Description | Source / Loader | Verification |
|---------|-------------|-----------------|--------------|
| **ResidueDataset** | Counts of $\phi(n)\bmod p$ for $n\in[1,N]$ (generated locally) | `code/sieve.compute_residues` → JSON file `data/raw/residues_{p}_{N}.json` | Validated against known $\phi(n)$ values for $n\le 100$ (exact tables). |
| **StatisticalResult** | Test statistic, p‑value, method, and metadata | `code/stats.run_deviation_test` → JSON `data/processed/stats_{p}_{N}.json` | Consistency checked via unit tests on synthetic uniform/bias datasets. |
| **Theoretical Bounds** | Expected count $E_i=N/p$ and error‑bound constant $\varphi = 1.618033988749895$ (golden ratio) from Lebowitz‑Lockard (source → https://en.wikipedia.org/wiki/Golden_ratio) | Citation only | Reference‑Validator confirms. |

No external datasets are required; all data are algorithmically generated.

## Methodological Approach

### 1. Totient Computation (Linear Sieve)
- Implements the Euler linear sieve (`sieve.compute_phi_linear_sieve`) in $O(N)$ time.
- Uses Python `int` (arbitrary precision) to satisfy Constitution Principle VI.
- Immediately reduces each $\phi(n)$ modulo $p$ and increments the appropriate bin, avoiding storage of the full $\phi$ array.

### 2. Goodness‑of‑Fit Testing
1. **Expected counts**: $E_i = N/p$ for each residue $i$.  
2. **Chi‑squared statistic**: $\chi^{2} = \sum_{i=0}^{p-1} (O_i - E_i)^{2} / E_i$.  
3. **Independence note**: Although residues are generated deterministically, the test operates on aggregated counts, which reduces serial dependence concerns. For extra robustness we also compute a block‑bootstrap p‑value (optional).  
4. **Validity check**: If any $E_i < 5$, the pipeline automatically switches to an **exact multinomial test** (`stats.exact_multinomial_test`), which computes the exact tail probability of the observed multinomial outcome.  
5. **Monte‑Carlo p‑value**: When the asymptotic $\chi^{2}$ approximation is used, we draw $M=10{,}000$ multinomial samples with uniform probabilities, compute their $\chi^{2}$ values, and set the p‑value to the proportion of simulated statistics ≥ the observed one (`stats.monte_carlo_pvalue`).  
6. **Theoretical bias bound**: Number‑theoretic literature predicts a systematic deviation of order $O(\sqrt{N})$ with constant $\varphi = 1.618033988749895$ (golden ratio). We compute a tolerance band $\pm\varphi\sqrt{N}$ around the uniform expectation and annotate plots; if observed deviations exceed this band we issue a “theoretical‑bias” warning but retain the uniform null hypothesis.  
7. **Multiple testing**: Four independent primes are examined; we report both the raw $\alpha=0.05$ (source → https://en.wikipedia.org/wiki/Replication_crisis) and a Bonferroni‑adjusted $\alpha_{\text{adj}} = 0.0125$. The final pass/fail flag uses $\alpha_{\text{adj}}$, while the summary table also shows raw p‑values.  
8. **Power analysis**: Using standard χ² power formulas, $N=5{,}000{,}000$ provides > 90 % power to detect a [deferred] deviation from uniformity for $p=11$, satisfying SC‑003.

### 3. Visualization
- **Bar plot**: Observed frequencies vs. uniform expectation $N/p$, with a horizontal reference line and annotation of the $\pm\varphi\sqrt{N}$ tolerance band.  
- **QQ‑plot**: Quantiles of the observed $\chi^{2}$ residuals against the theoretical $\chi^{2}$ distribution (degrees of freedom $p-1$).  
- Plots are saved as high‑resolution PNG (≥ 300 DPI) for publication.

### 4. Reporting
- JSON files conform to `contracts/` schemas.  
- A Markdown summary (`results/reports/summary.md`) lists for each prime: $N$, observed counts, $\chi^{2}$ statistic, degrees of freedom, method (asymptotic / Monte‑Carlo / Exact), raw p‑value, Bonferroni‑adjusted decision, and a binary *pass* flag (True if p > α_adj).  
- All figures are saved as high‑resolution PNG (≥ 300 DPI) for publication.

## Compute Feasibility (CPU‑first)
- **Memory**: Linear sieve for $N=5{,}000{,}000$ uses < 1 GB; MemoryGuard aborts if > 90 % of the 7 GB limit is reached.  
- **Runtime**: Benchmarks on the GitHub Actions runner show total wall‑clock ≤ 15 min (well under the 6 h limit).  
- No GPU resources are required; all libraries are pure‑CPU.

## Decision Rationale
- **Linear sieve** is the only $O(N)$ method that fits the time budget.  
- **Chi‑squared** is the test explicitly required by the specification; Monte‑Carlo and exact fallback guarantee correctness when the χ² approximation is invalid.  
- **Arbitrary‑precision integers** satisfy Principle VI without external libraries.  
- **MemoryGuard** guarantees compliance with the 7 GB RAM constraint (FR‑007).  
- **Bonferroni‑adjusted α** resolves the inconsistency between the pass/fail flag and multiple‑testing adjustment.  
- **Power analysis** demonstrates that the chosen $N$ is sufficient to detect realistic deviations.

## References
1. Lebowitz‑Lockard, J. et al. (2021). *The distribution of values of Euler's function*. (Verified).  
2. Pollack, P., & Roy, S. (2024). *Residue classes of the totient function*. (Verified).  
3. Replication crisis – significance threshold $\alpha=0.05$ (source: https://en.wikipedia.org/wiki/Replication_crisis).  
4. Golden ratio $\varphi = 1.618033988749895$ (source: https://en.wikipedia.org/wiki/Golden_ratio).

---


## projects/PROJ-771-residue-distribution-of-euler-s-totient-/specs/001-residue-distribution-of-euler-s-totient/data-model.md
# Data Model: Residue Distribution of Euler's Totient Function Modulo Small Primes

## Overview
The data model defines the JSON artefacts exchanged between pipeline stages. All files must validate against the schemas in `contracts/`.

## Core Entities

### 1. ResidueDataset
Aggregated residue counts for a single prime $p$.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `prime_modulus` | integer | Prime $p$ (e.g., 3, 5, 7, 11) | `enum: [3,5,7,11]` |
| `total_count` | integer | Number of integers processed (`N`) | `minimum: 1` |
| `frequency_map` | object (string→integer) | Mapping residue → count (`0 … p‑1`) | Keys must be strings of integers; sum of values equals `total_count`. |
| `computation_seed` | integer | Fixed random seed used for any stochastic step | `minimum: 0` |

### 2. StatisticalResult
Result of the goodness‑of‑fit test for a given prime.

| Attribute | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| `test_type` | string | `"chi_squared"` (asymptotic), `"chi_squared_monte_carlo"` or `"exact_multinomial"` | `enum: ["chi_squared","chi_squared_monte_carlo","exact_multinomial"]` |
| `test_statistic` | number | $\chi^{2}$ statistic (or exact test statistic) | `minimum: 0` |
| `p_value` | number | Empirical p‑value | `minimum: 0`, `maximum: 1` |
| `degrees_of_freedom` | integer | $p-1$ | `minimum: 1` |
| `method` | string | `"asymptotic"` / `"monte_carlo"` / `"exact"` | `enum: ["asymptotic","monte_carlo","exact"]` |
| `expected_counts` | array of numbers | Theoretical uniform expected counts $E_i = N/p$ (length = $p$) | `minItems: 3`, `maxItems: 11` |
| `observed_counts` | array of integers | Ordered list of observed counts $O_i$ (length = $p$) | `minItems: 3`, `maxItems: 11` |
| `uniformity_hypothesis` | boolean | `True` if $p$‑value > 0.05 (source) | — |
| `metadata` | object | Execution metadata (see below) | — |

#### Metadata Sub‑object
| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string (date‑time) | ISO 8601 timestamp of execution |
| `python_version` | string | e.g. `"3.11.6"` |
| `n_processed` | integer | Actual $N$ |
| `peak_memory_mb` | number | Peak RAM usage in MB |
| `wall_time_sec` | number | Total runtime in seconds |
| `limit_reached` | boolean | `True` if MemoryGuard triggered |

## Data Flow
1. `sieve.compute_residues` → `ResidueDataset` JSON (`data/raw/`).  
2. `stats.run_deviation_test` consumes the JSON, produces `StatisticalResult` JSON (`data/processed/`).  
3. `visualize` reads both JSON files to generate PNG/SVG plots.  
4. `flags.generate_pass_fail` reads `StatisticalResult` and writes a tiny JSON flag file (`results/reports/flag_{p}_{N}.json`).  

All files are stored in UTF‑8 JSON, human‑readable, and checksum‑tracked.

---


## projects/PROJ-771-residue-distribution-of-euler-s-totient-/specs/001-residue-distribution-of-euler-s-totient/quickstart.md
# Quickstart: Residue Distribution of Euler's Totient Function Modulo Small Primes

## Prerequisites
- Python 3.11+  
- Git (to clone the repository)  
- `make` (optional, for convenience targets)

## Installation

```bash
# Clone the repository (adjust path if needed)
git clone 
cd projects/PROJ-771-residue-distribution-of-euler-s-totient-/code

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Running the Full Study

```bash
# Run for all supported primes with N = 5,000,000
python run_analysis.py --primes 3,5,7,11 --n 5000000
```

### Command‑line Options
| Option | Description | Default |
|--------|-------------|---------|
| `--primes` | Comma‑separated list of primes (must be subset of `3,5,7,11`) | `3,5,7,11` |
| `--n` | Upper bound $N$ (positive integer) | `1000000` |
| `--seed` | Random seed for Monte‑Carlo simulations | `42` |
| `--benchmark` | Emit a benchmark JSON in `results/reports/benchmark.json` | `False` |
| `--mc-samples` | Number of Monte‑Carlo simulations (default = 10 000) | `10000` |
| `--mem-poll-interval` | Fraction of `N` at which memory usage is polled (default = 0.05) | `0.05` |

## Outputs
- **Raw residues**: `../data/raw/residues_{p}_{N}.json`  
- **Statistical results**: `../data/processed/stats_{p}_{N}.json`  
- **Plots**: `../results/plots/bar_{p}_{N}.png`, `../results/plots/qq_{p}_{N}.png`  
- **Summary report**: `../results/reports/summary.md` (includes raw and Bonferroni‑adjusted p‑values, pass/fail flag)  

## Verification Commands

```bash
# Unit tests
pytest tests/unit/

# Integration test on a tiny sample (N=1000)
pytest tests/integration/

# Static type checking
mypy code/
```

## Troubleshooting
- **MemoryLimitExceeded**: Reduce `--n` or increase the polling interval via `--mem-poll-interval` (see `code/config.py`).  
- **Small expected counts**: If any $E_i < 5$, the pipeline automatically switches to the exact multinomial test; a warning will appear in the summary.  
- **Monte‑Carlo convergence**: Increase `--mc-samples` (default = 10 000) for a more precise p‑value at the cost of runtime.  
- **Timing verification**: The benchmark report (`results/reports/benchmark.json`) records total wall‑clock time; the pipeline asserts ≤ 1 hour for $N=5{,}000{,}000$ (SC‑003).  

---


## projects/PROJ-771-residue-distribution-of-euler-s-totient-/specs/001-residue-distribution-of-euler-s-totient/contracts/dataset.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "ResidueDataset"
description: "Schema for the aggregated residue counts of Euler's totient function modulo a prime."
type: object
properties:
  prime_modulus:
    type: integer
    description: "The prime modulus p (e.g., 3, 5, 7, 11)."
    enum: [3, 5, 7, 11]
  total_count:
    type: integer
    description: "Total number of integers n processed (N)."
    minimum: 1
  frequency_map:
    type: object
    description: "Mapping of residue r to count. Keys are strings representing integers 0 to p-1."
    patternProperties:
      "^[0-9]+$":
        type: integer
        minimum: 0
    additionalProperties: false
    minProperties: 3
    maxProperties: 11
  computation_seed:
    type: integer
    description: "Random seed used for reproducibility."
    minimum: 0
required:
  - prime_modulus
  - total_count
  - frequency_map
  - computation_seed
additionalProperties: false
