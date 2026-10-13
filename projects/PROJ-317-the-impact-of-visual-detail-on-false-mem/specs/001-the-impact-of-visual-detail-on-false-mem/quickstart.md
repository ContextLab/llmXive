# Quickstart: Visual Detail and False Memory Susceptibility

## Prerequisites
- Python 3.11 or newer  
- `git`  
- Internet connection (only for optional full Visual Genome download)

## Installation
```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-317-the-impact-of-visual-detail-on-false-mem

# Set up a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Running the CI Validation Pipeline (uses pre‑bundled subset)
```bash
# 1. Load the pre‑bundled images and compute complexity scores
python code/utils/data_loader.py --source prebundled --count <sample_size> --seed 42

# 2. Generate enhanced and reduced stimuli (writes metadata files)
python code/stimuli/generator.py --mode all --seed 42

# 3. Simulate participant sessions (mock mode, no IRB needed)
#    Each session presents an equal number of true and lure items per condition.
python code/participants/interface.py --mode mock --n-sessions <representative number> --seed 123

# 4. Power analysis (passes because N = 60 ≥ 50)
python code/analysis/power.py

# 5. Primary analysis (GLMM) and optional descriptive ANOVA backup
python code/analysis/glmm.py          # primary binomial mixed‑effects model
python code/analysis/anova.py         # secondary descriptive ANOVA (run after assumption checks)

# 6. Generate the confidence‑interval plot
python code/analysis/viz.py --output data/analysis/false_memory_rates.png
```

## Running the Full Study (requires verified Visual Genome)
1. **Verify Visual Genome** – Add the dataset to the verified list or obtain an explicit verification token.  
2. **Download & Stream**  
```bash
python code/utils/data_loader.py --source visual_genome --limit <desired sample size> --stream
```
3. **Collect Real Data** (after IRB approval)  
```bash
python code/participants/interface.py --mode real --n-sessions 60
```
4. **Analyze** – same commands as steps 4‑6 above.

## Verification Checklist
- `data/stimuli/generated/` contains `*_enhanced.jpg`, `*_reduced.jpg`, and matching `metadata.yaml` files.  
- `data/responses/` holds one JSONL file per participant; each line conforms to `contracts/response.schema.yaml`.  
- `data/analysis/false_memory_rates.png` displays mean false‑memory rates with confidence intervals for the three conditions.  
- SHA‑256 checksums for all outputs are recorded in `state/projects/PROJ-317-…yaml`.  

---  

## projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/specs/001-the-impact-of-visual-detail-on-false-mem/contracts/response.schema.yaml