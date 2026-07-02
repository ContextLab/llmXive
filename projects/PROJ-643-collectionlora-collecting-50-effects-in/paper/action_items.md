# Automated-review action items — CollectionLoRA: Collecting 50 Effects in 1 LoRA via Multi-Teacher On-Policy Distillation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** DINO Score: The single-task "Base" model achieves a DINO score of 0.611, while the proposed "Ours" method achieves 0.600. The proposed method is actually lower on this standard metric.
- **[writing]** CLIP Score: The scores are nearly identical (0.726 vs 0.727).
- **[writing]** VSA Score: The proposed method does achieve a higher VSA (4.380 vs 4.075). While the authors introduce VSA to address limitations of DINO in stylized scenarios, the blanket statement that the method "surpasses" teachers in fidelity is misleading when a standard metric (DINO) shows a decline. The text should be nuanced to reflect that it surpasses teachers *on the proposed VSA metric* or *in terms of style alignment (CLIP)*, rather than making a general claim of superior fidelity that contradicts
- **[writing]** Evidence: Table 2 (table/deploy_cost.tex) provides data up to 150 LoRAs. At 150 LoRAs, the baseline storage is $2.2G \times 150 = 330G$. The proposed method storage is $2.2G \times 3 = 6.6G$.
- **[writing]** Calculation: $6.6 / 330 = 0.02$ or 2%.
- **[writing]** Discrepancy: The claim of 0.5% is not derived from the storage numbers presented in the table. If the 0.5% figure includes routing latency or other factors, the text must explicitly define the "overhead" metric being used. As written, the claim appears mathematically inconsistent with the provided table data. 3. Exaggeration of "Training Failure" In Section 4.4 (lines 235-238), the authors state that applying vanilla DMD to the multi-teacher setting "causes the student distribution to collapse..
- **[writing]** Evidence: Table 3 (table/ablation.tex), specifically Experiment (1), shows a configuration with PDSR but without the proposed TS and TA-FM components (effectively a baseline DMD approach with routing). This experiment yields a CLIP of 0.725 and a VSA of 2.756.
- **[writing]** Analysis: While the performance is lower than the full method, the model clearly trains and produces results (it does not "fail" in the sense of collapsing to noise or producing no output). The term "training failure" is an overstatement of the empirical evidence, which shows degradation rather than total collapse. The text should be revised to describe this as "significant performance degradation" or "suboptimal convergence" rather than "failure." 4. Citation Context The citations for DMD (dmd1

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 1: The image is a promotional graphic for a '50 in 1 Collection LoRA' product rather than a scientific figure; it lacks axes, data, or methodological context required for a preprint.
- **[science]** Figure 1: The caption describes the figure as a 'PlaceHolder' and defines 'Customized image editing' in a way that does not match the visual content, which is a collage of generated images without explanatory text or labels.
- **[writing]** Figure 2: The figure has no caption provided, making it impossible to understand the context of the 'Bad Case' and 'Good Case' labels or the specific meaning of the DINO and VSA scores shown.
- **[science]** Figure 2: The 'Bad Case' example shows a generated image with a score of DINO: 0.952 and VSA: 0, but without a caption or axis labels, it is unclear what specific metric or comparison is being visualized to support the claim of VSA's superiority over DINO.
- **[fatal]** Figure 6: The rendered image is a qualitative grid of image editing results labeled 'Source Image', 'Exp.(1)' through 'Exp.(5)', and 'Reference Effect', but the caption explicitly states '(no caption)' and the filename 'zip_ablation_compare.pdf' suggests it should be an ablation study; the content does not match the provided caption or the implied figure type.
- **[fatal]** Figure 7: The figure is rendered as a qualitative grid of images (showing cats and dogs in pink houses) but lacks a caption. The filename 'zip_ablation_trainsteps.pdf' implies a quantitative ablation study on training steps, yet the visual content does not match the expected format for such a study, and the missing caption prevents verification of the figure's purpose.
- **[writing]** Figure 8: The caption 'DreamSim Distance' is insufficient; it fails to define the three ablation conditions (Baseline, Baseline + Target Simulation, Baseline + Target Simulation + TA-FM) shown in the legend, making the figure's specific contribution unclear without external context.
- **[fatal]** Figure 9: The caption is explicitly marked '(no caption)' and the filename '[zip_intro.pdf]' suggests this is a placeholder or intro slide rather than a scientific figure. It lacks a descriptive caption explaining the diagram's components (e.g., 'Effect LoRA Bank', 'Query Routing', 'Collection LoRA') or its purpose, making it impossible to interpret the figure's scientific contribution.
- **[writing]** Figure 10: The caption contains a typo in the loss function name, writing '$L_TA-FM$' instead of '$L_{TA-FM}$' to match the label in panel (b).
- **[writing]** Figure 10: The caption text is missing a closing parenthesis after the description of the Effect Stream in section (b).
- **[science]** Figure 11: The caption claims the figure demonstrates the 'Effectiveness of C2F-DO' and compares 'trajectory anchoring' vs 'target simulation', but the image labels only show 'Standard DMD' and 'Reference Effect'. The specific ablation components (C2F-DO, trajectory anchoring, target simulation) are not visually identified in the figure, making the caption's technical claims unverifiable from the visual evidence.
- **[writing]** Figure 11: The caption refers to sub-figures (a) and (b), but the image lacks explicit (a) and (b) labels to distinguish the 'Standard DMD' results from the 'Reference Effect' results.
- **[science]** Figure 12: The 'Source Image' (cat) and 'Target Image' (cat in shorts) are identical in both panels (a) and (b), yet the caption claims panel (a) suffers from 'severe domain deviation' while panel (b) does not. The visual evidence contradicts the claim that the inputs differ in domain deviation; the figure fails to demonstrate the specific heterogeneous setting described.
- **[writing]** Figure 12: The labels 'real' and 'fake' are applied to the intermediate images, but the diagram does not explicitly define which image corresponds to the 'student' or 'teacher' output, relying on the reader to infer the distillation flow from the caption.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript exhibits a high density of domain-specific acronyms and jargon that are frequently introduced without explicit definition, creating barriers for non-specialist readers. In the Introduction (Section 1), the term VLM (Vision-Language Model) is used in the description of the Asymmetric Orthogonal Prompting strategy without being spelled out. Similarly, DMD (Distribution Matching Distillation) is introduced with its full name, but subsequent references to DMD2 and the specific mechani

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Clarify the teacher source for L_DMD_BS in the Effect Stream (Sec 4.4). Is it the base model (like General Stream) or the specific effect teacher? The current text implies it acts as a regularizer but lacks logical precision on the target distribution.
- **[science]** The claim that AOP creates 'orthogonal subspaces' enabling zero-shot composition (Sec 5.2) lacks supporting evidence. Provide empirical proof (e.g., embedding similarity) or remove the causal claim linking orthogonality to the emergent capability.
- **[writing]** The Introduction claims routing latency is 'fundamentally resolved,' yet Sec 5.1 states routing reverts for 100+ LoRAs. Reconcile this contradiction by clarifying the scaling threshold where routing is re-enabled.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Claiming the method 'surpasses independent single-task teachers' (Intro) is unsupported as Table 1 shows the Base model has a higher DINO score (0.611 vs 0.600). Qualify this to specify superiority only in VSA, not all fidelity metrics.
- **[writing]** The 'zero-shot effect composition' claim (Intro) implies generalization to unseen pairs, but Fig. AB_Test only shows composition of two specific trained effects. Restrict the claim to 'composition of trained effects' to avoid over-generalization.
- **[writing]** Stating the framework scales to 180 effects 'without catastrophic quality degradation' (Intro) minimizes the CLIP drop from 0.727 to 0.709. Rephrase to acknowledge the performance trade-off or use 'graceful degradation' instead.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The evaluation protocol relies on the Qwen-VL-Max-Latest API (Appendix, 'Prompt Design for Evaluation') to calculate VSA and BCR metrics. The manuscript must explicitly disclose the data privacy policy regarding the 5,000 test images sent to this external API, confirming whether images are retained for model training or processed in a privacy-preserving manner.
- **[writing]** The 'User Study' section (Supplementary Material) states that 10 professional evaluators were hired. The manuscript must confirm that informed consent was obtained from these participants and that the study protocol was reviewed by an Institutional Review Board (IRB) or equivalent ethics committee, as is standard for human-subject research.
- **[writing]** The 'Asymmetric Orthogonal Prompting' (AOP) strategy uses a VLM to generate student prompts from training data (Sec 4.3). The authors should clarify if the training images used for this prompt generation contain any personally identifiable information (PII) or copyrighted material, and if so, how consent or licensing was handled.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of scaling to 180 effects (Sec 1, Tab 4) lacks statistical rigor. The CLIP score drop from 0.727 (50 effects) to 0.709 (180 effects) is presented as 'competitive' without confidence intervals or significance testing against the baseline. Provide error bars or p-values to substantiate that the degradation is not statistically significant.
- **[science]** The VSA metric relies entirely on a single MLLM (Qwen-VL-Max-Latest) for evaluation (Sec 5.1, App 7). No inter-rater reliability or human validation of this automated metric is provided. Given the high stakes of the 'Bad Case' classification, report a human-in-the-loop validation study on a subset of samples to confirm the MLLM's alignment with human judgment.
- **[science]** The ablation study (Tab 3) shows Exp (3) achieving higher CLIP (0.736) than the full model (0.727), yet the full model is claimed as optimal. The text attributes this to 'stability' but does not provide a statistical test or a multi-run average to prove the full model's performance is not a result of random variance or overfitting to the specific test set.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The VSA metric relies on an MLLM (Qwen-VL-Max) for scoring. The manuscript lacks statistical validation of this evaluator's reliability (e.g., inter-rater agreement with human judges or consistency across multiple MLLM calls). Without confidence intervals or error bounds for these MLLM-derived scores, the reported improvements (e.g., VSA 4.380 vs 4.150) cannot be statistically distinguished from evaluator noise.
- **[science]** The ablation study (Table 4) presents single-point metric values without measures of variance (standard deviation) or statistical significance testing (e.g., t-tests or ANOVA). Given the stochastic nature of diffusion training and the small number of ablation runs implied, it is unclear if the observed differences (e.g., CLIP 0.736 vs 0.727) are statistically significant or due to random initialization variance.
- **[science]** The user study (Appendix) reports preference percentages (e.g., 66.2% for Consistency) based on 50 samples and 10 evaluators but omits confidence intervals or binomial test results. The statistical power of this sample size to detect meaningful differences between methods is not addressed, making the claim of 'significant' superiority statistically weak.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Abstract, correct the phrase 'numerous these effect LoRAs' to 'these numerous effect LoRAs' for proper syntax.
- **[writing]** In Section 4.3, remove the trailing space in the title 'Asymmetric Orthogonal Prompting }' to fix formatting.
- **[writing]** In Section 4.4, improve the transition between the definition of Target Simulation and its implementation description to enhance flow.
- **[writing]** In the Introduction, change 'an zero-shot effect composition' to 'a zero-shot effect composition' to correct the article usage.
- **[writing]** In Section 1, explicitly state the basis for the '0.5%' deployment overhead claim in the text to clarify the calculation for readers.
