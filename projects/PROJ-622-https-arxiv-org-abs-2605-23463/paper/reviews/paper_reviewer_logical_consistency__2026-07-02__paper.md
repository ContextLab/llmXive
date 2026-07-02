---
action_items:
- id: d9c8e551d1b3
  severity: writing
  text: The claim that MTP-5 yields a 39% gain in average accepted length over MTP-3
    is ambiguous. Table 3 shows lengths 3.6 and 5.0, but also includes a second value
    (e.g., "3.6 / 4"). Clarify if the percentage gain is relative to the actual accepted
    length or the theoretical maximum to ensure the metric is interpreted correctly.
- id: cf4b15b3658e
  severity: science
  text: The TTS section claims to "completely eliminate the encoder-adapter module,"
    contradicting the "shared backbone" definition in the Architecture section which
    mandates this stack. Explain how the TTS branch maintains a shared foundation
    if it structurally removes a core component defined as essential for the unified
    stack.
artifact_hash: 88c34566a338d5ce01bdd1f1a7a5589647e4fe5286433548c997e1603e2b9886
artifact_path: projects/PROJ-622-https-arxiv-org-abs-2605-23463/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:24:39.050837Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent high-level thesis: that ASR, TTS, and Realtime are different operational regimes of a single audio-language foundation. However, there are specific logical gaps in how the evidence supports the architectural claims, particularly regarding the TTS branch and the interpretation of efficiency metrics.

First, in the **TTS section (content/tts.tex)**, the authors state: "the distinctive aspect of StepAudio 2.5 TTS is that it completely eliminates the encoder-adapter module and relies solely on the LLM backbone." This creates a logical tension with the **Architecture section (content/architecture.tex)** and **Figure 1**, which define the "Shared Backbone" as an "audio-encoder--adapter--LLM-decoder" pattern. If the TTS branch removes the encoder and adapter, it is no longer using the *same* shared backbone described in the architecture section, but rather a modified or distinct variant. The paper fails to logically reconcile how a "unified foundation" can simultaneously possess a mandatory encoder-adapter stack (for ASR/Realtime) and completely eliminate it (for TTS) without explicitly defining the TTS branch as a structural exception or explaining how audio tokens are ingested without the encoder. This undermines the central claim of a singular, shared architecture.

Second, in the **ASR section (content/asr.tex)**, the text claims that increasing branches from MTP-3 to MTP-5 yields a "substantial 39% gain in average accepted length." Table 3 lists the average accepted lengths as 3.6 for MTP-3 and 5.0 for MTP-5. While the calculation (5.0 - 3.6) / 3.6 ≈ 38.9% is arithmetically correct, the table also includes a second value in the "Avg. Length" column (e.g., "3.6 / 4" and "5.0 / 6"). The text does not clarify what the second number represents (likely the maximum possible tokens), nor does it explicitly state that the 39% gain is relative to the *actual* accepted length rather than the theoretical maximum. While likely a minor clarification, the ambiguity in the data presentation weakens the precision of the causal claim regarding the efficiency trade-off.

Finally, the **Realtime section (content/realtime.tex)** claims that the model "inherits the core foundation architecture without modification." However, the training pipeline described involves "audio-centric mid-training" and specific "persona-conditioned data" streams that are not present in the base foundation description. While this is a standard fine-tuning procedure, the logical consistency of "no modification" to the architecture is slightly strained if the data distribution and objective functions (RLHF with generative rewards) fundamentally alter the model's behavior in a way that requires architectural adjustments (e.g., specific attention masks or context windows) not mentioned. The paper should clarify if "without modification" refers strictly to the parameter count and layer structure, or if the inference graph remains identical.

These issues do not invalidate the core results but require clarification to ensure the logical flow from "shared foundation" to "specialized branches" is watertight.
