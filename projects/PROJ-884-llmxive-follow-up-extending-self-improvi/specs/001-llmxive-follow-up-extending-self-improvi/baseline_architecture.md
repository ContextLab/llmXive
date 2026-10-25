# Baseline Architecture Selection

**Task**: T014 (US3) - Select Baseline Architecture
**Date generated**: 2026-10-22T06:38:39.685190+00:00
**Selection status**: FINAL

## Primary baseline model

- **Model identifier**: `distilbert-base-uncased`
- **Exact HuggingFace commit hash**: `12040accade4e8a0f71eabdb258fecc2e7e948be`
- **Hub pipeline tag**: fill-mask
- **Hub downloads (at selection time)**: 6,850,254
- **Hub likes (at selection time)**: 1,135

### Rationale

`distilbert-base-uncased` is a 6-layer, 66M-parameter distilled encoder [UNRESOLVED-CLAIM: c_2603d525 — status=not_enough_info] that:

- runs entirely on CPU with default float32 precision (no CUDA, no
 bitsandbytes quantization), satisfying the project's CPU-only constraint;
- has a small memory footprint (~250 MB in float32), well within the ~7 GB
 GitHub Actions free-tier runner limit;
- is fast enough for the forward recombination step of the BES loop within
 the ≤ 6 hour total experiment budget;
- is widely used as a small learned‑verifier baseline, making the comparison
 against the symbolic planner reproducible and interpretable.

## Device settings

All inference is executed with the following explicit settings:

```python
import torch
from transformers import AutoModel, AutoTokenizer

MODEL_ID = "distilbert-base-uncased"
REVISION = "12040accade4e8a0f71eabdb258fecc2e7e948be" # pinned commit hash

device = torch.device("cpu")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
model = AutoModel.from_pretrained(
 MODEL_ID,
 revision=REVISION,
 torch_dtype=torch.float32, # default precision, no quantization
)
model.to(device)
model.eval()
```

Settings summary:

| Setting | Value |
|--------------------|-------|
| `device` | `cpu` (explicit; no CUDA / mixed precision anywhere) |
| `torch_dtype` | `torch.float32` (default precision) |
| Quantization | None (no bitsandbytes; `optimum` CPU quantization only as fallback) |
| Inference mode | `model.eval()`, `torch.no_grad()` during forward passes |
| Revision pinning | exact commit hash `12040accade4e8a0f71eabdb258fecc2e7e948be` |

## Fallback options

If the primary model cannot be fetched or is too slow on the target runner,
the following fallbacks are used **in this order** (each pinned to its own
commit hash at load time):

| Rank | Model identifier | Commit hash | Notes |
|------|--------------------------------------|---------------------------------------------|-------|
| 1 | `huawei-noah/TinyBERT_General_4L_312D` | `34707a33cd59a94ecde241ac209bf35103691b43` | downloads=535,595, pipeline=None |
| 2 | `google/bert_uncased_L-2_H-128_A-2` | `30b0a37ccaaa32f332884b96992754e246e48c5f` | downloads=273,136, pipeline=None |
| 3 | `prajjwal1/bert-tiny` | `6f75de8b60a9f8a2fdf7b69cbd86d9e64bcb3837` | downloads=956,473, pipeline=None |

A final fallback tier is CPU-optimized dynamic quantization of the primary
model via `optimum` (ONNX Runtime / `torch.quantization.quantize_dynamic`),
which is permitted by the plan (bitsandbytes 8-bit is NOT, as it requires CUDA).

## Reproducibility notes

- The commit hashes above were fetched live from
 `https://huggingface.co/api/models/<model_id>` at generation time;
 re‑running `python code/utils/select_baseline_architecture.py`
 refreshes them from the Hub.
- All runs must pass `revision=<commit hash>` to
 `AutoModel.from_pretrained` / `AutoTokenizer.from_pretrained` so that
 weight updates on the Hub cannot silently change the baseline.
- Model fetch failures must raise (no synthetic substitute model is ever
 used), per the project's no‑fabrication policy.

## Verification command

```bash
python code/utils/select_baseline_architecture.py
```

writes this document to
`specs/001-llmxive-follow-up-extending-self-improvi/baseline_architecture.md`.