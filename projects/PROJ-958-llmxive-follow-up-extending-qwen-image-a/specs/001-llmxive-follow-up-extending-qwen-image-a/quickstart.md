# Quickstart: llmXive follow-up: extending "Qwen-Image-Agent: Bridging the Context Gap in Real-World Image Generation"

## Prerequisites
- Python 3.11+
- `pip`
- Access to HuggingFace (for dataset download)
- ~10GB disk space (for datasets, images, and derived files)

## Installation

1. **Clone the repository** (if not already done) and navigate to the project root.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins `nltk`, `spacy`, `transformers`, `scikit-learn`, `statsmodels`, `pandas`, `numpy`, `textstat`.*

4. **Download NLTK data** (required for parsing):
   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('maxent_ne_chunker'); nltk.download('words'); nltk.download('stopwords')"
   ```

5. **Download Spacy model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Running the Pipeline

### 1. Validate Citations (Blocking Gate)
Run the Reference-Validator Agent to ensure all dataset citations are valid before proceeding:
```bash
python code/validate_citations.py
```
*This step is mandatory and blocks further execution if any citation is invalid.*

### 2. Download Raw Data
Run the data loader to fetch IA-Bench dataset (prompts and images):
```bash
python code/data_loader.py --download
```
*This creates `data/raw/prompts_ia_bench.jsonl` and downloads images to `data/raw/images/`.*

### 3. Compute Ambiguity Scores
```bash
python code/scoring.py
```
*Output: `data/derived/scoring_results.csv`*

### 4. Route & Simulate
```bash
python code/router.py
```
*Output: `data/derived/routing_logs.csv` (updated with latency/token stats and expanded text).*

### 5. Compute Fidelity (CLIP)
*Note: This step computes CLIP scores between the (original/expanded) prompt and the ground-truth image.*
```bash
python code/fidelity.py
```
*Output: `data/derived/fidelity_deltas.csv`*

### 6. Run Regression Analysis
```bash
python code/regression.py
```
*Output: `data/derived/regression_results.json` and plots in `data/plots/`*

### 7. Full Pipeline (One Command)
```bash
python code/main.py
```
*Includes the citation validation gate as the first step.*

## Testing

Run the unit tests to verify logic (e.g., routing thresholds, scoring independence):
```bash
pytest tests/unit/ -v
```

Run the integration test on a 100-prompt subset:
```bash
pytest tests/integration/ -v
```

## Expected Outputs
- **Console**: Logs showing routing decisions, progress bars for CLIP inference.
- **Files**:
  - `data/derived/scoring_results.csv`
  - `data/derived/routing_logs.csv`
  - `data/derived/fidelity_deltas.csv`
  - `data/derived/regression_results.json`
  - `data/plots/fidelity_curve.png` (Fidelity Delta vs. Ambiguity Score)
  - `data/plots/knee_point_detection.png`

## Troubleshooting
- **Memory Error**: If CLIP inference fails due to RAM, reduce `BATCH_SIZE` in `code/config.py` (default 8).
- **Parsing Error**: If `nltk` fails, ensure the `en_core_web_sm` model is installed.
- **Dataset Missing**: Ensure you have internet access for the initial `data_loader.py` run. The data is cached in `data/raw/`.
- **Citation Invalid**: If `validate_citations.py` fails, check the `spec.md` for incorrect dataset URLs.
