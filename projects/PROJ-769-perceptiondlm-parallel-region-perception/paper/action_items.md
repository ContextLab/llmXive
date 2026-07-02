# Automated-review action items — PerceptionDLM: Parallel Region Perception with Multimodal Diffusion Language Models

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The claim of being the 'first to achieve parallel region caption' (Abstract) is overstated. The authors must distinguish their work from prior non-autoregressive or parallel decoding attempts in vision-language models that may have touched on similar concepts, even if not explicitly for 'region' tasks.
- **[science]** The citation 'gpt5.2' (Section 4) refers to a model version that does not exist in the public domain. Citing a non-existent model as a judge for benchmark evaluation undermines the reproducibility and factual accuracy of the experimental claims. Use a publicly available model or provide a verifiable source.
- **[writing]** The claim that PerceptionDLM-Base 'outperforms LLaDA-V on 15 of 16 benchmarks' (Intro) is technically accurate but misleading without explicitly highlighting the specific benchmark (MMMU) where it fails, as the text implies near-universal superiority.
- **[science]** The citation 'carion2025sam' (Section 3) refers to 'SAM 3', a 2025 arXiv preprint. If this model is not publicly available, the claim that the authors used it to construct the dataset is unverifiable. Clarify the exact version and availability of this tool.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption claims to show 'failure cases' of the model, but the image displays ground-truth segmentation masks (yellow bag, pink flowers) and text descriptions that appear accurate, failing to demonstrate the specific error or hallucination the figure is intended to illustrate.
- **[writing]** Figure 1: The text descriptions for 'Mask 1' and 'Mask 2' are not clearly linked to the visual overlays; the figure lacks arrows, labels, or a layout convention to indicate which text corresponds to which highlighted region.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'AR' (autoregressive) and 'DLM' (diffusion language model) at their first occurrence in the Abstract and Introduction. Currently, 'AR' appears in the abstract without definition, and 'DLM' is used in the intro before being explicitly spelled out as 'Diffusion Language Models' in the Related Work section.
- **[writing]** Replace the acronym 'RoI' (Region of Interest) with the full term 'region of interest' or 'region' on first use in Section 3 (Method) and Section 2 (Related Work). The term is used frequently without prior definition, which may confuse non-specialist readers.
- **[writing]** Define the metric 'TPF' (Tokens Per Forward) in Section 4.2 where it is first introduced. The text states 'we adopt the Tokens Per Forward (TPF) metric' but does not explain what the metric measures or why it is relevant to the parallel decoding claim.
- **[writing]** Replace the acronym 'SFT' (Supervised Fine-Tuning) with the full term 'supervised fine-tuning' in Section 3.1 (Stage 3) and Section 3.2. While common in the field, it is not defined upon first use in the main text.
- **[writing]** Clarify the term 'pixel unshuffle' in Section 3.1. While a standard operation in super-resolution, it is jargon that may be opaque to general readers. Consider adding a brief parenthetical explanation (e.g., 'a downsampling operation that rearranges pixels into channels').

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The claim that PerceptionDLM generates captions 'in a single denoising step' (Conclusion) contradicts the methodology (Eq. 1, Sec 4) which specifies a multi-step Markov process (32 steps). This logical inconsistency misrepresents the inference mechanism.
- **[writing]** The argument that parallel generation 'entirely avoids linear growth' (Fig 1 caption) is logically incomplete. While token-level parallelism is achieved, the total compute still scales with the number of regions (N) due to the fixed number of diffusion steps per region. The claim should be refined to 'sub-linear latency growth' or 'constant latency per region' rather than avoiding linear growth entirely.
- **[science]** The conclusion that 'arbitrary-order parallel decoding fundamentally limits reasoning potential' (Sec 4.1) is asserted without a causal mechanism or internal evidence in the paper. The paper demonstrates efficiency gains but does not logically derive the reasoning limitation from the parallel architecture itself, creating a gap between the premise (parallelism) and the conclusion (reasoning failure).

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of being the 'first to achieve parallel region caption' (Abstract, Intro) is overreaching. Qualify this to 'first to achieve... using diffusion language models' to avoid implying broader novelty not supported by the data.
- **[writing]** The claim that PerceptionDLM 'nearly doubles the performance' of LLaDA-V (62.4% vs 35.2%) on ParaDLC-Bench (Intro, Exp) conflates architectural parallelism with model capability. Clarify that the gap reflects the parallel vs. sequential paradigm difference, not just inherent model quality.
- **[writing]** The statement that 'arbitrary-order parallel decoding fundamentally limits reasoning potential' (Exp, Sec 4.2) is a strong theoretical claim. Ensure this is not overgeneralized from the cited work without specific ablation or analysis supporting this limitation in the authors' own architecture.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The Ethics Statement section is commented out in main.tex (lines 68-75). Given the use of human-centric datasets (Objects365, COCONut) and the generation of detailed descriptions for human/animal regions, an active, explicit ethics statement is required to address potential biases, privacy implications, and the scope of generated content.
- **[writing]** The benchmark construction (ParaDLC-Bench) relies on GPT-5.2 for attribute extraction and question generation. The manuscript must explicitly disclose the specific prompts used (currently only referenced as figures in the appendix) and detail the human-in-the-loop verification process to ensure the evaluation questions do not encode model biases or hallucinations.
- **[writing]** The training data pipeline (ParaCaption-5.7M) utilizes GAR-8B to generate captions for SA-1B and COCONut masks. The authors must clarify the consent status of the source images in these datasets and confirm that the automated generation of detailed descriptions does not violate the original data licenses regarding derivative works or commercial use.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The efficiency claims (3.44x speedup) rely on TPF=2.9 but lack statistical validation. Report mean/std latency over multiple runs and a significance test (e.g., t-test) against the AR baseline to rule out variance or hardware noise.
- **[science]** The ParaDLC-Bench evaluation relies entirely on GPT-5.2 as a judge. While Appendix A shows robustness to Qwen3.5, the primary results lack human verification. Include a human evaluation subset (e.g., 50-100 samples) to validate the LLM judge's correlation with ground truth.
- **[science]** The ablation study in Table 4 (Appendix) shows a catastrophic drop to 1.1% accuracy without region prompting. This extreme sensitivity suggests a potential confounding variable or implementation artifact. Provide a qualitative analysis or error breakdown to confirm the failure mode is strictly due to missing prompts.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The efficiency comparison in Table 2 and Figure 1(b) lacks statistical rigor. The reported 'Time (s)' and 'TPS' are single-point measurements without confidence intervals, standard deviations, or sample sizes (N). Given the stochastic nature of diffusion sampling and hardware variance, a single run is insufficient to claim a '3.44x speedup'. Please report mean and standard deviation over at least 5 independent runs per configuration.
- **[science]** The evaluation metric 'Avg (%)' in Table 2 is derived from an LLM judge (GPT-5.2) without reporting inter-rater reliability or sensitivity analysis. While Appendix Table 4 shows results with different judges, the main text treats the GPT-5.2 score as ground truth. Please include a statistical test (e.g., bootstrap confidence intervals) to demonstrate that the observed performance gap (62.4% vs 35.2%) is statistically significant and not an artifact of the specific judge model's bias.
- **[science]** In the ablation studies (Appendix Tables 3-6), the authors report percentage point differences (e.g., '6.2% drop') but do not provide p-values or effect sizes to determine if these differences are statistically significant. With the large dataset sizes implied (millions of samples), even trivial differences may appear significant, or conversely, small but meaningful improvements may be dismissed. Please add statistical significance testing for all ablation comparisons.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3 (Method), the phrase 'relying on autoregressive (AR) decoding' is used, but the sentence structure in the paragraph beginning 'Despite high accuracy...' is slightly repetitive. Consider varying the sentence structure to improve flow.
- **[writing]** In the Abstract, the sentence 'To the best of our knowledge, we are the first to achieve parallel region caption and perception...' is grammatically slightly awkward. Consider rephrasing to '...parallel region captioning and perception...' for better parallelism.
- **[writing]** In Section 4 (Experiment), the phrase 'official1 checkpoints' appears in the caption of Table 1. This is likely a typo (extra '1') and should be corrected to 'official checkpoints'.
- **[writing]** In the Appendix, the phrase 'The four-stage training setup of PerceptionDLM-Base is listed in~\Cref{tab:traing_params}' contains a typo in the table label name ('traing_params' vs 'training_params'). Ensure consistency with the actual label defined in the LaTeX source.
