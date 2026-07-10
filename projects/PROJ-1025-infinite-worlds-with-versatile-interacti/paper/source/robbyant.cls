% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% LaTex style for RobbyAnt technical reports
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{robbyant}[2025/12/29 RobbyAnt LaTeX Template - Customizable]

% Define options for logo display within the abstract area.
\newif\if@showlogo
\@showlogotrue  % Show logo by default
\DeclareOption{nologo}{\@showlogofalse}

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax

\LoadClass{article}


% Customizable branding parameters.
\RequirePackage{color}
\RequirePackage{xcolor}
\def\@antlogopath{assets/antgroup.png}               % Path to the Ant Group logo
\def\@robbylogopath{assets/robbyant.png}             % Path to the Robbyant logo
\def\@combinelogopath{assets/antgroup_robbyant.png}  % Path to the combination of Ant Group and Robbyant logos
\definecolor{robbybrandcolor}{HTML}{555FFF}          % Brand color
\definecolor{robbyfontfg}{HTML}{000000}              % Body text color (black)
\definecolor{robbyfontbg}{HTML}{F5F6FF}              % Highlight box background
\definecolor{robbylinecolor}{HTML}{0E17B5}           % Border/line color


%%%% Packages
\RequirePackage[top=2.5cm,bottom=2.5cm,left=2.5cm,right=2.5cm,columnsep=0.65cm,headheight=30pt,headsep=20pt]{geometry}
\RequirePackage{microtype}
\RequirePackage[T1]{fontenc}
\RequirePackage{times}
\RequirePackage{fancyhdr}
\RequirePackage{ragged2e}
\RequirePackage{placeins}
\RequirePackage{hyphenat}
\RequirePackage{parskip}
\RequirePackage[latin,english]{babel}
\RequirePackage{lipsum}
\RequirePackage{comment}
\RequirePackage{graphicx}
\RequirePackage{xspace}
\RequirePackage[most]{tcolorbox}
\RequirePackage{etoolbox}
\RequirePackage{titlesec}
\RequirePackage{float}
\RequirePackage[format=plain,labelformat=simple,labelsep=period,font=small,compatibility=false]{caption}
\RequirePackage[font=footnotesize,skip=3pt,subrefformat=parens]{subcaption}
\RequirePackage{capt-of}
\RequirePackage{wrapfig}
\RequirePackage{enumitem}
\RequirePackage{amsmath,amsthm,amssymb,amsfonts,dsfont,pifont,bm,bbm,mathrsfs,mathtools,nicefrac,extarrows,relsize}
\RequirePackage{algorithm,algorithmicx,algpseudocode,listings}
\RequirePackage{booktabs,multirow,nicematrix,adjustbox,diagbox,threeparttable,tabularray,setspace}
\RequirePackage[numbers,sort&compress]{natbib}
\RequirePackage[pagebackref=false,breaklinks=true,colorlinks=true,citecolor=robbybrandcolor,linkcolor=robbybrandcolor,urlcolor=robbybrandcolor,bookmarks=false]{hyperref}
\RequirePackage[capitalize]{cleveref}  % Should be loaded after 'hyperref', and works perfectly with 'subfigure'.
\newtheorem{theorem}{Theorem}
\newtheorem{proposition}{Proposition}
\newtheorem{lemma}{Lemma}
\newtheorem{corollary}{Corollary}
\newtheorem{remark}{Remark}
\crefname{section}{Sec.}{Secs.}
\Crefname{section}{Section}{Sections}
\crefname{appendix}{App.}{Apps.}
\Crefname{appendix}{Appendix}{Appendices}
\crefname{table}{Tab.}{Tabs.}
\Crefname{table}{Table}{Tables}
\crefname{figure}{Fig.}{Figs.}
\Crefname{figure}{Figure}{Figures}
\crefname{equation}{Eq.}{Eqs.}
\Crefname{equation}{Equation}{Equations}
\crefname{theorem}{Thm.}{Thms.}
\Crefname{theorem}{Theorem}{Theorems}
\crefname{lemma}{Lem.}{Lems.}
\Crefname{lemma}{Lemma}{Lemmas}
\crefname{remark}{Rem.}{Rems.}
\Crefname{remark}{Remark}{Remarks}
\crefname{corollary}{Cor.}{Cors.}
\Crefname{corollary}{Corollary}{Corollaries}
\crefname{algorithm}{Alg.}{Algs.}
\Crefname{algorithm}{Algorithm}{Algorithms}
\hyphenpenalty=1200
\ifpdf
  \DisableLigatures[f]{family=sf*}
