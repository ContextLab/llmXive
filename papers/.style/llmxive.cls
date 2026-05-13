%% llmxive.cls — house-style document class for llmXive papers.
%%
%% A clean, modern, single-column scientific-paper style that matches the
%% llmXive website's visual identity:
%%   - Fraunces (serif, variable) for body text + headings — same family as
%%     the dashboard's hero typeface.
%%   - JetBrains Mono for code / inline code / verbatim — same monospace as
%%     the dashboard's wordmark + run-log entries.
%%   - Dartmouth green (#00693E) for accent (section numbers, hyperlinks,
%%     rules) — the website's --accent.
%%
%% Required engine: XeLaTeX or LuaLaTeX (uses fontspec).
%% Fonts are vendored under papers/.style/fonts/ so the class is portable.
%%
%% Usage:
%%   \documentclass[11pt]{llmxive}
%%   \title{...}
%%   \author{...}
%%   \date{...}                  % optional; omit for "today"
%%   \arxivid{2510.21958}         % optional
%%   \githubrepo{...}             % optional
%%   \begin{document}
%%   \maketitle
%%   \begin{abstract}...\end{abstract}
%%   ...
%%   \bibliographystyle{plainnat}
%%   \bibliography{...}
%%   \end{document}

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{llmxive}[2026/05/13 v0.1.0 llmXive house style]

% ── Class options ──────────────────────────────────────────────────────────
% The class is engine: XeLaTeX or LuaLaTeX (uses fontspec). Fonts are vendored
% under papers/.style/fonts/ — the compile MUST be run from the repository root
% so the relative font Path resolves. (When you compile from inside
% projects/<id>/paper/source/, set TEXINPUTS to include ../../../.. and pass
% --output-directory back to the source dir. The class auto-detects the
% LLMXIVE_REPO_ROOT environment variable as an override.)
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
\LoadClass[11pt]{article}

% ── Geometry ────────────────────────────────────────────────────────────────
\RequirePackage[a4paper, margin=1in, top=1.1in, bottom=1.1in,
                headheight=14pt, headsep=0.35in, footskip=0.4in]{geometry}

% ── Math + graphics + core text packages everyone uses ─────────────────────
\RequirePackage{amsmath}
\RequirePackage{amssymb}
\RequirePackage{graphicx}
\RequirePackage{xspace}

% ── Fonts (XeLaTeX / LuaLaTeX via fontspec) ────────────────────────────────
\RequirePackage{fontspec}
% Vendored under papers/.style/fonts/. The fontspec Path is relative to the
% compile's cwd; that means: either compile from the repo root, or pre-set
% OSFONTDIR to point at papers/.style/fonts/. The agent's paper_initializer
% wraps xelatex in a script that always cd's to the repo root first.
\defaultfontfeatures{Path=\detokenize{papers/.style/fonts/}}
\setmainfont{Fraunces-Variable.ttf}[
  UprightFont       = Fraunces-Variable.ttf,
  BoldFont          = Fraunces-Variable.ttf,
  ItalicFont        = Fraunces-Italic-Variable.ttf,
  BoldItalicFont    = Fraunces-Italic-Variable.ttf,
  UprightFeatures   = {RawFeature={axis={opsz=24,SOFT=50,WONK=0,wght=400}}},
  BoldFeatures      = {RawFeature={axis={opsz=24,SOFT=50,WONK=0,wght=700}}},
  ItalicFeatures    = {RawFeature={axis={opsz=24,SOFT=50,WONK=0,wght=400}}},
  BoldItalicFeatures= {RawFeature={axis={opsz=24,SOFT=50,WONK=0,wght=700}}},
  Ligatures         = TeX,
]
\setmonofont{JetBrainsMono-Regular.ttf}[
  ItalicFont        = JetBrainsMono-Italic.ttf,
  BoldFont          = JetBrainsMono-Bold.ttf,
  Scale             = 0.92,
]
\newfontfamily\llmxivedisplay{Fraunces-Variable.ttf}[
  RawFeature  = {axis={opsz=144,SOFT=50,WONK=0,wght=400}},
  Ligatures   = TeX,
]
\newfontfamily\llmxivedisplayit{Fraunces-Italic-Variable.ttf}[
  RawFeature  = {axis={opsz=144,SOFT=50,WONK=0,wght=400}},
  Ligatures   = TeX,
]
\newfontfamily\llmxivemono{JetBrainsMono-Regular.ttf}[Scale=0.92]
\newfontfamily\llmxivemonobold{JetBrainsMono-Bold.ttf}[Scale=0.92]

