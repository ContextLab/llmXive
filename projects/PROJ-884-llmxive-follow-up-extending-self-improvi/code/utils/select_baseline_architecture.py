"""T014: Select and document the baseline architecture.

Queries the HuggingFace Hub API for the exact commit hash of the chosen
CPU-only baseline model (distilbert-base-uncased) and writes
specs/001-llmxive-follow-up-extending-self-improvi/baseline_architecture.md
with the model identifier, commit hash, and device settings.

The commit hash is fetched live from the real Hub API; if the fetch fails
the script raises (no fabricated values are ever written).
"""

import sys
from datetime import datetime, timezone

import requests

from llmxive_toolkit import paths

PRIMARY_MODEL = "distilbert-base-uncased"
FALLBACK_MODELS = [
    "huawei-noah/TinyBERT_General_4L_312D",
    "google/bert_uncased_L-2_H-128_A-2",
    "prajjwal1/bert-tiny",
]
HF_API = "https://huggingface.co/api/models/{model}"


def fetch_model_info(model_id: str) -> dict:
    """Fetch real model metadata (including the pinned commit sha) from the
    HuggingFace Hub API. Raises on any failure - no fallbacks to invented data."""
    url = HF_API.format(model=model_id)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    info = resp.json()
    sha = info.get("sha")
    if not sha:
        raise ValueError(f"No commit sha returned by the Hub API for {model_id}")
    return {
        "model_id": model_id,
        "sha": sha,
        "downloads": info.get("downloads"),
        "likes": info.get("likes"),
        "pipeline_tag": info.get("pipeline_tag"),
    }


def build_document(primary: dict, fallbacks: list) -> str:
    lines = []
    a = lines.append
    a("# Baseline Architecture Selection")
    a("")
    a("**Task**: T014 (US3) - Select Baseline Architecture  ")
    a(f"**Date generated**: {datetime.now(timezone.utc).isoformat()}  ")
    a("**Selection status**: FINAL")
    a("")
    a("## Primary baseline model")
    a("")
    a(f"- **Model identifier**: `{primary['model_id']}`")
    a(f"- **Exact HuggingFace commit hash**: `{primary['sha']}`")
    a(f"- **Hub pipeline tag**: {primary.get('pipeline_tag')}")
    a(f"- **Hub downloads (at selection time)**: {primary.get('downloads')}")
    a(f"- **Hub likes (at selection time)**: {primary.get('likes')}")
    a("")
    a("### Rationale")
    a("")
    a("`distilbert-base-uncased` is a 6-layer, 66M-parameter distilled encoder that:")
    a("")
    a("- runs entirely on CPU with default float32 precision (no CUDA, no")
    a("  bitsandbytes quantization), satisfying the project's CPU-only constraint;")
    a("- has a small memory footprint (~250 MB in float32), well within the ~7 GB")
    a("  GitHub Actions free-tier runner limit;")
    a("- is fast enough for the forward recombination step of the BES loop within")
    a("  the <= 6 hour total experiment budget;")
    a("- is widely used as a small learned-verifier baseline, making the comparison")
    a("  against the symbolic planner reproducible and interpretable.")
    a("")
    a("## Device settings")
    a("")
    a("All inference is executed with the following explicit settings:")
    a("")
    a("```python")
    a("import torch")
    a("from transformers import AutoModel, AutoTokenizer")
    a("")
    a(f'MODEL_ID = "{primary["model_id"]}"')
    a(f'REVISION = "{primary["sha"]}"  # pinned commit hash')
    a("")
    a('device = torch.device("cpu")')
    a("tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)")
    a("model = AutoModel.from_pretrained(")
    a("    MODEL_ID,")
    a("    revision=REVISION,")
    a("    torch_dtype=torch.float32,  # default precision, no quantization")
    a(")")
    a("model.to(device)")
    a("model.eval()")
    a("```")
    a("")
    a("Settings summary:")
    a("")
    a("| Setting | Value |")
    a("|---|---|")
    a("| `device` | `cpu` (explicit; no CUDA / mixed precision anywhere) |")
    a("| `torch_dtype` | `torch.float32` (default precision) |")
    a("| Quantization | None (no bitsandbytes; `optimum` CPU quantization only as fallback) |")
    a("| Inference mode | `model.eval()`, `torch.no_grad()` during forward passes |")
    a(f"| Revision pinning | exact commit hash `{primary['sha']}` |")
    a("")
    a("## Fallback options")
    a("")
    a("If the primary model cannot be fetched or is too slow on the target runner,")
    a("the following fallbacks are used **in this order** (each pinned to its own")
    a("commit hash at load time):")
    a("")
    a("| Rank | Model identifier | Commit hash | Notes |")
    a("|---|---|---|---|")
    for i, fb in enumerate(fallbacks, start=1):
        a(f"| {i} | `{fb['model_id']}` | `{fb['sha']}` | "
          f"downloads={fb.get('downloads')}, pipeline={fb.get('pipeline_tag')} |")
    a("")
    a("A final fallback tier is CPU-optimized dynamic quantization of the primary")
    a("model via `optimum` (ONNX Runtime / `torch.quantization.quantize_dynamic`),")
    a("which is permitted by the plan (bitsandbytes 8-bit is NOT, as it requires CUDA).")
    a("")
    a("## Reproducibility notes")
    a("")
    a("- The commit hashes above were fetched live from")
    a("  `https://huggingface.co/api/models/<model_id>` at generation time;")
    a("  re-running `python code/utils/select_baseline_architecture.py`")
    a("  refreshes them from the Hub.")
    a("- All runs must pass `revision=<commit hash>` to")
    a("  `AutoModel.from_pretrained` / `AutoTokenizer.from_pretrained` so that")
    a("  weight updates on the Hub cannot silently change the baseline.")
    a("- Model fetch failures must raise (no synthetic substitute model is ever")
    a("  used), per the project's no-fabrication policy.")
    a("")
    a("## Verification command")
    a("")
    a("```bash")
    a("python code/utils/select_baseline_architecture.py")
    a("```")
    a("")
    a("writes this document to")
    a("`specs/001-llmxive-follow-up-extending-self-improvi/baseline_architecture.md`.")
    return "\n".join(lines) + "\n"


def main() -> int:
    print(f"Fetching primary model info: {PRIMARY_MODEL}")
    primary = fetch_model_info(PRIMARY_MODEL)
    print(f"  commit hash: {primary['sha']}")
    fallbacks = []
    for fb_id in FALLBACK_MODELS:
        print(f"Fetching fallback model info: {fb_id}")
        fb = fetch_model_info(fb_id)
        print(f"  commit hash: {fb['sha']}")
        fallbacks.append(fb)

    doc = build_document(primary, fallbacks)
    out_path = paths.path(
        "specs", "001-llmxive-follow-up-extending-self-improvi",
        "baseline_architecture.md",
    )
    out_path.write_text(doc, encoding="utf-8")
    print(f"Wrote {out_path}")

    # Verify the document contains the required fields (observable check).
    text = out_path.read_text(encoding="utf-8")
    assert PRIMARY_MODEL in text, "model identifier missing from document"
    assert primary["sha"] in text, "commit hash missing from document"
    assert "device" in text.lower(), "device settings missing from document"
    print("Observable check passed: model identifier, commit hash, device settings present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())