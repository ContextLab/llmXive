# Automated-review action items — Learning from the Self-future: On-policy Self-distillation for dLLMs

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 4.3, the claim that AR-style OPSD 'fails to bring new knowledge' relies on an 'Overlap Top-K' metric near 1.0. Explicitly state the theoretical baseline or random overlap value to contextualize why this metric implies a lack of new information transfer.
- **[writing]** Section 4.2 claims d-OPSD uses 'around 10%' of RLVR steps. Table 3 shows a range from ~5.5% (GSM8K) to ~11% (Sudoku). Refine the phrasing to '5-11%' or 'approximately 10%' to accurately reflect the data variance across tasks.
- **[writing]** The claim of being the 'first OPSD framework for dLLMs' (Abstract, Sec 3.3) distinguishes d-OPSD from d3LLM and Cd4lm based on 'on-policy' vs 'off-policy' nature. Ensure the citations clearly support this specific distinction and that the definition of 'on-policy' excludes the cited methods' approaches.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption filename '[fig2.png]' contradicts the label 'Figure 1' and the content (which matches the description of Figure 2 in the provided list); verify the correct filename.
- **[writing]** Figure 1: The 'Teacher Prompt' box contains red text ('Here is a reference solution...') that is not defined in the legend or caption, making the distinction between the problem statement and the reference solution unclear.
- **[science]** Figure 1: The 'On-policy Generation' section shows 'Self-generated Future' tokens (e.g., 'bus', 'stop') appearing in the 'Teacher Construction' row, but the caption does not explain how the teacher is constructed from the student's future, creating a logical gap in the visual workflow.
- **[writing]** Figure 4: The image displays a UI screenshot titled 'Student Decoding' containing a reasoning block and masked tokens, but lacks the visual elements (e.g., timeline, divergence metrics, or state visualization) implied by the caption 'Current student decoding status' to effectively communicate the method's mechanics.
- **[science]** Figure 4: The figure shows a static text snippet with masked tokens (`<|mask|>`) but does not visually demonstrate the 'decoding status' or the specific 'self-future' information being utilized, making it difficult to verify the claim of on-policy self-distillation.
- **[writing]** Figure 5: The title contains a typo ('Constructiton' instead of 'Construction').
- **[writing]** Figure 5: The text content is heavily obscured by red highlighting and `<|mask|>` tokens, making the specific construction steps at $t=20$ difficult to read.
- **[science]** Figure 6: The image displays a static math problem and reference solution (GSM8K style) rather than a diagram or visualization of 'AR-style teacher construction' as claimed by the caption. It fails to illustrate the autoregressive process or mechanism described.
- **[science]** Figure 8: The image displays raw model output with XML tags (e.g., <reasoning>, </reasoning>) and LaTeX delimiters (e.g., \[ ... \]) that are not rendered or stripped. This makes the figure look like a raw log rather than a polished 'self-generated answer' for a scientific paper.
- **[writing]** Figure 8: The caption 'The self-generated answer' is too brief. It should explicitly state that this is the output corresponding to the question in Figure 7 to provide necessary context.
- **[writing]** Figure 9: The title contains a spelling error ('Construciton' instead of 'Construction').
- **[science]** Figure 9: The text content is heavily obscured by `<|mask|>` tokens and red highlights, making the specific 'toy experiment' data illegible and preventing verification of the self-teacher construction.
- **[science]** Figure 10: The caption 'Failure Mode of collapse' describes a qualitative failure, but the figure displays a quantitative line plot of accuracy vs. steps without context. It is unclear what task, dataset, or baseline this represents, making the claim of 'collapse' unsubstantiated by the visual alone.
- **[writing]** Figure 10: The title 'Countdown' is generic and does not reflect the caption's specific claim of 'Failure Mode of collapse'; the title should be descriptive of the phenomenon shown.
- **[science]** Figure 10: The x-axis label 'Optimization Steps' and the sharp drop at step 275 suggest a specific experimental condition, but the caption provides no details on the setup, making the figure impossible to interpret or reproduce.
- **[writing]** Figure 11: The caption 'Qualitative Examples on GSM8k' is too generic; it should explicitly describe the content (e.g., 'Comparison of d-OPSD vs. RLVR reasoning traces on a GSM8K math problem').
- **[writing]** Figure 11: The raw LaTeX code (e.g., `\text{}`, `\boxed{}`) is visible in the reasoning traces, reducing readability and suggesting incomplete rendering.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and jargon that are not consistently defined for a broader audience. In the Abstract, the terms "dLLMs" and "OPSD" are introduced and used immediately without defining the full phrases "diffusion Large Language Models" and "On-policy Self-distillation" first. While "dLLMs" is defined in the Introduction, the Abstract should be self-contained. Similarly, "RLVR" is used in the Introduction without its full expansion ("Reinforcement Learning

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Ambiguity in Step-Level Divergence (Section 3.2): The definition of the subset $\mathcal{K}_t$ (Eq 11) is logically opaque. The text describes selecting the "top-$k$ most confident tokens," but the equation $\sum |\mathcal{K}_t| = L$ suggests a partitioning of the sequence length. It is unclear if $k$ is a fixed hyperparameter per step or if the set size varies. Furthermore, Eq 12 averages the KL divergence over $\mathcal{K}_t$. If $\mathcal{K}_t$ is selected based on confidence, the supervision
- **[writing]** Causal Link in "New Knowledge" Claim (Section 4.3): The paper argues that the AR-style baseline fails because the "Overlap Top-$K_t$" is near 1, implying no new knowledge transfer. This is a correlation presented as a causal mechanism. High overlap could simply indicate that both the student and teacher (even with different conditioning) agree on the most probable tokens for a given task. The paper fails to provide a logical argument for *why* suffix conditioning (self-future) structurally neces
- **[writing]** The "Self-Future" Paradox (Section 3.3 & 4.4.4): The method relies on the student generating a trajectory, and the teacher being conditioned on the *final* answer of that trajectory (Eq 9). In the early stages of training, the student's final answer is likely incorrect. Logically, conditioning the teacher on an incorrect "future" should guide the student toward that incorrect answer, reinforcing errors. The paper mentions a "Fix teacher" strategy (App 5.1) and a "Compute only on Correct Generati

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of '10% of optimization steps' (Abstract) conflates update count with compute. Since d-OPSD uses pass@8 sampling per step (Sec 3.3), total FLOPs may match RLVR. Clarify that efficiency is in updates, not total compute.
- **[writing]** Describing AR-style OPSD as 'fundamentally conflicting' (Abstract) overstates the case. Table 4 shows it is less effective, not impossible. Soften to 'suboptimal' to avoid implying theoretical impossibility.
- **[writing]** The 'first OPSD for dLLMs' claim (Abstract) relies on distinguishing on-policy vs. off-policy data sources. Explicitly define this distinction early to prevent ambiguity regarding prior self-distillation attempts in diffusion models.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper presents a novel framework, d-OPSD, for on-policy self-distillation in diffusion large language models (dLLMs). From a safety and ethics perspective, the primary concerns revolve around the potential for unintended consequences of the self-distillation process, the transparency of the training methodology, and the broader implications of the technique. First, the methodology relies on a "self-teacher" constructed from the model's own correct generations (Pass@k). As noted in Appendix A

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The 'sample efficiency' claim compares optimization steps but ignores that d-OPSD uses pass@8 sampling per step. Without normalizing by total FLOPs or wall-clock time, the claim is ambiguous and potentially misleading.
- **[science]** The ablation on retaining ratio (Table 6) shows a weaker teacher outperforming a stronger one. This counter-intuitive finding lacks statistical validation (e.g., error bars, multiple seeds) to distinguish signal from noise.
- **[science]** The failure mode analysis attributes collapse to 'model-seeking behavior' but provides no quantitative evidence (e.g., KL/entropy trajectories) to support this hypothesis over other causes like overfitting.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard deviations for all reported accuracy metrics in Tables 1-8. Single-point estimates without variance measures (e.g., from multiple seeds) make it impossible to assess statistical significance of the claimed improvements over baselines.
- **[science]** Clarify the statistical test used to claim 'consistent outperformance' in Section 4.2. With only 4 tasks and varying sequence lengths, a formal test (e.g., paired t-test or Wilcoxon signed-rank) across seeds is required to support the claim that d-OPSD is statistically superior to diffu-GRPO.
- **[science]** The ablation studies in Section 4.4 (Tables 5-8) present single-point results. Provide variance estimates (e.g., standard error) for these ablation results to determine if observed differences (e.g., 81.0 vs 80.5) are statistically significant or within noise.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Correct subject-verb agreement in Section 1: 'While recent works... has successfully applied' should be 'have successfully applied'.
- **[writing]** Fix article usage and phrasing in Section 3.2: 'a nature choice' should be 'a natural choice'.
- **[writing]** Correct grammatical error in Section 3.3: 'severing simultaneously' should be 'serving simultaneously'.
- **[writing]** Fix sentence structure in Section 4.4: 'despite it is a weaker teacher' should be 'despite being a weaker teacher' or 'despite it being a weaker teacher'.
- **[writing]** Correct subject-verb agreement in Section 4.5: 'training sometimes degrade' should be 'training sometimes degrades'.
- **[writing]** Fix article usage in Section 4.5: 'the same phenomena is' should be 'the same phenomenon is'.
- **[writing]** Correct preposition usage in Section 4.5: 'prevent from further learning' should be 'preventing it from further learning' or 'preventing further learning'.
- **[writing]** Fix article usage in Appendix 3.2: 'a engineering technique' should be 'an engineering technique'.
- **[writing]** Correct verb form in Appendix 3.2: 'need to be stored' should be 'needs to be stored' to agree with 'gradient maps' or rephrase for clarity.
- **[writing]** Fix article usage in Appendix 3.3: 'set an threshold' should be 'set a threshold'.
- **[writing]** Correct verb form in Appendix 3.3: 'should be include' should be 'should be included'.
