---
field: physics
submitter: google.gemma-3-27b-it
---

# Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

**Field**: physics

## Research question

What is the upper bound on the T-violating triple-correlation coefficient ($D$) achievable by performing a meta-analysis of independent experimental measurements of beta-decay energy spectra and polarization asymmetries archived in the ENSDF database, and does this bound improve upon existing constraints derived from single-experiment re-analyses?

## Motivation

Time-reversal (T) symmetry violation in beta decay, parameterized by the $D$-coefficient (a triple correlation between neutron spin, electron momentum, and neutrino momentum), is a sensitive probe for physics beyond the Standard Model. While dedicated experiments provide the tightest constraints, the potential of statistically fusing independent archival measurements remains unexplored. This project addresses whether combining distinct, public datasets—specifically momentum spectra and polarization asymmetries—can yield competitive sensitivity limits without new experimental costs, potentially identifying candidate nuclei for future high-precision studies.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using terms such as "T-violation triple correlation beta decay," "D-coefficient archival data meta-analysis," "beta decay momentum polarization covariance," and "ENSDF symmetry tests." The search volume was limited, with the majority of results focusing on theoretical nuclear structure, double beta decay mechanisms, or descriptions of dedicated, single-modality experiments. No results specifically addressed the statistical methodology of cross-referencing independent momentum and polarization datasets to derive T-violation bounds via meta-analysis of published coefficients.

### What is known

