# Evaluating the Impact of Code Generation on Code Review Time

**Project ID**: PROJ-302-evaluating-the-impact-of-code-generation

This project investigates the causal impact of AI-generated code on code review duration using a rigorous causal inference methodology (Propensity Score Matching) on real-world GitHub data.

## Research Question

Does the use of LLM-generated code significantly reduce (or increase) the time required for code review compared to human-written code, after controlling for code complexity, file size, and repository activity?

## Methodology

1. **Data Acquisition**: Fetch Pull Request (PR) metadata and code snippets from high-star GitHub repositories (≥1,000 stars).
2. **Cohort Generation**:
 - **Human Cohort**: Original code snippets from PRs.
 - **LLM Context-Based Cohort**: Synthetic code generated using the original file context (via `CodeLlama-7B-8bit`).
 - **LLM Prompt-Based Cohort**: Synthetic code generated from rewritten commit messages (intent prompts) without file context.
3. **Feature Extraction**: Compute complexity (cyclomatic), style metrics, and semantic similarity scores.
4. **Causal Analysis**:
 - **Propensity Score Matching**: Match LLM-generated and Human code based on covariates (file size, complexity, activity) to create a balanced dataset.
 - **Statistical Testing**: Compare review durations using t-tests or Mann-Whitney U tests.
5. **Sensitivity Analysis**: Validate results across stratified subsets of the data.
6. **Reporting**: Generate visualizations and a comprehensive PDF report.

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Matching, statistical tests, sensitivity analysis
│ ├── data_acquisition/ # GitHub scraping, code generation
│ ├── feature_extraction/# Complexity, style, semantic similarity
│ ├── security/ # PII scanning
│ ├── utils/ # Configuration, models, validators
│ └── main.py # Pipeline orchestrator
├── data/ # Data storage
│ ├── raw/ # Raw data from GitHub
│ └── processed/ # Processed datasets (Parquet, JSON)
├── docs/ # Documentation
├── figures/ # Generated plots
├── logs/ # Execution logs
├── reports/ # Final PDF/HTML reports
├── specs/ # Feature specifications
└── tests/ # Test suite
```

## Quick Start

See [`docs/quickstart.md`](docs/quickstart.md) for detailed setup and execution instructions.

## Key Features

- **GPU Escape Hatch**: Automatically offloads code generation to a GPU-enabled runner if CPU execution exceeds 60 seconds.
- **Robust Matching**: Implements retry logic with interaction terms to ensure covariate balance (SMD < 0.1).
- **Sensitivity Gates**: Enforces consistency checks across data subsets to validate causal claims.
- **PII Protection**: Scans all data for PII before processing.

## Dependencies

- Python 3.9+
- PyTorch, Hugging Face `transformers`, `datasets`
- `pandas`, `numpy`, `scipy`, `statsmodels`
- `radon` (for complexity analysis)
- `reportlab`, `jinja2` (for reporting)
- GitHub API

## License

[MIT License](LICENSE)

## Contact

For questions or contributions, please open an issue or submit a pull request.
