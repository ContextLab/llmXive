---
action_items:
- id: 318a97a89e7f
  severity: writing
  text: Section 3.1 (Setup) states Wan 2.1-1.3B uses '81 frames', but Section 3.3
    (Video generation) and Table 2 caption refer to 'Wan 14B' for the qualitative
    video comparison in Figure 3. The text in Section 3.3 claims 'Wan 14B video at
    W4A4' is shown, but the Setup section only defines parameters for Wan 2.1-1.3B
    and CogVideoX-2B. Clarify if Wan 14B results were generated and if so, define
    its parameters in Section 3.1, or correct the figure caption/text to match the
    evaluated models.
- id: 3f9518499b14
  severity: writing
  text: Section 4.1 (Ablations) text claims 'RPBH adds 0.070 s over Block-RHT' (0.451s
    vs 0.381s in Table 1), but the text also states 'RPBH is no slower than the Full
    RHT' (0.451s vs 0.452s). While numerically close, the phrasing 'no slower' implies
    equality or superiority, whereas the table shows RPBH is 0.001s slower. This is
    a minor precision issue in the comparative claim relative to the table data.
artifact_hash: d056dc4f21ae1b95e98f52ede135ede40ce7ffad195ba83894f4cf9d35e33f1a
artifact_path: projects/PROJ-995-orbitquant-data-agnostic-quantization-fo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T04:50:46.564636Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper's logical structure is generally sound, with the core argument (rotation + distributional codebook enables calibration-free quantization) following coherently from the premises. However, there are two specific inconsistencies between the experimental setup description and the reported results/figures that require clarification.

First, there is a mismatch in the model definitions. Section 3.1 ("Setup") explicitly lists the evaluated video models as "Wan 2.1-1.3B" and "CogVideoX-2B," providing their specific frame counts and resolutions. However, Section 3.3 ("Qualitative Comparison") and the caption for Figure 3 state: "For Wan 14B video at W4A4, OrbitQuant preserves scene layout..." The "Wan 14B" model is not defined in the Setup section, nor are its experimental parameters (frames, resolution, steps) provided. While the supplementary material (Table `tab:vbench-wan14b`) does report results for Wan 14B, the main text's Setup section fails to include it in the list of evaluated models, creating a disconnect between the defined scope and the reported qualitative results. The authors should either add Wan 14B to the Setup section with its parameters or correct the text/figure caption to refer to the evaluated Wan 2.1-1.3B model if that was the intended subject.

Second, in Section 4.1 ("Comparison between Rotation Matrix"), the text claims that RPBH is "no slower than the Full RHT." Table 1 reports RPBH latency as 0.451s and Full RHT as 0.452s. While the difference is negligible (0.001s), the phrasing "no slower" suggests RPBH is faster or equal, whereas the data shows it is technically 0.001s slower. While this is a very minor point, precise comparative language should align strictly with the tabulated data to avoid any implication of superiority where none exists.

These issues are primarily matters of textual consistency and precision rather than fundamental logical flaws in the argument. The core reasoning remains valid.
