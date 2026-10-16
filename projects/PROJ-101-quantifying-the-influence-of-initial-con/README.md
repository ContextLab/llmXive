# Quantifying the Influence of Initial Conditions on Chaotic Systems

This repository provides a reproducible pipeline for generating synthetic chaotic
trajectories, computing finite‑time Lyapunov exponents (FTLE), establishing a clean
asymptotic baseline, performing statistical regression, visualising the results,
and assembling a final scientific report.

---

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Data Generation](#data-generation)
3. [Baseline Computation](#baseline-computation)
4. [FTLE Sweep](#ftle-sweep)
5. [Regression Analysis](#regression-analysis)
6. [Visualisation](#visualisation)
7. [Final Report](#final-report)
8. [Validation & Testing](#validation--testing)

---

## Environment Setup

The project requires **Python 3.11** (or newer) and the packages listed in
`requirements.txt`. Follow the steps below to create an isolated environment:

```bash
# Clone the repository
git clone <REPO_URL>
cd projects/PROJ-101-quantifying-the-influence-of-initial-con

# Create and activate a virtual environment
python -m venv.venv
source.venv/bin/activate # Windows:.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

The environment includes the standard scientific stack (`numpy`, `scipy`,
`pandas`, `matplotlib`, `statsmodels`, `seaborn`) plus the internal
`llmxive_toolkit`. All other required modules are part of the repository.

---

## Data Generation

**Step 1 – Generate trajectories**

Use the CLI entry point to generate raw trajectories for the coupled Lorenz
system. The script creates immutable `.npz` files under `data/raw/`.

```bash
python code/main.py \
 --mode generate \
 --N-values 3,5 \
 --noise-levels 0.0001,0.001,0.01,0.05,0.1,0.2,0.5,0.8,1.0 \
 --trials 30 \
 --steps 10000 \
 --seed 42
```

Parameters:

- `--N-values` Comma‑separated list of system dimensions (number of coupled
 Lorenz oscillators).
- `--noise-levels` Comma‑separated list of Gaussian noise standard deviations
 (`σ_noise`).
- `--trials` Number of independent realizations per `(N, σ_noise)` pair.
- `--steps` Number of integration steps per trajectory (default 10 000).
- `--seed` Global random seed for reproducibility.

The generated files are named
`data/raw/trajectory_N{N}_sigma{sigma}_trial{t}.npz`.

---

## Baseline Computation

**Step 2 – Compute baseline**

Before analysing noisy data, compute the asymptotic Lyapunov exponent for the
clean system using Rosenstein’s algorithm. This produces a JSON file per
dimension under `data/processed/`.

```bash
python code/main.py \
 --mode baseline \
 --N-values 3,5 \
 --seed 42
```

Output files:

- `data/processed/baseline_3.json`
- `data/processed/baseline_5.json`

Each JSON conforms to `contracts/baseline.schema.yaml` and contains the
fields `lambda_max`, `error_estimate`, and `status`.

---

## FTLE Sweep

**Step 3 – FTLE sweep**

With trajectories and baselines in place, compute FTLE over sliding windows
`T ∈ {500, 1000, 5000}`. The CLI automatically loads the appropriate baseline
and writes aggregated results to `data/processed/ftle_results.json`.

```bash
python code/main.py \
 --mode ftle \
 --window-sizes 500,1000,5000 \
 --seed 42
```

The resulting JSON adheres to `contracts/ftle_results.schema.yaml` and
includes, for every trajectory and window size, the fields `lambda_ftle`,
`window_size`, `sigma_noise`, `status`, and a reference to the baseline.

---

## Regression Analysis

**Step 4 – Regression**

The regression step merges FTLE results with clean baselines, computes the
deviation `Δλ = λ_FTLE − λ_baseline`, fits a mixed‑effects multiple linear
regression, applies Benjamini‑Hochberg FDR correction, and always runs a
Tobit censored regression on the full dataset.

```bash
python code/main.py \
 --mode regression \
 --seed 42
```

Outputs:

- `data/processed/regression_results.json` (schema `regression_results.schema.yaml`)
- `data/processed/results.json` (bundles FTLE, regression, and escape‑probability
 metrics; validates against `contracts/results.schema.yaml`).

---

## Visualisation

**Step 5 – Visualisation**

Generate the three required PNG figures:

1. **Convergence plot** – FTLE vs. window size for noise levels 0, 0.01, 0.1.
2. **Bias‑scaling plot** – Δλ vs. `σ_noise` with standard‑error bars.
3. **Dimension‑scaling plot** – Δλ vs. system dimension `N`, annotated with the
 fitted scaling exponent.

```bash
python code/main.py \
 --mode plot \
 --seed 42
```

Figures are saved under `data/processed/plots/`:

- `convergence.png`
- `bias_scaling.png`
- `dimension_scaling.png`

---

## Final Report

**Step 6 – Final report**

Assemble the scientific report summarising all findings, including the four
mandatory sections required by the specification (convergence validation,
bias‑scaling relationship, statistical significance, dimension scaling) and
embed SHA‑256 checksums from the artifact manifest.

```bash
python code/main.py \
 --mode report \
 --seed 42
```

The report is written to
`data/processed/final_report.md`.

---

## Validation & Testing

- Run the full test suite: `pytest -q`.
- Validate all artifacts: `python code/utils/validate.py --check-all`.
- The CI pipeline executes `make docs` which renders this README and checks for
 the required section headings (`Step 1 – Generate trajectories`,
 `Step 2 – Compute baseline`, …). Ensure the headings are present exactly as
 shown above.

---

## License & Citation

This project is released under the **MIT License**. If you use the code or
results in a publication, please cite the repository URL and the original
specification document.

---

*Happy researching!*