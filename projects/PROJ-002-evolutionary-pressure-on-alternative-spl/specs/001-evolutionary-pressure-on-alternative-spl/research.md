# Research: Evolutionary Pressure on Alternative Splicing in Primates

**Feature**: Evolutionary Pressure on Alternative Splicing in Primates  
**Branch**: `PROJ-002-001-evolutionary-pressure`  
**Date**: 2026-07-08

## Dataset Strategy

| Dataset | Access Method | Species | Notes |
|---------|---------------|---------|-------|
| Human cortex RNA‑seq (SRP010775) | `prefetch`/`fastq-dump` via SRA Toolkit | Human | No verified URL; accession list must be supplied by the user. |
| Chimpanzee cortex RNA‑seq (SRP009050) | SRA Toolkit | Chimpanzee | Same as above. |
| Rhesus macaque cortex RNA‑seq (SRP009051) | SRA Toolkit | Macaque | Same as above. |
| Common marmoset cortex RNA‑seq (SRP009052) | SRA Toolkit | Marmoset | Same as above. |
| PhyloP 100‑way bigWig | UCSC public bigWig server (http://hgdownload.soe.ucsc.edu/goldenPath/hg38/phyloP100way/) | All genomes | Direct download of the appropriate assembly‑specific bigWig. |
| Primate species tree | Download from NCBI Taxonomy or Springer et al. 2012 supplementary material (URL will be recorded in `data/primate_tree.nwk`). | – | Required for `phylolm`. |
| Reference genomes & GTFs | Ensembl FTP (e.g., `ftp://ftp.ensembl.org/pub/release-112/fasta/...`) | All species | Versioned in `config/genomes.yaml`. |

> **Important**: No other datasets are used. All URLs above are verified or explicitly noted as "no verified source".

## Decision / Rationale

- **Why SRA Toolkit?** The spec mandates exact SRA accession IDs; SRA Toolkit is the canonical, URL‑independent method to retrieve FASTQs and works on GitHub Actions without external URLs.
- **Why UCSC phyloP bigWig?** Real phyloP scores are required (FR‑005). The UCSC public server provides the 100‑way track for each assembly; we will download the appropriate file per species.
- **Why Ensembl genomes?** Alignments must use the latest reference assemblies (GRCh38, panTro6, rheMac10, calJac4) as required by FR‑002 and Principle VI. Ensembl provides stable, versioned FASTA/GTF bundles.
- **Why a pre‑downloaded tree file?** `phylolm` needs a Newick tree; we will store it under `data/` and checksum it (Principle V).
- **Why Continuous Predictor?** To avoid arbitrary binarization of the phyloP score (methodology-c8c4b145), the primary model uses `mean_phyloP` as a continuous variable. The binary threshold (≤-2.0) is used only for descriptive reporting and sensitivity analysis.
- **Why Matched Controls?** To break circularity (methodology-00b44909), we generate a control set of non-LSE regions matched on genomic properties (length, expression, conservation) to ensure the null model is valid.

## Methodology

1. **Data Retrieval** – `download.py` parses a YAML config listing required SRA accessions per species, verifies ≥ 3 and ≤ 5 replicates, aborts with error code 101/102 otherwise. FASTQs are stored under `data/raw/<species>/`. Checksums (SHA‑256) are written to `artifacts_manifest.json`.

2. **Alignment** – `align.py` runs STAR with default parameters, outputs sorted BAMs to `data/aligned/`. Wall‑clock time per sample is captured; `validate_alignment_time.py` asserts ≤ 2 h on the reference node (FR‑015). Alignment logs and duration are appended to `pipeline.log`.

3. **PSI Quantification** – `quantify.py` invokes SUPPA2 on the GTF + BAMs, producing `results/psi.tsv`. The file contains `gene_id`, `event_id`, and a PSI column per sample.

4. **Lineage‑Specific Event Detection** – `detect_events.py` computes ΔPSI between each lineage and the others, applies |ΔPSI| > 0.1 and BH‑FDR < 0.05 (FR‑004). Output: `results/lineage_specific_events.tsv`. The `is_placeholder` flag is set based on whether the input data is synthetic or real.

5. **Control Set Generation** – `generate_controls.py` creates a set of non-LSE intronic regions matched to the LSEs on exon length, mean expression, and conservation score. This ensures the control group is a valid neutral baseline.

6. **Aggregate Counts** – `aggregate_counts.py` computes `count_LSE`, `count_NonLSE`, and other summary statistics per lineage.

7. **Cohort Assembly** – `assemble_cohort.py` merges the LSE and Control datasets into a single dataframe (`regression_cohort.tsv`) for the regression model.

8. **Flanking Sequence Extraction** – `extract_flanks.py` builds a BED of ±500 bp around each event's exon, runs `bedtools getfasta` → `results/flanks.fasta` (FR‑005).

9. **PhyloP Annotation** – `annotate_phyloP.py` loads the species‑specific bigWig via `pyBigWig`, computes mean phyloP per flank (ignoring Ns), writes `results/annotation.csv`. Accelerated flag = TRUE if mean ≤ ‑2.0 (FR‑006) for descriptive stats. Gaps → `NA` and flagged for exclusion.

10. **Sensitivity Analysis** – `sensitivity_analysis.py` sweeps the acceleration threshold (±0.5) to validate the robustness of the binary classification.

11. **Enrichment Testing** – `stats.R`:
    - Loads `regression_cohort.tsv` + `primate_tree.nwk`.
    - Runs `phylolm::phyloglm` per lineage with `mean_phyloP` (continuous) as the predictor and LSE status as the response.
    - Generates 100 (CI) or 1000 (Full) permutations: 'accelerated' labels are shuffled across the *combined* LSE+Control cohort to generate a null distribution (FR‑014).
    - Applies Benjamini‑Hochberg across the four lineage p‑values (FR‑012).
    - Writes `results/enrichment_results.tsv`.

12. **Visualization** – `plot.py` reads `enrichment_results.tsv` and creates `results/manhattan.png` (≥ 1200 × 800 px) with chromosome on x‑axis, –log₁₀(p) on y‑axis, a horizontal line at the FDR‑corrected threshold (FR‑008). `validate_plot.py` checks dimensions, axis labels, and line presence. Traceability is ensured via `result_id`.

13. **Lifecycle Management** – `lifecycle.py` is scheduled via cron (00:00 UTC). After 90 days it compresses `data/raw/` to `.tar.gz`, uploads to Zenodo via its API, records the DOI in `metadata.json`, and deletes local copies. `lifecycle_manifest.json` records timestamps and checksums (FR‑010).

14. **Synthetic‑Data CI** – A minimal synthetic dataset (tiny FASTQ, mock phyloP bigWig) resides under `tests/fixtures/`. CI runs the full pipeline on this data, expecting placeholder flags (`PLACEHOLDER`) in output tables and verifying abort codes for replicate violations (FR‑015, FR‑016).

## Statistical Rigor

- **Multiple‑Comparison**: Benjamini‑Hochberg across the four lineage tests (FR‑012). No within‑lineage correction (single p‑value per lineage).
- **Power / Sample Size**: Minimum 3 replicates justified by `power_analysis.R` (FR‑011). CI uses synthetic data; real‑data power is not asserted in CI.
- **Causal Assumptions**: The analysis is purely associational; we do **not** claim causality (Principle VII compliance). The model tests whether accelerated regulatory status predicts LSE status, not the reverse.
- **Measurement Validity**: phyloP scores are taken from the UCSC 100‑way track, a widely validated conservation metric (citation will be checked by Reference‑Validator). SUPPA2 PSI has been benchmarked in the literature (citation added later).
- **Collinearity**: Predictors are binary (LSE status) and continuous (phyloP). The matched control set ensures that the 'Non-LSE' group is not confounded by genomic properties.
- **Circularity Avoidance**: The null model shuffles labels across the *combined* LSE+Control cohort, ensuring the test compares the observed association against a valid background where the relationship is broken.

## Success Criteria Alignment

| SC | How the pipeline satisfies it |
|----|--------------------------------|
| SC‑001 | `pipeline.log` records success/failure per sample; `artifacts_manifest.json` shows ≥ 90% of expected FASTQs present (excluding intentional aborts). |
| SC‑002 | `lineage_specific_events.tsv` contains at least one row per lineage when events exist; columns `lineage`, `count_LSE`, `count_NonLSE`. |
| SC‑003 | `enrichment_results.tsv` has exactly one row per lineage with columns `lineage`, `p_raw`, `p_fdr`, `p_empirical`. |
| SC‑004 | `validate_plot.py` confirms PNG dimensions, axis labels, title, and significance line. |
| SC‑005 | Every BAM, PSI, annotation, and result file has a SHA‑256 hash recorded in `pipeline.log` and `artifacts_manifest.json`. |

---