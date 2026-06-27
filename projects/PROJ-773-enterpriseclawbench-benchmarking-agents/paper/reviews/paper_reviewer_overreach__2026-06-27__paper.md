---
action_items:
- id: c9b0501072e5
  severity: writing
  text: Abstract claims 'enterprise agent evaluation must report...' as a prescriptive
    conclusion. This overreaches beyond the single-enterprise data. Qualify as 'suggests'
    or 'indicates' rather than 'must'.
- id: 83c4e5d97e78
  severity: science
  text: Section 5.3 skill evaluation generalizes from ONE task subclass (frontend
    page generation, 10+5 tasks) to 'task-class-level skill evaluation' as a general
    capability. This is unsupported extrapolation.
- id: ff0f32036b04
  severity: science
  text: Section 5.2 claims full 852-task set 'preserves the broad model ranking' but
    only 4 harness-model combinations were run. This is insufficient evidence for
    the scalability claim.
- id: 1f781af50ab2
  severity: science
  text: Visual judge has negative human correlation (-0.259 Spearman, Table 5) yet
    is used for main leaderboard scoring. The paper should not claim these scores
    are valid without stronger caveats.
artifact_hash: 436f60fbb896e41d063ceb9811d2249a06e1b5eaa235430cfaccb20cf6596607
artifact_path: projects/PROJ-773-enterpriseclawbench-benchmarking-agents/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-27T00:53:02.663831Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

**Overreach Review**

This review focuses exclusively on whether the paper's claims exceed what its data and methods justify.

**1. Abstract Prescriptive Claims (Lines 1-15)**
The abstract concludes: "These results show that enterprise agent evaluation **must** report harness--model combinations, artifact delivery, visual quality, cost, runtime, and skill-transfer behavior." This is a prescriptive claim about the field that goes beyond what a single-enterprise benchmark can support. The data shows *this* benchmark uses these dimensions, not that *all* enterprise evaluation must. Qualify to "suggests" or "indicates" rather than "must show."

**2. Skill Evaluation Generalization (Section 5.3, Lines 380-420)**
The paper claims native support for "evaluating skill generalization across held-out tasks from the same enterprise task class" as a contribution. However, the experiment is limited to ONE task subclass (frontend page generation) with only 10 in-domain and 5 held-out tasks. The conclusion that "evaluating skills at the task-class level" is valid generalizes from a single subclass. This requires either broader skill-class experiments or reframing as a "demonstration" rather than a validated capability.

**3. Full Set Scalability Claim (Section 5.2, Lines 340-360)**
The paper states the full 852-task set "preserves the broad model ranking observed on the manually audited Lite subset." However, only 4 harness-model combinations (all DeepAgents) were run on the full set. This is insufficient evidence to claim the full set preserves rankings across the 32 combinations tested on Lite. The claim should be restricted to "preserves model ranking within the DeepAgents harness" or similar.

**4. Visual Judge Validity (Section 5.4, Table 5, Lines 430-450)**
Table 5 shows visual judge has negative Spearman correlation with humans (-0.259). Yet the main leaderboard (Figure 1) uses Sonnet 4.6 as both text and visual judge. The paper acknowledges judges are "imperfect" but does not sufficiently qualify that visual scores may be invalid. This overstates the reliability of the main results.

**5. Limitations vs. Main Text (Section 6, Lines 460-470)**
The limitations section honestly states the single-enterprise constraint, but the introduction and abstract make broader claims about "enterprise agent evaluation" that the limitations do not fully retract. The main text should be more consistent with the limitations' scope.

**Recommendation:** Full revision required to align claims with evidence scope.
