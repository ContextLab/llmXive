Version 1.0.0

This workspace now hosts the MinT technical report draft for Mind Lab.

Notes
1. The report is configured for `pdflatex` compilation.
2. The visible report content has been rewritten around MinT as a Mind Lab system report.
3. The current draft combines narrative text, summary tables, and a lightweight MinT architecture diagram; a final named author roster can still be added later if needed.

Quick update guide
1. Edit `paper.tex` to adjust the title block, abstract, or section order.
2. Edit files under `sections/` to revise narrative content.
3. Edit files under `tables/mint/` to revise model coverage, platform capabilities, or deployment profiles.
4. Compile with `latexmk -pdf paper.tex` from this directory.
