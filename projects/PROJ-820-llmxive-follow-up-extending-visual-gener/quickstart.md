# Quick Start Guide for llmXive

## Environment Setup

1. **Install Python 3.11**
2. **Create Virtual Environment**
 ```bash
 python3.11 -m venv venv
 source venv/bin/activate
 ```
3. **Install Dependencies**
 ```bash
 pip install -r requirements.txt
 ```
 *Note: This installs CPU‑optimized versions of torch and diffusers.*

## Data Fetching (N=100 Scope) [UNRESOLVED-CLAIM: c_954009e5 — status=not_enough_info]

The project fetches real scene descriptions from the COCO‑Captions dataset. [UNRESOLVED-CLAIM: c_063864c0 — status=not_enough_info]
If that fetch fails, a deterministic fallback script generates valid physics‑inferable scenes. [UNRESOLVED-CLAIM: c_4784ad75 — status=not_enough_info]

```bash
python code/utils/create_scene_descriptions.py
```

## Execution Steps

### Step 1: Initialise Directories
```bash
python code/setup/create_directories.py
```

### Step 2: Physics Simulation
```bash
python code/simulation/physics_engine.py
```
*Outputs physics constraints to `data/derived/physics_constraints/`.*

### Step 3: Prompt Engineering
```bash
python code/generation/prompt_engine.py
```
*Outputs prompts to `data/derived/prompts/` (Baseline, Experimental, Control).*

### Step 4: Image Generation (Full Run)
```bash
python code/main.py --full
```
*This step:
 1. Generates a deterministic seed manifest (`data/derived/seed_manifest.json`).
 2. Generates reference geometry.
 3. Runs the diffusion model (CPU‑optimised LCM‑LoRA) for both baseline and experimental groups.
 4. Writes images to `data/derived/generated_images/{baseline,experimental}/`.
 5. Produces `data/derived/generated_images/manifest.csv` and `seed_lock_status.json`.*

### Step 5: Evaluation & Analysis
```bash
python code/evaluation/detector.py
python code/analysis/statistics.py
```

## Validation

- Check `data/derived/generated_images/` for the expected number of PNGs (≈ 100 per group, minus any generation failures).
- Verify `data/derived/seed_manifest.json` exists.
- Verify `data/processed/final_analysis.csv` exists and contains statistical results.
- Verify `data/processed/power_analysis_report.json` reports power ≥ 0.8.

## Troubleshooting

- **CUDA Error**: Ensure you are using the CPU version of PyTorch.
- **Model Download Failed**: Check internet connection or manually download the model from HuggingFace.
- **Memory Error**: Reduce batch size in `code/generation/diffusion_runner.py` (runs sequentially by default).
