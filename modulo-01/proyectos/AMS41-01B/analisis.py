"""
analisis.py — Abstracts of Papers Presented to the AMS, Volume 41 (2020)
=========================================================================
Fuente: https://pubs.ams.org/ABS?active=all

PDFs analizados (volumen 41, números 1–4):
  abs-41-01.pdf  → meeting 1154  (JMM Denver, enero 2020)
  abs-41-02.pdf  → meetings 1155-1158  (cancelados por COVID-19)
  abs-41-03.pdf  → meetings 1159-1160  (virtuales, otoño 2020)
  abs-41-04.pdf  → meetings 1161-1162  (virtuales, otoño 2020)

Uso (desde la raíz del repositorio):
    conda activate RAGLAB
    python modulo-01/proyectos/AMS41-01B/analisis.py

Salida:
    docs/proyectos/AMS41-01B/graficos/*.png
    docs/proyectos/AMS41-01B/index.html
"""

import re
import sys
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pypdf import PdfReader

# ── Rutas ─────────────────────────────────────────────────────────────────────
HERE      = Path(__file__).resolve().parent   # …/AMS41-01B/
ROOT      = HERE.parents[2]                   # raíz del repositorio
DATOS_DIR = HERE / "datos"
GRAF_DIR  = ROOT / "docs" / "proyectos" / "AMS41-01B" / "graficos"
HTML_OUT  = ROOT / "docs" / "proyectos" / "AMS41-01B" / "index.html"
FUENTE    = "https://pubs.ams.org/ABS?active=all"

GRAF_DIR.mkdir(parents=True, exist_ok=True)
HTML_OUT.parent.mkdir(parents=True, exist_ok=True)

PDF_FILES = [
    DATOS_DIR / "abs-41-01.pdf",
    DATOS_DIR / "abs-41-02.pdf",
    DATOS_DIR / "abs-41-03.pdf",
    DATOS_DIR / "abs-41-04.pdf",
]

CANCELED_MEETINGS = {1155, 1156, 1157, 1158}

# ── Metadatos de cada meeting ──────────────────────────────────────────────────
MEETING_META = {
    1154: ("Joint Mathematics Meetings",          "Denver, CO",                  "15–18 ene 2020", False),
    1155: ("Spring Eastern Sectional",            "Charlottesville, VA",         "13–15 mar 2020", True),
    1156: ("Spring Eastern Sectional",            "Medford, MA",                 "21–22 mar 2020", True),
    1157: ("Spring Central Sectional",            "West Lafayette, IN",          "4–5 abr 2020",   True),
    1158: ("Spring Western Sectional",            "Fresno, CA",                  "2–3 may 2020",   True),
    1159: ("Fall Central Virtual Sectional",      "El Paso, TX (virtual)",       "12–13 sep 2020", False),
    1160: ("Fall Eastern Virtual Sectional",      "State College, PA (virtual)", "3–4 oct 2020",   False),
    1161: ("Fall Southeastern Virtual Sectional", "Chattanooga, TN (virtual)",   "10–11 oct 2020", False),
    1162: ("Fall Western Virtual Sectional",      "Salt Lake City, UT (virtual)","24–25 oct 2020", False),
}

# ── Etiquetas MSC 2010 ────────────────────────────────────────────────────────
MSC_LABELS = {
    "00": "General",
    "01": "History & Biography",
    "03": "Mathematical Logic & Foundations",
    "05": "Combinatorics",
    "06": "Order, Lattices",
    "08": "General Algebraic Systems",
    "11": "Number Theory",
    "12": "Field Theory & Polynomials",
    "13": "Commutative Algebra",
    "14": "Algebraic Geometry",
    "15": "Linear & Multilinear Algebra",
    "16": "Associative Rings & Algebras",
    "17": "Non-associative Rings & Algebras",
    "18": "Category Theory",
    "19": "K-Theory",
    "20": "Group Theory",
    "22": "Topological Groups, Lie Groups",
    "26": "Real Functions",
    "28": "Measure & Integration",
    "30": "Functions of a Complex Variable",
    "31": "Potential Theory",
    "32": "Several Complex Variables",
    "33": "Special Functions",
    "34": "Ordinary Differential Equations",
    "35": "Partial Differential Equations",
    "37": "Dynamical Systems & Ergodic Theory",
    "39": "Difference & Functional Equations",
    "40": "Sequences, Series, Summability",
    "41": "Approximations & Expansions",
    "42": "Fourier Analysis",
    "43": "Abstract Harmonic Analysis",
    "44": "Integral Transforms",
    "45": "Integral Equations",
    "46": "Functional Analysis",
    "47": "Operator Theory",
    "49": "Calculus of Variations & Optimal Control",
    "51": "Geometry",
    "52": "Convex & Discrete Geometry",
    "53": "Differential Geometry",
    "54": "General Topology",
    "55": "Algebraic Topology",
    "57": "Manifolds & Cell Complexes",
    "58": "Global Analysis",
    "60": "Probability Theory & Stochastic Processes",
    "62": "Statistics",
    "65": "Numerical Analysis",
    "68": "Computer Science",
    "70": "Mechanics of Particles & Systems",
    "74": "Mechanics of Deformable Solids",
    "76": "Fluid Mechanics",
    "78": "Optics & Electromagnetic Theory",
    "80": "Classical Thermodynamics",
    "81": "Quantum Theory",
    "82": "Statistical Mechanics",
    "83": "Relativity & Gravitational Theory",
    "85": "Astronomy & Astrophysics",
    "86": "Geophysics",
    "90": "Operations Research",
    "91": "Game Theory & Economics",
    "92": "Biology & Other Natural Sciences",
    "93": "Systems Theory & Control",
    "94": "Information & Communication",
    "97": "Mathematics Education",
}

