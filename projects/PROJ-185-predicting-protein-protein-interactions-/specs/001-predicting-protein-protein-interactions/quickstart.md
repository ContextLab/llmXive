# Quickstart: Predicting PPIs from Co‑expression

## Prerequisites
1. **Git clone** the repository.
2. Install the Python environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Install the R environment (run once):
   ```bash
   Rscript -e "if (!requireNamespace('renv')) install.packages('renv'); renv::restore()"
   ```
   This installs DESeq2, limma, sva, and `org.At.tair.db`.

## Configuration
- Edit `config/species.yaml` to list GEO series per species (default includes Arabidopsis series).  
- Adjust optional parameters in `config/parameters.yaml` (e.g., `normalization: vst`, `correlation_threshold: 0.80`, `colocalization_filter: true`).  
- Set a global seed (default `42`).

## Running the Full Pipeline
```bash
make all SEED=42
```
- **`make all`** executes the complete workflow (download → normalize → correlate → map → edge selection → optional colocalization filter → evaluation → enrichment → summary).  
- Output files are placed under `results/<species>/`.

## Targeted Steps
- **Download only**:
  ```bash
  make download SEED=42
  ```
- **Run evaluation only** (requires previous steps):
  ```bash
  make evaluate SEED=42
  ```
- **Run GO enrichment only**:
  ```bash
  make enrich SEED=42
  ```

## Orthogonal Validation (optional)
Set `colocalization_filter: false` in `config/parameters.yaml` to skip the UniProt subcellular colocalization filter if you prefer the raw co‑expression edge set.

## Verification
After each target, the verification script runs automatically (FR‑017). Example:
```bash
$ cat results/Arabidopsis/summary_Arabidopsis.txt
Edges: a substantial number of edges
Mapping rate: high (approximately ninety percent).
AUROC: indicative of strong discriminative performance.
AUPRC (primary): anticipated to be robust (substantially above baseline).
Optimal threshold (max F1, FDR≤0.05): 0.82
Top GO term: GO:0008150 (biological_process)  adj. p=0.003
...
```
The `pipeline.log` file can be inspected with:
```bash
jq . pipeline.log | less
```

## Reproducibility Checklist
- Seed is fixed (`--seed` flag).  
- All software versions are recorded in `requirements.txt` and `renv.lock`.  
- Checksums of raw GEO files are stored in `state/artifact_hashes.yaml`.  
- Schema validation ensures output integrity (edges validated against `predicted_edges.schema.yaml`, GO enrichment against `go_enrichment.schema.yaml`).  

---

