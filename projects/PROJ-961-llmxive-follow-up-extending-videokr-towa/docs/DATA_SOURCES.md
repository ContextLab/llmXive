# Data Sources and Requirements

This document details the external data sources required for the llmXive VideoKR analysis pipeline.

## 1. VideoKR-SFT Dataset

- **Description**: The Video-Knowledge-Reasoning SFT dataset containing questions, answers, and video context.
- **Source**: HuggingFace Datasets or the official VideoKR repository.
- **File Format**: JSON/Parquet (processed to CSV by the ingestion script).
- **Columns Required**: `id`, `question`, `answer`, `video_id`.
- **Download Script**: `code/ingest/download_data.py`

## 2. Knowledge Graph

- **Description**: A graph structure representing entities and relationships relevant to the VideoKR domain.
- **Source**: Provided via the project's data repository or a specific academic release (e.g., UCI, NAB).
- **File Format**: CSV (nodes and edges) or JSON.
- **Usage**: Used to calculate the shortest path (chain length) between entities mentioned in questions.
- **Download Script**: `code/ingest/download_data.py`

## Data Verification

All downloaded data is verified using checksums (SHA-256) to ensure integrity. The checksums are defined in `code/ingest/checksum.py` and verified by `code/ingest/verify_raw_data_integrity.py`.

## Local Data Structure

Upon successful download, the data structure will be:

```
data/
└── raw/
 ├── videokr_sft/
 │ └── [dataset files]
 └── knowledge_graph/
 ├── nodes.csv
 └── edges.csv
```

## Reproducibility

To ensure reproducibility, all data sources are versioned. The specific version used in this analysis is recorded in `state/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa.yaml`.