% Class declarations %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{galbot}
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

\DisableLigatures[f]{family=sf*} 

% Graphics %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{graphicx}
\RequirePackage{subcaption}

% Tables %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{booktabs}
\RequirePackage{nicematrix}
\RequirePackage{multirow}
\RequirePackage{bm}
\newcommand{\nm}[1]{#1}

% Colorful stuff %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage[most]{tcolorbox}
\RequirePackage{xcolor}
\definecolor{galbot}{HTML}{1C1C1E}
\definecolor{galbotfg}{HTML}{1C2B33}
\definecolor{galbotbg}{HTML}{6B6B73}
\definecolor{galbotlight}{HTML}{F2F2F7}
\definecolor{galbotnavy}{HTML}{1B3A5C}

% % fancy
% \RequirePackage{fancyhdr}
% \fancypagestyle{firstheader}{
% 	\fancyhf{}
% 	\fancyhead[R]{
% 		\includegraphics[height=0.8cm]{assets/logo.png}}
% 	\renewcommand{\headrulewidth}{1pt} % 
% }
% fancy
% \RequirePackage{fancyhdr}
% \fancypagestyle{firstheader}{
% 	\fancyhf{}
% 	\fancyhead[R]{
% 		\includegraphics[height=0.8cm]{assets/Logo_Header.png}}
% 	\renewcommand{\headrulewidth}{1pt} % 
% }
% References %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
\hypersetup{
  colorlinks,
  linkcolor=galbotbg,
  citecolor=galbotbg,
  urlcolor=galbotbg
}

% \RequirePackage[round,authoryear]{natbib}
\RequirePackage[numbers,square]{natbib}
\def\bibfont{\small}

% Section and caption format %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{titlesec}
\titleformat*{\paragraph}{\itshape}
\titleformat*{\section}{\Large\sffamily\bfseries}
\titleformat*{\subsection}{\large\sffamily\bfseries}
\titleformat*{\subsubsection}{\normalsize\sffamily\bfseries}
\titlespacing*{\section}      {0pt}{3.0ex plus 1ex minus .2ex}{1.5ex plus .2ex}
\titlespacing*{\subsection}   {0pt}{2.5ex plus 1ex minus .2ex}{1.0ex plus .2ex}
\titlespacing*{\subsubsection}{0pt}{2.0ex plus 0.8ex minus .2ex}{0.8ex plus .2ex}
\DeclareTextFontCommand{\textbf}{\bfseries\sffamily}

\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\sffamily\textbf{#1 #2}} #3}
\captionsetup{singlelinecheck=false,format=custom,labelsep=custom,font=small}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}

% Fonts %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage[T1]{fontenc}
\DeclareFontFamily{T1}{optimistic}{}
\DeclareFontShape{T1}{optimistic}{m}{n}{<-> s * [0.88] assets/optimistic}{}
\DeclareFontShape{T1}{optimistic}{b}{n}{<-> s * [0.88] assets/optimistic}{}
\pdfmapline{+optimistic < assets/Optimistic.ttf <T1-WGL4.enc}
\renewcommand{\sfdefault}{optimistic}

% Authors, affiliations, infos %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\renewcommand\addtolist[5][]{
  \begingroup
    \if\relax#3\relax\def\sep{}\else\def\sep{#5}\fi
    \let\protect\@unexpandable@protect 
    \xdef#3{\expandafter{#3}\sep #4[#1]{#2}}%
  \endgroup
}

\newcommand\authorlist{}
\newcommand\authorformat[2][]{{\sffamily \bfseries #2$^{#1}$}}
\renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{, }}

\newcommand\affiliationlist{}
\newcommand\affiliationformat[2][]{{\normalsize $^{#1}$#2}}
\newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{ }}

\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\small $^{#1}$#2}}
\newcommand\contribution[2][]{\addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}

\newcommand\galbotdatalist{}
\newcommand\galbotdataformat[2][]{{\small {\sffamily \bfseries #1:} #2}}
\newcommand\galbotdata[2][]{\addtolist[#1]{#2}{\galbotdatalist}{\galbotdataformat}{\par}}

\renewcommand{\abstract}[1]{\def\abstractlist{{\color{galbotfg} #1}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}

\renewcommand\date[1]{\galbotdata[Date]{#1}}
\newcommand\correspondence[1]{\galbotdata[Correspondence]{#1}}
\newcommand\code[1]{\galbotdata[Code]{#1}}
\newcommand\page[1]{\galbotdata[Project Page]{#1}}
\newcommand\huggingface[1]{\galbotdata[HuggingFace]{#1}}

\renewcommand{\title}[1]{\newcommand{\titlelist}{{\huge\sffamily\bfseries #1}}}

\newcommand{\beginappendix}{\appendix{\huge\sffamily Appendix\par}}

% Titlebox %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


\newcommand{\mymaketitle}{%
  \setlength{\parindent}{0cm}
  %% Dark title banner
  \begin{tcolorbox}[
    enhanced,
    frame hidden,
    colback=galbotbg,
    left=18pt,
    right=18pt,
    top=17pt,
    bottom=17pt,
    arc=0pt,
    boxrule=0pt,
    before skip=0pt,
    after skip=0pt,
    grow to left by=1.5pt,
    grow to right by=1.5pt,
  ]
    \color{white}
    \raggedright
    \nohyphens
    {%
      \setstretch{1.618}
      \titlelist\par
    }%
  \end{tcolorbox}
  \vskip 0.4cm
  %% Authors & Affiliations
  {%
    \setlength{\parskip}{0cm}
    \raggedright
    \nohyphens
    {\color{galbotnavy}\authorlist}\par
    \vskip 0.2cm
    {\color{galbotnavy!75}\affiliationlist}\par
    {\color{galbotnavy!65}\contributionlist}\par
  }%
  \vskip 0.45cm
  %% Abstract card with shadow and rounded corners
  \begin{tcolorbox}[
    enhanced,
    colback=galbotlight,
    colframe=galbotbg!20,
    borderline west={3pt}{0pt}{galbotbg},
    left=12pt,
    right=12pt,
    top=10pt,
    bottom=10pt,
    arc=5pt,
    boxrule=0.3pt,
    drop shadow southeast,
    before skip=0pt,
    after skip=0pt,
  ]
    \abstractlist
  \end{tcolorbox}
  %% Links + Logo
  \vskip 0.4cm
  \noindent\begin{minipage}[b]{0.7\textwidth}
    \setlength{\parskip}{0.05cm}
    \ifdefempty{\galbotdatalist}{}{\galbotdatalist\par}
  \end{minipage}%
  \hfill
  \begin{minipage}[b]{0.25\textwidth}
    \raggedleft
    \includegraphics[width=3cm]{assets/Galbot.png}
  \end{minipage}
  \vskip 0.2cm
  \noindent\textcolor{galbotbg!30}{\rule{\textwidth}{0.4pt}}
  \FloatBarrier
}

\if@twocolumn%
\renewcommand{\maketitle}{
\twocolumn[%
  \mymaketitle
  \vskip 0.6cm
]
}%
\else%
\renewcommand{\maketitle}{
  \mymaketitle
}%
\fi
