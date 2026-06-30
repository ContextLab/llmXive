---
action_items:
- id: be18f4fa12a1
  severity: writing
  text: 'The paper relies heavily on three figures to convey its architectural novelty
    and system design. While the conceptual flow is clear, the figures currently lack
    the self-contained clarity required for a standalone review or print publication.
    Figure 1 (overview.pdf): This figure is central to the paper''s argument, illustrating
    the "watch-and-do" paradigm. However, the caption is minimal. It describes the
    high-level flow but fails to explicitly define the visual encoding of the three
    distinct acti'
artifact_hash: 5266e7279b96ba8c30af6614b2b08bda02ec2220e0d4769bb56ba9df667b0fe5
artifact_path: projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T08:12:56.889458Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The paper relies heavily on three figures to convey its architectural novelty and system design. While the conceptual flow is clear, the figures currently lack the self-contained clarity required for a standalone review or print publication.

**Figure 1 (overview.pdf):** This figure is central to the paper's argument, illustrating the "watch-and-do" paradigm. However, the caption is minimal. It describes the high-level flow but fails to explicitly define the visual encoding of the three distinct actions (speak, silence, delegate) or the specific nature of the "background model" loop. For a reviewer or reader skimming the PDF, the figure should immediately communicate the decision logic. Additionally, the figure lacks alt text, which is a critical omission for accessibility and for ensuring the content is preserved if the image fails to render.

**Figure 2 (adacodec-streaming-dialogue.pdf):** This figure attempts to visualize the token efficiency of AdaCodec. The current caption is too generic ("Model overview and video encoding..."). It does not explain the visual cues: which parts of the diagram represent the 256-token reference frames versus the ~16-token P-tokens. Without this explicit mapping in the caption or clear visual legends within the figure itself, the reader must infer the mechanism from the text, defeating the purpose of a visual aid. The diagram needs to clearly label the "predictive cost reset" mechanism visually.

**Figure 3 (joyvl-system-architecture.pdf):** As a system architecture diagram, legibility is paramount. The file size (45KB) suggests a potentially low-resolution or vector-based image that might render poorly if not handled correctly by the PDF engine. The labels for the pluggable components (ASR, TTS, Memory, Background Bridge) must be crisp and readable at 100% zoom. If the diagram is dense, the text within the boxes may be too small for print. The figure should also clearly distinguish between the "real-time loop" and the "asynchronous loop" using distinct visual styles (e.g., dashed vs. solid lines, or color coding) to reinforce the text's description of the two concurrent processes.

**General:** None of the figures include explicit units or scales where applicable (e.g., time in seconds for the streaming examples). While the text provides these details, the figures should ideally be self-explanatory. The lack of alt text across all figures is a significant oversight for an arXiv submission intended for broad accessibility.