% ── Colors (match web/css/site.css --accent et al.) ─────────────────────────
\RequirePackage{xcolor}
\definecolor{llmxAccent}{HTML}{00693E}
\definecolor{llmxAccent2}{HTML}{0A8A55}
\definecolor{llmxAccentSoft}{HTML}{D6E9DD}
\definecolor{llmxText}{HTML}{16241B}
\definecolor{llmxText2}{HTML}{405548}
\definecolor{llmxMuted}{HTML}{6E8478}
\definecolor{llmxLine}{HTML}{D8E0DA}

\AtBeginDocument{\color{llmxText}}

% ── Microtype + spacing ─────────────────────────────────────────────────────
\RequirePackage[protrusion=true, expansion=false]{microtype}
\RequirePackage{setspace}
\setstretch{1.18}

% Generous paragraph behavior — no indent, modest skip — matches the website's
% rhythm. Override with \setlength{\parindent}{1em}\setlength{\parskip}{0pt} in
% a user preamble if traditional academic indenting is preferred.
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.55em plus 0.15em minus 0.05em}

% ── Hyperlinks (last-loaded; uses llmxAccent for href + cite) ───────────────
\RequirePackage[unicode]{hyperref}
\hypersetup{
  colorlinks  = true,
  linkcolor   = llmxAccent2,
  citecolor   = llmxAccent,
  urlcolor    = llmxAccent,
  filecolor   = llmxAccent,
  pdfborder   = {0 0 0},
}
\RequirePackage[capitalize]{cleveref}

% ── Section headings ────────────────────────────────────────────────────────
\RequirePackage{titlesec}
% Section: heading text + number both in accent green, bold. The format-block
% applies ONLY to the heading text; it doesn't leak into the following body.
\titleformat{\section}
  {\normalfont\Large\bfseries\color{llmxAccent}}
  {\thesection}{0.8em}{}
\titleformat{\subsection}
  {\normalfont\large\bfseries\color{llmxText}}
  {\thesubsection}{0.7em}{}
\titleformat{\subsubsection}
  {\normalfont\normalsize\bfseries\itshape\color{llmxText2}}
  {\thesubsubsection}{0.6em}{}
\titlespacing*{\section}      {0pt}{1.6em plus .4em minus .2em}{0.5em plus .1em}
\titlespacing*{\subsection}   {0pt}{1.2em plus .3em minus .1em}{0.35em}
\titlespacing*{\subsubsection}{0pt}{1.0em plus .2em minus .1em}{0.30em}

% ── Captions (figures + tables) ─────────────────────────────────────────────
\RequirePackage[font={small}, labelfont={bf,color=llmxAccent},
                labelsep=period, justification=raggedright, singlelinecheck=off]{caption}

