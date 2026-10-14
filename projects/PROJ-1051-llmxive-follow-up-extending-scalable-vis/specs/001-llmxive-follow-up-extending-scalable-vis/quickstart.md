# Quickstart: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

This guide walks a fresh GitHub Actions runner through the complete end‑to‑end pipeline.

## 1. Setup Environment
```bash
# Create a fresh virtualenv (GitHub Actions does this automatically)
python -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r code/requirements.txt
```

## 2. Verify Data Availability
```bash
python -m src.data.download \
    --dataset-name publaynet \
    --output-dir data/raw
```
*Downloads the verified PubLayNet dataset from the URL listed in the “# Verified datasets” block. If the download fails, the script exits with a clear error message.*

## 3. Preprocess Documents
```bash
python -m src.data.preprocess \
    --input-dir data/raw/publaynet \
    --output-parquet data/processed/document_pairs.parquet \
    --schema contracts/documentpair.schema.yaml
```
*Extracts OCR text (using Tesseract), loads the provided layout annotations, validates each record against the schema, and writes a Parquet file. Any validation failure aborts the run with a detailed log.*

## 4. Generate Visual Latents (CPU‑only)
```bash
python -m src.data.latent_generator \
    --input-parquet data/processed/document_pairs.parquet \
    --output-parquet data/processed/document_pairs_with_latent.parquet \
    --encoder-name layoutlmv3-base \
    --device cpu
```
*If the encoder cannot be loaded on CPU, the script exits with an informative error (edge‑case handling).*

## 5. Create Consistent Train/Val/Test Splits
```bash
python -m src.utils.split_generator \
    --input-parquet data/processed/document_pairs_with_latent.parquet \
    --output-dir data/splits \
    --seed 42 \
    --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1
```
*Generates `train_idx.json`, `val_idx.json`, `test_idx.json` used by both distilled and baseline training scripts.*

## 6. Train Distilled Model (30 seeds)
```bash
for SEED in {42..71}; do
  python -m src.models.distilled \
      --data-parquet data/processed/document_pairs_with_latent.parquet \
      --splits-dir data/splits \
      --seed $SEED \
      --output-dir artifacts/models/distilled_$SEED \
      --max-epochs 5 \
      --batch-size 16
done
```
*Training respects the RAM ceiling; batch size auto‑reduces on OOM detection.*

## 7. Train Baseline Models (30 seeds, padded input)
```bash
for SEED in {42..71}; do
  python -m src.models.baseline \
      --data-parquet data/processed/document_pairs.parquet \
      --splits-dir data/splits \
      --seed $SEED \
      --output-dir artifacts/models/baseline_$SEED \
      --max-epochs 5 \
      --batch-size 16
done
```

## 8. Download Downstream Benchmark (DocVQA)
```bash
python -m src.data.download \
    --dataset-name docvqa \
    --output-dir data/raw/docvqa
```
*Verified open benchmark; exits with clear error if unavailable.*

## 9. Downstream Evaluation
```bash
python -m src.eval.downstream \
    --distilled-dir artifacts/models/distilled_*/ \
    --baseline-dir artifacts/models/baseline_*/ \
    --test-data data/raw/docvqa/test.parquet \
    --results-path artifacts/eval/downstream_results.json
```
*Computes Exact Match and F1 for both models, runs paired statistical tests (Bonferroni‑corrected), and reports Mutual Information and Pearson r between predicted latents and text embeddings.*

## 10. Inspect Results
```bash
cat artifacts/eval/downstream_results.json | python -m json.tool
```
*Key fields: `mean_em_augmented`, `mean_em_baseline`, `p_value`, `mi`, `pearson_r`, `validation_mse`. All must satisfy the success criteria (SC‑001 – SC‑007).*

## 11. Reproducibility Check
Run the full CI workflow locally (or rely on GitHub Actions) to ensure identical hashes and results:

```bash
pytest -k "contract" tests/
```
*Contract tests validate that `documentpair.schema.yaml` matches the actual Parquet schema and that all checksums are correct.*

---

