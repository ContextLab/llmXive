%% =====================================================================
%%  llmxive.cls — Document class for llmXive papers
%%  ---------------------------------------------------------------------
%%  A clean, modern LaTeX class matching the llmXive web aesthetic:
%%  Dartmouth green accents, Fraunces serif + JetBrains Mono.
%%
%%  Compile with:  xelatex  (recommended)  or  lualatex
%%  Fallback:      pdflatex (uses libertinus + inconsolata substitutes)
%%
%%  Usage:
%%      \documentclass{llmxive}
%%      \title{...}
%%      \author{...}
%%      \affiliation{...}
%%      \paperid{llmXive-2026-014}
%%      \paperstatus{Peer Reviewed}
%%      \begin{document}
%%        \maketitle
%%        \begin{abstract} ... \end{abstract}
%%        ...
%%      \end{document}
%% =====================================================================
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{llmxive}[2026/05/13 v1.0 llmXive paper class]

%% ---- options & base class -----------------------------------------------
\newif\ifllmx@twocolumn   \llmx@twocolumnfalse
\newif\ifllmx@draft       \llmx@draftfalse
\DeclareOption{twocolumn}{\llmx@twocolumntrue}
\DeclareOption{draft}{\llmx@drafttrue}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
\LoadClass[11pt,letterpaper]{article}

%% ---- engine detection ---------------------------------------------------
\RequirePackage{iftex}

%% ---- core packages ------------------------------------------------------
\RequirePackage[T1]{fontenc}
\RequirePackage[utf8]{inputenc}
\RequirePackage{geometry}
\RequirePackage{xcolor}
\RequirePackage{microtype}
\RequirePackage{graphicx}
\RequirePackage{caption}
\RequirePackage{booktabs}
\RequirePackage{array}
\RequirePackage{tabularx}
\RequirePackage{colortbl}    %% provides \arrayrulecolor
\RequirePackage{enumitem}
\RequirePackage{amsmath,amssymb,amsthm,mathtools}
\RequirePackage{titlesec}
\RequirePackage{titletoc}
\RequirePackage{fancyhdr}
\RequirePackage{ragged2e}
\RequirePackage{etoolbox}
\RequirePackage{xparse}
\RequirePackage{calc}
\RequirePackage{tikz}
\RequirePackage{listings}
\RequirePackage{hyperref}
\RequirePackage{url}
%% Note: we deliberately do NOT load `cite` here; many arXiv papers use
%% `natbib` (with \citep/\citet) and `cite` clashes. If the paper's preamble
%% doesn't load a bibliography manager, the default LaTeX \cite still works.

%% ---- geometry -----------------------------------------------------------
\geometry{
  letterpaper,
  top=1.05in,
  bottom=1.0in,
  inner=1.05in,
  outer=1.20in,
  headheight=14pt,
  headsep=18pt,
  footskip=28pt,
}

%% ---- palette (Dartmouth green family) -----------------------------------
\definecolor{llmxGreen}    {HTML}{00693E}
\definecolor{llmxGreenDeep}{HTML}{004F2E}
\definecolor{llmxGreen2}   {HTML}{0A8A55}
\definecolor{llmxInk}      {HTML}{0A2818}
\definecolor{llmxInk2}     {HTML}{2D4A3E}
\definecolor{llmxMuted}    {HTML}{5A7268}
\definecolor{llmxLine}     {HTML}{C9D6CC}
\definecolor{llmxBg}       {HTML}{F0F5F1}
\definecolor{llmxTint}     {HTML}{E6EFE8}
\definecolor{llmxPaper}    {HTML}{F7FAF7}

%% ---- fonts --------------------------------------------------------------
\ifPDFTeX
  % pdflatex path — use substitutes that ship with TeX Live
  \IfFileExists{libertinus.sty}{\RequirePackage{libertinus}}{%
    \IfFileExists{libertine.sty}{\RequirePackage{libertine}}{}}
  \IfFileExists{inconsolata.sty}{\RequirePackage[scaled=0.94]{inconsolata}}{}
  \renewcommand{\sfdefault}{\rmdefault} % keep everything serif-ish
