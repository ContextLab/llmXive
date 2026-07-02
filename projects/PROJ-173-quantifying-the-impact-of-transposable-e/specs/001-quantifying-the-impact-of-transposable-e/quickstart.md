# Quickstart: Quantifying the Impact of Transposable Element Activity on Gene Expression Variation in Drosophila

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Git

## Installation

1. **Clone the repository**  
   ```bash
   git clone <repo-url>
   cd projects/PROJ-173-quantifying-the-impact-of-transposable-e
   ```

2. **Create and activate a virtual environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline (Mock Mode)

Because no verified public DGRP TE‑genotype + TE‑aware expression dataset exists, the pipeline ships with a **Mock Mode** for CI testing.

1. **Generate Mock Data** (synthetic but schema‑compliant)  
   ```bash
   python src/cli.py generate-mock --n-lines 50 --n-pairs 500 --seed 42
   ```
   *Creates `data/raw/mock/` with genotype, FASTQ (empty placeholders), GTF, and a TE‑aware expression matrix.*

2. **Execute the Full Analysis**  
   ```bash
   python src/cli.py run --mode mock
   ```
   This runs:
   - PCA computation  
   - TE‑aware quantification (mock step)  
   - TE‑gene pairing, monomorphic & power filtering  
   - Linear models with VIF & BH correction  
   - Freedman‑Lane permutation (100 iters) and null‑distribution plot  
   - R² reduction metric (SC‑004)  
   - Replication (if a second mock dataset is supplied)  

3. **Inspect Results**  
   - `results/associations.csv` – final association table (includes `vif_flag`, `ambiguous_flag`, `power_flag`).  
   - `results/plots/null_distribution.png` – permutation null plot with observed statistic line and 95 % threshold.  
   - `results/population_structure_control.csv` – R² reduction metric.  
   - `results/replication/comparison.tsv` – replication comparison (if applicable).

## Running with Real Data (When Available)

If you obtain a verified DGRP VCF with TE calls **and** TE‑aware RNA‑seq quantifications:

1. Place the files under `data/raw/` (e.g., `genotypes.vcf`, `expression_TEaware.tsv`, `genes.gtf`).  
2. Edit `config.yaml`:
   ```yaml
   data:
     genotypes_path: "data/raw/genotypes.vcf"
     expression_path: "data/raw/expression_TEaware.tsv"
     gene_models_path: "data/raw/genes.gtf"
     use_mock: false
   ```
3. Run the pipeline:
   ```bash
   python src/cli.py run
   ```

## Verification

Run the contract tests to ensure all outputs conform to the schemas:

```bash
pytest tests/test_contracts.py
```

**Important:** Until a public, verified dataset containing both TE genotypes and TE‑aware expression becomes available, the pipeline can only demonstrate methodology on mock data. The scientific conclusions about TE impact on *Drosophila* gene expression will require real data.