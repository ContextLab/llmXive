# Automated-review action items — Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Models

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 3.1, the claim that inference is 'driven entirely by the model's per-position output distribution' contradicts the deterministic argmax used for the 'Reveal' action in Eq. 1. Clarify that the decision to reveal is probabilistic, but the token selection is deterministic.
- **[writing]** In Section 4.3, the claim that MATH500 'focuses primarily on the final answer' is used to explain lower gains. Explicitly confirm the benchmark evaluates only the final answer, as the method targets intermediate CoT steps which might otherwise be penalized in other protocols.
- **[writing]** In Section 4.3, the attribution of larger MBPP gains to 'a greater number of token-level errors' is a hypothesis. The paper lacks data on error density or correction counts. Qualify this as a likely explanation rather than a proven fact.
- **[writing]** In Section 4.2, the text claims the decay variant 'improves over the no-history baseline' (89.4% vs 82.4%). While numerically true, the phrasing is dense. Ensure the comparison clearly distinguishes between the 'decay-only' and 'HR-only' ablations to avoid confusion.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The 'Predict Mask(Ours)' row displays red overlays on the original images, but the caption does not define this visualization method or explain that red indicates the predicted mask area.
- **[writing]** Figure 1: The column headers in the top section (e.g., 'Predict Mask(Ours)', 'Ours', 'Lumina') are not explicitly defined in the caption, leaving the reader to infer that these represent different model outputs.
- **[writing]** Figure 2: The caption states 'The masks predicted by are highlighted in red,' which contains a grammatical error and missing subject (likely 'by our model').
- **[writing]** Figure 2: The caption claims 'Heat maps at the bottom visualize pixel-wise differences,' but the figure displays a grid of qualitative image editing results without any heat maps.
- **[science]** Figure 2: The column labeled 'Predict Mask(Ours)' shows red overlays, but the caption's claim about heat maps visualizing pixel-wise differences is not supported by the visual content shown.
- **[science]** Figure 3: The 'History construction rules' panel shows a 'Wrong' sequence starting with w0, but the diagram below it shows the 'Current Step' sequence starting with '2' (a correct token), creating a disconnect between the rule definition and the application example.
- **[writing]** Figure 3: The legend at the bottom left defines 'Noisy' as a dashed box, but the 'Sample wrong' section uses solid orange boxes for wrong tokens without explicitly linking them to the 'Wrong' legend entry (solid orange box) in a way that clarifies the transition from 'Noisy' to 'Wrong'.
- **[science]** Figure 4: The figure displays mathematical problem-solving steps (Cases 1-5) rather than 'text generation' results, contradicting the caption's claim.
- **[science]** Figure 4: The figure lacks a descriptive caption explaining the specific tasks, the model's performance, or the meaning of the red/green markers, making it impossible to interpret the 'qualitative results'.
- **[writing]** Figure 5: The caption begins with a lowercase verb ('actively re-masks...') and lacks a subject, failing to identify the model or method being illustrated.
- **[science]** Figure 5: The mathematical problem shown at the top is a linear inequality, but the solution steps display 'M' tokens and arithmetic operations that do not correspond to standard algebraic solving methods for inequalities.
- **[writing]** Figure 5: The 'Step' labels (45, 115, 135, 138, 139) are non-sequential and arbitrary, making it difficult to follow the chronological progression of the reasoning process.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on field-specific acronyms and shorthand that are not consistently defined at their first occurrence, creating barriers for non-specialist readers. In the Abstract, 'MDM' and 'AR' are used immediately without expansion. While 'Mask Diffusion Models' and 'autoregressive' appear in the Introduction, the Abstract should be self-contained. Similarly, 'SFT' is used in Section 5.1 without definition, and 'CoT' appears in Section 5.3 without the full phrase 'Chain-of-Thoug

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Section 3.1 claims the deterministic inference rule causes loops, and Section 3.2 asserts History Reference fixes this by changing input. However, the paper does not logically prove that the new input distribution breaks the fixed-point cycle, only that it 'addresses' it. A formal argument or empirical proof of termination is missing.
- **[science]** Appendix A.1 (Theorem 1) assumes a 'rich-family' model class to prove convergence to the oracle distribution. The experiments use finite-capacity models (e.g., 0.81M params). The paper fails to logically bridge the gap between the infinite-capacity theoretical guarantee and the empirical performance of the specific small models used.
- **[writing]** In Section 4.2, the ablation distinguishes between 'History Reference' and 'decay', yet Eq. 2 defines the mechanism inherently with decay. The claim that 'decay alone' performs worse is logically ambiguous because the mechanism definition includes decay. The distinction between the mechanism structure and the decay parameter needs clarification.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that RM provides 'native test-time scaling' (Abstract, Intro) is overreaching. The paper demonstrates performance gains with fixed T=6 steps (Appendix A.3) but does not empirically show that increasing T (scaling compute) yields monotonic improvements or converges to a better solution compared to baselines. This needs explicit scaling curves to justify the 'scaling' terminology.
- **[writing]** The assertion that the method 'elicits reasoning' (Title, Abstract) is too strong for the Sudoku and text results. The improvements on MATH500 are marginal (+2.4%) and the method relies on oracle-labeled synthetic data (Eq. 3) that explicitly teaches the model to correct known errors. This demonstrates learning a correction policy, not necessarily emergent reasoning capabilities beyond the training distribution.
- **[writing]** The claim that History Reference is 'parameter-free' (Abstract, Intro) is technically true regarding learnable weights but overstates the efficiency. The method requires maintaining and updating an accumulated embedding vector $a_i^{(t)}$ for every position at every step, which increases memory bandwidth and compute overhead compared to standard MDM inference. The paper should clarify this trade-off rather than implying zero cost.