# ── Tabla de dominios de email → institución ──────────────────────────────────
# Construida a partir de los dominios académicos más frecuentes en los PDFs.
# Solo cubre dominios educativos. Emails personales o comerciales se marcan
# explícitamente. Dominios no listados devuelven "unknown".
EMAIL_DOMAIN_MAP = {
    # EE. UU. — Universidades grandes con presencia frecuente en AMS
    "mit.edu":           "Massachusetts Institute of Technology",
    "harvard.edu":       "Harvard University",
    "princeton.edu":     "Princeton University",
    "yale.edu":          "Yale University",
    "stanford.edu":      "Stanford University",
    "caltech.edu":       "California Institute of Technology",
    "uchicago.edu":      "University of Chicago",
    "columbia.edu":      "Columbia University",
    "cornell.edu":       "Cornell University",
    "upenn.edu":         "University of Pennsylvania",
    "brown.edu":         "Brown University",
    "dartmouth.edu":     "Dartmouth College",
    "duke.edu":          "Duke University",
    "northwestern.edu":  "Northwestern University",
    "vanderbilt.edu":    "Vanderbilt University",
    "emory.edu":         "Emory University",
    "wustl.edu":         "Washington University in St. Louis",
    "nd.edu":            "University of Notre Dame",
    "tulane.edu":        "Tulane University",
    "georgetown.edu":    "Georgetown University",
    # Big Ten / Midwest
    "umich.edu":         "University of Michigan",
    "msu.edu":           "Michigan State University",
    "wisc.edu":          "University of Wisconsin–Madison",
    "umn.edu":           "University of Minnesota",
    "illinois.edu":      "University of Illinois Urbana-Champaign",
    "northwestern.edu":  "Northwestern University",
    "ohio-state.edu":    "Ohio State University",
    "osu.edu":           "Ohio State University",
    "indiana.edu":       "Indiana University",
    "purdue.edu":        "Purdue University",
    "iastate.edu":       "Iowa State University",
    "uiowa.edu":         "University of Iowa",
    "ku.edu":            "University of Kansas",
    "ksu.edu":           "Kansas State University",
    "unl.edu":           "University of Nebraska–Lincoln",
    "umd.edu":           "University of Maryland",
    "psu.edu":           "Pennsylvania State University",
    "pitt.edu":          "University of Pittsburgh",
    "cmu.edu":           "Carnegie Mellon University",
    # Southeast
    "unc.edu":           "University of North Carolina",
    "ncsu.edu":          "NC State University",
    "duke.edu":          "Duke University",
    "virginia.edu":      "University of Virginia",
    "vt.edu":            "Virginia Tech",
    "gmu.edu":           "George Mason University",
    "gatech.edu":        "Georgia Institute of Technology",
    "gsu.edu":           "Georgia State University",
    "uga.edu":           "University of Georgia",
    "auburn.edu":        "Auburn University",
    "ua.edu":            "University of Alabama",
    "ufl.edu":           "University of Florida",
    "fsu.edu":           "Florida State University",
    "ucf.edu":           "University of Central Florida",
    "usf.edu":           "University of South Florida",
    "usc.edu":           "University of Southern California",
    "tulane.edu":        "Tulane University",
    "lsu.edu":           "Louisiana State University",
    "msstate.edu":       "Mississippi State University",
    "olemiss.edu":       "University of Mississippi",
    "memphis.edu":       "University of Memphis",
    "utk.edu":           "University of Tennessee",
    "utc.edu":           "University of Tennessee at Chattanooga",
    "tuskegee.edu":      "Tuskegee University",
    "sc.edu":            "University of South Carolina",
    "clemson.edu":       "Clemson University",
    # Southwest / Mountain
    "utexas.edu":        "University of Texas at Austin",
    "tamu.edu":          "Texas A&M University",
    "uta.edu":           "University of Texas at Arlington",
    "utsa.edu":          "University of Texas at San Antonio",
    "utep.edu":          "University of Texas at El Paso",
    "ttu.edu":           "Texas Tech University",
    "uh.edu":            "University of Houston",
    "rice.edu":          "Rice University",
    "tcu.edu":           "Texas Christian University",
    "baylor.edu":        "Baylor University",
    "asu.edu":           "Arizona State University",
    "arizona.edu":       "University of Arizona",
    "nau.edu":           "Northern Arizona University",
    "unm.edu":           "University of New Mexico",
    "colorado.edu":      "University of Colorado Boulder",
    "colostate.edu":     "Colorado State University",
    "mines.edu":         "Colorado School of Mines",
    "du.edu":            "University of Denver",
    "utah.edu":          "University of Utah",
    "usu.edu":           "Utah State University",
    "unr.edu":           "University of Nevada, Reno",
    "unlv.edu":          "University of Nevada, Las Vegas",
    "uwyo.edu":          "University of Wyoming",
    "montana.edu":       "Montana State University",
    "uidaho.edu":        "University of Idaho",
    "boisestate.edu":    "Boise State University",
    "oregonstate.edu":   "Oregon State University",
    "uoregon.edu":       "University of Oregon",
    "wsu.edu":           "Washington State University",
    "uw.edu":            "University of Washington",
    # California
    "berkeley.edu":      "University of California, Berkeley",
    "ucla.edu":          "University of California, Los Angeles",
    "ucsd.edu":          "University of California, San Diego",
    "ucsb.edu":          "University of California, Santa Barbara",
    "uci.edu":           "University of California, Irvine",
    "ucdavis.edu":       "University of California, Davis",
    "ucr.edu":           "University of California, Riverside",
    "ucsc.edu":          "University of California, Santa Cruz",
    "ucsf.edu":          "University of California, San Francisco",
    "calstate.edu":      "California State University",
    "sfsu.edu":          "San Francisco State University",
    "csufresno.edu":     "California State University, Fresno",
    "cpp.edu":           "Cal Poly Pomona",
    "calpoly.edu":       "California Polytechnic State University",
    "sandiego.edu":      "University of San Diego",
    "usfca.edu":         "University of San Francisco",
    "stmarys-ca.edu":    "Saint Mary's College of California",
    "pepperdine.edu":    "Pepperdine University",
    "chapman.edu":       "Chapman University",
    "lmu.edu":           "Loyola Marymount University",
    # Northeast liberal arts & small colleges
    "williams.edu":      "Williams College",
    "amherst.edu":       "Amherst College",
    "swarthmore.edu":    "Swarthmore College",
    "haverford.edu":     "Haverford College",
    "brynmawr.edu":      "Bryn Mawr College",
    "wellesley.edu":     "Wellesley College",
    "smith.edu":         "Smith College",
    "mtholyoke.edu":     "Mount Holyoke College",
    "vassar.edu":        "Vassar College",
    "middlebury.edu":    "Middlebury College",
    "colgate.edu":       "Colgate University",
    "colby.edu":         "Colby College",
    "hamilton.edu":      "Hamilton College",
    "union.edu":         "Union College",
    "oberlin.edu":       "Oberlin College",
    "kenyon.edu":        "Kenyon College",
    "denison.edu":       "Denison University",
    "depauw.edu":        "DePauw University",
    "grinnell.edu":      "Grinnell College",
    "carleton.edu":      "Carleton College",
    "macalester.edu":    "Macalester College",
    "stolaf.edu":        "St. Olaf College",
    "wooster.edu":       "College of Wooster",
    "wittenberg.edu":    "Wittenberg University",
    "bates.edu":         "Bates College",
    "bowdoin.edu":       "Bowdoin College",
    "tufts.edu":         "Tufts University",
    "bc.edu":            "Boston College",
    "bu.edu":            "Boston University",
    "northeastern.edu":  "Northeastern University",
    "brandeis.edu":      "Brandeis University",
    "clarku.edu":        "Clark University",
    "wpi.edu":           "Worcester Polytechnic Institute",
    "umassd.edu":        "University of Massachusetts Dartmouth",
    "umass.edu":         "University of Massachusetts",
    "uconn.edu":         "University of Connecticut",
    "unh.edu":           "University of New Hampshire",
    "uvm.edu":           "University of Vermont",
    "uri.edu":           "University of Rhode Island",
    "rit.edu":           "Rochester Institute of Technology",
    "rochester.edu":     "University of Rochester",
    "fordham.edu":       "Fordham University",
    "nyu.edu":           "New York University",
    "stonybrook.edu":    "Stony Brook University",
    "binghamton.edu":    "Binghamton University",
    "buffalo.edu":       "University at Buffalo",
    "albany.edu":        "University at Albany",
    "rutgers.edu":       "Rutgers University",
    "njit.edu":          "New Jersey Institute of Technology",
    "stevens.edu":       "Stevens Institute of Technology",
    "drew.edu":          "Drew University",
    "shu.edu":           "Seton Hall University",
    "rider.edu":         "Rider University",
    "drexel.edu":        "Drexel University",
    "temple.edu":        "Temple University",
    "lehigh.edu":        "Lehigh University",
    "bucknell.edu":      "Bucknell University",
    "dickinson.edu":     "Dickinson College",
    "gettysburg.edu":    "Gettysburg College",
    "jhu.edu":           "Johns Hopkins University",
    "umd.edu":           "University of Maryland",
    "american.edu":      "American University",
    "gwu.edu":           "George Washington University",
    "howard.edu":        "Howard University",
    "catholic.edu":      "Catholic University of America",
    # Canadá
    "mcgill.ca":         "McGill University",
    "utoronto.ca":       "University of Toronto",
    "ubc.ca":            "University of British Columbia",
    "uwaterloo.ca":      "University of Waterloo",
    "ualberta.ca":       "University of Alberta",
    "ucalgary.ca":       "University of Calgary",
    "sfu.ca":            "Simon Fraser University",
    "yorku.ca":          "York University",
    "uottawa.ca":        "University of Ottawa",
    "queensu.ca":        "Queen's University",
    "mcmaster.ca":       "McMaster University",
    "dal.ca":            "Dalhousie University",
    "umanitoba.ca":      "University of Manitoba",
    "usask.ca":          "University of Saskatchewan",
    "uleth.ca":          "University of Lethbridge",
    # Europa
    "ox.ac.uk":          "University of Oxford",
    "cam.ac.uk":         "University of Cambridge",
    "ic.ac.uk":          "Imperial College London",
    "ucl.ac.uk":         "University College London",
    "edinburgh.ac.uk":   "University of Edinburgh",
    "bristol.ac.uk":     "University of Bristol",
    "warwick.ac.uk":     "University of Warwick",
    "manchester.ac.uk":  "University of Manchester",
    "leeds.ac.uk":       "University of Leeds",
    "nottingham.ac.uk":  "University of Nottingham",
    "kcl.ac.uk":         "King's College London",
    "soton.ac.uk":       "University of Southampton",
    "birmingham.ac.uk":  "University of Birmingham",
    "bath.ac.uk":        "University of Bath",
    "lse.ac.uk":         "London School of Economics",
    "fau.de":            "Friedrich-Alexander-Universität Erlangen-Nürnberg",
    "uni-bonn.de":       "University of Bonn",
    "uni-berlin.de":     "Freie Universität Berlin",
    "hu-berlin.de":      "Humboldt University of Berlin",
    "tum.de":            "Technical University of Munich",
    "kit.edu":           "Karlsruhe Institute of Technology",
    "uni-frankfurt.de":  "Goethe University Frankfurt",
    "uni-hamburg.de":    "University of Hamburg",
    "uni-koeln.de":      "University of Cologne",
    "uni-muenster.de":   "University of Münster",
    "uni-leipzig.de":    "University of Leipzig",
    "mpim-bonn.mpg.de":  "Max Planck Institute for Mathematics",
    "mis.mpg.de":        "Max Planck Institute for Mathematics in the Sciences",
    "upmc.fr":           "Université Pierre et Marie Curie",
    "ens.fr":            "École Normale Supérieure",
    "polytechnique.edu": "École Polytechnique",
    "inria.fr":          "INRIA",
    "univ-paris-diderot.fr": "Université Paris Diderot",
    "math.cnrs.fr":      "CNRS",
    "unistra.fr":        "University of Strasbourg",
    "sorbonne-universite.fr": "Sorbonne Université",
    "univ-grenoble-alpes.fr":  "Université Grenoble Alpes",
    "univ-lyon1.fr":     "Université Claude Bernard Lyon 1",
    "ethz.ch":           "ETH Zürich",
    "epfl.ch":           "EPFL",
    "unige.ch":          "University of Geneva",
    "unibas.ch":         "University of Basel",
    "unibe.ch":          "University of Bern",
    "uzh.ch":            "University of Zurich",
    "math.uu.se":        "Uppsala University",
    "kth.se":            "KTH Royal Institute of Technology",
    "su.se":             "Stockholm University",
    "chalmers.se":       "Chalmers University of Technology",
    "math.gu.se":        "University of Gothenburg",
    "ntnu.no":           "Norwegian University of Science and Technology",
    "uio.no":            "University of Oslo",
    "dtu.dk":            "Technical University of Denmark",
    "ku.dk":             "University of Copenhagen",
    "aau.dk":            "Aalborg University",
    "helsinki.fi":       "University of Helsinki",
    "jyu.fi":            "University of Jyväskylä",
    "uva.nl":            "University of Amsterdam",
    "uu.nl":             "Utrecht University",
    "leidenuniv.nl":     "Leiden University",
    "tudelft.nl":        "Delft University of Technology",
    "tue.nl":            "Eindhoven University of Technology",
    "kuleuven.be":       "KU Leuven",
    "ulb.ac.be":         "Université Libre de Bruxelles",
    "ugent.be":          "Ghent University",
    "uclouvain.be":      "Université catholique de Louvain",
    "unipd.it":          "University of Padua",
    "unibo.it":          "University of Bologna",
    "unimi.it":          "University of Milan",
    "sns.it":            "Scuola Normale Superiore",
    "sissa.it":          "SISSA",
    "polimi.it":         "Politecnico di Milano",
    "uam.es":            "Universidad Autónoma de Madrid",
    "ucm.es":            "Universidad Complutense de Madrid",
    "usc.es":            "University of Santiago de Compostela",
    "upv.es":            "Universitat Politècnica de València",
    "mat.uc.pt":         "University of Coimbra",
    "ist.utl.pt":        "Instituto Superior Técnico",
    "fc.ul.pt":          "University of Lisbon",
    "math.uni.wroc.pl":  "University of Wrocław",
    "mimuw.edu.pl":      "University of Warsaw",
    "agh.edu.pl":        "AGH University of Science and Technology",
    "math.muni.cz":      "Masaryk University",
    "karlin.mff.cuni.cz":"Charles University Prague",
    "elte.hu":           "Eötvös Loránd University",
    "renyi.hu":          "Alfréd Rényi Institute of Mathematics",
    "math.bme.hu":       "Budapest University of Technology",
    "math.uoa.gr":       "University of Athens",
    "math.ntua.gr":      "National Technical University of Athens",
    "math.auth.gr":      "Aristotle University of Thessaloniki",
    # Israel
    "huji.ac.il":        "Hebrew University of Jerusalem",
    "weizmann.ac.il":    "Weizmann Institute of Science",
    "tau.ac.il":         "Tel Aviv University",
    "technion.ac.il":    "Technion",
    "bgu.ac.il":         "Ben-Gurion University",
    "math.haifa.ac.il":  "University of Haifa",
    # América Latina
    "puc-rio.br":        "Pontifical Catholic University of Rio de Janeiro",
    "impa.br":           "IMPA",
    "unicamp.br":        "University of Campinas",
    "usp.br":            "University of São Paulo",
    "ufmg.br":           "Federal University of Minas Gerais",
    "cinvestav.mx":      "CINVESTAV",
    "unam.mx":           "UNAM",
    "utb.edu.co":        "Universidad Tecnológica de Bolívar",
    "uniandes.edu.co":   "Universidad de los Andes",
    # Asia & Pacífico
    "nus.edu.sg":        "National University of Singapore",
    "ntu.edu.sg":        "Nanyang Technological University",
    "hku.hk":            "University of Hong Kong",
    "cuhk.edu.hk":       "Chinese University of Hong Kong",
    "kyoto-u.ac.jp":     "Kyoto University",
    "u-tokyo.ac.jp":     "University of Tokyo",
    "math.tohoku.ac.jp": "Tohoku University",
    "kaist.ac.kr":       "KAIST",
    "snu.ac.kr":         "Seoul National University",
    "postech.ac.kr":     "POSTECH",
    "math.pku.edu.cn":   "Peking University",
    "math.tsinghua.edu.cn": "Tsinghua University",
    "fudan.edu.cn":      "Fudan University",
    "tifr.res.in":       "Tata Institute of Fundamental Research",
    "imsc.res.in":       "Institute of Mathematical Sciences Chennai",
    "cmi.ac.in":         "Chennai Mathematical Institute",
    "ims.ac.in":         "Indian Statistical Institute",
    "math.iitb.ac.in":   "IIT Bombay",
    "maths.anu.edu.au":  "Australian National University",
    "usyd.edu.au":       "University of Sydney",
    "unimelb.edu.au":    "University of Melbourne",
    "auckland.ac.nz":    "University of Auckland",
    # Emails personales/comerciales — no son instituciones
    "gmail.com":         "(email personal)",
    "yahoo.com":         "(email personal)",
    "hotmail.com":       "(email personal)",
    "outlook.com":       "(email personal)",
    "icloud.com":        "(email personal)",
    "me.com":            "(email personal)",
    "aol.com":           "(email personal)",
    "protonmail.com":    "(email personal)",
}

