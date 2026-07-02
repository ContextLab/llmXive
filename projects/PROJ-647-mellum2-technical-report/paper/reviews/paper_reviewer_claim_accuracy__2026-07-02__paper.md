---
action_items:
- id: 3ea2ce28e9e6
  severity: science
  text: Verify the MMLU-Pro baseline score of 48.6% for Qwen2.5-7B cited in Table
    1. Public benchmarks often report higher scores for this model. Ensure the cited
    source (qwen2.5) supports this specific value to validate the claim of surpassing
    it.
- id: b2419718b291
  severity: writing
  text: Clarify the unit for the RULER score '0.64' in Section 3. The cited paper
    (hsieh2024ruler) typically reports percentages. Specify if this is 64% or a normalized
    metric to avoid misinterpretation of the result's magnitude.
- id: 3b28a1367e25
  severity: science
  text: Confirm the existence and benchmark score of 'Ministral-3-14B' in Table 3.
    The cited source (liu2026ministral3) may not list a 14B variant. Verify if this
    model and its 42.4% LiveCodeBench score are accurately represented in the reference.
- id: cdeaeab3fbe6
  severity: writing
  text: Reconcile the 167B token count for the 'Thinking' SFT variant with the prompt
    counts in Table 2. The prompt counts are nearly identical to the 'Instruct' variant.
    Explain if the token difference stems from longer sequences or unlisted data volume.
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:30:28.374436Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and the alignment between claims and their cited sources.

**1. Benchmark Score Discrepancies and Baseline Verification**
In Section 2, Table 1, the paper claims Mellum2 achieves 59.3% on MMLU-Pro, explicitly stating this surpasses Qwen2.5-7B (48.6%). The bibliography cites `qwen2.5` (2024) for the Qwen2.5-7B baseline. However, public benchmarks for Qwen2.5-7B on MMLU-Pro often report scores significantly higher than 48.6% (typically in the 50-60% range depending on the specific evaluation protocol). The claim that Mellum2 "surpasses" Qwen2.5-7B relies on this specific 48.6% figure. If the cited source (`qwen2.5`) reports a higher score, the claim is factually unsupported. The authors must verify that the 48.6% figure corresponds exactly to the version of Qwen2.5-7B cited, or clarify if a different baseline (e.g., a specific fine-tuned version) was used.

**2. Metric Definition in Long-Context Claims**
Section 3 states that layer-selective YaRN achieves a "RULER score of 0.64" at 64K context, citing `hsieh2024ruler`. The RULER benchmark (Hsieh et al., 2024) typically reports results as pass@1 percentages (e.g., 64%) or normalized scores. The notation "0.64" is ambiguous: does it represent 64% or a normalized 0.64? If it is 64%, the text should explicitly state "64%" to avoid confusion with a normalized metric. If it is a normalized score, the citation must support this specific scaling. The current phrasing risks misrepresenting the magnitude of the result relative to the cited work.

**3. Baseline Model Availability and Specificity**
Section 5, Table 3, introduces a baseline "Ministral-3-14B" with a LiveCodeBench v6 score of 42.4. The bibliography cites `liu2026ministral3` (2026). The "Ministral" family (by Mistral AI) is publicly known for 8B and 3B models. A "14B" variant is not a standard public release in the cited timeframe. The claim that this specific 14B model exists and achieved 42.4% on LiveCodeBench v6 requires verification against the cited source. If the source does not contain a 14B model, the claim is unsupported, and the baseline comparison is invalid.

**4. Data Volume vs. Prompt Count Inconsistency**
Section 4 claims the "Thinking" variant was trained on ~167B tokens, while the "Instruct" variant used ~47B tokens. Table 2 lists the prompt counts for the RL data mix as nearly identical (260,500 vs 259,000). While the text mentions "harder long-form math" for the Thinking mix, a 3.5x difference in total training tokens (167B vs 47B) implies a significant difference in average sequence length or data volume not reflected in the prompt counts of Table 2. The text should clarify whether the token count difference arises from longer sequences in the Thinking mix or if the prompt counts in Table 2 are incomplete. Without this clarification, the claim of 167B tokens appears inconsistent with the provided data mix statistics.

**Conclusion**
The paper makes several strong comparative claims that rely on specific baseline scores and model configurations. The discrepancies in MMLU-Pro baselines, the ambiguity of the RULER metric, the existence of the "Ministral-3-14B" model, and the token count vs. prompt count inconsistency require clarification to ensure the claims are accurately supported by the cited evidence.
