# Quickstart: Running the Evolutionary Splicing Pipeline

The quickstart demonstrates a minimal end‑to‑end run on a **single sample per species** (four samples total). Adjust `config.yaml` to point to your own SRA accession list.

## Prerequisites
1. **GitHub Actions runner** (or local Linux env) with **Python 3.11**, **R 4.3**, **conda** installed.
2. Clone the repository and navigate to the project root.

```bash
git clone https://github.com/your-org/evolutionary-splicing.git
cd evolutionary-splicing
```

## Step 1: Set up the environment
```bash
conda env create -f environment.yml   # pins all CPU‑only packages
conda activate evo-splice
```

## Step 2: Prepare `config.yaml`
```yaml
samples:
  - accession_id: SRR1234567
    species: human
  - accession_id: SRR2345678
    species: chimpanzee
  - accession_id: SRR3456789
    species: macaque
  - accession_id: SRR4567890
    species: marmoset
output_dir: data/
seed: 42
max_replicates: 3
```
> **Important**: Replace the placeholder accession IDs with real SRA runs that contain cortex RNA‑seq. The pipeline will abort (error 101) if fewer than three replicates per species are supplied.

## Step 3: Run the full pipeline
```bash
python -m src.pipeline.run --config config.yaml
```
The command executes the following sub‑steps (see `plan.md` for mapping to FR IDs):
1. Download FASTQ (`FR-001`).
2. Align with STAR (`FR-002`).
3. Quantify PSI via SUPPA2 (`FR-003`).
4. Filter lineage‑specific events (`FR-004`).
5. Extract flanking sequences and annotate phyloP (`FR-005`, `FR-006`).
6. Enrichment testing with Fisher, BH & Bonferroni corrections (`FR-007`, `FR-012`).
7. Phylogenetic correction with PGLS (`FR-013`).
8. Plot Manhattan figure (`FR-008`).
9. Archive raw FASTQ after 90 days (`FR-010`).

All major steps log to `pipeline.log` (timestamped, exit codes) satisfying `FR-009`.

## Step 4: Verify outputs
```bash
python src/validation/validate_psi.py data/psi/combined_psi.tsv
python src/validation/validate_plot.py data/results/manhattan.png
```
Both scripts exit with code 0 if `SC-001` and `SC-004` are met.

## Step 5: Inspect results
- `data/events/lineage_specific_events.tsv` – list of significant splicing events.  
- `data/results/enrichment.tsv` – enrichment statistics per lineage.  
- `data/results/manhattan.png` – publication‑ready plot.  

## Cleanup (optional)
To free space after verification:
```bash
rm -rf data/raw/
```
Raw FASTQ will be automatically compressed and uploaded to Zenodo after 90 days (handled by the scheduled `archiver` script).

---
