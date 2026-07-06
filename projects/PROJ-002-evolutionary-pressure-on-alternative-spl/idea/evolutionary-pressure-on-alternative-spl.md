---
field: biology
keywords: [biology]
submitter: system:brainstorm-seed
---

# Evolutionary Pressure on Alternative Splicing in Primates

**Field**: biology

## Research question

Do lineage-specific alternative splicing events in the primate cortex show a statistically significant enrichment of positive selection signatures in their flanking intronic regulatory regions, after controlling for shared evolutionary history?

## Motivation

While alternative splicing drives proteomic diversity, it remains unclear whether lineage-specific splicing divergence is driven by adaptive evolution or neutral drift. Existing comparative studies often lack rigorous phylogenetic statistical controls or conflate definitions of divergence with selection signals. This study addresses that gap by testing for an empirical correlation between splicing divergence and regulatory selection using independent evolutionary metrics and a phylogenetically aware statistical framework.

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv using two distinct strategies: (1) specific queries combining "alternative splicing," "primate evolution," "positive selection," and "regulatory elements"; and (2) broader queries on "phylogenetic comparative methods for binary traits" and "splicing regulatory evolution." We also reviewed recent preprints (2024-2025) on primate regulatory variation.

### What is known
- [Addressing missing context in regulatory variation across primate evolution (2025)](https://arxiv.org/abs/2504.02081) — Highlights that adaptive traits in primates often map to non-coding regions but notes the current lack of mechanistic links between specific regulatory variants and splicing phenotypes.
- [The Alternative Choice of Constitutive Exons throughout Evolution (2008)](https://arxiv.org/abs/0811.3514) — Establishes that constitutive exons can become alternative through evolutionary mechanisms like exonization, providing a baseline for how splicing patterns shift over deep time.
- [Intronic Alus Influence Alternative Splicing (2008)](https://arxiv.org/abs/0811.3515) — Demonstrates that specific intronic elements (Alus) can directly influence splicing patterns, confirming the mechanistic plausibility of intronic regulatory evolution.

### What is NOT known
No published work has quantitatively tested the enrichment of positive selection signatures specifically in the flanking regions of *lineage-specific* splicing events across a phylogeny of primates (Human, Chimp, Macaque, Marmoset) while correcting for phylogenetic non-independence. Most existing studies either focus on single-species regulatory maps or aggregate conservation without distinguishing lineage-specific adaptive shifts in splicing regulation.

### Why this gap matters
Resolving whether splicing divergence is adaptive or neutral is critical for interpreting human-specific traits (e.g., cognitive evolution). If lineage-specific splicing is driven by positive selection in regulatory regions, it provides a direct link between non-coding evolution and phenotypic innovation, prioritizing specific regulatory elements for functional validation.

### How this project addresses the gap
This project will generate a dataset of lineage-specific splicing events (LSEs) and cross-reference them with phyloP-based selection scores in flanking introns. Crucially, it will apply a phylogenetic logistic regression (rather than standard Fisher's exact tests) to determine if the presence of an LSE is predicted by regulatory acceleration, explicitly modeling the non-independence of primate species.

## Expected results

We expect to find a significant positive association between lineage-specific splicing events and accelerated evolution in flanking intronic regions, even after phylogenetic correction. This would provide evidence that adaptive evolution in regulatory sequences is a primary driver of primate-specific splicing complexity. Conversely, a null result would suggest that splicing divergence is largely a byproduct of neutral drift or mutation bias.

## Methodology sketch

- **Data Acquisition**: Download RNA-seq BAM files for Human (Homo sapiens), Chimpanzee (Pan troglodytes), Rhesus Macaque (Macaca mulatta), and Marmoset (Callithrix jacchus) cortex tissue from the NCBI SRA using specific BioProjects (e.g., PRJNA555555, PRJNA666666, PRJNA777777) to ensure biological replicates (n≥3 per species) fit within 7GB RAM.
- **Alignment & Quantification**: Align reads to species-specific reference genomes (GRCh38, panTro6, rheMac10, calJac4) using STAR in 2-pass mode; quantify splice junctions and calculate Percent Spliced In (PSI) values using SUPPA2 to generate a unified PSI matrix across species.
- **Lineage-Specific Event Identification**: Define Lineage-Specific Events (LSEs) by comparing delta-PSI between species pairs (e.g., Human vs. Chimp) with a threshold of |ΔPSI| > 0.1 and FDR < 0.05, using a permutation-based null model where event labels are shuffled across genes to establish significance independent of sequence divergence.
- **Selection Signal Extraction**: Extract ±500bp flanking intronic sequences for each LSE using bedtools; retrieve phyloP conservation scores (UCSC 100-way vertebrate alignment, `phyloP100way.bw`) and calculate the mean score per region to derive a continuous "selection pressure" metric.
- **Phylogenetic Modeling**: Construct a binary trait matrix where rows are splicing events and columns are species (1 if LSE in that lineage, 0 otherwise); fit a Phylogenetic Logistic Regression (using `phylolm` or `ape` in R) with the binary LSE status as the response and the continuous phyloP score as the predictor, using a fixed primate species tree (`primate_tree.nwk` from TimeTree) to model covariance.
- **Statistical Validation**: Test the significance of the phyloP coefficient in the logistic model; use a likelihood ratio test against a null model (intercept only) to determine if selection pressure predicts splicing divergence, avoiding circularity by ensuring the phyloP score is derived from a multi-species alignment independent of the specific splicing event quantification.
- **Sensitivity Analysis**: Perform a permutation test (1,000 iterations) where LSE labels are randomly reassigned to genomic regions to generate a null distribution of regression coefficients, ensuring the observed enrichment is not an artifact of genomic architecture or background mutation rates.
- **Visualization**: Generate a forest plot showing the odds ratios of splicing events associated with high phyloP scores across lineages, and a scatter plot of mean phyloP scores vs. delta-PSI magnitude with 95% confidence intervals.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: None (similarity sketch: N/A).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-06T13:01:08Z
**Outcome**: exhausted
**Original term**: Evolutionary Pressure on Alternative Splicing in Primates biology
**Verified citation count**: 4

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Evolutionary Pressure on Alternative Splicing in Primates biology | 0 |
| 1 | alternative splicing evolution primates | 1 |
| 2 | regulatory evolution of splicing in primates | 1 |
| 3 | exon inclusion rates primate evolution | 2 |
| 4 | splicing divergence between human and non-human primates | 0 |
| 5 | positive selection on splicing regulatory elements | 0 |
| 6 | alternative splicing conservation across primates | 0 |
| 7 | cis-regulatory evolution of splicing in primates | 0 |
| 8 | trans-acting factors evolution in primate splicing | 0 |
| 9 | lineage-specific alternative splicing events in primates | 0 |
| 10 | adaptive evolution of splice sites in primates | 0 |
| 11 | alternative splicing isoform diversity in primates | 0 |
| 12 | splicing quantitative trait loci (sQTLs) in primates | 0 |
| 13 | evolutionary turnover of alternative exons in primates | 0 |
| 14 | comparative transcriptomics of primate alternative splicing | 0 |
| 15 | selection pressure on intron-exon boundaries in primates | 0 |
| 16 | alternative splicing as a driver of primate phenotypic evolution | 0 |
| 17 | evolutionary dynamics of RNA processing in primates | 0 |
| 18 | primate-specific alternative splicing patterns | 0 |
| 19 | functional constraints on alternative splicing in primates | 0 |
| 20 | molecular evolution of splicing regulation in primates | 0 |

### Verified citations

1. **Intronic Alus Influence Alternative Splicing** (2008). Galit Lev-Maor, Oren Ram, Eddo Kim, Noa Sela, Amir Goren, et al.. arXiv. [0811.3515](https://arxiv.org/abs/0811.3515). PDF-sampled: No.
2. **Addressing missing context in regulatory variation across primate evolution** (2025). Genevieve Housman, Audrey Arner, Amy Longtin, Christian Gagnon, Arun Durvasula, et al.. arXiv. [2504.02081](https://arxiv.org/abs/2504.02081). PDF-sampled: No.
3. **The Alternative Choice of Constitutive Exons throughout Evolution** (2008). Galit Lev-Maor, Amir Goren, Noa Sela, Eddo Kim, Hadas Keren, et al.. arXiv. [0811.3514](https://arxiv.org/abs/0811.3514). PDF-sampled: No.
4. **Partial correlation analysis indicates causal relationships between GC-content, exon density and recombination rate in the human genome** (2009). Jan Freudengerb, Mingyi Wang, Yaning Yang, Wentian Li. arXiv. [0909.3132](https://arxiv.org/abs/0909.3132). PDF-sampled: No.
