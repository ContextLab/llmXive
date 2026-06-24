---
field: physics
submitter: google.gemma-3-27b-it
---

# Investigating the Relationship Between Cosmic Ray Anisotropy and Solar Cycle Variations

**Field**: physics  

## Research question  

Do the large‑scale anisotropies observed in the arrival directions of TeV–PeV cosmic rays exhibit systematic modulation that correlates with the phase of the 11‑year solar cycle?

## Motivation  

Cosmic‑ray anisotropy at the ‑3 % level has been measured by IceCube and the Pierre Auger Observatory, yet the physical origin of these patterns remains uncertain. Solar activity reshapes the heliospheric magnetic field, which modulates the intensity of galactic cosmic rays on shorter (27‑day) timescales. Demonstrating a solar‑cycle‑linked modulation of anisotropy would bridge high‑energy cosmic‑ray propagation and heliospheric physics, providing a new constraint on particle‑transport models.

## Related work  

- [On the relationship of the 27‑day variations of the solar wind velocity and galactic cosmic ray intensity in minimum epoch of solar activity (2015)](https://arxiv.org/abs/1504.00778) — Shows 27‑day modulation of GCR intensity linked to solar‑wind speed, establishing a solar‑activity proxy relevant for our correlation analysis.  
- [Solar Modulation of Cosmic Rays during the Declining and Minimum Phases of Solar Cycle 23: Comparison with Past Three Solar Cycles (2013)](https://arxiv.org/abs/1311.7387) — Provides long‑term measurements of GCR intensity across solar‑cycle phases, useful for contextualising any anisotropy modulation.  
- [On the 27‑day Variations of Cosmic Ray Intensity in Recent Solar Minimum 23/24 (2015)](https://arxiv.org/abs/1504.00180) — Extends 27‑day analysis to the most recent minimum, confirming the robustness of solar‑wind–GCR connections.  
- [The Solar Cycle (2015)](https://arxiv.org/abs/1502.07020) — Comprehensive review of 11‑year solar‑activity indicators (sunspot number, IMF magnitude, solar‑wind speed) that we will use as proxies.  
- [Will Solar Cycles 25 and 26 Be Weaker than Cycle 24? (2017)](https://arxiv.org/abs/1711.04117) — Discusses predictions of future solar‑cycle strength, informing expectations for the latter part of our 10‑year data span.  
- [The State of Self‑Organized Criticality of the Sun During the Last 3 Solar Cycles. I. Observations (2010)](https://arxiv.org/abs/1006.4861) — Provides statistical characterisation of solar‑flare activity over multiple cycles, offering additional solar‑activity metrics.  
- [Similarities and Distinctions in Cosmic‑Ray Modulation during Different Phases of Solar and Magnetic Activity Cycles (2013)](https://arxiv.org/abs/1312.2002) — Analyses how GCR intensity depends on solar‑cycle polarity, directly relevant to testing polarity‑dependent anisotropy modulation.

## Expected results  

We anticipate detecting a statistically significant (|r| ≥ 0.4, two‑sided p ≤ 0.01 after block‑bootstrap correction and multiple‑testing adjustment) modulation of the large‑scale anisotropy amplitude that tracks the solar‑cycle phase. A positive correlation would appear as higher dipole strength near solar minimum; a lack of correlation or a phase lag inconsistent with heliospheric models would falsify the hypothesis.

## Methodology sketch  

1. **Data acquisition**  
   - Download IceCube public 10‑yr muon‑track dataset (IceCube Open Data portal).  
   - Download Pierre Auger public surface‑detector event files for the same period (Auger Open Data portal).  
   - Retrieve daily solar‑activity indices (sunspot number, solar‑wind speed, IMF magnitude) from NOAA NGDC FTP.  
2. **Pre‑processing**  
   - Convert event timestamps to UTC Julian dates; bin into 27‑day (Carrington) intervals.  
   - For each interval, build a relative‑intensity sky map (HEALPix Nside 64) and extract dipole & quadrupole components via spherical‑harmonic fitting.  
   - Align solar‑activity series to the same interval timestamps; apply a 27‑day moving average to reduce high‑frequency noise.  
3. **Time‑series construction**  
   - Create vectors of dipole amplitude and phase per interval for IceCube, Auger, and the combined dataset.  
   - Assemble three solar proxies (sunspot number, solar‑wind speed, IMF magnitude) for the identical timestamps.  
4. **Statistical analysis**  
   - Compute Pearson and Spearman correlation coefficients between anisotropy amplitude and each solar proxy for each detector (up to six tests).  
   - Estimate significance using a block‑bootstrap (block length = 27 days, 10 000 resamples) to preserve autocorrelation.  
   - Apply a Bonferroni correction for the six hypothesis tests; the adjusted significance threshold is α = 0.01 / 6 ≈ 0.0017.  
   - Declare success only if |r| ≥ 0.4 **and** the corrected p‑value ≤ 0.0017 for at least one proxy–detector pair.  
   - Complement with Lomb‑Scargle periodograms to verify power at the ~11‑year frequency.  
5. **Robustness checks**  
   - Repeat analysis using (a) IceCube only, (b) Auger only, and (c) the combined dataset.  
   - Test alternative temporal binning (14‑day, 54‑day) to assess sensitivity to interval choice.  
   - Perform a permutation test (10 000 random shuffles of the solar‑proxy series) to confirm that observed correlations exceed chance expectations.  
6. **Visualization & reproducibility**  
   - Plot dipole amplitude vs. each solar proxy, heat‑maps of correlation strength across the solar cycle, and periodograms highlighting the 11‑year peak.  
   - Publish all Python 3.11 scripts (`numpy`, `pandas`, `healpy`, `astropy`, `scipy`) and a `requirements.txt` that fit within the 2‑CPU, 7 GB RAM, 6‑hour GitHub Actions free‑tier limits.  

All steps are designed to run within the 6‑hour GHA runner budget (≈ 1 GB data download, ≤ 4 GB RAM, ≤ 2 cores).

## Duplicate-check  

- Reviewed existing ideas: *(none provided for comparison)*.  
- Closest match: N/A.  
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-24T21:10:25Z
**Outcome**: success
**Original term**: Investigating the Relationship Between Cosmic Ray Anisotropy and Solar Cycle Variations physics
**Verified citation count**: 7

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Investigating the Relationship Between Cosmic Ray Anisotropy and Solar Cycle Variations physics | 7 |

### Verified citations

1. **On the relationship of the 27-day variations of the solar wind velocity and galactic cosmic ray intensity in minimum epoch of solar activity** (2015). M. V. Alania, R. Modzelewska, A. Wawrzynczak. arXiv. [1504.00778](https://arxiv.org/abs/1504.00778). PDF-sampled: No.
2. **Solar Modulation of Cosmic Rays during the Declining and Minimum Phases of Solar Cycle 23: Comparison with Past Three Solar Cycles** (2013). O. P. M. Aslam,  Badruddin. arXiv. [1311.7387](https://arxiv.org/abs/1311.7387). PDF-sampled: No.
3. **On the 27-day Variations of Cosmic Ray Intensity in Recent Solar Minimum 23/24** (2015). R. Modzelewska, M. V. Alania. arXiv. [1504.00180](https://arxiv.org/abs/1504.00180). PDF-sampled: No.
4. **The Solar Cycle** (2015). David H. Hathaway. arXiv. [1502.07020](https://arxiv.org/abs/1502.07020). PDF-sampled: No.
5. **Will Solar Cycles 25 and 26 Be Weaker than Cycle 24 ?** (2017). J. Javaraiah. arXiv. [1711.04117](https://arxiv.org/abs/1711.04117). PDF-sampled: No.
6. **The State of Self-Organized Criticality of the Sun During the Last 3 Solar Cycles. I. Observations** (2010). Markus J. Aschwanden. arXiv. [1006.4861](https://arxiv.org/abs/1006.4861). PDF-sampled: No.
7. **Similarities and Distinctions in Cosmic-Ray Modulation during Different Phases of Solar and Magnetic Activity Cycles** (2013). O. P. M. Aslam,  Badruddin. arXiv. [1312.2002](https://arxiv.org/abs/1312.2002). PDF-sampled: No.
