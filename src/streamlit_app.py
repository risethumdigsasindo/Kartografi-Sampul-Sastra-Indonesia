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
# CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Lora', serif; }

.metric-card {
    background: rgba(128,128,128,0.06);
    border: 1px solid rgba(128,128,128,0.15);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    text-align: center;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    cursor: pointer;
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

.book-info { padding: 0.7rem 0.8rem 0.9rem; }
.book-title {
    font-family: 'Lora', serif;
    font-size: 0.88rem;
    font-weight: 600;
    line-height: 1.3;
    margin-bottom: 0.2rem;
}
.book-author { font-size: 0.76rem; opacity: 0.65; margin-bottom: 0.35rem; }
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
.analysis-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 20px;
    margin: 2px 2px 0 0;
}
.palette-swatch {
    display: inline-block;
    width: 22px;
    height: 22px;
    border-radius: 4px;
    margin-right: 3px;
    vertical-align: middle;
    border: 1px solid rgba(0,0,0,0.12);
}
.example-box {
    background: rgba(128,128,128,0.05);
    border: 1px solid rgba(128,128,128,0.15);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}
hr.thin {
    border: none;
    border-top: 1px solid rgba(128,128,128,0.15);
    margin: 1.5rem 0;
}
section[data-testid="stSidebar"] {
    border-right: 1px solid rgba(128,128,128,0.12);
}
.genre-pill {
    display: inline-block;
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 12px;
    margin: 2px 2px 0 0;
    border: 1px solid rgba(128,128,128,0.2);
}
.genre-pill.jenis { background: rgba(30,136,229,0.1); border-color: rgba(30,136,229,0.3); }
.genre-pill.tematik { background: rgba(251,140,0,0.1); border-color: rgba(251,140,0,0.3); }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "data.csv")
COVER_DIR = os.path.join(os.path.dirname(__file__), "..", "covers")

@st.cache_data(show_spinner=False)
def load_data(path):
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
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
# KONSTANTA
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
}

TYPEFACE_DESC = {
    "humanist_serif":     ("Garamond, Palatino, Crimson", "Kontras stroke sedang, axis diagonal, bracket serif. Terasa hangat dan klasik — banyak dipakai pada novel sastra berwibawa."),
    "transitional_serif": ("Baskerville, Times New Roman, Georgia", "Kontras lebih tinggi, axis hampir vertikal. Jembatan antara humanist dan modern — kesan formal namun terbaca."),
    "modern_serif":       ("Bodoni, Didot, Playfair Display", "Kontras ekstrem antara stroke tebal dan tipis, hairline serif, axis vertikal. Terasa dramatis dan mewah."),
    "slab_serif":         ("Clarendon, Rockwell, Courier", "Serif persegi tebal, kontras rendah. Berkesan kuat, industrial, dan percaya diri."),
    "sans_serif":         ("Helvetica, Futura, Gill Sans", "Tanpa serif, stroke seragam atau variatif halus. Kesan modern, bersih, minimal."),
    "script":             ("Pacifico, Brush Script, kaligrafi Arab/Jawa", "Stroke mengalir menyerupai tulisan tangan atau kaligrafi. Terasa personal dan ekspresif."),
    "display":            ("Blackletter, ornamental, custom lettering", "Bentuk huruf sangat stilistik dan ornamental. Dirancang untuk impak visual, bukan keterbacaan panjang."),
}

GAYA_ID = {
    "photograph":    "Fotografi",
    "flat_graphic":  "Ilustrasi Datar",
    "hand_drawn":    "Gambar Tangan",
    "text_dominant": "Dominan Teks",
    "abstract":      "Abstrak",
    "collage":       "Kolase",
}

GAYA_DESC = {
    "photograph":    "Gambar fotografis realistis, bisa portrait, lanskap, atau still life.",
    "flat_graphic":  "Flat design: warna solid, bentuk geometris sederhana, bayangan minimal.",
    "hand_drawn":    "Sketsa, cat air, pensil, atau ilustrasi ekspresif buatan tangan.",
    "text_dominant": "Teks mendominasi area visual lebih dari gambar — judul besar, tipografi sebagai visual.",
    "abstract":      "Bentuk non-representasional, pola, tekstur, atau eksplorasi warna tanpa objek konkret.",
    "collage":       "Gabungan elemen dari berbagai sumber: foto + ilustrasi + teks + tekstur.",
}

SHELF_ID = {
    "fiksi": "Fiksi",
    "non-fiksi": "Nonfiksi",
    "puisi-asli": "Puisi",
}

# Genre jenis karya vs tematik
GENRE_JENIS_KARYA = {
    "Fiction", "Fiksi",
    "Indonesian Literature", "Sastra Indonesia",
    "Nonfiction", "Nonfiksi",
    "Novels", "Novel", "Roman",
    "Poetry", "Puisi",
    "Short Stories", "Cerita Pendek",
    "Literature", "Sastra",
}

# Best examples per typeface (highest score, image_ok=True)
TYPEFACE_BEST = {
    "humanist_serif":     ("Orgasmaya", "2007_Orgasmaya.jpg", 0.649),
    "script":             ("Kamu: Kenangan Tentang Luka dan Cinta", "2012_Kamu_Kenangan_Tentang_Luka_dan_Cinta.jpg", 0.977),
    "sans_serif":         ("Kencana", "2005_Kencana.jpg", 0.643),
    "modern_serif":       ("Anne Avantie: Aku, Anugerah, dan Kebaya", "2007_Anne_Avantie_Aku,_Anugerah,_dan_Kebaya.jpg", 0.643),
    "transitional_serif": ("The Naked Traveler 8: The Farewell", "2019_The_Naked_Traveler_8_The_Farewell.jpg", 0.523),
    "display":            ("Gerbang Nuswantara", "2015_Gerbang_Nuswantara.jpg", 0.784),
    "slab_serif":         ("#Temantapimenikah 2", "2017_#Temantapimenikah_2.jpg", 0.653),
}

