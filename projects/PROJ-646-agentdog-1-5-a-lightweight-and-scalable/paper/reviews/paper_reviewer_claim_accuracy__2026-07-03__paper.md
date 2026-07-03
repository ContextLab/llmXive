---
action_items:
- id: e6b6a2b5787a
  severity: science
  text: The claim that AgentDoG matches GPT-5.4 performance (Abstract, Intro) relies
    on citations to unreleased/future-dated sources (e.g., openai_gpt54_2026, anthropic_claude_opus_46_2026).
    Verify these citations exist and that the comparison data is not hallucinated
    or based on speculative system cards.
- id: b6d7c78215de
  severity: writing
  text: The claim of 'around 1k samples' for training (Abstract, Sec 4.2) is supported
    by a purification step from 5,973 tools, but the exact final count of training
    trajectories used for the 0.8B-8B models is not explicitly stated in the text
    or tables, making the '1k' figure an unverified approximation.
- id: d6f9985b143e
  severity: science
  text: Table 1 (e006) and Table 2 (e000) present conflicting results for AgentDoG-4B
    on R-Judge (92.2% vs 91.8% F1) and ATBench (72.4% vs 92.8% F1). The text does
    not explain which table represents the final results or why the metrics differ
    so drastically between the two tables.
- id: e17959fd0f7d
  severity: science
  text: The claim that the environment reduces Docker overhead by 'two orders of magnitude'
    (Abstract) and to '1/100' (Intro) is supported by a memory claim (<2.5GB) but
    lacks a direct comparison of Docker memory usage for equivalent tasks, making
    the specific '100x' ratio an unsupported extrapolation.
artifact_hash: 0da3b72044460a5165e111e630e8cbd536a6b5b6d368e4237e9f5b706de0008d
artifact_path: projects/PROJ-646-agentdog-1-5-a-lightweight-and-scalable/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T04:00:17.257719Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript makes several high-impact factual claims that are not fully supported by the provided text or citations.

First, the central claim that AgentDoG achieves performance "comparable to GPT-5.4" and "Gemini-3.1-Pro" (Abstract, Introduction) relies entirely on citations to sources with future dates (e.g., `openai_gpt54_2026`, `anthropic_claude_opus_46_2026`, `gemini3`). As a third-party preprint reviewer, I cannot verify the existence or content of these unreleased system cards. If these sources do not contain the specific benchmark results cited, the claim of parity with frontier models is unsupported. The paper must either provide the actual data from these sources or qualify the claim as a projection based on available data.

Second, there is a significant internal inconsistency in the reported results. Table 1 in the Introduction (e006) reports AgentDoG-4B achieving 92.8% F1 on ATBench, while Table 2 in Section 4 (e000) reports 72.4% F1 on the same benchmark for the same model. The text does not explain this discrepancy (e.g., different evaluation settings, model variants, or data splits). This contradiction undermines the accuracy of the performance claims.

Third, the claim of training on "around 1k samples" (Abstract, Sec 4.2) is derived from a purification process starting with 5,973 tools, but the exact number of final training trajectories is not explicitly stated. While "around 1k" is a reasonable approximation, the lack of a precise figure in the methodology or tables makes the claim difficult to verify against the "influence-function purification" description.

Finally, the claim of reducing Docker overhead by "two orders of magnitude" (Abstract) and to "1/100" (Intro) is supported by a peak memory figure of <2.5GB (Sec 5.2.2) but lacks a direct baseline comparison of Docker memory usage for the *same* tasks. Without a stated baseline (e.g., "Docker environments consume ~250GB for equivalent workloads"), the "100x" reduction is an unsupported extrapolation.
