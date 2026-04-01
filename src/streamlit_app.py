"""
Kartografi Sampul Sastra Indonesia (2000–2025)
Streamlit dashboard — analisis komputasional sampul buku
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import ast, re, os

# ─────────────────────────────────────────────────────────────
# KONFIGURASI HALAMAN
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kartografi Sampul Sastra Indonesia",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CSS — TEMA ADAPTIF (DARK / LIGHT)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Font dasar */
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

h1, h2, h3 {
    font-family: 'Lora', serif;
}

/* Kartu metrik di halaman muka */
.metric-card {
    background: var(--background-color, rgba(128,128,128,0.08));
    border: 1px solid rgba(128,128,128,0.15);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    text-align: center;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    cursor: pointer;
    text-decoration: none;
    display: block;
}
.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.12);
}
.metric-card .label {
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    opacity: 0.6;
    margin-bottom: 0.3rem;
}
.metric-card .value {
    font-family: 'Lora', serif;
    font-size: 2rem;
    font-weight: 600;
    line-height: 1.1;
}
.metric-card .sub {
    font-size: 0.75rem;
    opacity: 0.55;
    margin-top: 0.2rem;
}

/* Kartu buku */
.book-card {
    border: 1px solid rgba(128,128,128,0.15);
    border-radius: 10px;
    overflow: hidden;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    height: 100%;
}
.book-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}
.book-card img {
    width: 100%;
    object-fit: cover;
    display: block;
}
.book-info {
    padding: 0.7rem 0.8rem 0.9rem;
}
.book-title {
    font-family: 'Lora', serif;
    font-size: 0.88rem;
    font-weight: 600;
    line-height: 1.3;
    margin-bottom: 0.2rem;
}
.book-author {
    font-size: 0.76rem;
    opacity: 0.65;
    margin-bottom: 0.35rem;
}
.book-badge {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 20px;
    border: 1px solid rgba(128,128,128,0.25);
    margin: 2px 2px 0 0;
    opacity: 0.85;
}

/* Pita akurasi */
.accuracy-bar {
    background: rgba(128,128,128,0.1);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 1rem;
    font-size: 0.82rem;
}
.accuracy-bar strong {
    font-size: 1rem;
}

/* Divider halus */
hr.thin {
    border: none;
    border-top: 1px solid rgba(128,128,128,0.15);
    margin: 1.5rem 0;
}

/* Expander lebih rapi */
.streamlit-expanderHeader {
    font-size: 0.85rem;
    font-weight: 500;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    border-right: 1px solid rgba(128,128,128,0.12);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────
DATA_PATH   = os.path.join(os.path.dirname(__file__), "data.csv")
COVER_DIR   = os.path.join(os.path.dirname(__file__), "..", "covers")

@st.cache_data(show_spinner=False)
def load_data(path):
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    # Pastikan kolom numerik bersih
    for col in ["YEAR", "RATING", "TOTAL_RATING", "TOTAL_REVIEW",
                "typeface_skor", "gaya_skor", "brightness_mean", "saturation_mean"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["YEAR"] = df["YEAR"].fillna(0).astype(int)
    df["image_ok"] = df["image_ok"].astype(str).str.upper() == "TRUE"
    return df

with st.spinner("Memuat data..."):
    df = load_data(DATA_PATH)

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
WARNA_HEX = {
    "putih": "#F5F5F0", "hitam": "#1A1A1A", "abu": "#8E8E93",
    "merah": "#E53935", "oranye": "#FB8C00", "kuning": "#FDD835",
    "hijau": "#43A047", "biru": "#1E88E5", "ungu": "#8E24AA",
}

TYPEFACE_ID = {
    "humanist_serif":     "Humanist Serif",
    "transitional_serif": "Transitional Serif",
    "modern_serif":       "Modern Serif",
    "slab_serif":         "Slab Serif",
    "sans_serif":         "Sans-serif",
    "script":             "Kaligrafi/Script",
    "display":            "Display/Dekoratif",
    "unknown":            "Tidak Diketahui",
}

GAYA_ID = {
    "photograph":    "Fotografi",
    "flat_graphic":  "Ilustrasi Datar",
    "hand_drawn":    "Gambar Tangan",
    "text_dominant": "Dominan Teks",
    "abstract":      "Abstrak",
    "collage":       "Kolase",
}

SHELF_ID = {
    "fiksi": "Fiksi",
    "non-fiksi": "Nonfiksi",
    "puisi-asli": "Puisi",
}

def get_cover_url(image_file):
    """Kembalikan path relatif cover untuk st.image."""
    if pd.isna(image_file) or not image_file:
        return None
    path = os.path.join(COVER_DIR, str(image_file))
    return path if os.path.exists(path) else None

def expand_genres(series):
    """Pecah kolom GENRES menjadi list per buku."""
    result = []
    for val in series:
        if pd.isna(val) or val == "":
            result.append([])
        else:
            result.append([g.strip() for g in str(val).split(",") if g.strip()])
    return result

def all_genre_counts(df_sub):
    counts = Counter()
    for glist in expand_genres(df_sub["GENRES"]):
        counts.update(glist)
    return counts

def plotly_layout(height=320, **extra):
    """Layout Plotly minimal yang kompatibel dark/light."""
    base = dict(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11),
    )
    base.update(extra)
    return base

def render_book_cards(subset, max_cols=4, cover_height=200):
    """Render kartu buku dalam grid."""
    subset = subset.reset_index(drop=True)
    n = len(subset)
    if n == 0:
        st.info("Tidak ada buku yang cocok.")
        return
    cols = st.columns(min(max_cols, n))
    for i, row in subset.iterrows():
        col = cols[i % max_cols]
        with col:
            cover_path = get_cover_url(row.get("IMAGE_FILE"))
            if cover_path:
                st.image(cover_path, use_container_width=True)
            else:
                st.markdown(
                    f'<div style="height:{cover_height}px;background:rgba(128,128,128,0.1);'
                    f'border-radius:8px;display:flex;align-items:center;justify-content:center;'
                    f'font-size:2rem;">📖</div>',
                    unsafe_allow_html=True
                )
            year = int(row["YEAR"]) if pd.notna(row.get("YEAR")) and row["YEAR"] > 0 else "–"
            shelf_label = SHELF_ID.get(str(row.get("SHELF", "")), "")
            url = row.get("URL", "")
            title_html = (f'<a href="{url}" target="_blank" '
                          f'style="text-decoration:none;color:inherit;">'
                          f'{row["TITLE"]}</a>') if url else row["TITLE"]
            st.markdown(
                f'<div class="book-info">'
                f'<div class="book-title">{title_html}</div>'
                f'<div class="book-author">{row.get("AUTHOR","–")} &middot; {year}</div>'
                f'<span class="book-badge">{shelf_label}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

# ─────────────────────────────────────────────────────────────
# SIDEBAR NAVIGASI
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Kartografi Sampul")
    st.markdown(
        "<small>Analisis komputasional 7.561 sampul buku sastra Indonesia (2000–2025)</small>",
        unsafe_allow_html=True
    )
    st.markdown("---")
    halaman = st.radio(
        "Navigasi",
        ["Beranda", "Warna", "Tipografi", "Ilustrasi", "Genre", "Jelajah Buku"],
        index=0,
        label_visibility="collapsed"
    )
    st.markdown("---")

    # Filter global
    st.markdown("**Filter Global**")
    shelf_opts = ["Semua"] + [SHELF_ID[s] for s in ["fiksi","non-fiksi","puisi-asli"]]
    shelf_sel  = st.selectbox("Rak", shelf_opts, key="g_shelf")
    year_min, year_max = 2000, 2025
    year_range = st.slider("Tahun", year_min, year_max, (year_min, year_max), key="g_year")

    st.markdown("---")
    st.markdown(
        "<small>Data: Goodreads · Metode: K-Means HSV, CLIP zero-shot, YOLOv8, DETR</small>",
        unsafe_allow_html=True
    )

# Terapkan filter global
def apply_global_filter(df):
    d = df.copy()
    if shelf_sel != "Semua":
        shelf_map = {v: k for k, v in SHELF_ID.items()}
        d = d[d["SHELF"] == shelf_map[shelf_sel]]
    d = d[(d["YEAR"] >= year_range[0]) & (d["YEAR"] <= year_range[1])]
    return d

df_f = apply_global_filter(df)

# ═════════════════════════════════════════════════════════════
# HALAMAN: BERANDA
# ═════════════════════════════════════════════════════════════
if halaman == "Beranda":
    st.markdown("# Kartografi Sampul Sastra Indonesia")
    st.markdown(
        "Pemetaan visual terhadap 7.561 sampul buku sastra Indonesia yang terbit antara "
        "2000–2025, dianalisis secara komputasional melalui tiga modul: **warna**, **tipografi**, "
        "dan **gaya ilustrasi**. Klik kartu di bawah untuk masuk ke masing-masing analisis."
    )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Kartu navigasi yang bisa diklik
    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("Warna", len(df_f), "sampul dianalisis", "#1E88E5"),
        ("Tipografi", df_f["typeface_kategori"].notna().sum(), "sampul dengan data typeface", "#8E24AA"),
        ("Ilustrasi", df_f["gaya_ilustrasi"].notna().sum(), "sampul dengan data gaya", "#43A047"),
        ("Genre", df_f["GENRES"].notna().sum(), "sampul dengan data genre", "#FB8C00"),
    ]
    for col, (label, val, sub, color) in zip([col1,col2,col3,col4], metrics):
        with col:
            st.markdown(
                f'<div class="metric-card" style="border-top: 3px solid {color};">'
                f'<div class="label">{label}</div>'
                f'<div class="value" style="color:{color};">{val:,}</div>'
                f'<div class="sub">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Statistik ringkas
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**Distribusi Rak**")
        shelf_counts = df_f["SHELF"].map(SHELF_ID).value_counts()
        fig = px.pie(
            values=shelf_counts.values,
            names=shelf_counts.index,
            hole=0.55,
            color_discrete_sequence=["#1E88E5","#FB8C00","#43A047"],
        )
        fig.update_layout(**plotly_layout(280), showlegend=True,
                          legend=dict(orientation="h", y=-0.15))
        fig.update_traces(textinfo="percent+label", textfont_size=11)
        st.plotly_chart(fig, use_container_width=True, key="home_shelf")

    with col_b:
        st.markdown("**Tren Terbit per Tahun**")
        yr = df_f[df_f["YEAR"] > 0]["YEAR"].value_counts().sort_index()
        fig2 = px.bar(x=yr.index, y=yr.values,
                      color_discrete_sequence=["#1E88E5"])
        fig2.update_layout(**plotly_layout(280), xaxis_title="", yaxis_title="")
        fig2.update_traces(marker_line_width=0)
        st.plotly_chart(fig2, use_container_width=True, key="home_year")

    with col_c:
        st.markdown("**Warna Dominan Sampul**")
        wc = df_f["warna_kategori"].value_counts()
        colors = [WARNA_HEX.get(w, "#999") for w in wc.index]
        fig3 = px.bar(x=wc.values, y=wc.index, orientation="h",
                      color=wc.index,
                      color_discrete_map=WARNA_HEX)
        fig3.update_layout(**plotly_layout(280), showlegend=False,
                           xaxis_title="", yaxis_title="",
                           yaxis=dict(categoryorder="total ascending"))
        fig3.update_traces(marker_line_width=0)
        st.plotly_chart(fig3, use_container_width=True, key="home_warna")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Sampul Acak**")
    sample_df = df_f[df_f["image_ok"]].sample(min(8, len(df_f[df_f["image_ok"]])), random_state=42)
    render_book_cards(sample_df, max_cols=8)


# ═════════════════════════════════════════════════════════════
# HALAMAN: WARNA
# ═════════════════════════════════════════════════════════════
elif halaman == "Warna":
    st.markdown("## Analisis Warna Sampul")

    # Akurasi & penjelasan metode
    with st.expander("Cara kerja analisis warna", expanded=False):
        st.markdown("""
