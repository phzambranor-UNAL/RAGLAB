"""
analisis.py — Análisis de abstracts del volumen 41 de Proceedings of AMS
=========================================================================
Fuente: https://pubs.ams.org/ABS?active=all
Volumen 41 (2020): meetings 1154–1162

Uso:
    python modulo-01/proyectos/AMS41-01/analisis.py

Genera:
    docs/proyectos/AMS41-01/graficos/*.png
    docs/proyectos/AMS41-01/index.html
"""

import re
import sys
import json
import textwrap
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pypdf import PdfReader

# ---------------------------------------------------------------------------
# RUTAS
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[3]          # raíz del repositorio
DATOS_DIR = Path(__file__).resolve().parent / "datos"
GRAFICOS_DIR = ROOT / "docs" / "proyectos" / "AMS41-01" / "graficos"
HTML_OUT = ROOT / "docs" / "proyectos" / "AMS41-01" / "index.html"

GRAFICOS_DIR.mkdir(parents=True, exist_ok=True)
HTML_OUT.parent.mkdir(parents=True, exist_ok=True)

FUENTE = "https://pubs.ams.org/ABS?active=all"

PDF_FILES = [
    DATOS_DIR / "abs-41-01.pdf",
    DATOS_DIR / "abs-41-02.pdf",
    DATOS_DIR / "abs-41-03.pdf",
    DATOS_DIR / "abs-41-04.pdf",
]

# Meetings cancelados por COVID-19 (contenidos en abs-41-02.pdf)
CANCELED_MEETINGS = {1155, 1156, 1157, 1158}

# ---------------------------------------------------------------------------
# MSC2010: etiquetas de dos dígitos
# Fuente: https://mathscinet.ams.org/msc/msc2010.html
# ---------------------------------------------------------------------------
MSC2010_LABELS = {
    "00": "General",
    "01": "History & Biography",
    "03": "Mathematical Logic",
    "05": "Combinatorics",
    "06": "Order, Lattices",
    "08": "General Algebraic Systems",
    "11": "Number Theory",
    "12": "Field Theory",
    "13": "Commutative Algebra",
    "14": "Algebraic Geometry",
    "15": "Linear & Multilinear Algebra",
    "16": "Associative Rings",
    "17": "Non-assoc. Rings & Algebras",
    "18": "Category Theory",
    "19": "K-Theory",
    "20": "Group Theory",
    "22": "Topological Groups",
    "26": "Real Functions",
    "28": "Measure & Integration",
    "30": "Complex Variables",
    "31": "Potential Theory",
    "32": "Several Complex Variables",
    "33": "Special Functions",
    "34": "Ordinary Diff. Equations",
    "35": "Partial Diff. Equations",
    "37": "Dynamical Systems",
    "39": "Difference & Functional Eq.",
    "40": "Sequences, Series, Summability",
    "41": "Approximations & Expansions",
    "42": "Fourier Analysis",
    "43": "Abstract Harmonic Analysis",
    "44": "Integral Transforms",
    "45": "Integral Equations",
    "46": "Functional Analysis",
    "47": "Operator Theory",
    "49": "Calculus of Variations",
    "51": "Geometry",
    "52": "Convex & Discrete Geometry",
    "53": "Differential Geometry",
    "54": "General Topology",
    "55": "Algebraic Topology",
    "57": "Manifolds & Cell Complexes",
    "58": "Global Analysis",
    "60": "Probability Theory",
    "62": "Statistics",
    "65": "Numerical Analysis",
    "68": "Computer Science",
    "70": "Mechanics of Particles",
    "74": "Mechanics of Deformable Solids",
    "76": "Fluid Mechanics",
    "78": "Optics & Electromagnetic Theory",
    "80": "Classical Thermodynamics",
    "81": "Quantum Theory",
    "82": "Statistical Mechanics",
    "83": "Relativity & Gravitation",
    "85": "Astronomy & Astrophysics",
    "86": "Geophysics",
    "90": "Operations Research",
    "91": "Game Theory & Economics",
    "92": "Biology & Other Nat. Sciences",
    "93": "Systems & Control Theory",
    "94": "Information & Communication",
    "97": "Math. Education",
}

# ---------------------------------------------------------------------------
# PAÍS: lista de estados de EE. UU. (abreviaturas de 2 letras)
# ---------------------------------------------------------------------------
US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
    "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
    "TX","UT","VT","VA","WA","WV","WI","WY","DC","PR","GU","VI","MP","AS",
}

