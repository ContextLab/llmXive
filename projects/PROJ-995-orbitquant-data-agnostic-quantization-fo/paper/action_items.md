# Automated-review action items — OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion Transformers

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper presents a strong case for OrbitQuant's effectiveness, with most claims supported by the provided tables and figures. However, there are minor instances of overgeneralization or ambiguity in the text that could mislead a reader about the scope of the results. Specifically, the claim that OrbitQuant "exceeds FP16" is technically true for two models but not the third (FLUX.1-dev), and the text does not explicitly qualify this. Similarly, the statement that OrbitQuant is the "strongest PT

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The mathematical notation in the central panel ($W' 	ilde{x}' pprox (W  i_d^	op)( i_d x) = Wx$) is missing the rotation matrix $ i_d$ in the final equality term shown in the caption ($W'x' Wx$), creating a visual disconnect between the diagram's logic and the caption's claim that the rotation 'cancels'.
- **[writing]** Figure 1: The 3D surface plots in Panel 1 lack visible axis tick labels and units, making it impossible to verify the magnitude of the 'drift' described in the caption.
- **[science]** Figure 4: The legend defines four methods (OrbitQuant, SmoothQuant, QuaRot, ViDiT-Q), but the right panel (Video) only displays three data points (OrbitQuant, SmoothQuant, ViDiT-Q). The QuaRot data point is missing, preventing a complete comparison for the video task.
- **[writing]** Figure 4: The x-axis label 'Latency (s/img)' for the left panel implies a per-image metric, but the x-axis values (25-35) are unusually high for a single image inference step on modern hardware, suggesting the unit might be 'ms/img' or the metric is 'time per batch'. This ambiguity makes the performance claims difficult to verify.
- **[science]** Figure 5: The left panel's x-axis labels ('BF16', 'W4', 'W3', 'W2') contradict the caption's claim that 'AdaLN activations in BF16' are fixed; the labels imply the activations are being quantized alongside the weights.
- **[writing]** Figure 5: The right panel's y-axis label 'Compression ratio' is ambiguous; the caption clarifies it is 'model compression', but the axis label alone does not specify if this is total model size or just the AdaLN component.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 1 (Introduction) and Section 2 (Methodology) use the acronym 'RPBH' (Randomized Permuted Block-Hadamard) multiple times before it is explicitly defined. The term appears in the abstract and intro without expansion. Define it at first use: 'randomized permuted block-Hadamard (RPBH) rotation'.
- **[writing]** Section 2.3 (RPBH) introduces the symbol `h` in Equation 5 and the text ('where h is the largest power of two...') without defining it in the notation section or immediately preceding the equation. Define `h` as the block size parameter where it first appears in the text or equation context.
- **[writing]** Section 3.1 (Setup) and Table 1 use the notation 'W4A4', 'W2A4', etc., without defining the convention. While common in quantization, an adjacent-field reader may not know 'W' stands for weight bits and 'A' for activation bits. Add a brief gloss at first use: 'W4A4 (4-bit weights, 4-bit activations)'.
- **[writing]** Section 2.3 mentions 'Rademacher sign diagonal' and 'Walsh–Hadamard matrix' without a one-sentence operational definition for a reader outside randomized linear algebra. Briefly clarify: 'Rademacher signs (random ±1 values)' and 'Walsh–Hadamard matrix (a structured orthogonal matrix with ±1 entries)'.
- **[writing]** Section 4 (Ablations) and Table 3 refer to 'Full RHT' and 'Block-RHT' without defining these acronyms. Define them at first use: 'Full Randomized Hadamard Transform (RHT)' and 'Block-Randomized Hadamard Transform (Block-RHT)'.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 3.1 (Setup) states Wan 2.1-1.3B uses '81 frames', but Section 3.3 (Video generation) and Table 2 caption refer to 'Wan 14B' for the qualitative video comparison in Figure 3. The text in Section 3.3 claims 'Wan 14B video at W4A4' is shown, but the Setup section only defines parameters for Wan 2.1-1.3B and CogVideoX-2B. Clarify if Wan 14B results were generated and if so, define its parameters in Section 3.1, or correct the figure caption/text to match the evaluated models.
- **[writing]** Section 4.1 (Ablations) text claims 'RPBH adds 0.070 s over Block-RHT' (0.451s vs 0.381s in Table 1), but the text also states 'RPBH is no slower than the Full RHT' (0.451s vs 0.452s). While numerically close, the phrasing 'no slower' implies equality or superiority, whereas the table shows RPBH is 0.001s slower. This is a minor precision issue in the comparative claim relative to the table data.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract/Conclusion claim 'sets the state of the art' and 'only method' at W2A4. Table 1 shows OrbitQuant leads overall but AdaTSQ beats it on 'Two object' (FLUX-schnell W4A4). 'Only method' is true for tested baselines, but 'SOTA' implies universal dominance. Narrow to 'best among calibration-free methods' or 'best overall score on tested models'.
- **[writing]** Abstract claims 'no per-modality tuning' for image-to-video transfer. Section 3.2 shows video results but doesn't confirm if RPBH permutation seeds were shared or re-sampled. If re-sampled, this is per-modality config. Clarify if exact same seeds/params were used across modalities to support the claim.
- **[writing]** Conclusion states 'supports usable 2-bit weights'. Table 1 shows Z-Image-Turbo drops from 0.754 (FP16) to 0.319 (W2A4), a >50% drop. 'Usable' is subjective here. Qualify as 'retains non-trivial performance' or acknowledge Z-Image-Turbo degradation to avoid overgeneralizing W2A4 robustness.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a post-training quantization (PTQ) method for Diffusion Transformers (DiTs) that relies on mathematical rotations and pre-computed codebooks. The work does not involve human subjects, personal data collection, or the generation of sensitive content (e.g., biological agents, cyber-attack payloads, or non-consensual deepfakes). The datasets used for evaluation (GenEval, VBench) are standard public benchmarks, and the models evaluated (FLUX, Wan, CogVideoX) are existing public checkpoints.

