# Quickstart: llmXive cross‑lingual edge‑spectrum analysis

The following steps assume a fresh GitHub Actions runner or a local Linux environment with Python 3.11.

## 1. Clone the repository & set up environment
```bash
git clone https://github.com/yourorg/llmxive-crosslingual.git
cd llmxive-crosslingual
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Verify data integrity (optional but recommended)
```bash
python -m llmxive.utils.verify_checksums
# Computes SHA‑256 for any existing raw files and compares to stored metadata.
```

## 3. Run the full pipeline
```bash
python scripts/run_pipeline.py \
  --models llama3 mistral bloom \
  --k 100 \
  --token_guard 1000000 \
  --seed 42 \
  --iterations 5000 \
  --output_dir data/derived/
```
- `--models` names the three target checkpoints (downloaded automatically from HuggingFace).  
- `--k` sets the number of singular vectors (edge spectrum size).  
- `--token_guard` enforces the ≥ 1 M token requirement for frequency estimation.  
- `--iterations` sets the **minimum** number of permutation iterations (adaptive early‑stop may reduce this).  
- All intermediate artifacts are written under `data/derived/` and final JSON under the same directory.

## 4. Inspect the outputs
```bash
# Subspace similarity matrix with bootstrap CI
cat data/derived/edge_spectrum_similarity.json | jq .

# Token attribution for BLOOM
cat data/derived/token_attribution_bloom.json | head

# Permutation test result
cat data/derived/permutation_result.json | jq .

# Final aggregated report (conforms to contract)
cat data/derived/final_report.json | jq .
```

## 5. Run the test suite (CI‑style)
```bash
pytest -vv
```
The test suite checks:
- Contract validation against `contracts/edge_spectrum.schema.yaml`, `contracts/permutation_result.schema.yaml`, `contracts/token_attribution.schema.yaml`, and `contracts/similarity_report.schema.yaml`.
- Correct handling of missing or corrupted model files.
- Guard enforcement for token counts (≥ 1 M per language).

## 6. Reproduce figures for the paper
```bash
python -m llmxive.visualization.plot_subspace_similarity \
  --input data/derived/edge_spectrum_similarity.json \
  --output figures/subspace_similarity.png

python -m llmxive.visualization.plot_permutation_pvalue \
  --input data/derived/permutation_result.json \
  --output figures/permutation_pvalue.png
```

All commands are deterministic; re‑running the pipeline yields identical JSON and PNG files.
