# Quickstart: llmXive follow-up: extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

## Prerequisites

- **Python**: 3.11+
- **System**: Linux (Ubuntu 22.04 recommended), 8 GB+ RAM, Adequate disk storage capacity.
- **Dependencies**: `pip install -r code/requirements.txt`

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-880-llmxive-follow-up-extending-your-unembed
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

4. **Download data** (Optional, for local debugging):
   ```bash
   python code/data/download.py --dataset oscar --language fr
   ```

## Running the Pipeline

### Full Execution

To run the complete analysis (SVD, Alignment, Similarity, Attribution, Bootstrap, WALS):

```bash
python code/main.py --config config/default.yaml
```

This will:
1. Download/stream datasets (OSCAR, RedPajama, WALS).
2. Extract edge spectrum subspaces for Llama, Mistral, BLOOM.
3. Align subspaces via Procrustes (Phase 0).
4. Compute similarity matrices.
5. Perform token attribution.
6. Run the label permutation bootstrap test.
7. Validate against WALS.
8. Record hashes and save results to `data/processed/`.

### Individual Phases

- **Extract & Align Subspaces**:
  ```bash
  python code/main.py --phase alignment
  ```
- **Compute Similarity**:
  ```bash
  python code/main.py --phase similarity
  ```
- **Token Attribution**:
  ```bash
  python code/main.py --phase attribution
  ```
- **Statistical Test**:
  ```bash
  python code/main.py --phase bootstrap
  ```

## Output Inspection

After completion, check the results:

- **Similarity Report**: `data/processed/similarity_report.json`
- **Token Attribution**: `data/processed/token_attribution.json`
- **Bootstrap Results**: `data/processed/permutation_result.json`
- **WALS Validation**: `data/processed/wals_validation.json`
- **SVD Details**: `data/processed/spectrum_output.json`

### Example Output (similarity_report.json)
```json
{
  "model_pairs": [
    {
      "model_a": "Llama-3-EN",
      "model_b": "BLOOM-Multilingual",
      "cosine_similarity": 0.87,
      "alignment_method": "procrustes_shared_vocab",
      "confidence_interval": [0.85, 0.89]
    }
  ]
}
```

## Troubleshooting

- **OOM Error**: Ensure `load_in_8bit=True` is used in `code/analysis/svd_extractor.py`. If still failing, reduce `k` (top-$k$) to 50.
- **Data Missing**: If `data/raw/` is empty, run the download script or ensure internet access for streaming.
- **WALS Error**: If WALS data is missing, the pipeline will skip the correlation step and log a warning.