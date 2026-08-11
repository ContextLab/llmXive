# llmXive Follow-up: Extending "Zone of Proximal Policy Optimization"

This project implements a follow-up study to the ZPPO paper, introducing Confidence-Adaptive Pruning (CAP) to improve data efficiency.

## Setup
```bash
pip install -r requirements.txt
```

## Running the Pipeline
```bash
python code/main.py --num-seeds 10 --num-tasks 10
```

## Project Structure
- `code/`: Source code
- `contracts/`: Schema definitions
- `data/`: Generated data and metrics
- `specs/`: Feature specifications
- `tests/`: Unit and integration tests

## License
MIT
