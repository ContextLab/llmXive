# Automated-review action items — FashionChameleon: Towards Real-Time and Interactive Human-Garment Video Customization

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** $23.8 / 0.77 \approx 31x$ While the calculated range (31x to 183x) roughly aligns with the "30-180x" claim, the upper bound is slightly exceeded. More importantly, the claim relies on the specific baselines listed. If the "180x" figure was derived from a baseline not included in Table 1 (e.g., a slower configuration or a different resolution), the claim is misleading without context. The authors should ensure the range strictly reflects the data presented in Table 1 or explicitly state which bas

## paper_reviewer_code_quality_paper — verdict: minor_revision

- **[science]** The manuscript references a 'High-Quality Data Curation Pipeline' (Sec 3.4) and 'Training Details' (Appendix) but provides no code artifacts, repository links, or data processing scripts. Without the actual implementation of the 4-stage pipeline (filtering, captioning, extraction, construction) and the training loops, the reproducibility of the 62K dataset and the 23.8 FPS claim cannot be verified.
- **[science]** The paper claims 'real-time' generation at 23.8 FPS on an H200 GPU (Table 1), yet the experimental setup lacks a `requirements.txt`, `Dockerfile`, or specific environment configuration (e.g., CUDA version, specific Wan2.2 checkpoint hash). The 'Training-Free KV Cache Rescheduling' logic is described mathematically but not provided as executable code, making independent verification of the inference speed impossible.
- **[science]** The 'HGC-Bench' benchmark is described as containing 240 samples with specific prompts (Appendix), but the dataset files (images, prompts, ground truth) are not included in the provided artifacts. Reproducibility requires the actual data files or a script to generate them, not just the prompt text.

## paper_reviewer_data_quality_paper — verdict: minor_revision

- **[science]** The paper claims to use a curated dataset of 62K triplets (Appendix, Sec. Data Curation Pipeline Details) but provides no license information, source URLs, or provenance for the raw video collection. Without explicit licensing (e.g., CC-BY, fair use justification) and source attribution, the dataset cannot be legally or ethically reused, violating standard data quality requirements for reproducibility.
- **[science]** The HGC-Bench benchmark (240 samples) is described as curated from the Internet with face swapping for anonymization (Appendix, Sec. HGC-Bench Details). The paper fails to specify the license of the source images used for the benchmark or the legal basis for the face-swapping operation. This creates a significant legal risk and prevents independent verification of the benchmark's composition.
- **[writing]** The data curation pipeline relies on external APIs (Gemini-3.0/3.1, Q-Align, UniMatch) for filtering and captioning (Appendix, Sec. Data Curation Pipeline Details). The paper does not document the specific API versions, rate limits, or terms of service compliance for these external services. If these services change or become unavailable, the data pipeline becomes non-reproducible.
- **[writing]** The paper mentions "manual verification" retaining 62K of 82K triplets (Appendix, Sec. Data Curation Pipeline Details) but provides no details on the verification protocol, inter-annotator agreement, or the specific criteria used for rejection. This lack of transparency in the data cleaning process undermines the reliability of the training data quality claims.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** Figure 1 (teaser.pdf) and Figure 2 (intro.pdf) lack explicit axis labels and units where quantitative data is presented. Specifically, Figure 2 compares performance metrics (Cur., GME, etc.) and FPS but does not define the units or scales on the axes, making it difficult to interpret the magnitude of differences at print resolution.
- **[writing]** The color palette in Table 1 (main_results) and Figure 2 (intro.pdf) relies heavily on grayscale and standard blue/red. For print accessibility, ensure that the distinction between 'best' (bold) and 'second best' (underlined) is not solely dependent on color or font weight, as these may be lost in black-and-white printing. Consider adding distinct patterns or markers for data points in Figure 2.
- **[writing]** Figure 3 (analysis.pdf) contains attention visualization heatmaps. The colorbar for the attention weights is missing or illegible in the provided source context. Ensure the colorbar includes a clear label (e.g., 'Attention Weight'), a numerical scale, and a distinct colormap that is perceptually uniform and accessible to colorblind readers.
- **[writing]** Figure 4 (qualitative.pdf) and subsequent qualitative figures (app.pdf, ablation.pdf) are referenced as 'omitting prompts' in captions. While acceptable for space, the figure captions should explicitly state the resolution of the displayed frames (e.g., 720p) and the specific garment switching timestamps if applicable, to ensure the visual evidence is self-contained and reproducible without reading the full text.

## paper_reviewer_jargon_police — verdict: full_revision