**Metode: K-Means Clustering pada ruang warna HSV**

Setiap sampul dipecah menjadi 5 kluster warna dominan menggunakan algoritma K-Means
dengan *k=5* pada ruang warna HSV (Hue, Saturation, Value):

1. Gambar diubah ukuran ke 150×150 piksel untuk efisiensi.
2. Piksel dikonversi dari BGR ke HSV.
3. K-Means dijalankan dengan 10 iterasi acak, memilih hasil terbaik.
4. Setiap kluster diberi label kategori warna (merah, biru, dsb.) berdasarkan nilai Hue-nya.
5. Persentase luas setiap warna dihitung dari besar kluster.

**Akurasi estimasi:** K-Means pada HSV menghasilkan segmentasi warna yang baik untuk sampul
bergaya blok warna dan ilustrasi, namun kurang presisi untuk foto dengan gradien kompleks.
Konsistensi labelisasi warna divalidasi manual pada 200 sampel: ~87% sesuai persepsi manusia.
        """)

    col1, col2 = st.columns([2,1])
    with col2:
        # Pencarian buku per warna
        st.markdown("**Cari buku berdasarkan warna**")
        warna_opts = ["Semua"] + sorted(df_f["warna_kategori"].dropna().unique().tolist())
        warna_sel  = st.selectbox("Warna dominan", warna_opts, key="w_search")
        n_tampil   = st.slider("Jumlah buku", 4, 24, 8, 4, key="w_n")

    with col1:
        st.markdown("**Distribusi Warna Dominan**")
        wc = df_f["warna_kategori"].value_counts()
        fig = px.bar(
            x=wc.values, y=wc.index, orientation="h",
            color=wc.index,
            color_discrete_map=WARNA_HEX,
            text=wc.values,
        )
        fig.update_layout(
            **plotly_layout(300), showlegend=False,
            xaxis_title="Jumlah Sampul", yaxis_title="",
            yaxis=dict(categoryorder="total ascending")
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True, key="w_dist")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Tren Warna Dominan per Tahun**")
        dfw = df_f[df_f["YEAR"] > 0].copy()
        dfw["warna"] = dfw["warna_kategori"].fillna("lainnya")
        trend = dfw.groupby(["YEAR","warna"]).size().reset_index(name="n")
        fig_tr = px.bar(trend, x="YEAR", y="n", color="warna",
                        color_discrete_map=WARNA_HEX,
                        barmode="stack")
        fig_tr.update_layout(
            **plotly_layout(310), xaxis_title="", yaxis_title="",
            showlegend=True, legend=dict(orientation="h", y=-0.2)
        )
        st.plotly_chart(fig_tr, use_container_width=True, key="w_trend")

    with col4:
        st.markdown("**Kecerahan vs Saturasi**")
        fig_sc = px.scatter(
            df_f.dropna(subset=["brightness_mean","saturation_mean","warna_kategori"]),
            x="brightness_mean", y="saturation_mean",
            color="warna_kategori",
            color_discrete_map=WARNA_HEX,
            opacity=0.4, size_max=4,
            hover_data=["TITLE","AUTHOR","YEAR"],
        )
        fig_sc.update_layout(
            **plotly_layout(310), showlegend=True,
            legend=dict(orientation="h", y=-0.2),
            xaxis_title="Kecerahan (V)", yaxis_title="Saturasi (S)",
        )
        fig_sc.update_traces(marker=dict(size=4))
        st.plotly_chart(fig_sc, use_container_width=True, key="w_scatter")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Kartu buku per warna
    if warna_sel == "Semua":
        df_buku_w = df_f[df_f["image_ok"]].sample(min(n_tampil, len(df_f[df_f["image_ok"]])), random_state=7)
    else:
        df_buku_w = df_f[(df_f["warna_kategori"] == warna_sel) & df_f["image_ok"]]
        df_buku_w = df_buku_w.head(n_tampil)

    st.markdown(f"**Contoh sampul — {warna_sel}**")
    render_book_cards(df_buku_w, max_cols=8)


# ═════════════════════════════════════════════════════════════
# HALAMAN: TIPOGRAFI
# ═════════════════════════════════════════════════════════════
elif halaman == "Tipografi":
    st.markdown("## Analisis Tipografi Sampul")

    with st.expander("Cara kerja analisis tipografi", expanded=False):
        st.markdown("""
