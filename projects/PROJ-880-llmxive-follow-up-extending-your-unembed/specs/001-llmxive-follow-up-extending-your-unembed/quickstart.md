# Quickstart: llmXive follow-up – Edge Spectrum Cross‑Lingual Analysis

This guide walks a new researcher from a fresh GitHub Actions runner to a complete set of results.

## 1. Clone & Setup
```bash
git clone
cd llmxive-crosslingual
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## 2. Run the Full Pipeline
```bash
python -m src.cli run-all \
 --models llama3 mistral \
 --languages en fr de es zh \
 --adapters llama3-fr llama3-de llama3-es mistral-fr \
 --top_k 100 \
 --perm_iters 1000 \
 --seed 42
```
The command performs:
1. **Data download & token‑count guard** (fails if < 1 M tokens).
 The guard creates `data/processed/token_count_guard.json` and aborts with a clear error if the threshold is not met.
2. **Edge‑spectrum extraction** for each base model **and** language‑specific adapters (same architecture across languages). BLOOM is loaded in 8‑bit mode for an exploratory check only.
3. **Subspace similarity matrix** generation.
4. **Token attribution** and vocabulary mapping (shared vocab size = 11200).
5. **Frequency‑based mean‑embedding** projection.
6. **External validation** (WALS PCA, SentEval STS).
7. **Permutation test** with architecture‑controlled nulls.
All outputs are written under `data/results/`.

## 3. Inspect Results
```bash
cat data/results/edge_similarity.json | jq.
cat data/results/token_attribution_llama3_en.json | jq.
cat data/results/permutation_test.json | jq.
```

## 4. Re‑run Individual Steps (optional)
| Step | CLI flag | Description |
|------|----------|-------------|
| Data download only | `--stage download` | Pull raw datasets, verify checksums, enforce token‑count guard, and generate `results/reproducibility_audit.json`. |
| Edge spectrum only | `--stage edge` | Skip downstream validation. |
| Validation only | `--stage validate` | Assumes `edge_spectrum` already exists. |

## 5. Testing
```bash
pytest -q
```
All contract tests must pass (`contracts/*.schema.yaml`).

## 6. Reproducibility Checklist
- Seed fixed (`--seed 42`).
- All URLs are hard‑coded in `src/data_loader.py`.
- Checksums recorded in `state/projects/PROJ-880-llmxive-follow-up-extending-your-unembed.yaml`.
- No manual file edits required.
- The SSoT manifest `state/projects/PROJ-880-llmxive-follow-up-extending-your-unembed.yaml` is the authoritative source for all figures and tables.
- `results/reproducibility_audit.json` contains a machine‑readable summary of dataset checksums, random seeds, and runtime metadata for full auditability.

---



