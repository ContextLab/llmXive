# Automated-review action items — DreamX-World 1.0: A General-Purpose Interactive World Model

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 3.1 (Camera-Aware Training), the text claims E-PRoPE reduces inference latency by 'approximately 30%' and training time by '50%'. Table 1 shows latency dropping from 80s to 59s (a 26.25% reduction). The text overstates the empirical result. Please align the claim with the table data or clarify the specific conditions under which the 30% figure was derived.
- **[science]** In Section 5.1 (Basic Evaluation), the text states the camera control error is computed as the geometric mean of rotation and translation errors, then normalized. However, the text does not specify the empirical bounds used for normalization to [0,1]. Without these bounds, the claim that 'higher scores indicate better adherence' and the specific score of 73.75 cannot be independently verified or reproduced.
- **[writing]** In Section 5.3 (Memory Evaluation), the paper claims to use 'MutualVPR' for place recognition. The bibliography lists 'MutualVPR' (gu2026mutualvpr) as a NeurIPS 2026 paper. Given the current date context (June 2026 in the paper), this is a future-dated citation. If this is a preprint, the citation should reflect its preprint status (e.g., arXiv) rather than a future conference proceeding, to ensure factual accuracy regarding the source's availability.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 2: The diagram depicts the 'Long-video Autoregressive Model' (student) receiving inputs from 'E-PRoPE' and 'LoRA' blocks, but the caption describes distillation from a 'bidirectional E-PRoPE teacher'. The figure fails to visually represent the 'teacher' model or the specific distillation supervision signal (DMD Loss) connecting the teacher to the student, making the mechanism described in the caption invisible.
- **[writing]** Figure 2: The fire emoji (🔥) and snowflake emoji (❄️) are used as labels for 'LoRA' and 'E-PRoPE' components respectively, but there is no legend or caption text defining what these symbols signify (e.g., frozen vs. trainable parameters), rendering them ambiguous.
- **[writing]** Figure 3: The caption contains a grammatical error ('Qualitative results of .') where the model name is missing, and the image itself lacks any internal labels or row headers to identify the specific scene types mentioned.
- **[writing]** Figure 4: The caption contains raw LaTeX formatting artifacts (e.g., '%', '$$3', 'blueblue', 'redred') that should be cleaned for readability.
- **[writing]** Figure 4: The caption text for subfigure (b) lists a sequence of letters (W$$S$$L$$R$$R$$L$$L) that does not match the visual labels in the plot (S, W, L, R) or the 'Translation-Rotation' title.
- **[writing]** Figure 5: The caption contains multiple grammatical errors and missing subjects (e.g., 'comparing with...', 'perspective of under...', 'is preferred in...'), making it unclear which model is the subject of the study.
- **[writing]** Figure 5: The labels 'HY-WorldPlay' and 'LingBot-World' appear on the right side of the bars, but the caption does not explicitly state that these represent the comparison baselines against the primary model.
- **[science]** Figure 6: The diagram depicts a 'History KV cache' feeding into the 'Denoising' block, but the caption describes 'chunk-relative camera controls' without explaining how the camera pose inputs (shown at the top) interact with the denoising process or the KV cache.
- **[writing]** Figure 6: The text labels 'History KV cache' and 'Denoising' are rotated 90 degrees, making them difficult to read and visually cluttered compared to the horizontal text.
- **[writing]** Figure 7: The caption reads 'System overview of .' with a missing model name (likely 'DreamX-World'), which is critical for context.
- **[writing]** Figure 7: The caption claims the pipeline integrates 'interaction alignment' and 'optimized serving', but these specific components are not explicitly labeled in the diagram.
- **[writing]** Figure 8: The caption mentions 'residual-recycling path' and 'perturbs conditioning tokens', but the diagram lacks a visual representation of this path or the perturbation mechanism, making the text unverifiable from the image.
- **[writing]** Figure 8: The 'Error Bank' and 'Save Error' loop are shown, but the caption does not explain their role in the 'Training framework', creating a disconnect between the visual pipeline and the textual description.
- **[writing]** Figure 9: The caption contains a grammatical error where the subject is missing ('Figure 9: generates interactive videos...'). It should read 'DreamX-World generates...' or similar.
- **[writing]** Figure 9: The caption claims 'precise camera and event control', but the figure is a static collage of keyframes. It does not visually demonstrate the 'control' aspect (e.g., via arrows, overlays, or before/after comparisons) to support this specific claim.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'DiT' (Diffusion Transformer) at first use in Section 3.1. Currently, the acronym appears without expansion, assuming reader familiarity with specific architecture families.
- **[writing]** Define 'DMD' (Distribution Matching Distillation) at first use in Section 3.4. The text mentions 'DMD-style distillation' and 'DMD-forcing' without explicitly stating what the acronym stands for.
- **[writing]** Define 'RL' (Reinforcement Learning) at first use in Section 3.5. While common, the paper uses 'RL' immediately after 'DMD distillation' without a prior definition in the text body.
- **[writing]** Define 'VAE' (Variational Autoencoder) at first use in Section 3.6. The term 'VAE decoding' appears without the full name being spelled out first.
- **[writing]** Define 'FPS' (Frames Per Second) at first use in the Abstract and Section 3.6. While standard, strict adherence to defining acronyms at first use is required for non-specialist accessibility.
- **[writing]** Replace '6-DoF' with 'six degrees of freedom' at first use in Section 3.1. Acronyms for physical dimensions should be defined for general readers.
- **[writing]** Define 'KV cache' (Key-Value cache) at first use in Section 3.6. The term 'rolling KV cache' is used without expansion.
- **[writing]** Define 'T2V' and 'I2V' (Text-to-Video and Image-to-Video) at first use in Section 3.6. These abbreviations are used frequently without prior definition.
- **[writing]** Define 'UE' (Unreal Engine) at first use in Section 2.1. The text uses 'UE-generated' and 'UE5' without explicitly defining the acronym first.
- **[writing]** Replace 'SLERP' with 'spherical linear interpolation' at first use in Section 2.2. This is a specific mathematical operation that should be spelled out for clarity.
- **[writing]** Define 'RoPE' (Rotary Positional Embedding) at first use in Section 3.1. The text references 'RoPE' and 'RoPE scaling' without defining the acronym.
- **[writing]** Define 'DiT' again or ensure consistency if used in Section 3.2. The acronym is central to the method but needs a clear initial definition.
- **[writing]** Replace 'FPS' with 'frames per second' in the Abstract. The first instance of the acronym should be spelled out.
- **[writing]** Define 'VLM' (Vision-Language Model) at first use in Section 4.1. The text mentions 'VLM examines' without defining the term.
- **[writing]** Define 'FVD' and 'FID' (Fréchet Video Distance and Fréchet Inception Distance) at first use in Section 4.3. These are standard metrics but should be defined for non-specialists.
- **[writing]** Replace 'RTX' with 'NVIDIA RTX' or define the hardware family at first use in the Abstract. While 'RTX 5090' is specific, the brand acronym might need context for a general audience.
- **[writing]** Define 'PRoPE' (Projective Relative Positional Encoding) at first use in Section 3.1. The text introduces 'PRoPE' as a method name but does not explicitly state the full phrase.
- **[writing]** Define 'E-PRoPE' (Efficient PRoPE) at first use in the Abstract. The acronym is introduced without the full name.
- **[writing]** Replace 'WASD' and 'IJKL' with 'keyboard-style control signals (e.g., WASD for translation, IJKL for rotation)' in Section 2.1. While common in gaming, the specific mapping should be clear to non-gamers.
- **[writing]** Define 'DiT' in the Abstract. The term 'DiT execution' appears without definition.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Table 1 claims 'Overall' is the average of metrics, but the mean of listed values (~84.77) differs from the reported 84.76, creating a minor inconsistency between the stated formula and result.
- **[writing]** Section 3.1 claims E-PRoPE reduces training time by ~50% but provides no data to support this, unlike the inference latency claim which is backed by Table 1.
- **[writing]** Section 3.4 asserts repeating DMD training fixes chunk-boundary smoothness issues but fails to explain the causal mechanism linking the solution to the specific problem.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim of 'general-purpose' operation across photorealistic, game, and stylized domains is over-extended. The evaluation data sources (SpatialVID, RealEstate10K, Sekai) are heavily skewed towards real-world and specific game engines. The paper lacks evidence that the model generalizes to unseen stylized domains (e.g., anime, oil painting) without specific fine-tuning, yet the abstract and introduction assert broad domain agnosticism.
- **[writing]** The '16 FPS on eight RTX 5090 GPUs' claim is premature and potentially misleading. The RTX 5090 is a hypothetical/unreleased hardware at the time of this preprint (June 2026). Presenting performance benchmarks on non-existent hardware as a concrete result overstates the current state of the system's deployability. This should be qualified as a projection or based on equivalent current-gen hardware.
- **[science]** The claim that the model 'outperforms' HY-WorldPlay 1.5 and LingBot-World in 'overall score' relies on a custom, non-standardized metric suite (Omni-WorldBench) where the authors are also listed as contributors (see bib entry wu2026omniworldbench). The paper does not sufficiently justify why this specific weighted average of metrics constitutes a definitive 'outperformance' over baselines that may excel in unmeasured dimensions (e.g., physics simulation, specific interaction types).

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper describes training on real-world videos (SpatialVID, RealEstate10K, Sekai, DL3DV) with recovered camera poses but lacks explicit statements regarding data privacy, consent, or compliance with the original dataset licenses. A dedicated 'Data Ethics' or 'Privacy' subsection is required to confirm that all real-world data usage adheres to the source terms and that no personally identifiable information (PII) was retained or exposed.
- **[writing]** The 'Event Instruction Tuning' and 'Composable Events' capabilities allow users to generate specific interactions (e.g., collisions, handoffs) and modify world states. The paper does not address potential dual-use risks where these features could be exploited to generate realistic disinformation, deepfakes of specific individuals, or harmful scenarios. A discussion on safety guardrails, content filtering, or responsible release policies is necessary.
- **[writing]** The evaluation section relies on a VLM (Gemini-3.1-Pro) for artifact detection and human preference studies. The paper does not disclose the demographic composition of the human assessors or the specific safety guidelines provided to them to prevent bias or the generation of harmful content during the study. Clarification on the ethical oversight of the human evaluation process is needed.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The evaluation section (Section 5) lacks statistical rigor. Tables 1, 2, and 3 report single-point scores without standard deviations, confidence intervals, or p-values. Given the claim of outperforming baselines, the authors must report variance across multiple seeds or test splits to rule out random fluctuation.
- **[science]** The 'Artifact Detection Metric' relies on a single VLM (Gemini-3.1-Pro) without reporting inter-rater reliability or calibration against human judgment. The binary pass/fail judgment is subjective; the authors should provide a validation study showing the VLM's agreement with human annotators on a held-out set.
- **[science]** The memory consistency evaluation (Table 3) reports 'gain-based' scores but does not specify the sample size (number of revisit pairs) or the statistical test used to determine if the observed gains are significant. Without this, the claim of 'stronger memory' is not statistically supported.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The camera control error formula (Eq. 1) defines a geometric mean of rotation and translation errors, but the text fails to specify the normalization bounds or the exact mapping function used to convert these errors into the [0,100] score reported in Table 1. Without this, the metric is not reproducible.
- **[science]** The 'Gain-based Scoring' for memory evaluation (Section 5.3) reports differences against a baseline but omits the standard deviation or confidence intervals for these gains. Given the high variance typical in generative model evaluation, statistical significance testing (e.g., paired t-tests) is required to validate the claimed improvements.
- **[science]** The human preference study (Section 5.4) reports win/tie/loss percentages but does not state the total number of trials (N) or the number of human assessors. This prevents the calculation of confidence intervals or the assessment of statistical power for the reported preferences.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.1 (Camera-Aware Training), the sentence 'We argue that PRoPE primarily captures the view-dependent high-level semantics' lacks a clear logical bridge to the subsequent claim that full-resolution tokens are unnecessary. Clarify the causal link between semantic abstraction and token downsampling to improve argumentative flow.
- **[writing]** In Section 3.2 (Memory-Conditioned Scene Persistence), the phrase 'In specific, we use camera pose...' contains a grammatical error. It should be corrected to 'Specifically, we use...' or 'In particular, we use...' for standard academic phrasing.
- **[writing]** In Section 3.4 (Autoregressive Long Video Generation), the sentence 'We train few-step autoregressive model using causal forcing...' is missing the indefinite article 'a' before 'autoregressive model'. Correct to 'a few-step autoregressive model'.
- **[writing]** In Section 4.1 (Basic Evaluation), the paragraph describing the 'Artifact Detection Metric' repeats the phrase 'critical defects and failures during the generation process' almost verbatim from the previous sentence. Rephrase to avoid redundancy and improve conciseness.
- **[writing]** In Section 5 (Related Work), the paragraph on 'World Model Evaluation' contains a citation formatting inconsistency: 'Omni-WorldBench\citep{wu2026omniworldbench}' lacks a space before the citation command, while others have it. Ensure consistent spacing for readability.
