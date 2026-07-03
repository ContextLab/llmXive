---
action_items:
- id: 407dc2099a31
  severity: science
  text: 'Figure 1: The caption claims the student ''down-snaps'' the unlabelled y=500
    at x=1 to the 400-row, but the plot shows a line passing exactly through the grid
    intersection (1, 400) with no visual indication of the ''unlabelled 500'' point
    or the snapping error described.'
- id: 59a94d2b2722
  severity: science
  text: 'Figure 1: The caption describes a ''BCQ/NCQ example'' contrasting two traces,
    yet the figure displays only a single linear plot with no visual distinction between
    the ''400-row chain'' and the ''exact-intersection'' chain mentioned.'
- id: 2266750eea7e
  severity: writing
  text: 'Figure 1: The plot includes generic axis labels ''x'' and ''y'' at the arrowheads
    which are redundant and clutter the visualization given the specific ''Time (hours)''
    and ''Distance (miles)'' labels already present.'
- id: 9008c2eddb30
  severity: fatal
  text: 'Figure 2: The rendered image displays a photograph of groceries (bananas,
    apples, bread, salt, stuffing mix) on a table, which does not match the caption''s
    description of a ''Visual counting'' example involving ''BCQ/NCQ'' traces, ''teacher-correct''
    and ''student-wrong'' rollouts, or any textual data.'
- id: c1b2ebfdea2f
  severity: science
  text: 'Figure 2: The image content (a still life of food items) is completely unrelated
    to the paper''s subject matter (ZPPO, LLM training, policy optimization) and fails
    to provide any evidence for the claims made in the caption regarding model performance
    or reasoning traces.'
- id: bc64e2b65294
  severity: fatal
  text: 'Figure 3: The rendered image is an interior design photograph of a console
    table with vases, which is completely unrelated to the caption''s description
    of a ''Visual counting, 4B student'' example involving BCQ/NCQ traces and text-based
    reasoning.'
- id: 79e41be26b04
  severity: fatal
  text: 'Figure 4: The rendered image is a photograph of a person holding a box of
    Krispy Kreme donuts, which is completely unrelated to the caption''s description
    of a ''Scene QA'' task involving a ''2B student'' analyzing a ''coat'' with ''braided-cord''
    and ''pocket flap'' features.'
- id: 27e81e79ab05
  severity: fatal
  text: 'Figure 5: The rendered image displays a slice of pizza on a paper plate,
    which contradicts the caption''s description of a ''Visual counting'' task involving
    a ''cluster of straws'' and a ''right-edge cluster''.'
- id: cd82420edf95
  severity: science
  text: 'Figure 5: The image content (pizza) does not support the claims regarding
    the student''s failure to count straws or the BCQ/NCQ prompt mechanics described
    in the caption.'
- id: fa5cdd3e3a43
  severity: writing
  text: 'Figure 6: The caption describes panel (a) as ''Two failure modes'' but the
    panel contains three distinct sub-panels (1, 2, 3) labeled ''Distillation'', ''RL
    from Teacher'', and ''New Problems''; the caption should explicitly list all three
    modes to match the visual content.'
- id: 00c0d447e09f
  severity: writing
  text: 'Figure 6: Panel (a) sub-panels 1 and 2 use the terms ''Distillation'' and
    ''RL from Teacher'' which are not defined in the caption, while the caption text
    refers to ''fitting the student to a much larger teacher''s logits'' and ''injecting
    a teacher response into the policy gradient'' without explicitly linking these
    descriptions to the specific sub-panels.'
- id: a6dc9902b630
  severity: writing
  text: 'Figure 7: The caption describes panel (a) as ''Hard questions... admitted
    to the prompt replay buffer'', but the rendered panel (a) is titled ''Rollouts
    and Hard Question Admission to Replay Buffer'' and depicts the admission logic
    (Teacher vs Student rollouts) rather than the buffer composition itself, creating
    a mismatch between the caption''s description and the visual content.'
- id: 268dbdbe9c11
  severity: writing
  text: 'Figure 7: The caption describes panel (b) as ''BCQ pairs one correct teacher
    response with one wrong student response'', but the rendered panel (b) is titled
    ''Binary Candidate-included Question (BCQ)'' and shows a prompt template with
    one correct and one wrong candidate, which is a representation of the prompt format
    rather than the pairing process described.'
- id: 03d480786780
  severity: writing
  text: 'Figure 7: The caption describes panel (c) as ''NCQ aggregates the student''s
    wrong rollouts into a single prompt'', but the rendered panel (c) is titled ''Negative
    Candidate-included Question (NCQ)'' and shows a prompt template with multiple
    wrong candidates, which is a representation of the prompt format rather than the
    aggregation process described.'
- id: be38a9115771
  severity: writing
  text: 'Figure 7: The caption describes panel (d) as ''Integrated batch drives the
    policy gradient update with RL Recipe'', but the rendered panel (d) is titled
    ''Overview of ZPPO'' and shows the training loop with ''BCQ'' and ''NCQ'' labels
    in the batch, which is a high-level overview rather than a detailed description
    of the policy gradient update.'
- id: 32d47120f909
  severity: writing
  text: 'Figure 8: The caption defines the y-axis as ''Cumulative graduate counts
    (graduated/admitted = ratio)'', but the axis label in the plot is simply ''cumulative
    graduations'' and the tick marks (0, 200, ..., 1000) represent raw counts, not
    the ratios described in the caption.'
