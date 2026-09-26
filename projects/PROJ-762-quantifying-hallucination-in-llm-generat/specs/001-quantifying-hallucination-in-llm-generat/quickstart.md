# Quickstart: Quantifying Hallucination in LLM-Generated API Documentation

## Prerequisites

- Python 3.11+
- Sufficient RAM available (for CPU inference)
- Significant disk space (for model weights and data)
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-762-quantifying-hallucination-in-llm-generat
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

## Running the Pipeline

### 1. Download Data
Fetch the CodeSearchNet Python subset.
```bash
python code/download.py
```
*Output*: `data/raw/train.parquet`

### 2. Generate Descriptions & Compute Metrics
Run the generation pipeline with pinned seeds.
```bash
python code/generate.py --model codegen-350M --batch-size 1
python code/generate.py --model starcoderbase-1b --batch-size 1
```
*Output*: `data/processed/records.csv` (contains F1 scores and decomposed metrics)

### 3. Manual Validation (Annotation Interface)
Generate the annotation template for human input.
```bash
python code/validate.py --generate-template --sample-ratio 0.05
```
*Output*: `data/manual/annotation_template.csv`

*Note: In a real research run, humans fill this template. For CI testing, use `--simulate` to generate placeholder scores, but these will be flagged in the final report.*
```bash
python code/validate.py --simulate --sample-ratio 0.05
```
*Output*: `data/manual/scores.csv` (placeholder or real data)

### 4. Statistical Analysis
Run correlation, regression, and sensitivity analysis.
```bash
python code/analyze.py
```
*Output*: `results/final_report.json`

### 5. Performance Validation (Success Criteria Check)
Verify memory and time limits.
```bash
python code/main.py --validate-performance
```
*Expected*: `results/performance_log.json` containing `max_memory_mb < 7168` and `total_time_sec < 21600`.

## Expected Output

The final `results/final_report.json` will contain:
- Correlation coefficients and adjusted p-values.
- Regression coefficients (controlled for source length).
- VIF scores.
- Sensitivity analysis table.
- Validation flag (PASS/NEEDS_REVIEW).

## Troubleshooting

- **OOM Error**: Reduce `--batch-size` to 1. Ensure no other heavy processes are running.
- **Model Load Error**: Ensure `transformers` and `torch` are installed with CPU support (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
- **Spacy Error**: Run `python -m spacy download en_core_web_sm`.