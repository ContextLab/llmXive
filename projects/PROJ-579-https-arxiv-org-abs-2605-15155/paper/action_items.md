# Automated-review action items — Self-Distilled Agentic Reinforcement Learning

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract claims +10.2% WebShop-Acc gain but omits model size. Table 1 shows this gain applies only to 7B (3B is +4.7%). Specify '7B' in Abstract to prevent misattribution.
- **[writing]** Section 3.1 claims OPSD collapses to 'near-zero' on Search-QA. Table 1 shows 0.0 for 3B but 6.2 for 7B. Qualify claim to specify '3B model' or 'smaller models' for accuracy.
- **[science]** Abstract claims SDAR 'consistently outperforms' baselines across all scales. Table 1 shows SDAR (41.9) < GRPO+OPSD (42.2) on Qwen3-1.7B Search-QA. Correct claim or data.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 1 caption is incomplete: '(a) Comparison between GRPO+OPSD and ;' omits the second method name, though the legend shows 'SDAR (Ours)'.
- **[science]** Figure 1 caption part (b) 'Overall Performance' is too vague; the plot shows 'Success Rate' over 'Step' for two methods, not a comprehensive overall performance summary.
- **[writing]** Figure 2: The middle and right panels lack a legend or explicit label identifying the blue bars as 'Average teacher-student gap', relying solely on the caption for definition.
- **[science]** Figure 2: The middle panel's x-axis ('Turn Step Interval') has non-uniform tick spacing (1, 11, 21...) that does not align with the visual density of the bars, potentially misleading the reader about the data distribution.
- **[writing]** Figure 3: The caption contains a grammatical error ('Illustrations of framework' should be 'Illustration of the framework') and a dangling comparison in the full caption list ('Comparison between GRPO+OPSD and ;') which suggests missing text.
- **[science]** Figure 3: The 'Self-Teacher' and 'Self-Student' icons are identical, which may confuse the reader regarding the distinct roles of the teacher and student models in the distillation process.
- **[writing]** Figure 4: The left plot's y-axis label 'Teacher Gap Mean' is ambiguous; the caption specifies 'Average teacher-student gap', but the negative values (ranging from -0.12 to -0.02) are not explained (e.g., is this a difference metric where negative implies the student is ahead?).
- **[writing]** Figure 4: The plots lack a legend or explicit line style definitions to distinguish the 'Average' trend line (darker) from the variance/noise band (lighter), relying on visual convention rather than explicit labeling.
- **[fatal]** Figure 5: The rendered image is a line chart of 'Success Rate' vs 'Step' with three metrics (Entropy, SOFT-OR Score, Teacher-Student Gap), but the caption describes it as 'Ablations of Token-level Gating'. The content does not match the caption, and the figure lacks the necessary ablation curves (e.g., gating on/off) to support the title.
- **[fatal]** Figure 6: The caption reads 'Ablations of $$' which is a rendering error or placeholder; it fails to define the parameter $\lambda$ shown in the legend.
- **[science]** Figure 6: The plot lacks error bars or shaded regions for the success rate curves, making it impossible to assess the statistical significance of the differences between the $\lambda$ values.
- **[writing]** Figure 7: The y-axis label 'ALFWorld', 'WebShop', and 'Search' is placed only on the far left of the grid, making it ambiguous whether these labels apply to the entire row or just the first subplot; explicit row labels or a shared y-axis label is needed.
- **[writing]** Figure 7: The x-axis label 'Step' is repeated on the bottom row but missing from the top two rows, creating visual inconsistency across the grid.
- **[writing]** Figure 7: The y-axis scales differ significantly between rows (e.g., 0.30–0.50 for ALFWorld vs. 0.175–0.375 for Search), but this is not explicitly noted in the caption, potentially misleading readers about relative magnitudes.
- **[writing]** Figure 8: The y-axis labels are illegible due to overlapping text and insufficient spacing, making it impossible to read the specific numerical values.
- **[writing]** Figure 8: The x-axis label 'Step' is only present on the bottom row; the top two rows lack x-axis labels, which is inconsistent with standard multi-panel figure formatting.
- **[science]** Figure 9: The y-axis labels (0.010–0.070) are inconsistent with the caption's claim of 'OPSD Loss'; these values are too low for standard loss curves and likely represent a metric like 'Gate Mean' (matching Figure 8) or 'Reward' (matching Figure 11). The caption appears to be mislabeled or the plot data is incorrect.
- **[writing]** Figure 9: The y-axis labels are missing for the middle and top rows of plots; only the bottom row (Search) has visible y-axis ticks and values, making it difficult to compare magnitudes across the grid.
- **[science]** Figure 10: The y-axis values are negative (ranging from -0.5 to -0.02), but the caption describes the metric as 'Teacher-Student Gap'. A 'gap' is typically a non-negative difference; negative values suggest the metric is actually a raw score or log-probability difference, not a gap. This contradicts the caption's description.
- **[writing]** Figure 10: The y-axis labels are present but lack units or a clear definition of what the negative values represent (e.g., log-probability difference, score difference). The caption does not clarify this, making the metric ambiguous.
- **[writing]** Figure 10: The x-axis is labeled 'Step' but does not specify the unit (e.g., training steps, epochs). This is critical for interpreting the training dynamics shown.
- **[science]** Figure 11: The caption claims to show training on 'Search-QA', but the y-axis label for the bottom row is 'Search'. This discrepancy creates ambiguity about whether the dataset is Search-QA or a different task named 'Search'.
- **[writing]** Figure 11: The y-axis label 'Search' in the bottom row is likely an abbreviation for the dataset 'Search-QA' mentioned in the caption; it should be updated to 'Search-QA' for consistency and clarity.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'OPSD' (On-Policy Self-Distillation) at its first occurrence in the Abstract and Introduction. The acronym is used immediately without expansion, violating standard readability norms for non-specialist readers.
- **[writing]** Replace the phrase 'reverse distillation' in the Abstract and Introduction with a plain description (e.g., 'distillation from a weaker teacher'). The term is used as a proper noun without definition and may confuse readers unfamiliar with specific distillation literature.
- **[writing]** Define 'UCB' (Upper Confidence Bound) at its first use in the 'Skills Retrieval' subsection. While common in RL, it is an acronym that should be spelled out for general accessibility.
- **[writing]** Replace the jargon-heavy phrase 'relegated to a carefully controlled auxiliary role' in the Introduction with plainer language (e.g., 'used only as a secondary, carefully managed component'). The current phrasing is unnecessarily dramatic and obscure.
- **[writing]** Define 'KL' (Kullback-Leibler) divergence at its first mention in the 'OPSD Optimization' subsection. The paper assumes the reader knows this acronym without expansion.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a logical argument for using a sigmoid gate to modulate On-Policy Self-Distillation (OPSD) in multi-turn RL, citing the instability caused by negative teacher-student gaps. The core premise—that negative gaps induce reverse distillation and that a gate can filter these—is logically sound in principle. However, there are inconsistencies in how the mathematical formulation supports the claimed causal mechanisms. First, in Section 3.2, the paper defines the gap $\Delta_t$ as the

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim 'consistently outperforms hybrid baselines across all model scales' overstates the margin. Table 1 shows SDAR often ties or leads by small margins (e.g., Qwen2.5-7B Search-QA: 49.0 vs 47.0). Temper 'substantial' to 'consistent' when comparing to hybrids, reserving 'substantial' for the GRPO baseline comparison.
- **[science]** Attributing Random Retrieval gains 'primarily' to gating is an overreach. Random skills may still provide regularization or generic context. Clarify that the method is robust to retrieval quality, rather than claiming the gains stem solely from the gating mechanism without a no-context control.
- **[writing]** The argument that Reverse KL is the key design choice aligning with 'weak teacher signals' overreaches. The gating mechanism already handles negative gaps; the divergence choice appears secondary. Tone down the claim that Reverse KL 'perfectly aligns' with the rationale, acknowledging the gating is the primary driver.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper relies on 'privileged training-only context' (skills) available to the teacher but not the student. Explicitly state the source of these skills (e.g., human-annotated, synthetic generation) and confirm they do not contain PII, copyrighted text, or harmful instructions.
- **[writing]** The method uses a 'SkillBank' from 'SkillRL' (cited as xia2026skillrl). Verify the license and data provenance of this external skill library to ensure it does not introduce copyright infringement or safety risks (e.g., jailbreak patterns) into the training loop.
- **[writing]** The evaluation includes 'WebShop' (online shopping) and 'Search-QA'. Clarify if the training data or the 'SkillBank' contains real user transaction logs or private search queries. If so, confirm that all data was anonymized and consent was obtained, or that only synthetic/public data was used.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Report standard deviation or confidence intervals for all main results in Table 1. The paper claims substantial improvements (e.g., +9.4% on ALFWorld) but provides no measure of variance across seeds or runs, making statistical significance impossible to assess.
- **[science]** Clarify the sample size (number of random seeds) used for the main experiments. The 'Implementation Details' section mentions GPU count and batch sizes but omits the number of independent training runs, which is critical for evaluating the robustness of the reported gains.
- **[science]** Provide effect size metrics (e.g., Cohen's d) or statistical test results (p-values) when comparing SDAR against baselines like GRPO and Skill-SD. The current reliance on point estimates in Table 1 is insufficient to rule out random fluctuation as the cause of observed differences.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report statistical significance (e.g., p-values, confidence intervals, or standard deviations over seeds) for the performance gains in Table 1. The current presentation of single-point estimates (e.g., +9.4% on ALFWorld) does not allow assessment of whether improvements are robust or due to random variance.
- **[science]** Clarify the number of random seeds used for all experiments. The 'Implementation Details' section mentions training steps and batch sizes but omits the number of independent runs used to generate the mean scores in Table 1 and the ablation studies.
- **[science]** Provide error bars or variance metrics in the training dynamics figures (e.g., Figure 7b_alfworld_gap_gate, ablation plots). The curves show mean trends, but without uncertainty bands, it is difficult to judge the stability of the gating mechanism across different training runs.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The abstract contains a significant redundancy where the first paragraph is almost entirely duplicated by the second paragraph. The first paragraph ends with '...across all model scales.' and the second immediately repeats 'Reinforcement learning (RL) has emerged...' with slight variations. One of these paragraphs must be removed to fix the flow.
- **[writing]** In the Introduction, the sentence '...while skill-conditioned privileged guidance requires asymmetric treatment for negative teacher rejections may arise from...' is grammatically broken and confusing. It appears to be a fragment or a run-on that conflates two distinct ideas. This needs to be split or rewritten for clarity.
- **[writing]** In the 'Training Dynamics' section, the text states 'the teacher is on average no confident than the student'. This is a typo; it should read 'not more confident' or 'less confident' to match the context of the negative gap described.
- **[writing]** In the 'Related Work' section, there is a typo 'reasoning tasksn' which should be 'reasoning tasks'. Additionally, the citation list contains a trailing comma inside the brackets: 'GUI automation~\citep{ye2025mobileagentv3,},'.
