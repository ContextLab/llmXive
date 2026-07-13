# Quickstart: Dynamic Socio-Cognitive State Injection

## Prerequisites

- Python 3.11+
- Git
- ≤7 GB RAM available (CPU inference)
- Optional: HuggingFace CLI for model caching

## Installation

```bash
cd projects/PROJ-885-llmxive-follow-up-extending-socrates-tow
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Study

### 1. Generate Synthetic Trajectories (Oversampling)
Creates 500 trajectories with ≥40 % high‑difficulty samples.

```bash
python code/data/generator.py --count 500 --oversample 0.4 --seed 42
```

*Output*: `data/processed/trajectories.jsonl` and a summary JSON (`data/processed/summary.json`).

### 2. Train the Dynamic State Classifier
Trains a logistic‑regression model on turn‑level text features plus metadata.

```bash
python code/models/classifier.py --train
```

*Output*: `data/models/classifier.pkl`.

### 3. Execute Paired Experiments (Adapter vs. Static)
Runs all CPU‑compatible LLMs on the generated trajectories.

```bash
python code/experiments/runner.py \
  --llms "llama-3-8b, mistral-7b, gemma-7b, ..." \
  --conditions static adapter
```

*Note*: The script respects a bounded wall‑clock budget on a free‑tier runner.

*Outputs*: `data/processed/experiments/<llm_id>.jsonl`.

### 4. Analyze Results
Computes consensus‑gap scores and performs statistical testing with Holm‑Bonferroni correction.

```bash
python code/analysis/stats.py \
  --input data/processed/experiments/ \
  --output data/results/statistical_summary.json
```

*Output*: `data/results/statistical_summary.json`.

## Verification

- **Distribution Check**:  
  ```bash
  python code/data/generator.py --verify data/processed/summary.json
  ```  
  Should report > 40 % high‑difficulty samples.

- **Statistical Significance**: Inspect `data/results/statistical_summary.json` for `is_significant: true` and `p_value < 0.05`.

## Troubleshooting

- **Memory Error**: Reduce `--count` or run a subset of LLMs.
- **CUDA Error**: Ensure `CUDA_VISIBLE_DEVICES=""` is set; the code forces CPU execution.
- **Timeout**: Increase the GitHub Actions job timeout or lower trajectory count.
