% ============================================================================
% aifrontiers.cls
% LaTeX class for Microsoft AI Frontiers technical reports
% ============================================================================
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{aifrontiers}[2025/05/15 v2.0 AI Frontiers report class]

% ---------------------------------------------------------------------------
% Base class + option handling
% ---------------------------------------------------------------------------
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax

\LoadClass{article}

% ---------------------------------------------------------------------------
% Packages
% ---------------------------------------------------------------------------
% Fonts similar to Qwen/Palatino look
\RequirePackage{tgpagella} % text only
\RequirePackage{mathpazo}  % math & text

\RequirePackage{amsmath,amssymb}
\RequirePackage{graphicx}
\RequirePackage{microtype}
\RequirePackage{setspace}
\RequirePackage{xcolor}
\RequirePackage{url}
\RequirePackage{hyperref}
\RequirePackage{fancyhdr}
\RequirePackage{natbib}
\RequirePackage[letterpaper,margin=2.5cm,headheight=24pt]{geometry}
\RequirePackage{environ}
\RequirePackage{etoolbox}
\RequirePackage[skins,breakable]{tcolorbox}

% ---------------------------------------------------------------------------
% Colors
% ---------------------------------------------------------------------------
\definecolor{darkblue}{rgb}{0, 0, 0.6}
\definecolor{aifrontiersblue}{HTML}{0050EF}
\definecolor{aifrontiersgrey}{RGB}{80,80,80}
% Softer background + teal-ish frame for abstract
% \definecolor{aifrontiersabstractbg}{HTML}{F6FBFF}
% \definecolor{aifrontiersabstractframe}{HTML}{6AB7C8}
\definecolor{aifrontiersabstractbg}{HTML}{eaf5fa}
\definecolor{aifrontiersabstractframe}{HTML}{F0F7FF}
%\definecolor{aifrontiersabstractframe}{HTML}{003366}



% ---------------------------------------------------------------------------
% Hyperref + natbib setup
% ---------------------------------------------------------------------------
\hypersetup{
  colorlinks=true,
  linkcolor=darkblue,
  citecolor=aifrontiersblue,
  urlcolor=darkblue,
}

\setcitestyle{authoryear,round,citesep={;},aysep={,},yysep={;}}

% ---------------------------------------------------------------------------
% Spacing
% ---------------------------------------------------------------------------
\setlength{\parskip}{6pt}
\setlength{\parindent}{0pt}
\onehalfspacing

