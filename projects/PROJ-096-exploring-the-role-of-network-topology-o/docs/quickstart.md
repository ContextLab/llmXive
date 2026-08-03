# Quickstart Guide: Exploring the Role of Network Topology on Synchronization

This guide provides a step-by-step walkthrough for reproducing the research on how network topology influences synchronization in coupled oscillators (Kuramoto model).

## Prerequisites

- Python 3.9+
- pip (package installer)
- Virtual environment tool (venv or virtualenv)

## 1. Environment Setup

Clone the repository and set up the Python environment:

```bash
# Create virtual environment
python -m venv code/.venv
source code/.venv/bin/activate # On Windows: code\.venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 2. Project Initialization

Ensure the directory structure and configuration files are in place:

```bash
# Verify directory structure
python code/setup_directories.py

# Verify linting configuration
python code/verify_linting.py
```

## 3. Feasibility Study

Determine the maximum feasible simulation parameters within the compute budget:

```bash
python code/feasibility_study.py
```

**Output**: `data/processed/config.json` containing `time_steps`, `n_topologies`, and `run_count`.

## 4. Generate Network Topologies (User Story 1)

Generate synthetic regular ring lattices with varying small-world rewiring probabilities:

```bash
python code/generate_topology.py
```

**Outputs**:
- `data/processed/topology_{id}_p{p:.2f}_seed_{seed}.gpickle` (graph files)
- `data/processed/graph_metadata.json` (metadata)

**Verification**: Ensure all generated graphs are connected and have N=500 nodes.

## 5. Simulate Kuramoto Dynamics (User Story 2)

Run the Kuramoto oscillator simulation on each generated topology to determine the critical coupling strength ($K_c$):

```bash
python code/simulate_kuramoto.py
```

**Output**: `data/processed/simulation_results.csv` containing $K_c$ values for each topology.

## 6. Physical Invariance Verification (MANDATORY)

**This step is required to validate that the critical coupling strength is an observer-invariant physical property.**

Execute the invariance check to verify that $K_c$ remains consistent regardless of the phase reference frame (single oscillator vs. center-of-mass) and across multiple random seeds:

```bash
python code/verify_invariance.py
```

**Input**: `data/processed/simulation_results.csv` and topology graphs from Step 4.
**Output**: `data/processed/invariance_verification.json`

**Success Criteria**:
- The difference between mean $K_c$ in the single-oscillator frame and the center-of-mass frame must be < $10^{-4}$.
- Variance across seeds must be below the stability threshold (e.g., 0.01).
- If any topology fails these criteria, the pipeline halts with `PHYSICAL_INVARIANCE_FAILURE` or `STABILITY_FAILURE`.

**Note**: This verification addresses the requirement that physical quantities must correspond to elements of reality independent of the observer's coordinate frame (EPR criterion).

## 7. Stability Analysis (User Story 2)

Verify the stability of the synchronization dynamics across multiple runs:

```bash
python code/check_stability.py
```

**Output**: `data/processed/stability_results.json`

## 8. Statistical Analysis (User Story 3)

Quantify the relationship between rewiring probability and critical coupling strength:

```bash
# Calculate correlation
python code/analyze_results.py

# Run sensitivity analysis
python code/sensitivity_analysis.py
```

**Outputs**:
- `data/processed/correlation_results.json`
- `data/processed/sensitivity_analysis.json`
- `data/processed/plot_kc_vs_p.png`
- `data/processed/analysis_report.md`

## 9. Review Results

The final analysis report is generated at `data/processed/analysis_report.md`. This document includes:
- Spearman correlation coefficient and p-value.
- Physical invariance verification status.
- Stability analysis results.
- Sensitivity analysis outcomes.
- Scope reduction details (if applicable).

## Troubleshooting

- **Missing config.json**: Ensure `code/feasibility_study.py` has been run successfully.
- **Disconnected graphs**: The topology generator logs disconnected graphs to `disconnected_log.json`.
- **Invariance failure**: Check `data/processed/invariance_verification.json` for specific topology failures.

## References

- See `docs/methodology.md` for detailed theoretical background on the rotational invariance test.
- See `specs/001-exploring-the-role-of-network-topology-synchronization/spec.md` for full project specifications.