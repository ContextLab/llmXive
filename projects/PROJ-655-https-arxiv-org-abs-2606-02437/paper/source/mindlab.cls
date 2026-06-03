% Mind Lab technical-report template.
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{mindlab}[2026/05/12 Mind Lab paper template]
\LoadClassWithOptions{article}
\pdfoutput=1

\RequirePackage[top=2.25cm,bottom=2.5cm,left=2.5cm,right=2.5cm,columnsep=0.65cm]{geometry}
\RequirePackage{microtype}
\microtypesetup{expansion=false}
\RequirePackage{placeins}
\RequirePackage{hyphenat}
\RequirePackage{setspace}
\RequirePackage{parskip}
\RequirePackage[english]{babel}
\RequirePackage{etoolbox}
\RequirePackage{graphicx}
\RequirePackage{booktabs}
\RequirePackage{multirow}
\RequirePackage{bm}
\RequirePackage[table,dvipsnames]{xcolor}
\RequirePackage[most]{tcolorbox}
\RequirePackage[T1]{fontenc}
\RequirePackage{caption}
\RequirePackage{subcaption}
\RequirePackage{titlesec}
\RequirePackage{fancyhdr}
\RequirePackage{fontawesome5}
\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
\RequirePackage[round,authoryear]{natbib}

