---
field: other
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/200
---

# https://arxiv.org/abs/2605.15298

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2605.15298

Submitted by: github-actions[bot]

(Intake from human-submission issue #200.)

## Rejection rationale (2026-06-10)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[78079bf5235c]** Multiple critical bibliography entries are missing from ref.bib, including GoogleRobotics_2025_arxiv, PhysBench_2025_arXiv, and OCRBenchV2_2025_arXiv. Claims relying on these sources cannot be verified.
- **[69989f3bb5b9]** Incorrect citation key used for RealWorldQA in sec/body.tex (line 467). It cites OCRBenchV2_2025_arXiv instead of the existing realworldqa2024 entry.
- **[c6a4fc6b9e06]** Verify SOTA claims in the Abstract and Introduction. Ensure baseline comparisons in tables are comprehensive enough to support "SOTA" assertions, particularly for benchmarks where margins are narrow (e.g., LIBERO 98.8% vs 98.7%).
- **[5d3e99bf0973]** Provide access to the source code repository to evaluate modularity, tests, and dependency hygiene.
- **[a4926af003ca]** Complete the implementation details section in sec/real_world_exp.tex (lines 130-150) by filling in TODOs for hyperparameters and hardware specs.
- **[17cd411eefab]** Add license declarations for the PhysBrain dataset, real-world Franka collection, and all third-party sources (e.g., Ego4D, BuildAI) in Section 2.2 and 6.
- **[5e9886743b07]** Provide a direct repository URL (e.g., Hugging Face, GitHub) for the dataset and code in the bibliography or project page to prevent link rot.
- **[ae6c5ff41525]** Release annotation prompts and logs for proprietary models (GPT-5, Gemini) to ensure annotation provenance transparency.
- **[7c17e27446c8]** Report data filtering statistics (e.g., % of clips discarded by motion score) in Section 2.2 to quantify selection bias.
- **[221b53b81c05]** In Figure 4 (vlm_qa_results_grouped.pdf, line ~543), independent y-axis ranges across panels hinder cross-benchmark visual comparison. Standardize y-axes or add explicit scale indicators to prevent misinterpretation of relative gains.
- **[a1abbd1726f6]** Qualitative grasping sequence figures (eggplant, carrot, etc.) are commented out in sec/real_world_exp.tex (lines 145-188) but referenced in the section's intent. Uncomment or remove these to ensure visual evidence matches claims of 'fine-grained physical understanding' in real-world experiments.
- **[ae7140f77f5b]** Ensure color choices in Figure 6 (real_world_vegetable_results.pdf, line ~134) are colorblind-safe. Caption mentions 'blue and peach accents'—verify these provide sufficient contrast for accessibility standards.
- **[c3434f2a33e6]** Replace informal acronym 'SOTA' with 'state-of-the-art' in Abstract and Introduction for formal consistency.
- **[e9f0900a0bb3]** Define all acronyms at first use (e.g., VGGT, DoF, EEF, JSON) to ensure accessibility for non-specialist readers.
- **[6a02f69fc4c3]** Simplify dense technical phrases like 'capability-preserving and language-sensitive adaptation design' in the Abstract.
- **[fc3c167a21e2]** Revise the claim of 'data efficiency' in Section 3.5 and Conclusion. The Real-World Experiments (Section 5) use equal data (450 trajectories) for both PhysBrain and the baseline. Demonstrate performance with reduced robot data or rephrase to 'performance efficiency under fixed data budgets.'
- **[8ec557bf5bb0]** Address the architectural confounding variable in Section 5. PhysBrain uses a dual-pathway architecture (Section 3.2) while the baseline ($\pi_{0.5}$) does not. Add ablation studies to isolate the contribution of human priors from architectural changes before attributing gains solely to priors.
- **[dcea918702bd]** Add IRB approval statement or informed consent details for human teleoperation data collection described in sec/real_world_exp.tex.
- **[05da97288c54]** Describe physical safety protocols (emergency stops, barriers) used during real-world Franka robot trials in sec/real_world_exp.tex.
- **[e519b833299e]** Include a dual-use discussion and responsible deployment limitations in sec/discussion.
- **[88331bb3accc]** Report standard deviations or confidence intervals for all simulation benchmark results (Tables 1-4). Current point estimates (e.g., 80.2% vs 79.2% in SimplerEnv-WidowX) lack statistical significance context.
- **[4cf34ed1c8cd]** Add ablation studies separating the contribution of the human-video data engine from the dual-pathway architecture. Without this, the central claim that 'physical priors from human video' drive gains is confounded.
- **[6e5ccfced9a2]** Specify exact sample sizes for the human video corpus (number of clips, hours) and robot adaptation trajectories for SimplerEnv/LIBERO, not just RoboCasa (24K). Current 'large-scale' claims are unverifiable.
- **[32713ff13569]** Report confidence intervals or standard deviations for all benchmark success rates (Tables 1-4, Figure 2) to quantify variance.
- **[d2c97cdd8961]** Add statistical significance tests (e.g., paired t-tests or bootstrap) for performance claims comparing PhysBrain to baselines.
- **[c0b66459700f]** Resolve TODO placeholders in sec/real_world_exp.tex (learning rate, batch size, epochs) to ensure reproducibility of the analysis.
- **[0a7921cf3e47]** Remove all \todo commands and definitions from the source code, including commented-out instances in Section 4 and Section 5, to ensure a clean submission.
- **[66cd507c2152]** Fix the missing space typo in Section Discussion: 'PhysBrain 1.0follows' should be 'PhysBrain 1.0 follows'.
- **[75f0a4465879]** Standardize citation commands throughout the document (currently mixed \cite and \citep).
- **[181e278581be]** Remove commented-out figure environments and implementation details sections that are marked with TODOs to avoid clutter.
