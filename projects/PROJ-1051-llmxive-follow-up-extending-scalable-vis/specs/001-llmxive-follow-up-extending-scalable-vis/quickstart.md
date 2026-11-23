# Quickstart: llmXive follow-up (Re‑plan v4)

```bash
# 1. Set up a virtual environment
python -m venv .venv && source .venv/bin/activate
pip install -r code/requirements.txt

# 2. Download & verify the real dataset (single verified URL)
# NOTE: Replace the SHA256 placeholder with the actual checksum of the parquet.
# The script will abort if the computed checksum does not match.
python -m src.data.download \
  --url https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet \
  --output data/raw/mixsub_overlap.parquet \
  --provenance data/raw/provenance.json \
  --sha256 3a1f5e8b9c2d4f6e7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f
# Exits non‑zero with a clear message if download fails, checksum mismatch,
# or row count < 10 000 (FR‑007). Records column inventory + label semantics.

# 3. Preprocess (schema validation; skips+logs invalid rows)
python -m src.data.preprocess \
  --input data/raw/mixsub_overlap.parquet \
  --output data/processed/document_pairs.parquet \
  --schema contracts/documentpair.schema.yaml

# 4. Structural latent generation (deterministic, CPU) + non‑degeneracy gate
python -m src.features.structure \
  --input data/processed/document_pairs.parquet \
  --output data/processed/document_pairs_with_latent.parquet
# Exits non‑zero with a clear scope‑mismatch error if the feature matrix is degenerate.

# 5. Create splits
python -m src.utils.split_generator \
  --input data/processed/document_pairs_with_latent.parquet \
  --output-dir data/splits --seed 42

# 6. Train student + per‑seed re‑trained baseline + random‑latent control across seeds
# Fixed seed set: a contiguous block of ten consecutive seeds.
for SEED in 42 43 44 45 46 47 48 49 50 51; do
  python -m src.models.distilled  --data data/processed/document_pairs_with_latent.parquet --splits data/splits --seed $SEED --out artifacts/models/distilled_$SEED
  python -m src.models.baseline   --data data/processed/document_pairs_with_latent.parquet --splits data/splits --seed $SEED --out artifacts/models/baseline_$SEED
  python -m src.models.random_latent --data data/processed/document_pairs_with_latent.parquet --splits data/splits --seed $SEED --out artifacts/models/random_latent_$SEED
done

# 7. Leakage pre‑check + orthogonalization + downstream evaluation + statistics
python -m src.eval.downstream \
  --models artifacts/models --splits data/splits \
  --results artifacts/eval/results.json
# Runs the label‑semantics/leakage pre‑check first; if the label is a trivial
# function of the input text, `results.json` records the finding and no
# augmented‑vs‑baseline gain is claimed.

# 8. Inspect results (single source of truth)
python -m json.tool artifacts/eval/results.json

# 9. Run contract tests
pytest tests/ -k contract
```

> **Note**: The visual‑encoder / image‑latent component of the original spec is **not executed** – no verified dataset provides page images or layout annotations, and FR‑008's independence claim is not executable in the reframed design. See the *Scope Revision* and *Required spec amendments* sections of `plan.md`.

---


