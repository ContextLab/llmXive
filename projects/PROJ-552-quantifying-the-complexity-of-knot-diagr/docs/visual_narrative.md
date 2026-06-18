# Interactive 3‑D Knot Landscape

This document describes the proposed visual narrative for the project: an interactive 3‑D “knot landscape”.

## Axes
- **X‑axis** – crossing number invariant.
- **Y‑axis** – braid index invariant.
- **Z‑axis (height)** – hyperbolic volume of the knot.

## Interaction
Users can rotate, zoom, and hover over points to see tooltip details (knot name, invariants, volume).

## Implementation sketch
Use `plotly` or `pythreejs` in `code/analysis/interactive_knot_family_map.py` to generate a WebGL scene exported as an HTML file.

## User Story
*As a researcher, I want to explore the complexity space visually, so that I can gain intuitive artistic insight into how invariants relate to geometric complexity.*


