% Class declarations %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{style}
\LoadClassWithOptions{article}

% Layout %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage[top=2.25cm, bottom=2.25cm, left=2.5cm, right=2.5cm, columnsep=0.65cm]{geometry}
\setlength{\headsep}{0.6cm}
\RequirePackage{microtype}
\RequirePackage{placeins}
\RequirePackage{hyphenat}
\RequirePackage{setspace}
\RequirePackage{parskip}
\RequirePackage[latin, english]{babel}
\RequirePackage{lipsum}
\RequirePackage{etoolbox}
\RequirePackage{fancyhdr}

% Body line spacing
\AtBeginDocument{\setstretch{0.99}}

% header and footer settings
\newcommand{\headertext}[1]{\def\@headertext{#1}}
\newcommand{\@headertext}{}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[C]{\sffamily\small\color{stylegreen}\@headertext}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.5pt}
\renewcommand{\footrulewidth}{0pt}


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

% \RequirePackage[most]{tcolorbox}
\RequirePackage{tcolorbox}
\tcbuselibrary{skins}
\RequirePackage{xcolor}
% \definecolor{stylebg}{HTML}{eff9ed}
% \definecolor{stylegreen}{HTML}{2a7a1b}
\definecolor{stylebg}{HTML}{F5F2FF}
\definecolor{stylegreen}{HTML}{534AD1}
% References %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
\hypersetup{
  colorlinks,
  linkcolor=stylegreen,
  citecolor=stylegreen,
  urlcolor=stylegreen
}

\RequirePackage[numbers, sort&compress]{natbib}
\def\bibfont{\small}

% Section and caption format %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% \RequirePackage{titlesec}
% \titleformat*{\paragraph}{\itshape}
% \titleformat*{\section}{\Large\sffamily\bfseries}
% \titleformat*{\subsection}{\large\sffamily\bfseries}
% \titleformat*{\subsubsection}{\normalsize\sffamily\bfseries}
% \DeclareTextFontCommand{\textbf}{\bfseries\sffamily}
\RequirePackage{titlesec}
\titleformat*{\paragraph}{\palatinofont\itshape}
\titleformat*{\section}{\Large\palatinofont\bfseries}
\titleformat*{\subsection}{\large\palatinofont\bfseries}
\titleformat*{\subsubsection}{\normalsize\palatinofont\bfseries}
\DeclareTextFontCommand{\textbf}{\palatinofont\bfseries}

\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}
% \DeclareCaptionFormat{custom}{{\sffamily\textbf{#1 #2}} #3}
\DeclareCaptionFormat{custom}{{\palatinofont\bfseries #1 #2} #3}
% \captionsetup{singlelinecheck=false,format=custom,labelsep=custom,font=small}
\captionsetup{
  singlelinecheck=false,
  format=custom,
  labelsep=custom,
  font=small,
  justification=raggedright
}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}

\renewcommand*\ttdefault{cmvtt}
\RequirePackage[T1]{fontenc}
% Local Palatino-like font for title and authors only
\newcommand{\palatinofont}{\fontfamily{qpl}\selectfont}
\DeclareFontFamily{T1}{optimistic}{}
\DeclareFontShape{T1}{optimistic}{m}{n}{<-> s * [0.88] style/optimistic}{}
\DeclareFontShape{T1}{optimistic}{b}{n}{<-> s * [0.88] style/optimistic}{}
\pdfmapline{+optimistic < style/Optimistic.ttf <T1-WGL4.enc}
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
% \newcommand\authorformat[2][]{{\normalsize\sffamily \bfseries #2$^{#1}$}}
\newcommand\authorformat[2][]{{\normalsize\palatinofont\bfseries #2$^{#1}$}}
\renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{, }}

\newcommand\affiliationlist{}
\newcommand\affiliationformat[2][]{{\normalsize $^{#1}$#2}}
\newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{\quad}}

\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\small $^{#1}$#2}}
\newcommand\contribution[2][]{\addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}

\newcommand\metadatalist{}
\newcommand\metadataformat[2][]{{\small {\sffamily \bfseries #1:} #2}}
\newcommand\metadata[2][]{\addtolist[#1]{#2}{\metadatalist}{\metadataformat}{\par}}

% \renewcommand{\abstract}[1]{\def\abstractlist{{\color{stylegreen} #1}}}
\renewcommand{\abstract}[1]{\def\abstractlist{{#1}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}


% \renewcommand{\title}[1]{\newcommand{\titlelist}{{\huge\sffamily\bfseries #1}}}
\renewcommand{\title}[1]{%
  \newcommand{\titlelist}{%
    \parbox{0.95\textwidth}{%
      \centering
      \palatinofont\huge\bfseries
      \setstretch{1}%
      #1\par
    }%
  }%
}

\newcommand{\beginappendix}{\appendix{\huge\sffamily Appendix\par}}

%%======== Header and Footer Content ========
\fancypagestyle{firststyle}{
    \fancyhf{}
    \fancyfoot[C]{\thepage} %
    \fancyhead[R]{
        % Intentionally left blank
    }
    \fancyhead[L]{
        \vskip 4mm
        \includegraphics[width=20mm]{style/wanlogo.png}
    }
    % \fancyhead[R]{
    %     \vskip 4mm
    % }
    \renewcommand{\headrulewidth}{1pt}
}

% Rules for title box
\newcommand{\@toptitlebar}{
  \color{stylebg}{\hrule height 0.5pt}
  \vskip 6mm
}
\newcommand{\@bottomtitlebar}{
  \vskip 6mm
  \color{stylebg}{\hrule height 0.5pt}
}

% Titlebox %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\newcommand{\mymaketitle}{%
  % Apply the header with logo to the first page
  \thispagestyle{firststyle}
  % Title and Author Block
  \begin{center}
    \vspace*{0.8cm}
    % \@toptitlebar % MODIFICATION: REMOVED TOP LINE
    \titlelist
    % \@bottomtitlebar % MODIFICATION: REMOVED BOTTOM LINE
    \vskip 4mm
    \authorlist
    \vskip 2mm
    \affiliationlist
    \vskip 2mm
    \contributionlist
  \end{center}
  \vskip 2mm

  % Abstract and Metadata Block
  \tcbset{enhanced,frame hidden}
  \tcbset{left=0.5cm}
  \tcbset{right=0.5cm}
  \tcbset{top=0.5cm}
  \tcbset{bottom=0.5cm}
  \tcbset{arc=10pt}
  \tcbset{colback=stylebg}
  \tcbset{before skip=0pt}
  \tcbset{grow to left by=1.5pt}
  \tcbset{grow to right by=1.5pt}
  % \tcbset{overlay={\node[
  %   anchor=south east,
  %   at= (frame.south east),
  %   xshift=-0.5cm,
  %   yshift=0.5cm] {\includegraphics[width=1.5cm]{assets/logometa.pdf}};}}

  % \begin{tcolorbox}
  %   \setlength{\parindent}{0cm}
  %   \setlength{\parskip}{0.5cm}
  %   %
  %   \abstractlist\par
  %   %
  %   \vskip 0.5cm
  %   %
  %   {
  %     \setlength{\parskip}{0cm}
  %     \ifdefempty{\metadatalist}{\vspace*{0.65cm}}{\metadatalist\par}
  %   }
  % \end{tcolorbox}
  \begin{tcolorbox}
  \setlength{\parindent}{0cm}
  \setlength{\parskip}{0.5cm}

  \begin{center}
    {\palatinofont\large\bfseries Abstract}
  \end{center}
  \vspace{-0.2cm}

  \abstractlist\par

  \ifdefempty{\metadatalist}{}{%
    \vskip 0.5cm
    {
      \setlength{\parskip}{0cm}
      \metadatalist\par
    }
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