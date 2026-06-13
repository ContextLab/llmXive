
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{nvidiatechreport}

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

\AtEndOfClass{\RequirePackage[tracking=smallcaps]{microtype}}
\RequirePackage[utf8]{inputenc}
\RequirePackage[english]{babel}
\RequirePackage{amsthm, amsmath, amsfonts, amssymb}
\RequirePackage{cmap}
\RequirePackage[T1]{fontenc}
\RequirePackage{url}
\RequirePackage[svgnames,dvipsnames]{xcolor}
\definecolor{nvidiagreen}{HTML}{76B900}
\RequirePackage[pdfauthor={},pdftitle={Fast-ThinkAct: Efficient Vision-Language-Action Reasoning via Verbalizable Latent Planning},hyperfootnotes=false,pagebackref=true,breaklinks=true,colorlinks=true,allcolors=nvidiagreen]{hyperref}
\RequirePackage{pifont}
\RequirePackage{textcomp}
\RequirePackage[overload]{textcase}
\RequirePackage{graphicx}
\RequirePackage{colortbl}
\RequirePackage{booktabs}
\RequirePackage{changepage}
\RequirePackage{enumitem}
\RequirePackage{tabularx}
\RequirePackage{datetime}
\RequirePackage{fancyhdr}
\RequirePackage{lastpage}
\RequirePackage{enumitem}
\setlist[itemize]{noitemsep}
\setlist[enumerate]{noitemsep}
\RequirePackage[explicit]{titlesec}
\RequirePackage{bibentry}
\RequirePackage{mdframed}
\RequirePackage{caption}
\RequirePackage{needspace}
\RequirePackage{xspace}


\RequirePackage{XCharter}


\RequirePackage[left=2.2cm,%
right=2.2cm,%
top=3cm,%
bottom=3cm,%
headheight=40pt,%
headsep=20pt,%
a4paper]{geometry}%
\setlength{\columnsep}{15pt}
\setlength{\parskip}{0.5\baselineskip}

\input{NVIDIA-Sans-Font-TTF/t1NVIDIASans.fd}
\pdfmapline{+NVIDIASans_Rg < NVIDIA-Sans-Font-TTF/NVIDIASans_Rg.ttf <T1-WGL4.enc}
\pdfmapline{+NVIDIASans_Bd < NVIDIA-Sans-Font-TTF/NVIDIASans_Bd.ttf <T1-WGL4.enc}
\pdfmapline{+NVIDIASans_It < NVIDIA-Sans-Font-TTF/NVIDIASans_It.ttf <T1-WGL4.enc}
\pdfmapline{+NVIDIASans_BdIt < NVIDIA-Sans-Font-TTF/NVIDIASans_BdIt.ttf <T1-WGL4.enc}
\pdfmapline{+NVIDIASans_Lt < NVIDIA-Sans-Font-TTF/NVIDIASans_Lt.ttf <T1-WGL4.enc}
\pdfmapline{+NVIDIASans_LtIt < NVIDIA-Sans-Font-TTF/NVIDIASans_LtIt.ttf <T1-WGL4.enc}
\pdfmapline{+NVIDIASans_Md < NVIDIA-Sans-Font-TTF/NVIDIASans_Md.ttf <T1-WGL4.enc}
\renewcommand{\rmdefault}{NVIDIASans}

\newcommand{\watermarkfont}{\color{black50}\normalfont\fontsize{10}{12}\selectfont}
\newcommand{\headerfont}{\normalfont\sffamily\fontsize{8}{10}\selectfont}
\newcommand{\titlefont}{\color{nvidiagreen}\normalfont\bfseries\fontsize{17}{20}\selectfont}
\newcommand{\datesfont}{\normalfont\sffamily\itshape\fontsize{8}{10}\selectfont}
\newcommand\urlheaderfont{\color{blue}\fontsize{8}{10}\selectfont}
\newcommand{\absfont}{\bfseries\linespread{1.2}\fontsize{10}{12}\selectfont}
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
\newtoks\authornotes

\newdateformat{monthyeardate}{\THEYEAR-\THEMONTH-\THEDAY}

\setcounter{secnumdepth}{3}
\ifthenelse{\boolean{nonumbering}}{\setcounter{secnumdepth}{0}}{}

\RequirePackage{authblk}
\setcounter{Maxaffil}{0}
\setlength{\affilsep}{0.2em}
\renewcommand\Authfont{\normalfont\bfseries\fontsize{9}{13}\selectfont}
\renewcommand\Affilfont{\normalfont\fontsize{8}{10}\selectfont}
\makeatletter
\renewcommand\AB@affilsepx{, \protect\Affilfont}
\makeatother
\renewcommand\Authands{ and }

\newcommand{\internalonly}{Confidential -- NVIDIA, do not share or forward externally.}
\newcommand{\copyrightext}{\textcopyright\, \the\year{} NVIDIA. All rights
reserved.}


