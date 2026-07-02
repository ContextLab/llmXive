---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Data Journalist Agent: Transforming Data into Verifiable Multimodal St"

## Summary of the prior work
The paper introduces Data2Story, a multi-agent framework that automates the end-to-end creation of evidence-grounded, multimodal news articles by orchestrating specialized roles for analysis, design, and verification. Its core innovations include an "Inspector" module that traces every claim back to raw data or code to ensure verifiability, and a generative engine that selects appropriate modalities like interactive maps or audio based on content. Evaluation against human-written features shows the system excels in transparency and auditability but currently lags in editorial creativity and narrative angle.

## Proposed extension
How does the introduction of a "Counterfactual Inspector" agent, which explicitly generates and tests alternative narrative angles against the same dataset, improve the depth of causal reasoning and reduce confirmation bias in automatically generated stories? This direction matters because current agents, while factually accurate, tend to default to the most statistically obvious or pre-trained narrative patterns, potentially missing nuanced or contradictory insights that a human editor would explore to ensure a balanced report.

## Methodology sketch
We will construct a dataset of 50 complex, multi-variable public policy datasets (e.g., housing, crime, health) where the ground-truth "human story" is known to contain a non-obvious counter-intuitive finding. The procedure involves running the original Data2Story pipeline to generate a baseline story, then deploying a new "Counterfactual Inspector" agent that systematically queries the data for correlations that contradict the baseline angle and forces the narrative engine to integrate at least one such alternative perspective. We will evaluate the output using a blinded rubric assessing "Narrative Depth" and "Bias Mitigation" by 20 domain experts, hypothesizing that stories with the Counterfactual Inspector will score significantly higher on detecting non-obvious insights while maintaining the original system's verifiability scores.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Data Journalist Agent: Transforming Data into Verifiable Multimodal Stories** — Kevin Qinghong Lin, Batu EI, Yuhong Shi, Pan Lu, Philip Torr, James Zou. https://arxiv.org/abs/2606.11176.

```bibtex
@article{orig_arxiv_2606_11176,
  title = {Data Journalist Agent: Transforming Data into Verifiable Multimodal Stories},
  author = {Kevin Qinghong Lin and Batu EI and Yuhong Shi and Pan Lu and Philip Torr and James Zou},
  year = {2026},
  eprint = {2606.11176},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.11176},
  url = {https://arxiv.org/abs/2606.11176}
}
```