# ── Colores ───────────────────────────────────────────────────────────────────
CMAP20 = matplotlib.colormaps["tab20"]
CMAP10 = matplotlib.colormaps["tab10"]
CMAP_SET3 = matplotlib.colormaps["Set3"]


# ══════════════════════════════════════════════════════════════════════════════
# EXTRACCIÓN DE TEXTO
# ══════════════════════════════════════════════════════════════════════════════

def pdf_to_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(p.extract_text() or "" for p in reader.pages)


# ── Patrones regex ─────────────────────────────────────────────────────────────
_RE_ID        = re.compile(r"(?:^|\n)(\d{4})-(\d{2})-(\d+)\s+", re.MULTILINE)
_RE_RECEIVED  = re.compile(r"\(Received\s+([^)]{4,40})\)", re.IGNORECASE)
_RE_EMAIL     = re.compile(r"[\w.+\-]+@[\w.\-]+\.[a-z]{2,}", re.IGNORECASE)
_RE_PRESENTER = re.compile(
    r"((?:[A-ZÁÉÍÓÚÜÑ\u00C0-\u024F][a-záéíóúüñ\u00C0-\u024F.\-]+\s+){1,5}"
    r"[A-ZÁÉÍÓÚÜÑ\u00C0-\u024F][a-záéíóúüñ\u00C0-\u024F.\-]+)\*"
)


