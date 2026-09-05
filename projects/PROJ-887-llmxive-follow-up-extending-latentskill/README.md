# llmXive: Extending "LatentSkill"

This project implements the automated science pipeline for extending the "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills" research. It ingests pre-trained LoRA adapters, constructs a skill vector database, executes retrieval and interpolation strategies, and validates performance via environment logic.

## Installation

```bash
pip install -r requirements.txt
sudo apt-get install -y cmake build-essential
```

## Data Sources

All data originates from verified real sources defined in `data_sources.yaml`:
- **Proxy LoRA Dataset**: `mrm8488/peft-examples` (Hugging Face)
- **ArXiv Supplementary**: `https://arxiv.org/src/2606.06087v1/ancillary.zip`

Verification logs are available in `data/processed/citation_verification.json`.

## Usage

Run the full pipeline end-to-end:

```bash
python src/evaluation/runner.py --adapter <path> --task <path> --output <path>
```

Or execute specific stages:

```bash
# Ingestion
python src/ingestion/download_weights.py --output data/raw
python src/ingestion/flatten_lora.py --input data/raw --output data/processed

# Retrieval
python src/retrieval/vector_db.py --input data/processed/weights_flattened.npz --output data/processed/skill_index.npz --k 5

# Evaluation & Stats
python src/evaluation/report_generator.py
```

## Results Summary

The final statistical report is generated at `data/results/stats_report.json`.
Key metrics from the final run:

| Metric | Value |
|:--- |:--- |
| **Linearity Validated (SC-005)** | `data/results/stats_report.json` (Check `linearity_valid`) |
| **Mean Success Rate** | `data/results/stats_report.json` |
| **Pearson Correlation** | `data/results/stats_report.json` |
| **Max Reconstruction Error** | `data/results/stats_report.json` |
| **Power Estimate** | `data/results/stats_report.json` |

**Statistical Significance**:
Primary and sensitivity p-values have been Benjamini-Hochberg corrected.
See `data/results/stats_report.json` for `bh_corrected_primary` and `bh_corrected_sensitivity`.

## Generated Plots

Visualizations are saved in `reports/plots/`:
- `success_rate_vs_k.png`: Success Rate vs Top-k
- `text_weight_correlation.png`: Text-Weight Pearson Correlation
- `latency_breakdown.png`: Latency breakdown (embedding, retrieval, interpolation, baseline)

## Limitations & Warnings

- **Power Analysis**: See `power_estimate` in `stats_report.json`. If < 0.8, results should be interpreted with caution.
- **Zero-Variance**: Any tasks skipped due to lack of variance are logged in `stats_zero_variance_warning.log` and listed in the `warnings` array of `stats_report.json`.
- **Data Integrity**: All results are derived from real LoRA weights. No synthetic data was used. See `data/audit_data_integrity.json` for confirmation.

## Final Report

The comprehensive Markdown report is available at `reports/final_report.md`.

## API Documentation

See `docs/api.md` for module signatures and descriptions.