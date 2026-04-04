"""Kartografi Sampul Sastra Indonesia (2000-2025)"""
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
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
h1,h2,h3{font-family:'Lora',serif;letter-spacing:-.02em;}
.stat-card{border:1px solid rgba(128,128,128,.15);border-radius:12px;padding:1.1rem 1.2rem 1rem;text-align:center;transition:transform .15s,box-shadow .15s;}
.stat-card:hover{transform:translateY(-3px);box-shadow:0 6px 18px rgba(0,0,0,.10);}
.stat-card .lbl{font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;opacity:.55;}
.stat-card .val{font-family:'Lora',serif;font-size:2.1rem;font-weight:600;line-height:1.1;}
.stat-card .sub{font-size:.72rem;opacity:.5;margin-top:.15rem;}
.bk-info{padding:.55rem .7rem .75rem;}
.bk-title{font-family:'Lora',serif;font-size:.82rem;font-weight:600;line-height:1.3;}
.bk-meta{font-size:.71rem;opacity:.6;margin:.15rem 0 .3rem;}
.badge{display:inline-block;font-size:.64rem;font-weight:500;padding:1px 7px;border-radius:20px;border:1px solid rgba(128,128,128,.2);margin:2px 2px 0 0;opacity:.82;}
.pal-row{display:flex;height:10px;border-radius:4px;overflow:hidden;margin:.35rem 0 .4rem;gap:1px;}
.pal-sw{flex-shrink:0;}
.prob-bar-wrap{margin:.12rem 0;}
.prob-label{font-size:.6rem;display:flex;justify-content:space-between;margin-bottom:1px;opacity:.72;}
.prob-bar-bg{background:rgba(128,128,128,.12);border-radius:3px;height:6px;overflow:hidden;}
.prob-bar-fill{height:6px;border-radius:3px;}
hr.thin{border:none;border-top:1px solid rgba(128,128,128,.12);margin:1.3rem 0;}
</style>""", unsafe_allow_html=True)

# ── KONSTANTA ───────────────────────────────────────────────────────────────
WARNA_HEX = {
    "putih":  "#F5F5F0",
    "hitam":  "#1A1A1A",
    "abu":    "#8E8E93",
    "merah":  "#E53935",
    "oranye": "#FB8C00",
    "kuning": "#FDD835",
    "hijau":  "#43A047",
    "biru":   "#1E88E5",
    "ungu":   "#8E24AA",
}
WARNA_TXT = {
    "putih":"#333","hitam":"#eee","abu":"#fff","merah":"#fff",
    "oranye":"#fff","kuning":"#333","hijau":"#fff","biru":"#fff","ungu":"#fff"
}

# Threshold HSV untuk re-klasifikasi warna yang lebih akurat
# H dalam OpenCV 0–180 (kalikan 2 untuk derajat sebenarnya)
WARNA_RANGES = {
    # (H_min, H_max) dalam skala OpenCV 0-180; S,V threshold terpisah
    "merah_low":  (0,   10),
    "merah_high": (170, 180),
    "oranye":     (10,  25),
    "kuning":     (25,  40),
    "hijau":      (40,  85),
    "biru":       (85,  130),
    "ungu":       (130, 170),
}

TYPEFACE_ID = {
    "humanist_serif":      "Humanist Serif",
    "transitional_serif":  "Transitional Serif",
    "modern_serif":        "Modern Serif",
    "slab_serif":          "Slab Serif",
    "sans_serif":          "Sans-serif",
    "script":              "Kaligrafi/Script",
    "display":             "Display/Dekoratif",
}
TYPEFACE_CLR = {
    "humanist_serif":     "#5C6BC0",
    "transitional_serif": "#7E57C2",
    "modern_serif":       "#AB47BC",
    "slab_serif":         "#EC407A",
    "sans_serif":         "#42A5F5",
    "script":             "#26A69A",
    "display":            "#FFA726",
}
TYPEFACE_FONT = {
    "humanist_serif":     "Georgia,serif",
    "transitional_serif": "'Times New Roman',serif",
    "modern_serif":       "'Playfair Display',Georgia,serif",
    "slab_serif":         "'Courier New',monospace",
    "sans_serif":         "Helvetica,Arial,sans-serif",
    "script":             "cursive",
    "display":            "Impact,fantasy",
}
TYPEFACE_DESC = {
    "humanist_serif":     "Kontras sedang, axis diagonal, bracket serif. Garamond, Sabon.",
    "transitional_serif": "Kontras lebih tinggi, axis hampir vertikal. Baskerville, Times.",
    "modern_serif":       "Kontras ekstrem, hairline serif, axis vertikal. Bodoni, Didot.",
    "slab_serif":         "Serif persegi tebal, kontras rendah. Clarendon, Rockwell.",
    "sans_serif":         "Tanpa serif, stroke seragam. Helvetica, Futura.",
    "script":             "Stroke mengalir, menyerupai kaligrafi atau tulisan tangan.",
    "display":            "Bentuk huruf sangat stilistik, ornamental, untuk impak besar.",
}

GAYA_ID = {
    "photograph":     "Fotografi",
    "flat_graphic":   "Ilustrasi Datar",
    "hand_drawn":     "Gambar Tangan",
    "text_dominant":  "Dominan Teks",
    "abstract":       "Abstrak",
    "collage":        "Kolase",
}
GAYA_CLR = {
    "photograph":    "#1E88E5",
    "flat_graphic":  "#43A047",
    "hand_drawn":    "#FB8C00",
    "text_dominant": "#E53935",
    "abstract":      "#8E24AA",
    "collage":       "#00ACC1",
}
GAYA_ICON = {
    "photograph":    "📷",
    "flat_graphic":  "🎨",
    "hand_drawn":    "✏️",
    "text_dominant": "🔤",
    "abstract":      "🔷",
    "collage":       "🗂️",
}
GAYA_DESC = {
    "photograph":    "Gambar fotografis realistis.",
    "flat_graphic":  "Flat design: warna solid, bentuk geometris.",
    "hand_drawn":    "Sketsa, cat air, ilustrasi ekspresif.",
    "text_dominant": "Teks mendominasi elemen visual.",
    "abstract":      "Bentuk non-representasional, pola, tekstur.",
    "collage":       "Gabungan foto, ilustrasi, teks dari berbagai sumber.",
}
GAYA_PROB_KEYS = ["photograph","hand_drawn","abstract","flat_graphic","text_dominant"]

SHELF_LABEL = {"fiksi":"Fiksi","puisi-asli":"Puisi"}

GENRE_NORM = {
    "Sastra":              "Sastra Indonesia",
    "Cinta":               "Romansa",
    "Roman":               "Romansa",
    "Romansa Kontemporer": "Romansa",
    "Kontemporer":         "Romansa",
    "Thriller":            "Thriller/Misteri",
    "Misteri":             "Thriller/Misteri",
    "Misteri Thriller":    "Thriller/Misteri",
    "Humor":               "Komedi",
}
GENRE_EXCLUDE = {"Sastra Indonesia", "Sastra", "Fiksi"}

# ── PATH ─────────────────────────────────────────────────────────────────────
# Gunakan data_final_v2.csv jika tersedia (tipografi lengkap), fallback ke data.csv
_v2_path = os.path.join(os.path.dirname(__file__), "data_final_v2.csv")
_v1_path = os.path.join(os.path.dirname(__file__), "data.csv")
DATA_PATH  = _v2_path if os.path.exists(_v2_path) else _v1_path
COVER_DIR  = os.path.join(os.path.dirname(__file__), "..", "covers")


# ── RE-KLASIFIKASI WARNA AKURAT ──────────────────────────────────────────────
def _reklasifikasi_warna(row):
    """
    Recompute warna_kategori dari nilai HSV kolom warna_h_1, warna_s_1, warna_v_1.
    Skala OpenCV: H 0–180, S 0–255, V 0–255.
    """
    try:
        h = float(row.get("warna_h_1", 0) or 0)
        s = float(row.get("warna_s_1", 0) or 0)
        v = float(row.get("warna_v_1", 0) or 0)
    except Exception:
        return row.get("warna_kategori", "putih")

    # Hitam: brightness sangat rendah
    if v < 50:
        return "hitam"
    # Putih: saturasi sangat rendah + cerah
    if s < 30 and v > 160:
        return "putih"
    # Abu: saturasi rendah
    if s < 50:
        if v > 160:
            return "putih"
        return "abu"

    # Warna berdasarkan Hue (OpenCV 0–180)
    if h < 10 or h >= 170:
        return "merah"
    elif h < 25:
        return "oranye"
    elif h < 40:
        return "kuning"
    elif h < 85:
        return "hijau"
    elif h < 130:
        return "biru"
    elif h < 170:
        return "ungu"
    return "merah"


@st.cache_data(show_spinner=False)
def load_data(path):
    d = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    # Data sudah hanya berisi fiksi dan puisi-asli; filter sebagai safeguard
    d = d[d["SHELF"].isin(["fiksi", "puisi-asli"])].copy()

    # Numerik
    num_cols = [
        "YEAR","RATING","TOTAL_RATING","TOTAL_REVIEW",
        "brightness_mean","saturation_mean",
        "typeface_skor","gaya_skor","teks_coverage",
        "n_region_teks","judul_match_score","yolo_n_objek","detr_objek_n"
    ]
    for c in num_cols:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")

    for i in range(1, 6):
        for s in ["pct","h","s","v"]:
            c = f"warna_{s}_{i}"
            if c in d.columns:
                d[c] = pd.to_numeric(d[c], errors="coerce")

    for c in d.columns:
        if c.startswith("typeface_prob_") or c.startswith("gaya_prob_"):
            d[c] = pd.to_numeric(d[c], errors="coerce")

    d["YEAR"] = d["YEAR"].fillna(0).astype(int)
    d["image_ok"] = d["image_ok"].astype(str).str.upper().isin(["TRUE","1"])
    d["ILLUSTRATOR"] = d["ILLUSTRATOR"].fillna("").astype(str).str.strip()
    d.loc[d["ILLUSTRATOR"].isin(["nan","NaN","None"]), "ILLUSTRATOR"] = ""

    # ── Normalisasi typeface_kategori ──────────────────────────────────────
    # Jika masih ada nilai tidak valid (None, nan, dsb) → unclassified
    # Pada data_final_v2.csv (setelah re-analisis 236 buku) ini seharusnya minimal
    if "typeface_kategori" in d.columns:
        d["typeface_kategori"] = d["typeface_kategori"].fillna("unclassified")
        valid_tf = set(TYPEFACE_ID.keys()) | {"unclassified"}
        d["typeface_kategori"] = d["typeface_kategori"].where(
            d["typeface_kategori"].astype(str).str.strip().isin(valid_tf),
            other="unclassified"
        )

    if "gaya_ilustrasi" in d.columns:
        d["gaya_ilustrasi"] = d["gaya_ilustrasi"].where(
            d["gaya_ilustrasi"].astype(str).str.strip().isin(set(GAYA_ID.keys())),
            other=pd.NA
        )

    # ── RE-KLASIFIKASI WARNA AKURAT ────────────────────────────────────────
    # Gunakan nilai HSV asli untuk menentukan label warna yang benar
    d["warna_kategori"] = d.apply(_reklasifikasi_warna, axis=1)

    return d


with st.spinner("Memuat data..."):
    df = load_data(DATA_PATH)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def cover_path(img):
    if not img or str(img) in ("","nan"):
        return None
    p = os.path.join(COVER_DIR, str(img))
    return p if os.path.exists(p) else None


def _norm_genre(g):
    return GENRE_NORM.get(g.strip(), g.strip())


def expand_genres(series, normalize=False):
    out = []
    for v in series:
        if pd.isna(v) or str(v).strip() == "":
            out.append([])
        else:
            raw = [g.strip() for g in str(v).split(",") if g.strip()]
            if normalize:
                seen, normed = set(), []
                for g in raw:
                    g2 = _norm_genre(g)
                    if g2 not in seen:
                        normed.append(g2); seen.add(g2)
                out.append(normed)
            else:
                out.append(raw)
    return out


def genre_counts(d, normalize=True):
    c = Counter()
    for gl in expand_genres(d["GENRES"], normalize=normalize):
        c.update(gl)
    return c


def pb(height=320, **kw):
    b = dict(
        height=height,
        margin=dict(l=8,r=8,t=28,b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color="#1A1A1A")
    )
    b.update(kw)
    return b


def _nama_warna(hex_str):
    try:
        h = hex_str.lstrip("#")
        r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    except Exception:
        return hex_str
    best, best_d = "lainnya", float("inf")
    for nama, hx in WARNA_HEX.items():
        try:
            hh = hx.lstrip("#")
            rr,gg,bb = int(hh[0:2],16), int(hh[2:4],16), int(hh[4:6],16)
            dist = (r-rr)**2+(g-gg)**2+(b-bb)**2
            if dist < best_d:
                best, best_d = nama, dist
        except Exception:
            pass
    return best


def palette_html(row, n=5):
    parts, total = [], 0.0
    for i in range(1, n+1):
        hx  = str(row.get(f"warna_hex_{i}","") or "").strip()
        pct = row.get(f"warna_pct_{i}", 0)
        try: pct = float(pct)
        except: pct = 0.0
        if not hx or hx in ("nan",""):
            continue
        if not hx.startswith("#"):
            hx = "#" + hx
        nama = _nama_warna(hx)
        parts.append((hx, pct, nama)); total += pct
    if not parts:
        return ""
    scale = 100.0/total if total > 0 else 1.0
    sw = "".join(
        f'<div class="pal-sw" style="background:{hx};width:{pct*scale:.1f}%;" '
        f'title="{nama} ({pct:.1f}%)"></div>'
        for hx,pct,nama in parts
    )
    return f'<div class="pal-row">{sw}</div>'


def prob_bars(probs_dict, colors_dict, label_map):
    html = ""
    for key, val in sorted(probs_dict.items(), key=lambda x: -x[1]):
        label = label_map.get(key, key)
        clr   = colors_dict.get(key, "#999")
        pct   = val * 100
        html += (
            f'<div class="prob-bar-wrap"><div class="prob-label"><span>{label}</span>'
            f'<span>{pct:.1f}%</span></div><div class="prob-bar-bg">'
            f'<div class="prob-bar-fill" style="width:{pct:.1f}%;background:{clr};"></div>'
            f'</div></div>'
        )
    return html


def book_card(row, col_obj, show_tf=False, show_gi=False):
    with col_obj:
        cp = cover_path(row.get("IMAGE_FILE"))
        if cp:
            st.image(cp, use_container_width=True)
        else:
            st.markdown(
                '<div style="height:160px;background:rgba(128,128,128,.09);border-radius:8px 8px 0 0;'
                'display:flex;align-items:center;justify-content:center;font-size:2rem">📖</div>',
                unsafe_allow_html=True
            )
        year = int(row["YEAR"]) if row.get("YEAR",0) and int(row.get("YEAR",0)) > 0 else "–"
        url   = row.get("URL","")
        title = str(row.get("TITLE","–"))
        title_html = (
            f'<a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">{title}</a>'
            if url else title
        )
        shelf_lbl = SHELF_LABEL.get(str(row.get("SHELF","")), str(row.get("SHELF","")))
        badges = f'<span class="badge">{shelf_lbl}</span>'

        tf_bars = gi_bars = ""
        if show_tf and pd.notna(row.get("typeface_kategori")) and str(row.get("typeface_kategori")) != "unclassified":
            tk  = str(row["typeface_kategori"])
            clr = TYPEFACE_CLR.get(tk, "#999")
            try: sc = f"{float(row.get('typeface_skor',0)):.2f}"
            except: sc = "–"
            badges += (
                f'<span class="badge" style="border-color:{clr};color:{clr};">'
                f'{TYPEFACE_ID.get(tk,tk)} {sc}</span>'
            )
            probs = {k: float(row.get(f"typeface_prob_{k}", 0) or 0) for k in TYPEFACE_ID}
            if any(probs.values()):
                tf_bars = prob_bars(probs, TYPEFACE_CLR, TYPEFACE_ID)

        if show_gi and pd.notna(row.get("gaya_ilustrasi")):
            gk  = str(row["gaya_ilustrasi"])
            clr = GAYA_CLR.get(gk, "#999")
            try: sc_gi = f"{float(row.get('gaya_skor',0)):.2f}"
            except: sc_gi = "–"
            badges += (
                f'<span class="badge" style="border-color:{clr};color:{clr};">'
                f'{GAYA_ID.get(gk,gk)} {sc_gi}</span>'
            )
            probs_gi = {k: float(row.get(f"gaya_prob_{k}", 0) or 0) for k in GAYA_PROB_KEYS}
            if any(probs_gi.values()):
                gi_bars = prob_bars(probs_gi, GAYA_CLR, GAYA_ID)

        bars = tf_bars or gi_bars
        st.markdown(
            f'<div class="bk-info"><div class="bk-title">{title_html}</div>'
            f'<div class="bk-meta">{row.get("AUTHOR","–")} · {year}</div>'
            f'{palette_html(row)}{badges}'
            f'{"<div style=margin-top:.4rem>"+bars+"</div>" if bars else ""}'
            f'</div>',
            unsafe_allow_html=True
        )


def grid(subset, n_cols=4, **kw):
    subset = subset.reset_index(drop=True)
    if subset.empty:
        st.info("Tidak ada buku yang cocok.")
        return
    for start in range(0, len(subset), n_cols):
        chunk = subset.iloc[start:start+n_cols]
        cols  = st.columns(n_cols)
        for j,(_, row) in enumerate(chunk.iterrows()):
            book_card(row, cols[j], **kw)


def _top_genres_filtered(d, n=12):
    gc = genre_counts(d, normalize=True)
    return [g for g,_ in gc.most_common() if g not in GENRE_EXCLUDE and gc[g] >= 3][:n]


def heatmap_warna_genre(d, top_n=12):
    genres    = _top_genres_filtered(d, top_n)
    warna_keys = list(WARNA_HEX.keys())
    mat = pd.DataFrame(0.0, index=genres, columns=warna_keys)
    genre_lists = expand_genres(d["GENRES"], normalize=True)
    for genre in genres:
        mask = [genre in gl for gl in genre_lists]
        sub  = d[mask]
        if len(sub) == 0:
            continue
        vc = sub["warna_kategori"].value_counts(normalize=True)
        for w in warna_keys:
            mat.loc[genre, w] = vc.get(w, 0.0)
    text_mat = (mat * 100).round(0).astype(int).astype(str) + "%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=warna_keys, y=genres,
        colorscale="YlOrRd",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=9, color="#1A1A1A"),
        hovertemplate="Genre: %{y}<br>Warna: %{x}<br>Proporsi: %{text}<extra></extra>",
        showscale=True
    ))
    fig.update_layout(**pb(
        max(340, top_n*28),
        margin=dict(l=140,r=20,t=32,b=60),
        yaxis=dict(autorange="reversed"),
        xaxis_title="", yaxis_title=""
    ))
    return fig


def heatmap_tf_genre(d, top_n=12):
    genres    = _top_genres_filtered(d, top_n)
    tf_keys   = list(TYPEFACE_ID.keys())
    tf_labels = [TYPEFACE_ID[k] for k in tf_keys]
    mat = pd.DataFrame(0.0, index=genres, columns=tf_labels)
    d2  = d[
        d["typeface_kategori"].notna() &
        (d["typeface_kategori"] != "unclassified")
    ]
    genre_lists = expand_genres(d2["GENRES"], normalize=True)
    for genre in genres:
        mask = [genre in gl for gl in genre_lists]
        sub  = d2[mask]
        if len(sub) == 0:
            continue
        vc = sub["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)
        for k in tf_keys:
            mat.loc[genre, TYPEFACE_ID[k]] = vc.get(TYPEFACE_ID[k], 0.0)
    text_mat = (mat * 100).round(0).astype(int).astype(str) + "%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=tf_labels, y=genres,
        colorscale="Purples",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=9, color="#1A1A1A"),
        hovertemplate="Genre: %{y}<br>Tipografi: %{x}<br>Proporsi: %{text}<extra></extra>",
        showscale=True
    ))
    fig.update_layout(**pb(
        max(340, top_n*28),
        margin=dict(l=140,r=20,t=32,b=90),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickangle=-30),
        xaxis_title="", yaxis_title=""
    ))
    return fig


def heatmap_gaya_genre(d, top_n=12):
    genres     = _top_genres_filtered(d, top_n)
    gaya_keys  = list(GAYA_ID.keys())
    gaya_labels = [GAYA_ID[k] for k in gaya_keys]
    mat = pd.DataFrame(0.0, index=genres, columns=gaya_labels)
    d2  = d[d["gaya_ilustrasi"].notna()]
    genre_lists = expand_genres(d2["GENRES"], normalize=True)
    for genre in genres:
        mask = [genre in gl for gl in genre_lists]
        sub  = d2[mask]
        if len(sub) == 0:
            continue
        vc = sub["gaya_ilustrasi"].map(GAYA_ID).value_counts(normalize=True)
        for k in gaya_keys:
            mat.loc[genre, GAYA_ID[k]] = vc.get(GAYA_ID[k], 0.0)
    text_mat = (mat * 100).round(0).astype(int).astype(str) + "%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=gaya_labels, y=genres,
        colorscale="Greens",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=9, color="#1A1A1A"),
        hovertemplate="Genre: %{y}<br>Gaya: %{x}<br>Proporsi: %{text}<extra></extra>",
        showscale=True
    ))
    fig.update_layout(**pb(
        max(340, top_n*28),
        margin=dict(l=140,r=20,t=32,b=60),
        yaxis=dict(autorange="reversed"),
        xaxis_title="", yaxis_title=""
    ))
    return fig


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Kartografi Sampul")
    st.markdown(
        "<small>Analisis komputasional sampul buku sastra Indonesia ",
        unsafe_allow_html=True
    )
    st.markdown("---")
    HAL = st.radio(
        "Navigasi",
        ["Beranda","Warna","Tipografi","Ilustrasi","Genre","Illustrator","Jelajah Buku"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("**Filter Tahun**")
    yr_range = st.slider("Tahun", 2000, 2025, (2000,2025), label_visibility="collapsed")
    st.markdown("---")
    st.markdown(
        "<small>Metode: K-Means HSV · CLIP zero-shot · YOLOv8n · DETR ResNet-50</small>",
        unsafe_allow_html=True
    )

DF = df[(df["YEAR"] >= yr_range[0]) & (df["YEAR"] <= yr_range[1])].copy()
_gc     = genre_counts(DF, normalize=True)
_n_unik = len([g for g in _gc if g not in GENRE_EXCLUDE])


# ══════════════════════════════════════════════════════════════════════════════
# BERANDA
# ══════════════════════════════════════════════════════════════════════════════
if HAL == "Beranda":
    st.markdown("# Kartografi Sampul Sastra Indonesia")
    st.markdown(
        f"Pemetaan komputasional terhadap **{len(DF):,} sampul buku** fiksi dan puisi Indonesia "
        f"yang terbit periode 2000–2025, dianalisis melalui tiga aspek visual: warna, tipografi, "
        f"dan gaya ilustrasi."
    )
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    n_warna = int(DF["warna_kategori"].notna().sum())
    n_tf    = int(DF[
        DF["typeface_kategori"].notna() & (DF["typeface_kategori"] != "unclassified")
    ].shape[0])
    n_gi    = int(DF["gaya_ilustrasi"].notna().sum())

    c1,c2,c3,c4 = st.columns(4)
    for col,(lbl,val,sub,clr) in zip([c1,c2,c3,c4],[
        ("Warna",     n_warna, "teranalisis",     "#FB8C00"),
        ("Tipografi", n_tf,    "teranalisis",     "#8E24AA"),
        ("Ilustrasi", n_gi,    "terklasifikasi",  "#E53935"),
        ("Genre",     _n_unik, "genre unik",      "#00ACC1"),
    ]):
        with col:
            st.markdown(
                f'<div class="stat-card" style="border-top:3px solid {clr};">'
                f'<div class="lbl">{lbl}</div>'
                f'<div class="val" style="color:{clr};">{int(val):,}</div>'
                f'<div class="sub">{sub}</div></div>',
                unsafe_allow_html=True
            )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Status kelengkapan data
    n_tf_error = int((df["error_modul_b"].astype(str).str.strip() == "name 'analyze_typography' is not defined").sum()) if "error_modul_b" in df.columns else 0
    is_v2 = os.path.exists(os.path.join(os.path.dirname(__file__), "data_final_v2.csv"))
    if is_v2 and n_tf_error == 0:
        st.success(
            "✅ **Data tipografi lengkap** — semua 5.069 sampul berhasil teranalisis tipografinya "
            "(236 buku yang sebelumnya error sudah diperbaiki via notebook re-analisis)."
        )
    elif n_tf_error > 0:
        st.info(
            f"ℹ️ **Catatan tipografi:** {n_tf_error} sampul belum teranalisis tipografinya. "
            f"Jalankan notebook `reanalisis_typeface_236.ipynb` untuk memperbaikinya — "
            f"hasilnya akan tersimpan sebagai `data_final_v2.csv` dan otomatis digunakan app ini."
        )

    # Tren terbit per tahun
    st.markdown("**Tren Terbit per Tahun**")
    yr = (
        DF[DF["YEAR"] > 0]
        .groupby("YEAR")
        .size()
        .reset_index(name="n")
    )

    fig_yr = px.bar(
        yr,
        x="YEAR",
        y="n"
    )

    fig_yr.update_layout(
        **pb(280),
        xaxis_title="",
        yaxis_title="",
        showlegend=False
    )

    fig_yr.update_traces(marker_line_width=0)

    st.plotly_chart(fig_yr, use_container_width=True)

    # Distribusi Genre
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Distribusi Genre**", unsafe_allow_html=True)
    
    gc_beranda = [(g,n) for g,n in _gc.most_common() if g not in GENRE_EXCLUDE and n >= 5]
    n_gr_show  = st.slider(
        "Tampilkan top N genre", 10, min(len(gc_beranda), 40), 20, 5, key="beranda_gn"
    )
    df_gb  = pd.DataFrame(gc_beranda[:n_gr_show], columns=["Genre","Jumlah"])
    fig_gb = px.bar(
        df_gb, x="Jumlah", y="Genre", orientation="h",
        color_discrete_sequence=["#1E88E5"], text="Jumlah"
    )
    fig_gb.update_layout(
        **pb(max(300, n_gr_show*26)), showlegend=False,
        xaxis_title="", yaxis_title="",
        yaxis=dict(categoryorder="total ascending")
    )
    fig_gb.update_traces(textposition="outside", marker_line_width=0)
    st.plotly_chart(fig_gb, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    ca,cb = st.columns(2)
    with ca:
        st.markdown("**Warna Dominan**")
        wc   = DF["warna_kategori"].value_counts()
        fig3 = px.bar(
            x=wc.values, y=wc.index, orientation="h",
            color=wc.index, color_discrete_map=WARNA_HEX
        )
        fig3.update_layout(**pb(280), showlegend=False, xaxis_title="", yaxis_title="",
                           yaxis=dict(categoryorder="total ascending"))
        fig3.update_traces(marker_line_width=0)
        st.plotly_chart(fig3, use_container_width=True)
    with cb:
        st.markdown("**Gaya Ilustrasi**")
        gc2  = DF["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        fig4 = px.bar(
            x=gc2.values, y=gc2.index, orientation="h",
            color=gc2.index,
            color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID}
        )
        fig4.update_layout(**pb(280), showlegend=False, xaxis_title="", yaxis_title="",
                           yaxis=dict(categoryorder="total ascending"))
        fig4.update_traces(marker_line_width=0)
        st.plotly_chart(fig4, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# WARNA
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Warna":
    st.markdown("## Analisis Warna")

    with st.expander("Cara kerja analisis warna", expanded=False):
        st.markdown(
            "**K-Means Clustering (k=5) pada ruang warna HSV**\n\n"
            "1. Sampul → 150×150 piksel → BGR→HSV.\n"
            "2. K-Means k=5, 10 inisialisasi acak.\n"
            "3. Label warna dari rentang Hue dominan (skala OpenCV 0–180).\n"
            "4. Persentase dari bobot kluster.\n\n"
            "**Re-klasifikasi otomatis** dijalankan pada load data untuk memperbaiki "
            "label yang tidak sesuai (misal: oranye pucat terklasifikasi sebagai putih).\n\n"
            "**Akurasi ~87%** (200 sampel)."
        )
        hue_info = [
            ("merah",  "0–10° & 340–360°"),
            ("oranye", "20–50°"),
            ("kuning", "50–80°"),
            ("hijau",  "80–170°"),
            ("biru",   "170–260°"),
            ("ungu",   "260–340°"),
            ("abu",    "S rendah"),
            ("hitam",  "V < 50"),
            ("putih",  "S<30 & V>160"),
        ]
        hcols = st.columns(len(hue_info))
        for hc,(w,rng) in zip(hcols,hue_info):
            with hc:
                st.markdown(
                    f'<div style="background:{WARNA_HEX[w]};border-radius:6px;padding:5px 3px;'
                    f'text-align:center;color:{WARNA_TXT[w]};font-size:.62rem;font-weight:600;">'
                    f'{w}<br><span style="font-weight:400;opacity:.85">{rng}</span></div>',
                    unsafe_allow_html=True
                )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    ca2,cb2 = st.columns(2)
    with ca2:
        st.markdown("**Distribusi Warna Dominan**")
        wc   = DF["warna_kategori"].value_counts()
        fig  = px.bar(
            x=wc.values, y=wc.index, orientation="h",
            color=wc.index, color_discrete_map=WARNA_HEX,
            text=wc.values
        )
        fig.update_layout(**pb(310), showlegend=False, xaxis_title="", yaxis_title="",
                          yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    with cb2:
        st.markdown("**Tren Warna per Tahun**")
        dft  = DF[DF["YEAR"] > 0].copy()
        dft["warna"] = dft["warna_kategori"].fillna("lainnya")
        trnd = dft.groupby(["YEAR","warna"]).size().reset_index(name="n")
        fig2 = px.bar(
            trnd, x="YEAR", y="n", color="warna",
            color_discrete_map=WARNA_HEX, barmode="stack"
        )
        fig2.update_layout(**pb(310), xaxis_title="", yaxis_title="",
                           showlegend=True,
                           legend=dict(orientation="h",y=-.2,font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Kecerahan vs Saturasi per Warna**")
    fig_sc = px.scatter(
        DF.dropna(subset=["brightness_mean","saturation_mean","warna_kategori"]),
        x="brightness_mean", y="saturation_mean",
        color="warna_kategori", color_discrete_map=WARNA_HEX,
        opacity=.35, custom_data=["TITLE","AUTHOR","YEAR","warna_kategori"]
    )
    fig_sc.update_traces(
        marker=dict(size=4),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>%{customdata[1]} · %{customdata[2]}<br>"
            "Warna: %{customdata[3]}<br>V: %{x:.2f} · S: %{y:.2f}<extra></extra>"
        )
    )
    fig_sc.update_layout(
        **pb(300), showlegend=True,
        legend=dict(orientation="h",y=-.18,font=dict(size=10)),
        xaxis_title="Kecerahan (V)", yaxis_title="Saturasi (S)"
    )
    st.plotly_chart(fig_sc, use_container_width=True)

    # ── KOMBINASI WARNA ─────────────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Filter Kombinasi Warna**")
    st.markdown(
        "<small>Pilih warna yang harus muncul bersama dalam satu sampul "
        "(berdasarkan 5 kluster warna dominan). "
        "Berguna untuk mencari sampul dengan palet warna spesifik.</small>",
        unsafe_allow_html=True
    )

    semua_warna = list(WARNA_HEX.keys())
    warna_combo = st.multiselect(
        "Pilih 1–3 warna kombinasi",
        options=semua_warna,
        default=[],
        format_func=lambda w: w.capitalize(),
        key="warna_combo"
    )

    if warna_combo:
        # Cari buku yang memiliki SEMUA warna terpilih dalam 5 kluster
        def has_all_colors(row, colors):
            row_warna = set()
            for i in range(1, 6):
                w = str(row.get(f"warna_{i}","") or "").strip().lower()
                if w and w not in ("nan",""):
                    row_warna.add(w)
            return all(c in row_warna for c in colors)

        mask_combo = DF.apply(lambda r: has_all_colors(r, warna_combo), axis=1)
        df_combo   = DF[mask_combo & DF["image_ok"]].copy()
        st.markdown(
            f"**{len(df_combo):,} buku** memiliki kombinasi warna: "
            + " + ".join(
                f'<span style="display:inline-block;background:{WARNA_HEX[w]};'
                f'color:{WARNA_TXT[w]};padding:1px 8px;border-radius:10px;'
                f'font-size:.75rem;">{w}</span>'
                for w in warna_combo
            ),
            unsafe_allow_html=True
        )
        if not df_combo.empty:
            n_combo = st.slider("Tampilkan", 4, 32, 8, 4, key="n_warna_combo")
            grid(df_combo.head(n_combo))
    else:
        st.caption("Pilih minimal satu warna untuk melihat kombinasi.")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Peta Panas Warna × Genre**")
    st.markdown(
        "<small>Proporsi warna dominan per genre (setelah normalisasi). "
        "Sastra Indonesia, Sastra, Fiksi dikecualikan.</small>",
        unsafe_allow_html=True
    )
    hn_w = st.slider("Jumlah genre", 6, 20, 12, 2, key="hn_warna")
    st.plotly_chart(heatmap_warna_genre(DF, hn_w), use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Cari Buku berdasarkan Warna**")
    wc1,wc2,wc3 = st.columns([2,2,1])
    with wc1:
        q_w = st.text_input("Judul / penulis", key="w_q")
    with wc2:
        w_sel = st.selectbox(
            "Filter warna", ["Semua"] + semua_warna, key="w_sel"
        )
    with wc3:
        n_w = st.slider("Tampilkan", 4, 32, 8, 4, key="w_n")

    dw = DF[DF["image_ok"]].copy()
    if q_w:
        ql = q_w.lower()
        dw = dw[
            dw["TITLE"].str.lower().str.contains(ql, na=False) |
            dw["AUTHOR"].str.lower().str.contains(ql, na=False)
        ]
    if w_sel != "Semua":
        dw = dw[dw["warna_kategori"] == w_sel]
    if not dw.empty:
        grid(dw.head(n_w))


# ══════════════════════════════════════════════════════════════════════════════
# TIPOGRAFI
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Tipografi":
    st.markdown("## Analisis Tipografi")

    with st.expander("Cara kerja analisis tipografi", expanded=False):
        is_v2_tip = os.path.exists(os.path.join(os.path.dirname(__file__), "data_final_v2.csv"))
        n_err_tip = int((df["error_modul_b"].astype(str).str.strip() == "name 'analyze_typography' is not defined").sum()) if "error_modul_b" in df.columns else 0
        st.markdown(
            "**MSER + CLIP ViT-B/32 zero-shot (Lupton 2024, hal. 54–57)**\n\n"
            "1. **MSER** mendeteksi blob stabil khas huruf (delta=5, min_area=30). "
            "Region sepertiga atas di-crop sebagai area judul.\n"
            "2. **CLIP ViT-B/32** mengukur kemiripan dengan 7 deskripsi teks kategori typeface "
            "berdasarkan anatomi visual Lupton 2024.\n"
            "3. Softmax → probabilitas per kategori.\n\n"
            "**Akurasi ~68% top-1** (150 sampel). Script/Display paling presisi (>80%)."
            + (
                "\n\n✅ **Data lengkap** — semua 5.069 buku terklasifikasi "
                "(236 buku yang sebelumnya error sudah diperbaiki via `reanalisis_typeface_236.ipynb`)."
                if is_v2_tip and n_err_tip == 0 else
                f"\n\n⚠️ **{n_err_tip} sampul belum teranalisis.** "
                "Jalankan `reanalisis_typeface_236.ipynb` di Google Colab, "
                "lalu simpan hasilnya sebagai `data_final_v2.csv` di folder yang sama dengan `app_v2.py`."
            )
        )

    st.markdown("**Tujuh Kategori Typeface (Lupton 2024, hal. 54–57)**")
    tf_cols7 = st.columns(7)
    for col_tf,key in zip(tf_cols7, TYPEFACE_ID):
        clr  = TYPEFACE_CLR[key]
        font = TYPEFACE_FONT[key]
        with col_tf:
            st.markdown(
                f'<div style="border:1px solid rgba(128,128,128,.18);border-radius:8px;'
                f'padding:.55rem .45rem;text-align:center;">'
                f'<div style="font-family:{font};font-size:1.5rem;color:{clr};'
                f'font-weight:700;line-height:1.2">Aa</div>'
                f'<div style="font-size:.63rem;font-weight:600;opacity:.72;margin:.2rem 0 .1rem">'
                f'{TYPEFACE_ID[key]}</div>'
                f'<div style="font-size:.58rem;opacity:.5;text-align:left;line-height:1.35">'
                f'{TYPEFACE_DESC[key]}</div></div>',
                unsafe_allow_html=True
            )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Hanya data yang teranalisis (exclude unclassified)
    DF_tf = DF[DF["typeface_kategori"].notna() & (DF["typeface_kategori"] != "unclassified")]
    n_tf_total = len(DF_tf)
    n_tf_miss  = len(DF) - n_tf_total
    st.caption(
        f"Teranalisis: **{n_tf_total:,}** buku · Tidak teranalisis (error pipeline): **{n_tf_miss}** buku"
    )

    ca3,cb3 = st.columns(2)
    with ca3:
        st.markdown("**Distribusi Typeface**")
        tc  = DF_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts()
        fig = px.bar(
            x=tc.values, y=tc.index, orientation="h",
            color=tc.index,
            color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID},
            text=tc.values
        )
        fig.update_layout(**pb(300), showlegend=False, xaxis_title="", yaxis_title="",
                          yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    with cb3:
        st.markdown("**Tren Typeface per Tahun**")
        dft2 = DF_tf[DF_tf["YEAR"] > 0].copy()
        dft2["tf"] = dft2["typeface_kategori"].map(TYPEFACE_ID)
        tr2  = dft2.groupby(["YEAR","tf"]).size().reset_index(name="n")
        fig2 = px.bar(
            tr2, x="YEAR", y="n", color="tf", barmode="stack",
            color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID}
        )
        fig2.update_layout(**pb(300), xaxis_title="", yaxis_title="",
                           showlegend=True,
                           legend=dict(orientation="h",y=-.22,font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)

    prob_cols_tf = [c for c in DF_tf.columns if c.startswith("typeface_prob_")]
    if prob_cols_tf:
        st.markdown("**Rata-rata Probabilitas CLIP per Kategori**")
        means = DF_tf[prob_cols_tf].mean().sort_values()
        means.index = [
            TYPEFACE_ID.get(c.replace("typeface_prob_",""), c) for c in means.index
        ]
        fp = px.bar(
            x=means.values, y=means.index, orientation="h",
            color=means.index,
            color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID},
            text=[f"{v:.3f}" for v in means.values]
        )
        fp.update_layout(**pb(240), showlegend=False,
                         xaxis_title="Rata-rata Softmax", yaxis_title="")
        fp.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fp, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Peta Panas Tipografi × Genre**")
    st.markdown(
        "<small>Proporsi typeface per genre setelah normalisasi genre.</small>",
        unsafe_allow_html=True
    )
    hn_tf = st.slider("Jumlah genre", 6, 20, 12, 2, key="hn_tf")
    st.plotly_chart(heatmap_tf_genre(DF, hn_tf), use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Contoh Buku — Kepercayaan Tertinggi per Kategori**")
    df_tv = DF_tf[DF_tf["image_ok"]].copy()
    df_tv["typeface_skor"] = pd.to_numeric(df_tv["typeface_skor"], errors="coerce")
    ex_cols7 = st.columns(7)
    for col_ex,key in zip(ex_cols7, TYPEFACE_ID):
        sub  = df_tv[df_tv["typeface_kategori"] == key]
        if sub.empty:
            continue
        best = sub.nlargest(1,"typeface_skor").iloc[0]
        clr  = TYPEFACE_CLR[key]
        with col_ex:
            cp = cover_path(best.get("IMAGE_FILE"))
            if cp:
                st.image(cp, use_container_width=True)
            try: sc = f"{float(best.get('typeface_skor',0)):.2f}"
            except: sc = "–"
            probs_b = {k: float(best.get(f"typeface_prob_{k}",0) or 0) for k in TYPEFACE_ID}
            bars    = prob_bars(probs_b, TYPEFACE_CLR, TYPEFACE_ID) if any(probs_b.values()) else ""
            st.markdown(
                f'<div style="font-size:.62rem;padding:.25rem 0;">'
                f'<div style="font-weight:600;color:{clr}">{TYPEFACE_ID[key]}</div>'
                f'<div style="opacity:.6;line-height:1.3">{str(best.get("TITLE",""))[:28]}</div>'
                f'<div style="opacity:.5">skor {sc}</div>'
                f'{"<div style=margin-top:.35rem>"+bars+"</div>" if bars else ""}</div>',
                unsafe_allow_html=True
            )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Cari Buku berdasarkan Tipografi**")
    tfc1,tfc2,tfc3 = st.columns([2,2,1])
    with tfc1:
        q_tf = st.text_input("Judul / penulis", key="tf_q")
    with tfc2:
        tf_sel = st.selectbox(
            "Filter typeface",
            ["Semua"] + [TYPEFACE_ID[k] for k in TYPEFACE_ID],
            key="tf_sel"
        )
    with tfc3:
        n_tf2 = st.slider("Tampilkan", 4, 32, 8, 4, key="tf_n")

    dtf = DF_tf[DF_tf["image_ok"]].copy()
    if q_tf:
        ql2 = q_tf.lower()
        dtf = dtf[
            dtf["TITLE"].str.lower().str.contains(ql2, na=False) |
            dtf["AUTHOR"].str.lower().str.contains(ql2, na=False)
        ]
    if tf_sel != "Semua":
        tf_rev = {v:k for k,v in TYPEFACE_ID.items()}
        dtf    = dtf[dtf["typeface_kategori"] == tf_rev.get(tf_sel, tf_sel)]
    if not dtf.empty:
        grid(dtf.head(n_tf2), show_tf=True)


# ══════════════════════════════════════════════════════════════════════════════
# ILUSTRASI
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Ilustrasi":
    st.markdown("## Analisis Gaya Ilustrasi")

    with st.expander("Cara kerja analisis ilustrasi", expanded=False):
        st.markdown(
            "**YOLOv8n + DETR ResNet-50 + CLIP zero-shot**\n\n"
            "1. **YOLOv8n** — deteksi objek COCO-80, confidence ≥ 0.25.\n"
            "2. **DETR ResNet-50** — validator keberadaan manusia, confidence ≥ 0.85.\n"
            "3. **CLIP ViT-B/32** — klasifikasi 6 gaya visual.\n\n"
            "**Akurasi ~72% top-1** (200 sampel). Fotografi >90%. YOLO–DETR sepakat ~83%."
        )

    st.markdown("**Enam Kategori Gaya Ilustrasi**")
    gcols6 = st.columns(6)
    for gcol,key in zip(gcols6, GAYA_ID):
        clr = GAYA_CLR[key]
        with gcol:
            st.markdown(
                f'<div style="border:1px solid rgba(128,128,128,.18);border-radius:8px;'
                f'padding:.55rem .45rem;text-align:center;">'
                f'<div style="font-size:1.5rem">{GAYA_ICON[key]}</div>'
                f'<div style="font-size:.66rem;font-weight:600;margin:.2rem 0 .1rem;color:{clr}">'
                f'{GAYA_ID[key]}</div>'
                f'<div style="font-size:.58rem;opacity:.55;text-align:left;line-height:1.35">'
                f'{GAYA_DESC[key]}</div></div>',
                unsafe_allow_html=True
            )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    ca4,cb4 = st.columns(2)
    with ca4:
        st.markdown("**Distribusi Gaya**")
        gc   = DF["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        fig  = px.bar(
            x=gc.values, y=gc.index, orientation="h",
            color=gc.index,
            color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID},
            text=gc.values
        )
        fig.update_layout(**pb(290), showlegend=False, xaxis_title="", yaxis_title="",
                          yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    with cb4:
        st.markdown("**Tren Gaya per Tahun**")
        dfg  = DF[(DF["YEAR"] > 0) & DF["gaya_ilustrasi"].notna()].copy()
        dfg["gaya"] = dfg["gaya_ilustrasi"].map(GAYA_ID)
        trg  = dfg.groupby(["YEAR","gaya"]).size().reset_index(name="n")
        fig2 = px.bar(
            trg, x="YEAR", y="n", color="gaya", barmode="stack",
            color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID}
        )
        fig2.update_layout(**pb(290), xaxis_title="", yaxis_title="",
                           showlegend=True,
                           legend=dict(orientation="h",y=-.2,font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Peta Panas Gaya Ilustrasi × Genre**")
    st.markdown(
        "<small>Proporsi gaya ilustrasi per genre setelah normalisasi genre.</small>",
        unsafe_allow_html=True
    )
    hn_gi = st.slider("Jumlah genre", 6, 20, 12, 2, key="hn_gi")
    st.plotly_chart(heatmap_gaya_genre(DF, hn_gi), use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Figur Manusia vs Non-Manusia**")
    yh    = int(DF["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
    dh    = int(DF["detr_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
    tot   = len(DF)
    agree = int((
        DF["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") &
        DF["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")
    ).sum())

    man_a,man_b,man_c = st.columns([2,1,2])
    with man_a:
        fig_man = go.Figure(data=[
            go.Bar(
                name="YOLOv8n",
                x=["Ada manusia","Tidak ada"],
                y=[yh, tot-yh],
                marker_color=["#66BB6A","rgba(128,128,128,.15)"]
            ),
            go.Bar(
                name="DETR",
                x=["Ada manusia","Tidak ada"],
                y=[dh, tot-dh],
                marker_color=["#42A5F5","rgba(128,128,128,.08)"]
            ),
        ])
        fig_man.update_layout(
            **pb(240), barmode="group", showlegend=True,
            legend=dict(orientation="h",y=-.15), xaxis_title="", yaxis_title=""
        )
        st.plotly_chart(fig_man, use_container_width=True)
    with man_b:
        st.metric("Sepakat keduanya", f"{agree:,}", f"{agree/tot*100:.1f}%")
        st.metric("Hanya YOLOv8n",    f"{yh-agree:,}")
        st.metric("Hanya DETR",       f"{dh-agree:,}")
    with man_c:
        st.markdown("**Top Objek Non-Manusia (YOLO)**")
        obj_ctr = Counter()
        for v in DF["yolo_objek"].dropna():
            s = str(v).strip()
            if s and s not in ("0","nan"):
                for o in s.split(","):
                    o = o.strip()
                    if o and o not in ("person","0"):
                        obj_ctr[o] += 1
        if obj_ctr:
            top_obj = pd.DataFrame(obj_ctr.most_common(12), columns=["Objek","Jumlah"])
            fig_obj = px.bar(
                top_obj, x="Jumlah", y="Objek", orientation="h",
                color_discrete_sequence=["#00ACC1"], text="Jumlah"
            )
            fig_obj.update_layout(**pb(300), showlegend=False, xaxis_title="", yaxis_title="",
                                  yaxis=dict(categoryorder="total ascending"))
            fig_obj.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_obj, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Contoh Buku — Kepercayaan Tertinggi per Gaya**")
    df_gv = DF[DF["gaya_ilustrasi"].notna() & DF["image_ok"]].copy()
    df_gv["gaya_skor"] = pd.to_numeric(df_gv["gaya_skor"], errors="coerce")
    ex_gcols6 = st.columns(6)
    for gcol_ex,key in zip(ex_gcols6, GAYA_ID):
        sub_g = df_gv[df_gv["gaya_ilustrasi"] == key]
        if sub_g.empty:
            continue
        best_g = sub_g.nlargest(1,"gaya_skor").iloc[0]
        clr    = GAYA_CLR[key]
        with gcol_ex:
            cp = cover_path(best_g.get("IMAGE_FILE"))
            if cp:
                st.image(cp, use_container_width=True)
            try: sg = f"{float(best_g.get('gaya_skor',0)):.2f}"
            except: sg = "–"
            probs_bg = {k: float(best_g.get(f"gaya_prob_{k}",0) or 0) for k in GAYA_PROB_KEYS}
            bars_g   = prob_bars(probs_bg, GAYA_CLR, GAYA_ID) if any(probs_bg.values()) else ""
            st.markdown(
                f'<div style="font-size:.62rem;padding:.25rem 0;">'
                f'<div style="font-weight:600;color:{clr}">{GAYA_ID[key]}</div>'
                f'<div style="opacity:.6;line-height:1.3">{str(best_g.get("TITLE",""))[:28]}</div>'
                f'<div style="opacity:.5">skor {sg}</div>'
                f'{"<div style=margin-top:.35rem>"+bars_g+"</div>" if bars_g else ""}</div>',
                unsafe_allow_html=True
            )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Cari Buku berdasarkan Gaya Ilustrasi**")
    gic1,gic2,gic3,gic4 = st.columns([2,2,1,1])
    with gic1: q_gi   = st.text_input("Judul / penulis", key="gi_q")
    with gic2: gaya_sel = st.selectbox("Filter gaya", ["Semua"]+[GAYA_ID[k] for k in GAYA_ID], key="gi_sel")
    with gic3: ada_man  = st.checkbox("Ada manusia", key="gi_man")
    with gic4: n_gi2    = st.slider("Tampilkan", 4, 32, 8, 4, key="gi_n")

    dgi = DF[DF["image_ok"]].copy()
    if q_gi:
        ql3 = q_gi.lower()
        dgi = dgi[
            dgi["TITLE"].str.lower().str.contains(ql3, na=False) |
            dgi["AUTHOR"].str.lower().str.contains(ql3, na=False)
        ]
    if ada_man:
        dgi = dgi[
            dgi["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") |
            dgi["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")
        ]
    if gaya_sel != "Semua":
        grev = {v:k for k,v in GAYA_ID.items()}
        dgi  = dgi[dgi["gaya_ilustrasi"] == grev.get(gaya_sel, gaya_sel)]
    if not dgi.empty:
        grid(dgi.head(n_gi2), show_gi=True)


# ══════════════════════════════════════════════════════════════════════════════
# GENRE
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Genre":
    st.markdown("## Analisis Genre")

    with st.expander("Catatan metodologi & normalisasi", expanded=False):
        st.markdown(
            f"Genre dari metadata Goodreads (crowd-sourced, multi-label). "
            f"Terdapat **{_n_unik} genre unik** setelah normalisasi.\n\n"
            "**Aturan normalisasi:**\n"
            "- Sastra → Sastra Indonesia\n"
            "- Cinta, Roman, Romansa Kontemporer, Kontemporer → Romansa\n"
            "- Thriller, Misteri, Misteri Thriller → Thriller/Misteri\n"
            "- Humor → Komedi\n\n"
            "Genre *Sastra Indonesia*, *Sastra*, dan *Fiksi* dikecualikan dari peta panas."
        )

    all_items = [(g,n) for g,n in _gc.most_common() if g not in GENRE_EXCLUDE and n >= 3]

    st.markdown("**Peta Panas Tumpang Tindih Genre**")
    st.markdown("<small>Co-occurrence antar genre. Diagonal = jumlah buku per genre.</small>",
                unsafe_allow_html=True)
    n_co   = st.slider("Jumlah genre teratas", 8, min(len(all_items),30), 16, 2, key="n_co")
    top_co = [g for g,_ in all_items[:n_co]]
    co     = pd.DataFrame(0, index=top_co, columns=top_co)
    for gl in expand_genres(DF["GENRES"], normalize=True):
        rel = [g for g in gl if g in top_co]
        for i,g1 in enumerate(rel):
            for g2 in rel[i+1:]:
                co.loc[g1,g2] += 1; co.loc[g2,g1] += 1
    for g in top_co:
        co.loc[g,g] = _gc[g]

    fig_co = go.Figure(data=go.Heatmap(
        z=co.values, x=top_co, y=top_co,
        colorscale="Oranges",
        text=co.values.astype(int).astype(str),
        texttemplate="%{text}", textfont=dict(size=9, color="#1A1A1A"),
        hovertemplate="Genre A: %{y}<br>Genre B: %{x}<br>Co-occurrence: %{z}<extra></extra>",
        showscale=True
    ))
    fig_co.update_layout(
        **pb(max(420,n_co*28),
             margin=dict(l=130,r=20,t=32,b=130),
             xaxis=dict(tickangle=-40),
             yaxis=dict(autorange="reversed"),
             xaxis_title="", yaxis_title="")
    )
    st.plotly_chart(fig_co, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Analisis per Genre**")
    st.markdown("<small>Klik genre untuk melihat analisis warna, tipografi, dan ilustrasi.</small>",
                unsafe_allow_html=True)

    if "sel_genre" not in st.session_state:
        st.session_state["sel_genre"] = all_items[0][0] if all_items else None

    top_btn = [g for g,_ in all_items[:40]]
    for cs in range(0, len(top_btn), 8):
        chunk_g = top_btn[cs:cs+8]
        btn_row = st.columns(len(chunk_g))
        for col_b,g in zip(btn_row, chunk_g):
            if col_b.button(g, key=f"gbtn_{g}", use_container_width=True):
                st.session_state["sel_genre"] = g

    sel_genre = st.session_state["sel_genre"]
    if sel_genre:
        st.markdown("<hr class='thin'>", unsafe_allow_html=True)
        genre_lists_all = expand_genres(DF["GENRES"], normalize=True)
        mask_g  = [sel_genre in gl for gl in genre_lists_all]
        df_gs   = DF[mask_g]
        if df_gs.empty:
            st.info(f"Tidak ada buku dengan genre *{sel_genre}*.")
        else:
            st.markdown(
                f'#### Genre: **{sel_genre}** '
                f'<span style="font-family:Inter;font-size:1rem;font-weight:400;opacity:.6">'
                f'— {len(df_gs):,} buku</span>',
                unsafe_allow_html=True
            )
            tab_w,tab_tf,tab_gi = st.tabs(["Warna","Tipografi","Ilustrasi"])

            with tab_w:
                wc_g   = df_gs["warna_kategori"].value_counts()
                wc_all = DF["warna_kategori"].value_counts()
                cw1,cw2 = st.columns(2)
                with cw1:
                    fig_wg = px.bar(
                        x=wc_g.values, y=wc_g.index, orientation="h",
                        color=wc_g.index, color_discrete_map=WARNA_HEX,
                        text=wc_g.values
                    )
                    fig_wg.update_layout(**pb(260), showlegend=False,
                                        xaxis_title="Jumlah", yaxis_title="",
                                        yaxis=dict(categoryorder="total ascending"))
                    fig_wg.update_traces(textposition="outside", marker_line_width=0)
                    st.plotly_chart(fig_wg, use_container_width=True)
                with cw2:
                    diff = (wc_g/len(df_gs) - wc_all/len(DF)).dropna().sort_values(ascending=False)
                    diff_df = diff.reset_index(); diff_df.columns = ["warna","delta"]
                    fig_diff = px.bar(
                        diff_df, x="delta", y="warna", orientation="h",
                        color="warna", color_discrete_map=WARNA_HEX
                    )
                    fig_diff.update_layout(**pb(260), showlegend=False,
                                          xaxis_title="Simpangan proporsi", yaxis_title="",
                                          yaxis=dict(categoryorder="total ascending"))
                    fig_diff.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
                    st.plotly_chart(fig_diff, use_container_width=True)

                st.markdown("**Contoh sampul per warna dominan**")
                top_w      = wc_g.head(4).index.tolist()
                ex_w       = st.columns(len(top_w))
                df_gs_img  = df_gs[df_gs["image_ok"]]
                for wcol,wkey in zip(ex_w, top_w):
                    sub_w = df_gs_img[df_gs_img["warna_kategori"] == wkey]
                    if sub_w.empty:
                        continue
                    sample_w = sub_w.sample(1, random_state=7).iloc[0]
                    with wcol:
                        cp = cover_path(sample_w.get("IMAGE_FILE"))
                        if cp:
                            st.image(cp, use_container_width=True)
                        st.markdown(
                            f'<div style="font-size:.65rem;text-align:center;">'
                            f'<span style="display:inline-block;width:10px;height:10px;'
                            f'background:{WARNA_HEX.get(wkey,"#999")};border-radius:2px;'
                            f'margin-right:4px;vertical-align:middle;"></span>'
                            f'<strong>{wkey}</strong><br>'
                            f'<span style="opacity:.6">{str(sample_w.get("TITLE",""))[:30]}</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

            with tab_tf:
                df_gs_tf = df_gs[
                    df_gs["typeface_kategori"].notna() &
                    (df_gs["typeface_kategori"] != "unclassified")
                ]
                if df_gs_tf.empty:
                    st.info("Belum ada data tipografi untuk genre ini.")
                else:
                    tc_g   = df_gs_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts()
                    tc_all = DF[
                        DF["typeface_kategori"].notna() &
                        (DF["typeface_kategori"] != "unclassified")
                    ]["typeface_kategori"].map(TYPEFACE_ID).value_counts()
                    ctf1,ctf2 = st.columns(2)
                    with ctf1:
                        fig_tg = px.bar(
                            x=tc_g.values, y=tc_g.index, orientation="h",
                            color=tc_g.index,
                            color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID},
                            text=tc_g.values
                        )
                        fig_tg.update_layout(**pb(250), showlegend=False,
                                            xaxis_title="Jumlah", yaxis_title="",
                                            yaxis=dict(categoryorder="total ascending"))
                        fig_tg.update_traces(textposition="outside", marker_line_width=0)
                        st.plotly_chart(fig_tg, use_container_width=True)
                    with ctf2:
                        n_all_tf = len(DF[DF["typeface_kategori"].notna()])
                        diff_tf  = (
                            tc_g/len(df_gs_tf) - tc_all/n_all_tf
                        ).dropna().sort_values(ascending=False)
                        diff_tf_df = diff_tf.reset_index()
                        diff_tf_df.columns = ["tipografi","delta"]
                        fig_dtf = px.bar(
                            diff_tf_df, x="delta", y="tipografi", orientation="h",
                            color="tipografi",
                            color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID}
                        )
                        fig_dtf.update_layout(**pb(250), showlegend=False,
                                             xaxis_title="Simpangan proporsi", yaxis_title="",
                                             yaxis=dict(categoryorder="total ascending"))
                        fig_dtf.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
                        st.plotly_chart(fig_dtf, use_container_width=True)

                    st.markdown("**Contoh sampul per tipografi**")
                    top_tf = [k for k,_ in df_gs_tf["typeface_kategori"].value_counts().head(4).items()]
                    ex_tf  = st.columns(len(top_tf))
                    df_gs_tf_img = df_gs_tf[df_gs_tf["image_ok"]].copy()
                    df_gs_tf_img["typeface_skor"] = pd.to_numeric(
                        df_gs_tf_img["typeface_skor"], errors="coerce"
                    )
                    for tcol,tkey in zip(ex_tf, top_tf):
                        sub_t = df_gs_tf_img[df_gs_tf_img["typeface_kategori"] == tkey]
                        if sub_t.empty:
                            continue
                        best_t = sub_t.nlargest(1,"typeface_skor").iloc[0]
                        clr_t  = TYPEFACE_CLR.get(tkey,"#999")
                        with tcol:
                            cp = cover_path(best_t.get("IMAGE_FILE"))
                            if cp:
                                st.image(cp, use_container_width=True)
                            try: sc_t = f"{float(best_t.get('typeface_skor',0)):.2f}"
                            except: sc_t = "–"
                            st.markdown(
                                f'<div style="font-size:.65rem;text-align:center;">'
                                f'<strong style="color:{clr_t}">{TYPEFACE_ID.get(tkey,tkey)}</strong><br>'
                                f'<span style="opacity:.6">{str(best_t.get("TITLE",""))[:30]}</span><br>'
                                f'<span style="opacity:.5">skor {sc_t}</span></div>',
                                unsafe_allow_html=True
                            )

            with tab_gi:
                gc_g     = df_gs["gaya_ilustrasi"].map(GAYA_ID).value_counts()
                gc_all_d = DF["gaya_ilustrasi"].map(GAYA_ID).value_counts()
                cg1,cg2  = st.columns(2)
                with cg1:
                    fig_gg = px.bar(
                        x=gc_g.values, y=gc_g.index, orientation="h",
                        color=gc_g.index,
                        color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID},
                        text=gc_g.values
                    )
                    fig_gg.update_layout(**pb(250), showlegend=False,
                                        xaxis_title="Jumlah", yaxis_title="",
                                        yaxis=dict(categoryorder="total ascending"))
                    fig_gg.update_traces(textposition="outside", marker_line_width=0)
                    st.plotly_chart(fig_gg, use_container_width=True)
                with cg2:
                    diff_gi    = (gc_g/len(df_gs) - gc_all_d/len(DF)).dropna().sort_values(ascending=False)
                    diff_gi_df = diff_gi.reset_index(); diff_gi_df.columns = ["gaya","delta"]
                    fig_dgi = px.bar(
                        diff_gi_df, x="delta", y="gaya", orientation="h",
                        color="gaya",
                        color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID}
                    )
                    fig_dgi.update_layout(**pb(250), showlegend=False,
                                         xaxis_title="Simpangan proporsi", yaxis_title="",
                                         yaxis=dict(categoryorder="total ascending"))
                    fig_dgi.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
                    st.plotly_chart(fig_dgi, use_container_width=True)

                st.markdown("**Contoh sampul per gaya ilustrasi**")
                top_gi       = [k for k,_ in df_gs["gaya_ilustrasi"].value_counts().head(4).items()]
                ex_gi        = st.columns(len(top_gi))
                df_gs_gi_img = df_gs[df_gs["image_ok"]].copy()
                df_gs_gi_img["gaya_skor"] = pd.to_numeric(df_gs_gi_img["gaya_skor"], errors="coerce")
                for gcoli,gikey in zip(ex_gi, top_gi):
                    sub_gi = df_gs_gi_img[df_gs_gi_img["gaya_ilustrasi"] == gikey]
                    if sub_gi.empty:
                        continue
                    best_gi = sub_gi.nlargest(1,"gaya_skor").iloc[0]
                    clr_gi  = GAYA_CLR.get(gikey,"#999")
                    with gcoli:
                        cp = cover_path(best_gi.get("IMAGE_FILE"))
                        if cp:
                            st.image(cp, use_container_width=True)
                        try: sc_gi2 = f"{float(best_gi.get('gaya_skor',0)):.2f}"
                        except: sc_gi2 = "–"
                        st.markdown(
                            f'<div style="font-size:.65rem;text-align:center;">'
                            f'<strong style="color:{clr_gi}">'
                            f'{GAYA_ICON.get(gikey,"")} {GAYA_ID.get(gikey,gikey)}</strong><br>'
                            f'<span style="opacity:.6">{str(best_gi.get("TITLE",""))[:30]}</span><br>'
                            f'<span style="opacity:.5">skor {sc_gi2}</span></div>',
                            unsafe_allow_html=True
                        )


# ══════════════════════════════════════════════════════════════════════════════
# ILLUSTRATOR
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Illustrator":
    st.markdown("## Illustrator Sampul")

    has_ill   = DF["ILLUSTRATOR"].ne("")
    n_ill     = has_ill.sum()
    n_no_ill  = (~has_ill).sum()

    st.markdown(f"**{n_ill} buku** dari {len(DF):,} yang menyebutkan nama illustrator di Goodreads.")
    df_ill = DF[has_ill].copy()

    q_ill = st.text_input("Cari illustrator atau judul buku", key="ill_q")
    if q_ill:
        ql = q_ill.lower()
        df_ill = df_ill[
            df_ill["ILLUSTRATOR"].str.lower().str.contains(ql, na=False) |
            df_ill["TITLE"].str.lower().str.contains(ql, na=False)
        ]

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    ill_sum = (
        df_ill.groupby("ILLUSTRATOR").agg(
            Buku=("TITLE","count"),
            Judul=("TITLE", lambda x: " · ".join(x.values.tolist())),
            Tahun=("YEAR",  lambda x: ", ".join(sorted({str(int(v)) for v in x if v > 0})))
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
        }
    )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("### Perbandingan Sampul: Dengan vs Tanpa Illustrator")
    df_with  = DF[has_ill].copy()
    df_wout  = DF[~has_ill].copy()
    for d in [df_with, df_wout]:
        for c in ["brightness_mean","saturation_mean","gaya_skor","typeface_skor"]:
            if c in d.columns:
                d[c] = pd.to_numeric(d[c], errors="coerce")

    met_cols = st.columns(4)
    for mcol,(lbl,col) in zip(met_cols,[
        ("Kecerahan",    "brightness_mean"),
        ("Saturasi",     "saturation_mean"),
        ("Skor Gaya",    "gaya_skor"),
        ("Skor Tipografi","typeface_skor"),
    ]):
        v_w = df_with[col].mean() if col in df_with.columns else 0
        v_o = df_wout[col].mean() if col in df_wout.columns else 0
        mcol.metric(f"{lbl} (dengan ill.)", f"{v_w:.3f}", f"{v_w-v_o:+.3f} vs tanpa")

    st.markdown("**Distribusi Warna Dominan**")
    wc_w   = df_with["warna_kategori"].value_counts(normalize=True)
    wc_o   = df_wout["warna_kategori"].value_counts(normalize=True)
    all_w  = sorted(set(wc_w.index) | set(wc_o.index))
    warna_cmp = pd.DataFrame({
        "Dengan Illustrator": [wc_w.get(w,0) for w in all_w],
        "Tanpa Illustrator":  [wc_o.get(w,0) for w in all_w],
    }, index=all_w)
    fig_wc = go.Figure()
    fig_wc.add_trace(go.Bar(
        name="Dengan Illustrator", x=warna_cmp.index,
        y=warna_cmp["Dengan Illustrator"],
        marker_color=[WARNA_HEX.get(w,"#999") for w in all_w], opacity=.9
    ))
    fig_wc.add_trace(go.Bar(
        name="Tanpa Illustrator", x=warna_cmp.index,
        y=warna_cmp["Tanpa Illustrator"],
        marker_color=[WARNA_HEX.get(w,"#999") for w in all_w], opacity=.35
    ))
    fig_wc.update_layout(
        **pb(280), barmode="group", showlegend=True,
        xaxis_title="", yaxis_title="Proporsi",
        legend=dict(orientation="h",y=-.15)
    )
    st.plotly_chart(fig_wc, use_container_width=True)

    il2a,il2b = st.columns(2)
    with il2a:
        st.markdown("**Gaya Ilustrasi — Dengan Illustrator**")
        gc_w   = df_with["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        fig_gw = px.pie(
            values=gc_w.values, names=gc_w.index, hole=.5,
            color=gc_w.index,
            color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID}
        )
        fig_gw.update_layout(**pb(240), showlegend=True,
                             legend=dict(orientation="h",y=-.1,font=dict(size=10)))
        fig_gw.update_traces(textinfo="percent", textfont_size=10)
        st.plotly_chart(fig_gw, use_container_width=True)
    with il2b:
        st.markdown("**Gaya Ilustrasi — Tanpa Illustrator**")
        gc_o   = df_wout["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        fig_go = px.pie(
            values=gc_o.values, names=gc_o.index, hole=.5,
            color=gc_o.index,
            color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID}
        )
        fig_go.update_layout(**pb(240), showlegend=True,
                             legend=dict(orientation="h",y=-.1,font=dict(size=10)))
        fig_go.update_traces(textinfo="percent", textfont_size=10)
        st.plotly_chart(fig_go, use_container_width=True)

    st.markdown("**Simpangan Gaya: Dengan − Tanpa Illustrator**")
    diff_gaya    = (gc_w/n_ill - gc_o/n_no_ill).dropna().sort_values(ascending=False)
    diff_gaya_df = diff_gaya.reset_index(); diff_gaya_df.columns = ["gaya","delta"]
    fig_dg = px.bar(
        diff_gaya_df, x="delta", y="gaya", orientation="h",
        color="gaya",
        color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID}
    )
    fig_dg.update_layout(**pb(240), showlegend=False,
                         xaxis_title="Selisih proporsi", yaxis_title="",
                         yaxis=dict(categoryorder="total ascending"))
    fig_dg.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
    st.plotly_chart(fig_dg, use_container_width=True)
    st.markdown(
        "<small style='opacity:.55'>Nilai positif = gaya lebih sering ditemukan "
        "pada buku dengan nama illustrator.</small>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# JELAJAH BUKU
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Jelajah Buku":
    st.markdown("## Jelajah Buku")
    st.markdown("Temukan buku dari kombinasi kriteria visual dan metadata.")

    top25_j = [g for g,_ in _gc.most_common() if g not in GENRE_EXCLUDE][:25]

    with st.form("form_jelajah"):
        r1       = st.columns(4)
        q_j      = r1[0].text_input("Judul / penulis")
        warna_j  = r1[1].selectbox("Warna dominan", ["Semua"]+sorted(DF["warna_kategori"].dropna().unique()))
        tf_j     = r1[2].selectbox("Tipografi", ["Semua"]+[TYPEFACE_ID[k] for k in TYPEFACE_ID])
        gaya_j   = r1[3].selectbox("Gaya ilustrasi", ["Semua"]+[GAYA_ID[k] for k in GAYA_ID])

        r2       = st.columns(4)
        genre_j  = r2[0].selectbox("Genre", ["Semua"]+top25_j)
        rak_j    = r2[1].selectbox("Rak", ["Semua","Fiksi","Puisi"])
        ill_j    = r2[2].selectbox("Illustrator", ["Semua","Dengan illustrator"])
        man_j    = r2[3].checkbox("Ada figur manusia")

        r3  = st.columns([3,1])
        n_j = r3[1].slider("Tampilkan", 8, 48, 16, 8)
        st.form_submit_button("Cari")

    dj = DF[DF["image_ok"]].copy()
    if q_j:
        ql = q_j.lower()
        dj = dj[
            dj["TITLE"].str.lower().str.contains(ql, na=False) |
            dj["AUTHOR"].str.lower().str.contains(ql, na=False)
        ]
    if warna_j != "Semua":
        dj = dj[dj["warna_kategori"] == warna_j]
    if tf_j != "Semua":
        tf_rev3 = {v:k for k,v in TYPEFACE_ID.items()}
        dj = dj[dj["typeface_kategori"] == tf_rev3.get(tf_j, tf_j)]
    if gaya_j != "Semua":
        grev3 = {v:k for k,v in GAYA_ID.items()}
        dj = dj[dj["gaya_ilustrasi"] == grev3.get(gaya_j, gaya_j)]
    if genre_j != "Semua":
        gl_all  = expand_genres(dj["GENRES"], normalize=True)
        mask_j  = [genre_j in gl for gl in gl_all]
        dj      = dj[mask_j]
    if rak_j == "Fiksi":
        dj = dj[dj["SHELF"] == "fiksi"]
    elif rak_j == "Puisi":
        dj = dj[dj["SHELF"] == "puisi-asli"]
    if ill_j == "Dengan illustrator":
        dj = dj[dj["ILLUSTRATOR"].ne("")]
    if man_j:
        dj = dj[
            dj["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") |
            dj["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")
        ]

    st.markdown(f"**{len(dj):,} buku ditemukan**")
    if not dj.empty:
        grid(dj.head(n_j), show_tf=True, show_gi=True)
