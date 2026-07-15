# Quickstart: Linguistic Accommodation & Human‑Rated Empathy

## 1. Prerequisites

- Python 3.11+
- `pip`
- ≤ 7 GB RAM
- Internet access (for dataset download and human‑rating collection)

## 2. Installation

```bash
# Clone the repository (or cd to the project root)
git clone <repo-url>
cd projects/PROJ-391-the-impact-of-linguistic-accommodation-o

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt

# Download the small English spaCy model
python -m spacy download en_core_web_sm
```

## 3. Data Collection (FR‑010)

```bash
# Phase 0a: collect human empathy ratings (requires IRB‑approved consent)
python code/00_collect_human_empathy.py
# This script will prompt the annotator(s) to rate AI responses and will
# produce data/raw/human_empathy/human_empathy.csv.
```

## 4. Running the Full Pipeline

All steps must be run in order; each script produces the next script’s input.

| Step | Command | Output |
| ---- | ------- | ------ |
| 0b | `python code/01_ingest_and_preprocess.py` | `data/raw/daily_dialog_raw.csv` |
| 1 | `python code/02_map_emotion_score.py` | `data/processed/emotion_mapped.csv` |
| 2 | `python code/03_compute_metrics.py` | `data/processed/metrics.csv` |
| 3 | `python code/04_define_sampling_strategy.py` | `config/sampling_config.json` |
| 4 | `python code/05_sensitivity_analysis.py` | `outputs/reports/sensitivity_results.json` |
| 5 | `python code/06_generate_topics.py` | `data/processed/lda_topics.csv` |
| 6 | `python code/07_analyze_correlations.py` | `outputs/reports/correlation_summary.json` + `outputs/figures/scatter_plot.png` |
| 7 | `python code/08_regression_control.py` | `outputs/reports/regression_summary.json` |
| 8 | `python code/09_manual_validation.py` | `outputs/reports/validation_summary.json` |

## 5. Verification

```bash
pytest tests/
```

## 6. Troubleshooting

- **MemoryError** in any step: reduce batch size in `config.py`.  
- **Bootstrap non‑convergence**: check `bootstrap_results.json`; the pipeline will abort with an error if CI < 0.01 is not reached after 50 000 iterations.  
- **Missing spaCy model**: ensure `en_core_web_sm` is installed; run `python -m spacy download en_core_web_sm` again.  
