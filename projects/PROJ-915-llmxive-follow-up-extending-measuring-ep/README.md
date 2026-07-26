# llmXive: Measuring Epistemic Resilience of LLMs Under Misleading Medical Context

Automated science pipeline for measuring epistemic resilience in language models when exposed to misleading medical contexts.

## Project Structure

```
.
├── code/ # Pipeline implementation
│ ├── config.py # Configuration management
│ ├── secrets_manager.py # API key and secrets handling
│ ├── data_models.py # Data structures
│ ├── ingestion.py # Dataset download and filtering
│ ├── features.py # Linguistic feature extraction
│ ├── inference.py # LLM inference
│ ├── labeling.py # Adherence labeling
│ ├── modeling.py # Statistical modeling
│ └──...
├── data/
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Processed data with features
│ ├── interim/ # Intermediate results
│ └── results/ # Final analysis results
├── tests/ # Test suite
├── state/ # Pipeline state and checksums
├──.env.example # Environment variables template
├── requirements.txt # Python dependencies
└── README.md
```

## Setup

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd llmXive
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your API keys:

```bash
cp.env.example.env
```

Edit `.env` and add:

- `HF_TOKEN`: Your HuggingFace API token (required for dataset/model access)
- `PROLIFIC_API_KEY`: Your Prolific API key (required for rater recruitment)

> **Security Note**: Never commit `.env` to version control. It is already in `.gitignore`.

### 3. Validate Configuration

```bash
python -c "from config import Config; c = Config(); c.validate()"
```

## Pipeline Execution

The pipeline runs through several phases:

1. **Data Ingestion**: Download and filter MedMisBench dataset
2. **Feature Extraction**: Compute linguistic features for prompts
3. **Model Inference**: Generate responses using quantized LLM
4. **Labeling**: Classify responses as adherent, resilient, or refusal
5. **Statistical Analysis**: Perform regression and sensitivity analysis

Run the full pipeline:

```bash
python code/pipeline.py
```

Or run individual stages:

```bash
python code/ingestion.py
python code/features.py
python code/inference.py
```

## Configuration

Create a `config.yaml` file in the project root to override defaults:

```yaml
seeds:
 random_seed: 42
timeouts:
 inference_timeout_seconds: 300
model:
 model_name: "TinyLlama-1.1B-Chat"
 quantization_bits: 4
```

## Testing

```bash
pytest tests/ -v --cov=code
```

## License

MIT License - See LICENSE file for details.