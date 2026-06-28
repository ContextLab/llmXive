---
action_items:
- id: 8c0597d9b364
  severity: science
  text: Report variance (std dev) or confidence intervals for Pass@1 metrics in Tables
    A2 and B to validate significance of reported differences.
- id: 91cef7418417
  severity: science
  text: Clarify confounding between harness architecture and tool permissions in the
    claw sweep (Appendix D) to isolate the 'harness' variable.
artifact_hash: d91d9216ec1b23d5ae21a0d631e31b9f94ceb55943984c394279379a22a67899
artifact_path: projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T17:52:49.678872Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a robust benchmark protocol and adapter design, evidenced by the dramatic improvement in Pass@1 from 19.1% to 73.4% after fixing the patch contract (Table 1). However, the scientific evidence supporting the comparative claims regarding model and harness performance is weakened by the reliance on single-run aggregates. Section 7 explicitly admits 'main experiments report single-run aggregates,' yet Tables A2 and B report point estimates without variance (standard deviation or confidence intervals). In LLM evaluation, single-run Pass@1 can vary significantly due to stochasticity; without replication, the reported 1.88 pp mean absolute difference in Lite-80 cross-claw parity (Section 4.3) may fall within the noise margin.

Furthermore, the 'harness sweep' (Section 6.4) claims harness choice reorders rankings, but Appendix D reveals significant confounding variables: OpenClaw enforces a strict tool deny-list and per-instance isolation, whereas Hermes-agent and others are stateless with different toolsets. This conflates 'harness architecture' with 'tool permissions,' making it difficult to attribute performance differences solely to the harness design. The Lite subset selection (Section 4.2) optimizes over calibration data that is itself single-run, risking overfitting to noise. To ensure robustness, the authors should report variance metrics (e.g., std dev across 3 seeds) for key results or explicitly discuss the noise floor of single-run evaluation. Additionally, the harness comparison should control for tool permissions to isolate the orchestration variable. The adapter diagnostic is strong evidence, but the comparative claims require stronger statistical backing to be scientifically conclusive.
