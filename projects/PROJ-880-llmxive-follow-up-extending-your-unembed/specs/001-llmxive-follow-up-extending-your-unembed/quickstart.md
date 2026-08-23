# Quickstart: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

These instructions assume a fresh GitHub Actions runner (Ubuntu‑latest) or a local Linux environment with **≥ 7 GB RAM** and **Python 3.x**.

## 1. Clone the repository & set up the environment
```bash
git clone https://github.com/your-org/llmxive-crosslingual.git
cd llmxive-crosslingual
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions
```

## 2. Verify external dataset URLs (one‑time)
```bash
python -m src.utils.verify_urls \
    --url https://huggingface.co/datasets/Gopher-Lab/bankless_PREMIUM_Taiko__The_Future_of_Rollups__Justin_Drake_Brecht_Devos__Jeff_Walsh/resolve/main/data/train-00000-of-00001.parquet \
    --url https://huggingface.co/datasets/SetFit/SentEval-CR/resolve/main/test.jsonl \
    --url https://huggingface.co/datasets/PhilipMay/stsb_multi_mt/resolve/main/de/dev-00000-of-00001.parquet \
    --url https://huggingface.co/datasets/oscar/unshuffled_deduplicated_en \
    --url https://huggingface.co/datasets/oscar/unshuffled_deduplicated_fr \
    --url https://huggingface.co/datasets/oscar/unshuffled_deduplicated_zh \
    --url https://huggingface.co/datasets/oscar/unshuffled_deduplicated_ar \
    --url https://huggingface.co/datasets/oscar/unshuffled_deduplicated_sw \
    --url https://huggingface.co/datasets/oscar/unshuffled_deduplicated_de \
    --url https://huggingface.co/datasets/oscar/unshuffled_deduplicated_es \
    --url https://huggingface.co/datasets/oscar/unshuffled_deduplicated_hi \
    --url https://huggingface.co/datasets/oscar/unshuffled_deduplicated_ja \
    --url https://huggingface.co/datasets/oscar/unshuffled_deduplicated_pt
```
The script records SHA‑256 checksums and timestamps in `data/derived/checksums.json`.

## 3. Run the data loader verification (Phase 0.5)
```bash
python -m src.data_loader.run \
    --config config/common_crawl_urls.yaml \
    --output_dir data/derived
```
This streams each OSCAR split, counts tokens, enforces the ≥ 1 M token threshold, and writes `data/derived/token_count_guard.json`. If any language fails, the script aborts with a clear error.

## 4. Provide language‑filtered Common Crawl configuration
Create a YAML file `config/common_crawl_urls.yaml`:
```yaml
en: "https://huggingface.co/datasets/oscar/unshuffled_deduplicated_en"
fr: "https://huggingface.co/datasets/oscar/unshuffled_deduplicated_fr"
zh: "https://huggingface.co/datasets/oscar/unshuffled_deduplicated_zh"
ar: "https://huggingface.co/datasets/oscar/unshuffled_deduplicated_ar"
sw: "https://huggingface.co/datasets/oscar/unshuffled_deduplicated_sw"
de: "https://huggingface.co/datasets/oscar/unshuffled_deduplicated_de"
es: "https://huggingface.co/datasets/oscar/unshuffled_deduplicated_es"
hi: "https://huggingface.co/datasets/oscar/unshuffled_deduplicated_hi"
ja: "https://huggingface.co/datasets/oscar/unshuffled_deduplicated_ja"
pt: "https://huggingface.co/datasets/oscar/unshuffled_deduplicated_pt"
```
If this file is absent, the pipeline will stop with a clear error (see Constitution Check).

## 5. Run the full pipeline
```bash
python -m src.pipeline.run_all \
    --models llama series mistral bloom \
    --languages en fr zh ar sw de es hi ja pt \
    --top_k a large number of candidates \
    --bootstrap_iters <adequate number of iterations> \
    --perm_iters <sufficiently large iteration count> \
    --common_crawl_cfg config/common_crawl_urls.yaml
```
The command executes the phases in order, writes each artifact under `data/derived/`, and validates them against the contracts.

## 6. Inspect results
```bash
# List all generated artifacts
ls data/derived/

# Validate JSON against schemas (automated in CI, but you can run locally)
pytest -m "contract"
```

## 7. Language‑Projection artifacts
The pipeline also produces `language_projection_{model}_{lang}.json` files (one per model‑language pair). These conform to `contracts/language_projection.schema.yaml` and are used for the language‑projection similarity and validation steps.

## 8. Reproducibility audit
After the run completes, inspect `results/reproducibility_audit.json` which records the random seeds, checksum logs, and any warnings. This file satisfies Constitution Principle I.

## 9. Generate paper figures
The `src.pipeline.report` module reads `similarity_report.json` and `validation.json` and emits markdown tables and Matplotlib figures in `paper/figures/`. Include those figures directly in the manuscript; each caption cites the originating artifact ID.

---



