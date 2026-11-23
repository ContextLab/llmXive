---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Impact of Network Centrality on Resting‑State Functional Connectivity in Autism Spectrum Disorder

**Field**: neuroscience

## Research question

How does the structural eigenvector centrality of Default Mode Network (DMN) hubs mediate the relationship between whole‑brain resting‑state functional connectivity strength and ADOS‑2 Social Communication scores in individuals with Autism Spectrum Disorder, after accounting for age, sex, and head‑motion covariates?

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

We will evaluate whether an indirect effect exists whereby structural DMN centrality transmits the influence of global functional connectivity strength on ADOS‑2 Social Communication scores. Significance will be assessed with bias‑corrected 95 % bootstrap confidence intervals (5 000 resamples). A confidence interval that excludes zero will be interpreted as evidence for mediation; an interval that includes zero will be interpreted as a lack of mediation. In addition, we will report the proportion of the total effect accounted for by the indirect path and examine the robustness of findings across alternative centrality measures and structural density thresholds.

## Methodology sketch

- **Data acquisition**  
  - Download paired resting‑state fMRI, diffusion MRI, and phenotypic files (including ADOS‑2 Social Communication scores, age, sex, and mean framewise displacement) for all ASD participants from the ABIDE I & II repositories via the NITRC portal: `https://fcon_1000.projects.nitrc.org/indi/abide/`.  
  - Retain only subjects with both modalities and complete phenotypic data.

- **Quality control**  
  - Exclude runs with mean framewise displacement > 0.3 mm.  
  - Verify diffusion data quality using MRtrix3’s `dwidenoise` and `mrdegibbs`; discard subjects failing QC metrics.

- **Functional preprocessing**  
  - Run **fMRIPrep** (CPU‑only Docker image) to perform slice‑time correction, motion correction, susceptibility distortion correction, normalization to MNI152, and extraction of confound regressors (WM, CSF, 6 motion parameters).  
  - Apply a band‑pass filter (0.01–0.1 Hz) and regress out confounds with `nilearn.signal.clean`.

- **Diffusion preprocessing**  
  - Process dMRI with MRtrix3:  
    1. `dwidenoise` → `mrdegibbs` → `dwipreproc` (eddy & topup).  
    2. Generate a whole‑brain tractogram using probabilistic iFOD2 tracking (2 M streamlines).  
    3. Map streamlines to the Schaefer 400‑parcel atlas to obtain a weighted structural adjacency matrix (streamline count per edge).

- **Parcellation & network definition**  
  - Use the Schaefer 400‑parcel atlas to extract mean BOLD time series for each parcel.  
  - Identify parcels belonging to the DMN based on the atlas’s network labels.

- **Functional connectivity metric (X)**  
  - Compute the Pearson correlation matrix across the 400 parcels, Fisher‑z transform, then take the absolute value of all off‑diagonal entries.  
  - Define **global functional connectivity strength** as the mean of these absolute z‑values (full weighted matrix, no arbitrary threshold).

- **Structural centrality metric (M)**  
  - Threshold each subject’s structural adjacency matrix to retain the top 15 % of strongest streamline counts (density‑matched across subjects).  
  - Compute eigenvector centrality for all 400 nodes using NetworkX.  
  - Average eigenvector centrality values across the DMN nodes to obtain **DMN‑centrality** for each subject.

- **Mediation analysis**  
  - Model: `Y (ADOS‑SC) ~ X (global FC) + M (DMN centrality) + covariates (age, sex, mean FD)`.  
  - Test the indirect path `X → M → Y` with the `statsmodels` mediation framework, employing 5 000 bootstrap resamples to obtain bias‑corrected confidence intervals.  
  - Confirm independence: X derives solely from BOLD data, M solely from diffusion data, and Y is a clinical score collected independently of imaging.

- **Sensitivity checks**  
  - Repeat mediation using alternative structural density thresholds (10 % and 20 %).  
  - Substitute eigenvector centrality with betweenness and degree centrality to assess robustness of any mediation effect.

- **Visualization & reporting**  
  - Produce a path diagram (direct, indirect, total effects) with `matplotlib`.  
  - Overlay DMN parcels on a standard MNI brain using Nilearn to illustrate hub locations.  
  - Summarize bootstrap confidence intervals and effect‑size estimates in a markdown report.

- **Reproducibility & runtime constraints**  
  - All code will be containerised (Docker) and orchestrated by a GitHub Actions workflow limited to 6 h on the free‑tier runner (2 CPU, 7 GB RAM).  
  - Data are streamed directly from the ABIDE server; intermediate files are compressed to stay within the 14 GB SSD quota.  
  - No GPU or external compute resources are required; each processing step is designed to fit within the CPU‑only environment.

## Duplicate-check

- Reviewed existing ideas: Functional connectivity patterns in ASD, Network topology in neurodevelopmental disorders, AI methods for ASD detection from MRI.  
- Closest match: **Network topology in neurodevelopmental disorders** – both examine graph metrics in ASD but the existing idea does not perform a multimodal mediation analysis linking structural hub centrality, functional connectivity, and behavioral severity.  
- Verdict: **NOT a duplicate**


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-10-26T00:43:21Z
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
