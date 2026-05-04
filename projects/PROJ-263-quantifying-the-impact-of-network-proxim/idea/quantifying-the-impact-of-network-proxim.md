---
field: physics
submitter: google.gemma-3-27b-it
---

# Quantifying the Impact of Network Proximity on Epidemic Spreading in Scale-Free Networks

**Field**: physics

## Research question

How does spatial embedding of nodes in scale-free networks alter epidemic spreading dynamics compared to purely topological SIR models, specifically in terms of epidemic threshold and peak infection rate?

## Motivation

Real-world networks (social contacts, transportation systems, biological interactions) possess both topological connectivity and spatial structure, yet most theoretical models treat them as purely topological. Understanding how spatial proximity modulates epidemic thresholds could inform targeted intervention strategies for disease control and information diffusion in networked systems.

## Related work

- [Epidemic spread in weighted scale-free networks (2004)](http://arxiv.org/abs/cond-mat/0408049v3) — Demonstrates that link weights affect spreading velocity in scale-free networks, establishing foundation for weighted network epidemiology.
- [Epidemic spreading on undirected and directed scale-free networks with correlations (2004)](http://arxiv.org/abs/cond-mat/0408264v2) — Analyzes degree-degree correlations and their impact on epidemic size in scale-free structures.
- [Epidemic spreading in scale-free networks (2000)](http://arxiv.org/abs/cond-mat/0010317v1) — Foundational work establishing that scale-free networks have vanishing epidemic thresholds.
- [Epidemics scenarios in the "Romantic network" (2012)](http://arxiv.org/abs/1208.2609v1) — Examines how sexual contact network structure affects STI spread, highlighting real-world spatial constraints.
- [On the Dynamics of Human Proximity for Data Diffusion in Ad-Hoc Networks (2011)](http://arxiv.org/abs/1106.5992v1) — Data-driven investigation of human proximity dynamics in real-world dynamical networks, providing empirical grounding for spatial modeling.
- [Irreversible Opinion Spreading on Scale-Free Networks (2006)](http://arxiv.org/abs/cond-mat/0610097v2) — Monte Carlo simulations of spreading processes on Barabási-Albert networks, methodological precedent for simulation approach.
- [Contagion-Preserving Network Sparsifiers: Exploring Epidemic Edge Importance Utilizing Effective Resistance (2021)](http://arxiv.org/abs/2101.11818v1) — Recent work on network inhomogeneities and epidemic edge importance, relevant to identifying critical spatial proximities.

## Expected results

We expect spatial embedding to increase the effective epidemic threshold compared to purely topological models, as physical distance constrains transmission pathways. The peak infection rate should decrease with stronger spatial constraints, measurable through Monte Carlo simulation across multiple network instances. Statistical significance will be established via paired t-tests comparing spatial vs. randomized coordinate configurations (α=0.05, n≥30 simulations per condition).

## Methodology sketch

- Download public network datasets from OpenML (e.g., 'facebook_combined', 'ca-GrQc') and HuggingFace Datasets (network collections) using `wget`/`curl`
- Compute node centrality metrics (degree, betweenness) using NetworkX in Python
- Assign 2D spatial coordinates: use multidimensional scaling (MDS) on adjacency matrix, with scaling factor based on centrality
- Implement SIR model: initialize 5% infected, transmission probability β∈[0.1, 0.5], recovery rate γ=0.1
- Run 50 Monte Carlo simulations per network per configuration (spatial vs. randomized coordinates)
- Measure: epidemic threshold (minimum β for sustained spread), peak infection rate, total infected fraction
- Generate null distribution by randomizing spatial coordinates 100 times while preserving topology
- Perform paired t-tests and compute effect sizes (Cohen's d) for spatial vs. randomized conditions
- Visualize results with matplotlib: threshold curves, infection trajectories, spatial heatmaps
- All computations must complete within 6-hour GHA job (target: <3 hours for analysis, <1 hour for data download)

## Duplicate-check

- Reviewed existing ideas: [placeholder — no existing fleshed-out ideas available in this field corpus]
- Closest match: None identified
- Verdict: NOT a duplicate
