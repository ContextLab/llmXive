---
action_items:
- id: a96fa5443cac
  severity: writing
  text: Clarify Abstract to specify 'without external grading during optimization'
    rather than implying the evaluation is label-free. The pass rate metric requires
    the external grader.
- id: 89085c2337c8
  severity: writing
  text: Refine 'using only past trajectories' to 'using past trajectories to select
    tasks for re-solution' to accurately reflect the active rollout phase.
artifact_hash: 1dfb81df34347455cd78b0f836bbc4b7178b6fbb2681f9f18e5c917a00048d5b
artifact_path: projects/PROJ-690-evolving-agents-in-the-dark-retrospectiv/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T18:49:40.344485Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling label-free optimization method, but the Abstract and Introduction contain phrasing that risks overclaiming the scope of "no external grading." Specifically, the Abstract states: "raises SWE‑Bench Pro pass rate from 59% to 78% without external grading" (Abstract, lines 15-16). While the *optimization signal* is indeed label-free, the *evaluation metric* (pass rate) strictly requires the external benchmark grader (Docker test suite). This distinction is clarified in Section 5 ("held-out pass rate", "official Docker test suite"), but the Abstract's phrasing conflates the two, potentially misleading readers into thinking the evaluation itself is self-supervised. This is a critical distinction for reproducibility and claims of "dark" optimization.

Additionally, the claim "using only past trajectories" (Abstract, line 5) is slightly imprecise. The method uses past trajectories to select a coreset, but then generates *new* rollouts ($G=3$) on those tasks for diagnosis. It does not optimize solely on the static past data; it actively re-solves. This is a minor semantic point but worth tightening to avoid implying the method is purely offline on static logs.

The Limitations section (Section "Limitations") is honest about environmental reset requirements and adversarial content risks. The Ethics Statement appropriately flags self-preference bias. No fatal overreach is detected regarding the core methodology or results, as the tables support the reported gains. However, the Abstract needs precision to prevent misinterpretation of the evaluation protocol.
