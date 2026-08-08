# llmXive: Extending "LatentSkill"

This project implements an automated pipeline to transform in-context textual skills into in-weight latent skills. It ingests pre-trained LoRA adapters, constructs a high-dimensional skill vector database, retrieves and interpolates skills based on natural language queries, and validates the synthesized adapters via environment logic.

## Features

- **Skill Vector Database**: Ingests LoRA A/B matrices from ALFWorld and Search-QA benchmarks, flattens them into normalized high-dimensional vectors, and builds a static CPU-compatible index.
- **Retrieval & Interpolation**: Queries the skill database using text embeddings (`all-MiniLM-L6-v2 (2607.07974, https://arxiv.org/abs/2607.07974)`) and synthesizes new LoRA adapters via unweighted mean or cosine-weighted averaging.
- **Validation**: Evaluates synthesized adapters on composite tasks using environment logic (ALFWorld/Search-QA)and performs statistical analysis (Benjamini-Hochberg correction).
- **Reproducibility**: Full pipeline reproducibility with pinned dependencies and deterministic seed handling.

## Installation

### Prerequisites

- Python 3.11+
- Git
- CPU with at least 7GB RAM (for inference)

### Setup

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd llmxive-follow-up-extending-latentskill
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. (Optional) Download the base model for evaluation:
 - Place `llama-2-7b-q4_0.gguf` in `data/models/`.
 - The model can be downloaded from HuggingFace or other official sources.

## Data Sources

The project relies on the following real data sources:

- **LoRA Weights**:
 - HuggingFace Dataset: `latent-skills/alfworld-weights`
 - HuggingFace Dataset: `latent-skills/searchqa-weights`
 - These datasets contain the pre-trained LoRA adapters (A and B matrices) for ALFWorld and Search-QA benchmarks.

- **Base Model**:
 - `llama-2-7b-q4_0.gguf` (placed in `data/models/`)

- **Benchmark Data**:
 - ALFWorld and Search-QA environment logic and test cases are accessed programmatically during evaluation.

See `data_sources.yaml` for canonical URLs and IDs.

## Usage

### 1. Ingest and Build Skill Index

Run the ingestion pipeline to download weights, flatten them, and build the skill vector database:

```bash
python code/src/ingestion/download_weights.py
python code/src/ingestion/flatten_lora.py
python code/src/retrieval/vector_db.py
```

**Output**: `data/processed/skill_index.npz`

### 2. Query and Synthesize Adapters

Given a natural language task description, retrieve relevant skills and synthesize a new LoRA adapter:

```bash
python code/src/retrieval/query.py --query "Your task description here"
```

**Output**: Synthesized LoRA adapter files in `artifacts/synthesized_adapters/`.

### 3. Evaluate Synthesized Adapters

Evaluate the synthesized adapters on composite tasks:

```bash
python code/src/evaluation/runner.py
```

**Output**: Success/failure logs and statistical reports in `data/results/`.

### 4. Generate Final Report

Compile all results into a final statistical report:

```bash
python code/src/evaluation/report_generator.py
```

**Output**: `data/results/stats_report.json`

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── ingestion/ # Data ingestion and preprocessing
│ │ ├── retrieval/ # Vector database and retrieval strategies
│ │ ├── evaluation/ # Evaluation and statistical analysis
│ │ ├── validation/ # Validation and reconstruction error checks
│ │ └── utils/ # Utilities (config, versioning)
│ └── validate/ # Citation and data source validation
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed data (e.g., skill_index.npz)
│ ├── results/ # Evaluation results and reports
│ └── models/ # Base LLM models
├── artifacts/
│ └── synthesized_adapters/ # Synthesized LoRA adapters
├── specs/ # Design documents and contracts
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└── README.md
```

## Validation

- **Data Source Verification**: Run `python code/src/validate/citation_check.py` to verify dataset URLs.
- **Linearity Check**: Run `python code/src/validation/linearity_check.py` to validate the linearity assumption between text-space and weight-space distances.
- **Reconstruction Error**: Run `python code/src/validation/reconstruction_error.py` to measure the cosine distance between synthesized and true weights.

## Contributing

Contributions are welcome! Please follow the project's coding standards (Black, Ruff) and ensure all tests pass before submitting a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.