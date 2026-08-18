# llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

## Project Overview
This project implements a virtual tactile estimation system for zero-shot adaptation
to unseen damping and friction conditions in robotic manipulation tasks.

## Installation

### Prerequisites
- Python 3.9+
- pip

### Setup
1. Clone the repository
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Usage

### Data Generation
```bash
python code/generator.py --count 30 --seed 42 --friction-min 0.1 --friction-max 1.2 --output data/generated/
```

### Training
```bash
python code/train.py --config configs/training.yaml
```

### Evaluation
```bash
python code/evaluate.py --objects data/generated/ --output data/results/eval_logs.csv
```

### Analysis
```bash
python code/analysis.py --input data/results/aggregated.csv
```

## Contribution Guidelines
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

Please ensure all tests pass before submitting PRs.
Follow the coding standards and add appropriate documentation.
