---
field: other
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/212
---

# https://arxiv.org/abs/2605.16403

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2605.16403

Submitted by: github-actions[bot]

(Intake from human-submission issue #212.)

## Rejection rationale (2026-06-09)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[5d3bde5bcaed]** Include all source code artifacts (training scripts, data processing pipelines, evaluation scripts) in the submission package. Currently, only LaTeX and PDFs are provided.
- **[207463d5b61b]** Provide a requirements.txt or environment.yml file to validate dependency hygiene and ensure reproducibility of the training environment (H200/H100 GPUs, DeepSpeed).
- **[a95acb6f7248]** Add unit tests or validation scripts for the intervention pipeline (Shift/Mute/Swap) to verify the correctness of the Thud diagnostic framework.
- **[910de45a28ac]** Explicitly state the license (e.g., CC-BY, MIT) for the source datasets (Oops, FineVideo) and the newly constructed intervention dataset in Appendix app:assets.
- **[40d29ff7804d]** Add version numbers or commit hashes for all external evaluation benchmarks (VGGSoundSync, Video-MME, etc.) to ensure reproducibility in Section 4.1.
- **[93e57b2083e8]** Clarify the data release mechanism (e.g., supplementary material, specific URL) and access restrictions for the Thud diagnostic assets in Appendix app:assets.
- **[d929e6b055e9]** Figures lack alt text for accessibility compliance. All 11 figures (motivation_fig_3.pdf, fig2_v2.pdf, heatmap_v2.pdf, etc.) must include \alttext{} or equivalent accessibility metadata for screen readers and print accessibility.
- **[ba1c60317f1c]** Color-critical figures (heatmap_v2.pdf, prediction_breakdown_v2.pdf) lack grayscale/print-safe verification. The red heatmap encoding in fig:failure_heatmap may be indistinguishable in black/white print; add pattern fills or texture overlays to differentiate failure modes.
- **[ddd9502972bc]** Multi-panel figure sync-results-combined (Fig. 5) has subfigures without individual axis labels visible in the caption. Ensure y-axis units (% accuracy) and x-axis labels (model names or offset bands) are legible at 100% zoom and when printed at conference poster scale.
- **[74a4b1f5112e]** wrapfigure placements (fig:falsealarm, fig:failure_heatmap, fig:vgg_diff, fig:beyond_sync) risk column overflow in two-column format. Verify final PDF compilation does not truncate figure content or create awkward text wrapping at column boundaries.
- **[65122636c844]** Expand acronyms in Table 4 (e.g., V-MME, LVB, WS, DO, OP, SP, CTP, FV-D, LV-MCQA, FV-A) within the caption or footnote to ensure non-specialist readability.
- **[b247b6d956c4]** Resolve inconsistency between Table 4's 'FV-A' and Appendix's 'FV-AVQA-L'. Define 'FV-A' explicitly or use the full name consistently.
- **[23006f77b713]** Replace 'SOTA' and 'OD' in Introduction with 'state-of-the-art' and 'out-of-distribution' to avoid unexpanded acronyms.
- **[546570c3d957]** Simplify abstract metaphors like 'existential and material traps' and 'cognitive decoupling' to precise technical descriptions of model behavior.
- **[9d8f326dd10e]** Define 'Omni' explicitly in Introduction when first used (e.g., 'omni-modal (audio-video-text)'), rather than relying on shorthand.
- **[6beabed19eac]** Abstract contains contradictory claims: it states the '10K-sample recipe' improves all three dimensions by 28% (Abstract, lines 20-22) but also claims the same optimization yields 'marginal improvements against existential and material traps' (Abstract, lines 26-28). Section 4.3 clarifies the 28% gain requires *additional* Mute/Swap SFT on top of the 10K recipe. The Abstract must distinguish between the 10K temporal recipe and the final model to avoid misattribution.
- **[560bee985367]** Table 2 ('Alignment Tax') reports results for 'Ours' on Sync and General benchmarks but omits Mute/Swap scores, despite the Abstract claiming a 28% average gain across all three dimensions. To support this claim logically, the table or main text must explicitly report the intervention-specific accuracies corresponding to the 28% figure.
- **[5aacbdc85d2d]** Clarify ethical oversight for human annotators viewing 'Oops' dataset videos, which may contain distressing content involving real people.
- **[32023a5f8bf3]** Complete funding and conflict-of-interest disclosure in the 'ack' section for the camera-ready version.
- **[905f3ae498df]** Report exact sample size (N) for all evaluation tables (Table 1, Table 2) to allow effect size context.
- **[868a54f88714]** Add confidence intervals or significance tests for accuracy comparisons, especially for marginal gains (e.g., Table 2 Avg differences).
- **[20dff5937ce5]** Validate the GPT-5.4 judge reliability used in Appendix E (lines 1050+) against human gold standards (e.g., Cohen's kappa).
- **[1b7d5078448b]** Confirm data disjointness between training sources (FineVideo/Oops) and evaluation benchmarks to rule out leakage.
- **[6ca2a2850101]** Report confidence intervals or statistical significance tests (e.g., paired t-tests, bootstrapping) for the accuracy comparisons in Table 2 to validate the claimed 'substantial improvements' over baselines.
- **[d223306d4051]** Explicitly state the number of test samples (N) for each benchmark in Section 4.1 to allow assessment of statistical power, particularly for the 'Avg Gap' metric.
- **[dfe4b2aa5aab]** Address multiple-comparisons correction in the recipe ablation study (Table 2) where 8 DPO variants are compared to select the best performing recipe.
- **[e098be9a641c]** Quantify the reliability of the GPT-5.4 judge used for parsing free-form outputs (e.g., inter-judge agreement or calibration against human labels) to ensure evaluation noise does not obscure small effects.
