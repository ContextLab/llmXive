# Contributing to llmXive: Structure-Only Surrogate Model for 2D Material Elastic Moduli

Thank you for your interest in contributing to this project. To ensure scientific rigor and clarity, please adhere to the following guidelines, particularly regarding terminology and model description.

## Terminology Guidelines

This project builds a **Structure-Only Surrogate Model** that interpolates pre-computed Density Functional Theory (DFT) results. It is **NOT** a first-principles solver.

### Forbidden Terminology

**DO NOT** use the following terms to describe the Machine Learning (ML) model, its predictions, or the project's core methodology:

- "First-Principles Calculations"
- "Solving the Schrödinger Equation"
- "Ab Initio" (when referring to the ML model)
- "Quantum Mechanical Solver"
- "Fundamental Physics Discovery"

**Reason:** The model is a statistical interpolator trained on existing DFT data. It does not solve the Hamiltonian, does not calculate electron density from first principles, and cannot discover new physics outside its training distribution. Using these terms creates a false impression of the model's capabilities and violates scientific accuracy.

### Required Terminology

**ALWAYS** use the following terms when describing the model:

- "Surrogate Model"
- "ML Interpolation of DFT Data"
- "Graph Neural Network (GNN) Predictor"
- "Data-Driven Approximation"
- "Statistical Correlation"

### Example Usage

| ❌ Incorrect (Forbidden) | ✅ Correct (Required) |
|:--- |:--- |
| "We perform first-principles calculations of elastic moduli." | "We train a surrogate model to interpolate DFT-calculated elastic moduli." |
| "The model solves the Schrödinger equation for 2D materials." | "The model learns statistical correlations between structure and DFT-predicted moduli." |
| "This is an ab initio prediction of Young's modulus." | "This is a GNN-based prediction derived from pre-computed DFT data." |
| "Our method discovers new quantum mechanical variables." | "Our analysis identifies structural descriptors that correlate with elastic properties in the training data." |

## Code Style and Standards

- **Linting:** We use `ruff` with strict rules (E, F, W, I). Run `ruff check code/` before committing.
- **Formatting:** We use `black` with a line length of 88. Run `black code/` before committing.
- **Type Hinting:** All function signatures must include type hints.
- **Documentation:** All public functions and classes must have docstrings.

## Data and Reproducibility

- **Real Data Only:** Never fabricate data. If external data is required, fetch it from the verified source defined in `code/ingest/download.py`. If the source is unreachable, the script must fail loudly with a clear error message.
- **Single Source:** Ensure only one data source is active per run, as enforced by `code/ingest/download.py`.
- **Memory Limits:** Respect the 7GB RAM limit. Use streaming or dynamic sampling if the dataset exceeds available memory.

## Commit Messages

- Use the format: `[T<task_id>] <short description>`
- Example: `[T031] Enforce terminology guidelines in contributing docs`

## Reporting Issues

If you encounter a bug or have a suggestion, please open an issue with:
1. A clear description of the problem.
2. Steps to reproduce.
3. Expected vs. actual behavior.
4. Relevant logs or error messages.

## Pull Request Process

1. Fork the repository and create a branch for your task.
2. Ensure all tests pass (`pytest tests/`).
3. Update documentation if necessary.
4. Submit a Pull Request with a clear description of changes.
5. Address any review comments promptly.

By contributing to this project, you agree to maintain the highest standards of scientific accuracy and clarity.