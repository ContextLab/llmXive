# Visual Narrative Extension

## User Story

**As a** researcher exploring knot complexity,
**I want** an interactive 3‑D “knot landscape” visualization where the three axes
represent selected invariants (e.g., crossing number, braid length, hyperbolic
volume) and the terrain height encodes the hyperbolic volume,
**so that** I can intuitively and artistically perceive the structure of the
complexity space.

## Acceptance Criteria
1. The visualization can be launched via a CLI command `visualize‑landscape`.
2. Users can rotate, zoom, and pan the 3‑D view in a web‑based interface.
3. Axes are labelled with the chosen invariants; the height map reflects volume.
4. The tool exports a high‑resolution screenshot and an interactive HTML file.

## Implementation Sketch
* Add a function `build_knot_landscape` in `code/analysis/complexity_visualization.py`
  that assembles a pandas DataFrame of invariants and computes a mesh grid.
* Use Plotly or PyVista to render the interactive 3‑D plot.
* Provide a wrapper script `code/analysis/complexity_visualization_runner.py`
  to invoke the visualization with optional invariant selections.

This extension fulfills the reviewer’s request for a striking visual narrative
that conveys the complexity space in an intuitive, artistic manner.

