# llmXive: Extending "MemLens: Benchmarking Multimodal Long-Term Memory in Large Vision-Language Models"

## Project Overview

This project extends the MemLens benchmark to evaluate multimodal long-term memory strategies in Large Vision-Language Models (LVLMs). It implements Coarse, Medium, and Fine memory stores, performs CPU-optimized inference, and conducts statistical significance testing.

## Prerequisites

- Python 3.9+
- CPU-only environment (no CUDA required)
- 7GB+ RAM available

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data Setup

The MemLens dataset will be downloaded automatically by running `code/download.py`. Ensure you have sufficient disk space (~7GB).

## Usage

### Run the Full Pipeline

```bash
python code/main.py
```

### Download Dataset Only

```bash
python code/download.py
```

### Run Inference on a Subset

```bash
python code/main.py --subset 10
```

## Project Structure

```
.
├── code/ # Implementation modules
│ ├── download.py # Dataset download and checksums
│ ├── preprocessing.py # Data loading, filtering, store construction
│ ├── retrieval.py # Similarity search and retrieval
│ ├── detection.py # Object detection (YOLOv8)
│ ├── inference.py # CPU-optimized LLM inference
│ ├── evaluation.py # Accuracy and resource metrics
│ ├── stats.py # Statistical significance testing
│ ├── config.py # Configuration parameters
│ └── main.py # Pipeline orchestrator
├── data/
│ ├── raw/ # Downloaded MemLens dataset
│ └── processed/ # Generated artifacts (stores, metrics)
├── tests/ # Unit tests
├── state/ # Pipeline state tracking
└── requirements.txt # Python dependencies
```

## Configuration

Key parameters can be adjusted in `code/config.py`:
- `TOP_K`: Number of retrieved items (default: 5)
- `MODEL_NAME`: LLM model for inference (default: "microsoft/Phi-3-mini-4k-instruct")
- `DETECTION_MODEL`: Object detection model (default: "yolov8n.pt")

## License

This project is for research purposes only.
