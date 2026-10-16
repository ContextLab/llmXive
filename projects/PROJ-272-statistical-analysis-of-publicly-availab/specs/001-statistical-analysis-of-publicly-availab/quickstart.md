# Quickstart: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

## Prerequisites
- Python 3.11 or newer  
- Git  
- Internet access (to download the ADReSS embeddings from Hugging Face)

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd specs/001-statistical-cognitive-decline

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install the pinned dependencies
pip install -r requirements.txt

# 4. Install the spaCy English model (required by feature code)
python -m spacy download en_core_web_sm
```

## Running the Full Pipeline

```bash
# Step 1: Download and verify the ADReSS embeddings
python code/ingestion.py \
    --url https://huggingface.co/datasets/pruiu/ADReSS-IS2020_emb/resolve/main/IS2020_test_embeddings/dataset_info.json \
    --output data/raw/adress_embeddings.parquet

# Step 2: Create the cleaned interim CSV (includes empty text placeholder)
python code/ingestion.py \
    --create-cleaned \
    --input data/raw/adress_embeddings.parquet \
    --output data/interim/cleaned_adress.csv

# Step 3: Compute semantic similarity (the only available linguistic feature)
python code/features.py \
    --input data/interim/cleaned_adress.csv \
    --output data/processed/features.csv

# Step 4: Perform statistical hypothesis testing
python code/stats.py \
    --input data/processed/features.csv \
    --output data/processed/stats_results.json

# Step 5: Train and evaluate predictive models (covariates included if present)
python code/modeling.py \
    --input data/processed/features.csv \
    --output data/processed/model_results.json

# Optional: Run the whole workflow with a single command
python code/main.py
```

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
| `data/interim/cleaned_adress.csv` | Participant ID, label, empty `text` placeholder, and path to each embedding array. |
| `data/processed/features.csv` | Feature matrix (`sentence_embedding_cosine_similarity` plus `null` placeholders for omitted lexical/syntactic features). |
| `data/processed/stats_results.json` | Mann‑Whitney U statistics, Bonferroni‑adjusted p‑values, Cohen's d, and rank‑biserial effect sizes. |
| `data/processed/model_results.json` | Mean AUC, SD of AUC, accuracy, and F1‑score for LR and RF models (nested CV, covariates included). |
| `data/results/raw_record_count.json` | Total number of participants processed. |
| `data/results/group_counts.json` | Counts per cognitive status. |
| `data/results/metadata.json` | SHA‑256 checksums, timestamps, and data‑hygiene metadata. |

---

