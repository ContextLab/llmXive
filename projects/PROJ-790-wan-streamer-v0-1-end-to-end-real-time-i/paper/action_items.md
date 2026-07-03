# Automated-review action items — Wan-Streamer v0.1: End-to-end Real-time Interactive Foundation Models

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Table 1, the citation for 'Gemini Live API' and 'Sesame web app' points to `hume2025evi3`. This citation key corresponds to the Hume EVI 3 paper, not Google's Gemini or Sesame. Verify the correct source for these benchmarks or remove the citation if the data is proprietary/unpublished.
- **[writing]** The claim that Wan-Streamer 'does not rely on external language, speech, avatar, or video-generation modules' (Abstract, Intro) is absolute. While the architecture is unified, the training section mentions initializing from `yang2025qwen25` and `yang2025qwen3`. Clarify if these base models count as 'external language modules' in the context of the claim, or rephrase to 'does not rely on *separate* external modules at inference'.
- **[writing]** Table 2 lists 'Qwen3/3.5-Omni' with a 'first-packet' latency of 234/547 ms. The citation `qwen3omni2025` and `qwen35omni2026` are included in the bib, but ensure the specific numbers (234/547) are explicitly reported in those sources or clearly marked as internal measurements to avoid misattribution.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** Figure 2: The legend at the top defines 'Thinker GPU' and 'Performer GPU' with colored outlines, but the diagram uses these colors to fill the entire task blocks (e.g., 'Encode', 'Update KV'), creating a visual mismatch between the legend definition and the figure's rendering.
- **[writing]** Figure 2: The time axis label 'time' is partially cut off at the far right edge of the image.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript contains several instances of specialized jargon and acronyms that are used without definition, which conflicts with the goal of making the work accessible to non-specialist readers. First, the term "block-causal attention" appears in the Abstract and Introduction as a central architectural component. While the paper explains that it enables incremental streaming, it does not define what distinguishes "block-causal" from standard "causal" attention. A brief plain-language explanat

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a compelling architecture for real-time interactive models, but several logical gaps exist between the premises and the conclusions drawn. First, the central claim that Wan-Streamer operates without external VAD, ASR, or TTS modules (Abstract, Section 1) is not substantiated by the provided text. While the architecture is described as a "single Transformer" processing interleaved tokens, the paper does not provide evidence that the model performs speech-to-text or voice activi

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper exhibits significant overreach in its characterization of the model's architectural unity and training methodology. The Abstract and Introduction repeatedly assert that Wan-Streamer is a "single Transformer" that does not rely on external modules, implying a monolithic, end-to-end learned system. However, Section 3.4 (Inference) reveals a "thinker-performer" deployment strategy where the model is split into two distinct functional units (thinker for encoding/state, performer for latent

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[science]** The paper describes a system capable of generating synchronized, realistic video and audio responses in real-time (Sec 1, 4). This creates significant dual-use risks for deepfake generation, non-consensual impersonation, and social engineering. The manuscript must explicitly detail the safety guardrails, content filters, and watermarking strategies implemented to prevent malicious deployment, as currently no mitigation is described.
- **[science]** The training data section (Sec 3.2) mentions using "end-to-end duplex interaction data" and "video understanding data" but lacks any statement regarding human subject consent, IRB approval, or data privacy protocols. Given the model processes and generates human faces and voices, the authors must clarify the provenance of this data and confirm compliance with ethical standards for human data usage.
- **[writing]** The system is designed to produce "visible listening behavior" and "proactive speaking" (Sec 4). Without explicit disclosure mechanisms, this could be used to deceive users into believing they are interacting with a human. The paper should address the ethical implications of this anthropomorphism and propose mandatory disclosure requirements for end-users.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The latency claims (200 ms model-side, 550 ms total) lack statistical validation. The paper reports single-point estimates without sample sizes, standard deviations, or confidence intervals. Re-run latency measurements over a statistically significant number of trials (e.g., N > 100) under controlled network conditions and report mean, median, and 95% CI.
- **[science]** The comparison tables (Tab. 1, Tab. 2) aggregate heterogeneous metrics (e.g., 'first-packet' vs. 'total interaction latency') without a unified experimental protocol. To support the claim of superior latency, provide a controlled benchmark where Wan-Streamer and baselines are evaluated on the same hardware, network conditions, and input sequences, reporting the full distribution of response times.
- **[science]** The 'Naturalness' and 'Interruption' claims are currently qualitative. Provide quantitative metrics (e.g., interruption success rate, turn-taking latency, lip-sync error scores like LSE-D/LSE-C) derived from human evaluation studies or automated benchmarks to substantiate the claim that the unified model outperforms cascaded systems in interaction quality.

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The manuscript presents a novel architecture for real-time full-duplex interaction but lacks rigorous statistical analysis to support its performance claims. The primary concern is the reporting of latency metrics in the 'Experiments' section (lines 330-360). The authors state the model achieves "approximately 200 ms model-side response latency" and "approximately 550 ms total interaction latency" as single point estimates. In statistical reporting, such values must be accompanied by measures of

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Introduction (lines 105-110), the sentence describing the 'thinker-performer' pipeline is overly dense and contains a long list of overlapping processes. Consider breaking this into two sentences to improve readability and clarify the distinct roles of the thinker and performer.
- **[writing]** In Section 2.3 (Training), the phrase 'rolling distillation' is introduced without a brief definition or context for readers unfamiliar with this specific technique. Add a clarifying clause or a short sentence explaining the mechanism to ensure clarity.
- **[writing]** In the Experiments section (lines 340-345), the transition between discussing latency metrics and the content of Table 1 is abrupt. Add a bridging sentence to explicitly guide the reader on how to interpret the 'measurement boundary' column before presenting the table.
