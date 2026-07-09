# Implementation Plan: Evolutionary Pressure on Alternative Splicing in Primates

**Branch**: `PROJ-002-001-evolutionary-pressure` | **Date**: 2026-07-08 | **Spec**: [spec.md](../specs/PROJ-002-001-evolutionary-pressure/spec.md)  
**Input**: Feature specification from `/specs/PROJ-002-001-evolutionary-pressure/spec.md`

## Summary
The project must (1) download cortex RNA‑seq FASTQ files for human, chimpanzee, macaque, and marmoset (minimum 3, maximum 5 replicates per species), (2) align reads with STAR, (3) quantify splice‑junction usage and compute PSI values (SUPPA2), (4) identify lineage‑specific splicing events (|ΔPSI| > 0.1, FDR < 0.05), (4b) generate a matched control set of non-LSE regions to break circularity, (4c) aggregate counts, (4d) assemble the regression cohort, (5) extract ±500 bp intronic flanks, (6) annotate them with real phyloP multi-way scores (using continuous values for primary analysis), (6b) perform a sensitivity analysis on the acceleration threshold, (7) test enrichment using phylogenetic logistic regression (`phylolm::phyloglm`) with a permutation‑based null (shuffling labels across the combined LSE+Control set), (8) produce a Manhattan‑style plot, and (9) log every step, hash all artifacts, and manage lifecycle. All steps must be reproducible on a free‑tier GitHub Actions runner (CPU‑only, ≤6 h) via a "Sampled Mode", with "Full Mode" for local/HPC execution.

## Compute Feasibility & CI Constraints
The full pipeline (multiple samples, a large number of permutations) exceeds the free-tier CI limits (GB RAM, 6h runtime). To ensure `research_complete` is reachable on CI:
- **CI Mode (Sampled)**: Uses 1 sample per species (synthetic or real subset), A series of permutations, and pre-aligned BAMs where possible. Runtime target: < 2 hours.
- **Full Mode (Local/HPC)**: Uses all replicates, A sufficient number of permutations, full alignment. Requires ≥ 32GB RAM and ≥ 8 cores.
- **Library Pins**: `torch` (CPU-only), `scikit-learn`, `phylolm` (R). No CUDA/GPU dependencies.
- **Data Sampling**: If real data is used in CI, the pipeline automatically subsamples to the A fixed number of reads per FASTQ to fit memory.

## Technical Context
- **Language/Version**: Python 3.11, R 4.3, Bash
- **Primary Dependencies**:
  - Python: `pandas`, `numpy`, `pyyaml`, `biopython`, `requests`, `tqdm`, `pybedtools`, `pyBigWig`, `scikit-learn`, `loguru`
  - R: `phylolm`, `ape`, `data.table`, `ggplot2`
  - System: `STAR` 2.7.11a, `SUPPA2`, `bedtools` 2.30.0, `samtools` 1.20, `sra-toolkit`
- **Storage**: File‑based hierarchy under `data/` and `results/`
- **Testing**: `pytest` for Python modules, `testthat` for R scripts, integration tests via synthetic data.
- **Target Platform**: Linux (Ubuntu‑22.04) on GitHub Actions runners (CI) and HPC (Full).
- **Performance Goals**: Alignment ≤ 2 h per sample on 8‑core reference node; CI total runtime ≤ 6 h.
- **Constraints**: CPU‑only (no GPU), maximum RAM ≈ 7 GB for CI, disk ≈ 14 GB.
- **Scale/Scope**: Four primate species, 3–5 replicates each (≈ 12–20 samples total).

## Constitution Check
| Principle | Compliance Check |
|-----------|------------------|
| I. Reproducibility | All scripts are deterministic, random seeds pinned, external data fetched via SRA Toolkit (no hard‑coded URLs). |
| II. Verified Accuracy | All citations (e.g., phyloP track, `phylolm` paper) will be validated by the Reference‑Validator before acceptance. |
| III. Data Hygiene | Checksums recorded in `artifacts_manifest.json`; no in‑place modification. |
| IV. Single Source of Truth | Every figure/table traced to a single row in the final TSVs via `result_id`. |
| V. Versioning Discipline | Content hashes recorded for every artifact; `pipeline.log` includes SHA‑256. |
| VI. Cross‑Species Data Harmonization | Reference genome versions (GRCh*, panTro*, rheMac*, calJac*) listed in `config/genomes.yaml`; orthology mapping via Ensembl Compara will be performed before cross‑species aggregation. |
| VII. Phylogenetic Statistical Independence | Phylogenetic logistic regression with `primate_tree.nwk`; permutation respects phylogenetic distance and shuffles across the combined cohort. |

## Project Structure
```text
specs/PROJ-002-001-evolutionary-pressure/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── lineage_events.schema.yaml
│   ├── enrichment_results.schema.yaml
│   ├── control_region.schema.yaml
│   └── splicing_event.schema.yaml
└── tasks.md          # generated later by /speckit-tasks
```

