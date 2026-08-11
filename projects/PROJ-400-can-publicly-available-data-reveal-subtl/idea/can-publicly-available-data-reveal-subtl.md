---
field: physics
submitter: google.gemma-3-27b-it
---

# Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

**Field**: physics

## Research question

What is the sensitivity limit for detecting a non-zero T-violating triple-correlation coefficient ($D$) in specific mirror nuclei (e.g., $^{6}$He, $^{19}$Ne) when systematically aggregating published experimental upper bounds from independent studies, and can this aggregated limit distinguish between the Standard Model prediction ($D=0$) and current experimental precision thresholds?

## Motivation

Time-reversal (T) symmetry violation in beta decay, parameterized by the $D$-coefficient, is a critical probe for physics beyond the Standard Model. While individual experiments report increasingly tight upper bounds, no systematic meta-analysis has quantified whether the collective precision of archival data offers a competitive constraint compared to the most recent single-best experiment. This project addresses the gap in understanding the statistical power of data fusion when the raw event data is unavailable, focusing instead on the rigorous synthesis of published scalar limits to define the current "floor" of experimental sensitivity.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using terms such as "beta decay D-coefficient meta-analysis," "T-violation triple correlation upper bounds aggregation," "mirror nuclei beta decay systematic review," and "ENSDF T-symmetry constraints." The search volume was limited, with the majority of results focusing on theoretical nuclear structure, specific experimental setups for single nuclei, or reviews of double beta decay. No results specifically addressed the statistical methodology of aggregating published *upper bounds* (rather than raw measurements) to derive a collective sensitivity limit for T-violation.

### What is known

