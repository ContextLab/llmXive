# llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

**Project ID**: PROJ-860-llmxive-follow-up-extending-dragmesh-2-p

## Overview

This project implements a virtual tactile adaptation system for robotic manipulation,
focusing on zero-shot adaptation to unseen damping and friction conditions using
DragMesh-2 dataset and PICA baseline policies.

## Key Features

- Virtual tactile stiffness estimation ($k_{est}$)
- Adaptive reward scheduling based on real-time friction detection
- Zero-shot generalization to novel object sets
- CPU-tractable inference pipeline

## Prerequisites

- Python 3.8+
- CPU-only PyBullet environment (no CUDA)
- Access to DragMesh-2 dataset via HuggingFace

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r code/requirements.txt`
3. Verify citations: `python code/validate_citations.py`
4. Download datasets: `python code/data_loader.py`

## Usage

See `quickstart.md` for detailed execution flow.

## License

Research use only.
