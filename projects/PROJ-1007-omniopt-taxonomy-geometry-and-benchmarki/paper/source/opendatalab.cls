% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% A new style for FAIR pre-prints
% Author: dlp@meta.com
% Version: 1.1
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Class declarations %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{opendatalab}
\LoadClassWithOptions{article}

% Layout %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage[top=3cm, bottom=3cm, left=3cm, right=3cm, columnsep=0.65cm]{geometry}
\RequirePackage{microtype}
\RequirePackage{placeins}
\RequirePackage{hyphenat}
\RequirePackage{setspace}
\RequirePackage{parskip}
\RequirePackage[latin, english]{babel}
\RequirePackage{lipsum}
\RequirePackage{etoolbox}

\DisableLigatures[f]{family=sf*} 

% Palatino font
\RequirePackage{tgpagella} % text only
\RequirePackage{mathpazo}  % math & text
\RequirePackage{inconsolata} % for tt font


% Graphics %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\RequirePackage{fancyhdr}
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
\definecolor{odlblue}{HTML}{0064E0}
\definecolor{odlfg}{HTML}{1C2B33}
\definecolor{odlbg}{HTML}{F0FFFF}

% References %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
\hypersetup{
  colorlinks,
  linkcolor=odlblue,
  citecolor=odlblue,
  urlcolor=odlblue
}

\RequirePackage[square, numbers]{natbib}
\def\bibfont{\small}

% Section and caption format %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% \RequirePackage{titlesec}
% \titleformat*{\paragraph}{\itshape}
% \titleformat*{\section}{\Large\sffamily\bfseries}
% \titleformat*{\subsection}{\large\sffamily\bfseries}
% \titleformat*{\subsubsection}{\normalsize\sffamily\bfseries}
% \DeclareTextFontCommand{\textbf}{\bfseries\sffamily}

