# Automated-review action items — LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Teaser caption (main-llmxive.tex, lines 108-112) claims training latency is 1372.9 ms, but Table 1 (sec/05_experiment.tex, line 108) reports 1372.9 s. The unit 'ms' is a typo that misrepresents the magnitude of the speedup.
- **[writing]** Abstract (line 48) claims 1.84x inference speedup. Table 3 (sec/05_experiment.tex, line 136) shows this ratio comes from comparing 4-step BF16 (24.8 FPS) to 2-step NVFP4 (45.7 FPS). The claim conflates quantization with step distillation; clarify that the speedup requires both.
- **[writing]** Section 3.2 (sec/03_inference_infra.tex, line 168) claims a 3.6x KV-cache compression ratio. While 4/(9/8) ≈ 3.55, the text implies this is the total ratio including overhead. Clarify that 3.6x is the theoretical payload compression before scale overhead.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption claims the figure shows 'Iteration speed and peak memory' with 'Left: iteration speed. Right: peak memory,' but the rendered image contains only a single chart showing 'Training Time per Iteration' (speed). The peak memory data is missing.
- **[science]** Figure 1: The x-axis label 'Training Video Frames' (128, 256, 512, 768) contradicts the caption's reference to 'sequence lengths' and 'long contexts,' creating ambiguity about whether the x-axis represents frame count or token sequence length.
- **[writing]** Figure 2 caption: The sentence 'With the multi-shot attention sink stabilizes shot-level appearance' is grammatically incorrect and should be rephrased (e.g., 'With the multi-shot attention sink, shot-level appearance is stabilized').
- **[science]** Figure 3: The 'PTQ' and 'Ours' rows depict completely different video scenes (different furniture, lighting, and background portraits), making a direct comparison of 'temporal visual quality' or facial details scientifically invalid.
- **[writing]** Figure 3: The caption states the first column shows the 'initial frame,' but the images in the 'Shot 1' column are visually distinct between the PTQ and Ours rows, contradicting the premise of a controlled comparison.
- **[writing]** Figure 4: The caption text is truncated at the end ('...various t'), cutting off the sentence and likely the citation.
- **[science]** Figure 4: The label 'DMD on Diffusion Model (with AR mask)' is visually unaligned and appears to be a third category rather than a description of the 'Standalone LoRA injection' row, creating ambiguity about the experimental setup.
- **[science]** Figure 5: The 'Training Infra' box shows 'LoRA Few-step' as a distinct input to the final model, but the caption describes LoRA as 'standalone weights' derived in parallel. The diagram implies LoRA is a training step added to the AR model, whereas the text suggests it is a separate injection for inference, creating ambiguity about the training pipeline's output.
- **[writing]** Figure 5: The 'Inference Infra' box lists 'VAE Async Decode' but does not visually connect the VAE to the 'Model' output in the same way the 'Training Infra' connects components, making the data flow for asynchronous decoding unclear.
- **[writing]** Figure 6: The legend at the top of the middle panel defines 'Video Seq.' and 'Halo' with specific fill patterns, but the 'Clean Latent Seq.' and 'Noisy Latent Seq.' entries in the same legend lack the corresponding fill pattern swatches, making them visually ambiguous.
- **[writing]** Figure 6: The 'NVFP4 GEMM Speedup 2-4x' label in the right panel is a floating text annotation without a clear visual pointer or bracket indicating exactly which components (e.g., DGDRAD, WGRAD, FPROP) constitute the speedup.
- **[science]** Figure 7: The 'LongLive 2.0' column depicts a feedback loop labeled 'DMD' and 'LoRA Weights' on the AR Model, but the caption explicitly claims the method 'bypasses... intermediate DMD' and achieves results by 'injecting standalone LoRA weights'. The diagram contradicts the text by showing DMD as part of the LongLive 2.0 pipeline rather than a separate pre-training step.
- **[writing]** Figure 7: The 'LongLive 2.0' column contains a red arrow and text ('LoRA Weights') that are visually cluttered and overlap with the 'AR Model' box, making the diagram difficult to parse.
- **[science]** Figure 8: The diagram shows 'LoRA BF16' modules attached to the Generator and Fake Score models, but the caption describes a 'low-precision NVFP4 setup' without explaining the presence of BF16 LoRA weights or how they interact with the NVFP4 quantization.
- **[writing]** Figure 8: The 'update' arrows and 'Diffusion Loss'/'DMD Loss' boxes are extremely small and low-contrast, making the specific gradient flow paths difficult to trace and read.
- **[science]** Figure 9: The diagram labels the top row 'NVFP4 KV Cache Window' but the text 'Memory 10GB↓' is placed ambiguously near the window boundary without a clear pointer indicating if it refers to the window size or total memory reduction.
- **[writing]** Figure 9: The 'Wait / Idle' block in the bottom row is unlabeled with a chunk index (0-4) like the others, making the timeline alignment slightly ambiguous compared to the rest of the sequence.
- **[science]** Figure 10: The diagram illustrates the 'Multi-shot Attention Sink' mechanism with visual examples and a heatmap, but it lacks a quantitative plot (e.g., attention weights vs. token index) or explicit numerical labels to substantiate the claim of 'sink' behavior or the specific attention distribution.
- **[writing]** Figure 10: The caption is a single phrase ('Multi-shot Attention Sink for streaming multi-shot inference') that merely names the figure rather than explaining the visual components (e.g., the meaning of the blue squares, the 'Key'/'Query' arrows, or the specific role of the 'Global-level Sink' vs 'Shot-level Sink').

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'NVFP4' at first use in the Abstract and Introduction. Currently, the term appears as a proper noun without explanation of the underlying format (E2M1) or scaling hierarchy for non-specialist readers.
- **[writing]** Replace or define 'SP' (Sequence Parallelism) and 'AR' (Auto-Regressive) at their first occurrence in the Abstract. Acronyms should be spelled out before abbreviation to ensure accessibility.
- **[writing]** Define 'DMD' (Distribution Matching Distillation) upon first mention in the Abstract. The term is used as a standard method without context for readers unfamiliar with specific distillation literature.
- **[writing]** Clarify 'W4A4' in the Abstract and Section 3.1. While common in quantization circles, the specific meaning (4-bit weights, 4-bit activations) should be explicitly stated for a broader audience.
- **[writing]** Define 'DiT' (Diffusion Transformer) at first use in Section 1. The acronym is used frequently but not explicitly defined in the main text, assuming prior knowledge of the architecture.
- **[writing]** Define 'RHT' (Random Hadamard Transform) in Section 2.2. The acronym is introduced without expansion, which may obscure the specific stabilization technique being referenced.
- **[writing]** Define 'VAE' (Variational Autoencoder) at first use in Section 3.3. While common, the full term should be provided for readers outside the specific generative modeling sub-field.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** In Section 3.2, the text claims storage changes from '4 T_c H d bytes' to '9/8 T_c H d bytes'. This implies a 32-bit baseline, but the paper uses BF16 (16-bit). Correct the baseline byte count to 2 to match the BF16 definition used elsewhere.
- **[writing]** The Abstract claims NVFP4 yields a 1.84x speedup (40.3ms to 21.9ms). Table 3 shows this result requires both NVFP4 and 2-step distillation. Clarify that the speedup is a compound effect of quantization and step reduction, not NVFP4 alone.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of being the 'first NVFP4 training and inference system for long video generation' (Abstract) is potentially overreaching. Qualify with 'to our knowledge' or explicitly rule out prior video-specific NVFP4 work in Related Work.
- **[writing]** Attributing the 'clean pipeline' solely to 'high-quality infrastructure' (Intro) overstates causality. The paper lacks ablation isolating infrastructure from dataset or algorithmic design. Temper claims to reflect correlation rather than sole causation.
- **[writing]** Claiming NVFP4 'preserves semantics' (Teaser) without a controlled NVFP4-vs-BF16 ablation within the same pipeline is overreach. The observed quality may stem from the 'clean pipeline' or SP, not just quantization. Clarify this limitation.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper presents a significant technical advancement in long video generation infrastructure but lacks necessary depth in its safety and ethical disclosures. Broader Impacts and Dual-Use Risks: The "Broader Impacts" section (Conclusion) is critically underdeveloped. The authors state that the infrastructure "involves no negative social implications" and simply "shares the ethical impacts with existing video generation models." This is a dangerous oversimplification. LongLive-2.0's specific cap

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Table 1 (sec/05_experiment.tex) reports training iteration times but lacks standard deviation or confidence intervals across multiple runs. Given the stochastic nature of training and the claim of a 2.1x speedup, statistical significance testing or error bars are required to rule out variance as a confounding factor.
- **[science]** The claim of 'strong performance' on VBench-Long (Table 2, sec/05_experiment.tex) relies on a single aggregate score without reporting the variance across the 120K dataset samples or the specific distribution of scores. A statistical test comparing the mean/median of LongLive-2.0 against the best baseline (LongLive) is needed to confirm the improvement is not due to random sampling.
- **[science]** The ablation study for NVFP4 quantization (Appendix, Table 'appendix_ll2_precision_settings') compares PTQ vs. Pre-trained NVFP4 but does not include a baseline BF16 model trained with the exact same random seeds and data shuffling to isolate the quantization effect from training dynamics. Re-running the BF16 baseline with matched seeds is necessary to attribute the ~1.0 point drop solely to quantization.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Table 1 (tab:wan22_ffn1_nvfp4) and Table 3 (tab:inference_progressive) report single-point latency/FPS measurements without standard deviations, confidence intervals, or sample sizes (N). Given the stochastic nature of video generation and hardware variability, statistical significance of the reported speedups (e.g., 2.15x) cannot be assessed. Please report mean ± std dev over multiple runs.
- **[science]** The VBench-Long results in Table 5 (tab:vbench_long_30s_60s) present mean scores but lack measures of variance (e.g., standard error) or statistical tests (e.g., t-tests) to validate the claim that LongLive-2.0 is 'significantly' better than baselines. Without variance estimates, the robustness of the ranking claims is unclear.
- **[science]** The paper claims a '2.15x speedup' and '1.84x speedup' in the abstract and conclusion based on single measurements. These point estimates should be accompanied by confidence intervals or a statement on the number of trials performed to ensure reproducibility and statistical reliability of the performance gains.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Conclusion, correct the grammatical error 'a algorithm–infrastructure' to 'an algorithm–infrastructure' (Section 6, line 1).
- **[writing]** In Section 2.2 (NVFP4 Training), the text presents Equation 2 and then immediately repeats the exact same equation as Equation 3 with identical variable definitions. Remove the duplicate equation to improve flow and avoid confusion.
- **[writing]** In Section 3.2 (Parallel KV Quantization), the sentence 'The storage cost changes from 4 T_c H d bytes to 9/8 T_c H d bytes' contains awkward spacing around the variables. Standardize the mathematical notation (e.g., use $4 T_c H d$) for better readability.
- **[writing]** In the Abstract, the phrase 'throughout the full training and inference workflow' is slightly redundant. Consider simplifying to 'across the full training and inference workflow' or 'for the full training and inference workflow'.