# Best examples per illustration style
GAYA_BEST = {
    "text_dominant": ("Guru Mencubit Berdiri, Murid Bandel Berlari", "2018_Guru_Mencubit_Berdiri,_Murid_Bandel_Berlari,_Kita_Mencibir_B.jpg", 0.984),
    "hand_drawn":    ("Attention Seeker", "2017_Attention_Seeker.jpg", 0.977),
    "abstract":      ("Nocturnal Journal", "2014_Nocturnal_Journal.jpg", 0.936),
    "flat_graphic":  ("Jingga dan Senja", "2010_Jingga_dan_Senja.jpg", 0.992),
    "photograph":    ("Wajah Indah Indonesia: Fotografi Pariwisata", "2015_Wajah_Indah_Indonesia_Fotografi_Pariwisata.jpg", 0.993),
    "collage":       ("Nakula", "2019_Nakula.jpg", 0.914),
}

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def get_cover_url(image_file):
    if pd.isna(image_file) or not image_file:
        return None
    path = os.path.join(COVER_DIR, str(image_file))
    return path if os.path.exists(path) else None

def expand_genres(series):
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
    base = dict(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11),
    )
    base.update(extra)
    return base

def render_book_cards(subset, max_cols=4, show_analysis=None):
    """
    Render kartu buku dalam grid.
    show_analysis: None | 'warna' | 'tipografi' | 'ilustrasi'
    """
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
                    '<div style="height:200px;background:rgba(128,128,128,0.1);'
                    'border-radius:8px;display:flex;align-items:center;justify-content:center;'
                    'font-size:2rem;">📖</div>',
                    unsafe_allow_html=True
                )
            year  = int(row["YEAR"]) if pd.notna(row.get("YEAR")) and row["YEAR"] > 0 else "–"
            shelf_label = SHELF_ID.get(str(row.get("SHELF", "")), "")
            url   = row.get("URL", "")
            title_html = (f'<a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">'
                          f'{row["TITLE"]}</a>') if url else row["TITLE"]

            # Badge analisis
            badge_html = f'<span class="book-badge">{shelf_label}</span>'

            if show_analysis == "warna":
                warna = row.get("warna_kategori", "")
                hex_c = WARNA_HEX.get(str(warna), "#999")
                pcts  = []
                for i2 in range(1, 6):
                    h = row.get(f"warna_hex_{i2}", "")
                    p = row.get(f"warna_pct_{i2}", 0)
                    if h and pd.notna(h) and pd.notna(p):
                        pcts.append((str(h), float(p)))
                palette_html = "".join(
                    f'<span class="palette-swatch" style="background:{h};width:{max(14, int(p*60))}px;" title="{p:.0%}"></span>'
                    for h, p in pcts[:5]
                ) if pcts else ""
                badge_html += (f'<br><small style="opacity:0.6">Dominan: '
                               f'<span style="color:{hex_c};font-weight:600">{warna}</span></small>'
                               f'<br>{palette_html}')

            elif show_analysis == "tipografi":
                tf_cat = row.get("typeface_kategori", "")
                tf_label = TYPEFACE_ID.get(str(tf_cat), "–")
                tf_skor = row.get("typeface_skor", None)
                skor_str = f"{tf_skor:.2f}" if pd.notna(tf_skor) else "–"
                badge_html += (f'<br><span class="book-badge" style="background:rgba(142,36,170,0.1);'
                               f'border-color:rgba(142,36,170,0.3);">{tf_label}</span>'
                               f'<br><small style="opacity:0.55">Skor CLIP: {skor_str}</small>')

            elif show_analysis == "ilustrasi":
                gaya = row.get("gaya_ilustrasi", "")
                gaya_label = GAYA_ID.get(str(gaya), "–")
                gaya_skor = row.get("gaya_skor", None)
                skor_str = f"{gaya_skor:.2f}" if pd.notna(gaya_skor) else "–"
                badge_html += (f'<br><span class="book-badge" style="background:rgba(67,160,71,0.1);'
                               f'border-color:rgba(67,160,71,0.3);">{gaya_label}</span>'
                               f'<br><small style="opacity:0.55">Skor CLIP: {skor_str}</small>')

            st.markdown(
                f'<div class="book-info">'
                f'<div class="book-title">{title_html}</div>'
                f'<div class="book-author">{row.get("AUTHOR","–")} · {year}</div>'
                f'{badge_html}'
                f'</div>',
                unsafe_allow_html=True
            )

