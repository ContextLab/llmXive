# Implementation Plan: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

**Branch**: `001-assess-heterogeneity-impact` | **Date**: 2026-10-18 | **Spec**: `specs/001-assessing-the-impact-of-data-heterogenei/spec.md`

## Summary
The project will (1) download an open, verified meta‑analysis dataset (OpenML ID 4210) and use it as the base template, (2) generate synthetic meta‑analysis datasets with controlled between‑study variance $\tau^2$ (FR‑001), (3) apply Fixed‑Effects, DerSimonian‑Laird, and REML estimators (FR‑002) while **excluding** REML replicates that fail to converge from coverage calculations (FR‑006), (4) compute bias and coverage for each replicate (FR‑003), (5) test coverage against the nominal level with an exact binomial test **using a Bonferroni‑adjusted $\alpha=0.01$** (FR‑004, FR‑007), (6) **use Kruskal‑Wallis for bias comparisons across all τ² levels** (FR‑008), and (7) visualise coverage and mean bias versus $\tau^2$ (FR‑005). All steps run on the GitHub Actions free‑tier CPU runner, processing replicates in batches to stay within the 7 GB RAM / 6 h limit.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `matplotlib`, `pyyaml`, `pytest` (CPU‑only).  
- **Storage**: Local file system under `data/` (CSV for aggregated metrics, JSON‑lines for raw simulation and estimation results, PNG for plots).  
- **Testing**: `pytest` for unit and integration tests.  
- **Target Platform**: Linux (GitHub Actions Ubuntu runner).  
- **Performance Goals**: Complete the full primary sweep (5 × 900 replicates) + sensitivity sweep (3 × 900 replicates) = **7 200** records ≤ 3 h, RAM ≤ 5 GB.  
- **Constraints**: No GPU, deterministic random seeds, reproducible downloads only from verified URLs (OpenML ID 4210).

## Constitution Check
| Principle | Status | Verification |
|-----------|--------|--------------|
| **I. Reproducibility** | PASS | Fixed seeds, `requirements.txt` pinned, deterministic OpenML download. |
| **II. Verified Accuracy** | PASS | All external citations (OpenML dataset, Jackson et al., 2010) verified by Reference‑Validator. |
| **III. Data Hygiene** | PASS | Raw OpenML file immutable; all transformations write new files; SHA‑256 checksums recorded in `state/`. |
| **IV. Single Source of Truth** | PASS | Every figure/table traces to a single CSV/JSON file in `data/results/`; **EstimationResult stored **only** in `simulation_raw.json`. |
| **V. Versioning Discipline** | PASS | Content hashes stored in `state/project_state.yaml`; any change updates the hash. |
| **VI. Simulation Fidelity** | PASS | $\tau^2$ levels {0, 0.1, 0.5, 1.0, 2.0} (primary) + {0.05, 0.1, 0.5} (sensitivity) with **900 replicates per level**; two‑stage SE generation mirrors real meta‑analysis. |
| **VII. Estimator Standardization** | PASS | Fixed‑Effects, DerSimonian‑Laird, REML implemented per standard formulas; unit tests validate against known examples. |

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
│   └── aggregated_metric.schema.yaml
└── tasks.md          # created later by /speckit-tasks
```

```text
code/
├── __init__.py
├── requirements.txt
├── simulation/
│   ├── __init__.py
│   ├── generator.py          # FR‑001, SC‑004
│   └── estimators.py         # FR‑002, FR‑006 (log & exclude failures)
├── analysis/
│   ├── __init__.py
│   ├── metrics.py            # FR‑003
│   └── stats.py              # FR‑004, FR‑007, FR‑008 (Kruskal‑Wallis always)
├── visualization/
│   ├── __init__.py
│   └── plots.py              # FR‑005
├── reporting/
│   ├── __init__.py
│   └── report_gen.py         # SC‑005
├── main.py                   # orchestrates phases
└── scripts/
    ├── fetch_openml.py       # downloads OpenML ID 4210
    └── generate_synthetic_base.py
tests/
├── unit/
│   ├── test_generator.py
│   ├── test_estimators.py
│   └── test_metrics.py
└── integration/
    └── test_pipeline.py      # end‑to‑end verification of all artifacts
data/
├── raw/                      # OpenML download
├── processed/                # cleaned base template
└── results/
    ├── simulation_raw.json   # JSON‑lines of SimulatedDataset + EstimationResult (≈ 7 200 lines)
    ├── aggregated_metrics.csv
    ├── coverage_vs_tau2.png
    ├── mean_bias_vs_tau2.png
    ├── reml_failures.json
    └── report.md
