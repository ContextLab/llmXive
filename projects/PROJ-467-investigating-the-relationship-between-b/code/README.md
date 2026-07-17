# Brain Network Dynamics and Tactile Discrimination Study

This project investigates the relationship between brain network dynamics and individual differences in tactile discrimination.

## Setup

### Prerequisites
- Python 3.11+
- pip

### Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

### Project Structure

```
.
├── code/
│ ├── src/
│ │ └── brainnet/
│ │ ├── __init__.py
│ │ ├── utils.py
│ │ ├── preprocessing.py
│ │ └──...
│ ├── tests/
│ │ ├── unit/
│ │ └── contract/
│ ├── data/
│ │ ├── raw/
│ │ └── processed/
│ ├── results/
│ │ └── figures/
│ ├── metadata/
│ ├── contracts/
│ └── requirements.txt
├── pyproject.toml
└── README.md
```

## Usage

### Preprocessing

Run the preprocessing pipeline on fMRI data:

```python
from src.brainnet.preprocessing import preprocess_pipeline

output_path = preprocess_pipeline(
 input_file="data/raw/subject_001_func.nii.gz",
 output_dir="data/processed",
 t_r=2.0
)
```

### Running Tests

```bash
pytest code/tests/
```

## License

MIT License
