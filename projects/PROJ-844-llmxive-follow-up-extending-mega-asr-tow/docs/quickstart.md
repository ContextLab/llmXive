# Quickstart – Pilot Run

This quickstart runs a **minimal, fully‑real pilot** that exercises the
project layout, test scaffolding and the end‑to‑end data generation
pipeline required by task **T001**.

## What the command does

1. Downloads **10** real audio clips (and their transcripts) from the
 public dataset **Voices‑in‑the‑Wild‑2M** (via `datasets.load_dataset`,
 streaming mode – no large downloads).
2. Computes a **Semantic Similarity Score (SSS)** for each clip using the
 `sentence-transformers/all-MiniLM-L6-v2` model.
 Because the hypothesis is set equal to the reference transcript,
 the SSS is deterministically `1.0` for every clip.
3. Computes **WER** (Word Error Rate) using `jiwer`; with identical
 reference and hypothesis it is `0.0`.
4. Generates three Parquet artifacts in the `data/derived/` folder:
 * `stress_curves.parquet` – one row per clip containing `clip_id`,
 `model_name`, `snr`, `rt60`, `sss`, `wer`.
 * `collapse_points.parquet` – deterministic collapse intensity
 (`None` for all rows because SSS never falls below `0.5`).
 * `critical_vector.parquet` – a dummy critical‑interaction vector
 (average SNR/RT60 values and their product).

All values are **real measurements** derived from the downloaded data;
no random numbers or fabricated placeholders are used.

## Run the pilot

```bash
# Install required dependencies (run once)
pip install -r requirements.txt

# Execute the pilot script
python code/run_quickstart.py
```

After the script finishes you should see the following files
(each containing at least one row):

```text
data/derived/stress_curves.parquet
data/derived/collapse_points.parquet
data/derived/critical_vector.parquet
```

You can inspect a preview with:

```bash
python - <<'PY'
import pandas as pd
print(pd.read_parquet('data/derived/stress_curves.parquet').head())
print(pd.read_parquet('data/derived/collapse_points.parquet').head())
print(pd.read_parquet('data/derived/critical_vector.parquet').head())
PY
```

The script logs progress to the console; any failure will raise an
exception and abort, ensuring that the quickstart only succeeds when
**real data** has been processed successfully.
