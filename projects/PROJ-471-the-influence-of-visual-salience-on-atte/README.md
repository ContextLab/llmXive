# Visual Salience – Attentional Bias in Moral Judgements

This repository implements the end‑to‑end pipeline for investigating whether
computational visual salience predicts attentional allocation (eye‑tracking)
during moral‑judgment tasks.

## Quickstart

1. **Clone the repository**

 ```bash
 git clone <repo-url>
 cd projects/PROJ-471-the-influence-of-visual-salience-on-atte
 ```

2. **Bootstrap the project layout**

 ```bash
 python code/bootstrap.py
 ```

 The script creates the required folder structure, writes a pinned
 `requirements.txt`, and prints a directory tree as proof.

3. **Install the pinned dependencies**

 ```bash
 pip install -r requirements.txt
 ```

4. **Verify the environment**

 ```bash
 python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
 # Expected output: CUDA available: False
 ```

5. **Run a smoke test of the pipeline**

 ```bash
 python code/main.py --stage smoke
 ```

 The command checks that the directory layout exists and reports success. [UNRESOLVED-CLAIM: c_4e86db48 — status=not_enough_info]

## Data acquisition

The pipeline expects the **Moral Foundations Eye‑Tracking Dataset**
(`ds003123`) to be placed in `data/raw/ds003123/`. The dataset must be
downloaded manually from OpenNeuro (it is not automatically fetched).

If the dataset is missing, the pipeline will abort with error code
`DATA_MISSING_001`.

## Project layout

```
.
├─ code/
│ ├─ bootstrap.py # creates the layout & requirements
│ ├─ main.py # minimal entry point (smoke test)
│ └─ tests/ # unit tests for bootstrap
├─ data/
│ ├─ raw/
│ ├─ interim/
│ ├─ processed/
│ └─ results/
├─ docs/
│ └─ pipeline.md # detailed processing description
├─ requirements.txt # pinned versions
└─ README.md
```

Further stages (salience generation, ROI segmentation, analysis, etc.)
are added in subsequent tasks.
