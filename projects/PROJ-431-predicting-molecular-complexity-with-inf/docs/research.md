# Research: Predicting Molecular Complexity with Information Theory

## Introduction

This project investigates whether information-theoretic measures of molecular graph structure can predict physicochemical properties relevant to drug discovery, specifically aqueous solubility (logS) and membrane permeability (logP).

## Candidate Information-Theoretic Measures

To address the need for formal framing and to justify our metric selection, we explicitly enumerate and compare three primary classes of information-theoretic measures applicable to molecular graphs: Shannon Entropy (degree distribution), Mutual Information, and Algorithmic Complexity (Kolmogorov).

### 1. Shannon Entropy of Degree Distributions (Selected Metric)

**Definition**:
Shannon entropy, $H(X) = -\sum p(x) \log p(x)$, measures the uncertainty or information content of a random variable $X$. In our context, we define $X$ as the degree (number of bonds) of atoms within a molecular graph.

**Operationalization**:
- **Atom Entropy**: The distribution of atom degrees (0 for isolated, 1 for terminal, 2 for chain, 3 for branching, 4 for quaternary carbon, etc.) is computed for the molecule. The entropy of this distribution quantifies the structural heterogeneity of the atomic connectivity.
- **Bond Entropy**: Similarly, the distribution of bond orders (single, double, triple) or bond degrees (number of connections to the bond's endpoints) is analyzed.

**Justification for Selection**:
- **Computational Tractability**: Calculating degree distributions is $O(N)$ where $N$ is the number of atoms, making it feasible for high-throughput screening of millions of molecules.
- **Topological Relevance**: Molecular complexity in drug discovery is often correlated with structural branching and heterogeneity, which are directly captured by degree distributions.
- **Interpretability**: The metric directly maps to chemical intuition: highly branched, heterogeneous molecules (high entropy) often exhibit different solvation and permeation behaviors than linear, homogeneous ones.
- **Empirical Performance**: Our experimental results (see `results/reports/metrics.json`) demonstrate that entropy-based features achieve competitive or superior predictive performance for logS and logP compared to baseline size-dependent metrics.

### 2. Mutual Information (MI)

**Definition**:
Mutual Information, $I(X; Y) = \sum \sum p(x,y) \log \frac{p(x,y)}{p(x)p(y)}$, measures the reduction in uncertainty about one random variable given knowledge of another.

**Operationalization**:
In molecular graphs, MI could measure the dependency between the local environment of an atom and its contribution to global properties, or the correlation between subgraph occurrences.

**Why Not Selected**:
- **Data Sparsity**: Estimating joint probability distributions $p(x,y)$ for complex molecular substructures requires massive datasets to avoid high variance in estimation.
- **Computational Cost**: Calculating MI for all pairs of structural features scales poorly ($O(N^2)$ or worse) and often requires discretization or binning strategies that introduce arbitrary hyperparameters.
- **Interpretability Gap**: While MI captures non-linear dependencies, the resulting "information" is less directly interpretable as a "complexity score" for a single molecule compared to the marginal entropy of its structural distribution.

### 3. Algorithmic Complexity (Kolmogorov Complexity)

**Definition**:
Kolmogorov complexity, $K(x)$, is the length of the shortest program that outputs string $x$. It represents the absolute amount of information in an object.

**Operationalization**:
Approximations (e.g., Lempel-Ziv complexity, compression ratios of SMILES strings) are often used as proxies.

**Why Not Selected**:
- **Uncomputability**: True Kolmogorov complexity is uncomputable; all practical measures are approximations sensitive to the choice of encoding (e.g., SMILES vs. InChI vs. graph canonicalization).
- **Lack of Chemical Semantics**: Compression ratios of SMILES strings primarily capture string-level redundancy rather than the topological complexity of the underlying graph. A chemically complex molecule might have a highly redundant SMILES representation, and vice versa.
- **Instability**: Small changes in molecular structure can lead to disproportionate changes in compression ratios, making it a noisy predictor for continuous physicochemical properties.

## Structural vs. Functional Information

Addressing the distinction raised in recent review (per reviewer john-von-neumann-simulated), we clarify the relationship between structural and functional information in this context:

- **Structural Information**: This refers to the topological properties of the molecular graph (connectivity, branching, ring systems). Our chosen metric (Shannon entropy of degree distributions) is a direct measure of this structural information. It quantifies the "pattern" of the graph without reference to external physical laws.

- **Functional Information**: This refers to the physicochemical outcome (logS, logP) which emerges from the interaction of the molecule's structure with the solvent environment.

**Bridging the Gap**:
The hypothesis of this research is that the *structural information* (complexity) captured by Shannon entropy is a strong predictor of *functional information* (solubility/permeability). This is not a tautology; it is an empirical claim that the topological heterogeneity of a molecule correlates with its thermodynamic behavior in solution.

Our results indicate that while molecular size (number of atoms) is a dominant factor, the *distribution* of connectivity (entropy) provides significant additional predictive power. This suggests that the "functional" property of solubility is not solely determined by mass but is sensitive to the "structural" arrangement of atoms, validating the use of topological entropy as a bridge between structure and function.

## Conclusion

Shannon entropy of degree distributions was selected as the primary metric due to its optimal balance of computational efficiency, chemical interpretability, and empirical predictive power. While Mutual Information offers deeper dependency analysis and Algorithmic Complexity offers a theoretical upper bound, their practical limitations in data requirements, stability, and semantic relevance make them less suitable for the specific goal of high-throughput prediction of logS and logP. The chosen metric successfully bridges the gap between structural graph properties and functional physicochemical outcomes.