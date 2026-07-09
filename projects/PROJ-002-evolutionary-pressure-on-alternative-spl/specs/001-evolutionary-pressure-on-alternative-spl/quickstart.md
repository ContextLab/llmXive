# Quickstart: Evolutionary Pressure on Alternative Splicing in Primates

This guide walks a new user through running the full analysis on a small synthetic dataset (suitable for CI) and on real data (once the required SRA accession list is provided).

## Prerequisites

- GitHub Actions runner (Linux) **or** a local Linux/macOS machine with Docker.
- Docker installed (recommended for reproducibility).
- `conda` or `micromamba` for environment creation (optional; the Docker image contains everything).

## Step 0 – Clone the Repository

```bash
git clone
cd evolutionary-pressure-splicing
```

## Step 1 – Build the Docker Image (CPU‑only)

```bash
docker build -t evo-splicing:latest -f Dockerfile.
```

The Dockerfile pins all versions (Python 3.11, R 4.3, STAR 2.7.11a, etc.) and installs `sra-toolkit`, `bedtools`, `pyBigWig`, and required Python/R packages.

## Step 2 – Prepare a Configuration File

Create `config/run_config.yaml`:

```yaml
species:
 Human:
 accessions:
 - SRR1234567
 - SRR1234568
 - SRR1234569
 Chimpanzee:
 accessions:
 - SRR2234567
 - SRR2234568
 - SRR2234569
 Macaque:
 accessions:
 - SRR3234567
 - SRR3234568
 - SRR3234569
 Marmoset:
 accessions:
 - SRR4234567
 - SRR4234568
 - SRR4234569
max_replicates: 5
min_replicates: 3
mode: ci # Options: 'ci' (sampled, 100 permutations) or 'full' (all samples, 1000 permutations)
```

*Replace the placeholder SRR IDs with the real SRA accession numbers from the spec (SRP010775, SRP009050, SRP009051, SRP009052).*

## Step 3 – Run the Full Pipeline (Docker)

```bash
docker run --rm -v "$(pwd)":/workspace -w /workspace evo-splicing:latest \
 bash./run_pipeline.sh config/run_config.yaml
```

`run_pipeline.sh` orchestrates the phases described in `plan.md`. It creates the following directories:

```
data/
 raw/ # FASTQs
 aligned/ # BAMs
 phyloP/ # bigWig files
results/
 psi.tsv
 lineage_specific_events.tsv
 control_regions.tsv
 regression_cohort.tsv
 annotation.csv
 enrichment_results.tsv
 manhattan.png
logs/
 pipeline.log
artifacts_manifest.json
```

## Step 4 – Inspect Results

```bash
# Check the log for any abort codes
cat logs/pipeline.log

# Verify that hashes exist
jq. data/artifacts_manifest.json

# View the enrichment table
column -t results/enrichment_results.tsv

# Open the Manhattan plot (requires an image viewer)
open results/manhattan.png # macOS
xdg-open results/manhattan.png # Linux
```

## Step 5 – Run CI‑Only Synthetic Test (Fast)

The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`). To run locally:

```bash
docker run --rm -v "$(pwd)":/workspace -w /workspace evo-splicing:latest \
 pytest -m "ci"
```

This executes the synthetic‑data path, checks that:

- `pipeline.log` contains timestamps and exit codes.
- Abort codes 101/102 are triggered when the config violates replicate limits.
- Output tables contain the placeholder flag `"PLACEHOLDER"`.

## Step 6 – Lifecycle Management (Optional)

To simulate the 90‑day archiving step:

```bash
docker run --rm -v "$(pwd)":/workspace -w /workspace evo-splicing:latest \
 python -m src.pipeline.lifecycle --dry-run
```

The script prints actions it would take (compression, Zenodo upload, DOI insertion).

---