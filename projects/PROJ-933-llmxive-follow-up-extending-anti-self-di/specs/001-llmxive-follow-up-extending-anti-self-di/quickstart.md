# Quickstart: llmXive follow-up: extending "Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information"

## Prerequisites
- Python 3.11+
- Git
- Access to Hugging Face Hub (for dataset download)

## Installation

1. **Clone the repository and navigate to the project directory:**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-933-llmxive-followup-extending-anti-self-di/code/
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Verify Dataset Access:**
   Ensure you can access the verified URLs. The script `data/download.py` will handle this.

## Running the Pipeline

The pipeline is orchestrated by `main.py`. It performs the following steps automatically:
1. **Data Download & Filter**: Downloads UltraFeedback, filters for ≥4 traces.
2. **Context Simulation**: Samples privileged contexts.
3. **Inference-Only Pass**: Computes teacher distributions.
4. **Training Loop**: Runs AntiSD and Standard SD training for a fixed number of steps.
5. **Analysis**: Computes metrics and statistical tests.

### Full Run (CPU)
```bash
python main.py --mode full --timeout [configured duration]
```
*Note: This will respect the timeout. If it exceeds, it logs partial results.*

### Run Specific Phase
- **Data Prep Only**: `python main.py --mode data_prep`
- **Training Only**: `python main.py --mode train --run_id <id>`
- **Analysis Only**: `python main.py --mode analyze --run_id <id>`

## Configuration

Edit `config/settings.yaml` to adjust:
- `seed`: Random seed for reproducibility.
- `max_steps`: Number of training steps (default 250).
- `model_name`: HuggingFace model ID (default `distilbert-base-uncased`).
- `deliberation_tokens`: List of tokens to track (default `["Wait", "However", "Let's think"]`).

## Output Locations

- **Raw Data**: `data/raw/`
- **Processed Data**: `data/processed/`
- **Training Logs**: `data/results/training_run_*.jsonl`
- **Final Report**: `data/results/analysis_results.json`

## Troubleshooting

- **OOM Error**: Reduce `max_steps` or switch to a smaller model (e.g., `TinyBERT`).
- **Dataset Empty**: If no prompts with ≥4 traces are found, the script will exit with a warning. Check `data/raw/audit_report.json`.
- **Timeout**: If the job is killed, check `data/results/partial_results.json`.
