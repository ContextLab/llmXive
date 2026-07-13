# Phenomenological AI: First-Person Experience Modeling - Quick Start Guide

This guide provides the essential steps to set up the environment and run the automated science pipeline for generating and analyzing phenomenological reports.

## Prerequisites

- Python 3.9+
- pip (Python package manager)
- ~4GB RAM (for CPU-only TinyLlama execution)
- ~2GB disk space for models and data

## 1. Environment Setup

### Clone and Navigate
```bash
git clone <repository-url>
cd llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie
```

### Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies
Install the core requirements, including `llama-cpp-python` for CPU inference and `datasets` for control corpus loading:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note on `llama-cpp-python`**: Ensure you have a compatible C++ compiler installed. For CPU-only execution, install with `CMAKE_ARGS="-DLLAMA_BLAS=OFF"` to avoid unnecessary dependencies.
> ```bash
> CMAKE_ARGS="-DLLAMA_BLAS=OFF" pip install llama-cpp-python
> ```

### Download the Model
The pipeline uses `TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF` (specifically `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`).
If not already present in `data/models/`, download it:
```bash
mkdir -p data/models
wget -O data/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
```

## 2. Project Structure

- `code/`: Source code for generation, analysis, and validation.
- `data/raw/`: Generated phenomenological reports and control corpus samples.
- `data/processed/`: Computed metrics (validity scores, statistics).
- `data/qualitative/`: Human rating sheets and anonymized data.
- `specs/`: Feature specifications and contracts.

## 3. Running the Pipeline

The main entry point is `code/main.py`. Use the `--task` argument to select the phase.

### A. Generate Phenomenological Reports (US1)
Generates ~80 samples per prompt per strategy (4 strategies) using the TinyLlama model on CPU.
```bash
python code/main.py --task generate --config code/config.py
```
**Output**: `data/raw/generation_samples.json`

### B. Generate Control Corpus (US1)
Generates control samples from the `arxiv_nlp` dataset for discriminant validity testing.
```bash
python code/main.py --task generate_control --config code/config.py
```
**Output**: `data/raw/control_samples.json`

### C. Analyze Metrics (US2)
Computes Internal Consistency, Semantic Stability, and Marker Presence metrics.
```bash
python code/main.py --task analyze --config code/config.py
```
**Output**: Intermediate metric files in `data/processed/`

### D. Statistical Analysis (US2)
Performs Shapiro-Wilk, Levene, ANOVA/Kruskal-Wallis, and post-hoc tests.
```bash
python code/main.py --task stats --config code/config.py
```
**Output**: `data/processed/validity_scores.csv` and statistical summary logs.

### E. Validation & Sampling (US3)
Selects a stratified sample for human rating.
```bash
python code/main.py --task validate_human --config code/config.py
```
**Output**: `data/qualitative/sampled_reports.json`

### F. Full Pipeline (End-to-End)
Executes Generation → Control → Analysis → Stats in sequence.
```bash
python code/main.py --task full --config code/config.py
```
**Expected Duration**: ≤6 hours on free-tier CPU resources.

## 4. Verification

After running the full pipeline, verify the following artifacts exist:
- `data/raw/generation_samples.json` (≥3200 samples expected: 20 prompts × 4 strategies × ~40 seeds)
- `data/raw/control_samples.json` (≥80 samples)
- `data/processed/validity_scores.csv` (Non-null scores for all metrics)
- `data/qualitative/sampled_reports.json` (Stratified subset)

## 5. Troubleshooting

- **CUDA Errors**: Ensure you are not using a GPU. The `config.py` is set to CPU-only for TinyLlama.
- **Memory Errors**: If OOM occurs, reduce `MAX_SAMPLES_PER_PROMPT` in `code/config.py`.
- **Missing Model**: Verify `data/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf` exists.

## 6. Next Steps

- Review `specs/contracts/` for data schemas.
- Implement custom analysis in `code/analysis/` modules.
- Run human rating using `code/validation/human_rater.py` on the sampled reports.
- Archive reproducibility data with `python code/main.py --task archive`.