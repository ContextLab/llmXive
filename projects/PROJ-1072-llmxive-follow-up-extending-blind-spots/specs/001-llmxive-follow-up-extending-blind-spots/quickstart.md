# Quickstart: llmXive follow-up: extending "Blind-Spots-Bench"

## Prerequisites

*   Python 3.11+
*   Git
*   Access to Hugging Face Hub (for dataset and model downloads)
*   (Optional) Hugging Face token for gated models (Llama-3)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: `datasets`, `transformers`, `sentence-transformers`, `scikit-learn`, `pandas`, `numpy`, `statsmodels`, `bitsandbytes` (for 4-bit quantization).*

## Running the Pipeline

The pipeline is orchestrated via `src/main.py`.

### Step 1: Data Acquisition & Filtering
Downloads the dataset and filters for "Abstract Reasoning" and "Object-Centric".
```bash
python src/main.py --step acquire
```
*Output*: `data/filtered/blind_spots_filtered.jsonl`

### Step 2: Pilot Study (Optional)
Runs a small pilot to validate the semantic matching threshold.
```bash
python src/main.py --step pilot
```
*Output*: `data/pilot/threshold.json`

### Step 3: CoT Generation
Generates traces using a 4-bit quantized LLM.
```bash
python src/main.py --step generate
```
*Note*: This step respects a timeout per task and a global limit. It will use CPU by default.

### Step 4: Parsing & Classification
Parses traces for constraint mentions and classifies errors.
```bash
python src/main.py --step parse
python src/main.py --step classify
```
*Output*: `data/classified/labels.jsonl`

### Step 5: Statistical Analysis
Runs the hypothesis test and generates the report.
```bash
python src/main.py --step stats
```
*Output*: `data/reports/statistical_report.json`

## Validation

### Unit Tests
Run the test suite to verify parser and classifier logic:
```bash
pytest tests/unit/
```

### Integration Test
Run a small-scale end-to-end test (a limited number of tasks):
```bash
python src/main.py --step full --sample-size 5
```

## Troubleshooting

*   **OOM Error**: If you encounter Out-Of-Memory errors, ensure `load_in_4bit=True` is set in `src/inference/generate.py`. If running on a local machine with < 7 GB RAM, consider reducing the batch size or using a smaller model.
*   **Dataset Integrity Error**: If the script halts with "Dataset Integrity Error", check `data/raw/` for missing `constraint` fields. This is a hard stop per FR-006.
*   **Timeout**: If tasks are timing out, the model may be too slow for the 10-minute limit on your hardware. The pipeline will log skipped tasks and continue.
