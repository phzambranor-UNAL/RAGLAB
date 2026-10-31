"""
analisis.py — Análisis de casos positivos de COVID-19 en Boyacá
================================================================
Fuente: Datos Abiertos Colombia
https://www.datos.gov.co/Salud-y-Protecci-n-Social/Casos-positivos-de-COVID-19-en-Colombia-/gt2j-8ykr/about_data

Genera dos gráficos en docs/proyectos/demo-covid/graficos/
y escribe docs/proyectos/demo-covid/index.html con el tablero.

Uso (desde la raíz del repositorio):
    conda activate RAGLAB
    python modulo-01/proyectos/demo-covid/analisis.py
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")           # renderizado sin pantalla
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ─────────────────────────────────────────────
# 0. RUTAS  (relativas a la raíz del repositorio)
# ─────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parents[3]   # …/RAGLAB
CSV_PATH   = ROOT / "modulo-01/proyectos/demo-covid/datos/casos_covid.csv"
GRAFICOS   = ROOT / "docs/proyectos/demo-covid/graficos"
HTML_OUT   = ROOT / "docs/proyectos/demo-covid/index.html"

GRAFICOS.mkdir(parents=True, exist_ok=True)

FUENTE_URL = (
    "https://www.datos.gov.co/Salud-y-Protecci-n-Social/"
    "Casos-positivos-de-COVID-19-en-Colombia-/gt2j-8ykr/about_data"
)

DEPARTAMENTO_FILTRO = "BOYACA"
COL_FECHA   = "Fecha de notificación"
COL_DEPT    = "Nombre departamento"
COL_ID      = "ID de caso"
COL_RECUP   = "Recuperado"
COL_MUERTE  = "Fecha de muerte"

# ─────────────────────────────────────────────
# 1. CARGA Y LIMPIEZA
# ─────────────────────────────────────────────
print("Cargando datos…")
if not CSV_PATH.exists():
    sys.exit(f"ERROR: No se encontró el archivo {CSV_PATH}")

df_raw = pd.read_csv(CSV_PATH, low_memory=False)

print(f"  Filas leídas: {len(df_raw):,}")
print(f"  Columnas:     {list(df_raw.columns)}")

# --- Verificar que realmente son datos de BOYACÁ ---
depts_encontrados = df_raw[COL_DEPT].unique().tolist()
otros = [d for d in depts_encontrados if d != DEPARTAMENTO_FILTRO]
if otros:
    print(f"  AVISO: se encontraron filas de otros departamentos: {otros}. Se filtrarán.")
    df = df_raw[df_raw[COL_DEPT] == DEPARTAMENTO_FILTRO].copy()
else:
    df = df_raw.copy()
    print(f"  Verificado: todas las filas son de {DEPARTAMENTO_FILTRO}.")

# --- Convertir fecha principal ---
df[COL_FECHA] = pd.to_datetime(df[COL_FECHA], errors="coerce")
filas_fecha_invalida = df[COL_FECHA].isna().sum()
if filas_fecha_invalida:
    print(f"  Eliminando {filas_fecha_invalida} fila(s) con '{COL_FECHA}' inválida.")
df.dropna(subset=[COL_FECHA], inplace=True)

# --- Eliminar duplicados por ID ---
dupes = df.duplicated(subset=[COL_ID]).sum()
if dupes:
    print(f"  Eliminando {dupes} fila(s) duplicada(s) por '{COL_ID}'.")
    df.drop_duplicates(subset=[COL_ID], keep="first", inplace=True)
else:
    print("  Sin duplicados por ID de caso.")

# --- Columnas derivadas ---
df["anio_mes"]     = df[COL_FECHA].dt.to_period("M")
df["anio_trim"]    = df[COL_FECHA].dt.to_period("Q")

# Convertir fecha de muerte para indicador 2
df[COL_MUERTE] = pd.to_datetime(df[COL_MUERTE], errors="coerce")
df["mes_muerte"] = df[COL_MUERTE].dt.to_period("M")

# Normalizar 'Recuperado' (quitar espacios)
df[COL_RECUP] = df[COL_RECUP].str.strip().fillna("Sin datos")

print(f"  Filas limpias finales: {len(df):,}")

# ─────────────────────────────────────────────
# 2. INDICADORES
# ─────────────────────────────────────────────

# -- Indicador 1: Evolución mensual de casos nuevos --
serie_mensual = (
    df.groupby("anio_mes")
    .size()
    .reset_index(name="casos_nuevos")
    .sort_values("anio_mes")
)
serie_mensual["casos_acumulados"] = serie_mensual["casos_nuevos"].cumsum()

periodo_inicio = str(serie_mensual["anio_mes"].iloc[0])
periodo_fin    = str(serie_mensual["anio_mes"].iloc[-1])
total_casos    = int(serie_mensual["casos_nuevos"].sum())
mes_pico       = str(serie_mensual.loc[serie_mensual["casos_nuevos"].idxmax(), "anio_mes"])
casos_pico     = int(serie_mensual["casos_nuevos"].max())

# -- Indicador 2: Tasa mensual de fallecidos reportados --
fallecidos_mes = (
    df[df[COL_MUERTE].notna()]
    .groupby("mes_muerte")
    .size()
    .reset_index(name="fallecidos")
)
fallecidos_mes.rename(columns={"mes_muerte": "anio_mes"}, inplace=True)

serie_con_fall = serie_mensual.merge(fallecidos_mes, on="anio_mes", how="left")
serie_con_fall["fallecidos"] = serie_con_fall["fallecidos"].fillna(0).astype(int)
serie_con_fall["tasa_letalidad_pct"] = (
    serie_con_fall["fallecidos"] / serie_con_fall["casos_nuevos"] * 100
).round(2)

total_fallecidos = int(serie_con_fall["fallecidos"].sum())
tasa_global      = round(total_fallecidos / total_casos * 100, 2)

# -- Distribución por resultado (Recuperado) --
dist_resultado = (
    df.groupby([COL_RECUP])
    .size()
    .reset_index(name="total")
    .sort_values("total", ascending=False)
)

print("\n=== INDICADORES ===")
print(f"  Departamento : {DEPARTAMENTO_FILTRO}")
print(f"  Periodo      : {periodo_inicio} → {periodo_fin}")
print(f"  Total casos  : {total_casos:,}")
print(f"  Mes pico     : {mes_pico} ({casos_pico:,} casos)")
print(f"  Total fallecidos reportados: {total_fallecidos:,}")
print(f"  Tasa de letalidad global   : {tasa_global}%")

# ─────────────────────────────────────────────
# 3. GRÁFICO 1 — Casos nuevos por mes (barras + línea acumulada)
# ─────────────────────────────────────────────
print("\nGenerando Gráfico 1…")

meses_str = [str(p) for p in serie_mensual["anio_mes"]]
x_pos     = range(len(meses_str))

fig1, ax1 = plt.subplots(figsize=(14, 5))
ax2 = ax1.twinx()

bars = ax1.bar(
    x_pos,
    serie_mensual["casos_nuevos"],
    color="#2196F3",
    alpha=0.75,
    label="Casos nuevos",
    zorder=2,
)
ax2.plot(
    x_pos,
    serie_mensual["casos_acumulados"],
    color="#E53935",
    linewidth=2,
    marker="o",
    markersize=3,
    label="Acumulados",
    zorder=3,
)

# Etiqueta en el mes pico
idx_pico = int(serie_mensual["casos_nuevos"].idxmax())
ax1.annotate(
    f"Pico: {casos_pico:,}",
    xy=(idx_pico, casos_pico),
    xytext=(idx_pico, casos_pico * 1.07),
    ha="center",
    fontsize=8,
    color="#1565C0",
    arrowprops=dict(arrowstyle="-", color="#1565C0", lw=0.8),
)

# Ejes y leyendas
step = max(1, len(meses_str) // 12)
ax1.set_xticks(list(x_pos)[::step])
ax1.set_xticklabels(meses_str[::step], rotation=45, ha="right", fontsize=7)
ax1.set_ylabel("Casos nuevos notificados", fontsize=9)
ax2.set_ylabel("Casos acumulados", fontsize=9, color="#E53935")
ax2.tick_params(axis="y", colors="#E53935")
ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
ax1.set_xlabel("Mes de notificación", fontsize=9)
ax1.set_title(
    f"COVID-19 en {DEPARTAMENTO_FILTRO}: casos nuevos y acumulados por mes de notificación\n"
    f"({periodo_inicio} – {periodo_fin})",
    fontsize=11,
    pad=10,
)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)

ax1.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
fig1.tight_layout()

G1_PATH = GRAFICOS / "grafico1_casos_mensuales.png"
fig1.savefig(G1_PATH, dpi=150, bbox_inches="tight")
plt.close(fig1)
print(f"  Guardado: {G1_PATH}")

# ─────────────────────────────────────────────
# 4. GRÁFICO 2 — Distribución de casos por resultado (estado final)
# ─────────────────────────────────────────────
print("Generando Gráfico 2…")

# Agrupar por trimestre y resultado para barras apiladas
pivot = (
    df.groupby(["anio_trim", COL_RECUP])
    .size()
    .unstack(fill_value=0)
)

# Colores por categoría
CATEGORIA_COLORES = {
    "Recuperado":  "#4CAF50",
    "Fallecido":   "#E53935",
    "Activo":      "#FF9800",
    "Sin datos":   "#9E9E9E",
}
cats_presentes = list(pivot.columns)
colores = [CATEGORIA_COLORES.get(c, "#78909C") for c in cats_presentes]

fig2, ax3 = plt.subplots(figsize=(14, 5))

bottom = [0] * len(pivot)
trims_str = [str(t) for t in pivot.index]

for cat, color in zip(cats_presentes, colores):
    vals = pivot[cat].values
    ax3.bar(trims_str, vals, bottom=bottom, label=cat, color=color, alpha=0.85)
    bottom = [b + v for b, v in zip(bottom, vals)]

ax3.set_xlabel("Trimestre de notificación", fontsize=9)
ax3.set_ylabel("Número de casos", fontsize=9)
ax3.set_title(
    f"COVID-19 en {DEPARTAMENTO_FILTRO}: distribución de casos por resultado\n"
    f"(por trimestre, {periodo_inicio} – {periodo_fin})",
    fontsize=11,
    pad=10,
)
ax3.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
ax3.legend(title="Resultado", fontsize=8, title_fontsize=8)
ax3.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
fig2.tight_layout()

G2_PATH = GRAFICOS / "grafico2_resultado_trimestral.png"
fig2.savefig(G2_PATH, dpi=150, bbox_inches="tight")
plt.close(fig2)
print(f"  Guardado: {G2_PATH}")

# ─────────────────────────────────────────────
# 5. HTML — Tablero estático
# ─────────────────────────────────────────────
print("Generando tablero HTML…")

LIMITACIONES = textwrap.dedent("""\
    <ul>
      <li>El CSV es un corte estático; no refleja correcciones o adiciones posteriores a la descarga.</li>
      <li><strong>Fecha de notificación</strong> es la fecha en que el caso ingresó al sistema,
          que puede ser posterior al contagio o diagnóstico real.</li>
      <li>La tasa de letalidad puede estar subestimada: algunas muertes se registran con rezago
          o en meses posteriores al caso original.</li>
      <li>El campo <em>Recuperado</em> no distingue entre alta clínica verificada y cierre
          administrativo por tiempo transcurrido (<em>Tipo de recuperación = Tiempo</em>).</li>
      <li>834 registros (0,6 %) no tienen <em>Fecha de inicio de síntomas</em>;
          ese campo no se usa en estos gráficos.</li>
    </ul>
