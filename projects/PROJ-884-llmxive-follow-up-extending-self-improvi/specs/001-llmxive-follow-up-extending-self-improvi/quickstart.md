# Quickstart: llmXive follow-up: extending "Self-Improving Language Models with Bidirectional Evolutionary Search"

## Prerequisites

- **Python**: 3.11+
- **Git**: For cloning the repository.
- **Hardware**: CPU-only environment (tested on GitHub Actions free-tier: multiple cores, ~7GB RAM).
- **Dependencies**: `requirements.txt` (pins all versions).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-884-llmxive-follow-up-extending-self-improvi
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: This installs CPU-only versions of `transformers`, `torch`, `optimum`, etc. No CUDA dependencies.*

## Dataset Curation (Phase 0)

The dataset is generated programmatically to ensure deterministic verification and includes a scaling subset for complexity analysis.

1. **Generate the puzzle dataset**:
   ```bash
   python code/dataset/generator.py --count 500 --output data/raw/puzzles.jsonl --scaling
   ```
   - This creates 500 puzzle instances (including a scaling subset) and their corresponding Python verifier scripts in `data/raw/`.
   - **Verification**: Run `python tests/unit/test_verifier.py` to ensure all verifiers return valid/invalid correctly.

## Running the Experiment (Phase 1)

1. **Execute the Symbolic-Guided BES**:
   ```bash
   python code/main.py --method symbolic --pop-size 50 --generations 20 --output data/processed/symbolic_run.jsonl
   ```
   - Uses a small CPU LLM for forward steps and the symbolic planner for backward steps.
   - Logs success rates and costs.

2. **Execute the Learned Verifier Baseline**:
   ```bash
   python code/main.py --method neural --pop-size 50 --generations 20 --output data/processed/neural_run.jsonl
   ```
   - Uses a small CPU LLM for forward steps and a learned verifier (DistilBERT) for backward steps.
   - If DistilBERT is too slow, the script will automatically switch to TinyBERT or CPU-quantized model.

## Analysis (Phase 2)

1. **Run statistical analysis**:
   ```bash
   python code/analysis/stats.py --symbolic data/processed/symbolic_run.jsonl --neural data/processed/neural_run.jsonl --output data/processed/results.json
   ```
   - Outputs `p_value_z` (success rate - TOST) and `p_value_t` (cost) to `results.json`.
   - Includes `logical_contradiction_rate` for the symbolic planner.

## Verification & Testing

- **Unit Tests**:
  ```bash
  pytest tests/unit/
  ```
  - Verifies puzzle generation, verifier correctness, and symbolic planner logic.

- **Integration Tests**:
  ```bash
  pytest tests/integration/
  ```
  - Runs a mini BES loop to ensure end-to-end flow.

## Reproducibility

- **Seeds**: Set `PYTHONHASHSEED` and random seeds in `code/main.py` (default: 42).
- **Checksums**: Verify `data/raw/` and `data/processed/` checksums against `state/...yaml`.
- **Environment**: Re-run on a fresh GitHub Actions runner to confirm results.

## Troubleshooting

- **Memory Error**: Reduce `--pop-size` or `--generations` in `main.py`.
- **Verifier Timeout**: Ensure `code/dataset/verifier.py` is optimized (<100ms).
- **LLM Slow**: If inference is too slow, the script will automatically switch to a smaller model (TinyBERT) or quantized version.