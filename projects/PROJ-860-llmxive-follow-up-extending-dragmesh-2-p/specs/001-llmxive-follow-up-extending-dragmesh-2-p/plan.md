# Implementation Plan: Virtual Tactile Zero-Shot Adaptation

**Branch**: `001-virtual-tactile-adaptation` | **Date**: 2026-10-13 | **Spec**: `specs/001-virtual-tactile-adaptation/spec.md`  
**Input**: Feature specification from `/specs/001-virtual-tactile-adaptation/spec.md`

## Summary
The goal is to enable zero‑shot adaptation of a dexterous hand manipulation policy to unseen friction conditions by (1) estimating a **Dynamic Resistance Proxy** (`k_norm`) from torque and velocity derivatives, (2) feeding this proxy to an **AdaptiveRewardScheduler** that scales detachment and contact rewards based on percentile position, and (3) validating the approach with a CPU‑only pipeline that satisfies all functional (FR‑001…FR‑011) and success‑criteria (SC‑001…SC‑006) requirements.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pybullet`, `torch` (CPU‑only), `numpy`, `pandas`, `scipy`, `statsmodels`, `pytest`  
- **Storage**: Local `data/` directory (raw manifests, generated objects, CSV logs, JSON summaries)  
- **Testing**: `pytest` with CPU‑resource assertions  
- **Target Platform**: GitHub Actions free‑tier runner (Linux, 2 vCPU, 7 GB RAM)  
- **Performance Goals**: Full experiment ≤ 6 h wall‑clock, peak RAM ≤ 7 GB, **no CUDA** usage  
- **Constraints**: CPU‑only (Constitution Principle VI), reproducibility (Principle I), data hygiene (Principle III)  

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | **PASS** | Fixed seeds, isolated `requirements.txt`, deterministic loaders. |
| II. Verified Accuracy | **PASS** | All citations (DragMesh‑2, Gaussian filter) are verified URLs. |
| III. Data Hygiene | **PASS** | Checksums recorded, raw vs. derived files separated. |
| IV. Single Source of Truth | **PASS** | All figures/tables trace back to `data/` artifacts; spec amendment is a separate, versioned artifact. |
| V. Versioning Discipline | **PASS** | Content hashes stored in project state; amendment proposal versioned separately. |
| VI. CPU‑Only Simulation Fidelity | **PASS** | Explicit `pybullet` `DIRECT` mode; `torch.cuda` never imported. |
| VII. Derivative‑Based Stiffness Proxy Validation | **PASS** | GLMM analysis, correlation experiment, paired‑t‑test, and ablation study directly test the estimator. |

## Project Structure
```text
specs/001-virtual-tactile-adaptation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── estimator_output.schema.yaml
│   └── sweep_output.schema.yaml
└── docs/
    ├── README.md
    └── CHANGELOG.md

projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/
├── code/
│   ├── __init__.py
│   ├── environment/
│   │   ├── __init__.py
│   │   ├── drag_mesh_env.py
│   │   └── articulated_object_gen.py
│   ├── estimators/
│   │   ├── __init__.py
│   │   └── virtual_tactile.py
│   ├── policies/
│   │   ├── __init__.py
│   │   ├── static_pica.py
│   │   └── adaptive_pica.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── statistical_test.py
│   └── main.py
├── data/
│   ├── raw/
│   │   └── dragmesh_manifest.jsonl
│   ├── generated/
│   │   └── novel_objects/
│   └── logs/
│       ├── simulation_run_*.csv
│       └── experiment_summary.json
├── tests/
│   ├── unit/
│   │   ├── test_estimator.py
│   │   └── test_scheduler.py
│   ├── integration/
│   │   └── test_cpu_pipeline.py
│   └── contract/
│       └── test_schema_validation.py
├── docs/
│   ├── README.md
│   └── CHANGELOG.md
├── requirements.txt
└── .gitignore
```

## Phase & Task Mapping (covers all FR/SC)

| Phase | Task ID | FR / SC | Description |
|-------|---------|--------|-------------|
| **0. Spec Amendment** | T000 | — | Create `amendment_proposal.md` **adding** a paired‑t‑test analysis (see Task T025a) while retaining the GLMM; this amendment aligns the plan with Constitution Principle VII. |
| **1. Data Preparation** | T010 | FR‑010, FR‑009 | Download DragMesh‑2 manifest, checksum, generate **10** novel articulated objects with friction ∈ [0.8, 1.2] ∪ [0.0, 0.1]; log normal contact force `N`. |
| **2. Simulation & Logging** | T015a | FR‑001, FR‑006, FR‑007, FR‑009, SC‑003, SC‑004 | Run `drag_mesh_env.py` for each object under three policies (`static`, `adaptive`, `ablation_random`). Log raw `torque_hand`, `velocity_object`, and `N` per timestep to CSV. |
| **3. Estimation & Reward Scheduling** | T015b | FR‑001, FR‑002, FR‑006, FR‑007, **FR‑011** | `virtual_tactile.py` reads raw CSV, applies moving‑average (W=5), epsilon clamping (ε=1e‑4), computes `k_norm`, clamps to [1e‑4, 10], updates reward weights per percentile rules (90th/10th). |
| **4. Ablation (Random Proxy)** | T015c | SC‑001, SC‑002 | Replace `k_norm` with uniform random values **while keeping object geometry and initial conditions identical** across policies, thereby isolating the estimator’s contribution. |
| **5. CPU‑Only Enforcement** | T015d | FR‑004 | Verify that no CUDA imports or GPU‑specific calls are present; include a unit test that scans source files for `torch.cuda` and fails if found. |
| **6. Correlation‑Validation Experiment** | T020 | FR‑008, SC‑006 | Run **≥ 30** trials where the true friction coefficient is known. Record `k_norm` and also **normalize** by `N` (or compute partial correlation controlling for `N`). Compute Pearson r; require `r ≥ 0.8`. |
| **7. Power Analysis & Contingency** | T045 | — | Perform a quick analytical power check for the GLMM with 10 objects; if predicted power < 0.8, automatically increase `--num_objects` up to 20 (still ≤ 6 h). |
| **8. Reward Threshold Sensitivity** | T045b | — | Evaluate alternative percentile thresholds (80/20, 85/15) and report impact on success rate; choose the most robust setting. |
| **9. Statistical Analysis – GLMM** | T025 | FR‑005, SC‑005 | Fit a **Generalized Linear Mixed Model** (logit link) with `policy_type` as fixed effect, `object_id` as random intercept; report `p < 0.05`. |
| **10. Statistical Analysis – Paired t‑test** | T025a | FR‑005, SC‑005 | Conduct a paired‑t‑test on per‑object success rates (adaptive vs. static) as required by Constitution Principle VII; report effect size and significance. |
| **11. Result Summarization** | T030 | SC‑001, SC‑002 | Write `experiment_summary.json` with success rates, improvement %, `p_value` (GLMM), `t_test_p`, `correlation_r`, and conclusion flag. |
| **12. Documentation Update** | T040 | — | Populate `docs/README.md` and `docs/CHANGELOG.md` with usage, reproducibility notes, and version history. |
| **13. Contract Validation** | T050 | — | Run `tests/contract/test_schema_validation.py` against generated JSON/CSV artifacts. |
| **14. CI Integration** | T060 | — | Ensure `code/main.py --mode full` runs end‑to‑end on a fresh GitHub Actions runner within the 6 h / 7 GB budget. |

All phases are ordered so that data download precedes generation, generation precedes simulation, simulation precedes estimation, estimation precedes analysis, and analysis precedes reporting.

---

## Decision/Rationale Summary
- **GLMM + Paired t‑test** – Binary outcomes demand a GLMM for mixed‑effects inference *and* a paired t‑test to satisfy Constitution Principle VII. Both are run; GLMM handles random effects, t‑test provides the mandated direct comparison.  
- **Ablation with Random Proxy** – Controls for object‑specific factors by evaluating all policies on the *same* objects and initial states; only the proxy is randomized.  
- **CPU‑only execution** – Enforced by Task T015d; no CUDA imports, `torch` installed with `+cpu`.  
- **Moving‑average window = 5** – Directly matches the verified filter size (Gaussian filter source).  
- **DragMesh‑2 as sole data source** – Open, programmatically downloadable, and provides required geometry; friction is assigned during generation, meeting dataset‑variable fit.  
- **Dynamic Resistance Proxy construct validity** – Acknowledged that torque and velocity derivatives also depend on geometry and mass; justified via the *controlled* correlation experiment that normalizes by contact force `N`.  
- **Reward thresholds** – Sensitivity analysis (Task T045b) will verify that 90th/10th percentiles are robust; alternative thresholds are explored.  
- **Power analysis** – Quick analytic check (Task T045) ensures sufficient statistical power; if under‑powered, object count is increased up to 20 while staying within the 6 h budget.  

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Simulation instability at extreme friction | Clamp `k_norm` (FR‑007) and enforce maximum reward scaling; fallback to reduced timestep if PyBullet reports high forces. |
| Insufficient statistical power | Power analysis (T045) will trigger increase of `--num_objects` up to 20; GLMM and paired t‑test will be re‑run. |
| Noisy derivatives | Apply mandatory moving‑average filter; if still noisy, increase window size to 7 in a secondary run (still documented). |
| Spec‑analysis mismatch | Amendment proposal (`amendment_proposal.md`) adds paired t‑test without removing GLMM; both are documented and versioned. |
| Memory overflow | Stream CSV rows during GLMM fitting; limit episode length and use PyBullet’s `MAX_SUBSTEPS` to reduce state size. |

---


## Quick Reference of FR/SC Coverage
- **FR‑001‑007** – Implemented in `virtual_tactile.py` (estimator).  
- **FR‑008‑009** – Correlation experiment and normal‑force logging in `drag_mesh_env.py`.  
- **FR‑010‑011** – Object generation and percentile‑based reward scaling in `articulated_object_gen.py` & `adaptive_pica.py`.  
- **FR‑004** – Enforced by Task T015d.  
- **FR‑005** – GLMM (Task T025) *and* paired t‑test (Task T025a).  
- **SC‑001‑002** – Success‑rate comparisons recorded in `experiment_summary.json`.  
- **SC‑003‑004** – CI‑budget tracking via `tests/integration/test_cpu_pipeline.py`.  
- **SC‑005** – GLMM `p < 0.05` requirement.  
- **SC‑006** – Pearson r ≥ 0.8 over ≥ 30 trials in correlation experiment.  

---


## Timeline (approximate)

| Week | Milestones |
|------|------------|
| 1 | Data download, object generation (T010). |
| 2 | Simulation runs, logging (T015a‑c). |
| 3 | Estimator implementation, reward scheduler (T015b). |
| 4 | CPU‑only verification (T015d) + ablation runs. |
| 5 | Correlation experiment (T020) + power analysis (T045). |
| 6 | GLMM & paired t‑test analyses (T025, T025a). |
| 7 | Sensitivity analysis (T045b) + result summarization (T030). |
| 8 | Documentation, contract validation, CI integration (T040‑T060). |

---


## Appendices
- **Algorithmic Details** – formulas, filter implementation, percentile computation.  
- **Software Stack** – exact version pins (see `requirements.txt`).  
- **Reproducibility** – random seed (`--seed 42`) recorded in all scripts.  
