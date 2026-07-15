# Quickstart: Quantization Robustness of Multi-Effect LoRA Adapters

## Prerequisites

- Python 3.11+
- 7 GB + RAM (Free‑Tier GitHub Actions compatible)
- Git

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-892-llmxive-follow-up-extending-collectionlo
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```

## Configuration

Edit `code/config.yaml` to adjust (if needed):

```yaml
seed: 12345
prompts_file: data/prompts.txt            # 5 lines, each "effect_id<TAB>prompt"
quantization_levels: ["FP16", "INT8", "INT4"]
base_model_id: "stabilityai/stable-diffusion-1-5"
adapter_model_id: "user/collectionlora-multi-teacher-onp"
inference_steps: 50
```

*The prompts file already contains a deterministic one‑to‑one mapping of effects to prompts (FR‑009).*

## Running the Full Pipeline

```bash
python code/main.py
```

The script executes the following ordered phases:

1. **Constitution amendment** (creates PR to replace ANOVA with BHM).  
2. **Foundational** – load models, compute & persist LoRA subspace ranks.  
3. **Baseline generation** – FP16 images *with* LoRA and LoRA‑free reference images.  
4. **Quantization** – INT8 / INT4 adapters via `torch.ao.quantization`; skips level if backend unavailable.  
5. **Metric extraction** – CLIP similarity, LPIPS, style‑classifier score, CESR.  
6. **Statistical analysis** – Bayesian hierarchical model & correlation analysis.  
7. **Reporting** – `data/report.md` summarises all results.

## Validation

- Run unit tests: `pytest tests/unit/`.  
- Contract validation: `pytest tests/contract/`.  
- Verify SHA‑256 hashes in `state/artifact_hashes.yaml`.  

## Troubleshooting

- **OOM (Exit 137)**: The pipeline logs “Quantization Failure – level X skipped” and continues.  
- **Quantization backend missing**: Logs “Quantization Backend Unavailable – skipping INT8/INT4”. No fallback is attempted, preserving noise‑isolation (Principle VI).  
- **Slow runtime**: Reduce `inference_steps` (minimum 30 recommended) or decrease number of effects (minimum 5 required by the spec).  
