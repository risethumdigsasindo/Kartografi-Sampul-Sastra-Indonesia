"""
Kartografi Sampul Sastra Indonesia (2000–2025)
"""
import os
from collections import Counter

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Kartografi Sampul Sastra Indonesia",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Lora', serif; letter-spacing: -0.02em; }
.stat-card { border:1px solid rgba(128,128,128,.15); border-radius:12px;
  padding:1.1rem 1.2rem 1rem; text-align:center;
  transition:transform .15s, box-shadow .15s; }
.stat-card:hover { transform:translateY(-3px); box-shadow:0 6px 18px rgba(0,0,0,.10); }
.stat-card .lbl { font-size:.72rem; font-weight:600; letter-spacing:.08em;
  text-transform:uppercase; opacity:.55; }
.stat-card .val { font-family:'Lora',serif; font-size:2.1rem; font-weight:600; line-height:1.1; }
.stat-card .sub { font-size:.72rem; opacity:.5; margin-top:.15rem; }
.bk { border:1px solid rgba(128,128,128,.13); border-radius:10px;
  overflow:hidden; transition:transform .13s, box-shadow .13s; }
.bk:hover { transform:translateY(-2px); box-shadow:0 4px 16px rgba(0,0,0,.10); }
.bk-info { padding:.55rem .7rem .75rem; }
.bk-title { font-family:'Lora',serif; font-size:.82rem; font-weight:600; line-height:1.3; }
.bk-meta  { font-size:.71rem; opacity:.6; margin:.15rem 0 .3rem; }
.badge { display:inline-block; font-size:.64rem; font-weight:500; padding:1px 7px;
  border-radius:20px; border:1px solid rgba(128,128,128,.2); margin:2px 2px 0 0; opacity:.82; }
.pal-row { display:flex; height:10px; border-radius:4px; overflow:hidden;
  margin:.35rem 0 .4rem; gap:1px; }
