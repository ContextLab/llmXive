---
action_items:
- id: ef7c708c78ff
  severity: science
  text: 'Branch-Loading Mechanism: The two-stage branch-loading approach (gated view
    selection + planning) is a clever engineering solution to the "context pollution"
    and "visual anchoring" problems inherent in loading large multimodal skill packages.
    The ablation studies in Figure 3 effectively demonstrate the necessity of both
    components.'
- id: 81c975b72300
  severity: science
  text: 'Comprehensive Evaluation: The paper evaluates across diverse benchmarks (OSWorld,
    macOSWorld, VAB-Minecraft, Super Mario) and model sizes (from 8B to 235B parameters),
    providing a robust picture of the method''s generalizability.'
- id: 7f370a9b8f42
  severity: science
  text: 'Behavioral Analysis: The analysis of agent behavior (RQ4) goes beyond success
    rates, showing that MMSkills reduce repetitive actions and low-level primitive
    usage, which is a strong qualitative indicator of improved reasoning. ## Concerns'
- id: edeae2bdbacf
  severity: science
  text: 'Critical Data Leakage Risk (Major): The most significant flaw is the potential
    overlap between the evaluation benchmarks (OSWorld, macOSWorld) and the skill
    source (OpenCUA).'
- id: d38ba59950f7
  severity: science
  text: OSWorld and macOSWorld are standard benchmarks for computer-use agents.
- id: 1a821de72e93
  severity: science
  text: OpenCUA is described as a source of "public non-evaluation trajectories" for
    Ubuntu and macOS.
- id: 4ac185912e1c
  severity: science
  text: Both datasets cover the same application domains (Chrome, LibreOffice, VS
    Code, etc.).
- id: e0c70d70cff1
  severity: science
  text: The paper claims in Appendix A.2 that "All MMSkills are extracted from non-test
    trajectories" and that source data is "disjoint from the final evaluation cases."
    However, without a rigorous deduplication check (e.g., comparing task instructions,
    screenshots, or trajectory hashes), it is highly probable that the "source" trajectories
    contain the exact same tasks or very similar variations as the "test" set. If
    the agent is effectively "memorizing" the test tasks from the source data, the
    reported
- id: d46fd4f0050b
  severity: science
  text: 'Bibliography Integrity: The bibliography entry for the paper itself (arXiv
    2605.13527) is marked as "unreachable" in the provided metadata. While this might
    be a metadata artifact, the reference list contains several 2025/2026 citations
    (e.g., wang2025opencua, yang2025macosworld). The reviewer must verify that these
    are real, accessible preprints or published works. If they are future-dated or
    inaccessible, the scientific grounding is weak.'
- id: 8e208d1a5c5c
  severity: science
  text: 'Skill Generation Complexity: The "Generator" pipeline (5 phases) is complex.
    While the paper describes it, the reproducibility of the skill generation process
    is unclear. How are "meta-skills" defined? How is the "audit" phase automated?
    The lack of a detailed algorithm or pseudocode for the Generator (beyond the high-level
    pipeline) makes it hard to assess the quality of the generated skills.'
- id: 255633cb1985
  severity: science
  text: Perform a rigorous deduplication analysis between the source trajectories
    and the test sets. If any overlap is found, the experiments must be re-run with
    a strictly filtered source set.
- id: 6938ac50b846
  severity: science
  text: Provide a detailed explanation of how the "disjoint" property was ensured
    (e.g., hash matching, semantic similarity thresholds).
- id: 6100f6e13488
  severity: science
  text: Clarify the provenance and accessibility of the cited 2025/2026 works.
- id: b30221d25044
  severity: science
  text: Add a section or table quantifying the inference cost/latency overhead of
    the branch-loading mechanism. Once these scientific concerns are addressed, the
    paper will be a strong contribution to the field of visual agents.
artifact_hash: d1f8365f26381f8307ae3c2777500a8f5e24701d5ef1d5e42dce305039a248a5
artifact_path: projects/PROJ-599-mmskills-towards-multimodal-skills-for-g/paper/metadata.json
backend: dartmouth
feedback: 'Critical data leakage risk: evaluation benchmarks (OSWorld/macOSWorld)
  and skill sources (OpenCUA) share overlapping domains and likely trajectories, invalidating
  the "disjoint" claim and requiring a rigorous re-evaluation of the experimental
  setup.

  '
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:13:05.915061Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: major_revision_science
---

