---
action_items:
- id: ef886ac6d6ef
  severity: science
  text: Resolve contradiction between Section 3.1 text (claiming 35% average WER for
    Qwen3-ASR on Voices-in-the-wild-2M) and Table 1 (reporting 18.42% WER).
- id: 3029f8d093ed
  severity: writing
  text: Correct the relative reduction percentages in Section 5.2 [Enh.3]; the text
    attributes 65.8% to Whisper-Large-v3, but calculations suggest 65.8% refers to
    Gemini-3-Flash.
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T02:13:24.238586Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper generally maintains a high level of internal consistency between its reported metrics and the claims made in the text. Most relative reductions (e.g., the 17.4% and 64.5% reductions on NOIZEUS 0dB in Section 5.2) are mathematically supported by the values in Table 2. The inference overhead claim (-0.8%) is also accurately derived from the values in Table 11.

However, there are two significant accuracy issues that require correction before acceptance:

1. **Factual Contradiction in Dataset Baseline**: In Section 3.1 (Overview), the authors state that "even the state-of-the-art Qwen3-ASR attains a high average WER of **35%** on this benchmark [Voices-in-the-wild-2M]." However, Table 1 explicitly lists the WER for the same dataset as **18.42**. This is a substantial discrepancy (nearly double) that undermines the claim regarding the dataset's difficulty and the necessity of the proposed method. The authors must verify the correct baseline performance and align the text with the table.

2. **Misattribution of Relative Gains**: In Section 5.2 under [Enh.3], the text states: "...corresponding to a 65.8%/69.1% relative reduction over Whisper-Large-v3 and 65.8% over Gemini-3-Flash." Based on Table 3 (Mixed Real/Sim), Mega-ASR (2.73/4.57) vs. Gemini-3-Flash (7.99/9.62) yields a reduction of approximately 65.8% for the "Real" subset. Mega-ASR (2.73/4.57) vs. Whisper-Large-v3 (8.91/14.79) yields reductions of approximately 69.3% and 69.1%. The phrasing in the text erroneously groups the 65.8% figure with Whisper-Large-v3, whereas the math indicates it belongs to Gemini-3-Flash.

Aside from these points, the citations (e.g., \citep{dapo}, \citep{qwen3-asr}) are used appropriately to support the methodological choices, and the case study claims (Section 6) are supported by the provided figures. The core methodology claims are supported by the ablation studies in Section 5.1.