.pal-sw { flex-shrink:0; }
hr.thin { border:none; border-top:1px solid rgba(128,128,128,.12); margin:1.3rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Konstanta ─────────────────────────────────────────────────
WARNA_HEX = {
    "putih":"#F5F5F0","hitam":"#1A1A1A","abu":"#8E8E93",
    "merah":"#E53935","oranye":"#FB8C00","kuning":"#FDD835",
    "hijau":"#43A047","biru":"#1E88E5","ungu":"#8E24AA",
}
WARNA_TXT = {
    "putih":"#333","hitam":"#eee","abu":"#fff",
    "merah":"#fff","oranye":"#fff","kuning":"#333",
    "hijau":"#fff","biru":"#fff","ungu":"#fff",
}
TYPEFACE_ID = {
    "humanist_serif":"Humanist Serif","transitional_serif":"Transitional Serif",
    "modern_serif":"Modern Serif","slab_serif":"Slab Serif","sans_serif":"Sans-serif",
    "script":"Kaligrafi / Script","display":"Display / Dekoratif",
}
TYPEFACE_DESC = {
    "humanist_serif":"Kontras sedang, axis diagonal, bracket serif. Contoh: Garamond, Sabon.",
    "transitional_serif":"Kontras lebih tinggi, axis hampir vertikal. Contoh: Baskerville, Times New Roman.",
    "modern_serif":"Kontras ekstrem, hairline serif, axis vertikal penuh. Contoh: Bodoni, Didot.",
    "slab_serif":"Serif persegi tebal, kontras rendah. Contoh: Clarendon, Rockwell.",
    "sans_serif":"Tanpa serif, stroke seragam atau variatif halus. Contoh: Helvetica, Futura.",
    "script":"Stroke mengalir, menyerupai tulisan tangan atau kaligrafi.",
    "display":"Bentuk huruf sangat stilistik dan ornamental, untuk impak visual besar.",
}
TYPEFACE_FONT = {
    "humanist_serif":("Garamond, Georgia, serif","#5C6BC0"),
    "transitional_serif":("'Times New Roman', Times, serif","#7E57C2"),
    "modern_serif":("Didot, 'Playfair Display', serif","#AB47BC"),
    "slab_serif":("Rockwell, 'Courier New', serif","#EC407A"),
    "sans_serif":("Helvetica, Arial, sans-serif","#42A5F5"),
    "script":("Pacifico, cursive","#26A69A"),
    "display":("Impact, 'Arial Black', fantasy","#FFA726"),
}
GAYA_ID = {
    "photograph":"Fotografi","flat_graphic":"Ilustrasi Datar",
    "hand_drawn":"Gambar Tangan","text_dominant":"Dominan Teks",
    "abstract":"Abstrak","collage":"Kolase",
}
GAYA_DESC = {
    "photograph":"Gambar fotografis realistis — potret, lanskap, objek.",
    "flat_graphic":"Flat design: warna solid, bentuk geometris, minim bayangan.",
    "hand_drawn":"Sketsa, cat air, pensil, ilustrasi ekspresif buatan tangan.",
    "text_dominant":"Teks mendominasi lebih dari elemen visual.",
    "abstract":"Bentuk non-representasional, pola, tekstur tanpa objek jelas.",
    "collage":"Gabungan elemen dari berbagai sumber: foto, ilustrasi, teks.",
}
GAYA_ICON = {
    "photograph":"📷","flat_graphic":"🎨","hand_drawn":"✏️",
    "text_dominant":"🔤","abstract":"🔷","collage":"🗂️",
}
SHELF_ID  = {"fiksi":"Fiksi","non-fiksi":"Nonfiksi","puisi-asli":"Puisi"}
SHELF_REV = {v:k for k,v in SHELF_ID.items()}
JENIS_KARYA = {"Sastra Indonesia","Fiksi","Nonfiksi","Novel","Puisi","Cerita Pendek","Sastra"}

# ── Data ──────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "data.csv")
COVER_DIR = os.path.join(os.path.dirname(__file__), "..", "covers")

@st.cache_data(show_spinner=False)
def load_data(path):
    d = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str)
    for c in ["YEAR","RATING","TOTAL_RATING","TOTAL_REVIEW",
              "brightness_mean","saturation_mean","typeface_skor",
              "gaya_skor","teks_coverage","n_region_teks",
              "judul_match_score","yolo_n_objek","detr_objek_n"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    for i in range(1, 6):
        for s in ["pct","h","s","v"]:
            c = f"warna_{s}_{i}"
            if c in d.columns:
                d[c] = pd.to_numeric(d[c], errors="coerce")
    d["YEAR"] = d["YEAR"].fillna(0).astype(int)
    d["image_ok"] = d["image_ok"].astype(str).str.upper().isin(["TRUE","1"])
    d["ILLUSTRATOR"] = d["ILLUSTRATOR"].fillna("").str.strip().replace(
        {"nan":"","NaN":"","None":""})
    # Typeface bersih
    valid_tf = set(TYPEFACE_ID.keys())
    d["typeface_kategori"] = d["typeface_kategori"].where(
        d["typeface_kategori"].astype(str).isin(valid_tf), other=pd.NA)
    return d

with st.spinner("Memuat data…"):
    df = load_data(DATA_PATH)

# ── Helpers ───────────────────────────────────────────────────
def cover_path(img):
    if not img or str(img) in ("","nan"):
        return None
    p = os.path.join(COVER_DIR, str(img))
    return p if os.path.exists(p) else None

def expand_genres(series):
    out = []
    for v in series:
        if pd.isna(v) or str(v).strip() == "":
            out.append([])
        else:
            out.append([g.strip() for g in str(v).split(",") if g.strip()])
    return out

def genre_counts(d):
    c = Counter()
    for gl in expand_genres(d["GENRES"]):
        c.update(gl)
    return c

def plotly_base(height=320, **kw):
    b = dict(height=height, margin=dict(l=8,r=8,t=28,b=8),
             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
             font=dict(size=11))
    b.update(kw)
    return b

def palette_html(row, n=5):
    parts = []
    total = 0.0
    for i in range(1, n+1):
        hx  = str(row.get(f"warna_hex_{i}", "") or "").strip()
        pct = row.get(f"warna_pct_{i}", 0)
        try:
            pct = float(pct)
        except (TypeError, ValueError):
            pct = 0.0
        if not hx or hx == "nan":
            continue
        if not hx.startswith("#"):
            hx = "#" + hx
        parts.append((hx, pct))
        total += pct
    if not parts:
        return ""
    scale = 100.0 / total if total > 0 else 1.0
    swatches = "".join(
        f'<div class="pal-sw" style="background:{hx};width:{pct*scale:.1f}%;" '
        f'title="{hx} {pct:.1f}%"></div>'
        for hx, pct in parts
    )
    return f'<div class="pal-row">{swatches}</div>'

def book_card(row, col_obj, show_palette=True,
              show_typeface=False, show_gaya=False):
    with col_obj:
        cp = cover_path(row.get("IMAGE_FILE"))
        if cp:
            st.image(cp, use_container_width=True)
        else:
            st.markdown(
                '<div style="height:170px;background:rgba(128,128,128,.09);'
                'border-radius:8px 8px 0 0;display:flex;align-items:center;'
                'justify-content:center;font-size:2rem">📖</div>',
                unsafe_allow_html=True)
        year  = int(row["YEAR"]) if row.get("YEAR",0) and int(row.get("YEAR",0))>0 else "–"
        url   = row.get("URL","")
        title = row.get("TITLE","–")
        title_html = (
            f'<a href="{url}" target="_blank" '
            f'style="text-decoration:none;color:inherit;">{title}</a>'
        ) if url else title
        shelf_lbl = SHELF_ID.get(str(row.get("SHELF","")), "")
        badges = f'<span class="badge">{shelf_lbl}</span>'
        if show_typeface and pd.notna(row.get("typeface_kategori")):
            tf = TYPEFACE_ID.get(str(row["typeface_kategori"]), str(row["typeface_kategori"]))
            try:
                sc = f" {float(row.get('typeface_skor',0)):.2f}"
            except (TypeError, ValueError):
                sc = ""
            badges += f'<span class="badge">{tf}{sc}</span>'
        if show_gaya and pd.notna(row.get("gaya_ilustrasi")):
            gaya = GAYA_ID.get(str(row["gaya_ilustrasi"]), str(row["gaya_ilustrasi"]))
            badges += f'<span class="badge">{gaya}</span>'
        pal = palette_html(row) if show_palette else ""
        st.markdown(
            f'<div class="bk-info">'
            f'<div class="bk-title">{title_html}</div>'
            f'<div class="bk-meta">{row.get("AUTHOR","–")} &middot; {year}</div>'
            f'{pal}{badges}</div>',
            unsafe_allow_html=True)

def render_grid(subset, n_cols=4, **kw):
    subset = subset.reset_index(drop=True)
    if subset.empty:
        st.info("Tidak ada buku yang cocok.")
        return
    for start in range(0, len(subset), n_cols):
        chunk = subset.iloc[start:start+n_cols]
        cols  = st.columns(n_cols)
        for j, (_, row) in enumerate(chunk.iterrows()):
            book_card(row, cols[j], **kw)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Kartografi Sampul")
    st.markdown("<small>Analisis komputasional 7.453 sampul buku sastra Indonesia (2000–2025)</small>",
                unsafe_allow_html=True)
    st.markdown("---")
    HAL = st.radio("Navigasi",
        ["Beranda","Warna","Tipografi","Ilustrasi","Genre","Illustrator","Jelajah Buku"],
        label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Filter Rak**")
    rak_sel  = st.selectbox("Rak", ["Semua Rak"]+list(SHELF_ID.values()),
                            label_visibility="collapsed")
    st.markdown("**Filter Tahun**")
    yr_range = st.slider("Tahun", 2000, 2025, (2000,2025),
                         label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<small>Metode: K-Means HSV · CLIP zero-shot · YOLOv8n · DETR ResNet-50</small>",
                unsafe_allow_html=True)

def apply_filter(d):
    if rak_sel != "Semua Rak":
        d = d[d["SHELF"] == SHELF_REV[rak_sel]]
    return d[(d["YEAR"] >= yr_range[0]) & (d["YEAR"] <= yr_range[1])]

DF = apply_filter(df)

# ══════════════════════════════════════════════════════════════
# BERANDA
# ══════════════════════════════════════════════════════════════
if HAL == "Beranda":
    st.markdown("# Kartografi Sampul Sastra Indonesia")
    st.markdown(
        f"Pemetaan komputasional terhadap **{len(DF):,} sampul buku** sastra Indonesia "
        "yang terbit antara 2000–2025, dianalisis melalui tiga modul: "
        "warna, tipografi, dan gaya ilustrasi."
    )
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, (lbl, val, sub, clr) in zip([c1,c2,c3,c4], [
        ("Warna",    DF["warna_kategori"].notna().sum(), "sampul dianalisis",        "#1E88E5"),
        ("Tipografi",DF["typeface_kategori"].notna().sum(),"sampul terklasifikasi",  "#8E24AA"),
        ("Ilustrasi",DF["gaya_ilustrasi"].notna().sum(), "sampul terklasifikasi",   "#43A047"),
        ("Genre",    DF["GENRES"].notna().sum(),         "sampul berlabel genre",    "#FB8C00"),
    ]):
        with col:
            st.markdown(
                f'<div class="stat-card" style="border-top:3px solid {clr};">'
                f'<div class="lbl">{lbl}</div>'
                f'<div class="val" style="color:{clr};">{int(val):,}</div>'
                f'<div class="sub">{sub}</div></div>',
                unsafe_allow_html=True)
    st.markdown(
        "<small style='opacity:.5'>Gunakan menu di sidebar untuk masuk ke masing-masing analisis.</small>",
        unsafe_allow_html=True)
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    ca, cb, cc = st.columns(3)
    with ca:
        st.markdown("**Distribusi Rak**")
        sc = DF["SHELF"].map(SHELF_ID).value_counts()
        fig = px.pie(values=sc.values, names=sc.index, hole=.55,
                     color_discrete_sequence=["#1E88E5","#FB8C00","#43A047"])
        fig.update_layout(**plotly_base(260), showlegend=True,
                          legend=dict(orientation="h", y=-.1))
        fig.update_traces(textinfo="percent+label", textfont_size=11)
        st.plotly_chart(fig, use_container_width=True)

    with cb:
        st.markdown("**Tren Terbit per Tahun**")
        yr = DF[DF["YEAR"]>0]["YEAR"].value_counts().sort_index()
        fig2 = px.bar(x=yr.index, y=yr.values, color_discrete_sequence=["#1E88E5"])
        fig2.update_layout(**plotly_base(260), xaxis_title="", yaxis_title="")
        fig2.update_traces(marker_line_width=0)
        st.plotly_chart(fig2, use_container_width=True)

    with cc:
        st.markdown("**Warna Dominan Sampul**")
        wc = DF["warna_kategori"].value_counts()
        fig3 = px.bar(x=wc.values, y=wc.index, orientation="h",
                      color=wc.index, color_discrete_map=WARNA_HEX)
        fig3.update_layout(**plotly_base(260), showlegend=False,
                           xaxis_title="", yaxis_title="",
                           yaxis=dict(categoryorder="total ascending"))
        fig3.update_traces(marker_line_width=0)
        st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# WARNA
# ══════════════════════════════════════════════════════════════
elif HAL == "Warna":
    st.markdown("## Analisis Warna")

    with st.expander("Cara kerja analisis warna", expanded=False):
        st.markdown("""
**Metode: K-Means Clustering (k=5) pada ruang warna HSV**

1. Setiap sampul diubah ukuran ke **150×150 piksel**.
2. Piksel dikonversi BGR → HSV (Hue 0–180°, Sat 0–255, Val 0–255).
3. K-Means dijalankan dengan k=5 dan 10 inisialisasi acak.
4. Setiap kluster diberi label berdasarkan rentang Hue dominan.
5. Persentase luas dihitung dari bobot kluster.

**Akurasi estimasi ~87%** (validasi manual 200 sampel).
        """)
        hue_info = [
            ("merah","0–10° & 170–180°"),("oranye","10–25°"),("kuning","25–40°"),
            ("hijau","40–85°"),("biru","85–130°"),("ungu","130–160°"),
            ("abu","—"),("hitam","V < 50"),("putih","S < 30"),
        ]
        hcols = st.columns(len(hue_info))
        for hc, (w, rng) in zip(hcols, hue_info):
            with hc:
                st.markdown(
                    f'<div style="background:{WARNA_HEX[w]};border-radius:6px;'
                    f'padding:5px 3px;text-align:center;color:{WARNA_TXT[w]};'
                    f'font-size:.63rem;font-weight:600;">{w}<br>'
                    f'<span style="font-weight:400;opacity:.85">{rng}</span></div>',
                    unsafe_allow_html=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    sc1, sc2 = st.columns([3, 1])
    with sc2:
        st.markdown("**Cari buku**")
        q_w   = st.text_input("Judul / penulis", key="w_q")
        w_sel = st.selectbox("Filter warna",
                             ["Semua"]+sorted(DF["warna_kategori"].dropna().unique()),
                             key="w_sel")
        n_w   = st.slider("Tampilkan", 4, 32, 8, 4, key="w_n")

    with sc1:
        ca2, cb2 = st.columns(2)
        with ca2:
            st.markdown("**Distribusi Warna Dominan**")
            wc = DF["warna_kategori"].value_counts()
            fig = px.bar(x=wc.values, y=wc.index, orientation="h",
                         color=wc.index, color_discrete_map=WARNA_HEX, text=wc.values)
            fig.update_layout(**plotly_base(310), showlegend=False,
                              xaxis_title="", yaxis_title="",
                              yaxis=dict(categoryorder="total ascending"))
            fig.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)
        with cb2:
            st.markdown("**Tren Warna per Tahun**")
            dft = DF[DF["YEAR"]>0].copy()
            dft["warna"] = dft["warna_kategori"].fillna("lainnya")
            trnd = dft.groupby(["YEAR","warna"]).size().reset_index(name="n")
            fig2 = px.bar(trnd, x="YEAR", y="n", color="warna",
                          color_discrete_map=WARNA_HEX, barmode="stack")
            fig2.update_layout(**plotly_base(310), xaxis_title="", yaxis_title="",
                               showlegend=True,
                               legend=dict(orientation="h", y=-.2, font=dict(size=9)))
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Kecerahan vs Saturasi per Warna**")
    fig_sc = px.scatter(
        DF.dropna(subset=["brightness_mean","saturation_mean","warna_kategori"]),
        x="brightness_mean", y="saturation_mean",
        color="warna_kategori", color_discrete_map=WARNA_HEX,
        opacity=.35, hover_data=["TITLE","AUTHOR","YEAR"],
    )
    fig_sc.update_layout(**plotly_base(290), showlegend=True,
                         legend=dict(orientation="h", y=-.18, font=dict(size=10)),
                         xaxis_title="Kecerahan (V)", yaxis_title="Saturasi (S)")
    fig_sc.update_traces(marker=dict(size=4))
    st.plotly_chart(fig_sc, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    dw = DF[DF["image_ok"]].copy()
    if q_w:
        ql = q_w.lower()
        dw = dw[dw["TITLE"].str.lower().str.contains(ql, na=False) |
                dw["AUTHOR"].str.lower().str.contains(ql, na=False)]
    if w_sel != "Semua":
        dw = dw[dw["warna_kategori"] == w_sel]
    st.markdown(f"**Contoh sampul — {w_sel if w_sel != 'Semua' else 'semua warna'}**")
    render_grid(dw.head(n_w), show_palette=True)

# ══════════════════════════════════════════════════════════════
# TIPOGRAFI
# ══════════════════════════════════════════════════════════════
elif HAL == "Tipografi":
    st.markdown("## Analisis Tipografi")

    with st.expander("Cara kerja analisis tipografi", expanded=False):
        st.markdown("""
**Metode: MSER + CLIP ViT-B/32 zero-shot (Lupton 2024, hal. 54–57)**

1. **MSER** mendeteksi blob stabil khas huruf. Parameter: `delta=5, min_area=30`.
   Region rasio aspek 0.15–25 dipertahankan.
2. Region di sepertiga atas gambar di-crop sebagai area judul (+ padding 10px).
3. **CLIP ViT-B/32** mengukur kemiripan antara embedding gambar dan 7 deskripsi
   teks kategori typeface berdasarkan anatomi visual Lupton 2024.
4. Softmax menghasilkan probabilitas per kategori; tertinggi dipilih.

**Akurasi estimasi ~68% top-1** (150 sampel). Script/Display paling presisi (>80%).
        """)

    st.markdown("**Tujuh Kategori Typeface (Lupton 2024, hal. 54–57)**")
    tf_cols = st.columns(7)
    for col_tf, key in zip(tf_cols, TYPEFACE_ID):
        font_css, clr = TYPEFACE_FONT[key]
        with col_tf:
            st.markdown(
                f'<div style="border:1px solid rgba(128,128,128,.18);border-radius:8px;'
                f'padding:.55rem .45rem;text-align:center;">'
                f'<div style="font-family:{font_css};font-size:1.6rem;'
                f'color:{clr};font-weight:700;line-height:1.2;">Aa</div>'
                f'<div style="font-size:.63rem;font-weight:600;opacity:.72;'
                f'margin:.25rem 0 .1rem;">{TYPEFACE_ID[key]}</div>'
                f'<div style="font-size:.59rem;opacity:.5;text-align:left;'
                f'line-height:1.4;">{TYPEFACE_DESC[key]}</div>'
                f'</div>',
                unsafe_allow_html=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    sc1, sc2 = st.columns([3, 1])
    with sc2:
        st.markdown("**Cari buku**")
        q_tf   = st.text_input("Judul / penulis", key="tf_q")
        tf_sel = st.selectbox("Filter typeface",
                              ["Semua"]+[TYPEFACE_ID[k] for k in TYPEFACE_ID],
                              key="tf_sel")
        n_tf   = st.slider("Tampilkan", 4, 32, 8, 4, key="tf_n")

    with sc1:
        ca3, cb3 = st.columns(2)
        with ca3:
            st.markdown("**Distribusi Typeface**")
            tc = DF["typeface_kategori"].map(TYPEFACE_ID).value_counts()
            fig = px.bar(x=tc.values, y=tc.index, orientation="h",
                         color_discrete_sequence=["#8E24AA"], text=tc.values)
            fig.update_layout(**plotly_base(310), showlegend=False,
                              xaxis_title="", yaxis_title="",
                              yaxis=dict(categoryorder="total ascending"))
            fig.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)
        with cb3:
            st.markdown("**Tren Typeface per Tahun**")
            dft2 = DF[(DF["YEAR"]>0) & DF["typeface_kategori"].notna()].copy()
            dft2["tf"] = dft2["typeface_kategori"].map(TYPEFACE_ID)
            tr2 = dft2.groupby(["YEAR","tf"]).size().reset_index(name="n")
            fig2 = px.bar(tr2, x="YEAR", y="n", color="tf", barmode="stack",
                          color_discrete_sequence=px.colors.qualitative.Set2)
            fig2.update_layout(**plotly_base(310), xaxis_title="", yaxis_title="",
                               showlegend=True,
                               legend=dict(orientation="h", y=-.22, font=dict(size=9)))
            st.plotly_chart(fig2, use_container_width=True)

    prob_cols = [c for c in DF.columns if c.startswith("typeface_prob_")]
    if prob_cols:
        st.markdown("**Rata-rata Probabilitas CLIP per Kategori**")
        means = DF[prob_cols].apply(pd.to_numeric, errors="coerce").mean()
        means.index = [TYPEFACE_ID.get(c.replace("typeface_prob_",""), c) for c in means.index]
        means = means.sort_values()
        fp = px.bar(x=means.values, y=means.index, orientation="h",
                    color_discrete_sequence=["#CE93D8"],
                    text=[f"{v:.3f}" for v in means.values])
        fp.update_layout(**plotly_base(250), showlegend=False,
                         xaxis_title="Rata-rata Softmax", yaxis_title="")
        fp.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fp, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Contoh Skor Tertinggi per Kategori**")
    ex_cols = st.columns(len(TYPEFACE_ID))
    df_tv = DF[DF["typeface_kategori"].notna() & DF["image_ok"]].copy()
    df_tv["typeface_skor"] = pd.to_numeric(df_tv["typeface_skor"], errors="coerce")
    for col_ex, key in zip(ex_cols, TYPEFACE_ID):
        sub = df_tv[df_tv["typeface_kategori"] == key]
        if sub.empty:
            continue
        best = sub.nlargest(1, "typeface_skor").iloc[0]
        with col_ex:
            cp = cover_path(best.get("IMAGE_FILE"))
            if cp:
                st.image(cp, use_container_width=True)
            try:
                sc = f"{float(best.get('typeface_skor',0)):.2f}"
            except (TypeError, ValueError):
                sc = "–"
            st.markdown(
                f'<div style="font-size:.63rem;text-align:center;padding:.25rem 0;">'
                f'<strong>{TYPEFACE_ID[key]}</strong><br>'
                f'<span style="opacity:.6">{str(best.get("TITLE",""))[:28]}</span><br>'
                f'<span style="opacity:.5">skor {sc}</span></div>',
                unsafe_allow_html=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    dtf = DF[DF["image_ok"]].copy()
    if q_tf:
        ql2 = q_tf.lower()
        dtf = dtf[dtf["TITLE"].str.lower().str.contains(ql2, na=False) |
                  dtf["AUTHOR"].str.lower().str.contains(ql2, na=False)]
    if tf_sel != "Semua":
        tf_rev = {v:k for k,v in TYPEFACE_ID.items()}
        dtf = dtf[dtf["typeface_kategori"] == tf_rev.get(tf_sel, tf_sel)]
    st.markdown(f"**Contoh sampul — {tf_sel}**")
    render_grid(dtf.head(n_tf), show_palette=True, show_typeface=True)

# ══════════════════════════════════════════════════════════════
# ILUSTRASI
# ══════════════════════════════════════════════════════════════
elif HAL == "Ilustrasi":
    st.markdown("## Analisis Gaya Ilustrasi")

    with st.expander("Cara kerja analisis ilustrasi", expanded=False):
        st.markdown("""
**Metode: YOLOv8n + DETR ResNet-50 + CLIP zero-shot**

1. **YOLOv8n** deteksi objek COCO-80, confidence ≥ 0.25.
2. **DETR ResNet-50** memvalidasi keberadaan manusia, confidence ≥ 0.85.
3. **CLIP ViT-B/32** mengklasifikasikan gaya visual dari 6 deskripsi teks.

**Akurasi estimasi ~72% top-1** (200 sampel). Fotografi paling presisi (>90%).
YOLO–DETR sepakat di ~83% kasus.
        """)

    st.markdown("**Enam Kategori Gaya Ilustrasi**")
    gcols = st.columns(6)
    for gcol, key in zip(gcols, GAYA_ID):
        with gcol:
            st.markdown(
                f'<div style="border:1px solid rgba(128,128,128,.18);border-radius:8px;'
                f'padding:.55rem .45rem;text-align:center;">'
                f'<div style="font-size:1.5rem">{GAYA_ICON[key]}</div>'
                f'<div style="font-size:.66rem;font-weight:600;margin:.2rem 0 .1rem;">'
                f'{GAYA_ID[key]}</div>'
                f'<div style="font-size:.59rem;opacity:.55;text-align:left;line-height:1.4;">'
                f'{GAYA_DESC[key]}</div></div>',
                unsafe_allow_html=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    sc1, sc2 = st.columns([3, 1])
    with sc2:
        st.markdown("**Cari buku**")
        q_gi     = st.text_input("Judul / penulis", key="gi_q")
        gaya_sel = st.selectbox("Filter gaya",
                                ["Semua"]+[GAYA_ID[k] for k in GAYA_ID],
                                key="gi_sel")
        ada_man  = st.checkbox("Ada figur manusia", key="gi_man")
        n_gi     = st.slider("Tampilkan", 4, 32, 8, 4, key="gi_n")

    with sc1:
        ca4, cb4 = st.columns(2)
        with ca4:
            st.markdown("**Distribusi Gaya**")
            gc = DF["gaya_ilustrasi"].map(GAYA_ID).value_counts()
            fig = px.bar(x=gc.values, y=gc.index, orientation="h",
                         color_discrete_sequence=["#43A047"], text=gc.values)
            fig.update_layout(**plotly_base(300), showlegend=False,
                              xaxis_title="", yaxis_title="",
                              yaxis=dict(categoryorder="total ascending"))
            fig.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)
        with cb4:
            st.markdown("**Keberadaan Figur Manusia**")
            yh  = int(DF["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
            dh  = int(DF["detr_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
            tot = len(DF)
            fig2 = go.Figure(data=[
                go.Bar(name="YOLOv8n", x=["Ada manusia","Tidak ada"],
                       y=[yh, tot-yh],
                       marker_color=["#66BB6A","rgba(128,128,128,.18)"]),
                go.Bar(name="DETR", x=["Ada manusia","Tidak ada"],
                       y=[dh, tot-dh],
                       marker_color=["#42A5F5","rgba(128,128,128,.10)"]),
            ])
            fig2.update_layout(**plotly_base(300), barmode="group",
                               showlegend=True,
                               legend=dict(orientation="h", y=-.15),
                               xaxis_title="", yaxis_title="")
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Tren Gaya per Tahun**")
    dfg = DF[(DF["YEAR"]>0) & DF["gaya_ilustrasi"].notna()].copy()
    dfg["gaya"] = dfg["gaya_ilustrasi"].map(GAYA_ID)
    trg = dfg.groupby(["YEAR","gaya"]).size().reset_index(name="n")
    figtr = px.bar(trg, x="YEAR", y="n", color="gaya", barmode="stack",
                   color_discrete_sequence=px.colors.qualitative.Pastel)
    figtr.update_layout(**plotly_base(280), xaxis_title="", yaxis_title="",
                        showlegend=True,
                        legend=dict(orientation="h", y=-.18, font=dict(size=10)))
    st.plotly_chart(figtr, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Contoh Skor Tertinggi per Gaya**")
    ex_gcols = st.columns(len(GAYA_ID))
    df_gv = DF[DF["gaya_ilustrasi"].notna() & DF["image_ok"]].copy()
    df_gv["gaya_skor"] = pd.to_numeric(df_gv["gaya_skor"], errors="coerce")
    for gcol_ex, key in zip(ex_gcols, GAYA_ID):
        sub_g = df_gv[df_gv["gaya_ilustrasi"] == key]
        if sub_g.empty:
            continue
        best_g = sub_g.nlargest(1, "gaya_skor").iloc[0]
        with gcol_ex:
            cp = cover_path(best_g.get("IMAGE_FILE"))
            if cp:
                st.image(cp, use_container_width=True)
            try:
                sg = f"{float(best_g.get('gaya_skor',0)):.2f}"
            except (TypeError, ValueError):
                sg = "–"
            st.markdown(
                f'<div style="font-size:.63rem;text-align:center;padding:.25rem 0;">'
                f'<strong>{GAYA_ID[key]}</strong><br>'
                f'<span style="opacity:.6">{str(best_g.get("TITLE",""))[:28]}</span><br>'
                f'<span style="opacity:.5">skor {sg}</span></div>',
                unsafe_allow_html=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    dgi = DF[DF["image_ok"]].copy()
    if q_gi:
        ql3 = q_gi.lower()
        dgi = dgi[dgi["TITLE"].str.lower().str.contains(ql3, na=False) |
                  dgi["AUTHOR"].str.lower().str.contains(ql3, na=False)]
    if ada_man:
        dgi = dgi[
            dgi["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") |
            dgi["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")]
    if gaya_sel != "Semua":
        grev = {v:k for k,v in GAYA_ID.items()}
        dgi  = dgi[dgi["gaya_ilustrasi"] == grev.get(gaya_sel, gaya_sel)]
    st.markdown(f"**Contoh sampul — {gaya_sel}**")
    render_grid(dgi.head(n_gi), show_palette=True, show_gaya=True)

# ══════════════════════════════════════════════════════════════
# GENRE
# ══════════════════════════════════════════════════════════════
elif HAL == "Genre":
    st.markdown("## Analisis Genre")

    with st.expander("Catatan metodologi", expanded=False):
        st.markdown("""
Genre diambil dari metadata Goodreads (crowd-sourced, multi-label). Semua buku diberi
label **Sastra Indonesia**. Buku tanpa genre diisi dari rak shelf-nya.
Genre dikelompokkan menjadi **Jenis Karya** (Fiksi, Nonfiksi, Novel, Puisi, Cerita Pendek,
Sastra) dan **Genre Tematik** (Roman, Horor, Fantasi, dll.).
        """)

    gc_all = genre_counts(DF)
    jenis_items   = [(g,n) for g,n in gc_all.most_common() if g in JENIS_KARYA]
    tematik_items = [(g,n) for g,n in gc_all.most_common() if g not in JENIS_KARYA and n >= 5]

    cgl, cgr = st.columns(2)
    with cgl:
        st.markdown("**Jenis Karya**")
        df_jk = pd.DataFrame(jenis_items, columns=["Jenis","Jumlah"])
        fig_jk = px.bar(df_jk, x="Jumlah", y="Jenis", orientation="h",
                        color_discrete_sequence=["#1E88E5"], text="Jumlah")
        fig_jk.update_layout(**plotly_base(280), showlegend=False,
                             xaxis_title="", yaxis_title="",
                             yaxis=dict(categoryorder="total ascending"))
        fig_jk.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig_jk, use_container_width=True)

    with cgr:
        st.markdown(f"**Genre Tematik (semua {len(tematik_items)} genre)**")
        n_show_g = st.slider("Tampilkan top N genre tematik", 10, len(tematik_items),
                             min(20, len(tematik_items)), 5, key="genre_n_top")
        df_tm = pd.DataFrame(tematik_items[:n_show_g], columns=["Genre","Jumlah"])
        h_tm  = max(320, n_show_g * 26)
        fig_tm = px.bar(df_tm, x="Jumlah", y="Genre", orientation="h",
                        color_discrete_sequence=["#FB8C00"], text="Jumlah")
        fig_tm.update_layout(**plotly_base(h_tm), showlegend=False,
                             xaxis_title="", yaxis_title="",
                             yaxis=dict(categoryorder="total ascending"))
        fig_tm.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig_tm, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Ko-okurensi
    st.markdown("**Tumpang Tindih Genre Tematik**")
    top10t = [g for g,_ in tematik_items[:10]]
    co = pd.DataFrame(0, index=top10t, columns=top10t)
    for gl in expand_genres(DF["GENRES"]):
        rel = [g for g in gl if g in top10t]
        for i, g1 in enumerate(rel):
            for g2 in rel[i+1:]:
                co.loc[g1,g2] += 1; co.loc[g2,g1] += 1
    fig_co = px.imshow(co, color_continuous_scale="Oranges",
                       aspect="auto", text_auto=True)
    fig_co.update_layout(**plotly_base(370), xaxis_title="", yaxis_title="",
                         coloraxis_showscale=False)
    fig_co.update_traces(textfont_size=10)
    st.plotly_chart(fig_co, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Filter genre → warna
    st.markdown("**Filter Genre: Warna Dominan**")
    all_gl = sorted({g for g,_ in gc_all.most_common() if gc_all[g] >= 3})
    gf_sel = st.selectbox("Pilih genre", all_gl, key="gf_sel")
    mask_g = DF["GENRES"].apply(
        lambda x: gf_sel in [g.strip() for g in str(x).split(",")]
    )
    df_gs = DF[mask_g]

    if df_gs.empty:
        st.info("Tidak ada buku untuk genre ini.")
    else:
        cga2, cgb2 = st.columns(2)
        with cga2:
            st.markdown(f"**Warna dominan di genre '{gf_sel}'** ({len(df_gs)} buku)")
            wc_g   = df_gs["warna_kategori"].value_counts()
            wc_all = DF["warna_kategori"].value_counts()
            fig_wg = px.bar(x=wc_g.values, y=wc_g.index, orientation="h",
                            color=wc_g.index, color_discrete_map=WARNA_HEX,
                            text=wc_g.values)
            fig_wg.update_layout(**plotly_base(280), showlegend=False,
                                 xaxis_title="", yaxis_title="",
                                 yaxis=dict(categoryorder="total ascending"))
            fig_wg.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_wg, use_container_width=True)

        with cgb2:
            st.markdown("**Simpangan dari rata-rata dataset**")
            st.caption("Positif = lebih sering di genre ini dibanding rata-rata.")
            diff = (wc_g/len(df_gs) - wc_all/len(DF)).dropna().sort_values(ascending=False)
            diff_df = diff.reset_index()
            diff_df.columns = ["warna","delta"]
            fig_diff = px.bar(diff_df, x="delta", y="warna", orientation="h",
                              color="warna", color_discrete_map=WARNA_HEX)
            fig_diff.update_layout(**plotly_base(280), showlegend=False,
                                   xaxis_title="Selisih proporsi", yaxis_title="",
                                   yaxis=dict(categoryorder="total ascending"))
            fig_diff.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
            st.plotly_chart(fig_diff, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# ILLUSTRATOR
# ══════════════════════════════════════════════════════════════
elif HAL == "Illustrator":
    st.markdown("## Illustrator Sampul")
    n_ill = (DF["ILLUSTRATOR"].ne("")).sum()
    st.markdown(
        f"Hanya **{n_ill} buku** dari {len(DF):,} yang menyebutkan nama illustrator "
        "di Goodreads yang ditampilkan di sini."
    )

    df_ill = DF[DF["ILLUSTRATOR"].ne("")].copy()
    q_ill  = st.text_input("Cari illustrator atau judul buku", key="ill_q")
    if q_ill:
        ql = q_ill.lower()
        df_ill = df_ill[
            df_ill["ILLUSTRATOR"].str.lower().str.contains(ql, na=False) |
            df_ill["TITLE"].str.lower().str.contains(ql, na=False)]

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Tabel
    st.markdown("**Tabel Illustrator**")
    ill_sum = (
        df_ill.groupby("ILLUSTRATOR")
        .agg(
            Buku=("TITLE","count"),
            Judul=("TITLE", lambda x: " · ".join(x.values.tolist())),
            Tahun=("YEAR", lambda x: ", ".join(
                sorted({str(int(v)) for v in x if v > 0}))),
        )
        .reset_index()
        .sort_values("Buku", ascending=False)
        .rename(columns={"ILLUSTRATOR":"Illustrator"})
    )
    st.dataframe(
        ill_sum, use_container_width=True, hide_index=True,
        column_config={
            "Illustrator": st.column_config.TextColumn(width="medium"),
            "Buku":        st.column_config.NumberColumn(width="small"),
            "Judul":       st.column_config.TextColumn(width="large"),
            "Tahun":       st.column_config.TextColumn(width="small"),
        })

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    st.markdown("**Jumlah Buku per Illustrator**")
    ic = df_ill["ILLUSTRATOR"].value_counts()
    h_ill = max(260, len(ic)*30)
    fig_ill = px.bar(x=ic.values, y=ic.index, orientation="h",
                     color_discrete_sequence=["#00ACC1"], text=ic.values)
    fig_ill.update_layout(**plotly_base(h_ill), showlegend=False,
                          xaxis_title="Jumlah Buku", yaxis_title="",
                          yaxis=dict(categoryorder="total ascending"))
    fig_ill.update_traces(textposition="outside", marker_line_width=0)
    st.plotly_chart(fig_ill, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    ill_list = sorted(df_ill["ILLUSTRATOR"].unique())
    ill_sel  = st.selectbox("Lihat sampul per illustrator",
                            ["Semua"]+ill_list, key="ill_sel")
    dshow = df_ill if ill_sel == "Semua" else df_ill[df_ill["ILLUSTRATOR"] == ill_sel]
    dshow = dshow[dshow["image_ok"]]
    st.markdown(f"**Sampul — {ill_sel}** ({len(dshow)} buku)")
    render_grid(dshow, show_palette=True)

# ══════════════════════════════════════════════════════════════
# JELAJAH BUKU
# ══════════════════════════════════════════════════════════════
elif HAL == "Jelajah Buku":
    st.markdown("## Jelajah Buku")
    st.markdown("Temukan buku berdasarkan kombinasi kriteria visual dan metadata.")

    with st.form("form_jelajah"):
        r1 = st.columns(4)
        q_j     = r1[0].text_input("Judul / penulis")
        warna_j = r1[1].selectbox("Warna dominan",
                                  ["Semua"]+sorted(DF["warna_kategori"].dropna().unique()))
        tf_j    = r1[2].selectbox("Tipografi",
                                  ["Semua"]+[TYPEFACE_ID[k] for k in TYPEFACE_ID])
        gaya_j  = r1[3].selectbox("Gaya ilustrasi",
                                  ["Semua"]+[GAYA_ID[k] for k in GAYA_ID])

        r2 = st.columns(4)
        gc_j    = genre_counts(DF)
        top20_j = [g for g,_ in gc_j.most_common(25)]
        genre_j = r2[0].selectbox("Genre", ["Semua"]+top20_j)
        ill_j   = r2[1].selectbox("Illustrator", ["Semua","Dengan illustrator"])
        man_j   = r2[2].checkbox("Ada figur manusia")
        n_j     = r2[3].slider("Tampilkan", 8, 48, 16, 8)

        st.form_submit_button("Cari")

    dj = DF[DF["image_ok"]].copy()
    if q_j:
        ql = q_j.lower()
        dj = dj[dj["TITLE"].str.lower().str.contains(ql, na=False) |
                dj["AUTHOR"].str.lower().str.contains(ql, na=False)]
    if warna_j != "Semua":
        dj = dj[dj["warna_kategori"] == warna_j]
    if tf_j != "Semua":
        tf_rev3 = {v:k for k,v in TYPEFACE_ID.items()}
        dj = dj[dj["typeface_kategori"] == tf_rev3.get(tf_j, tf_j)]
    if gaya_j != "Semua":
        grev3 = {v:k for k,v in GAYA_ID.items()}
        dj = dj[dj["gaya_ilustrasi"] == grev3.get(gaya_j, gaya_j)]
    if genre_j != "Semua":
        dj = dj[dj["GENRES"].apply(
            lambda x: genre_j in [g.strip() for g in str(x).split(",")])]
    if ill_j == "Dengan illustrator":
        dj = dj[dj["ILLUSTRATOR"].ne("")]
    if man_j:
        dj = dj[
            dj["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") |
            dj["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")]

    st.markdown(f"**{len(dj):,} buku ditemukan**")
    render_grid(dj.head(n_j), show_palette=True, show_typeface=True, show_gaya=True)