# Free-form review body

## Strengths
- **Novel Representation**: The concept of "multimodal procedural knowledge" (binding text, state cards, and visual evidence) is a significant step forward from text-only skill libraries. The formalization of state cards with "when-to-use" and "verification cues" is well-motivated.
- **Branch-Loading Mechanism**: The two-stage branch-loading approach (gated view selection + planning) is a clever engineering solution to the "context pollution" and "visual anchoring" problems inherent in loading large multimodal skill packages. The ablation studies in Figure 3 effectively demonstrate the necessity of both components.
- **Comprehensive Evaluation**: The paper evaluates across diverse benchmarks (OSWorld, macOSWorld, VAB-Minecraft, Super Mario) and model sizes (from 8B to 235B parameters), providing a robust picture of the method's generalizability.
- **Behavioral Analysis**: The analysis of agent behavior (RQ4) goes beyond success rates, showing that MMSkills reduce repetitive actions and low-level primitive usage, which is a strong qualitative indicator of improved reasoning.

## Concerns
- **Critical Data Leakage Risk (Major)**: The most significant flaw is the potential overlap between the evaluation benchmarks (OSWorld, macOSWorld) and the skill source (OpenCUA).
    - OSWorld and macOSWorld are standard benchmarks for computer-use agents.
    - OpenCUA is described as a source of "public non-evaluation trajectories" for Ubuntu and macOS.
    - Both datasets cover the same application domains (Chrome, LibreOffice, VS Code, etc.).
    - The paper claims in Appendix A.2 that "All MMSkills are extracted from non-test trajectories" and that source data is "disjoint from the final evaluation cases." However, without a rigorous deduplication check (e.g., comparing task instructions, screenshots, or trajectory hashes), it is highly probable that the "source" trajectories contain the exact same tasks or very similar variations as the "test" set. If the agent is effectively "memorizing" the test tasks from the source data, the reported improvements are invalid. The current evidence (just stating they are disjoint) is insufficient for a scientific claim of generalization.
- **Bibliography Integrity**: The bibliography entry for the paper itself (arXiv 2605.13527) is marked as "unreachable" in the provided metadata. While this might be a metadata artifact, the reference list contains several 2025/2026 citations (e.g., `wang2025opencua`, `yang2025macosworld`). The reviewer must verify that these are real, accessible preprints or published works. If they are future-dated or inaccessible, the scientific grounding is weak.
- **Skill Generation Complexity**: The "Generator" pipeline (5 phases) is complex. While the paper describes it, the reproducibility of the skill generation process is unclear. How are "meta-skills" defined? How is the "audit" phase automated? The lack of a detailed algorithm or pseudocode for the Generator (beyond the high-level pipeline) makes it hard to assess the quality of the generated skills.
- **Cost Analysis**: The paper mentions "extra inference cost from branch loading" as a limitation but does not quantify it. Given the two-stage branch process and the loading of images, the latency and token cost increase could be significant. A brief analysis of the trade-off between performance gain and computational cost would strengthen the paper.

## Recommendation
The paper presents a compelling and well-structured framework for multimodal skills, with strong experimental results and a novel branch-loading mechanism. However, the **validity of the experimental results is currently in question due to the high risk of data leakage** between the skill source (OpenCUA) and the evaluation benchmarks (OSWorld/macOSWorld). The claim that the source and test sets are "disjoint" is not sufficiently supported by evidence.

**Verdict: major_revision_science**

The authors must:
1.  Perform a rigorous deduplication analysis between the source trajectories and the test sets. If any overlap is found, the experiments must be re-run with a strictly filtered source set.
2.  Provide a detailed explanation of how the "disjoint" property was ensured (e.g., hash matching, semantic similarity thresholds).
3.  Clarify the provenance and accessibility of the cited 2025/2026 works.
4.  Add a section or table quantifying the inference cost/latency overhead of the branch-loading mechanism.

Once these scientific concerns are addressed, the paper will be a strong contribution to the field of visual agents.
