# Paper Writing Prompt

Write a complete research paper in PROPER LaTeX FORMAT based on the following project materials:

**Title:** {title}
**Technical Design:** {design_doc}
**Implementation:** {impl_plan}
**Code:** {code_content}
**Analysis Results:** {analysis_results}

## LaTeX Format Requirements
IMPORTANT: Generate a COMPLETE LaTeX document that includes:
- \documentclass{article}
- \usepackage commands for necessary packages
- \title{} and \author{} commands
- \begin{document} and \end{document}
- \maketitle command
- \begin{abstract} and \end{abstract}
- Proper LaTeX section commands (\section{}, \subsection{})

## Paper Structure Required
1. Abstract
2. Introduction  
3. Methods
4. Results
5. Discussion
6. Conclusion
7. References (use \bibliography or manual \bibitem entries)

## Critical Instructions
- Use proper LaTeX syntax throughout - NO MARKDOWN formatting like **bold** or # headers
- Use \textbf{} for bold, \textit{} for italics, \section{} for sections
- Include proper citations and ensure all claims are supported by the provided materials
- Follow standard academic paper format and style
- Make sure the document will compile with pdflatex

## Variables
- {title}: Project title
- {design_doc}: Technical design document (truncated)
- {impl_plan}: Implementation plan (truncated)
- {code_content}: Generated code (truncated)
- {analysis_results}: Analysis results