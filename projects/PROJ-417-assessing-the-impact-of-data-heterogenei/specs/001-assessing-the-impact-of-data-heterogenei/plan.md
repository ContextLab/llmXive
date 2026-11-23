# Implementation Plan: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

**Branch**: `001-assess-heterogeneity-impact` | **Date**: 2026-10-25 | **Spec**: `specs/001-assessing-the-impact-of-data-heterogeneity/spec.md`

## Summary
The project will (1) generate a deterministic synthetic base meta‑analysis template (no external Cochrane download required), (2) create **900 replicates per τ² level** (0, 0.1, 0.5, 1.0, 2.0) and a sensitivity sweep (0.05, 0.1, 0.5), (3) apply Fixed‑Effects, DerSimonian‑Laird, and REML estimators with robust convergence handling, (4) compute bias and coverage for every replicate, (5) perform exact binomial tests **with Bonferroni‑adjusted α = 0.05/5 ≈ 0.01** (across the five τ² levels only) and normality‑driven ANOVA/Kruskal‑Wallis tests, (6) visualise coverage and mean bias versus τ², and (7) produce a fully reproducible markdown report. All steps run on the GitHub Actions free‑tier CPU runner, streaming data in batches to respect the 7 GB RAM / ≤6 h limit.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `matplotlib`, `pyyaml`, `jsonschema`, `pytest` (CPU‑only).  
- **Storage**: Local filesystem under `data/` (CSV, JSON‑lines, PNG).  
- **Testing**: `pytest` (unit & integration).  
- **Target Platform**: Linux (GitHub Actions Ubuntu runner).  
- **Performance Goals**: Full primary + sensitivity sweeps ≤ 3 h, RAM ≤ 5 GB.  
- **Constraints**: No GPU; deterministic random seeds; reproducible synthetic base generation; all output files must appear under the exact paths required by the specification.

## Constitution Check
| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Reproducibility | PASS | Fixed seeds, pinned `requirements.txt`, deterministic base generation; all scripts accept CLI arguments. |
| II. Verified Accuracy | PASS | No external citations beyond the verified URLs list; all references are internal or to the synthetic base. |
| III. Data Hygiene | PASS | Raw synthetic base is immutable; all transformations write new files; SHA‑256 checksums recorded in `state/project_state.yaml`. |
| IV. Single Source of Truth | PASS | Every figure/table traces to a single CSV/JSONL file in `data/results/`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/project_state.yaml`; any change updates the hash. |
| VI. Simulation Fidelity | PASS | τ² levels {0, 0.1, 0.5, 1.0, 2.0} (primary) + {0.05, 0.1, 0.5} (sensitivity); 900 replicates per level; fixed study‑size vector across replicates. |
| VII. Estimator Standardization | PASS | Fixed‑Effects, DerSimonian‑Laird, REML implemented per standard formulas; unit tests validate against textbook examples. |

## Project Structure
```text
specs/001-assessing-the-impact-of-data-heterogeneity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── simulated_dataset.schema.yaml
│   ├── estimation_result.schema.yaml
│   ├── aggregated_metric.schema.yaml
│   └── coverage_test.schema.yaml
└── tasks.md          # generated later by /speckit-tasks
```

```text
code/
├── __init__.py
├── requirements.txt
├── simulation/
│   ├── __init__.py
│   ├── generator.py          # FR‑001, SC‑004
│   └── estimators.py         # FR‑002, FR‑006
├── analysis/
│   ├── __init__.py
│   ├── metrics.py            # FR‑003
│   └── stats.py              # FR‑004, FR‑007, FR‑008
├── visualization/
│   ├── __init__.py
│   └── plots.py              # FR‑005
├── reporting/
│   ├── __init__.py
│   └── report_gen.py         # SC‑005
├── scripts/
│   └── generate_base.py      # deterministic base creation
└── main.py                   # orchestrates all phases, accepts CLI args
```

```text
data/
├── raw/                      # empty (no external download)
├── processed/
│   └── base_template.csv     # deterministic synthetic base
└── results/
    ├── simulation_raw.jsonl   # JSON‑lines of SimulatedDataset & EstimationResult
    ├── aggregated_metrics.csv
    ├── coverage_vs_tau2.png
    ├── mean_bias_vs_tau2.png
    ├── reml_failures.json
    ├── coverage_tests.json    # list of CoverageTest objects
    └── report.md
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| **Synthetic base instead of Cochrane download** | No verified Cochrane URL exists; generating a realistic synthetic base respects the constitution. | Attempting to fetch a non‑existent OpenML dataset (which caused the previous failure). |
| **Bonferroni across τ² levels only** | Aligns with FR‑007 and the constitution (α = 0.05/5). | Using α ≈ 0.0033 would violate the spec. |
| **REML failure handling** | Guarantees unbiased coverage estimates; failures are logged and counted as non‑coverage. | Substituting a tiny variance would artificially boost REML coverage. |
| **Shapiro‑Wilk conditional test** | Satisfies FR‑008 and avoids a blanket non‑parametric approach. | Using Kruskal‑Wallis everywhere would violate FR‑008. |
| **Fixed k/N across replicates** | Removes confounding between heterogeneity and study‑size variability. | Varying k/N would obscure the heterogeneity effect. |
| **Batch streaming** | Keeps RAM ≤ 5 GB on the CI runner; avoids the “file written to wrong path” issue that triggered T002. | Loading all replicates in memory would exceed RAM. |