- **[science]** The manuscript suffers from significant jargon overuse, creating a barrier for non-specialist readers and even experts in adjacent fields. The Abstract introduces a dense cluster of undefined acronyms and compound technical terms. Specifically, "Teacher Model with In-Context Learning," "Streaming Distillation with In-Context Learning," and "Training-Free KV Cache Rescheduling" are presented as proper nouns without explaining the underlying mechanics in plain language. The term "KV Cache" (and it

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The logical consistency of the paper's core claims requires clarification in three areas. First, in Section 3.1, the authors claim that training a teacher model on a single reference-garment pair with a *mismatch* (where the reference person wears a different garment than the target) implicitly enables the model to learn "single-garment switching." The logical leap here is significant: the paper does not provide a mechanism explaining how a model trained on *one* specific mismatched pair can gen

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper makes several claims that extrapolate beyond the provided evidence or lack necessary context, specifically regarding performance metrics, novelty, and the scope of "long-video" capabilities. First, the efficiency claims in the Abstract and Introduction ("30-180x faster," "real-time generation at 23.8 FPS") are heavily dependent on the specific hardware used (H200 GPU) and the architectural difference between the proposed autoregressive method and the bidirectional baselines. Table 1 sh

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper addresses safety and ethics primarily through a dedicated "Potential Negative Societal Impact" section in the Appendix. While the authors correctly identify risks such as the generation of sexually explicit content, reinforcement of stereotypes, and the creation of misleading advertisements (Appendix, "Potential Negative Societal Impact"), the discussion remains high-level. The manuscript lists these risks but fails to propose specific, actionable mitigation strategies or technical saf

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of 23.8 FPS on an H200 GPU (Table 1) lacks necessary context regarding batch size, resolution, and chunk size. The baseline comparisons (0.13-0.77 FPS) do not specify if they were run under identical hardware or configuration constraints. Re-run baselines on the same H200 with identical settings or explicitly state the hardware differences to validate the 30-180x speedup claim.
- **[science]** The garment consistency metrics (HGC, LGC, NTP) rely entirely on Gemini-3.0 scoring (Appendix). No inter-rater reliability, human correlation study, or ground-truth validation is provided for this LLM-as-a-judge approach. Without a correlation coefficient against human annotations, the quantitative superiority claims in Table 1 are scientifically weak.
- **[science]** The ablation study for Gradient-Reweighted DMD (Table 2) shows a significant drop in Amplitude (0.8395 vs 0.5106) when changing tau from 0.2 to 0.3, yet the text only claims 'best overall performance' without statistical significance testing or error bars. Provide standard deviations over multiple seeds to confirm these differences are not due to random variance.
- **[science]** The dataset size (62K triplets) is not compared against the scale of training data used by the baselines (e.g., VACE, Kaleido). If baselines were trained on significantly larger datasets, the performance gap might be attributed to data scale rather than the proposed architecture. Clarify the data scale of all baselines.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The evaluation of garment consistency relies entirely on Gemini-3.0 (a VLM) without reporting inter-rater reliability (e.g., Cohen's Kappa) or confidence intervals. Given the subjective nature of 'high-level' and 'low-level' consistency, statistical validation of the metric's reliability is required to support the quantitative claims in Table 1.
- **[science]** The ablation study in Table 2 (GR-DMD) reports single-point performance metrics for different temperature coefficients ($\tau$) without indicating variance across multiple seeds or runs. To claim $\tau=0.2$ is optimal, the authors must provide standard deviations or statistical significance tests (e.g., t-tests) to rule out random fluctuation.
- **[writing]** The FPS metric (23.8 FPS) is reported as a single value. For reproducibility and statistical robustness, the authors should report the mean and standard deviation of inference time over a sufficient number of samples (e.g., n=50) rather than a single point estimate.

## paper_reviewer_text_formatting — verdict: minor_revision

- **[writing]** In main.tex, the \captionof{figure} command is used inside a center environment without a floating figure environment. This is syntactically valid but semantically incorrect for standard LaTeX workflows and may cause caption numbering or placement issues. It should be wrapped in a proper figure environment or the caption command adjusted.
- **[writing]** In sections/3-method.tex, the label for the third contribution is formatted as 'Sec.,~\ref{sec:3-3}' (line 14). The comma before the tilde is a typo and should be removed to match the style of the previous two references ('Sec.\,\ref{...}').
- **[writing]** In sections/4-exp.tex, Table 1 (tab:main_results) uses \rowcolor{gray!25} for the method row. Ensure the 'table' option is passed to xcolor (which it is in main.tex), but verify that the gray color definition does not conflict with the 'taobaocolor' or 'xmucolor' definitions if the document is compiled with specific color constraints.
- **[writing]** In sections/X-suppl.tex, the system prompts for VLMs are enclosed in tcolorbox environments. The text inside uses double backslashes (\\) for line breaks. While functional, ensure these do not cause excessive vertical spacing or overflow in the final PDF layout, especially given the long prompt text.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Abstract and Introduction, the phrase 'switch garment' should be corrected to 'switch garments' (plural) for grammatical agreement. This appears multiple times (e.g., Abstract line 12, Intro line 34).
- **[writing]** In Section 3.3, the sentence 'we replace the old KV^gar in the cache with new new KV^gar_2' contains a typo ('new new'). Please correct to 'a new KV^gar_2'.
- **[writing]** In Section 3.3, the phrase 'Recall that we deliberately I2V property' is missing a verb. It should read 'Recall that we deliberately retained the I2V property' or similar.
- **[writing]** In Section 3.3, 'streaming eneration' is a typo for 'streaming generation'.
- **[writing]** In Section 3.1, the sentence 'These shared projection matrices enables global interaction' has a subject-verb agreement error. 'Matrices' is plural, so it should be 'enable'.
- **[writing]** In Section 4, the caption for Table 1 states 'The best results are highlighted in bold and the second best are underlined.' However, the table uses 'underline' for some second-best values and 'bold' for others inconsistently in the text description vs visual representation. Ensure the text description matches the visual style exactly.
