# Implementation Plan: llmXive follow-up: extending "Foundation Protocol: A Coordination Layer for Agentic Society"

**Branch**: `001-policy-compression-tradeoff` | **Date**: 2026-10-22 | **Spec**: `specs/001-policy-compression-tradeoff/spec.md`  
**Input**: Feature specification from `/specs/001-policy-compression-tradeoff/spec.md`

## Summary
The project will (1) deterministically generate a substantial set of synthetic multi‑agent workflows with varied delegation depth and policy complexity, (2) execute each workflow under a full‑context baseline and under multiple compressed‑context variants (BFS/DFS depth limits), (3) record token usage via `tiktoken` (`cl100k_base`) and policy‑violation counts against an independent Oracle Policy Engine, and (4) perform a **step‑level binomial GEE** regression with bootstrap‑derived confidence intervals to locate the “safe operating zone” where error ≤ 1 %. All steps are CPU‑only, reproducible, and validated against schema contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `networkx`, `tiktoken` (model `cl100k_base`), `pandas`, `scikit-learn`, `statsmodels`, `pm4py`, `pytest`  
- **Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/results/`)  
- **Testing**: `pytest` + schema validation (`jsonschema`)  
- **Target Platform**: GitHub Actions `ubuntu-latest` (2 vCPU, ~7 GB RAM)  
- **Constraints**: CPU‑only, deterministic seeds, no external data download  

## Constitution Check

| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Reproducibility | PASS | Fixed seeds (`SEED=42`), `requirements.txt`, checksummed artifacts. |
| II. Verified Accuracy | PASS | All statistical methods cite standard references; no unverified citations. |
| III. Data Hygiene | PASS | Synthetic data generated on‑the‑fly, checksums stored in `state/…yaml`. |
| IV. Single Source of Truth | PASS | `data/results/tradeoff_curve.csv` is the sole source for figures/tables. |
| V. Versioning Discipline | PASS | Post‑run script updates artifact hashes in project state file. |
| VI. Deterministic State‑Modeling | PASS | Oracle Policy Engine (`models/policy.py`) is independent of compression logic. |
| VII. Resource‑Constrained Execution Fidelity | PASS | No GPU‑only libraries; all code runs on CPU within memory limits. |

## Project Structure
```text
specs/001-policy-compression-tradeoff/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── workflow.schema.yaml
│   ├── execution_log.schema.yaml
│   ├── tradeoff_curve.schema.yaml
│   └── analysis_results.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
src/
├── models/
│   ├── workflow.py          # dataclasses for Workflow, PolicyNode
│   ├── policy.py            # Oracle Policy Engine (independent)
│   └── compression.py       # BFS/DFS depth‑limited subgraph extraction
├── services/
│   ├── generator.py         # deterministic workflow generator (FR‑001)
│   ├── executor.py          # Full & Compressed execution engines (FR‑002‑FR‑004)
│   └── analyzer.py          # GEE regression, bootstrap CI, monotonicity check (FR‑005‑FR‑006)
├── cli/
│   └── run_simulation.py    # orchestrates pipeline (FR‑007)
└── lib/
    └── utils.py             # tokenizer wrapper, checksum utilities (FR‑009)