## Phased Execution Plan

| Phase | Goal | Primary FR / SC addressed | Key Outputs |
|-------|------|---------------------------|-------------|
| **Phase 0 – Research & Design** | Confirm data model, statistical plan, and feasibility. | VI, VII, all FR/SC | `research.md`, `data-model.md`, `contracts/*.schema.yaml` |
| **Phase 1 – Implementation Setup** | Build generator, estimators, metrics, stats, visualisation, reporting. | FR‑001 – FR‑008, SC‑001 – SC‑005 | `code/` modules, unit tests |
| **Phase 2 – Primary Sweep Execution** | Run 5 × 900 replicates, streaming in batches of 100, write **`data/results/simulation_raw.jsonl`**. | FR‑001, FR‑002, FR‑003, FR‑006, SC‑003 | `simulation_raw.jsonl` |
| **Phase 3 – Sensitivity Sweep** | Run 3 × 900 replicates for τ² ∈ {0.05, 0.1, 0.5}. | SC‑004 | Additional records appended to `simulation_raw.jsonl` |
| **Phase 4 – Metric Aggregation & Testing** | Compute bias, coverage; perform Shapiro‑Wilk → ANOVA/KW; exact binomial tests with **Bonferroni‑adjusted α = 0.01**; write `aggregated_metrics.csv`, `coverage_tests.json`, `reml_failures.json`. | FR‑004, FR‑007, FR‑008, SC‑001, SC‑002 | `aggregated_metrics.csv`, `coverage_tests.json`, `reml_failures.json` |
| **Phase 5 – Visualisation** | Produce PNGs of coverage vs τ² and mean bias vs τ². | FR‑005, SC‑001, SC‑002 | `coverage_vs_tau2.png`, `mean_bias_vs_tau2.png` |
| **Phase 6 – Reporting** | Compile `report.md` with “associational” label, REML‑failure summary, and embed figures/tables. | SC‑005, SC‑001‑SC‑005 | `report.md` |
| **Phase 7 – Verification & Handoff** | Run integration test, validate contracts, record checksums, update `state/`. | All verification tasks | Integration tests pass; `state/project_state.yaml` updated |

### Mapping of Functional Requirements to Phases
| FR | Phase(s) |
|----|----------|
| FR‑001 | 2, 3 |
| FR‑002 | 1 (implementation) → used in 2‑4 |
| FR‑003 | 1 → used in 2‑4 |
| FR‑004 | 4 |
| FR‑005 | 5 |
| FR‑006 | 1 (implementation) → exercised in 2‑4 |
| FR‑007 | 4 |
| FR‑008 | 4 |

### Mapping of Success Criteria to Phases
| SC | Phase |
|----|-------|
| SC‑001 | 4 |
| SC‑002 | 4 |
| SC‑003 | 2‑3 (runtime monitoring) |
| SC‑004 | 3 |
| SC‑005 | 6 |

## Implementation Details to Satisfy Verification Failures
1. **CLI Argument Support** – `code/main.py` now accepts `--tau-squared` (comma‑separated list), `--replicates`, `--batch-size`, `--mode` (dry‑run/full), and `--seed`. This resolves prior argument‑mismatch failures.
2. **Correct Output Paths** – All scripts write to `data/results/` (e.g., `simulation_raw.jsonl`, `aggregated_metrics.csv`, `coverage_tests.json`). This fixes earlier path inconsistencies.
3. **Exact Replicate Count & τ² Values** – Generator loops over the prescribed τ² list and creates **900** replicates per level (primary) and **900** per level (sensitivity). Each record includes the correct `tau_squared` field.
4. **Aggregated Metrics Schema Compliance** – `analysis/stats.py` now produces a CSV with all required columns (`tau_squared`, `estimator_type`, `sweep_type`, `mean_bias`, `coverage_rate`, `coverage_deviation`, `coverage_ci_lower`, `coverage_ci_upper`, `binomial_p_value`, `bias_test_p_value`, `report_framing`). Exactly **15** rows (3 estimators × 5 τ² levels) are written.
5. **Coverage Tests JSON** – New file `coverage_tests.json` stores the raw binomial test results per estimator/τ², matching the newly added `contracts/coverage_test.schema.yaml`.
6. **Batch Streaming** – Generator processes replicates in configurable batches (default 100) to keep memory usage ≤ 5 GB.
7. **Unit & Integration Tests** – Updated tests now check file existence, schema compliance, and correct replicate counts. They are executed in the CI pipeline to guarantee deterministic verification.
8. **Power Statement Updated** – Power calculations now reference the correct α = 0.01, acknowledging the reduced power relative to the earlier (incorrect) α ≈ 0.0033.

---

