# Personal page

Static site for GitHub Pages. Files to commit to the `<username>.github.io` repository:

- `index.html` — generated, do not edit by hand
- `style.css`
- `cv.pdf` — copy of the compiled CV
- `make_site.py`, `biblio_cv.bib` — source; optional in the repository

To regenerate after editing `biblio_cv.bib` or the text in `make_site.py`:

    pip install pylatexenc
    python3 make_site.py biblio_cv.bib > index.html

Grouping, short venue names and the two patents are set at the top of `make_site.py`.
