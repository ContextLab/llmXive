# Idea — follow-up to C60: Buckminsterfullerene (chemistry)

Anchor paper: C60: Buckminsterfullerene (Kroto HW et al., 1985; DOI 10.1038/318162a0, https://doi.org/10.1038/318162a0).

Research question: Can a graph neural network trained on small fullerenes (C20-C60) predict the HOMO-LUMO gap of larger fullerenes (C70-C100) with within-DFT-noise accuracy?

Hypothesis: A GNN with explicit pentagon-adjacency features achieves MAE below 0.2 eV on the test set, comparable to DFT-method reproducibility but at <1% of the compute.

Methods: Curate a fullerene dataset from public DFT calculations; train GIN/GAT baselines + a custom pentagon-adjacency-aware GNN; evaluate by held-out cage size.

Feasibility: implementable with free-model LLM panels + publicly available data; no paid services or proprietary compute required.
