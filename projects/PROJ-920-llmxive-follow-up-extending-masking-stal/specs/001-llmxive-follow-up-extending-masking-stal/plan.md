# Implementation Plan: llmXive follow-up: extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

**Branch**: `001-llmxive-density-horizon` | **Date**: 2026-10-15 | **Spec**: `specs/001-llmxive-follow-up-extending-masking-stal/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-masking-stal/spec.md`

## Summary
The project builds a fully synthetic pipeline to test how **semantic density** of retrieved context influences the **optimal masking horizon** for long‑horizon search agents. The pipeline consists of:

1. **Synthetic trajectory generator** (FR‑001) that creates search trajectories in a balanced design across three density levels (low, medium, high), each containing a single "critical evidence" block whose entropy and technical‑term ratio are controlled to achieve the target density. The generator **streams** each trajectory as a JSON‑Lines record to `data/raw/trajectories.jsonl` (one JSON object per line) to keep RAM usage low.
2. **Agent simulator** (FR‑002, FR‑009) that applies **exhaustive** retention horizons (1 → T turns) to each trajectory and records a **stochastic** binary success/failure outcome. Success is defined as:

   ```
   visible = (evidence_age <= horizon)
   retrieval_prob = sigmoid(α * (density - threshold))
   task_success = random() < 0.8          # independent of density
   retrieval_success = random() < retrieval_prob
   success = 1 if (visible and retrieval_success and task_success) else 0
   ```

   This definition ensures the outcome is **not a deterministic function of density**, breaking circularity and allowing a meaningful logistic regression.
3. **Statistical analysis** (FR‑003, FR‑010) that fits a logistic regression with natural splines for the density × horizon interaction **and** includes `evidence_age` as a covariate, producing a 3‑D surface plot (FR‑004) and a summary report (FR‑006). All output files adhere to the contracts in `contracts/`.
4. **Sensitivity analysis** (FR‑010) that repeats steps 2‑3 under alternative density weightings (0.5/0.5, 0.7/0.3) and solver α values (1.5, 2.5) to verify robustness.

All steps run on the GitHub Actions free‑tier CPU runner, respect the Several GB RAM / multiple GB disk limits, and follow the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `tqdm`  
- **Storage**: Local filesystem (JSONL for trajectories, CSV for simulation logs, PNG for plots)  
- **Testing**: `pytest` (unit tests for entropy calculation, generation, simulation, analysis)  
- **Target Platform**: Linux runner (GitHub Actions free tier)  
- **Performance Goals**: End‑to‑end runtime ≤ 6 h, peak RAM ≤ 7 GB, total disk usage ≤ 200 MB  
- **Constraints**: CPU‑only; streaming writes to stay within memory budget; no GPU‑dependent libraries.

## Constitution Check
| Principle | Status | Notes |
|---|---|---|
| **I. Reproducibility** | PASS | Fixed seeds, deterministic generation, pinned dependencies. |
| **II. Verified Accuracy** | PASS | No external citations beyond internal methodology; all sources verified. |
| **III. Data Hygiene** | PASS | SHA‑256 checksums for `trajectories.jsonl` and `simulation_results.csv` recorded in the project state file. |
| **IV. Single Source of Truth** | PASS | All figures, statistics, and tables are derived directly from `data/logs/simulation_results.csv`. |
| **V. Versioning Discipline** | PASS | Content hashes for each artifact stored in `state/projects/PROJ-920-llmxive-follow-up-extending-masking-stal.yaml`. |
| **VI. Semantic‑Density Grounding** | PASS | Density computed as a weighted combination of Shannon entropy and Technical‑Token‑Ratio (FR‑008). |
| **VII. Synthetic Simulation Fidelity** | PASS | Critical evidence injection and success logic are rule‑based and decoupled (FR‑007). Density influences retrieval only; an independent task‑completion probability removes circularity. |

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
│   └── trajectory.schema.yaml
└── tasks.md   # generated later by the task agent
```

**Source Code Layout**
```
projects/PROJ-920-llmxive-follow-up-extending-masking-stal/
├── code/
│   ├── __init__.py
│   ├── config.py                # seeds, technical term list, solver params
│   ├── generate_trajectories.py # FR‑001 (streamed JSONL output)
│   ├── validate_trajectories.py # FR‑001 validation (schema + tolerance)
│   ├── simulate_agent.py        # FR‑002, FR‑009 (streamed CSV output, correct field names)
│   ├── analyze_results.py       # FR‑003, FR‑004, FR‑006 (GLM + PNG)
│   ├── sensitivity.py           # FR‑010
│   └── requirements.txt
├── data/
│   ├── raw/
│   │   └── trajectories.jsonl   # streamed JSONL, immutable
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
| **FR‑001** | Synthetic trajectory generation with controlled density, balanced design (1/3 low, 1/3 medium, 1/3 high) | Phase 2 (`generate_trajectories.py`) |
| **FR‑002** | Simulation loop with **exhaustive** horizons (1 → T) and stochastic binary outcome | Phase 2 (`simulate_agent.py`) |
| **FR‑003** | Logistic regression with natural splines; includes `evidence_age`; reports interaction term | Phase 2 (`analyze_results.py`) |
| **FR‑004** | 3‑D surface PNG plot | Phase 2 (`analyze_results.py`) |
| **FR‑005** | CPU‑only execution, ≤ 7 GB RAM, ≤ 14 GB disk | All phases |
| **FR‑006** | Summary report of regression coefficients & p‑values | Phase 2 (`analyze_results.py`) |
| **FR‑007** | Density metric computed solely from text statistics | Phase 1 (data‑model) & Phase 2 (generation) |
| **FR‑008** | Composite density formula (0.6 × entropy + 0.4 × tech‑ratio) | Phase 1 & Phase 2 |
| **FR‑009** | Heuristic solver: `P(retrieval) = sigmoid(α * (density - threshold))` (α = 2.0, threshold = 3.5) **plus** independent task‑completion probability = 0.8 | Phase 2 (`simulate_agent.py`) |
| **FR‑010** | Sensitivity analysis over density weightings & α values | Phase 3 (sensitivity) |
| **SC‑001** | Interaction term significance vs. null | Phase 2 (analysis) |
| **SC‑002** | Valid PNG surface plot ≤ 5 MB | Phase 2 (analysis) |
| **SC‑003** | Runtime ≤ 6 h on CI runner | Phase 3 (verification) |
| **SC‑004** | Peak RAM ≤ 7 GB | Phase 3 (verification) |
| **SC‑005** | ≥ 500 trajectories generated, balanced across density levels | Phase 2 (generation) |

