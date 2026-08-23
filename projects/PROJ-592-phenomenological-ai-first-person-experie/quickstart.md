# Phenomenological AI: First-Person Experience Modeling - Quickstart

This guide provides instructions for running the Phenomenological AI pipeline locally or on a CI runner.

## Prerequisites

- Python 3.10+
- `llama-cpp-python` (for model inference)
- `datasets` (for control corpus)
- `pandas`, `numpy`, `scipy` (for analysis)

Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

- `code/`: Source code for generation, analysis, and validation
- `data/`: Raw and processed data
- `specs/`: Feature specifications and contracts
- `tests/`: Unit and integration tests

## Configuration

Create a `config.yaml` file in the project root with the following parameters:

```yaml
model_path: "models/phi-2.Q4_K_M.gguf"
output_dir: "data/processed"
num_samples: 100
strategies:
 - Direct
 - Hypothetical
 - Comparative
 - Role-play
```

## Usage

The pipeline is orchestrated via `code/main.py`. Below are the primary modes of operation.

### 1. Generation Mode

Generate phenomenological reports using the specified model and prompting strategies.

```bash
python code/main.py --mode generation --config config.yaml
```

To limit the number of samples for testing:
```bash
python code/main.py --mode generation --limit 10 --config config.yaml
```

### 2. Analysis Mode

Compute phenomenological metrics (consistency, stability, marker presence) on generated reports.

```bash
python code/main.py --mode analysis --config config.yaml
```

This will produce `data/processed/validity_scores.csv` and `data/processed/stats_report.json`.

### 3. Validation Mode

Prepare samples for human rating and compute inter-rater reliability.

```bash
python code/main.py --mode validate --config config.yaml
```

This will produce `data/qualitative/sampling_list.csv` and `data/qualitative/ratings.csv` (if rated).

### 4. Full Pipeline

Run the entire pipeline from generation to validation.

```bash
python code/main.py --mode full --config config.yaml
```

## Local Reproduction (Optional)

For users with local hardware (>=16GB RAM), you can run the Phi-2 checkpoint using the local runner:

```bash
python code/generation/runner_local.py --test
```

This generates a minimal sample set and writes it to `data/raw/local_generation_test.json`.

## Verification

After running the pipeline, verify the outputs:

```bash
# Check generation output
ls -la data/raw/generation_batch_*.json

# Check analysis output
ls -la data/processed/validity_scores.csv data/processed/stats_report.json

# Check validation output
ls -la data/qualitative/sampling_list.csv
```

## Troubleshooting

- **Model Loading Errors**: Ensure the GGUF model file is downloaded and placed at the path specified in `config.yaml`.
- **CUDA Errors**: If using a GPU, ensure `llama-cpp-python` is installed with CUDA support.
- **Dataset Errors**: If the control corpus dataset is unreachable, check your internet connection or switch to a mirrored dataset.

## License

This project is licensed under the MIT License.
