# llmXive Follow-up: Extending DanceOPD

This project extends the DanceOPD paper by generating teacher routing ground truth, training static decision trees, and quantifying fidelity degradation.

## Features

- **Data Generation**: Stream samples from ImageNet-1K and LAION-400M, run teacher model inference, and extract routing features.
- **Tree Training**: Train DecisionTreeClassifier models for various depths to approximate teacher routing.
- **Fidelity Evaluation**: Compute FID and CLIP scores for tree-generated vs. teacher-baseline images.
- **Statistical Analysis**: Perform bootstrap and t-test analyses to determine significance of degradation.

## Prerequisites

- Python 3.11
- pip

## Installation

```bash
cd code
pip install -r requirements.txt
python setup_data_dirs.py
```

## Usage

Run the full pipeline:
```bash
python main.py
```

Or run individual stages:
```bash
# Data generation
python 00_data_generation.py

# Tree training
python 01_train_trees.py

# Fidelity evaluation
python 02_evaluate_fidelity.py
```

## Project Structure

```
.
├── code/
│ ├── utils/
│ ├── models/
│ ├── 00_data_generation.py
│ ├── 00_teacher_inference.py
│ ├── 00_data_extraction.py
│ ├── 01_train_trees.py
│ ├── 02_evaluate_fidelity.py
│ ├── 03_versioning.py
│ └──...
├── data/
│ ├── raw/
│ ├── processed/
│ └── results/
├── models/
├── specs/
│ └── contracts/
├── tests/
│ ├── unit/
│ └── integration/
└── docs/
```

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Design Document](docs/DESIGN.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [User Guide](docs/USER_GUIDE.md)

## License

This project is licensed under the MIT License.

## Contributing

See [Developer Guide](docs/DEVELOPER_GUIDE.md) for contribution guidelines.