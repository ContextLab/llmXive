# Quickstart: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## Prerequisites
* Python 3.11+  
* Git  
* Internet access (to download the ADReSS embeddings)  

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd specs/001-statistical-cognitive-decline

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt

# 4. Install pre‑commit hooks (optional but recommended)
pre-commit install
```

## Running the Full Pipeline

```bash
# Step 1: Power analysis (primary combined contrast)
python code/power.py \
    --output data/results/power_analysis.txt \
    --primary-contrast combined

# Step 2: Download and verify ADReSS embeddings, create cleaned CSV
python code/ingestion.py \
    --download \
    --url https://huggingface.co/datasets/pruiu/ADReSS-IS2020_emb/resolve/main/IS2020_test_embeddings/dataset_info.json \
    --output data/raw/adress_embeddings.parquet

# Step 3: Create the interim cleaned CSV (includes empty text placeholder and sentence count)
python code/ingestion.py \
    --create-cleaned \
    --input data/raw/adress_embeddings.parquet \
    --output data/interim/cleaned_adress.csv

# Step 4: Compute semantic coherence (the only available linguistic feature)
python code/features.py \
    --input data/interim/cleaned_adress.csv \
    --output data/processed/features.csv

# Step 5: Perform ANCOVA, assumption checks, multicollinearity (VIF) check, and bootstrap η² CIs (with fallback permutation ANCOVA)
python code/stats.py \
    --input data/processed/features.csv \
    --output data/processed/ancova_results.json \
    --assumptions-out data/processed/assumptions.json

# Step 6: Generate the PDF statistical report (includes visualizations)
python code/main.py \
    --features data/processed/features.csv \
    --ancova data/processed/ancova_results.json \
    --assumptions data/processed/assumptions.json \
    --output data/results/statistical_report.pdf

# Optional: Run the entire workflow with a single command
python code/main.py
```

## Specification Amendment Notice
The original workflow assumed access to raw transcripts for lexical and syntactic analysis. Since the publicly available ADReSS dataset provides only embeddings, the pipeline now **conditionally** computes lexical and syntactic features if raw transcripts become available (as requested in the Specification Amendment). Until then, those columns are written as `null`.

## Verification

```bash
# Unit tests
pytest tests/unit/

# Contract validation (ensures CSV/JSON artifacts conform to schemas)
pytest tests/contract/

# End‑to‑end integration test (runs a miniature pipeline on a tiny sample)
pytest tests/integration/test_pipeline.py
```

## Expected Outputs

| Path | Description |
|------|-------------|
| `data/interim/cleaned_adress.csv` | Participant ID, label, empty `text` placeholder (or actual transcript if available), age, education, and path to each embedding. |
| `data/interim/exclusions.log` | Log of records omitted due to missing label or insufficient **sentence count** (< 5 sentences). |
| `data/results/raw_record_count.json` | Total number of participants before exclusions (now stored in `results`). |
| `data/results/group_counts.json` | Per‑group participant counts after exclusions (now stored in `results`). |
| `data/processed/features.csv` | Semantic coherence metric (`sentence_embedding_cosine_similarity`) plus Fisher‑z transformed `z_coherence`; lexical/syntactic fields are `null` unless raw transcripts are supplied. |
| `data/processed/ancova_results.json` | ANCOVA statistics, Bonferroni‑adjusted p‑values, partial η², and 95 % BCa CIs. |
| `data/processed/assumptions.json` | Results of Shapiro‑Wilk, homogeneity of slopes, linearity diagnostics, and VIF values. |
| `data/results/power_analysis.txt` | A‑priori power analysis for the ANCOVA models (primary combined contrast). |
| `data/results/metadata.json` | SHA‑256 checksums, timestamps, and data‑hygiene metadata. |
| `data/results/statistical_report.pdf` | Full PDF report with tables, boxplots, and effect‑size violin plot. |
| `logs/privacy_audit.log` | Log of the PII audit (should contain no detections). |

**Note:** Lexical and syntactic features are omitted because raw transcripts are not publicly available. A **spec amendment** is required to relax FR‑001 and FR‑002 if these features are desired; the pipeline will still produce a valid analysis of semantic coherence.

---