state/
└── project_state.yaml        # hashes & timestamps
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| **Bonferroni correction** (FR‑007) | Controls family‑wise error across 5 heterogeneity levels. | Ignoring multiplicity would inflate Type I error. |
| **REML exclusion** (FR‑006) | Guarantees unbiased coverage estimates; failures are reported separately. | Substituting a tiny variance would artificially boost REML coverage. |
| **Exact binomial test** (FR‑004) | Coverage proportions near 0 or 1 need exact inference. | Normal approximation would be inaccurate for 900 replicates per level. |
| **Kruskal‑Wallis everywhere** (FR‑008) | Pre‑specifies a robust non‑parametric test, avoiding p‑hacking. | Conditional ANOVA would compromise Type I error control. |
| **Two‑stage SE generation** (SC‑004) | Mirrors real meta‑analysis uncertainty, improving external validity. | Fixed SEs would underestimate variability. |
| **900 replicates per τ² level** (Power) | Monte‑Carlo SE ≈ 0.016; exact binomial test has ≥ 80 % power to detect a [deferred] deviation from 0.95. | 500 replicates would be under‑powered. |

## Phased Execution Plan

| Phase | Goal | Primary FR / SC addressed | Key Outputs |
|-------|------|---------------------------|-------------|
| **Phase 0 – Research & Design** | Confirm data model, statistical plan, and feasibility. | VI, VII, all FR/SC | `research.md`, `data-model.md`, `contracts/*.schema.yaml` |
| **Phase 1 – Implementation Setup** | Build generator, estimators, metrics, stats, visualisation, reporting. | FR‑001 – FR‑008, SC‑001 – SC‑005 | `code/` modules, unit tests |
| **Phase 2 – Primary Sweep Execution** | Run 5 × 900 replicates, batch‑process, write `simulation_raw.json`. | FR‑001, FR‑002, FR‑003, FR‑006, SC‑003 | `data/results/simulation_raw.json` (4 500 records) |
| **Phase 3 – Sensitivity Sweep** | Run 3 × 900 replicates for τ² ∈ {0.05, 0.1, 0.5}. | SC‑004 | Additional 2 700 records appended to `simulation_raw.json` |
| **Phase 4 – Metric Aggregation & Testing** | Compute bias, coverage; exact binomial tests (Bonferroni‑adjusted) and **Kruskal‑Wallis** for bias; exclude REML failures from coverage. | FR‑004, FR‑007, FR‑008, SC‑001, SC‑002 | `data/results/aggregated_metrics.csv`, `data/results/reml_failures.json` |
| **Phase 5 – Visualisation** | Produce PNGs of coverage vs τ² and mean bias vs τ². | FR‑005, SC‑001, SC‑002 | `coverage_vs_tau2.png`, `mean_bias_vs_tau2.png` |
| **Phase 6 – Reporting** | Compile `report.md` with associational framing, REML‑failure summary, and all figures/tables. | SC‑005, SC‑001‑SC‑005 | `data/results/report.md` |
| **Phase 7 – Verification & Handoff** | Run integration test, validate contracts, record checksums, update `state/`. | All verification tasks | `tests/integration/test_pipeline.py` passes; `state/project_state.yaml` updated |

### Mapping of Functional Requirements to Phases
- **FR‑001** – Phases 2 & 3 (generator).  
- **FR‑002** – Phase 1 (estimators) used in Phases 2‑4.  
- **FR‑003** – Phase 1 (metrics) used in Phases 2‑4.  
- **FR‑004** – Phase 4 (stats).  
- **FR‑005** – Phase 5 (plots).  
- **FR‑006** – Phase 1 (estimators) with exclusion logic exercised in Phases 2‑4.  
- **FR‑007** – Phase 4 (stats).  
- **FR‑008** – Phase 4 (stats) – Kruskal‑Wallis applied uniformly.

### Mapping of Success Criteria to Phases
- **SC‑001** – Evaluated in Phase 4.  
- **SC‑002** – Evaluated in Phase 4.  
- **SC‑003** – Monitored during Phases 2‑3 (runtime logs).  
- **SC‑004** – Sensitivity sweep in Phase 3.  
- **SC‑005** – Enforced in Phase 6 (report framing). 

---