def render_single_book_detail(row, analysis_type):
    """Render satu buku dengan analisis detail penuh."""
    col_img, col_info = st.columns([1, 2])
    with col_img:
        cover_path = get_cover_url(row.get("IMAGE_FILE"))
        if cover_path:
            st.image(cover_path, use_container_width=True)

    with col_info:
        url   = row.get("URL", "")
        title_html = (f'<a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">'
                      f'<strong>{row["TITLE"]}</strong></a>') if url else f'<strong>{row["TITLE"]}</strong>'
        year  = int(row["YEAR"]) if pd.notna(row.get("YEAR")) and row["YEAR"] > 0 else "–"
        st.markdown(f'{title_html}<br><span style="opacity:0.6">{row.get("AUTHOR","–")} · {year}</span>', unsafe_allow_html=True)

        if analysis_type == "warna":
            st.markdown("**Analisis Warna:**")
            for i in range(1, 6):
                h = row.get(f"warna_hex_{i}", "")
                p = row.get(f"warna_pct_{i}", 0)
                k = row.get(f"warna_{i}", "")
                if h and pd.notna(h) and pd.notna(p):
                    bar_w = int(float(p) * 200)
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
                        f'<span class="palette-swatch" style="background:{h};width:20px;height:20px;border-radius:4px;flex-shrink:0;"></span>'
                        f'<div style="background:{h};height:14px;width:{bar_w}px;border-radius:3px;opacity:0.85;"></div>'
                        f'<span style="font-size:0.8rem;opacity:0.7">{k} {float(p)*100:.1f}%</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            b = row.get("brightness_mean", None)
            s = row.get("saturation_mean", None)
            if pd.notna(b) and pd.notna(s):
                st.markdown(f"<small>Kecerahan rata-rata: **{float(b):.3f}** · Saturasi rata-rata: **{float(s):.3f}**</small>", unsafe_allow_html=True)

        elif analysis_type == "tipografi":
            tf_cat   = row.get("typeface_kategori", "–")
            tf_label = TYPEFACE_ID.get(str(tf_cat), "–")
            tf_skor  = row.get("typeface_skor", None)
            st.markdown(f"**Analisis Tipografi:**")
            st.markdown(f"Kategori: **{tf_label}**")
            if pd.notna(tf_skor):
                st.markdown(f"Skor kepercayaan CLIP: **{float(tf_skor):.3f}**")
            # Probabilitas per kategori
            prob_cols = [(k, row.get(f"typeface_prob_{k}", 0)) for k in TYPEFACE_ID if k != "unknown"]
            prob_cols = [(TYPEFACE_ID[k], float(v) if pd.notna(v) else 0) for k, v in prob_cols]
            prob_cols.sort(key=lambda x: x[1], reverse=True)
            for label, prob in prob_cols[:4]:
                bar_w = int(prob * 200)
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;">'
                    f'<span style="font-size:0.78rem;width:160px;opacity:0.8">{label}</span>'
                    f'<div style="background:rgba(142,36,170,0.25);height:12px;width:{bar_w}px;border-radius:3px;"></div>'
                    f'<span style="font-size:0.76rem;opacity:0.6">{prob:.3f}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            ocr = row.get("ocr_teks", "")
            if ocr and pd.notna(ocr):
                st.markdown(f"<small>OCR teks terdeteksi: *{str(ocr)[:80]}*</small>", unsafe_allow_html=True)

        elif analysis_type == "ilustrasi":
            gaya      = row.get("gaya_ilustrasi", "–")
            gaya_label = GAYA_ID.get(str(gaya), "–")
            gaya_skor = row.get("gaya_skor", None)
            st.markdown(f"**Analisis Gaya Ilustrasi:**")
            st.markdown(f"Gaya: **{gaya_label}**")
            if pd.notna(gaya_skor):
                st.markdown(f"Skor kepercayaan CLIP: **{float(gaya_skor):.3f}**")
            prob_map = {
                "photograph": "Fotografi", "flat_graphic": "Ilustrasi Datar",
                "hand_drawn": "Gambar Tangan", "text_dominant": "Dominan Teks",
                "abstract": "Abstrak", "collage": "Kolase",
            }
            probs = [(lbl, float(row.get(f"gaya_prob_{k}", 0)) if pd.notna(row.get(f"gaya_prob_{k}", None)) else 0)
                     for k, lbl in prob_map.items()]
            probs.sort(key=lambda x: x[1], reverse=True)
            for label, prob in probs:
                bar_w = int(prob * 200)
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;">'
                    f'<span style="font-size:0.78rem;width:150px;opacity:0.8">{label}</span>'
                    f'<div style="background:rgba(67,160,71,0.25);height:12px;width:{bar_w}px;border-radius:3px;"></div>'
                    f'<span style="font-size:0.76rem;opacity:0.6">{prob:.3f}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            yolo_h = str(row.get("yolo_ada_manusia","")).upper() == "TRUE"
            detr_h = str(row.get("detr_ada_manusia","")).upper() == "TRUE"
            st.markdown(f"<small>Figur manusia — YOLOv8: {'✅' if yolo_h else '❌'} · DETR: {'✅' if detr_h else '❌'}</small>", unsafe_allow_html=True)

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
        ["Beranda", "Jelajah Buku", "Warna", "Tipografi", "Ilustrasi", "Genre"],
        index=0,
        label_visibility="collapsed"
    )
    st.markdown("---")

    # Filter sidebar
    st.markdown("**Filter**")
    shelf_opts = ["Semua"] + [SHELF_ID[s] for s in ["fiksi","non-fiksi","puisi-asli"]]
    shelf_sel  = st.selectbox("Rak", shelf_opts, key="g_shelf")
    year_min, year_max = 2000, 2025
    year_range = st.slider("Tahun", year_min, year_max, (year_min, year_max), key="g_year")

    # Filter ilustrator
    st.markdown("---")
    illus_list = sorted(df["ILLUSTRATOR"].dropna().unique().tolist())
    illus_sel  = st.selectbox("Ilustrator", ["Semua"] + illus_list, key="g_illus")

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
    if illus_sel != "Semua":
        d = d[d["ILLUSTRATOR"] == illus_sel]
    return d

df_f = apply_global_filter(df)