\else
  % xelatex / lualatex path — real Fraunces + JetBrains Mono
  \RequirePackage{fontspec}
  \RequirePackage{unicode-math}
  \defaultfontfeatures{Ligatures=TeX}
  \IfFontExistsTF{Fraunces}{%
    % Fraunces is a variable font with `wght`, `opsz`, `SOFT`, `WONK` axes.
    % LuaLaTeX (`luaotfload`) honors `RawFeature={+axis={...}}` correctly;
    % XeTeX ignores the wght axis and renders at the font's default (heavy)
    % weight regardless. We recommend lualatex (see README) but the class
    % sets the axis explicitly so XeTeX at least picks a sensible upright
    % when wght isn't applied. Body wght=400; display wght=400, opsz=144.
    \setmainfont{Fraunces}[
      UprightFeatures = {RawFeature={+axis={wght=400}},
                         SmallCapsFont={Fraunces}, SmallCapsFeatures={Letters=SmallCaps}},
      BoldFeatures    = {RawFeature={+axis={wght=700}}},
      ItalicFeatures  = {RawFeature={+axis={wght=400}}},
      BoldItalicFeatures = {RawFeature={+axis={wght=700}}},
      Numbers         = OldStyle,
    ]%
  }{\IfFontExistsTF{TeX Gyre Pagella}{\setmainfont{TeX Gyre Pagella}}{}}
  \IfFontExistsTF{JetBrains Mono}{%
    \setmonofont{JetBrains Mono}[Scale=0.86]%
  }{\IfFontExistsTF{Inconsolata}{\setmonofont{Inconsolata}[Scale=0.92]}{}}
  \IfFontExistsTF{JetBrains Mono}{%
    \newfontfamily\llmxmono{JetBrains Mono}[Scale=0.86]%
  }{\newcommand{\llmxmono}{\ttfamily}}
  \IfFontExistsTF{Fraunces}{%
    % Display family at wght=400; the opsz axis bumps proportions for big titles.
    % NoCommonLigatures + -liga,-clig,-dlig disable the fi/fl/ffi ligatures
    % for headings and the author block. Fraunces's `fi` ligature collides
    % with names like "Latifi" (the substitution leaves a visible gap
    % between the ligature glyph and the following `i`), and there's no
    % typographic benefit at display sizes anyway. We also turn ligatures
    % off in BOTH the upright and the synthesised italic variants because
    % `\itshape` of the display family falls back to a slanted upright (no
    % real italic shape is declared) and the ligature substitution applies
    % to that slanted upright too.
    \newfontfamily\llmxdisplay{Fraunces}[
      RawFeature = {+axis={wght=400,opsz=144};-liga;-clig;-dlig;-rlig},
      Ligatures = {NoCommon,NoRequired},
      Numbers=Lining]%
  }{\newcommand{\llmxdisplay}{}}
  % math
  \IfFontExistsTF{STIX Two Math}{\setmathfont{STIX Two Math}}{}
\fi

% small helper for engine-agnostic mono
\providecommand{\llmxmono}{\ttfamily}
\providecommand{\llmxdisplay}{}

%% ---- base text ----------------------------------------------------------
\color{llmxInk}
\linespread{1.13}
\setlength{\parindent}{1.15em}
\setlength{\parskip}{0pt}
\frenchspacing

