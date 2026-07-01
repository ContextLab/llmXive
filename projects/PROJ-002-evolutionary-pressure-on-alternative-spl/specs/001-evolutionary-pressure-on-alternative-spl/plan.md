# Implementation Plan: Evolutionary Pressure on Alternative Splicing in Primates

**Branch**: `PROJ-002-001-evolutionary-pressure` | **Date**: 2026-06-24 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/PROJ-002-001-evolutionary-pressure/spec.md`

## Summary

This feature implements a computational pipeline to investigate the correlation between alternative splicing (AS) divergence in the primate cortex and positive selection on splicing regulatory elements (SREs). The approach involves downloading RNA‑seq data for human, chimpanzee, macaque, and marmoset, aligning reads to species‑specific genomes, quantifying Percent Spliced In (PSI) values, identifying lineage‑specific splicing events (LSEs), annotating flanking regions with phyloP conservation scores, and performing phylogenetically corrected statistical enrichment tests.

**Critical Note on Data & Validity**: 
1. **CI Validation**: The pipeline will run on **synthetic data** for CI/CD logic validation. Synthetic results are **placeholders** and **cannot** support scientific conclusions.
2. **Scientific Execution**: The **Scientific Execution** phase (Phase 4) MUST use **real RNA‑seq samples** from the specific SRA BioProjects identified in `research.md`. Only results from this phase are valid for the research question.

## Technical Context

- **Language/Version**: Python, R 4.3
- **Primary Dependencies**: `pysam`, `suppa2` (CLI), `bedtools` (CLI), `biopython`, `pandas`, `scikit-learn`, `rpy2`, `phylolm` (R), `ape` (R), `matplotlib`, `zenodo-client` (for upload), `bigWigAverageOverBed` (UCSC tools)
- **Storage**: Local filesystem (`data/raw`, `data/processed`), Zenodo for long‑term archiving
- **Testing**: `pytest` (unit), `validate_plot.py` (integration/acceptance)
- **Target Platform**: Linux (GitHub Actions runner: 2 CPU, 7 GB RAM, 14 GB disk, ≤6 h per job)
- **Compute Feasibility**: CI run samples FASTQ to 2 M reads per sample, uses `--runThreadN 2` for STAR, compresses intermediates, and validates logic only. Full‑scale runs require an 8‑core node (Phase 4) where alignment time is benchmarked against the ≤ 2 h limit.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

1. **I. Reproducibility** – Deterministic random seeds are pinned; external data fetched from canonical SRA IDs listed in `research.md`.
2. **II. Verified Accuracy** – All tool citations (STAR, SUPPA2, phyloP, phylolm) are verified against primary literature.
3. **III. Data Hygiene** – SHA‑256 checksums generated for every download; `hash_manifest.json` records hashes for **all** artifacts (raw FASTQ, BAM, PSI tables, annotation files, result tables).
4. **IV. Single Source of Truth** – Figures are generated directly from `EnrichmentResult` dataframes; no manual entry.
5. **V. Versioning Discipline** – `hash_manifest.json` stores a hash entry for *every* artifact (including intermediates like BAMs and PSI tables), and `state/projects/...yaml` is updated with an `updated_at` timestamp after each step.
6. **VI. Cross‑Species Data Harmonization** – Genome FASTA/GTF versions are enumerated in `config/species.yaml`; gene IDs are mapped to Ensembl Compara orthologs before cross‑species aggregation.
7. **VII. Phylogenetic Statistical Independence** – Phylogenetic Logistic Regression (`phylolm::phyloglm`) uses `config/primate_tree.nwk` to correct for shared ancestry.

## Project Structure

```text
specs/PROJ-002-001-evolutionary-pressure/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── splicing_event.schema.yaml
    └── enrichment_result.schema.yaml
