# PROJ-052: Leveraging LLMs for Automated Test Case Generation

## Project Overview

This project implements an automated pipeline to generate JUnit test cases from natural language bug descriptions using Small Language Models (SLMs). The pipeline ingests data from the Defects4J dataset, generates test code using a quantized Phi-2 model (running on CPU), executes tests with JaCoCo instrumentation to measure code coverage on changed lines, and performs statistical analysis to compare LLM-generated tests against manual baselines.

**Key Features:**
- **Data Ingestion**: Streams real Defects4J bug fixes and extracts changed lines.
- **Test Generation**: Uses `llama-cpp-python` with Q4_K_M quantization to generate valid Java test code.
- **Execution & Coverage**: Compiles and runs tests, capturing line-level coverage on specific changed lines.
- **Statistical Analysis**: Performs Wilcoxon signed-rank or paired t-tests based on normality checks, calculating effect sizes and confidence intervals.
- **Strict Constraints**: Designed to run on CPU-only free-tier CI with <7GB RAM and strict runtime limits.

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or macOS.
- **Memory**: Minimum 7GB RAM (strictly enforced).
- **Disk**: ~15GB free space (for Defects4J dataset and build artifacts).
- **CPU**: Multi-core processor (inference is CPU-bound).
- **Java**: JDK 11 or higher (required for compilation and JaCoCo).
- **Python**: 3.9 or higher.

### Dependencies
Install Python dependencies:
```bash
pip install -r requirements.txt
```

Ensure `javac` and `java` are available in your `PATH`.

## Project Structure

```
.
├── code/ # Source code modules
│ ├── config.py # Environment and runtime configuration
│ ├── data_loader.py # Defects4J data fetching and processing
│ ├── llm_generator.py # LLM loading and test code generation
│ ├── test_executor.py # Java compilation, execution, and JaCoCo coverage
│ ├── analyzer.py # Statistical analysis (Shapiro, Wilcoxon, t-test)
│ ├── report_generator.py# Final report generation
│ └── main.py # Pipeline orchestration
├── data/ # Output artifacts (datasets, coverage metrics, reports)
│ ├── changed_lines.json
│ ├── coverage_metrics.csv
│ ├── analysis_results.json
│ └── final_report.md
├── specs/ # Feature specifications
├── contracts/ # JSON/YAML schemas for validation
├── tests/ # Unit and integration tests
└── README.md
```

## Quickstart Instructions

1. **Initialize the Environment**
 ```bash
 python -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt
 ```

2. **Configure Runtime Limits**
 Set environment variables for runtime and sample limits (optional, defaults apply):
 ```bash
 export RUNTIME_LIMIT_SECONDS=300
 export SAMPLE_LIMIT=10
 ```

3. **Run the Pipeline**
 Execute the main pipeline script. This will:
 - Fetch Defects4J data (streamed).
 - Extract changed lines.
 - Generate test code using the local LLM.
 - Compile and execute tests.
 - Calculate coverage and perform statistical analysis.
 - Generate `data/final_report.md`.

 ```bash
 python code/main.py
 ```

4. **Validate Outputs**
 The pipeline produces several artifacts in the `data/` directory:
 - `data/changed_lines.json`: Extracted line changes per bug.
 - `data/coverage_metrics.csv`: Coverage percentages and assertion density.
 - `data/analysis_results.json`: Statistical test results.
 - `data/final_report.md`: Human-readable summary.

 You can validate these artifacts against their schemas:
 ```bash
 python code/validate_schemas.py
 ```

5. **Run Tests**
 Execute the test suite to verify individual components:
 ```bash
 pytest tests/
 ```

## Data Sourcing

This project uses the **Defects4J** dataset, fetched programmatically via the Hugging Face `datasets` library.
- **Source**: `defects4j/defects4j`
- **Mode**: Streaming (`streaming=True`) to handle large datasets within memory constraints.
- **Integrity**: SHA-256 checksums are computed and stored in `state/projects/PROJ-052-...yaml` to ensure data provenance.

**Note**: If the data fetch fails, the pipeline will raise a `DataFetchError`. No synthetic data is generated.

## Statistical Methodology

- **Normality Check**: Shapiro-Wilk test (threshold p > 0.10).
- **Test Selection**:
 - Normal: Paired t-test.
 - Non-Normal: Wilcoxon signed-rank test.
- **Effect Size**: Cohen's d or Rank-biserial correlation.
- **Power Analysis**: Post-hoc power calculation reported as a descriptive metric.
- **Confidence Intervals**: 95% CI for mean ratio.

## License

This project is for research purposes. Refer to the Defects4J license for dataset usage.