# Quickstart: Evaluating the Impact of Code Duplication on LLM Code Understanding

**Branch**: `001-evaluate-code-duplication-llm-understanding` | **Date**: 2026-05-12

## Prerequisites

- Python 3.11+
- 7GB+ available RAM (for 8-bit model inference)
- Internet access (for HuggingFace dataset/model download)
- GitHub Actions runner or equivalent Linux environment

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Verify Configuration

```bash
python -c "import config; print(f'Seed: {config.SEED}')"
```

Expected output: `Seed: 42` (or configured value)

### 3. Run Pipeline (Sample)

```bash
# Process 10 files for validation
python main.py --sample-size 10
```

### 4. Run Full Pipeline

```bash
# Process 500MB corpus
python main.py
```

### 5. Verify Results

```bash
# Check output files exist
ls -la data/processed/
ls -la data/analysis/

# Validate schema compliance
pytest tests/contract/
```

## Configuration

Edit `config.py` to modify:

| Parameter | Default | Description |
|-----------|---------|-------------|
| SEED | 42 | Random seed for reproducibility |
| DATASET_SUBSET_SIZE | 500MB | Size of codeparrot/github-code subset |
| CLONE_THRESHOLD | 0.8 | Clone detection threshold |
| MODEL_NAME | "Salesforce/codegen-350M-mono" | Pre-trained model |
| HUMAN_EVAL_SUBSET | 50 | Number of problems to evaluate |
| MEMORY_LIMIT_GB | 7 | Maximum memory usage |

## Output Files

After successful run:

```
data/
├── raw/
│   └── github-code-sample.csv      # Raw code segments
├── processed/
│   ├── clone_metrics.csv           # Clone density per segment
│   ├── perplexity_scores.csv       # Perplexity per segment
│   ├── bug_detection_results.csv   # HumanEval results
│   └── parse_failures.csv          # Failed parses (if any)
└── analysis/
    ├── correlation_results.csv     # Spearman correlations
    └── figures/
        ├── clone_vs_perplexity.png
        └── clone_vs_bug_detection.png
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| HuggingFace rate limit | Wait and retry; check `HF_HUB_ENABLE_HF_TRANSFER=1` |
| AST parse error | Check `parse_failures.csv`; file may have non-standard syntax |
| OOM error | Verify 8-bit quantization enabled; reduce sample size |
| NaN perplexity | Check log-probability outputs; exclude invalid segments |

## Next Steps

- Review `research.md` for detailed methodology
- Review `data-model.md` for entity definitions
- Run `pytest tests/` for full test suite
- Generate paper from `data/analysis/` outputs
