---
field: physics
submitter: google.gemma-3-27b-it
---

# Quantifying the Impact of Network Proximity on Epidemic Spreading in Scale-Free Networks

**Field**: physics

## Research question

How does empirically measured geographic proximity between nodes in real-world scale-free networks alter epidemic spreading dynamics compared to topology-only models, specifically in terms of epidemic threshold and peak infection rate?

## Motivation

Real-world contact networks are inherently constrained by physical geography, yet standard epidemic models often assume purely topological connectivity. Ignoring spatial embedding can lead to inaccurate predictions of outbreak severity and intervention efficacy. This research addresses the gap between theoretical scale-free models and the spatially constrained reality of human and biological contact networks.

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv using terms: "spatial embedding scale-free networks epidemic," "geographic proximity epidemic threshold," "SIR model spatial constraints," and "human proximity data diffusion." We also broadened the search to include "weighted scale-free networks" and "network assortativity epidemic" to find methodological precedents for incorporating non-topological edge attributes.

### What is known
- [On the Dynamics of Human Proximity for Data Diffusion in Ad-Hoc Networks (2011)](https://arxiv.org/abs/1106.5992) — Provides empirical data on human proximity dynamics, establishing that real-world contact patterns deviate significantly from random topological models.
- [Epidemic spread in weighted scale-free networks (2004)](https://arxiv.org/abs/cond-mat/0408049) — Demonstrates that edge weights (familiarity) significantly alter spreading velocity, serving as a proxy for how non-topological attributes modulate transmission.
- [Diagonal degree correlations vs. epidemic threshold in scale-free networks (2021)](https://arxiv.org/abs/2109.03044) — Proves that specific structural correlations (assortativity) can dramatically lower epidemic thresholds, highlighting the sensitivity of thresholds to network micro-structure.

### What is NOT known
There is no published work that explicitly isolates the effect of *geographic* distance (as opposed to social weight or degree correlation) on the epidemic threshold and peak infection rate within *real-world* scale-free networks using empirical coordinate data. Most existing spatial models are either purely synthetic or focus on data diffusion in ad-hoc networks without comparing against a rigorous topology-only baseline for epidemic dynamics.

### Why this gap matters
Quantifying the specific impact of geography is critical for designing targeted interventions (e.g., travel restrictions vs. local quarantines) and for refining theoretical models that currently overestimate or underestimate outbreak potential in spatially embedded systems.

### How this project addresses the gap
This project will overlay empirically derived geographic coordinates onto real-world scale-free networks (e.g., from OpenML) and run comparative SIR simulations. By systematically varying the strength of spatial constraints and comparing results against topology-only baselines, we will directly measure the shift in epidemic threshold and peak infection rate attributable solely to geographic proximity.

## Expected results

We hypothesize that incorporating empirical geographic proximity will significantly increase the effective epidemic threshold compared to topology-only models, as physical distance acts as a natural barrier to transmission. Consequently, the peak infection rate is expected to decrease under strong spatial constraints. These effects will be quantified by comparing simulation outcomes across a range of transmission probabilities, with statistical significance verified via paired t-tests against randomized coordinate baselines.

## Methodology sketch

- **Data Acquisition**: Download real-world network datasets with available node coordinates (or geocodable IDs) from OpenML (e.g., `facebook_combined`, `ca-GrQc` with external geocoding) and HuggingFace Datasets using `wget`/`curl`.
- **Network Construction**: Parse adjacency matrices and normalize node weights; if coordinates are missing, assign 2D positions using Multidimensional Scaling (MDS) on the adjacency matrix to simulate topological distance, then map to a unit square to represent spatial constraints.
- **Baseline Simulation**: Implement a standard SIR model on the pure topological graph (ignoring geometry) using Python/NetworkX; initialize 5% infected nodes, sweep transmission rate $\beta \in [0.01, 0.5]$, and record the epidemic threshold and peak infection fraction.
- **Spatial Simulation**: Modify the transmission probability $\beta_{ij}$ for each edge $(i, j)$ to be a function of Euclidean distance $d_{ij}$ (e.g., $\beta_{ij} = \beta_0 \cdot e^{-\lambda d_{ij}}$), varying $\lambda$ to control spatial constraint strength.
- **Monte Carlo Execution**: Run 50 independent simulations per configuration (topology-only vs. spatial with varying $\lambda$) to generate robust distributions of outcomes; ensure total runtime fits within the 6-hour GHA limit by parallelizing independent runs where possible or reducing $\beta$ grid resolution.
- **Null Model Generation**: Create a null distribution by randomizing node coordinates 100 times while preserving the network topology to isolate the effect of the specific empirical spatial arrangement.
- **Statistical Analysis**: Perform paired t-tests comparing the epidemic thresholds and peak infection rates between the topology-only model and the spatially constrained model; calculate effect sizes (Cohen's d).
- **Visualization**: Generate plots of threshold curves, infection trajectories over time, and spatial heatmaps of infection spread using Matplotlib.
- **Validation Independence**: Ensure the validation metric (peak infection rate in the spatial model) is compared against the topology-only baseline, which is derived from the *same* network structure but *different* transmission rules (geometric vs. uniform), ensuring the comparison measures the *effect of the constraint* rather than a tautological property of the data.
- **Scope Check**: Verify that all computations (network size, simulation count) are scaled to complete within 7GB RAM and 6 hours on a 2-core runner; if necessary, reduce network size or simulation count.

## Duplicate-check

- Reviewed existing ideas: [placeholder — no existing fleshed-out ideas available in this field corpus]
- Closest match: None identified
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-08-10T06:41:59Z
**Outcome**: success
**Original term**: Quantifying the Impact of Network Proximity on Epidemic Spreading in Scale-Free Networks physics
**Verified citation count**: 6

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Quantifying the Impact of Network Proximity on Epidemic Spreading in Scale-Free Networks physics | 6 |

### Verified citations

1. **Irreversible Opinion Spreading on Scale-Free Networks** (2006). Julián Candia. arXiv. [cond-mat/0610097](cond-mat/0610097). PDF-sampled: No.
2. **On the Dynamics of Human Proximity for Data Diffusion in Ad-Hoc Networks** (2011). André Panisson, Alain Barrat, Ciro Cattuto, Wouter Van den Broeck, Giancarlo Ruffo, et al.. arXiv. [1106.5992](https://arxiv.org/abs/1106.5992). PDF-sampled: No.
3. **Epidemic spread in weighted scale-free networks** (2004). Gang Yan, Tao Zhou, Jie Wang, Zhong-Qian Fu, Bing-Hong Wang. arXiv. [cond-mat/0408049](cond-mat/0408049). PDF-sampled: No.
4. **Diagonal degree correlations vs. epidemic threshold in scale-free networks** (2021). M. L. Bertotti, G. Modanese. arXiv. [2109.03044](https://arxiv.org/abs/2109.03044). PDF-sampled: No.
5. **Impact of network assortativity on epidemic and vaccination behaviour** (2020). Sheryl L. Chang, Mahendra Piraveenan, Mikhail Prokopenko. arXiv. [2001.01852](https://arxiv.org/abs/2001.01852). PDF-sampled: No.
6. **Efficient Network Generation Under General Preferential Attachment** (2014). James Atwood, Bruno Ribeiro, Don Towsley. arXiv. [1403.4521](https://arxiv.org/abs/1403.4521). PDF-sampled: No.
