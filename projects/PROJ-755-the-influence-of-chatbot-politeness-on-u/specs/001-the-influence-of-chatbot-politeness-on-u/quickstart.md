# Quickstart: The Influence of Chatbot Politeness on User-Perceived Quality

## Prerequisites

- Python 3.11+
- R 4.3+ (with `lme4`, `ordinal`, `dplyr` packages)
- Git
- Access to Hugging Face Hub (optional, for datasets)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd <project-dir>
    ```

2.  **Create virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install R dependencies** (if not using system R):
    ```r
    install.packages(c("lme4", "ordinal", "dplyr", "tidyr"))
    ```

5.  **Set environment variables**:
    Copy `.env.example` to `.env` and add your `HF_TOKEN` if required for private datasets (though we use public ones).
    ```bash
    cp .env.example .env
    # Edit .env to add HF_TOKEN=your_token
    ```

## Running the Pipeline

### 1. Download and Validate Data
```bash
python code/data/download_datasets.py
python code/data/validate_data.py
```
*Outputs: `data/raw/*.parquet`, `data/processed/validation_log.txt`*

### 2. Score Politeness
```bash
python code/data/score_politeness.py
```
*Outputs: `data/processed/dialogues_scored.csv`*

### 3. Run CLMM Analysis
```bash
python code/analysis/run_clmm.py
```
*Outputs: `data/processed/model_results.csv`, `data/processed/figures/`*

### 4. Robustness Check
```bash
python code/analysis/robustness_check.py
```
*Outputs: `data/processed/robustness_results.csv`*

### 5. Subgroup Analysis (if applicable)
```bash
python code/analysis/subgroup_analysis.py
```
*Outputs: `data/processed/subgroup_results.csv`*

## Verification

Run the test suite:
```bash
pytest tests/
```

Run schema validation:
```bash
python code/utils/schema_validator.py --input data/processed/dialogues_merged.csv --schema contracts/dataset.schema.yaml
```

## Troubleshooting

- **OOM Error**: If `score_politeness.py` fails due to memory, reduce `BATCH_SIZE` in `code/data/score_politeness.py` or enable the GPU escape hatch.
- **R Package Missing**: Ensure R is installed and packages are in the library path.
- **Dataset Not Found**: Check `code/data/download_datasets.py` for updated Hugging Face IDs.
