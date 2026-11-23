# Implementation Plan: llmXive follow‑up: extending “DVAO: Dynamic Variance‑adaptive Advantage Optimization for Multi‑reward”

**Branch**: `001-llmxive-noise-scaling` | **Date**: 2026‑07‑12 | **Spec**: `specs/001-llmxive-noise-scaling/spec.md`  
**Input**: Feature specification from `specs/001-llmxive-noise-scaling/spec.md`

## Summary
The project delivers two tightly coupled deliverables:

1. **Theoretical derivation** of a closed‑form variance accumulation law for a weighted advantage function with \(N\) independent noisy objectives and the resulting sample‑complexity lower bound (FR‑001, FR‑002, SC‑001).  
2. **Empirical validation** using synthetic tabular MDPs (FR‑003‑FR‑019, SC‑002‑SC‑007).  The validation pipeline implements the Moving‑Window Heuristic, a static scalarization baseline, extensive sensitivity sweeps (window size \(k\), noise correlation \(\rho\), reward‑distribution type), and a held‑out heavy‑tailed set (FR‑012). All experiments run on a GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM) and respect the resource guard for \(N>50\) (FR‑016, FR‑005).

## Technical Context
| Item | Detail |
|------|--------|
| **Language / Version** | Python 3.11 |
| **Primary Dependencies** | `numpy`, `scipy`, `sympy`, `pandas`, `matplotlib`, `statsmodels`, `pyyaml` |
| **Storage** | Local filesystem under `data/processed/` (JSON) |
| **Testing** | `pytest` (unit & integration) |
| **Target Platform** | Linux runner on GitHub Actions (CPU‑only) |
| **Project Type** | Research library / CLI |
| **Constraints** | 2 CPU cores, ≤ 7 GB RAM, wall‑time ≤ 6 h per job |
| **Scale / Scope** | Objective counts \(N \in \{5,10,15,20,30,40,50\}\); state‑space fixed at 200 (constant across all N); episode count halved when \(N>50\) to keep RAM ≤ 7 GB; window‑size fractions \(\{0.01,0.05,0.1\}\) |

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| **I. Reproducibility** | PASS | Fixed random seeds, `requirements.txt`, deterministic synthetic generation. |
| **II. Verified Accuracy** | PASS | `docs/citations.md` + `src/verification/verify_citations.py` audit before any run. |
| **III. Data Hygiene** | PASS | All generated JSON files are checksummed; no in‑place mutation. |
| **IV. Single Source of Truth** | PASS | Each figure/table references a single JSON artifact and a single code path. |
| **V. Versioning Discipline** | PASS | Content hashes recorded in `state/…yaml`. |
| **VI. Theoretical Lower Bound Validation** | PASS | Derivation lives in `src/derivation/`; empirical validation uses independent held‑out set (FR‑012). |
| **VII. Computational Resource Constraint Adherence** | PASS | CPU‑only pipeline, state‑space kept constant, resource guard reduces *episode count* for very large N, explicit RAM monitor (FR‑005). |

## Project Structure
```text
specs/001-llmxive-noise-scaling/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── empirical_results.schema.yaml
└── tasks.md          # generated later by /speckit-tasks

code/
├── src/
│   ├── derivation/
│   │   ├── sample_complexity.py          # symbolic derivation (FR‑001, FR‑002)
│   │   └── verify_symbolic.py            # SC‑001 verification
│   ├── environment/
│   │   ├── synthetic_mdp.py              # FR‑003, FR‑014, FR‑016, FR‑012 logging
│   │   └── reward_generators.py          # Linear / Sparse / Non‑Convex / Heavy‑Tailed / NonLinearMLP (construct‑validity extension)
│   ├── analysis/
│   │   ├── heuristic.py                  # Moving‑Window Heuristic (FR‑004, FR‑013)
│   │   ├── baseline_scalarization.py     # Static scalarization baseline (FR‑018)
│   │   ├── pareto_oracle.py              # Exhaustive Pareto frontier (FR‑017)
│   │   └── statistics.py                 # Regression, t‑tests, binomial test, TOST (FR‑006, FR‑007, FR‑009, FR‑015)
│   ├── verification/
│   │   └── verify_citations.py           # Constitution II audit
│   └── main.py                           # Orchestration script
├── scripts/
│   └── validate_construct_validity.py    # FR‑010 aggregation (added)
├── tests/
│   ├── unit/
│   │   ├── test_derivation.py
│   │   ├── test_mdp.py
│   │   └── test_heuristic.py
│   └── integration/
│       └── test_full_suite.py
├── data/
│   ├── raw/                               # empty (synthetic only)
│   └── processed/
│       ├── theoretical_bound.json
│       ├── noise_properties.json
│       ├── empirical_results.json
│       ├── construct_validity_results.json
│       └── statistical_results.json
├── docs/
│   └── citations.md                      # primary theoretical sources
├── requirements.txt
└── pyproject.toml
```
*Structure Decision*: A modular library layout isolates derivation (`derivation/`) from simulation (`environment/`) and analysis (`analysis/`), satisfying Principle IV (single source of truth) and enabling unit testing of each component.

