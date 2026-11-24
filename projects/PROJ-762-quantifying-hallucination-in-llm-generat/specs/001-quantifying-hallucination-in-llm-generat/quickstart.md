# Quickstart: Quantifying Hallucination in LLM‑Generated API Documentation

## Prerequisites
- Python 3.11 or newer
- At least 7 GB free RAM
- Git
- Internet access (to download CodeSearchNet parquet files and model weights)

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-762-quantifying-hallucination-in-llm-generat

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Step‑by‑Step Run‑Book

### 1. Download the dataset
```bash
python code/download.py
```
*Output*: `data/raw/train.parquet` and `data/raw/test.parquet` (verified checksums).

### 2. Generate API descriptions (CPU‑only)
```bash
# CodeGen 350M
python code/generate.py --model codegen-350M --batch-size 1

# StarCoder 1B (4‑bit)
python code/generate.py --model starcoderbase-1b --batch-size 1
```
*Output*: `data/processed/records.csv` (includes both models, provenance, and all metrics).

### 3. Create the manual annotation template
```bash
python code/validate.py --generate-template --sample-ratio 0.05
```
*Output*: `data/manual/annotation_template.csv` (stratified on HallucinationIndex quartiles **and** token‑count deciles).

> **Human annotators** fill the `annotation_template.csv` and save it as `data/manual/scores.csv`.  

### 4. Collect human similarity ratings (semantic‑similarity validation)
```bash
python code/validate.py --semantic-sim-validation
```
*Output*: `data/manual/semantic_similarity_ratings.csv` containing human similarity scores and the Pearson r result (`semantic_validation_flag` recorded).

### 5. Run statistical analysis
```bash
python code/analyze.py
```
*Output*: `results/final_report.json` containing:
- Partial Spearman ρ and Bonferroni‑adjusted p‑values (per model)
- Multiple linear regression coefficients + 95 % CI (per model, source‑code predictors only)
- Sensitivity sweep table
- Manual validation correlation & flag
- Semantic‑similarity validation correlation & flag
- Model‑comparison table
- Disclaimer `"correlation observed"`

### 6. Validate performance against success criteria
```bash
python code/main.py --validate-performance
```
*Output*: `results/performance_log.json` with fields `max_memory_mb` and `total_time_sec`. The script asserts:
- `max_memory_mb < 7168`
- `total_time_sec < 14400` (4 h)

If any assertion fails, the CI job aborts, ensuring SC‑001 and SC‑002 are met.

### 7. Senior‑Reviewer Adjudication (if needed)
If the Krippendorff’s α < 0.7 **or** any validation flag is raised, run:
```bash
python code/validate.py --senior-review
```
This launches an interactive (or email‑based) adjudication step where the designated senior reviewer resolves discrepancies and produces an adjudicated manual score file.

## Expected Files

| Path | Description |
|------|-------------|
| `data/raw/*.parquet` | Original CodeSearchNet download (unchanged). |
| `data/processed/records.csv` | All computed metrics per function (FR‑001 – FR‑018). |
| `data/manual/annotation_template.csv` | Stratified template for human annotation (FR‑009). |
| `data/manual/scores.csv` | Human validation data (FR‑009, FR‑011, FR‑017). |
| `data/manual/semantic_similarity_ratings.csv` | Human semantic similarity ratings (FR‑020). |
| `results/final_report.json` | Consolidated analysis (FR‑007, FR‑010, SC‑003 – SC‑007). |
| `results/performance_log.json` | RAM & runtime diagnostics (SC‑001, SC‑002). |
| `results/power_analysis.json` | Documented power‑analysis results (SC‑001). |

## Troubleshooting

- **Out‑of‑Memory**: Reduce batch size to `1` (default) and ensure no other heavy processes run concurrently.
- **Model Load Errors**: Verify `torch` was installed with CPU support (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
- **Spacy Errors**: Run `python -m spacy download en_core_web_sm` again.
- **Missing docstrings**: Rows with `missing_docstring=True` are expected and will be omitted from analysis (see relevant documentation).
- **Low Krippendorff’s α**: Follow the senior‑reviewer step (FR‑017) to resolve inconsistencies.
- **Semantic‑Similarity Validation Failure**: If `semantic_validation_flag` is `"NEEDS_REVIEW"`, consider revising the SBERT model or collecting additional human ratings.

---

