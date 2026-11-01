"""
analisis.py — Abstracts of Papers Presented to the AMS, Volume 41 (2020)
=========================================================================
Fuente: https://pubs.ams.org/ABS?active=all

Analiza los cuatro números del volumen 41:
  abs-41-01.pdf  → meeting 1154  (Joint Mathematics Meetings, Denver)
  abs-41-02.pdf  → meetings 1155-1158  (cancelados por COVID-19)
  abs-41-03.pdf  → meetings 1159-1160  (virtuales)
  abs-41-04.pdf  → meetings 1161-1162  (virtuales)

Uso (desde la raíz del repositorio):
    conda activate RAGLAB
    python modulo-01/proyectos/AMS41-01A/analisis.py

Salida:
    docs/proyectos/AMS41-01A/graficos/*.png
    docs/proyectos/AMS41-01A/index.html
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
HERE       = Path(__file__).resolve().parent          # …/AMS41-01A/
ROOT       = HERE.parents[2]                          # raíz del repositorio
DATOS_DIR  = HERE / "datos"
GRAF_DIR   = ROOT / "docs" / "proyectos" / "AMS41-01A" / "graficos"
HTML_OUT   = ROOT / "docs" / "proyectos" / "AMS41-01A" / "index.html"
FUENTE     = "https://pubs.ams.org/ABS?active=all"

GRAF_DIR.mkdir(parents=True, exist_ok=True)
HTML_OUT.parent.mkdir(parents=True, exist_ok=True)

PDF_FILES = [
    DATOS_DIR / "abs-41-01.pdf",
    DATOS_DIR / "abs-41-02.pdf",
    DATOS_DIR / "abs-41-03.pdf",
    DATOS_DIR / "abs-41-04.pdf",
]

CANCELED_MEETINGS = {1155, 1156, 1157, 1158}

# ── Etiquetas MSC 2010 (dos dígitos) ──────────────────────────────────────────
MSC_LABELS = {
    "00": "General",
    "01": "History & Biography",
    "03": "Mathematical Logic & Foundations",
    "05": "Combinatorics",
    "06": "Order, Lattices, Ordered Algebraic Structures",
    "08": "General Algebraic Systems",
    "11": "Number Theory",
    "12": "Field Theory & Polynomials",
    "13": "Commutative Algebra",
    "14": "Algebraic Geometry",
    "15": "Linear & Multilinear Algebra; Matrix Theory",
    "16": "Associative Rings & Algebras",
    "17": "Non-associative Rings & Algebras",
    "18": "Category Theory; Homological Algebra",
    "19": "K-Theory",
    "20": "Group Theory & Generalizations",
    "22": "Topological Groups, Lie Groups",
    "26": "Real Functions",
    "28": "Measure & Integration",
    "30": "Functions of a Complex Variable",
    "31": "Potential Theory",
    "32": "Several Complex Variables & Analytic Spaces",
    "33": "Special Functions",
    "34": "Ordinary Differential Equations",
    "35": "Partial Differential Equations",
    "37": "Dynamical Systems & Ergodic Theory",
    "39": "Difference & Functional Equations",
    "40": "Sequences, Series, Summability",
    "41": "Approximations & Expansions",
    "42": "Fourier Analysis",
    "43": "Abstract Harmonic Analysis",
    "44": "Integral Transforms, Operational Calculus",
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
    "58": "Global Analysis, Analysis on Manifolds",
    "60": "Probability Theory & Stochastic Processes",
    "62": "Statistics",
    "65": "Numerical Analysis",
    "68": "Computer Science",
    "70": "Mechanics of Particles & Systems",
    "74": "Mechanics of Deformable Solids",
    "76": "Fluid Mechanics",
    "78": "Optics, Electromagnetic Theory",
    "80": "Classical Thermodynamics, Heat Transfer",
    "81": "Quantum Theory",
    "82": "Statistical Mechanics, Structure of Matter",
    "83": "Relativity & Gravitational Theory",
    "85": "Astronomy & Astrophysics",
    "86": "Geophysics",
    "90": "Operations Research, Mathematical Programming",
    "91": "Game Theory, Economics, Social Sciences",
    "92": "Biology & Other Natural Sciences",
    "93": "Systems Theory; Control",
    "94": "Information & Communication, Circuits",
    "97": "Mathematics Education",
}

# Información de cada meeting
MEETING_META = {
    1154: ("Joint Mathematics Meetings",           "Denver, CO",                    "15–18 ene 2020", False),
    1155: ("Spring Eastern Sectional",             "Charlottesville, VA",           "13–15 mar 2020", True),
    1156: ("Spring Eastern Sectional",             "Medford, MA",                   "21–22 mar 2020", True),
    1157: ("Spring Central Sectional",             "West Lafayette, IN",            "4–5 abr 2020",   True),
    1158: ("Spring Western Sectional",             "Fresno, CA",                    "2–3 may 2020",   True),
    1159: ("Fall Central Virtual Sectional",       "El Paso, TX (virtual)",         "12–13 sep 2020", False),
    1160: ("Fall Eastern Virtual Sectional",       "State College, PA (virtual)",   "3–4 oct 2020",   False),
    1161: ("Fall Southeastern Virtual Sectional",  "Chattanooga, TN (virtual)",     "10–11 oct 2020", False),
    1162: ("Fall Western Virtual Sectional",       "Salt Lake City, UT (virtual)",  "24–25 oct 2020", False),
}

# ── Paleta de colores ──────────────────────────────────────────────────────────
CMAP20 = matplotlib.colormaps["tab20"]
CMAP10 = matplotlib.colormaps["tab10"]


# ══════════════════════════════════════════════════════════════════════════════
# EXTRACCIÓN
# ══════════════════════════════════════════════════════════════════════════════

def pdf_to_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


# Patrón de identificador de abstract
_RE_ID = re.compile(r"(?:^|\n)(\d{4})-(\d{2})-(\d+)\s+", re.MULTILINE)
# Fecha de recepción
_RE_RCV = re.compile(r"\(Received\s+([^)]{4,40})\)", re.IGNORECASE)
# Email
_RE_EMAIL = re.compile(r"[\w.+\-]+@[\w.\-]+\.[a-z]{2,}", re.IGNORECASE)
# Nombre propio antes de *
_RE_PRESENTER = re.compile(
    r"((?:[A-ZÁÉÍÓÚÜÑ\u00C0-\u024F][a-záéíóúüñ\u00C0-\u024F.\-]+\s+){1,5}"
    r"[A-ZÁÉÍÓÚÜÑ\u00C0-\u024F][a-záéíóúüñ\u00C0-\u024F.\-]+)\*"
)


def _extract_presenter_block(block: str):
    """
    Devuelve (presenter, presenter_email, affiliation_raw).

    El bloque de un abstract sigue este esquema:
        NNNN-CC-NNN  Nombre Apellido* (email@inst.edu), Departamento,
                     Universidad, Ciudad, ST NNNNN. Título del trabajo.
                     Cuerpo. (Received DATE)

    Estrategia:
    1. Presenter = nombre inmediatamente antes de *.
    2. Presenter email = primer email dentro del primer par de paréntesis
       tras el identificador.
    3. Affiliation raw = texto entre el cierre del primer paréntesis y el
       primer punto seguido de espacio+mayúscula (inicio del título),
       siempre que ese punto no forme parte del final de una abreviatura
       de estado (2 letras + punto).
    """
    presenter = ""
    pm = _RE_PRESENTER.search(block)
    if pm:
        presenter = pm.group(1).strip()

    # Email del presentador: primer email en el bloque
    emails_found = _RE_EMAIL.findall(block)
    presenter_email = emails_found[0] if emails_found else ""

    # Afiliación: entre cierre del primer ")" y primer ". [A-Z]"
    affil_raw = ""
    paren_close = block.find(")")
    if paren_close != -1:
        after = block[paren_close + 1:].strip().lstrip(",").strip()
        # Buscar fin de la afiliación: punto + espacio + mayúscula
        # Evitar falsos positivos con iniciales (una sola letra + punto)
        m = re.search(r'(?<![A-Z])\.\s+[A-Z]', after)
        if m:
            affil_raw = after[: m.start()].strip(" ,\n")
        else:
            # Sin título legible: tomar la primera línea
            affil_raw = after.split("\n")[0].strip(" ,")

    # Limpiar espacios múltiples y saltos embebidos
    affil_raw = re.sub(r"\s+", " ", affil_raw).strip(" .,")

    return presenter, presenter_email, affil_raw


def _normalize_institution(affil: str) -> str:
    """
    Extrae el nombre de la institución del texto de afiliación.
    Elimina el departamento inicial (si va seguido de coma+nombre de inst.),
    la ciudad, el estado y el código postal.

    Retorna el texto limpio o cadena vacía si no hay afiliación.
    """
    if not affil:
        return ""

    # Quitar código postal (5 dígitos, opcionalmente -4 dígitos)
    s = re.sub(r"\b\d{5}(?:-\d{4})?\b", "", affil)
    # Quitar abreviatura de estado EE. UU. al final o precedida de coma
    s = re.sub(r",?\s+[A-Z]{2}\s*$", "", s.strip())
    # Quitar ciudad si aparece duplicada (pattern "City, City, ST")
    parts = [p.strip() for p in s.split(",") if p.strip()]

    if not parts:
        return ""

    # Si la primera parte parece "Department of X" y hay más partes, omitirla
    first_low = parts[0].lower()
    dept_keywords = ("department", "dept", "division", "school of",
                     "college of", "faculty", "institute of", "program")
    if len(parts) > 1 and any(first_low.startswith(k) for k in dept_keywords):
        parts = parts[1:]

    # Tomar la primera parte restante como nombre de institución
    institution = parts[0].strip(" .,") if parts else ""

    # Limpiar espacios
    institution = re.sub(r"\s+", " ", institution).strip()
    return institution


def parse_pdf(pdf_path: Path) -> list[dict]:
    """Extrae todos los abstracts de un PDF y devuelve lista de dicts."""
    print(f"  Leyendo {pdf_path.name} …", flush=True)
    text = pdf_to_text(pdf_path)
    matches = list(_RE_ID.finditer(text))
    if not matches:
        print(f"    [ADVERTENCIA] No se encontraron abstracts en {pdf_path.name}")
        return []

    records = []
    for i, m in enumerate(matches):
        start = m.start()
        end   = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()

        meeting_num = int(m.group(1))
        msc_code    = m.group(2)
        talk_num    = int(m.group(3))
        abstract_id = f"{m.group(1)}-{msc_code}-{m.group(3)}"

        presenter, presenter_email, affil_raw = _extract_presenter_block(block)
        institution = _normalize_institution(affil_raw)

        rcv = _RE_RCV.search(block)
        received_date = rcv.group(1).strip() if rcv else ""

        records.append({
            "abstract_id":     abstract_id,
            "meeting_num":     meeting_num,
            "msc_code":        msc_code,
            "msc_label":       MSC_LABELS.get(msc_code, f"Código {msc_code}"),
            "talk_num":        talk_num,
            "presenter":       presenter,
            "presenter_email": presenter_email,
            "affiliation_raw": affil_raw,
            "institution":     institution,
            "received_date":   received_date,
            "issue_file":      pdf_path.name,
            "canceled":        meeting_num in CANCELED_MEETINGS,
        })

    print(f"    → {len(records)} abstracts extraídos")
    return records


def load_all() -> pd.DataFrame:
    all_records = []
    for p in PDF_FILES:
        if not p.exists():
            print(f"  [ERROR] No encontrado: {p}", file=sys.stderr)
            sys.exit(1)
        all_records.extend(parse_pdf(p))

    df = pd.DataFrame(all_records)
    df["msc_full"] = df["msc_code"] + " – " + df["msc_label"]
    return df


# ══════════════════════════════════════════════════════════════════════════════
# VALIDACIÓN
# ══════════════════════════════════════════════════════════════════════════════

def validate(df: pd.DataFrame) -> dict:
    n  = len(df)
    na = df[~df["canceled"]]

    missing_affil   = (df["institution"] == "").sum()
    missing_email   = (df["presenter_email"] == "").sum()
    missing_rcv     = (df["received_date"] == "").sum()
    n_canceled      = df["canceled"].sum()

    print("\n" + "=" * 58)
    print("REPORTE DE CALIDAD")
    print("=" * 58)
    print(f"  Total abstracts:                   {n:>6}")
    print(f"  Activos (meetings presentados):    {len(na):>6}")
    print(f"  Cancelados (COVID-19, 1155–1158):  {n_canceled:>6}")
    print(f"  Sin institución extraída:          {missing_affil:>6}  ({100*missing_affil/n:.1f}%)")
    print(f"  Sin email del presentador:         {missing_email:>6}  ({100*missing_email/n:.1f}%)")
    print(f"  Sin fecha 'Received':              {missing_rcv:>6}  ({100*missing_rcv/n:.1f}%)")
    print("=" * 58 + "\n")

    return {
        "n_total":         n,
        "n_active":        len(na),
        "n_canceled":      int(n_canceled),
        "pct_no_inst":     round(100 * missing_affil / n, 1),
        "pct_no_email":    round(100 * missing_email  / n, 1),
        "pct_no_rcv":      round(100 * missing_rcv    / n, 1),
        "n_no_inst":       int(missing_affil),
    }


# ══════════════════════════════════════════════════════════════════════════════
# INDICADORES
# ══════════════════════════════════════════════════════════════════════════════

def compute_indicators(df: pd.DataFrame) -> dict:
    active = df[~df["canceled"]]
    n_act  = len(active)

    # Indicador 1: total abstracts activos
    ind1 = n_act

    # Indicador 2: diversidad temática — códigos MSC únicos (total y por meeting)
    ind2_global = df["msc_code"].nunique()
    ind2_active = active["msc_code"].nunique()
    ind2_by_meeting = (
        active.groupby("meeting_num")["msc_code"]
        .nunique()
        .to_dict()
    )

    # Indicador 3: concentración institucional Top-5 (activos, institución no vacía)
    act_inst = active[active["institution"] != ""]
    if len(act_inst) > 0:
        top5_count = act_inst["institution"].value_counts().head(5).sum()
        ind3 = round(100 * top5_count / len(act_inst), 1)
    else:
        ind3 = None

    # Indicador 4: proporción de abstracts cancelados
    ind4 = round(100 * df["canceled"].sum() / len(df), 1)

    return {
        "ind1_total_active":    ind1,
        "ind2_msc_global":      int(ind2_global),
        "ind2_msc_active":      int(ind2_active),
        "ind2_by_meeting":      ind2_by_meeting,
        "ind3_top5_pct":        ind3,
        "ind4_canceled_pct":    ind4,
    }


# ══════════════════════════════════════════════════════════════════════════════
# HALLAZGOS
# ══════════════════════════════════════════════════════════════════════════════

def compute_findings(df: pd.DataFrame) -> list[str]:
    active = df[~df["canceled"]]
    finds  = []

    # Hallazgo 1: área MSC dominante en JMM vs. meetings virtuales
    jmm  = active[active["meeting_num"] == 1154]
    virt = active[active["meeting_num"].isin({1159, 1160, 1161, 1162})]

    if not jmm.empty and not virt.empty:
        top_jmm   = jmm["msc_code"].value_counts()
        top_virt  = virt["msc_code"].value_counts()
        c_jmm,  n_jmm  = top_jmm.idxmax(),  top_jmm.max()
        c_virt, n_virt = top_virt.idxmax(), top_virt.max()
        pct_jmm  = round(100 * n_jmm  / len(jmm),  1)
        pct_virt = round(100 * n_virt / len(virt), 1)
        lab_jmm  = MSC_LABELS.get(c_jmm,  c_jmm)
        lab_virt = MSC_LABELS.get(c_virt, c_virt)
        finds.append(
            f"<strong>Área dominante por tipo de evento.</strong> "
            f"En la JMM Denver (meeting 1154, presencial), el área más frecuente fue "
            f"<em>{c_jmm} {lab_jmm}</em> ({n_jmm} abstracts, {pct_jmm}% del total del meeting). "
            f"En los cuatro meetings virtuales post-COVID (1159–1162 agrupados), "
            f"el área más frecuente fue <em>{c_virt} {lab_virt}</em> "
            f"({n_virt} abstracts, {pct_virt}% del total de esos meetings)."
        )

    # Hallazgo 2: institución más activa en meetings activos
    act_inst = active[active["institution"] != ""]
    if not act_inst.empty:
        top_inst = act_inst["institution"].value_counts()
        inst1, cnt1 = top_inst.index[0], top_inst.iloc[0]
        pct1 = round(100 * cnt1 / len(act_inst), 1)
        finds.append(
            f"<strong>Institución más activa.</strong> "
            f"Considerando los abstracts con institución identificada en los meetings "
            f"presentados, <em>{inst1}</em> aparece en {cnt1} abstracts "
            f"({pct1}% del total con institución). "
            f"Nota: el nombre de institución proviene directamente del texto del PDF "
            f"y no está deduplicado; variantes ortográficas cuentan por separado."
        )

    # Hallazgo 3: diversidad temática JMM vs. meetings virtuales individuales
    if not jmm.empty and not virt.empty:
        div_jmm  = jmm["msc_code"].nunique()
        div_by_m = {
            m: active[active["meeting_num"] == m]["msc_code"].nunique()
            for m in [1159, 1160, 1161, 1162]
        }
        div_virt_str = ", ".join(
            f"meeting {m}: {v} áreas" for m, v in sorted(div_by_m.items())
        )
        finds.append(
            f"<strong>Diversidad temática: presencial vs. virtual.</strong> "
            f"La JMM Denver (meeting 1154) cubrió {div_jmm} áreas MSC2010 distintas, "
            f"lo que refleja su carácter de reunión nacional amplia. "
            f"Los meetings virtuales sectoriales mostraron menor diversidad: "
            f"{div_virt_str}. Esto es esperable dado que las reuniones seccionales "
            f"se enfocan en regiones geográficas y temáticas más acotadas."
        )

    return finds


# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICOS
# ══════════════════════════════════════════════════════════════════════════════

def _save(fig: plt.Figure, fname: str) -> str:
    path = GRAF_DIR / fname
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Guardado: {fname}")
    return fname


# ── Gráfico 1: Top-25 MSC consolidado, activos vs. cancelados ─────────────────
def g_msc_consolidado(df: pd.DataFrame) -> str:
    top = (
        df.groupby(["msc_code", "msc_label", "canceled"])
        .size()
        .reset_index(name="n")
    )
    # Top-25 por total
    order = (
        top.groupby("msc_code")["n"].sum()
        .sort_values(ascending=False)
        .head(25)
        .index
    )
    top = top[top["msc_code"].isin(order)].copy()
    top["etiqueta"] = top["msc_code"] + " " + top["msc_label"]

    # Pivotar
    pivot = (
        top.pivot_table(index="etiqueta", columns="canceled",
                        values="n", aggfunc="sum", fill_value=0)
        .rename(columns={False: "Activo", True: "Cancelado (COVID-19)"})
    )
    # Ordenar por total descendente
    pivot["_total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("_total").drop(columns="_total")
    pivot = pivot[[c for c in ["Activo", "Cancelado (COVID-19)"] if c in pivot.columns]]

    fig, ax = plt.subplots(figsize=(11, 9))
    colors = ["#1976D2", "#E57373"]
    pivot.plot(kind="barh", stacked=True, ax=ax,
               color=colors[:len(pivot.columns)], edgecolor="white", linewidth=0.4)
    ax.set_xlabel("Número de abstracts", fontsize=10)
    ax.set_title("Top 25 áreas MSC2010 — Vol. 41 completo\n(azul = meeting presentado  ·  rojo = cancelado COVID-19)",
                 fontsize=11, pad=10)
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=8)
    return _save(fig, "msc_consolidado.png")


# ── Gráfico 2: Top-10 MSC por meeting (subplots) ──────────────────────────────
def g_msc_por_meeting(df: pd.DataFrame) -> str:
    meetings = sorted(df["meeting_num"].unique())
    ncols = 3
    nrows = -(-len(meetings) // ncols)

    fig, axes = plt.subplots(nrows, ncols, figsize=(15, 4.5 * nrows))
    axes = axes.flatten()

    for i, m in enumerate(meetings):
        ax  = axes[i]
        sub = df[df["meeting_num"] == m]
        counts = (
            sub.groupby(["msc_code", "msc_label"])
            .size()
            .reset_index(name="n")
            .sort_values("n", ascending=False)
            .head(10)
        )
        counts["etiqueta"] = counts["msc_code"] + " " + counts["msc_label"]
        counts = counts.sort_values("n")
        meta = MEETING_META.get(m, (str(m), "", "", False))
        canceled = meta[3]
        color = "#E57373" if canceled else "#1976D2"
        bars = ax.barh(counts["etiqueta"], counts["n"],
                       color=color, edgecolor="white", linewidth=0.3)
        ax.bar_label(bars, padding=2, fontsize=7)
        suffix = "  ✗ COVID-19" if canceled else ""
        ax.set_title(f"Meeting {m}{suffix}\n{meta[1]}, {meta[2]}", fontsize=8, pad=5)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="both", labelsize=7)

    for j in range(len(meetings), len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("Top 10 áreas MSC2010 por meeting — Vol. 41",
                 fontsize=13, y=1.01)
    plt.tight_layout()
    return _save(fig, "msc_por_meeting.png")


# ── Gráfico 3: Top-20 instituciones (activos, institución no vacía) ───────────
def g_instituciones(df: pd.DataFrame) -> str:
    act = df[~df["canceled"] & (df["institution"] != "")]
    counts = act["institution"].value_counts().head(20).sort_values()

    fig, ax = plt.subplots(figsize=(11, 7))
    colors = [CMAP20(i / len(counts)) for i in range(len(counts))]
    bars = ax.barh(counts.index, counts.values, color=colors,
                   edgecolor="white", linewidth=0.4)
    ax.bar_label(bars, padding=3, fontsize=8)
    ax.set_xlabel("Número de abstracts del presentador", fontsize=10)
    ax.set_title("Top 20 instituciones del presentador — meetings activos Vol. 41\n"
                 "(nombre extraído del PDF, sin deduplicación de variantes)",
                 fontsize=11, pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=8)
    return _save(fig, "instituciones.png")


# ── Gráfico 4: Instituciones por meeting (Top-5 + Otros, barras apiladas) ─────
def g_instituciones_por_meeting(df: pd.DataFrame) -> str:
    active = df[~df["canceled"] & (df["institution"] != "")]
    top5 = active["institution"].value_counts().head(5).index.tolist()

    def cat(inst):
        return inst if inst in top5 else "Otras"

    active = active.copy()
    active["inst_cat"] = active["institution"].map(cat)

    pivot = (
        active.groupby(["meeting_num", "inst_cat"])
        .size()
        .unstack(fill_value=0)
    )
    cols = [c for c in top5 if c in pivot.columns] + (["Otras"] if "Otras" in pivot.columns else [])
    pivot = pivot[cols]

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = [CMAP10(i / len(cols)) for i in range(len(cols))]
    pivot.plot(kind="bar", stacked=True, ax=ax, color=colors,
               edgecolor="white", linewidth=0.3)
    ax.set_xlabel("Meeting", fontsize=10)
    ax.set_ylabel("Abstracts", fontsize=10)
    ax.set_title("Top-5 instituciones por meeting (activos) — Vol. 41",
                 fontsize=11, pad=10)
    ax.legend(title="Institución", bbox_to_anchor=(1.01, 1),
              loc="upper left", fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    plt.xticks(rotation=0, fontsize=9)
    return _save(fig, "instituciones_por_meeting.png")


# ── Gráfico 5: Barras apiladas MSC por meeting (activos) ──────────────────────
def g_msc_apilado(df: pd.DataFrame) -> str:
    active = df[~df["canceled"]]
    top8 = active["msc_code"].value_counts().head(8).index.tolist()

    def cat_msc(code):
        return code + " " + MSC_LABELS.get(code, code) if code in top8 else "Otros"

    active = active.copy()
    active["msc_cat"] = active["msc_code"].map(cat_msc)

    pivot = (
        active.groupby(["meeting_num", "msc_cat"])
        .size()
        .unstack(fill_value=0)
    )
    top8_labels = [c + " " + MSC_LABELS.get(c, c) for c in top8 if c + " " + MSC_LABELS.get(c, c) in pivot.columns]
    cols = top8_labels + (["Otros"] if "Otros" in pivot.columns else [])
    pivot = pivot[[c for c in cols if c in pivot.columns]]

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = [CMAP20(i / len(cols)) for i in range(len(cols))]
    pivot.plot(kind="bar", stacked=True, ax=ax, color=colors,
               edgecolor="white", linewidth=0.3)
    ax.set_xlabel("Meeting", fontsize=10)
    ax.set_ylabel("Abstracts", fontsize=10)
    ax.set_title("Composición temática MSC2010 por meeting (activos) — Vol. 41",
                 fontsize=11, pad=10)
    ax.legend(title="Área MSC2010", bbox_to_anchor=(1.01, 1),
              loc="upper left", fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    plt.xticks(rotation=0, fontsize=9)
    return _save(fig, "msc_apilado.png")


# ── Gráfico 6: Diversidad temática (códigos MSC únicos por meeting) ───────────
def g_diversidad(df: pd.DataFrame) -> str:
    active = df[~df["canceled"]]
    div = (
        active.groupby("meeting_num")["msc_code"]
        .nunique()
        .reset_index(name="n_msc")
        .sort_values("meeting_num")
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(div["meeting_num"].astype(str), div["n_msc"],
                  color="#7E57C2", edgecolor="white")
    ax.bar_label(bars, padding=3, fontsize=9)
    ax.set_xlabel("Meeting", fontsize=10)
    ax.set_ylabel("Áreas MSC2010 únicas", fontsize=10)
    ax.set_title("Diversidad temática: códigos MSC2010 únicos por meeting (activos)",
                 fontsize=11, pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    return _save(fig, "diversidad_msc.png")


# ── Gráfico 7: Abstracts por meeting (activos vs. cancelados) ─────────────────
def g_por_meeting(df: pd.DataFrame) -> str:
    counts = (
        df.groupby(["meeting_num", "canceled"])
        .size()
        .reset_index(name="n")
    )
    act = counts[~counts["canceled"]]
    can = counts[counts["canceled"]]

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(act["meeting_num"].astype(str), act["n"],
           color="#43A047", label="Presentado", edgecolor="white")
    ax.bar(can["meeting_num"].astype(str), can["n"],
           color="#E53935", label="Cancelado (COVID-19)", edgecolor="white")
    for _, row in pd.concat([act, can]).iterrows():
        ax.text(str(int(row["meeting_num"])), row["n"] + 3,
                str(int(row["n"])), ha="center", va="bottom", fontsize=8)
    ax.set_xlabel("Meeting", fontsize=10)
    ax.set_ylabel("Abstracts", fontsize=10)
    ax.set_title("Abstracts por meeting — Vol. 41 (verde = presentado  ·  rojo = cancelado)",
                 fontsize=11, pad=10)
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    return _save(fig, "abstracts_por_meeting.png")


# ══════════════════════════════════════════════════════════════════════════════
# HTML
# ══════════════════════════════════════════════════════════════════════════════

_GRAPH_META = {
    "msc_consolidado.png": (
        "Top 25 áreas MSC2010 — Vol. 41 completo",
        "Los 25 códigos MSC2010 más frecuentes en todo el volumen. "
        "Azul = meetings presentados; rojo = meetings cancelados por COVID-19."
    ),
    "msc_por_meeting.png": (
        "Top 10 áreas MSC2010 por meeting",
        "Los 10 temas más frecuentes en cada uno de los 9 meetings del volumen. "
        "Barras rojas indican meetings cancelados."
    ),
    "instituciones.png": (
        "Top 20 instituciones del presentador (meetings activos)",
        "Instituciones con más abstracts en los meetings efectivamente presentados. "
        "Nombre extraído del texto del PDF sin deduplicación de variantes ortográficas."
    ),
    "instituciones_por_meeting.png": (
        "Top-5 instituciones por meeting (activos, barras apiladas)",
        "Distribución de las 5 instituciones más frecuentes en cada meeting activo. "
        "El resto se agrupa como 'Otras'."
    ),
    "msc_apilado.png": (
        "Composición temática MSC2010 por meeting (activos)",
        "Los 8 códigos MSC2010 más frecuentes agrupados por meeting activo. "
        "Permite ver cómo varía el perfil temático entre eventos."
    ),
    "diversidad_msc.png": (
        "Diversidad temática por meeting (activos)",
        "Número de códigos MSC2010 únicos registrados en cada meeting activo. "
        "Refleja la amplitud temática del programa."
    ),
    "abstracts_por_meeting.png": (
        "Abstracts por meeting: presentados vs. cancelados",
        "Conteo de abstracts por meeting. Verde = presentado; "
        "rojo = cancelado por la pandemia de COVID-19."
    ),
}


def _img_tag(fname: str) -> str:
    alt, caption = _GRAPH_META.get(fname, (fname, ""))
    return (
        f'<figure class="chart">'
        f'<img src="graficos/{fname}" alt="{alt}" loading="lazy">'
        f'<figcaption>{caption}</figcaption>'
        f'</figure>\n'
    )


def build_html(df: pd.DataFrame, qv: dict, ind: dict,
               findings: list[str], graphs: list[str]) -> None:

    # ── Tabla de meetings ──────────────────────────────────────────────────────
    meeting_rows = []
    for m in sorted(df["meeting_num"].unique()):
        meta    = MEETING_META.get(m, (str(m), str(m), "", False))
        name, place, dates, canceled = meta
        n_total = len(df[df["meeting_num"] == m])
        n_msc   = df[df["meeting_num"] == m]["msc_code"].nunique()
        div_val = ind["ind2_by_meeting"].get(m, "—")
        flag    = ('<span class="badge-covid">Cancelado COVID-19</span>'
                   if canceled else
                   '<span class="badge-active">Presentado</span>')
        meeting_rows.append(
            f"<tr><td>{m}</td><td>{name}</td><td>{place}</td><td>{dates}</td>"
            f"<td>{n_total}</td>"
            f"<td>{n_msc if not canceled else div_val}</td>"
            f"<td>{flag}</td></tr>"
        )
    meeting_table = "\n".join(meeting_rows)

    # ── Indicadores ───────────────────────────────────────────────────────────
    ind3_str = f"{ind['ind3_top5_pct']}%" if ind["ind3_top5_pct"] is not None else "n/d"

    cards_html = f"""
    <div class="cards">
      <div class="card">
        <div class="value">{ind["ind1_total_active"]:,}</div>
        <div class="label">Abstracts en meetings<br>presentados</div>
      </div>
      <div class="card">
        <div class="value">{ind["ind2_msc_active"]}</div>
        <div class="label">Áreas MSC2010 únicas<br>(meetings activos)</div>
      </div>
      <div class="card">
        <div class="value">{ind3_str}</div>
        <div class="label">Abstracts en Top-5 inst.<br>(meetings activos)</div>
      </div>
      <div class="card">
        <div class="value">{ind["ind4_canceled_pct"]}%</div>
        <div class="label">Abstracts en meetings<br>cancelados (COVID-19)</div>
      </div>
    </div>"""

    # ── Hallazgos ─────────────────────────────────────────────────────────────
    findings_html = "\n".join(
        f'<div class="finding"><span class="finding-n">{i+1}</span>{f}</div>'
        for i, f in enumerate(findings)
    )

    # ── Gráficos ──────────────────────────────────────────────────────────────
    graphs_html = "".join(_img_tag(g) for g in graphs)

    # ── Limitaciones ──────────────────────────────────────────────────────────
    lims = [
        "La afiliación extraída corresponde únicamente al <strong>presentador</strong> "
        "(autor marcado con *). La afiliación de los co-autores no se puede separar "
        "con fiabilidad del texto plano cuando hay múltiples autores.",

        f"El nombre de institución se obtiene limpiando el texto libre de la afiliación. "
        f"No está estandarizado: la misma universidad puede aparecer con distintas grafías. "
        f"El script no aplica deduplicación. "
        f"{qv['n_no_inst']} abstracts ({qv['pct_no_inst']}%) no tienen institución extraída.",

        "Los abstracts de los meetings <strong>1155–1158</strong> fueron publicados en el "
        "volumen 41 pero <strong>no fueron presentados</strong> (reuniones canceladas por "
        "COVID-19). Se muestran en la tabla de meetings y en el gráfico consolidado con "
        "color rojo, pero se excluyen de los indicadores de meetings activos y de los "
        "gráficos de instituciones.",

        "<code>pypdf</code> extrae texto plano sin estructura de columnas. Fórmulas LaTeX, "
        "caracteres especiales y saltos de página pueden fragmentar nombres, afiliaciones "
        f"o títulos. {qv['pct_no_email']}% de los abstracts no tienen email del presentador "
        "parseable.",

        "El volumen 41 cubre exclusivamente el año 2020. Los resultados no son comparables "
        "con otros volúmenes sin normalizar por número de meetings y sesiones.",

        f"{qv['pct_no_rcv']}% de los abstracts no tienen fecha \u201cReceived\u201d "
        "parseable.",
    ]
    lims_html = "\n".join(f"<li>{l}</li>" for l in lims)

    # ── HTML completo ─────────────────────────────────────────────────────────
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
      background: #f5f6fa;
      color: #222;
      line-height: 1.6;
    }}
    header {{
      background: #0d47a1;
      color: #fff;
      padding: 2rem 2.5rem 1.4rem;
    }}
    header h1 {{ font-size: 1.65rem; font-weight: 700; margin-bottom: .3rem; }}
    header p  {{ font-size: .93rem; opacity: .85; }}
    header a  {{ color: #90caf9; }}
    main {{ max-width: 1120px; margin: 2rem auto; padding: 0 1.5rem 3rem; }}
    h2 {{
      font-size: 1.15rem; font-weight: 700;
      margin: 2.2rem 0 .75rem;
      border-left: 4px solid #0d47a1;
      padding-left: .7rem;
      color: #0d47a1;
    }}
    /* TARJETAS */
    .cards {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }}
    .card {{
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,.1);
      padding: 1.2rem 1.4rem;
      flex: 1 1 180px;
      text-align: center;
    }}
    .card .value {{ font-size: 1.9rem; font-weight: 800; color: #0d47a1; }}
    .card .label {{ font-size: .82rem; color: #555; margin-top: .2rem; }}
    /* TABLA */
    .table-wrap {{ overflow-x: auto; margin-top: .4rem; }}
    table {{
      width: 100%; border-collapse: collapse;
      font-size: .87rem; background: #fff;
      border-radius: 8px; overflow: hidden;
      box-shadow: 0 1px 4px rgba(0,0,0,.08);
    }}
    th {{
      background: #0d47a1; color: #fff;
      padding: .5rem .8rem; text-align: left; font-weight: 600;
    }}
    td {{ padding: .45rem .8rem; border-bottom: 1px solid #e3e8f0; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #e8eaf6; }}
    .badge-covid {{
      background: #e53935; color: #fff;
      border-radius: 4px; padding: .12rem .45rem;
      font-size: .76rem; font-weight: 600;
    }}
    .badge-active {{
      background: #43a047; color: #fff;
      border-radius: 4px; padding: .12rem .45rem;
      font-size: .76rem; font-weight: 600;
    }}
    /* HALLAZGOS */
    .finding {{
      background: #e8eaf6;
      border-left: 5px solid #3949ab;
      padding: .9rem 1.1rem;
      border-radius: 4px;
      font-size: .93rem;
      margin-bottom: .8rem;
      display: flex;
      gap: .8rem;
      align-items: flex-start;
    }}
    .finding-n {{
      background: #3949ab; color: #fff;
      border-radius: 50%; width: 1.6rem; height: 1.6rem;
      display: flex; align-items: center; justify-content: center;
      font-weight: 700; font-size: .85rem; flex-shrink: 0;
    }}
    /* GRÁFICOS */
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
      gap: 1.4rem;
      margin-top: .5rem;
    }}
    figure.chart {{
      background: #fff; border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,.1); overflow: hidden;
    }}
    figure.chart img {{ width: 100%; height: auto; display: block; }}
    figure.chart figcaption {{
      padding: .55rem .9rem; font-size: .81rem;
      color: #555; border-top: 1px solid #e3e8f0;
    }}
    /* LIMITACIONES */
    .limitations {{
      background: #fff8e1; border-left: 5px solid #f9a825;
      padding: .9rem 1.1rem; border-radius: 4px;
    }}
    .limitations ul {{ padding-left: 1.4rem; }}
    .limitations li {{ margin-bottom: .4rem; font-size: .89rem; }}
    footer {{
      text-align: center; font-size: .81rem;
      color: #888; padding: 1.5rem 0 2rem;
    }}
    footer a {{ color: #0d47a1; }}
  </style>
</head>
<body>

<header>
  <h1>Abstracts of Papers Presented to the AMS — Vol. 41 (2020)</h1>
  <p>
    Análisis de abstracts de los 9 meetings del volumen 41.
    Fuente: <a href="{FUENTE}" target="_blank" rel="noopener">{FUENTE}</a>
  </p>
</header>

<main>

  <h2>Indicadores</h2>
  {cards_html}

  <h2>Meetings analizados</h2>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Meeting #</th><th>Nombre</th><th>Lugar</th><th>Fechas</th>
          <th>Abstracts</th><th>Áreas MSC</th><th>Estado</th>
        </tr>
      </thead>
      <tbody>{meeting_table}</tbody>
    </table>
  </div>

  <h2>Hallazgos</h2>
  {findings_html}

  <h2>Gráficos</h2>
  <div class="charts-grid">
    {graphs_html}
  </div>

  <h2>Limitaciones</h2>
  <div class="limitations">
    <ul>{lims_html}</ul>
  </div>

</main>

<footer>
  <p>
    Generado con <code>analisis.py</code> ·
    Datos: <a href="{FUENTE}" target="_blank" rel="noopener">pubs.ams.org/ABS</a> ·
    No se publican filas individuales
  </p>
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
    print("\n" + "=" * 58)
    print("AMS Proceedings Vol. 41 — Análisis de abstracts (v2)")
    print("=" * 58)

    print("\n[1/5] Extrayendo texto de PDFs …")
    df = load_all()

    print("\n[2/5] Validando calidad …")
    qv = validate(df)

    print("[3/5] Calculando indicadores …")
    ind = compute_indicators(df)
    print(f"  Abstracts activos:           {ind['ind1_total_active']}")
    print(f"  Áreas MSC únicas (activos):  {ind['ind2_msc_active']}")
    print(f"  Conc. Top-5 instituciones:   {ind['ind3_top5_pct']}%")
    print(f"  % cancelados:                {ind['ind4_canceled_pct']}%")

    print("\n[4/5] Generando gráficos …")
    graphs = []
    graphs.append(g_msc_consolidado(df))
    graphs.append(g_msc_por_meeting(df))
    graphs.append(g_instituciones(df))
    graphs.append(g_instituciones_por_meeting(df))
    graphs.append(g_msc_apilado(df))
    graphs.append(g_diversidad(df))
    graphs.append(g_por_meeting(df))

    print("\n[5/5] Generando tablero HTML …")
    findings = compute_findings(df)
    build_html(df, qv, ind, findings, graphs)

    print("\n" + "=" * 58)
    print("LISTO")
    print(f"  Tablero : {HTML_OUT}")
    print(f"  Gráficos: {GRAF_DIR}  ({len(graphs)} archivos)")
    print("=" * 58 + "\n")


if __name__ == "__main__":
    main()
