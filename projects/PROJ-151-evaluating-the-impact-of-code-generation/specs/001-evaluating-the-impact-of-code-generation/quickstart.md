# Quickstart: Evaluating the Impact of Code Generation Models on Code Review Efficiency

## Prerequisites

- Python 3.11+  
- ≥ 7 GB RAM (required for optional StarCoder‑1B loading)  
- Internet access (for GHTorrent download or HuggingFace access)  
- **Note**: This pipeline requires access to the GHTorrent Gerrit Chromium dataset. If unavailable, the script will halt and generate a Spec Amendment Request to use the verified HuggingFace proxy.

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-151-evaluating-the-impact-of-code-generation
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Pipeline

### 1. Data Ingestion
```bash
python code/ingestion.py --output data/processed/prs_filtered.csv
```
*Checks*: ≥ 1,000 rows; `review_time_seconds` may be null; `comment_count` must be non‑null.
*Gate*: If GHTorrent is inaccessible, the script exits and prints "SPEC AMENDMENT REQUIRED" (to switch to HuggingFace proxy).

### 2. Code Generation
```bash
python code/generation.py --input data/processed/prs_filtered.csv \
    --models starcoder1b codegen350m
```
*Behavior*: 
1. Reconstructs full problem context from PR diffs.
2. Performs a RAM check; if StarCoder‑1B would exceed 5 GB, it is skipped and only CodeGen‑350M runs.
3. Generates code with the context-augmented prompt.
4. Applies **Semantic Validity Filter** (syntax + triviality + semantic logic check).
5. Generates `data/generated/snippets/` and `data/generated_provenance.csv`. Failures are recorded with `status = "invalid_syntax"`, `"trivial"`, or `"semantic_failure"`.

### 3. Metrics Computation
```bash
python code/metrics.py --input data/processed/prs_filtered.csv \
    --generated data/generated/snippets
```
*Output*: `data/metrics/all_metrics.csv` (includes `status` field and language-specific scores: `pylint` for Python, `checkstyle` for Java).

### 4. Statistical Analysis
```bash
python code/analysis.py --metrics data/metrics/all_metrics.csv
```
*Outputs*: `data/models/lmm_results.json` containing mixed‑effects coefficients, Bonferroni‑adjusted p‑values, sensitivity tables, residual diagnostics, **Proxy Attenuation Correction** details, and **Transfer Estimation** results.

### 5. Validation Study (Manual Step)
1. Randomly select ≥ 50 `status = "valid"` generated snippets.
2. Distribute them **and a matched set of human snippets** (same problem_statement) to ≥ 2 independent reviewers.
3. Collect `review_time_seconds`, `comment_count`, and 5‑point difficulty ratings in `data/validation/survey_results.csv`.
4. Run:
   ```bash
   python code/validation.py --survey data/validation/survey_results.csv
   ```
   Produces `data/models/validation_results.csv` with Pearson r, Wilcoxon test, and **Systematic Bias Analysis** (mean residual difference).

## Reproducibility

- All random operations use `seed=42`.
- Dataset checksum stored under `data/`.
- No manual edits required; the pipeline is end‑to‑end runnable on a fresh GitHub Actions runner (provided GHTorrent or the verified HuggingFace proxy is accessible).
