# Quickstart: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

This guide gets you from a fresh GitHub Actions runner to a complete end‑to‑end run of the pipeline.

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
    --primary-name docbank \
    --fallback-name pubmed-layout
```
*The script will attempt to fetch the named datasets. If the combined page count < 10 000, it will abort with a clear error (FR‑007).*

## 3. Preprocess & Validate
```bash
python -m src.data.preprocess \
    --input-dir data/raw \
    --output-path data/processed/document_pairs.parquet \
    --schema contracts/documentpair.schema.yaml
```
*Checksums are recorded; any missing `layout_annotations` generate a warning and the page is skipped.*

## 4. Generate Visual Latents (CPU‑only)
```bash
python -m src.data.latent_generator \
    --input-path data/processed/document_pairs.parquet \
    --output-path data/processed/document_pairs_with_latent.parquet \
    --encoder-name layoutlmv3-base \
    --device cpu
```
*If the encoder cannot be loaded on CPU, the script exits with an informative message (edge case handling).*

## 5. Create Consistent Train/Val/Test Splits
```bash
python -m src.utils.split_generator \
    --input-path data/processed/document_pairs_with_latent.parquet \
    --output-dir data/splits \
    --seed 42 \
    --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1
```
*Generates `data/splits/train_idx.json`, `val_idx.json`, `test_idx.json` used by both distilled and baseline models.*

## 6. Train Distilled Model (several seeds)
```bash
for SEED in {42..56}; do
  python -m src.models.distilled \
      --data-path data/processed/document_pairs_with_latent.parquet \
      --splits-dir data/splits \
      --seed $SEED \
      --output-dir artifacts/models/distilled_$SEED \
      --max-epochs 5 \
      --batch-size 16
done
```
*Training respects the 7 GB RAM ceiling; batch size may be auto‑reduced if OOM is detected.*

## 7. Train Baseline Models (one per seed)
```bash
for SEED in {42..56}; do
  python -m src.models.baseline \
      --data-path data/processed/document_pairs.parquet \
      --splits-dir data/splits \
      --seed $SEED \
      --output-dir artifacts/models/baseline_$SEED \
      --max-epochs 5 \
      --batch-size 16
done
```

## 8. Downstream Evaluation (optional)
```bash
# Run only if a verified downstream reasoning benchmark is available.
if [ -f data/processed/downstream_test.parquet ]; then
  python -m src.eval.downstream \
      --distilled-dir artifacts/models/distilled_*/ \
      --baseline-dir artifacts/models/baseline_*/ \
      --test-data data/processed/downstream_test.parquet \
      --results-path artifacts/eval/downstream_results.json
fi
```
*The script computes accuracy/F1 for both models, runs a paired t‑test (or Wilcoxon if normality fails) across the fifteen seeds, and writes a JSON report.*

## 9. Inspect Results
```bash
cat artifacts/eval/downstream_results.json | python -m json.tool
```
*Key fields: `mean_accuracy_augmented`, `mean_accuracy_baseline`, `p_value`, `validation_mse`. All must satisfy the success criteria (SC‑001…SC‑007).*

## 10. Reproducibility Check
Run the full CI workflow locally (or rely on GitHub Actions) to ensure that the same hashes and results are reproduced.

```bash
pytest -k "contract" tests/
```
*Contract tests validate that `documentpair.schema.yaml` matches the actual parquet schema.*

---

