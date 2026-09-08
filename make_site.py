#!/usr/bin/env python3
"""Build index.html from biblio_cv.bib.

Usage:  python3 make_site.py biblio_cv.bib > index.html

The grouping mirrors cv.typ: journals, international conferences, French
conferences, preprints, thesis. Patents are written by hand below, as in the CV.
Requires: pip install pylatexenc
"""
import re
import sys
from html import escape
from pylatexenc.latex2text import LatexNodes2Text

L2T = LatexNodes2Text()

# ---------------------------------------------------------------- grouping
GROUPS = [
    ("Journal articles", [
        "hainzl_edp2026", "edp_wallner2026",
        "caizergues_durand_noy_edp_ravelomanana2025",
        "dovgal_edp_ralaivaosaona_rasendrahasina_wagner2024",
        "dovgal_edp_ravelomanana2023",
        "collet_edp_gardy_gittenberger_ravelomanana2020",
        "edp2019", "edp_gardy_gittenberger_kuba2016",
        "edp_ravelomanana2015", "edp2015",
        "attrapadung_herranz_laguillaumie_libert_edp_rafols2012",
    ]),
    ("Conference papers", [
        "durand_edp_perarnau2026_conf", "edp_durand_lang2026_conf",
        "hainzl_edp2024_conf", "chen_keevash_kennedy_edp_vetta2024_conf",
        "caizergues_edp2023_conf", "lutz_edp_stein_scott2021_conf",
        "edp_dovgal2020_conf", "edp_lamali_wallner2019_conf",
        "bouillard_comte_edp_mathieu2018_conf",
        "collet_edp_gardy_gittenberger_ravelomanana2017_conf",
        "edp_ramos2016_conf", "edp2016_conf", "edp2015_conf",
        "edp_gardy_gittenberger_kuba2014_conf", "bostan_chyzak_edp2013_conf",
        "attrapadung_libert_edp2011_conf",
    ]),
    ("French national conferences", [
        "edp_lamali_wallner2019_algotel", "bouillard_comte_edp_mathieu2019_algotel",
    ]),
    ("Preprints", [
        "edp2024_arxiv", "gosgens_luchtrath_magnanini_noy_edp2024_arxiv",
    ]),
    ("Thesis", ["edp2014_thesis"]),
]

# Short venue names for the web (the bib keeps the full proceedings titles)
VENUE = {
    "durand_edp_perarnau2026_conf": "IJCAI 2026",
    "edp_durand_lang2026_conf": "IJCAI 2026",
    "hainzl_edp2024_conf": "AofA 2024",
    "chen_keevash_kennedy_edp_vetta2024_conf": "ICALP 2024",
    "caizergues_edp2023_conf": "EUROCOMB 2023",
    "lutz_edp_stein_scott2021_conf": "NeurIPS 2021",
    "edp_dovgal2020_conf": "FPSAC 2020, Séminaire Lotharingien de Combinatoire 84B",
    "edp_lamali_wallner2019_conf": "ANALCO 2019",
    "bouillard_comte_edp_mathieu2018_conf": "ITC 30, 2018",
    "collet_edp_gardy_gittenberger_ravelomanana2017_conf": "EUROCOMB 2017",
    "edp_ramos2016_conf": "ANALCO 2016",
    "edp2016_conf": "FPSAC 2016",
    "edp2015_conf": "FPSAC 2015",
    "edp_gardy_gittenberger_kuba2014_conf": "LATIN 2014",
    "bostan_chyzak_edp2013_conf": "ISSAC 2013",
    "attrapadung_libert_edp2011_conf": "PKC 2011",
    "edp_lamali_wallner2019_algotel": "ALGOTEL 2019",
    "bouillard_comte_edp_mathieu2019_algotel": "ALGOTEL 2019",
    "edp2014_thesis": "PhD thesis, Université Paris-Diderot, 2014",
    "dovgal_edp_ravelomanana2023": "Combinatorial Theory 3(2), article 7",
    "edp_wallner2026": "Combinatorial Theory, to appear",
}

