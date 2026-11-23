# Quickstart: llmXive follow-up: extending "InterleaveThinker: Reinforcing Agentic Interleaved Generation"

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a GitHub Actions runner (or local environment with 16GB+ RAM)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-916-llmxive-follow-up-extending-interleaveth/code/
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Set random seeds**:
    Ensure `PYTHONHASHSEED` and `RANDOM_SEED` are set in your environment or `.env` file for reproducibility.
    ```bash
    export PYTHONHASHSEED=42
    export RANDOM_SEED=42
    ```

2.  **Configure dataset paths**:
    Update `config.yaml` (if present) or environment variables to point to the correct dataset directories. The `datasets` library will handle downloading from verified sources automatically.

## Running the Experiment

### 1. Run the Simulator (Perfect Mode)

```bash
python -m src.simulator --mode perfect --dataset visual_genome --output data/intermediate/scenes_perfect.jsonl
```

### 2. Run the Simulator (Noisy Mode)

```bash
python -m src.simulator --mode noisy --target_error_rate 0.10 --dataset visual_genome --output data/intermediate/scenes_noisy.jsonl
```

### 3. Validate Simulator Output

```bash
python -m src.simulator.validate --input data/intermediate/scenes_noisy.jsonl --ground_truth data/raw/visual_genome_scene_graphs.jsonl --output data/simulator_validation/error_report.json
```

### 4. Execute the Agentic Pipeline

```bash
python -m src.pipeline.run --scenes data/intermediate/scenes_noisy.jsonl --thresholds 0.7,0.8,0.9 --output data/intermediate/trajectories.jsonl
```

### 5. Run Ablation Study (No-Critic)

```bash
python -m src.pipeline.run --scenes data/intermediate/scenes_noisy.jsonl --ablation no_critic --output data/intermediate/trajectories_ablation.jsonl
```

### 6. Perform Statistical Analysis

```bash
python -m src.stats.analyze --full data/intermediate/trajectories.jsonl --ablation data/intermediate/trajectories_ablation.jsonl --output stats/results.json
```

### 7. Generate Report

```bash
python -m src.stats.report --input stats/results.json --output docs/statistical_significance_report.md
```

## Verification

*   **Simulator**: Check `data/simulator_validation/error_report.json` for `simulator_error_rate` (Graph Edit Distance) within the 5-15% target range.
*   **Pipeline**: Ensure `data/intermediate/trajectories.jsonl` contains valid `ReasoningScore` for each sample.
*   **Statistics**: Verify `docs/statistical_significance_report.md` contains p-values and effect sizes.

## Troubleshooting

*   **OOM Errors**: If you encounter memory errors, reduce the batch size in `config.yaml` or use a smaller model variant.
*   **Dataset Download Failures**: Ensure you have internet access and that the verified URLs are reachable. The `datasets` library will retry automatically.
*   **Critic Threshold Sensitivity**: If the Critic triggers too many re-plans, adjust the threshold in the `--thresholds` argument.