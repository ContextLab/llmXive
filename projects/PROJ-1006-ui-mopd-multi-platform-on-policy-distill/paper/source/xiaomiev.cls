%%======== Pckage options and base class ========
%\newboolean{logo}

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{xiaomiev}
\LoadClassWithOptions{article}

\RequirePackage{iftex}
\ifxetex
  % XeLaTeX: use brand fonts via fontspec
\else
  \pdfoutput=1
  \RequirePackage[T1]{fontenc}
  \RequirePackage{lmodern}
  \RequirePackage[scale=0.95]{montserrat}
  \renewcommand{\sfdefault}{Montserrat-TLF}
\fi

% Layout
\RequirePackage[top=2.75cm, bottom=2.5cm, left=2.5cm, right=2.5cm, columnsep=0.65cm]{geometry}
\RequirePackage{microtype}
\RequirePackage{placeins}
\RequirePackage{hyphenat}
\RequirePackage{setspace}
\RequirePackage{parskip}
\RequirePackage[english]{babel}
\RequirePackage{lipsum}
\RequirePackage{etoolbox}
\RequirePackage{fancyhdr}  % custom headers/footers
\RequirePackage{ulem}  % 引用下划线
% [xelatex] \DisableLigatures is a pdfTeX-only microtype feature; omitted.
\RequirePackage{graphicx}
\RequirePackage{subcaption}


