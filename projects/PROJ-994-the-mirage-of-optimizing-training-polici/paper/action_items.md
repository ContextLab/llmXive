# Automated-review action items — The Mirage of Optimizing Training Policies: Monotonic Inference Policies as the Real Objective for LLM Reinforcement Learning

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper makes several strong claims regarding the theoretical guarantees and empirical metrics that are not fully supported by the provided text or tables. First, the Abstract and Introduction repeatedly assert that the proposed method ensures "monotonic" improvement of the inference policy. However, Section 3.2 ("Step 2: Inference-Gap-Aware Update Acceptance") explicitly contradicts this by stating: "This mechanism does not provide a formal monotonic-improvement guarantee, but it reduces the

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption claims to compare 'PPO-IS, Vanilla-IS, and TIS', but the 'Reward' and 'Mismatch-K3' plots include a 'Baseline' series (grey) that is not mentioned in the caption text.
- **[science]** Figure 1: The 'Clip Ratio' bar chart displays a value of 7.18e-03 for TIS, which is an order of magnitude higher than the other methods (~2e-04), yet the y-axis is not labeled with units or a title, making the scale interpretation ambiguous.
- **[science]** Figure 2: The caption claims to show sensitivity to $c$ and $T_{post}$, but the legend only defines $c=0$, $c=0.0001$, $c=-0.0001$, and 'Ours'. The 'Ours' method is undefined in the caption or legend, and the $T_{post}$ metric is not explicitly labeled on any axis (though the rightmost panel is likely it).
- **[writing]** Figure 2: The rightmost panel's y-axis label is missing; the caption identifies this metric as '$T_{post}$', but the plot itself lacks this label, relying solely on the caption for identification.
- **[science]** Figure 3: The 'Inference Gap' panel shows the 'ours' method (yellow) oscillating around 0.0000, while the caption claims the full method obtains a 'more controlled inference-policy trajectory.' The visual data suggests the 'ours' method is unstable or noisy rather than controlled compared to the baselines.
- **[writing]** Figure 3: The legend uses two distinct shades of orange for '+ step 1' and '+ step 2' which are visually very similar and difficult to distinguish from one another in the plots, especially in the 'Mismatch-K3' panel.
- **[science]** Figure 4: The caption describes the plot as 'Inference-training K3-KL and inference gap' but does not define the colors. The legend identifies the lines as 'Qwen3-4B FP8' and 'Qwen3-1.7B FP8', yet the caption fails to specify which model corresponds to the orange or red lines, making the data interpretation ambiguous.
- **[writing]** Figure 4: The x-axis label 'Training Step' is present, but the caption does not specify the total number of steps or the context of the training run (e.g., which specific experiment or baseline from Figure 3 this data is drawn from).

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The paper generally maintains a high standard of technical clarity for an audience familiar with Reinforcement Learning and LLMs. Most core concepts like "training-inference mismatch," "GRPO," and "importance sampling" are either standard or well-contextualized. However, there are several instances where specific notation, acronyms, or named variants are introduced without immediate, self-contained definitions, forcing the reader to rely on external citations or later sections to understand the

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** In Section 4.3, the text claims random rollback is 'more conservative' because it rejects 67% vs Step 2's 53.5%. While numerically true, the phrasing is slightly ambiguous. Clarify to 'rejects a higher percentage' to ensure the logical link between 'conservative' and the rejection rate is explicit.
- **[writing]** In the Appendix, c_end=0 for Qwen3-4B implies strict non-negative acceptance. Ensure the main text explicitly defines c=0 as 'strict non-regression' to prevent misinterpretation of the tolerance parameter's behavior at the end of annealing.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract claims MIPU 'improves average reasoning performance' generally, but experiments (Sec 5.1) are restricted to FP8-quantized rollout on two Qwen3 models. Scope the claim to 'under high training-inference mismatch (e.g., FP8 quantization)' or add evidence from full-precision settings.
- **[writing]** Conclusion states MIPU improves 'training stability' generally, but Limitations admit tests are only on 'moderate-scale models' and never in non-quantized settings. Clarify that stability is demonstrated specifically under quantization-induced mismatch, not as a universal property.
- **[writing]** Introduction frames the solution as addressing 'training-inference mismatch' generally, yet validation is only in 'FP8-quantized rollout' (Sec 5.1). Clarify that the method targets mismatch 'amplified by low-precision inference' rather than all forms of mismatch.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a methodological contribution to Reinforcement Learning for Large Language Models (LLMs), specifically addressing training-inference mismatch in mathematical reasoning tasks. The work involves training models (Qwen3-1.7B and Qwen3-4B) on public mathematical benchmarks (MATH-500, AIME24, etc.) using standard RL algorithms (GRPO) and a proposed variant (MIPU).

