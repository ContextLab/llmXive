%%======== Package options and base class ========
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{EPIC Lab@SJTU}
\LoadClassWithOptions{article}

%%======== Packages Required ========
\RequirePackage{microtype}
\RequirePackage{placeins}
\RequirePackage{hyphenat}
\RequirePackage{setspace}
\RequirePackage{parskip}
\RequirePackage[latin, english]{babel}
\RequirePackage{lipsum}
\RequirePackage{helvet}
\RequirePackage{etoolbox}
\RequirePackage{fancyhdr}  % custom headers/footers
\RequirePackage{ulem}  % 引用下划线
\RequirePackage{graphicx}
\RequirePackage{subcaption}
\RequirePackage{booktabs}
\RequirePackage{nicematrix}
\RequirePackage{multirow}
\RequirePackage{bm}
\RequirePackage[most]{tcolorbox}
\RequirePackage{xcolor}
\RequirePackage[T1]{fontenc}

%%======== Layout ========
\RequirePackage[top=2.5cm, bottom=2.5cm, left=2.5cm, right=2.5cm, columnsep=0.65cm]{geometry}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

%%======== Color (紫色系) ========
% \definecolor{epicbg}{HTML}{6A5ACD} % 主色：紫罗兰
% \definecolor{epiccolor}{HTML}{6A5ACD}
% \definecolor{epiccolor2}{HTML}{F8F4FF} % 浅紫背景
% \newcommand{\epiccolor}[1]{{\bfseries\color[HTML]{6A5ACD} #1}} 

%% 浅蓝色
% \definecolor{epicbg}{HTML}{0077b6} 
% \definecolor{epiccolor}{HTML}{0077b6}
% \definecolor{epiccolor2}{HTML}{FFFFFF} 
% \newcommand{\epiccolor}[1]{{\bfseries\color[HTML]{0077b6} #1}} 

\definecolor{epicbg}{HTML}{001893} 
\definecolor{epiccolor}{HTML}{001893}
\definecolor{epiccolor2}{HTML}{FFFFFF} 
\definecolor{epiclinkcolor}{HTML}{00bbf9}
\newcommand{\epiccolor}[1]{{\bfseries\color[HTML]{001893} #1}} 


%% 红色
% \definecolor{epicbg}{HTML}{9e2a2b} 
% \definecolor{epiccolor}{HTML}{9e2a2b}
% \definecolor{epiccolor2}{HTML}{FFFFFF} 
% \newcommand{\epiccolor}[1]{{\bfseries\color[HTML]{9e2a2b} #1}} 


%%========  Custom font sizes and styles ========
\renewcommand{\sfdefault}{cmr}  
\renewcommand{\rmdefault}{cmr}
\newcommand{\sectionfont}{\fontsize{12}{10}\selectfont} 
\newcommand{\subsectionfont}{\fontsize{11}{10}\selectfont}
\newcommand{\bffont}{\fontsize{8.8}{10}\selectfont} 
\newcommand{\authorfont}{\bfseries\fontsize{10}{12}\selectfont} 
\newcommand{\affiliationfont}{\fontsize{10}{12}\selectfont}
\newcommand{\contributionfont}{\fontsize{10}{12}\selectfont}
\newcommand{\checkdatafont}{\fontsize{7.92}{10}\selectfont}
\newcommand{\abstractinfont}{\fontsize{10}{12}\selectfont} 
\newcommand{\titlefont}{\fontsize{17}{20}\selectfont} 
\newcommand{\abstractfont}{\fontsize{12}{12}\selectfont} 
\usepackage[subfigure]{tocloft}
\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}}
\renewcommand{\cftsecfont}{\sffamily}
\renewcommand{\cftsecpagefont}{\sffamily}{\color{epiccolor}}
\renewcommand{\cfttoctitlefont}{\sffamily\sectionfont\epiccolor}
\DeclareTextFontCommand{\textbf}{\bffont\bfseries\sffamily}

%%======== Title and Section format  ========
\renewcommand{\title}[1]{%
  \newcommand{\thetitle}{#1}%
  \newcommand{\titlelist}{\resizebox{\linewidth}{!}{{\titlefont\rmfamily\bfseries #1}}}%
}
\RequirePackage{titlesec}
\titleformat*{\paragraph}{\itshape}
\titleformat*{\section}{\sectionfont\sffamily\bfseries\epiccolor}
\titleformat*{\subsection}{\subsectionfont\sffamily\bfseries\epiccolor}
\titleformat*{\subsubsection}{\normalsize\sffamily\bfseries\epiccolor}
\newcommand{\beginabstract}{\abstractfont{\sffamily\bfseries \epiccolor{Abstract}\par}}
\newcommand{\beginappendix}{\appendix{\titlefont\sffamily \epiccolor{Appendix}\par}}



%%======== Bibliography style switch ========
\newif\ifnumberscite     % 定义开关
\numberscitefalse         % 默认 author-year，可改为 \numberscitetrue 切换数字引用

\ifnumberscite
    % 数字引用
    \RequirePackage[numbers,sort&compress]{natbib}
\else
    % author-year 引用
    \RequirePackage[round,authoryear]{natbib}
\fi

\def\bibfont{\small}
\addto{\captionsenglish}{\renewcommand{\refname}{References}}
\newcommand{\citeas}[1]{\Needspace*{8\baselineskip}\noindent\bibentry{#1}}


%%======== References ========
\RequirePackage{xurl}
\RequirePackage{hyperref}
\hypersetup{
  colorlinks,
  linkcolor=epiccolor,
  citecolor=epiccolor,
  urlcolor=epiccolor
}
\RequirePackage[noabbrev,nameinlink]{cleveref}




%%======== Caption format ========
\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\sffamily\textbf{#1 #2}} #3}
\captionsetup{singlelinecheck=true,format=custom,labelsep=custom,font=small}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}

%%======== Authors, affiliations, contributions, thanks ========
\renewcommand\addtolist[5][]{
  \begingroup
    \if\relax#3\relax\def\sep{}\else\def\sep{#5}\fi
    \let\protect\@unexpandable@protect 
    \xdef#3{\expandafter{#3}\sep #4[#1]{#2}}%
  \endgroup
}

\newcommand\authorlist{}
% \newcommand\authorformat[2][]{\authorfont {\sffamily #2$^{#1}$}}
\newcommand\authorformat[2][]{%
  \authorfont {\sffamily #2%
    \if\relax\detokenize{#1}\relax\else$^{#1}$\fi}%
}
% \renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{, }}
\renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{\ }}

\newcommand\authorthankslist{}
\newcommand\authorthanks[2][]{\addtolist[#1]{#2}{\authorthankslist}{\authorformat}{, }}

\newcommand\affiliationlist{}
\newcommand\affiliationformat[2][]{{\affiliationfont {\sffamily\selectfont $^{#1}$#2}}}
\newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{, }}

\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\contributionfont $^{#1}$#2}}
\newcommand\contribution[2][]{\addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}

\newcommand\checkdatalist{}
\newcommand\checkdataformat[2][]{{\small {\checkdatafont\sffamily \bfseries #1:} #2}}
\newcommand\checkdata[2][]{\addtolist[#1]{#2}{\checkdatalist}{\checkdataformat}{\par}}
\renewcommand{\abstract}[1]{\def\abstractlist{{\abstractinfont #1}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}
\newcommand\correspondence[1]{\checkdata[Correspondence]{#1}}

%%======== Header and Footer Content ========
\fancypagestyle{firststyle}{
  \fancyhf{}
  \fancyhead[R]{\includegraphics[height=12.3mm]{assets/bytedance.jpg}}
  \fancyhead[L]{\includegraphics[height=12.3mm]{assets/sjtu_log.png}}
}

% 新增：后续页面页眉样式，显示标题
\fancypagestyle{titlestyle}{
  \fancyhf{}
  \fancyhead[L]{\small\sffamily\color{epiccolor}\leftmark}
  \fancyhead[R]{\small\sffamily\color{epiccolor}\thetitle}
  \fancyfoot[C]{\small\sffamily\thepage}
  \renewcommand{\headrulewidth}{0.5pt}
  \renewcommand{\headrule}{
  \vskip -2mm
  \hbox to\headwidth{\color{epiccolor}\leaders\hrule height 0.5pt\hfill}}
}


\newcommand{\@toptitlebar}{
 \vspace*{0mm}
  \epiccolor{\hrule height 0.0pt }
  \vskip 3mm
}
\newcommand{\@bottomtitlebar}{
  \vskip 4mm
  \epiccolor{\hrule height 0.0pt}
}

%%======== 标题/摘要框模块化 ========
\newcommand{\setTitleBoxStyle}[1]{\tcbset{#1}}


\newcommand{\printAbstractBox}[1]{%
\begin{tcolorbox}[top=3mm,bottom=3mm]
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0cm}
    {\centering
      \beginabstract
      \vskip 1mm
    }
    #1\par
    {
      \setlength{\parskip}{0cm}
      \ifdefempty{\checkdatalist}{}{\vskip 1mm\checkdatalist\par}
    }
  \end{tcolorbox}
}

%%======== Titlebox ========
\newcommand{\mymaketitle}{%
  \setTitleBoxStyle{
    enhanced,
    left=8mm,
    right=8mm,
    top=6mm,
    bottom=6mm,
    colback=epiccolor2,
    colframe=epicbg,
    boxrule=0.5pt,
    before skip=0pt,
    grow to left by=1.5pt,
    grow to right by=1.5pt,
    arc=2.5mm
  }
  {
    \setlength{\parskip}{0mm}
    \centering
    \nohyphens
    \@toptitlebar
    \titlelist\par
    \@bottomtitlebar
    \vskip 2mm
    \authorlist
    \vskip 1mm
    \ifdefempty{\authorthankslist}{}{%
      \authorthankslist\par
    }
    \vskip 3mm
    \affiliationlist\par
    \vskip 3mm
    \contributionlist\par
  }
  \vskip 6mm   
  \printAbstractBox{\abstractlist}
  \FloatBarrier
  \thispagestyle{firststyle}
  \pagestyle{titlestyle}  % 从下一页开始使用标题页眉
}

\if@twocolumn%
\renewcommand{\maketitle}{
\twocolumn[%
 \vskip 3mm
  \mymaketitle
  \vskip 8mm
]
}%
\else%
\renewcommand{\maketitle}{
  \mymaketitle
  \vskip 8mm
}%
\fi