% ---------------------------------------------------------------------------
% Header / footer (short title on every page)
% ---------------------------------------------------------------------------
% Short title handling
\newcommand{\AIFShortTitle}{}%
\newcommand{\shorttitle}[1]{\gdef\AIFShortTitle{#1}}%
\newcommand{\AIFDisplayShortTitle}{%
  \ifx\AIFShortTitle\@empty
    \@title
  \else
    \AIFShortTitle
  \fi
}

% Logo macro (user can redefine this in the document if desired)
\newcommand{\AIFLogo}{%
  % Default placeholder: Microsoft four squares + "AI Frontiers"
  % Replace "ms-logo" with your actual logo filename.
  \raisebox{-0.3ex}{\includegraphics[height=1.4em]{logo/ms-logo.png}}%
  \hspace{0.6em}%
  {\sffamily\bfseries\large  Microsoft}%
}

% Fancyhdr setup
\pagestyle{fancy}
\fancyhf{}%
\renewcommand{\headrulewidth}{1pt}
\renewcommand{\headrule}{%
  {\color[HTML]{4D4D4D}\hrule\@height\headrulewidth\@width\headwidth\vskip-\headrulewidth}%
}

% Default (non-first) pages: short title left, page number right
\fancyhead[L]{\sffamily\small\bfseries\AIFDisplayShortTitle}
\fancyhead[R]{\sffamily\small\thepage}

% First page style: logo, date on right
\fancypagestyle{firstpage}{%
  \fancyhf{}%
  \fancyhead[L]{%
    \AIFLogo\hspace{1em}%
    % {\sffamily\small\bfseries\AIFDisplayShortTitle}%
  }%
  \fancyhead[R]{\sffamily\small\@date}%
  \renewcommand{\headrulewidth}{1pt}%
  \renewcommand{\headrule}{%
    {\color[HTML]{4D4D4D}\hrule\@height\headrulewidth\@width\headwidth\vskip-\headrulewidth}%
  }%
}

% ---------------------------------------------------------------------------
% Abstract handling (captured and rendered in box)
% ---------------------------------------------------------------------------
\newcommand{\abstracttext}{}%
\RenewEnviron{abstract}{%
  \global\let\abstracttext\BODY
}

% ---------------------------------------------------------------------------
% Link block above abstract (HF / project / GitHub)
% ---------------------------------------------------------------------------
% URLs (user sets these in the main .tex)
\providecommand{\hflink}{}%
\providecommand{\weblink}{}%
\providecommand{\ghlink}{}%
\providecommand{\foundrylink}{}

% Default icons (PDFs expected to ship with the class)
% Users may override these in their document.

\providecommand{\websiteicon}{%
  \raisebox{-1.5pt}{\includegraphics[height=1.2em]{logo/ms-logo.png}}%
}

\providecommand{\huggingfaceicon}{%
  \raisebox{-1.5pt}{\includegraphics[height=1.2em]{logo/hf-logo.pdf}}%
}

\providecommand{\foundryicon}{%
    \raisebox{-1.5pt}{\includegraphics[height=1.2em]{logo/foundry-logo.pdf}}
}

\providecommand{\githubicon}{%
  \raisebox{-1.5pt}{\includegraphics[height=1.2em]{logo/github-logo.pdf}}%
}


\newcommand{\AIFRenderLinks}{%
  \begin{center}
    \small
    \begin{tabular}{@{}ll@{}}
      % Row 1
      \ifdefempty{\weblink}{}{%
        \websiteicon\ \href{\weblink}{\weblink}%
      }%
      &
      \ifdefempty{\hflink}{}{%
        \githubicon\ \href{\hflink}{\hflink}%
      }%
      \\
      % Row 2
      \ifdefempty{\foundrylink}{}{%
        \huggingfaceicon\ \href{\foundrylink}{\foundrylink}%
      }%
      &
      \ifdefempty{\ghlink}{}{%
        \foundryicon\ \href{\ghlink}{\ghlink}%
      }%
    \end{tabular}
  \end{center}
}


% ---------------------------------------------------------------------------
% Custom \maketitle (no page break)
% ---------------------------------------------------------------------------
\renewcommand{\maketitle}{%
  \thispagestyle{firstpage}%
  \begingroup
  \setlength{\parindent}{0pt}%
  \setlength{\parskip}{6pt}%
  % \vspace*{.5cm}%
  \begin{center}
    {\LARGE\bfseries \@title\par}%
    \vspace{1em}%
    {\@author\par}%
    {\footnotesize \@thanks\par}%
    \vspace*{5pt}
    % Work performed at MSR AI Frontiers
  \end{center}
  % \vspace{0.5em}%
  % Links block (HF/project/GitHub) if provided
  \AIFRenderLinks
  % Abstract (if provided)
  \ifx\abstracttext\@empty
  \else


    \begin{tcolorbox}[
        colback=aifrontiersabstractbg,
        colframe=aifrontiersabstractframe,
        boxrule=0.5pt,
        enhanced,
        arc=8pt,
        left=8pt,
        right=8pt,
        top=6pt,
        bottom=6pt
      ]
      \abstracttext
    \end{tcolorbox}
    
    % \vspace{0.5cm}%
  \fi
  \endgroup
}

% ---------------------------------------------------------------------------
% Section headings
% ---------------------------------------------------------------------------
\RequirePackage{titlesec}
\titleformat{\section}
  {\normalfont\Large\bfseries}
  {\thesection}{0.75em}{}
\titleformat{\subsection}
  {\normalfont\large\bfseries}
  {\thesubsection}{0.75em}{}
\titleformat{\subsubsection}
  {\normalfont\normalsize\bfseries}
  {\thesubsubsection}{0.75em}{}

% ---------------------------------------------------------------------------
% Convenience macros
% ---------------------------------------------------------------------------
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}
\newcommand{\affiliation}[1]{%
  {\normalsize\textit{#1}\par}
}

% ---------------------------------------------------------------------------
% End of class
% ---------------------------------------------------------------------------
\endinput