def _parse_block(block: str) -> tuple[str, str, str, str]:
    """
    Extrae (presenter, presenter_email, email_domain, affiliation_raw)
    de un bloque de abstract.

    Estructura del bloque:
        NNNN-CC-NNN  Nombre* (email), [Dept,] Institución, Ciudad, ST ZIP. Título.
                     Cuerpo. (Received DATE)
    """
    # Presenter
    pm = _RE_PRESENTER.search(block)
    presenter = pm.group(1).strip() if pm else ""

    # Email del presentador (primer email en el bloque)
    emails = _RE_EMAIL.findall(block)
    presenter_email = emails[0] if emails else ""

    # Dominio del email
    if presenter_email and "@" in presenter_email:
        email_domain = presenter_email.split("@", 1)[1].lower().strip(".")
    else:
        email_domain = ""

    # Afiliación: texto entre cierre del primer ")" y primer ". [A-Z]"
    affil_raw = ""
    p_close = block.find(")")
    if p_close != -1:
        after = block[p_close + 1:].strip().lstrip(",").strip()
        # Corte en punto seguido de espacio+mayúscula (inicio del título)
        m = re.search(r"(?<![A-Z])\.\s+[A-Z]", after)
        if m:
            affil_raw = after[: m.start()].strip(" ,\n")
        else:
            affil_raw = after.split("\n")[0].strip(" ,")
    affil_raw = re.sub(r"\s+", " ", affil_raw).strip(" .,")

    return presenter, presenter_email, email_domain, affil_raw


def _institution_from_text(affil: str) -> str:
    """
    Extrae nombre de institución del texto de afiliación.
    Elimina departamento, ciudad, estado y código postal.
    """
    if not affil:
        return ""
    s = re.sub(r"\b\d{5}(?:-\d{4})?\b", "", affil)        # zip
    s = re.sub(r",?\s+[A-Z]{2}\s*$", "", s.strip())        # estado final
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if not parts:
        return ""
    # Quitar departamento si el primero empieza con palabra clave
    dept_kw = ("department", "dept", "division", "school of",
               "college of", "faculty", "institute of", "program in")
    if len(parts) > 1 and any(parts[0].lower().startswith(k) for k in dept_kw):
        parts = parts[1:]
    institution = parts[0].strip(" .,") if parts else ""
    return re.sub(r"\s+", " ", institution).strip()


def _institution_from_domain(domain: str) -> str:
    """
    Consulta la tabla EMAIL_DOMAIN_MAP.
    Busca coincidencia exacta primero; luego sufijo (ej. sub.uni.edu → uni.edu).
    Retorna "" si el dominio es vacío, "(email personal)" si es personal,
    o "unknown" si no está en la tabla.
    """
    if not domain:
        return ""
    # Coincidencia exacta
    if domain in EMAIL_DOMAIN_MAP:
        return EMAIL_DOMAIN_MAP[domain]
    # Sufijo progresivo: quitar subdominios de izquierda
    parts = domain.split(".")
    for i in range(1, len(parts) - 1):
        suffix = ".".join(parts[i:])
        if suffix in EMAIL_DOMAIN_MAP:
            return EMAIL_DOMAIN_MAP[suffix]
    return "unknown"


def parse_pdf(pdf_path: Path) -> list[dict]:
    print(f"  Leyendo {pdf_path.name} …", flush=True)
    text = pdf_to_text(pdf_path)
    matches = list(_RE_ID.finditer(text))
    if not matches:
        print(f"    [ADVERTENCIA] Sin abstracts en {pdf_path.name}")
        return []

    records = []
    for i, m in enumerate(matches):
        start = m.start()
        end   = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()

        meeting_num = int(m.group(1))
        msc_code    = m.group(2)
        talk_num    = int(m.group(3))

        presenter, presenter_email, email_domain, affil_raw = _parse_block(block)

        inst_text   = _institution_from_text(affil_raw)
        inst_email  = _institution_from_domain(email_domain)

        # Fuente consolidada: texto primero; dominio como fallback
        if inst_text:
            institution     = inst_text
            inst_source     = "texto"
        elif inst_email and inst_email not in ("(email personal)", "unknown"):
            institution     = inst_email
            inst_source     = "dominio_email"
        elif inst_email == "(email personal)":
            institution     = "unknown"
            inst_source     = "email_personal"
        else:
            institution     = "unknown"
            inst_source     = "unknown"

        rcv = _RE_RECEIVED.search(block)
        received_date = rcv.group(1).strip() if rcv else ""

        records.append({
            "abstract_id":     f"{m.group(1)}-{msc_code}-{m.group(3)}",
            "meeting_num":     meeting_num,
            "msc_code":        msc_code,
            "msc_label":       MSC_LABELS.get(msc_code, f"Código {msc_code}"),
            "talk_num":        talk_num,
            "presenter":       presenter,
            "presenter_email": presenter_email,
            "email_domain":    email_domain,
            "affiliation_raw": affil_raw,
            "inst_from_text":  inst_text,
            "inst_from_email": inst_email,
            "institution":     institution,
            "inst_source":     inst_source,
            "received_date":   received_date,
            "issue_file":      pdf_path.name,
            "canceled":        meeting_num in CANCELED_MEETINGS,
        })

    print(f"    → {len(records)} abstracts")
    return records


