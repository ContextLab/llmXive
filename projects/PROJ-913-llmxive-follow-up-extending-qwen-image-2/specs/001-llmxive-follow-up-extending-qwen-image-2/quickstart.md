# Quickstart: llmXive Follow-up: OPD Generalization Gap in Unified Diffusion

## 1. Prerequisites

- Python 3.11+
- Git
- Hugging Face CLI (optional, for model downloads)
- 7 GB+ RAM (free-tier GitHub Actions runner)

## 2. Setup

### 2.1 Clone the Repository
```bash
git clone
cd projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2
```

### 2.2 Install Dependencies
```bash
pip install -r code/requirements.txt
```

### 2.3 Authenticate with Hugging Face (if required)
```bash
huggingface-cli login
```

## 3. Running the Pipeline

### 3.1 Data Acquisition
Download models and curate prompts. **Note**: The OOD source is now `stabilityai/stable-diffusion-3-prompts` to ensure valid image-generation prompts.
```bash
python code/data_acquisition.py --base-model qwen-image-2.0 --rl-model qwen-image-2.0-rl --ood-source stabilityai/stable-diffusion-3-prompts
```

### 3.2 Inference
Generate images (CPU-only):
```bash
python code/inference.py --batch-size 1 --max-ram 7GB
```

### 3.3 Scoring
Score generated images:
```bash
python code/scoring.py --metrics aesthetics,prompt_adherence,identity_preservation
```

### 3.4 Analysis
Compute generalization gap and statistical significance:
```bash
python code/analysis.py --bootstrap-iterations 10000
```

## 4. Expected Outputs

- `data/outputs/base/`: Generated images from the base model.
- `data/outputs/rl_unified/`: Generated images from the RL-unified model.
- `data/scores/scores.jsonl`: Evaluation scores.
- `data/analysis/results.json`: Statistical analysis results (mean degradation, p-value, confidence intervals, achieved power).

## 5. Troubleshooting

- **OOM Error**: Reduce `--batch-size` in `inference.py`.
- **Model Download Failure**: Check network connectivity and Hugging Face authentication.
- **OOD Contamination**: Re-run `data_acquisition.py` with stricter cosine similarity thresholds or verify keyword filtering.

## 6. Reproducibility

- All random seeds are pinned in `code/`.
- Data checksums are recorded in `data/`.
- Re-run the entire pipeline with `./run_pipeline.sh` for full reproducibility.
