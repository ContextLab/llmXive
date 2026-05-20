
%%======== Pckage options and base class ========
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{MemTensor}
\LoadClassWithOptions{article}
\pdfoutput=1

%%======== Packages Required ========
\RequirePackage{microtype}
\RequirePackage{placeins}
\RequirePackage{hyphenat}
\RequirePackage{setspace}
\RequirePackage{parskip}
\RequirePackage[latin, english]{babel}
\RequirePackage{lipsum}
\RequirePackage{helvet}
\RequirePackage{etoolbox}
\RequirePackage{fancyhdr}  % custom headers/footers
\RequirePackage{ulem}  % 引用下划线
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
\RequirePackage[T1]{fontenc}

%%======== Layout ========
\RequirePackage[top=2.75cm, bottom=2.5cm, left=2.5cm, right=2.5cm, columnsep=0.65cm]{geometry}
%去除页眉页脚横线
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

%%======== Color ========
\definecolor{membg}{HTML}{5A7EFA}
\definecolor{memblue}{HTML}{5A7EFA}
\definecolor{memblue2}{HTML}{F0F8FF}
\newcommand{\memblue}[1]{{\bfseries\color[HTML]{5A7EFA} #1}}

%%========  Custom font sizes and styles ========
\renewcommand{\sfdefault}{cmr}
\renewcommand{\rmdefault}{cmr}
\newcommand{\sectionfont}{\fontsize{12}{10}\selectfont}
\newcommand{\subsectionfont}{\fontsize{11}{10}\selectfont}
\newcommand{\bffont}{\fontsize{8.8}{10}\selectfont}
\newcommand{\authorfont}{\bfseries\fontsize{12}{14}\selectfont}
\newcommand{\affiliationfont}{\fontsize{10}{12}\selectfont}
\newcommand{\contributionfont}{\fontsize{10}{12}\selectfont}
\newcommand{\checkdatafont}{\fontsize{7.92}{10}\selectfont}
\newcommand{\abstractinfont}{\fontsize{10}{12}\selectfont}
\newcommand{\titlefont}{\fontsize{21}{23}\selectfont}
\newcommand{\abstractfont}{\fontsize{12}{12}\selectfont}
\usepackage[subfigure]{tocloft}
\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}}
\renewcommand{\cftsecfont}{\sffamily}
\renewcommand{\cftsecpagefont}{\sffamily}{\color{memblue}}
\renewcommand{\cfttoctitlefont}{\sffamily\sectionfont\memblue}
\DeclareTextFontCommand{\textbf}{\bffont\bfseries\sffamily}

%%======== Title and Section format  ========
\renewcommand{\title}[1]{\newcommand{\titlelist}{\titlefont{\sffamily\bfseries #1}}}
\RequirePackage{titlesec}
\titleformat*{\paragraph}{\itshape}
\titleformat*{\section}{\sectionfont\sffamily\bfseries\memblue}
\titleformat*{\subsection}{\subsectionfont\sffamily\bfseries\memblue}
\titleformat*{\subsubsection}{\normalsize\sffamily\bfseries\memblue}
\newcommand{\beginabstract}{\abstractfont{\sffamily\bfseries \memblue{Abstract}\par}}
\newcommand{\beginappendix}{\appendix{\titlefont\sffamily \memblue{Appendix}\par}}


%%======== References ========
\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
\hypersetup{
  colorlinks,
  linkcolor=memblue,
  citecolor=memblue,
  urlcolor=memblue
}
%%========  Bibliography using bibtex ========
\RequirePackage[numbers, sort&compress]{natbib}
\def\bibfont{\small}
\addto{\captionsenglish}{\renewcommand{\refname}{References}}
\newcommand{\citeas}[1]{\Needspace*{8\baselineskip}\noindent\bibentry{#1}}


%%======== Caption format ========
\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\sffamily\textbf{#1 #2}} #3}
\captionsetup{singlelinecheck=true,format=custom,labelsep=custom,font=small}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}


%%======== Authors and affiliations infos ========
\renewcommand\addtolist[5][]{
  \begingroup
    \if\relax#3\relax\def\sep{}\else\def\sep{#5}\fi
    \let\protect\@unexpandable@protect
    \xdef#3{\expandafter{#3}\sep #4[#1]{#2}}%
  \endgroup
}

\newcommand\authorlist{}
\newcommand\authorformat[2][]{\authorfont {\sffamily #2$^{#1}$}}
\renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{, }}
\newcommand\affiliationlist{}
\newcommand\affiliationformat[2][]{{\affiliationfont {\sffamily\selectfont $^{#1}$#2}}}
\newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{, }}
\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\contributionfont $^{#1}$#2}}
\newcommand\contribution[2][]{\addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}
\newcommand\checkdatalist{}
\newcommand\checkdataformat[2][]{{\small {\checkdatafont\sffamily \bfseries #1:} #2}}
\newcommand\checkdata[2][]{\addtolist[#1]{#2}{\checkdatalist}{\checkdataformat}{\par}}
\renewcommand{\abstract}[1]{\def\abstractlist{{\abstractinfont #1}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}
\renewcommand\date[1]{\checkdata[Date]{#1}}
\newcommand\correspondence[1]{\checkdata[Correspondence]{#1}}

%%======== Header and Footer Content ========
\fancypagestyle{firststyle}{
    \fancyhead[R]{
        % Other content for the left side of the header, if any
    }
    \fancyhead[L]{
        \vskip 7.5mm
    \includegraphics[width=42.4mm,height=7.6mm]{assets/logo.png}
    }

}
\newcommand{\@toptitlebar}{
 \vspace*{0mm}
  \memblue{\hrule height 0.5pt }
  \vskip 6mm
  %\vskip -\parskip%
}
\newcommand{\@bottomtitlebar}{
  \vskip 6mm
  %\vskip -\parskip
  \memblue{\hrule height 0.0pt}
  %\vskip 0.09in%
}

%%======== Titlebox ========
\newcommand{\mymaketitle}{%
  \tcbset{enhanced}
  \tcbset{left=8mm}
  \tcbset{right=8mm}
  \tcbset{top=6mm}
  \tcbset{bottom=6mm}
  \tcbset{colback=white}
  \tcbset{colframe=membg}
  \tcbset{boxrule=0.5pt}
  \tcbset{before skip=0pt}
  \tcbset{grow to left by=1.5pt}
  \tcbset{grow to right by=1.5pt}
  \tcbset{arc=2.5mm}
  \tcbset{colback=memblue2}
      {
      \setlength{\parskip}{0mm}
    \raggedright
      \nohyphens
      %

      {
      \@toptitlebar

        \titlelist\par
         \@bottomtitlebar
      }
      \vskip 6mm
      \authorlist
      \vskip 3mm
      %
      \affiliationlist\par
      \vskip 3mm
      %
      \contributionlist\par
    }
   \vskip 6mm

  \begin{tcolorbox}
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0cm}

    %

    \begin{center}
        \beginabstract
        \vskip 3mm
    \end{center}

    \abstractlist\par
    %
    \vskip 3mm
    %
    {
      \setlength{\parskip}{0cm}
      \ifdefempty{\checkdatalist}{\vspace*{0.65cm}}{\checkdatalist\par}
    }
  \end{tcolorbox}
  \tcbset{reset}
  \FloatBarrier
  \thispagestyle{firststyle}

}

\if@twocolumn%
\renewcommand{\maketitle}{
\twocolumn[%
 \vskip 3mm
  \mymaketitle
  \vskip 8mm
]
}%
\else%
\renewcommand{\maketitle}{
  \mymaketitle
  \vskip 8mm
}%
\fi
