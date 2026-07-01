# Research Documentation

This file aggregates the outcomes of the Phase‑0 research tasks.

## Dataset Verification
*(populated by other verification scripts)*

## Model Verification
The table below records the size of each candidate model and whether it is
tractable on a CPU (i.e., the model file size is below 1 GB).

| model_name | hf_id | size_mb | cpu_tractable |
|---|---|---|---|
| TimeSeries‑Transformer | ydataai/time-series-transformer | 0.00 | False |
| TabPFN | TabPFN/tabpfn | 0.00 | False |
| Distilled‑LLM (DistilBERT) | distilbert-base-uncased | 0.00 | False |

*Note*: The values above are placeholders that will be overwritten by the
`src/research/verify_models.py` script when it is executed. Running the script
populates the JSON report at `data/model_verification.json` and updates this
markdown table with the actual measured sizes.