```text
src/
├── pipeline/
│   ├── download.py
│   ├── align.py
│   ├── quantify.py
│   ├── detect_events.py
│   ├── generate_controls.py
│   ├── aggregate_counts.py
│   ├── assemble_cohort.py
│   ├── annotate_phyloP.py
│   ├── stats.R
│   ├── sensitivity_analysis.py
│   ├── plot.py
│   └── lifecycle.py
├── utils/
│   ├── logger.py
│   └── hash.py
├── config/
│   ├── genomes.yaml
│   └── species_replicates.yaml
tests/
├── unit/
│   ├── test_download.py
│   ├── test_align.py
│   └── …
├── integration/
│   └── test_full_pipeline.py
└── contract/
    ├── test_lineage_schema.py
    └── test_enrichment_schema.py
```

## Phase Overview & Mapping to FR/SC

| Phase | Description | FRs Covered | SCs Covered |
|-------|-------------|-------------|-------------|
| **0 – Research & Feasibility** | Verify dataset accessibility, benchmark STAR on synthetic reads, prototype phyloP extraction. | FR‑015, FR‑016 | – |
| **0.5 – Power Analysis** | Execute `power_analysis.R` to validate the minimum 3 replicates requirement. | FR‑011 | – |
| **1 – Data Acquisition & QC** | Download FASTQs via SRA Toolkit, enforce replicate limits (error 101/102), generate `pipeline.log` and checksums. | FR‑001, FR‑009, FR‑010, FR‑011 | SC‑001 |
| **2 – Alignment** | Run STAR with default params, log wall‑time, abort on >2 h (validation script). | FR‑002, FR‑009, FR‑015 | SC‑001 |
| **3 – PSI Quantification** | SUPPA2 quantifies junctions → unified PSI TSV. | FR‑003, FR‑009 | SC‑001 |
| **4 – Lineage‑Specific Event Detection** | Apply |ΔPSI| > 0.1 & BH‑FDR < 0.05 → `lineage_specific_events.tsv`. Populate `is_placeholder` based on data source. | FR‑004, FR‑009 | SC‑002 |
| **4b – Control Set Generation** | Generate a matched set of non-LSE intronic regions (matched on exon length, expression, conservation) to serve as the neutral baseline. | FR‑007 | SC‑002 |
| **4c – Aggregate Counts** | Compute `count_LSE`, `count_NonLSE`, `n_lse_accelerated`, etc., per lineage. | FR‑004, FR‑007 | SC‑002 |
| **4d – Cohort Assembly** | Merge LSEs and Controls into a single dataframe (`regression_cohort.tsv`) linked by `event_id`. | FR‑007 | SC‑002 |
| **5 – Flanking Sequence Extraction** | bedtools `getfasta` (±500 bp). | FR‑005, FR‑009 | SC‑001 |
| **6 – PhyloP Annotation** | Query UCSC multi-way bigWig via `pyBigWig`; compute mean, flag accelerated (≤‑2.0) for descriptive stats. | FR‑005, FR‑006, FR‑009 | SC‑001 |
| **6b – Sensitivity Analysis** | Sweep acceleration threshold (±0.5) to validate robustness of the binary flag. | FR‑014 | – |
| **7 – Enrichment Testing** | R script (`stats.R`) runs `phylolm::phyloglm` per lineage using `mean_phyloP` (continuous) as predictor. Includes control regions. Permutation (a sufficient number for CI, A substantial number of samples for Full) shuffles 'accelerated' labels across the *combined* LSE+Control cohort. Applies BH‑FDR across lineages. | FR‑007, FR‑008, FR‑012, FR‑013, FR‑014, FR‑009 | SC‑003, SC‑004 |
| **8 – Plot Generation** | PNG Manhattan plot (≥ 1200×800). Traceable via `result_id`. | FR‑008, FR‑009 | SC‑004 |
| **9 – Lifecycle Management** | `lifecycle.py` compresses FASTQs after 90 days, deposits to Zenodo, writes `metadata.json`. | FR‑010, FR‑009 | SC‑005 |
| **10 – Validation & CI** | Synthetic‑data tests for each module; ensure abort codes, hash logging, placeholder flagging. | FR‑015, FR‑016 | SC‑001‑SC‑005 |

## Detailed Task List (to be emitted by `/speckit-tasks`)

1. `tasks/download.yml` – download FASTQs, validate replicate count.
2. `tasks/align.yml` – STAR alignment, time logging, checksum.
3. `tasks/quantify.yml` – SUPPA2 PSI generation.
4. `tasks/detect_events.yml` – ΔPSI & FDR filtering, populate `is_placeholder`.
5. `tasks/power_analysis.yml` – execute `power_analysis.R` script.
6. `tasks/generate_controls.yml` – generate matched non-LSE control regions.
7. `tasks/aggregate_counts.yml` – compute lineage counts.
8. `tasks/assemble_cohort.yml` – merge LSEs and Controls.
9. `tasks/extract_flanks.yml` – bedtools getfasta.
10. `tasks/annotate_phyloP.yml` – pyBigWig mean score, accelerated flag.
11. `tasks/sensitivity_analysis.yml` – threshold sweep (±0.5).
12. `tasks/enrichment.yml` – R `phyloglm` (continuous predictor), permutation, BH correction.
13. `tasks/plot.yml` – PNG generation.
14. `tasks/lifecycle.yml` – cron‑driven compression & Zenodo upload.
15. `tasks/validation.yml` – synthetic data runs, abort‑code checks, placeholder tagging.

All tasks will be orchestrated by a top‑level `run_pipeline.sh` wrapper that respects the ordering above.

---