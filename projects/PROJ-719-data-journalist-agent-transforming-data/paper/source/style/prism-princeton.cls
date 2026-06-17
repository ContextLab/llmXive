% --------------------------------------------------------------------------- %
% LaTeX Class File
% Author: PRISM Lab (Modified for Princeton University)
% Version: 1.0
% Inspired by the Meta FAIR latex template
% --------------------------------------------------------------------------- %

% --------------------------------------------------------------------------- %

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{prism-princeton}
\LoadClassWithOptions{article}

% --------------------------------------------------------------------------- %
% Layout %

\RequirePackage[top=2.25cm, bottom=2.5cm, left=2.5cm, right=2.5cm, columnsep=0.65cm]{geometry}

% --------------------------------------------------------------------------- %
% Packages %
\RequirePackage[T1]{fontenc}
% \RequirePackage[utf8]{inputenc}
\RequirePackage[latin, english]{babel}
\RequirePackage{lmodern}
\RequirePackage{XCharter}
\RequirePackage[varqu,varl]{inconsolata}
\RequirePackage{multicol}
\RequirePackage{amsmath, amsfonts, amssymb, amsthm}
\RequirePackage[charter, vvarbb, scaled=1.07]{newtxmath}
\RequirePackage{enumerate}
\RequirePackage[inline]{enumitem}
\RequirePackage{mathtools}
\RequirePackage{graphicx}
\RequirePackage{setspace}
\RequirePackage{longtable,tabularx}
\RequirePackage{parskip}
\RequirePackage{placeins} 
\RequirePackage{hyphenat}
\RequirePackage{float}
\RequirePackage{multirow}
\RequirePackage{bbm}
\RequirePackage[table,dvipsnames]{xcolor}
\RequirePackage{threeparttable}
\RequirePackage{balance}
\RequirePackage[ruled,algo2e]{algorithm2e}
\RequirePackage{algpseudocode}
\RequirePackage{adjustbox}
\RequirePackage{booktabs}
\RequirePackage{bm}
\RequirePackage{etoolbox}
\RequirePackage{microtype}
% \RequirePackage{appendix}
% \RequirePackage[title]{appendix}
\RequirePackage{units}
\RequirePackage{xspace}
\RequirePackage[most]{tcolorbox}
\RequirePackage{caption}

% \DisableLigatures[f]{family=sf*} 


% --------------------------------------------------------------------------- %
% Packages %
% \definecolor{princeton_orange}{HTML}{7a22d8}
% \colorlet{bgcolor}{princeton_orange!8}

\definecolor{princeton_orange}{HTML}{1F4E79}
\colorlet{bgcolor}{princeton_orange!10}

% --------------------------------------------------------------------------- %
% References %

\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref} 
\hypersetup{
  colorlinks,
  linkcolor=princeton_orange,
  citecolor=princeton_orange,
  urlcolor=princeton_orange
}

\RequirePackage[square,numbers,sort]{natbib}
\def\bibfont{\small}


% --------------------------------------------------------------------------- %
% Sections %

\RequirePackage{titlesec}
\titleformat*{\paragraph}{\itshape}
\titleformat*{\section}{\Large\sffamily\bfseries}
\titleformat*{\subsection}{\large\sffamily\bfseries}
\titleformat*{\subsubsection}{\normalsize\sffamily\bfseries}
\DeclareTextFontCommand{\textbf}{\bfseries\sffamily}

\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\sffamily\textbf{#1 #2}} #3}
\captionsetup{singlelinecheck=false,format=custom,labelsep=custom,font=small}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}



% --------------------------------------------------------------------------- %
% Title Page %

\RequirePackage{tikz}
\usetikzlibrary{mindmap,trees}
\RequirePackage[title]{appendix}
\RequirePackage{pifont} % for cmark/xmark

