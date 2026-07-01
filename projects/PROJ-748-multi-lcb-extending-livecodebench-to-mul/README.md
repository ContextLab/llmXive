# Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages

## Overview
This project implements a cross-language code generation benchmark based on LiveCodeBench (LCB), extending it to support multiple programming languages (C++, Java, Python, Rust, etc.). The pipeline includes dataset download, preprocessing, execution in a sandboxed environment, and statistical analysis of model performance.

## Research Goals
- Evaluate LLM performance across multiple programming languages
- Analyze cross-language correlations in code generation capabilities
- Implement robust statistical methods (GLMM, PCA, Bonferroni correction)
- Verify robustness through sensitivity analysis and contamination filtering

## Project Structure
```
.
├── README.md
├── quickstart.md
├── requirements.txt
├── code/
│ ├── config.py
│ ├── setup_hooks.py
│ ├── data/
│ │ ├── download.py
│ │ └── preprocess.py
│ ├── execution/
│ │ ├── sandbox.py
│ │ ├── runner.py
│ │ ├── aggregators.py
│ │ └── docker_images.py
│ ├── analysis/
│ │ ├── pca.py
│ │ ├── glmm.py
│ │ ├── correlation.py
│ │ ├── correction.py
│ │ ├── pairwise.py
│ │ ├── sensitivity.py
│ │ ├── contamination.py
│ │ ├── overfitting.py
│ │ └── run_analysis.py
│ ├── execute_pipeline.py
│ ├── logging.py
│ └── validation/
│ └── validate_artifacts.py
├── tests/
│ ├── unit/
│ └── integration/
├── docs/
├── data/
├── results/
│ └── artifacts/
├── contracts/
├── figures/
└── logs/
```

## Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up pre-commit hooks: `pre-commit install`

## Usage
See `quickstart.md` for detailed instructions on running the pipeline.

## License
This project is licensed under the MIT License.
