%%======== Pckage options and base class ========
%\newboolean{logo}

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{gensi}
\LoadClassWithOptions{article}
\ifdefined\pdftexversion
  \pdfoutput=1
\fi

% Layout 
% \RequirePackage[top=2.75cm, bottom=2.5cm, left=2.5cm, right=2.5cm, columnsep=0.65cm]{geometry}
% 顶部间距调整为 1 cm，以免顶部太空
\RequirePackage[top=1cm, bottom=4.5cm, left=2.5cm, right=2.5cm, columnsep=0.65cm]{geometry}
\RequirePackage{microtype}
\RequirePackage{placeins}
\RequirePackage{hyphenat}
\RequirePackage{setspace}
\RequirePackage{parskip}
\RequirePackage[latin, english]{babel}
\RequirePackage{lipsum}
\RequirePackage{etoolbox}
\RequirePackage{fancyhdr}  % custom headers/footers
\RequirePackage{ulem}  % 引用下划线
\ifdefined\pdftexversion
  \ifnum\pdftexversion>129
    \DisableLigatures[f]{family=sf*}
  \fi
\fi
\RequirePackage{graphicx}
\RequirePackage{subcaption}


\RequirePackage{booktabs}
\RequirePackage{nicematrix}
\RequirePackage{multirow}
\RequirePackage{bm}
\newcommand{\nm}[1]{#1}
\RequirePackage[most]{tcolorbox}
\RequirePackage{xcolor}

% AIR 蓝
% \definecolor{gensibg}{HTML}{194EA1} % #194EA1
% \definecolor{gensicolor}{HTML}{194EA1}
% \newcommand{\gensicolor}[1]{{\bfseries\color[HTML]{194EA1} #1}} 

% 清华紫
% \definecolor{gensibg}{RGB}{102,8,116} %
% \definecolor{gensicolor}{RGB}{102,8,116}
% \newcommand{\gensicolor}[1]{{\bfseries\color[RGB]{102,8,116} #1}} 

% gensi 蓝
% \definecolor{gensibg}{HTML}{2E5AA8} % #2E5AA8
% \definecolor{gensicolor}{HTML}{2E5AA8}
% \newcommand{\gensicolor}[1]{{\bfseries\color[HTML]{2E5AA8} #1}} 

% GenSI 蓝，感觉有点浅
% \definecolor{gensibg}{HTML}{9EE8FF} % #9EE8FF
% \definecolor{gensicolor}{HTML}{9EE8FF}
% \newcommand{\gensicolor}[1]{{\bfseries\color[HTML]{9EE8FF} #1}} 

% gensi 黑
\definecolor{gensibg}{HTML}{000000} % #000000
\definecolor{gensicolor}{HTML}{000000}
\newcommand{\gensicolor}[1]{{\bfseries\color[HTML]{000000} #1}} 

% gensi 灰
% \definecolor{gensibg}{HTML}{F0F0F0} % #F0F0F0
% \definecolor{gensicolor}{HTML}{F0F0F0}
% \newcommand{\gensicolor}[1]{{\bfseries\color[HTML]{F0F0F0} #1}} 



% References %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
\hypersetup{
  colorlinks,
  linkcolor=gensicolor,
  citecolor=gensicolor,
  urlcolor=gensicolor
}



\RequirePackage[numbers, sort&compress]{natbib}
%\RequirePackage[round,authoryear]{natbib}
\def\bibfont{\small}

%%========  Bibliography using bibtex ========
\addto{\captionsenglish}{\renewcommand{\refname}{References}}
\newcommand{\citeas}[1]{\Needspace*{8\baselineskip}\noindent\bibentry{#1}}



% Section and caption format 
\newcommand{\sectionfont}
{\fontsize{12}{10}\selectfont} 

\newcommand{\subsectionfont}
{\fontsize{11}{10}\selectfont} 

\RequirePackage{titlesec}
\titleformat*{\paragraph}{\itshape}
\titleformat*{\section}{\sectionfont\sffamily\bfseries\gensicolor}
\titleformat*{\subsection}{\subsectionfont\sffamily\bfseries\gensicolor}


%一级二级三级标题用12 11 10
\titleformat*{\subsubsection}{\normalsize\sffamily\bfseries\gensicolor}


\newcommand{\bffont}
{\fontsize{8.8}{10}\selectfont} 

\DeclareTextFontCommand{\textbf}{\bffont\bfseries\sffamily}



\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\sffamily\textbf{#1 #2}} #3}
\captionsetup{singlelinecheck=true,format=custom,labelsep=custom,font=small}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}


\ifdefined\pdftexversion
  \RequirePackage[T1]{fontenc}
  \DeclareFontFamily{T1}{sora}{}
  \DeclareFontShape{T1}{sora}{m}{n}{<-> s * [1] sora}{}
  \pdfmapline{+sora < Sora-Bold.ttf <T1-WGL4.enc}
  \DeclareFontFamily{T1}{soramedium}{}
  \DeclareFontShape{T1}{soramedium}{m}{n}{<-> s*[1] soramedium}{}
  \DeclareFontShape{T1}{soramedium}{b}{n}{<-> s*[1] sora}{}
  \DeclareFontShape{T1}{soramedium}{bx}{n}{<-> s*[1] sora}{}
  \pdfmapline{+soramedium < Sora-Medium.ttf <T1-WGL4.enc}
  \renewcommand{\sfdefault}{soramedium}%
  \renewcommand{\rmdefault}{cmr}
  \newcommand{\gensimediumfont}{\fontfamily{soramedium}\selectfont}
\else
  \RequirePackage{fontspec}
  \setsansfont[
    UprightFont=Sora-Medium.ttf,
    BoldFont=Sora-Bold.ttf
  ]{Sora}
  \newfontfamily{\gensimediumfont}[
    UprightFont=Sora-Medium.ttf,
    BoldFont=Sora-Bold.ttf
  ]{Sora}
\fi


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Authors, affiliations, infos %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\renewcommand\addtolist[5][]{
  \begingroup
    \if\relax#3\relax\def\sep{}\else\def\sep{#5}\fi
    \let\protect\@unexpandable@protect 
    \xdef#3{\expandafter{#3}\sep #4[#1]{#2}}%
  \endgroup
}

\newcommand{\authorfont}
{\fontsize{9}{14}\selectfont} 

\newcommand\authorlist{}
\newcommand\authorformat[2][]{\authorfont {\sffamily #2$^{#1}$}}
\renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{, }}

%给affiliation换成medium字体

\newcommand{\affiliationfont}
{\fontsize{9}{12}\selectfont}

\newcommand\affiliationlist{}
\newcommand\affiliationformat[2][]{{\affiliationfont {\gensimediumfont $^{#1}$#2}}}
\newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{\\}}

\newcommand{\contributionfont}
{\fontsize{10}{12}\selectfont}

\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\contributionfont $^{#1}$#2}}
\newcommand\contribution[2][]{\addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}

\newcommand{\checkdatafont}
{\fontsize{7.92}{10}\selectfont}

\newcommand\checkdatalist{}
\newcommand\checkdataformat[2][]{{\small {\checkdatafont\sffamily \bfseries #1:} #2}}
\newcommand\checkdata[2][]{\addtolist[#1]{#2}{\checkdatalist}{\checkdataformat}{\par}}


\newcommand{\abstractinfont}
{\fontsize{10}{12}\selectfont} 

\renewcommand{\abstract}[1]{\def\abstractlist{{\abstractinfont #1}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}

\renewcommand\date[1]{\checkdata[Date]{#1}}
\newcommand\correspondence[1]{\checkdata[Correspondence]{#1}}
\newcommand\projectpage[1]{\checkdata[Project Page]{#1}}


\newcommand{\titlefont}
{\fontsize{13}{18}\selectfont}

\renewcommand{\title}[1]{\newcommand{\titlelist}{\titlefont{\sffamily #1}}}


\newcommand{\abstractfont}
{\fontsize{12}{12}\selectfont} 

\newcommand{\beginabstract}{\abstractfont{\sffamily\bfseries \gensicolor{Abstract}\par}}

\newcommand{\beginappendix}{\appendix{\titlefont\sffamily \gensicolor{Appendix}\par}}


\usepackage[subfigure]{tocloft}
\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}} % 目录后一行连续的点
\renewcommand{\cftsecfont}{\sffamily}
%\renewcommand{\cftsubsecfont}{\sffamily\large}
\renewcommand{\cftsecpagefont}{\sffamily}{\color{gensicolor}}
\renewcommand{\cfttoctitlefont}
{\sffamily\sectionfont\gensicolor}


%%======== Header and Footer Content ========
\fancypagestyle{firststyle}{
  \fancyhead[L]{
    \hspace*{8mm}
    \raisebox{-28mm}{ % 2mm
      \includegraphics[width=33mm]{gensi/gensi_logo_black.png}
    }
  }
}

%去除页眉页脚横线
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}



% rules for title box at top of first page
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%此处为标题两侧线段，0.5pt 长160mm
\newcommand{\@toptitlebar}{
  \gensicolor{\hrule height 1pt }
  \vskip 6mm
  % \vskip -\parskip%
}
\newcommand{\@bottomtitlebar}{
  \vskip 6mm
  %\vskip -\parskip
  % \gensicolor{\hrule height 0.5pt}
  %\vskip 0.09in%
}


% Titlebox %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


% 首页设置
\newcommand{\mymaketitle}{%
  % 设置 color box
  \tcbset{
    enhanced,
    left=8mm,
    right=8mm,
    % top=6mm, % 取消上边距，避免页眉太空
    bottom=6mm,
    colback=gensicolor!0, % 浅 gensicolor 色背景，!0 表示 0% 的 gensicolor 色，相当于无色
    colframe=white, % 框线颜色设为白色（与背景一致，相当于无框线）
    boxrule=0pt,    % 框线粗细为0pt，去除框线
    before skip=0pt,
    grow to left by=1.5pt,
    grow to right by=1.5pt,
    % arc=2.5mm,
  }

  \begin{tcolorbox} % box cover 标题、作者和摘要
    {
      \setlength{\parskip}{0mm}
      \centering
      \nohyphens
      %
      
      {
        % 显示标题上的横线
        \@toptitlebar

        \titlelist\par

        % 显示标题下的横线
        % \@bottomtitlebar
      }
      \vskip 6mm
      % 显示作者列表
      \authorlist
      \vskip 3mm
      
      % 显示单位列表
      \affiliationlist\par
      \vskip 3mm

      % 显示贡献列表, e.g. 实习、通讯作者
      \contributionlist\par
    }

  % 作者列表和摘要之间的间距
  \vskip 6mm   
  
  % 显示摘要
  % \begin{tcolorbox} % box 只 cover 摘要
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0cm}
    
    \begin{center}
        \beginabstract
        \vskip 3mm
    \end{center}
    
    \abstractlist\par
    
    \vskip 3mm
    
    {
      \setlength{\parskip}{0cm}
      \ifdefempty{\checkdatalist}{\vspace*{0.65cm}}{\checkdatalist\par}
    }
  \end{tcolorbox}

  % 重置 tcolorbox 的设置
  \tcbset{reset}
  \FloatBarrier

  %加入页眉页脚
  \thispagestyle{firststyle}
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
  %\setlength{\parskip}{4mm}
}%
\fi