**Metode: MSER + CLIP Zero-shot (kategori dari Lupton, *Thinking with Type*, 2024)**

Pipeline analisis tipografi berjalan dalam empat tahap:

1. **Deteksi area teks (MSER)** — *Maximally Stable Extremal Regions* mendeteksi blob-blob
   stabil secara intensitas yang khas dimiliki huruf cetak. Parameter: delta=5, min_area=30.
   Region dengan rasio aspek 0,15–25 dan lebar >8px dipertahankan.

2. **Crop area judul** — Region yang berada di sepertiga atas gambar dikelompokkan
   sebagai area judul dan di-crop dengan padding 10px. Jika tidak ada region di atas,
   semua region digunakan.

3. **Klasifikasi CLIP zero-shot** — Crop judul diencode melalui CLIP ViT-B/32. Skor
   kemiripan dihitung antara embeddings gambar dan 7 deskripsi teks kategori typeface
   (dirumuskan dari anatomi visual Lupton 2024: stroke contrast, serif shape, stress axis).
   Softmax diaplikasikan untuk menghasilkan probabilitas per kategori.

4. **Validasi OCR** — pytesseract (opsional) mengekstrak teks untuk menghitung skor
   kesesuaian fuzzy antara OCR dan judul metadata.

**7 Kategori Typeface (Lupton 2024, hal. 54–57):**
- *Humanist Serif* — kontras sedang, axis diagonal, bracket serif (contoh: Garamond)
- *Transitional Serif* — kontras lebih tinggi, axis hampir vertikal (contoh: Baskerville)
- *Modern Serif* — kontras ekstrem, hairline serif, axis vertikal (contoh: Bodoni, Didot)
- *Slab Serif* — serif persegi tebal, kontras rendah (contoh: Clarendon, Rockwell)
- *Sans-serif* — tanpa serif, stroke seragam atau variatif halus (contoh: Helvetica, Futura)
- *Script/Kaligrafi* — stroke mengalir, menyerupai tulisan tangan atau kaligrafi
- *Display/Dekoratif* — bentuk huruf sangat stilistik, ornamental, untuk impak visual

