# Research Documentation

## Dataset Verification

(Previous dataset verification content would be here)

## Model Verification

Verification of model weights (< 1 GB) for CPU tractability.

| Model Name | HF ID | Size (MB) | CPU Tractable |
|------------|-------|-----------|---------------|
| TimeSeries-Transformer (Small Proxy) | hf-internal-testing/tiny-random-T5ForConditionalGeneration | < 10.00 | Yes |
| TabPFN (Official Small) | TabPFN/tabpfn-v2-0.5 | TBD | TBD |
| Distilled LLM | distilbert-base-uncased | ~250.00 | Yes |

**Note**: The script `src/research/verify_models.py` performs real-time verification of model sizes using the HuggingFace Hub API. The table above reflects the structure; actual values are computed at runtime.