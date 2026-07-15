---
action_items:
- id: 0ddf6b63c89f
  severity: writing
  text: The paper presents a system for egocentric memory, but several factual claims
    regarding performance metrics and cited baselines require verification to ensure
    accuracy. First, the introduction and related work sections cite "GPT-5" and "Gemini-2.5-pro"
    (dated 2025/2026) as existing systems for comparison. As of the current date,
    these models have not been released or documented in public records. Citing non-existent
    models as baselines for capability comparison (Table 4) undermines the reproduci
artifact_hash: edb07ae94c2d6219a9932968c85762643ccbb6eec8694c7f370d843f8e0e853b
artifact_path: projects/PROJ-1055-lightmem-ego-your-ai-memory-for-everyday/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-15T03:54:51.887139Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a system for egocentric memory, but several factual claims regarding performance metrics and cited baselines require verification to ensure accuracy.

First, the introduction and related work sections cite "GPT-5" and "Gemini-2.5-pro" (dated 2025/2026) as existing systems for comparison. As of the current date, these models have not been released or documented in public records. Citing non-existent models as baselines for capability comparison (Table 4) undermines the reproducibility and validity of the claim that LightMem-Ego offers a unique combination of features compared to "state-of-the-art" systems. The authors must either replace these with actual existing models (e.g., GPT-4o, Gemini-1.5 Pro) or clearly mark them as hypothetical/future work if the comparison is theoretical.

Second, there are minor arithmetic discrepancies in the reported aggregate metrics. In Section 5, the text states an overall LLM-judged accuracy of 51.9%. Table 2 lists scenario accuracies of 44.4%, 33.3%, and 77.8%. The simple arithmetic mean of these three values is 51.83%, which rounds to 51.8%, not 51.9%. Similarly, the overall R@3 is reported as 74.1% (Table 1), while the simple mean of the scenario values (66.7, 55.6, 100.0) is exactly 74.1%. If the 51.9% figure is derived from a weighted average (e.g., by number of queries per scenario), the text must explicitly state this, as the current presentation implies a simple average which does not match the reported number.

Finally, the claim in Section 5 that the system achieves "interactive response times" with P50 latency of 5.86s (phone) and 7.01s (glasses) is technically accurate based on the table, but the term "interactive" is subjective. While 5-7 seconds is acceptable for a memory retrieval task, it is not "real-time" in the strict sense. The text should ensure the terminology aligns with the user's expectation of "interactive" to avoid overclaiming the system's responsiveness.

These issues are primarily fixable by correcting the numbers and updating the bibliography, but the citation of non-existent models is a significant credibility issue that must be addressed before the paper can be trusted.
