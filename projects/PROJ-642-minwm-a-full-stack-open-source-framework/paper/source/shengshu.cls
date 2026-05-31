%%%%%%%%%
% Copyright (c) 2026, ShengShu.  Licensed under CC BY-SA 4.0.
%
% This template is a modified version of the NVIDIA Tech Report template,
% which was itself based on Google DeepMind's style file.
% Original NVIDIA template: https://arxiv.org/abs/2509.24695 by Junsong Chen et al., 2025.
% Original DeepMind template by Shakir Mohamed et al., London, 2018.
%
% Basic style file for ShengShu Tech Report papers --
% based on Google DeepMind's style file (see below).
%
% Licence: This template is released under the Creative Commons licence
% Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
%
% This class allows for several options depending on the preferences of the authors.
% Use it in the following way, with the full set of option possible:
% \documentclass[11pt, a4paper, twocolumn, logo, address, copyright, nonumbering,
% internal]{techreport}
%
% Options:
%    - 11pt: Sets the normal font size of the text. Can be only 10, 11, 12pt.
%    - a4paper: Paper size. Usually would not adjust.
%    - twocolumn: Makes the paper into two column mode; single column by default.
%    - logo: Adds the ShengShu logo to the top right. No logo included if left out.
%    - address: Add a postal address for correspondence to the bottom footer.
%    - copyright: Add a copyright statement to the first page of the paper in the left footnote
%    - nonumbering: Uses unnumbered sections.
%    - internal: for internal only docs that should not be shared externally.
%           Can only use techreportnumber with this option.
%
% %%%%%%%%%%%%%%%

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{shengshu}

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
% Fonts and language
\AtEndOfClass{\RequirePackage{microtype}}
\RequirePackage[english]{babel}
\RequirePackage{amsthm, amsmath, amsfonts, amssymb}
\RequirePackage{url}
\RequirePackage[colorlinks=true, citecolor=shengshublue, linkcolor=shengshublue]{hyperref}
\RequirePackage{pifont}
\RequirePackage{textcomp}
\RequirePackage[overload]{textcase}
%% *Graphics, tables and other formatting
\RequirePackage{graphicx}
\RequirePackage{colortbl}
\RequirePackage{booktabs}
\RequirePackage{changepage}
\RequirePackage{enumitem}
\RequirePackage{tabularx}
\RequirePackage{datetime}
% Headers and footers
\RequirePackage{fancyhdr}
\RequirePackage{lastpage}
% Lists and their spacing
\RequirePackage{enumitem}
\setlist[itemize]{noitemsep}
\setlist[enumerate]{noitemsep}
% Title, Abstract, Bibliography
\RequirePackage[explicit]{titlesec}
\RequirePackage{bibentry}
\RequirePackage{mdframed}
\RequirePackage{caption}
\RequirePackage{needspace}

\RequirePackage[svgnames,dvipsnames]{xcolor}
\definecolor{shengshublue}{HTML}{296d97}

%%======== Margins and column spacing ========
\RequirePackage[left=1in,%
right=1in,%
top=1in,%
bottom=1in,%
headheight=40pt,%
headsep=20pt,%
letterpaper]{geometry}%
\setlength{\columnsep}{15pt}
\setlength{\parskip}{0.5\baselineskip}

%% *Custom font sizes and styles
\newcommand{\watermarkfont}{\color{black50}\normalfont\fontsize{10}{12}\selectfont}
\newcommand{\headerfont}{\normalfont\sffamily\fontsize{8}{10}\selectfont}
% Title: 18pt bold black (preserved from lab.cls style)
\newcommand{\titlefont}{\bfseries\fontsize{16}{20}\selectfont}

\newcommand{\datesfont}{\normalfont\sffamily\itshape\fontsize{8}{10}\selectfont}
\newcommand\urlheaderfont{\color{blue}\fontsize{8}{10}\selectfont}
\newcommand{\absfont}{\linespread{1.1}\fontsize{10}{12}\selectfont}
\newcommand{\keywordstitlefont}{\bfseries\linespread{1.2}\fontsize{8}{10}\selectfont}
\newcommand{\keywordsfont}{\itshape\linespread{1.2}\fontsize{11}{12}\selectfont}
\newcommand{\copyrightfont}{\normalfont\fontsize{7}{9}\selectfont}
\newcommand{\footerfont}{\color{black}\normalfont\fontsize{8}{10}\selectfont}
\newcommand{\subjectfont}{\color{white}\bfseries\fontsize{10}{12}\selectfont}
\newcommand{\headingfont}{\color{shengshublue}\bfseries\fontsize{12}{10}\selectfont}

