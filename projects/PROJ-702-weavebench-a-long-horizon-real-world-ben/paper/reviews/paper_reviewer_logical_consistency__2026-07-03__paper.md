---
action_items:
- id: 4f97c21e9a09
  severity: science
  text: The claim that CLI-only scores 'stay at or below 3.5%' implies a hard bound,
    yet the non-zero score contradicts the strict P1 definition of 'non-substitutability'
    for all tasks. Clarify if P1 enforcement has a margin of error or if the CLI agent
    found workarounds.
- id: aa6a4ac49411
  severity: science
  text: The conclusion that outcome-only grading 'overestimates' performance relies
    on the trajectory-aware judge being ground truth. However, the judge is an LLM
    with a confidence threshold, and no false-positive rate is provided. The magnitude
    of overestimation is logically unanchored without external audit.
- id: 89535f017465
  severity: writing
  text: Section 4.2 attributes the entire +31.6pp hybrid gain to orchestration. However,
    the 3.5% CLI baseline implies some tasks are solvable by CLI alone, contradicting
    P1. Reconcile the non-zero CLI score with the claim of strict channel non-substitutability.
artifact_hash: fe47fd5151ed0fa01e324bf6a3d1eb3486f522739d02266159e873e4cf63e576
artifact_path: projects/PROJ-702-weavebench-a-long-horizon-real-world-ben/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T06:05:04.067093Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a logically coherent framework for the WeaveBench benchmark, particularly in its definition of P1 (Channel Non-Substitutability) and the design of the trajectory-aware judge. The core argument—that hybrid interfaces are necessary for complex tasks—is well-supported by the ablation studies showing a massive performance gap between single-channel and hybrid settings.

However, there are minor logical inconsistencies regarding the interpretation of the ablation data and the validation of the evaluation metric itself.

First, the claim in Section 3.4 that "GUI-only and CLI-only settings stay at or below 3.5%" is slightly at odds with the strict definition of P1. If P1 strictly requires that *no* task can be solved by a single channel, the CLI-only score should theoretically be 0%. The observed 3.5% score for Opus 4.7 suggests either that some tasks are not strictly P1-compliant or that the CLI agent found a workaround (e.g., using shell scripts to simulate GUI actions). The paper does not explicitly reconcile this non-zero baseline with the "non-substitutability" premise, creating a minor logical tension.

Second, the central conclusion that "outcome-only grading substantially overestimates agent performance" (Abstract, Section 4.3) rests on the assumption that the trajectory-aware judge is the ground truth. The paper establishes that this judge is an LLM (GPT-5.5) operating with a confidence threshold of $\geq 0.85$. While the logic that "Judge A < Judge B" implies "Judge B is inflated" is sound *if* Judge A is correct, the paper provides no evidence of the judge's own false-positive rate. If the judge incorrectly flags valid shortcuts as "hacks" (e.g., due to hallucination or over-sensitivity), the claim of "overestimation" is logically unanchored. The magnitude of the correction (e.g., 20.2 points) is presented as a fact, but its validity depends entirely on the unproven accuracy of the judge.

Finally, the interpretation of the +31.6pp hybrid gain in Section 4.2 attributes the entire difference to the necessity of orchestration. However, given the non-zero CLI baseline, a portion of this gain might simply reflect the CLI agent's ability to solve the small subset of tasks that are not strictly P1-compliant. The paper should clarify whether the 3.5% CLI score represents a failure of P1 enforcement or a legitimate capability, as this distinction affects the logical strength of the "non-substitutability" claim.
