---
action_items:
- id: 1f2431942a36
  severity: science
  text: The abstract and introduction claim StepAudio 2.5 achieves 'state-of-the-art
    results' across ASR, TTS, and Realtime, 'outperforming both leading unified and
    specialized systems.' However, Table 1 shows StepAudio 2.5 ASR underperforms Doubao-ASR-2603
    on WenetSpeech testnet (4.54% vs 4.03%) and Earnings22 (6.52% vs 5.62%). The claim
    of universal SOTA is factually unsupported by the provided data.
- id: 25a47f138086
  severity: writing
  text: The Realtime evaluation (Figure 4) claims StepAudio 2.5 outperforms GPT-realtime-1.5
    and Gemini Live across all metrics. However, the baselines are dated '202604'
    while the paper is dated '2605' (May 2026). Without a clear explanation of the
    evaluation timeline or access to the specific model versions used, the claim of
    superiority over 'leading' systems is potentially misleading due to temporal ambiguity.
- id: 5c97101ce90b
  severity: writing
  text: The TTS section claims a 67.6% arena win rate against 'three leading models'
    but does not specify the exact win rates against each individual baseline (MiniMax,
    Elevenlabs, Gemini). Aggregating results without per-model breakdowns obscures
    whether the model is truly superior to all or just the weakest of the three, potentially
    overclaiming the breadth of its dominance.
artifact_hash: 88c34566a338d5ce01bdd1f1a7a5589647e4fe5286433548c997e1603e2b9886
artifact_path: projects/PROJ-622-https-arxiv-org-abs-2605-23463/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:26:01.692750Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

The paper exhibits significant overreach in its central claims regarding "state-of-the-art" (SOTA) performance across all three specialized branches (ASR, TTS, Realtime). While the architectural unification is a strong contribution, the empirical evidence provided does not fully support the absolute nature of the claims made in the Abstract and Introduction.

Specifically, in the ASR section, the authors claim the model "outperforms both leading unified and specialized systems." However, Table 1 explicitly shows that StepAudio 2.5 ASR has a higher Character Error Rate (CER) than Doubao-ASR-2603 on the WenetSpeech testnet (4.54% vs 4.03%) and the Earnings22 dataset (6.52% vs 5.62%). Claiming universal SOTA status when the model is demonstrably outperformed on specific, named benchmarks by a cited baseline is a clear over-extrapolation of the data. The text should be revised to reflect a more nuanced performance profile (e.g., "competitive SOTA" or "leading performance on long-form tasks") rather than an unqualified "state-of-the-art" across the board.

Furthermore, the Realtime evaluation presents a potential temporal overreach. The baselines (GPT-realtime, Gemini Live) are labeled with a date of "202604" (April 2026), while the paper itself is dated "2605" (May 2026). While the model may be newer, the claim of outperforming "leading" systems requires rigorous justification that the comparison is fair and that the baselines represent the absolute state-of-the-art at the time of evaluation, not just a snapshot from the previous month. The lack of detailed breakdown in the TTS arena results (aggregating three models into one win rate) also risks masking specific weaknesses against stronger individual baselines, inflating the perceived breadth of the model's superiority.

The paper must temper its absolute claims to align strictly with the provided tables and figures. The narrative should focus on the *unification* of capabilities and specific areas of strength (e.g., long-form ASR efficiency) rather than a blanket assertion of dominance over all specialized competitors.
