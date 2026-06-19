% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% A style for AI2 pre-prints
% Author: jacobm@allenai.org
% Version: 1.1
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Class declarations %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ai2style/ai2}
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
\RequirePackage{ragged2e}
\RequirePackage{fancyhdr}  % custom headers/footers

% \DisableLigatures[f]{family=sf*}

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

\RequirePackageWithOptions{xcolor}
\RequirePackage[most]{tcolorbox}
\definecolor{ai2accent}{HTML}{407579}
% \definecolor{ai2accent}{HTML}{ff0000}
\definecolor{ai2foreground}{HTML}{1C2B33}
\definecolor{ai2background}{HTML}{faf2e9}
\definecolor{ai2foregroundDark}{HTML}{0A2B35}
\definecolor{ai2pink}{HTML}{F0529C}

% References %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{hyperref}
\hypersetup{
  colorlinks=true,
  linkcolor=ai2accent,
  citecolor=ai2accent,
  urlcolor=ai2accent,
  anchorcolor=ai2accent,
  menucolor=ai2accent,
  filecolor=ai2accent,
  % linktocpage=true,
  allcolors=ai2accent
}


\RequirePackage[noabbrev,nameinlink]{cleveref}
% Reapply hyperref settings after cleveref to ensure they stick
\AtBeginDocument{
  \hypersetup{
    allcolors=ai2accent,
    linkcolor=ai2accent,
    citecolor=ai2accent,
    urlcolor=ai2accent
  }
}


% change base color of text
\AtBeginDocument{
  \color{ai2foregroundDark}
  \pagecolor{white}
}


\RequirePackage[round,authoryear]{natbib}
\def\bibfont{\small}


% Create a custom size that's exactly 1pt larger than normalsize
\newcommand{\slightlylarger}{%
  \fontsize{\dimexpr\f@size pt+1}{\dimexpr\f@size pt-0.2\baselineskip}\selectfont%
}

% Create a custom size that's exactly 1pt smaller than normalsize
\newcommand{\slightlysmaller}{%
  \fontsize{\dimexpr\f@size pt-1}{\dimexpr\f@size pt+0.2\baselineskip}\selectfont%
}

% Section and caption format %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{titlesec}
% \titleformat*{\paragraph}{\bfseries}
\titleformat*{\section}{\Large\sffamily\bfseries}
\titleformat*{\subsection}{\large\sffamily\bfseries}
\titleformat*{\subsubsection}{\slightlylarger\sffamily\bfseries}
\titleformat*{\paragraph}{\slightlysmaller\sffamily\bfseries}

% make bolded text smaller to match with serif.
% \DeclareTextFontCommand{\textbf}{\bfseries\sffamily}
\DeclareTextFontCommand{\textbf}{\fontsize{9}{11}\selectfont\bfseries\sffamily}


