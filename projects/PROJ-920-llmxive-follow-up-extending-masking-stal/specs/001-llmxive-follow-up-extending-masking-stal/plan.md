# Implementation Plan: llmXive follow-up: extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

**Branch**: `001-llmxive-density-horizon` | **Date**: 2026-10-09 | **Spec**: `specs/001-llmxive-follow-up-extending-masking-stal/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-masking-stal/spec.md`

## Summary
The project builds a fully synthetic pipeline to test how **semantic density** of retrieved context influences the **optimal masking horizon** for long‑horizon search agents. The pipeline consists of:

1. **Synthetic trajectory generator** (FR‑001) that creates search trajectories in a balanced design across three density levels (low, medium, high), each containing a single "critical evidence" block whose entropy and technical‑term ratio are controlled to achieve the target density.
2. **Agent simulator** (FR‑002, FR‑009) that applies configurable retention horizons (1 → T turns) and records binary success/failure using a density-dependent heuristic solver: `P(success) = visibility AND sigmoid(α * (density - threshold))` where α=2.0 and threshold=3.5 bits/token (FR‑009).
3. **Statistical analysis** (FR‑003, FR‑010) that fits a logistic regression with tensor-product splines for the density × horizon interaction, then produces a 3‑D surface plot (FR‑004) and a summary report (FR‑006).
4. **Sensitivity analysis** (FR‑010) that repeats steps 2‑3 under alternative density‑weightings and solver α values to confirm robustness.

All steps run on the GitHub Actions free‑tier CPU runner, respect the Several GB RAM / multiple GB disk limits, and follow the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `matplotlib`, `seaborn` (for 3‑D plotting), `tqdm` (progress bars)  
- **Storage**: Local filesystem (JSON for trajectories, CSV for simulation logs, PNG for plots)  
- **Testing**: `pytest` (unit tests for entropy calculation, generation, simulation, analysis)  
- **Target Platform**: Linux runner (GitHub Actions free tier)  
- **Project Type**: Research‑oriented CLI / library  
- **Performance Goals**: End‑to‑end runtime ≤ 6 h, peak RAM ≤ 7 GB, total disk usage ≤ 200 MB  
- **Constraints**: CPU‑only; no GPU‑dependent libraries; streaming writes to stay within memory budget  

## Constitution Check
| Principle | Status | Notes |
|---|---|---|
| **I. Reproducibility** | PASS | Random seeds are fixed in `code/config.py`; all dependencies pinned in `code/requirements.txt`; no external data. |
| **II. Verified Accuracy** | PASS | No external citations are required; all calculations are deterministic and documented. |
| **III. Data Hygiene** | PASS | SHA‑256 checksums for `trajectories.json` and `simulation_results.csv` will be recorded in the project state file. Raw files are immutable. |
| **IV. Single Source of Truth** | PASS | All figures, statistics, and tables are derived directly from `data/logs/simulation_results.csv`. |
| **V. Versioning Discipline** | PASS | Content hashes for each artifact are stored in `state/projects/PROJ-920-llmxive-follow-up-extending-masking-stal.yaml`. |
| **VI. Semantic‑Density Grounding** | PASS | Density is computed as a weighted combination of Shannon_Entropy and Technical_Token_Ratio, with greater weight assigned to Shannon_Entropy. per FR‑008; the metric is used as a predictor in the solver and regression. |
| **VII. Synthetic Simulation Fidelity** | PASS | Critical evidence injection and success logic are rule‑based and decoupled (FR‑007). Density directly influences success via the sigmoid solver (FR‑009), ensuring no circular dependencies. |

## Project Structure
```
specs/001-llmxive-density-horizon/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── regression_output.schema.yaml
│   ├── simulation_log.schema.yaml
│   ├── simulation_result.schema.yaml
│   └── trajectory.schema.yaml
└── tasks.md   # generated later by the task agent
```

**Source Code Layout**
```
projects/PROJ-920-llmxive-follow-up-extending-masking-stal/
├── code/
│   ├── __init__.py
│   ├── config.py                # seeds, technical term list, solver params
│   ├── generate_trajectories.py # FR‑001
│   ├── validate_trajectories.py # FR‑001 validation
│   ├── simulate_agent.py        # FR‑002, FR‑009
│   ├── analyze_results.py       # FR‑003, FR‑004, FR‑006
│   ├── sensitivity.py           # FR‑010
│   └── requirements.txt
├── data/
│   ├── raw/
│   │   └── trajectories.json
│   └── logs/
│       └── simulation_results.csv
├── results/
│   ├── regime_map.png
│   └── regression_summary.json
└── tests/
    ├── test_generation.py
    ├── test_simulation.py
    └── test_analysis.py
```

