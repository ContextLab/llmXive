# Quickstart: llmXive Follow-up: Semantic Divergence Diagnostic for Agentic Reasoning

## Prerequisites

- Python 3.11+
- Internet access for HuggingFace Hub downloads
- At least **7 GB** of free RAM
- Sufficient free disk space

## Installation

1. **Clone the repository** and `cd` into the project root.  
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
3. **Install pinned dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *The `requirements.txt` pins `torch` to a CPU‑only wheel and all other libraries to stable releases.*

## Required Supplemental Files

| File | Description | Checksum File |
|------|-------------|---------------|
| `data/external/tool_mapping.csv` | `problem_id` → list of ground‑truth tool IDs. | `tool_mapping_checksum.txt` |
| `data/external/tool_descriptions.csv` | `tool_id`, `description` for BM25 indexing. | `tool_descriptions_checksum.txt` |
| `data/external/rl_failure_rates.csv` | `problem_id`, `failure_rate` (independent RL outcome). | `rl_failure_rates_checksum.txt` |

**Simulation Mode**: If any of these files are **missing**, the system will automatically generate **synthetic** data:

- **Tool Mapping** – deterministic assignment based on problem difficulty (see `research.md`).  
- **Tool Descriptions** – a synthetic corpus of domain‑relevant tools with templated descriptions.  
- **RL Failure Rates** – `failure_rate = 0.5 * difficulty + 0.5 * Uniform(0,1)` using a fixed seed.  

All generated files are written with SHA‑256 checksums recorded in the project state file.

## Running the Pipeline

```bash
python src/cli/main.py \
  --dataset "AI4Math/MathVista" \
  --subset "test" \
  --max-records a sufficient number to ensure comprehensive coverage without exceeding computational limits. \
  --seed 42 \
  --output-dir data/processed
```

Flags:

- `--max-records` caps the number of problem instances (enforces RAM limit).  
- `--seed` fixes all random operations (sampling, synthetic generation, Logistic Regression, train‑test split).  
- `--output-dir` is where all JSON outputs and checksum files are written.

The script performs:

1. Dataset download & checksum validation (with streaming fallback for large files).  
2. BM25 index creation from `tool_descriptions.csv` (or synthetic generation).  
3. DistilBERT embedding of thinking prefixes and tool texts.  
4. Divergence score calculation.  
5. Pearson correlation with the RL failure rates (or synthetic).  
6. **K‑Means** clustering for risk‑group labeling **(training split only)**.  
7. Logistic regression training & test‑set evaluation (using divergence score only).  
8. Generation of `divergence_scores.json`, `analysis_results.json`, and `checksums.txt`.

## Reproducibility

Rerun the exact command with the same `--seed` to obtain identical results. After each run, `scripts/update_state_hashes.py` records SHA‑256 hashes of all outputs in `state/projects/PROJ-849-llmxive-follow-up-extending-agent-explor.yaml`.

## Troubleshooting

- **MemoryError** → The system automatically switches to streaming mode. If it fails, reduce `--max-records` (e.g., to 200).  
- **Missing checksum** → Create a checksum file with `sha256sum <file> > <file>_checksum.txt`.  
- **Timeout** → The CI runner enforces a hard time limit; the pipeline is designed to finish well within this bound.  
- **Simulation Mode Active** → Check the output logs for “Simulation Mode: Synthetic data generated”. This indicates that user‑provided data was missing and synthetic fallbacks were used.
