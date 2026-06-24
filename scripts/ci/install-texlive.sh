#!/usr/bin/env bash
# Single source of truth for the CI TeX Live install used by EVERY workflow that
# compiles a paper (lualatex): paper-compile.yml, pipeline-paper-write.yml,
# pipeline-review.yml. Keeping the package set in ONE place stops the drift that
# let a paper compile in one lane but die "File soul.sty not found" in another
# (the package set diverged per-workflow). Edit here, never per-workflow.
#
# texlive-plain-generic: Ubuntu ships soul.sty / ulem.sty under tex/generic/ in
# THIS package, not latex-extra — without it any paper forwarding soul/ulem dies
# with "File soul.sty not found" (PROJ-646/655 class).
set -euo pipefail

sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
  texlive-luatex texlive-fonts-recommended texlive-fonts-extra \
  texlive-latex-recommended texlive-latex-extra texlive-science \
  texlive-publishers texlive-bibtex-extra biber \
  texlive-plain-generic \
  ghostscript latexmk
which lualatex && lualatex --version | head -1