PATENTS = [
    dict(title="Positioning approach",
         authors="Chung Shue Chen, Paolo Baracca, <b>Élie de Panafieu</b>, Diomidis Michalopoulos",
         venue="Nokia Technologies. GB 2631540 A, EP 4488708 A1, US 2025/0016725 A1; "
               "priority 7 July 2023, published January 2025. Under examination",
         links=[("EPO", "https://worldwide.espacenet.com/publicationDetails/biblio?CC=EP&NR=4488708A1&KC=A1&FT=D")]),
    dict(title="Clustering of a set of items",
         authors="<b>Élie de Panafieu</b>, Maria Laura Maag, Quentin Lutz",
         venue="Nokia Solutions and Networks. EP 3923191 A1; filed 11 June 2020, "
               "published 15 December 2021, subsequently withdrawn",
         links=[("EPO", "https://worldwide.espacenet.com/publicationDetails/biblio?CC=EP&NR=3923191A1&KC=A1&FT=D")]),
]

DOI_FALLBACK = {
    "hainzl_edp2026": "10.1016/j.ejc.2026.104386",
    "dovgal_edp_ralaivaosaona_rasendrahasina_wagner2024": "10.1002/rsa.21176",
    "dovgal_edp_ravelomanana2023": "10.5070/C63261985",
    "collet_edp_gardy_gittenberger_ravelomanana2020": "10.1016/j.ejc.2020.103113",
    "edp2019": "10.1002/rsa.20836",
    "edp_gardy_gittenberger_kuba2016": "10.1007/s00453-016-0119-x",
    "edp_ravelomanana2015": "10.1016/j.ejc.2015.02.020",
    "edp2015": "10.1016/j.jda.2015.01.009",
    "attrapadung_herranz_laguillaumie_libert_edp_rafols2012": "10.1016/j.tcs.2011.12.004",
}

# ---------------------------------------------------------------- bib parsing
def parse_bib(text):
    """Brace-balanced parser: handles nested accents like Fran{\\c{c}}ois."""
    entries = {}
    pos = 0
    while True:
        m = re.search(r'@(\w+)\{([^,]+),', text[pos:])
        if not m:
            break
        kind, key = m.group(1), m.group(2).strip()
        i = pos + m.end()
        fields = {}
        while True:
            fm = re.match(r'\s*(\w+)\s*=\s*', text[i:])
            if not fm:
                break
            name = fm.group(1).lower()
            i += fm.end()
            if text[i] == '{':
                depth, j = 0, i
                while True:
                    c = text[j]
                    if c == '{': depth += 1
                    elif c == '}':
                        depth -= 1
                        if depth == 0: break
                    j += 1
                val = text[i+1:j]
                i = j + 1
            else:
                j = i
                while text[j] not in ',}\n': j += 1
                val = text[i:j].strip()
                i = j
            fields[name] = val
            cm = re.match(r'\s*,', text[i:])
            if cm:
                i += cm.end()
            else:
                break
        entries[key] = (kind, fields)
        pos = i
    return entries


def tex(s):
    s = L2T.latex_to_text(s)
    return s.replace('--', '–').strip()


def authors_html(field):
    out = []
    for a in field.split(' and '):
        a = tex(a)
        if ',' in a:
            last, first = [p.strip() for p in a.split(',', 1)]
            name = f"{first} {last}"
        else:
            name = a
        name = escape(name)
        if 'Panafieu' in name:
            name = f"<b>{name}</b>"
        out.append(name)
    if len(out) == 1:
        return out[0]
    return ', '.join(out[:-1]) + ' and ' + out[-1]


def links_html(f, key=''):
    links = []
    if 'arxiv' in f:
        links.append(("arXiv", "https://arxiv.org/abs/" + f['arxiv'].split(':')[-1]))
    if 'doi' in f and not f['doi'].startswith('10.48550/'):   # arXiv DOIs duplicate the arXiv link
        links.append(("DOI", "https://doi.org/" + f['doi']))
    elif f.get('url', '').startswith('https://doi.org/'):
        links.append(("DOI", f['url']))
    elif key in DOI_FALLBACK:
        links.append(("DOI", "https://doi.org/" + DOI_FALLBACK[key]))
    if 'hal.science' in f.get('url', ''):
        links.append(("HAL", f['url']))
    if not links and f.get('url'):
        links.append(("Link", f['url']))
    return links


