---
action_items:
- id: 97308c663336
  severity: writing
  text: 'Section 3.1, Challenge 2: The term ''RK-based'' appears without definition.
    While ''Jetson'' is a well-known NVIDIA platform, ''RK-based'' (likely Rockchip)
    is specific hardware shorthand. Add ''(e.g., Rockchip-based)'' at first use to
    ensure an adjacent-field reader understands the hardware class.'
- id: c4e972b88f7f
  severity: writing
  text: 'Section 3.2, Design Principles: The phrase ''embodied AI kernel warehouse''
    is introduced as a specific subsystem name. While ''kernel'' is standard, ''warehouse''
    in this context is in-group shorthand for a repository of operators. Add a brief
    gloss, e.g., ''a repository (warehouse) of reusable operators,'' to clarify the
    operational meaning.'
- id: 8e35d6124896
  severity: writing
  text: 'Section 4, Evaluation: The term ''MEM'' appears in the description of HY-VLA
    (''video-history/MEM vision path'') without definition. It is unclear if this
    refers to a specific module, memory type, or a named component from a prior work.
    Define ''MEM'' (e.g., ''Memory-Enhanced Module'') at first use.'
- id: 0adef38cad79
  severity: writing
  text: 'Section 4, Evaluation: The table column header ''Inf. (ms)'' uses the abbreviation
    ''Inf.'' for ''Inference''. While common in notes, it is not expanded in the text
    or table caption. Expand to ''Inference Latency (ms)'' or define ''Inf.'' in the
    caption for clarity.'
artifact_hash: 09a01042a88fbdf5f5c789375b34beb2ecc7627cb133cf76d171a0ac8c9d372b
artifact_path: projects/PROJ-996-embodied-cpp-a-portable-inference-runtim/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T03:32:09.959481Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper is generally accessible to a competent reader from an adjacent systems or robotics field, with most acronyms (VLA, WAM, LLM, VLM) either defined at first use or being standard disciplinary vocabulary. However, there are a few instances of specific hardware shorthand and undefined abbreviations that would cause a reader from a neighboring specialty (e.g., general systems or computer vision) to pause.

Specifically, "RK-based" in Section 3.1 is a common industry shorthand for Rockchip hardware but is not universally known outside specific embedded systems circles; a brief expansion would prevent confusion. Similarly, "MEM" in the HY-VLA description (Section 4) is used as a proper noun for a vision path component without definition, which obscures the architectural contribution for an outsider. The term "kernel warehouse" in Section 3.2 is also slightly opaque; while "kernel" is standard, "warehouse" functions as a metaphor that should be explicitly linked to "repository" or "library" to ensure the operational meaning is clear. Finally, the abbreviation "Inf." in the evaluation table headers is a minor but unnecessary barrier to immediate comprehension.

Addressing these four points by adding brief parenthetical expansions or definitions at first use will ensure the paper is fully self-contained for the target audience of an adjacent-field PhD.
