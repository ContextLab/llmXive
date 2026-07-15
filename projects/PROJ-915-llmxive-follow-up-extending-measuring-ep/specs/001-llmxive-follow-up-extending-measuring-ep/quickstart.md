# Quickstart: llmXive follow-up: extending "Measuring Epistemic Resilience of LLMs Under Misleading Medical Context"

## Prerequisites

- **Python**: 3.11 or higher.
- **Dependencies**: `requirements.txt` (pinned versions).
- **Hardware**: 2 CPU cores, 7 GB RAM (GitHub Actions Free Tier compatible).
- **Disk**: ~14 GB free space.

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-915-llmxive-follow-up-extending-measuring-ep
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

> **Note**: `llama-cpp-python` provides pre‑built wheels for Linux/macOS; on Windows use the `--no-binary` flag as documented.

## Running the Full Pipeline

```bash
python code/main.py
```

The script executes the following ordered phases:

1. **Data Verification & Ingestion** – downloads MedMisBench, checks for `false_claim`, falls back to regex extraction.
2. **Feature Extraction** – creates `data/processed/features.csv`.
3. **Model Inference** – CPU‑only 1.1B‑parameter quantized model (`TinyLlama`); outputs `data/interim/labeled_responses.csv`.
4. **External Fact Retrieval & Labeling** – queries PubMed via Entrez, computes semantic similarities, writes `data/interim/labeling_meta.csv`.
5. **Human Outcome Validation Gate** – runs a 50‑sample audit; aborts if κ < 0.7.
6. **Statistical Modeling** – produces `data/results/regression_results.csv` and `data/results/convergence_log.csv`.
7. **Sensitivity Analysis** – generates `data/results/sensitivity_analysis.csv`.
8. **Manual Annotation Pilot** – launches a Prolific survey (see `code/annotation.py`); results saved as `data/results/annotation_pilot.csv`.

## Configuration (`code/config.py`)

- `MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"` (quantized at runtime).  
- `MAX_PROMPTS = -1` (process all; set a lower number for quick tests).  
- `SEED = 42`.  
- `THRESHOLDS = [0.05, 0.10]`.  
- `TIMEOUT_PER_PROMPT = 30` (seconds).  

## Expected Outputs

| File | Description |
| :--- | :--- |
| `data/raw/medmisb_filtered.jsonl` | Filtered MedMisBench subset. |
| `data/processed/features.csv` | Linguistic features. |
| `data/interim/labeled_responses.csv` | Model outputs + labels. |
| `data/interim/labeling_meta.csv` | Similarity scores & external facts. |
| `data/results/regression_results.csv` | Logistic regression tables. |
| `data/results/convergence_log.csv` | Convergence status / Firth fallback info. |
| `data/results/sensitivity_analysis.csv` | Threshold sweep report. |
| `data/results/annotation_pilot.csv` | Human authority density scores. |
| `data/results/baseline_asr.yaml` | Baseline ASR reference. |
| `pipeline_log.json` | Runtime, checksum, and timing information. |

## Validation Checklist

1. **Row Count** – `features.csv` rows ≥ 500.  
2. **Label Integrity** – `adherence_label` values only 0, 1, 2.  
3. **Safety Flag** – `safety_refusal` column present.  
4. **Human Validation** – κ ≥ 0.7 logged in `pipeline_log.json`.  
5. **Runtime** – total elapsed time ≤ 6 h (checked automatically).  

## Troubleshooting

- **OOM** – Reduce `MAX_PROMPTS` or switch to a smaller model (e.g., `TinyLlama` is already the smallest viable option).  
- **Inference Timeout** – Increase `TIMEOUT_PER_PROMPT` or reduce `MAX_PROMPTS`; the pipeline will abort if the limit is exceeded.  
- **Missing `false_claim`** – Verify the dataset version; the pipeline will attempt regex extraction and warn if both fail.  