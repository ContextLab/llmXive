\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{gtech}
\LoadClassWithOptions{article}

\RequirePackage[top=2.25cm, bottom=2.5cm, left=2.5cm, right=2.5cm, columnsep=0.65cm]{geometry}
\RequirePackage{microtype}
\RequirePackage{placeins}
\RequirePackage{hyphenat}
\RequirePackage{setspace}
\RequirePackage{parskip}
\RequirePackage[latin, english]{babel}
\RequirePackage{etoolbox}

\DisableLigatures[f]{family=sf*}

\RequirePackage{graphicx}
\RequirePackage{subcaption}

\RequirePackage{booktabs}
\RequirePackage{nicematrix}
\RequirePackage{multirow}
\RequirePackage{bm}
\newcommand{\nm}[1]{#1}

\RequirePackage[most]{tcolorbox}
\RequirePackage{xcolor}
\definecolor{gtechblue}{HTML}{0064E0}
\definecolor{gtechfg}{HTML}{1C2B33}
\definecolor{gtechbg}{HTML}{e6f6ff}

\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
\hypersetup{
  colorlinks,
  linkcolor=gtechblue,
  citecolor=gtechblue,
  urlcolor=gtechblue
}

\RequirePackage[round,authoryear]{natbib}
\def\bibfont{\small}

\RequirePackage{titlesec}
\titleformat*{\paragraph}{\itshape\bfseries\raggedright}
\titleformat*{\section}{\large\bfseries\raggedright}
\titleformat*{\subsection}{\normalsize\bfseries\raggedright}
\titleformat*{\subsubsection}{\normalsize\bfseries\raggedright}
\DeclareTextFontCommand{\textbf}{\bfseries\raggedright}

\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\sffamily\textbf{#1 #2}} #3}
\captionsetup{singlelinecheck=false,format=custom,labelsep=custom,font=small}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}

\renewcommand*\ttdefault{cmvtt}
\RequirePackage[T1]{fontenc}

\DeclareFontFamily{T1}{optimistic}{}
\DeclareFontShape{T1}{optimistic}{m}{n}{<-> s * [0.88] assets/optimistic}{}
\pdfmapline{+optimistic < assets/Optimistic.ttf <T1-WGL4.enc}
\renewcommand{\sfdefault}{ptm}
\renewcommand{\rmdefault}{ptm}
\renewcommand{\normalsize}{\fontsize{11}{14}\selectfont}

\renewcommand\addtolist[5][]{
  \begingroup
    \if\relax#3\relax\def\sep{}\else\def\sep{#5}\fi
    \let\protect\@unexpandable@protect
    \xdef#3{\expandafter{#3}\sep #4[#1]{#2}}%
  \endgroup
}

\newcommand\authorlist{}
\newcommand\authorformat[2][]{{\fontfamily{optimistic}\selectfont \bfseries #2$^{#1}$}}
\renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{, }}


\newcommand\affiliationlist{}
\newcommand\affiliationformat[2][]{{\normalsize $^{#1}$#2}}
\newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{, }}

\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\small $^{#1}$#2}}
\newcommand\contribution[2][]{\addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}
\newcommand\projectpageline{}
\newcommand\authornoteline{}

\newcommand\gtechdatalist{}
\newcommand\gtechdataformat[2][]{{\small {\sffamily \bfseries #1:} #2}}
\newcommand\gtechdata[2][]{\addtolist[#1]{#2}{\gtechdatalist}{\gtechdataformat}{\par}}

\renewcommand{\abstract}[1]{\def\abstractlist{{\color{gtechfg} #1}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}

\renewcommand\date[1]{\gtechdata[Date]{#1}}
\newcommand\correspondence[1]{\gtechdata[Correspondence]{#1}}

\renewcommand{\title}[1]{\newcommand{\titlelist}{{\huge\sffamily\bfseries #1}}}

\newcommand{\beginappendix}{\appendix{\huge\sffamily Appendix\par}}

\newcommand{\secondlogocmd}{}
\newcommand{\addsecondlogo}[2][2cm]{%
    \renewcommand{\secondlogocmd}{\includegraphics[width=#1]{#2}}%
}

\newcommand{\mymaketitle}{%
  \tcbset{enhanced,frame hidden}
  \tcbset{left=0.5cm}
  \tcbset{right=0.5cm}
  \tcbset{top=0.7cm}
  \tcbset{bottom=0.5cm}
  \tcbset{arc=10pt}
  \tcbset{colback=gtechbg}
  \tcbset{before skip=0pt}
  \tcbset{grow to left by=1.5pt}
  \tcbset{grow to right by=1.5pt}

  \tcbset{overlay={\node[
    anchor=south east,
    at= (frame.south east),
    xshift=-0.5cm,
    yshift=0.6cm] {
        \ifx\secondlogocmd\empty
            \includegraphics[width=2cm]{assets/logoant.pdf}
        \else
            \secondlogocmd\hspace{0.2cm}\includegraphics[width=1.95cm,valign=c]{assets/logoant.pdf}
        \fi
    };}}

  \begin{tcolorbox}
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
      \ifdefempty{\authornoteline}{}{{\small\authornoteline\par}}
      \ifdefempty{\projectpageline}{}{\vskip 0.18cm {\centering\projectpageline\par}}
    }
    \abstractlist\par
    \vskip 0.5cm
    {
      \setlength{\parskip}{0cm}
      \ifdefempty{\gtechdatalist}{\vspace*{0.65cm}}{\gtechdatalist\par}
    }
  \end{tcolorbox}
  \tcbset{reset}
  \FloatBarrier
}

\if@twocolumn%
\renewcommand{\maketitle}{
\twocolumn[%
  \mymaketitle
  \vskip 0.38cm
]
}%
\else%
\renewcommand{\maketitle}{
  \mymaketitle
}%
\fi
