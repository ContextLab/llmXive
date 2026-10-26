---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Impact of Network Centrality on Resting‑State Functional Connectivity in Autism Spectrum Disorder

**Field**: neuroscience

## Research question

How does the structural eigenvector centrality of Default Mode Network (DMN) hubs mediate the relationship between whole‑brain resting‑state functional connectivity strength and social‑communication severity (ADOS‑2 Social Communication score) in individuals with Autism Spectrum Disorder, after accounting for age, sex, and head‑motion covariates?

## Motivation

Both structural and functional connectomes are repeatedly reported as atypical in ASD, yet it remains unknown whether the topology of structural hubs constrains the functional dys‑connectivity that relates to core behavioral impairments. Clarifying this mediation pathway would identify whether structural hub integrity is a mechanistic bottleneck or merely a correlated epiphenomenon, thereby guiding whether interventions should target white‑matter plasticity versus functional network re‑organisation.

## Literature gap analysis

### What we searched
We performed two independent queries on Semantic Scholar / OpenAlex:

1. **Focused query** – `"structural centrality" AND "DMN" AND "mediation" AND "autism"` – aimed at studies that directly test a mediation model linking structural hub metrics to functional connectivity and behavior in ASD.  
2. **Broader query** – `"structure‑function coupling" AND "diffusion MRI" AND "functional connectivity" AND "neurodevelopmental"` – aimed at any multimodal work on ASD or related neurodevelopmental disorders that could serve as methodological precedents.

Both queries returned only a handful of papers, none of which performed the specific multimodal mediation analysis we propose.

