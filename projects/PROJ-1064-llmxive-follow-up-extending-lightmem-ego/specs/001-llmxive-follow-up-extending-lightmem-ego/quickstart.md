# Quickstart: Semantic Decay Retrieval

This guide describes how to set up the environment and run the initial validation pipeline for the Semantic Decay retrieval mechanism.

## 1. Installation
Install the required dependencies from the project root:
```bash
pip install -r requirements.txt
```

## 2. Data Acquisition
Download a small public dataset sample (SQuAD) which serves as a stand‑in for the Ego4D data:
```bash
python src/data/download.py --output-dir data/raw/
```
This script fetches data from the Hugging Face Hub and saves a real sample to `data/raw/ego4d_train.jsonl`.

## 3. Checksum Verification
Verify the integrity of the downloaded files using the generated checksums:
```bash
sha256sum -c data/raw/CHECKSUMS.txt
```

## 4. Validation Pipeline
Execute the small validation pipeline to verify the end‑to‑end flow:
```bash
python src/cli/run.py --mode validation
```