# Automated-review action items — StepAudio 2.5 Technical Report

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** The claim of SOTA performance relies on baselines like 'VibeVoice-ASR' and 'Qwen3-ASR-1.7B' cited with 2026 dates. Verify these models exist and are publicly available; if they are hypothetical, the SOTA claim is unsupported.
- **[science]** Realtime evaluation compares against 'DouBao Realtime-202604' and 'Gemini live-202604'. These future dates suggest the baselines may be hypothetical. Clarify the existence of these specific versions to validate the SOTA claim.
- **[writing]** The TTS section claims to eliminate the encoder-adapter module, contradicting the 'unified foundation' description. Clarify if TTS uses a different architecture or if the claim refers only to inference paths.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 2: The diagram depicts a 'Main Backbone' predicting x2, x3, x4, x5 (T+1 to T+4) and MTP modules predicting T+2 to T+6, which contradicts the caption's claim of 'parallel future-token branches' for efficient decoding; the architecture shown is a standard multi-token prediction setup without the specific efficiency mechanisms described.
- **[writing]** Figure 2: The 'Main Backbone' input shows 'Text Tokens' (x0-x3) and 'Waveform' (via Encoder/Adaptor), but the diagram does not explicitly show how these two modalities are fused or concatenated before entering the 'StepAudio 2.5 Shared Backbone' block.
- **[writing]** Figure 4: The caption states 'Best results are in bold', but the rendered chart does not show bold text for the best scores (e.g., 86.36, 84.80, 82.18, 79.80), making this claim unverifiable.
- **[writing]** Figure 4: The x-axis labels (Human Eval, General, Car, AU, Step-SPQA) are not defined in the caption or legend, leaving the specific evaluation tasks ambiguous.
- **[writing]** Figure 5: The caption 'Arena Win Rates of StepAudio-2.5-TTS' is too brief; it should explicitly list the specific models compared (Minimax-2.8-HD, ElevenLabs-v3, Gemini-3.1-flash-tts) to make the figure self-contained.
- **[writing]** Figure 5: The 'TOTAL' sample counts (e.g., 774, 387) are displayed as small, unlabelled text on the right; they should be explicitly labeled as 'Total Samples' or 'N' for clarity.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript exhibits a high density of specialized terminology and acronyms that, while standard in the immediate sub-field of audio-language modeling, create barriers for a broader technical audience. The primary issue is the inconsistent definition of acronyms and the use of abstract, jargon-heavy phrasing for core concepts. In the Abstract and Section 2.1 (ASR Specialization), the term "MTP" is introduced as "MTP-5" and "MTP head" without ever explicitly stating "Multi-Token Prediction." W

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The claim that MTP-5 yields a 39% gain in average accepted length over MTP-3 is ambiguous. Table 3 shows lengths 3.6 and 5.0, but also includes a second value (e.g., "3.6 / 4"). Clarify if the percentage gain is relative to the actual accepted length or the theoretical maximum to ensure the metric is interpreted correctly.
- **[science]** The TTS section claims to "completely eliminate the encoder-adapter module," contradicting the "shared backbone" definition in the Architecture section which mandates this stack. Explain how the TTS branch maintains a shared foundation if it structurally removes a core component defined as essential for the unified stack.

## paper_reviewer_overreach — verdict: full_revision