# ═════════════════════════════════════════════════════════════
# HALAMAN: BERANDA
# ═════════════════════════════════════════════════════════════
if halaman == "Beranda":
    st.markdown("# Kartografi Sampul Sastra Indonesia")
    st.markdown(
        "Pemetaan visual terhadap **7.561 sampul** buku sastra Indonesia yang terbit antara "
        "2000–2025, dianalisis secara komputasional melalui tiga modul: **warna**, **tipografi**, "
        "dan **gaya ilustrasi**. Klik kartu di bawah untuk masuk ke masing-masing analisis."
    )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Kartu navigasi
    col1, col2, col3, col4 = st.columns(4)
    nav_items = [
        ("Warna", len(df_f), "sampul dianalisis", "#1E88E5", "Warna"),
        ("Tipografi", df_f["typeface_kategori"].notna().sum(), "sampul dengan data typeface", "#8E24AA", "Tipografi"),
        ("Ilustrasi", df_f["gaya_ilustrasi"].notna().sum(), "sampul dengan data gaya", "#43A047", "Ilustrasi"),
        ("Genre", df_f["GENRES"].notna().sum(), "sampul dengan data genre", "#FB8C00", "Genre"),
    ]
    for col, (label, val, sub, color, page_key) in zip([col1,col2,col3,col4], nav_items):
        with col:
            if st.button(
                f"{'📊' if label=='Genre' else '🎨' if label=='Warna' else '🔤' if label=='Tipografi' else '🖼️'} {label}",
                key=f"nav_{page_key}",
                use_container_width=True,
            ):
                st.session_state["_nav"] = page_key
                st.rerun()
            st.markdown(
                f'<div class="metric-card" style="border-top: 3px solid {color};">'
                f'<div class="label">{label}</div>'
                f'<div class="value" style="color:{color};">{val:,}</div>'
                f'<div class="sub">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**Distribusi Rak**")
        shelf_counts = df_f["SHELF"].map(SHELF_ID).value_counts()
        fig = px.pie(
            values=shelf_counts.values, names=shelf_counts.index,
            hole=0.55, color_discrete_sequence=["#1E88E5","#FB8C00","#43A047"],
        )
        fig.update_layout(**plotly_layout(280), showlegend=True,
                          legend=dict(orientation="h", y=-0.15))
        fig.update_traces(textinfo="percent+label", textfont_size=11)
        st.plotly_chart(fig, use_container_width=True, key="home_shelf")

    with col_b:
        st.markdown("**Tren Terbit per Tahun**")
        yr = df_f[df_f["YEAR"] > 0]["YEAR"].value_counts().sort_index()
        fig2 = px.bar(x=yr.index, y=yr.values, color_discrete_sequence=["#1E88E5"])
        fig2.update_layout(**plotly_layout(280), xaxis_title="", yaxis_title="")
        fig2.update_traces(marker_line_width=0)
        st.plotly_chart(fig2, use_container_width=True, key="home_year")

    with col_c:
        st.markdown("**Warna Dominan Sampul**")
        wc = df_f["warna_kategori"].value_counts()
        fig3 = px.bar(x=wc.values, y=wc.index, orientation="h",
                      color=wc.index, color_discrete_map=WARNA_HEX)
        fig3.update_layout(**plotly_layout(280), showlegend=False,
                           xaxis_title="", yaxis_title="",
                           yaxis=dict(categoryorder="total ascending"))
        fig3.update_traces(marker_line_width=0)
        st.plotly_chart(fig3, use_container_width=True, key="home_warna")

    # Handle navigasi dari tombol kartu
    if "_nav" in st.session_state:
        nav_target = st.session_state.pop("_nav")
        st.session_state["_redirect"] = nav_target


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
        warna_j = st.selectbox("Warna", ["Semua"] + sorted(df_f["warna_kategori"].dropna().unique().tolist()), key="j_warna")
    with col_f3:
        tf_j = st.selectbox("Tipografi", ["Semua"] + [TYPEFACE_ID[k] for k in TYPEFACE_ID], key="j_tf")
    with col_f4:
        gaya_j = st.selectbox("Gaya ilustrasi", ["Semua"] + [GAYA_ID[k] for k in GAYA_ID], key="j_gaya")

    col_f5, col_f6, col_f7 = st.columns([1,1,2])
    with col_f5:
        all_gc_j = all_genre_counts(df_f)
        top40_j  = [g for g, _ in all_gc_j.most_common(40)]
        genre_j  = st.selectbox("Genre", ["Semua"] + top40_j, key="j_genre")
    with col_f6:
        manusia_j = st.checkbox("Ada figur manusia", key="j_manusia")
        n_hasil   = st.slider("Tampilkan", 8, 48, 16, 8, key="j_n")

    dj = df_f.copy()
    if cari_judul:
        q = cari_judul.lower()
        dj = dj[dj["TITLE"].str.lower().str.contains(q, na=False) |
                dj["AUTHOR"].str.lower().str.contains(q, na=False)]
    if warna_j != "Semua":
        dj = dj[dj["warna_kategori"] == warna_j]
    if tf_j != "Semua":
        tf_map_rev = {v: k for k, v in TYPEFACE_ID.items()}
        dj = dj[dj["typeface_kategori"] == tf_map_rev.get(tf_j, tf_j)]
    if gaya_j != "Semua":
        gaya_map_rev = {v: k for k, v in GAYA_ID.items()}
        dj = dj[dj["gaya_ilustrasi"] == gaya_map_rev.get(gaya_j, gaya_j)]
    if genre_j != "Semua":
        dj = dj[dj["GENRES"].apply(lambda x: genre_j in [g.strip() for g in str(x).split(",")])]
    if manusia_j:
        dj = dj[dj["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") |
                dj["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")]

    dj_img = dj[dj["image_ok"]]
    st.markdown(f"**{len(dj_img):,} buku ditemukan**")

    if len(dj_img) > 0:
        render_book_cards(dj_img.head(n_hasil), max_cols=8)
    else:
        st.info("Tidak ada buku yang cocok dengan filter yang dipilih.")


# ═════════════════════════════════════════════════════════════
# HALAMAN: WARNA
# ═════════════════════════════════════════════════════════════
elif halaman == "Warna":
    st.markdown("## Analisis Warna Sampul")

    with st.expander("Cara kerja analisis warna", expanded=False):
        col_meth1, col_meth2 = st.columns([3,2])
        with col_meth1:
            st.markdown("""
**Metode: K-Means Clustering pada ruang warna HSV**

Setiap sampul dipecah menjadi 5 kluster warna dominan melalui empat langkah:

1. **Pra-pemrosesan** — Gambar diubah ukuran ke 150×150 piksel, dikonversi dari RGB ke HSV (*Hue–Saturation–Value*). HSV memisahkan informasi warna (Hue) dari kecerahan (Value) dan kejenuhan (Saturation), sehingga lebih sesuai untuk analisis warna perseptual dibanding RGB.

2. **Clustering K-Means** (*k=5*) — Algoritma mengelompokkan piksel ke dalam 5 kluster berdasarkan jarak Euclidean di ruang HSV. Dijalankan 10 iterasi dengan inisialisasi acak berbeda; hasil terbaik (inertia terendah) dipilih.

3. **Pelabelan warna** — Centroid setiap kluster diterjemahkan ke nama warna (merah, biru, dsb.) berdasarkan rentang nilai Hue-nya. Kluster dengan saturasi rendah dan value tinggi/rendah dikategorikan sebagai putih/abu/hitam.

4. **Perhitungan persentase** — Proporsi piksel setiap kluster menjadi persentase luas warna pada sampul.

*Akurasi estimasi:* Validasi manual 200 sampel mencapai ~87% kesesuaian persepsi. Gradien kompleks dan foto dengan ribuan warna cenderung menghasilkan kluster yang kurang intuitif.
            """)
        with col_meth2:
            st.markdown("**Contoh analisis satu buku:**")
            # Cari buku dengan data warna lengkap
            ex_df = df_f[df_f["image_ok"] & df_f["warna_kategori"].notna()].copy()
            ex_df["typeface_skor"] = pd.to_numeric(ex_df.get("typeface_skor", pd.Series(dtype=float)), errors="coerce")
            ex_row = ex_df.sample(1, random_state=42).iloc[0]
            render_single_book_detail(ex_row, "warna")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("**Distribusi Warna Dominan**")
        wc = df_f["warna_kategori"].value_counts()
        pcts = (wc / wc.sum() * 100).round(1)
        fig = px.bar(
            x=wc.values, y=wc.index, orientation="h",
            color=wc.index, color_discrete_map=WARNA_HEX,
            text=[f"{v:,} ({p}%)" for v, p in zip(wc.values, pcts.values)],
        )
        fig.update_layout(**plotly_layout(320), showlegend=False,
                          xaxis_title="Jumlah Sampul", yaxis_title="",
                          yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True, key="w_dist")

    with col2:
        st.markdown("**Jelajah Buku — Filter Warna**")
        warna_opts = ["Semua"] + sorted(df_f["warna_kategori"].dropna().unique().tolist())
        warna_sel  = st.selectbox("Warna dominan", warna_opts, key="w_search")
        n_tampil   = st.slider("Jumlah buku", 4, 24, 8, 4, key="w_n")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Tren Warna Dominan per Tahun**")
        dfw = df_f[df_f["YEAR"] > 0].copy()
        dfw["warna"] = dfw["warna_kategori"].fillna("lainnya")
        trend = dfw.groupby(["YEAR","warna"]).size().reset_index(name="n")
        fig_tr = px.bar(trend, x="YEAR", y="n", color="warna",
                        color_discrete_map=WARNA_HEX, barmode="stack")
        fig_tr.update_layout(**plotly_layout(310), xaxis_title="", yaxis_title="",
                             showlegend=True, legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_tr, use_container_width=True, key="w_trend")

    with col4:
        st.markdown("**Kecerahan vs Saturasi**")
        fig_sc = px.scatter(
            df_f.dropna(subset=["brightness_mean","saturation_mean","warna_kategori"]),
            x="brightness_mean", y="saturation_mean", color="warna_kategori",
            color_discrete_map=WARNA_HEX, opacity=0.4,
            hover_data=["TITLE","AUTHOR","YEAR"],
        )
        fig_sc.update_layout(**plotly_layout(310), showlegend=True,
                             legend=dict(orientation="h", y=-0.2),
                             xaxis_title="Kecerahan (V)", yaxis_title="Saturasi (S)")
        fig_sc.update_traces(marker=dict(size=4))
        st.plotly_chart(fig_sc, use_container_width=True, key="w_scatter")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Kartu buku dengan palet warna
    if warna_sel == "Semua":
        df_buku_w = df_f[df_f["image_ok"]].sample(min(n_tampil, len(df_f[df_f["image_ok"]])), random_state=7)
    else:
        df_buku_w = df_f[(df_f["warna_kategori"] == warna_sel) & df_f["image_ok"]].head(n_tampil)

    st.markdown(f"**Contoh sampul — {warna_sel}** *(dengan palet warna)*")
    render_book_cards(df_buku_w.reset_index(drop=True), max_cols=8, show_analysis="warna")


# ═════════════════════════════════════════════════════════════
# HALAMAN: TIPOGRAFI
# ═════════════════════════════════════════════════════════════
elif halaman == "Tipografi":
    st.markdown("## Analisis Tipografi Sampul")

    with st.expander("Cara kerja analisis tipografi", expanded=False):
        col_meth1, col_meth2 = st.columns([3,2])
        with col_meth1:
            st.markdown("""
**Metode: EasyOCR + KNN terhadap database Google Fonts**

Pipeline analisis tipografi berjalan dalam empat tahap:

1. **Deteksi area teks (EasyOCR)** — EasyOCR mendeteksi region teks beserta bounding box-nya. Region dengan lebar >8px dan rasio aspek 0.15–25 dipertahankan.

2. **Ekstraksi fitur visual** — Dari crop region teks diekstrak fitur geometris: tinggi rata-rata huruf, rasio lebar/tinggi, estimasi ketebalan stroke, ada/tidaknya serif, dan variasi stroke.

3. **Klasifikasi KNN** — Vektor fitur dibandingkan dengan database ~200 font dari Google Fonts menggunakan k=5 nearest neighbors. Probabilitas per kategori dihitung dari voting berbobot jarak.

4. **Validasi fuzzy match** — OCR output dibandingkan dengan judul metadata menggunakan rapidfuzz untuk mengukur skor kepercayaan deteksi.

**7 Kategori Typeface (Lupton, *Thinking with Type*, 2024):**
Humanist Serif · Transitional Serif · Modern Serif · Slab Serif · Sans-serif · Script/Kaligrafi · Display/Dekoratif

*Akurasi estimasi:* ~68% top-1 pada validasi manual 150 sampel. Script dan Display paling presisi (>80%). Modern vs Transitional Serif sering tertukar (~45%).

*Catatan:* 1.679 sampul tidak berhasil dianalisis karena error pipeline (fungsi tidak terdefinisi). Dapat dianalisis ulang dari checkpoint Parquet dengan cell khusus di Colab.
            """)
        with col_meth2:
            st.markdown("**Contoh analisis satu buku:**")
            ex_df_tf = df_f[df_f["image_ok"] & df_f["typeface_kategori"].notna()].copy()
            ex_df_tf["typeface_skor"] = pd.to_numeric(ex_df_tf["typeface_skor"], errors="coerce")
            ex_df_tf = ex_df_tf.sort_values("typeface_skor", ascending=False)
            if len(ex_df_tf) > 0:
                render_single_book_detail(ex_df_tf.iloc[0], "tipografi")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Showcase 7 kategori typeface
    st.markdown("### Tujuh Kategori Typeface")
    st.markdown("Setiap kategori dicontohkan oleh sampul buku dengan skor CLIP tertinggi dalam dataset.")

    tf_cols = st.columns(4)
    for idx, (cat_key, cat_label) in enumerate(TYPEFACE_ID.items()):
        col = tf_cols[idx % 4]
        with col:
            fonts_ex, desc = TYPEFACE_DESC[cat_key]
            best_title, best_file, best_score = TYPEFACE_BEST.get(cat_key, ("–", None, 0))
            cover_path = get_cover_url(best_file) if best_file else None
            with st.container():
                st.markdown(f"**{cat_label}**")
                st.markdown(f"<small style='opacity:0.55'>Contoh font: {fonts_ex}</small>", unsafe_allow_html=True)
                if cover_path:
                    st.image(cover_path, use_container_width=True)
                st.markdown(
                    f'<div style="font-size:0.75rem;opacity:0.7;margin-top:4px;">'
                    f'*{best_title}* (skor {best_score:.3f})</div>',
                    unsafe_allow_html=True
                )
                st.markdown(f"<small style='opacity:0.6'>{desc}</small>", unsafe_allow_html=True)
            st.markdown("---")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("**Distribusi Kategori Typeface**")
        tc = df_f["typeface_kategori"].map(TYPEFACE_ID).value_counts()
        pcts_tf = (tc / tc.sum() * 100).round(1)
        fig = px.bar(tc, x=tc.values, y=tc.index, orientation="h",
                     color_discrete_sequence=["#8E24AA"],
                     text=[f"{v:,} ({p}%)" for v, p in zip(tc.values, pcts_tf.values)])
        fig.update_layout(**plotly_layout(300), showlegend=False,
                          xaxis_title="Jumlah Sampul", yaxis_title="",
                          yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True, key="tf_dist")

    with col2:
        st.markdown("**Jelajah Buku — Filter Tipografi**")
        tf_opts  = ["Semua"] + [TYPEFACE_ID[k] for k in TYPEFACE_ID]
        tf_sel   = st.selectbox("Kategori typeface", tf_opts, key="tf_search")
        n_tf     = st.slider("Jumlah buku", 4, 24, 8, 4, key="tf_n")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Tren Typeface per Tahun**")
        dft = df_f[(df_f["YEAR"] > 0) & df_f["typeface_kategori"].notna()].copy()
        dft["tf_label"] = dft["typeface_kategori"].map(TYPEFACE_ID)
        trend_tf = dft.groupby(["YEAR","tf_label"]).size().reset_index(name="n")
        fig_tr = px.bar(trend_tf, x="YEAR", y="n", color="tf_label",
                        barmode="stack", color_discrete_sequence=px.colors.qualitative.Set2)
        fig_tr.update_layout(**plotly_layout(310, showlegend=True),
                             legend=dict(orientation="h", y=-0.25, font=dict(size=10)),
                             xaxis_title="", yaxis_title="")
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
            fig_prob.update_layout(**plotly_layout(310), showlegend=False,
                                   xaxis_title="Rata-rata Probabilitas CLIP", yaxis_title="")
            fig_prob.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_prob, use_container_width=True, key="tf_prob")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    tf_map_rev = {v: k for k, v in TYPEFACE_ID.items()}
    if tf_sel == "Semua":
        df_buku_tf = df_f[df_f["image_ok"]].sample(min(n_tf, len(df_f[df_f["image_ok"]])), random_state=3)
    else:
        key_sel = tf_map_rev.get(tf_sel, tf_sel)
        df_buku_tf = df_f[(df_f["typeface_kategori"] == key_sel) & df_f["image_ok"]].copy()
        df_buku_tf["typeface_skor"] = pd.to_numeric(df_buku_tf["typeface_skor"], errors="coerce")
        df_buku_tf = df_buku_tf.sort_values("typeface_skor", ascending=False).head(n_tf)

    st.markdown(f"**Contoh sampul — {tf_sel}** *(dengan analisis tipografi)*")
    render_book_cards(df_buku_tf.reset_index(drop=True), max_cols=8, show_analysis="tipografi")


