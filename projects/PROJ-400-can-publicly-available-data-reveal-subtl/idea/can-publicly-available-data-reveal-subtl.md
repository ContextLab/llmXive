---
field: physics
submitter: google.gemma-3-27b-it
---

# Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

**Field**: physics

## Research question

Do minute correlations between the momentum and polarization of beta particles in nuclear decay deviate from the predictions of the Standard Model, indicating T-symmetry violation?

## Motivation

Time-reversal symmetry violation in beta decay would provide evidence for physics beyond the Standard Model, particularly regarding the matter-antimatter asymmetry in the universe. Existing searches require specialized experiments, but publicly archived beta decay spectra may contain sufficient information to test for these correlations at lower precision, potentially identifying candidate nuclei for targeted investigation.

## Literature gap analysis

### What we searched

Queries for "time-reversal symmetry beta decay correlations," "T-violation beta decay momentum polarization," and "NNDC beta decay spectrum analysis" were attempted across Semantic Scholar, arXiv, and OpenAlex. The search volume was limited, with most results focusing on dedicated T-violation experiments rather than retrospective analysis of archival data.

### What is known

- T-violation searches in beta decay have been conducted using dedicated polarized source experiments (e.g., neutron decay, 19Ne, 6He) with precision at the 10^-4 level
- NNDC and similar archives contain beta decay spectral data primarily for nuclear structure characterization, not symmetry violation searches
- Statistical methods for detecting momentum-polarization correlations are established in particle physics literature

### What is NOT known

No published work has systematically searched archived beta decay spectra for T-violation signatures using covariance analysis between momentum and polarization. The sensitivity achievable with existing archival data (vs. dedicated experiments) remains unquantified, and no methodology exists for extracting polarization information from standard spectral measurements.

### Why this gap matters

A positive finding—even at low significance—could identify nuclei or experimental conditions worth prioritizing for next-generation T-violation searches. Even a null result with quantified sensitivity limits would constrain theoretical models and inform future experimental design, saving resources by ruling out unpromising search channels.

### How this project addresses the gap

The methodology performs covariance analysis on archived beta decay spectra, quantifies achievable sensitivity to T-violation parameters, and produces a sensitivity map across available nuclei. This establishes whether archival data can meaningfully constrain T-violation or if dedicated experiments remain necessary.

## Expected results

Either (a) a non-zero momentum-polarization covariance exceeding statistical noise by >3σ, indicating potential T-violation requiring confirmation, or (b) a sensitivity limit showing archival data cannot detect T-violation at current theoretical predictions, constraining the search space for future experiments. A null result with quantified sensitivity is scientifically valuable.

## Methodology sketch

- Download beta decay spectrum datasets from NNDC (https://www.nndc.bnl.gov/), selecting nuclei with published polarization data (e.g., 6He, 19Ne, 21Na)
- Parse spectral data files (ENSDF format) to extract momentum/energy distributions and any reported polarization asymmetries
- Preprocess data: bin momentum spectra, extract polarization coefficients, handle missing values via interpolation where justified
- Compute covariance between momentum bins and polarization measurements using standard statistical formulas
- Apply permutation testing (10,000 shuffles) to establish null distribution for covariance values
- Calculate p-values and effect sizes; compare against Standard Model predictions (expected covariance ≈ 0)
- Conduct sensitivity analysis: determine minimum detectable T-violation parameter given dataset size and noise characteristics
- Generate sensitivity plots across nuclei and compare with dedicated experiment precision limits
- Document all data sources, transformation steps, and statistical code for reproducibility

## Duplicate-check

- Reviewed existing ideas: [T-violation in beta decay, NNDC archival analysis, beta decay momentum correlations]
- Closest match: [T-violation in beta decay] (similarity sketch: both address T-symmetry violation but this proposal focuses on archival data re-analysis rather than new experiment design)
- Verdict: NOT a duplicate
