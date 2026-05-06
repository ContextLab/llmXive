---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Impact of Simulated Sensory Deprivation on Resting-State Brain Network Dynamics

**Field**: neuroscience

## Research question

How does the intrinsic organization of human brain functional networks change when sensory input is experimentally reduced, and does this reorganization manifest as altered modularity and global efficiency in resting-state fMRI?

## Motivation

Understanding how the brain reorganizes in the absence of external input could inform treatments for sensory processing disorders and provide insights into the brain's intrinsic activity patterns. This question addresses a gap in current literature: while predictive processing theories suggest sensory input shapes intrinsic dynamics, empirical evidence from deprivation paradigms remains limited in publicly available datasets.

## Literature gap analysis

### What we searched

Search queries included "sensory deprivation resting-state fMRI," "sensory deprivation functional connectivity," "blind/visual deprivation brain network," and "auditory deprivation functional connectivity." Sources queried were Semantic Scholar, arXiv, and OpenAlex. The literature block returned 6 papers on functional connectivity methodology, ROI selection, and theoretical frameworks, but no direct studies measuring deprivation effects on resting-state network metrics.

### What is known

- [Whatever next? Predictive brains, situated agents, and the future of cognitive science (2013)](https://doi.org/10.1017/s0140525x12000477) — Establishes the theoretical framework that brains are prediction machines that match incoming sensory inputs with internal models, suggesting deprivation should alter intrinsic dynamics.
- [Consistency of Regions of Interest as nodes of functional brain networks measured by fMRI (2017)](http://arxiv.org/abs/1704.07635v1) — Demonstrates that functional network properties depend on how nodes are defined, which is critical for comparing deprivation versus control conditions.
- [Questions and controversies in the study of time-varying functional connectivity in resting fMRI (2019)](https://doi.org/10.1162/netn_a_00116) — Highlights challenges in measuring dynamic connectivity that must be addressed when comparing network states across conditions.

### What is NOT known

No published work has directly measured how short-term sensory deprivation (hours to days) alters resting-state network modularity and global efficiency in publicly available fMRI datasets. Existing studies focus on chronic conditions (e.g., congenital blindness) rather than acute deprivation paradigms, and network metrics are rarely compared across input-reduced versus normal conditions.

### Why this gap matters

Filling this gap would enable evidence-based interventions for sensory processing disorders and constrain theoretical models of predictive processing. Clinically, understanding deprivation-induced network changes could inform sensory rehabilitation protocols. Theoretically, it would test whether the brain's intrinsic organization is plastic on short timescales.

### How this project addresses the gap

The methodology will analyze existing fMRI datasets with deprivation or input-reduction conditions, compute network metrics (modularity, global efficiency) before and after deprivation, and quantify changes using permutation tests. This produces previously unavailable evidence on short-term deprivation effects on intrinsic network dynamics.

## Expected results

We expect to observe increased modularity and decreased global efficiency in sensory networks following deprivation, with compensatory increases in default mode network connectivity. The measurement will confirm or falsify this using network metric differences (effect size Cohen's d > 0.5) with statistical significance (p < 0.05, corrected for multiple comparisons). Evidence level will be moderate (n ≥ 20 subjects with pre/post scans).

## Methodology sketch

- Download resting-state fMRI data from OpenNeuro or HCP datasets containing pre/post deprivation scans (e.g., DS1017, DS1153) using `wget`/`curl`.
- Preprocess fMRI using FSL or AFNI (motion correction, normalization, bandpass filtering 0.01-0.1 Hz) on CPU-compatible pipelines.
- Define network nodes using 200-400 cortical ROIs from Schaefer or AAL atlas (download from GitHub).
- Compute functional connectivity matrices using Pearson correlation on BOLD time series for each ROI pair.
- Calculate network metrics: modularity (Louvain algorithm), global efficiency (networkx), and node strength.
- Compare metrics between pre-deprivation and post-deprivation conditions using paired t-tests with FDR correction.
- Perform permutation testing (1,000 iterations) to validate significance given sample size constraints.
- Generate visualization of network changes using matplotlib (degree plots, edge weight heatmaps).
- Document all code in reproducible Python scripts with requirements.txt for GHA execution.
- Store intermediate data in compressed formats (.npy, .csv) to stay within 14GB SSD limit.

## Duplicate-check

- Reviewed existing ideas: None in current corpus (first flesh-out in this field).
- Closest match: None identified.
- Verdict: NOT a duplicate