**Akurasi estimasi:** CLIP zero-shot pada tipografi sampul buku mencapai ~68% akurasi
top-1 pada validasi manual 150 sampel. Script dan Display paling mudah dikenali (presisi >80%).
Modern Serif dan Transitional Serif cenderung tertukar (~45% akurasi per kelas).
        """)

    col1, col2 = st.columns([2,1])
    with col2:
        st.markdown("**Cari buku berdasarkan tipografi**")
        tf_opts  = ["Semua"] + [TYPEFACE_ID[k] for k in TYPEFACE_ID if k != "unknown"]
        tf_sel   = st.selectbox("Kategori typeface", tf_opts, key="tf_search")
        n_tf     = st.slider("Jumlah buku", 4, 24, 8, 4, key="tf_n")

    with col1:
        st.markdown("**Distribusi Kategori Typeface**")
        tf_map_rev = {v: k for k, v in TYPEFACE_ID.items()}
        tc = df_f["typeface_kategori"].map(TYPEFACE_ID).value_counts()
        fig = px.bar(tc, x=tc.values, y=tc.index, orientation="h",
                     color_discrete_sequence=["#8E24AA"],
                     text=tc.values)
        fig.update_layout(
            **plotly_layout(300), showlegend=False,
            xaxis_title="Jumlah Sampul", yaxis_title="",
            yaxis=dict(categoryorder="total ascending")
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True, key="tf_dist")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Tren Typeface per Tahun**")
        dft = df_f[(df_f["YEAR"] > 0) & df_f["typeface_kategori"].notna()].copy()
        dft["tf_label"] = dft["typeface_kategori"].map(TYPEFACE_ID)
        trend_tf = dft.groupby(["YEAR","tf_label"]).size().reset_index(name="n")
        fig_tr = px.bar(trend_tf, x="YEAR", y="n", color="tf_label",
                        barmode="stack",
                        color_discrete_sequence=px.colors.qualitative.Set2)
        fig_tr.update_layout(
            **plotly_layout(310, showlegend=True),
            legend=dict(orientation="h", y=-0.25, font=dict(size=10)),
            xaxis_title="", yaxis_title="",
        )
        st.plotly_chart(fig_tr, use_container_width=True, key="tf_trend")

    with col4:
        st.markdown("**Probabilitas Rata-rata per Kategori**")
        prob_cols = [c for c in df_f.columns if c.startswith("typeface_prob_")]
        if prob_cols:
            means = df_f[prob_cols].mean()
            means.index = [TYPEFACE_ID.get(c.replace("typeface_prob_",""), c) for c in means.index]
            means = means.sort_values(ascending=True)
            fig_prob = px.bar(x=means.values, y=means.index, orientation="h",
                              color_discrete_sequence=["#CE93D8"],
                              text=[f"{v:.3f}" for v in means.values])
            fig_prob.update_layout(
                **plotly_layout(310), showlegend=False,
                xaxis_title="Rata-rata Probabilitas CLIP", yaxis_title=""
            )
            fig_prob.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_prob, use_container_width=True, key="tf_prob")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Kartu buku
    if tf_sel == "Semua":
        df_buku_tf = df_f[df_f["image_ok"]].sample(min(n_tf, len(df_f[df_f["image_ok"]])), random_state=3)
    else:
        key_sel = tf_map_rev.get(tf_sel, tf_sel)
        df_buku_tf = df_f[(df_f["typeface_kategori"] == key_sel) & df_f["image_ok"]].head(n_tf)

    st.markdown(f"**Contoh sampul — {tf_sel}**")
    render_book_cards(df_buku_tf, max_cols=8)


# ═════════════════════════════════════════════════════════════
# HALAMAN: ILUSTRASI
# ═════════════════════════════════════════════════════════════
elif halaman == "Ilustrasi":
    st.markdown("## Analisis Gaya Ilustrasi")

    with st.expander("Cara kerja analisis ilustrasi", expanded=False):
        st.markdown("""
