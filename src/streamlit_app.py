"""
streamlit_app.py — Kartografi Sampul Sastra Indonesia 2000–2025
Deploy: HuggingFace Spaces → src/streamlit_app.py

Struktur repo:
  src/
    streamlit_app.py      ← file ini
    data.csv              ← gabungan semua modul (atau parsial)
  covers/                 ← folder gambar (Git LFS)
  requirements.txt

requirements.txt:
  streamlit>=1.32.0
  pandas>=2.0.0
  numpy>=1.24.0
  plotly>=5.18.0
  matplotlib>=3.7.0
  pillow>=10.0.0
"""

import os
import re
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kartografi Sampul Sastra Indonesia",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Path ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_PATH  = os.path.join(BASE_DIR, "data.csv")
COVERS_DIR = os.path.join(os.path.dirname(BASE_DIR), "covers")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Source+Sans+3:wght@300;400;600&display=swap');

/* ❌ HAPUS ini:
html, body, [class*="css"]
*/

/* ✅ Pakai ini saja */
body {
  font-family: 'Source Sans 3', sans-serif;
}

/* 🎯 Typography aman */
.hero-title {
  font-family: 'Playfair Display', serif;
  font-size: clamp(1.4rem, 2.5vw, 2rem);
  font-weight: 700;
  color: var(--text-color);
  line-height: 1.2;
  margin-bottom: 0.2rem;
}

.hero-sub { 
  font-size: 0.9rem; 
  color: rgba(128,128,128,0.8); 
}

.section-title {
  font-family: 'Playfair Display', serif;
  font-size: clamp(0.9rem, 2vw, 1.1rem);
  font-weight: 600;
  color: var(--text-color);
  border-bottom: 1px solid rgba(128,128,128,0.2);
  padding-bottom: 0.3rem;
}

/* 🎯 Card */
.stat-chip {
  background: rgba(240,240,240,0.1);
  border: 1px solid rgba(128,128,128,0.2);
  border-radius: 8px;
  padding: 0.5rem 1rem;
}

/* 🎯 Fix container biar nggak kepotong */
.block-container {
  padding-top: 1.5rem;
  padding-bottom: 2rem;
  max-width: 1200px;
}

/* 🎯 Fix overflow bug */
.main {
  overflow-x: hidden;
}

/* 🎯 Sidebar aman */
section[data-testid="stSidebar"] {
  background: var(--background-color);
}

