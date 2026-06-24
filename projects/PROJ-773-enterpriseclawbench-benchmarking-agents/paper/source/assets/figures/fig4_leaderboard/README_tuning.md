# Figure 3 Tuning Notes

Edit `render_fig4_leaderboard.py`, then rerun the figure script and compile the paper.

## Common Parameters

Title:

```python
ax.set_title("Main leaderboard by harness-model combination",
             fontsize=17, weight="bold", pad=12, y=1.07)
```

- `fontsize`: title size.
- `pad`: distance between title and plot area.
- `y`: title vertical position in axes coordinates. Larger moves the title up, for example `y=1.10`.

Model names on the x axis:

```python
ax.set_xticklabels(..., rotation=40, ha="right", fontsize=8.3, color=COL["ink"])
```

- Increase `fontsize` to enlarge model names.
- Change `rotation` if labels are crowded.

Top cost/time labels:

```python
top_y = 81.0
ax.text(..., top_y, f"{money(cost)} / {tmin:.1f}m",
        fontsize=7.2, rotation=38, ...)
```

- Increase `fontsize` to enlarge cost/time text.
- Increase `top_y` to move cost/time labels up.
- Increase `ax.set_ylim(0, 92)` if larger labels need more vertical room.

Harness legend:

```python
ax.legend(..., bbox_to_anchor=(0.5, -0.58), fontsize=9.2,
          handlelength=1.2, columnspacing=1.5)
```

- Increase `fontsize` to enlarge legend text.
- Make the second `bbox_to_anchor` value more negative to move the legend down, for example `-0.65`.
- Increase `columnspacing` if legend items are crowded.
- Increase `handlelength` if color swatches look too short.

Figure margins:

```python
fig.subplots_adjust(bottom=0.58, top=0.82)
```

- Increase `bottom` to make more room for model labels and the legend.
- Decrease `top` to make more room above the plot for a higher title.

## Regenerate

From the repository root:

```bash
cd /hpc_data/jczhong/FrontisBench
/hpc_data/jczhong/frontis-bench/frontis-bench-handoff/code/.venv/bin/python assets/figures/fig4_leaderboard/render_fig4_leaderboard.py
./.conda-tectonic/bin/tectonic acl_latex.tex
```

To regenerate all self-contained figures:

```bash
cd /hpc_data/jczhong/FrontisBench
/hpc_data/jczhong/frontis-bench/frontis-bench-handoff/code/.venv/bin/python scripts/make_main_text_figures.py
./.conda-tectonic/bin/tectonic acl_latex.tex
```
