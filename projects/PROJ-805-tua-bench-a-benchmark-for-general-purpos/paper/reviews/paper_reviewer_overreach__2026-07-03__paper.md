---
action_items:
- id: afdb401f41a9
  severity: writing
  text: The claim that tasks are 'co-designed with PhD-level domain experts' (Abstract,
    Sec 1) is over-claimed given the lack of methodological detail. The paper does
    not specify the number of experts, their specific qualifications, the iterative
    design process, or how their input was validated. Without this, the 'expert' label
    is a marketing term rather than a scientific claim. Add a subsection detailing
    the expert curation protocol.
- id: b382e084bceb
  severity: science
  text: The statement that tasks were 'converted to CLI' from OSWorld (Sec 3.2.1)
    implies a direct mapping that may not exist. Many OSWorld tasks rely heavily on
    visual GUI cues (e.g., specific button locations, drag-and-drop) that do not have
    direct CLI equivalents. The paper over-reaches by suggesting these are 'real-world'
    terminal tasks without explaining how the semantic gap between GUI intent and
    CLI execution was bridged or if the tasks were fundamentally altered.
- id: dce9e81bf870
  severity: writing
  text: The benchmark claims to evaluate 'general-purpose' agents (Title, Abstract),
    yet the task distribution is heavily skewed toward Office/Productivity (38.3%)
    and System Ops, with only 20/120 tasks in Scientific/Engineering domains. The
    term 'general-purpose' suggests broad coverage across all computing domains, but
    the data does not support a claim of generalization beyond office automation and
    basic system administration. Temper the 'general-purpose' claim or expand the
    scientific task set.
artifact_hash: 24b3876d2f6d382fabc2cec7e848c6b9800288aa6424ce399e516dbcde8b3ba2
artifact_path: projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T14:50:30.518167Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims regarding the scope and rigor of TUA-Bench that appear to exceed the evidence provided in the manuscript.

First, the assertion that the benchmark includes tasks "co-designed with PhD-level domain experts" (Abstract, Section 1, Section 3.2.2) is a significant claim regarding the validity and difficulty of the scientific tasks. However, the manuscript provides no details on the expert curation process. It does not state how many experts were involved, their specific fields of expertise, the duration of the collaboration, or the specific criteria used to validate the tasks. Without a description of the expert-in-the-loop methodology, this claim functions as an appeal to authority rather than a demonstrated scientific contribution. The authors must either provide the methodological details of this co-design process or rephrase the claim to reflect that tasks were "inspired by" or "adapted for" these domains.

Second, the paper claims to convert tasks from OSWorld to the CLI (Section 3.2.1). This implies a direct translation of GUI-based workflows to terminal commands. However, many GUI tasks rely on visual grounding (e.g., "click the red button," "drag the file to the trash") that has no direct CLI equivalent. The paper over-reaches by presenting these as "real-world" terminal tasks without explaining how the semantic gap was bridged. If the tasks were fundamentally altered to fit the CLI (e.g., replacing a drag-and-drop with a `mv` command), the resulting task may no longer reflect the original "real-world" complexity or intent. The authors need to clarify the extent of this conversion and whether the tasks remain faithful to the original real-world scenarios or are merely synthetic CLI exercises.

Finally, the title and abstract describe TUA-Bench as a benchmark for "General-Purpose" terminal agents. While the benchmark covers five families, the distribution is heavily weighted toward Office & Productivity (38.3%) and System & Software Operations, with only 20 tasks (16.7%) in the Scientific & Engineering category. The term "general-purpose" implies a broad capability across diverse computing domains, but the data suggests a focus on office automation and system administration. The claim of "general-purpose" is an over-extrapolation of the current task distribution. The authors should either temper this claim (e.g., "General-Purpose Office and System Agents") or provide a stronger justification for why the current distribution represents "general-purpose" computing.
