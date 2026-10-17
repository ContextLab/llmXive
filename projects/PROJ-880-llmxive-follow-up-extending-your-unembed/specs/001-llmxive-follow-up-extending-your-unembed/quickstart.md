# Quickstart: llmXive cross‑lingual edge‑spectrum analysis

This guide reproduces the full pipeline on a standard GitHub Actions runner.

## Environment Setup
```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install pinned dependencies
pip install -r requirements.txt
```

## Run the Pipeline
The orchestrator `src/pipeline/run_all.py` executes all phases in order.

```bash
python -m src.pipeline.run_all \
    --models llama3 mistral bloom \
    --languages en fr zh ar sw de es hi ja pt \
    --top-k 100 \
    --bootstrap-replicates 1000 \
    --perm-iterations 10000 \
    --seed 42
```

### Guarded Behaviour
- **Token‑count guard**: For each language, the Common Crawl split is streamed via `datasets.load_dataset("common_crawl", name="<lang>")`. If the resulting token count is `< 1 000 000`, a `DataInsufficiencyError` is raised and processing for that language aborts (others continue).  
- **Permutation‑time guard**: If the permutation phase exceeds 5 hours, a warning is logged in `feasibility_report.json` and the run aborts (FR‑004).  
- **Memory guard**: Only the `lm_head` weights are loaded, keeping RAM ≤ 7 GB.

### Verification Timestamps
All external dataset downloads (Common Crawl language splits, WALS, SentEval) are logged with a verification timestamp in the generated `feasibility_report.json`. The URLs used are the **verified HuggingFace links** listed in the research.md Dataset Strategy table, satisfying SC‑008 and Constitution II.

### Pseudo‑inverse Diagnostics
During Phase 4 the condition number of $W_U$ is computed. If `cond(W_U) > 1e6`, the script automatically switches to ridge regularization (λ = 1e‑3) and records the chosen λ and condition number in `mean_embedding_{lang}_{hash}.json`.

## Expected Artifacts
All outputs appear under `data/derived/`:

- `edge_spectrum_{model}_{lang}_{hash}.json`  
- `frequency_list_{lang}_{hash}.json`  
- `token_attribution_{model}_{hash}.json`  
- `mean_embedding_{lang}_{hash}.json`  
- `similarity_matrix_{hash}.json`  
- `similarity_report_{hash}.json`  
- `permutation_test_{hash}.json`  
- `validation_{hash}.json`  
- `control_analysis_{hash}.json`  
- `ablation_report_{hash}.json`  
- `feasibility_report_{hash}.json`  
- `checksum_manifest_{hash}.json`

Each file is validated against its corresponding JSON‑Schema contract in `contracts/`.
