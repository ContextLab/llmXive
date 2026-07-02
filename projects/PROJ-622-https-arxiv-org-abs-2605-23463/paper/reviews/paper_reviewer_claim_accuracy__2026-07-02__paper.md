---
action_items:
- id: 9fb4b1dc8ce0
  severity: science
  text: The claim of SOTA performance relies on baselines like 'VibeVoice-ASR' and
    'Qwen3-ASR-1.7B' cited with 2026 dates. Verify these models exist and are publicly
    available; if they are hypothetical, the SOTA claim is unsupported.
- id: 3340b7080dbc
  severity: science
  text: Realtime evaluation compares against 'DouBao Realtime-202604' and 'Gemini
    live-202604'. These future dates suggest the baselines may be hypothetical. Clarify
    the existence of these specific versions to validate the SOTA claim.
- id: 716f710dd61b
  severity: writing
  text: The TTS section claims to eliminate the encoder-adapter module, contradicting
    the 'unified foundation' description. Clarify if TTS uses a different architecture
    or if the claim refers only to inference paths.
artifact_hash: 88c34566a338d5ce01bdd1f1a7a5589647e4fe5286433548c997e1603e2b9886
artifact_path: projects/PROJ-622-https-arxiv-org-abs-2605-23463/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:25:38.197574Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and the validity of the evidence provided to support them.

**1. Validity of Baseline Comparisons and SOTA Claims**
The paper repeatedly asserts that StepAudio 2.5 achieves "state-of-the-art" (SOTA) performance across ASR, TTS, and Realtime tasks. This claim is substantiated by Tables and Figures comparing the model against specific baselines. However, a critical examination of the citation dates and model names reveals a significant factual inconsistency.

In the ASR evaluation (content/asr.tex, Table 1), the model is compared against "VibeVoice-ASR" and "Qwen3-ASR-1.7B". The bibliography and in-text citations for these models (e.g., `peng2026vibevoiceasrtechnicalreport`, `shi2026qwen3asrtechnicalreport`) bear the year **2026**. Similarly, the Realtime evaluation (content/realtime.tex, Figure 4) compares against "DouBao Realtime-202604" and "Gemini live-202604".

Given that the current date is prior to 2026, these citations refer to either:
1.  **Hypothetical or unreleased models:** If these models do not yet exist, the comparison is invalid, and the SOTA claim is unsupported.
2.  **Typographical errors:** If the authors intended to cite 2024 or 2025 versions, the specific version numbers (e.g., "202604") and the citation keys must be corrected to match real, verifiable releases.

Without clarification on the existence and availability of these specific baseline models, the central claim of outperforming "leading unified and specialized systems" cannot be verified. The review cannot accept the SOTA claim as fact until the baselines are confirmed to be real, accessible systems.

**2. Architectural Consistency Claims**
The paper posits a "Unified Foundation Architecture" (content/architecture.tex) consisting of an "audio-encoder--adapter--LLM-decoder" pattern. However, the TTS section (content/tts.tex) states: "the distinctive aspect of StepAudio 2.5 TTS is that it completely eliminates the encoder-adapter module and relies solely on the LLM backbone."

This creates a potential contradiction in the "unified" claim. If the TTS branch fundamentally lacks the encoder and adapter components present in the ASR and Realtime branches (which process audio input), it is not strictly a "specialization of a common foundation" in the architectural sense described in the abstract. The text should clarify whether the "foundation" implies a shared *pretrained* LLM backbone only, or if the TTS branch truly operates without the audio encoder/adapter stack during inference. If the latter, the claim of a "shared audio-language stack" for all three branches is an overstatement.

**3. Data and Metric Specificity**
The claim regarding the "50K-hour long-form dataset" (content/asr.tex) and the specific "100K hours" of short-form data is presented as fact. While the pipeline is described, the specific sources of the "inhouse datasets" are not detailed, which is standard for proprietary reports. However, the claim that the model processes "up to 30 minutes of audio" (content/asr.tex) relies on the 32K context window and 80ms embedding rate. The math holds (32,000 tokens / 12.5 tokens/sec ≈ 2560 seconds ≈ 42 minutes), so the "30 minutes" claim is conservative and accurate.

**Conclusion**
The primary issue is the **verifiability of the baselines**. The use of future-dated model names (2026) in the comparison tables renders the "state-of-the-art" claims scientifically unproven in their current form. The authors must either correct the dates to match existing models or provide evidence that these specific 2026 versions are real and accessible. Until this is resolved, the paper's central empirical claims remain unsupported.
