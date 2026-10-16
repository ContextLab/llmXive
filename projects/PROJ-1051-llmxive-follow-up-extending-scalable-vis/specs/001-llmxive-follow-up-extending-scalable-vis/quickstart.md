# Quickstart: llmXive follow-up (Re-plan v3)

```bash
# 1. Environment
python -m venv .venv && source .venv/bin/activate
pip install -r code/requirements.txt

# 2. Download & verify the real dataset (single verified URL)
python -m src.data.download \
  --url https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet \
  --output data/raw/mixsub_overlap.parquet \
  --provenance data/raw/provenance.json
# Exits non-zero with a clear message if download fails, checksum mismatch,
# or row count < minimum (FR-007). Records column inventory + label semantics.

# 3. Preprocess (schema validation; skips+logs invalid rows)
python -m src.data.preprocess \
  --input data/raw/mixsub_overlap.parquet \
  --output data/processed/document_pairs.parquet \
  --schema contracts/documentpair.schema.yaml

# 4. Structural latent generation (deterministic, CPU) + non-degeneracy gate
python -m src.features.structure \
  --input data/processed/document_pairs.parquet \
  --output data/processed/document_pairs_with_latent.parquet
# Exits non-zero with a clear scope-mismatch error if the structural feature
# matrix is degenerate (after the newline-free feature fallback).

# 5. Splits
python -m src.utils.split_generator \
  --input data/processed/document_pairs_with_latent.parquet \
  --output-dir data/splits --seed 42

# 6. Train student + per-seed re-trained baseline across seeds
for SEED in 42 43 44 45 46 47 48 49 50 51; do
  python -m src.models.distilled  --data data/processed/document_pairs_with_latent.parquet --splits data/splits --seed $SEED --out artifacts/models/distilled_$SEED
  python -m src.models.baseline   --data data/processed/document_pairs_with_latent.parquet --splits data/splits --seed $SEED --out artifacts/models/baseline_$SEED
done

# 7. Leakage pre-check + downstream evaluation + statistics (val-tuned, test-reported)
python -m src.eval.downstream \
  --models artifacts/models --splits data/splits \
  --results artifacts/eval/results.json
# Runs the label-semantics/leakage pre-check first; if the label is a trivial
# function of the input text, results.json records the leakage finding and no
# augmented-vs-baseline gain is claimed.

# 8. Inspect results (single source of truth)
python -m json.tool artifacts/eval/results.json

# 9. Contract tests
pytest tests/ -k contract
```

Note: the visual-encoder / image-latent component of the original spec is not executed — no verified dataset provides page images or layout annotations, and FR-008's independence claim is not executable in the reframed design (the latent is a function of the text by construction). See the Scope Revision and Required spec amendments sections of `plan.md`.