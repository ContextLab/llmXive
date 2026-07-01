\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{googledeepmind} % no versioning; versioning does not work well with arxiv.

%%======== Pckage options and base class ========
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
\AtEndOfClass{\RequirePackage[tracking=smallcaps]{microtype}}
\RequirePackage[utf8]{inputenc}
\RequirePackage[english]{babel}
\RequirePackage{amsthm, amsmath, amsfonts, amssymb}
\RequirePackage{cmap}
\RequirePackage[T1]{fontenc}
\RequirePackage{url}
\RequirePackage[colorlinks=true, allcolors=blue]{hyperref}
\RequirePackage{pifont}
\RequirePackage[dvipsnames,table]{xcolor}
\RequirePackage{textcomp} % For copyright symbol styling
\RequirePackage[overload]{textcase}
%\RequirePackage{balance}
%% *Graphics, tables and other formatting
\RequirePackage{graphicx}
\RequirePackage{colortbl}
\RequirePackage{booktabs}
\RequirePackage{changepage}
\RequirePackage{enumitem} % For reducing bullet list item separation
\RequirePackage{tabularx}
\RequirePackage{datetime}
% Headers and footers
\RequirePackage{fancyhdr}  % custom headers/footers
\RequirePackage{lastpage}  % Number of pages in the document
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

%%======== Can use any of these fonts ========
%\RequirePackage{charter}
%\RequirePackage[scaled]{helvet}
%\RequirePackage{bookman}
%\RequirePackage{times}
%\RequirePackage[default]{opensans} %fosfamily
%\usepackage{antpolt}
% Math fonts
%\RequirePackage{mathpazo} % Palatino
%\usepackage{euler} % for math fints

% Use Bitstream Charter as the main font. Does not include a typewriter font.
\RequirePackage{XCharter}
\RequirePackage[xcharter,bigdelims,vvarbb]{newtxmath}

% Use the typewriter font from lmodern, scaled up to match Charter's xheight.
% You may wish to add the "p" option to use the proportional font instead of
% the monospaced one, which might look nicer in cases where you do not need
% aligned columns
\RequirePackage[scaled=1.1]{zlmtt}

% ======== Header logos API ========

\newcommand{\GDMLeftLogo}{\GDM@maybeLeftLogo}
\newcommand{\GDMRightLogo}{\GDM@maybeRightLogo}

\newcommand\GDM@leftlogo{}   \newcommand\GDM@leftlogow{0pt}
\newcommand\GDM@rightlogo{}  \newcommand\GDM@rightlogow{0pt}

