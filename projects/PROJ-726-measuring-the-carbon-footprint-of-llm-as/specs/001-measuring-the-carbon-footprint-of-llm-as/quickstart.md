# Quickstart: Measuring the Carbon Footprint of LLM‑Assisted Code Generation

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with sufficient RAM).

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llmXive/projects/PROJ-726-measuring-the-carbon-footprint-of-llm-as
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline is executed via a single entry point script that orchestrates all phases.

1. **Download Data**:
 ```bash
 python code/download_data.py
 ```
 *This fetches CodeXGLUE prompts and validates/synthesizes the human baseline JSON.*

2. **Run Inference (GPT-2-medium)**:
 ```bash
 python code/run_inference.py --model gpt2-medium
 ```
 *This runs the inference loop with CodeCarbon and saves results.*

3. **Calculate Baseline & Normalize**:
 ```bash
 python code/calculate_baseline.py
 python code/sensitivity_analysis.py
 python code/normalize_and_join.py
 ```

4. **Run Statistical Analysis**:
 ```bash
 python code/stats_analysis.py
 ```

5. **Generate Report**:
 ```bash
 python code/generate_report.py
 ```

6. **Robustness Check (DistilGPT-2)**:
 ```bash
 python code/run_inference.py --model distilgpt2
 python code/normalize_and_join.py --model distilgpt2
 python code/stats_analysis.py --model distilgpt2
 python code/generate_report.py --append-robustness
 ```

## Verifying Results

- Check `data/outputs/report.md` for the final summary, p-values, and plots.
- Verify `data/processed/paired_emissions.csv` for the joined data.
- Verify `data/processed/sensitivity_analysis.csv` for the stability analysis.
- Ensure `data/raw/` contains the checksummed raw datasets.

## Troubleshooting

- **Memory Error**: Reduce the batch size in `run_inference.py` or ensure no other heavy processes are running.
- **CodeCarbon Error**: Ensure the environment is CPU-only. If CUDA is detected, set `CUDA_VISIBLE_DEVICES=""`.
- **Missing Baseline**: The system will automatically synthesize a baseline using literature values if `data/raw/human_baseline_times.json` is missing. Check the log for the synthesis source.