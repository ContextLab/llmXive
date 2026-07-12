# Quickstart: Robotic AI Sensory Fidelity Ablation Study

## Prerequisites

- Python 3.11+
- 2+ CPU cores, 8GB+ RAM (for development), 7GB+ RAM (for CI).
- Docker (optional, for CARLA container).

## Installation

1.  **Clone and Setup**:
    ```bash
    git checkout 001-sensory-fidelity-ablation
    cd code
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import torch; print('PyTorch CPU:', torch.__version__)"
    python -c "import gymnasium; print('Gymnasium:', gymnasium.__version__)"
    ```

## Running the Baselines (US-1)

Execute the classical and stochastic baselines to establish performance bounds.

```bash
python scripts/run_baselines.py --seeds 30 --modality all
```
- **Output**: `results/baselines.csv` containing path optimality ratios and success rates.
- **Expected**: Pure Pursuit ≥ 80% success; Random ≤ 10% success.

## Generating Modalities (US-2)

Generate the three sensory representations from the simulation.

```bash
python scripts/generate_modalities.py --frames <variable> --output data/modalities/
```
- **Output**: `data/modalities/` containing RGB, Depth, and Grid tensors.
- **Validation**: Check `data/modalities/validation_report.json` for shape and alignment checks.

## Training and Analysis (US-3)

Train the DQN agents and perform statistical analysis.

```bash
python scripts/train_and_analyze.py --time-limit [configured-duration] --seeds 30
```
- **Time Limit**: 21600 seconds (6 hours).
- **Output**:
    - `results/training_curves.csv`: Learning curve data.
    - `results/statistical_report.json`: AUC, p-values, test type.
    - `results/resource_usage.json`: Peak RAM and CPU logs.

## Verification

Run the contract tests to ensure data integrity.

```bash
pytest tests/contract/ -v
```
