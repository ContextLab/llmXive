# Automated-review action items — IndusAgent: Reinforcing Open-Vocabulary Industrial Anomaly Detection with Agentic Tools

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper cites 'Qwen3-VL-8B' (e.g., Table 2, Fig. captions) and 'GPT-4.1' (Table 1) as baselines. These model versions do not exist in public records as of the paper's context (2025/2026). Verify if these are typos for Qwen2.5-VL or internal unreleased models, and correct citations to match actual public versions or clarify their status.
- **[writing]** The bibliography lists 'arXiv:2605.20682' (the paper itself) and several 2026-dated citations (e.g., 'zhang2026pelican', 'song2026human', 'wang2026cac') as established works. Since the paper is a 2026 preprint, citing future-dated works as completed literature is factually inconsistent. Ensure all cited works are either published or clearly marked as 'in preparation' or 'arXiv preprint' with correct dates.
- **[writing]** The 'NeurIPS Paper Checklist' states 'Answer: No' for 'Open access to data and code' with justification 'data and code will be released upon publication'. However, the paper claims to be a preprint on arXiv (2605.20682). If the paper is already public, the code/data should ideally be available or the justification should reflect the specific embargo policy. Clarify the availability status to avoid misleading readers about reproducibility.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** Figure 1: The caption text is truncated at the end ('...overcomes both visual ambiguities and physic'), cutting off the sentence and likely the figure reference tag.
- **[writing]** Figure 1: The text in panel (b) contains a formatting error with a missing space between the question mark and the instruction ('...this image ?structure your response...').
- **[writing]** Figure 3: The caption is generic ('Case Study between Qwen3-VL-8B and our method') and fails to describe the specific visual content (cable cross-section) or the specific failure mode (hallucination of normalcy) shown in the image.
- **[writing]** Figure 3: The image contains a decorative crying emoji in the Qwen3-VL-8B panel which is unprofessional for a scientific publication and lacks a definition in the caption.
- **[writing]** Figure 4: The caption is generic ('Case Study between Qwen3-VL-8B and our method') and fails to describe the specific visual content (a screw defect detection task) or the specific outcome shown, making it impossible to interpret the figure's scientific contribution without reading the internal text.
- **[writing]** Figure 4: The image contains a large, distracting emoji (crying face) in the Qwen3-VL-8B panel that is unprofessional for a scientific publication and serves no analytical purpose.
- **[writing]** Figure 5: The caption is generic ('Case Study between Qwen3-VL-8B and our method') and fails to describe the specific visual content (a defect detection task on a textured surface) or the specific outcome shown, making it impossible to interpret the figure without reading the internal text boxes.
- **[writing]** Figure 5: The image contains a large, distracting crying emoji icon in the Qwen3-VL-8B panel; while likely intended to indicate failure, this informal graphic is unprofessional for a scientific publication and should be replaced with a standard indicator or removed.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript exhibits a high density of domain-specific acronyms and jargon that are not consistently defined upon first use, potentially excluding readers from adjacent fields or those new to agentic AI. In Section 3.2, the term "IoU" is used to describe the spatial localization reward component without definition. While standard in computer vision, a general reader may not immediately grasp its meaning. Similarly, in Section 4.3, the ablation study refers to "TOL" (Tool Augmentation library)

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Table 1 claims SOTA but omits specialized baselines like PatchCore. The text generalizes 'leading commercial systems' despite only listing GPT-4.1, creating a logical gap in the comparative evidence.
- **[science]** Eq. 3 defines an 'Accuracy-Gated' reward but adds R_format outside the gate. This allows credit for formatting even when accuracy is zero, contradicting the stated mechanism that failure voids all other rewards.
- **[science]** Ablation 'w/o SFT' conflates SFT utility with RL training stability. If SFT is a prerequisite for RL, removing it breaks the pipeline, making the performance drop a training artifact rather than proof of SFT's specific value.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim of 'SOTA' performance (Section 4.2) is overreaching given the exclusion of recent specialized IAD agents (e.g., AgentIAD, cited in bibliography but not compared in Table 1). The authors must either include these baselines or qualify the claim to 'among evaluated models'.
- **[writing]** The conclusion states the method 'overcomes perceptual dilution and hallucinations' (Section 5). This is an absolute claim not fully supported by the data, which shows high recall but does not explicitly quantify hallucination rates against a baseline. Temper this to 'mitigates' or provide specific hallucination metrics.
- **[writing]** The paper claims to address the 'false-negative bottleneck' with 'massive recall surges' (Section 4.2). However, the comparison baseline for this specific claim (Qwen3-VL-8B) is a general-purpose model, not a specialized IAD method. The authors should clarify that this improvement is relative to general VLMs, not necessarily the state-of-the-art in IAD.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The NeurIPS Checklist explicitly states 'No' for Open access to data and code, with justification that they will be released 'upon publication.' This creates a reproducibility barrier and potential conflict with open-science norms. Authors must clarify the specific license, release timeline, and repository URL in the final manuscript to ensure compliance with ethical data sharing standards.
- **[writing]** The paper relies on 'Indus-CoT' generated by a 'strong teacher model' (Section Limitations). The authors must explicitly disclose the identity of this teacher model, the data used to generate the CoT, and any potential biases introduced by the teacher's training data to ensure transparency and prevent the propagation of hidden biases in the industrial inspection domain.
- **[writing]** The 'Safeguards' checklist item is marked 'NA' with the justification that the method uses pre-trained models. However, the system actively invokes tools (e.g., T_crop, T_measure) on industrial assets. Authors should briefly discuss potential risks if the agent is deployed in safety-critical environments (e.g., false negatives leading to undetected defects) and whether any human-in-the-loop verification is recommended.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The NeurIPS Checklist explicitly states 'No' for statistical significance (Item 7), claiming error bars are not required in the field. However, the ablation studies (Tables 4 & 5) show large performance swings (e.g., VisA dropping from 76.8% to 55.5% without SFT). The authors must provide standard deviations or results from multiple random seeds to confirm these gains are not due to random initialization or data split variance.
- **[science]** The reward function (Eq. 3) relies on ground-truth IoU ($R_{loc}$) and semantic distance ($R_{type}$) during training. The paper does not specify if the test set annotations used for these rewards are the same as those used for evaluation, or if a separate validation set was used for RL tuning. If the RL policy was optimized directly on the test set metrics, this constitutes data leakage and invalidates the SOTA claim.
- **[science]** The 'Tool Usage Statistics' table (Appendix) reports a 99.1% success rate for tool calls. The definition of 'success' is ambiguous (e.g., API return 200 vs. correct visual crop). Without a clear definition and error analysis of failed tool calls, the claim that the agent is 'cost-aware' and 'reliable' is not fully supported by the evidence.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The NeurIPS Checklist explicitly states 'No' for statistical significance (Item 7), justifying this by claiming the field 'doesn't require error bars.' This is scientifically unsound for a paper claiming SOTA performance with specific margins (e.g., +17.4% on MPDD). The authors must report standard deviations or confidence intervals derived from multiple random seeds or cross-validation folds to validate that these gains are not due to random initialization or data split variance.
- **[science]** The ablation studies (Tables 4 and 5) present single-point performance metrics without any measure of variance. Given the stochastic nature of RL training (GRPO) and SFT, the reported improvements (e.g., VisA dropping from 76.8% to 55.5% without SFT) need to be contextualized with statistical significance tests (e.g., paired t-tests or bootstrap confidence intervals) to ensure the observed effects are robust and reproducible.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the NeurIPS Checklist (e002), item 'Broader impacts' contains a typo: 'The border impacts is provided...' should be 'The broader impacts are provided...'. Additionally, item 'Safeguards' has a grammatical error: 'This proposed methods is safe' should be 'This proposed method is safe'.
- **[writing]** In Appendix e001, Figure captions for 'fig/case3.png' and 'fig/case2.png' are repetitive and slightly awkward: 'Case Study between Qwen3-VL-8B and our method.' Consider rephrasing to 'Comparison of Qwen3-VL-8B and IndusAgent on [specific task/defect type]' for better clarity and flow.
- **[writing]** In Section 'Agentic Reinforcement Learning' (e002), the sentence 'We utilize GRPO... to avoid actor-critic memory costs' is slightly abrupt. Consider adding a brief clause explaining *why* actor-critic memory costs are a specific concern in this context (e.g., '...which are prohibitive for long-horizon tool-use trajectories').
