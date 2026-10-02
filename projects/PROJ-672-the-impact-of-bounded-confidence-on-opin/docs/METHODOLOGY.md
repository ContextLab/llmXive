# Methodology: The Impact of Bounded Confidence on Opinion Polarization Speed

## 1. Overview

This project investigates how the bounded confidence threshold ($\epsilon$) in the Hegselmann-Krause (HK) model influences the speed of opinion polarization and cluster formation across different network topologies. Unlike previous studies focusing solely on final states, we explicitly measure **convergence time** ($T$) and analyze its scaling behavior near the critical threshold ($\epsilon_c$).

## 2. Theoretical Framework

### 2.1 The Hegselmann-Krause Model
We implement the discrete-time HK rule where agents update their opinions based on a weighted average of neighbors within a confidence bound $\epsilon$:
$$ x_i(t+1) = \frac{1}{|N_i(t)|} \sum_{j \in N_i(t)} x_j(t) $$
where $N_i(t) = \{j: |x_i(t) - x_j(t)| \le \epsilon\}$.

### 2.2 Critical Threshold Hypothesis
We hypothesize a phase transition at a critical $\epsilon_c$ where convergence time diverges according to a power law:
$$ T \sim A(\epsilon - \epsilon_c)^{-\gamma} $$
This mirrors critical phenomena in statistical physics, where $\gamma$ characterizes the universality class of the polarization dynamics.

## 3. Experimental Design

### 3.1 Network Ensembles
To isolate topological effects, we generate ensembles of $N=500$ agents using three distinct random graph models:
1. **Erdős-Rényi (ER)**: Homogeneous degree distribution, serving as a baseline.
2. **Barabási-Albert (BA)**: Scale-free networks with power-law degree distributions, modeling preferential attachment.
3. **Watts-Strogatz (WS)**: Small-world networks with high clustering and short path lengths.

Each topology is instantiated 50 times with fixed random seeds to ensure reproducibility and statistical robustness. [UNRESOLVED-CLAIM: c_8dcd4fb3 — status=not_enough_info]

### 3.2 Simulation Protocol
- **Initial Conditions**: Opinions $x_i(0)$ are drawn uniformly from $[0, 1]$.
- **Parameter Sweep**: $\epsilon$ is swept from $0.01$ to $0.50$ with step size $0.01$.
- **Convergence Criterion**: The simulation terminates when $\max_i |x_i(t+1) - x_i(t)| < 10^{-4}$ or a maximum of $10,000$ iterations is reached.
- **Non-convergence Handling**: Runs exceeding the iteration limit are flagged as "non-convergent" and excluded from scaling analysis.

### 3.3 Structural Metrics
For each network instance, we compute:
- **Assortativity**: Correlation of degrees between connected nodes.
- **Average Path Length**: Mean shortest path distance.
- **Clustering Coefficient**: Local density of triangles.

These metrics are used to regress against the extracted scaling exponent $\gamma$ to determine if topology-specific features drive polarization speed.

## 4. Data Processing & Analysis

### 4.1 Critical Threshold Detection
We employ a grid-search algorithm to identify $\epsilon_c$ for each network instance. Candidates are tested in the range $[0.01, 0.50]$. The optimal $\epsilon_c$ is the value that minimizes the Residual Sum of Squares (RSS) for the power-law fit in the critical regime $\epsilon \in [\epsilon_c + 0.05, 0.50]$.

### 4.2 Scaling Exponent Extraction
Using the identified $\epsilon_c$, we fit the power-law model $T = A(\epsilon - \epsilon_c)^{-\gamma}$ using non-linear least squares. The quality of fit is assessed via $R^2$, with a threshold of $0.8$ required for inclusion.

### 4.3 Regression Models
Two regression models are employed to correlate $\gamma$ with structural properties:
1. **Model A**: $\gamma \sim \text{Topology}$ (categorical). Tests if the graph class alone explains variance.
2. **Model B**: $\gamma \sim \text{Assortativity} + \text{PathLength}$ (continuous). Tests if specific topological features drive the scaling behavior within a topology.

## 5. Sensitivity Analysis
To ensure robustness, we re-run simulations for a subset of configurations using convergence thresholds $\delta \in [10^{-3}, 10^{-5}]$. We verify that the variation in $\gamma$ across these thresholds remains below $5\%$, confirming that our results are not artifacts of the specific stopping criterion.

## 6. Addressing Reviewer Concerns

### 6.1 Rule Space Exploration (Stephen Wolfram)
While this study focuses on the static HK rule, we acknowledge that complexity often emerges from simple rule variations. Future work will explore "Rule Space" variants, such as weighted averaging or median-based updates, to map the phase transition landscape across different micro-rules.

### 6.2 Adaptive Thresholds (Alan Turing)
The current model assumes a static cognitive limitation. We discuss the theoretical implications of adaptive $\epsilon$ (where agents adjust their confidence based on local disagreement) as a future extension, contrasting it with the static baseline implemented here.

### 6.3 Biological Imperative (David Krakauer)
We reframe bounded confidence as a signal detection heuristic evolved to filter noise. The observed polarization may be a shadow of an ancestral mechanism for distinguishing signal from noise, rather than a purely statistical optimization process.

### 6.4 Scaling of $\epsilon$ with Density (Geoffrey West)
We investigate the hypothesis that $\epsilon$ scales with network density, potentially leading to critical transitions at specific network sizes. Our analysis of $\gamma$ across different topologies provides preliminary evidence for topological constraints on scaling behavior.

## 7. Reproducibility
All simulations use deterministic seed distribution strategies (`worker_seed = base_seed + worker_id`) to ensure floating-point reproducibility. Raw data, checksums, and analysis scripts are versioned and stored in the `data/` and `code/` directories.
