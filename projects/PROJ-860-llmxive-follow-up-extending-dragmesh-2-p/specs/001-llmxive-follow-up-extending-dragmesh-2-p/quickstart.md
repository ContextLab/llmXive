# Quickstart: Virtual Tactile Zero-Shot Adaptation

## Prerequisites
- Python 3.11 or newer
- Internet access to download the DragMesh-2 manifest

## Installation
```bash
pip install -r requirements.txt
```

## Fetch the DragMesh-2 data
```bash
python code/data_loader.py
```
This command fetches the manifest from HuggingFace and writes it to `data/raw/dragmesh_manifest.jsonl`. It will fail loudly if the source is unreachable.

## Running the Full Experiment
```bash
python code/main.py --mode full --num_objects 10 --seed 42
```