\pagestyle{fancy}
\fancypagestyle{firststyle}{
	\fancyhead[L]{
		\ifthenelse{\boolean{logo}}{
			\includegraphics[width=90pt]{assets/nvidia-logo.png}
	 }{}
}
\fancyhead[R]{
	\ifdefined\paperurl
	\if\relax\the\paperurl\relax \else
		\href{\the\paperurl}{\urlheaderfont \itshape \the\paperurl}\\ \fi
	\else \fi
	{\footerfont\itshape\monthyeardate\today}
}
\fancyhead[C]{}
\fancyfoot[L]{%
	\footerfont
	\begin{tabular}[t]{@{}l@{}}
	\ifdefined\correspondingauthor
	\if\relax\the\correspondingauthor\relax
	\else {Additional affiliations: $^1$ National Taiwan University. $^2$ University of Illinois Urbana-Champaign.\\} \fi
	\else \fi
	\the\authornotes \\
    \ifthenelse{\boolean{internal}}{\internalonly \\}{}
	\ifthenelse{\boolean{address}}{
		{\itshape 2788 San Tomas Expressway, Santa Clara, CA 95051, USA} \\}{}
	\ifthenelse{\boolean{copyright}}{\copyrightext}{}
	\end{tabular}%
}
\fancyfoot[R]{
	\ifthenelse{\boolean{internal}}{
	\ifdefined\reportnumber
	\if\relax\the\reportnumber\relax
	\else \footerfont\itshape  {\footerfont \bfseries NVIDIA Technical Report \the\reportnumber} \fi
	\else \fi
	}{\footerfont\bfseries\relax}
}
\fancyfoot[C]{\footerfont\bfseries\relax}}

\fancyhead[L,R]{}
\makeatletter
\fancyhead[C]{\footerfont \@title}
\makeatother
\fancyfoot[C]{}
\fancyfoot[L]{
	\ifthenelse{\boolean{internal}}{\footerfont \internalonly\newline
		\ifdefined\reportnumber
		\if\relax\the\reportnumber\relax
		\else \footerfont {\the\reportnumber} \fi
		\else \fi}{\footerfont\bfseries\relax}
}
\fancyfoot[R]{\footerfont \thepage}

\renewcommand{\headrulewidth}{1pt}
\renewcommand{\footrulewidth}{1pt}
\let\DefaultHeadRule\headrule
\let\DefaultFootRule\footrule
\renewcommand{\headrule}{\color{gray}\DefaultHeadRule}
\renewcommand{\footrule}{\textcolor{gray}{\DefaultFootRule}}

\renewenvironment{abstract}
{\par\noindent\\  \ignorespaces \bfseries}
{\par\bigskip}

\addto{\captionsenglish}{\renewcommand{\refname}{References}}
\newcommand{\citeas}[1]{\Needspace*{8\baselineskip}\noindent\bibentry{#1}}

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

\makeatletter
\newcommand{\abscontent}{
	\noindent
        {\large\bfseries\headingfont Abstract}\par\vspace{0.5em}
        \noindent
	\parbox{\dimexpr\linewidth}{\absfont \theabstract}
	\@ifundefined{@keywords}{}{
		\vskip1em \noindent \keywordsfont  Keywords: \@keywords}
}

\if@twocolumn%
\renewcommand{\maketitle}{
	\twocolumn[
	\begin{adjustwidth}{0pt}{24pt}
		\begin{flushleft}
			{
				{ \raggedright \titlefont
				\@title\par}%
				\vskip11pt
				{\raggedright \@author\par}
				\vskip20pt%
			}%
		\end{flushleft}
	\end{adjustwidth}
	\vskip20pt%
	]
	\thispagestyle{firststyle}
}%
\else%
\renewcommand{\maketitle}{\bgroup\setlength{\parindent}{0pt}
	\begin{adjustwidth}{0pt}{24pt}
		\begin{flushleft}
			{
				{\raggedright \titlefont \@title\par}%
				\vskip11pt
				{\raggedright \@author\par}
				\vskip20pt%
			}%
		\end{flushleft}
	\end{adjustwidth}
	\egroup
	\thispagestyle{firststyle}
}%
\fi
\makeatother

\titleformat{\section}
{\large\bfseries\headingfont}
{\thesection.}
{0.5em}
{#1}
[]
\titleformat{name=\section,numberless}
{\Large\bfseries\headingfont}
{}
{0.5em}
{#1}
[]
\titleformat{\subsection}
{\large\bfseries}
{\thesubsection.}
{0.5em}
{#1}
[]
\titleformat{\subsubsection}%
{\bfseries}
{\thesubsubsection.}
{0.5em}
{#1}
[]


\titlespacing*{\section}{0pc}{3ex plus4pt minus3pt}{5pt}
\titlespacing*{\subsection}{0pc}{2.5ex plus3pt minus2pt}{2pt}
\titlespacing*{\subsubsection}{0pc}{2ex plus2.5pt minus1.5pt}{2pt}
\titleformat{\paragraph}[runin]{\normalfont\normalsize\bfseries}{\theparagraph}{1em}{#1}
\titlespacing*{\paragraph}{0pc}{1.2ex plus1pt minus0.5pt}{0.75em}

\DeclareCaptionLabelSeparator{pipe}{:~}%
\captionsetup{labelfont={},
labelsep=space,%
figurename=Figure,%
labelsep=pipe,
singlelinecheck=off,%
}

\makeatletter
\DeclareRobustCommand\onedot{\futurelet\@let@token\@onedot}
\def\@onedot{\ifx\@let@token.\else.\null\fi\xspace}

\def\eg{\emph{e.g}\onedot} \def\Eg{\emph{E.g}\onedot}
\def\ie{\emph{i.e}\onedot} \def\Ie{\emph{I.e}\onedot}
\def\cf{\emph{c.f}\onedot} \def\Cf{\emph{C.f}\onedot}
\def\etc{\emph{etc}\onedot} \def\vs{\emph{vs}\onedot}
\def\wrt{\emph{w.r.t}\onedot} \def\dof{\emph{d.o.f}\onedot}
\def\iid{\emph{i.i.d}\onedot} \def\wolog{\emph{w.l.o.g}\onedot}
\def\etal{\emph{et al}\onedot}
\makeatother
