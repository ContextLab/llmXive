# llmXive: Extending "LatentSkill"

An automated science pipeline for constructing, retrieving, and validating latent skills from LoRA adapters. This project implements the research follow-up to "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills".

## Installation

1. Clone the repository and navigate to the project root.
2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
4. Ensure the required directories exist (created by T001c):
 ```bash
 mkdir -p data/raw data/processed data/results artifacts/figures
 ```

## Usage

The pipeline is executed in stages corresponding to the User Stories.

### Phase 1: Setup & Validation
Verify data sources and download weights:
```bash
python src/validate/citation_check.py
python src/ingestion/download_weights.py
```

### Phase 2: Ingestion (Skill Vector Database)
Flatten LoRA weights and build the vector index:
```bash
python src/ingestion/flatten_lora.py
python src/retrieval/vector_db.py
```

### Phase 3: Retrieval & Interpolation
Query the database and synthesize adapters:
```bash
python src/retrieval/query.py
python src/retrieval/strategies.py
```

### Phase 4: Validation (Linearity & Reconstruction)
Check linearity assumptions and reconstruction errors:
```bash
python src/validation/linearity_check.py
python src/validation/reconstruction_error.py
```

### Phase 5: Evaluation (Environment Logic)
Run the full evaluation loop, sensitivity sweeps, and statistical analysis:
```bash
python src/evaluation/runner.py
python src/evaluation/run_sensitivity_sweep.py
python src/evaluation/stats.py
```

### Generate Final Report
```bash
python src/evaluation/report_generator.py
```

## Data Sources

The project relies on the following verified data sources defined in `data_sources.yaml`:

- **ALFWorld Weights**: HuggingFace dataset `latent-skills/alfworld-weights` (Path: `weights/alfworld/*.npz`)
- **Search-QA Weights**: HuggingFace dataset `latent-skills/searchqa-weights` (Path: `weights/searchqa/*.npz`)
- **Base Model**: `TinyLlama/TinyLlama-Chat-v1.0` (Converted to GGUF format via `scripts/download_and_quantize_model.py`)

All raw data is stored in `data/raw/`, processed indices in `data/processed/`, and results in `data/results/`.

## Results

Upon successful execution of the pipeline, the following artifacts are generated:

- **Skill Index**: `data/processed/skill_index.npz` (Flattened, normalized skill vectors)
- **Synthesized Adapters**: `artifacts/synthesized_adapters/` (Generated LoRA weights)
- **Linearity Analysis**: `data/results/linearity_correlation.json` (Pearson correlation between text and weight spaces)
- **Reconstruction Error**: `data/results/reconstruction_error.json` (Cosine distance metrics)
- **Sensitivity Sweep**: `data/results/sensitivity.yaml` (Performance across different k values)
- **Statistical Report**: `data/results/stats_report.json` (Final statistical validation with BH correction)
- **Final Report**: `data/results/report_final.md` (Aggregated findings)