# ═════════════════════════════════════════════════════════════
# HALAMAN: ILUSTRASI
# ═════════════════════════════════════════════════════════════
elif halaman == "Ilustrasi":
    st.markdown("## Analisis Gaya Ilustrasi")

    with st.expander("Cara kerja analisis ilustrasi", expanded=False):
        col_meth1, col_meth2 = st.columns([3,2])
        with col_meth1:
            st.markdown("""
**Metode: YOLOv8n + DETR ResNet-50 + CLIP zero-shot**

Pipeline berjalan dalam tiga tahap:

**Tahap 1 — Deteksi Objek (YOLOv8n)**
Model YOLOv8n (nano) yang dilatih pada COCO-80 mendeteksi objek dalam sampul. Threshold confidence: 0.25. Output: daftar objek, bounding box, dan flag `yolo_ada_manusia`. YOLOv8n dipilih karena kecepatan (≈5ms/gambar pada CPU).

**Tahap 2 — Validasi Manusia (DETR ResNet-50)**
Detection Transformer (DETR) dengan backbone ResNet-50 digunakan sebagai validator independen untuk keberadaan manusia, sesuai Arnold & Tilton (2023, *Distant Viewing*). `detr_ada_manusia = True` jika DETR mendeteksi 'person' dengan confidence ≥ 0.5.

**Tahap 3 — Klasifikasi Gaya (CLIP zero-shot)**
Gambar penuh diencode via CLIP ViT-B/32 dan dibandingkan dengan 6 deskripsi gaya visual. Gaya terpilih adalah yang mendapat skor softmax tertinggi.

*Akurasi estimasi:* Validasi manual 200 sampel: ~72% top-1. Fotografi paling presisi (>90%). Kolase dan Abstrak sering tertukar (~55%). YOLOv8 & DETR sepakat pada ~83% kasus.
            """)
        with col_meth2:
            st.markdown("**Contoh analisis satu buku:**")
            ex_df_gi = df_f[df_f["image_ok"] & df_f["gaya_ilustrasi"].notna()].copy()
            ex_df_gi["gaya_skor"] = pd.to_numeric(ex_df_gi["gaya_skor"], errors="coerce")
            ex_df_gi = ex_df_gi.sort_values("gaya_skor", ascending=False)
            if len(ex_df_gi) > 0:
                render_single_book_detail(ex_df_gi.iloc[0], "ilustrasi")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Showcase 6 kategori ilustrasi
    st.markdown("### Enam Kategori Gaya Ilustrasi")
    st.markdown("Setiap kategori dicontohkan oleh sampul buku dengan skor CLIP tertinggi dalam dataset.")

    gi_cols = st.columns(3)
    for idx, (cat_key, cat_label) in enumerate(GAYA_ID.items()):
        col = gi_cols[idx % 3]
        with col:
            desc = GAYA_DESC[cat_key]
            best_title, best_file, best_score = GAYA_BEST.get(cat_key, ("–", None, 0))
            cover_path = get_cover_url(best_file) if best_file else None
            st.markdown(f"**{cat_label}**")
            st.markdown(f"<small style='opacity:0.6'>{desc}</small>", unsafe_allow_html=True)
            if cover_path:
                st.image(cover_path, use_container_width=True)
            st.markdown(
                f'<div style="font-size:0.75rem;opacity:0.65;margin-bottom:0.5rem;">'
                f'*{best_title[:50]}* (skor {best_score:.3f})</div>',
                unsafe_allow_html=True
            )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("**Distribusi Gaya Ilustrasi**")
        gc = df_f["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        pcts_gi = (gc / gc.sum() * 100).round(1)
        fig = px.bar(gc, x=gc.values, y=gc.index, orientation="h",
                     color_discrete_sequence=["#43A047"],
                     text=[f"{v:,} ({p}%)" for v, p in zip(gc.values, pcts_gi.values)])
        fig.update_layout(**plotly_layout(300), showlegend=False,
                          xaxis_title="Jumlah Sampul", yaxis_title="",
                          yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True, key="gi_dist")

    with col2:
        st.markdown("**Jelajah Buku — Filter Ilustrasi**")
        gaya_opts = ["Semua"] + [GAYA_ID[k] for k in GAYA_ID]
        gaya_sel  = st.selectbox("Gaya ilustrasi", gaya_opts, key="gi_search")
        n_gi      = st.slider("Jumlah buku", 4, 24, 8, 4, key="gi_n")
        manusia_sel = st.checkbox("Hanya dengan figur manusia", key="gi_manusia")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Tren Gaya Ilustrasi per Tahun**")
        dfg = df_f[(df_f["YEAR"] > 0) & df_f["gaya_ilustrasi"].notna()].copy()
        dfg["gaya_label"] = dfg["gaya_ilustrasi"].map(GAYA_ID)
        trend_g = dfg.groupby(["YEAR","gaya_label"]).size().reset_index(name="n")
        fig_tr = px.bar(trend_g, x="YEAR", y="n", color="gaya_label",
                        barmode="stack", color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_tr.update_layout(**plotly_layout(310, showlegend=True),
                             legend=dict(orientation="h", y=-0.25, font=dict(size=10)),
                             xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_tr, use_container_width=True, key="gi_trend")

    with col4:
        st.markdown("**Kehadiran Figur Manusia**")
        yolo_human  = int(df_f["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
        detr_human  = int(df_f["detr_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
        total       = len(df_f)
        agree_human = int((df_f["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") &
                           df_f["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")).sum())
        fig_mn = go.Figure(data=[
            go.Bar(name="YOLOv8n", x=["Ada manusia","Tidak ada"],
                   y=[yolo_human, total - yolo_human],
                   marker_color=["#66BB6A","#EF9A9A"]),
            go.Bar(name="DETR",    x=["Ada manusia","Tidak ada"],
                   y=[detr_human, total - detr_human],
                   marker_color=["#42A5F5","#FFB74D"]),
        ])
        fig_mn.update_layout(**plotly_layout(310, showlegend=True, barmode="group"),
                             legend=dict(orientation="h", y=-0.2),
                             xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_mn, use_container_width=True, key="gi_human")
        st.markdown(
            f"<small>YOLOv8 & DETR sepakat pada **{agree_human:,}** sampul ({agree_human/total*100:.1f}%)</small>",
            unsafe_allow_html=True
        )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    df_buku_gi = df_f[df_f["image_ok"]].copy()
    if manusia_sel:
        df_buku_gi = df_buku_gi[df_buku_gi["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") |
                                df_buku_gi["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")]
    if gaya_sel != "Semua":
        gaya_map_rev = {v: k for k, v in GAYA_ID.items()}
        key_gaya = gaya_map_rev.get(gaya_sel, gaya_sel)
        df_buku_gi = df_buku_gi[df_buku_gi["gaya_ilustrasi"] == key_gaya]

    df_buku_gi["gaya_skor"] = pd.to_numeric(df_buku_gi.get("gaya_skor", pd.Series(dtype=float)), errors="coerce")
    df_buku_gi = df_buku_gi.sort_values("gaya_skor", ascending=False).head(n_gi)

    label_gi = gaya_sel if gaya_sel != "Semua" else "semua gaya"
    if manusia_sel:
        label_gi += " · dengan manusia"
    st.markdown(f"**Contoh sampul — {label_gi}** *(dengan analisis ilustrasi)*")
    render_book_cards(df_buku_gi.reset_index(drop=True), max_cols=8, show_analysis="ilustrasi")


# ═════════════════════════════════════════════════════════════
# HALAMAN: GENRE
# ═════════════════════════════════════════════════════════════
elif halaman == "Genre":
    st.markdown("## Analisis Genre")

    with st.expander("Catatan metodologi genre", expanded=False):
        st.markdown("""
**Sumber data genre:** Genre diambil dari metadata Goodreads yang ditetapkan oleh pembaca
melalui sistem *shelving*. Setiap buku dapat memiliki lebih dari satu genre (multi-label).

**Pengolahan:** Genre dipisahkan menjadi dua lapisan — *jenis karya* (kategori formal seperti Novel, Puisi, Cerita Pendek) dan *genre tematik* (konten seperti Fantasi, Thriller, Islam). Pemisahan ini mengikuti kerangka Genette (1997) tentang paratext sebagai mediator antara teks dan pembaca.

**Keterbatasan:** Label genre Goodreads bersifat *crowd-sourced* dan tidak konsisten antar buku. Genre seperti "Novel" dan "Fiksi" sering tumpang tindih secara konseptual.
        """)

    all_gc = all_genre_counts(df_f)

    # Pisahkan jenis karya dan genre tematik
    jenis_karya_found = [(g, all_gc[g]) for g in all_gc
                         if g in GENRE_JENIS_KARYA and all_gc[g] > 0]
    jenis_karya_found.sort(key=lambda x: x[1], reverse=True)

    genre_tematik = [(g, c) for g, c in all_gc.most_common()
                     if g not in GENRE_JENIS_KARYA]

    col_j, col_t = st.columns(2)

    with col_j:
        st.markdown("#### Jenis Karya")
        st.markdown("<small style='opacity:0.6'>Fiction · Indonesian Literature · Nonfiction · Novels · Poetry · Short Stories · Literature dan padanannya</small>", unsafe_allow_html=True)
        jk_names = [g for g, _ in jenis_karya_found]
        jk_vals  = [c for _, c in jenis_karya_found]
        pcts_jk = [f"{c/len(df_f)*100:.1f}%" for c in jk_vals]
        fig_jk = px.bar(
            x=jk_vals, y=jk_names, orientation="h",
            color_discrete_sequence=["#1E88E5"],
            text=[f"{v:,} ({p})" for v, p in zip(jk_vals, pcts_jk)],
        )
        fig_jk.update_layout(**plotly_layout(max(300, len(jk_names)*30)),
                             showlegend=False, xaxis_title="Jumlah Buku", yaxis_title="",
                             yaxis=dict(categoryorder="total ascending"))
        fig_jk.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig_jk, use_container_width=True, key="genre_jenis")

    with col_t:
        st.markdown("#### Genre Tematik")
        st.markdown("<small style='opacity:0.6'>Semua genre selain jenis karya — tampilkan 40 teratas</small>", unsafe_allow_html=True)
        gt_top = genre_tematik[:40]
        gt_names = [g for g, _ in gt_top]
        gt_vals  = [c for _, c in gt_top]
        fig_gt = px.bar(
            x=gt_vals, y=gt_names, orientation="h",
            color_discrete_sequence=["#FB8C00"],
            text=[f"{v:,}" for v in gt_vals],
        )
        fig_gt.update_layout(**plotly_layout(720),
                             showlegend=False, xaxis_title="Jumlah Buku", yaxis_title="",
                             yaxis=dict(categoryorder="total ascending"))
        fig_gt.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig_gt, use_container_width=True, key="genre_tematik")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Ko-okurensi genre
    st.markdown("**Tumpang Tindih Genre (Ko-okurensi)**")
    st.markdown("<small>Pasangan genre yang paling sering muncul bersama pada satu buku. Genre jenis karya dikeluarkan.</small>", unsafe_allow_html=True)

    top10_tematik = [g for g, _ in genre_tematik[:12] if g not in {"Sastra Indonesia"}][:10]
    co_matrix = pd.DataFrame(0, index=top10_tematik, columns=top10_tematik)
    for glist in expand_genres(df_f["GENRES"]):
        relevant = [g for g in glist if g in top10_tematik]
        for i2, g1 in enumerate(relevant):
            for g2 in relevant[i2+1:]:
                co_matrix.loc[g1, g2] += 1
                co_matrix.loc[g2, g1] += 1

    fig_heat = px.imshow(co_matrix, color_continuous_scale="Oranges",
                         aspect="auto", text_auto=True)
    fig_heat.update_layout(**plotly_layout(400), xaxis_title="", yaxis_title="",
                           coloraxis_showscale=False)
    fig_heat.update_traces(textfont_size=10)
    st.plotly_chart(fig_heat, use_container_width=True, key="genre_heat")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Filter pencarian buku per genre (tanpa contoh sampul acak)
    st.markdown("**Cari Buku Berdasarkan Genre**")
    all_genre_list = [g for g, _ in all_gc.most_common()]
    col_gs1, col_gs2 = st.columns([1,3])
    with col_gs1:
        genre_sel = st.selectbox("Pilih genre", ["—"] + all_genre_list, key="genre_search")
        n_genre   = st.slider("Jumlah buku", 4, 24, 8, 4, key="genre_n")
    with col_gs2:
        if genre_sel != "—":
            mask = df_f["GENRES"].apply(
                lambda x: genre_sel in [g.strip() for g in str(x).split(",")]
            )
            df_buku_g = df_f[mask & df_f["image_ok"]].head(n_genre)
            st.markdown(f'**{mask.sum():,} buku dengan genre "{genre_sel}"**')
            if len(df_buku_g) > 0:
                render_book_cards(df_buku_g.reset_index(drop=True), max_cols=8)
            else:
                st.info("Tidak ada buku dengan sampul yang tersedia untuk genre ini.")
        else:
            st.info("Pilih genre di sebelah kiri untuk melihat contoh buku.")
