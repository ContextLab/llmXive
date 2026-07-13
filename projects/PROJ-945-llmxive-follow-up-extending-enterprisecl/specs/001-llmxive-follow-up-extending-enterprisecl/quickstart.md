# Quickstart: llmXive Follow-up: Extending EnterpriseClawBench

## 1. Prerequisites

- **Python**: 3.11+
- **System**: Linux (compatible with GitHub Actions Free Runner).
- **Data**: `EnterpriseClawBench` dataset files (must be provided locally as no verified URL exists).

## 2. Installation

1. **Clone the repository** and navigate to the project directory:
   ```bash
   cd projects/PROJ-945-llmxive-follow-up-extending-enterprisecl
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## 3. Data Setup

Since EnterpriseClawBench has no verified public URL, you must provide the data locally.

### Local Data Schema Requirement
The dataset **MUST** be a JSON file (or list of JSON objects) with the following structure:
```json
{
  "trace_id": "unique_id",
  "task_id": "task_001",
  "status": "failed",
  "paired_trace_id": "unique_id_of_success_trace",
  "raw_log_content": "...",
  "outcome_label": "failed"
}
```
**Critical**: If `status` is "failed", `paired_trace_id` **MUST** be present and point to a valid successful trace. If missing, the pipeline will halt.

### Setup Steps

1. **Create the data directory**:
   ```bash
   mkdir -p data/raw
   ```

2. **Place your dataset files** in `data/raw/`. Ensure they are checksummed:
   ```bash
   sha256sum data/raw/your_dataset_file.json > data/raw/your_dataset_file.json.sha256
   ```

3. **Create the -task Lite set**:
   ```bash
   mkdir -p data/lite_set
   # Manually select or script the selection of 120 tasks for the held-out set
   ```

4. **Update the configuration** (if applicable) to point to the local path.

## 4. Running the Pipeline

Execute the full pipeline (Extraction -> Training -> Evaluation):

```bash
python code/run_pipeline.sh
```

### Step-by-Step Execution

1. **Feature Extraction**:
   ```bash
   python code/src/extractors/extract_features.py --input data/raw/ --output data/processed/features.json
   ```
   *Verifies*: Syntax tree depth, token frequency, pragmatic markers. **Halts if parser fails.**

2. **Oracle Labeling**:
   ```bash
   python code/src/oracle/apply_oracle.py --input data/processed/features.json --output data/processed/triplets.json
   ```
   *Verifies*: Correctable vs. Unfixable labels. **Halts if paired_trace_id is missing for failed traces.**

3. **Model Training**:
   ```bash
   python code/src/models/train_classifier.py --input data/processed/triplets.json --output code/models/classifier.pkl
   ```
   *Verifies*: Convergence, memory usage (FR-006).

4. **Evaluation**:
   ```bash
   python code/src/evaluation/run_eval.py --model code/models/classifier.pkl --lite-set data/lite_set/
   ```
   *Verifies*: ADS comparison, statistical significance (FR-005).

## 5. Verification

- **Check Logs**: Review `logs/memory_usage.log` to ensure peak RAM < 7GB.
- **Check Results**: Review `data/results/final_report.json` for statistical significance (p-value).
- **Unit Tests**: Run `pytest tests/unit/` to verify feature extraction logic.

## 6. Troubleshooting

- **OOM Error**: Reduce the batch size in `code/src/models/train_classifier.py` or enable chunking in `extract_features.py`.
- **Data Missing**: If `data/raw/` is empty or `paired_trace_id` is missing, the pipeline will halt. Ensure the dataset is provided locally and conforms to the schema.
- **Model Divergence**: If training loss does not converge, check the fallback heuristic model logs.
- **Parser Failure**: If logs are not in the expected format, the pipeline halts at Phase 1.