## paper_reviewer_safety_ethics — verdict: accept

The manuscript presents a novel method for enabling reflective reasoning in Mask Diffusion Models (MDMs) through a lightweight post-training paradigm. From a safety and ethics perspective, the work does not raise immediate red flags regarding dual-use risks, data privacy violations, or the generation of harmful content.

The training methodology relies on synthetic data construction (Section 3.3, Fig. 2) where "wrong tokens" are sampled from a corruption distribution $\nu$. The authors explicitly state in Appendix A.5 that for text generation, this distribution is derived from a frozen, pre-trained checkpoint's top-$k$ predictions, excluding the ground truth. This approach avoids the need to scrape or utilize private, sensitive, or potentially harmful datasets for the specific purpose of training the revision mechanism. The use of standard, public benchmarks (MATH, MBPP, ARC-Challenge, ImgEdit) for evaluation further mitigates concerns regarding data privacy and consent, as these datasets are widely accepted in the research community and typically have established usage licenses.

The proposed "Reflective Masking" mechanism allows models to iteratively revise their own outputs. While this capability could theoretically be used to refine harmful outputs (e.g., making a generated hate speech more coherent or a malicious code snippet more functional), the paper frames this as a general reasoning primitive for error correction in tasks like math and code synthesis. The authors do not claim to optimize for adversarial robustness or jailbreak resistance, nor do they demonstrate the method's ability to bypass safety filters. The "Limitations" section (Section 6) appropriately acknowledges that the current base models have limited reasoning capabilities, suggesting that the method is not yet a powerful tool for sophisticated adversarial attacks.

There are no indications of conflicts of interest, and the authors do not appear to be using human subjects in a way that would require IRB approval, as the evaluation is purely algorithmic on public benchmarks. The "User Study" mentioned in Table 1 (Image Editing) involves 29 participants evaluating image quality; while the paper does not detail the IRB approval for this specific study, it is a standard practice in computer vision to use small-scale user studies for preference ranking without full IRB oversight, provided no sensitive data is collected. Given the context of a preprint on a public archive, this is acceptable, though a brief statement on ethical approval for the user study in the final version would be a minor best practice.

Overall, the paper adheres to standard ethical guidelines for AI research. The method is a technical improvement on model architecture and training dynamics rather than a tool designed to exploit or harm. No action items are required from a safety and ethics standpoint.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The Sudoku ablation (Table 2) shows a performance drop when adding decay without HER (89.4% vs 91.4%). The text attributes this to 'insufficient' signal weakening, but does not rule out that the decay hyperparameter was simply suboptimal for that specific configuration. Report a sensitivity analysis or grid search over decay factors for the 'HR+decay' variant to confirm the drop is structural, not tuning-related.
- **[science]** The text generation results (Table 3) show a +8.8% gain on MBPP but only +2.4% on MATH500. The authors attribute this to token count differences, but do not provide statistical significance testing (e.g., bootstrap confidence intervals) to confirm these gains are not due to variance in the evaluation set, especially given the small delta on MATH500.
- **[science]** The image editing user study (Table 1) reports a score of 68.2 vs 53.3 for the baseline with 29 participants. The paper lacks details on the study protocol (e.g., randomization, blinding, number of samples per participant) required to assess the robustness of this statistical claim against selection bias or order effects.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** In Section 4.1 (Image Editing), the user study involves 29 participants but lacks statistical reporting. Please report confidence intervals (e.g., 95% CI) for the mean preference scores and specify the statistical test used to determine significance against baselines (e.g., paired t-test or Wilcoxon signed-rank), including p-values.
- **[science]** In Section 4.2 (Sudoku), Table 2 reports performance improvements (e.g., +9.0% Exact Accuracy) without indicating statistical significance. Given the ablation study nature, please report standard deviations or confidence intervals across multiple random seeds to confirm these gains are not due to variance.
- **[science]** In Section 4.3 (Text Reasoning), Table 3 and Table 4 show performance gains on MATH500 and MBPP. The paper does not mention the number of random seeds used for these benchmarks or provide error bars. Please clarify the experimental variance and add statistical significance tests (e.g., bootstrap CIs) to support the claimed improvements.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.1 (Eq. 1), the text states 'model can produce' but should be 'the model can produce' for grammatical correctness. Additionally, the phrase 'driven entirely by the model's per-position output distribution' is slightly redundant; consider 'driven by the model's per-position output distribution'.
- **[writing]** In Section 3.2, the sentence 'The current state contributes unrotated, while each past state is added with a lag-dependent rotation R_Δ and decay γ^|Δ|' is grammatically sound but slightly dense. Consider splitting or clarifying 'lag-dependent rotation' to ensure the reader immediately grasps the mechanism without re-reading.
- **[writing]** In Section 4.1, the phrase 'The brighter regions in pixel-wise difference heat maps indicates larger pixel change' contains a subject-verb agreement error: 'regions' (plural) should match 'indicate' (plural), not 'indicates'.
- **[writing]** In Section 4.2, the sentence 'However, introducing a decay factor alone still improves over the no-history baseline but performs worse than the HR-only variant' is slightly clunky. Consider rephrasing to 'However, introducing a decay factor alone improves over the no-history baseline but performs worse than the HR-only variant' to remove the redundant 'still' and improve flow.