% ── Title block ─────────────────────────────────────────────────────────────
% Metadata commands the title page may use. \arxivid{} and \githubrepo{}
% are optional; if set, they render as a small "Source" line below the date.
\newcommand{\llmx@arxivid}{}
\newcommand{\arxivid}[1]{\renewcommand{\llmx@arxivid}{#1}}
\newcommand{\llmx@githubrepo}{}
\newcommand{\githubrepo}[1]{\renewcommand{\llmx@githubrepo}{#1}}
\newcommand{\llmx@journal}{llmXive --- automated scientific discovery}
\newcommand{\journal}[1]{\renewcommand{\llmx@journal}{#1}}

% Override \and so `Foo \and Bar` renders inline as "Foo, Bar" (the
% article-class default puts it in a tabular which doesn't suit our
% single-flow title block).
\renewcommand{\and}{,\space}

\renewcommand\maketitle{%
  \begingroup
    \thispagestyle{empty}
    \pagestyle{llmxive}
    % Top brand bar: "llmXive" wordmark in JetBrains Mono, accent-bordered, like
    % the website header.
    \noindent
    {\llmxivemonobold\color{llmxAccent}%
      \setlength{\fboxsep}{2pt}\setlength{\fboxrule}{1pt}%
      \fcolorbox{llmxAccent}{white}{\strut\hspace{0.4em}llmXive\hspace{0.4em}}}%
    \hfill
    {\llmxivemono\footnotesize\color{llmxMuted}\MakeUppercase{\llmx@journal}}
    \par\vspace{0.6em}
    {\color{llmxLine}\hrule height 0.5pt}
    \par\vspace{2.2em}
    % Title (Fraunces display, optical-size 144)
    \noindent
    {\llmxivedisplay\Huge\@title\par}
    \vspace{1.1em}
    % Authors
    \ifx\@author\empty\else
      \noindent{\large\color{llmxText2}\@author\par}
      \vspace{0.7em}
    \fi
    % Date
    \noindent
    {\llmxivemono\small\color{llmxMuted}\@date}%
    % Source line (arXiv id / GitHub repo)
    \ifx\llmx@arxivid\empty\else
      \par\vspace{0.25em}
      \noindent{\llmxivemono\footnotesize\color{llmxMuted}%
        Source: \href{https://arxiv.org/abs/\llmx@arxivid}{arXiv:\llmx@arxivid}%
        \ifx\llmx@githubrepo\empty\else%
          \ \textbullet\ Code: \href{\llmx@githubrepo}{\llmx@githubrepo}%
        \fi}
    \fi
    \ifx\llmx@arxivid\empty
      \ifx\llmx@githubrepo\empty\else
        \par\vspace{0.25em}
        \noindent{\llmxivemono\footnotesize\color{llmxMuted}%
          Code: \href{\llmx@githubrepo}{\llmx@githubrepo}}
      \fi
    \fi
    \par\vspace{2.0em}
    {\color{llmxLine}\hrule height 0.5pt}
    \par\vspace{1.4em}
  \endgroup
}

% Page style with a small "llmXive" mark in the header.
\RequirePackage{fancyhdr}
\fancypagestyle{llmxive}{%
  \fancyhf{}%
  \fancyhead[L]{\llmxivemono\footnotesize\color{llmxMuted}llmXive}%
  \fancyhead[R]{\llmxivemono\footnotesize\color{llmxMuted}\@title{}}%
  \fancyfoot[C]{\llmxivemono\footnotesize\color{llmxMuted}\thepage}%
  \renewcommand{\headrulewidth}{0pt}%
  \renewcommand{\footrulewidth}{0pt}%
}
\AtBeginDocument{\pagestyle{llmxive}}

% ── Abstract ───────────────────────────────────────────────────────────────
\renewenvironment{abstract}
  {\par\vspace{0.5em}\noindent
   \begin{minipage}{0.94\textwidth}
   \small
   \itshape\color{llmxText2}\quad}
  {\end{minipage}\par\vspace{1.4em}}

% ── List spacing (tighter, more web-like) ──────────────────────────────────
\RequirePackage{enumitem}
\setlist[itemize]{leftmargin=1.4em, itemsep=0.1em, parsep=0.1em, topsep=0.25em}
\setlist[enumerate]{leftmargin=1.6em, itemsep=0.1em, parsep=0.1em, topsep=0.25em}

% ── Code (verbatim + listings) ──────────────────────────────────────────────
\RequirePackage{listings}
\lstdefinestyle{llmxive}{
  basicstyle    = {\llmxivemono\small\color{llmxText}},
  keywordstyle  = {\color{llmxAccent}\bfseries},
  commentstyle  = {\color{llmxMuted}\itshape},
  stringstyle   = {\color{llmxAccent2}},
  backgroundcolor = \color{llmxAccentSoft!30},
  frame         = leftline,
  framesep      = 6pt,
  rulecolor     = \color{llmxLine},
  xleftmargin   = 8pt,
  showstringspaces = false,
  breaklines    = true,
}
\lstset{style=llmxive}

% ── Tables ─────────────────────────────────────────────────────────────────
\RequirePackage{booktabs}
\renewcommand{\arraystretch}{1.15}

% ── A friendly default for bibliographies (natbib) ─────────────────────────
\RequirePackage[numbers, sort&compress]{natbib}
\bibliographystyle{plainnat}

\endinput
