---
action_items:
- id: adae7d39f81f
  severity: science
  text: 'Figure 3: The ''IoR'' row (second from top) uses a mixed scale where the
    y-axis includes negative values (e.g., -10^1) alongside a logarithmic scale (10^0,
    10^1), which is mathematically invalid for log plots and makes the visualization
    of negative bars impossible or misleading.'
- id: d7bdc43600e2
  severity: writing
  text: 'Figure 3: The x-axis labels (''20%'', ''40%'', ''60%'', ''Random'') are only
    visible on the bottom row; the top three rows lack these labels, forcing the reader
    to guess the grouping for the upper metrics.'
- id: b2df1b7bcff4
  severity: science
  text: 'Figure 4: The caption claims ''ProRL (blue stars)'' but the legend and plot
    show blue squares; the symbol definition is inconsistent.'
- id: 23c7eeaf98af
  severity: science
  text: 'Figure 4: The orange lines (fixed reward offsets) lack a legend mapping specific
    colors to specific offset values, making the ''sensitivity analysis'' uninterpretable.'
- id: 3bc73c8699a0
  severity: writing
  text: 'Figure 4: The y-axis label ''Path Length'' is ambiguous as it does not specify
    the unit (e.g., number of items).'
- id: a2d74825638b
  severity: writing
  text: 'Figure 5: The caption is insufficient as it fails to define the metrics (IoI,
    IoR) plotted on the y-axes or the specific line styles and markers used for each
    method, which are only defined in the shared legend at the bottom.'
- id: 81c111685476
  severity: writing
  text: 'Figure 5: The subplots are not labeled with letters (A, B, C, D) as referenced
    in the caption, making it difficult to explicitly map the text description to
    the specific visual panels.'
- id: 42ad0b05c7e3
  severity: writing
  text: 'Figure 6: The legend at the top defines four methods (RF, RTG, GRPO, ProRL),
    but the ''Steam'' column plots (middle row) display a fifth distinct grey line
    that is not defined in the legend or caption.'
- id: 04b21a35506c
  severity: writing
  text: 'Figure 6: The ''Amazon-Book'' column (right) plots only two lines (blue and
    green), yet the legend and caption imply four methods should be compared; the
    missing baselines (RF, GRPO) are not explained.'
- id: f76eb0f7f4f7
  severity: writing
  text: 'Figure 8: The caption contains a malformed mathematical expression for the
    expected reward accumulation: ''$(_t=1^L E[r_t] L)$'' is missing the summation
    symbol and likely intended to be ''$\sum_{t=1}^L E[r_t] \propto L$''.'
- id: d23764fe9530
  severity: writing
  text: 'Figure 8: The caption defines the Stepwise Reward Centering formula as ''$r_t
    = r_t - r$'' (using the same symbol for the centered and uncentered reward), whereas
    the figure itself correctly uses distinct notation ''$\tilde{r}_t = r_t - \bar{r}$''.'
- id: 6401c5c5aba4
  severity: science
  text: "Figure 9: The top row plots show 'Diversity' on the right y-axis (0.0\u2013\
    1.0), but the green dashed line (Amazon-Book) drops to 0.0 and stays flat, while\
    \ the red dashed line (MovieLens-1M) remains high. The caption claims 'degenerates\
    \ into generating nearly identical overlong paths' for standard policy gradient,\
    \ yet the red dashed line (diversity) does not collapse to zero for MovieLens-1M\
    \ under CTR/IoI/IoR rewards \u2014 contradicting the claim that all methods degenerate.\
    \ This misrepresents the failur"
- id: 3b49243fe3c1
  severity: writing
  text: 'Figure 9: Bottom row y-axis label ''E[r_t]'' is present, but no units or
    scale context (e.g., normalized? raw reward?) is given in caption or axis; values
    range from -0.1 to 100 across subplots without explanation, making cross-comparison
    ambiguous.'
- id: ec4102a50874
  severity: science
  text: "Figure 9: Top row, rightmost subplot (Reward = IoR) shows green dashed line\
    \ (Amazon-Book diversity) dipping below 0.0 at step 1000 \u2014 impossible if\
    \ diversity is bounded [0,1]. Likely plotting error or mislabeled axis; undermines\
    \ validity of diversity metric."
artifact_hash: 59e5ed22cd4a5270f33af7ca1a0149493d75bf5066fd8fe56191e1e437bc5c6a
artifact_path: projects/PROJ-640-https-arxiv-org-abs-2605-28293/paper/metadata.json
backend: dartmouth
feedback: Vision review of 9 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T11:02:44.815546Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 is a clear, text-based illustration of the prompt and item profile generation for the MovieLens-1M dataset. It effectively demonstrates the input and output format without requiring complex axes or legends, and the content aligns perfectly with its caption.

### Figure 2

Figure 2 effectively visualizes the impact of pre-training maturity on RL efficiency with clear axes, units, and a comprehensive legend. The two subplots (IoI and IoR) clearly demonstrate the performance gap between the 1% pre-training baseline and the higher maturity levels, directly supporting the caption's claim that a converged semantic prior is a prerequisite for effective optimization.

### Figure 3

The figure presents a comprehensive robustness analysis, but the 'IoR' row contains a critical plotting error by attempting to display negative values on a logarithmic scale. Additionally, the x-axis labels are missing from the top three metric rows, reducing readability.

### Figure 4

The figure effectively demonstrates the path collapse phenomenon described in the caption, but the legend is incomplete as it fails to map the orange lines to specific offset values, and the symbol for ProRL (squares) contradicts the caption's description (stars).

### Figure 5

The figure effectively displays performance trends across path lengths, but the caption is too brief to stand alone, failing to define the plotted metrics or the visual encoding of the methods shown in the legend.

### Figure 6

The figure effectively visualizes training dynamics across datasets, but the legend is incomplete for the Steam column (missing a grey line definition) and the Amazon-Book column omits two baselines without explanation.

### Figure 7

Figure 7 effectively illustrates the concept of proactive recommendation using a clear visual metaphor. The progression from Sci-Fi to Comedy is well-represented through the movie posters and the shifting distribution curves, and the pie charts above the posters provide a concise summary of the genre blending described in the caption.

### Figure 8

The figure effectively visualizes the ProRL mechanism and contrasts it with standard policy gradient estimation. However, the caption contains a malformed summation formula and a notation error in the reward centering equation that contradicts the clear notation used in the figure.

### Figure 9

Figure 9’s top row contradicts its own claim of universal path degeneracy by showing non-collapsed diversity for MovieLens-1M; bottom row lacks unit/scale context for E[r_t]; and one subplot shows physically impossible negative diversity values.