% 用户接口：\setleftlogo[<width>]{<path>} 与 \setrightlogo[<width>]{<path>}
\newcommand{\setleftlogo}[2][60pt]{%
  \renewcommand\GDM@leftlogo{#2}%
  \renewcommand\GDM@leftlogow{#1}%
}
\newcommand{\setrightlogo}[2][60pt]{%
  \renewcommand\GDM@rightlogo{#2}%
  \renewcommand\GDM@rightlogow{#1}%
}

% 内部：根据 \boolean{logo} 决定是否显示
\newcommand{\GDM@maybeLeftLogo}{%
  \ifthenelse{\boolean{logo}}{%
    \ifx\GDM@leftlogo\@empty\else
      \raisebox{-0.15\height}{\includegraphics[width=\GDM@leftlogow]{\GDM@leftlogo}}%
    \fi
  }{}%
}
\newcommand{\GDM@maybeRightLogo}{%
  \ifthenelse{\boolean{logo}}{%
    \ifx\GDM@rightlogo\@empty\else
      \raisebox{-0.15\height}{}%
    \fi
  }{}%
}

% \newcommand{\GDM@maybeLeftLogo}{%
%   \ifthenelse{\boolean{logo}}{%
%     \ifx\GDM@leftlogo\@empty\else
%       \raisebox{-0.15\height}{\includegraphics[width=\GDM@leftlogow]{imgs/logo_left.png}}%
%     \fi
%   }{}%
% }
% \newcommand{\GDM@maybeRightLogo}{%
%   \ifthenelse{\boolean{logo}}{%
%     \ifx\GDM@rightlogo\@empty\else
%       \raisebox{-0.15\height}{\includegraphics[width=\GDM@rightlogow]{imgs/logo_right.png}}%
%     \fi
%   }{}%
% }

%%======== Margins and column spacing ========
\RequirePackage[left=2.2cm,%
right=2.2cm,%
top=3cm,%
bottom=3cm,%
headheight=40pt,%
headsep=20pt,%
%showframe, % for testing
a4paper]{geometry}%
\setlength{\columnsep}{15pt} % Distance between the two columns of text
%\setlength{\parindent}{0pt}
\setlength{\parskip}{0.5\baselineskip}

%% *Custom font sizes and styles
\newcommand{\watermarkfont}{\color{black50}\normalfont\fontsize{10}{12}\selectfont}
\newcommand{\headerfont}{\normalfont\sffamily\fontsize{8}{10}\selectfont}
\newcommand{\titlefont}{\color{black}\normalfont\bfseries\fontsize{21}{23}\selectfont}
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

% Dates and Times for footer
%\newdateformat{monthyeardate}{\THEDAY{ }\monthname[\THEMONTH] \THEYEAR}
% ISO-8601 date format
\newdateformat{monthyeardate}{\THEYEAR-\THEMONTH-\THEDAY}

\setcounter{secnumdepth}{3}
\ifthenelse{\boolean{nonumbering}}{\setcounter{secnumdepth}{0}}{}

%%========  Author and affiliation ========
\RequirePackage{authblk}
\setcounter{Maxaffil}{0}
\setlength{\affilsep}{0.2em}
\renewcommand\Authfont{\normalfont\bfseries\fontsize{9}{13}\selectfont}
\renewcommand\Affilfont{\normalfont\fontsize{8}{10}\selectfont}
\makeatletter
\renewcommand\AB@affilsepx{, \protect\Affilfont}
\makeatother
\renewcommand\Authands{ and }

\newcommand{\internalonly}{Confidential -- Google DeepMind, do not share or forward externally.}
\newcommand{\copyrightext}{\footerfont \textcopyright\, \the\year{} Google DeepMind. All rights
reserved}

%%======== Header and Footer Content ========
%
% Header and footer rules (coloured) - 先定义规则
\renewcommand{\headrulewidth}{1pt}
\renewcommand{\footrulewidth}{1pt}

% 设置默认 fancy 样式
\pagestyle{fancy}
\fancyhf{} % 清除默认设置

% Header and Footer for pages from 2 onwards (默认 fancy 样式)
\makeatletter
\fancyhead[L]{\GDM@maybeLeftLogo}
\fancyhead[C]{}
\fancyhead[R]{\GDM@maybeRightLogo}
\makeatother
\fancyfoot[C]{}
\fancyfoot[L]{%
	\ifthenelse{\boolean{internal}}{\footerfont \internalonly\newline
		\ifdefined\reportnumber
		\if\relax\the\reportnumber\relax
		\else \footerfont {GDM-TR \the\reportnumber} \fi
		\else \fi}{\footerfont\bfseries\relax}
}
\fancyfoot[R]{\footerfont \thepage}

% 设置页眉页脚线颜色
\let\DefaultHeadRule\headrule
\let\DefaultFootRule\footrule
\renewcommand{\headrule}{\color{gray}\DefaultHeadRule}
\renewcommand{\footrule}{\textcolor{gray}{\DefaultFootRule}}

% Header and Footer for the first page - 在规则定义之后
\fancypagestyle{firststyle}{%
  \fancyhf{}% 清除所有页眉页脚
  \fancyhead[L]{\GDMLeftLogo}%
  \fancyhead[C]{}%
  \fancyhead[R]{%
    \begin{minipage}[b]{0.68\linewidth}\raggedleft
      \GDMRightLogo\\[-2pt]
      \ifdefined\paperurl
        \if\relax\the\paperurl\relax \else
          \href{\the\paperurl}{\urlheaderfont \itshape \the\paperurl}\\
        \fi
      \fi
      {}
    \end{minipage}%
  }%
  \fancyfoot[L]{%
    \ifdefined\correspondingauthor
    \if\relax\the\correspondingauthor\relax
    \else \footerfont  { \the\correspondingauthor \\} \fi
    \else \fi
    \ifthenelse{\boolean{internal}}{\footerfont \internalonly \\}{\footerfont\bfseries\relax}
    \ifthenelse{\boolean{address}}{%
      \itshape\footerfont Google DeepMind, 5 New Street Square, London EC4A 3TW \\}{}
    \ifthenelse{\boolean{copyright}}{\copyrightext}{}%
  }%
  \fancyfoot[R]{\footerfont \thepage}%
  \fancyfoot[C]{}%
}

% 重定义 plain 样式为 firststyle 的内容（防止被其他代码覆盖）
\fancypagestyle{plain}{%
  \fancyhf{}% 清除所有页眉页脚
  \fancyhead[L]{\GDMLeftLogo}%
  \fancyhead[C]{}%
  \fancyhead[R]{%
    \begin{minipage}[b]{0.68\linewidth}\raggedleft
      \GDMRightLogo\\[-2pt]
      \ifdefined\paperurl
        \if\relax\the\paperurl\relax \else
          \href{\the\paperurl}{\urlheaderfont \itshape \the\paperurl}\\
        \fi
      \fi
      {}
    \end{minipage}%
  }%
  \fancyfoot[L]{%
    \ifdefined\correspondingauthor
    \if\relax\the\correspondingauthor\relax
    \else \footerfont  { \the\correspondingauthor \\} \fi
    \else \fi
    \ifthenelse{\boolean{internal}}{\footerfont \internalonly \\}{\footerfont\bfseries\relax}
    \ifthenelse{\boolean{address}}{%
      \itshape\footerfont Google DeepMind, 5 New Street Square, London EC4A 3TW \\}{}
    \ifthenelse{\boolean{copyright}}{\copyrightext}{}%
  }%
  \fancyfoot[R]{\footerfont \thepage}%
  \fancyfoot[C]{}%
}

\renewenvironment{abstract}
{\par\noindent\\  \ignorespaces \bfseries}
{\par\bigskip}

%%========  Bibliography using bibtex ========
\addto{\captionsenglish}{\renewcommand{\refname}{References}}
\newcommand{\citeas}[1]{\Needspace*{8\baselineskip}\noindent\bibentry{#1}}
% Uncomment the next line if you want the  numbered refs to be "1." instead of "[1]".
%\makeatletter \renewcommand\@biblabel[1]{#1.} \makeatother

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

% Define an environment with abstract content and styling
\makeatletter
\newcommand{\abscontent}{
	\noindent
	\parbox{\dimexpr\linewidth}{\absfont \theabstract}
	\@ifundefined{@keywords}{}{
		\vskip1em \noindent \keywordsfont  Keywords: \@keywords}
}

\if@twocolumn%
\renewcommand{\maketitle}{
    \thispagestyle{firststyle}
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

		\abscontent
	\vskip20pt%
	]
}%
\else% \@twocolumnfalse
\renewcommand{\maketitle}{%
	\thispagestyle{firststyle}% 移到开头确保首页样式生效
	\bgroup\setlength{\parindent}{0pt}
	\begin{adjustwidth}{0pt}{23pt}
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
	{%
		{\abscontent}
	}%
}%
\fi
\makeatother

\titleformat{\section}
{\Large\bfseries\headingfont}
{\thesection.}
{0.5em}
%{\MakeUppercase{#1}}[]
{#1}
[]
\titleformat{name=\section,numberless}
{\Large\bfseries\headingfont}
{}
{0em}
%{\MakeUppercase{#1}}[]
{#1}
[]
\titleformat{\subsection}
{\large\bfseries}
{\thesubsection.}
{0.5em}
{#1}
[]
\titleformat{\subsubsection}% [runin] If want to have inline for the subsubsect
{\bfseries}
{\thesubsubsection.}
{0.5em}
{#1}
[]

\titlespacing*{\section}{0pc}{3ex plus4pt minus3pt}{5pt}
%\titlespacing*{\section}{0pc}{1ex }{\baselineskip}
\titlespacing*{\subsection}{0pc}{2.5ex plus3pt minus2pt}{2pt}
\titlespacing*{\subsubsection}{0pc}{2ex plus2.5pt minus1.5pt}{2pt}
%\titlespacing*{\paragraph}{0pc}{2ex plus2pt minus1pt}{0pt}

%%======== Captions in tables and figures ========
\DeclareCaptionLabelSeparator{pipe}{ $\vert$ }% or $\vert$
\captionsetup{labelfont={}, %{bf,sf},%
labelsep=space,%
figurename=Figure,%
labelsep=pipe,
singlelinecheck=off,%
%justification=centering
}