\def\mindlabtemplatepath{mindlab_templates}
\newcommand{\mindlabasset}[1]{\mindlabtemplatepath/assets/#1}

\renewcommand*\ttdefault{cmvtt}
\DeclareFontFamily{T1}{optimistic}{}
\DeclareFontShape{T1}{optimistic}{m}{n}{<-> s * [0.88] \mindlabasset{optimistic}}{}
\DeclareFontShape{T1}{optimistic}{b}{n}{<-> s * [0.88] \mindlabasset{optimistic}}{}
\pdfmapline{+optimistic < \mindlabasset{Optimistic.ttf} <T1-WGL4.enc}
\renewcommand{\sfdefault}{optimistic}

\DisableLigatures[f]{family=sf*}

\definecolor{mindlabblue}{HTML}{002BFF}
\definecolor{mindlabbluepale}{HTML}{DEE6FF}
\definecolor{mindlabfg}{HTML}{111111}
\definecolor{mindlabmuted}{HTML}{4A4A4A}
\definecolor{mindlabbg}{HTML}{F2F2F0}
\definecolor{mindlabink}{HTML}{1F2A2E}
\colorlet{mindlabbluewash}{mindlabbluepale!45}
\colorlet{mindlabline}{mindlabblue!72!mindlabfg}
\colorlet{mindlabgrid}{mindlabbluepale!70}
\colorlet{mindlabneutral}{mindlabfg!58}

\colorlet{metablue}{mindlabblue}
\colorlet{metafg}{mindlabfg}
\colorlet{metabg}{mindlabbg}
\colorlet{macaronprimary}{mindlabblue}
\colorlet{macarondark}{mindlabfg}
\colorlet{macaronsoft}{mindlabbluewash}
\colorlet{macaronink}{mindlabink}

\newcommand{\mindlabaccent}[1]{{\bfseries\color{mindlabblue}#1}}
\newcommand{\macaronaccent}[1]{\mindlabaccent{#1}}
\newcommand{\nm}[1]{#1}

\hypersetup{
  colorlinks,
  linkcolor=mindlabblue,
  citecolor=mindlabblue,
  urlcolor=mindlabblue,
  filecolor=mindlabblue
}
\def\bibfont{\small}
\addto{\captionsenglish}{\renewcommand{\refname}{References}}
\setlength{\headheight}{28pt}

\newcommand{\sectionfont}{\fontsize{14}{16}\selectfont}
\newcommand{\subsectionfont}{\fontsize{12}{14}\selectfont}
\titleformat{\section}{\sectionfont\sffamily\bfseries}{\textcolor{mindlabblue}{\thesection}}{0.75em}{}
\titleformat{\subsection}{\subsectionfont\sffamily\bfseries}{\textcolor{mindlabblue}{\thesubsection}}{0.65em}{}
\titleformat{\subsubsection}{\normalsize\sffamily\bfseries}{\textcolor{mindlabblue}{\thesubsubsection}}{0.6em}{}
\titleformat*{\paragraph}{\bfseries}

\newcommand{\bffont}{\fontsize{9.5}{11}\selectfont}
\DeclareTextFontCommand{\textbf}{\bffont\bfseries\sffamily}
\providecommand{\botrule}{\bottomrule}

\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\sffamily\textbf{\textcolor{mindlabblue}{#1 #2}}} #3}
\captionsetup{singlelinecheck=false,format=custom,labelsep=custom,font=small}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}

\newlength{\cftbeforesubsecskip}
\providecommand{\cftdotsep}{4.5}
\providecommand{\cftdotfill}[1]{\dotfill}
\providecommand{\cftsecleader}{\dotfill}
\providecommand{\cftsecfont}{}
\providecommand{\cftsecpagefont}{}
\providecommand{\cfttoctitlefont}{}

\newcommand\mindlab@addtolist[5][]{
  \begingroup
    \if\relax#3\relax\def\sep{}\else\def\sep{#5}\fi
    \let\protect\@unexpandable@protect
    \xdef#3{\expandafter{#3}\sep #4[#1]{#2}}%
  \endgroup
}

\newcommand\mindlab@sup[1]{\ifblank{#1}{}{\textcolor{mindlabblue}{$^{#1}$}}}

\newcommand\authorlist{}
\newcommand\authorformat[2][]{{\sffamily\bfseries #2\mindlab@sup{#1}}}
\renewcommand\author[2][]{\mindlab@addtolist[#1]{#2}{\authorlist}{\authorformat}{, }}

\newcommand\affiliationlist{}
\newcommand\affiliationformat[2][]{{\normalsize \mindlab@sup{#1}#2}}
\newcommand\affiliation[2][]{\mindlab@addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{, }}

\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\small \mindlab@sup{#1}#2}}
\newcommand\contribution[2][]{\mindlab@addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}

\newcommand\metadatalist{}
\newcommand\metadataformat[2][]{{\small {\sffamily\bfseries\textcolor{mindlabblue}{#1:}} #2}}
\newcommand\metadata[2][]{\mindlab@addtolist[#1]{#2}{\metadatalist}{\metadataformat}{\par}}
\newcommand\checkdatalist{}
\newcommand\checkdata[2][]{\metadata[#1]{#2}}

\newif\ifhasabstract
\hasabstractfalse
\renewcommand{\abstract}[1]{%
  \def\@tempa{#1}%
  \ifx\@tempa\empty\hasabstractfalse\else\hasabstracttrue\fi
  \def\abstractlist{{\color{mindlabfg}#1}}%
}

\newcommand{\keywords}[1]{\metadata[Keywords]{#1}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}
\renewcommand\date[1]{\metadata[\faCalendar\ Date]{#1}}
\newcommand\correspondence[1]{\metadata[\faEnvelope\ Correspondence]{#1}}
\newcommand\code[1]{\metadata[Code]{#1}}

\newcommand{\titlefont}{\fontsize{21}{24}\selectfont}
\renewcommand{\title}[2][]{\newcommand{\titlelist}{{\titlefont\sffamily\bfseries #2\par}}}

\newcommand{\beginabstract}{{\sffamily\bfseries\textcolor{mindlabblue}{Abstract}\par}}
\newcommand{\beginappendix}{\appendix{\titlefont\sffamily\bfseries\textcolor{mindlabblue}{Appendix}\par}}
\newcommand{\backmatter}{}
\newcommand{\bmhead}[1]{\section*{#1}}

\fancypagestyle{firststyle}{
  \fancyhf{}
  \fancyfoot[C]{\thepage}
}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\newcommand{\mindlab@logo}{%
  \includegraphics[height=12mm]{\mindlabasset{logo/mindlab-logo-transparent.png}}%
}
\newcommand{\mindlab@secondarylogos}{}
\newcommand{\secondarylogos}[1]{\gdef\mindlab@secondarylogos{#1}}

\newcommand{\mindlab@titlebar}{\textcolor{mindlabblue}{\hrule height 0.8pt}}

\newcommand{\mymaketitle}{%
  \tcbset{enhanced,frame hidden}
  \tcbset{left=0.5cm,right=0.5cm,top=0.5cm,bottom=0.5cm}
  \tcbset{arc=14pt,colback=mindlabbg,before skip=0pt}
  \tcbset{grow to left by=1.5pt,grow to right by=1.5pt}
  \begin{tcolorbox}
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0.5cm}
    \begin{minipage}{0.98\textwidth}
      \setlength{\parskip}{0pt}
      \begin{minipage}[c]{0.48\textwidth}
        \raggedright
        \mindlab@logo
      \end{minipage}%
      \hfill
      \begin{minipage}[c]{0.48\textwidth}
        \raggedleft
        \mindlab@secondarylogos
      \end{minipage}\par
      \vspace{0.6em}
      \mindlab@titlebar
      \vspace{1.35em}
      \centering
      \setstretch{1.04}
      \titlelist
      \vspace{0.35em}
      \mindlab@titlebar
      \vspace{0.65em}
    \end{minipage}
    {
      \setlength{\parskip}{0cm}
      \centering
      \nohyphens
      \authorlist\par
      \ifdefempty{\affiliationlist}{}{%
        \vskip 0.2cm
        \affiliationlist\par
      }
      \contributionlist\par
    }
    \ifhasabstract
      {
        \setlength{\parskip}{0.12cm}
        \abstractlist\par
      }
    \fi
    \vskip 0.5cm
    {
      \setlength{\parskip}{0cm}
      \ifdefempty{\metadatalist}{\vspace*{0.1cm}}{\metadatalist\par}
    }
  \end{tcolorbox}
  \tcbset{reset}
  \thispagestyle{firststyle}
  \FloatBarrier
}

\if@twocolumn
\renewcommand{\maketitle}{
\twocolumn[%
  \mymaketitle
  \vskip 0.38cm
]
}
\else
\renewcommand{\maketitle}{
  \mymaketitle
}
\fi
