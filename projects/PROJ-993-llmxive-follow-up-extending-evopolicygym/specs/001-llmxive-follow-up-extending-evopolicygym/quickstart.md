# Quickstart: llmXive follow-up: extending "EvoPolicyGym: Evaluating Autonomous Policy Evolution in Interactive En"

## Prerequisites

*   Python 3.11+
*   Git
*   Access to the `gymnasium` repository (public URL).

## Installation

1.  **Clone the Project**:
    ```bash
    git clone <repo-url>
    cd <repo-name>
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins `transformers`, `gymnasium`, `statsmodels`, `radon`, `pandas`.*

## Configuration

Edit `code/utils/config.yaml` to set:
*   `seeds`: List of random seeds (e.g., `[42, 123, 456, 789, 1011]`).
*   `runs_per_seed`: Number of evolutionary runs per seed.
*   `condition`: "baseline" or "counterfactual" (or run both).
*   `shift_threshold`: Default 0.5.
*   `llm_model`: Model name (e.g., "microsoft/phi-2" for CPU).

## Running the Pipeline

### 1. Run the Full Evolutionary Harness
Execute the main CLI entry point:
```bash
python code/main.py --run-evolution --seeds 42,123,456,789,1011 --runs 5 --envs all --conditions baseline,counterfactual
```
*   This will:
    *   Initialize the discovered environments (targeting up to 16).
    *   Run the evolutionary algorithm for both conditions.
    *   Generate counterfactual explanations (with fallbacks).
    *   Save raw trajectories and policies to `data/raw/`.

### 2. Analyze Results
Once the evolution is complete, run the analysis pipeline:
```bash
python code/main.py --analyze --input data/raw --output data/final
```
*   This will:
    *   Calculate complexity metrics using `radon`.
    *   Compute generalization scores.
    *   Parse `fallbacks.log` for success rates.
    *   Run the mixed-effects model.
    *   Output `data/final/stats_results.json`.

### 3. Verify Outputs
Check the generated artifacts:
*   `data/processed/evolution_results.csv`: Contains scores and complexity metrics.
*   `data/final/stats_results.json`: Contains the p-value, effect size, and explanation success rate.

## Troubleshooting

*   **LLM Timeout**: If the LLM fails to generate an explanation within 30s, the system will automatically use the fallback template. Check `data/processed/fallbacks.log` for counts.
*   **Memory Error**: If running on the GitHub Actions runner, ensure the LLM is loaded in 8-bit mode. If it still fails, the system will switch to the `TinyLlama-1.1B` fallback or template fallback.
*   **Environment Count Mismatch**: If the upstream `gymnasium` repo count changes, the script will log a warning but proceed (no hard fail) to ensure robustness.

## Expected Output

*   `data/final/stats_results.json`:
    ```json
    {
      "p_value": 0.032,
      "effect_size": 0.45,
      "significant": true,
      "explanation_success_rate": 0.92,
      "method": "mixed_effects"
    }
    ```