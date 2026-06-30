# llmXive: Survey of Large Audio Language Models – Hallucination Analysis

This repository implements an automated pipeline to evaluate hallucination rates in Large Audio Language Models (LALMs) across three domains: Speech, Music, and Environmental Sounds.

## Project Structure

```
.
├── code/ # Core implementation modules
├── data/ # Raw and processed datasets
├── results/ # Analysis outputs (CSV, JSON)
├── tests/ # Unit, integration, and contract tests
├── docs/ # Documentation
├── specs/ # Feature specifications and design docs
├── requirements.txt # Python dependencies
└── quickstart.md # Execution guide
```

## Key Modules

- **`code/run_inference.py`**: Orchestrates model loading, caption generation, and hallucination detection.
- **`code/detect_hallucination.py`**: Implements rule-based detection with WordNet expansion and fuzzy matching.
- **`code/estimate_training_data.py`**: Parses model cards to estimate training data volume.
- **`code/analyze_correlation.py`**: Computes Spearman correlations and Cohen’s κ for human validation.
- **`code/submit_crowd_job.py`** & **`code/retrieve_crowd_judgments.py`**: Interfaces with Prolific for human validation.

## Dependencies

See `requirements.txt` for the full list. Key packages include:
- `torch` (CPU-only)
- `transformers`, `librosa`, `datasets`
- `scikit-learn`, `pandas`, `nltk`
- `fuzzywuzzy`, `pdfplumber`, `PyPDF2`

## Execution

Refer to `quickstart.md` for detailed steps to run the full pipeline.

## License

MIT License.
