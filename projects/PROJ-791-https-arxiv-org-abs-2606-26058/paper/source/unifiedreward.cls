\RequirePackage{silence} % 
\WarningFilter{latex}{Command \showhyphens has changed} 

\PassOptionsToPackage{table}{xcolor}
\NeedsTeXFormat{LaTeX2e}
\LoadClassWithOptions{article}
\pdfoutput=1


\RequirePackage[top=1.75cm, bottom=2cm, left=2.5cm, right=2.5cm, columnsep=0.65cm]{geometry}

\RequirePackage{placeins}
\RequirePackage{hyphenat}
\RequirePackage{setspace}
\setstretch{1.04}

\RequirePackage[latin, english]{babel}
\RequirePackage{lipsum}
\RequirePackage{etoolbox}
\RequirePackage{fancyhdr}  
\RequirePackage{ulem}  

\RequirePackage{graphicx}
\RequirePackage{subcaption}


\RequirePackage{booktabs}
\RequirePackage{nicematrix}
\RequirePackage{multirow}
\RequirePackage{bm}
\newcommand{\nm}[1]{#1}

\RequirePackage[most]{tcolorbox}

\definecolor{onbg}{HTML}{111111}
% 这里是摘要颜色
\definecolor{onblue}{HTML}{6198ac}
% 这里是website超链接的颜色
\newcommand{\onblue}[1]{{\bfseries\color[HTML]{1a607e} #1}} 
% 这里是每个section title的颜色和title上大横线的颜色

\RequirePackage[numbers, sort]{natbib}

\def\bibfont{\small}


\addto{\captionsenglish}{\renewcommand{\refname}{References}}
\newcommand{\citeas}[1]{\Needspace*{8\baselineskip}\noindent\bibentry{#1}}




\newcommand{\sectionfont}
{\fontsize{12}{10}\selectfont} 

\newcommand{\subsectionfont}
{\fontsize{11}{10}\selectfont} 

\RequirePackage{titlesec}
\titleformat*{\paragraph}{\itshape}
\titleformat*{\section}{\sectionfont\bfseries\onblue}
\titleformat*{\subsection}{\subsectionfont\bfseries\onblue}


\titleformat*{\subsubsection}{\normalsize\bfseries\onblue}





\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}

\DeclareCaptionFormat{custom}{{{\bfseries #1 #2}} #3}
\captionsetup{singlelinecheck=true,format=custom,labelsep=custom,font=small}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}


\RequirePackage{amsthm, amsmath, amsfonts, amssymb}

% 原本，偏圆润可爱
% \RequirePackage[T1]{fontenc}           % 字体编码
% \RequirePackage{newpxtext}             % 正文使用 Palatino 风格的字体（TeX Gyre Pagella）
% \RequirePackage[bigdelims,vvarbb]{newpxmath}  % 数学字体（Palatino 风格）
% \RequirePackage[scaled=1.1]{zlmtt}     % 等宽字体（打字机字体），缩放 1.1 倍


% 锋利 times new roman，NIPS 风格
% \RequirePackage[T1]{fontenc}
% \RequirePackage{newtxtext}   % Times 正文
% \RequirePackage{newtxmath}   % Times 数学字体
% \RequirePackage[scaled=1.0]{zlmtt}  % 等宽字体，稍微缩小

% CVPR 风格，没那么锋利
\RequirePackage[T1]{fontenc}
% 正文和数学都用 Times
\RequirePackage{newtxtext}
\RequirePackage{newtxmath}
% 等宽字体用 Courier
\RequirePackage[scaled=0.92]{couriers}



\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
\hypersetup{
  colorlinks,
  linkcolor=onblue,
  citecolor=onblue,
  urlcolor=onblue
}


\newcounter{authorcount}

\newcounter{affiliationcount}

\newcommand\addtolistAff[5][]{%
  \begingroup
    \stepcounter{affiliationcount}
    \def\sep{}%
    % 从第2个开始才需要分隔符/换行
    \ifnum\value{affiliationcount}>1
      % 在第3,5,7,... 个 affiliation 前换行 => 每行2个
      \ifodd\value{affiliationcount}
        \ifnum\value{affiliationcount}=3
          \def\sep{\\[0.5mm]}%
        \else
          \def\sep{\\[-0.2mm]}%
        \fi
      \else
        \def\sep{#5}% 2,4,6,... 用逗号分隔
      \fi
    \fi
    \let\protect\@unexpandable@protect
    \xdef#3{\expandafter{#3}\sep #4[#1]{#2}}%
  \endgroup
}


\renewcommand\addtolist[5][]{
  \begingroup
    \stepcounter{authorcount}
    \if\relax#3\relax
      \def\sep{}
    \else
      \ifnum\value{authorcount}=5

        \def\sep{\\[0.5mm]}%
      \else
        \ifnum\value{authorcount}=10

          \def\sep{\\[-0.2mm]}%
        \else
          \def\sep{#5}%
        \fi
      \fi
    \fi
    \let\protect\@unexpandable@protect 
    \xdef#3{\expandafter{#3}\sep #4[#1]{#2}}%
  \endgroup
}

\newcommand{\authorfont}
{\fontsize{12}{14}\selectfont} 

\newcommand\authorlist{}


\newcommand\authorformat[2][]{\authorfont {\bfseries #2$^{#1}$}}
% \newcommand\authorformat[2][]{\authorfont {#2$^{#1}$}}

\renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{, }}





\newcommand{\affiliationfont}
{\fontsize{10}{12}\selectfont}

\newcommand\affiliationlist{}
% \newcommand\affiliationformat[2][]{{\affiliationfont {\fontfamily{bytesansmedium}\selectfont $^{#1}$#2}}}
\newcommand\affiliationformat[2][]{{\affiliationfont $^{#1}$#2}}
% \newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{, }}
\newcommand\affiliation[2][]{%
  \addtolistAff[#1]{#2}{\affiliationlist}{\affiliationformat}{\quad}%
}

\newcommand{\contributionfont}
{\fontsize{10}{12}\selectfont}

\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\contributionfont $^{#1}$#2}}
\newcommand\contribution[2][]{\addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}

\newcommand{\checkdatafont}
{\fontsize{7.92}{10}\selectfont}

\newcommand\checkdatalist{}
\newcommand\checkdataformat[2][]{{\small {\checkdatafont \bfseries #1:} #2}}
\newcommand\checkdata[2][]{\addtolist[#1]{#2}{\checkdatalist}{\checkdataformat}{\par}}


\newcommand{\abstractinfont}
{\fontsize{10}{12}\selectfont} 

\renewcommand{\abstract}[1]{\def\abstractlist{{\abstractinfont #1}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}

\renewcommand\date[1]{\checkdata[Date]{#1}}
\newcommand\correspondence[1]{\checkdata[Correspondence]{#1}}


\newcommand{\titlefont}
{\fontsize{18}{20}\selectfont} 

% \renewcommand{\title}[1]{\newcommand{\titlelist}{\titlefont{ #1}}}
\renewcommand{\title}[1]{\newcommand{\titlelist}{\titlefont{\bfseries #1}}}
% \renewcommand{\title}[1]{\newcommand{\titlelist}{\titlefont{#1}}}

\newcommand{\abstractfont}
{\fontsize{12}{12}\selectfont} 

\newcommand{\beginabstract}{\abstractfont{\bfseries \onblue{Abstract}\par}}

\newcommand{\beginappendix}{%
  \appendix
  \par\noindent{\titlefont \onblue{Appendix}\par}%
  \vspace{1em}%
}



\RequirePackage[titles, subfigure]{tocloft}
\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}} % 目录后一行连续的点
\renewcommand{\cftsecfont}{}

\renewcommand{\cftsecpagefont}{}{\color{onblue}}
\renewcommand{\cfttoctitlefont}
{\sectionfont\onblue}



\fancypagestyle{firststyle}{
    \fancyhf{}          
}


\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}




\newcommand{\@toptitlebar}{
  \onblue{\hrule height 2.5pt }
  \vskip 6mm
  %\vskip -\parskip%
}
\newcommand{\@bottomtitlebar}{
  \vskip 5mm
  %\vskip -\parskip
  \onblue{\hrule height 1pt}
  %\vskip 0.09in%
}

\newcommand{\mymaketitle}{%
  %\tcbset{enhanced,frame hidden}
  \tcbset{enhanced}
  \tcbset{left=8mm}
  \tcbset{right=8mm}
  \tcbset{top=6mm}
  \tcbset{bottom=6mm}
  \tcbset{colback=white}  

  \tcbset{colframe=onbg} 

  \tcbset{boxrule=0.5pt} 
  \tcbset{before skip=0pt}
  \tcbset{grow to left by=1.5pt}
  \tcbset{grow to right by=1.5pt}
  \tcbset{arc=2.5mm}
      {
      \setlength{\parskip}{0mm}
      \centering
      \nohyphens
      {
        {\raggedright
          \includegraphics[height=13mm]{assets/logo-c4g.png}\par
        }
        \vspace{3mm} 

        \@toptitlebar
    
        \titlelist\par
        \@bottomtitlebar
      }
      
      \vskip 6mm
      \authorlist
      \vskip 3mm
      
      \affiliationlist\par
      \vskip 3mm
      
      \contributionlist\par
    }
   \vskip 6mm   
   

  \begin{tcolorbox}[
    colback=onbg!7, 
    colframe=white,     
    boxrule=0pt,       
    arc=2.5mm,          
    left=6mm,           
    right=6mm,          
    top=4mm,            
    bottom=4mm          
  ]
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0cm}

    %
    
    \begin{center}
        \beginabstract
        \vskip 3mm
    \end{center}
    
    \abstractlist\par
    %
    \vskip 3mm
    %
    {
      \setlength{\parskip}{0cm}
      \ifdefempty{\checkdatalist}{\vspace*{0.65cm}}{\checkdatalist\par}
    }
  \end{tcolorbox}
  \tcbset{reset}
  \FloatBarrier


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

\AtEndOfClass{
    \RequirePackage[tracking=smallcaps]{microtype}
    \DisableLigatures[f]{family=sf*}
}
