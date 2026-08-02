# Quickstart: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Prerequisites

-   **Python**: 3.11+
-   **OS**: Linux (Ubuntu 20.04+ recommended for PyBullet compatibility)
-   **Memory**: > 7 GB RAM
-   **Disk**: > 14 GB free space

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-898-llmxive-follow-up-extending-geometric-ac
    python -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: `pybullet`, `torch`, `cvxpy`, `scipy`, `datasets`, `pandas`, `pytest`, `lifelines`.*

3.  **Verify Environment**:
    ```bash
    python -c "import pybullet; import torch; print('Environment OK')"
    ```

## Data Preparation

1.  **Download GFM Weights (Phase 0.1)**:
    The script `code/data/loader.py` will automatically download the GFM weights from the verified source `GFM-Bench/3D-Robotics` if `data/raw/gfm_weights.pt` is missing.
    ```bash
    python code/data/loader.py --download
    ```
    *This fetches weights from `https://huggingface.co/GFM-Bench/3D-Robotics`.*

2.  **Generate Synthetic Test Set (Phase 1)**:
    ```bash
    python code/data/generator.py --num-topologies 50 --seed 42
    ```
    *This creates `data/generated/topology_shift_set/`, verifies uniqueness, and generates `data/raw/gam_reference_stats.json`.*

3.  **Run Pilot Study (Phase 0.2)**:
    ```bash
    python code/eval/runner.py --method symbolic --trials 5 --pilot
    ```
    *This estimates solver latency to determine final trial count.*

## Running the Experiment

1.  **Execute Baseline & Symbolic Trials (Phase 2 & 3)**:
    ```bash
    python code/eval/runner.py --method symbolic --method baseline_gam --trials 50 --timeout 300
    ```
    *This runs both methods on the generated test set, enforcing timeouts and logging results to `data/results/trial_log.csv`.*

2.  **Run Statistical Analysis (Phase 3)**:
    ```bash
    python code/eval/stats.py --input data/results/trial_log.csv
    ```
    *This generates `data/results/stats_report.json` with p-values and effect sizes (Log-Rank/Wilcoxon for latency if censored).*

## Verification

1.  **Check Results**:
    ```bash
    cat data/results/stats_report.json
    ```
    *Verify `null_hypothesis_rejected` is True/False as expected.*

2.  **Check Gradient Logs**:
    ```bash
    cat data/results/gradient_flow_log.json
    ```
    *Verify `is_differentiable` is true for all entries.*

3.  **Run Tests**:
    ```bash
    pytest tests/ -v
    ```
    *Ensures all contract tests (schema validation) and unit tests pass.*

## Troubleshooting

-   **PyBullet Errors**: Ensure `libGLU.so` and `libGL` are installed (common on headless Linux).
-   **Timeout Failures**: If many trials time out, check `data/results/failure_report.json` for solver infeasibility.
-   **GPU Errors**: If `torch` tries to use CUDA, ensure `CUDA_VISIBLE_DEVICES=""` is set or `torch.device("cpu")` is used.