- **[science]** The abstract and introduction claim StepAudio 2.5 achieves 'state-of-the-art results' across ASR, TTS, and Realtime, 'outperforming both leading unified and specialized systems.' However, Table 1 shows StepAudio 2.5 ASR underperforms Doubao-ASR-2603 on WenetSpeech testnet (4.54% vs 4.03%) and Earnings22 (6.52% vs 5.62%). The claim of universal SOTA is factually unsupported by the provided data.
- **[writing]** The Realtime evaluation (Figure 4) claims StepAudio 2.5 outperforms GPT-realtime-1.5 and Gemini Live across all metrics. However, the baselines are dated '202604' while the paper is dated '2605' (May 2026). Without a clear explanation of the evaluation timeline or access to the specific model versions used, the claim of superiority over 'leading' systems is potentially misleading due to temporal ambiguity.
- **[writing]** The TTS section claims a 67.6% arena win rate against 'three leading models' but does not specify the exact win rates against each individual baseline (MiniMax, Elevenlabs, Gemini). Aggregating results without per-model breakdowns obscures whether the model is truly superior to all or just the weakest of the three, potentially overclaiming the breadth of its dominance.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper describes a 'Generative Reward Model' (GRM) trained on human preference data for TTS and Realtime branches (content/tts.tex, content/realtime.tex) but lacks an explicit statement regarding IRB approval, informed consent from human annotators, or ethical review board oversight. Given the use of human feedback for RLHF, a statement on ethical compliance and data privacy is required.
- **[writing]** The data pipeline for long-form ASR (content/asr.tex) utilizes 'inhouse datasets' and 'raw long recordings' processed via VAD and multi-system transcription. The manuscript does not specify the provenance of these recordings, whether they contain personally identifiable information (PII), or the consent mechanisms used for data collection. A section on data privacy, anonymization, and consent is necessary to mitigate dual-use and privacy risks.
- **[writing]** The Realtime branch (content/realtime.tex) explicitly trains on 'persona-conditioned data' and 'paralinguistic cues' to simulate specific personalities and emotional states. The paper does not address the ethical risks of deepfake audio, identity impersonation, or the potential for malicious use of these capabilities. A discussion on safety guardrails, usage policies, or mitigation strategies for these specific risks is needed.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The Realtime evaluation (content/realtime.tex) relies on a subjective mobile-app score (80.41) without reporting the number of human raters, inter-annotator agreement (e.g., Krippendorff's alpha), or the specific rubric used. This prevents assessment of statistical significance or rater bias.
- **[science]** The TTS evaluation (content/tts.tex) reports a 67.6% arena win rate against three baselines but omits the total number of pairwise comparisons, the confidence interval for the win rate, and the statistical test used to claim 'consistent gains.' Without N and p-values, the claim of superiority is not statistically verifiable.
- **[science]** The ASR efficiency claim (content/asr.tex) cites an RTF of 0.0053 on a single H800 GPU but does not specify the batch size or concurrency level used during measurement. Since RTF is highly sensitive to batch size in LLM-based ASR, the lack of serving configuration details makes the efficiency claim non-reproducible.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** In Table 1 (ASR results), report confidence intervals or standard deviations for the error rates (CER/WER) across the 100+ test clips. Point estimates alone do not convey the statistical significance of the marginal improvements (e.g., 0.06 absolute points) claimed to be 'essentially unchanged'.
- **[science]** The TTS evaluation (content/tts.tex) relies on an 'arena-style' win rate of 67.6% against three baselines. The text mentions 774 prompts but omits the sample size per model pair, the specific statistical test used (e.g., binomial test, Bradley-Terry), and the resulting p-values or confidence intervals to support the claim of 'consistent gains'.
- **[science]** In the Realtime evaluation (content/realtime.tex), the subjective human evaluation score (80.41) is compared to baselines without reporting the number of human raters, the inter-rater reliability (e.g., Krippendorff's alpha), or the statistical significance of the reported +10.0 margin.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In content/introduction.tex, the phrase 'as LLMs became the standard interface' uses the past tense 'became' to describe an ongoing trend. Change to 'have become' or 'are becoming' to maintain temporal consistency with the present-tense narrative of the field's evolution.
- **[writing]** In content/tts.tex, Section 2.1, the sentence 'The final reward used for policy optimization is obtained by applying a reward-shaping transformation to this score' is vague. Explicitly define the transformation function s(·) or cite the specific shaping method used, as the current phrasing obscures the mathematical operation.
- **[writing]** In content/realtime.tex, Section 2.2.2, the list item 'Reward Sparsity' describes a challenge but lacks a parallel grammatical structure to the other items (Conversational Coherence, Persona Consistency, Paralinguistic Sensitivity). Rephrase to 'Reward Sparsity: The lack of a single ground-truth target...' to match the noun-phrase style of the other headers.
