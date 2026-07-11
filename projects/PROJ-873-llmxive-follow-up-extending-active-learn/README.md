# llmXive: Active Learners as Efficient PRP Rerankers

This project implements an automated science pipeline to quantify and mitigate redundancy-induced efficiency loss in Passage Reranking (PRP) using active learning and pre-clustering.

## Features

- **Synthetic Redundancy Injection**: Generates near-duplicate document clusters to simulate real-world redundancy.
- **Cosine Similarity Proxy**: Uses `all-MiniLM-L6-v2` to flag redundant pairs (>0.95 similarity). [UNRESOLVED-CLAIM: c_0acbe1ed — status=refuted]
- **LLM Consensus Validation**: Dynamically samples flagged pairs for ground-truth validation.
- **MinHash-LSH Clustering**: CPU-tractable pre-clustering to filter redundant pairs before ranking.
- **Statistical Analysis**: Wilcoxon signed-rank tests with Bonferroni correction to validate efficiency gains.

## Setup

1. Ensure Python 3.11+ is installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Run the validation script:
 ```bash
 python code/env_validator.py
 ```

## Usage

### Run the Pipeline

```bash
python code/run_pipeline.py
```

### Run Tests

```bash
pytest tests/
```

## Project Structure

- `code/`: Source code modules
- `data/`: Datasets and results
- `tests/`: Unit and integration tests
- `specs/`: Design documents and requirements
- `requirements.txt`: Python dependencies

## License

MIT