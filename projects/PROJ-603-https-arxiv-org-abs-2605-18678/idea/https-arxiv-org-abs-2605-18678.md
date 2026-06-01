---
field: other
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/207
---

# https://arxiv.org/abs/2605.18678

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2605.18678

Submitted by: github-actions[bot]

(Intake from human-submission issue #207.)

## Rejection rationale (2026-06-01)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[ffff116e5a65]** No code repository link is provided in the manuscript, preventing verification of implementation details and reproducibility.
- **[2d36272dc964]** Training hyperparameters and data mixture schedules are described in tables but lack associated configuration files or scripts.
- **[a640753a9eb6]** Dependency specifications (e.g., requirements.txt, Dockerfile) are missing, hindering environment reproducibility.
- **[a2805b944209]** Evaluation scripts and benchmarking code are not referenced, making performance claims difficult to validate independently.
- **[a05ef5755634]** Specify provenance for the 1B image-text and 140M video-text training samples (e.g., public dataset names or internal data governance).
- **[3f1c09cab53b]** Provide licensing information for all training corpora to clarify redistribution and commercial use rights.
- **[394e59885642]** Document exact benchmark versions (commit hashes or release tags) for GenEval, VBench, and MVBench to ensure reproducibility.
- **[c83af6145e00]** Convert figs/combined_radar_aligned.png to vector format (PDF/EPS) to ensure axis labels and legend text remain legible at print scale.
- **[fed9d809ba9c]** Verify fig:token_scaling_curve has explicit axis labels (e.g., 'Training Tokens (B)', 'DPG-Bench Score (%)') and units; captions describe points not visible in code.
- **[2b83259c9f5e]** Ensure color-dependent annotations (e.g., red highlights in fig:T2I-baseline) have grayscale-robust alternatives (patterns/labels) for B&W printing.
- **[a333aa397e53]** Define VAE (Variational Autoencoder) and ViT (Vision Transformer) at first use in Section 3.2.
- **[24c1c079fc6e]** Expand GRPO acronym in Section 5.4; currently undefined.
- **[96f5cfb0b0f3]** Define X2T, X2I, X2V acronyms explicitly in the text body, not just context.
- **[34acdc71ae1d]** Replace dense jargon like 'native unified paradigm' with plainer alternatives in Section 1.
- **[825b96b59d5d]** Resolve the contradiction between 'trained from scratch' (Abstract) and 'initialized from Qwen2.5-VL' (Sec 4.2).
- **[ace295bc77fb]** Reconcile the VBench Total Score discrepancy between Table tab:video_generation (85.60) and tab:vbench_full (85.11).
- **[ee65a991aac3]** Clarify the GenEval score difference between Main Results (0.90) and Ablation Study (80.94) to ensure consistent baseline reporting.
- **[1ce21f8590f2]** Add a dedicated section or paragraph discussing safety mitigations (e.g., content filters, watermarking) for the high-fidelity video generation capabilities described in Section 5_exps.
- **[a8baeb5bd70b]** Clarify data provenance and consent mechanisms for the large-scale training datasets (1B image-text, 140M video-text) referenced in Section 5_data to address privacy and copyright concerns.
- **[3e6357113d05]** Report confidence intervals or standard deviations for all benchmark scores (GenEval, DPG-Bench, VBench, MVBench, GEdit-Bench). Single point estimates without variance metrics make performance claims unverifiable.
- **[8d0b83c996d6]** Add statistical significance testing (e.g., paired t-tests, bootstrap CI) for ablation study results. Small differences like MaPE (80.56→80.94 GenEval) require significance validation.
- **[bb8f402b7958]** Apply multiple-comparisons correction (Bonferroni, FDR) when reporting best/second-best across 20+ VBench metrics and 20+ MVBench sub-metrics. Current claims risk false positives.
- **[83e67c05feb0]** Document number of evaluation runs per benchmark (seeds, repetition count). Reproducibility requires variance reporting across independent runs.
- **[2a248068a9e9]** Multiple sentence fragments found in Conclusion and Related Work sections (e.g., 'Key finding: multi-task synergy advances unified modeling' in Conclusion; 'Early systems: Flamingo...' in Related Work). These should be converted to complete sentences for formal academic prose.
- **[5f8a44e805c9]** Inconsistent writing style between the llmxive version (e000/e001 first part) and the bytedance version (main.tex/sec/*.tex). The latter contains telegraphic fragments (e.g., 'Freeze VAE and ViT encoders; optimize backbone' in Training section). Ensure the final manuscript uses consistent, complete sentences.
- **[4b2eade35666]** Some training objectives listed as fragments (e.g., 'Freeze VAE and ViT encoders; optimize backbone' in Training and Data section). Rephrase as complete sentences (e.g., 'We freeze the VAE and ViT encoders and optimize the backbone.').