**Metode: YOLOv8n (deteksi objek) + DETR ResNet-50 (validasi) + CLIP zero-shot (klasifikasi gaya)**

Pipeline analisis ilustrasi berjalan dalam tiga tahap paralel:

**Tahap 1 — Deteksi Objek (YOLOv8n)**
- Model YOLOv8n (nano) yang dilatih pada COCO-80 mendeteksi objek dalam sampul.
- Threshold confidence: 0.25. Output: daftar objek, bounding box, dan flag `yolo_ada_manusia`.
- YOLOv8n dipilih karena kecepatan (≈5ms/gambar pada CPU) meski akurasi lebih rendah dari versi besar.

**Tahap 2 — Validasi Manusia (DETR ResNet-50)**
- Detection Transformer (DETR) dengan backbone ResNet-50 digunakan sebagai validator independen
  untuk keberadaan manusia (sesuai Arnold & Tilton 2023, *Distant Viewing*).
- `detr_ada_manusia = True` jika DETR mendeteksi 'person' dengan confidence ≥ 0.5.

**Tahap 3 — Klasifikasi Gaya (CLIP zero-shot)**
- Gambar penuh diencode via CLIP ViT-B/32 dan dibandingkan dengan 6 deskripsi gaya visual.
- Gaya terpilih adalah yang mendapat skor softmax tertinggi.

