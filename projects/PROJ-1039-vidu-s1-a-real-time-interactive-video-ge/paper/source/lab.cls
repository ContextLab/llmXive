\PassOptionsToPackage{table}{xcolor}
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{lab}
\LoadClassWithOptions{article}
\pdfoutput=1

% Layout 
\RequirePackage[top=2.75cm, bottom=2.5cm, left=2.5cm, right=2.5cm, columnsep=0.65cm]{geometry}
\RequirePackage{microtype}
\RequirePackage{placeins}
\RequirePackage{hyphenat}
\RequirePackage{setspace}
\RequirePackage{parskip}
\RequirePackage[latin, english]{babel}
\RequirePackage{lipsum}
\RequirePackage{etoolbox}
\RequirePackage{fancyhdr}  % custom headers/footers
\RequirePackage{ulem}  %
\DisableLigatures[f]{family=sf*} 
\RequirePackage{graphicx}
\RequirePackage{subcaption}


\RequirePackage{booktabs}
\RequirePackage{nicematrix}
\RequirePackage{multirow}
\RequirePackage{bm}
\newcommand{\nm}[1]{#1}
% \RequirePackage[table]{xcolor} 
\RequirePackage[most]{tcolorbox}
%\RequirePackage{xcolor}
\definecolor{labbg}{HTML}{296d97}
\definecolor{labblue}{HTML}{296d97}
\newcommand{\labblue}[1]{{\bfseries\color[HTML]{296d97} #1}} 


\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
\hypersetup{
  colorlinks,
  linkcolor=labblue,
  citecolor=labblue,
  urlcolor=labblue
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
\titleformat*{\paragraph}{\bfseries\itshape}
\titleformat*{\section}{\sectionfont\selectfont\bfseries\labblue}
\titleformat*{\subsection}{\subsectionfont\selectfont\bfseries\labblue}


%一级二级三级标题用12 11 10
\titleformat*{\subsubsection}{\normalsize\selectfont\bfseries\labblue}


\newcommand{\bffont}
{\fontsize{8.8}{10}\selectfont} 

\DeclareTextFontCommand{\textbf}{\bffont\bfseries\selectfont}



\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\selectfont\textbf{#1 #2}} #3}
\captionsetup{singlelinecheck=true,format=custom,labelsep=custom,font=small}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}


\newcounter{authorcount}
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

\newcommand\authorformat[2][]{\authorfont {\selectfont\bfseries #2$^{#1}$}}
\renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{, }}



\newcommand{\affiliationfont}
{\fontsize{10}{12}\selectfont}

\newcommand\affiliationlist{}
\newcommand\affiliationformat[2][]{{\affiliationfont {\fontfamily{charter}\selectfont $^{#1}$#2}}}
\newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{, }}

\newcommand{\contributionfont}
{\fontsize{10}{12}\selectfont}

\newcommand\contributionlist{}
\newcommand\contributionformat[2][]{{\contributionfont $^{#1}$#2}}
\newcommand\contribution[2][]{\addtolist[#1]{#2}{\contributionlist}{\contributionformat}{, }}

\newcommand{\checkdatafont}
{\fontsize{7.92}{10}\selectfont}

\newcommand\checkdatalist{}
\newcommand\checkdataformat[2][]{{\small {\checkdatafont\selectfont \bfseries #1:} #2}}
\newcommand\checkdata[2][]{\addtolist[#1]{#2}{\checkdatalist}{\checkdataformat}{\par}}


\newcommand{\abstractinfont}
{\fontsize{10}{12}\selectfont} 

\renewcommand{\abstract}[1]{\def\abstractlist{{\abstractinfont #1}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}

\renewcommand\date[1]{\checkdata[Date]{#1}}
\newcommand\correspondence[1]{\checkdata[Correspondence]{#1}}


\newcommand{\titlefont}
{\fontsize{18}{20}\selectfont} 

% \renewcommand{\title}[1]{\newcommand{\titlelist}{\titlefont{\sffamily #1}}}
\renewcommand{\title}[1]{\newcommand{\titlelist}{\titlefont{\selectfont\bfseries #1}}}

\newcommand{\abstractfont}
{\fontsize{12}{12}\selectfont} 

\newcommand{\beginabstract}{\abstractfont{\selectfont\bfseries \labblue{Abstract}\par}}

\newcommand{\beginappendix}{\appendix{\titlefont\selectfont \labblue{Appendix}\par}}


\usepackage[subfigure]{tocloft}
\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}} % 
\renewcommand{\cftsecfont}{\selectfont}
%\renewcommand{\cftsubsecfont}{\sffamily\large}
\renewcommand{\cftsecpagefont}{\selectfont}{\color{labblue}}
\renewcommand{\cfttoctitlefont}
{\selectfont\sectionfont\labblue}


%%======== Header and Footer Content ========
\fancypagestyle{firststyle}{
    \fancyhead[R]{
        \vskip 3mm
    % \includegraphics[height=12mm]{lab_logo.png}  
    }
    \fancyhead[L]{
        \vskip 3mm
    \includegraphics[height=12mm]{shengshu_logo.png}  
    }

}

\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}



% rules for title box at top of first page
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\newcommand{\@toptitlebar}{
  \labblue{\hrule height 2.5pt }
  \vskip 6mm
  %\vskip -\parskip%
}
\newcommand{\@bottomtitlebar}{
  \vskip 5mm
  %\vskip -\parskip
  \labblue{\hrule height 1pt}
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
  \tcbset{colframe=labbg} 
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
      \vskip 6mm
      \authorlist
      \vskip 3mm
      %
      \affiliationlist\par
      \vskip 3mm
      %
      \contributionlist\par
    }
   \vskip 6mm   
   
  % abstract color
  \begin{tcolorbox}[
    colback=labbg!7,  
    colframe=white,  
    boxrule=0pt,     
    arc=2.5mm,       
    left=6mm,       
    right=6mm,      
    top=2mm,       
    bottom=-3mm       
  ]
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0cm}

    %
    
    \begin{center}
        \beginabstract
        \vskip 1mm
    \end{center}
    
    \abstractlist\par
    %
    \vskip 3mm
    %
    {
      \setlength{\parskip}{0cm}
      \ifdefempty{\checkdatalist}{\vspace*{0.21cm}}{\checkdatalist\par}
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