# Palabras clave de países (en orden de preferencia, más específico primero)
COUNTRY_KEYWORDS = [
    ("United Kingdom", ["United Kingdom", "UK", " England", "Scotland", "Wales"]),
    ("Germany",        ["Germany", "Deutschland"]),
    ("France",         ["France"]),
    ("Canada",         ["Canada"]),
    ("Japan",          ["Japan"]),
    ("China",          ["China", "P.R. China", "P. R. China", "PRC"]),
    ("South Korea",    ["South Korea", "Korea", "Republic of Korea"]),
    ("Israel",         ["Israel"]),
    ("Australia",      ["Australia"]),
    ("Brazil",         ["Brazil", "Brasil"]),
    ("Italy",          ["Italy", "Italia"]),
    ("Spain",          ["Spain", "España"]),
    ("Mexico",         [" Mexico", "México"]),
    ("India",          ["India"]),
    ("Russia",         ["Russia", "Russian Federation"]),
    ("Switzerland",    ["Switzerland", "Suisse", "Schweiz"]),
    ("Netherlands",    ["Netherlands", "Holland"]),
    ("Sweden",         ["Sweden"]),
    ("Norway",         ["Norway"]),
    ("Denmark",        ["Denmark"]),
    ("Austria",        ["Austria"]),
    ("Belgium",        ["Belgium"]),
    ("Poland",         ["Poland"]),
    ("Czech Republic", ["Czech Republic", "Czechia"]),
    ("Hungary",        ["Hungary"]),
    ("Portugal",       ["Portugal"]),
    ("Greece",         ["Greece"]),
    ("Turkey",         ["Turkey"]),
    ("Iran",           ["Iran"]),
    ("Saudi Arabia",   ["Saudi Arabia"]),
    ("Argentina",      ["Argentina"]),
    ("Colombia",       ["Colombia"]),
    ("Chile",          ["Chile"]),
    ("New Zealand",    ["New Zealand"]),
    ("Singapore",      ["Singapore"]),
    ("Hong Kong",      ["Hong Kong"]),
    ("Taiwan",         ["Taiwan"]),
    ("Egypt",          ["Egypt"]),
    ("South Africa",   ["South Africa"]),
    ("Nigeria",        ["Nigeria"]),
    ("Morocco",        ["Morocco"]),
    ("Pakistan",       ["Pakistan"]),
    ("Bangladesh",     ["Bangladesh"]),
    ("Ukraine",        ["Ukraine"]),
    ("Romania",        ["Romania"]),
]


def detect_country(affil: str) -> str:
    """Detecta el país a partir del texto de afiliación."""
    if not affil:
        return "unknown"
    affil_stripped = affil.strip()
    # Patrón USA: termina en "ST NNNNN" o "ST NNNNN-NNNN"
    if re.search(r'\b([A-Z]{2})\s+\d{5}(?:-\d{4})?\s*$', affil_stripped):
        st = re.search(r'\b([A-Z]{2})\s+\d{5}', affil_stripped).group(1)
        if st in US_STATES:
            return "United States"
    # Patrón: abreviatura de estado sola al final (sin zip)
    m = re.search(r',\s*([A-Z]{2})\s*$', affil_stripped)
    if m and m.group(1) in US_STATES:
        return "United States"
    # Patrón: ciudad, ST abreviatura dentro del texto
    if re.search(r',\s*[A-Z]{2}\b', affil_stripped):
        candidates = re.findall(r',\s*([A-Z]{2})\b', affil_stripped)
        for c in candidates:
            if c in US_STATES:
                return "United States"
    # Búsqueda por palabras clave de países
    for country, keywords in COUNTRY_KEYWORDS:
        for kw in keywords:
            if kw.lower() in affil_stripped.lower():
                return country
    return "unknown"