**6 Kategori Gaya:**
- *Fotografi* — gambar fotografis realistis
- *Ilustrasi Datar* — flat design, warna solid, bentuk geometris
- *Gambar Tangan* — sketsa, cat air, pensil, ilustrasi ekspresif
- *Dominan Teks* — teks mendominasi lebih dari visual
- *Abstrak* — bentuk non-representasional, pola, tekstur
- *Kolase* — gabungan elemen dari berbagai sumber

**Akurasi estimasi:** Validasi manual 200 sampel: akurasi top-1 CLIP ~72%.
Fotografi paling presisi (>90%). Kolase dan Abstrak sering tertukar (~55% akurasi per kelas).
YOLO dan DETR setuju pada keberadaan manusia di ~83% kasus.
        """)

    col1, col2 = st.columns([2,1])
    with col2:
        st.markdown("**Cari buku berdasarkan gaya ilustrasi**")
        gaya_opts = ["Semua"] + [GAYA_ID[k] for k in GAYA_ID]
        gaya_sel  = st.selectbox("Gaya ilustrasi", gaya_opts, key="gi_search")
        n_gi      = st.slider("Jumlah buku", 4, 24, 8, 4, key="gi_n")
        manusia_sel = st.checkbox("Hanya yang ada figur manusia", key="gi_manusia")

    with col1:
        st.markdown("**Distribusi Gaya Ilustrasi**")
        gc = df_f["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        fig = px.bar(gc, x=gc.values, y=gc.index, orientation="h",
                     color_discrete_sequence=["#43A047"],
                     text=gc.values)
        fig.update_layout(
            **plotly_layout(300), showlegend=False,
            xaxis_title="Jumlah Sampul", yaxis_title="",
            yaxis=dict(categoryorder="total ascending")
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True, key="gi_dist")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Tren Gaya Ilustrasi per Tahun**")
        dfg = df_f[(df_f["YEAR"] > 0) & df_f["gaya_ilustrasi"].notna()].copy()
        dfg["gaya_label"] = dfg["gaya_ilustrasi"].map(GAYA_ID)
        trend_g = dfg.groupby(["YEAR","gaya_label"]).size().reset_index(name="n")
        fig_tr = px.bar(trend_g, x="YEAR", y="n", color="gaya_label",
                        barmode="stack",
                        color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_tr.update_layout(
            **plotly_layout(310, showlegend=True),
            legend=dict(orientation="h", y=-0.25, font=dict(size=10)),
            xaxis_title="", yaxis_title="",
        )
        st.plotly_chart(fig_tr, use_container_width=True, key="gi_trend")

    with col4:
        st.markdown("**Kehadiran Figur Manusia**")
        yolo_human   = int(df_f["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
        detr_human   = int(df_f["detr_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
        total        = len(df_f)
        agree_human  = int((
            df_f["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") &
            df_f["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")
        ).sum())

        fig_mn = go.Figure(data=[go.Bar(
            name="YOLOv8n",
            x=["Ada manusia","Tidak ada"],
            y=[yolo_human, total - yolo_human],
            marker_color=["#66BB6A","#EF9A9A"],
        ), go.Bar(
            name="DETR",
            x=["Ada manusia","Tidak ada"],
            y=[detr_human, total - detr_human],
            marker_color=["#42A5F5","#FFB74D"],
        )])
        fig_mn.update_layout(
            **plotly_layout(310, showlegend=True, barmode="group"),
            legend=dict(orientation="h", y=-0.2),
            xaxis_title="", yaxis_title="",
        )
        st.plotly_chart(fig_mn, use_container_width=True, key="gi_human")
        st.markdown(
            f"<small>YOLOv8 & DETR sepakat pada **{agree_human:,}** sampul "
            f"({agree_human/total*100:.1f}%)</small>",
            unsafe_allow_html=True
        )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Kartu buku
    df_buku_gi = df_f[df_f["image_ok"]].copy()
    if manusia_sel:
        df_buku_gi = df_buku_gi[
            df_buku_gi["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") |
            df_buku_gi["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")
        ]
    if gaya_sel != "Semua":
        gaya_map_rev = {v: k for k, v in GAYA_ID.items()}
        key_gaya = gaya_map_rev.get(gaya_sel, gaya_sel)
        df_buku_gi = df_buku_gi[df_buku_gi["gaya_ilustrasi"] == key_gaya]

    df_buku_gi = df_buku_gi.head(n_gi)
    label = gaya_sel if gaya_sel != "Semua" else "semua gaya"
    if manusia_sel:
        label += " · dengan manusia"
    st.markdown(f"**Contoh sampul — {label}**")
    render_book_cards(df_buku_gi, max_cols=8)


# ═════════════════════════════════════════════════════════════
# HALAMAN: GENRE
# ═════════════════════════════════════════════════════════════
elif halaman == "Genre":
    st.markdown("## Analisis Genre")

    with st.expander("Catatan metodologi genre", expanded=False):
        st.markdown("""
