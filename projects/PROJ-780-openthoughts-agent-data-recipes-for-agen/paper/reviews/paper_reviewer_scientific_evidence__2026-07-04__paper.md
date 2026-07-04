---
action_items:
- id: '815584472701'
  severity: writing
  text: "The paper presents an extensive ablation study on data curation for agentic\
    \ models, but several central claims rely on experimental designs that do not\
    \ fully rule out confounding variables or sampling noise. First, the stability\
    \ of the reported gains is unclear. Tables 1, 2, and 3 report standard errors\
    \ (e.g., \xB11.63) but do not state the number of random seeds (n) used to generate\
    \ these statistics. In agentic benchmarks, run-to-run variance can be high; a\
    \ 1.3 percentage point difference (e.g., T"
artifact_hash: 1762f575d6ad502232c74311f4c0e12a6d2ed21a38bf5e7d1493821d45367039
artifact_path: projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T02:25:24.178362Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents an extensive ablation study on data curation for agentic models, but several central claims rely on experimental designs that do not fully rule out confounding variables or sampling noise.

First, the stability of the reported gains is unclear. Tables 1, 2, and 3 report standard errors (e.g., ±1.63) but do not state the number of random seeds (n) used to generate these statistics. In agentic benchmarks, run-to-run variance can be high; a 1.3 percentage point difference (e.g., Top 4 vs. Top 2 mixing in Table 1) is well within the margin of error for a single seed. Without disclosing the seed count (e.g., n=3 or n=5), the reader cannot distinguish a robust effect from lucky initialization.

Second, the "compute-controlled" claims in the filtering and scaling sections are not fully supported by the presented tables. Section 3.6 asserts that filtering for longer traces improves performance "at a matched token budget," yet the provided tables (Table 2, Appendix A.3) do not explicitly display the control run where token budget is held fixed while turn count varies. Similarly, the scaling analysis in Section 4 attributes gains to data volume and augmentation, but Table S4 reveals that the hyperparameters (epochs and gradient clipping) change simultaneously with data scale (e.g., 7 epochs for 10K data vs. 5 epochs for 100K data). This confounds the effect of data diversity with the effect of training duration and optimization dynamics.

Finally, the RL conclusion that "undertrained" models benefit more is based on a comparison between a 10K SFT model and a 100K SFT model. However, as noted above, these models also differ in training epochs (7 vs. 5). The observed benefit could be an artifact of the 10K model receiving more training steps rather than a specific property of being "undertrained" in terms of data volume.

To close these gaps, the authors should: (1) explicitly state the number of seeds for all ablation runs; (2) provide the specific compute-controlled ablation tables for the filtering and scaling experiments where hyperparameters are held constant; and (3) run a control experiment for the RL comparison where the SFT models at different scales are trained for the same number of epochs.
