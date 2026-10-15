# Quickstart: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

This guide walks a fresh GitHub Actions runner through the complete end‑to‑end pipeline.

## 1. Setup Environment
```bash
python -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r code/requirements.txt
```

## 2. Verify Data Availability
```bash
python -m src.data.download \
    --dataset-name layout_corpus \
    --output-dir data/raw
```
*Programmatically fetches the layout-aware corpus (text + images + layout) using `datasets.load_dataset`. If the dataset is unavailable, the script exits with a clear error message.*

## 3. Preprocess Documents
```bash
python -m src.data.preprocess \
    --input-dir data/raw/layout_corpus \
    --output-parquet data/processed/document_pairs.parquet \
    --schema contracts/documentpair.schema.yaml
```
*Validates each record against the schema, ensures image accessibility, and writes a Parquet file, logging any rows with missing layout annotations.*

## 4. Generate Visual Latents (CPU‑only)
```bash
python -m src.data.latent_generator \
    --input-parquet data/processed/document_pairs.parquet \
    --output-parquet data/processed/document_pairs_with_latent.parquet \
    --encoder-name resnet18 \
    --device cpu
```
*Runs ResNet-18 inference and performs a construct validity check (correlation with layout complexity) before saving latents.*

## 5. Create Consistent Train/Val/Test Splits
```bash
python -m src.utils.split_generator \
    --input-parquet data/processed/document_pairs_with_latent.parquet \
    --output-dir data/splits \
    --seed 42 \
    --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1
```

## 6. Train Distilled Model (multiple seeds)
```bash
for SEED in {42..71}; do
  python -m src.models.distilled \
      --data-parquet data/processed/document_pairs_with_latent.parquet \
      --splits-dir data/splits \
      --seed $SEED \
      --output-dir artifacts/models/distilled_$SEED \
      --max-epochs 5 \
      --batch-size 32
done
```

## 7. Train Baseline Models (multiple seeds, random projection head)
```bash
for SEED in {42..71}; do
  python -m src.models.baseline \
      --data-parquet data/processed/document_pairs.parquet \
      --splits-dir data/splits \
      --seed $SEED \
      --output-dir artifacts/models/baseline_$SEED \
      --max-epochs 5 \
      --batch-size 32
done
```
*The baseline uses a frozen random projection head to match the augmented model's capacity.*

## 8. Download Downstream Benchmark (DocVQA)
```bash
python -m src.data.download \
    --dataset-name docvqa \
    --output-dir data/raw/docvqa
```

## 9. Downstream Evaluation (Val/Test Split)
```bash
python -m src.eval.downstream \
    --distilled-dir artifacts/models/distilled_*/ \
    --baseline-dir artifacts/models/baseline_*/ \
    --test-data data/raw/docvqa/test.parquet \
    --val-data data/raw/docvqa/val.parquet \
    --results-path artifacts/eval/downstream_results.json
```
*Tunes hyperparameters on the validation set and reports final metrics on the test set, including paired statistical tests and independence checks.*

## 10. Inspect Results
```bash
cat artifacts/eval/downstream_results.json | python -m json.tool
```

## 11. Reproducibility Check
```bash
pytest -k "contract" tests/
```