From a safety and ethics perspective, the research is low-risk. The datasets used are standard, public, and non-sensitive mathematical problem sets. The models are open-weight (Qwen3) and trained on these benign tasks. The proposed method (MIPU) aims to improve training stability and performance; it does not introduce capabilities for generating harmful content, bypassing safety filters, conducting cyberattacks, or deceiving users. The "risk" discussed in the paper is purely technical (training collapse or performance degradation), not societal harm.

The paper includes a "Licenses" section (Appendix) that correctly identifies the licenses for the datasets and models used (MIT, Apache-2.0, etc.), demonstrating compliance with data provenance norms. There is no use of human-subject data requiring IRB approval, no release of Personally Identifiable Information (PII), and no dual-use capabilities described that would lower the barrier to a specific harmful application (e.g., automated vulnerability discovery or biological synthesis).

Consequently, there are no foreseeable, non-trivial risks of harm that the paper fails to acknowledge or mitigate. The standard "broader impacts" discussion is not strictly required for this type of algorithmic optimization paper, and the absence of a dedicated ethics section does not constitute a safety failure given the benign nature of the data and task. The paper is safe to accept.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling theoretical argument for objective misalignment in LLM RL and proposes MIPU to address it. However, the empirical evidence supporting the central claims of performance improvement and stability is currently insufficient to rule out sample noise or lucky seeds. The primary concern lies in the lack of variance reporting. Table 1 presents headline accuracy numbers (e.g., 66.71% vs 65.66% for Qwen3-4B) derived from what appears to be single runs. In reinforcement lear

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 1 and Table 2 report pass@1 accuracy to two decimal places (e.g., 66.71%) without any measure of uncertainty (SD, SE, or CI) or mention of the number of random seeds used. In RL experiments, performance is highly stochastic; reporting a single point estimate implies false precision. Report mean ± SD over at least 3 independent seeds for all methods, or explicitly state that results are from a single run and rephrase claims of 'stability' accordingly.
- **[writing]** The 'Stable' column in Table 1 is a binary qualitative judgment (checkmark/cross) derived from visual inspection of training curves (Figure 1) rather than a statistical test of variance or a formal stability metric (e.g., coefficient of variation over the final 20% of training). Define a quantitative stability metric (e.g., max drop from peak, or variance of the last 100 steps) and report it numerically to support the binary classification.
- **[writing]** The paper claims MIPU is 'significantly better' or 'more stable' than baselines in the abstract and conclusion, but no hypothesis tests (e.g., paired t-tests or Wilcoxon signed-rank tests) are reported in the text or tables to support these comparative claims. If multiple seeds are run, perform a statistical test on the final scores and report p-values; if only one run is available, remove the word 'significantly' and qualify the comparison as 'observed improvement'.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript presents a clear and compelling argument regarding the training-inference mismatch in LLM reinforcement learning. The logical flow from the problem statement to the proposed MIPI objective and the MIPU framework is generally strong. However, there are several specific instances where the prose requires polishing to ensure the reader can parse sentences on the first pass without stumbling over grammatical errors or ambiguous phrasing. The most significant issue is a grammatical err