\fi
\RequirePackage{silence}
\WarningFilter*{latex}{Text page \thepage\space contains only floats}
\WarningFilter{latex}{Command \showhyphens has changed}


\definecolor{cellred}{RGB}{213, 123, 101}
\definecolor{cellgreen}{RGB}{0, 205, 0}
\definecolor{cellblue}{RGB}{54, 125, 189}
\definecolor{codegreen}{rgb}{0,0.6,0}
\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\definecolor{codepurple}{rgb}{0.58,0,0.82}
\definecolor{backcolour}{rgb}{1.0,1.0,1.0}
\lstdefinestyle{mystyle}{
    backgroundcolor=\color{backcolour},
    commentstyle=\color{codegreen},
    keywordstyle=\color{magenta},
    numberstyle=\tiny\color{codegray},
    stringstyle=\color{codepurple},
    basicstyle=\ttfamily\scriptsize,
    breakatwhitespace=false,
    breaklines=true,
    captionpos=b,
    keepspaces=true,
    numbers=left,
    numbersep=5pt,
    showspaces=false,
    showstringspaces=false,
    showtabs=false,
    tabsize=2
}
\lstset{style=mystyle}


\newcommand{\todo}[1]{{\color{red} [TODO: #1]}}
\newcommand{\torevise}[1]{{\color{red} [TO REVISE: #1]}}
\newcommand{\tocheck}[1]{{\color{red} [TO CHECK: #1]}}
\newcommand{\tofinish}[1]{{\color{red} [TO FINISH: #1]}}
\newcommand{\tocite}[1]{{\color{red} [TO CITE]}}
\newcommand{\supp}{\textit{Appendix}\xspace}


% Header and footer.
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\fancyhead[L]{}
\fancyhead[C]{}
\fancyhead[R]{}
\fancyfoot[C]{\thepage}


\fancypagestyle{firstpage}{
    \fancyhf{}
    \renewcommand{\headrulewidth}{0.5pt}
    \renewcommand{\headrule}{{\color{robbylinecolor}\hrule width\headwidth height\headrulewidth \vskip-\headrulewidth}}
    \fancyhead[L]{
        \includegraphics[height=20pt]{\@antlogopath}
        \vspace{5pt}
    }
    \fancyhead[C]{}
    \fancyhead[R]{}
    \fancyfoot[C]{\thepage}
}


% Section, caption, font format.
%   http://c.caignaert.free.fr/Install-ttf-Font.pdf
%   https://www.tug.org/FontCatalogue/allfonts.html
%   Optional: If you have the Optimistic font, uncomment these lines and comment out the above
%   \DeclareFontFamily{T1}{optimistic}{}
%   \DeclareFontShape{T1}{optimistic}{m}{n}{<-> s * [0.88] assets/optimistic}{}
%   \pdfmapline{+optimistic < assets/Optimistic.ttf <T1-WGL4.enc}
%   \renewcommand{\sfdefault}{optimistic}
\titleformat*{\paragraph}{\itshape}
\titleformat{\section}{\Large\sffamily\bfseries\raggedright}{\thesection}{1em}{}
\titleformat{\subsection}{\large\sffamily\bfseries\raggedright}{\thesubsection}{1em}{}
\titleformat{\subsubsection}{\normalsize\sffamily\bfseries\raggedright}{\thesubsubsection}{1em}{}

\DeclareCaptionLabelSeparator{custom}{. }
\captionsetup{singlelinecheck=true,labelsep=custom,font=small,labelfont={bf,sf}}
\captionsetup[sub]{singlelinecheck=true,labelsep=custom,font=small,labelfont={bf,sf}}

\renewcommand*\ttdefault{cmvtt}
\renewcommand{\sfdefault}{phv}  % Sans-serif font for headings and special text (Helvetica)
\renewcommand{\rmdefault}{ptm}  % Set Times as the default body font


% Formatting title and abstract.
\renewcommand\addtolist[5][]{
  \begingroup
    \if\relax#3\relax\def\sep{}\else\def\sep{#5}\fi
    \let\protect\@unexpandable@protect
    \xdef#3{\expandafter{#3}\sep #4[#1]{#2}}%
  \endgroup
}
\newcommand\metadatalist{}
\newcommand\metadataformat[2][]{{\small {\sffamily \bfseries #1:} #2}}
\newcommand\metadata[2][]{\addtolist[#1]{#2}{\metadatalist}{\metadataformat}{\par}}

\renewcommand{\abstract}[1]{\def\abstractlist{{\normalsize\color{robbyfontfg} #1}}}   % Abstract in Times
\renewcommand{\title}[1]{\newcommand{\titlelist}{{\huge\sffamily\bfseries #1}}}       % Title in Helvetica, black color


\newcommand{\mymaketitle}{%
  % Title outside the box - centered (header line serves as top line)
  \setlength{\parindent}{0cm}
  \centering
  \nohyphens
  {
    \setstretch{1.2}
    \titlelist\par
  }
  \vspace{8pt}
  % Authors and affiliations in a transparent box matching abstract style
  \tcbset{enhanced,frame hidden}
  \tcbset{left=0.5cm}
  \tcbset{right=0.5cm}
  \tcbset{top=0.5cm}
  \tcbset{bottom=0.5cm}
  \tcbset{arc=10pt}
  \tcbset{colback=white}
  \tcbset{before skip=0pt}
  \tcbset{grow to left by=1.5pt}
  \tcbset{grow to right by=1.5pt}
  \begin{tcolorbox}
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0cm}
    \raggedright
    \nohyphens
    \@author
  \end{tcolorbox}
  \vspace{8pt}
  % Colored box for abstract, and metadata
  \tcbset{reset}
  \tcbset{enhanced,frame hidden}
  \tcbset{left=0.5cm}
  \tcbset{right=0.5cm}
  \tcbset{top=0.5cm}
  \tcbset{bottom=0.5cm}
  \tcbset{arc=10pt}
  \tcbset{colback=robbyfontbg}
  \tcbset{before skip=0pt}
  \tcbset{grow to left by=1.5pt}
  \tcbset{grow to right by=1.5pt}
  % Conditionally add logo overlay
  \if@showlogo
    \tcbset{overlay={\node[
      anchor=south east,
      at= (frame.south east),
      xshift=-0.5cm,
      yshift=0.5cm] {\includegraphics[width=2.5cm]{\@robbylogopath}};}}
  \fi
  %
  \begin{tcolorbox}
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0.5cm}
    \abstractlist\par
    \vspace{15pt}
    {
      \setlength{\parskip}{0cm}
      \ifdefempty{\metadatalist}{\vspace*{0.65cm}}{\metadatalist\par}
    }
  \end{tcolorbox}
  \vspace{8pt}
  \tcbset{reset}
  \FloatBarrier
}


\if@twocolumn%
\renewcommand{\maketitle}{
\twocolumn[%
  \mymaketitle
  \vskip 0.38cm
]
\thispagestyle{firstpage}
}%
\else%
\renewcommand{\maketitle}{
  \mymaketitle
  \thispagestyle{firstpage}
}%
\fi