def entry_html(key, kind, f):
    year = tex(f.get('year', ''))
    title = escape(tex(f['title']))
    authors = authors_html(f['author'])
    if key in VENUE:
        venue = escape(VENUE[key])
    else:
        j = escape(tex(f.get('fjournal', f.get('journal', ''))))
        vol = escape(tex(f.get('volume', '')))
        num = escape(tex(f.get('number', '')))
        pages = escape(tex(f.get('pages', '')))
        venue = j
        if vol:
            venue += f" {vol}"
            if num:
                venue += f"({num})"
        if pages and pages != 'TODO':
            venue += f", {pages}"
        if 'Accepted' in f.get('note', ''):
            venue += ". Accepted, to appear"
    links = ''.join(f'<a href="{escape(u)}">{escape(t)}</a>' for t, u in links_html(f, key))
    return (f'<li><span class="year">{escape(year)}</span>'
            f'<span class="pub"><span class="title">{title}</span>'
            f'<span class="authors">{authors}</span>'
            f'<span class="venue">{venue}</span>'
            + (f'<span class="links">{links}</span>' if links else '') +
            '</span></li>')


def patent_html(p):
    links = ''.join(f'<a href="{escape(u)}">{escape(t)}</a>' for t, u in p['links'])
    return (f'<li><span class="year"></span><span class="pub">'
            f'<span class="title">{escape(p["title"])}</span>'
            f'<span class="authors">{p["authors"]}</span>'
            f'<span class="venue">{escape(p["venue"])}</span>'
            f'<span class="links">{links}</span></span></li>')


# ---------------------------------------------------------------- page
def build(entries):
    pubs = []
    for label, keys in GROUPS:
        items = ''.join(entry_html(k, *entries[k]) for k in keys)
        pubs.append(f'<h3>{label}</h3>\n<ul class="publist">\n{items}\n</ul>')
    pubs.append('<h3>Patents</h3>\n<ul class="publist">\n'
                + ''.join(patent_html(p) for p in PATENTS) + '\n</ul>')
    publications = '\n'.join(pubs)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Élie de Panafieu</title>
<meta name="description" content="Élie de Panafieu, researcher at Nokia Bell Labs France. Analytic combinatorics, random graphs, analysis of algorithms.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
</head>
<body>

<header>
  <img class="portrait" src="portrait.jpg" alt="Élie de Panafieu" width="476" height="532">
  <div class="intro">
  <h1>Élie de Panafieu</h1>
  <p class="role">Researcher at Nokia Bell Labs France, Paris-Saclay</p>
  <p class="lede">I work in analytic combinatorics: encoding discrete structures by
  generating functions, and reading their asymptotics off the analytic behaviour of
  those functions. I apply it to the enumeration and typical structure of random
  graphs, and to the analysis of algorithms, with a focus on computational social
  choice.</p>
  <ul class="contact">
    <li><a href="mailto:depanafieuelie@gmail.com">depanafieuelie@gmail.com</a></li>
    <li><a href="cv.pdf">Curriculum vitae (PDF)</a></li>
    <li><a href="https://orcid.org/0009-0002-1386-971X">ORCID</a>,
        <a href="https://dblp.org/pid/33/9238.html">dblp</a>,
        <a href="https://arxiv.org/a/depanafieu_e_1">arXiv</a>,
        <a href="https://gitlab.com/depanafieuelie">GitLab</a></li>
  </ul>
  </div>
</header>

<main>

<section id="research">
  <h2>Research</h2>
  <div class="body">
    <p>Since my PhD I have worked at enriching analytic combinatorics for graph
    enumeration, in two directions: extending what the method can describe to richer
    models (degree constraints, hypergraphs, inhomogeneous graphs, directed graphs),
    and extracting more from the classical ones, such as complete asymptotic expansions
    of connected and regular graphs, the structure of sparse random digraphs across
    their phase transition, and the spectrum of sparse random graphs.</p>
    <p>The analysis of algorithms is my other source of problems, and the two mix: the
    exact enumeration of satisfiable 2-SAT formulas, cluster graphs and modularity,
    active clustering, and the manipulability of voting rules all use the same tools.</p>
    <p>I am the main coordinator of PROSOC, an ANR project on probability and social
    choice, submitted to the 2026 call and currently on the waiting list. I was the
    local coordinator at Nokia of RandNET, a European MSCA-RISE project on random
    graphs and networks (2021–2026).</p>
  </div>