""")

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>COVID-19 en {DEPARTAMENTO_FILTRO} — Tablero</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Segoe UI", system-ui, sans-serif;
      background: #f4f6f9;
      color: #222;
      line-height: 1.6;
    }}
    header {{
      background: #1565C0;
      color: #fff;
      padding: 1.5rem 2rem;
    }}
    header h1 {{ font-size: 1.5rem; font-weight: 700; }}
    header p  {{ font-size: 0.9rem; opacity: 0.85; margin-top: 0.25rem; }}
    main {{
      max-width: 1100px;
      margin: 2rem auto;
      padding: 0 1.5rem;
    }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }}
    .kpi {{
      background: #fff;
      border-radius: 8px;
      padding: 1.2rem 1.5rem;
      box-shadow: 0 1px 4px rgba(0,0,0,.1);
      border-left: 5px solid #1565C0;
    }}
    .kpi .valor  {{ font-size: 1.9rem; font-weight: 700; color: #1565C0; }}
    .kpi .etiq   {{ font-size: 0.78rem; color: #555; margin-top: 0.2rem; }}
    .kpi.rojo    {{ border-left-color: #E53935; }}
    .kpi.rojo .valor {{ color: #E53935; }}
    .grafico-card {{
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,.1);
      padding: 1.5rem;
      margin-bottom: 2rem;
    }}
    .grafico-card h2 {{
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 1rem;
      color: #1565C0;
    }}
    .grafico-card img {{
      width: 100%;
      height: auto;
      border-radius: 4px;
    }}
    .hallazgo {{
      background: #E3F2FD;
      border-left: 5px solid #1565C0;
      padding: 1rem 1.5rem;
      border-radius: 4px;
      margin-bottom: 2rem;
      font-size: 0.95rem;
    }}
    .hallazgo strong {{ color: #1565C0; }}
    .limites {{
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,.1);
      padding: 1.5rem;
      margin-bottom: 2rem;
      font-size: 0.87rem;
    }}
    .limites h2 {{
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 0.75rem;
      color: #555;
    }}
    .limites ul {{ padding-left: 1.4rem; color: #444; }}
    .limites li {{ margin-bottom: 0.4rem; }}
    footer {{
      text-align: center;
      font-size: 0.8rem;
      color: #888;
      padding: 1.5rem 0 2.5rem;
    }}
    footer a {{ color: #1565C0; }}
  </style>
</head>
<body>

<header>
  <h1>COVID-19 en {DEPARTAMENTO_FILTRO} — Tablero de seguimiento</h1>
  <p>Período: {periodo_inicio} – {periodo_fin} &nbsp;|&nbsp;
     Fuente: <a href="{FUENTE_URL}" target="_blank" rel="noopener"
                style="color:#90CAF9;">Datos Abiertos Colombia</a></p>
</header>

<main>

  <!-- KPIs -->
  <section class="kpis" aria-label="Indicadores clave">
    <div class="kpi">
      <div class="valor">{total_casos:,}</div>
      <div class="etiq">Casos positivos confirmados<br>(total del período)</div>
    </div>
    <div class="kpi">
      <div class="valor">{mes_pico}</div>
      <div class="etiq">Mes con más notificaciones<br>({casos_pico:,} casos)</div>
    </div>
    <div class="kpi rojo">
      <div class="valor">{total_fallecidos:,}</div>
      <div class="etiq">Fallecidos registrados<br>(con fecha de muerte)</div>
    </div>
    <div class="kpi rojo">
      <div class="valor">{tasa_global}%</div>
      <div class="etiq">Tasa de letalidad global<br>(fallecidos / casos notificados)</div>
    </div>
  </section>

  <!-- Hallazgo principal -->
  <div class="hallazgo" role="note">
    <strong>Hallazgo principal:</strong>
    En {DEPARTAMENTO_FILTRO} se registraron <strong>{total_casos:,}</strong> casos positivos
    entre {periodo_inicio} y {periodo_fin}.
    El pico de notificaciones ocurrió en <strong>{mes_pico}</strong> con
    <strong>{casos_pico:,}</strong> casos en un solo mes.
    De los {total_fallecidos:,} fallecidos con fecha registrada,
    la tasa de letalidad global fue de <strong>{tasa_global}%</strong>
    (ver nota de limitaciones sobre posible subestimación).
  </div>

  <!-- Gráfico 1 -->
  <div class="grafico-card">
    <h2>Gráfico 1 — Casos nuevos notificados por mes y evolución acumulada</h2>
    <img src="graficos/grafico1_casos_mensuales.png"
         alt="Barras de casos nuevos por mes con línea acumulada superpuesta"
         loading="lazy" />
  </div>

  <!-- Gráfico 2 -->
  <div class="grafico-card">
    <h2>Gráfico 2 — Distribución de casos por resultado final (por trimestre)</h2>
    <img src="graficos/grafico2_resultado_trimestral.png"
         alt="Barras apiladas del resultado de cada caso por trimestre"
         loading="lazy" />
  </div>

  <!-- Limitaciones -->
  <div class="limites">
    <h2>Limitaciones del análisis</h2>
    {LIMITACIONES}
  </div>

</main>

<footer>
  Datos: <a href="{FUENTE_URL}" target="_blank" rel="noopener">
    Casos positivos de COVID-19 en Colombia — Datos Abiertos Colombia
  </a>.
  Análisis generado con Python / pandas / matplotlib.
  No se publican filas individuales ni datos sensibles.
</footer>

</body>
</html>
"""

HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
HTML_OUT.write_text(html, encoding="utf-8")
print(f"  Guardado: {HTML_OUT}")

print("\n✓ Análisis completado.")
print(f"  Departamento : {DEPARTAMENTO_FILTRO}")
print(f"  Período      : {periodo_inicio} → {periodo_fin}")
print(f"  Casos totales: {total_casos:,}")
print(f"  Mes pico     : {mes_pico} ({casos_pico:,} casos)")
print(f"  Fallecidos   : {total_fallecidos:,}  |  Tasa letal.: {tasa_global}%")
print(f"\n  Tablero  → {HTML_OUT}")
print(f"  Gráfico1 → {G1_PATH}")
print(f"  Gráfico2 → {G2_PATH}")
