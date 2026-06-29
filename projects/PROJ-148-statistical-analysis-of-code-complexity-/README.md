# Statistical Analysis of Code Complexity Metrics and Bug Prediction

**Project ID:** PROJ-148
**Repository:**

## Overview

This project implements an end‑to‑end research pipeline that:

1. **Downloads** a set of Java projects from the GHTorrent dataset.
2. **Extracts** source files and commit metadata.
3. **Computes** a suite of code‑complexity metrics using **lizard** (cyclomatic complexity, LOC, token count, nesting depth, Halstead volume).
4. **Labels** bug‑fix commits based on commit messages and linked issue IDs.
5. **Preprocesses** the data (imputation, log‑transform, outlier removal).
6. **Splits** the dataset with project‑level stratification (30 % test).
7. **Trains** two predictive models – an L1‑regularized logistic regression (primary) and a Random Forest (alternative).
8. **Evaluates** performance (ROC‑AUC, PR‑AUC, calibration), applies multiple‑hypothesis correction, and generates partial‑dependence plots.
9. **Produces** a concise research report (PDF/HTML) summarising findings.

The pipeline is fully reproducible and validated by a comprehensive test‑suite (unit, contract, and integration tests).

## Installation

```bash
# Clone the repository
git clone.git
cd statistical-analysis-of-code-complexity

# Create a virtual environment (Python 3.11)
python -m venv.venv
source.venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

The `requirements.txt` file pins the exact versions used during development (pandas, scikit‑learn, lizard, statsmodels, matplotlib, seaborn, pymer4, pytest, black, flake8, etc.).

## Usage

The pipeline can be executed with a single command:

```bash
python -m code.data.pipeline
```

This entry point runs the full data acquisition, preprocessing, splitting, model training, evaluation, and report generation steps.

### Individual stages

- **Download raw data**
 ```bash
 python -m code.data.download_gh
 ```
- **Extract commits**
 ```bash
 python -m code.data.extract_commits
 ```
- **Compute metrics**
 ```bash
 python -m code.data.extract_metrics
 ```
- **Label bug fixes**
 ```bash
 python -m code.data.label_bug_fixes
 ```
- **Preprocess**
 ```bash
 python -m code.data.preprocess
 ```
- **Split dataset**
 ```bash
 python -m code.data.split_dataset
 ```
- **Train models**
 ```bash
 python -m code.modeling.pipeline
 ```
- **Evaluate & generate plots**
 ```bash
 python -m code.modeling.evaluate
 python -m code.modeling.pdp
 python -m code.modeling.correct_pvalues
 python -m code.modeling.generate_thresholds
 ```
- **Create final report**
 ```bash
 python -m code.report.generate_report
 ```

All scripts write their outputs under the `data/` directory (e.g., `data/raw/`, `data/processed/`, `data/model/`) or `figures/` for visualisations.

## Data Source Citations

- **GHTorrent** – A comprehensive archive of GitHub activity used to obtain Java project repositories and commit histories.
 *Reference:* Gousios, G., & Spinellis, D. (2012). GHTorrent: Github data at scale. *Proceedings of the 10th Working Conference on Mining Software Repositories*.
 - URL: https://ghtorrent.org/

- **Lizard** – Static analysis tool for extracting code‑complexity metrics.
 *Reference:* Lizard – a simple yet powerful code analysis tool. https://github.com/terryyin/lizard

- **Python Packages** – pandas, scikit‑learn, statsmodels, matplotlib, seaborn, pymer4, etc., all publicly available via PyPI.

## Reproducibility Notes

1. **Random seed handling** – All stochastic components (data shuffling, model training) use the central seed defined in `code/utils/config.py`. [UNRESOLVED-CLAIM: c_404224da — status=not_enough_info] The seed can be overridden via the `SEED` environment variable or by editing `Config.seed` in that module.
2. **Deterministic pipelines** – The pipeline respects the seed at every step, ensuring that repeated runs produce identical splits, model parameters, and evaluation metrics.
3. **Checksum verification** – Downloaded archives are verified against SHA‑256 checksums (implemented in `code/utils/checksum.py`). Corrupt downloads abort the pipeline.
4. **Versioned dependencies** – The `requirements.txt` file locks package versions, guaranteeing the same library behaviour across environments.
5. **Data contract validation** – Dataset and model‑output schemas are defined in `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml`. Contract tests (`tests/contract/...`) automatically validate that generated artifacts conform to these schemas.
6. **Computational resources** – The metric extraction step processes files in a memory‑aware, chunked fashion (see `code/data/extract_metrics.py`), enabling execution on modest hardware (≤2 GB RAM).

## Testing

Run the full test suite with:

```bash
pytest -vv
```

Coverage is enforced at ≥ 85 % (`pytest --cov=code`). [UNRESOLVED-CLAIM: c_4e15ca3a — status=not_enough_info] All contract and integration tests must pass before the pipeline is considered production‑ready.

## License

This project is released under the **MIT License**. See the `LICENSE` file for details.