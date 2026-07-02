---
action_items:
- id: ceb002b868e3
  severity: science
  text: 'Figure 2: The diagram depicts a ''Main Backbone'' predicting x2, x3, x4,
    x5 (T+1 to T+4) and MTP modules predicting T+2 to T+6, which contradicts the caption''s
    claim of ''parallel future-token branches'' for efficient decoding; the architecture
    shown is a standard multi-token prediction setup without the specific efficiency
    mechanisms described.'
- id: 217c6a47c646
  severity: writing
  text: 'Figure 2: The ''Main Backbone'' input shows ''Text Tokens'' (x0-x3) and ''Waveform''
    (via Encoder/Adaptor), but the diagram does not explicitly show how these two
    modalities are fused or concatenated before entering the ''StepAudio 2.5 Shared
    Backbone'' block.'
- id: 658aed982f7c
  severity: writing
  text: 'Figure 4: The caption states ''Best results are in bold'', but the rendered
    chart does not show bold text for the best scores (e.g., 86.36, 84.80, 82.18,
    79.80), making this claim unverifiable.'
- id: 14cca23ffe25
  severity: writing
  text: 'Figure 4: The x-axis labels (Human Eval, General, Car, AU, Step-SPQA) are
    not defined in the caption or legend, leaving the specific evaluation tasks ambiguous.'
- id: c1a620d252be
  severity: writing
  text: 'Figure 5: The caption ''Arena Win Rates of StepAudio-2.5-TTS'' is too brief;
    it should explicitly list the specific models compared (Minimax-2.8-HD, ElevenLabs-v3,
    Gemini-3.1-flash-tts) to make the figure self-contained.'
- id: 31db9a1aec9c
  severity: writing
  text: 'Figure 5: The ''TOTAL'' sample counts (e.g., 774, 387) are displayed as small,
    unlabelled text on the right; they should be explicitly labeled as ''Total Samples''
    or ''N'' for clarity.'
artifact_hash: 88c34566a338d5ce01bdd1f1a7a5589647e4fe5286433548c997e1603e2b9886
artifact_path: projects/PROJ-622-https-arxiv-org-abs-2605-23463/paper/metadata.json
backend: dartmouth
feedback: Vision review of 5 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:27:58.466329Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 is a clear and well-organized architectural diagram that effectively visualizes the shared audio-language stack and its application to the ASR, TTS, and Realtime model families. The flow from encoder to decoder and the subsequent branching into specific tasks is intuitive, and the caption accurately describes the components shown.

### Figure 2

The figure provides a clear visual of the MTP architecture but contains a discrepancy between the depicted token prediction ranges and the caption's description of efficiency mechanisms. Additionally, the fusion point of the audio and text modalities is not explicitly illustrated.

### Figure 3

Figure 3 is a clear and legible flowchart that accurately depicts the long-form ASR data construction pipeline described in the caption. All process steps are labeled, the sequence is logical, and there are no missing elements or communication issues.

### Figure 4

The bar chart is visually clear with data labels, but the caption's claim about bolding best results is not reflected in the image, and the specific evaluation tasks on the x-axis lack definition.

### Figure 5

The figure clearly presents win rates and counts for three comparisons, but the caption is too brief to identify the specific competitors, and the total sample counts lack explicit labels.