% Custom Colors
\definecolor{claude_color}{HTML}{F89E62}
\definecolor{deepseek_color}{HTML}{78B6E8}
\definecolor{o3_mini_color}{HTML}{6CD5A1}
\definecolor{red_color}{HTML}{E13B55}
\definecolor{prompt_color}{HTML}{71502B}

% Custom TColorBox Styles
\tcbset{
  promptstyle/.style={
    colback=gray!10,
    colframe=gray!60,
    boxrule=0.5pt,
    arc=2pt,
    outer arc=2pt,
    left=4pt,
    right=4pt,
    top=4pt,
    bottom=4pt,
    fonttitle=\bfseries,
    sharp corners=south,
  }
}

\tcbset{
  promptstyle_prompt_iuq/.style={
    colback=prompt_color!10,
    colframe=prompt_color!60,
    coltitle=white,
    boxrule=1.0pt,
    arc=2pt,
    outer arc=2pt,
    left=4pt,
    right=4pt,
    top=4pt,
    bottom=4pt,
    fonttitle=\bfseries,
  }
}

\tcbset{
  promptstyle_claude/.style={
    colback=claude_color!10,
    colframe=claude_color!60,
    coltitle=black,
    boxrule=1.0pt,
    arc=2pt,
    outer arc=2pt,
    left=4pt,
    right=4pt,
    top=4pt,
    bottom=4pt,
    fonttitle=\bfseries,
  }
}

\tcbset{
  promptstyle_deepseek/.style={
    colback=deepseek_color!10,
    colframe=deepseek_color!60,
    coltitle=black,
    boxrule=1.0pt,
    arc=2pt,
    outer arc=2pt,
    left=4pt,
    right=4pt,
    top=4pt,
    bottom=4pt,
    fonttitle=\bfseries,
  }
}

\tcbset{
  promptstyle_o3_mini/.style={
    colback=o3_mini_color!10,
    colframe=o3_mini_color!60,
    coltitle=black,
    boxrule=1.0pt,
    arc=2pt,
    outer arc=2pt,
    left=4pt,
    right=4pt,
    top=4pt,
    bottom=4pt,
    fonttitle=\bfseries,
  }
}

% Theorems and Environments
\newtheorem{theorem}{Theorem}
\newtheorem{assumption}{Assumption}
\newtheorem{proposition}{Proposition}
\newtheorem{definition}{Definition}
\newtheorem{corollary}{Corollary}
\newtheorem{remark}{Remark}
\newtheorem{lemma}{Lemma}

% Utility Macros
\newcommand{\cmark}{\ding{51}}
\newcommand{\xmark}{\ding{55}}

