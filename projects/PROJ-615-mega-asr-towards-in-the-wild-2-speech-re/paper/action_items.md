# Automated-review action items — Mega-ASR: Towards In-the-wild^2 Speech Recognition via Scaling up Real-world Acoustic Simulation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 4.2 (DG-WGPO), the text states the WER-gated threshold is set to τ=0.3, but Table 3 (tab:dg_wgpo_reward_hparams) in the Appendix lists τ=0.5. This contradiction must be resolved to ensure the reported hyperparameters match the experimental setup.
- **[writing]** The abstract and Section 3 claim the dataset covers '7 classic acoustic phenomena,' yet Table 1 (tab:primitive_effects) in the Appendix lists '8 primitive effects' before aggregation. Clarify whether one effect was merged or excluded to ensure the count of 7 is accurate and consistent with the simulation pipeline.
- **[writing]** Section 4.2 claims that errors shift 'abruptly' at WER > 30%, justifying the gated reward. However, the ablation study in Table 2 (tab:hp-tau) shows only a marginal WER difference (7.68 vs 7.64) between τ=0.2 and τ=0.3. The text should temper the claim of an 'abrupt' shift or provide stronger evidence that the 30% threshold is the critical inflection point.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The left radar chart's radial axis is labeled '100' at the outermost ring, but the data points for 'CommonVoice22' (6.97) and 'Voxpopuli' (6.25) are plotted near the 80% mark, implying the axis represents a percentage scale (0-100%) while the labels suggest absolute values or a different metric. This creates a severe visual distortion where low scores appear high.
- **[writing]** Figure 1: The legend at the bottom is cut off on the left side, making the full name of the blue line ('Qwen3-ASR-1.7B(Previous SOTA)') partially illegible.
- **[science]** Figure 3: The right panel's y-axis (0.45–0.65) is unlabeled, making it impossible to interpret the 'comparison of difficulty sampling distributions' claimed in the caption.
- **[science]** Figure 3: The right panel legend lists four sampling methods (Gaussian, Linear, Sqrt-Bwd, Sqrt-Fwd), but the caption does not define these terms or link them to the left panel’s 'atomic effects'.
- **[writing]** Figure 3: Left panel subplots lack individual y-axis labels; while '1 - WER' is shown on the first subplot, it is not repeated or clarified for the other seven, risking misinterpretation.
- **[fatal]** Figure 4: The caption is a placeholder ('Enter Caption [figure3.pdf]') and does not describe the figure content, making it impossible to verify if the figure supports its claims.
- **[fatal]** Figure 4: The filename in the caption ('figure3.pdf') contradicts the figure label ('Figure 4'), indicating a likely copy-paste error or mislabeling.
- **[science]** Figure 4: The diagram contains undefined abbreviations and symbols (e.g., 'q', 'O1', 'R1', 'A1', 'WER', 'LCS') without a legend or explanation in the caption.
- **[science]** Figure 5: The caption describes the framework as 'DG-WGPO', but the diagram explicitly labels the initialization stage as 'A2S-SFT' and the core mechanism as 'Recov-Recon Dynamic Reward' without ever mentioning 'DG-WGPO' or 'gated fusion' in the visual elements, creating a disconnect between the text and the figure content.
- **[writing]** Figure 5: The 'Word-level Reward' box contains a formula for 'n_recal' that is illegible due to low resolution; the subscripts and specific terms in the fraction cannot be read.
- **[fatal]** Figure 6: The caption is 'Enter Caption [figure3.pdf]', indicating a placeholder error where the figure content (likely a pipeline diagram) does not match the assigned caption file or text.
- **[science]** Figure 6: The diagram displays a complex 'Recov-Recon Dynamic Reward' framework with specific components like 'A2S-SFT' and 'Mega-ASR', but the missing caption fails to define these terms or explain the workflow, rendering the figure unintelligible without external context.
- **[science]** Figure 7: The 'WER' (Word Error Rate) for the Ground Truth row is labeled as '--', which is technically incorrect as the WER of a reference against itself is 0.0%. This creates a confusing baseline for the comparison.
- **[writing]** Figure 7: The WER for the 'Qwen3-ASR' model in the 'Far field' case is listed as 100.0% for an '<Empty>' output. While understandable, WER is typically undefined or requires a specific convention for empty predictions; a note or alternative metric (like 'Empty Output') would be clearer.
- **[writing]** Figure 7: The 'Entity Recovery' case shows a WER of 14.3% for Mega-ASR, yet the text output appears to match the Ground Truth exactly (ignoring capitalization). If the WER is non-zero, the text should reflect the specific error (e.g., 'VictorNet' vs 'Victor Company'), or the WER should be 0.0%.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology and acronyms that are not defined for a broader audience, creating a barrier to entry for non-specialist readers. First, several acronyms are introduced without expansion. "LALMs" (Large Audio-Language Models) appears in the Introduction without being spelled out. "WER" (Word Error Rate) is used frequently in the Abstract and Introduction but is never explicitly defined. "LoRA" (Low-Rank Adaptation) is mentioned in the context of the route

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Inconsistent WER gate threshold: Section 4.2.2 defines the WER-gated fusion threshold as τ=0.3, but Appendix Table 4 (Reward hyperparameters) and the text in Appendix Section 'Reward tuning and diagnostics' state τ=0.5. This contradiction undermines the reproducibility of the DG-WGPO mechanism.
- **[science]** Contradictory generation counts: Section 5.1 'Implementation Details' states K=16 rollouts per input, while Appendix Table 3 (DG-WGPO generation hyperparameters) lists 'Number of generations' as 12. The effective batch size calculation in the same table (4x3x16=192) also conflicts with the stated 12 generations.
- **[writing]** Inconsistent hyperparameter reporting: Section 4.2.2 sets α_dyn=0.6 and α_s=0.4, which matches Table 4, but the text in Appendix 'Reward tuning and diagnostics' repeats these values while the table caption for Table 4 lists 'Low-WER fusion' as 0.75/0.25 and 'High-WER fusion' as 0.25/0.75, which is consistent, but the text in Section 4.2.2 does not explicitly define the fusion weights, only the threshold logic, creating ambiguity in the exact formula application.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of 'over 30% relative WER reduction' in the abstract and conclusion is not universally supported by the provided tables. Table 1 shows a 17.4% reduction on NOIZEUS 0dB and ~15-20% on other subsets. The '30%' figure likely applies only to specific compound scenarios in Voices-in-the-Wild-Bench (Table 3), but the text generalizes this to 'complex compositional acoustic scenarios' without explicit qualification, risking over-claiming on general benchmarks.
- **[science]** The paper claims the dataset covers '54 physically plausible compound scenarios' verified by an 'agentic check' (Section 3). However, the methodology for this 'agentic check' is not described, nor is the failure rate or criteria for 'physical plausibility' defined. Without this evidence, the claim of physical plausibility for all 54 scenarios is an unsupported extrapolation.
- **[writing]** The abstract states the model achieves 'human-level performance' on canonical benchmarks, yet Table 2 shows WERs of 1.63-3.57 on LibriSpeech. While low, 'human-level' is a strong claim that typically requires comparison to human transcription error rates (often cited as ~5% for difficult speech, but <1% for clean). The paper does not provide this specific human baseline comparison to justify the 'human-level' terminology.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[fatal]** The paper states the evaluation benchmark includes '1,500 real-world recordings collected from internet sources and 16 human participants' (Section 3.3) but lacks explicit details on IRB approval, informed consent procedures, or data privacy safeguards for these participants. This is a critical ethical gap for human-subject research.
- **[science]** The dataset construction relies on 'clean speech from LibriSpeech, Common Voice, WenetSpeech, and AISHELL-1' (Section 3.2). The authors must explicitly confirm that the licensing terms of these source datasets permit the creation of a new, derivative synthetic dataset ('Voices-in-the-Wild-2M') and its public release, including any restrictions on commercial use or redistribution.
- **[writing]** The methodology involves generating '54 physically plausible compound scenarios' including 'electronic distortion' and 'transmission dropout' (Section 3.2). While intended for robustness, the authors should briefly discuss potential dual-use risks, such as the possibility of these simulation techniques being adapted to generate adversarial audio attacks or deepfake audio that evades detection systems.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The paper claims a 30% relative WER reduction on compositional scenarios but does not report confidence intervals or statistical significance tests (e.g., bootstrap or paired t-tests) for these gains. Given the high variance in WER across different acoustic conditions, statistical validation is required to confirm the robustness of the reported improvements.
- **[science]** The 'Voices-in-the-wild-2M' dataset is entirely synthetic, generated via spectral manipulation. The paper lacks a rigorous cross-validation experiment demonstrating that performance gains on this synthetic benchmark transfer to a held-out, purely real-world dataset not used in any training or validation step. Without this, the claim of 'in-the-wild' robustness is partially unverified.
- **[science]** The ablation study (Table 4) shows that removing the sentence-level structural reward ($R_{struc}$) causes the largest degradation. However, the paper does not provide a sensitivity analysis on the specific threshold $	au=0.3$ used for the WER-gated fusion. A small shift in this threshold could significantly alter the balance between token-level and sentence-level rewards, yet the robustness of this hyperparameter choice is not fully explored.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The paper reports specific WER values (e.g., 19.80 vs 23.97 in Table 1) but lacks statistical significance testing (e.g., paired t-tests or bootstrap confidence intervals) to confirm these improvements are not due to random variance, especially given the stochastic nature of RL training.
- **[science]** The WER-gated threshold $\tau$ is set to 0.3 in the main text (Section 4.2) but listed as 0.5 in Table 6 (Appendix). This inconsistency in a critical hyperparameter governing the reward fusion strategy must be resolved and justified.
- **[science]** The ablation study in Table 3 compares rule-based vs. LLM-judge rewards based on a single run's WER and time cost. It lacks variance estimates (e.g., standard deviation over multiple seeds) to validate the claim that performance is 'comparable' within ~0.1 WER.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.1, the phrase 'between	extbf{ 4\%--10\%}' contains a missing space before the bold command and inconsistent punctuation. It should be 'between 4\%--10\%' or 'between 4\% and 10\%'. Additionally, the bolding of the numbers within the sentence flow is stylistically inconsistent with the rest of the manuscript.
- **[writing]** Section 4.1 contains a sentence fragment: 'instilling perceptual robustness and semantic recovery.' This phrase lacks a main verb and is grammatically disconnected from the preceding clause. It should be integrated into the sentence (e.g., '...via ..., instilling...') or rewritten as a complete sentence.
- **[writing]** In Section 4.2, the text states 'We observe during training that errors when $	ext{WER}{<=}30\%$...' The use of the symbol '<=' is informal for a research paper; it should be written as '$\leq$' or 'less than or equal to'. Furthermore, the sentence structure is slightly clunky and could be smoothed for better flow.
- **[writing]** Throughout the manuscript, there are inconsistent capitalizations in section titles and figure captions (e.g., 'Voices-in-the-wild-2M' vs 'Voices-in-the-Wild-2M'). The dataset name should be consistently capitalized (likely 'Voices-in-the-Wild-2M') to maintain professional polish and readability.