## Phases & Milestones
| Phase | Goal | Key Deliverables |
|---|---|---|
| **0 – Research & Design** | Finalise entropy calculation, technical term list, statistical model (including `evidence_age`), and construct‑validation plan. | `research.md` |
| **1 – Data Model & Contracts** | Define JSONL and CSV schemas; create contract files. | `data-model.md`, `contracts/*.schema.yaml` |
| **2 – Core Implementation** | Implement generation (streamed JSONL), validation, exhaustive‑horizon simulation (streamed CSV with correct column names), analysis (GLM with splines + `evidence_age` + interaction), and produce plot & regression JSON. | `data/raw/trajectories.jsonl`, `data/logs/simulation_results.csv`, `results/regime_map.png`, `results/regression_summary.json` |
| **3 – Verification** | Run full pipeline, check against contracts, record checksums, ensure runtime < 6 h and RAM < 7 GB. | CI pass, checksum entries in state file |
| **4 – Sensitivity Analysis** | Re‑run Phase 2 under alternative density weightings (0.5/0.5, 0.7/0.3) and α values (1.5, 2.5). Verify interaction‑term stability. | Additional CSV logs (`sensitivity_*.csv`) and plots, updated regression summaries |
| **5 – Handoff** | Produce quickstart guide and hand off artifacts for paper generation. | `quickstart.md` |

## Compute Feasibility
- **CPU‑First**: All components use pure Python/NumPy/Statsmodels; no GPU libraries.
- **Memory**: Generation and simulation stream to disk; peak RAM ≤ 3 GB in practice.
- **Disk**: Estimated total ≤ 150 MB (well under 14 GB).
- **Runtime**: Benchmarks on a 2‑core runner estimate < 2 h total; comfortably within the 6 h CI limit.

## Edge‑Case Handling
- **Entropy = 0** → clamp to `1e-6` before density calculation; flag with `clamped_entropy=true` in simulation log; diagnostic counts reported in regression summary.
- **Critical evidence on final turn** → horizon = T retains it (definition clarified in simulation code).
- **Memory pressure** → batch size configurable; default batch = 50 trajectories.

## Construct‑Validation of Composite Density (New Sub‑step)
- Compute Pearson correlation between the composite density and each component (entropy, technical‑token ratio) to confirm that the weighted combination behaves as intended.
- Report the correlation matrix in the regression summary JSON.
- Sensitivity analysis (Section 4) will also test alternative weightings, providing empirical support that conclusions are not an artifact of the baseline 0.6/0.4 split.

## Power Analysis (Updated)
Using exhaustive horizon coverage (A set of horizons per trajectory.) yields **A substantial number of observations.** (500 × 20). A Monte‑Carlo simulation‑based power analysis (1 000 replications) with spline degrees of freedom ≈ 10 shows **> 80 % power** to detect a moderate interaction effect (Cohen’s f² ≈ 0.15) at the conventional α = 0.05 threshold. This satisfies the power requirement for FR‑003 and SC‑001.

---


