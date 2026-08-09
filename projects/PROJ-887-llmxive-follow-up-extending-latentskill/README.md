# llmXive: Extending LatentSkill

An automated science pipeline for transforming in-context textual skills into in-weight latent skills. This project implements the retrieval, interpolation, and evaluation of LoRA adapters based on task descriptions.

## Project Overview

llmXive investigates the linearity of skill spaces by:
1. Ingesting pre-trained LoRA adapters (A and B matrices) from ALFWorld and Search-QA benchmarks.
2. Flattening and normalizing these weights into a high-dimensional skill vector database.
3. Retrieving nearest neighbors based on text embeddings of task descriptions.
4. Synthesizing new adapters via interpolation strategies (unweighted mean, cosine-weighted averaging).
5. Validating performance on composite tasks using a CPU-optimized TinyLlama model.

## Prerequisites

- Python 3.11+
- CPU-only environment (Max 7GB RAM for inference)
- `llama-cpp-python` support

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd llmXive-follow-up-extending-latentskill
 ```

2. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `faiss-cpu` is intentionally excluded as per project constraints.*

3. **Setup Data Directories**:
 Ensure the following directories exist (created via `T001c`):
 - `data/raw/`
 - `data/processed/`
 - `data/results/`
 - `artifacts/synthesized_adapters/`
 - `specs/001-lattentskill-retrieval-geometry/contracts/`

## Data Sources

The project relies on specific HuggingFace datasets for LoRA weights. If real weights are unavailable, the system falls back to a documented proxy generation method (T012).

- **ALFWorld Weights**: `latent-skills/alfworld-weights` (Path: `weights/alfworld/*.npz`)
- **Search-QA Weights**: `latent-skills/searchqa-weights` (Path: `weights/searchqa/*.npz`)

**Verification**:
Run the citation check script to verify source availability before ingestion:
```bash
python code/src/validate/citation_check.py
```

## Usage

### 1. Ingest and Flatten Weights (User Story 1)

Download weights (or generate proxies) and build the skill vector index.

```bash
# Download weights (T012)
python code/src/ingestion/download_weights.py

# Flatten and normalize (T013)
python code/src/ingestion/flatten_lora.py

# Build the static index (T014b)
python code/scripts/run_t014b.py
```
*Output*: `data/processed/skill_index.npz`

### 2. Retrieve and Synthesize Adapters (User Story 2)

Query the database with a task description and synthesize a new adapter.

```bash
# Run the full synthesis pipeline (T019, T022a, T022b)
python code/scripts/run_t022b.py
```
*Output*: Synthesized adapters in `artifacts/synthesized_adapters/`

### 3. Evaluation (User Story 3)

Evaluate synthesized adapters on the TinyLlama model.

```bash
# Ensure base model is downloaded and quantized (T026a)
python code/scripts/download_and_quantize_model.py

# Run evaluation (T026)
python code/src/evaluation/runner.py
```
*Output*: Statistical report in `data/results/stats_report.json`

## Project Structure

```text
.
├── code/
│ ├── src/
│ │ ├── ingestion/ # Weight download and flattening
│ │ ├── retrieval/ # Vector DB, query, and synthesis strategies
│ │ ├── evaluation/ # Runner, stats, and report generation
│ │ ├── validate/ # Citation and schema checks
│ │ └── utils/ # Config and versioning
│ └── scripts/ # Execution wrappers for specific tasks
├── data/
│ ├── raw/ # Raw weights (real or proxy)
│ ├── processed/ # Flattened vectors, indices, ground truth
│ └── results/ # Final statistical reports
├── artifacts/
│ └── synthesized_adapters/ # Generated LoRA files
├── tests/ # Unit, integration, and contract tests
├── specs/ # Design documents and contracts
├── requirements.txt
└── README.md
```

## Validation & Testing

Run the full test suite to ensure pipeline integrity:

```bash
pytest tests/
```

Specific validation steps:
- **Linearity Check**: `data/results/linearity_check.json` (T030)
- **Reconstruction Error**: `data/results/reconstruction_error.json` (T022d)
- **Statistical Report**: `data/results/stats_report.json` (T032)

## License

[Insert License Information]