```

## Mapping of Functional & Success Criteria to Plan Phases
| Phase | Tasks | FRs addressed | SCs addressed |
|-------|-------|---------------|----------------|
| **0 – Setup** | Install deps, pin seeds, generate checksums | FR‑007, FR‑009 | SC‑005 |
| **1 – Synthetic Data Generation** | `generator.py` creates 500 workflows with uniform depth distribution (≥ 25 per depth) and varied policy complexity; flags invalid workflows | FR‑001, FR‑008 | SC‑001 |
| **2 – Full‑Context Baseline** | `executor.py` runs each valid workflow with complete policy graph; logs token count & violations | FR‑002, FR‑004 | SC‑001, SC‑002 |
| **3 – Compressed‑Context Variants** | For each depth `k ∈ {0,…,10}` (adaptive sampling densifies near expected inflection), `executor.py` extracts subgraph via BFS/DFS, tokenizes, records violations | FR‑003, FR‑004, FR‑009 | SC‑001, SC‑002 |
| **4 – Edge‑Case Handling** | Detect single‑node graphs & depth 0; record `context_reduction_pct="[deferred]"`; monitor proportion of `is_valid=False` workflows and generate `invalid_exclusion_report.json`. **These rows are retained for descriptive statistics and a separate sensitivity analysis but are excluded from the regression model because they lack a numeric reduction value.** | FR‑001, FR‑008 | SC‑001 |
| **5 – Statistical Analysis** | **T‑Prepare‑Step‑Level‑Data** expands execution logs into a flat table of per‑step binary outcomes (`step_id`, `outcome` = 0/1). `analyzer.py` fits a **step‑level binomial GEE** model (logit link, exchangeable correlation, clustered by `workflow_id`) on these raw outcomes, with covariates `context_reduction_pct`, `policy_complexity`, `delegation_depth`. <br> **Monotonicity Diagnostic**: after fitting, we compute the predicted error curve. **If the curve is monotonic**, we proceed to threshold extraction. **If non‑monotonicity is observed**, we **report** it as a substantive finding (including an optional isotonic regression plot for illustration only) and do **not** refit the model to enforce monotonicity. | FR‑005, FR‑006 | SC‑003, SC‑004 |
| **5a – Power‑Analysis** | Conduct a **simulation‑based power analysis**: assume a logistic coefficient of 0.10 per [deferred] context‑reduction (i.e., a 0.10 increase in log‑odds corresponding to a [deferred] reduction) and a target absolute error increase of ≥ 1 % at that reduction. Simulate a sufficient number of datasets matching the design., embed the above effect size, fit the GEE each time, and record the proportion that detects a statistically significant error increase at the 1 % bound (α = 0.05, Bonferroni‑adjusted where applicable). Report the estimated power in `run_metrics.json`. | — | — |
| **5b – Invalid‑Workflow Reporting** | `T‑Invalid‑Exclusion‑Report` generates `data/results/invalid_exclusion_report.json` containing `invalid_workflow_count`, `excluded_count`, and `status`; values are stored in `run_metrics.json` | FR‑008 | SC‑001 |
| **5c – Analysis‑Results Schema Validation** | `T‑Analyze‑Results‑Schema` validates the intermediate `analysis_results.json` against `contracts/analysis_results.schema.yaml` | — | — |
| **6 – Reporting & Artifacts** | Write `tradeoff_curve.csv`, `threshold_report.json`, `run_metrics.json`; generate `tradeoff_curve.png`; compute SHA‑256 hashes stored in `state/…yaml` | FR‑006, FR‑007 | SC‑005 |
| **7 – Validation & Tests** | Unit tests for generator distribution, compression token reduction, Oracle independence, schema compliance, end‑to‑end pipeline (`tests/integration/test_pipeline.py`) | FR‑007, FR‑008, FR‑009 | All SCs (via assertions) |
| **8 – Quickstart Documentation** | `quickstart.md` (this file) – linked to FR‑007 (reproducibility) | FR‑007 | — |
| **9 – Auxiliary Scripts** | `T‑Update‑Final‑State` – compute checksums and update project state file. <br> `T‑Verify‑Invalid‑Exclusion` – script `code/utils/verify_invalid_exclusion.py`. <br> `T‑Generate‑Reproducibility‑Report` – produce `reproducibility_report.json` with command log and checksum verification. <br> `T‑Main‑Pipeline` – implement `code/main.py` orchestrating the full workflow. <br> `T‑Abort‑On‑Threshold` – analyzer aborts pipeline if predicted error exceeds 1 % before final report. | — | — |
| **10 – Adaptive Sampling Extension** | `T‑Adapt‑Generator‑Adaptive` – extend `generator.py` with `--adaptive` flag to densify depth distribution around the anticipated inflection point. | FR‑001 | — |
| **11 – CSV Validation** | `T‑Validate‑Tradeoff‑CSV` – validate `tradeoff_curve.csv` against `contracts/tradeoff_curve.schema.yaml`. | — | — |

## Specific Implementation Tasks (to be emitted in `tasks.md`)

1. **T‑Gen‑Deterministic** – Implement `generator.py` with fixed seed, uniform depth sampling, validation of solvability.  
2. **T‑Oracle‑Independent** – Build `policy.py` as a pure deterministic state machine; no imports from compression modules.  
3. **T‑Compress‑BFSDFS** – Implement depth‑limited traversal in `compression.py`; expose both BFS and DFS options.  
4. **T‑Tokenizer‑Wrapper** – `utils.py` uses `tiktoken` with `cl100k_base`; returns token count for serialized subgraph.  
5. **T‑Exec‑Full** – `executor.py` runs full context, records logs per `execution_log.schema.yaml`.  
6. **T‑Exec‑Compressed** – Loop over adaptive depth list; handle edge cases (`k=0`, single‑node) with `"[deferred]"`.  
7. **T‑Prepare‑Step‑Level‑Data** – Expand execution logs into per‑step binary outcome rows for GEE.  
8. **T‑Analyze‑GEE** – Fit binomial GEE model using `statsmodels.genmod.generalized_estimating_equations.GEE` with exchangeable correlation; include covariates `policy_complexity` and `delegation_depth`.  
9. **T‑Analyze‑Trend** – Cochran‑Armitage trend test (`statsmodels.stats.proportion.proportional_trend_test`); Bonferroni for secondary pairwise tests.  
10. **T‑Analyze‑Bootstrap** – A **1000**‑resample bootstrap (per verified fact) to compute a 95 % CI for the 1 % error threshold.  
11. **T‑Monotonicity‑Check** – Verify predicted error curve monotonicity; if violated, **report** the finding and optionally plot an isotonic regression for illustration only.  
12. **T‑Power‑Simulation** – Perform simulation‑based power analysis assuming logistic coefficient 0.10 per 10 % reduction; 1000 simulated datasets; report estimated power.  
13. **T‑Invalid‑Exclusion‑Report** – Generate `invalid_exclusion_report.json` and record counts in `run_metrics.json`.  
14. **T‑Analyze‑Results‑Schema** – Validate `analysis_results.json` against `contracts/analysis_results.schema.yaml`.  
15. **T‑Report‑Artifacts** – Serialize CSV/JSON, compute SHA‑256, update `state/projects/...yaml`.  
16. **T‑Tests‑Unit** – Verify distribution, token reduction, Oracle independence, schema validation.  
17. **T‑Tests‑Integration** – End‑to‑end pipeline test ensuring total wall‑clock < 6 h on CI.  
18. **T‑Doc‑Quickstart** – Write `quickstart.md` (this file) and link it to FR‑007.  
19. **T‑Contract‑Schemas** – Provide the four YAML schema files under `contracts/`.  
20. **T‑Update‑Final‑State** – Compute SHA‑256 checksums for all generated artifacts and update the project state YAML.  
21. **T‑Verify‑Invalid‑Exclusion** – Implement `code/utils/verify_invalid_exclusion.py` to generate the exclusion report.  
22. **T‑Generate‑Reproducibility‑Report** – Produce `data/results/reproducibility_report.json` summarizing command logs and checksum verification.  
23. **T‑Main‑Pipeline** – Implement `code/main.py` that calls the generation, execution, analysis, and reporting steps in order, with robust error handling (exit 0 on success, non‑zero with clear message on failure).  
24. **T‑Abort‑On‑Threshold** – Analyzer aborts the pipeline if the predicted error rate exceeds 1 % before final artefacts are written.  
25. **T‑Adapt‑Generator‑Adaptive** – Extend `generator.py` with an `--adaptive` flag for depth‑densified sampling.  
26. **T‑Validate‑Tradeoff‑CSV** – Validate `tradeoff_curve.csv` against `contracts/tradeoff_curve.schema.yaml`.  
27. **T‑Generate‑Figure** – Create `figures/tradeoff_curve.png` from `tradeoff_curve.csv` for inclusion in the paper.

## Complexity Tracking
No constitution violations remain; all principles satisfied.

## Compute Feasibility
- **CPU‑First**: All libraries (`networkx`, `tiktoken`, `statsmodels`, `sklearn`) run on CPU. No GPU‑only components.  
- **Memory**: A modest number of small graphs plus logs yields a relatively small data footprint.; well under 7 GB limit.  
- **Runtime**: Estimated ≤ 2 h on 2 vCPU (generation ≈ several minutes, execution ≈ ≈ 1 h, analysis ≈ a few minutes, testing ≈ several minutes).  

## Decision / Rationale
- **Synthetic data** gives full control over depth/complexity and avoids unavailable external datasets.  
- **CPU‑only** respects the resource‑constrained constraint (Constitution VII).  
- **Oracle independence** fulfills Constitution VI, preventing circular validation.  
- **Step‑level binomial GEE** provides a statistically valid approach for binary outcomes, addressing scientific‑soundness concern.  
- **Explicit effect size** in power analysis makes the estimate interpretable.  
- **Monotonicity diagnostic** reports non‑monotonicity rather than enforcing it, preserving scientific integrity.  
- **Deferred rows** are handled transparently to avoid selection bias.  
- **Adaptive sampling** concentrates runs near the anticipated inflection while keeping total runs manageable.  
- **Robust main pipeline** (`code/main.py`) includes clear error handling to satisfy verification of T101/T111.  

## Compute Feasibility (re‑stated)
All steps run within the free‑tier GitHub Actions constraints; no GPU is required.  
