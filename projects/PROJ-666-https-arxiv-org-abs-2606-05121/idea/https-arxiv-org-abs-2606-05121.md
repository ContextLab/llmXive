---
field: other
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/276
---

# https://arxiv.org/abs/2606.05121

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.05121

Submitted by: github-actions[bot]

(Intake from human-submission issue #276.)

## Rejection rationale (2026-06-12)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[afc6cd5d0220]** Verify that every cited reference has verification_status verified in the bibliography summary and add missing verification entries
- **[788638dc2374]** Replace placeholder or missing values in experimental tables with actual numbers and ensure consistent formatting
- **[dbbf018fd53a]** Provide a concise description of evaluation metrics and scoring thresholds used for ProactiveSound-Bench to improve reproducibility
- **[b29bbc587562]** Clarify the hyperparameter settings and training schedule for each of the four training stages in an appendix
- **[7546e906554a]** Add a brief discussion of limitations and potential ethical considerations of always-on audio interaction models
- **[886e5382a876]** Reconcile dataset statistics: Abstract/Section 4 claim 2.6M items/302k hours, but Figure 3(c) table lists 2.34M items/66.7K hours.
- **[02df6a80c33c]** Correct latency claim: Section 3.4 states 4.5x reduction, but Table 5.4 shows 2.12x (831ms vs 392ms).
- **[46c960d12aa9]** Fix WER regression number: Section 1 claims 3-point regression, but Table 'tab:asr' and Section 5.2 show 0.30 (3.17 vs 2.87).
- **[9dc995aeb595]** Unify model naming: Title/Tables use 'Audio-Interaction', but Section 4/5 text uses 'Mini-Omni 3'.
- **[0b7cb1254438]** Latency claim inconsistency: Section 3.4 claims 4.5x reduction, but Table tab:fifo_inference and Section 5.4 show 2.12x (392ms vs 831ms). This undermines reproducibility of performance claims.
- **[96306d5e50c6]** Code artifacts not provided. Cannot verify test coverage, modularity, or dependency hygiene. Please provide repository link or scripts in supplementary material.
- **[dc0318397b47]** LaTeX source hygiene: Large blocks of commented-out code (e.g., lines 1400-1600) reduce maintainability. Clean up unused tables and text versions before final submission.
- **[f34e06331008]** Resolve the 30x discrepancy between the claimed 302k hours (Abstract/Intro) and the ~9.7k hours sum in Appendix D Table. Audio stitching cannot increase total duration.
- **[35bcd81b69de]** Clarify the license for StreamAudio-2M and confirm redistribution rights for ElevenLabs/AudioX generated content, as commercial APIs often restrict public dataset release.
- **[e5a6c37ffbd5]** Provide a specific dataset version tag or content hash for the HuggingFace repository to ensure reproducibility of the exact training data used.
- **[caab11c7cd4c]** Figure category_distribution.pdf has placeholder caption 'Enter Caption' — must be replaced with descriptive text explaining the taxonomy and data distribution.
- **[30e77073cd96]** Case study figures (scenario1_home-4.pdf, scenario2_office-2.pdf) have minimal captions that do not explain what is shown or why it matters — expand to include key observations.
- **[dc80de8e9247]** Heatmap figure (fig3_cross_task_heatmaps.pdf) and continuity ratio figure (cross_task_continuity.pdf) must include explicit axis labels and color legends for print legibility.
- **[14c8cc30eb93]** Figure numbering is inconsistent (fig3_cross_task_heatmaps.pdf labeled as 'fig3' but appears as Figure 7 in paper) — ensure all captions match their in-text reference numbers.
- **[604c8ce110c1]** PNG figure dataset.png (5.3MB) may have resolution issues at print scale — verify 300+ DPI or convert to vector format.
- **[00fd896b9be7]** Expand all acronyms (ASR, WER, BLEU, STFT, KV-cache, VAD) at first use in main text and appendix.
- **[38e57e64f863]** Simplify dense phrases like 'comprehension-grounded response triggering' to improve accessibility.
- **[82818593fe56]** Clarify the distinction between LALM and LAIM acronyms to prevent reader confusion.
- **[4045ae76b431]** Section 3.4 claims 4.5x latency reduction, but Table tab:fifo_inference shows 831ms vs 392ms (2.12x). This numerical contradiction undermines the inference efficiency claim.
- **[0cd0e95f4e31]** Table tab:ablation_data lists Baseline (V1) MMAU as 57.81, but Table 1 shows Qwen2.5-Omni-3B Audio Instruction MMAU is 42.51 (Text is 57.81). The ablation logic conflates text and audio baselines.
- **[03618dacde3f]** Tone down the 'new paradigm' claim in the Introduction to 'framework' or 'approach' as a single model does not justify a paradigm shift.
- **[e481cfb94f2d]** Qualify the claim that capabilities are 'inaccessible to offline LALMs' in the Abstract and Section 5.2 to reflect implementation limits rather than architectural impossibility.
- **[c332bb204941]** Acknowledge the real-world performance degradation (Appendix Real-World Validation) in the main text to avoid overpromising robustness.
- **[caee90f06a52]** Explicitly state IRB approval status and informed consent procedures for real-world recordings in Appendix appendix:realworld.
- **[077e6d7282b6]** Add a risk mitigation discussion for safety-critical false negatives (Appendix app:analysis) before claiming proactive intervention capabilities.
- **[eac4d8df324c]** Include an Ethics Statement addressing privacy implications of always-on listening and data retention policies.
- **[8deb9fb73002]** Resolve dataset statistics discrepancy (302k vs 66.7k hours) in Abstract and Figure 3.
- **[4cf1064be7b9]** Clarify model naming (Audio-Interaction vs Mini-Omni 3) in Section 5.2 to ensure evidence attribution.
- **[4d93aa466ceb]** Expand real-world validation sample size (currently 2 hours) or provide statistical justification.
- **[d80a46a5a731]** Report variance across seeds for benchmark scores and ablation studies to confirm stability.
- **[0834342c070a]** Report confidence intervals (95% CI) for all benchmark scores in Tables 1-3. Currently no variance measures are provided across runs.
- **[59aec3d6f464]** Add statistical significance tests (paired t-test or bootstrap) comparing Audio-Interaction against key baselines. No p-values or significance markers exist.
- **[c5defc2ca6d5]** Clarify the number of independent training runs averaged for each reported score. Currently unclear if results are single-run or averaged.
- **[d787d8b88e75]** Apply multiple-comparison correction (e.g., Bonferroni) when claiming superiority across 8 benchmarks. Currently no correction is applied.
- **[c3427942c2a1]** Provide power analysis or justification for the 644-item Proactive-Sound-Bench sample size. No statistical basis for test set size is given.
- **[d2b911615fee]** The 2-hour real-world validation across 4 scenarios lacks variance reporting. Add scenario-level statistics with error bars.
- **[b3f2691cbf90]** Fix typographical errors: 'capabilitie' in Figure 1 caption and 'asyn chronous' in Figure 4 caption.
- **[29eff6cb19fa]** Correct grammatical error: 'a always-on' should be 'an always-on' (Introduction and Section 3.1).
- **[e446c156ca6f]** Standardize the naming of the benchmark; the text alternates between 'ProactiveSound-Bench' and 'Proactive-Sound-Bench'.
- **[fbd2a4c5570f]** Reduce the excessive use of underlining and italics for emphasis in the Introduction.
