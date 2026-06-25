%%%%%%%%%
%
% FRONTIS style file for papers, internal reports, and unpublished
% papers.
%
% This class allows for several options depending on the preferences of the authors.
% Use it in the following way, with the full set of option possible:
% \documentclass[11pt, a4paper, twocolumn, copyright, nonumbering,
% confidential, frontis]{frontis}
%
% Options:
%    - 11pt: Sets the normal font size of the text. Can be only 10, 11, 12pt.
%    - a4paper: Paper size. Usually would not adjust.
%    - twocolumn: Makes the paper into two column mode; single column by default.
%    - copyright: Add a copyright statement to the first page of the paper in the left footnote
%    - nonumbering: Uses unnumbered sections.
%    - confidential: add labels for internal only reports that should not be shared externally.
%           Can only use techreportnumber with this option.
%.   - frontis/frontis-icon/frontis-thu: select the logo style. frontis = horizontal logo (default); frontis-icon = icon only; frontis-thu = FRONTIS + divider + Tsinghua logo (expects assets/logo-tsinghua.pdf or .png). Remember to activate with \uselogo{} in the preamble.
%
% Date of Paper
%   The report is by default given the current date in the top right. If you want to fix the
%   date: add the date to your preamble with your own date as follows:
%   \renewcommand{\today}{1 January 2000}
%
% Confidentiality
%   Change the confidentiality statement for internal docs by adding this in the preamble
%   \renewcommand{\internalonly}{Confidential.}
%
%  
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
% v0.6, June 2026 - Unified brand class: margin=1in default (correct page-1 logo
%        spacing), author + affiliation byline 11pt bold, \fvtitlecenter switch.
% v0.5, March 2025 - Allow for more logos. Change too google.cls
% v0.4, Sept 2023 - Update to Google DeepMind unit
% v0.31, May 2019 - Allow corresponding authors without internal option
% v0.3, March 2019 - Math font consistency, better handling of optional arguments
% v0.2, January 2019 - Consistency of fonts, margins, additional notes
% v0.1, December 2018 - Initial version for testing
%
% Ongoing Review
%    We review and improve this regularly.
%    Send comments to shakir@
%
%
% %%%%%%%%%%%%%%%
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{frontis} % no versioning; versioning does not work well with arxiv.

%%======== Package options and base class ========
\RequirePackage{xifthen}
\newboolean{nonumbering}
\newboolean{address}
\newboolean{copyright}
\newboolean{confidential}
\DeclareOption{nonumbering}{\setboolean{nonumbering}{true}}
\DeclareOption{address}{\setboolean{address}{true}}
\DeclareOption{copyright}{\setboolean{copyright}{true}}
\DeclareOption{confidential}{\setboolean{confidential}{true}}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{extarticle}}
\ProcessOptions
\LoadClass{extarticle}

%%======== Packages Required ========
% Fonts and language
\RequirePackage{iftex}
\ifPDFTeX
  \AtEndOfClass{\RequirePackage[tracking=smallcaps]{microtype}}
\else
  \AtEndOfClass{\RequirePackage{microtype}}
\fi
\RequirePackage[utf8]{inputenc}
\RequirePackage[english]{babel}
\RequirePackage{amsthm, amsmath, amsfonts, amssymb}
\RequirePackage{cmap}
\RequirePackage[T1]{fontenc}
\RequirePackage{url}
\RequirePackage[colorlinks=true, allcolors=frontisblue]{hyperref}
\RequirePackage{pifont}
\RequirePackage[dvipsnames]{xcolor}
\RequirePackage{textcomp} % For copyright symbol styling
\RequirePackage[overload]{textcase}
%\RequirePackage{balance}
%% *Graphics, tables and other formatting
\RequirePackage{graphicx}
\RequirePackage{colortbl}
\RequirePackage{booktabs}
% \RequirePackage[most]{tcolorbox}

