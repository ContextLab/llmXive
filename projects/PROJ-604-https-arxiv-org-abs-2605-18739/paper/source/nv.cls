%%%%%%%%%
% Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
% modified from Arxiv RecurrentGemma Tech report
%%%%%%%%%

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{nv}

%%======== Package options and base class ========
\RequirePackage{xifthen}
\newboolean{nonumbering}
\newboolean{logo}
\newboolean{address}
\newboolean{copyright}
\newboolean{internal}
\DeclareOption{nonumbering}{\setboolean{nonumbering}{true}}
\DeclareOption{logo}{\setboolean{logo}{true}}
\DeclareOption{address}{\setboolean{address}{true}}
\DeclareOption{copyright}{\setboolean{copyright}{true}}
\DeclareOption{internal}{\setboolean{internal}{true}}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{extarticle}}
\ProcessOptions
\LoadClass{extarticle}

%%======== Packages Required ========
\AtEndOfClass{\RequirePackage[tracking=smallcaps]{microtype}}
\RequirePackage[utf8]{inputenc}
\RequirePackage[english]{babel}
\RequirePackage{amsthm, amsmath, amsfonts, amssymb}
\RequirePackage{cmap}
\RequirePackage[T1]{fontenc}
\RequirePackage{url}
\RequirePackage[colorlinks=true, citecolor=nvidiagreen, linkcolor=nvidiagreen]{hyperref}
\RequirePackage{pifont}
\RequirePackage{textcomp}
\RequirePackage{graphicx}
\RequirePackage{colortbl}
\RequirePackage{booktabs}
\RequirePackage{changepage}
\RequirePackage{enumitem}
\RequirePackage{tabularx}
\RequirePackage{datetime}
\RequirePackage{fancyhdr}
\RequirePackage{lastpage}
\RequirePackage[explicit]{titlesec}
\RequirePackage{bibentry}
\RequirePackage{mdframed}
\RequirePackage{caption}
\RequirePackage{needspace}
\RequirePackage{lmodern}
\RequirePackage[scaled=1.0]{zlmtt}
\RequirePackage[svgnames,dvipsnames]{xcolor}

\definecolor{nvidiagreen}{HTML}{76B900}

%%======== Margins and column spacing ========
\RequirePackage[
left=2.2cm,
right=2.2cm,
top=3cm,
bottom=3cm,
headheight=40pt,
headsep=20pt,
a4paper
]{geometry}

\setlength{\columnsep}{15pt}
\setlength{\parskip}{0.5\baselineskip}

%%======== Custom font sizes and styles ========
\newcommand{\watermarkfont}{\color{black50}\normalfont\fontsize{10}{12}\selectfont}
\newcommand{\headerfont}{\normalfont\sffamily\fontsize{8}{10}\selectfont}
\newcommand{\titlefont}{\color{nvidiagreen}\normalfont\bfseries\fontsize{17}{20}\selectfont}
\newcommand{\datesfont}{\normalfont\sffamily\itshape\fontsize{8}{10}\selectfont}
\newcommand\urlheaderfont{\color{blue}\fontsize{8}{10}\selectfont}
\newcommand{\absfont}{\linespread{1.1}\fontsize{10}{12}\selectfont}
\newcommand{\keywordstitlefont}{\bfseries\linespread{1.2}\fontsize{8}{10}\selectfont}
\newcommand{\keywordsfont}{\itshape\linespread{1.2}\fontsize{11}{12}\selectfont}
\newcommand{\copyrightfont}{\normalfont\fontsize{7}{9}\selectfont}
\newcommand{\footerfont}{\color{black}\normalfont\fontsize{8}{10}\selectfont}
\newcommand{\subjectfont}{\color{white}\bfseries\fontsize{10}{12}\selectfont}
\newcommand{\headingfont}{\color{black}\bfseries\fontsize{13}{14}\selectfont}

