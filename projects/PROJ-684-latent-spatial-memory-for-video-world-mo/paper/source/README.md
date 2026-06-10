# Microsoft Technical Report Overleaf Template

Author: [Weijie Wang](http://lhmd.top)

Copy `microsoft-tech-report-template` as a new project on Overleaf and set
`main.tex` as the main file.

## Common edits

- Replace the report metadata near the top of `main.tex`.
- Leave optional metadata fields empty (`{}`) to hide them. The title box can
  show `Project Page`, `Correspondence`, `Conference`, `Code`, `Date`, `ORCID`,
  and `Keywords`.
- Adjust `\reportlogoheight` in `main.tex` if the title-page logo row needs a
  different shared height.
- Put cropped logo files in `figures/logos/` and update `\techreportlogos{...}`.
  The included examples use one shared height so the row stays aligned.
- Replace the teaser placeholder box in `main.tex` with `\includegraphics`.
- Edit the section files under `sections/`. The default body order is
  Introduction, Related Works, Method, Experiments, and Conclusion.
- Add references to `reference.bib`.

The title-page logo row accepts multiple logos:

```tex
\techreportlogos{%
  \techreportlogo{figures/logos/zju-logo-cropped.png}
  \techreportlogo{figures/logos/monash-university-logo-cropped.png}
}
```

Use PDF logos when possible for clean rendering in Overleaf.
