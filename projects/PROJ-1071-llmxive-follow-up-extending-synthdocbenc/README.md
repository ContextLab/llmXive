# PROJ-1071: llmXive Follow-up: Extending SynthDocBench with Decoupled Retrieval

## Project Overview
This project extends the SynthDocBench benchmark to evaluate the efficacy of decoupled retrieval mechanisms in mitigating the "middle-third" positional bias in Vision Language Models (VLMs).

## Structure
- `code/`: Python source modules for document generation, baseline evaluation, retrieval indexing, and statistical analysis.
- `data/`: Raw synthetic documents, derived metrics, and checksums.
- `tests/`: Unit and integration tests.
- `specs/`: Design documents and requirements.
- `logs/`: Structured JSON logs for pipeline tracing.

## Execution
Run the pipeline via `python code/doc_generator.py` to generate data, followed by `python code/baseline_eval.py` and `python code/retrieval_eval.py`.