\newcommand{\keywords}[1]{\def\@keywords{#1}}
\newtoks\correspondingauthor
\newtoks\paperurl
\newtoks\reportnumber

% Running title for page headers.
% Usage in main.tex:
% \runningtitle{Short one-line title}
\makeatletter
\newcommand{\runningtitle}[1]{\gdef\@runningtitle{#1}}
\makeatother

%%======== Dates ========
\newdateformat{monthyeardate}{\THEYEAR-\THEMONTH-\THEDAY}

\setcounter{secnumdepth}{3}
\ifthenelse{\boolean{nonumbering}}{\setcounter{secnumdepth}{0}}{}

%%======== Author and affiliation ========
\RequirePackage{authblk}
\setcounter{Maxaffil}{0}
\setlength{\affilsep}{0.2em}
\renewcommand\Authfont{\normalfont\bfseries\fontsize{9}{13}\selectfont}
\renewcommand\Affilfont{\normalfont\fontsize{8}{10}\selectfont}

\makeatletter
\renewcommand\AB@affilsepx{, \protect\Affilfont}
\makeatother

\renewcommand\Authands{ and }

\newcommand{\internalonly}{* Equal Contribution}
\newcommand{\copyrightext}{\footerfont \textcopyright\, \the\year{} NVIDIA. All rights reserved.}

%%======== Header and Footer Content ========
\pagestyle{fancy}

\fancypagestyle{firststyle}{
\fancyhead[L]{
  \ifthenelse{\boolean{logo}}{
    \includegraphics[width=90pt]{assets/nvlogo2}
  }{}
}
\fancyhead[R]{
  \ifdefined\paperurl
    \if\relax\the\paperurl\relax
    \else
      \href{\the\paperurl}{\urlheaderfont \itshape \the\paperurl}\\
    \fi
  \else
  \fi
  {\footerfont\monthyeardate\today}
}
\fancyhead[C]{}

\fancyfoot[L]{%
\footerfont
\textcopyright\ \the\year\ NVIDIA. All rights reserved.\hspace{1em}
$^{*}$ Equal contribution \quad
$^{\dagger}$ Project Lead
}
\fancyfoot[R]{
  \ifthenelse{\boolean{internal}}{
    \ifdefined\reportnumber
      \if\relax\the\reportnumber\relax
      \else
        \footerfont\itshape {\footerfont \bfseries NVIDIA Technical Report \the\reportnumber}
      \fi
    \else
    \fi
  }{\footerfont\bfseries\relax}
}
\fancyfoot[C]{\footerfont\bfseries\relax}
}

% Header and Footer for pages from 2 onwards
\fancyhead[L,R]{}
\makeatletter
\AtBeginDocument{
  \@ifundefined{@runningtitle}{
    \gdef\@runningtitle{\@title}
  }{}
}
\fancyhead[C]{\footerfont \@runningtitle}
\makeatother
\fancyfoot[C]{}
\fancyfoot[L]{}
\fancyfoot[R]{\footerfont \thepage}

\renewcommand{\headrulewidth}{1pt}
\renewcommand{\footrulewidth}{1pt}
\let\DefaultHeadRule\headrule
\let\DefaultFootRule\footrule
\renewcommand{\headrule}{\color{gray}\DefaultHeadRule}
\renewcommand{\footrule}{\textcolor{gray}{\DefaultFootRule}}

\renewenvironment{abstract}
{\par\noindent\\ \ignorespaces \bfseries}
{\par\bigskip}

%%======== Bibliography ========
\addto{\captionsenglish}{\renewcommand{\refname}{References}}
\newcommand{\citeas}[1]{\Needspace*{8\baselineskip}\noindent\bibentry{#1}}

%%======== Abstract and title formatting ========
\def\xabstract{abstract}
\long\def\abstract#1\end#2{
  \def\two{#2}
  \ifx\two\xabstract
    \long\gdef\theabstract{\ignorespaces#1}
    \def\go{\end{abstract}}
  \else
    \typeout{^^J^^J PLEASE DO NOT USE ANY \string\begin\space \string\end^^J COMMANDS WITHIN ABSTRACT^^J^^J}
    #1\end{#2}
    \gdef\theabstract{\vskip12pt BADLY FORMED ABSTRACT: PLEASE DO NOT USE {\tt\string\begin...\string\end} COMMANDS WITHIN THE ABSTRACT\vskip12pt}
    \let\go\relax
  \fi
  \go
}

\makeatletter
\newcommand{\abscontent}{
  \noindent
  \parbox{\dimexpr\linewidth}{\absfont \theabstract}
  \@ifundefined{@keywords}{}{
    \vskip1em \noindent \keywordsfont Keywords: \@keywords
  }
}

\if@twocolumn
\renewcommand{\maketitle}{
  \twocolumn[
  \begin{adjustwidth}{0pt}{24pt}
    \begin{center}
      {\titlefont \@title\par}
      \vskip11pt
      {\@author\par}
      \vskip20pt
    \end{center}
  \end{adjustwidth}
  \abscontent
  \vskip20pt
  ]
  \thispagestyle{firststyle}
}
\else
\renewcommand{\maketitle}{
  \bgroup
  \setlength{\parindent}{0pt}
  \begin{adjustwidth}{0pt}{24pt}
    \begin{center}
      {\titlefont \@title\par}
      \vskip11pt
      {\@author\par}
      \vskip20pt
    \end{center}
  \end{adjustwidth}
  \egroup
  {\abscontent}
  \thispagestyle{firststyle}
}
\fi
\makeatother

%%======== Section formatting ========
\titleformat{\section}
{\large\bfseries\headingfont}
{\thesection.}
{0.5em}
{#1}
[]

\titleformat{name=\section,numberless}
{\large\bfseries\headingfont}
{}
{0em}
{#1}
[]

\titleformat{\subsection}
{\bfseries}
{\thesubsection.}
{0.5em}
{#1}
[]

\titleformat{\subsubsection}
{\bfseries\itshape}
{\thesubsubsection.}
{0.5em}
{#1}
[]

\titlespacing*{\section}{0pc}{3ex plus4pt minus3pt}{5pt}
\titlespacing*{\subsection}{0pc}{2.5ex plus3pt minus2pt}{2pt}
\titlespacing*{\subsubsection}{0pc}{2ex plus2.5pt minus1.5pt}{2pt}

%%======== Captions ========
\DeclareCaptionLabelSeparator{pipe}{ $\vert$ }

\captionsetup{
  labelfont={},
  labelsep=space,
  figurename=Figure,
  labelsep=pipe,
  singlelinecheck=on
}