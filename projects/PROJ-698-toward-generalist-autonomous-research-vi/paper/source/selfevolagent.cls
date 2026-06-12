% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% A new style for FAIR pre-prints
% Author: dlp@meta.com
% Version: 1.1
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Class declarations %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{selfevolagent}
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
\RequirePackage{iftex}

\ifPDFTeX
  \DisableLigatures[f]{family=sf*}
\fi

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
\definecolor{metablue}{HTML}{E2EFEF}
\definecolor{metafg}{HTML}{1C2B33}
\definecolor{metabg}{HTML}{EFF6F6}
\definecolor{darkred}{RGB}{174, 11, 42}

% References %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
% \hypersetup{
%   colorlinks,
%   linkcolor=metablue,
%   citecolor=metablue,
%   urlcolor=metablue
% }
\renewcommand{\UrlFont}{\rmfamily}
\hypersetup{
    colorlinks=true,
    linkcolor=red,
    citecolor=cyan,
    filecolor=magenta,      
    urlcolor=magenta,
    }


\RequirePackage[round,authoryear]{natbib}
\def\bibfont{\small}

% Section and caption format %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{titlesec}
\titleformat*{\paragraph}{\bfseries}
\titleformat*{\section}{\Large\sffamily\bfseries}
\titleformat*{\subsection}{\large\sffamily\bfseries}
\titleformat*{\subsubsection}{\normalsize\sffamily\bfseries}
\DeclareTextFontCommand{\textbf}{\bfseries\sffamily}
% \DeclareTextFontCommand{\texttt}{\sffamily}

\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\sffamily\textbf{#1 #2}} #3}
\captionsetup{singlelinecheck=true,justification=raggedright,format=custom,labelsep=custom,font=small}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}

% \newcommand{\myurlfont}{\fontfamily{libertine}\selectfont}

% Meta custom fonts %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% http://c.caignaert.free.fr/Install-ttf-Font.pdf
% \renewcommand*\ttdefault{cmvtt}
% Declared before \ifPDFTeX so the conditional stays balanced when the
% pdfTeX branch is skipped (e.g. under XeLaTeX/LuaLaTeX).
\newif\ifoptimisticfont
\ifPDFTeX
  \RequirePackage[T1]{fontenc}
  \RequirePackage[varqu]{zi4}
  \renewcommand*\ttdefault{zi4}
  \RequirePackage[tt=false, type1=true]{libertine}
  % The custom "Optimistic" TTF cannot be used with pdfLaTeX on arXiv (arXiv
  % does not place submission .tfm files on the font-metric search path), so we
  % use Linux Biolinum -- the libertine companion sans, bundled in TeX Live --
  % as the sans default. If the Optimistic metrics are available locally, they
  % are used instead so local previews keep the original look.
  \IfFileExists{optimistic.tfm}{\optimisticfonttrue}{\optimisticfontfalse}
  \ifoptimisticfont
    \pdfmapline{+optimistic < Optimistic.ttf <T1-WGL4.enc}
    \DeclareFontFamily{T1}{optimistic}{}
    \DeclareFontShape{T1}{optimistic}{m}{n}{<-> s * [0.88] optimistic}{}
    \DeclareFontShape{T1}{optimistic}{b}{n}{<-> s * [0.88] optimistic}{}
    \renewcommand{\sfdefault}{optimistic}
  \else
    \renewcommand{\sfdefault}{LinuxBiolinumT}
  \fi
\else
  % XeLaTeX / LuaLaTeX: load fonts directly through fontspec so the original
  % look is preserved on arXiv (no .tfm lookup needed).
  %   roman = Linux Libertine, sans = Optimistic (loaded from assets/),
  %   mono  = Inconsolata. All three ship as OpenType with TeX Live.
  \RequirePackage{fontspec}
  \RequirePackage{libertine}
  \setmonofont{Inconsolatazi4}[Extension=.otf,UprightFont=*-Regular,BoldFont=*-Bold,Scale=MatchLowercase]
  \IfFileExists{Optimistic.ttf}{%
    \setsansfont{Optimistic.ttf}[
      Path=/,
      BoldFont=Optimistic.ttf,
      ItalicFont=Optimistic.ttf,
      BoldItalicFont=Optimistic.ttf,
      Scale=0.88
    ]%
  }{}%
\fi

% Authors, affiliations, infos %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\renewcommand\addtolist[5][]{%
  \begingroup%
    \if\relax#3\relax\def\sep{}\else\def\sep{#5}\fi%
    \let\protect\@unexpandable@protect%
    \xdef#3{\expandafter{#3}\sep #4[#1]{#2}}%
  \endgroup%
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

\newcommand\metadatalist{}
\newcommand\metadataformat[2][]{{\small {\sffamily \bfseries #1:} #2}}
\newcommand\metadata[2][]{\addtolist[#1]{#2}{\metadatalist}{\metadataformat}{\par}}

\renewcommand{\abstract}[1]{\def\abstractlist{{\color{metafg} #1}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}

\renewcommand\date[1]{\metadata[\faCalendar\ Date]{#1}}
% \renewcommand\code[1]{\metadata[Code]{#1}}
\newcommand\correspondence[1]{\metadata[Correspondence]{#1}}

\renewcommand{\title}[1]{\newcommand{\titlelist}{{\huge\sffamily\bfseries #1}}}

\newcommand{\beginappendix}{\appendix{\huge\sffamily Appendix\par}}

% Titlebox %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


\newcommand{\mymaketitle}{%
  \tcbset{enhanced,frame hidden}
  \tcbset{left=0.5cm}
  \tcbset{right=0.5cm}
  \tcbset{top=0.5cm}
  \tcbset{bottom=0.5cm}
  \tcbset{arc=10pt}
  \tcbset{colback=metabg}
  \tcbset{before skip=0pt}
  \tcbset{grow to left by=1.5pt}
  \tcbset{grow to right by=1.5pt}
  \tcbset{overlay={%
	    \node[anchor=south east, inner sep=0pt, at=(frame.south east),
	          xshift=-0.55cm, yshift=0.78cm]
           (microsoftlogo) {\includegraphics[height=0.58cm,trim=299 300 301 299,clip]{fig/Microsoft_official.png}};
	    \node[anchor=east, inner sep=0pt, at=(microsoftlogo.west),
	          xshift=-0.42cm]
	         {\includegraphics[height=0.58cm,trim=0 16 21 7,clip]{fig/ruc.png}};%
  }}
  % 
  \begin{tcolorbox}
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0.5cm}
    {
      \setlength{\parskip}{0cm}
      \raggedright
      \nohyphens
      %
      {
        \setstretch{1.618}
        \titlelist\par
      }
      \vskip 0.2cm
      %
      \authorlist\par
      \vskip 0.2cm
      %
      \affiliationlist\par
      %
      \contributionlist\par
    }%
    %
    \abstractlist\par
    %
    \vskip 0.5cm
    %
    {
      \setlength{\parskip}{0cm}
      \ifdefempty{\metadatalist}{\vspace*{0.65cm}}{\metadatalist\par}
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
