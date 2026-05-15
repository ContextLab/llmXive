%%%%%%%%%
%
% Style file used by UC Berkeley RAIL folks.
% This is an edited version of the Google DeepMind tech report template, used under CC Licence, obtained from tex sources of Google DeepMind arxiv papers. There are several changes including font sizes, abstract formatting, title formatting, figure formatting, colors, and math fonts which are allowed per the license.
% 
%
% Use it in the following way, with the full set of option possible:
% \documentclass[11pt, a4paper, twocolumn, logo, copyright, nonumbering, 
% internal]{berkeley} 
%
% Options:
%    - 11pt: Sets the normal font size of the text. Can be only 10, 11, 12pt.
%    - a4paper: Paper size. Usually would not adjust.
%    - twocolumn: Makes the paper into two column mode; single column by default.
%    - logo: Adds the BAIR logo to the top left. No logo included if left out.
%    - copyright: Add a copyright statement to the first page of the paper in the left footnote
%    - nonumbering: Uses unnumbered sections.
%    - internal: for internal only docs that should not be shared externally. 
%           Can only use techreportnumber with this option.
%
% Date of Paper
%   The report is by default given the curren date in the top right. If you want to fix the 
%   date: add the date to your preamble with your own date as follows:
%   \renewcommand{\today}{1 January 2000}
%
% Confidentiality
%   Change the confidentiality statement for internal docs by adding this in the preable 
%   \renewcommand{\internal}{Confidential.}
%   
% ----------------
% Licence: This template is released under the Creative Commons licence 
% Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
%
%
% Known issues:
%   - Package todonotes does not work in the abstract
%
% Version history: 
% v0.3 - Oct 2025: Added deep blue-purple colors, running title in header, date on first page
% v0.2 - Feb 2024: revised some details
% v0.1 - Jan 2024: Obtained from arxiv papers
% %%%%%%%%%%%%%%%


\NeedsTeXFormat{LaTeX2e}

% Palatino font %%%%---- to switch to computer modern font, comment next three lines, and line 126
\RequirePackage{tgpagella} % text only
\RequirePackage{mathpazo}  % math & text
\RequirePackage{inconsolata} % for tt font



%%======== Pckage options and base class ========
\RequirePackage{tcolorbox}
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
\RequirePackage{pifont}
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
% % Title, Abstract, Bibliography
\RequirePackage[explicit]{titlesec}
\RequirePackage{bibentry}
\RequirePackage{mdframed}
\RequirePackage{caption}
\RequirePackage{needspace}

% \RequirePackage[svgnames]{xcolor}
\definecolor{TinaCrimson}{HTML}{DC143C} % Renamed from Crimson
% \RequirePackage[dvipsnames]{xcolor}
% \definecolor{Crimson}{HTML}{990000}

\definecolor{CalGoldHex}{HTML}{fff7e8}
% \definecolor{CalGoldHex}{HTML}{FFF5E1}
\definecolor{IronGrey}{HTML}{6D6E71}

% ========== 【颜色定义】深蓝紫色系 ==========
\definecolor{LARGBlue}{HTML}{2B2563}      % 深蓝紫（标题、超链接）
\definecolor{LightBlue}{HTML}{E8F4FD}    % 偏蓝色浅色（背景）
\definecolor{DarkBlue}{HTML}{1F1A47}     % 更深蓝紫（边框）
\definecolor{Violet}{HTML}{8E24AA}
\definecolor{VioletLight}{HTML}{FAF5FB}

\RequirePackage[colorlinks=true, allcolors=LARGBlue]{hyperref}

%%======== Can use any of these fonts ========
% \RequirePackage{charter}
% \RequirePackage[scaled]{helvet}
% \RequirePackage{bookman}
% \RequirePackage{times}
% \RequirePackage[default]{opensans} %fosfamily
%\usepackage{antpolt}
% Math fonts
% \RequirePackage{mathpazo} % Palatino
%\usepackage{euler} % for math fints