</style>
""", unsafe_allow_html=True)

# ── Colour palettes ───────────────────────────────────────────────────────────
WARNA_HEX = {
    "merah":  "#ef4444", "biru":   "#3b82f6", "hijau":  "#22c55e",
    "kuning": "#eab308", "oranye": "#f97316", "ungu":   "#a855f7",
    "hitam":  "#374151", "putih":  "#d1d5db", "abu":    "#9ca3af",
}
GAYA_COLOR = {
    "photograph":    "#3b82f6", "hand_drawn":    "#ef4444",
    "abstract":      "#a855f7", "flat_graphic":  "#22c55e",
    "collage":       "#f97316", "text_dominant": "#14b8a6",
    "unknown":       "#d1d5db",
}
TYPEFACE_COLOR = {
    "serif":      "#1e40af", "sans-serif": "#0891b2",
    "slab-serif": "#b45309", "script":     "#be185d",
    "display":    "#7c3aed", "monospace":  "#15803d",
    "unknown":    "#9ca3af",
}
PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_family="Source Sans 3, sans-serif",
    margin=dict(t=28, b=28, l=16, r=16),
    showlegend=False,
)


# ── Load & normalise ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Memuat data…")
def load_data(path):
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str, low_memory=False)
    df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_")

    def _rating(v):
        if pd.isna(v) or str(v).strip() in ("", "nan", "N/A"):
            return np.nan
        v2 = re.sub(r"[^0-9.,]", "", str(v)).replace(",", ".")
        if not v2:
            return np.nan
        try:
            f = float(v2)
            return round(f / 100, 2) if f > 10 else round(f, 2)
        except Exception:
            return np.nan

    def _count(v):
        if pd.isna(v) or str(v).strip() in ("", "nan", "N/A"):
            return 0
        nums = re.sub(r"[^0-9.,]", "", str(v))
        if not nums:
            return 0
        if re.search(r"[,.]\d{3}($|[,.])", nums):
            nums = nums.replace(",", "").replace(".", "")
        elif "," in nums and "." not in nums:
            parts = nums.split(",")
            nums = nums.replace(",", "") if (len(parts) == 2 and len(parts[1]) == 3) \
                   else nums.replace(",", ".")
        elif "." in nums and "," not in nums:
            parts = nums.split(".")
            if len(parts) == 2 and len(parts[1]) == 3:
                nums = nums.replace(".", "")
        try:
            return int(float(nums))
        except Exception:
            return 0

    for col in ["RATING_AVG", "RATING", "AVERAGE_RATING"]:
        if col in df.columns:
            df[col] = df[col].apply(_rating)

    for col in ["TOTAL_RATING", "RATINGS_COUNT", "JUMLAH_RATING",
                "TOTAL_REVIEW", "REVIEWS_COUNT", "JUMLAH_REVIEW"]:
        if col in df.columns:
            df[col] = df[col].apply(_count)

    for col in ["TAHUN_TERBIT", "TAHUN", "YEAR"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    num_cols = [
        "BRIGHTNESS_MEAN", "SATURATION_MEAN", "TEKS_COVERAGE",
        "TYPEFACE_SKOR", "TYPEFACE_CONFIDENCE",
        "GAYA_SKOR", "YOLO_N_OBJEK", "DETR_OBJEK_N",
        "JUDUL_MATCH_SCORE", "HUE_DOMINANT",
    ] + [f"WARNA_PCT_{i}" for i in range(1, 6)] + \
      [f"WARNA_H_{i}" for i in range(1, 6)]

    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            if "PCT" in col:
                df[col] = df[col].fillna(0)

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].fillna("").astype(str).str.strip()

    return df


# ── Kolom kunci ───────────────────────────────────────────────────────────────
def detect_cols(df):
    return {
        "img":       next((c for c in ["NAMA_FILE_GAMBAR","IMAGE_FILE","GAMBAR","COVER"] if c in df.columns), None),
        "title":     next((c for c in ["JUDUL","TITLE","NAMA_BUKU"] if c in df.columns), None),
        "author":    next((c for c in ["PENULIS","AUTHOR","PENGARANG"] if c in df.columns), None),
        "year":      next((c for c in ["TAHUN_TERBIT","TAHUN","YEAR"] if c in df.columns), None),
        "genre":     next((c for c in ["GENRES","GENRE","KATEGORI"] if c in df.columns), None),
        "rating":    next((c for c in ["RATING_AVG","RATING","AVERAGE_RATING"] if c in df.columns), None),
        "n_rating":  next((c for c in ["TOTAL_RATING","RATINGS_COUNT","JUMLAH_RATING"] if c in df.columns), None),
        "publisher": next((c for c in ["PENERBIT","PUBLISHER"] if c in df.columns), None),
        "tf":        next((c for c in ["TYPEFACE_KATEGORI","FONT_KATEGORI"] if c in df.columns), None),
        "tf_skor":   next((c for c in ["TYPEFACE_SKOR","TYPEFACE_CONFIDENCE","FONT_CONFIDENCE"] if c in df.columns), None),
    }


# ── Modul availability ────────────────────────────────────────────────────────
def mod_ok(df, module):
    checks = {
        "A": ["WARNA_KATEGORI", "WARNA_1"],
        "B": ["TYPEFACE_KATEGORI", "FONT_KATEGORI"],
        "C": ["GAYA_ILUSTRASI"],
    }
    return any(c in df.columns for c in checks.get(module, []))


# ── Genre helpers ─────────────────────────────────────────────────────────────
def expand_genres(val):
    if not val or val in ("", "nan"):
        return []
    val = re.sub(r"\.\.\.more$", "", val).strip()
    return [g.strip() for g in re.split(r"[,;|/]", val) if g.strip()]

def get_all_genres(df, genre_col):
    if not genre_col:
        return []
    genres = set()
    for val in df[genre_col].dropna():
        for g in expand_genres(str(val)):
            if g and g != "nan":
                genres.add(g)
    return sorted(genres)

def filter_genre(df, genre_col, genre):
    if genre == "Semua" or not genre_col:
        return df
    return df[df[genre_col].apply(lambda v: genre in expand_genres(str(v)))]


# ── Misc helpers ──────────────────────────────────────────────────────────────
def star_rating(val):
    if pd.isna(val) or float(val) == 0:
        return ""
    v = float(val)
    full  = int(v)
    half  = 1 if (v - full) >= 0.5 else 0
    empty = 5 - full - half
    return "★" * full + "½" * half + "☆" * empty

def cover_path(fname):
    return os.path.join(COVERS_DIR, str(fname))

def palet_strip(row, k=5):
    parts = []
    for i in range(1, k + 1):
        hx  = row.get(f"WARNA_HEX_{i}", "") or "#d1d5db"
        pct = float(row.get(f"WARNA_PCT_{i}", 0) or 0)
        nm  = row.get(f"WARNA_{i}", "") or ""
        if pct > 0:
            parts.append(
                f'<div style="flex:{pct:.1f};background:{hx};height:5px;'
                f'margin:0 1px;border-radius:2px;" title="{nm} {pct:.0f}%"></div>'
            )
    return '<div style="display:flex;gap:0;margin-top:3px;">' + "".join(parts) + "</div>"

def simple_bar(series, color_map=None, orient="v", h=290):
    vc = series.value_counts().reset_index()
    vc.columns = ["lbl", "n"]
    vc["pct"] = (vc["n"] / vc["n"].sum() * 100).round(1)
    cm = color_map or {}
    if orient == "h":
        fig = px.bar(vc, y="lbl", x="n", orientation="h",
                     text="pct", color="lbl", color_discrete_map=cm,
                     labels={"n": "Jumlah", "lbl": ""})
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    else:
        fig = px.bar(vc, x="lbl", y="n",
                     text="pct", color="lbl", color_discrete_map=cm,
                     labels={"n": "Jumlah", "lbl": ""})
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(**PLOTLY_BASE, height=h)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#f3f4f6")
    return fig

def heatmap_genre_x_col(df, genre_col, col, scale="Blues", max_genre=14, min_n=5):
    genres = get_all_genres(df, genre_col)[:max_genre]
    heat = {}
    for g in genres:
        sub = filter_genre(df, genre_col, g)
        sub_valid = sub[sub[col].str.lower().isin(
            list(WARNA_HEX) + list(GAYA_COLOR) + list(TYPEFACE_COLOR)
        )] if col in sub.columns else sub
        if len(sub_valid) >= min_n:
            heat[g] = sub_valid[col].value_counts(normalize=True) * 100
    if not heat:
        return None
    hdf = pd.DataFrame(heat).fillna(0).T
    fig = px.imshow(hdf, color_continuous_scale=scale,
                    text_auto=".1f", labels={"color": "%"})
    fig.update_layout(**PLOTLY_BASE, height=max(300, len(heat) * 28 + 100),
                      coloraxis_showscale=False)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if not os.path.exists(DATA_PATH):
    st.error(f"File data tidak ditemukan: `{DATA_PATH}`")
    st.info("Letakkan `data.csv` di folder `src/` dan pastikan sudah berisi hasil analisis.")
    st.stop()

df_raw = load_data(DATA_PATH)
C = detect_cols(df_raw)
MA = mod_ok(df_raw, "A")
MB = mod_ok(df_raw, "B")
MC = mod_ok(df_raw, "C")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<p style="font-family:\'Playfair Display\',serif;font-size:1.05rem;'
        'font-weight:700;color:#1a1a2e;margin-bottom:0;">📚 Kartografi Sampul</p>'
        '<p style="font-size:0.72rem;color:#9ca3af;margin-top:1px;">'
        'Sastra Indonesia 2000–2025</p>',
        unsafe_allow_html=True,
    )

    # Status modul
    st.markdown('<div class="section-label" style="margin-top:0.6rem">Status Modul</div>',
                unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    for col_w, lbl, ok in [(m1, "Warna", MA), (m2, "Typeface", MB), (m3, "Ilustrasi", MC)]:
        col_w.markdown(
            f'<div style="text-align:center;font-size:0.68rem;">'
            f'{"✅" if ok else "⏳"}<br>{lbl}</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown('<div class="section-label">Navigasi</div>', unsafe_allow_html=True)
    PAGE = st.radio("", [
        "🗺️  Ringkasan",
        "🎨  Warna",
        "🔤  Typeface",
        "🖼️  Ilustrasi",
        "📊  Genre & Tren",
        "⭐  Rating & Agregat",
        "📖  Jelajah Buku",
    ], label_visibility="collapsed")

    st.divider()
    st.markdown('<div class="section-label">Filter Global</div>', unsafe_allow_html=True)

    all_genres = ["Semua"] + get_all_genres(df_raw, C["genre"]) if C["genre"] else ["Semua"]
    sel_genre = st.selectbox("Genre", all_genres)

    # Rentang tahun — hindari karakter em-dash langsung di f-string
    sel_year = (2000, 2025)
    if C["year"]:
        yv = df_raw[C["year"]][df_raw[C["year"]].between(1990, 2030)]
        if len(yv) > 0:
            y_min = int(yv.min())
            y_max = int(yv.max())
            sel_year = st.slider("Tahun terbit", y_min, y_max, (y_min, y_max))

    st.divider()
    st.markdown(
        '<div style="font-size:0.68rem;color:#9ca3af;line-height:1.7;">'
        '<b>Rujukan:</b><br>'
        'Arnold &amp; Tilton (2023) <i>Distant Viewing</i><br>'
        'Lupton (2024) <i>Thinking with Type</i><br>'
        'Genette (1997) <i>Paratexts</i><br>'
        'Manovich (2020) <i>Cultural Analytics</i>'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Filter df ─────────────────────────────────────────────────────────────────
df = filter_genre(df_raw, C["genre"], sel_genre)
if C["year"]:
    df = df[df[C["year"]].between(sel_year[0], sel_year[1])]
df = df.reset_index(drop=True)
N = len(df)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: RINGKASAN
# ═════════════════════════════════════════════════════════════════════════════
if "Ringkasan" in PAGE:
    st.markdown('<div class="hero-title">Kartografi Sampul Sastra Indonesia</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Pipeline komputasional: K-Means Warna · '
        'Typeface CLIP · YOLOv8 + DETR + CLIP Ilustrasi</div>',
        unsafe_allow_html=True,
    )

    # Stat chips
    yr_str = "—"
    if C["year"]:
        yv2 = df[C["year"]][df[C["year"]].between(1990, 2030)]
        if len(yv2) > 0:
            yr_str = str(int(yv2.min())) + chr(8211) + str(int(yv2.max()))

    n_g    = len(get_all_genres(df, C["genre"])) if C["genre"] else "—"
    rat_m  = ""
    if C["rating"]:
        rv = pd.to_numeric(df[C["rating"]], errors="coerce").dropna()
        rat_m = f"{rv.mean():.2f}" if len(rv) > 0 else "—"

    chips = [(str(N), "Buku"), (yr_str, "Tahun"), (str(n_g), "Genre"), (rat_m or "—", "Rating rata-rata")]
    st.markdown(
        '<div class="stat-row">' +
        "".join(f'<div class="stat-chip"><div class="num">{v}</div>'
                f'<div class="lbl">{l}</div></div>' for v, l in chips) +
        "</div>",
        unsafe_allow_html=True,
    )

    if not MA and not MB and not MC:
        st.markdown(
            '<div class="note-box">⏳ Analisis belum tersedia. '
            'Jalankan pipeline di Colab terlebih dahulu, lalu upload data.csv.</div>',
            unsafe_allow_html=True,
        )

    # Tiga distribusi
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="section-title">Warna Dominan</div>', unsafe_allow_html=True)
        if MA and "WARNA_KATEGORI" in df.columns:
            st.plotly_chart(simple_bar(df["WARNA_KATEGORI"], WARNA_HEX, h=270),
                            use_container_width=True, key="rs_a")
        else:
            st.caption("⏳ Modul A belum tersedia")
    with c2:
        st.markdown('<div class="section-title">Kategori Typeface</div>', unsafe_allow_html=True)
        if MB and C["tf"] and C["tf"] in df.columns:
            st.plotly_chart(simple_bar(df[C["tf"]], TYPEFACE_COLOR, h=270),
                            use_container_width=True, key="rs_b")
        else:
            st.caption("⏳ Modul B belum tersedia")
    with c3:
        st.markdown('<div class="section-title">Gaya Ilustrasi</div>', unsafe_allow_html=True)
        if MC and "GAYA_ILUSTRASI" in df.columns:
            st.plotly_chart(simple_bar(df["GAYA_ILUSTRASI"], GAYA_COLOR, orient="h", h=270),
                            use_container_width=True, key="rs_c")
        else:
            st.caption("⏳ Modul C belum tersedia")

    # Tren warna per tahun
    if MA and C["year"] and "WARNA_KATEGORI" in df.columns:
        st.markdown('<div class="section-title">Tren Warna Dominan per Tahun</div>',
                    unsafe_allow_html=True)
        df_tr = df[df[C["year"]].between(1990, 2030)]
        tren = df_tr.groupby([C["year"], "WARNA_KATEGORI"]).size().reset_index(name="n")
        fig_tr = px.area(tren, x=C["year"], y="n", color="WARNA_KATEGORI",
                         color_discrete_map=WARNA_HEX,
                         labels={C["year"]: "Tahun", "n": "Jumlah", "WARNA_KATEGORI": "Warna"})
        fig_tr.update_layout(**PLOTLY_BASE, showlegend=True,
                              legend=dict(orientation="h", y=-0.2), height=290)
        st.plotly_chart(fig_tr, use_container_width=True, key="rs_tren")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: WARNA
# ═════════════════════════════════════════════════════════════════════════════
elif "Warna" in PAGE:
    st.markdown('<div class="hero-title">Modul A — Analisis Warna</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">K-Means k=5 pada ruang warna HSV · '
        'Rujukan: Arnold &amp; Tilton (2023) <i>Distant Viewing</i></div>',
        unsafe_allow_html=True,
    )
    if not MA:
        st.info("⏳ Data Modul A belum tersedia dalam data.csv.")
        st.stop()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-title">Distribusi Warna Dominan</div>', unsafe_allow_html=True)
        if "WARNA_KATEGORI" in df.columns:
            vc = df["WARNA_KATEGORI"].value_counts().reset_index()
            vc.columns = ["warna", "n"]
            fig_pie = px.pie(vc, names="warna", values="n", hole=0.4,
                             color="warna", color_discrete_map=WARNA_HEX)
            fig_pie.update_traces(texttemplate="%{label}<br>%{percent:.1%}")
            fig_pie.update_layout(**PLOTLY_BASE, height=340)
            st.plotly_chart(fig_pie, use_container_width=True, key="wa_pie")

    with c2:
        st.markdown('<div class="section-title">Kecerahan vs Saturasi</div>', unsafe_allow_html=True)
        if "BRIGHTNESS_MEAN" in df.columns and "SATURATION_MEAN" in df.columns:
            dsc = df.dropna(subset=["BRIGHTNESS_MEAN", "SATURATION_MEAN"])
            smp = dsc.sample(min(600, len(dsc)), random_state=42)
            fig_sc = px.scatter(
                smp, x="BRIGHTNESS_MEAN", y="SATURATION_MEAN",
                color="WARNA_KATEGORI" if "WARNA_KATEGORI" in smp.columns else None,
                color_discrete_map=WARNA_HEX, opacity=0.55,
                hover_data=[C["title"]] if C["title"] else None,
                labels={"BRIGHTNESS_MEAN": "Kecerahan", "SATURATION_MEAN": "Saturasi",
                        "WARNA_KATEGORI": "Warna"},
            )
            fig_sc.update_layout(**PLOTLY_BASE, height=340)
            st.plotly_chart(fig_sc, use_container_width=True, key="wa_sc")

    # Proporsi klaster rata-rata
    pct_avail = [f"WARNA_PCT_{i}" for i in range(1, 6) if f"WARNA_PCT_{i}" in df.columns]
    if pct_avail:
        st.markdown('<div class="section-title">Proporsi Rata-Rata Klaster K-Means</div>',
                    unsafe_allow_html=True)
        means = df[pct_avail].mean().reset_index()
        means.columns = ["k", "pct"]
        means["k"] = means["k"].str.replace("WARNA_PCT_", "Klaster ")
        fig_k = px.bar(means, x="k", y="pct", text="pct",
                       color_discrete_sequence=["#3b82f6"])
        fig_k.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_k.update_layout(**PLOTLY_BASE, height=250)
        st.plotly_chart(fig_k, use_container_width=True, key="wa_kl")

    # Tren per tahun
    if C["year"] and "WARNA_KATEGORI" in df.columns:
        st.markdown('<div class="section-title">Tren Warna Dominan per Tahun</div>',
                    unsafe_allow_html=True)
        dtr = df[df[C["year"]].between(1990, 2030)]
        tren = dtr.groupby([C["year"], "WARNA_KATEGORI"]).size().reset_index(name="n")
        fig_tr = px.bar(tren, x=C["year"], y="n", color="WARNA_KATEGORI",
                        color_discrete_map=WARNA_HEX, barmode="stack",
                        labels={C["year"]: "Tahun", "n": "Jumlah", "WARNA_KATEGORI": "Warna"})
        fig_tr.update_layout(**PLOTLY_BASE, showlegend=True,
                              legend=dict(orientation="h", y=-0.2), height=310)
        st.plotly_chart(fig_tr, use_container_width=True, key="wa_tr")

    # Sample cover + palet
    if C["img"] and "WARNA_HEX_1" in df.columns:
        st.markdown('<div class="section-title">Contoh Sampul &amp; Palet</div>',
                    unsafe_allow_html=True)
        df_smp = df[df[C["img"]].str.strip().ne("")].sample(min(8, len(df)), random_state=7)
        cols = st.columns(4)
        for idx, (_, row) in enumerate(df_smp.iterrows()):
            with cols[idx % 4]:
                p = cover_path(row[C["img"]])
                if os.path.exists(p):
                    st.image(p, use_column_width=True)
                t = str(row.get(C["title"], ""))[:30] if C["title"] else ""
                st.markdown(palet_strip(row) + f'<p class="cover-title">{t}</p>',
                            unsafe_allow_html=True)

    # Heatmap genre × warna
    if C["genre"] and "WARNA_KATEGORI" in df.columns:
        st.markdown('<div class="section-title">Warna Dominan per Genre</div>',
                    unsafe_allow_html=True)
        fig_h = heatmap_genre_x_col(df, C["genre"], "WARNA_KATEGORI", "YlOrRd")
        if fig_h:
            st.plotly_chart(fig_h, use_container_width=True, key="wa_heat")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: TYPEFACE
# ═════════════════════════════════════════════════════════════════════════════
elif "Typeface" in PAGE:
    st.markdown('<div class="hero-title">Modul B — Analisis Typeface</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">CLIP zero-shot + MSER text detection · '
        '<i>Typeface</i> = entitas desain (Lupton 2024, hal. 54&#8211;57) · '
        '6 kategori: serif · sans-serif · slab-serif · script · display · monospace</div>',
        unsafe_allow_html=True,
    )

    if not MB or not C["tf"]:
        st.info("⏳ Data Modul B belum tersedia dalam data.csv.")
        st.stop()

    TF  = C["tf"]
    TFS = C["tf_skor"]
    COV = "TEKS_COVERAGE" if "TEKS_COVERAGE" in df.columns else None

    VALID_TF = {"serif", "sans-serif", "slab-serif", "script", "display", "monospace"}

    # Normalise: underscore → hyphen, lowercase
    df_tf = df.copy()
    df_tf[TF] = df_tf[TF].str.lower().str.replace("_", "-").str.strip()
    df_tf = df_tf[df_tf[TF].isin(VALID_TF)].reset_index(drop=True)

    if len(df_tf) == 0:
        st.warning(
            "Tidak ada data typeface yang valid. "
            "Nilai unik yang ditemukan di kolom tersebut:"
        )
        st.write(df[TF].value_counts())
        st.stop()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-title">Distribusi Kategori Typeface</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(simple_bar(df_tf[TF], TYPEFACE_COLOR, h=320),
                        use_container_width=True, key="tf_dist")

    with c2:
        st.markdown('<div class="section-title">Confidence vs Coverage Teks</div>',
                    unsafe_allow_html=True)
        if TFS and COV and TFS in df_tf.columns and COV in df_tf.columns:
            dsc2 = df_tf.dropna(subset=[TFS, COV])
            smp2 = dsc2.sample(min(500, len(dsc2)), random_state=42)
            fig_sc2 = px.scatter(
                smp2, x=COV, y=TFS,
                color=TF, color_discrete_map=TYPEFACE_COLOR, opacity=0.6,
                hover_data=[C["title"]] if C["title"] else None,
                labels={COV: "Coverage teks (proporsi area)",
                        TFS: "Confidence CLIP", TF: "Typeface"},
            )
            fig_sc2.update_layout(**PLOTLY_BASE, showlegend=True,
                                   legend=dict(orientation="h", y=-0.25), height=320)
            st.plotly_chart(fig_sc2, use_container_width=True, key="tf_sc")
        else:
            st.caption("Kolom confidence/coverage belum tersedia.")

    # Tren per tahun
    if C["year"] and TF in df_tf.columns:
        st.markdown('<div class="section-title">Tren Typeface per Tahun</div>',
                    unsafe_allow_html=True)
        dtr = df_tf[df_tf[C["year"]].between(1990, 2030)]
        tren_tf = dtr.groupby([C["year"], TF]).size().reset_index(name="n")
        fig_ttr = px.bar(tren_tf, x=C["year"], y="n", color=TF,
                         color_discrete_map=TYPEFACE_COLOR, barmode="stack",
                         labels={C["year"]: "Tahun", "n": "Jumlah", TF: "Typeface"})
        fig_ttr.update_layout(**PLOTLY_BASE, showlegend=True,
                               legend=dict(orientation="h", y=-0.2), height=300)
        st.plotly_chart(fig_ttr, use_container_width=True, key="tf_tren")

    # Heatmap genre
    if C["genre"]:
        st.markdown('<div class="section-title">Typeface per Genre</div>',
                    unsafe_allow_html=True)
        fig_th = heatmap_genre_x_col(df_tf, C["genre"], TF, "RdPu")
        if fig_th:
            st.plotly_chart(fig_th, use_container_width=True, key="tf_heat")

    # Ringkasan statistik
    stat_tf = [c for c in [TFS, COV, "N_REGION_TEKS", "JUDUL_MATCH_SCORE"]
               if c and c in df_tf.columns]
    if stat_tf:
        st.markdown('<div class="section-title">Statistik Deskriptif</div>', unsafe_allow_html=True)
        st.dataframe(df_tf[stat_tf].describe().round(3), use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: ILUSTRASI
# ═════════════════════════════════════════════════════════════════════════════
elif "Ilustrasi" in PAGE:
    st.markdown('<div class="hero-title">Modul C — Analisis Ilustrasi</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">YOLOv8n · DETR ResNet-50 · CLIP ViT-B/32 zero-shot · '
        'Rujukan: Arnold &amp; Tilton (2023) <i>Distant Viewing</i> 2.4</div>',
        unsafe_allow_html=True,
    )
    if not MC:
        st.info("⏳ Data Modul C belum tersedia.")
        st.stop()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-title">Distribusi Gaya Ilustrasi</div>',
                    unsafe_allow_html=True)
        if "GAYA_ILUSTRASI" in df.columns:
            st.plotly_chart(simple_bar(df["GAYA_ILUSTRASI"], GAYA_COLOR, orient="h", h=320),
                            use_container_width=True, key="il_gaya")

    with c2:
        st.markdown('<div class="section-title">Figur Manusia: YOLO vs DETR</div>',
                    unsafe_allow_html=True)
        if "YOLO_ADA_MANUSIA" in df.columns and "DETR_ADA_MANUSIA" in df.columns:
            def _bool(v):
                return str(v).strip().lower() in ("true", "1", "yes")
            dm = df.copy()
            dm["_y"] = dm["YOLO_ADA_MANUSIA"].apply(_bool)
            dm["_d"] = dm["DETR_ADA_MANUSIA"].apply(_bool)
            n_tot = len(dm)
            fig_mn = go.Figure([
                go.Bar(name="Ada manusia",
                       x=["YOLOv8n", "DETR"],
                       y=[dm["_y"].sum(), dm["_d"].sum()],
                       marker_color=["#ef4444", "#f97316"]),
                go.Bar(name="Tidak ada",
                       x=["YOLOv8n", "DETR"],
                       y=[n_tot - dm["_y"].sum(), n_tot - dm["_d"].sum()],
                       marker_color=["#e5e7eb", "#e5e7eb"]),
            ])
            fig_mn.update_layout(**PLOTLY_BASE, barmode="stack", height=320,
                                  showlegend=True, legend=dict(orientation="h", y=-0.25))
            st.plotly_chart(fig_mn, use_container_width=True, key="il_mn")
            k = (dm["_y"] == dm["_d"]).sum()
            st.caption(f"Konsistensi YOLO–DETR: {k}/{n_tot} ({k/n_tot*100:.1f}%)")

    if "YOLO_N_OBJEK" in df.columns:
        st.markdown('<div class="section-title">Distribusi Jumlah Objek (YOLOv8n)</div>',
                    unsafe_allow_html=True)
        obj_s = pd.to_numeric(df["YOLO_N_OBJEK"], errors="coerce").dropna()
        fig_obj = px.histogram(obj_s, nbins=15, color_discrete_sequence=["#3b82f6"],
                               labels={"value": "Jumlah Objek", "count": "Frekuensi"})
        fig_obj.update_layout(**PLOTLY_BASE, height=250)
        st.plotly_chart(fig_obj, use_container_width=True, key="il_obj")

    if C["genre"] and "GAYA_ILUSTRASI" in df.columns:
        st.markdown('<div class="section-title">Gaya Ilustrasi per Genre</div>',
                    unsafe_allow_html=True)
        fig_gh = heatmap_genre_x_col(df, C["genre"], "GAYA_ILUSTRASI", "Greens")
        if fig_gh:
            st.plotly_chart(fig_gh, use_container_width=True, key="il_heat")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: GENRE & TREN
# ═════════════════════════════════════════════════════════════════════════════
elif "Genre" in PAGE:
    st.markdown('<div class="hero-title">Genre &amp; Tren Temporal</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Distribusi genre multi-label · Tren penerbitan per tahun</div>',
                unsafe_allow_html=True)

    if C["genre"]:
        st.markdown('<div class="section-title">Distribusi Genre (Top 20)</div>',
                    unsafe_allow_html=True)
        all_g_flat = []
        for val in df[C["genre"]]:
            all_g_flat.extend(expand_genres(str(val)))
        vc_g = pd.Series(all_g_flat).value_counts().head(20).reset_index()
        vc_g.columns = ["genre", "n"]
        vc_g["pct"] = (vc_g["n"] / N * 100).round(1)
        fig_gd = px.bar(vc_g, y="genre", x="n", orientation="h",
                        text="pct", color="n", color_continuous_scale="Blues",
                        labels={"n": "Jumlah", "genre": ""})
        fig_gd.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_gd.update_layout(**PLOTLY_BASE, coloraxis_showscale=False, height=500)
        st.plotly_chart(fig_gd, use_container_width=True, key="ge_dist")

    if C["year"]:
        st.markdown('<div class="section-title">Jumlah Buku per Tahun</div>',
                    unsafe_allow_html=True)
        dyr = df[df[C["year"]].between(1990, 2030)]
        yrc = dyr[C["year"]].value_counts().sort_index().reset_index()
        yrc.columns = ["tahun", "n"]
        fig_yr = px.area(yrc, x="tahun", y="n",
                         labels={"tahun": "Tahun", "n": "Jumlah Buku"},
                         color_discrete_sequence=["#3b82f6"])
        fig_yr.update_layout(**PLOTLY_BASE, height=270)
        st.plotly_chart(fig_yr, use_container_width=True, key="ge_yr")

    if C["genre"] and MA and "WARNA_KATEGORI" in df.columns:
        st.markdown('<div class="section-title">Warna Dominan per Genre</div>',
                    unsafe_allow_html=True)
        fig_gwh = heatmap_genre_x_col(df, C["genre"], "WARNA_KATEGORI", "YlOrRd")
        if fig_gwh:
            st.plotly_chart(fig_gwh, use_container_width=True, key="ge_wh")

    if C["genre"] and MC and "GAYA_ILUSTRASI" in df.columns:
        st.markdown('<div class="section-title">Gaya Ilustrasi per Genre</div>',
                    unsafe_allow_html=True)
        fig_gih = heatmap_genre_x_col(df, C["genre"], "GAYA_ILUSTRASI", "Greens")
        if fig_gih:
            st.plotly_chart(fig_gih, use_container_width=True, key="ge_ih")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: RATING & AGREGAT
# ═════════════════════════════════════════════════════════════════════════════
elif "Rating" in PAGE:
    st.markdown('<div class="hero-title">Rating &amp; Agregat</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Statistik rating Goodreads · Korelasi atribut visual dengan rating</div>',
                unsafe_allow_html=True)

    if not C["rating"]:
        st.info("Kolom rating tidak ditemukan di data.")
        st.stop()

    df_r = df.copy()
    df_r[C["rating"]] = pd.to_numeric(df_r[C["rating"]], errors="coerce")
    df_r = df_r[df_r[C["rating"]].between(0.5, 5.5)].reset_index(drop=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Rating rata-rata", f"{df_r[C['rating']].mean():.2f}")
    c2.metric("Median",           f"{df_r[C['rating']].median():.2f}")
    c3.metric("Buku dengan rating", f"{len(df_r):,}")

    st.markdown('<div class="section-title">Distribusi Rating</div>', unsafe_allow_html=True)
    fig_rd = px.histogram(df_r, x=C["rating"], nbins=40,
                          color_discrete_sequence=["#f97316"],
                          labels={C["rating"]: "Rating Goodreads", "count": "Jumlah"})
    fig_rd.update_layout(**PLOTLY_BASE, height=250)
    st.plotly_chart(fig_rd, use_container_width=True, key="ra_hist")

    # Per genre
    if C["genre"]:
        st.markdown('<div class="section-title">Rating Rata-Rata per Genre</div>',
                    unsafe_allow_html=True)
        rg_rows = []
        for g in get_all_genres(df_r, C["genre"])[:18]:
            sub = filter_genre(df_r, C["genre"], g)
            rv  = pd.to_numeric(sub[C["rating"]], errors="coerce").dropna()
            if len(rv) >= 5:
                rg_rows.append({"Genre": g, "Rating": round(rv.mean(), 3), "N": len(rv)})
        if rg_rows:
            rg_df = pd.DataFrame(rg_rows).sort_values("Rating", ascending=False)
            fig_rg = px.bar(rg_df, y="Genre", x="Rating", orientation="h",
                            text="Rating", color="Rating",
                            color_continuous_scale="RdYlGn",
                            range_x=[3.0, 5.0],
                            labels={"Rating": "Rating rata-rata"})
            fig_rg.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig_rg.update_layout(**PLOTLY_BASE, coloraxis_showscale=False,
                                  height=max(300, len(rg_df) * 28 + 80))
            st.plotly_chart(fig_rg, use_container_width=True, key="ra_genre")

    # Per warna
    if MA and "WARNA_KATEGORI" in df_r.columns:
        st.markdown('<div class="section-title">Rating per Warna Dominan</div>',
                    unsafe_allow_html=True)
        rw = df_r.groupby("WARNA_KATEGORI")[C["rating"]].agg(["mean", "count"]).reset_index()
        rw.columns = ["warna", "mean", "n"]
        rw = rw[rw["n"] >= 5].sort_values("mean", ascending=False)
        fig_rw = px.bar(rw, x="warna", y="mean", text="mean",
                        color="warna", color_discrete_map=WARNA_HEX,
                        labels={"mean": "Rating rata-rata", "warna": ""},
                        range_y=[3.0, 5.0])
        fig_rw.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_rw.update_layout(**PLOTLY_BASE, height=270)
        st.plotly_chart(fig_rw, use_container_width=True, key="ra_warna")

    # Per typeface
    if MB and C["tf"] and C["tf"] in df_r.columns:
        TF2 = C["tf"]
        df_rtf = df_r.copy()
        df_rtf[TF2] = df_rtf[TF2].str.lower().str.replace("_", "-")
        df_rtf = df_rtf[df_rtf[TF2].isin({"serif","sans-serif","slab-serif",
                                            "script","display","monospace"})]
        st.markdown('<div class="section-title">Rating per Kategori Typeface</div>',
                    unsafe_allow_html=True)
        rt = df_rtf.groupby(TF2)[C["rating"]].agg(["mean","count"]).reset_index()
        rt.columns = ["typeface", "mean", "n"]
        rt = rt[rt["n"] >= 5].sort_values("mean", ascending=False)
        fig_rt = px.bar(rt, x="typeface", y="mean", text="mean",
                        color="typeface", color_discrete_map=TYPEFACE_COLOR,
                        labels={"mean": "Rating rata-rata", "typeface": ""},
                        range_y=[3.0, 5.0])
        fig_rt.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_rt.update_layout(**PLOTLY_BASE, height=270)
        st.plotly_chart(fig_rt, use_container_width=True, key="ra_tf")

    # Per gaya ilustrasi
    if MC and "GAYA_ILUSTRASI" in df_r.columns:
        st.markdown('<div class="section-title">Rating per Gaya Ilustrasi</div>',
                    unsafe_allow_html=True)
        ri = df_r.groupby("GAYA_ILUSTRASI")[C["rating"]].agg(["mean","count"]).reset_index()
        ri.columns = ["gaya", "mean", "n"]
        ri = ri[ri["n"] >= 5].sort_values("mean", ascending=False)
        fig_ri = px.bar(ri, x="gaya", y="mean", text="mean",
                        color="gaya", color_discrete_map=GAYA_COLOR,
                        labels={"mean": "Rating rata-rata", "gaya": ""},
                        range_y=[3.0, 5.0])
        fig_ri.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_ri.update_layout(**PLOTLY_BASE, height=270)
        st.plotly_chart(fig_ri, use_container_width=True, key="ra_gaya")

    # Top 10
    if C["title"]:
        st.markdown('<div class="section-title">Top 10 Rating Tertinggi</div>',
                    unsafe_allow_html=True)
        top_cols = [c for c in [C["title"], C["author"], C["year"],
                                C["rating"], C["n_rating"]] if c and c in df_r.columns]
        top10 = df_r.nlargest(10, C["rating"])[top_cols].copy()
        top10["⭐"] = top10[C["rating"]].apply(star_rating)
        st.dataframe(top10, use_container_width=True, hide_index=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: JELAJAH BUKU
# ═════════════════════════════════════════════════════════════════════════════
elif "Jelajah" in PAGE:
    st.markdown('<div class="hero-title">Jelajah Buku</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Telusuri setiap sampul beserta hasil analisis</div>',
                unsafe_allow_html=True)

    cs1, cs2, cs3 = st.columns([3, 1, 1])
    with cs1:
        query = st.text_input("", placeholder="Cari judul atau penulis…",
                              label_visibility="collapsed")
    with cs2:
        sort_opt = st.selectbox("", ["Terbaru", "Terlama", "Rating ↓", "Rating ↑"],
                                label_visibility="collapsed")
    with cs3:
        n_per = st.selectbox("", [20, 40, 60], label_visibility="collapsed")

    df_sh = df.copy()
    if query:
        mask = pd.Series([False] * len(df_sh), index=df_sh.index)
        if C["title"]:  mask |= df_sh[C["title"]].str.contains(query, case=False, na=False)
        if C["author"]: mask |= df_sh[C["author"]].str.contains(query, case=False, na=False)
        df_sh = df_sh[mask]

    if sort_opt == "Terbaru" and C["year"]:
        df_sh = df_sh.sort_values(C["year"], ascending=False)
    elif sort_opt == "Terlama" and C["year"]:
        df_sh = df_sh.sort_values(C["year"], ascending=True)
    elif sort_opt == "Rating ↓" and C["rating"]:
        df_sh[C["rating"]] = pd.to_numeric(df_sh[C["rating"]], errors="coerce")
        df_sh = df_sh.sort_values(C["rating"], ascending=False)
    elif sort_opt == "Rating ↑" and C["rating"]:
        df_sh[C["rating"]] = pd.to_numeric(df_sh[C["rating"]], errors="coerce")
        df_sh = df_sh.sort_values(C["rating"], ascending=True)

    df_sh = df_sh.reset_index(drop=True)
    st.caption(f"{len(df_sh):,} buku ditemukan")

    n_pages = max(1, (len(df_sh) - 1) // n_per + 1)
    pg = st.selectbox(f"Halaman (dari {n_pages})", range(1, n_pages + 1)) if n_pages > 1 else 1
    df_pg = df_sh.iloc[(pg - 1) * n_per: pg * n_per]

    for chunk in [df_pg.iloc[i: i + 4] for i in range(0, len(df_pg), 4)]:
        cols = st.columns(4)
        for col_w, (_, book) in zip(cols, chunk.iterrows()):
            with col_w:
                if C["img"] and str(book.get(C["img"], "")) not in ("", "nan"):
                    p = cover_path(book[C["img"]])
                    if os.path.exists(p):
                        st.image(p, use_column_width=True)

                t  = str(book.get(C["title"],  ""))[:45] if C["title"]  else ""
                au = str(book.get(C["author"], ""))[:28] if C["author"] else ""
                yr = str(int(book.get(C["year"], 0))) \
                     if C["year"] and str(book.get(C["year"], "0")) not in ("0", "", "nan") else ""
                rv = float(book.get(C["rating"], 0) or 0) if C["rating"] else 0

                wv = str(book.get("WARNA_KATEGORI", "")) if MA else ""
                tv = str(book.get(C["tf"], "") if C["tf"] else "")
                tv = tv.lower().replace("_", "-") if tv else ""
                gv = str(book.get("GAYA_ILUSTRASI", "")) if MC else ""

                valid_tf = {"serif","sans-serif","slab-serif","script","display","monospace"}
                badges = ""
                if wv and wv not in ("", "nan"):
                    badges += f'<span class="badge tag-warna">🎨 {wv}</span>'
                if tv and tv in valid_tf:
                    badges += f'<span class="badge tag-typeface">🔤 {tv}</span>'
                if gv and gv not in ("", "nan", "unknown"):
                    badges += f'<span class="badge tag-gaya">🖼 {gv}</span>'

                pal = palet_strip(book) if "WARNA_HEX_1" in book else ""
                st.markdown(
                    f'{pal}'
                    f'<p class="cover-title">{t}</p>'
                    f'<p class="cover-meta">{au}{" · " if au and yr else ""}{yr}</p>'
                    f'<p class="cover-meta" style="color:#f59e0b">{star_rating(rv)}</p>'
                    f'<div style="margin-top:3px">{badges}</div>'
                    f'<div style="margin-bottom:1rem"></div>',
                    unsafe_allow_html=True,
                )