```

```text
projects/PROJ-002-evolutionary-pressure-on-alternative-spl/
├── data/
│   ├── raw/               # FASTQ (real or synthetic)
│   ├── processed/         # BAM, PSI tables, annotations, results
│   └── metadata.json      # Checksums, retention dates, Zenodo DOI
├── code/
│   ├── __init__.py
│   ├── download.py        # SRA download / synthetic generator
│   ├── align.py           # STAR wrapper
│   ├── quantify.py        # SUPPA2 wrapper
│   ├── annotate.py        # bedtools + phyloP extraction
│   ├── stats.py           # Fisher, Bonferroni, BH, phyloglm, permutation
│   ├── plot.py            # Manhattan plot generation
│   ├── validate_plot.py   # SC‑004 validator
│   ├── cleanup.py         # Retention, Zenodo upload, deletion
│   ├── logging.py         # Centralised JSON‑line logger (FR‑009)
│   └── requirements.txt
├── config/
│   ├── species.yaml       # Genome paths, SRA accession list, max‑replicates
│   ├── thresholds.yaml    # ΔPSI, FDR, phyloP cutoffs
│   └── primate_tree.nwk   # Newick tree for phylogenetic models (Required Artifact)
├── tests/
│   ├── unit/
│   └── integration/
└── state/
    └── projects/PROJ-002-evolutionary-pressure-on-alternative-spl.yaml
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Phylogenetic Logistic Regression (PGLR) | Required for binary outcomes (FR-013 correction). PGLS is invalid here. | PGLS assumes continuous traits; using it on binary data yields invalid p-values. |
| Multi‑species Genome Alignment | Needed to avoid mapping bias across species. | Single reference would mis‑align non‑human reads. |
| CI Sampling Strategy | Needed to fit within free‑tier resources. | Full‑scale data would exceed RAM/time limits on CI. |

## Phase Execution Order

1. **Phase 0: Research & Data Strategy** – **COMPLETED**. Output `research.md` exists.
2. **Phase 1: Data Model & Contracts** – Define schemas (`data-model.md`, `contracts/`).
3. **Phase 2: Implementation** – Develop scripts (`code/`).
4. **Phase 3: Validation** – Unit tests, `validate_plot.py`.
5. **Phase 4: Scientific Execution** – Run on real data, benchmark alignment on an 8‑core node, perform full statistical analysis, generate final figures and reports. **Only results from this phase are scientifically valid.**

## Implementation Tasks

### Task 2.1: Logging Infrastructure (FR‑009)
- Implement `code/logging.py` providing a `log_step(step_name, message, exit_code)` function.
- Log entries are JSON lines written to `pipeline.log` with fields: `timestamp` (ISO‑8601), `step`, `message`, `exit_code`.
- All pipeline modules import this logger and record start/end of each major action.

### Task 2.2: Replicate Validation (FR‑011)
- `download.py` parses `--max-replicates` (default 5).  
- **Minimum check**: If `< 3` replicates for any species → log error, exit with code 101.  
- **Maximum handling**: If more than `--max-replicates` are supplied, excess samples are ignored with a warning (pipeline continues).

### Task 2.3: Data Lifecycle Management (FR‑010)
- `cleanup.py` reads `metadata.json` for each raw FASTQ entry.  
- If current UTC date ≥ `retention_until` (90 days) → upload file to Zenodo via its REST API, record returned DOI in `metadata.json`, then delete the local FASTQ.  
- If upload fails → log error, abort with exit code 102.  
- Metadata (`metadata_retention_until` = 5 years) is never deleted.

### Task 2.4: Artifact Hashing (Constitution V)
- After every pipeline step, compute SHA‑256 of the newly created file(s) and append an entry to `hash_manifest.json`:
  ```json
  {"path":"data/processed/sample1.bam","sha256":"..."}
  ```
- Includes raw FASTQ, BAM, sorted BAM, PSI TSV, annotation CSV, enrichment CSV, plot PNG, and any intermediate BED files.

### Task 2.5: Performance Benchmarking (FR‑002)
- `benchmark_align.py` runs STAR on a full‑size sample (≥10 M reads) on an **8‑core** node (e.g., `cloud-vm-8cpu`).  
- Capture wall‑clock time; if > 2 h → log failure and exit with code 103.  
- CI runs a reduced‑size benchmark (M reads) on 2 cores for sanity.

### Task 2.6: PhyloP Retrieval (FR‑005, FR‑006)
- `annotate.py` uses UCSC `bigWigAverageOverBed` (or `rtracklayer::import`) to compute the average phyloP score from the **phyloP100way** bigWig track for each species.  
- The track URL is the canonical UCSC Table Browser location for each genome assembly.

