# llmXive: Extending "Kairos: A Native World Model Stack for Physical AI"

**Project ID**: PROJ-888-llmxive-follow-up-extending-kairos-a-nat

## Overview

This project implements a follow-up study to the "Kairos" paper, focusing on extending the Native World Model Stack for Physical AI using discrete state representations. The research investigates the stability of discrete world models under varying quantization levels (4-bit, 6-bit, 8-bit, 16-bit) and noise injection, aiming to identify minimum information density thresholds for stable long-horizon prediction.

Key objectives include:
1. Converting continuous LIBERO dataset trajectories into discrete, JSON-serialized state vectors.
2. Training CPU-only adapted Kairos models on these discrete representations.
3. Performing statistical stability analysis (LMM) to map error growth to quantization bandwidth.

## Quickstart

### Prerequisites
- Python 3.9+
- pip
- ~7GB RAM (for dataset streaming)
- CPU-only environment (No CUDA required)

### Installation
1. Clone the repository and navigate to the project root.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

### Running the Pipeline
The main entry point orchestrates the download, quantization, noise injection, and validation steps.

```bash
# Validate configuration first
python code/utils/validate_config.py

# Run the full data pipeline (with streaming to manage memory)
python code/main.py --config config.yaml
```

### Output
Processed discrete state vectors will be saved to `data/processed/`.
Statistical analysis results will be stored in `results/`.

## Project Structure

```text
.
├── code/
│ ├── main.py # Orchestration logic
│ ├── config.py # Configuration (seeds, paths, quantization levels)
│ ├── data/ # Data processing modules
│ │ ├── download_libero.py # Streaming data fetcher
│ │ ├── quantize.py # Discretization logic
│ │ ├── noise.py # Noise injection
│ │ ├── schema.py # Data schemas
│ │ └── validation.py # Degeneracy checks
│ ├── models/ # Model adapters and training
│ │ ├── kairos_adapter.py # CPU-only model adaptation
│ │ ├── training_loop.py # Training logic
│ │ └── inference.py # Inference engine
│ ├── analysis/ # Statistical analysis
│ │ ├── metrics.py # Error metric calculation
│ │ └── stats.py # LMM and bootstrap analysis
│ └── utils/ # Utilities (logging, monitoring, checkpointing)
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Discrete state vectors
├── results/ # Analysis outputs
├── tests/ # Unit and integration tests
├── specs/ # Design documents
└── README.md
```

## Verification
To verify the setup:
1. Ensure `code/utils/validate_config.py` runs without errors.
2. Run the quickstart script to confirm data streaming works.
3. Check `state/directory_listing.txt` for the project structure.

## License
MIT License