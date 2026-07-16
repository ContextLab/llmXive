# Quickstart: llmXive Follow-up: Extending AgentDoG 1.5 with Zero-Shot Drift Detection

## Prerequisites

- Python 3.11 or higher
- `pip` or `poetry`
- Access to HuggingFace Hub (for model and dataset download)

## Installation

1. **Clone the repository** and navigate to the project directory:
   ```bash
   cd projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins `sentence-transformers`, `scikit-learn`, `pandas`, `numpy`, `datasets`, `jsonschema`, and `statsmodels`.*

## Running the Pipeline

### 1. Generate Taxonomy Centroids
This step creates the fixed embeddings for the AgentDoG 1.5 safety taxonomy.
```bash
python code/taxonomy_builder.py
```
*Output*: `data/processed/centroids.npy` and `data/processed/taxonomy_metadata.json`.

### 2. Compute Drift Scores
Process a batch of agent logs and calculate their drift scores.
```bash
python code/main.py --input data/raw/logs.jsonl --output data/processed/drift_scores.csv
```
*Output*: `data/processed/drift_scores.csv` containing `log_id`, `drift_score`, `nearest_category_id`.

### 3. Prepare Annotator Data (Blinded)
Generate stratified CSVs for human annotation, ensuring the `drift_score` is removed.
```bash
python code/annotator_interface.py --scores data/processed/drift_scores.csv --output data/processed/blind_annotations.csv
```
*Output*: `data/processed/blind_annotations.csv` (columns: `log_id`, `text`, `label` - no score).

### 4. Validate Results (Simulation)
Run the statistical validation against a simulated ground truth (or load real annotations).
```bash
python code/validation.py --scores data/processed/drift_scores.csv --labels data/raw/annotations_gold.csv
```
*Output*: Console report with Mann-Whitney U p-value, Odds Ratio, and AUC-ROC.

### 5. Compare with Baseline (Optional)
Compare drift scores against a zero-shot LLM classifier (requires API key).
```bash
python code/comparison.py --scores data/processed/drift_scores.csv --labels data/raw/annotations_gold.csv --api-key $LLM_API_KEY
```

## Verifying Reproducibility

To ensure the results are reproducible, run the end-to-end test:
```bash
pytest tests/integration/test_end_to_end.py -v
```
This test verifies that:
- The same inputs produce the same outputs (deterministic seeds).
- The Drift Score distribution matches the expected range.
- Statistical tests return the expected p-values (within tolerance).
- Contract validation passes (`test_contracts.py`).

## Troubleshooting

- **Memory Error**: If you encounter OOM errors, reduce the batch size in `config.py` (default: 100).
- **Dataset Not Found**: Ensure you are logged into HuggingFace (`huggingface-cli login`) if the dataset is gated (though the verified sources here are public).
- **Model Loading Failure**: The `all-MiniLM-L6-v2` model is cached after the first download. If it fails, check your internet connection.