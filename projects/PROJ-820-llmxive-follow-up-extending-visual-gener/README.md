# llmXive: Visual Generation in the New Era

This project implements a research pipeline for generating physics-constrained images using diffusion models.

## Project Structure

- `code/`: Source code for simulation, generation, evaluation, and analysis.
- `data/`:
 - `raw/`: Input scene descriptions.
 - `derived/`: Intermediate artifacts (physics constraints, prompts, generated images, evaluation results).
 - `processed/`: Final analysis results.
- `specs/`: Feature specifications and contracts.
- `tests/`: Unit and integration tests.

## Prerequisites

- Python 3.11+
- CPU-only environment (no CUDA required, but supported if available)
- 16GB+ RAM recommended for model loading

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Quick Start

### 1. Setup (Phase 1 & 2)
Ensure directories are created and configuration is set:
```bash
python code/setup/create_directories.py
python code/setup/configure_tools.py
```

### 2. Generate Physics Constraints (User Story 1)
```bash
python code/simulation/physics_engine.py
```

### 3. Generate Prompts (User Story 1)
```bash
python code/generation/prompt_engine.py
```

### 4. Generate Images (User Story 2 - T018)
```bash
python code/generation/diffusion_runner.py
```
This will generate images for Baseline, Experimental, and Control groups in `data/derived/generated_images/`.

### 5. Evaluate and Analyze (User Story 3)
```bash
python code/evaluation/detector.py
python code/analysis/statistics.py
```

## Running Tests

```bash
pytest tests/ -v
```

## Results

- Generated images are stored in `data/derived/generated_images/{group}/{scene_id}.png`.
- Evaluation results in `data/derived/evaluation_results/`.
- Final analysis in `data/processed/final_analysis.csv`.

## License

MIT License
