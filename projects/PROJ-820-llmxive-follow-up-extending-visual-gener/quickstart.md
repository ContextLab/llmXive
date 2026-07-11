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
 *Note: This installs CPU-optimized versions of torch and diffusers.*

## Data Fetching (N=100 Scope)

The project fetches real scene descriptions from the COCO-Captions dataset. [UNRESOLVED-CLAIM: c_4d62e564 — status=not_enough_info]
Run the following to generate `data/raw/scene_descriptions.csv`:
```bash
python code/utils/create_scene_descriptions.py
```
*If the dataset fetch fails, a deterministic fallback script generates valid physics-inferable scenes.*

## Execution Steps

### Step 1: Initialize Directories
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

### Step 4: Image Generation (T018)
```bash
python code/generation/diffusion_runner.py
```
*This step downloads the LCM-LoRA model and generates images.*
*Expected Output: `data/derived/generated_images/{group}/{scene_id}.png` for all three groups.*

### Step 5: Evaluation & Analysis
```bash
python code/evaluation/detector.py
python code/analysis/statistics.py
```

## Validation

- Check `data/derived/generated_images/` for 300 images (100 scenes x 3 groups).
- Check `data/processed/final_analysis.csv` for statistical results.
- Verify `power_analysis_report.json` indicates power >= 0.8.

## Troubleshooting

- **CUDA Error**: Ensure you are using the CPU version of PyTorch.
- **Model Download Failed**: Check internet connection or manually download the model from HuggingFace.
- **Memory Error**: Reduce batch size in `code/generation/diffusion_runner.py` (not implemented for batch yet, runs sequentially).
