% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% A new style for FAIR pre-prints (Modified for AILab)
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ailab}[2026/02/06 v1.2 AILab Custom Class] % 建议改个名字防止冲突
\LoadClassWithOptions{article}
% \LoadClass[11pt, a4paper]{article}

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
% \RequirePackage{xcolor}
\definecolor{metafg}{HTML}{1C2B33}
\definecolor{metabg}{HTML}{0052D9} % 你的蓝色

% fancy
\RequirePackage{fancyhdr}
\fancypagestyle{firstheader}{
	\fancyhf{}
	\fancyhead[R]{
        % 确保路径正确，如果不显示logo检查这里
		%\includegraphics[height=0.8cm]{assets/ailab_logo.jpg} 
        \includegraphics[height=0.8cm]{assets/hunyuanlogo.png}} 
	\renewcommand{\headrulewidth}{1pt} 
}

% References %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
\hypersetup{
  colorlinks,
  linkcolor=metabg,
  citecolor=metabg,
  urlcolor=metabg
}

\RequirePackage[round,authoryear,sort&compress]{natbib}
\def\bibfont{\small}

% Section and caption format %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
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

% Fonts %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\RequirePackage[T1]{fontenc}
% --- Custom "optimistic" font disabled for arXiv (Linux kpathsea cannot find
% --- TFM files in subdirectories, and we want to avoid shipping a private
% --- font through arXiv's strict TeX environment). Fall back to default sf.
% \DeclareFontFamily{T1}{optimistic}{}
% \DeclareFontShape{T1}{optimistic}{m}{n}{<-> s * [0.88] assets/optimistic}{}
% \DeclareFontShape{T1}{optimistic}{b}{n}{<-> s * [0.88] assets/optimistic}{}
% \pdfmapline{+optimistic < assets/Optimistic.ttf <T1-WGL4.enc}
% \renewcommand{\sfdefault}{optimistic}
\linespread{1.05}

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

% --- Email ---
\newcommand\emaillist{}
\newcommand\emailformat[2][]{{\small\texttt{\href{mailto:#2}{#2}}}}
\newcommand\email[1]{\addtolist[]{#1}{\emaillist}{\emailformat}{, }}

% --- 【新功能】万能头部区域 (Header Content) ---
\newcommand\headercontentlist{} 
% 定义 \headercontent 命令，用户在 tex 文件里调用
\newcommand\headercontent[1]{\renewcommand\headercontentlist{#1}}

% Metadata (Date, etc.)
\newcommand\metadatalist{}
\newcommand\metadataformat[2][]{{\small {\sffamily \bfseries #1:} #2}}
\newcommand\metadata[2][]{\addtolist[#1]{#2}{\metadatalist}{\metadataformat}{\par}}

\renewcommand{\abstract}[1]{%
  \def\abstractlist{{%
    \color{metafg}%
    \setlength{\parindent}{0pt}%
    \setlength{\parskip}{0.45em}%
    #1%
  }}%
}
\renewcommand\date[1]{\metadata[Date]{#1}}
\newcommand\correspondence[1]{\metadata[Correspondence]{#1}}
\renewcommand{\title}[1]{\newcommand{\titlelist}{{\huge\sffamily\bfseries #1}}}
\newcommand{\beginappendix}{\appendix{\huge\sffamily Appendix\par}}

% Titlebox Construction %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\newcommand{\mymaketitle}{%
  \tcbset{enhanced,frame hidden}
  \tcbset{left=0.5cm, right=0.5cm, top=0.5cm, bottom=0.5cm}
  \tcbset{arc=10pt}
  \tcbset{colback=metabg!10}
  \tcbset{before skip=0pt}
  \tcbset{grow to left by=1.5pt, grow to right by=1.5pt}
  
\begin{tcolorbox}
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0.5cm}
    {
      \setlength{\parskip}{0cm}
      \raggedright 
      \nohyphens
      {
        \setstretch{1.618}
        \titlelist\par
      }
      \vskip 0.2cm
      {\color{metabg}\authorlist}\par
      \vskip 0.2cm
      {\color{metabg}\affiliationlist}\par
      \vskip 0.1cm
      {\color{metabg}\contributionlist}\par
      
      \ifdefempty{\emaillist}{}{
         \vskip 0.1cm
         {\centering {\color{metabg}\emaillist}\par}
      }
      %注意：这里之前放链接的地方已经被删掉了
    }
    
    % --- 摘要部分 ---
    \abstractlist\par 
    
    % --- 【新位置】放在摘要下方 ---
    \ifdefempty{\headercontentlist}{}{
       \vskip 0cm % 这里控制摘要和链接的距离
       {
         \centering 
         \color{metabg} 
         \headercontentlist \par
       }
    }
    % ---------------------------

    \vskip 0.1cm % 这里控制链接和Date的距离
    {
      \setlength{\parskip}{0cm}
      % Metadata 包含 Date
      \ifdefempty{\metadatalist}{\vspace*{0.65cm}}{\metadatalist\par}
    }
  \end{tcolorbox}
  \tcbset{reset}
  \FloatBarrier
}

\if@twocolumn%
\renewcommand{\maketitle}{
\twocolumn[\mymaketitle \vskip 0.38cm]
}%
\else%
\renewcommand{\maketitle}{\mymaketitle}%
\fi