# Quickstart: llmXive follow-up: extending "Qwen-Image-Agent"

## Prerequisites

-   Python 3.11+
-   Git
-   Access to Hugging Face (for dataset download)
-   (Optional) Kaggle account (for GPU offload if running locally)

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note*: This installs `spacy`, `nltk`, `torch`, `transformers`, `scikit-learn`, `datasets`, `matplotlib`, `diffusers`.

3.  **Download Models**:
    ```bash
    python -m spacy download en_core_web_sm
    # CLIP, ResNet, and SDXL models will be downloaded automatically on first run
    ```

## Running the Pipeline

### 1. Data Download
Download the raw datasets to `data/raw/`:
```bash
python src/pipeline/download_data.py
```
*Output*: `data/raw/ia_bench_prompts.parquet`, `data/raw/laion_cc_prompts.parquet`.

### 2. Run Pilot Study (Phase 0)
Execute the pilot to validate scoring weights and freeze normalization:
```bash
python src/pilot/study_runner.py
```
*Output*: `data/processed/pilot_results.json`, `data/processed/normalization_params.json`.

### 3. Compute Complexity Scores
Calculate syntactic metrics for all prompts (using frozen params):
```bash
python src/pipeline/run_scoring.py
```
*Output*: `data/processed/complexity_scores.csv`.

### 4. Execute Hybrid Routing & Generation
Run the routing logic and generate **paired** images.
*Note*: This requires GPU access (Kaggle offload).
```bash
python src/pipeline/run_routing.py --paired-sample
```
*Output*: `data/processed/routing_logs.json`, `data/processed/generated_images/`.

### 5. Evaluate Fidelity
Compute CLIP scores and perform regression analysis:
```bash
python src/pipeline/run_fidelity_analysis.py
```
*Output*: `data/results/fidelity_metrics.csv`, `data/results/regression_stats.json`, `data/results/plots/fidelity_delta_curve.png`.

## Verification

Run the test suite to ensure integrity:
```bash
pytest tests/ -v
```

## Troubleshooting

-   **Memory Error**: If CLIP inference fails, reduce `BATCH_SIZE` in `config.yaml`.
-   **CUDA Not Found**: If the agent execution fails on CPU, the system will log a warning and trigger the Kaggle offload. Ensure the offload mechanism is active for full runs.
-   **Data Missing**: Re-run `download_data.py` to ensure checksums match.