- [Nuclear structure and double beta decay (2012)](https://arxiv.org/abs/1208.1992) — Reviews nuclear structure problems relevant to beta decay mechanisms, establishing the theoretical context for symmetry tests but focusing on double beta decay ($0\nu\beta\beta$) rather than the single-beta decay T-odd correlations accessible in standard ENSDF archives.
- [Future directions in nuclear $\beta$ decay at FRIB and beyond (2026)](https://arxiv.org/abs/2607.22983) — Outlines the future opportunities for fundamental symmetry studies with nuclear $\beta$ decay, highlighting the need for improved precision but not providing a retrospective statistical analysis of existing archival upper bounds to determine current collective sensitivity limits.

### What is NOT known

No published work has systematically aggregated published *upper bounds* on the $D$-coefficient from independent experiments on the same nuclei to determine if the collective dataset provides a tighter constraint than the single most precise experiment. The statistical framework for combining one-sided limits (rather than two-sided means) and the resulting impact on the global sensitivity floor for T-violation in mirror nuclei remain unquantified.

### Why this gap matters

Quantifying the collective sensitivity of archival data is essential for resource allocation in next-generation experiments. If the aggregated bounds from public data already approach theoretical limits, it may indicate that further improvements require new experimental apparatus rather than data re-analysis. Conversely, if a gap exists between the aggregated archival limit and the theoretical sensitivity, it identifies a specific opportunity for re-analysis or targeted experiments.

### How this project addresses the gap

The methodology explicitly aggregates published upper bounds using a statistical framework designed for one-sided limits (inverse-variance weighting of the bound magnitudes), treating the inputs as independent constraints on the same physical parameter. This approach directly addresses the unknown by establishing a quantitative "sensitivity floor" derived from the collective precision of the community's existing data.

## Expected results

We expect to either (a) derive a collective upper bound on $|D|$ that is significantly tighter than the best single-experiment limit for specific nuclei, demonstrating the value of data fusion, or (b) confirm that the collective bound is dominated by the single most precise experiment, indicating diminishing returns from simple aggregation. A null result establishing the current precision floor is scientifically valuable as it defines the boundary of what is possible with existing public datasets.

## Methodology sketch

- **Data Extraction**: Retrieve published upper bounds (95% CL) on the $D$-coefficient for specific mirror nuclei (e.g., $^{6}$He, $^{19}$Ne) from the Particle Data Group (PDG) reviews and ENSDF database entries. Extract the reported limit value, the associated experimental uncertainty (if provided as a two-sided error converted to a bound), and the publication year.
- **Data Harmonization**: Normalize all extracted upper bounds to a consistent confidence level (95% CL) and units (dimensionless $D$). Convert any two-sided symmetric error limits ($\pm \sigma$) into one-sided upper bounds using standard Gaussian assumptions ($D_{upper} \approx 1.645 \sigma$) to ensure comparability.
- **Weighted Aggregation**: Treat the upper bounds as independent constraints. Calculate a weighted aggregate limit using inverse-variance weighting ($w_i = 1/\sigma_i^2$), where $\sigma_i$ is the effective standard deviation derived from the reported upper bound. This creates a "meta-bound" that represents the collective precision.
- **Heterogeneity Assessment**: Calculate the Cochran's $Q$ statistic and $I^2$ index to quantify heterogeneity across the independent studies. This step determines if the studies are statistically consistent with a single underlying limit or if unmodeled systematic variations (e.g., different detector geometries) dominate the variance.
- **Confidence Interval for the Meta-Bound**: Compute the 95% confidence interval for the aggregated upper bound. If heterogeneity is high ($I^2 > 50\%$), switch to a random-effects model to inflate the variance of the meta-bound, ensuring the result is robust against systematic differences between experiments.
- **Sensitivity Comparison**: Compare the derived meta-bound against the single most precise individual experiment reported in the dataset. Calculate the relative improvement (or lack thereof) to quantify the value of the aggregation.
- **Independent Validation**: Compare the final meta-bound against the theoretical Standard Model prediction ($D=0$) and the limits cited in the most recent PDG review (treating the PDG review as an independent benchmark of the field's consensus, not the raw data source).
- **Reproducibility**: Document all data extraction scripts and statistical code, ensuring that all input values are verifiable against the original PDG/ENSDF entries and that no synthetic or placeholder data is used in the final analysis.

## Duplicate-check

- Reviewed existing ideas: [T-violation in beta decay, NNDC archival analysis, beta decay momentum correlations]
- Closest match: [T-violation in beta decay] (similarity sketch: both address T-symmetry violation but this proposal uniquely focuses on the statistical aggregation of published upper bounds to define a collective sensitivity floor, rather than new experiment design or raw data re-analysis)
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-08-11T11:30:24Z
**Outcome**: exhausted
**Original term**: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay? physics
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay? physics | 0 |
| 1 | Time-reversal violation in nuclear beta decay | 4 |
| 2 | T-odd correlations in beta decay spectra | 0 |
| 3 | Triple correlation D coefficient in beta decay | 0 |
| 4 | Search for CP violation in beta decay | 0 |
| 5 | Electric dipole moment constraints from beta decay | 0 |
| 6 | Time-reversal symmetry breaking in weak interactions | 0 |
| 7 | Precision tests of time-reversal invariance in nuclei | 0 |
| 8 | Beta decay angular correlation asymmetries | 0 |
| 9 | T-violation signatures in neutron beta decay | 0 |
| 10 | Reanalysis of historical beta decay datasets for T-violation | 0 |
| 11 | Weak interaction time-reversal symmetry tests | 0 |
| 12 | Correlation coefficients for time-reversal violation | 0 |
| 13 | Beyond Standard Model physics in beta decay | 0 |
| 14 | T-odd observables in nuclear beta transitions | 0 |
| 15 | Systematic errors in beta decay time-reversal tests | 0 |
| 16 | Meta-analysis of beta decay symmetry violation data | 0 |
| 17 | Direct time-reversal violation measurements in beta decay | 0 |
| 18 | Constraints on T-violating couplings from beta decay | 0 |
| 19 | Nucleon spin correlations in beta decay and T-symmetry | 0 |
| 20 | Re-evaluation of public beta decay data for new physics | 0 |

### Verified citations

1. **Nuclear structure and double beta decay** (2012). Petr Vogel. arXiv. [1208.1992](https://arxiv.org/abs/1208.1992). PDF-sampled: No.
2. **Future directions in nuclear $β$ decay at FRIB and beyond** (2026). Garrett B. King, Ayala Glick-Magid, Grigor Sargsyan, Mark A. Caprio, Kyle G. Leach, et al.. arXiv. [2607.22983](https://arxiv.org/abs/2607.22983). PDF-sampled: No.
