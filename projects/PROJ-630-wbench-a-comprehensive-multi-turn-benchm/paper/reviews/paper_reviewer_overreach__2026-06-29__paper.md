---
action_items:
- id: 508b91afda88
  severity: writing
  text: 'The paper presents a substantial benchmark, but several claims overreach
    the provided evidence, particularly regarding metric validity and capability decoupling.
    Metric Validity Overclaim: In Section 5.3 (Human Preference Alignment), the authors
    claim Spearman $\rho \ge 0.94$ across ten aspects, with four reaching $\rho=1.00$.
    A perfect correlation in human-AI alignment is statistically improbable and suggests
    potential data leakage (e.g., the automated metric may be trivially derived from
    the h'
artifact_hash: 583182a56bc8cd93d801cd098b02d980b9a48cb375dac6cc8130da68f508615f
artifact_path: projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T05:50:49.732981Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a substantial benchmark, but several claims overreach the provided evidence, particularly regarding metric validity and capability decoupling.

**Metric Validity Overclaim:** In Section 5.3 (Human Preference Alignment), the authors claim Spearman $\rho \ge 0.94$ across ten aspects, with four reaching $\rho=1.00$. A perfect correlation in human-AI alignment is statistically improbable and suggests potential data leakage (e.g., the automated metric may be trivially derived from the human labels or the human evaluation protocol). Claiming this "confirms metric validity" is an overreach; it confirms alignment with *this specific* human setup, not general validity. The text should be tempered to reflect that the metrics align with the specific crowd-sourced protocol used.

**Independence Claim:** The Introduction and Section 5.2 state navigation is "largely independent" of other dimensions based on near-zero correlation. Correlation does not imply independence in complex generative systems. This causal language overstates the statistical finding. The text should use "uncorrelated" rather than "independent" to avoid implying a lack of shared underlying capabilities.

**Scope Overreach:** The Abstract and Title claim the benchmark is "comprehensive," yet the navigation evaluation relies on discrete actions (WASD/Arrows, Appendix e001). For a benchmark targeting "Interactive Video World Models" (often implying continuous control for robotics/embodiment), this limitation should be more prominent in the abstract to avoid overstating applicability to continuous control domains.

**Physical Correctness Dependency:** The Conclusion states "Physical correctness follows visual quality." While supported by correlation ($r=0.84$), this phrasing implies a dependency that may be an artifact of VLM-based physics evaluation relying on visual cues rather than true physical understanding. This should be framed as a correlation observed in the current evaluation suite, not a general law.

These revisions will ensure the claims accurately reflect the evidence without overstating the benchmark's generalizability or the metrics' absolute validity.
