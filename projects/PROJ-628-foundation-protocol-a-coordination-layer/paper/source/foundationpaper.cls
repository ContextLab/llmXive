% Foundation Protocol paper style
% Paper-style class adapted from the provided arXiv reference template.
% The Foundation Agents logo is placed outside the title panel, at the first-page upper-left header area.

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{foundationpaper}[2026/05/17 Foundation Agents paper style]
\LoadClass{article}

% Layout: match the provided arXiv reference class as closely as possible.
\RequirePackage[left=2.5cm,right=2.5cm,top=2.25cm,bottom=2.5cm]{geometry}
\setlength\columnsep{0.65cm}

% Typography: keep the article default 10pt Computer Modern body font and reference spacing.
\RequirePackage[T1]{fontenc}
\RequirePackage[utf8]{inputenc}
\RequirePackage{microtype}
\RequirePackage{placeins}
\RequirePackage{hyphenat}
\RequirePackage{setspace}
\RequirePackage{parskip}

% Core packages used by the style.
\RequirePackage{graphicx}
\RequirePackage{xcolor}
\RequirePackage{etoolbox}
\RequirePackage{xparse}
\RequirePackage[most]{tcolorbox}
\RequirePackage{tikz}
\RequirePackage{titlesec}
\RequirePackage{caption}
\RequirePackage{hyperref}
\RequirePackage[nameinlink,noabbrev]{cleveref}

% Palette, aligned with the arXiv reference style while keeping Foundation Agents assets.
\definecolor{metacolor}{HTML}{0064E0}
\definecolor{metagray1}{HTML}{1C2B33}
\definecolor{metagray2}{HTML}{F1F4F7}

% References and links.
\hypersetup{
  colorlinks,
  linkcolor=metacolor,
  citecolor=metacolor,
  urlcolor=metacolor,
  filecolor=metacolor
}

% Section and caption format: same structure as the provided arXiv reference.
\titleformat*{\paragraph}{\itshape}
\titleformat*{\section}{\Large\sffamily\bfseries}
\titleformat*{\subsection}{\large\sffamily\bfseries}
\titleformat*{\subsubsection}{\normalsize\sffamily\bfseries}
\DeclareTextFontCommand{\textbf}{\bfseries\sffamily}

\DeclareCaptionLabelSeparator{custom}{}
\DeclareCaptionFormat{custom}{{\sffamily\textbf{#1 #2}} #3}
\captionsetup{singlelinecheck=false,format=custom,labelsep=custom,font=small}

% Front-matter storage.
\newcommand{\fp@title}{}
\newcommand{\fp@subtitle}{}
\newcommand{\fp@authorlist}{}
\newcommand{\fp@affiliationlist}{}
\newcommand{\fp@notelist}{}
\newcommand{\fp@metadatalist}{}
\newcommand{\fp@abstract}{}
\newif\iffp@firstauthor
\newif\iffp@firstaffiliation
\newif\iffp@firstnote
\newif\iffp@firstmetadata
\fp@firstauthortrue
\fp@firstaffiliationtrue
\fp@firstnotetrue
\fp@firstmetadatatrue

\renewcommand{\title}[1]{\gdef\fp@title{#1}}
\newcommand{\subtitle}[1]{\gdef\fp@subtitle{#1}}
\renewcommand{\abstract}[1]{\gdef\fp@abstract{{\color{metagray1}#1}}}

\newcommand{\fp@markers}[1]{\ifstrempty{#1}{}{$^{#1}$}}
% Names are intentionally not bold, regardless of author role.
\newcommand{\fp@authorformat}[2]{{\sffamily #2\fp@markers{#1}}}
\renewcommand{\author}[2][]{%
  \iffp@firstauthor
    \gdef\fp@authorlist{\fp@authorformat{#1}{#2}}%
    \global\fp@firstauthorfalse
  \else
    \gappto\fp@authorlist{, \fp@authorformat{#1}{#2}}%
  \fi
}

\newcommand{\fp@affiliationformat}[2][]{{\normalsize $^{#1}$#2}}
\newcommand{\affiliation}[2][]{%
  \iffp@firstaffiliation
    \gdef\fp@affiliationlist{\fp@affiliationformat[#1]{#2}}%
    \global\fp@firstaffiliationfalse
  \else
    \gappto\fp@affiliationlist{, \fp@affiliationformat[#1]{#2}}%
  \fi
}

\newcommand{\fp@noteformat}[2][]{{\small $^{#1}$#2}}
\newcommand{\contribution}[2][]{%
  \iffp@firstnote
    \gdef\fp@notelist{\fp@noteformat[#1]{#2}}%
    \global\fp@firstnotefalse
  \else
    \gappto\fp@notelist{\quad \fp@noteformat[#1]{#2}}%
  \fi
}

\newcommand{\fp@metadataformat}[2][]{{\small {\sffamily\bfseries #1:} #2}}
\newcommand{\metadata}[2][]{%
  \iffp@firstmetadata
    \gdef\fp@metadatalist{\fp@metadataformat[#1]{#2}}%
    \global\fp@firstmetadatafalse
  \else
    \gappto\fp@metadatalist{\par\fp@metadataformat[#1]{#2}}%
  \fi
}
\renewcommand{\date}[1]{\metadata[Date]{#1}}
\newcommand{\correspondence}[1]{\metadata[Correspondence]{#1}}

% Foundation Agents logo in the first-page upper-left header area, not inside the title box.
\newcommand{\fp@firstpagelogo}{%
  \begin{tikzpicture}[remember picture,overlay]
    \node[anchor=north west, xshift=2.5cm, yshift=-0.72cm]
      at (current page.north west)
      {\includegraphics[height=30pt]{figures/Foundation-Agent-Logo.pdf}};
  \end{tikzpicture}%
}

% Title panel: same box metrics as the arXiv reference, with subtitle support.
\renewcommand{\maketitle}{%
  \thispagestyle{plain}%
  \fp@firstpagelogo
  \tcbset{enhanced,frame hidden}
  \tcbset{left=0.5cm}
  \tcbset{right=0.5cm}
  \tcbset{top=0.7cm}
  \tcbset{bottom=0.6cm}
  \tcbset{arc=10pt}
  \tcbset{colback=metagray2}
  \tcbset{before skip=0pt}
  \tcbset{grow to left by=1.5pt}
  \tcbset{grow to right by=1.5pt}
  \begin{tcolorbox}
    \setlength{\parindent}{0cm}
    \setlength{\parskip}{0.5cm}
    {%
      \setlength{\parskip}{0cm}%
      \raggedright
      \nohyphens
      {\huge\sffamily\bfseries \fp@title\par}%
      \ifstrempty{\fp@subtitle}{}{%
        \vskip 0.18cm
        {\large\sffamily \fp@subtitle\par}%
      }%
      \vskip 0.4cm
      {\fp@authorlist\par}%
      \vskip 0.2cm
      {\fp@affiliationlist\par}%
      \ifstrempty{\fp@notelist}{}{\fp@notelist\par}%
    }%
    \fp@abstract\par
    \vskip 0.5cm
    {\setlength{\parskip}{0cm}\fp@metadatalist\par}%
  \end{tcolorbox}
  \tcbset{reset}
  \FloatBarrier
}

\endinput