\newcommand{\keywords}[1]{\def\@keywords{#1}}
\newtoks\correspondingauthor
\newtoks\paperurl
\newtoks\reportnumber

% ISO-8601 date format
\newdateformat{monthyeardate}{\THEYEAR-\THEMONTH-\THEDAY}

\setcounter{secnumdepth}{3}
\ifthenelse{\boolean{nonumbering}}{\setcounter{secnumdepth}{0}}{}

%%========  Author and affiliation ========
\RequirePackage{authblk}
\renewcommand{\thefootnote}{\fnsymbol{footnote}}
\setcounter{Maxaffil}{0}
\setlength{\affilsep}{0.2em}
\renewcommand\Authfont{\normalfont\bfseries\fontsize{10}{11}\selectfont}
\renewcommand\Affilfont{\normalfont\fontsize{10}{11}\selectfont}
\renewcommand\AB@affilsepx{, \protect\Affilfont}
\renewcommand\Authands{ and }

\newcommand{\internalonly}{* Equal Contribution}
\newcommand{\copyrightext}{\footerfont \the\year{} ShengShu.}


%%======== Header and Footer Content ========
%
% Header and Footer for the first page
% Logo on the RIGHT side (preserved from lab.cls style)
\pagestyle{fancy}
\fancypagestyle{firststyle}{
	\fancyhead[L]{}
	\fancyhead[R]{
		\ifthenelse{\boolean{logo}}{
			\includegraphics[height=12mm]{shengshu_logo.png}
            \vskip -1.25cm
	 }{}
}
\fancyhead[C]{}
%
\fancyfoot[L]{}
\fancyfoot[R]{}
\fancyfoot[C]{\footerfont\bfseries\relax}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
}


% Header and Footer for pages from 2 onwards
\fancyhead[L,R]{}
\fancyhead[C]{\footerfont \@title}
\fancyfoot[L]{}
\fancyfoot[R]{}
\fancyfoot[C]{\sffamily\footerfont \thepage}

% Header and footer rules (coloured).
\renewcommand{\headrulewidth}{1pt}
\renewcommand{\footrulewidth}{0pt}
\let\DefaultHeadRule\headrule
\let\DefaultFootRule\footrule
\renewcommand{\headrule}{\color{gray}\DefaultHeadRule}
\renewcommand{\footrule}{\textcolor{gray}{\DefaultFootRule}}

\RequirePackage{tcolorbox}
\tcbuselibrary{skins}

%%========  Bibliography using bibtex ========
\addto{\captionsenglish}{\renewcommand{\refname}{References}}
\newcommand{\citeas}[1]{\Needspace*{8\baselineskip}\noindent\bibentry{#1}}

%%======== Title bar rules (preserved from lab.cls) ========
\newcommand{\@toptitlebar}{
  {\color{shengshublue}\hrule height 2.5pt}
  \vskip 6mm
}
\newcommand{\@bottomtitlebar}{
  \vskip 5mm
  {\color{shengshublue}\hrule height 1pt}
}

%%======== Abstract and section formatting ========
\def\xabstract{abstract}
\long\def\abstract#1\end#2{\def\two{#2}\ifx\two\xabstract
	\long\gdef\theabstract{\ignorespaces#1}
	\def\go{\end{abstract}}\else
\typeout{^^J^^J PLEASE DO NOT USE ANY \string\begin\space \string\end^^J
	COMMANDS WITHIN ABSTRACT^^J^^J}#1\end{#2}
\gdef\theabstract{\vskip12pt BADLY FORMED ABSTRACT: PLEASE DO
NOT USE {\tt\string\begin...\string\end} COMMANDS WITHIN
THE ABSTRACT\vskip12pt}\let\go\relax\fi
\go}

% Define an environment with abstract content and styling (tcolorbox)
\newcommand{\abscontent}{
	\noindent
	\begin{tcolorbox}[
	  enhanced,
	  colframe=shengshublue,
	  colback=white,
	  arc=4pt,
	  boxrule=0.8pt,
	  left=10pt, right=10pt, top=8pt, bottom=8pt,
	  title={\centering\textbf{Abstract}},
	  fonttitle=\large,
	  coltitle=black,
	  colbacktitle=white,
	  attach boxed title to top center={yshift=-\tcboxedtitleheight/2},
	  boxed title style={colframe=white, colback=white, boxrule=0pt}
	]
	\absfont \theabstract
	\@ifundefined{@keywords}{}{
		\vskip1em \noindent \keywordsfont  Keywords: \@keywords}
	\end{tcolorbox}
}

\if@twocolumn%
\renewcommand{\maketitle}{
	\twocolumn[
	\begin{adjustwidth}{0pt}{0pt}
		\begin{center}
			{
				\@toptitlebar
				{ \titlefont
				\@title\par}%
				\@bottomtitlebar
				\vskip11pt
				{\@author\par}
				\vskip10pt%
			}%
		\end{center}
	\end{adjustwidth}
    \abscontent
    \vskip20pt%
	]
	\thispagestyle{firststyle}
}%
\else% \@twocolumnfalse
\renewcommand{\maketitle}{\bgroup\setlength{\parindent}{0pt}
	\begin{adjustwidth}{0pt}{0pt}
		\begin{center}
			{
				\@toptitlebar
				{\titlefont \@title\par}%
				\@bottomtitlebar
				\vskip10pt
				{\@author\par}
				\vskip10pt%
			}%
		\end{center}
	\end{adjustwidth}
	\egroup
	{%
		{\abscontent}
	}%
	\thispagestyle{firststyle}
}%
\fi

\titleformat{\section}
{\headingfont}
{\thesection.}
{0.5em}
{#1}
[]
\titleformat{name=\section,numberless}
{\headingfont}
{}
{0em}
{#1}
[]
\titleformat{\subsection}
{\color{shengshublue}\bfseries\fontsize{11}{10}\selectfont}
{\thesubsection.}
{0.5em}
{#1}
[]
\titleformat{\subsubsection}
{\color{shengshublue}\bfseries\normalsize}
{\thesubsubsection.}
{0.5em}
{#1}
[]

\titlespacing*{\section}{0pc}{3ex plus4pt minus3pt}{5pt}
\titlespacing*{\subsection}{0pc}{2.5ex plus3pt minus2pt}{2pt}
\titlespacing*{\subsubsection}{0pc}{2ex plus2.5pt minus1.5pt}{2pt}

%%======== Captions in tables and figures ========
\DeclareCaptionLabelSeparator{colonsp}{: }
\captionsetup{labelfont={bf},%
labelsep=colonsp,%
figurename=Figure,%
singlelinecheck=on,%
}
