## Research-question validation

### Phenomenon-vs-method check

**Verdict**: fail

The question is framed around whether a specific architecture (lightweight GNNs) works within specific resource constraints (2 CPU cores, 7GB RAM), rather than asking about the underlying phenomenon of what network traffic features or topological patterns indicate anomalous behavior. The answer ("yes, it fits in 6h" or "no, it doesn't") is a benchmark result, not a scientific finding about network security or traffic dynamics.

### Circularity check

**Verdict**: pass

The predictor (GNN-derived node/edge embeddings from flow graphs) and the predicted variable (anomaly labels from CTU-13 ground truth) come from independent sources. The anomaly labels are not derived from the same signal used to construct the GNN features.

### Triviality check

**Verdict**: concern

A positive result (GNN beats baseline within constraints) is expected given GNNs are designed for graph data; a null result (GNN doesn't beat baseline) could be due to constraints rather than fundamental limitations. Neither outcome is strongly informative about the nature of network anomalies themselves—both outcomes primarily answer a benchmark question rather than a domain question.

### Question-narrowing check

**Verdict**: fail

The question explicitly names implementation constraints (2 CPU cores, 7GB RAM, lightweight GNNs) rather than a domain relationship. This is "Can method M handle task T under budget B?" framing, which is an engineering feasibility question masquerading as a research question.

### Overall verdict

**Verdict**: validator_revise

[REVISED]
Which structural and temporal patterns in network traffic graphs (node degree distributions, edge weight dynamics, community structure) are most predictive of anomalous behavior, and how much can graph-structured models close the gap to state-of-the-art detection accuracy compared to feature-engineered baselines?
[/REVISED]
This reframing names a domain question (what traffic patterns predict anomalies) while preserving the GNN methodology as a tool rather than the question itself. Resource constraints can remain as implementation notes without becoming the research question.