## Implementation Phases & Task Mapping
| Phase | Goal | FR(s) Covered | Key Tasks |
|-------|------|---------------|-----------|
| **0 – Pre‑implementation verification** | Confirm citations & reproducibility | II | 0.1 Run `verify_citations.py`; 0.2 Pin seeds; 0.3 Record checksums. |
| **1 – Theoretical derivation** | Symbolic variance law & sample‑complexity bound | FR‑001, FR‑002, SC‑001 | 1.1 Derive with `sympy`; 1.2 Export closed‑form JSON; 1.3 Verify with `verify_symbolic.py`. |
| **2 – Synthetic environment generation** | Produce tabular MDPs for each \(N\) and correlation | FR‑003, FR‑014, FR‑016, FR‑012 | 2.1 Call `synthetic_mdp.py` with `--n {5,10,15,20,30,40,50}` and `--rho {0,0.2,0.5}`; 2.2 State‑space remains **200** for all N (constant); if `N>50` the guard halves **episode count** to keep RAM ≤ 7 GB; 2.3 Log full correlation matrix and write `noise_properties.json`. |
| **3 – Heuristic & baseline implementation** | Estimate variance, baseline comparison | FR‑004, FR‑013, FR‑018 | 3.1 Implement Moving‑Window Heuristic (`heuristic.py`); 3.2 Implement static scalarization (`baseline_scalarization.py`). |
| **4 – Core experimental runs** | Collect raw performance data, record convergence speed (FR‑019) | FR‑005, FR‑006, FR‑007, FR‑009, FR‑010, FR‑015, FR‑019 | 4.1 Enforce CPU & RAM guard; 4.2 Run **≥30** independent episodes per configuration (≥ 50 runs for final analysis); 4.3 Record `convergence_speed_episodes` and other metrics in `empirical_results.json`. |
| **5 – Statistical validation** | Test scaling‑law lower‑bound (one‑sided), estimator bias, sensitivity | SC‑002‑SC‑007, FR‑006, FR‑015, FR‑009, FR‑007 | 5.1 Noise sanity check (FR‑014); 5.2 **One‑sided** test that empirical sample count ≥ theoretical bound for each N; 5.3 Linear regression of log(sample) vs log(N) with a **one‑sided** test that empirical slope is not significantly less than the theoretical slope (margin ± 0.1); 5.4 One‑sample t‑test on heuristic bias (FR‑015); 5.5 TOST equivalence tests for window‑size sweep (FR‑007) and correlation sweep (FR‑009). |
| **6 – Construct‑validity & held‑out validation** | Verify robustness across reward families and heavy‑tailed noise | FR‑010, FR‑012, SC‑006, SC‑007 | 6.1 Generate Linear, Sparse, Non‑Convex, and **NonLinearMLP** rewards via `reward_generators.py`; 6.2 Compute descriptive statistics (mean, variance, skewness) and compare them to published LLM‑reward statistics (e.g., OpenAI RLHF reward logs) to demonstrate similarity; 6.3 Run full suite for each; 6.4 Generate heavy‑tailed held‑out set; 6.5 Aggregate results with `validate_construct_validity.py`. |
| **7 – Reporting & Artifact Generation** | Produce JSON & figures for paper | All SCs | 7.1 Write `statistical_results.json`; 7.2 Export regression plots, Pareto distance plots; 7.3 Ensure all artifacts conform to the schemas in `contracts/`. |

### Coverage Checklist
| Requirement | Mapped Phase/Task | Confirmation |
|-------------|-------------------|--------------|
| FR‑001‑FR‑002 | Phase 1 | Derivation module produces variance equation & sample‑complexity bound. |
| FR‑003‑FR‑004‑FR‑005‑FR‑006‑FR‑007‑FR‑009‑FR‑010‑FR‑012‑FR‑013‑FR‑014‑FR‑015‑FR‑016‑FR‑017‑FR‑018‑FR‑019 | Phases 2‑6 | Each functional requirement is addressed by a concrete module or test; FR‑019 now appears explicitly in Phase 4. |
| SC‑001‑SC‑007 | Phase 5‑6 | Statistical rigor (t‑tests, TOST, one‑sided bound test, power acknowledgement) is explicit. |
| Resource guard (FR‑016) | Phase 2 | `reduce_episode_count()` halves episodes when \(N>50\); state‑space stays constant. |
| Minimum window size enforcement | Phase 3 | Heuristic validates `k >= 0.02`; violations are logged as `ResourceLimitExceeded`. |
| Heavy‑tailed held‑out set | Phase 6 | Separate generation pass, distinct seed, logged in `noise_properties.json`. |

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| OOM for \(N=50\) | High | State‑space fixed; episode count halved; RAM monitor aborts with clear error. |
| Sparse N grid → low power | Medium | Added intermediate N values (15,30,40) and increased runs to ≥ 30 per config (≥ 50 for final analysis). |
| Confounding state‑space size | Medium | State‑space kept **constant**; episode count used as guard and logged as covariate. |
| Construct‑validity insufficiency | Medium | Added non‑linear MLP generator and statistical comparison to real LLM reward statistics. |
| Spec‑level mismatch (KS vs t‑test) | High | Replaced KS test with appropriate one‑sided bound test and regression slope test (see Phase 5). |

## Open Items
* **Spec Amendment** – Formal request to replace KS test with the one‑sided bound test (already reflected in the plan).  
* **Missing FR‑011** – Resolved by removing the spurious reference; FR‑018 correctly covers the static baseline.  

---


