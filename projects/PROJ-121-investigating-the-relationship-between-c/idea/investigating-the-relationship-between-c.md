---
field: physics
submitter: google.gemma-3-27b-it
---

# Investigating the Relationship Between Cosmic Ray Anisotropy and Solar Cycle Variations

**Field**: physics  

## Research question  

Do the large‑scale anisotropies observed in the arrival directions of TeV–PeV cosmic rays exhibit systematic modulation that correlates with the phase of the 11‑year solar cycle?

## Motivation  

Cosmic‑ray anisotropy at the ‑3 % level has been measured by IceCube and the Pierre Auger Observatory, yet the physical origin of these patterns remains uncertain. Solar activity reshapes the heliospheric magnetic field, which is known to modulate the intensity of galactic cosmic rays on shorter (27‑day) timescales. Demonstrating a solar‑cycle‑linked modulation of anisotropy would bridge two disparate research areas—high‑energy cosmic‑ray propagation and heliospheric physics—and could constrain models of particle transport in the Galaxy.

## Related work  

- [Time Variation in the TeV Cosmic Ray Anisotropy with IceCube and Energy Dependence of the Solar Dipole (2025)](http://arxiv.org/abs/2507.08242v1) — Reports sub‑‰ anisotropy measurements in IceCube data and mentions a possible solar‑dipole component that varies with time.  
- [On the relationship of the 27‑day variations of the solar wind velocity and galactic cosmic ray intensity in minimum epoch of solar activity (2015)](http://arxiv.org/abs/1504.00778v1) — Shows a clear 27‑day modulation of GCR intensity linked to solar‑wind speed during solar minimum.  
- [On the 27‑day Variations of Cosmic Ray Intensity in Recent Solar Minimum 23/24 (2015)](http://arxiv.org/abs/1504.00180v1) — Extends the 27‑day analysis to the most recent minimum, confirming the solar‑wind–GCR connection.  
- [The Solar Cycle (2015)](http://arxiv.org/abs/1502.07020v1) — Provides a comprehensive review of the 11‑year solar‑activity cycle and its observable proxies (sunspot number, solar‑wind parameters).  
- [Three dimensional solar anisotropy of galactic cosmic rays near the recent solar minimum 23/24 (2015)](http://arxiv.org/abs/1509.05718v1) – Presents 3‑D GCR anisotropy vectors derived from neutron‑monitor data for 2006‑2012.  
- [27‑day Variation of the Three Dimensional Solar Anisotropy of Galactic Cosmic Ray: 1965‑2014 (2015)](http://arxiv.org/abs/1509.05770v1) – Long‑term study of the 27‑day anisotropy variation over five solar cycles.  
- [Solar Modulation of Cosmic Rays during the Declining and Minimum Phases of Solar Cycle 23: Comparison with Past Three Solar Cycles (2013)](http://arxiv.org/abs/1311.7387v1) – Analyzes how GCR intensity changes across different phases of multiple solar cycles.

## Expected results  

We anticipate detecting a statistically significant (~3 σ) periodic modulation of the large‑scale anisotropy amplitude that tracks the solar‑cycle phase (e.g., higher dipole strength near solar minimum). Confirmation will come from cross‑correlating anisotropy time series with sunspot number and solar‑wind speed proxies, while a lack of correlation (or a phase‑lag inconsistent with heliospheric models) would falsify the hypothesis.

## Methodology sketch  

1. **Data acquisition**  
   - Download IceCube public 10 yr muon‑track dataset (available via the IceCube Open Data portal, e.g., `wget https://icecube-data.org/.../muon_tracks_2010_2020.hdf5`).  
   - Retrieve Pierre Auger public surface‑detector event files for the same period (from the Auger Open Data portal).  
   - Obtain solar‑activity indices (daily sunspot number, solar‑wind speed, IMF magnitude) from NOAA’s NGDC FTP site (`ftp://ftp.ngdc.noaa.gov/...`).  

2. **Pre‑processing**  
   - Convert event times to UTC Julian dates and bin into 27‑day (Carrington) intervals.  
   - For each interval, compute the relative intensity sky map (HEALPix Nside 64) and extract the dipole and quadrupole components using spherical‑harmonic fitting.  

3. **Time‑series construction**  
   - Build a vector of dipole amplitude and phase per interval for each detector.  
   - Align the solar‑activity series to the same timestamps, applying a 27‑day running average to reduce high‑frequency noise.  

4. **Statistical analysis**  
   - Apply Lomb‑Scargle periodograms to the anisotropy amplitude series to identify power at the 11‑year solar frequency.  
   - Compute Pearson and Spearman cross‑correlations between anisotropy amplitude and each solar proxy, testing significance with a block‑bootstrap (block length = 27 days).  
   - Perform a Monte‑Carlo shuffle test (10 000 permutations) to estimate the false‑alarm probability of any observed correlation.  

5. **Robustness checks**  
   - Repeat the analysis using only IceCube data, only Auger data, and the combined dataset to verify consistency.  
   - Test alternative bin sizes (14 day, 54 day) to assess sensitivity to the chosen temporal resolution.  

6. **Visualization & reporting**  
   - Produce time‑series plots of dipole amplitude vs. sunspot number, heat‑maps of correlation strength over the solar cycle, and periodograms highlighting the 11‑year peak.  
   - Export all scripts (Python 3.11, `numpy`, `healpy`, `astropy`, `pandas`, `scipy`) and a reproducible `requirements.txt` for execution on a GitHub Actions runner.  

All steps are designed to run within the 6‑hour free‑tier limit on a standard GHA runner (data download ≤ 1 GB, memory ≤ 4 GB, CPU ≤ 2 cores).

## Duplicate-check  

- Reviewed existing ideas: *(none provided for comparison)*.  
- Closest match: N/A.  
- Verdict: **NOT a duplicate**.
