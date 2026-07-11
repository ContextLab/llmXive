# PROJ-826-llmxive-follow-up-extending-memlens-benc

## Overview
This project extends the "MemLens: Benchmarking Multimodal Long-Term Memory in Large Vision-Language Models" benchmark.
It implements a pipeline for downloading, processing, and evaluating memory stores (Coarse, Medium, Fine) using CPU-optimized inference.

## Project Structure
- `code/`: Source code for the pipeline (download, preprocessing, retrieval, inference, evaluation).
- `data/`: Raw and processed data artifacts.
- `tests/`: Unit and integration tests.
- `state/`: Project state tracking (YAML).
- `specs/`: Design documents and requirements.

## Prerequisites
- Python 3.9+
- CUDA is NOT required; this project targets CPU-only execution.

## Installation
1. Clone the repository.
2. Navigate to the project root: `projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/`
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage
See individual task implementations (e.g., `code/download.py`, `code/main.py`) for specific CLI usage.
A general pipeline runner is expected in `code/main.py`.

## Data Sources
- MemLens dataset is fetched from HuggingFace at runtime.

## License
Research use only.
