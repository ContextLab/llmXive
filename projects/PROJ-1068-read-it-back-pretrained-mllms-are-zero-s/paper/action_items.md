# Automated-review action items — Read It Back: Pretrained MLLMs Are Zero-Shot Reward Models for Text-to-Image Generation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper makes several specific quantitative claims in the Introduction and Experiments sections that do not align precisely with the reported results in the tables, creating ambiguity about the magnitude and conditions of the reported improvements. First, the Introduction claims Self-\\method outperforms the best external MLLM by "+2 on WISE." However, Table 1 shows that without Chain-of-Thought (CoT), Self-\\method (0.52) actually underperforms the best external MLLM (\\method, 0.53). The gai

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption text is truncated and contains placeholders (e.g., 'Overview of .', 'aggregates this', 'Self-, using BAGEL's own') instead of the full method name 'SpectraReward', making it difficult to interpret the figure's claims.
- **[writing]** Figure 1: The caption for panel (d) is cut off mid-sentence ('bring significan'), failing to describe the content of the radar chart.
- **[science]** Figure 1: Panel (c) plots 'Reward MLLM Comparison' with a y-axis labeled 'Reward' but lacks a unit or scale definition (e.g., log-likelihood, normalized score), making the magnitude of the 'non-monotonic gains' uninterpretable.
- **[writing]** Figure 3: The caption contains multiple missing terms (e.g., 'Token-level semantic sensitivity of .', 'aggregates this', 'i.e., .') where variable names or method identifiers appear to be omitted.
- **[writing]** Figure 3: The caption text 'calculated over four pairs' is ambiguous; it is unclear if this refers to four image pairs or four token pairs, and the specific pairs are not defined.
- **[writing]** Figure 4: The caption contains a missing term ('visual interpretation of .') and the image lacks a label identifying the method (e.g., 'Self-') being visualized.
- **[writing]** Figure 4: The caption is extremely brief and does not explain the meaning of the numerical values (e.g., -3.490) displayed on the images.
- **[science]** Figure 5: The caption 'Qualitative comparison' is too generic and fails to describe the specific content shown (side-by-side image generation results for 'BAGEL' vs 'Self-SpectraReward' across four distinct prompts), making it impossible to understand the figure's specific contribution without guessing.
- **[writing]** Figure 5: The figure contains no internal labels, axes, or legends to identify the specific prompts or the models being compared; all context is derived solely from the image content itself, which is poor practice for a standalone scientific figure.
- **[writing]** Figure 7: The caption contains a typo in the filename reference '[appendix_visualization_campare.pdf]' (should be 'compare').

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 3.1, Eq. 1: The symbol `T` is used in the denominator and summation limit without explicit definition in the text immediately preceding the equation. While defined later in Section 4.1 as 'sampling steps', in the method section it refers to prompt token count. Define `T` as the number of prompt tokens at its first use in Section 3.1 to avoid confusion with the sampling steps `T` used later.
- **[writing]** Section 3.1: The term 'teacher-forced' is used to describe the forward pass. While standard in NLP, a brief parenthetical clarification (e.g., 'using ground-truth tokens as input') would ensure a reader from a pure computer vision background understands the specific decoding strategy without needing to infer it from context.
- **[writing]** Section 4.1: The acronym 'AWM' is introduced as the default RL algorithm without being spelled out (e.g., 'Adaptive Weighted...'). While it is a specific method name, defining the full name at first use in the Experimental Setup section is necessary for an adjacent-field reader to identify the algorithm.
- **[writing]** Section 4.1: The term 'DVReward' is used in the comparison with AlphaGRPO ('...with the proposed MLLM-derived DVReward') without definition. It appears to be a specific reward variant from the cited AlphaGRPO paper, but the acronym is not expanded or explained in this text, leaving the reader to guess its meaning.

## paper_reviewer_logical_consistency — verdict: accept

The paper presents a logically coherent argument for using image-conditioned prompt likelihood as a reward signal for text-to-image reinforcement learning. The core premise—that a pretrained MLLM's ability to predict a prompt given an image reflects the image's alignment with that prompt—is consistently defined and applied throughout the text.

The derivation of the reward function in Section 3 (Eq. 1) follows directly from the stated goal of measuring "how well the generated image can be translated back into the prompt." The subsequent analysis of "language-prior cancellation" in Section 3.3 correctly identifies that for group-relative RL, the text-only prior cancels out, justifying the omission of a PMI-style correction without introducing a logical gap.

The distinction between the external \method and the internal Self-\method is maintained consistently. The claim that Self-\method benefits from "reward-policy alignment" is supported by the premise that the branches share tokenizers and pretraining distributions, and the experimental results in Table 1 and Table 2 consistently show Self-\method outperforming larger external models, which aligns with the hypothesis that alignment can rival scale.

There are no contradictions between the abstract, introduction, and conclusion regarding the scope of the results. The limitations section (Appendix) appropriately qualifies the method's dependence on the MLLM's visual reasoning capabilities, which is consistent with the method's definition. The ablation studies (Tables 3 and 4) support the textual claims regarding the superiority of the likelihood-based reward over scalar scoring and VQA decomposition. The argument holds together without non-sequiturs or internal contradictions.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The abstract and introduction claim the method works for 'any pretrained MLLM' and 'any' model, but experiments are restricted to four specific families (Qwen, Gemma, InternVL, BAGEL) and a specific parameter range (4B-235B). Narrow the claim to 'across diverse MLLM families tested' or explicitly acknowledge the untested regimes (e.g., non-architectural variants, smaller/larger scales).
- **[writing]** The conclusion states the method 'significantly and consistently improves... across all evaluated benchmarks,' but Table 4 (DPG-Bench) shows Self-\method underperforming the \method variant on the 'Overall' score at 512 resolution (87.73 vs 88.08) and on 'Relation' at 1024 resolution. The narrative omits these specific failures. Add a sentence acknowledging that consistency is not absolute across all metrics and resolutions.
- **[writing]** The abstract claims the method is 'training-free' and 'off-the-shelf,' which is accurate for the reward function itself, but the conclusion frames the results as a 'closed-loop self-improving framework' without clarifying that this requires the specific architectural condition of a Unified Multimodal Model (UMM) with distinct understanding/generation branches. Generalize the 'self-improving' claim to apply only to UMMs, as standard MLLMs cannot form this loop without architectural modification.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a training-free reward mechanism for text-to-image generation using pretrained Multimodal Large Language Models (MLLMs). From a safety and ethics perspective, the work is low-risk. The methodology relies on computing log-likelihoods of existing prompts against generated images, which does not inherently create new dual-use capabilities, nor does it lower the barrier to generating harmful content beyond what the underlying MLLMs and diffusion models already allow.

The authors have appropriately addressed the relevant ethical considerations in the "Broader Impacts" section (Appendix, `sec/X_suppl.tex`). They explicitly acknowledge that easier RL optimization could amplify existing risks, such as the generation of misleading visual content or unsafe images, and note the potential for inheriting biases from the reward backbone. They recommend standard safety filters and bias auditing as mitigations.

There are no indications of human-subjects data usage requiring IRB approval, no release of personally identifiable information (PII), and no use of scraped data in violation of terms of service (the paper relies on public benchmarks and pretrained models). The "Self-SpectraReward" approach, while creating a closed-loop self-improvement system, is a methodological contribution to alignment and does not constitute a system designed to deceive or surveil. The paper does not disclose operational vulnerabilities or provide actionable exploit code.

Consequently, there are no foreseeable, non-trivial risks of harm that the paper fails to acknowledge or mitigate. The existing disclosure is sufficient for this type of algorithmic research.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling hypothesis that image-conditioned prompt likelihood serves as an effective zero-shot reward signal. However, the experimental design contains specific gaps that prevent the reported results from definitively establishing the claimed causal mechanisms, particularly regarding the stability of the gains and the isolation of the "alignment" effect. First, the main results in Tables 2 and 3 are presented as single-point estimates (e.g., Self-Method achieving 89.5 on Ge

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Tables 1-4 report single-point benchmark scores without uncertainty metrics (SD/SE/CI) or seed counts. RL results vary stochastically; report mean ± SD over ≥3 seeds for all main results to distinguish stable gains from noise.
- **[science]** Section 4.3 and Table 2 compare ~20+ configurations but claim 'significant' improvements without p-values or multiple-comparison corrections (e.g., Bonferroni). Apply FDR correction or rephrase claims to 'observed improvements' to avoid false positives.
- **[writing]** Figure 2 caption notes error bars over four pairs, but main tables lack uncertainty. Ensure consistent uncertainty reporting (e.g., SD over seeds) across all quantitative claims, not just in specific figures.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Section 3, subsection 'Analysis of \method': The paragraph on 'Token-level semantic sensitivity' opens with a sentence that lists two failure types but then immediately pivots to describing the specific instantiation (counting error) without a clear transition. Split the first sentence to state the general finding ('We examine sensitivity to local visual errors') before detailing the specific examples of attribute and object mismatch.
- **[writing]** Section 4, subsection 'Main Results': The paragraph begins with 'We use our \method as the proxy reward...' but the subsequent sentences jump between benchmark descriptions, baseline comparisons, and specific numerical gains without a clear topic sentence. Restructure to first state the primary finding (e.g., '\method and Self-\method consistently outperform baselines across all five benchmarks'), then list the specific metrics and comparisons.
- **[writing]** Section 4, subsection 'Effect of reward MLLM backbone': The paragraph discussing 'Pretraining-stage MLLMs' starts with a specific result ('Gemma3-12B-Pretrain consistently outperforms...') before explaining the hypothesis. Move the hypothesis sentence ('We hypothesize that pretraining learns...') to the beginning of the paragraph to provide context for the observed result.