% Use Bitstream Charter as the main font. Does not include a typewriter font.
\RequirePackage{XCharter} %%%%---- to switch to computer modern font, comment this line, and lines 47-49
% \RequirePackage[xcharter,bigdelims,vvarbb]{newtxmath}
% \RequirePackage{libertine}
% \RequirePackage{libertinust1math}
% \RequirePackage[p]{zlmtt} % for teletype, lmodern's typewriter font


% Use the typewriter font from lmodern, scaled up to match Charter's xheight.
% You may wish to add the "p" option to use the proportional font instead of
% the monospaced one, which might look nicer in cases where you do not need
% aligned columns
\RequirePackage[scaled=1.1]{zlmtt}
% \RequirePackage{libertine}
% \RequirePackage{libertinust1math}

%%======== Margins and column spacing ========
\RequirePackage[left=1.9cm,%
right=1.9cm,%
top=3cm,%
bottom=2.5cm,%
headheight=40pt,%
headsep=20pt,%
%showframe, % for testing
letterpaper]{geometry}%
\setlength{\columnsep}{15pt} % Distance between the two columns of text
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.5\baselineskip}

%% *Custom font sizes and styles
\newcommand{\watermarkfont}{\color{black50}\normalfont\fontsize{10}{12}\selectfont}
\newcommand{\headerfont}{\color{LARGBlue}\normalfont\sffamily\fontsize{8}{10}\selectfont}
% \newcommand{\titlefont}{\color{LARGBlue}\normalfont\bfseries\fontsize{21}{23}\selectfont} %%%%---- title font/color
\newcommand{\titlefont}{\centering\color{LARGBlue}\normalfont\fontsize{17}{19}\selectfont} %%%%---- title font/color
\newcommand{\datesfont}{\normalfont\sffamily\itshape\fontsize{8}{10}\selectfont}
\newcommand\urlheaderfont{\color{LARGBlue}\fontsize{8}{10}\selectfont}
\newcommand{\absfont}{\linespread{1.1}\fontsize{10}{12}\color{black}\selectfont}
\newcommand{\keywordstitlefont}{\bfseries\linespread{1.2}\fontsize{8}{10}\selectfont}
\newcommand{\keywordsfont}{\itshape\linespread{1.2}\fontsize{11}{12}\selectfont}
\newcommand{\copyrightfont}{\normalfont\fontsize{7}{9}\selectfont}
\newcommand{\footerfont}{\color{black}\normalfont\fontsize{8}{10}\selectfont}
\newcommand{\subjectfont}{\color{white}\bfseries\fontsize{10}{12}\selectfont}
\newcommand{\headingfont}{\color{LARGBlue}\bfseries\fontsize{13}{14}\selectfont}