</section>

<section id="publications">
  <h2>Publications</h2>
  <div class="body">
{publications}
  </div>
</section>

<section id="students">
  <h2>Students</h2>
  <div class="body">
    <ul class="plain">
      <li><b>Emma Caizergues</b>, PhD, Université Paris-Dauphine PSL, 2022–2025,
        co-supervised with Jérôme Lang and François Durand.
        <i>Analytic Combinatorics and the Probability of the Condorcet Paradox.</i></li>
      <li><b>Quentin Lutz</b>, PhD, Télécom Paris, 2019–2022, co-supervised with
        Thomas Bonald. <i>Graph-based Contributions to Machine Learning.</i></li>
      <li><b>Marta Teodora Trales</b>, bachelor thesis, École polytechnique, 2025,
        co-supervised with Cédric Adjih and Pierre Escamilla.</li>
    </ul>
  </div>
</section>

<section id="teaching">
  <h2>Teaching</h2>
  <div class="body">
    <ul class="plain">
      <li><a href="https://mpri-master.ens.fr/doku.php?id=cours:aofa">Analysis of
        Algorithms</a>, M2, Master Parisien de Recherche en Informatique, since 2019.</li>
      <li>Analytic Combinatorics, M2 <i>Mathématiques de l'aléatoire</i>,
        Université Paris-Saclay, since 2022.</li>
    </ul>
  </div>
</section>

</main>

<footer>
  <p>Nokia Bell Labs France, Centre Paris-Saclay, 91300 Massy, France.</p>
</footer>

