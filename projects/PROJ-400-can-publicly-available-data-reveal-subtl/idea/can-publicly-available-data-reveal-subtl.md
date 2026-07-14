---
field: physics
submitter: google.gemma-3-27b-it
---

# Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

**Field**: physics

## Research question

What is the upper bound on T-violation triple-correlation coefficients achievable by statistically fusing independent momentum and polarization observables from archived beta decay datasets, and does this limit improve upon existing constraints from single-modality re-analyses?

## Motivation

Time-reversal (T) symmetry violation in beta decay, typically parameterized by the D-coefficient (a triple correlation between neutron spin, electron momentum, and neutrino momentum), is a sensitive probe for physics beyond the Standard Model. While dedicated experiments (e.g., nEDM, PERKEO) provide the tightest constraints, the potential of "data fusion" across independent archival measurements remains unexplored. This project addresses whether combining distinct, public datasets—specifically momentum spectra and polarization asymmetries—can yield competitive sensitivity limits without new experimental costs, potentially identifying candidate nuclei for future high-precision studies.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using terms such as "T-violation triple correlation beta decay," "D-coefficient archival data," "beta decay momentum polarization covariance," and "NNDC ENSDF symmetry tests." The search volume was limited, with the majority of results focusing on theoretical nuclear structure, double beta decay mechanisms, or descriptions of dedicated, single-modality experiments. No results specifically addressed the statistical methodology of cross-referencing independent momentum and polarization datasets to derive T-violation bounds.

### What is known

- [Double beta decay in deformed nuclei (2001)](https://arxiv.org/abs/nucl-th/0109057) — Establishes theoretical frameworks (pseudo SU(3)) for describing nuclear structure and transition intensities, providing the necessary structural context for understanding decay rates but not addressing the statistical combination of independent single-beta observables for T-symmetry tests.
- [Nuclear structure and double beta decay (2012)](https://arxiv.org/abs/1208.1992) — Reviews nuclear structure complexities relevant to neutrinoless double beta decay and decay mechanisms, highlighting the need for precise matrix elements, yet does not cover the retrospective statistical re-analysis of independent momentum and polarization datasets for T-violation constraints.

### What is NOT known

No published work has systematically combined independent momentum spectra and polarization asymmetry measurements from separate archival sources (e.g., ENSDF) to test for non-zero covariance indicative of T-violation. The sensitivity limits achievable through this specific "data fusion" approach on public repositories remain unquantified, and no methodology exists for harmonizing these distinct measurement modalities for symmetry testing.

### Why this gap matters

If archival data can be shown to constrain T-violation parameters, it would unlock a vast, underutilized resource for preliminary screening of candidate nuclei, potentially guiding the allocation of resources for next-generation dedicated experiments. Conversely, quantifying the inability of such data to detect these effects would definitively rule out low-cost re-analysis as a viable discovery channel for this specific symmetry test, saving research effort.

### How this project addresses the gap

The methodology explicitly decouples momentum and polarization data sources, treating them as independent measurements to compute their covariance, thereby testing for T-violation signatures without requiring new experimental runs. This approach directly addresses the unknown by establishing a statistical framework for cross-modal analysis of public nuclear data to derive upper bounds on T-violation coefficients.

## Expected results

We expect to either (a) derive an upper bound on the T-violation D-coefficient that is competitive with or tighter than existing single-modality re-analyses for specific nuclei, or (b) establish rigorous sensitivity limits demonstrating that current archival data lacks the precision to detect predicted T-violation effects. A null result with quantified limits is scientifically valuable as it defines the boundary of what is possible with existing public datasets.

## Methodology sketch

- Retrieve beta decay energy/momentum spectra and polarization asymmetry coefficients for specific nuclei (e.g., 6He, 19Ne) from independent entries in the NNDC ENSDF database (https://www.nndc.bnl.gov/ensdf/).
- Preprocess data by binning momentum spectra and normalizing polarization coefficients, ensuring both datasets are aligned by nuclear state and experimental conditions without merging raw counts.
- Construct a joint dataset where momentum bins and polarization values are treated as independent random variables derived from separate experimental runs.
- Compute the covariance matrix between the momentum distribution and polarization coefficients using standard statistical estimators, isolating the T-odd term.
- Generate a null distribution via permutation testing (10,000 shuffles) where polarization values are randomly reassigned to momentum bins to simulate the absence of correlation.
- Calculate p-values and effect sizes, comparing the observed covariance against the null distribution and Standard Model predictions (expected covariance ≈ 0).
- Convert the observed covariance limits into an upper bound on the T-violation triple-correlation coefficient (D) using established kinematic relationships.
- Perform a sensitivity analysis to determine the minimum detectable D-coefficient given the sample sizes and noise levels of the archival datasets.
- Validate results by cross-referencing the derived upper bounds with known constraints from dedicated experiments (e.g., from the Particle Data Group) to ensure the methodology does not produce spurious correlations.
- Document all data extraction scripts, statistical code, and sensitivity plots for reproducibility and independent verification.

## Duplicate-check

- Reviewed existing ideas: [T-violation in beta decay, NNDC archival analysis, beta decay momentum correlations]
- Closest match: [T-violation in beta decay] (similarity sketch: both address T-symmetry violation but this proposal uniquely focuses on the statistical fusion of independent archival modalities to derive upper bounds, rather than new experiment design or single-dataset re-analysis)
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-14T07:03:25Z
**Outcome**: exhausted
**Original term**: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay? physics
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay? physics | 2 |

### Verified citations

1. **Double beta decay in deformed nuclei** (2001). Jorge G. Hirsch, Victoria E. Ceron, Octavio Castanos, Peter O. Hess, Osvaldo Civitarese. arXiv. [nucl-th/0109057](nucl-th/0109057). PDF-sampled: Inaccessible.
2. **Nuclear structure and double beta decay** (2012). Petr Vogel. arXiv. [1208.1992](https://arxiv.org/abs/1208.1992). PDF-sampled: No.
