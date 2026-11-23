# Quickstart: llmXive follow‑up – extending "Mellum2 Technical Report"

## Prerequisites
- Python 3.11+
- 8 GB RAM (minimum for CPU inference of Mistral‑7B; 4 GB for TinyLlama fallback)
- Access to the HuggingFace Hub (for dataset and model download)
- CodeQL CLI installed and available in PATH

## Installation

1. **Clone the repository**
 ```bash
 git clone <repo-url>
 cd projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech
 ```

2. **Create a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # Windows: venv\Scripts\activate
 ```

3. **Install pinned dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the full pipeline

The pipeline can be executed with a single command that respects the
orchestrated phase order and uses a *small* sample size for quick testing:

```bash
python -m code.main --phase all --sample small
```

- `--phase all` tells the orchestrator to run the complete DAG.
- `--sample small` selects a reduced sample size defined in the configuration.

### **Step 1: Download and sample the dataset**
```bash
python -m code.data.download
```

### **Step 2: Static analysis (CodeQL + tree‑sitter)**
```bash
python -m code.data.static_analysis
```

## Expected runtime limits

- **Total wall‑clock time:** ≤ 6 hours on the GitHub Actions free‑tier.
- **Per‑chunk inference timeout:** 60 seconds.

The pipeline writes all results under `data/results/` and generates
figures under `data/figures/`.