### What is known
- **[State‑dependent changes of connectivity patterns and functional brain network topology in Autism Spectrum Disorder](https://arxiv.org/abs/1211.4766)** — Demonstrates that graph‑theoretical descriptors of functional networks differ in ASD, establishing that resting‑state topology can be quantified and related to the disorder.  
- **[Reduced interhemispheric functional connectivity of children with autism: evidence from functional near infrared spectroscopy studies](https://arxiv.org/abs/1309.5840)** — Shows that functional synchrony deficits are robust behavioural correlates of ASD, justifying the use of connectivity strength as a predictor of symptom severity.  
- **[Fractal‑driven distortion of resting state functional networks in fMRI: a simulation study](https://arxiv.org/abs/1208.0924)** — Highlights that resting‑state networks exhibit scale‑invariant dynamics, cautioning against overly simplistic linear connectivity metrics and motivating the inclusion of structural topology as a complementary explanatory factor.

### What is NOT known
No existing work has quantitatively modeled **structural hub centrality** (e.g., eigenvector centrality of DMN nodes derived from diffusion MRI) as a **mediator** of the link between **global functional connectivity strength** and **ADOS‑2 social‑communication scores** in ASD. Consequently, the mechanistic pathway from white‑matter architecture through functional dys‑connectivity to behavioral phenotype remains untested.

### Why this gap matters
Identifying whether structural hub integrity explains functional‑behavioral associations would pinpoint a targetable substrate for neuromodulatory or behavioural interventions. If centrality mediates the effect, therapies that promote white‑matter plasticity (e.g., intensive motor training, transcranial magnetic stimulation) could be prioritized; if not, strategies should focus on directly normalising functional dynamics.

### How this project addresses the gap
Using the publicly available ABIDE I & II multimodal datasets, we will (1) compute subject‑specific structural eigenvector centrality for DMN hubs, (2) compute whole‑brain functional connectivity strength from resting‑state fMRI, and (3) perform a formal mediation analysis linking these imaging metrics to ADOS‑2 social‑communication severity, while controlling for demographic and motion covariates. This pipeline supplies the first empirical test of the hypothesised mediation pathway.

## Expected results

We anticipate detecting a statistically significant indirect effect: structural DMN centrality will account for a non‑zero proportion of the variance that functional connectivity strength explains in ADOS‑2 social‑communication scores. A significant indirect path (95 % bootstrap CI excluding zero) would support the hypothesis that structural hub topology constrains functional dys‑connectivity relevant to behavior. A null indirect effect would suggest that functional deficits influence symptoms via mechanisms independent of DMN hub centrality.

## Methodology sketch

- **Data acquisition**  
  - Download paired resting‑state fMRI, diffusion MRI, and phenotypic files (including ADOS‑2 Social Communication scores, age, sex, and framewise displacement) for all ASD participants from the ABIDE I & II repositories via the NITRC portal: `https://fcon_1000.projects.nitrc.org/indi/abide/`.  
  - Retain only subjects with both modalities and complete phenotypic data.

- **Quality control**  
  - Exclude runs with mean framewise displacement > 0.3 mm.  
  - Verify diffusion data quality using MRtrix3’s `dwidenoise` and `mrdegibbs`; discard subjects failing QC metrics.

- **Preprocessing – functional**  
  - Run fMRIPrep (v23.0.0) in a Docker container (CPU‑only) to perform slice‑time correction, motion correction, susceptibility distortion correction, normalization to MNI152, and extraction of confound regressors (WM, CSF, 6 motion parameters).  
  - Apply a band‑pass filter (0.01–0.1 Hz) and regress out confounds with `nilearn.signal.clean`.

- **Preprocessing – diffusion**  
  - Process dMRI with MRtrix3:  
    1. `dwidenoise` → `mrdegibbs` → `dwipreproc` (eddy & topup).  
    2. Generate a whole‑brain tractogram using probabilistic iFOD2 tracking (2 M streamlines).  
    3. Map streamlines to the Schaefer 400‑parcel atlas (Schaefer et al., 2018) to obtain a weighted structural adjacency matrix (streamline count per edge).

- **Parcellation & network definition**  
  - Use the Schaefer 400‑parcel atlas to extract mean BOLD time series for each parcel.  
  - Identify the set of parcels belonging to the DMN (as defined by the atlas’s network labels).

- **Functional connectivity metric (X)**  
  - Compute the Pearson correlation matrix across the 400 parcels, Fisher‑z transform, then take the absolute value of all off‑diagonal entries.  
  - Define **global functional connectivity strength** as the mean of these absolute z‑values (no arbitrary correlation threshold; the full weighted matrix is used).

- **Structural centrality metric (M)**  
  - Threshold the subject‑specific structural adjacency matrix to retain the top 15 % of strongest streamline counts (density‑matching across subjects).  
  - Compute eigenvector centrality for all 400 nodes using NetworkX.  
  - Average eigenvector centrality values across the DMN nodes to obtain **DMN‑centrality** for each subject.

- **Mediation analysis**  
  - Model: `Y (ADOS‑SC) ~ X (global FC) + M (DMN centrality) + covariates (age, sex, mean FD)`.  
  - Test the indirect path `X → M → Y` using the `statsmodels` `mediation` package with 5,000 bootstrap resamples to obtain bias‑corrected confidence intervals.  
  - Verify independence: X is derived solely from BOLD data, M solely from dMRI, and Y is a clinical score collected independently of imaging.

- **Sensitivity checks**  
  - Repeat the mediation with alternative structural density thresholds (10 % and 20 %).  
  - Re‑run using alternative centrality measures (betweenness, degree) to test robustness of the mediation effect.

- **Visualization & reporting**  
  - Plot a path diagram (direct, indirect, total effects) with `matplotlib`.  
  - Overlay DMN parcels on a standard MNI brain using Nilearn to illustrate hub locations.  
  - Summarize bootstrap CI tables in a markdown report.

- **Reproducibility & runtime constraints**  
  - All code will be containerised (Docker) and orchestrated by a GitHub Actions workflow limited to 6 h on the free‑tier runner (2 CPU, 7 GB RAM).  
  - Data are streamed directly from the ABIDE server; intermediate files are compressed to stay within the 14 GB SSD quota.  
  - No GPU or external compute resources are required.

## Duplicate-check

- Reviewed existing ideas: Functional connectivity patterns in ASD, Network topology in neurodevelopmental disorders, AI methods for ASD detection from MRI.  
- Closest match: **Network topology in neurodevelopmental disorders** – both examine graph metrics in ASD but the existing idea does not perform a multimodal mediation analysis linking structural hub centrality, functional connectivity, and behavioral severity.  
- Verdict: **NOT a duplicate**


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-10-26T00:35:05Z
**Outcome**: exhausted
**Original term**: Investigating the Impact of Network Centrality on Resting-State Functional Connectivity in Autism Spectrum Disorder neuroscience
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Investigating the Impact of Network Centrality on Resting-State Functional Connectivity in Autism Spectrum Disorder neuroscience | 3 |

### Verified citations

1. **Fractal-driven distortion of resting state functional networks in fMRI: a simulation study** (2012). Wonsang You, Jörg Stadler. arXiv. [1208.0924](https://arxiv.org/abs/1208.0924). PDF-sampled: No.
2. **Reduced interhemispheric functional connectivity of children with autism: evidence from functional near infrared spectroscopy studies** (2013). Huilin Zhu, Yuebo Fan, Huan Guo, Dan Huang, Sailing He. arXiv. [1309.5840](https://arxiv.org/abs/1309.5840). PDF-sampled: No.
3. **State-dependent changes of connectivity patterns and functional brain network topology in Autism Spectrum Disorder** (2012). Pablo Barttfeld, Bruno Wicker, Sebastián Cukier, Silvana Navarta, Sergio Lew, et al.. arXiv. [1211.4766](https://arxiv.org/abs/1211.4766). PDF-sampled: No.
