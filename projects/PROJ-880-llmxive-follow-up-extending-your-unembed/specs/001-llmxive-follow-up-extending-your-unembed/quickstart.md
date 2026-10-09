# Quickstart: llmXive cross-lingual edge-spectrum analysis

This guide enables the reproduction of the cross‑lingual subspace analysis on a GitHub Actions runner.

## Environment Setup
```bash
# 1. Setup virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install pinned dependencies
pip install -r requirements.txt
```

## Running the Pipeline
The pipeline is orchestrated by `src/pipeline/run_all.py`. It handles data acquisition, SVD, and statistical validation in sequence.

```bash
python -m src.pipeline.run_all \
    --models llama3 mistral bloom \
    --languages en fr zh ar sw de es hi ja pt \
    --top-k 100 \
    --bootstrap-replicates 1000 \
    --perm-iterations 10000 \
    --seed 42
```

## Key Guards & Behavior
- **Data Guard**: If any Common Crawl language subset contains $< 1{,}000{,}000$ tokens, the pipeline will raise a `DataInsufficiencyError` and abort.
- **Time Guard**: If the permutation phase exceeds 5 hours, the system will log a warning to `feasibility_report.json` and abort to prevent CI timeout.
- **Memory Guard**: The system loads only the `lm_head` weights from the models to fit within the 7 GB RAM limit.

## Expected Artifacts
- `edge_spectrum_{model}_{lang}_{hash}.json` (subspace bases)
- `frequency_list_{lang}_{hash}.json` (token frequency distributions)
- `token_attribution_{model}_{hash}.json` (top‑logit tokens)
- `mean_embedding_{lang}_{hash}.json` (mean embeddings and baselines)
- `similarity_matrix_{hash}.json` (pairwise cosine similarity matrix with bootstrap CIs)
- `similarity_report_{hash}.json` (detailed similarity metrics)
- `permutation_test_{hash}.json` (combined p‑values and significance flag)
- `validation_{hash}.json` (WALS and SentEval correlations)
- `ablation_report_{hash}.json` (ablation outcomes)
- `feasibility_report_{hash}.json` (resource usage)

All artifacts are validated against their JSON‑Schema contracts (see `contracts/`). 