% --------------------------------------------------------------------------- %
% Title Page %

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
\newcommand\affiliationformat[2][]{{\small $^{#1}$#2}}
\newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{, }}

\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\small \em $^{#1}$#2}}
\newcommand\contribution[2][]{\addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}

\newcommand\metadatalist{}
\newcommand\metadataformat[2][]{{\small {\sffamily \bfseries #1:} #2}}
\newcommand\metadata[2][]{\addtolist[#1]{#2}{\metadatalist}{\metadataformat}{\par}}

\renewcommand{\abstract}[1]{\def\abstractlist{{ #1}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}

\newcommand{\keywords}[1]{\def\keywordslist{{\small \sffamily \textbf{Keywords:} #1}}}

% \newcommand{\website}[2]{\def\websitelist{{\small \sffamily \textbf{Website:} \href{#1}{\color{princeton_orange}#2}}}}

% \newcommand{\code}[2]{\def\codelist{{\small \sffamily \textbf{Code:} \href{#1}{\color{princeton_orange}#2}}}}

% \renewcommand\date[1]{\metadata[Date]{#1}}
% \newcommand\correspondence[1]{\metadata[Correspondence]{#1}}

\definecolor{aui-magenta}{HTML}{D63384}
\newcommand{\website}[2]{\def\websitelist{{\small \sffamily \faHome\,\textbf{Website:} \href{#1}{\color{aui-magenta}\texttt{#2}}}}}

\newcommand{\code}[2]{\def\codelist{{\small \sffamily \faGithub\,\textbf{Code:} \href{#1}{\color{aui-magenta}\texttt{#2}}}}}

\renewcommand\date[1]{\metadata[Date]{#1}}
\newcommand{\corrlist}{}
\newcommand\correspondence[1]{\def\corrlist{{\small \sffamily \faEnvelope\,\textbf{Correspondence:} #1}}}

\renewcommand{\title}[1]{\newcommand{\titlelist}{{\huge\sffamily\bfseries #1}}}

\newcommand{\beginappendix}{\appendix{\huge\sffamily Appendix\par}}


% --------
% %% keywords definition
% \def\keywords#1{%
%  \ifdefined\isaccepted \else
%     \textbf{Keywords:} #1%
%  \fi
%   \ifdefined\nohyperref\else\ifdefined\hypersetup
%     \hypersetup{pdfkeywords={#1}}
%   \fi\fi
% }

% --------------------------------------------------------------------------- %
% Titlebox %


\newcommand{\mymaketitle}{%
  \tcbset{enhanced,frame hidden}
  \tcbset{left=0.5cm}
  \tcbset{right=0.5cm}
  \tcbset{top=0.5cm}
  % \tcbset{top=1.5cm}
  \tcbset{bottom=0.5cm}
  \tcbset{arc=10pt}
  \tcbset{boxrule=0.0pt}
  \tcbset{colback=bgcolor}
  \tcbset{before skip=0pt}
  \tcbset{grow to left by=1.5pt}
  \tcbset{grow to right by=1.5pt}
  % \tcbset{overlay={\node[
  %   anchor=south east,
  %   at= (frame.south east),
  %   xshift=-0.5cm,
  %   yshift=0.4cm] {\includegraphics[width=3.5cm]{style/logo/princeton_logo.png}};
  %   }}
  % 
 % \tcbset{overlay={
 %    \node[anchor=north west, at=(frame.north west), xshift=0.5cm, yshift=-0.4cm]
 %      {\includegraphics[height=1.1cm]{fig/ox.png}\hspace{0.3cm}%
 %       \includegraphics[height=1.1cm]{fig/stf.png}};
 %  }}
  \noindent
  \includegraphics[height=1cm]{fig/ox.png}
  \hspace{0.2cm}%
  \includegraphics[height=1cm]{fig/stf.png}
  \par
  \vskip -0.05cm
  % \vskip 0.01cm
  % \noindent\rule{\linewidth}{1pt}
  % \vskip 0.15cm
  
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
      %
      \vskip 0.3cm
      \websitelist\par
      \codelist\par
      \corrlist\par
    }
    %
    \abstractlist\par
    %
    {
      \setlength{\parskip}{0cm}
      \ifdefempty{\metadatalist}{}{\metadatalist\par}
    }
  \end{tcolorbox}      
  %     \affiliationlist\par
  %     %
  %     \contributionlist\par
  %   }
  %   %
  %   \abstractlist\par
  %   %
  %   \vskip -0.25cm
  %   %
  %   % \keywordslist\par
  %   % %
  %   % \vskip -0.25cm
  %   %
  %   \websitelist\par
  %   %
  %   \vskip -0.25cm
  %   %
  %   % \codelist\par
  %   %
  %   \vskip -0.25cm
    
  %   {
  %     \setlength{\parskip}{0cm}
  %     \ifdefempty{\metadatalist}{\vspace*{0.65cm}}{\metadatalist\par}
  %   }
  % \end{tcolorbox}
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

%%======== Captions in tables and figures ========
\DeclareCaptionLabelSeparator{pipe}{$\vert$}% or $\vert$
\captionsetup{labelfont={}, %{bf,sf},%
labelsep=space,%
figurename=Figure,%
labelsep=pipe,
singlelinecheck=off,%
%justification=centering
}