## Mapping of Functional & Success Criteria to Phases
| FR / SC | Description | Phase(s) implementing / verifying |
|---|---|---|
| **FR‑001** | Synthetic trajectory generation with controlled density, balanced design (1/3 low, 1/3 medium, 1/3 high) | Phase 2 (implementation of `generate_trajectories.py`) |
| **FR‑002** | Simulation loop with configurable horizon, binary outcome | Phase 2 (`simulate_agent.py`) |
| **FR‑003** | Logistic regression with tensor-product splines, report interaction term | Phase 2 (`analyze_results.py`) |
| **FR‑004** | 3‑D surface PNG plot | Phase 2 (`analyze_results.py`) |
| **FR‑005** | CPU‑only execution, ≤ 7 GB RAM, ≤ 14 GB disk | All phases (design choices) |
| **FR‑006** | Summary report of regression coefficients & p‑values | Phase 2 (`analyze_results.py`) |
| **FR‑007** | Density metric computed solely from text statistics | Phase 1 (data‑model) & Phase 2 (generation) |
| **FR‑008** | Composite density formula (weighted combination of entropy and tech‑ratio, with entropy receiving greater weight than tech‑ratio) | Phase 1 (data‑model) & Phase 2 (generation) |
| **FR‑009** | Heuristic solver: P(success) = visibility AND sigmoid(α * (density - threshold)) | Phase 2 (`simulate_agent.py`) |
| **FR‑010** | Sensitivity analysis over density weights & α values | Phase 3 (sensitivity) |
| **SC‑001** | Interaction term significance vs. null | Phase 2 (analysis) |
| **SC‑002** | Valid PNG surface plot ≤ 5 MB | Phase 2 (analysis) |
| **SC‑003** | Runtime ≤ 6 h on CI runner | Phase 3 (verification) |
| **SC‑004** | Peak RAM ≤ 7 GB | Phase 3 (verification) |
| **SC‑005** | ≥ 500 trajectories generated, balanced across density levels | Phase 2 (generation) |

## Phases & Milestones
| Phase | Goal | Key Deliverables |
|---|---|---|
| **0 – Research & Design** | Finalise entropy calculation, technical term list, and statistical model spec. | `research.md` |
| **1 – Data Model & Contracts** | Define JSON and CSV schemas; create contract files. | `data-model.md`, `contracts/*.schema.yaml` |
| **2 – Core Implementation** | Implement generation, validation, simulation, analysis. Produce raw data, logs, plot, and regression JSON. | `data/raw/trajectories.json`, `data/logs/simulation_results.csv`, `results/regime_map.png`, `results/regression_summary.json` |
| **3 – Verification** | Run full pipeline, check against contracts, record checksums, ensure runtime & memory limits. | CI pass, checksum entries in state file |
| **4 – Sensitivity Analysis** | Re‑run Phase 2 with alternative density weightings (0.5/0.5, 0.7/0.3) and α ∈ {low, moderate} exponent values. Verify interaction term stability. | Additional CSV logs (`sensitivity_*.csv`) and plots, updated regression summary. |
| **5 – Handoff** | Produce quickstart guide and hand off artifacts for paper generation. | `quickstart.md` |

## Compute Feasibility
- **CPU‑First**: All steps use pure Python/NumPy/Statsmodels; no GPU libraries.
- **Memory Management**: Generation writes JSON incrementally; simulation streams each trajectory's horizon trials directly to CSV; analysis reads CSV in chunks if needed.
- **Disk**: Estimated ≤ 150 MB (500 × ~200 KB JSON + logs + plots) well under 14 GB limit.
- **Runtime**: Empirically bounded < 2 h on a 2‑core runner (entropy calc ≈ sub-millisecond/turn, simulation ≈ sub-millisecond per horizon trial, regression < 30 s).

## Edge‑Case Handling
- **Entropy = 0** → clamp to `1e-6` before density calculation; flag with `clamped_entropy=true` in simulation log; perform diagnostic checks (histogram, outlier detection) before regression; report count and impact in summary.
- **Critical evidence on final turn** → horizon = T retains it (definition clarified in simulation code).
- **Memory pressure** → batch size configurable; default batch = 50 trajectories.

---
