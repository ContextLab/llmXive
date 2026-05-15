% Class declarations %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{fairsnow}
\LoadClassWithOptions{article}

% Layout %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage[top=2.25cm, bottom=2.5cm, left=2.5cm, right=2.5cm, columnsep=0.65cm]{geometry}
\RequirePackage{microtype}
\RequirePackage{placeins}
\RequirePackage{hyphenat}
\RequirePackage{setspace}
\RequirePackage{parskip}
\RequirePackage[latin, english]{babel}
\RequirePackage{lipsum}
\RequirePackage{etoolbox}
\usepackage{fontawesome5}
% \usepackage{emoji}

\DisableLigatures[f]{family=sf*}

% Graphics %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{graphicx}
% \RequirePackage{subcaption}

% Tables %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{booktabs}
\RequirePackage{nicematrix}
\RequirePackage{multirow}
\RequirePackage{bm}
\newcommand{\nm}[1]{#1}

% Colorful stuff %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage[most]{tcolorbox}
\RequirePackage{xcolor}

\definecolor{snowblue}{HTML}{0064E0} % original snow color for hyperlinks
% \definecolor{snowblue}{HTML}{073B0A}

\definecolor{snowfg}{HTML}{1C2B33} % original snow color for text abstract

% Light / Pastel Greens
% \definecolor{snowbg}{HTML}{D1F2CE}   % soft - Good
\definecolor{snowbg}{HTML}{63DF4E}   % SNOW wasabi

% References %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
\hypersetup{
  colorlinks,
  linkcolor=snowblue,
  citecolor=snowblue,
  urlcolor=snowblue
}

%\RequirePackage[round,authoryear]{natbib}
\RequirePackage[numbers,square]{natbib}

\def\bibfont{\small}

% Section and caption format %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{titlesec}
\titleformat*{\paragraph}{\sffamily\bfseries}
\titleformat*{\section}{\Large\sffamily\bfseries}
\titleformat*{\subsection}{\large\sffamily\bfseries}
\titleformat*{\subsubsection}{\normalsize\sffamily\bfseries}
\DeclareTextFontCommand{\textbf}{\bfseries\sffamily}

\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\sffamily\textbf{#1 #2}} #3}
\captionsetup{singlelinecheck=false,format=custom,labelsep=custom,font=small}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}

% snow custom fonts %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\renewcommand*\ttdefault{cmvtt}
\RequirePackage[T1]{fontenc}

% Authors, affiliations, infos %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\makeatletter

\renewcommand\addtolist[5][]{
  \begingroup
    \if\relax#3\relax\def\sep{}\else\def\sep{#5}\fi
    \let\protect\@unexpandable@protect
    \xdef#3{\expandafter{#3}\sep #4[#1]{#2}}%
  \endgroup
}

\newcommand\authorlist{}
\newcommand\authorformat[2][]{{\sffamily \bfseries #2$^{#1}$}}
\renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{, }}

\newcommand\affiliationlist{}
\newcommand\affiliationformat[2][]{{\normalsize $^{#1}$#2}}
\newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{, }}

\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\small $^{#1}$#2}}
\newcommand\contribution[2][]{\addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}

\newcommand\snowdatalist{}
\newcommand\snowdataformat[2][]{{\small {\sffamily \bfseries #1:} #2}}
\newcommand\snowdata[2][]{\addtolist[#1]{#2}{\snowdatalist}{\snowdataformat}{\par}}

\renewcommand{\abstract}[1]{\def\abstractlist{{\color{snowfg} #1}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}

\renewcommand\date[1]{\snowdata[Date]{#1}}
\newcommand\correspondence[1]{\snowdata[Correspondence]{#1}}

\newcommand\github[1]{\snowdata[{\color{black}\faGithub}\ ]{#1}}
\newcommand\website[1]{\snowdata[{\color{black}\faGlobe}\ ]{#1}}

\newcommand\huggingface[1]{\snowdata[\raisebox{-0.15em}{\includegraphics[height=1em]{assets/huggingface_logo-noborder.png}}\ ]{#1}}

% Add some command here if you want to add more links in the abstract
\newcommand\morelinks[1]{\snowdata[More links]{#1}}


\renewcommand{\title}[1]{\newcommand{\titlelist}{{\huge\sffamily\bfseries #1}}}

\newcommand{\beginappendix}{\appendix{\huge\sffamily Appendix\par}}

% Titlebox %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\newcommand{\mymaketitle}{%
  \begin{tcolorbox}[
    enhanced,
    arc=10pt,
    left=0.5cm, right=0.5cm, top=0.5cm, bottom=0.5cm,
    colback=white,
    colframe=snowbg,
    boxrule=2pt,
    before skip=0pt,
    grow to left by=1.5pt,
    grow to right by=1.5pt,
    overlay={\node[
      anchor=south east,
      at=(frame.south east),
      xshift=-0.5cm,
      yshift=0.5cm] {\includegraphics[width=3cm]{assets/ServiceNow_logo.png}};}
  ]
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0.5cm}

    {
      \setlength{\parskip}{0cm}
      \raggedright
      \nohyphens

      {
        \setstretch{1.618}
        \titlelist\par
      }
      \vskip 0.2cm

      \authorlist\par
      \vskip 0.2cm

      \affiliationlist\par
      \contributionlist\par
    }

    \abstractlist\par

    \vskip 0.5cm

    {
      \setlength{\parskip}{0cm}
      \ifdefempty{\snowdatalist}{\vspace*{0.65cm}}{\snowdatalist\par}
    }
  \end{tcolorbox}

  \FloatBarrier
}

\renewcommand{\maketitle}{%
  \if@twocolumn
    \twocolumn[%
      \mymaketitle
      \vskip 0.38cm
    ]%
  \else
    \mymaketitle
  \fi
}

\makeatother