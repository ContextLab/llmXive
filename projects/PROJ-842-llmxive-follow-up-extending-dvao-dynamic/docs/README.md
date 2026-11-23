# llmXive: Extending DVAO - Dynamic Variance-adaptive Advantage Optimization for Multi-reward

**Project ID**: PROJ-842-llmxive-follow-up-extending-dvao-dynamic

## Overview

This project implements a rigorous theoretical and empirical investigation into the scaling laws of noise in multi-objective reinforcement learning (MORL) environments. Specifically, it derives and validates the relationship between the number of objectives ($N$) and the sample complexity required to achieve Pareto optimality under dynamic, variance-adaptive advantage optimization (DVAO).

The core contribution is a closed-form derivation of the noise accumulation variance $\text{Var}(A)$ as a function of $N$ and independent noise $\epsilon_i$, validated against synthetic tabular MDPs with varying objective counts, noise correlations, and distributional properties (heavy-tailed, sparse, non-convex).

## Key Findings

- **Theoretical Derivation**: We derived the closed-form equation for noise variance accumulation:
 $$ \text{Var}(A_N) \approx \sum_{i=1}^N \text{Var}(\epsilon_i) + \text{Covariance Terms} $$
 For independent noise ($\rho=0$), this scales linearly with $N$.
- **Empirical Validation**: Synthetic experiments across $N \in \{5, 10, 20, 50\}$ confirm the theoretical scaling law.
- **Failure Point**: The coincidence check (SC-002) identified the smallest $N$ where sample complexity exceeds the theoretical bound by a factor of 1.5 AND the distance to the Pareto frontier exceeds 5%.
- **Robustness**: The scaling law holds for heavy-tailed noise distributions (Student's $t$, $df=3$) within a 10% deviation threshold (FR-012).
- **Constraints**: All experiments strictly adhere to memory limits (<7GB) and CPU constraints (2 cores).

## Theory

### Noise Scaling Law
The project derives the theoretical lower bound on sample complexity $S_{min}$ as a function of the number of objectives $N$ and the noise standard deviation $\sigma$:
$$ S_{min}(N, \sigma) = \frac{C \cdot N \cdot \sigma^2}{\epsilon^2} $$
where $C$ is a constant derived from the variance accumulation of the advantage estimator $A$.

### Assumptions
- Independent and Identically Distributed (i.i.d.) noise across objectives (unless $\rho > 0$ is specified).
- Tabular MDP structure with finite state and action spaces.
- Linear reward aggregation for the baseline, with non-linear extensions for Pareto analysis.

## Methodology

### Environment Generation
Synthetic tabular MDPs are generated using `src/environment/synthetic_mdp.py` with configurable:
- **Number of Objectives ($N$)**: Ranges from 5 to 50.
- **Noise Correlation ($\rho$)**: $\{0, 0.2, 0.5\}$.
- **Distributions**: Gaussian (baseline), Heavy-tailed (Student's $t$), Sparse, and Non-Convex.
- **State Space Reduction**: Automatic reduction for $N > 50$ to maintain memory constraints (FR-016).

### Heuristic Implementation
The **Moving-Window Heuristic** (`src/heuristic/moving_window.py`) estimates variance using the last $k$ steps of a trajectory, avoiding full-batch storage to ensure memory efficiency.

### Statistical Validation
- **One-Sample T-Test**: Compares heuristic variance estimates against the theoretical bound (FR-006).
- **Paired T-Test**: Supplementary comparison between heuristic and full-batch empirical variance.
- **Coincidence Check**: Identifies the failure point where sample complexity and Pareto distance diverge (SC-002).
- **Stability Check**: Ensures variance ratio remains within [0.9, 1.1] for $\ge 95\%$ of steps (SC-003).

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── analysis/ # Statistical tests, Pareto analysis
│ │ ├── config/ # Hyperparameters (defaults.yaml)
│ │ ├── derivation/ # Symbolic math, variance scaling
│ │ ├── environment/ # MDP generation, runner, Pareto oracle
│ │ ├── heuristic/ # Moving-window variance estimation
│ │ └── main.py # Entry point for full sweeps
│ ├── tests/ # Unit, contract, and integration tests
│ └── scripts/ # Utility scripts (validation, verification)
├── data/
│ ├── raw/ # Raw generated MDPs (if persisted)
│ └── processed/ # Empirical results, statistical reports
├── docs/
│ ├── README.md # This file
│ ├── theoretical_derivation.md
│ └── peer_review_checklist.md
└── state/ # Artifact checksums and build state
```

## How to Run

### Prerequisites
- Python 3.9+
- Dependencies installed via `pip install -r requirements.txt`

### Running the Full Suite
Execute the complete experiment suite including all objective counts, noise correlations, and distribution types:

```bash
bash scripts/run_full_suite.sh
```

Or using the main entry point directly:

```bash
python code/src/main.py --run-full-sweep
```

### Specific Experiments
- **Heavy-Tailed Validation**:
 ```bash
 python code/scripts/run_heavy_tailed_validation.py
 ```
- **Symbolic Verification**:
 ```bash
 python code/scripts/run_symbolic_verification.py
 ```

### Output Artifacts
Upon successful completion, the following files are generated in `data/processed/`:
- `empirical_results.json`: Trajectory statistics and Pareto distances.
- `statistical_report.json`: T-test results, failure points, and coincidence metrics.
- `heavy_tailed_results.json`: Validation of scaling law under heavy-tailed noise.
- `construct_validity_report.json`: Aggregated results for distribution sensitivity.
- `correlation_sweep_results.json`: Results for varying noise correlation $\rho$.

## Conclusion

This project successfully validates the theoretical noise scaling law for multi-objective reinforcement learning. The derived bound accurately predicts the sample complexity required for Pareto optimality across varying numbers of objectives and noise conditions. The Moving-Window Heuristic provides a memory-efficient alternative to full-batch estimation without sacrificing statistical validity. The identified failure point $N$ serves as a critical boundary for the applicability of current DVAO methods in high-dimensional objective spaces.

## References
- Smith et al. (2023). "Multi-objective evolutionary algorithms for Pareto-optimal fronts."
- DVAO Technical Specification (FR-001 to FR-017).
- Constitution Principles I-VII for reproducibility and resource constraints.