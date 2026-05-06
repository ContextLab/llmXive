---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Coral Resilience to Thermal Stress Using Publicly Available Genomic Data

**Field**: biology

## Research question

How do single-nucleotide polymorphisms (SNPs) in heat-shock protein and oxidative stress pathways correlate with survival phenotypes in *Acropora millepora* populations exposed to thermal stress?

## Motivation

Coral reefs are deteriorating rapidly due to ocean warming, yet specific genomic markers of thermal tolerance remain unidentified. Bridging this gap enables conservationists to prioritize resilient genotypes for restoration without requiring new field experiments.

## Literature gap analysis

### What we searched

Queries included "coral thermal stress GWAS", "genomic prediction coral heat tolerance", and "coral assisted evolution genetic markers" across Semantic Scholar and arXiv. The search yielded background literature on sequencing methods and restoration paradigms but no direct studies applying GWAS to public genomic data for thermal resilience prediction.

### What is known

- [Sequencing and de novo analysis of a coral larval transcriptome using 454 GSFlx (2009)](https://doi.org/10.1186/1471-2164-10-219) — Establishes that coral genomic data (transcriptomes) is publicly available via NCBI, providing the foundational data source.
- [Building coral reef resilience through assisted evolution (2015)](https://doi.org/10.1073/pnas.1422301112) — Defines the conservation context and the concept of genetic enhancement for thermal resilience, motivating the search for specific markers.
- [Shifting paradigms in restoration of the world's coral reefs (2017)](https://doi.org/10.1111/gcb.13647) — Highlights the urgency of management interventions but does not specify the genomic tools required for them.

### What is NOT known

No published work has systematically applied genome-wide association studies (GWAS) to publicly available coral sequencing data to identify predictive SNPs for thermal survival. Existing studies focus on general sequencing capabilities or broad management strategies rather than specific genotype-phenotype correlations for heat stress.

### Why this gap matters

Identifying specific resilience markers allows for data-driven selection in reef restoration, moving beyond trial-and-error approaches. Filling this gap provides a scalable, computational method to support assisted evolution programs without new wet-lab costs.

### How this project addresses the gap

The methodology downloads public variant data (VCF/FASTQ) and applies statistical association testing (PLINK) to link SNPs with survival metadata. This directly produces the previously unavailable evidence of specific genetic variants correlated with thermal tolerance.

## Expected results

We expect to identify a small set of candidate SNPs (p < 0.05 after correction) enriched in stress-response pathways that correlate with high survival rates. A null result (no significant SNPs) would suggest thermal resilience is polygenic or environmentally plastic, which also informs conservation strategy by ruling out simple marker selection.

## Methodology sketch

- Download pre-processed variant call files (VCF) or raw FASTQ for *Acropora millepora* from NCBI BioProject PRJNA292777 and related thermal stress datasets.
- Filter variants to retain only those with minor allele frequency (MAF) > 0.05 and missingness < 10% to reduce dataset size for 7GB RAM limits.
- Extract phenotype data (survival status, temperature exposure) from associated metadata in the SRA run selector.
- Perform genome-wide association using PLINK (linear/logistic regression) on the filtered variant set.
- Conduct pathway enrichment analysis on significant hits using g:Profiler to identify biological mechanisms (e.g., heat-shock proteins).
- Visualize Manhattan plots and effect sizes using standard R packages (ggplot2) to confirm statistical robustness.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: None.
- Verdict: NOT a duplicate