# ---------------------------------------------------------------------------
# EXTRACCIÓN DE TEXTO
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extrae todo el texto de un PDF concatenando páginas."""
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)


# ---------------------------------------------------------------------------
# PARSEO DE ABSTRACTS
# ---------------------------------------------------------------------------

# Patrón de identificador: NNNN-CC-NNN (meeting-msc-talk)
ID_PATTERN = re.compile(
    r'(?:^|\n)(\d{4})-(\d{2})-(\d+)\s+',
    re.MULTILINE
)

# Encabezado de sección MSC dentro de la página: "NN ▶ Nombre" o "NN ► Nombre"
SECTION_HEADER = re.compile(
    r'(?:^|\n)(\d{2})\s+[▶►]\s+[A-Z][^\n]+',
    re.MULTILINE
)

# Fecha de recepción
RECEIVED_PATTERN = re.compile(r'\(Received\s+([^)]+)\)', re.IGNORECASE)

# Emails
EMAIL_PATTERN = re.compile(r'[\w.+\-]+@[\w.\-]+\.[a-z]{2,}', re.IGNORECASE)

# Presenter (nombre seguido de *)
PRESENTER_PATTERN = re.compile(
    r'((?:[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ.\-]+\s+){1,4}[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ.\-]+)\*'
)


def parse_abstracts_from_text(full_text: str, issue_file: str) -> list[dict]:
    """
    Parsea el texto completo de un PDF y devuelve una lista de dicts,
    uno por abstract.
    """
    records = []

    # Encuentra todas las posiciones de identificadores
    matches = list(ID_PATTERN.finditer(full_text))
    if not matches:
        return records

    for idx, m in enumerate(matches):
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(full_text)
        block = full_text[start:end].strip()

        meeting_num = int(m.group(1))
        msc_code = m.group(2)
        talk_num = int(m.group(3))
        abstract_id = f"{m.group(1)}-{msc_code}-{m.group(3)}"

        # --- Autores y afiliación ---
        # El bloque comienza con el ID, luego texto hasta el primer punto
        # que precede al título.
        # Separamos: todo antes del primer ".\n" o ".\s[A-Z]" que no sea
        # parte de una abreviatura.
        after_id = block[len(m.group(0).strip()):].strip()

        # Extraer emails del bloque completo
        emails = EMAIL_PATTERN.findall(block)

        # Presenter
        presenter_match = PRESENTER_PATTERN.search(block)
        presenter = presenter_match.group(1).strip() if presenter_match else ""

        # Fecha de recepción
        received_match = RECEIVED_PATTERN.search(block)
        received_date = received_match.group(1).strip() if received_match else ""

        # Afiliación: buscamos el primer segmento entre el cierre del paréntesis
        # de emails y el siguiente punto seguido de mayúscula (inicio del título).
        # Estrategia: extraer texto hasta el primer ".\n" o ". [A-Z]"
        affil_raw = ""
        # Tomamos todo el texto que precede a la fecha recibida
        if received_match:
            pre_received = block[: received_match.start()]
        else:
            pre_received = block

        # La afiliación suele aparecer después del cierre del primer paréntesis
        # que contiene el email/institución del primer autor.
        # Buscamos el fragmento de texto que contiene ciudad + estado/país
        # usando la heurística: parte del texto después de ")" y antes del
        # primer "." seguido de mayúscula (el título).
        paren_end = pre_received.rfind(")")
        if paren_end != -1:
            after_paren = pre_received[paren_end + 1:].strip()
            # Recortamos en el primer punto seguido de espacio+mayúscula
            title_break = re.search(r'\.\s+[A-Z]', after_paren)
            if title_break:
                affil_raw = after_paren[: title_break.start()].strip(", \n")
            else:
                # Sin título claro: tomamos hasta el primer salto de línea largo
                affil_raw = after_paren.split("\n")[0].strip(", ")

        # Limpiar afiliación: quitar caracteres de control y normalizar espacios
        affil_raw = re.sub(r'\s+', ' ', affil_raw).strip(" .,")

        country = detect_country(affil_raw)

        canceled = meeting_num in CANCELED_MEETINGS

        records.append({
            "abstract_id":    abstract_id,
            "meeting_num":    meeting_num,
            "msc_code":       msc_code,
            "talk_num":       talk_num,
            "presenter":      presenter,
            "emails":         "; ".join(emails),
            "affiliation_raw": affil_raw,
            "country":        country,
            "received_date":  received_date,
            "issue_file":     issue_file,
            "canceled":       canceled,
        })

    return records


# ---------------------------------------------------------------------------
# CARGA COMPLETA
# ---------------------------------------------------------------------------

def load_all_pdfs(pdf_files: list[Path]) -> pd.DataFrame:
    all_records = []
    for pdf_path in pdf_files:
        if not pdf_path.exists():
            print(f"[ADVERTENCIA] No se encontró: {pdf_path}", file=sys.stderr)
            continue
        print(f"  Leyendo {pdf_path.name} ...", flush=True)
        text = extract_text_from_pdf(pdf_path)
        records = parse_abstracts_from_text(text, pdf_path.name)
        print(f"    → {len(records)} abstracts extraídos")
        all_records.extend(records)

    df = pd.DataFrame(all_records)

    if df.empty:
        print("[ERROR] No se extrajo ningún abstract. Verifique los PDFs.", file=sys.stderr)
        sys.exit(1)

    # Añadir etiqueta MSC2010
    df["msc_label"] = df["msc_code"].map(MSC2010_LABELS).fillna("Código " + df["msc_code"])

    # Columna combinada para gráficos
    df["msc_full"] = df["msc_code"] + " – " + df["msc_label"]

    return df


# ---------------------------------------------------------------------------
# VALIDACIÓN
# ---------------------------------------------------------------------------

def print_validation_report(df: pd.DataFrame) -> dict:
    total = len(df)
    unknown_country = (df["country"] == "unknown").sum()
    missing_received = (df["received_date"] == "").sum()
    missing_affil = (df["affiliation_raw"] == "").sum()
    canceled_count = df["canceled"].sum()

    print("\n" + "=" * 60)
    print("REPORTE DE CALIDAD DE EXTRACCIÓN")
    print("=" * 60)
    print(f"  Total abstracts extraídos:        {total:>6}")
    print(f"  País 'unknown':                   {unknown_country:>6} ({100*unknown_country/total:.1f}%)")
    print(f"  Sin fecha 'Received':             {missing_received:>6} ({100*missing_received/total:.1f}%)")
    print(f"  Sin afiliación extraída:          {missing_affil:>6} ({100*missing_affil/total:.1f}%)")
    print(f"  Abstracts en meetings cancelados: {canceled_count:>6}")
    print("=" * 60 + "\n")

    return {
        "total": total,
        "unknown_country": int(unknown_country),
        "pct_unknown": round(100 * unknown_country / total, 1),
        "missing_received": int(missing_received),
        "missing_affil": int(missing_affil),
        "canceled_count": int(canceled_count),
    }


# ---------------------------------------------------------------------------
# INDICADORES
# ---------------------------------------------------------------------------

def compute_indicators(df: pd.DataFrame) -> dict:
    """Calcula los tres indicadores del tablero."""

    # Indicador 1: Total de abstracts por meeting (solo no cancelados)
    active = df[~df["canceled"]]
    by_meeting = active.groupby("meeting_num").size().reset_index(name="n")
    ind1 = by_meeting.set_index("meeting_num")["n"].to_dict()

    # Indicador 2: Tasa de participación internacional por meeting
    # (abstracts con country != "United States" y != "unknown")
    def intl_rate(group):
        intl = (group["country"] != "United States") & (group["country"] != "unknown")
        return round(100 * intl.sum() / len(group), 1) if len(group) > 0 else 0.0

    intl_by_meeting = active.groupby("meeting_num").apply(intl_rate).to_dict()

    # Indicador 3: Concentración temática (Top-3 MSC / total abstracts del meeting)
    def top3_share(group):
        counts = group["msc_code"].value_counts()
        top3 = counts.head(3).sum()
        return round(100 * top3 / len(group), 1) if len(group) > 0 else 0.0

    top3_by_meeting = active.groupby("meeting_num").apply(top3_share).to_dict()

    # Consolidado
    total_active = len(active)
    total_intl = ((active["country"] != "United States") & (active["country"] != "unknown")).sum()
    intl_rate_global = round(100 * total_intl / total_active, 1) if total_active > 0 else 0.0

    top3_global = active["msc_code"].value_counts().head(3).sum()
    top3_share_global = round(100 * top3_global / total_active, 1) if total_active > 0 else 0.0

    return {
        "by_meeting_counts":      ind1,
        "intl_rate_by_meeting":   intl_by_meeting,
        "top3_share_by_meeting":  top3_by_meeting,
        "total_active":           total_active,
        "intl_rate_global":       intl_rate_global,
        "top3_share_global":      top3_share_global,
    }


# ---------------------------------------------------------------------------
# HALLAZGO PRINCIPAL
# ---------------------------------------------------------------------------

def compute_finding(df: pd.DataFrame) -> str:
    active = df[~df["canceled"]]
    jmm = active[active["meeting_num"] == 1154]
    rest = active[active["meeting_num"] != 1154]

    if jmm.empty or rest.empty:
        return "No hay datos suficientes para comparar meetings."

    def intl_rate(g):
        return 100 * ((g["country"] != "United States") & (g["country"] != "unknown")).sum() / len(g)

    jmm_rate = round(intl_rate(jmm), 1)
    rest_rate = round(intl_rate(rest), 1)

    top_jmm = jmm["msc_code"].value_counts().idxmax()
    top_jmm_label = MSC2010_LABELS.get(top_jmm, top_jmm)
    top_jmm_pct = round(100 * jmm["msc_code"].value_counts().max() / len(jmm), 1)

    top_rest = rest["msc_code"].value_counts().idxmax()
    top_rest_label = MSC2010_LABELS.get(top_rest, top_rest)
    top_rest_pct = round(100 * rest["msc_code"].value_counts().max() / len(rest), 1)

    return (
        f"La JMM Denver 2020 (meeting 1154) concentró el {top_jmm_pct}% de sus "
        f"abstracts en el área <em>{top_jmm} {top_jmm_label}</em> y registró una "
        f"participación internacional del {jmm_rate}%. En contraste, los meetings "
        f"virtuales post-COVID (1159–1162) mostraron su mayor concentración en "
        f"<em>{top_rest} {top_rest_label}</em> ({top_rest_pct}%) con una tasa "
        f"internacional del {rest_rate}%."
    )


# ---------------------------------------------------------------------------
# GRÁFICOS
# ---------------------------------------------------------------------------

PALETTE = matplotlib.colormaps["tab20"]

def fig_msc_consolidado(df: pd.DataFrame) -> str:
    """Gráfico 1: Top-20 códigos MSC2010 consolidados (todos los meetings activos)."""
    active = df[~df["canceled"]]
    counts = (
        active.groupby(["msc_code", "msc_label"])
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
        .head(20)
    )
    counts["etiqueta"] = counts["msc_code"] + " " + counts["msc_label"]
    counts = counts.sort_values("n")

    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(counts["etiqueta"], counts["n"],
                   color=[PALETTE(i / len(counts)) for i in range(len(counts))],
                   edgecolor="white", linewidth=0.5)
    ax.bar_label(bars, padding=3, fontsize=8)
    ax.set_xlabel("Número de abstracts", fontsize=10)
    ax.set_title("Top 20 áreas MSC2010 — Vol. 41 (meetings activos)", fontsize=12, pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=8)
    plt.tight_layout()
    fname = "msc_consolidado.png"
    fig.savefig(GRAFICOS_DIR / fname, dpi=150)
    plt.close(fig)
    print(f"  Guardado: {fname}")
    return fname


def fig_msc_por_meeting(df: pd.DataFrame) -> str:
    """Gráfico 2: Top-10 MSC por meeting (subplots), solo meetings activos."""
    active = df[~df["canceled"]]
    meetings = sorted(active["meeting_num"].unique())
    ncols = 3
    nrows = -(-len(meetings) // ncols)  # ceil division

    fig, axes = plt.subplots(nrows, ncols, figsize=(14, 4 * nrows))
    axes = axes.flatten()

    meeting_meta = {
        1154: "Denver, ene 2020",
        1159: "El Paso, sep 2020",
        1160: "State College, oct 2020",
        1161: "Chattanooga, oct 2020",
        1162: "Salt Lake City, oct 2020",
    }

    for i, m in enumerate(meetings):
        ax = axes[i]
        sub = active[active["meeting_num"] == m]
        counts = (
            sub.groupby(["msc_code", "msc_label"])
            .size()
            .reset_index(name="n")
            .sort_values("n", ascending=False)
            .head(10)
        )
        counts["etiqueta"] = counts["msc_code"] + " " + counts["msc_label"]
        counts = counts.sort_values("n")
        colors = [PALETTE(j / max(len(counts), 1)) for j in range(len(counts))]
        bars = ax.barh(counts["etiqueta"], counts["n"],
                       color=colors, edgecolor="white", linewidth=0.4)
        ax.bar_label(bars, padding=2, fontsize=7)
        subtitle = meeting_meta.get(m, "")
        ax.set_title(f"Meeting {m}\n{subtitle}", fontsize=9, pad=6)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="y", labelsize=7)
        ax.tick_params(axis="x", labelsize=7)

    # Ocultar ejes sobrantes
    for j in range(len(meetings), len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("Top 10 áreas MSC2010 por meeting (Vol. 41)", fontsize=13, y=1.01)
    plt.tight_layout()
    fname = "msc_por_meeting.png"
    fig.savefig(GRAFICOS_DIR / fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Guardado: {fname}")
    return fname


def fig_paises_consolidado(df: pd.DataFrame) -> str:
    """Gráfico 3: Top-15 países (todos los meetings activos)."""
    active = df[~df["canceled"]]
    counts = active["country"].value_counts().head(15)

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = [PALETTE(i / len(counts)) for i in range(len(counts))]
    bars = ax.bar(counts.index, counts.values, color=colors,
                  edgecolor="white", linewidth=0.5)
    ax.bar_label(bars, padding=3, fontsize=8)
    ax.set_ylabel("Número de abstracts", fontsize=10)
    ax.set_title("Top 15 países de afiliación — Vol. 41 (meetings activos)", fontsize=12, pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    plt.xticks(rotation=35, ha="right", fontsize=8)
    plt.tight_layout()
    fname = "paises_consolidado.png"
    fig.savefig(GRAFICOS_DIR / fname, dpi=150)
    plt.close(fig)
    print(f"  Guardado: {fname}")
    return fname


def fig_paises_por_meeting(df: pd.DataFrame) -> str:
    """Gráfico 4: Barras apiladas de país por meeting (activos)."""
    active = df[~df["canceled"]]
    top_countries = active["country"].value_counts().head(6).index.tolist()

    def categorize(c):
        if c in top_countries:
            return c
        if c == "unknown":
            return "Desconocido"
        return "Otros"

    active = active.copy()
    active["country_cat"] = active["country"].map(categorize)

    pivot = (
        active.groupby(["meeting_num", "country_cat"])
        .size()
        .unstack(fill_value=0)
    )

    # Ordenar columnas: top_countries primero, luego Otros, Desconocido
    ordered_cols = (
        [c for c in top_countries if c in pivot.columns]
        + [c for c in ["Otros", "Desconocido"] if c in pivot.columns]
    )
    pivot = pivot[ordered_cols]

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = [PALETTE(i / len(ordered_cols)) for i in range(len(ordered_cols))]
    pivot.plot(kind="bar", stacked=True, ax=ax, color=colors,
               edgecolor="white", linewidth=0.4)
    ax.set_xlabel("Meeting", fontsize=10)
    ax.set_ylabel("Número de abstracts", fontsize=10)
    ax.set_title("Distribución de país de afiliación por meeting (Vol. 41)", fontsize=12, pad=12)
    ax.legend(title="País", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    plt.xticks(rotation=0, fontsize=9)
    plt.tight_layout()
    fname = "paises_por_meeting.png"
    fig.savefig(GRAFICOS_DIR / fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Guardado: {fname}")
    return fname


def fig_tasa_internacional(df: pd.DataFrame) -> str:
    """Gráfico 5: Tasa de participación internacional por meeting."""
    active = df[~df["canceled"]]
    meetings = sorted(active["meeting_num"].unique())
    rates = []
    for m in meetings:
        g = active[active["meeting_num"] == m]
        intl = ((g["country"] != "United States") & (g["country"] != "unknown")).sum()
        rates.append(round(100 * intl / len(g), 1))

    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ["#2196F3" if r < 15 else "#4CAF50" for r in rates]
    bars = ax.bar([str(m) for m in meetings], rates, color=colors,
                  edgecolor="white", linewidth=0.5)
    ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)
    ax.set_ylim(0, max(rates) * 1.25 + 5)
    ax.set_xlabel("Meeting", fontsize=10)
    ax.set_ylabel("% abstracts internacionales", fontsize=10)
    ax.set_title("Tasa de participación internacional por meeting", fontsize=12, pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    plt.tight_layout()
    fname = "tasa_internacional.png"
    fig.savefig(GRAFICOS_DIR / fname, dpi=150)
    plt.close(fig)
    print(f"  Guardado: {fname}")
    return fname


def fig_abstracts_por_meeting(df: pd.DataFrame) -> str:
    """Gráfico 6: Número de abstracts por meeting (activos vs cancelados)."""
    by_m = df.groupby(["meeting_num", "canceled"]).size().reset_index(name="n")

    active_df = by_m[~by_m["canceled"]]
    cancel_df = by_m[by_m["canceled"]]

    fig, ax = plt.subplots(figsize=(9, 4))
    x_active = [str(m) for m in active_df["meeting_num"]]
    x_cancel = [str(m) for m in cancel_df["meeting_num"]]

    bars1 = ax.bar(x_active, active_df["n"], color="#4CAF50",
                   label="Presentados", edgecolor="white")
    bars2 = ax.bar(x_cancel, cancel_df["n"], color="#FF7043",
                   label="Cancelados (COVID-19)", edgecolor="white")
    ax.bar_label(bars1, padding=3, fontsize=8)
    ax.bar_label(bars2, padding=3, fontsize=8)
    ax.set_xlabel("Meeting", fontsize=10)
    ax.set_ylabel("Número de abstracts", fontsize=10)
    ax.set_title("Abstracts por meeting — Vol. 41 (verde = presentado, rojo = cancelado)", fontsize=11, pad=12)
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    fname = "abstracts_por_meeting.png"
    fig.savefig(GRAFICOS_DIR / fname, dpi=150)
    plt.close(fig)
    print(f"  Guardado: {fname}")
    return fname


def fig_diversidad_msc(df: pd.DataFrame) -> str:
    """Gráfico 7: Número de códigos MSC únicos por meeting."""
    active = df[~df["canceled"]]
    diversidad = (
        active.groupby("meeting_num")["msc_code"]
        .nunique()
        .reset_index(name="n_unique_msc")
        .sort_values("meeting_num")
    )

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(
        diversidad["meeting_num"].astype(str),
        diversidad["n_unique_msc"],
        color="#7E57C2", edgecolor="white"
    )
    ax.bar_label(bars, padding=3, fontsize=9)
    ax.set_xlabel("Meeting", fontsize=10)
    ax.set_ylabel("Áreas MSC únicas", fontsize=10)
    ax.set_title("Diversidad temática: áreas MSC2010 únicas por meeting", fontsize=12, pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    fname = "diversidad_msc.png"
    fig.savefig(GRAFICOS_DIR / fname, dpi=150)
    plt.close(fig)
    print(f"  Guardado: {fname}")
    return fname


# ---------------------------------------------------------------------------
# GENERACIÓN DE HTML
# ---------------------------------------------------------------------------

MEETING_META = {
    1154: ("Denver, CO",          "15–18 ene 2020", "Joint Mathematics Meetings",          False),
    1155: ("Charlottesville, VA", "13–15 mar 2020", "Spring Eastern Sectional",            True),
    1156: ("Medford, MA",         "21–22 mar 2020", "Spring Eastern Sectional",            True),
    1157: ("West Lafayette, IN",  "4–5 abr 2020",   "Spring Central Sectional",            True),
    1158: ("Fresno, CA",          "2–3 may 2020",   "Spring Western Sectional",            True),
    1159: ("El Paso, TX (virtual)","12–13 sep 2020", "Fall Central Virtual Sectional",     False),
    1160: ("State College, PA (virtual)","3–4 oct 2020","Fall Eastern Virtual Sectional",  False),
    1161: ("Chattanooga, TN (virtual)","10–11 oct 2020","Fall Southeastern Virtual Sectional",False),
    1162: ("Salt Lake City, UT (virtual)","24–25 oct 2020","Fall Western Virtual Sectional",False),
}


def build_html(df: pd.DataFrame, qv: dict, indicators: dict, finding: str,
               graph_files: list[str]) -> str:
    """Genera el HTML completo del tablero."""

    total_all = len(df)
    total_active = indicators["total_active"]
    total_canceled = qv["canceled_count"]

    # Tabla de meetings
    meeting_rows = []
    all_meetings = sorted(df["meeting_num"].unique())
    for m in all_meetings:
        meta = MEETING_META.get(m, (str(m), "", "", False))
        place, dates, name, cov = meta
        count = len(df[df["meeting_num"] == m])
        flag = '<span class="badge badge-covid">Cancelado COVID-19</span>' if cov else ""
        intl_r = indicators["intl_rate_by_meeting"].get(m, "—")
        top3_s = indicators["top3_share_by_meeting"].get(m, "—")
        intl_str = f"{intl_r}%" if isinstance(intl_r, float) else "—"
        top3_str = f"{top3_s}%" if isinstance(top3_s, float) else "—"
        meeting_rows.append(
            f"<tr><td>{m}</td><td>{name}</td><td>{place}</td><td>{dates}</td>"
            f"<td>{count}</td><td>{intl_str}</td><td>{top3_str}</td>"
            f"<td>{flag}</td></tr>"
        )
    meeting_table = "\n".join(meeting_rows)

    # Tarjetas de indicadores (tres)
    ind_a = f"{total_active:,}"
    ind_b = f"{indicators['intl_rate_global']}%"
    ind_c = f"{indicators['top3_share_global']}%"

    # Gráficos — rutas relativas desde docs/proyectos/AMS41-01/
    def img_tag(fname, alt, caption):
        return (
            f'<figure class="chart">'
            f'<img src="graficos/{fname}" alt="{alt}" loading="lazy">'
            f'<figcaption>{caption}</figcaption>'
            f'</figure>'
        )

    graphs_html = ""
    graph_meta = {
        "msc_consolidado.png":    ("Top 20 áreas MSC2010 consolidadas",
                                   "Distribución consolidada de los 20 códigos MSC2010 más frecuentes en todos los meetings activos del volumen 41."),
        "msc_por_meeting.png":    ("Top 10 MSC2010 por meeting",
                                   "Los 10 códigos MSC2010 más frecuentes en cada meeting activo. Permite comparar el perfil temático meeting a meeting."),
        "paises_consolidado.png": ("Top 15 países de afiliación",
                                   "Países más frecuentes en las afiliaciones de los abstracts activos. País derivado heurísticamente del texto de afiliación."),
        "paises_por_meeting.png": ("Países por meeting (barras apiladas)",
                                   "Distribución de países de afiliación por meeting. Los colores representan los 6 países más frecuentes; el resto se agrupa en 'Otros'."),
        "tasa_internacional.png": ("Tasa de participación internacional por meeting",
                                   "Porcentaje de abstracts cuya afiliación corresponde a una institución fuera de EE. UU."),
        "abstracts_por_meeting.png": ("Abstracts por meeting: presentados vs cancelados",
                                      "Meetings en verde fueron presentados; en rojo fueron cancelados por la pandemia de COVID-19."),
        "diversidad_msc.png":     ("Diversidad temática por meeting",
                                   "Número de códigos MSC2010 únicos registrados en cada meeting activo. Refleja la amplitud temática del programa."),
    }

    for fname in graph_files:
        if fname in graph_meta:
            alt, caption = graph_meta[fname]
            graphs_html += img_tag(fname, alt, caption) + "\n"

    # Limitaciones
    limitations = [
        f"La afiliación analizada corresponde al bloque de texto del abstract completo, "
        f"no necesariamente a cada autor por separado. Cuando hay múltiples autores con "
        f"distintas instituciones, el país asignado refleja la afiliación más prominente "
        f"en el texto.",
        f"La detección de país es heurística (reglas + abreviaturas de estados de EE.&nbsp;UU. "
        f"+ palabras clave). El {qv['pct_unknown']}% de los abstracts ({qv['unknown_country']}) "
        f"quedó clasificado como <em>unknown</em>.",
        f"Los abstracts de los meetings 1155–1158 aparecen publicados en el volumen 41 pero "
        f"<strong>no fueron presentados</strong> (reuniones canceladas por COVID-19). "
        f"Están excluidos de todos los indicadores y gráficos, pero se incluyen en la tabla.",
        f"pypdf extrae texto plano sin estructura de columnas. Fórmulas LaTeX y caracteres "
        f"especiales pueden fragmentar nombres, afiliaciones o títulos.",
        f"El volumen 41 cubre exclusivamente el año 2020. Los resultados no son comparables "
        f"con otros volúmenes sin normalizar por número de meetings y sesiones.",
        f"{qv['missing_received']} abstracts no tienen fecha \u201cReceived\u201d parseable.",
    ]
    lim_items = "\n".join(f"<li>{l}</li>" for l in limitations)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Abstracts AMS Vol. 41 — Tablero</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Segoe UI", Arial, sans-serif;
      background: #f5f6fa;
      color: #222;
      line-height: 1.6;
    }}
    header {{
      background: #1a237e;
      color: #fff;
      padding: 2rem 2.5rem 1.5rem;
    }}
    header h1 {{ font-size: 1.7rem; font-weight: 700; margin-bottom: .3rem; }}
    header p  {{ font-size: .95rem; opacity: .85; }}
    header a  {{ color: #90caf9; }}
    main {{ max-width: 1100px; margin: 2rem auto; padding: 0 1.5rem 3rem; }}
    h2 {{
      font-size: 1.2rem;
      font-weight: 700;
      margin: 2.2rem 0 .8rem;
      border-left: 4px solid #1a237e;
      padding-left: .7rem;
      color: #1a237e;
    }}
    /* TARJETAS */
    .cards {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }}
    .card {{
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,.1);
      padding: 1.2rem 1.5rem;
      flex: 1 1 200px;
      text-align: center;
    }}
    .card .value {{ font-size: 2rem; font-weight: 800; color: #1a237e; }}
    .card .label {{ font-size: .85rem; color: #555; margin-top: .2rem; }}
    /* TABLA */
    .table-wrap {{ overflow-x: auto; margin-top: .5rem; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: .88rem;
      background: #fff;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 1px 4px rgba(0,0,0,.08);
    }}
    th {{
      background: #1a237e;
      color: #fff;
      padding: .55rem .8rem;
      text-align: left;
      font-weight: 600;
    }}
    td {{ padding: .5rem .8rem; border-bottom: 1px solid #e8eaf6; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #e8eaf6; }}
    .badge-covid {{
      background: #ff7043;
      color: #fff;
      border-radius: 4px;
      padding: .15rem .5rem;
      font-size: .78rem;
      font-weight: 600;
    }}
    /* HALLAZGO */
    .finding {{
      background: #e8eaf6;
      border-left: 5px solid #3949ab;
      padding: 1rem 1.2rem;
      border-radius: 4px;
      font-size: .95rem;
    }}
    /* GRÁFICOS */
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
      gap: 1.5rem;
      margin-top: .5rem;
    }}
    figure.chart {{
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,.1);
      overflow: hidden;
    }}
    figure.chart img {{
      width: 100%;
      height: auto;
      display: block;
    }}
    figure.chart figcaption {{
      padding: .6rem .9rem;
      font-size: .82rem;
      color: #555;
      border-top: 1px solid #e8eaf6;
    }}
    /* LIMITACIONES */
    .limitations {{
      background: #fff8e1;
      border-left: 5px solid #ffa000;
      padding: 1rem 1.2rem;
      border-radius: 4px;
    }}
    .limitations ul {{ padding-left: 1.4rem; }}
    .limitations li {{ margin-bottom: .4rem; font-size: .9rem; }}
    footer {{
      text-align: center;
      font-size: .82rem;
      color: #888;
      padding: 1.5rem 0 2rem;
    }}
    footer a {{ color: #1a237e; }}
  </style>
</head>
<body>

<header>
  <h1>Abstracts of Papers Presented to the AMS — Vol. 41 (2020)</h1>
  <p>
    Análisis de los abstracts presentados en los meetings del volumen 41 (2020).
    Fuente: <a href="{FUENTE}" target="_blank" rel="noopener">{FUENTE}</a>
  </p>
</header>

<main>

  <!-- INDICADORES -->
  <h2>Indicadores</h2>
  <div class="cards">
    <div class="card">
      <div class="value">{ind_a}</div>
      <div class="label">Abstracts en meetings activos<br>(meetings 1154, 1159–1162)</div>
    </div>
    <div class="card">
      <div class="value">{ind_b}</div>
      <div class="label">Participación internacional<br>(afiliación fuera de EE.&nbsp;UU.)</div>
    </div>
    <div class="card">
      <div class="value">{ind_c}</div>
      <div class="label">Concentración en Top-3 MSC<br>(meetings activos, consolidado)</div>
    </div>
  </div>

  <!-- MEETINGS -->
  <h2>Meetings analizados</h2>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Meeting #</th>
          <th>Nombre</th>
          <th>Lugar</th>
          <th>Fechas</th>
          <th>Abstracts</th>
          <th>% Intl.</th>
          <th>Top-3 MSC</th>
          <th>Estado</th>
        </tr>
      </thead>
      <tbody>
        {meeting_table}
      </tbody>
    </table>
  </div>

  <!-- HALLAZGO -->
  <h2>Hallazgo principal</h2>
  <div class="finding">
    {finding}
  </div>

  <!-- GRÁFICOS -->
  <h2>Gráficos</h2>
  <div class="charts-grid">
    {graphs_html}
  </div>

  <!-- LIMITACIONES -->
  <h2>Limitaciones</h2>
  <div class="limitations">
    <ul>
      {lim_items}
    </ul>
  </div>

</main>

<footer>
  <p>
    Generado automáticamente con <code>analisis.py</code> ·
    Datos: <a href="{FUENTE}" target="_blank" rel="noopener">pubs.ams.org/ABS</a> ·
    No se publican filas individuales
  </p>
</footer>

</body>
</html>
"""
    return html


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 60)
    print("AMS Proceedings Vol. 41 — Análisis de abstracts")
    print("=" * 60)

    # 1. Cargar PDFs
    print("\n[1/5] Extrayendo texto de PDFs …")
    df = load_all_pdfs(PDF_FILES)

    # 2. Validación
    print("\n[2/5] Validando calidad de extracción …")
    qv = print_validation_report(df)

    # 3. Indicadores
    print("[3/5] Calculando indicadores …")
    indicators = compute_indicators(df)
    print(f"  Abstracts activos:      {indicators['total_active']}")
    print(f"  Tasa internacional:     {indicators['intl_rate_global']}%")
    print(f"  Top-3 MSC consolidado:  {indicators['top3_share_global']}%")

    # 4. Gráficos
    print("\n[4/5] Generando gráficos …")
    graph_files = []
    graph_files.append(fig_msc_consolidado(df))
    graph_files.append(fig_msc_por_meeting(df))
    graph_files.append(fig_paises_consolidado(df))
    graph_files.append(fig_paises_por_meeting(df))
    graph_files.append(fig_tasa_internacional(df))
    graph_files.append(fig_abstracts_por_meeting(df))
    graph_files.append(fig_diversidad_msc(df))

    # 5. HTML
    print("\n[5/5] Generando tablero HTML …")
    finding = compute_finding(df)
    html = build_html(df, qv, indicators, finding, graph_files)
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"  Guardado: {HTML_OUT}")

    print("\n" + "=" * 60)
    print("LISTO")
    print(f"  Tablero: {HTML_OUT}")
    print(f"  Gráficos ({len(graph_files)}): {GRAFICOS_DIR}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
