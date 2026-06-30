# Quickstart: CiteVQA CPU Adaptation

This guide runs the adapted CiteVQA benchmark on a CPU-only environment.

### Prerequisites
- Python 3.8+
- `pip install matplotlib` (optional, for plotting; script handles missing gracefully)

### Run Commands
Execute the adaptation script. It will generate synthetic data, simulate model responses, calculate the Strict Attributed Accuracy (SAA) metric, and write results to `data/` and `figures/`.

```bash
python code/citevqa_cpu_adaptation.py
```
