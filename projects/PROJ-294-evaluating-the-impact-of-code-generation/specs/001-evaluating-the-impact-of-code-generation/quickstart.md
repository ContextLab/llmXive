# Quickstart: Evaluating the Impact of Code Generation Models on Code Testability

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace (for model download)
- (Optional) Kaggle account for GPU offloading (if CPU fails)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd specs/294-evaluating-the-impact-of-code-generation
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

## Running the Pipeline

The pipeline is executed in stages. Each stage produces artifacts that are used by the next.

### Stage 1: Data Acquisition
```bash
python code/download_data.py
```
- Downloads HumanEval dataset.
- Verifies SHA256 checksum.
- Saves to `data/raw/humaneval.parquet`.

### Stage 2: Human Reference Extraction
```bash
python code/extract_human_reference.py
```
- Extracts human solutions from the raw dataset.
- Saves to `data/generated/human_samples.json`.

### Stage 3: Code Generation
```bash
python code/generate_code.py --model primary
python code/generate_code.py --model sensitivity
```
- Generates code using the specified model.
- Applies timeout and retry logic.
- Saves to `data/generated/codegen_samples.json` and `data/generated/sensitivity_samples.json`.

### Stage 4: Metric Analysis
```bash
python code/analyze_metrics.py
```
- Computes structural metrics.
- Executes test suites.
- Filters valid tasks.
- Saves to `data/analysis/metrics.json` and `data/analysis/valid_task_ids.json`.

### Stage 5: Statistical Analysis
```bash
python code/stats_analysis.py
```
- Performs Wilcoxon Signed-Rank test.
- Calculates MDES.
- Saves to `data/analysis/statistical_results.json`.

### Stage 6: Report Generation
```bash
python code/report_generator.py
```
- Generates `report.md` with figures.
- Validates citations.
- Updates `artifact_hashes.yaml`.

## Verification

1. **Check artifacts**:
   ```bash
   ls -l data/raw/ data/generated/ data/analysis/
   ```
   Ensure all expected files are present.

2. **Verify hashes**:
   ```bash
   python code/utils/hash_utils.py --verify
   ```
   Ensure all hashes match.

3. **Run tests**:
   ```bash
   pytest tests/
   ```

## Troubleshooting

- **OOM Error**: If the model fails to load due to memory, the script will attempt to offload to a Kaggle GPU. Ensure you have a Kaggle account and set the `KAGGLE_USERNAME` and `KAGGLE_KEY` environment variables.
- **Timeout**: If generation times out, check the `code/errors.log` for details. The script implements exponential backoff.
- **Citation Validation Failure**: If citation validation fails, check the `report.md` for broken links or mismatched titles.