\RequirePackage{booktabs}
\RequirePackage{nicematrix}
\RequirePackage{multirow}
\RequirePackage{bm}
\newcommand{\nm}[1]{#1}
\RequirePackage[most]{tcolorbox}
\RequirePackage{xcolor}
\definecolor{xiaomievbg}{HTML}{FF7E00}
\definecolor{xiaomievblue}{HTML}{FF7E00}
\definecolor{xiaomievblue}{HTML}{FF7E00}
\newcommand{\xiaomievblue}[1]{{\bfseries\color[HTML]{FF7E00} #1}} 

% References %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
\hypersetup{
  colorlinks,
  linkcolor=xiaomievblue,
  citecolor=xiaomievblue,
  urlcolor=xiaomievblue
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
\titleformat*{\section}{\sectionfont\sffamily\bfseries\xiaomievblue}
\titleformat*{\subsection}{\subsectionfont\sffamily\bfseries\xiaomievblue}


%一级二级三级标题用12 11 10
\titleformat*{\subsubsection}{\normalsize\sffamily\bfseries\xiaomievblue}


\newcommand{\bffont}
{\fontsize{8.8}{10}\selectfont} 

\DeclareTextFontCommand{\textbf}{\bffont\bfseries\sffamily}



\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\sffamily\textbf{#1 #2}} #3}
\captionsetup{singlelinecheck=true,format=custom,labelsep=custom,font=small}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}


\ifxetex
  \RequirePackage{fontspec}
  \newfontfamily\xiaomievsf{xiaomiev-Bold.ttf}[
    Path = xiaomiev/ ,
    UprightFont = xiaomiev-Bold.ttf ,
    BoldFont    = xiaomiev-Bold.ttf ]
  \setsansfont{xiaomiev-Bold.ttf}[
    Path = xiaomiev/ ,
    UprightFont = xiaomiev-Bold.ttf ,
    BoldFont    = xiaomiev-Bold.ttf ]
  \newfontfamily\xiaomievmediumfont{xiaomiev-Medium.ttf}[Path = xiaomiev/]
  \DeclareRobustCommand\xiaomievmediumselect{\xiaomievmediumfont}
  \renewcommand{\rmdefault}{cmr}
\else
  \DeclareRobustCommand\xiaomievmediumselect{\sffamily\mdseries}
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
{\fontsize{12}{14}\selectfont} 

\newcommand\authorlist{}
\newcommand\authorformat[2][]{\authorfont {\sffamily\bfseries #2$^{#1}$}}
\renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{, }}

%给affiliation换成medium字体

\newcommand{\affiliationfont}
{\fontsize{10}{12}\selectfont}

\newcommand\affiliationlist{}
\newcommand\affiliationformat[2][]{{\affiliationfont {\xiaomievmediumselect $^{#1}$#2}}}
\newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{, }}

\newcommand{\contributionfont}
{\fontsize{10}{12}\selectfont}

\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\contributionfont $^{#1}$#2}}
\newcommand\contribution[2][]{\addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}

\newcommand{\resourcelinkfont}
{\fontsize{8}{10}\selectfont}

\newcommand\resourcelinkslist{}
\newcommand\resourcelinks[1]{\def\resourcelinkslist{{\resourcelinkfont\sffamily #1}}}

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


\newcommand{\titlefont}
{\fontsize{17}{20}\selectfont} 

\renewcommand{\title}[1]{\newcommand{\titlelist}{\titlefont{\sffamily\bfseries #1}}}


\newcommand{\abstractfont}
{\fontsize{12}{12}\selectfont} 

\newcommand{\beginabstract}{\abstractfont{\sffamily\bfseries \xiaomievblue{Abstract}\par}}

\newcommand{\beginappendix}{\appendix{\titlefont\sffamily \xiaomievblue{Appendix}\par}}


\usepackage[subfigure]{tocloft}
\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}} % 目录后一行连续的点
\renewcommand{\cftsecfont}{\sffamily}
%\renewcommand{\cftsubsecfont}{\sffamily\large}
\renewcommand{\cftsecpagefont}{\sffamily}{\color{xiaomievblue}}
\renewcommand{\cfttoctitlefont}
{\sffamily\sectionfont\xiaomievblue}


%%======== Header and Footer Content ========
\fancypagestyle{firststyle}{
    \fancyhead[R]{
        % Other content for the left side of the header, if any
    }
    \fancyhead[L]{
        \vskip 4mm
    % \includegraphics[height=10mm]{images/xiaomi_logo.pdf}
    }
    \fancyhead[R]{
    }
     
}

%去除页眉页脚横线
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}



% rules for title box at top of first page
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%此处为标题两侧线段，0.5pt 长160mm
\newcommand{\@toptitlebar}{
  \xiaomievblue{\hrule height 0.5pt }
  \vskip 7mm
  %\vskip -\parskip%
}
\newcommand{\@bottomtitlebar}{
  \vskip 6mm
  %\vskip -\parskip
  \xiaomievblue{\hrule height 0.5pt}
  %\vskip 0.09in%
}


% Titlebox %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\definecolor{lightorange}{RGB}{255,250,245}


\newcommand{\mymaketitle}{%
  \noindent\includegraphics[height=8mm]{logo/xiaomi_logo.pdf}\hfill
  \includegraphics[height=10mm]{logo/Tsinghua.png}\hspace{2mm}%
  \includegraphics[height=10mm]{logo/zju-logo-small.png}\hspace{2mm}%
  \includegraphics[height=10mm]{logo/hitsz.png}\vspace{2mm}\par
  %\tcbset{enhanced,frame hidden}
  \tcbset{enhanced}
  \tcbset{left=8mm}
  \tcbset{right=8mm}
  \tcbset{top=4mm}
  \tcbset{bottom=4mm}
  \tcbset{colback=lightorange}  
   % 框线颜色
  \tcbset{colframe=xiaomievbg} 
  % 调整框线粗细
  \tcbset{boxrule=0.5pt} 
  \tcbset{before skip=0pt}
  \tcbset{grow to left by=1.5pt}
  \tcbset{grow to right by=1.5pt}
  \tcbset{arc=2.5mm}
      {
      \setlength{\parskip}{0mm}
      \centering
      \nohyphens
      %
      
      {
      \@toptitlebar
        
        \titlelist\par
         \@bottomtitlebar
      }
      \vskip 5mm
      \authorlist\par
      \vskip 0.5mm
      %
      \affiliationlist\par
      \vskip 0.5mm
      %
      \contributionlist\par
      \ifdefempty{\resourcelinkslist}{}{\vskip 1.5mm\resourcelinkslist\par}
    }
   \vskip 4mm   
   
  \begin{tcolorbox}
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0cm}

    %
    
    \begin{center}
        \beginabstract
        \vskip 2mm
    \end{center}
    
    \abstractlist\par
    %
    \vskip 0mm
    %
    {
      \setlength{\parskip}{0cm}
      \ifdefempty{\checkdatalist}{\vspace*{0cm}}{\checkdatalist\par}
    }
  \end{tcolorbox}
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