There are no foreseeable, non-trivial risks of harm specific to this methodology that are unaddressed. The "dual-use" potential of making generative models more efficient is a generic characteristic of the field and does not constitute a specific risk requiring mitigation in this context, as the method does not lower the barrier to generating harmful content beyond what the base models already allow. The paper does not release any new training data that could violate licenses or contain PII, nor does it disclose operational vulnerabilities in live systems. Consequently, no specific safety disclosures or mitigations are missing. The verdict is accept.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Table 1 (GenEval) and Table 2 (VBench) report single-run results for OrbitQuant against baselines. While Table S4 (Suppl) shows seed variance for OrbitQuant, the baselines (SVDQuant, AdaTSQ, etc.) are presented as single numbers without variance. To rule out that OrbitQuant's lead is a lucky seed, report mean ± SD for all baselines over the same 3 seeds, or explicitly state if baseline numbers are taken from fixed literature values that preclude re-running.
- **[science]** Table 1 (GenEval) shows OrbitQuant beating AdaTSQ by 0.015 on FLUX.1-schnell W4A4 (0.703 vs 0.688). Table S4 reports a standard deviation of 0.012 for OrbitQuant on this setting. The reported gain is smaller than the run-to-run variance, making the 'state-of-the-art' claim statistically indistinguishable from noise. Report the full distribution of differences across seeds or a paired statistical test to confirm the gain is real.
- **[science]** Section 3.1 states baseline numbers are 'taken primarily from AdaTSQ... and QVGen'. If baselines are not re-run by the authors, the comparison is confounded by different evaluation seeds, prompts, or generation settings used in the original papers. To establish a fair comparison, re-run all baselines with the exact same prompt set, seeds, and generation parameters used for OrbitQuant, or disclose the specific seed/settings of the cited numbers to verify comparability.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Tables 1 and 2 report single-point accuracy scores without uncertainty measures (SD/CI). While Table 4 shows OrbitQuant seed variance, baselines lack this context. Report mean ± SD over ≥3 seeds for all methods in main tables, or explicitly state single-run results and add a variance caveat.
- **[writing]** Table 3 claims RPBH is 'strongest' at low bit-widths based on point estimates without reported SDs or significance tests. Given generation stochasticity, this claim is unsupported. Report SD across seeds for ablation results or perform a paired test to validate the 'strongest' assertion.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured and the technical narrative is logical. However, there are specific instances where sentence construction and terminology consistency impede the reader's ability to parse the text on the first pass. In the Introduction, the third paragraph contains a long, complex sentence comparing LLM and DiT activation statistics. The clause structure forces the reader to hold multiple conditions in memory before reaching the main verb. Splitting this into two shorter se
