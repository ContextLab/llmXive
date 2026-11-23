# llmXive: Data-Agnostic Quantization for Diffusion Models

This project implements the research pipeline for "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion".
It explores the correlation between prompt semantic entropy and DiT activation variance to optimize quantization strategies.

## Project Structure

```
code/
├── analysis/ # Entropy, clustering, router logic
├── data/ # Data download and preprocessing
├── evaluation/ # Metrics (FID, CLIP, MSE)
├── models/ # DiT wrappers and model loaders
├── quantization/ # W2A4 engine and static baseline
├── runners/ # Modular orchestration scripts (T037)
├── utils/ # GPU offload, security, streaming
├── validation/ # Validation gates
├── config.py # Configuration
├── main.py # Main entry point
data/
├── raw/ # Raw datasets
├── processed/ # Processed data (prompts, matrices, results)
tests/
├── unit/ # Unit tests
└── integration/ # Integration tests
```

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Modular Runners (Recommended)

The pipeline is now organized into modular runners in `code/runners/`.

**Correlation Analysis (T017):**
```bash
cd code
python runners/correlation_runner.py
```

**Router Inference (T029):**
```bash
cd code
python runners/router_inference_runner.py
```

### Legacy Scripts

Legacy scripts in `code/` (e.g., `run_correlation.py`) are still available but deprecated in favor of the modular runners.

## Validation Gates

- **Phase 2.5**: Validates correlation significance (p < 0.05) before proceeding to router implementation.
- Run `python code/main_validation.py` to execute the validation gate.

## GPU Execution

The pipeline supports GPU offloading. If running on CPU and GPU is required, the system will trigger the offload mechanism (T041).

## Data Hygiene

All data is sourced from real datasets (MS-COCO, HuggingFace). [UNRESOLVED-CLAIM: c_28ce39bd — status=not_enough_info] No synthetic data is used. [UNRESOLVED-CLAIM: c_1740742a — status=not_enough_info]

## License

MIT
