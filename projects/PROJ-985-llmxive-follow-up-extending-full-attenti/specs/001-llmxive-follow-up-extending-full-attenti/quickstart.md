# Quickstart: llmXive Follow-up: Extending "Full Attention Strikes Back"

## Prerequisites

-   Python 3.11+
-   7 GB+ RAM (CPU)
-   Hugging Face account (if required for Llama-3-8B or Gemma-2-9B).
-   KenLM library installed (`pip install kenlm` or system install).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-985-llmxive-follow-up-extending-full-attenti
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### Step 1: Ground Truth Extraction (CPU, Sampled Subset)
This step generates the ground truth labels using Llama-3-8B and RTPurbo on a **sampled subset** (50 documents) to fit CI limits.
```bash
python code/data/extract_ground_truth.py --num-docs 50 --output data/intermediate/ground_truth.parquet
```

### Step 2: Feature Computation
Compute static features (entropy, POS, **KenLM perplexity**) for all tokens.
```bash
python code/data/compute_features.py --input data/intermediate/ground_truth.parquet --output data/derived/features.parquet
```

### Step 3: Merge and Prepare Dataset
Join features and labels into a single dataset.
```bash
python code/data/merge_dataset.py --features data/derived/features.parquet --output data/derived/merged_dataset.parquet
```

### Step 4: Train Static Predictor (5 Seeds)
Train the Decision Tree/Logistic Regression model with 5 random seeds to estimate variance.
```bash
python code/models/train_static.py --input data/derived/merged_dataset.parquet --output data/models/static_model.pkl --num-seeds 5
```

### Step 5: Derive Heuristic Rules
Extract hard rules from the trained model.
```bash
python code/models/derive_rules.py --model data/models/static_model.pkl --output data/models/static_rules.json
```

### Step 6: Evaluation (Llama-3-8B Baseline)
Run the evaluation suite against Full, Learned, and Static baselines on Llama-3-8B.
```bash
python code/evaluation/run_baselines.py --rules data/models/static_rules.json --output data/results/metrics.csv
```

### Step 7: Cross-Model Validation (Gemma-2-9B)
Evaluate the derived static rules on a different architecture (Gemma-2-9B).
```bash
python code/evaluation/cross_model_eval.py --rules data/models/static_rules.json --model gemma-2-9b --output data/results/cross_model_metrics.csv
```

### Step 8: Statistical Analysis
Perform paired t-tests on document-level performance differences.
```bash
python code/evaluation/stats_analysis.py --input data/results/metrics.csv --output data/results/statistical_report.txt
```

## Verification

-   **Check Ground Truth**: Ensure `data/intermediate/ground_truth.parquet` contains `is_rtpurbo_selected` labels.
-   **Check Features**: Ensure `data/derived/features.parquet` contains `entropy`, `pos_tag`, and `local_perplexity`.
-   **Check Rules**: Ensure `data/models/static_rules.json` contains valid thresholds and POS lists.
-   **Check Metrics**: Ensure `data/results/metrics.csv` contains perplexity and exact match scores for all three methods.
-   **Check Cross-Model**: Ensure `data/results/cross_model_metrics.csv` contains performance on Gemma-2-9B.

## Troubleshooting

-   **OOM Error**: If you encounter Out of Memory errors, reduce `--num-docs` in Step 1.
-   **KenLM Error**: Ensure KenLM is installed and the model file is present.
-   **POS Tagging Errors**: Ensure `spacy` models are downloaded (`python -m spacy download en_core_web_sm`).