- id: c55cdbac5193
  severity: writing
  text: "Figure 8: The legend uses the symbol '\u2020' for 'Qwen3.5-2B + GRPO\u2020\
    ', but the caption uses the symbol '^' for 'GRPO^'; the symbols do not match."
- id: 88f69e5406c6
  severity: writing
  text: 'Figure 9: The caption for (a) defines ''Easy'' as $r_x > 0.5$, but the rendered
    legend uses a double exclamation mark ($r_x!!0.5$) which is a rendering error
    or typo.'
- id: 805e632f4cd3
  severity: science
  text: 'Figure 9: The stacked bar chart in (a) shows percentages (e.g., 36%, 38%,
    34%) that sum to 108% for the 0.8B model, indicating a calculation or labeling
    error in the data visualization.'
- id: e40f7fa0d602
  severity: writing
  text: 'Figure 9: The x-axis label ''Fraction of Rollout over the entire training''
    is grammatically awkward and imprecise; ''Fraction of batch composition'' would
    be clearer.'
- id: d32e27a47568
  severity: writing
  text: 'Figure 10: The legend at the top of the figure is not enclosed in a box or
    panel, making it visually float above the subplots and potentially confusing regarding
    which data series it applies to.'
- id: 626858e67fa4
  severity: writing
  text: 'Figure 10: The x-axis label ''Iterations per step l'' is repeated for every
    subplot in the top row (a, b, c) rather than being shared or placed only on the
    bottom row, creating visual clutter.'
- id: e9c2a2680b6f
  severity: writing
  text: 'Figure 11: The caption ''All-averaged gain $$ (pp)'' contains a broken LaTeX
    placeholder ($$) instead of the method name (e.g., ZPPO), making the metric definition
    unclear.'
- id: 90a0c32a2424
  severity: writing
  text: 'Figure 11: The y-axis label ''Avg $\Delta$ (pp)'' uses the symbol $\Delta$
    without explicitly defining it as ''gain'' or ''improvement'' in the axis label
    itself, relying on the caption which is currently malformed.'
- id: fe1231adae59
  severity: writing
  text: 'Figure 12: The legend title ''Entry Rollout Accuracy'' is ambiguous; the
    caption clarifies these are ''admission bins'' (entry accuracy at admission),
    but the legend lacks the word ''admission'' or ''at admission'' to distinguish
    them from current training accuracy.'
- id: 520710027d2b
  severity: writing
  text: 'Figure 12: The y-axis label ''# entries in buffer'' is generic; the caption
    specifies ''buffer occupancy'', but the axis label does not explicitly state that
    the stacked height represents the total buffer size limit (10,000).'
artifact_hash: 0fd8fa2b8ede4e304df4503c08bd0823fb3038495b7a89b759c4ee4216df60db
artifact_path: projects/PROJ-731-zone-of-proximal-policy-optimization-tea/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T03:41:41.628250Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure fails to visualize the specific error described in the caption (snapping 500 to 400) and lacks the comparative traces (BCQ vs NCQ) implied by the text, presenting only a single generic line graph.

### Figure 2

The rendered image for Figure 2 is a photograph of groceries that is entirely unrelated to the caption's description of a visual counting task involving model traces and rollouts. The figure fails to support the paper's claims as it contains no data, text, or visualizations relevant to the described experiment.

### Figure 3

The provided image is a photograph of a room interior and does not match the figure caption, which describes a technical example of a 4B student model's performance on a visual counting task. The figure fails to display the described traces, data, or reasoning process.

### Figure 4

The provided image for Figure 4 is a photograph of a person with donuts, which does not match the caption's description of a scene QA example involving a coat. This is a critical mismatch between the visual content and the scientific claim.

### Figure 5

The figure is a mismatch for its caption; it shows a slice of pizza instead of the described image containing straws required to evaluate the visual counting task.

### Figure 6

Figure 6 effectively illustrates the conceptual failure modes and ZPPO mechanisms using clear diagrams, but the caption is incomplete as it fails to explicitly describe the third failure mode ('New Problems') shown in panel (a) and does not map the technical descriptions to the specific sub-panels.

### Figure 7

The figure provides a clear visual overview of the ZPPO framework, but the captions for panels (a), (b), and (c) describe the processes in a way that does not fully align with the rendered content, which focuses on prompt templates and high-level flow rather than the detailed processes described.

### Figure 8

The figure is readable and clearly compares the two methods, but the caption's description of the y-axis as a ratio contradicts the axis label and raw count values shown in the plot. Additionally, the symbol used for the GRPO method in the legend (†) does not match the symbol in the caption (^).

### Figure 9

The figure presents the requested data but contains a rendering error in the legend text for 'Easy' and a mathematical inconsistency in the stacked bar chart where the percentages for the 0.8B model sum to more than 100%.

### Figure 10

Figure 10 is scientifically clear with well-labeled axes and data points, but the layout is slightly cluttered due to the unboxed legend floating above the plots and the repetition of x-axis labels across the top row.

### Figure 11

The figure effectively visualizes performance gains across teacher sizes with clear data labels and a readable legend. However, the caption contains a broken LaTeX placeholder ('$$') that obscures the specific method being evaluated, and the y-axis relies on the caption to define the delta symbol.

### Figure 12

The figure effectively visualizes the evolution of replay buffer composition across model scales, but the legend title and y-axis label lack the specific context ('at admission', 'total occupancy') provided in the caption, which could lead to misinterpretation of the data categories.