</body>
</html>
'''


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'biblio_cv.bib'
    entries = parse_bib(open(path, encoding='utf-8').read())
    sys.stdout.write(build(entries))#!/usr/bin/env python3
"""Build index.html from biblio_cv.bib.

Usage:  python3 make_site.py biblio_cv.bib > index.html

The grouping mirrors cv.typ: journals, international conferences, French
conferences, preprints, thesis. Patents are written by hand below, as in the CV.
Requires: pip install pylatexenc
"""
import re
import sys
from html import escape
from pylatexenc.latex2text import LatexNodes2Text

L2T = LatexNodes2Text()

# ---------------------------------------------------------------- grouping
GROUPS = [
    ("Journal articles", [
        "hainzl_edp2026", "edp_wallner2026",
        "caizergues_durand_noy_edp_ravelomanana2025",
        "dovgal_edp_ralaivaosaona_rasendrahasina_wagner2024",
        "dovgal_edp_ravelomanana2023",
        "collet_edp_gardy_gittenberger_ravelomanana2020",
        "edp2019", "edp_gardy_gittenberger_kuba2016",
        "edp_ravelomanana2015", "edp2015",
        "attrapadung_herranz_laguillaumie_libert_edp_rafols2012",
    ]),
    ("Conference papers", [
        "durand_edp_perarnau2026_conf", "edp_durand_lang2026_conf",
        "hainzl_edp2024_conf", "chen_keevash_kennedy_edp_vetta2024_conf",
        "caizergues_edp2023_conf", "lutz_edp_stein_scott2021_conf",
        "edp_dovgal2020_conf", "edp_lamali_wallner2019_conf",
        "bouillard_comte_edp_mathieu2018_conf",
        "collet_edp_gardy_gittenberger_ravelomanana2017_conf",
        "edp_ramos2016_conf", "edp2016_conf", "edp2015_conf",
        "edp_gardy_gittenberger_kuba2014_conf", "bostan_chyzak_edp2013_conf",
        "attrapadung_libert_edp2011_conf",
    ]),
    ("French national conferences", [
        "edp_lamali_wallner2019_algotel", "bouillard_comte_edp_mathieu2019_algotel",
    ]),
    ("Preprints", [
        "edp2024_arxiv", "gosgens_luchtrath_magnanini_noy_edp2024_arxiv",
    ]),
    ("Thesis", ["edp2014_thesis"]),
]

# Short venue names for the web (the bib keeps the full proceedings titles)
VENUE = {
    "durand_edp_perarnau2026_conf": "IJCAI 2026",
    "edp_durand_lang2026_conf": "IJCAI 2026",
    "hainzl_edp2024_conf": "AofA 2024",
    "chen_keevash_kennedy_edp_vetta2024_conf": "ICALP 2024",
    "caizergues_edp2023_conf": "EUROCOMB 2023",
    "lutz_edp_stein_scott2021_conf": "NeurIPS 2021",
    "edp_dovgal2020_conf": "FPSAC 2020, Séminaire Lotharingien de Combinatoire 84B",
    "edp_lamali_wallner2019_conf": "ANALCO 2019",
    "bouillard_comte_edp_mathieu2018_conf": "ITC 30, 2018",
    "collet_edp_gardy_gittenberger_ravelomanana2017_conf": "EUROCOMB 2017",
    "edp_ramos2016_conf": "ANALCO 2016",
    "edp2016_conf": "FPSAC 2016",
    "edp2015_conf": "FPSAC 2015",
    "edp_gardy_gittenberger_kuba2014_conf": "LATIN 2014",
    "bostan_chyzak_edp2013_conf": "ISSAC 2013",
    "attrapadung_libert_edp2011_conf": "PKC 2011",
    "edp_lamali_wallner2019_algotel": "ALGOTEL 2019",
    "bouillard_comte_edp_mathieu2019_algotel": "ALGOTEL 2019",
    "edp2014_thesis": "PhD thesis, Université Paris-Diderot, 2014",
    "dovgal_edp_ravelomanana2023": "Combinatorial Theory 3(2), article 7",
    "edp_wallner2026": "Combinatorial Theory, to appear",
}

PATENTS = [
    dict(title="Positioning approach",
         authors="Chung Shue Chen, Paolo Baracca, <b>Élie de Panafieu</b>, Diomidis Michalopoulos",
         venue="Nokia Technologies. GB 2631540 A, EP 4488708 A1, US 2025/0016725 A1; "
               "priority 7 July 2023, published January 2025. Under examination",
         links=[("EPO", "https://worldwide.espacenet.com/publicationDetails/biblio?CC=EP&NR=4488708A1&KC=A1&FT=D")]),
    dict(title="Clustering of a set of items",
         authors="<b>Élie de Panafieu</b>, Maria Laura Maag, Quentin Lutz",
         venue="Nokia Solutions and Networks. EP 3923191 A1; filed 11 June 2020, "
               "published 15 December 2021, subsequently withdrawn",
         links=[("EPO", "https://worldwide.espacenet.com/publicationDetails/biblio?CC=EP&NR=3923191A1&KC=A1&FT=D")]),
]

DOI_FALLBACK = {
    "hainzl_edp2026": "10.1016/j.ejc.2026.104386",
    "dovgal_edp_ralaivaosaona_rasendrahasina_wagner2024": "10.1002/rsa.21176",
    "dovgal_edp_ravelomanana2023": "10.5070/C63261985",
    "collet_edp_gardy_gittenberger_ravelomanana2020": "10.1016/j.ejc.2020.103113",
    "edp2019": "10.1002/rsa.20836",
    "edp_gardy_gittenberger_kuba2016": "10.1007/s00453-016-0119-x",
    "edp_ravelomanana2015": "10.1016/j.ejc.2015.02.020",
    "edp2015": "10.1016/j.jda.2015.01.009",
    "attrapadung_herranz_laguillaumie_libert_edp_rafols2012": "10.1016/j.tcs.2011.12.004",
}

# ---------------------------------------------------------------- bib parsing
def parse_bib(text):
    """Brace-balanced parser: handles nested accents like Fran{\\c{c}}ois."""
    entries = {}
    pos = 0
    while True:
        m = re.search(r'@(\w+)\{([^,]+),', text[pos:])
        if not m:
            break
        kind, key = m.group(1), m.group(2).strip()
        i = pos + m.end()
        fields = {}
        while True:
            fm = re.match(r'\s*(\w+)\s*=\s*', text[i:])
            if not fm:
                break
            name = fm.group(1).lower()
            i += fm.end()
            if text[i] == '{':
                depth, j = 0, i
                while True:
                    c = text[j]
                    if c == '{': depth += 1
                    elif c == '}':
                        depth -= 1
                        if depth == 0: break
                    j += 1
                val = text[i+1:j]
                i = j + 1
            else:
                j = i
                while text[j] not in ',}\n': j += 1
                val = text[i:j].strip()
                i = j
            fields[name] = val
            cm = re.match(r'\s*,', text[i:])
            if cm:
                i += cm.end()
            else:
                break
        entries[key] = (kind, fields)
        pos = i
    return entries


def tex(s):
    s = L2T.latex_to_text(s)
    return s.replace('--', '–').strip()


def authors_html(field):
    out = []
    for a in field.split(' and '):
        a = tex(a)
        if ',' in a:
            last, first = [p.strip() for p in a.split(',', 1)]
            name = f"{first} {last}"
        else:
            name = a
        name = escape(name)
        if 'Panafieu' in name:
            name = f"<b>{name}</b>"
        out.append(name)
    if len(out) == 1:
        return out[0]
    return ', '.join(out[:-1]) + ' and ' + out[-1]


def links_html(f, key=''):
    links = []
    if 'arxiv' in f:
        links.append(("arXiv", "https://arxiv.org/abs/" + f['arxiv'].split(':')[-1]))
    if 'doi' in f and not f['doi'].startswith('10.48550/'):   # arXiv DOIs duplicate the arXiv link
        links.append(("DOI", "https://doi.org/" + f['doi']))
    elif f.get('url', '').startswith('https://doi.org/'):
        links.append(("DOI", f['url']))
    elif key in DOI_FALLBACK:
        links.append(("DOI", "https://doi.org/" + DOI_FALLBACK[key]))
    if 'hal.science' in f.get('url', ''):
        links.append(("HAL", f['url']))
    if not links and f.get('url'):
        links.append(("Link", f['url']))
    return links


def entry_html(key, kind, f):
    year = tex(f.get('year', ''))
    title = escape(tex(f['title']))
    authors = authors_html(f['author'])
    if key in VENUE:
        venue = escape(VENUE[key])
    else:
        j = escape(tex(f.get('fjournal', f.get('journal', ''))))
        vol = escape(tex(f.get('volume', '')))
        num = escape(tex(f.get('number', '')))
        pages = escape(tex(f.get('pages', '')))
        venue = j
        if vol:
            venue += f" {vol}"
            if num:
                venue += f"({num})"
        if pages and pages != 'TODO':
            venue += f", {pages}"
        if 'Accepted' in f.get('note', ''):
            venue += ". Accepted, to appear"
    links = ''.join(f'<a href="{escape(u)}">{escape(t)}</a>' for t, u in links_html(f, key))
    return (f'<li><span class="year">{escape(year)}</span>'
            f'<span class="pub"><span class="title">{title}</span>'
            f'<span class="authors">{authors}</span>'
            f'<span class="venue">{venue}</span>'
            + (f'<span class="links">{links}</span>' if links else '') +
            '</span></li>')


def patent_html(p):
    links = ''.join(f'<a href="{escape(u)}">{escape(t)}</a>' for t, u in p['links'])
    return (f'<li><span class="year"></span><span class="pub">'
            f'<span class="title">{escape(p["title"])}</span>'
            f'<span class="authors">{p["authors"]}</span>'
            f'<span class="venue">{escape(p["venue"])}</span>'
            f'<span class="links">{links}</span></span></li>')


# ---------------------------------------------------------------- page
def build(entries):
    pubs = []
    for label, keys in GROUPS:
        items = ''.join(entry_html(k, *entries[k]) for k in keys)
        pubs.append(f'<h3>{label}</h3>\n<ul class="publist">\n{items}\n</ul>')
    pubs.append('<h3>Patents</h3>\n<ul class="publist">\n'
                + ''.join(patent_html(p) for p in PATENTS) + '\n</ul>')
    publications = '\n'.join(pubs)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Élie de Panafieu</title>
<meta name="description" content="Élie de Panafieu, researcher at Nokia Bell Labs France. Analytic combinatorics, random graphs, analysis of algorithms.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
</head>
<body>

<header>
  <h1>Élie de Panafieu</h1>
  <p class="role">Researcher at Nokia Bell Labs France, Paris-Saclay</p>
  <p class="lede">I work in analytic combinatorics: encoding discrete structures by
  generating functions, and reading their asymptotics off the analytic behaviour of
  those functions. I apply it to the enumeration and typical structure of random
  graphs, and to the analysis of algorithms, in particular in computational social choice.</p>
  <ul class="contact">
    <li><a href="mailto:depanafieuelie@gmail.com">depanafieuelie@gmail.com</a></li>
    <li><a href="cv.pdf">Curriculum vitae (PDF)</a></li>
    <li><a href="https://orcid.org/0009-0002-1386-971X">ORCID</a>,
        <a href="https://dblp.org/pid/33/9238.html">dblp</a>,
        <a href="https://arxiv.org/a/depanafieu_e_1">arXiv</a>,
        <a href="https://gitlab.com/depanafieuelie">GitLab</a></li>
  </ul>
</header>

<main>

<section id="research">
  <h2>Research</h2>
  <div class="body">
    <p>Since my PhD I have worked at enriching analytic combinatorics for graph
    enumeration, in two directions: extending what the method can describe to richer
    models (degree constraints, hypergraphs, inhomogeneous graphs, directed graphs),
    and extracting more from the classical ones, such as complete asymptotic expansions
    of connected and regular graphs, the structure of sparse random digraphs across
    their phase transition, and the spectrum of sparse random graphs.</p>
    <p>The analysis of algorithms is my other source of problems, and the two mix: the
    exact enumeration of satisfiable 2-SAT formulas, cluster graphs and modularity,
    active clustering, and the manipulability of voting rules all use the same tools.</p>
    <p>I am the main coordinator of the ANR project PROSOC on probability and social
    choice, submitted in 2026 and in the waiting list, and was the local coordinator at Nokia of the European MSCA-RISE project
    RandNET on random graphs and networks.</p>
  </div>
</section>

<section id="publications">
  <h2>Publications</h2>
  <div class="body">
{publications}
  </div>
</section>

<section id="students">
  <h2>Students</h2>
  <div class="body">
    <ul class="plain">
      <li><b>Emma Caizergues</b>, PhD, Université Paris-Dauphine PSL, 2022–2025,
        co-supervised with Jérôme Lang and François Durand.
        <i>Analytic Combinatorics and the Probability of the Condorcet Paradox.</i></li>
      <li><b>Quentin Lutz</b>, PhD, Télécom Paris, 2019–2022, co-supervised with
        Thomas Bonald. <i>Graph-based Contributions to Machine Learning.</i></li>
      <li><b>Marta Teodora Trales</b>, bachelor thesis, École polytechnique, 2025,
        co-supervised with Cédric Adjih and Pierre Escamilla.</li>
    </ul>
  </div>
</section>

<section id="teaching">
  <h2>Teaching</h2>
  <div class="body">
    <ul class="plain">
      <li><a href="https://mpri-master.ens.fr/doku.php?id=cours:aofa">Analysis of
        Algorithms</a>, M2, Master Parisien de Recherche en Informatique, since 2019.</li>
      <li>Analytic Combinatorics, M2 <i>Mathématiques de l'aléatoire</i>,
        Université Paris-Saclay, since 2022.</li>
    </ul>
  </div>
</section>

</main>

<footer>
  <p>Nokia Bell Labs France, Centre Paris-Saclay, 91300 Massy, France.</p>
</footer>

</body>
</html>
'''


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'biblio_cv.bib'
    entries = parse_bib(open(path, encoding='utf-8').read())
    sys.stdout.write(build(entries))