def load_all() -> pd.DataFrame:
    rows = []
    for p in PDF_FILES:
        if not p.exists():
            print(f"  [ERROR] No encontrado: {p}", file=sys.stderr)
            sys.exit(1)
        rows.extend(parse_pdf(p))

    df = pd.DataFrame(rows)

    # Parse de fecha
    df["received_dt"] = pd.to_datetime(
        df["received_date"], format="mixed", errors="coerce", dayfirst=False
    )
    df["received_ym"] = df["received_dt"].dt.to_period("M")
    df["received_q"]  = df["received_dt"].dt.to_period("Q")

    df["msc_full"] = df["msc_code"] + " – " + df["msc_label"]
    return df


# ══════════════════════════════════════════════════════════════════════════════
# VALIDACIÓN
# ══════════════════════════════════════════════════════════════════════════════

def validate(df: pd.DataFrame) -> dict:
    n    = len(df)
    na   = df[~df["canceled"]]
    n_unk    = (df["institution"] == "unknown").sum()
    n_noem   = (df["presenter_email"] == "").sum()
    n_norcv  = (df["received_dt"].isna()).sum()
    n_cancel = df["canceled"].sum()
    src_txt  = (df["inst_source"] == "texto").sum()
    src_dom  = (df["inst_source"] == "dominio_email").sum()

    print("\n" + "=" * 60)
    print("REPORTE DE CALIDAD")
    print("=" * 60)
    print(f"  Total abstracts:                      {n:>6}")
    print(f"  Activos (presentados):                {len(na):>6}")
    print(f"  Cancelados (COVID-19, 1155–1158):     {n_cancel:>6}")
    print(f"  Institución 'unknown':                {n_unk:>6}  ({100*n_unk/n:.1f}%)")
    print(f"  Institución desde texto:              {src_txt:>6}  ({100*src_txt/n:.1f}%)")
    print(f"  Institución desde dominio email:      {src_dom:>6}  ({100*src_dom/n:.1f}%)")
    print(f"  Sin email del presentador:            {n_noem:>6}  ({100*n_noem/n:.1f}%)")
    print(f"  Sin fecha 'Received' parseable:       {n_norcv:>6}  ({100*n_norcv/n:.1f}%)")
    print("=" * 60 + "\n")

    return {
        "n_total":     n,
        "n_active":    len(na),
        "n_canceled":  int(n_cancel),
        "n_unk":       int(n_unk),
        "pct_unk":     round(100 * n_unk  / n, 1),
        "pct_noem":    round(100 * n_noem / n, 1),
        "pct_norcv":   round(100 * n_norcv/ n, 1),
        "pct_txt":     round(100 * src_txt / n, 1),
        "pct_dom":     round(100 * src_dom / n, 1),
    }


# ══════════════════════════════════════════════════════════════════════════════
# INDICADORES
# ══════════════════════════════════════════════════════════════════════════════

def compute_indicators(df: pd.DataFrame) -> dict:
    active = df[~df["canceled"]]
    n_act  = len(active)

    # 1. Total abstracts activos
    ind1 = n_act

    # 2. Diversidad temática (MSC únicos en meetings activos)
    ind2 = int(active["msc_code"].nunique())
    ind2_by_m = active.groupby("meeting_num")["msc_code"].nunique().to_dict()

    # 3. Cobertura de institución (% con institución != "unknown")
    n_with_inst = (active["institution"] != "unknown").sum()
    ind3 = round(100 * n_with_inst / n_act, 1) if n_act > 0 else 0.0

    # 4. Concentración en Top-5 instituciones (activos, institución conocida)
    act_k = active[active["institution"] != "unknown"]
    if len(act_k) > 0:
        top5 = act_k["institution"].value_counts().head(5).sum()
        ind4 = round(100 * top5 / len(act_k), 1)
    else:
        ind4 = None

    # 5. Proporción de abstracts cancelados
    ind5 = round(100 * df["canceled"].sum() / len(df), 1)

    return {
        "ind1": ind1,
        "ind2": ind2,
        "ind2_by_m": ind2_by_m,
        "ind3": ind3,
        "ind4": ind4,
        "ind5": ind5,
    }


# ══════════════════════════════════════════════════════════════════════════════
# HALLAZGOS
# ══════════════════════════════════════════════════════════════════════════════

def compute_findings(df: pd.DataFrame) -> list[str]:
    active = df[~df["canceled"]]
    finds  = []

    # Hallazgo 1: Área dominante JMM vs. virtuales
    jmm  = active[active["meeting_num"] == 1154]
    virt = active[active["meeting_num"].isin({1159, 1160, 1161, 1162})]
    if not jmm.empty and not virt.empty:
        top_j = jmm["msc_code"].value_counts()
        top_v = virt["msc_code"].value_counts()
        cj, nj = top_j.idxmax(), top_j.max()
        cv, nv = top_v.idxmax(), top_v.max()
        lj = MSC_LABELS.get(cj, cj)
        lv = MSC_LABELS.get(cv, cv)
        pj = round(100 * nj / len(jmm),  1)
        pv = round(100 * nv / len(virt), 1)
        finds.append(
            f"<strong>Área dominante por tipo de evento.</strong> "
            f"En la JMM Denver (meeting 1154, presencial), el tema más frecuente fue "
            f"<em>{cj} {lj}</em> ({nj} abstracts, {pj}% del meeting). "
            f"En los cuatro meetings virtuales seccionales post-COVID "
            f"(1159–1162 agrupados), el área más frecuente fue "
            f"<em>{cv} {lv}</em> ({nv} abstracts, {pv}% de esos meetings)."
        )

    # Hallazgo 2: Institución más activa (activos, institución conocida)
    act_k = active[active["institution"] != "unknown"]
    if not act_k.empty:
        vc = act_k["institution"].value_counts()
        i1, c1 = vc.index[0], vc.iloc[0]
        p1 = round(100 * c1 / len(act_k), 1)
        finds.append(
            f"<strong>Institución más activa.</strong> "
            f"<em>{i1}</em> concentra {c1} abstracts de los meetings activos "
            f"({p1}% del total con institución identificada). "
            f"El nombre proviene directamente del texto del PDF y no está "
            f"deduplicado; variantes ortográficas cuentan por separado."
        )

    # Hallazgo 3: Estacionalidad de envíos — comparar semestres
    df_rcv = df[df["received_dt"].notna()].copy()
    if not df_rcv.empty:
        # Clasificar por semestre del año de envío
        df_rcv["sem"] = df_rcv["received_dt"].dt.month.map(
            lambda m: "Ene–Jun" if m <= 6 else "Jul–Dic"
        )
        df_rcv["year"] = df_rcv["received_dt"].dt.year
        sem_count = df_rcv.groupby(["year", "sem"]).size().reset_index(name="n")
        peak = sem_count.loc[sem_count["n"].idxmax()]
        finds.append(
            f"<strong>Estacionalidad de envíos.</strong> "
            f"El pico de envíos al sistema AMS se concentró en "
            f"{int(peak['year'])} {peak['sem']} "
            f"({int(peak['n'])} abstracts). "
            f"Esto refleja los plazos de los meetings: las fechas límite de "
            f"recepción de los números de primavera e invierno del volumen 41 "
            f"corresponden al segundo semestre de 2019 y al primer trimestre de 2020."
        )

    # Hallazgo 4: Diversidad temática JMM vs. meetings seccionales
    if not jmm.empty and not virt.empty:
        div_jmm = jmm["msc_code"].nunique()
        div_by  = {
            m: active[active["meeting_num"] == m]["msc_code"].nunique()
            for m in [1159, 1160, 1161, 1162]
        }
        div_str = ", ".join(f"M{m}: {v}" for m, v in sorted(div_by.items()))
        finds.append(
            f"<strong>Diversidad temática: presencial vs. virtual.</strong> "
            f"La JMM Denver cubrió {div_jmm} áreas MSC2010 distintas, "
            f"frente a los meetings virtuales ({div_str} áreas respectivamente). "
            f"La menor diversidad de los meetings seccionales es esperable: "
            f"tienen un alcance geográfico y temático más acotado."
        )

    return finds


# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICOS
# ══════════════════════════════════════════════════════════════════════════════

def _save(fig: plt.Figure, fname: str) -> str:
    fig.savefig(GRAF_DIR / fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Guardado: {fname}")
    return fname


# ── G1: Top-25 MSC consolidado (activos vs. cancelados, apilado) ──────────────
def g_msc_consolidado(df: pd.DataFrame) -> str:
    grp = (
        df.groupby(["msc_code", "msc_label", "canceled"])
        .size().reset_index(name="n")
    )
    order = (
        grp.groupby("msc_code")["n"].sum()
        .sort_values(ascending=False).head(25).index
    )
    sub = grp[grp["msc_code"].isin(order)].copy()
    sub["etiq"] = sub["msc_code"] + " " + sub["msc_label"]
    pivot = (
        sub.pivot_table(index="etiq", columns="canceled",
                        values="n", aggfunc="sum", fill_value=0)
        .rename(columns={False: "Activo", True: "Cancelado (COVID-19)"})
    )
    pivot["_t"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("_t").drop(columns="_t")
    cols = [c for c in ["Activo", "Cancelado (COVID-19)"] if c in pivot.columns]
    pivot = pivot[cols]

    fig, ax = plt.subplots(figsize=(11, 9))
    pivot.plot(kind="barh", stacked=True, ax=ax,
               color=["#1976D2", "#E57373"], edgecolor="white", linewidth=0.4)
    ax.set_xlabel("Número de abstracts", fontsize=10)
    ax.set_title("Top 25 áreas MSC2010 — Vol. 41 completo\n"
                 "(azul = presentado · rojo = cancelado COVID-19)",
                 fontsize=11, pad=10)
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=8)
    return _save(fig, "msc_consolidado.png")


# ── G2: Top-10 MSC por meeting (subplots 3×3) ─────────────────────────────────
def g_msc_por_meeting(df: pd.DataFrame) -> str:
    meetings = sorted(df["meeting_num"].unique())
    ncols, nrows = 3, -(-len(meetings) // 3)
    fig, axes = plt.subplots(nrows, ncols, figsize=(15, 4.5 * nrows))
    axes = axes.flatten()
    for i, m in enumerate(meetings):
        ax  = axes[i]
        sub = df[df["meeting_num"] == m]
        cts = (
            sub.groupby(["msc_code", "msc_label"])
            .size().reset_index(name="n")
            .sort_values("n", ascending=False).head(10)
        )
        cts["etiq"] = cts["msc_code"] + " " + cts["msc_label"]
        cts = cts.sort_values("n")
        canceled = MEETING_META.get(m, ("", "", "", False))[3]
        color = "#E57373" if canceled else "#1976D2"
        bars = ax.barh(cts["etiq"], cts["n"],
                       color=color, edgecolor="white", linewidth=0.3)
        ax.bar_label(bars, padding=2, fontsize=7)
        meta = MEETING_META.get(m, (str(m), "", "", False))
        suf  = "  ✗ COVID-19" if canceled else ""
        ax.set_title(f"M{m}{suf}\n{meta[1]}, {meta[2]}", fontsize=8, pad=5)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="both", labelsize=7)
    for j in range(len(meetings), len(axes)):
        axes[j].set_visible(False)
    fig.suptitle("Top 10 áreas MSC2010 por meeting — Vol. 41",
                 fontsize=13, y=1.01)
    plt.tight_layout()
    return _save(fig, "msc_por_meeting.png")


# ── G3: Top-20 instituciones (activos, conocidas) ─────────────────────────────
def g_instituciones(df: pd.DataFrame) -> str:
    act = df[~df["canceled"] & (df["institution"] != "unknown")]
    cts = act["institution"].value_counts().head(20).sort_values()
    colors = [CMAP20(i / len(cts)) for i in range(len(cts))]

    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(cts.index, cts.values, color=colors,
                   edgecolor="white", linewidth=0.4)
    ax.bar_label(bars, padding=3, fontsize=8)
    ax.set_xlabel("Abstracts del presentador", fontsize=10)
    ax.set_title("Top 20 instituciones del presentador — meetings activos Vol. 41\n"
                 "(nombre extraído del PDF o inferido por dominio de email, sin deduplicación)",
                 fontsize=10, pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=8)
    return _save(fig, "instituciones.png")


# ── G4: Top-5 inst. por meeting (apilado, activos) ────────────────────────────
def g_inst_por_meeting(df: pd.DataFrame) -> str:
    act  = df[~df["canceled"] & (df["institution"] != "unknown")]
    top5 = act["institution"].value_counts().head(5).index.tolist()

    act = act.copy()
    act["inst_cat"] = act["institution"].map(
        lambda x: x if x in top5 else "Otras"
    )
    pivot = (
        act.groupby(["meeting_num", "inst_cat"])
        .size().unstack(fill_value=0)
    )
    cols = [c for c in top5 if c in pivot.columns]
    if "Otras" in pivot.columns:
        cols.append("Otras")
    pivot = pivot[cols]

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = [CMAP10(i / len(cols)) for i in range(len(cols))]
    pivot.plot(kind="bar", stacked=True, ax=ax,
               color=colors, edgecolor="white", linewidth=0.3)
    ax.set_xlabel("Meeting", fontsize=10)
    ax.set_ylabel("Abstracts", fontsize=10)
    ax.set_title("Top-5 instituciones por meeting activo — Vol. 41",
                 fontsize=11, pad=10)
    ax.legend(title="Institución", bbox_to_anchor=(1.01, 1),
              loc="upper left", fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    plt.xticks(rotation=0, fontsize=9)
    return _save(fig, "inst_por_meeting.png")


# ── G5: Composición MSC por meeting activo (apilado) ──────────────────────────
def g_msc_apilado(df: pd.DataFrame) -> str:
    active = df[~df["canceled"]]
    top8   = active["msc_code"].value_counts().head(8).index.tolist()
    active = active.copy()
    active["msc_cat"] = active["msc_code"].map(
        lambda c: c + " " + MSC_LABELS.get(c, c) if c in top8 else "Otros"
    )
    pivot = (
        active.groupby(["meeting_num", "msc_cat"])
        .size().unstack(fill_value=0)
    )
    t8_labels = [c + " " + MSC_LABELS.get(c, c) for c in top8
                 if c + " " + MSC_LABELS.get(c, c) in pivot.columns]
    cols = t8_labels + (["Otros"] if "Otros" in pivot.columns else [])
    pivot = pivot[[c for c in cols if c in pivot.columns]]

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = [CMAP20(i / len(cols)) for i in range(len(cols))]
    pivot.plot(kind="bar", stacked=True, ax=ax,
               color=colors, edgecolor="white", linewidth=0.3)
    ax.set_xlabel("Meeting", fontsize=10)
    ax.set_ylabel("Abstracts", fontsize=10)
    ax.set_title("Composición temática MSC2010 por meeting activo — Vol. 41",
                 fontsize=11, pad=10)
    ax.legend(title="Área MSC2010", bbox_to_anchor=(1.01, 1),
              loc="upper left", fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    plt.xticks(rotation=0, fontsize=9)
    return _save(fig, "msc_apilado.png")


# ── G6: Estacionalidad de envíos (received_ym, consolidado) ──────────────────
def g_estacionalidad(df: pd.DataFrame) -> str:
    rcv = df[df["received_dt"].notna()].copy()
    if rcv.empty:
        return ""
    cts = (
        rcv.groupby("received_ym")
        .size()
        .reset_index(name="n")
        .sort_values("received_ym")
    )
    labels = [str(p) for p in cts["received_ym"]]
    colors = ["#E57373" if df[df["received_ym"] == p]["canceled"].all()
              else "#1976D2"
              for p in cts["received_ym"]]

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.bar(labels, cts["n"], color="#1976D2", edgecolor="white", linewidth=0.3)
    ax.set_xlabel("Año–Mes de recepción ('Received')", fontsize=10)
    ax.set_ylabel("Abstracts", fontsize=10)
    ax.set_title("Estacionalidad de envíos — fechas 'Received' del Vol. 41\n"
                 "(todos los abstracts, independientemente del estado del meeting)",
                 fontsize=11, pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    plt.xticks(rotation=60, ha="right", fontsize=7)
    plt.tight_layout()
    return _save(fig, "estacionalidad.png")


# ── G7: Diversidad temática por meeting activo ────────────────────────────────
def g_diversidad(df: pd.DataFrame) -> str:
    active = df[~df["canceled"]]
    div = (
        active.groupby("meeting_num")["msc_code"]
        .nunique().reset_index(name="n_msc")
        .sort_values("meeting_num")
    )
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(div["meeting_num"].astype(str), div["n_msc"],
                  color="#7E57C2", edgecolor="white")
    ax.bar_label(bars, padding=3, fontsize=9)
    ax.set_xlabel("Meeting", fontsize=10)
    ax.set_ylabel("Áreas MSC2010 únicas", fontsize=10)
    ax.set_title("Diversidad temática (áreas MSC únicas) por meeting activo",
                 fontsize=11, pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    return _save(fig, "diversidad_msc.png")


# ── G8: Fuente de institución (texto vs. dominio email vs. unknown) ───────────
def g_fuente_inst(df: pd.DataFrame) -> str:
    src_map = {
        "texto":        "Desde texto (afil. explícita)",
        "dominio_email":"Desde dominio de email",
        "email_personal":"Email personal (no inst.)",
        "unknown":      "Desconocida",
    }
    cts = df["inst_source"].value_counts().rename(src_map)

    fig, ax = plt.subplots(figsize=(6, 4))
    colors = ["#43A047", "#1976D2", "#FFA726", "#E53935"]
    bars = ax.barh(cts.index, cts.values,
                   color=colors[:len(cts)], edgecolor="white")
    ax.bar_label(bars, padding=3, fontsize=9)
    ax.set_xlabel("Número de abstracts", fontsize=10)
    ax.set_title("Fuente de identificación de institución — Vol. 41 completo",
                 fontsize=11, pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=9)
    return _save(fig, "fuente_institucion.png")


# ══════════════════════════════════════════════════════════════════════════════
# HTML
# ══════════════════════════════════════════════════════════════════════════════

_GRAPH_CAPTIONS = {
    "msc_consolidado.png":   (
        "Top 25 áreas MSC2010 — Vol. 41 completo",
        "Los 25 temas más frecuentes de todo el volumen. "
        "Azul = meetings presentados; rojo = cancelados por COVID-19."
    ),
    "msc_por_meeting.png":   (
        "Top 10 áreas MSC2010 por meeting",
        "Los 10 temas más frecuentes en cada uno de los 9 meetings. "
        "Barras rojas = meetings cancelados."
    ),
    "instituciones.png":     (
        "Top 20 instituciones del presentador (meetings activos)",
        "Nombre extraído del PDF o inferido por dominio de email. "
        "Sin deduplicación de variantes ortográficas."
    ),
    "inst_por_meeting.png":  (
        "Top-5 instituciones por meeting activo (barras apiladas)",
        "Las 5 instituciones más frecuentes distribuidas por meeting activo. "
        "El resto se agrupa como 'Otras'."
    ),
    "msc_apilado.png":       (
        "Composición temática MSC2010 por meeting activo",
        "Los 8 códigos MSC más frecuentes apilados por meeting activo."
    ),
    "estacionalidad.png":    (
        "Estacionalidad de envíos — fechas 'Received'",
        "Número de abstracts por mes de envío al sistema AMS. "
        "Refleja la estacionalidad de los plazos de los meetings del vol. 41."
    ),
    "diversidad_msc.png":    (
        "Diversidad temática por meeting activo",
        "Número de códigos MSC2010 únicos en cada meeting activo."
    ),
    "fuente_institucion.png":(
        "Fuente de identificación de institución",
        "Muestra cuántos abstracts obtuvieron su institución desde el texto "
        "de la afiliación, desde el dominio del email, o quedaron desconocidos."
    ),
}


def _img(fname: str) -> str:
    alt, cap = _GRAPH_CAPTIONS.get(fname, (fname, ""))
    return (
        f'<figure class="chart">'
        f'<img src="graficos/{fname}" alt="{alt}" loading="lazy">'
        f'<figcaption>{cap}</figcaption>'
        f'</figure>\n'
    )


def build_html(df: pd.DataFrame, qv: dict, ind: dict,
               findings: list[str], graphs: list[str]) -> None:

    # Tabla de meetings
    rows = []
    for m in sorted(df["meeting_num"].unique()):
        meta = MEETING_META.get(m, (str(m), str(m), "", False))
        name, place, dates, canceled = meta
        n_total = len(df[df["meeting_num"] == m])
        n_msc   = df[df["meeting_num"] == m]["msc_code"].nunique()
        div_val = ind["ind2_by_m"].get(m, "—")
        badge   = ('<span class="badge-covid">Cancelado COVID-19</span>'
                   if canceled else
                   '<span class="badge-active">Presentado</span>')
        rows.append(
            f"<tr><td>{m}</td><td>{name}</td><td>{place}</td><td>{dates}</td>"
            f"<td>{n_total}</td>"
            f"<td>{n_msc if not canceled else div_val}</td>"
            f"<td>{badge}</td></tr>"
        )
    meeting_table = "\n".join(rows)

    # Indicadores
    ind4_str = f"{ind['ind4']}%" if ind["ind4"] is not None else "n/d"
    cards = f"""
    <div class="cards">
      <div class="card">
        <div class="value">{ind["ind1"]:,}</div>
        <div class="label">Abstracts en meetings<br>presentados</div>
      </div>
      <div class="card">
        <div class="value">{ind["ind2"]}</div>
        <div class="label">Áreas MSC2010 únicas<br>(meetings activos)</div>
      </div>
      <div class="card">
        <div class="value">{ind["ind3"]}%</div>
        <div class="label">Abstracts con institución<br>identificada (activos)</div>
      </div>
      <div class="card">
        <div class="value">{ind4_str}</div>
        <div class="label">Abstracts en Top-5 inst.<br>(meetings activos)</div>
      </div>
      <div class="card">
        <div class="value">{ind["ind5"]}%</div>
        <div class="label">Abstracts en meetings<br>cancelados (COVID-19)</div>
      </div>
    </div>"""

    # Hallazgos
    finds_html = "\n".join(
        f'<div class="finding">'
        f'<span class="fn">{i+1}</span>{f}'
        f'</div>'
        for i, f in enumerate(findings)
    )

    # Gráficos
    graphs_html = "".join(_img(g) for g in graphs if g)

    # Limitaciones
    lims = [
        "La afiliación extraída corresponde únicamente al <strong>presentador</strong> "
        "(autor marcado con *). La afiliación de los co-autores no se puede separar "
        "de forma fiable del texto plano.",

        f"El nombre de institución se obtiene por dos vías: (a) limpiando el texto de "
        f"la afiliación explícita ({qv['pct_txt']}% de los casos) y "
        f"(b) consultando una tabla estática de ~160 dominios académicos "
        f"({qv['pct_dom']}% de los casos). "
        f"El {qv['pct_unk']}% de los abstracts queda sin institución identificada. "
        f"La misma institución puede aparecer con distintas grafías; no se aplica "
        f"deduplicación.",

        "Los meetings <strong>1155–1158</strong> aparecen publicados en el volumen 41 "
        "pero <strong>no fueron presentados</strong> (cancelados por COVID-19). "
        "Se incluyen en los conteos globales con bandera <em>cancelado</em> "
        "y se excluyen de los indicadores de meetings activos.",

        "<code>pypdf</code> extrae texto plano. LaTeX, caracteres especiales y "
        f"saltos de página pueden fragmentar nombres o afiliaciones. "
        f"{qv['pct_noem']}% de los abstracts no tienen email del presentador parseable.",

        f"{qv['pct_norcv']}% de los abstracts no tienen fecha "
        f"\u201cReceived\u201d parseable. La fecha de recepción refleja cuándo se "
        f"envió el abstract al sistema AMS, no la fecha de presentación.",

        "El volumen 41 cubre exclusivamente el año 2020. Los resultados no son "
        "comparables con otros volúmenes sin normalizar por número de meetings.",
    ]
    lims_html = "\n".join(f"<li>{l}</li>" for l in lims)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Abstracts AMS Vol. 41 (2020) — Tablero</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Segoe UI", Arial, sans-serif;
      background: #f4f6fb; color: #222; line-height: 1.6;
    }}
    header {{
      background: #0d47a1; color: #fff;
      padding: 2rem 2.5rem 1.4rem;
    }}
    header h1 {{ font-size: 1.65rem; font-weight: 700; margin-bottom: .3rem; }}
    header p  {{ font-size: .93rem; opacity: .85; }}
    header a  {{ color: #90caf9; }}
    main {{ max-width: 1140px; margin: 2rem auto; padding: 0 1.5rem 3rem; }}
    h2 {{
      font-size: 1.15rem; font-weight: 700;
      margin: 2.2rem 0 .8rem;
      border-left: 4px solid #0d47a1;
      padding-left: .7rem; color: #0d47a1;
    }}
    .cards {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: .5rem; }}
    .card {{
      background: #fff; border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,.1);
      padding: 1.1rem 1.3rem; flex: 1 1 160px; text-align: center;
    }}
    .card .value {{ font-size: 1.85rem; font-weight: 800; color: #0d47a1; }}
    .card .label {{ font-size: .81rem; color: #555; margin-top: .15rem; }}
    .table-wrap {{ overflow-x: auto; margin-top: .4rem; }}
    table {{
      width: 100%; border-collapse: collapse; font-size: .87rem;
      background: #fff; border-radius: 8px; overflow: hidden;
      box-shadow: 0 1px 4px rgba(0,0,0,.08);
    }}
    th {{
      background: #0d47a1; color: #fff;
      padding: .5rem .75rem; text-align: left; font-weight: 600;
    }}
    td {{ padding: .45rem .75rem; border-bottom: 1px solid #e3e8f0; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #e8eaf6; }}
    .badge-covid {{
      background: #e53935; color: #fff; border-radius: 4px;
      padding: .1rem .4rem; font-size: .75rem; font-weight: 600;
    }}
    .badge-active {{
      background: #43a047; color: #fff; border-radius: 4px;
      padding: .1rem .4rem; font-size: .75rem; font-weight: 600;
    }}
    .finding {{
      background: #e8eaf6; border-left: 5px solid #3949ab;
      padding: .85rem 1rem; border-radius: 4px;
      font-size: .93rem; margin-bottom: .75rem;
      display: flex; gap: .75rem; align-items: flex-start;
    }}
    .fn {{
      background: #3949ab; color: #fff; border-radius: 50%;
      width: 1.55rem; height: 1.55rem; display: flex;
      align-items: center; justify-content: center;
      font-weight: 700; font-size: .83rem; flex-shrink: 0;
    }}
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
      gap: 1.4rem; margin-top: .5rem;
    }}
    figure.chart {{
      background: #fff; border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,.1); overflow: hidden;
    }}
    figure.chart img {{ width: 100%; height: auto; display: block; }}
    figure.chart figcaption {{
      padding: .5rem .85rem; font-size: .8rem;
      color: #555; border-top: 1px solid #e3e8f0;
    }}
    .limitations {{
      background: #fff8e1; border-left: 5px solid #f9a825;
      padding: .9rem 1.1rem; border-radius: 4px;
    }}
    .limitations ul {{ padding-left: 1.4rem; }}
    .limitations li {{ margin-bottom: .4rem; font-size: .88rem; }}
    footer {{
      text-align: center; font-size: .8rem;
      color: #888; padding: 1.5rem 0 2rem;
    }}
    footer a {{ color: #0d47a1; }}
  </style>
</head>
<body>
<header>
  <h1>Abstracts of Papers Presented to the AMS — Vol. 41 (2020)</h1>
  <p>Análisis de los 9 meetings del volumen 41. Fuente:
    <a href="{FUENTE}" target="_blank" rel="noopener">{FUENTE}</a>
  </p>
</header>
<main>
  <h2>Indicadores</h2>
  {cards}

  <h2>Meetings analizados</h2>
  <div class="table-wrap">
    <table>
      <thead>
        <tr><th>Meeting #</th><th>Nombre</th><th>Lugar</th><th>Fechas</th>
            <th>Abstracts</th><th>Áreas MSC</th><th>Estado</th></tr>
      </thead>
      <tbody>{meeting_table}</tbody>
    </table>
  </div>

  <h2>Hallazgos</h2>
  {finds_html}

  <h2>Gráficos</h2>
  <div class="charts-grid">{graphs_html}</div>

  <h2>Limitaciones</h2>
  <div class="limitations">
    <ul>{lims_html}</ul>
  </div>
</main>
<footer>
  <p>Generado con <code>analisis.py</code> ·
     Datos: <a href="{FUENTE}" target="_blank" rel="noopener">pubs.ams.org/ABS</a> ·
     No se publican filas individuales</p>
</footer>
</body>
</html>
"""
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"  Guardado: {HTML_OUT}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 60)
    print("AMS Proceedings Vol. 41 — Análisis (v3)")
    print("=" * 60)

    print("\n[1/5] Extrayendo texto de PDFs …")
    df = load_all()

    print("\n[2/5] Validando calidad …")
    qv = validate(df)

    print("[3/5] Calculando indicadores …")
    ind = compute_indicators(df)
    print(f"  Activos: {ind['ind1']}  |  MSC únicos: {ind['ind2']}"
          f"  |  Cobertura inst.: {ind['ind3']}%"
          f"  |  Cancelados: {ind['ind5']}%")

    print("\n[4/5] Generando gráficos …")
    graphs = [
        g_msc_consolidado(df),
        g_msc_por_meeting(df),
        g_instituciones(df),
        g_inst_por_meeting(df),
        g_msc_apilado(df),
        g_estacionalidad(df),
        g_diversidad(df),
        g_fuente_inst(df),
    ]
    graphs = [g for g in graphs if g]   # quitar vacíos (g_estacionalidad sin fechas)

    print("\n[5/5] Generando tablero HTML …")
    findings = compute_findings(df)
    build_html(df, qv, ind, findings, graphs)

    print("\n" + "=" * 60)
    print("LISTO")
    print(f"  Tablero : {HTML_OUT}")
    print(f"  Gráficos: {GRAF_DIR}  ({len(graphs)} archivos)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
