%%======== Package options and base class ========
%\newboolean{logo}
\usepackage[table,dvipsnames]{xcolor}

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ant_tech_report}
\LoadClassWithOptions{article}
\pdfoutput=1

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
% \RequirePackage[normalem]{ulem} 
\DisableLigatures[f]{family=sf*} 
\RequirePackage{graphicx}
\RequirePackage{subcaption}
\RequirePackage{xspace}

\RequirePackage{booktabs}
\RequirePackage{nicematrix}
\RequirePackage{multirow}
\RequirePackage{bm}
\newcommand{\nm}[1]{#1}
\RequirePackage[most]{tcolorbox}
\RequirePackage{pifont}
\RequirePackage{enumitem}
\RequirePackage{amsthm}
\RequirePackage{amsmath}
\RequirePackage{amssymb}
\RequirePackage{mathtools}
\RequirePackage{tabularx}
\RequirePackage{array}
% \RequirePackage{xcolor}

%custom color
\definecolor{alibabaorange}{HTML}{FF6A00}
\colorlet{antblue}{alibabaorange}
\definecolor{lightred}{RGB}{255, 182, 193}   
\definecolor{lightgreen}{RGB}{144, 238, 144}  
\definecolor{lightblue}{RGB}{173, 216, 230} 
\definecolor{lightergray}{gray}{0.90}
\definecolor{metabg}{HTML}{FFF4EB} 
\definecolor{ourg}{rgb}{0.23,0.49,0.14}
\definecolor{ourb}{rgb}{0.13,0.37,0.60}
\definecolor{ourp}{rgb}{0.44,0.18,0.63}
\definecolor{ouro}{rgb}{0.87,0.69,0.23}
\definecolor{ouro2}{rgb}{1,0.753,0}
\definecolor{upcolor}{rgb}{0.21,0.49,0.74}
\definecolor{our-yellow}{rgb}{221,175,57}
\definecolor{our-blue}{rgb}{29,113,168}

\newcommand{\eg}{\emph{e.g.}}
\newcommand{\ie}{\emph{i.e.}}
\newcommand{\up}[1]{\textcolor{upcolor}{\textcolor{upcolor}{$\uparrow$}#1}}
\newcommand{\upsft}[1]{\textcolor{gray}{\textcolor{gray}{$\uparrow$}#1}}
\newcommand{\down}[1]{\textcolor{red}{\textcolor{red}{$\downarrow$}#1}}

\newcommand{\antblue}[1]{{\bfseries\color{antblue} #1}} 

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% THEOREMS
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% \theoremstyle{plain}
\newtheorem{theorem}{Theorem}[section]
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{corollary}[theorem]{Corollary}
% \theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}
\newtheorem{assumption}[theorem]{Assumption}
% \theoremstyle{remark}
\newtheorem{remark}[theorem]{Remark}


% References %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\RequirePackage{hyperref}
\RequirePackage[noabbrev,nameinlink]{cleveref}
\hypersetup{
  colorlinks,
  linkcolor=antblue,
  citecolor=antblue,
  urlcolor=antblue
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
\titleformat*{\section}{\sectionfont\sffamily\bfseries\antblue}
\titleformat*{\subsection}{\subsectionfont\sffamily\bfseries\antblue}
\titleformat*{\subsubsection}{\normalsize\sffamily\bfseries\antblue}

\newcommand{\bffont}
{\fontsize{8.8}{10}\selectfont} 
\DeclareTextFontCommand{\textbf}{\bffont\bfseries\sffamily}

\RequirePackage{caption}
\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\sffamily\textbf{#1 #2}} #3}
\captionsetup{singlelinecheck=true,format=custom,labelsep=custom,font=small}
\captionsetup[sub]{singlelinecheck=true,format=custom,labelsep=custom,font=small}


\RequirePackage[T1]{fontenc}
\DeclareFontFamily{T1}{optimistic}{}
\DeclareFontShape{T1}{optimistic}{m}{n}{<-> s * [1] fonts/optimistic}{}
\pdfmapline{+optimistic < fonts/Optimistic.ttf <T1-WGL4.enc}
\renewcommand{\sfdefault}{optimistic}

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
{\fontsize{11}{12}\selectfont} 

\newcommand\authorlist{}
\newcommand\authorformat[2][]{\authorfont {\sffamily #2$^{#1}$}}
\renewcommand\author[2][]{\addtolist[#1]{#2}{\authorlist}{\authorformat}{, }}

%%%%%%%%%%%%%%%%%fix affiliation bug%%%%%%%%%%%%%
\newcommand{\affiliationfont}
{\fontsize{10}{12}\selectfont}

\newcommand\affiliationlist{}
\newcommand\affiliationformat[2][]{{\affiliationfont {\fontfamily{optimistic}\selectfont $^{#1}$#2}}}
\newcommand\affiliation[2][]{\addtolist[#1]{#2}{\affiliationlist}{\affiliationformat}{, }}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

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


\newcommand{\titlefont}
{\fontsize{16.5}{20}\selectfont} 

\renewcommand{\title}[1]{\newcommand{\titlelist}{\titlefont{\sffamily #1}}}


\newcommand{\abstractfont}
{\fontsize{12}{12}\selectfont} 

\newcommand{\beginabstract}{\abstractfont{\sffamily\bfseries{Abstract}\par}}

\newcommand{\beginappendix}{\appendix{\titlefont\sffamily \antblue{Appendix}\par}}


\usepackage[subfigure]{tocloft}
\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}}
\renewcommand{\cftsecfont}{\sffamily}
%\renewcommand{\cftsubsecfont}{\sffamily\large}
\renewcommand{\cftsecpagefont}{\sffamily}{\color{antblue}}
\renewcommand{\cfttoctitlefont}
{\sffamily\sectionfont\antblue}


%%======== Header and Footer Content ========
\fancypagestyle{firststyle}{
    \fancyhead[R]{
    }
    \fancyhead[R]{
        \vskip 3mm
    \includegraphics[width=48mm,height=11.5mm]{logos/comps.pdf}  
    }
    \fancyhead[L]{
        \vskip 3mm
    \includegraphics[height=12mm]{logos/university_lamda.png}  
    }
}

\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}


% rules for title box at top of first page
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\newcommand{\@toptitlebar}{
  \hrule height 1pt 
  \vskip 6mm
  %\vskip -\parskip%
}
\newcommand{\@bottomtitlebar}{
  \vskip 6mm
  %\vskip -\parskip
  \hrule height 0.5pt
  %\vskip 0.09in%
}

\newtcolorbox{insightline}{
    blanker,
    breakable,
    left=4.5mm, right=4.5mm, top=1.5mm, bottom=1.5mm,
    borderline west={2pt}{0pt}{antblue},
    colback=gray!5, 
    fontupper=\itshape
}
% Titlebox %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\newcommand{\mymaketitle}{%
  %\tcbset{enhanced,frame hidden}
  \tcbset{enhanced}
  \tcbset{left=8mm}
  \tcbset{right=8mm}
  \tcbset{top=6mm}
  \tcbset{bottom=6mm}
  \tcbset{colback=white}  
  \tcbset{colframe=black} 
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
      enhanced,
      colback=metabg,       
      colframe=metabg,     
      boxrule=0pt,          
      frame hidden,        
      arc=2.5mm,           
      top=2mm,              
      bottom=2mm
  ]
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0cm}

    \begin{center}
        \beginabstract
        \vskip 2mm
    \end{center}
    
    \abstractlist\par
    \vskip 3mm
    {
      \setlength{\parskip}{0cm}
      \ifdefempty{\checkdatalist}{\vspace*{0.65cm}}{\checkdatalist\par}
    }
  \end{tcolorbox}
  
  \tcbset{reset}
  \FloatBarrier
  \thispagestyle{firststyle}

}

\newtcolorbox{insightbox}{
  enhanced,
  breakable,
  colback=metabg,
  colframe=black!70,
  boxrule=0.7pt,
  arc=2.2mm,
  left=8pt,right=8pt,top=6pt,bottom=6pt, 
  title=\textbf{Key Insights in Reward Design},
  colbacktitle=black!85,
  coltitle=white,
  fonttitle=\bfseries\ttfamily\footnotesize,
  attach boxed title to top left={xshift=5mm,yshift=-2mm},
  boxed title style={
    boxrule=0pt,
    arc=1.2mm,
    left=2.2mm,right=2.2mm,top=1mm,bottom=1mm
  }
}

\newtcolorbox{theorybox}[1][]{%
  enhanced, breakable,
  colback=metabg,   
  colframe=metabg,  
  boxrule=0pt,            
  arc=2mm,                
  left=8pt,right=8pt,top=6pt,bottom=6pt, 
  before skip=8pt, after skip=8pt,
  #1
}

\newtcolorbox{systempromptbox}{
  enhanced,
  breakable,
  colback=gray!8,
  colframe=black!70,
  boxrule=0.7pt,
  arc=2.2mm,
  left=5mm,right=5mm,top=4mm,bottom=4mm,
  title=\texttt{SYSTEM\_PROMPT},
  colbacktitle=black!85,
  coltitle=white,
  fonttitle=\bfseries\ttfamily\footnotesize,
  attach boxed title to top left={xshift=5mm,yshift=-2mm},
  boxed title style={
    boxrule=0pt,
    arc=1.2mm,
    left=2.2mm,right=2.2mm,top=1mm,bottom=1mm
  }
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