% \newcommand{\logoimg}[2]{%
%   \raisebox{0pt}[0pt][0pt]{%
%     \includegraphics[height=0.85cm,trim=#1,clip]{#2}%
%   }%
% }

\newcommand{\logoimg}[3][12pt]{
  \includegraphics[
    height=#1,
    trim=#2,
    clip
  ]{#3}
}

\newcommand{\runningheaderfont}{\color{black}\normalfont\fontsize{11}{13}\selectfont}


\newcommand{\keywords}[1]{\def\@keywords{#1}}
\newtoks\correspondingauthor
\newtoks\paperurl
\newtoks\reportnumber
\def\runningtitle#1{\gdef\@runningtitle{#1}}
\def\@runningtitle{\@title}
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
\renewcommand\Authfont{\centering\normalfont\bfseries\fontsize{10}{14}\selectfont}
\renewcommand\Affilfont{\centering\normalfont\fontsize{10}{20}\selectfont}
\makeatletter
\renewcommand\AB@affilsepx{, \protect\Affilfont}
\makeatother
\renewcommand\Authands{, and }

\newcommand{\internalonly}{}
\newcommand{\copyrightext}{\footerfont \textcopyright\, \the\year{} }


%%======== Header and Footer Content ========
%
% Header and Footer for the first page
\pagestyle{fancy}   % Enables the custom headers/footers

% 第一页：添加日期在右上角，无页脚线



% \fancypagestyle{firststyle}{
% 	\fancyhead[L]{
%       \ifthenelse{\boolean{logo}}{%
%     \logoimg{20 10 20 10}{arxiv/assets/Block-I-orange-white-background.png}\hspace{8pt}%
%     \logoimg{10 10 20 10}{arxiv/assets/logometa.pdf}\hspace{8pt}%
%     \logoimg{40 30 40 30}{arxiv/assets/Amazon-logo-meaning-768x384.jpg}\hspace{8pt}%
%     \logoimg{10 5 10 5}{arxiv/assets/Google_DeepMind_Logo_rgb_3320x512px.png}%
%   }{}%
%     }
\fancypagestyle{firststyle}{
  \fancyhead[L]{
    \ifthenelse{\boolean{logo}}{%
      \logoimg[12pt]{1 1 1 1 1 1}{arxiv/figs/uiuc_logo.png}\hspace{12pt}%
      % \logoimg[10pt]{1 1 1 0}{arxiv/assets/logometa.pdf}\hspace{12pt}%
      % \logoimg[10pt]{1 1 1 5}{arxiv/figs/Amazon_logo.png}\hspace{16pt}%
      % \logoimg[12pt]{5 0 5 0}{arxiv/assets/Google_DeepMind_Logo_rgb_3320x512px.png}\hspace{12pt}%
      % \logoimg[11pt]{5 0 5 0}{arxiv/assets/University_of_California,_San_Diego_logo.png}\hspace{12pt}%
      % \logoimg[16pt]{5 0 5 0}{arxiv/assets/yale-university-logo-png-2.png}%
    }{}%
  }
	% \fancyhead[R]{\runningheaderfont\itshape\monthyeardate\today}
    \fancyhead[R]{}
	\fancyhead[C]{}
	\renewcommand{\headrulewidth}{1pt}
	\renewcommand{\footrulewidth}{0pt}
	%
	\fancyfoot[L]{
		\ifdefined\correspondingauthor
		\if\relax\the\correspondingauthor\relax
		\else \footerfont\itshape  {Corresponding author(s): \the\correspondingauthor \\} \fi
		\else \fi
	    \ifthenelse{\boolean{internal}}{\footerfont \internalonly \\}{\footerfont\bfseries\relax}
		\ifthenelse{\boolean{address}}{
			\itshape\footerfont UC Berkeley, Berkeley, California \\}{}
		\ifthenelse{\boolean{copyright}}{\copyrightext}{}
	}
	\fancyfoot[R]{\footerfont \thepage}
	\fancyfoot[C]{}
}

% Header and Footer for pages from 2 onwards
\renewcommand{\headrulewidth}{1pt}
\renewcommand{\footrulewidth}{0pt}  % 底部无线
\makeatletter
\fancyhead[L]{}  % 左边空
\fancyhead[R]{}  % 右边空
% \fancyhead[C]{\runningheaderfont\textbf{\@title}}
\fancyhead[C]{\runningheaderfont\textbf{\@runningtitle}}

\makeatother
\fancyfoot[L]{
	\ifdefined\correspondingauthor
	\if\relax\the\correspondingauthor\relax
	\else \footerfont\itshape  {Corresponding author(s): \the\correspondingauthor \\} \fi
	\else \fi
    \ifthenelse{\boolean{internal}}{\footerfont \internalonly \\}{\footerfont\bfseries\relax}
	\ifthenelse{\boolean{address}}{
		\itshape\footerfont UC Berkeley, Berkeley, California \\}{}
	\ifthenelse{\boolean{copyright}}{\copyrightext}{}
}
\fancyfoot[R]{\footerfont \thepage}
\fancyfoot[C]{}

% Header and footer rules (coloured).
\renewcommand{\headrulewidth}{1pt}
% \renewcommand{\footrulewidth}{1pt}
\let\DefaultHeadRule\headrule
\let\DefaultFootRule\footrule
\renewcommand{\headrule}{\color{black}\DefaultHeadRule}
\renewcommand{\footrule}{\textcolor{black}{\DefaultFootRule}}

\tcbset{
    titlebox/.style={
        % colback=LightBlue,       
        colback=VioletLight,
        colframe=DarkBlue,           
        boxrule=2pt,                 
        arc=0mm,                     
        leftrule=0pt,
        rightrule=0pt,
        left=5mm,
        right=5mm,
        top=3mm,
        bottom=3mm
    }
}

\renewenvironment{abstract}
{\par\noindent\\  \ignorespaces}
{\par\bigskip}


%%========  Bibliography using bibtex ========

% ========== 【新增】目录样式处理 ==========
\RequirePackage{tocloft}
% 修改目录中的 section 格式
\renewcommand{\cftsecfont}{\bfseries\color{LARGBlue}}
\renewcommand{\cftsecpagefont}{\bfseries\color{LARGBlue}}
% 修改目录中的 subsection 格式（更深的颜色）
\renewcommand{\cftsubsecfont}{\bfseries\color{LARGBlue}}
\renewcommand{\cftsubsecpagefont}{\color{LARGBlue}}
% 修改目录中的 subsubsection 格式
\renewcommand{\cftsubsubsecfont}{\bfseries\color{LARGBlue}}
\renewcommand{\cftsubsubsecpagefont}{\color{LARGBlue}}

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

\newcommand{\HorRule}{\color{black}\rule{\textwidth}{1pt}} %

\if@twocolumn%
\renewcommand{\maketitle}{
	\twocolumn[
	\begin{adjustwidth}{12pt}{12pt}
		\begin{center}
			{
                    % % \vskip-0.5cm
                    % \HorRule
                    \vskip5pt
				{\centering \titlefont
				\@title\par}%
				\vskip11pt
				{\centering \@author\par}
				\vskip-5pt%
                    \HorRule
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
\renewcommand{\maketitle}
{
\vphantom{a}
\vspace{-15mm}
\begin{tcolorbox}[titlebox]
\bgroup\setlength{\parindent}{0pt}
	\begin{adjustwidth}{12pt}{12pt}
		\begin{center}
			{
                    \centering
                    % \vskip-100pt
                    % \HorRule
                    \vskip5pt
				{\centering \titlefont \textbf{\@title}\vspace{5mm}\par}% %%%%---- title definition
				\vskip11pt
				{\centering \@author\par}
                    \vskip15pt%
			}%
		\end{center}
	\end{adjustwidth}
	\egroup
	{%
		{\abscontent}
	}%
	\thispagestyle{firststyle}
 \end{tcolorbox}
}%
\fi
\makeatother

\titleformat{\section}
{\large\bfseries\headingfont}
{\thesection.}
{0.5em}
%{\MakeUppercase{#1}}[]
{#1}
[]

\titleformat{name=\section,numberless}
{\large\bfseries\headingfont}
{}
{0em}
%{\MakeUppercase{#1}}[]
{#1}
[]
% ========== 【修改】Subsection 颜色更深 ==========
\titleformat{\subsection}
{\bfseries\color{LARGBlue}}
{\thesubsection.}
{0.5em}
{#1}
[]

% ========== 【修改】Subsubsection 颜色更深 ==========
\titleformat{\subsubsection}% [runin] If want to have inline for the subsubsect
{\bfseries\itshape\color{LARGBlue}}
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
\DeclareCaptionLabelSeparator{pipe}{:~}% or $\vert$
\captionsetup{labelfont={}, %{bf,sf},%
labelsep=space,%
figurename=\textbf{Figure},%
labelsep=pipe,
singlelinecheck=off,%
%justification=centering
}