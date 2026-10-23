# Quickstart: llmXive follow-up: extending "Self-Improving Language Models with Bidirectional Evolutionary Search"

## Prerequisites

- **Python**: 3.11+
- **Git**: For cloning the repository.
- **Hardware**: CPU‑only environment (tested on GitHub Actions free‑tier: multiple cores, ~7 GB RAM).
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
   pip install -r requirements.txt
   ```
   *Note: This installs CPU‑only versions of `transformers`, `torch`, `optimum`, etc. No CUDA dependencies.*

## Dataset Curation & Pilot (Phase 0)

The dataset is generated programmatically to ensure deterministic verification and includes a scaling subset for complexity analysis.

1. **Run the pilot experiment**:
   ```bash
   python -m code.main --pilot
   ```
   - This generates a minimal dataset (e.g., 4x4 Sudoku and 4x4 grid pathfinding) and runs a deterministic verification pass.
   - The pilot writes its result to `data/processed/pilot_result.jsonl`.
   - **Verification**: Run `pytest tests/unit/` to ensure the generator and verifier work correctly.

## Running the Full Experiment (Phase 1)

*Note: These commands require the completion of Phase 1 implementation tasks (T001-T003).*

1. **Symbolic‑guided BES**:
   ```bash
   python -m code.main --method symbolic --pop-size 50 --generations 20 --output data/processed/symbolic_run.jsonl
   ```
   - Uses a small CPU LLM for forward steps and the symbolic planner for backward steps.

2. **Neural‑verifier baseline**:
   ```bash
   python -m code.main --method neural --pop-size 50 --generations 20 --output data/processed/neural_run.jsonl
   ```
   - Uses the same forward LLM but a learned verifier (DistilBERT) for the backward step.

## Analysis (Phase 2)

*Note: These commands require the completion of Phase 2 implementation tasks (T004-T009).*

1. **Statistical analysis**:
   ```bash
   python -m code.analysis.stats --symbolic data/processed/symbolic_run.jsonl --neural data/processed/neural_run.jsonl --output data/processed/results.json
   ```
   - Produces `p_value_z`, `p_value_t`, and other summary statistics in `results.json`.

## Verification & Testing

- **Unit tests**:
   ```bash
   pytest tests/unit/
   ```
   - Verifies puzzle generation, verifier correctness, and symbolic planner logic.

- **Integration tests**:
   ```bash
   pytest tests/integration/
   ```
   - Runs a mini BES loop to ensure end‑to‑end flow.

## Reproducibility

- **Seeds**: The pilot and full runs use a deterministic seed (default = 42). You can override with `--seed`.
- **Checksums**: Verify `data/raw/` and `data/processed/` against the SHA‑256 hashes recorded in `state/...yaml`.
- **Environment**: Re-run on a fresh GitHub Actions runner to confirm results.

## Troubleshooting

- **Memory error**: Reduce `--pop-size` or `--generations`.
- **Verifier timeout**: Ensure `code/dataset/verifier.py` runs in < 100 ms.
- **LLM slow**: The script will automatically fall back to a smaller model (TinyBERT) if needed.
