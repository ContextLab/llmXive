# Implementation Plan: Evolutionary Pressure on Alternative Splicing in Primates

**Branch**: `PROJ-002-001-evolutionary-pressure` | **Date**: 2026-06-29 | **Spec**: [spec.md](../specs/PROJ-002-001-evolutionary-pressure/spec.md)  
**Input**: Feature specification from `/specs/PROJ-002-001-evolutionary-pressure/spec.md`

## Summary
The project must generate PSI values from cortex RNA‑seq for four primate species, annotate ±500 bp flanking intronic regions with phyloP scores, flag accelerated evolution, and test enrichment of lineage‑specific splicing events using Fisher’s exact test, multiple‑testing correction, and phylogenetic generalized least squares (PGLS). All steps must be reproducible, logged, and archived according to the constitution.

## Technical Context
- **Language/Version**: Python 3.11, R 4.3  
- **Primary Dependencies**:  
  - Python: `pysradb`, `star-aligner`, `supplight` (wrapper for SUPPA2), `pandas`, `pybedtools`, `requests`, `pytest`  
  - R: `caper`, `ape`, `ggplot2`, `data.table`  
  - System: `STAR`, `SUPPA2`, `bedtools`, `samtools` (all CPU‑only)  
- **Storage**: File‑system hierarchy under `data/` (raw FASTQ, BAM, PSI tables, annotations, results).  
- **Testing**: `pytest` for Python modules, `testthat` for R scripts, plus the project‑provided validation scripts (`validate_psi.py`, `validate_plot.py`).  
- **Target Platform**: Linux (Ubuntu 22.04) GitHub Actions runner (2 CPU cores, ~7 GB RAM, 14 GB disk).  
- **Project Type**: CLI / workflow‑oriented research pipeline.  
- **Constraints**: Must run on free‑tier CI (no GPU, ≤6 h total runtime). All tools must be installable via `conda`/`pip` without CUDA.  
- **Scale/Scope**: Up to 4 species × ≤ 5 samples each (max 20 samples).  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All external datasets are fetched via deterministic SRA queries; random seeds are fixed in `code/config.yaml`. |
| II. Verified Accuracy | Citations are limited to peer‑reviewed methods (STAR, SUPPA2, phyloP, caper). |
| III. Data Hygiene | Checksums recorded in `data/checksums.md`; every transformation writes a new file. |
| IV. Single Source of Truth | Each figure/table is generated directly from a single TSV/CSV output (e.g., `lineage_specific_events.tsv`). |
| V. Versioning Discipline | All artifacts are hashed; `state/projects/...yaml` will be updated by the CI. |
| VI. Cross‑Species Data Harmonization | Reference genomes (GRCh38, panTro6, rheMac10, calJac4) are version‑pinned; orthology mapping will use Ensembl Compara release 110. |
| VII. Phylogenetic Statistical Independence | Enrichment p‑values are adjusted with PGLS via the `caper` R package using `primate_tree.nwk`. |

## Project Structure
```text
specs/PROJ-002-001-evolutionary-pressure/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── splicing_event.schema.yaml
    └── enrichment_result.schema.yaml

code/
├── config.yaml                # global parameters, seeds, paths
├── download_sra.py            # FR‑001
├── align_star.py              # FR‑002
├── quantify_suppa.py          # FR‑003
├── filter_events.py           # FR‑004
├── annotate_flanks.py         # FR‑005, FR‑006
├── enrichment_fisher.py       # FR‑007, FR‑012
├── phylo_correction.R        # FR‑013
├── plot_manhattan.R           # FR‑008
├── utils/
│   └── logger.py
└── tests/
    ├── contract/
    │   ├── test_splicing_event_schema.py
    │   └── test_enrichment_result_schema.py
    └── integration/
        └── test_end_to_end.py

data/
├── raw/                       # FASTQ files (FR‑010)
├── aligned/                   # BAM files
├── psi/                       # PSI tables
├── events/                    # lineage_specific_events.tsv
├── annotations/               # BED, FASTA, phyloP CSV
└── results/                   # enrichment.tsv, manhattan.png
```

## Phase‑wise Plan (mapping FR/SC)

| Phase | Description | Key Scripts | FR IDs | SC IDs |
|-------|-------------|-------------|--------|--------|
| 0 | **Research & Dataset Verification** – confirm availability of primate cortex RNA‑seq SRA accessions. | `research.md` (analysis) | – | – |
| 1 | **Download FASTQ** – use `pysradb` to fetch reads into `data/raw/`. | `download_sra.py` | FR‑001, FR‑011 (replicate check) | SC‑001 |
| 2 | **Alignment** – run STAR per species with reference genome; produce sorted BAM. | `align_star.py` | FR‑002, FR‑009 (logging) | SC‑001 |
| 3 | **Quantify PSI** – SUPPA2 `psiPerEvent` on each BAM → unified TSV. | `quantify_suppa.py` | FR‑003, FR‑009 | SC‑001 |
| 4 | **Identify Lineage‑Specific Events** – filter ΔPSI > 0.1 & FDR < 0.05. | `filter_events.py` | FR‑004, FR‑009 | SC‑001 |
| 5 | **Extract Flanking Sequences** – bedtools `getfasta` ±500 bp. | `annotate_flanks.py` | FR‑005, FR‑009 | SC‑001 |
| 6 | **Retrieve phyloP Scores** – query UCSC 100‑way via HTTP API; compute average, flag accelerated (≤ ‑2.0). | `annotate_flanks.py` (continued) | FR‑006, FR‑009 | SC‑001 |
| 7 | **Enrichment Test (Fisher)** – build contingency tables per lineage, compute raw p, odds ratio. | `enrichment_fisher.py` | FR‑007, FR‑009 | SC‑001 |
| 8 | **Multiple‑Testing Corrections** – apply BH across lineages (FR‑012) and Bonferroni within lineage; store corrected p. | `enrichment_fisher.py` | FR‑012, FR‑009 | SC‑001 |
| 9 | **Phylogenetic Correction** – PGLS via `caper`; replace raw p with phylo‑adjusted p. | `phylo_correction.R` | FR‑013, FR‑009 | SC‑001 |
|10 | **Visualization** – Manhattan plot PNG, size ≥ 1200 × 800 px, threshold line. | `plot_manhattan.R` | FR‑008, FR‑009 | SC‑004 |
|11 | **Archival & Metadata** – compress raw FASTQ after 90 days, upload to Zenodo, write DOI to `metadata.json`. | `utils/archiver.py` (scheduled) | FR‑010, FR‑009 | SC‑001 |
|12 | **Validation & Reporting** – run `validate_psi.py` & `validate_plot.py`; generate final report. | `tests/integration/test_end_to_end.py` | – | SC‑001, SC‑004 |

All phases are ordered so that data is available before consumption, models are fitted before evaluation, and figures are generated before inclusion in the manuscript.

## Risk & Mitigation
- **Dataset Availability** – No verified primate cortex RNA‑seq URLs are supplied. Phase 0 will abort with a clear error if required SRA accessions cannot be resolved. The pipeline can be rerun once appropriate accession IDs are provided.
- **Runtime Limits** – STAR alignment is the most expensive step; we cap samples at 5 per species and enforce the 2‑hour per‑sample limit (FR‑002). If a sample exceeds this, the job fails early with log entry (FR‑009).
- **Memory Footprint** – All intermediate files are streamed where possible; BAM sorting uses `samtools sort -@ 2` to stay within 7 GB RAM.

---
