# Quickstart: llmXive follow-up: extending "Agents' Last Exam"

## Prerequisites

- Python 3.11+
- GB+ RAM (for 7B model Q4_K_M)
- CPU cores (GitHub Actions free-tier compatible)
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-840-llmxive-follow-up-extending-agents-last
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   *Note: `requirements.txt` pins versions compatible with CPU-only execution and `llama-cpp-python`.*

## Data Setup

1. **Generate Synthetic ALE Dataset**:
   The dataset is generated locally by `code/data/generator.py` from verified internal logic:
   - `data/raw/synthetic_ale.jsonl`

   To run manually:
   ```bash
   python code/data/generator.py --seed 42 --num-tasks a sufficient batch size
   ```

2. **Verify checksums**:
   ```bash
   python code/utils/verify_checksums.py
   ```

## Running the Classification (Phase 1)

1. **Parse and classify logs**:
   ```bash
   python code/classification/parser.py --input data/raw/synthetic_ale.jsonl --output data/processed/classified_traces.json
   ```

2. **Validate reconstruction accuracy** (using golden set):
   ```bash
   python code/classification/validator.py --input data/processed/classified_traces.json --golden data/raw/golden_set.json
   ```
   *Expected output: Reconstruction accuracy ≥ 95%.*

## Running the Experiment (Phase 2)

1. **Download 7B Model (GGUF Q4_K_M)**:
   Ensure `llama-3-8b-instruct.Q4_K_M.gguf` is in `models/`.
   *Note: This model is required. No 3B fallback is supported.*

2. **Run baseline (no checkpointing)**:
   ```bash
   python code/intervention/runner.py --condition baseline --model models/llama-3-8b-instruct.Q4_K_M.gguf --seed 42 --output data/processed/baseline_results.json
   ```

3. **Run intervention (checkpointing, N=3)**:
   ```bash
   python code/intervention/runner.py --condition intervention --checkpoint-interval 3 --model models/llama-3-8b-instruct.Q4_K_M.gguf --seed 42 --output data/processed/intervention_results.json
   ```

   *Note: If the 7B model fails to load or exceeds memory, the script will exit with "Hardware Infeasible".*

## Running the Analysis (Phase 3)

1. **Statistical significance test (GLMM)**:
   ```bash
   python code/analysis/stats.py --baseline data/processed/baseline_results.json --intervention data/processed/intervention_results.json --output data/processed/stats_report.json
   ```

2. **Sensitivity analysis (N=1, 3, 5)**:
   ```bash
   python code/analysis/sensitivity.py --results data/processed/experiment_results.json --intervals,3,5 --output data/processed/sensitivity_analysis.json
   ```

## Generating the Report

1. **Compile final report**:
   ```bash
   python code/utils/generate_report.py --stats data/processed/stats_report.json --sensitivity data/processed/sensitivity_analysis.json --output docs/report.md
   ```

## Testing

1. **Run unit tests**:
   ```bash
   pytest tests/unit/ -v
   ```

2. **Run integration tests (golden set)**:
   ```bash
   pytest tests/integration/ -v
   ```

3. **Run contract tests (schema validation)**:
   ```bash
   pytest tests/contract/ -v
   ```

## Troubleshooting

- **Memory Error**: If the 7B model fails to load, the script will exit with "Hardware Infeasible". Ensure you are using the Q4_K_M GGUF file. No fallback to 3B is available.
- **Data Missing**: If synthetic generation fails, check `code/data/generator.py` for seed errors.
- **Statistical Error**: If N < 80, the report will include a power limitation warning.