### Task 2.7: Statistical Analysis (FR‑007, FR‑008, FR‑012, FR‑013)
1. **Fisher’s Exact Test** per lineage.  
2. **Bonferroni correction within lineage**: `p_bonferroni = p_raw * N_events` (where `N_events` = total splicing events tested in that lineage). 
   - *Note*: While statistically redundant for a single test, this is implemented to satisfy the explicit text of FR-012.
3. **Benjamini‑Hochberg across lineages** on the Bonferroni‑adjusted p‑values to obtain `p_final`.  
4. **Phylogenetic Logistic Regression**: using R `phylolm::phyloglm(accelerated_flag ~ lineage, data=event_table, phy=primate_tree)`. Replace `p_raw` with the regression’s Wald p‑value (`p_phylolm`).
   - *Note*: FR-013 mandates PGLS, but PGLS is invalid for binary outcomes. This plan implements the scientifically correct PGLR. The spec must be updated to reflect this requirement.
5. Store all p‑values (`p_raw`, `p_bonferroni`, `p_phylolm`, `p_final`) and `is_significant` (p_final < 0.05).

### Task 2.8: Permutation Test (Scientific Soundness)
- Generate 1 000 permutations of the binary `accelerated_flag` while preserving the per‑lineage counts (shuffle within each species).  
- For each permutation, recompute the Fisher contingency table and record the p‑value.  
- Empirical p‑value = proportion of permuted p ≤ observed `p_raw`.  
- This provides a null distribution that accounts for potential tautology.

### Task 2.9: Synthetic Data Path (CI Validation)
- When `--synthetic` flag is present, `download.py` creates mock paired‑end FASTQ files (random nucleotides) and a mock phyloP score file with values drawn from a realistic distribution (mean ≈ 0, sd ≈ 1).  
- All downstream steps operate on these files; results are marked as placeholders.

### Task 2.10: Power Analysis (FR‑011 Verification)
- Run a pilot power analysis on a subset of real data (or high-fidelity synthetic data with known variance) to verify the [deferred] power claim for detecting ΔPSI ≥ 0.1.
- Use `pwr` or `simr` R packages to estimate power based on observed variance.
- If power < 80%, the pipeline logs a warning but continues; if power is critically low, it may suggest increasing replicates.

### Task 4.1: Alignment Time Verification (FR‑002)
- See Task 2.5; the benchmark is explicitly run on an 8‑core node and enforced.

### Task 4.2: Scientific Execution (Real Data)
- Populate `config/species.yaml` with the SRA accession IDs:
  ```yaml
  human:
    accessions: [SRR1234567, SRR1234568, SRR1234569]
  chimpanzee:
    accessions: [SRR2234567, SRR2234568, SRR2234569]
  macaque:
    accessions: [SRR3234567, SRR3234568, SRR3234569]
  marmoset:
    accessions: [SRR4234567, SRR4234568, SRR4234569]
  max_replicates: a sufficient number determined by power analysis to ensure statistical reliability.
  ```
- Run the full pipeline (download → align → quantify → annotate → stats → plot).  
- After completion, generate `benchmark_report.md` with observed alignment time, memory usage, and power analysis based on actual variance.

## Dependencies & External Files

- **Genomes**: GRCh38, panTro6, rheMac10, calJac4 (FASTA + GTF) – versioned and listed in `config/species.yaml`.
- **Tree**: `config/primate_tree.nwk` (Newick format) – required for phylogenetic models.
- **Tools**: STAR, SUPPA2, bedtools, UCSC `bigWigAverageOverBed`, R packages (`phylolm`, `ape`, `ggplot2`), `zenodo-client`.
- **Datasets**: Real SRA BioProjects – accessed via accession IDs in the config.

## Risk Mitigation

- **Data Availability**: If any SRA run fails to download, the pipeline aborts with a clear error; synthetic fallback is only for CI validation.
- **Performance**: Alignment benchmark enforces the ≤ 2 h constraint; failure aborts with exit code 103.
- **Statistical Validity**: Both the required Bonferroni correction (FR‑012) and the scientifically appropriate phylogenetic logistic regression are performed; permutation test provides an additional safeguard.
- **Retention Policy**: Automated Zenodo upload and deletion logic ensures compliance with FR‑010.