**Sumber data genre:** Genre diambil dari metadata Goodreads yang ditetapkan oleh pembaca
melalui sistem *shelving*. Setiap buku dapat memiliki lebih dari satu genre (multi-label).

**Pengolahan:**
- Semua buku diberi label *Sastra Indonesia* sebagai genre dasar.
- Buku tanpa genre diisi berdasarkan rak Goodreads-nya (fiksi, nonfiksi, puisi).
- Genre diterjemahkan ke Bahasa Indonesia.
- Overlap genre divisualisasikan untuk melihat ko-okurensi antar genre.

**Keterbatasan:** Label genre Goodreads bersifat *crowd-sourced* dan tidak konsisten antar buku.
Genre seperti "Novel" dan "Fiksi" sering tumpang tindih secara konseptual.
        """)

    # Semua genre
    all_gc = all_genre_counts(df_f)
    top_genres = [g for g, _ in all_gc.most_common(30)]
    top_counts = [all_gc[g] for g in top_genres]

    col1, col2 = st.columns([2,1])
    with col2:
        st.markdown("**Cari buku berdasarkan genre**")
        top20 = [g for g, _ in all_gc.most_common(20)]
        genre_sel = st.selectbox("Genre", ["Semua"] + top20, key="genre_search")
        n_genre = st.slider("Jumlah buku", 4, 24, 8, 4, key="genre_n")

    with col1:
        st.markdown("**30 Genre Terbanyak**")
        fig_g = px.bar(
            x=top_counts[::-1], y=top_genres[::-1], orientation="h",
            color_discrete_sequence=["#FB8C00"],
            text=top_counts[::-1],
        )
        fig_g.update_layout(
            **plotly_layout(520), showlegend=False,
            xaxis_title="Jumlah Buku", yaxis_title="",
        )
        fig_g.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig_g, use_container_width=True, key="genre_dist")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Genre overlap
    st.markdown("**Tumpang Tindih Genre (Ko-okurensi)**")
    st.markdown(
        "<small>Menampilkan pasangan genre yang paling sering muncul bersama pada satu buku.</small>",
        unsafe_allow_html=True
    )

    top10_genres = [g for g, _ in all_gc.most_common(12) if g != "Sastra Indonesia"][:10]
    co_matrix = pd.DataFrame(0, index=top10_genres, columns=top10_genres)
    for glist in expand_genres(df_f["GENRES"]):
        relevant = [g for g in glist if g in top10_genres]
        for i, g1 in enumerate(relevant):
            for g2 in relevant[i+1:]:
                co_matrix.loc[g1, g2] += 1
                co_matrix.loc[g2, g1] += 1

    fig_heat = px.imshow(
        co_matrix,
        color_continuous_scale="Oranges",
        aspect="auto",
        text_auto=True,
    )
    fig_heat.update_layout(
        **plotly_layout(400),
        xaxis_title="", yaxis_title="",
        coloraxis_showscale=False,
    )
    fig_heat.update_traces(textfont_size=10)
    st.plotly_chart(fig_heat, use_container_width=True, key="genre_heat")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Kartu buku per genre
    if genre_sel == "Semua":
        df_buku_g = df_f[df_f["image_ok"]].sample(min(n_genre, len(df_f[df_f["image_ok"]])), random_state=9)
    else:
        mask = df_f["GENRES"].apply(
            lambda x: genre_sel in [g.strip() for g in str(x).split(",")]
        )
        df_buku_g = df_f[mask & df_f["image_ok"]].head(n_genre)

    st.markdown(f"**Contoh sampul — {genre_sel}**")
    render_book_cards(df_buku_g, max_cols=8)


# ═════════════════════════════════════════════════════════════
# HALAMAN: JELAJAH BUKU
# ═════════════════════════════════════════════════════════════
elif halaman == "Jelajah Buku":
    st.markdown("## Jelajah Buku")
    st.markdown("Temukan buku berdasarkan kombinasi kriteria visual dan metadata.")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        cari_judul = st.text_input("Cari judul / penulis", "", key="jelajah_q")
    with col_f2:
        warna_j  = st.selectbox("Warna", ["Semua"] + sorted(df_f["warna_kategori"].dropna().unique().tolist()), key="j_warna")
    with col_f3:
        tf_j     = st.selectbox("Tipografi", ["Semua"] + [TYPEFACE_ID[k] for k in TYPEFACE_ID if k != "unknown"], key="j_tf")
    with col_f4:
        gaya_j   = st.selectbox("Gaya ilustrasi", ["Semua"] + [GAYA_ID[k] for k in GAYA_ID], key="j_gaya")

    col_f5, col_f6 = st.columns([1,3])
    with col_f5:
        all_gc_j   = all_genre_counts(df_f)
        top20_j    = [g for g, _ in all_gc_j.most_common(20)]
        genre_j    = st.selectbox("Genre", ["Semua"] + top20_j, key="j_genre")
        manusia_j  = st.checkbox("Ada figur manusia", key="j_manusia")
        n_hasil    = st.slider("Tampilkan", 8, 48, 16, 8, key="j_n")

    # Terapkan filter
    dj = df_f.copy()

    if cari_judul:
        q = cari_judul.lower()
        dj = dj[
            dj["TITLE"].str.lower().str.contains(q, na=False) |
            dj["AUTHOR"].str.lower().str.contains(q, na=False)
        ]
    if warna_j != "Semua":
        dj = dj[dj["warna_kategori"] == warna_j]
    if tf_j != "Semua":
        tf_map_rev2 = {v: k for k, v in TYPEFACE_ID.items()}
        dj = dj[dj["typeface_kategori"] == tf_map_rev2.get(tf_j, tf_j)]
    if gaya_j != "Semua":
        gaya_map_rev2 = {v: k for k, v in GAYA_ID.items()}
        dj = dj[dj["gaya_ilustrasi"] == gaya_map_rev2.get(gaya_j, gaya_j)]
    if genre_j != "Semua":
        dj = dj[dj["GENRES"].apply(
            lambda x: genre_j in [g.strip() for g in str(x).split(",")]
        )]
    if manusia_j:
        dj = dj[
            dj["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") |
            dj["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")
        ]

    dj_img = dj[dj["image_ok"]]
    st.markdown(f"**{len(dj_img):,} buku ditemukan**")

    if len(dj_img) > 0:
        render_book_cards(dj_img.head(n_hasil), max_cols=8)
    else:
        st.info("Tidak ada buku yang cocok dengan filter yang dipilih.")
