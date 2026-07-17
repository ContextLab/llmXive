# llmXive: Extending KVarN Variance-Normalized KV-Cache Quantization

This project implements a research pipeline to extend and evaluate the KVarN
(Variance-Normalized KV-Cache Quantization) method, focusing on mitigating
error accumulation in long-horizon autoregressive generation.

## Project Structure

```
.
 ├── code/ # Source code
 │ ├── data_generation/ # Synthetic data and ground truth generation
 │ ├── model_training/ # MLP training and baselines
 │ ├── simulation/ # Autoregressive simulation engine
 │ └── analysis/ # Statistical analysis and visualization
 ├── data/ # Generated artifacts
 │ ├── generated/ # Synthetic trajectories
 │ ├── models/ # Trained model weights
 │ ├── simulation/ # Simulation run results
 │ └── analysis/ # Analysis outputs
 ├── tests/ # Test suite
 │ ├── test_data_generation/
 │ ├── test_model_training/
 │ └── test_simulation/
 ├── requirements.txt # Python dependencies
 └── README.md # This file
```

## Prerequisites

- Python 3.11 or higher
- pip package manager

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Set up the directory structure:
 ```bash
 python code/setup_directories.py
 ```

## Usage

### Generate Data (User Story 1)
```bash
python code/data_generation/synthetic_attention.py
```

### Train Model (User Story 2)
```bash
python code/model_training/train.py
```

### Run Simulation (User Story 3)
```bash
python code/simulation/autoregressive_loop.py
```

### Run Tests
```bash
pytest tests/
```

## Development

- Formatting: `black code/ tests/`
- Linting: `ruff check code/ tests/`

## License

Research use only.