%% ---- transparent figure-cache redirect ---------------------------------
%% When `scripts/restyle_arxiv_paper.py` runs, it normalizes each figure
%% through ghostscript (workaround for Adobe Illustrator export quirks
%% that lualatex clips) and writes the result to
%%   <source_dir>/figs-sanitized/<same-relative-path>
%% leaving the originals under `figs/` untouched.
%%
%% We redefine `\includegraphics` so that calls like
%%   \includegraphics{figs/X.pdf}
%% are silently rewritten to `figs-sanitized/figs/X.pdf` when that file
%% exists. The body's bytes are NOT modified — the redirect happens at
%% \includegraphics-call time. If no sanitized copy exists, the original
%% path is used (the class is safe to use without the cache).
\let\llmx@origincludegraphics\includegraphics
\renewcommand{\includegraphics}[2][]{%
  \IfFileExists{figs-sanitized/#2}%
    {\llmx@origincludegraphics[#1]{figs-sanitized/#2}}%
    {\IfFileExists{figs-sanitized/#2.pdf}%
      {\llmx@origincludegraphics[#1]{figs-sanitized/#2.pdf}}%
      {\llmx@origincludegraphics[#1]{#2}}}%
}

%% ---- compatibility no-ops for stripped packages ------------------------
%% When an externally-submitted paper's preamble called \doublespacing /
%% \onehalfspacing / \singlespacing (from `setspace`) or \linenumbers
%% (from `lineno`) and those packages were stripped during restyle,
%% provide harmless no-ops so the body's calls don't error. The class's
%% own \linespread controls the line spacing.
\providecommand{\doublespacing}{}
\providecommand{\onehalfspacing}{}
\providecommand{\singlespacing}{}
\providecommand{\linenumbers}{}
\providecommand{\nolinenumbers}{}

%% ---- metadata storage ---------------------------------------------------
\newcommand{\llmx@paperid}{}
\newcommand{\llmx@paperstatus}{Preprint}
\newcommand{\llmx@papercategory}{Research paper}
% Affiliation/correspondence/reviewscore default to a TeX-empty token so
% the `\ifx \llmx@X \@empty` tests in the title block actually fire when
% no value was set. `\newcommand{...}{}` would *not* match `\@empty` —
% the macro token isn't `\@empty` even though its expansion is.
\let\llmx@affiliation\@empty
\let\llmx@correspondence\@empty
\let\llmx@reviewscore\@empty

\newcommand{\paperid}[1]{\renewcommand{\llmx@paperid}{#1}}
\newcommand{\paperstatus}[1]{\renewcommand{\llmx@paperstatus}{#1}}
\newcommand{\papercategory}[1]{\renewcommand{\llmx@papercategory}{#1}}
\newcommand{\affiliation}[1]{\renewcommand{\llmx@affiliation}{#1}}
\newcommand{\correspondence}[1]{\renewcommand{\llmx@correspondence}{#1}}
\newcommand{\reviewscore}[1]{\renewcommand{\llmx@reviewscore}{#1}}

%% Editorial-summary + artifact-list metadata. Stored as macros so the
%% title block can lay them out deterministically on the first (title)
%% page. `\seteditorialsummary` accepts the rendered summary body (already
%% containing `\edsection{}` headers + prose). `\seteditorialartifacts`
%% accepts a list of `\edartifact{label}{url}` lines.
%% Setting `\llmx@editorialbyline` empty suppresses the byline.
\newcommand{\llmx@editorialsummary}{}
\newcommand{\llmx@editorialartifacts}{}
\newcommand{\llmx@editorialbyline}{llmXive Editorial}
%% Flags: set to "1" by \seteditorial*; the title block consults these
%% (rather than \ifx \@empty, which is unreliable across engines) so the
%% editorial-summary box only appears when the publication agent actually
%% supplied content.
\newcommand{\llmx@hassummary}{0}
\newcommand{\llmx@hasartifacts}{0}
\newcommand{\seteditorialsummary}[1]{%
  \renewcommand{\llmx@editorialsummary}{#1}%
  \renewcommand{\llmx@hassummary}{1}%
}
\newcommand{\seteditorialartifacts}[1]{%
  \renewcommand{\llmx@editorialartifacts}{#1}%
  \renewcommand{\llmx@hasartifacts}{1}%
}
\newcommand{\seteditorialbyline}[1]{\renewcommand{\llmx@editorialbyline}{#1}}

%% ---- title block -------------------------------------------------------
\renewcommand{\maketitle}{%
  \begin{titlepage*}\end{titlepage*}%
}
\newenvironment{titlepage*}{}{%
  \begingroup
    \thispagestyle{llmx@title}%
    % top rule
    \noindent\color{llmxGreen}\rule{\textwidth}{1.2pt}\par
    \vspace{6pt}%
    % kicker row: brand left, meta right
    \noindent
    \begin{minipage}[t]{0.55\textwidth}
      {\llmxmono\footnotesize\color{llmxGreen}%
        \MakeUppercase{llmXive}\hspace{0.6em}\textcolor{llmxMuted}{\textbar}\hspace{0.6em}%
        \textcolor{llmxInk2}{Automated scientific discovery}}
    \end{minipage}\hfill
    \begin{minipage}[t]{0.40\textwidth}\raggedleft
      {\llmxmono\footnotesize\color{llmxMuted}%
        \ifx\llmx@paperid\@empty\else\llmx@paperid\quad\textbar\quad\fi
        \llmx@papercategory}\\[2pt]
      {\llmxmono\footnotesize
        \color{llmxGreen}\textbullet\ \color{llmxInk2}\llmx@paperstatus}
    \end{minipage}\par
    %% Title-block vspacing: balance against editorial-summary box height so
    %% the editorial summary fits on the title page. Tighter than the original
    %% "pure title page" layout — by design, since the editorial summary +
    %% artifact strip are now part of the title page.
    \vspace{24pt}%
    % title
    {\llmxdisplay\fontsize{28}{32}\selectfont\color{llmxInk}%
      \raggedright\@title\par}%
    \vspace{12pt}%
    % authors. Inside the author block we locally redefine \texttt so that
    % email addresses embedded in \author{...} (a common arXiv pattern, e.g.
    % \texttt{first.last@example.edu}) render in the same monospace small
    % muted style as the \affiliation and \correspondence lines — instead of
    % inheriting the larger italic display font that wraps the rest of the
    % author block.
    {\llmxdisplay\fontsize{12.5}{16}\selectfont\itshape\color{llmxInk2}%
      \raggedright
      \renewcommand{\texttt}[1]{%
        {\normalfont\llmxmono\footnotesize\color{llmxMuted}##1}%
      }%
      \@author\par}%
    \ifx\llmx@affiliation\@empty\else
      \vspace{5pt}%
      {\llmxmono\footnotesize\color{llmxMuted}\raggedright\llmx@affiliation\par}%
    \fi
    \ifx\llmx@correspondence\@empty\else
      \vspace{3pt}%
      {\llmxmono\footnotesize\color{llmxMuted}\raggedright
        Correspondence: \textcolor{llmxGreen}{\llmx@correspondence}\par}%
    \fi
    \vspace{10pt}%
    \noindent\color{llmxLine}\rule{\textwidth}{0.4pt}\par
    \vspace{10pt}%
    %% ── editorial summary (rendered inline so it's guaranteed on the
    %% title page; positioned between the title rule and the abstract).
    %% Compact layout — tight inner-sep + no spacer between summary box
    %% and artifact strip so editorial + artifacts always travel together
    %% on the title page. We test the explicit \llmx@hassummary flag
    %% (set by \seteditorialsummary) rather than \ifx \@empty — \ifx on
    %% \renewcommand'd tokens is unreliable across engines.
    \if1\llmx@hassummary
      \noindent\begin{tikzpicture}
        \node[
          draw=llmxLine, line width=0.4pt,
          fill=llmxTint,
          rounded corners=2pt,
          inner sep=10pt,
          text width=\textwidth-22pt,
        ] (edbox) \bgroup
          {\llmxmono\footnotesize\color{llmxGreen}\MakeUppercase{Editorial Summary}}%
          \ifx\llmx@editorialbyline\@empty\else
            \hfill{\llmxmono\scriptsize\color{llmxMuted}\llmx@editorialbyline}%
          \fi\\[4pt]
          %% Force a uniform baseline inside the box. Without this the
          %% global \linespread{1.13} interacts with TikZ's \pgfutil@font-
          %% rebuild and lines drift wider top-to-bottom. Setting
          %% \linespread{1.0} + an explicit \selectfont locks the
          %% line-height to the font's natural value.
          \linespread{1.0}\selectfont
          \color{llmxInk2}\footnotesize\ignorespaces
          \llmx@editorialsummary
        \egroup ;
      \end{tikzpicture}\par
      \vspace{6pt}%
    \fi
    \if1\llmx@hasartifacts
      \noindent{\llmxmono\footnotesize\color{llmxGreen}\MakeUppercase{Artifacts}\hspace{0.8em}}%
      {\llmxmono\footnotesize\color{llmxInk2}\llmx@editorialartifacts}\par
      \vspace{6pt}%
      \noindent\color{llmxLine}\rule{\textwidth}{0.4pt}\par
      \vspace{10pt}%
    \fi
  \endgroup
  \@afterheading
}

%% ---- abstract ----------------------------------------------------------
\renewenvironment{abstract}{%
  \begingroup
    \noindent
    \begin{minipage}{\textwidth}
      {\llmxmono\footnotesize\color{llmxGreen}\MakeUppercase{Abstract}}\par\vspace{4pt}%
      \color{llmxInk2}\itshape\small\noindent\ignorespaces
}{%
    \end{minipage}\par
    \vspace{10pt}%
    \noindent\color{llmxLine}\rule{\textwidth}{0.4pt}\par
    \vspace{18pt}%
  \endgroup
}

%% ---- keywords ----------------------------------------------------------
\newcommand{\keywords}[1]{%
  \par\vspace{-6pt}%
  \noindent
  {\llmxmono\footnotesize\color{llmxGreen}\MakeUppercase{Keywords}\quad}%
  {\llmxmono\footnotesize\color{llmxInk2}#1}\par
  \vspace{14pt}%
}

%% ---- section heads -----------------------------------------------------
\titleformat{\section}[block]
  {\normalfont\Large\llmxdisplay\color{llmxInk}}
  {\color{llmxGreen}\itshape\thesection\hspace{0.6em}}
  {0pt}{}
\titleformat{\subsection}[block]
  {\normalfont\large\llmxdisplay\color{llmxInk}}
  {\color{llmxGreen}\itshape\thesubsection\hspace{0.55em}}
  {0pt}{}
\titleformat{\subsubsection}[block]
  {\normalfont\normalsize\llmxdisplay\itshape\color{llmxInk2}}
  {\color{llmxGreen}\thesubsubsection\hspace{0.5em}}
  {0pt}{}
\titleformat{\paragraph}[runin]
  {\normalfont\normalsize\bfseries\color{llmxInk}}
  {}{0pt}{}[\hspace{0.4em}]
\titlespacing*{\section}      {0pt}{22pt}{8pt}
\titlespacing*{\subsection}   {0pt}{16pt}{6pt}
\titlespacing*{\subsubsection}{0pt}{12pt}{4pt}
\titlespacing*{\paragraph}    {0pt}{8pt}{0pt}

%% ---- captions ----------------------------------------------------------
\captionsetup{
  font={small,color=llmxInk2},
  labelfont={color=llmxGreen},
  labelsep=quad,
  labelformat=simple,
  format=plain,
  justification=raggedright,
  singlelinecheck=false,
}
\renewcommand{\thefigure}{\arabic{figure}}
\renewcommand{\thetable}{\arabic{table}}
\DeclareCaptionLabelFormat{llmxlabel}{%
  {\llmxmono\footnotesize\MakeUppercase{#1}\,#2}}
\captionsetup{labelformat=llmxlabel}

%% ---- lists -------------------------------------------------------------
\setlist[itemize,1]{leftmargin=1.4em, label={\textcolor{llmxGreen}{\textbullet}}, itemsep=2pt, topsep=4pt}
\setlist[itemize,2]{leftmargin=1.4em, label={\textcolor{llmxGreen}{\textendash}}, itemsep=2pt, topsep=2pt}
\setlist[enumerate,1]{leftmargin=1.8em, label={\textcolor{llmxGreen}{\arabic*.}}, itemsep=2pt, topsep=4pt}

%% ---- tables ------------------------------------------------------------
\setlength{\arrayrulewidth}{0.4pt}
\arrayrulecolor{llmxLine}
\renewcommand{\arraystretch}{1.18}

%% ---- theorem environments ----------------------------------------------
\newtheoremstyle{llmx}%
  {10pt}{10pt}%        space above / below
  {\itshape\color{llmxInk2}}% body font
  {0pt}%               indent
  {\bfseries\color{llmxGreen}}% head font
  {.}%                 punct after head
  { }%                 space after head
  {}%                  head spec (use default)
\theoremstyle{llmx}
\newtheorem{theorem}{Theorem}[section]
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\newtheoremstyle{llmxdef}%
  {10pt}{10pt}{\normalfont\color{llmxInk}}{0pt}%
  {\bfseries\color{llmxGreen}}{.}{ }{}
\theoremstyle{llmxdef}
\newtheorem{definition}{Definition}[section]
\newtheorem{remark}{Remark}[section]
\newtheorem{example}{Example}[section]

\renewenvironment{proof}{%
  \par\noindent\textit{\color{llmxGreen}Proof.}\hspace{0.5em}\ignorespaces}
  {\hfill\textcolor{llmxGreen}{$\blacksquare$}\par\vspace{4pt}}

%% ---- callout box (key result / takeaway) -------------------------------
\NewDocumentEnvironment{keyresult}{O{Key result}}{%
  \par\vspace{8pt}%
  \begingroup
    \noindent\begin{tikzpicture}
      \node[
        draw=llmxGreen, line width=0.5pt,
        fill=llmxTint,
        rounded corners=2pt,
        inner sep=12pt,
        text width=\textwidth-26pt,
      ] (box) \bgroup
        {\llmxmono\footnotesize\color{llmxGreen}\MakeUppercase{#1}}\\[3pt]
        \color{llmxInk}\ignorespaces
}{%
      \egroup ;
    \end{tikzpicture}
  \endgroup
  \par\vspace{6pt}%
}

%% ---- editorial summary (eLife-style "Public review" callout) ----------
%% Drafted by the llmXive publication agent on acceptance; rendered as a
%% labeled callout at the top of the published paper. The optional
%% argument is the byline (defaults to "llmXive Editorial").
%%
%% Usage:
%%   \begin{editorialsummary}[llmXive Editorial Board]
%%     Plain-English summary of significance, strengths, limitations.
%%     ...optionally split into \edsection{Significance} / \edsection{Strengths}
%%     / \edsection{Weaknesses} blocks for an eLife-style breakdown.
%%   \end{editorialsummary}
%%
%%   \editorialartifacts{%
%%     \edartifact{Project page}{https://...}%
%%     \edartifact{Reviews}{https://...}%
%%     \edartifact{Code}{https://...}%
%%   }
\NewDocumentEnvironment{editorialsummary}{O{llmXive Editorial}}{%
  \par\vspace{4pt}%
  \begingroup
    \noindent\begin{tikzpicture}
      \node[
        draw=llmxLine, line width=0.4pt,
        fill=llmxTint,
        rounded corners=2pt,
        inner sep=14pt,
        text width=\textwidth-30pt,
      ] (edbox) \bgroup
        {\llmxmono\footnotesize\color{llmxGreen}\MakeUppercase{Editorial Summary}}%
        \hfill
        {\llmxmono\scriptsize\color{llmxMuted}#1}\\[6pt]
        \color{llmxInk2}\small\ignorespaces
}{%
      \egroup ;
    \end{tikzpicture}
  \endgroup
  \par\vspace{4pt}%
}

%% A sub-header inside an editorial-summary block (eLife-style sections).
\providecommand{\edsection}[1]{%
  \par\smallskip\noindent
  {\llmxmono\footnotesize\color{llmxGreen}\MakeUppercase{#1}}\par\smallskip%
}

%% Artifact-link list (separate from the summary text so the agent can draft
%% the summary in pure prose, and the script can attach links deterministically).
\NewDocumentCommand{\editorialartifacts}{m}{%
  \par\vspace{2pt}%
  \begingroup
    \noindent\color{llmxLine}\rule{\textwidth}{0.2pt}\par
    \vspace{4pt}%
    \noindent{\llmxmono\footnotesize\color{llmxGreen}\MakeUppercase{Artifacts}}\par
    \vspace{3pt}%
    {\llmxmono\footnotesize\color{llmxInk2}\raggedright #1\par}%
    \vspace{6pt}%
    \noindent\color{llmxLine}\rule{\textwidth}{0.4pt}\par
    \vspace{14pt}%
  \endgroup
}

%% Single artifact entry: rendered as "Label  →  url" with the URL hyperlinked.
%% Multiple entries separated by `\par` or `\\` inside \editorialartifacts.
\providecommand{\edartifact}[2]{%
  {\color{llmxMuted}#1}\hspace{0.6em}{\color{llmxGreen}\textrightarrow}\hspace{0.4em}\href{#2}{\color{llmxGreen}#2}\par
}

%% ---- listings (code) ---------------------------------------------------
\lstdefinestyle{llmx}{
  basicstyle      = \llmxmono\footnotesize\color{llmxInk},
  keywordstyle    = \color{llmxGreen}\bfseries,
  commentstyle    = \itshape\color{llmxMuted},
  stringstyle     = \color{llmxGreen2},
  numberstyle     = \llmxmono\scriptsize\color{llmxMuted},
  backgroundcolor = \color{llmxPaper},
  frame           = single,
  framesep        = 8pt,
  framerule       = 0.4pt,
  rulecolor       = \color{llmxLine},
  numbers         = left,
  numbersep       = 10pt,
  xleftmargin     = 22pt,
  xrightmargin    = 6pt,
  aboveskip       = 12pt,
  belowskip       = 12pt,
  breaklines      = true,
  breakatwhitespace=true,
  showstringspaces=false,
  tabsize         = 2,
  columns         = fullflexible,
  keepspaces      = true,
}
\lstset{style=llmx}

%% ---- inline code shortcut ---------------------------------------------
\let\llmx@oldtt\texttt
\renewcommand{\texttt}[1]{{\llmxmono\color{llmxGreenDeep}#1}}

%% ---- hyperlinks --------------------------------------------------------
\hypersetup{
  colorlinks   = true,
  linkcolor    = llmxGreenDeep,
  citecolor    = llmxGreen,
  urlcolor     = llmxGreen,
  filecolor    = llmxGreen,
  pdfborder    = {0 0 0},
  pdfcreator   = {llmXive paper class},
  bookmarksopen= true,
  bookmarksnumbered=true,
}
\urlstyle{tt}

%% ---- running header / footer ------------------------------------------
\fancypagestyle{llmx@title}{%
  \fancyhf{}\renewcommand{\headrulewidth}{0pt}\renewcommand{\footrulewidth}{0pt}
  \fancyfoot[L]{\llmxmono\footnotesize\color{llmxMuted}llmXive\quad\textbullet\quad page \thepage}
  \fancyfoot[R]{\llmxmono\footnotesize\color{llmxMuted}\today}
}
\fancypagestyle{llmx@body}{%
  \fancyhf{}%
  \renewcommand{\headrulewidth}{0pt}%
  \renewcommand{\footrulewidth}{0pt}%
  \fancyhead[L]{\llmxmono\footnotesize\color{llmxMuted}\MakeUppercase{\llmx@runningtitle}}
  \fancyhead[R]{\llmxmono\footnotesize\color{llmxMuted}\llmx@paperid}
  \fancyfoot[L]{\llmxmono\footnotesize\color{llmxMuted}llmXive\;\textcolor{llmxGreen}{\textbullet}\;\the\year}
  \fancyfoot[R]{\llmxmono\footnotesize\color{llmxMuted}\thepage\,/\,\pageref*{LastPage}}
}
\pagestyle{llmx@body}

% running short title (defaults to \@title)
\newcommand{\llmx@runningtitle}{llmXive Paper}
\newcommand{\runningtitle}[1]{\renewcommand{\llmx@runningtitle}{#1}}

\AtBeginDocument{%
  \ifx\llmx@runningtitle\@empty
    \renewcommand{\llmx@runningtitle}{\@title}\fi
}

\RequirePackage{lastpage}

%% ---- bibliography (numeric, llmXive-styled) ---------------------------
\renewcommand{\refname}{References}
\renewenvironment{thebibliography}[1]{%
  \section*{\refname}%
  \addcontentsline{toc}{section}{\refname}%
  \list{\llmxmono\footnotesize\color{llmxGreen}[\arabic{enumi}]}%
       {\settowidth\labelwidth{[#1]}%
        \leftmargin\labelwidth
        \advance\leftmargin\labelsep
        \usecounter{enumi}%
        \itemsep 4pt
        \parsep 0pt}%
  \sloppy\clubpenalty4000\widowpenalty4000%
  \sfcode`\.\@m
  \small\color{llmxInk2}}%
 {\endlist}

%% ---- footnotes ---------------------------------------------------------
\renewcommand{\footnoterule}{\noindent\color{llmxLine}\rule{0.4\textwidth}{0.3pt}\vspace{4pt}}
\renewcommand{\thefootnote}{\textcolor{llmxGreen}{\arabic{footnote}}}

%% ---- TOC styling -------------------------------------------------------
\renewcommand{\contentsname}{Contents}
\titlecontents{section}[0pt]
  {\addvspace{4pt}\llmxdisplay}
  {\color{llmxGreen}\itshape\thecontentslabel\hspace{0.6em}}{}
  {\titlerule*[0.6pc]{\color{llmxLine}.}\contentspage}
\titlecontents{subsection}[1.5em]
  {\small\llmxdisplay\color{llmxInk2}}
  {\color{llmxGreen}\thecontentslabel\hspace{0.5em}}{}
  {\titlerule*[0.6pc]{\color{llmxLine}.}\contentspage}

%% ---- handy macros ------------------------------------------------------
\providecommand{\llmxnote}[1]{%
  \marginpar{\raggedright\llmxmono\scriptsize\color{llmxGreen}#1}}
\providecommand{\todo}[1]{%
  \ifllmx@draft{\color{llmxGreen2}\llmxmono\footnotesize[TODO: #1]}\fi}

%% ---- draft watermark ---------------------------------------------------
\ifllmx@draft
  \RequirePackage{everypage}
  \AddEverypageHook{%
    \begin{tikzpicture}[remember picture, overlay]
      \node[rotate=45, scale=8, opacity=0.05, color=llmxGreen] at (current page.center) {DRAFT};
    \end{tikzpicture}}
\fi

%% =====================================================================
%% Spec 009 additions (FR-015, FR-016, FR-020)
%% Bounded figure widths, canonical author block, fail-loud on unsupported.
%% =====================================================================

%% FR-015: \figwidth{narrow|column|full} -> sets the next \includegraphics width.
%% Used by the deterministic restyle pipeline (src/llmxive/pipeline/pdf_pipeline/
%% normalize_figures.py) which rewrites every \includegraphics to a bounded set.
\newlength{\llmx@figw}
\newcommand{\figwidth}[1]{%
  \def\llmx@figw@arg{#1}%
  \ifx\llmx@figw@arg\@empty
    \setlength{\llmx@figw}{\linewidth}%
  \else
    \edef\llmx@figw@narrow{narrow}%
    \edef\llmx@figw@column{column}%
    \edef\llmx@figw@full{full}%
    \ifx\llmx@figw@arg\llmx@figw@narrow
      \setlength{\llmx@figw}{0.45\linewidth}%
    \else\ifx\llmx@figw@arg\llmx@figw@column
      \setlength{\llmx@figw}{\linewidth}%
    \else\ifx\llmx@figw@arg\llmx@figw@full
      \setlength{\llmx@figw}{\textwidth}%
    \else
      \setlength{\llmx@figw}{\linewidth}%
    \fi\fi\fi
  \fi
  \llmx@figw
}

%% FR-016: canonical author block.
%% \authorblock{Name1, Name2}{Affiliation 1; Affiliation 2}{email1, orcid1}
%% Produces a uniform layout regardless of how the arXiv source formatted authors.
\newcommand{\authorblock}[3]{%
  \author{#1}%
  \ifx\\#2\\\else\renewcommand{\llmx@affiliation}{#2}\fi
  \ifx\\#3\\\else\renewcommand{\llmx@correspondence}{#3}\fi
}

%% FR-020: \unsupportedblock{<construct>}{<body>} fails loudly so the pipeline
%% explicitly surfaces an unsupported construct rather than silently rendering
%% raw text. The deterministic restyle pipeline wraps unsupported environments
%% in this macro.
\newcommand{\unsupportedblock}[2]{%
  \PackageError{llmxive}{Unsupported construct: #1}{The llmxive class does not yet support the construct named "#1". The deterministic pdf_pipeline marked it for explicit attention. Either add support to llmxive.cls or exclude this paper from the supported-PDFs registry. Body was: #2}%
}

\endinput
