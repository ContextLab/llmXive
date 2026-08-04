# Quickstart: Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes

## Prerequisites

- Python 3.11+
- `pip`
- Git

## Installation

1. **Clone the repository**  
   ```bash
   git clone <repo-url>
   cd projects/PROJ-266-exploring-the-correlation-between-molecu
   ```

2. **Create a virtual environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The entire workflow is orchestrated by a single entry‑point script:

```bash
python code/run_pipeline.py
```

### What the script does (high‑level)

1. **Data Fetch** – pulls Caco‑2 records from ChEMBL, writes `data/raw/chembl_caco2_raw.csv`.  
2. **Checksum** – `utils/checksum.py` computes SHA‑256 hashes and stores them in `state/artifact_hashes`.  
3. **Citation Validation** – `validate_citations.py` checks title overlap ≥ 0.7.  
4. **Preprocessing** – filters invalid rows, logs protocol heterogeneity.  
5. **Conformer Generation & Convergence Check** – RDKit `EmbedMultipleConfs` with iterative stability loop (batch = 100).  
6. **Normal‑Mode Analysis** – `nma_analysis.py` (PyVib) derives torsional variance (dihedral only for prediction).  
7. **Descriptor Calculation** – `descriptors.py` writes `flexibility_descriptors.csv` (diagnostic metrics excluded from modeling).  
8. **Statistical Analysis** – `analysis.py` performs power analysis, correlation, robust regression (Huber/Ridge), VIF handling, 5‑fold CV.  
9. **Visualization** – `visualize.py` creates `plot.png` (PNG, dpi ≥ 300).  
10. **Task Manifest** – `run_pipeline.py` writes `tasks.md` summarising each step and its checksum.

## Verifying Results

- **Data Completeness**  
  ```bash
  python code/utils/check_pass_rate.py data/processed/cleaned_dataset.csv
  ```
  Expected: ≥ 83% valid records.

- **Conformer/NMA Success**  
  ```bash
  python code/utils/check_success_rate.py data/processed/flexibility_descriptors.csv
  ```
  Expected: ≥ 90% success AND convergence flag = True.

- **View Plot**  
  Open `data/processed/plot.png` with any image viewer.

- **Run Tests**  
  ```bash
  pytest tests/
  ```

## Troubleshooting

- **ChEMBL Rate Limits** – exponential back‑off (max 3 retries, 5 s interval).  
- **Conformer Failures** – see `data/processed/failures.log`.  
- **Memory Errors** – reduce batch size via `--batch-size` flag in `run_pipeline.py`.  
- **Power Insufficiency** – pipeline will log "Limited Power" if N < 150 but proceeds.