# Quickstart: Impact of Environmental Factors on Fungal Community Structure in Soil

This guide shows how to run the full analysis on a fresh GitHub Actions runner (or local Linux environment) using the provided CLI.

## Prerequisites
```bash
# Clone the repository (assumes you are in the project root)
git clone https://github.com/yourorg/impact-of-environmental-factors.git
cd impact-of-environmental-factors

# Create a virtualenv and install exact dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins versions as per plan
```

## Important Note
The scientific workflow **requires** at least three verified public ITS datasets that contain all required abiotic columns (`pH`, `nitrogen`, `phosphorus`, `potassium`, `temperature`, `moisture`, `biome`). If such datasets are not provided, the pipeline **will abort** with a CRITICAL error and exit code 2. Users may optionally run the analysis with the `--placeholder` flag to generate empty stub files for CI sanity checks; no ecological conclusions will be drawn.

## Step‑by‑Step Commands

1. **Set random seed (reproducibility)**
   ```bash
   python -c "import code.seed as s; s.set_seed(an arbitrary integer)"

The research question is: Can large language models be effectively utilized for automated hypothesis generation in materials science?
The method is: We will employ a large language model (specifically, GPT-3.5-turbo) to generate novel hypotheses regarding material properties based on a curated dataset of materials science literature. The generated hypotheses will then be evaluated by expert materials scientists for plausibility and novelty.
References: (Smith et al., 2023) [DOI: 10.1021/acs.nanolett.3c02000]; (Jones, 2022) [arXiv:2205.10000]
   ````

2. **Download & Harmonize Datasets**  
   *(If you have a verified ITS dataset, replace the placeholder IDs)*
   ```bash
   python -m code.cli.run_analysis download \
       --study-ids SRR1234567 SRR2345678 SRR3456789 \
       --metadata-url https://example.com/soil_metadata.csv \
       . . .
   ```

3. **Denoise Sequences (DADA2)**
   ```bash
   python -m code.cli.run_analysis dada2 \
       --raw-dir data/raw-seq/ \
       --output-dir data/asv/
   ```

4. **Compute Diversity Metrics**
   ```bash
   python -m code.cli.run_analysis diversity \
       --asv-dir data/asv/ \
       . . .
   ```

5. **Prepare Environmental Matrix ****** **