%% Define dark blue color for hyperlinks
\definecolor{darkblue}{rgb}{0, 0, 0.5}
%% FRONTIS VI v1.5 palette
\definecolor{frontiscyan}{HTML}{00C1D4}   % Threshold Cyan (The Edge)
\definecolor{frontisgray}{HTML}{3D4145}   % Energy Level Grey (body/structure)
\definecolor{frontisorange}{HTML}{FA5F26} % Energy Orange (peak only, <=1/page)
\definecolor{frontisblue}{HTML}{1A6FD4}   % Info Blue (links)
\definecolor{frontisred}{HTML}{F22E2E}    % Danger Red
\definecolor{frontislight}{HTML}{F0F2F4}  % Residual Grey (secondary bg)
% Brand peak emphasis (use sparingly: at most once per page)
\newcommand{\peak}[1]{\textcolor{frontisorange}{\bfseries #1}}
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
\setlist[itemize]{nosep}
% \setlist[itemize]{itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt}
\setlist[enumerate]{noitemsep}
\renewcommand{\labelitemi}{\textcolor{frontiscyan}{$\bullet$}} % energy node
% Title, Abstract, Bibliography
\RequirePackage[explicit]{titlesec}
\RequirePackage{bibentry}
% \RequirePackage{mdframed}
\RequirePackage{caption}
\RequirePackage{needspace}
\RequirePackage{soul}
\RequirePackage{kvoptions}


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

%%======== Margins and column spacing ========
% Brand default = 1in margins. This is what gives the page-1 brand band its
% correct top whitespace (the band is lifted by \vspace*{-28pt}; with the old
% top=3cm the logo sat too low). Unified across all FRONTIS papers; no per-paper
% \geometry{margin=1in} override is needed anymore.
\RequirePackage[margin=1in,%
headheight=40pt,%
headsep=20pt,%
%showframe, % for testing
]{geometry}% paper size follows the \documentclass option (a4paper / letterpaper)
\setlength{\columnsep}{15pt} % Distance between the two columns of text
\setlength{\parindent}{0pt}
% \setlength{\parindent}{1.5em}
\setlength{\parskip}{0.5\baselineskip}

%% *Custom font sizes and styles
\newcommand{\watermarkfont}{\color{black50}\normalfont\fontsize{10}{12}\selectfont}
% \newcommand{\headerfont}{\normalfont\sffamily\fontsize{8}{10}\selectfont}
\newcommand{\headerfont}{\color{black}\normalfont\bfseries\fontsize{10}{12}\selectfont}
\newcommand{\titlefont}{\color{black}\normalfont\bfseries\fontsize{21}{23}\selectfont}
\newcommand{\datesfont}{\normalfont\sffamily\itshape\fontsize{8}{10}\selectfont}
\newcommand\urlheaderfont{\color{frontisblue}\fontsize{8}{10}\selectfont}
\newcommand{\absfont}{\linespread{1.2}\fontsize{10}{12}\selectfont}
\newcommand{\keywordstitlefont}{\bfseries\linespread{1.2}\fontsize{8}{10}\selectfont}
\newcommand{\keywordsfont}{\itshape\linespread{1.2}\fontsize{11}{12}\selectfont}
\newcommand{\copyrightfont}{\normalfont\fontsize{7}{9}\selectfont}
\newcommand{\footerfont}{\color{black}\normalfont\fontsize{10}{12}\selectfont}
\newcommand{\subjectfont}{\color{white}\bfseries\fontsize{10}{12}\selectfont}
\newcommand{\headingfont}{\color{black}\bfseries\fontsize{13}{14}\selectfont}

\newcommand{\keywords}[1]{\def\@keywords{#1}}
\newtoks\correspondingauthor
\newtoks\paperurl
\newtoks\reportnumber

% Dates and Times for footer
% ISO-8601 date format
\newdateformat{monthyeardate}{\THEYEAR-\twodigit{\THEMONTH}-\twodigit{\THEDAY}}

\setcounter{secnumdepth}{3}
\ifthenelse{\boolean{nonumbering}}{\setcounter{secnumdepth}{0}}{}

%%========  Author and affiliation ========
\RequirePackage{authblk}
\setcounter{Maxaffil}{0}
\setlength{\affilsep}{0.5em}
\renewcommand\Authfont{\normalfont\bfseries\fontsize{11}{14}\selectfont}
\renewcommand\Affilfont{\normalfont\bfseries\fontsize{11}{14}\selectfont}
\makeatletter
\renewcommand\AB@affilsepx{, \protect\Affilfont}
\makeatother
\renewcommand\Authands{ and }

% Role functionality - similar to affil but for author roles
\newcounter{role}
\newcommand\Rolefont{\normalfont\fontsize{10}{12}\selectfont}
\makeatletter
\newcommand\role[2][]{\stepcounter{role}%
  \expandafter\gdef\csname @role\therole\endcsname{#2}%
  \ifx\relax#1\relax
    \expandafter\gdef\csname @rolelabel\therole\endcsname{}%
  \else
    \expandafter\gdef\csname @rolelabel\therole\endcsname{$^{#1}$}%
  \fi
}

% Command to format and display all roles
\newcommand{\@roles}{%
  \ifnum\value{role}>0
    \vskip-2pt
    {\fvtitlealign \Rolefont
      \@tempcnta=1
      \loop
        \ifcsname @role\the\@tempcnta\endcsname
          \csname @rolelabel\the\@tempcnta\endcsname\csname @role\the\@tempcnta\endcsname
          \advance\@tempcnta by 1
          \ifnum\@tempcnta>\value{role}\else, \fi
        \fi
      \ifnum\@tempcnta>\value{role}\else\repeat
    \par}
  \fi
}

% Resource functionality - similar to role but for contact info and resources
\newcounter{resource}
\newcommand\Resourcefont{\normalfont\fontsize{10}{12}\selectfont}
\newcommand\resource[2]{\stepcounter{resource}%
  \expandafter\gdef\csname @resource\theresource\endcsname{#2}%
  \ifx\relax#1\relax
    \expandafter\gdef\csname @resourcelabel\theresource\endcsname{}%
  \else
    \expandafter\gdef\csname @resourcelabel\theresource\endcsname{\protect#1~}%
  \fi
}

% Command to format and display all resources
\newcommand{\@resources}{%
  \ifnum\value{resource}>0
    \vskip-2pt
    {\fvtitlealign \Resourcefont
      \@tempcnta=1
      \loop
        \ifcsname @resource\the\@tempcnta\endcsname
          \csname @resourcelabel\the\@tempcnta\endcsname\csname @resource\the\@tempcnta\endcsname
          \advance\@tempcnta by 1
          \ifnum\@tempcnta>\value{resource}\else, \fi
        \fi
      \ifnum\@tempcnta>\value{resource}\else\repeat
    \par}
  \fi
}
\makeatother

\newcommand{\internalonly}{\textcolor{frontisred}{\bfseries Confidential---Do not share or forward externally}}
\newcommand{\copyrightext}{\footerfont \textcopyright\, \the\year{} FRONTIS. All rights
reserved}


%%======== Set template and Logo ========
% --- Provide User Command for PA Name ---

\newcommand{\pafullname}{} % store the PA name

% Command to set header text when no logo is used
\newtoks\headertext
\newcommand{\setheadertext}[1]{\headertext{#1}}

% --- Process Standard Class Options ---
% Still useful for standard options like 10pt, 11pt, etc.
\DeclareOption* {\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax % Process standard options like 10pt, etc.

% Declare the options corresponding to the research group
% We use lowercase simple names for the options
\def\@selectedlogo{0} % Default to no logo
\newcommand{\uselogo}[1]{#1}
\DeclareOption{frontis}{
    \renewcommand{\pafullname}{FRONTIS}%
    \renewcommand{\uselogo}[1]{\gdef\@selectedlogo{1}}%
}
\DeclareOption{frontis-icon}{
    \renewcommand{\pafullname}{FRONTIS}%
    \renewcommand{\uselogo}[1]{\gdef\@selectedlogo{2}}%
}
\DeclareOption{frontis-thu}{
    \renewcommand{\pafullname}{FrontisAI $\times$ Tsinghua University}%
    \renewcommand{\uselogo}[1]{\gdef\@selectedlogo{3}}%
}
% --- Default Option ---
% Set a default option if no option is explicitly given in \documentclass
\ExecuteOptions{frontis} % Default to horizontal FRONTIS logo

% --- Handle Unrecognized Options ---
% Pass any other options (like '12pt', 'twoside') to the base class ('article')
\DeclareOption* {\PassOptionsToClass{\CurrentOption}{article}}

% --- Process Options ---
% Execute the code associated with the options provided (or the default)
\ProcessOptions\relax

% --- Provide User Command for Company Name ---
% Define a user-friendly command to access the stored full company name
% This should be done *after* \ProcessOptions
\newcommand{\thepa}{\pafullname}


%%======== Header and Footer Content ========
% Header and Footer for the first page
\pagestyle{fancy}   % Enables the custom headers/footers
% Brand band shown at the top of the title block (page 1 body flow, so the
% running-header geometry of pages 2+ is unaffected).
% Logo height knob: \renewcommand{\fvlogoheight}{38pt} in the preamble to adjust
\newcommand{\fvlogoheight}{34pt}
\newlength{\fvdividerlen}% private register (scratch \dimen0 gets clobbered)
\newsavebox{\fvlogobox}% measured logo group, so the band never wraps
% Divider between joint logos; turn off with \fvlogodividerfalse in the preamble
\newif\iffvlogodivider \fvlogodividertrue
\gdef\fvtitlelogo{%
	 \ifcase\@selectedlogo % Case 0: No logo
        \ifdefined\headertext
        \if\relax\the\headertext\relax
        \else {\headerfont\the\headertext} \fi
        \else \fi
      \or % Case 1
        \includegraphics[height=\fvlogoheight]{assets/frontis-logo-horizontal-light}%
      \or % Case 2
        \includegraphics[height=\fvlogoheight]{assets/frontis-logo-icon-light}%
      \or % Case 3: FRONTIS x Tsinghua joint mark
        \includegraphics[height=\fvlogoheight]{assets/frontis-logo-horizontal-light}%
        \iffvlogodivider
          \hspace{10pt}{\setlength{\fvdividerlen}{\fvlogoheight}\color{black!45}\rule[0.12\fvdividerlen]{1pt}{0.76\fvdividerlen}}\hspace{10pt}%
        \else\hspace{18pt}\fi%
        \includegraphics[height=\fvlogoheight]{assets/logo-tsinghua}%
      \else
      \fi}
\gdef\fvtitledateline{%
	\ifdefined\paperurl
	\if\relax\the\paperurl\relax \else
		\href{\the\paperurl}{\urlheaderfont \the\paperurl}\\ \fi
	\else 
	\fi
	{\footerfont\monthyeardate\today}%
	\ifthenelse{\boolean{confidential}}{\\ \footerfont \internalonly}{}}
\gdef\fvtitleband{%
	\begingroup\setlength{\parskip}{0pt}% keep band spacing explicit
	\vspace*{-28pt}% lift the page-1 brand band toward the top edge
	\noindent
	\sbox{\fvlogobox}{\fvtitlelogo}%
	\begin{minipage}[c]{\wd\fvlogobox}\usebox{\fvlogobox}\end{minipage}%
	\hfill
	\begin{minipage}[c]{\dimexpr\linewidth-\wd\fvlogobox-16pt\relax}\raggedleft\fvtitledateline\end{minipage}\par
	\nointerlineskip\vskip10pt
	% The Edge
	\noindent\textcolor{frontiscyan}{\rule{\linewidth}{2pt}}\par
	\nointerlineskip\vskip24pt
	\endgroup}
\fancypagestyle{firststyle}{
	\renewcommand{\headrulewidth}{0pt}% page-1 band is in the body flow
	\fancyhead[L]{}
	\fancyhead[R]{}
	\fancyhead[C]{}
%
\fancyfoot[L]{
    %\ifthenelse{\boolean{confidential}}{\footerfont \internalonly \\}{\footerfont\bfseries\relax}
    \ifdefined\correspondingauthor
	\if\relax\the\correspondingauthor\relax
	\else \footerfont\itshape  {Corresponding author(s): \the\correspondingauthor \\} \fi
	\else \fi
	\ifthenelse{\boolean{copyright}}{\copyrightext}{}
}
\fancyfoot[R]{
	\ifthenelse{\boolean{confidential}}{
	\ifdefined\reportnumber
	\if\relax\the\reportnumber\relax
	\else \footerfont\itshape  {\footerfont \thepa{} Technical Report \the\reportnumber} \fi
	\else \fi
	}{\footerfont\bfseries\relax}
}
\fancyfoot[C]{
    \footerfont\bfseries\relax}
}

% Header and Footer for pages from 2 onwards
\fancyhead[L,R]{}
\makeatletter
\fancyhead[C]{\footerfont \@title}
% \fancyhead[R]{
% 	\ifthenelse{\boolean{confidential}}{\footerfont \internalonly}{}
% }
\makeatother
\fancyfoot[C]{}
% \fancyfoot[L]{
% 	\ifthenelse{\boolean{confidential}}{\footerfont \internalonly\newline
% 		\ifdefined\reportnumber
% 		\if\relax\the\reportnumber\relax
% 		\else \footerfont {\thepa{} TR-\the\reportnumber} \fi
% 		\else \fi}{\footerfont\bfseries\relax}
% }
\fancyfoot[L]{
	\ifthenelse{\boolean{confidential}}{\footerfont \internalonly}{\footerfont\bfseries\relax}
}
\fancyfoot[R]{\footerfont 	
    %\ifdefined\reportnumber
	%\if\relax\the\reportnumber\relax
	%\else \footerfont\itshape  {\footerfont \thepa{} Technical Report \the\reportnumber} \fi
	%\else \fi \hspace{10mm} 
	\thepage}

% Header and footer rules (coloured).
\renewcommand{\headrulewidth}{1pt}
\renewcommand{\footrulewidth}{1pt}
\let\DefaultHeadRule\headrule
\let\DefaultFootRule\footrule
\renewcommand{\headrule}{\color{black}\DefaultHeadRule}
\renewcommand{\footrule}{\textcolor{black}{\DefaultFootRule}}

\renewenvironment{abstract}
{\par\noindent\\  \ignorespaces}
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
	{\setlength{\fboxsep}{14pt}%
	\colorbox{frontislight}{\parbox{\dimexpr\linewidth-2\fboxsep}{%
		\textbf{Abstract} \textcolor{frontiscyan}{$\vert$} \absfont \theabstract
		\@ifundefined{@keywords}{}{%
			\par\vskip0.8em {\keywordsfont Keywords: \@keywords}}}}}
}

% ---- Title/author alignment switch ----
% Default: left-aligned (NatureBench style). Put \fvtitlecentertrue in the
% preamble to center the whole title block (title + author + roles + resources),
% matching the centered badge row.
\newif\iffvtitlecenter \fvtitlecenterfalse
\newcommand{\fvtitlealign}{\iffvtitlecenter\centering\else\raggedright\fi}
\newcommand{\fvtitlerightinset}{\iffvtitlecenter 0pt\else 24pt\fi}

\if@twocolumn%
\renewcommand{\maketitle}{
	\twocolumn[
	\fvtitleband
	\begin{adjustwidth}{0pt}{\fvtitlerightinset}
		\begin{flushleft}
			{
				{ \fvtitlealign \titlefont
				\@title\par}%
				\vskip11pt
				{\fvtitlealign \@author\par}
				\@roles
				\@resources
				\vskip3pt%
			}%
		\end{flushleft}
	\end{adjustwidth}
	\vskip6pt
		\abscontent
	\vskip20pt%
	]
	\thispagestyle{firststyle}
}%
\else% \@twocolumnfalse
\renewcommand{\maketitle}{\bgroup\setlength{\parindent}{0pt}
	\fvtitleband
	\begin{adjustwidth}{0pt}{\fvtitlerightinset}
		\begin{flushleft}
			{
				{\fvtitlealign \titlefont \@title\par}%
				\vskip11pt
				{\fvtitlealign \@author\par}
				\@roles
				\@resources
				\vskip3pt%
			}%
		\end{flushleft}
	\end{adjustwidth}
	\egroup
	\vskip6pt
	{%
		{\abscontent}
	}%
	\thispagestyle{firststyle}
}%
\fi
\makeatother

% Cyan guide tick before section titles (VI "vertical guide line" element;
% heading text stays black -- the VI forbids cyan heading text)
\newcommand{\fvsectick}{\llap{\textcolor{frontiscyan}{\rule[-2pt]{2.5pt}{12.5pt}}\hspace{0.55em}}}
\titleformat{\section}
{\large\bfseries\headingfont}
{\fvsectick\thesection.}
{0.5em}
%{\MakeUppercase{#1}}[]
{#1}
[]
\titleformat{name=\section,numberless}
{\large\bfseries\headingfont}
{}
{0em}
%{\MakeUppercase{#1}}[]
{\fvsectick #1}
[]
\titleformat{\subsection}
{\color{black}\bfseries}
{\thesubsection.}
{0.5em}
{#1}
[]
\titleformat{\subsubsection}% [runin] If want to have inline for the subsubsect
{\color{frontisgray}\bfseries}% VI: no italic headings
{\thesubsubsection.}
{0.5em}
{#1}
[]

\titlespacing*{\section}{0pc}{3ex plus4pt minus3pt}{5pt}
%\titlespacing*{\section}{0pc}{1ex }{\baselineskip}
\titlespacing*{\subsection}{0pc}{2.5ex plus3pt minus2pt}{2pt}
\titlespacing*{\subsubsection}{0pc}{2ex plus2.5pt minus1.5pt}{2pt}
% \titlespacing*{\paragraph}{0pc}{2ex plus2pt minus1pt}{0pt}
\titleformat{\paragraph}[runin]{\bfseries}{}{-0.5em}{#1}
\titlespacing*{\paragraph}{0pt}{0ex}{.33em}
%%======== Captions in tables and figures ========
\DeclareCaptionLabelSeparator{pipe}{ \textcolor{frontiscyan}{$\vert$} }% or $\vert$
\captionsetup{labelfont={bf}, %{bf,sf},%
labelsep=space,%
figurename=Figure,%
labelsep=pipe,
singlelinecheck=off,%
%justification=centering
}