% \RequirePackage{caption}
% \DeclareCaptionLabelSeparator{custom}{}
% \DeclareCaptionFormat{custom}{{\sffamily\textbf{#1 #2}} #3}
% \captionsetup{singlelinecheck=false,format=custom,labelsep=custom,font=small}
% \captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}

% Meta custom fonts %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% http://c.caignaert.free.fr/Install-ttf-Font.pdf

% \renewcommand*\ttdefault{cmvtt}
% \RequirePackage[T1]{fontenc}

% % \pdfmapline{+optimistic < assets/Optimistic.ttf <T1-WGL4.enc}
% % \renewcommand{\sfdefault}{optimistic}

% \DeclareFontFamily{T1}{optimistic}{}
% \DeclareFontShape{T1}{optimistic}{m}{n}{<-> s * [0.88] assets/optimistic}{}
% \pdfmapline{+optimistic < assets/Optimistic.ttf <T1-WGL4.enc}
% \renewcommand{\sfdefault}{optimistic}

% Authors, affiliations, infos %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\renewcommand\addtolist[5][]{
  \begingroup
    \if\relax#3\relax\def\sep{}\else\def\sep{#5}\fi
    \let\protect\@unexpandable@protect 
    \xdef#3{\expandafter{#3}\sep #4[#1]{#2}}%
  \endgroup
}

\newcommand\authorlist{}
\newcommand\authorformat[2][]{{\bfseries #2$^{#1}$}}
\renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{, }}

\newcommand\affiliationlist{}
\newcommand\affiliationformat[2][]{{\normalsize $^{#1}$#2}}
\newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{, }}

\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\small $^{#1}$#2}}
\newcommand\contribution[2][]{\addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}

\newcommand\metadatalist{}
\newcommand\metadataformat[2][]{{\small {\bfseries #1:} #2}}
\newcommand\metadata[2][]{\addtolist[#1]{#2}{\metadatalist}{\metadataformat}{\par}}

\newcommand\metadataformatinfo[2][]{{\small #2}}
\newcommand\metadatainfo[1]{\addtolist{#1}{\metadatalist}{\metadataformatinfo}{}}

\renewcommand{\abstract}[1]{\def\abstractlist{{\color{odlfg} #1}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}

\renewcommand\date[1]{\metadata[Date]{#1}}
\newcommand\correspondence[1]{\metadata[Correspondence]{#1}}

% \renewcommand{\title}[1]{\newcommand{\titlelist}{{\Large\bfseries #1}}}
\makeatletter
\renewcommand{\title}[1]{%
  \gdef\@title{#1}%      % ① 写回 \@title，供 fancyhdr 使用
  \gdef\titlelist{{\Large\bfseries #1}}% ② 仍给 title-box 用
}
\makeatother

\newcommand{\beginappendix}{\appendix{\LARGE\bfseries Appendix\par}}

% Titlebox %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


\newcommand{\mymaketitle}{%
  \tcbset{enhanced,frame hidden}
  \tcbset{left=0.5cm}
  \tcbset{right=0.5cm}
  \tcbset{top=0.5cm}
  \tcbset{bottom=0.5cm}
  \tcbset{arc=10pt}
  \tcbset{colback=odlbg}
  \tcbset{before skip=0pt}
  \tcbset{grow to left by=1.5pt}
  \tcbset{grow to right by=1.5pt}
  \begin{tcolorbox}
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0.3cm}
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
    }
    %
    \abstractlist\par
    %
    \vskip 0.2cm
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


% Head
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% \fancypagestyle{myheader}{
%   \fancyhf{} %清空所有原有内容
%   \rhead{\includegraphics[height=0.8cm]{template/figures/shlab.png}}
%   \lhead{\includegraphics[height=0.8cm]{template/figures/OpenDataLab_blue_no_words.pdf}}
%   \renewcommand{\headrulewidth}{0.4pt}
%   \renewcommand{\footrulewidth}{0pt}
% }

% % \makeatletter
% % % 定义正文样式（只显示文章标题）
% % \fancypagestyle{otherpages}{
% %   \fancyhf{}
% %   \lhead{\textbf{\@title}} % 使用 \@title，你需要在导言区中定义标题
% %   \renewcommand{\headrulewidth}{0.4pt}
% %   \renewcommand{\footrulewidth}{0pt}
% % }
% % \makeatother

% % --- 重新定义 \maketitle，使首页使用带logo的页眉 ---
% \renewcommand{\maketitle}{
%   \thispagestyle{myheader} % 仅在第一页应用
%   \mymaketitle
% }

% % % 在正文开始设置样式
% % \AtBeginDocument{document}{
% %   \maketitle
% %   \pagenumbering{arabic}
% %   \pagestyle{otherpages}
% % }


%----------------------------------------------
% 1. 首页样式（双 Logo，页码仍在底部中央）
%----------------------------------------------
\fancypagestyle{firstpage}{%
  \fancyhf{}%
  \lhead{\includegraphics[height=0.8cm]{assets/OpenDataLab_blue_no_words}}%
  \rhead{\includegraphics[height=0.8cm]{assets/shlab}}%
  \fancyfoot[C]{\thepage}%
  \renewcommand{\headrulewidth}{0.4pt}%
}

%----------------------------------------------
% 2. 正文样式 —— *先留空*，稍后再把标题填进去
%----------------------------------------------
\fancypagestyle{body}{%
  \fancyhf{}%
  % 这里暂时不写 \lhead，稍后 \maketitle 里补
  \fancyfoot[C]{\thepage}%
  \renewcommand{\headrulewidth}{0.4pt}%
}

%------------------------------------------------
% 3. 重写 \maketitle
%------------------------------------------------
\makeatletter
\let\oldmaketitle\maketitle
\renewcommand{\maketitle}{%
  % ----- 原来的标题页 -----
  \begingroup
    \oldmaketitle
    \thispagestyle{firstpage}         % 首页：双 LOGO
  \endgroup
  %
  % ----- 正文页眉/页脚 -----
  \pagestyle{body}                    % 先切换到 body 样式
  \fancyhead[L]{\nouppercase{\textbf{\@title}\hspace{1em}}}% 再把标题填进去
}
\makeatother

%------------------------------------------------
% 4. “plain” 备用样式（章节或双栏分页时用）
%------------------------------------------------
\fancypagestyle{plain}{%
  \fancyhf{}%
  \fancyfoot[C]{\thepage}% 只给页码，不放标题
  \renewcommand{\headrulewidth}{0pt}%
}