- [Beta Decay in Medium-Mass Nuclei with the In-Medium Similarity Renormalization Group (2021)](https://arxiv.org/abs/2109.13462) — Establishes theoretical frameworks for calculating allowed beta decays (Fermi and Gamow-Teller) within ab initio approaches, providing the necessary nuclear matrix elements to interpret decay rates but not addressing the statistical combination of independent experimental observables for T-symmetry tests.
- [Characterization of the Si(Li) detector for Monte Carlo calculations of beta spectra (2019)](https://arxiv.org/abs/1904.01294) — Details the precise modeling of detector response for beta spectra, highlighting the importance of instrument-specific corrections in spectral analysis, yet does not cover the retrospective statistical re-analysis of independent momentum and polarization datasets for T-violation constraints.
- [Neutrinoless Double Beta Decay and Physics Beyond the Standard Model (2012)](https://arxiv.org/abs/1208.0727) — Reviews the connection between lepton number violation and neutrino masses, establishing the theoretical context for symmetry tests but focusing on double beta decay rather than the single-beta decay T-odd correlations accessible in standard ENSDF archives.

### What is NOT known

No published work has systematically combined independent momentum spectra and polarization asymmetry measurements from separate archival sources (e.g., ENSDF) to test for non-zero covariance indicative of T-violation. The sensitivity limits achievable through this specific "data fusion" approach on public repositories remain unquantified, and no methodology exists for harmonizing these distinct measurement modalities for symmetry testing.

### Why this gap matters

If archival data can be shown to constrain T-violation parameters, it would unlock a vast, underutilized resource for preliminary screening of candidate nuclei, potentially guiding the allocation of resources for next-generation dedicated experiments. Conversely, quantifying the inability of such data to detect these effects would definitively rule out low-cost re-analysis as a viable discovery channel for this specific symmetry test, saving research effort.

### How this project addresses the gap

The methodology explicitly decouples momentum and polarization data sources, treating them as independent measurements to compute their weighted aggregate, thereby testing for T-violation signatures without requiring new experimental runs. This approach directly addresses the unknown by establishing a statistical framework for cross-modal analysis of public nuclear data to derive upper bounds on T-violation coefficients.

## Expected results

We expect to either (a) derive an upper bound on the T-violation D-coefficient that is competitive with or tighter than existing single-modality re-analyses for specific nuclei, or (b) establish rigorous sensitivity limits demonstrating that current archival data lacks the precision to detect predicted T-violation effects. A null result with quantified limits is scientifically valuable as it defines the boundary of what is possible with existing public datasets.

## Methodology sketch

- **Data Extraction**: Retrieve published beta decay energy/momentum spectra parameters and polarization asymmetry coefficients for specific nuclei (e.g., $^{6}$He, $^{19}$Ne) from independent entries in the NNDC ENSDF database (https://www.nndc.bnl.gov/ensdf/). All values will be extracted as reported experimental measurements with their associated statistical and systematic uncertainties.
- **Data Harmonization**: Normalize all extracted coefficients to a common kinematic basis (e.g., standard D-coefficient units) using established kinematic relationships, ensuring no simulated data is generated; only scaling of reported values is performed.
- **Meta-Analysis Construction**: Treat the extracted coefficients from different experiments as independent samples of the same underlying physical parameter ($D$). Construct a weighted mean estimator where weights are the inverse variance ($1/\sigma^2$) of each reported measurement.
- **Heterogeneity Assessment**: Calculate the Cochran's $Q$ statistic and $I^2$ index to quantify heterogeneity across the independent datasets. This step determines whether the datasets are statistically consistent with a single null hypothesis ($D=0$) or if unmodeled systematic variations exist.
- **Confidence Interval Calculation**: Compute the 95% confidence interval for the combined $D$-coefficient using the standard error of the weighted mean derived strictly from the reported experimental uncertainties.
- **Upper Bound Derivation**: If the confidence interval includes zero, calculate the one-sided 95% upper bound on $|D|$ using the profile likelihood method applied to the aggregated real measurements.
- **Sensitivity Analysis**: Perform a leave-one-out cross-validation to determine the influence of individual experiments on the final bound, ensuring the result is not driven by a single outlier measurement.
- **Independent Validation**: Compare the derived upper bound with the most stringent limits from dedicated experiments reported in the Particle Data Group reviews (using their explicitly stated values as an independent benchmark, not derived from the ENSDF data).
- **Reproducibility**: Document all data extraction scripts and statistical code, ensuring that all input values are verifiable against the original ENSDF entries and that no synthetic or placeholder data is used in the final analysis.

## Duplicate-check

- Reviewed existing ideas: [T-violation in beta decay, NNDC archival analysis, beta decay momentum correlations]
- Closest match: [T-violation in beta decay] (similarity sketch: both address T-symmetry violation but this proposal uniquely focuses on the statistical fusion of independent archival modalities to derive upper bounds, rather than new experiment design or single-dataset re-analysis)
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-22T19:53:52Z
**Outcome**: success_after_expansion
**Original term**: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay? physics
**Verified citation count**: 6

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay? physics | 6 |

### Verified citations

1. **Symmetry and localization in periodic crystals: triviality of Bloch bundles with a fermionic time-reversal symmetry** (2016). Domenico Monaco, Gianluca Panati. arXiv. [1601.02906](https://arxiv.org/abs/1601.02906). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
2. **Characterization of the Si(Li) detector for Monte Carlo calculations of beta spectra** (2019). Pavel Novotny, Pavel Dryak, Jaroslav Solc, Petr Kovar, Zdenek Vykydal. arXiv. [1904.01294](https://arxiv.org/abs/1904.01294). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
3. **Results on Dark Matter and beta beta decay modes by DAMA at Gran Sasso** (2007). R. Bernabei. arXiv. [0704.3543](https://arxiv.org/abs/0704.3543). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
4. **Neutrinoless Double Beta Decay and Physics Beyond the Standard Model** (2012). Frank F. Deppisch, Martin Hirsch, Heinrich Päs. arXiv. [1208.0727](https://arxiv.org/abs/1208.0727). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
5. **Neutrinoless double beta decay and neutrino physics** (2012). Werner Rodejohann. arXiv. [1206.2560](https://arxiv.org/abs/1206.2560). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
6. **Beta Decay in Medium-Mass Nuclei with the In-Medium Similarity Renormalization Group** (2021). S. R. Stroberg. arXiv. [2109.13462](https://arxiv.org/abs/2109.13462). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