\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\sffamily\textbf{#1 #2}} #3}

% force caption color to match body text
\captionsetup{
  singlelinecheck=false,
  format=custom,
  labelsep=custom,
  font={small,color=ai2foregroundDark},
  labelfont={color=ai2foregroundDark},
  textfont={color=ai2foregroundDark},
}
\captionsetup[sub]{
  singlelinecheck=true,
  format=custom,
  labelsep=custom,
  font={small,color=ai2foregroundDark},
  labelfont={color=ai2foregroundDark},
  textfont={color=ai2foregroundDark},
}

% %%======== Header and Footer Content ========
% %
% % Header and Footer for the first page
% \pagestyle{fancy}   % Enables the custom headers/footers
% \fancyhf{}
% % \renewcommand{\headrulewidth}{0pt}
% \fancyhead[L]{
%     \includegraphics[width=50pt]{ai2style/assets/Ai2_logo_pink_RGB.png}
% }
% \fancyhead[R]{}
% \fancyhead[C]{}
% %
% \fancyfoot[L]{}
% \fancyfoot[R]{}
% \fancyfoot[C]{\footerfont\bfseries\relax}

% \usepackage{graphicx}
% \usepackage{eso-pic}

% % Adjust the dimensions and position of the image as needed
% \AddToShipoutPictureBG*{%
%   \AtPageUpperLeft{%
%     \hspace{10pt}
%     \raisebox{-\height+\dimexpr -15pt\relax}{
%     \includegraphics[width=0.1\textwidth]{ai2style/assets/Ai2_logo_pink_RGB.png}}%
%   }
% }


% % AI2 custom fonts (WIP) %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% % http://c.caignaert.free.fr/Install-ttf-Font.pdf

% Set the main font to Times New Roman
% \setmainfont{Manrope}
% Set sans-serif font to Manrope
\RequirePackage{ifxetex}
\usepackage{ifxetex}
\ifxetex
    \usepackage{fontspec}
    \setsansfont{Manrope}
\else
    \RequirePackage[T1]{fontenc}
    \usepackage[T1]{fontenc}
    \usepackage{ai2style/manrope}
    \renewcommand{\sfdefault}{manrope}
\fi

% % \pdfmapline{+optimistic < assets/Optimistic.ttf <T1-WGL4.enc}
% % \renewcommand{\sfdefault}{optimistic}

% \DeclareFontFamily{T1}{manrope}{}
% \DeclareFontShape{T1}{manrope}{m}{n}{<-> s * [0.88] ai2style/fonts/Manrope}{}
% \pdfmapline{+manrope < ai2style/fonts/Manrope.ttf <T1-WGL4.enc}
% \renewcommand{\sfdefault}{manrope}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Imporve appearance of ToC

\RequirePackage{tocloft}

% Make sure the section titles in TOC are in Manrope
\renewcommand{\cftsecfont}{\sffamily}
\renewcommand{\cftsubsecfont}{\sffamily}
\renewcommand{\cftsubsubsecfont}{\sffamily}
\renewcommand{\cftparafont}{\sffamily}

% Make the page numbers in TOC use Manrope
\renewcommand{\cftsecpagefont}{\sffamily}
\renewcommand{\cftsubsecpagefont}{\sffamily}
\renewcommand{\cftsubsubsecpagefont}{\sffamily}
\renewcommand{\cftparapagefont}{\sffamily}

% % Adjust the spacing
% \setlength{\cftsecindent}{1.5em}
% \setlength{\cftsubsecindent}{3.0em}
% \setlength{\cftsubsubsecindent}{4.5em}
% \setlength{\cftparaindent}{6.0em}

% \setlength{\cftsecnumwidth}{2.5em}
% \setlength{\cftsubsecnumwidth}{3.5em}
% \setlength{\cftsubsubsecnumwidth}{4.5em}
% \setlength{\cftparanumwidth}{5.5em}

% % Adjust vertical spacing
% \setlength{\cftbeforesecskip}{5pt plus 1pt}
% \setlength{\cftbeforesubsecskip}{2pt plus 1pt}
% \setlength{\cftbeforesubsubsecskip}{2pt plus 1pt}

% % Style the dots
% \renewcommand{\cftsecdotsep}{1.5}
% \renewcommand{\cftsubsecdotsep}{1.5}
% \renewcommand{\cftsubsubsecdotsep}{1.5}
% \renewcommand{\cftparadotsep}{1.5}

% % Color for the dots (using the pre-defined ai2accent color)
% \renewcommand{\cftsecleader}{\color{ai2accent}\cftsecdotsep}
% \renewcommand{\cftsubsecleader}{\color{ai2accent}\cftsubsecdotsep}
% \renewcommand{\cftsubsubsecleader}{\color{ai2accent}\cftsubsubsecdotsep}
% \renewcommand{\cftparaleader}{\color{ai2accent}\cftparadotsep}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


% KYLE TESTING SOME STUFF OUT
\newcommand\authorlistOne{}
\newcommand\authorlistTwo{}
\newcommand\authorlistThree{}
\newcommand\authorlistFour{}
\newcommand\authorlistFive{}


\newcommand\authorOne[2][]{\addtolist[#1]{#2}{\authorlistOne}{\authorformat}{\quad }}
\newcommand\authorTwo[2][]{\addtolist[#1]{#2}{\authorlistTwo}{\authorformat}{\quad }}
\newcommand\authorThree[2][]{\addtolist[#1]{#2}{\authorlistThree}{\authorformat}{\quad }}
\newcommand\authorFour[2][]{\addtolist[#1]{#2}{\authorlistFour}{\authorformat}{\ \ }} % to save space
\newcommand\authorFive[2][]{\addtolist[#1]{#2}{\authorlistFive}{\authorformat}{\quad }}






% Authors, affiliations, infos %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\renewcommand\addtolist[5][]{
  \begingroup
    \if\relax#3\relax\def\sep{}\else\def\sep{#5}\fi
    \let\protect\@unexpandable@protect
    \xdef#3{\expandafter{#3}\sep #4[#1]{#2}}%
  \endgroup
}

\newcommand\authorlist{}
\newcommand\authorformat[2][]{\mbox{\sffamily \bfseries #2#1}}
% \newcommand\authorformat[2][]{{\sffamily \bfseries \mbox{#2}$^{#1}$}}
% \renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{...}}/
\renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{\quad}}

\newcommand\affiliationlist{}
\newcommand\affiliationformat[2][]{\normalsize\hbox{#1#2}}
\newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{\quad}}


\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\small $^{#1}$#2}}
\newcommand\contribution[2][]{\addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}

\newcommand\metadatalist{}
\newcommand\metadataformat[2][]{{\small {\sffamily \bfseries #1} #2}}
\newcommand\metadata[2][]{\addtolist[#1]{#2}{\metadatalist}{\metadataformat}{\par}}

% switch to sans serif
\newcommand\sans[1][]{\sffamily #1}

\renewcommand{\abstract}[1]{\def\abstractlist{{\color{ai2foreground} #1}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}

\renewcommand\date[1]{\metadata[Date]{#1}}
\newcommand\correspondence[1]{\metadata[Correspondence]{#1}}


\renewcommand{\title}[1]{\newcommand{\titlelist}{{\Huge\sffamily\bfseries\color{ai2pink} #1}}}

\newcommand{\beginappendix}{\appendix{\huge\sffamily Appendix\par}}

% Titlebox %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


\newcommand{\mymaketitle}{%
  \tcbset{enhanced,frame hidden}
  \tcbset{left=0.5cm}
  \tcbset{right=0.5cm}
  \tcbset{top=0.5cm}
  \tcbset{bottom=0.5cm}
  \tcbset{arc=3.5pt}
  \tcbset{colback=ai2background}
  \tcbset{before skip=0pt}
  \tcbset{grow to left by=1.5pt}
  \tcbset{grow to right by=1.5pt}
  % \tcbset{overlay={\node[
  %   anchor=north east,
  %   at= (frame.north east),
  %   xshift=0cm,
  %   yshift=1.33cm] {\includegraphics[width=2cm]{ai2style/assets/Ai2_logo_pink_RGB.png}};}}
  \tcbset{overlay={\node[
    anchor=north east,
    at= (frame.north east),
    xshift=-0.5cm,
    yshift=-0.45cm] {\includegraphics[width=1.57cm]{ai2style/assets/Ai2_logo_pink_RGB.png}};}}

  \setlength{\parskip}{0cm}
  % \raggedright
  \nohyphens
  %
  {
    \setstretch{1.618}
    \titlelist\par
  }
  \vskip 0.5cm
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0cm}
    {
      % \setlength{\parskip}{0cm}
      % \raggedright
      % \nohyphens
      % %
      % {
      %   \setstretch{1.618}
      %   \titlelist\par
      % }
      % \vskip 0.2cm
      %
      \begin{minipage}[h]{0.95\linewidth}
        \RaggedRight
          \authorlistOne \par
          \vspace{0.3cm}  % Add spacing between first and second group
          \authorlistTwo\par
          \vspace{0.3cm}  % Add spacing between second and third group
          \authorlistThree\par
          \vspace{0.3cm}
          \authorlistFour\par
          % \vspace{0.05cm}
          \authorlistFive\par
          % \authorlist\par
      \end{minipage}%
      \hfill
      \vspace{0.3cm}
      % \vskip 0.2cm
      %
      % \setlength{\parskip}{0cm}
      \affiliationlist\par
      %
      \vspace{0.3cm}
      \contributionlist\par
      \vspace{0.5cm}
      \ifdefempty{\metadatalist}{}{\metadatalist}
    }
    %
    \vskip 0.5cm
    %
  \begin{tcolorbox}
    % \setlength{\parindent}{0cm}
    % \setlength{\parskip}{0.5cm}
    % {
    %   % \setlength{\parskip}{0cm}
    %   % \raggedright
    %   % \nohyphens
    %   % %
    %   % {
    %   %   \setstretch{1.618}
    %   %   \titlelist\par
    %   % }
    %   % \vskip 0.2cm
    %   %
    %   \authorlist\par
    %   \vskip 0.2cm
    %   %
    %   \affiliationlist\par
    %   %
    %   \contributionlist\par
    % }
    %
    {\Large\sffamily\bfseries Abstract\par}
    \vspace{0.5cm}
    \abstractlist\par
    % %
    % \vskip 0.5cm
    % %
    % {
    %   \setlength{\parskip}{0cm}
    %   \ifdefempty{\metadatalist}{\vspace*{0.65cm}}{\metadatalist\par}
    % }
  \end{tcolorbox}
  \tcbset{reset}
  \FloatBarrier
  \setlength{\parskip  }{5.5\p@}
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
