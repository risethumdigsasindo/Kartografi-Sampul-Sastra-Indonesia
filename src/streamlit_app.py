"""Kartografi Sampul Sastra Indonesia (2000–2025)"""
import io
import os
from collections import Counter
from itertools import combinations

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kartografi Sampul Sastra Indonesia",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
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

# ── KONSTANTA WARNA ───────────────────────────────────────────────────────────
WARNA_HEX = {
    "putih":   "#F5F5F0", "hitam": "#1A1A1A", "abu":    "#8E8E93",
    "merah":   "#E53935", "pink":  "#F06292", "oranye": "#FB8C00",
    "cokelat": "#795548", "kuning":"#FDD835", "hijau":  "#43A047",
    "biru":    "#1E88E5", "ungu":  "#8E24AA",
}
WARNA_TXT = {
    "putih":"#333","hitam":"#eee","abu":"#fff","merah":"#fff","pink":"#fff",
    "oranye":"#fff","cokelat":"#fff","kuning":"#333","hijau":"#fff",
    "biru":"#fff","ungu":"#fff",
}
WARNA_ORDER = ["putih","oranye","cokelat","biru","merah","pink","hitam","kuning","ungu","hijau","abu"]

# ── KONSTANTA TIPOGRAFI ───────────────────────────────────────────────────────
TIPE_FONT_GROUP = {
    "Display":             "display",
    "Display Condensed":   "display",
    "Handwriting":         "script",
    "Humanist Sans-Serif": "sans_serif",
    "Neo-Grotesque":       "sans_serif",
    "Geometric Sans-Serif":"sans_serif",
    "Grotesque Sans-Serif":"sans_serif",
    "Humanist Serif":      "humanist_serif",
    "Transitional Serif":  "transitional_serif",
    "Slab Serif":          "slab_serif",
}
# Warna per tipe_font (untuk konsistensi visual)
TIPE_FONT_CLR = {
    "Display":             "#FFA726",
    "Display Condensed":   "#FFB74D",
    "Handwriting":         "#26A69A",
    "Humanist Sans-Serif": "#42A5F5",
    "Neo-Grotesque":       "#29B6F6",
    "Geometric Sans-Serif":"#26C6DA",
    "Grotesque Sans-Serif":"#4FC3F7",
    "Humanist Serif":      "#5C6BC0",
    "Transitional Serif":  "#7E57C2",
    "Slab Serif":          "#EC407A",
}


TYPEFACE_ID = {
    "humanist_serif":     "Humanist Serif",
    "transitional_serif": "Transitional Serif",
    "slab_serif":         "Slab Serif",
    "sans_serif":         "Sans-serif",
    "script":             "Kaligrafi/Script",
    "display":            "Display/Dekoratif",
    "tidak_terklasifikasi": "Tidak Terklasifikasi",
}
TYPEFACE_CLR = {
    "humanist_serif":      "#5C6BC0",
    "transitional_serif":  "#7E57C2",
    "slab_serif":          "#EC407A",
    "sans_serif":          "#42A5F5",
    "script":              "#26A69A",
    "display":             "#FFA726",
    "tidak_terklasifikasi":"#BDBDBD",
}
TYPEFACE_FONT = {
    "humanist_serif":     "Georgia,serif",
    "transitional_serif": "'Times New Roman',serif",
    "slab_serif":         "'Courier New',monospace",
    "sans_serif":         "Helvetica,Arial,sans-serif",
    "script":             "cursive",
    "display":            "Impact,fantasy",
    "tidak_terklasifikasi":"inherit",
}
TYPEFACE_DESC = {
    "humanist_serif":     "Kontras sedang, axis diagonal, bracket serif. Garamond, Sabon.",
    "transitional_serif": "Kontras lebih tinggi, axis hampir vertikal. Baskerville, Times.",
    "slab_serif":         "Serif persegi tebal, kontras rendah. Clarendon, Rockwell.",
    "sans_serif":         "Tanpa serif, stroke seragam. Helvetica, Futura.",
    "script":             "Stroke mengalir, menyerupai kaligrafi atau tulisan tangan.",
    "display":            "Bentuk huruf sangat stilistik, ornamental, untuk impak besar.",
    "tidak_terklasifikasi":"Tidak dapat diklasifikasi otomatis.",
}
TF_ANALISIS = [k for k in TYPEFACE_ID if k != "tidak_terklasifikasi"]

# ── KONSTANTA ILUSTRASI ───────────────────────────────────────────────────────
GAYA_ID = {
    "photograph":    "Fotografi",
    "flat_graphic":  "Ilustrasi Datar",
    "hand_drawn":    "Gambar Tangan",
    "text_dominant": "Dominan Teks",
    "abstract":      "Abstrak",
    "collage":       "Kolase",
}
GAYA_CLR = {
    "photograph":   "#1E88E5","flat_graphic": "#43A047","hand_drawn":    "#FB8C00",
    "text_dominant":"#E53935","abstract":     "#8E24AA","collage":       "#00ACC1",
}
GAYA_ICON = {
    "photograph":"📷","flat_graphic":"🎨","hand_drawn":"✏️",
    "text_dominant":"🔤","abstract":"🔷","collage":"🗂️",
}
GAYA_PROB_KEYS = ["photograph","hand_drawn","abstract","flat_graphic","text_dominant"]

SHELF_LABEL = {"fiksi":"Fiksi","puisi-asli":"Puisi"}

GENRE_NORM = {
    "Cinta":"Romansa","Roman":"Romansa","Romansa Kontemporer":"Romansa",
    "Kontemporer":"Romansa","Thriller":"Thriller/Misteri","Misteri":"Thriller/Misteri",
    "Misteri Thriller":"Thriller/Misteri","Thriller Suspense":"Thriller/Misteri",
    "Psychological Thriller":"Thriller/Misteri","Suspense":"Thriller/Misteri",
    "Detective":"Thriller/Misteri","Kriminal":"Thriller/Misteri",
    "Supranatural":"Horor","Humor":"Komedi","Romansatic":"Romansa",
    "Young Adult Romansace":"Romansa","New Adult":"Remaja",
    "Collections":"Antologi","Middle Grade":"Fantasi",
    "Fiksi Ilmiah":"Fiksi Sains","Distopia":"Fiksi Sains",
    "Sejarah":"Fiksi Sejarah","Historical Fiction":"Fiksi Sejarah","Historical":"Fiksi Sejarah",
}
_NONFICTION_LOWER = {"nonfiction","non-fiction","nonfiksi","non fiksi","non-fiksi","nonfiction (general)"}
GENRE_EXCLUDE = {"Sastra Indonesia","Sastra","Fiksi","Nonfiction","Non-fiction",
                 "Nonfiksi","Non Fiksi","Non-fiksi"}

KLASTER_COOC = [
    {
        "id":"K1","label":"Klaster 1 — Novel sebagai genre bentuk yang dominan",
        "short":"Klaster 1","color":"#2E4057","bg":"#EEF2F7",
        "genres":["Novel","Cerita Pendek","Antologi","Puisi"],
        "pairs":[("Drama","Novel"),("Novel","Remaja"),("Antologi","Cerita Pendek"),
                 ("Novel","Romansa"),("Fiksi Sejarah","Novel"),("Komedi","Novel")],
    },
    {
        "id":"K2","label":"Klaster 2 — Romansa sebagai gravitasi genre tematik",
        "short":"Klaster 2","color":"#993556","bg":"#FBF0F3",
        "genres":["Romansa","Chick Lit","Persahabatan","Remaja","Dewasa","Keluarga","Drama","Slice of Life","Komedi"],
        "pairs":[("Chick Lit","Romansa"),("Persahabatan","Romansa"),("Remaja","Romansa"),
                 ("Dewasa","Romansa"),("Keluarga","Romansa"),("Drama","Romansa")],
    },
    {
        "id":"K3","label":"Klaster 3 — Eskapisme: fantasi, aksi & ketegangan",
        "short":"Klaster 3","color":"#1D9E75","bg":"#EEF8F4",
        "genres":["Fantasi","Fiksi Sejarah","Petualangan","Aksi","Fiksi Sains","Thriller/Misteri","Horor","Anak-anak"],
        "pairs":[("Fantasi","Fiksi Sains"),("Fantasi","Petualangan"),("Aksi","Fantasi"),
                 ("Aksi","Petualangan"),("Horor","Thriller/Misteri"),("Fiksi Sejarah","Novel")],
    },
]
GENRE_KLASTER_MAP = {}
for _kl in KLASTER_COOC:
    for _g in _kl["genres"]:
        if _g not in GENRE_KLASTER_MAP:
            GENRE_KLASTER_MAP[_g] = _kl


# ── PATH ──────────────────────────────────────────────────────────────────────
_base = os.path.dirname(__file__)
DATA_PATH = os.path.join(_base, "data.csv")
COVER_DIR = os.path.join(_base, "..", "covers")


# ── HELPERS WARNA ─────────────────────────────────────────────────────────────
def _klasifikasi_hsv(h, s, v):
    try:
        h, s, v = float(h or 0), float(s or 0), float(v or 0)
    except Exception:
        return None
    if v < 50:              return "hitam"
    if s < 30 and v > 160: return "putih"
    if s < 50:             return "putih" if v > 160 else "abu"
    if h < 25 and v < 130 and s > 80: return "cokelat"
    if (h < 10 or h >= 155) and v > 160 and s < 170: return "pink"
    if h < 10 or h >= 170:  return "merah"
    elif h < 25:             return "oranye"
    elif h < 40:             return "kuning"
    elif h < 85:             return "hijau"
    elif h < 130:            return "biru"
    elif h < 170:            return "ungu"
    return "merah"


def _reklasifikasi_warna(row):
    try:
        h = float(row.get("warna_h_1", 0) or 0)
        s = float(row.get("warna_s_1", 0) or 0)
        v = float(row.get("warna_v_1", 0) or 0)
    except Exception:
        return row.get("warna_kategori", "putih")
    return _klasifikasi_hsv(h, s, v) or "putih"


def compute_warna_distribusi(d):
    acc = {w: 0.0 for w in WARNA_ORDER}
    for _, row in d.iterrows():
        for i in range(1, 6):
            pct = row.get(f"warna_pct_{i}", 0)
            try:
                pct = float(pct or 0)
            except Exception:
                pct = 0.0
            if pct <= 0:
                continue
            k = _klasifikasi_hsv(row.get(f"warna_h_{i}", 0),
                                  row.get(f"warna_s_{i}", 0),
                                  row.get(f"warna_v_{i}", 0))
            if k and k in acc:
                acc[k] += pct
    total = sum(acc.values())
    if total > 0:
        acc = {k: v / total for k, v in acc.items()}
    return pd.Series(acc)


# ── LOAD DATA ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data(path):
    d = pd.read_csv(path, sep=",", encoding="utf-8-sig",
                    on_bad_lines="skip", engine="python")
    d = d[d["SHELF"].isin(["fiksi", "puisi-asli"])].copy()

    num_cols = ["YEAR","RATING","TOTAL_RATING","TOTAL_REVIEW",
                "brightness_mean","saturation_mean","typeface_skor",
                "gaya_skor","teks_coverage","n_region_teks",
                "judul_match_score","yolo_n_objek","detr_objek_n",
                "typeface_confidence"]
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

    valid_tf = set(TYPEFACE_ID.keys())
    if "typeface_kategori" in d.columns:
        d["typeface_kategori"] = d["typeface_kategori"].fillna("tidak_terklasifikasi")
        d["typeface_kategori"] = d["typeface_kategori"].where(
            d["typeface_kategori"].astype(str).str.strip().isin(valid_tf),
            other="tidak_terklasifikasi"
        )

    if "gaya_ilustrasi" in d.columns:
        d["gaya_ilustrasi"] = d["gaya_ilustrasi"].where(
            d["gaya_ilustrasi"].astype(str).str.strip().isin(set(GAYA_ID.keys())),
            other=pd.NA
        )

    d["warna_kategori"] = d.apply(_reklasifikasi_warna, axis=1)
    return d


# ── GENRE HELPERS ─────────────────────────────────────────────────────────────
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


def _top_genres(d, n=16):
    gc = genre_counts(d, normalize=True)
    return [g for g, _ in gc.most_common() if g not in GENRE_EXCLUDE and gc[g] >= 3][:n]


# ── PLOT BASE ─────────────────────────────────────────────────────────────────
def pb(height=320, **kw):
    b = dict(height=height, margin=dict(l=8,r=8,t=28,b=8),
             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
             font=dict(size=11, color="#1A1A1A"))
    b.update(kw)
    return b


# ── COVER & CARD ──────────────────────────────────────────────────────────────
def cover_path(img):
    if not img or str(img) in ("","nan"): return None
    p = os.path.join(COVER_DIR, str(img))
    return p if os.path.exists(p) else None


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
            if dist < best_d: best,best_d = nama,dist
        except Exception: pass
    return best


def palette_html(row, n=5):
    parts, total = [], 0.0
    for i in range(1, n+1):
        hx = str(row.get(f"warna_hex_{i}","") or "").strip()
        pct = row.get(f"warna_pct_{i}", 0)
        try: pct = float(pct)
        except: pct = 0.0
        if not hx or hx in ("nan",""): continue
        if not hx.startswith("#"): hx = "#"+hx
        parts.append((hx, pct, _nama_warna(hx))); total += pct
    if not parts: return ""
    scale = 100.0/total if total > 0 else 1.0
    sw = "".join(
        f'<div class="pal-sw" style="background:{hx};width:{pct*scale:.1f}%;" title="{n} ({pct:.1f}%)"></div>'
        for hx,pct,n in parts
    )
    return f'<div class="pal-row">{sw}</div>'


def prob_bars(probs_dict, colors_dict, label_map):
    html = ""
    for key, val in sorted(probs_dict.items(), key=lambda x: -x[1]):
        label = label_map.get(key, key)
        clr = colors_dict.get(key, "#999")
        pct = val * 100
        html += (
            f'<div class="prob-bar-wrap"><div class="prob-label"><span>{label}</span>'
            f'<span>{pct:.1f}%</span></div><div class="prob-bar-bg">'
            f'<div class="prob-bar-fill" style="width:{pct:.1f}%;background:{clr};"></div>'
            f"</div></div>"
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
        year = int(row["YEAR"]) if row.get("YEAR", 0) and int(row.get("YEAR", 0)) > 0 else "–"
        url = row.get("URL", "")
        title = str(row.get("TITLE", "–"))
        title_html = (
            f'<a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">{title}</a>'
            if url else title
        )
        shelf_lbl = SHELF_LABEL.get(str(row.get("SHELF", "")), str(row.get("SHELF", "")))
        badges = f'<span class="badge">{shelf_lbl}</span>'
        tf_bars = gi_bars = ""

        if show_tf:
            tk = str(row.get("typeface_kategori",""))
            if tk and tk != "tidak_terklasifikasi":
                clr = TYPEFACE_CLR.get(tk, "#999")
                try: sc = f"{float(row.get('typeface_skor',0)):.2f}"
                except: sc = "–"
                badges += f'<span class="badge" style="border-color:{clr};color:{clr};">{TYPEFACE_ID.get(tk,tk)} {sc}</span>'
                probs = {k: float(row.get(f"typeface_prob_{k}", 0) or 0) for k in TF_ANALISIS}
                if any(probs.values()): tf_bars = prob_bars(probs, TYPEFACE_CLR, TYPEFACE_ID)

        if show_gi and pd.notna(row.get("gaya_ilustrasi")):
            gk = str(row["gaya_ilustrasi"])
            clr = GAYA_CLR.get(gk, "#999")
            try: sc_gi = f"{float(row.get('gaya_skor',0)):.2f}"
            except: sc_gi = "–"
            badges += f'<span class="badge" style="border-color:{clr};color:{clr};">{GAYA_ID.get(gk,gk)} {sc_gi}</span>'
            probs_gi = {k: float(row.get(f"gaya_prob_{k}", 0) or 0) for k in GAYA_PROB_KEYS}
            if any(probs_gi.values()): gi_bars = prob_bars(probs_gi, GAYA_CLR, GAYA_ID)

        bars = tf_bars or gi_bars
        st.markdown(
            f'<div class="bk-info"><div class="bk-title">{title_html}</div>'
            f'<div class="bk-meta">{row.get("AUTHOR","–")} · {year}</div>'
            f'{palette_html(row)}{badges}'
            f'{"<div style=margin-top:.4rem>" + bars + "</div>" if bars else ""}</div>',
            unsafe_allow_html=True
        )


def grid(subset, n_cols=4, **kw):
    subset = subset.reset_index(drop=True)
    if subset.empty:
        st.info("Tidak ada buku yang cocok.")
        return
    for start in range(0, len(subset), n_cols):
        chunk = subset.iloc[start:start+n_cols]
        cols = st.columns(n_cols)
        for j, (_, row) in enumerate(chunk.iterrows()):
            book_card(row, cols[j], **kw)


# ── HEATMAPS ──────────────────────────────────────────────────────────────────
def heatmap_warna_genre(d, top_n=16):
    genres = _top_genres(d, top_n)
    mat = pd.DataFrame(0.0, index=genres, columns=WARNA_ORDER)
    genre_lists = expand_genres(d["GENRES"], normalize=True)
    for g in genres:
        mask = [g in gl for gl in genre_lists]
        sub = d[mask]
        if len(sub) == 0: continue
        vc = compute_warna_distribusi(sub)
        for w in WARNA_ORDER:
            mat.loc[g, w] = vc.get(w, 0.0)
    warna_global = compute_warna_distribusi(d)
    x_labels = [f"{w}<br>({warna_global.get(w,0)*100:.1f}%)" for w in WARNA_ORDER]
    y_labels = []
    for g in genres:
        kl = GENRE_KLASTER_MAP.get(g)
        y_labels.append(f"{g}  [{kl['id']}]" if kl else g)
    text_mat = (mat*100).round(1).astype(str)+"%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=x_labels, y=y_labels,
        colorscale="YlOrRd",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=9, color="#1A1A1A"),
        showscale=True, zmin=0, zmax=1,
    ))
    fig.update_layout(**pb(max(360,top_n*30),
        margin=dict(l=180,r=20,t=40,b=90),
        yaxis=dict(autorange="reversed"),
        xaxis_title="", yaxis_title="",
    ))
    return fig


def heatmap_tf_genre(d, top_n=12):
    genres = _top_genres(d, top_n)
    tf_keys = TF_ANALISIS
    tf_labels = [TYPEFACE_ID[k] for k in tf_keys]
    mat = pd.DataFrame(0.0, index=genres, columns=tf_labels)
    d2 = d[d["typeface_kategori"].isin(tf_keys)]
    genre_lists = expand_genres(d2["GENRES"], normalize=True)
    for g in genres:
        mask = [g in gl for gl in genre_lists]
        sub = d2[mask]
        if len(sub) == 0: continue
        vc = sub["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)
        for k in tf_keys:
            mat.loc[g, TYPEFACE_ID[k]] = vc.get(TYPEFACE_ID[k], 0.0)
    y_labels = []
    for g in genres:
        kl = GENRE_KLASTER_MAP.get(g)
        y_labels.append(f"{g}  [{kl['id']}]" if kl else g)
    text_mat = (mat*100).round(0).astype(int).astype(str)+"%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=tf_labels, y=y_labels,
        colorscale="Purples",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=9, color="#1A1A1A"),
        showscale=True,
    ))
    fig.update_layout(**pb(max(340,top_n*28),
        margin=dict(l=180,r=20,t=32,b=90),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickangle=-30),
        xaxis_title="", yaxis_title="",
    ))
    return fig


def heatmap_gaya_genre(d, top_n=12):
    genres = _top_genres(d, top_n)
    gaya_keys = list(GAYA_ID.keys())
    gaya_labels = [GAYA_ID[k] for k in gaya_keys]
    mat = pd.DataFrame(0.0, index=genres, columns=gaya_labels)
    d2 = d[d["gaya_ilustrasi"].notna()]
    genre_lists = expand_genres(d2["GENRES"], normalize=True)
    for g in genres:
        mask = [g in gl for gl in genre_lists]
        sub = d2[mask]
        if len(sub) == 0: continue
        vc = sub["gaya_ilustrasi"].map(GAYA_ID).value_counts(normalize=True)
        for k in gaya_keys:
            mat.loc[g, GAYA_ID[k]] = vc.get(GAYA_ID[k], 0.0)
    y_labels = []
    for g in genres:
        kl = GENRE_KLASTER_MAP.get(g)
        y_labels.append(f"{g}  [{kl['id']}]" if kl else g)
    text_mat = (mat*100).round(0).astype(int).astype(str)+"%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=gaya_labels, y=y_labels,
        colorscale="Greens",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=9, color="#1A1A1A"),
        showscale=True,
    ))
    fig.update_layout(**pb(max(340,top_n*28),
        margin=dict(l=180,r=20,t=32,b=60),
        yaxis=dict(autorange="reversed"),
        xaxis_title="", yaxis_title="",
    ))
    return fig


# ── CO-OCCURRENCE ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def compute_cooccurrence(_df, min_count=30):
    EXCL = {"sastra indonesia","fiksi","indonesia","fiction",
            "indonesian literature","novel indonesia","sastraindonesia","sastra"}
    NORM = {
        "Misteri":"Thriller/Misteri","Thriller":"Thriller/Misteri",
        "Misteri Thriller":"Thriller/Misteri","Humor":"Komedi",
        "Cinta":"Romansa","Sejarah":"Fiksi Sejarah","Romansa Kontemporer":"Romansa",
        "Kontemporer":"Romansa","Roman":"Romansa",
        "Historical Fiction":"Fiksi Sejarah","Historical":"Fiksi Sejarah",
    }
    def parse(g):
        if pd.isna(g): return []
        res = []
        for p in str(g).split(","):
            p = p.strip()
            if p.lower() not in EXCL and p.lower() not in _NONFICTION_LOWER and len(p) > 1:
                res.append(NORM.get(p, p))
        return list(set(res))

    genre_lists = _df["GENRES"].apply(parse)
    freq = Counter(g for gl in genre_lists for g in gl)
    top = {g for g,c in freq.items() if c >= min_count}
    counts, cooc = {}, Counter()
    for gl in genre_lists:
        gl_top = [g for g in gl if g in top]
        for g in gl_top:
            counts[g] = counts.get(g, 0)+1
        for a,b in combinations(sorted(gl_top), 2):
            cooc[(a,b)] += 1
    rows = []
    for (a,b),ov in cooc.items():
        ca,cb = counts.get(a,0), counts.get(b,0)
        pct = round(ov/min(ca,cb)*100)
        rows.append({"g1":a,"g2":b,"ca":ca,"cb":cb,"ov":ov,"pct":pct})
    return pd.DataFrame(rows).sort_values("pct", ascending=False), counts


def _pill_color(pct):
    if pct >= 80: return "#FADADD","#922B21"
    if pct >= 56: return "#FDEBD0","#784212"
    if pct >= 40: return "#D6EAF8","#1A5276"
    if pct >= 20: return "#D5F5E3","#1E8449"
    return "#F0F0F0","#555555"


def render_cooc_table(cooc_df, counts):
    lookup = {}
    for _,r in cooc_df.iterrows():
        lookup[(r["g1"],r["g2"])] = r
        lookup[(r["g2"],r["g1"])] = r

    def _lu(g1,g2):
        r = lookup.get((g1,g2))
        return r if r is not None else lookup.get((g2,g1))

    html = """<table style="width:100%;border-collapse:collapse;font-size:12px;font-family:'Inter',sans-serif;">
    <thead><tr style="background:#2E4057;color:white;">
      <th style="padding:7px 10px;text-align:left;">Genre 1</th>
      <th style="padding:7px 10px;text-align:left;">Genre 2</th>
      <th style="padding:7px 10px;text-align:center;">N Genre 1</th>
      <th style="padding:7px 10px;text-align:center;">N Genre 2</th>
      <th style="padding:7px 10px;text-align:center;">Overlap</th>
      <th style="padding:7px 10px;text-align:center;">%</th>
    </tr></thead><tbody>"""

    for kl in KLASTER_COOC:
        html += (f'<tr><td colspan="6" style="background:{kl["bg"]};color:{kl["color"]};'
                 f'font-style:italic;font-weight:600;padding:8px 10px;">{kl["label"]}</td></tr>\n')
        for g1,g2 in kl["pairs"]:
            r = _lu(g1,g2)
            if r is None: continue
            pct = int(r["pct"])
            bg,fg = _pill_color(pct)
            html += (
                f'<tr style="background:#fff;"><td style="padding:6px 10px;border:1px solid #E0E0E0;"><strong>{g1}</strong></td>'
                f'<td style="padding:6px 10px;border:1px solid #E0E0E0;"><strong>{g2}</strong></td>'
                f'<td style="padding:6px 10px;border:1px solid #E0E0E0;text-align:center;">{int(r["ca"]):,}</td>'
                f'<td style="padding:6px 10px;border:1px solid #E0E0E0;text-align:center;">{int(r["cb"]):,}</td>'
                f'<td style="padding:6px 10px;border:1px solid #E0E0E0;text-align:center;">{int(r["ov"]):,}</td>'
                f'<td style="padding:6px 10px;border:1px solid #E0E0E0;text-align:center;">'
                f'<span style="background:{bg};color:{fg};border-radius:10px;padding:1px 8px;font-weight:700;">{pct}%</span></td></tr>\n'
            )
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)


# ── LOAD ──────────────────────────────────────────────────────────────────────
with st.spinner("Memuat data…"):
    df = load_data(DATA_PATH)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📖 Kartografi Sampul")
    st.markdown("<small>Analisis komputasional sampul buku sastra Indonesia 2000–2025</small>",
                unsafe_allow_html=True)
    st.markdown("---")
    HAL = st.radio("Navigasi", [
        "Beranda","Warna","Tipografi","Ilustrasi","Genre","Illustrator","Jelajah Buku"
    ], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Filter Tahun**")
    yr_range = st.slider("Tahun", 2000, 2025, (2000, 2025), label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<small>Metode: K-Means HSV · CLIP zero-shot · YOLOv8n · DETR ResNet-50</small>",
                unsafe_allow_html=True)

DF = df[(df["YEAR"] >= yr_range[0]) & (df["YEAR"] <= yr_range[1])].copy()
_gc = genre_counts(DF, normalize=True)
_n_unik = len([g for g in _gc if g not in GENRE_EXCLUDE])
DF_tf = DF[DF["typeface_kategori"].isin(TF_ANALISIS)].copy()


# ══════════════════════════════════════════════════════════════════════════════
# BERANDA
# ══════════════════════════════════════════════════════════════════════════════
if HAL == "Beranda":
    st.markdown("# Kartografi Sampul Sastra Indonesia")
    st.markdown(
        f"Pemetaan komputasional terhadap **{len(DF):,} sampul buku** fiksi dan puisi Indonesia "
        f"yang terbit periode 2000–2025, dianalisis melalui tiga aspek visual: warna, tipografi, dan gaya ilustrasi."
    )
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    n_tf = len(DF_tf)
    n_gi = int(DF["gaya_ilustrasi"].notna().sum())

    c1,c2,c3,c4 = st.columns(4)
    for col,(lbl,val,sub,clr) in zip([c1,c2,c3,c4],[
        ("Total Buku",  len(DF), "teranalisis",    "#1E88E5"),
        ("Tipografi",  n_tf,    "terklasifikasi", "#8E24AA"),
        ("Ilustrasi",  n_gi,    "terklasifikasi", "#E53935"),
        ("Genre Unik", _n_unik, "genre ditemukan","#00ACC1"),
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
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Tren Terbit per Tahun**")
        yr = DF[DF["YEAR"]>0].groupby("YEAR").size().reset_index(name="n")
        fig_yr = px.bar(yr, x="YEAR", y="n", color_discrete_sequence=["#1E88E5"])
        fig_yr.update_layout(**pb(280), xaxis_title="", yaxis_title="", showlegend=False)
        fig_yr.update_traces(marker_line_width=0)
        st.plotly_chart(fig_yr, use_container_width=True)

    with col_b:
        st.markdown("**Distribusi Typeface**")
        tc_b = DF_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts()
        fig_tc = px.bar(x=tc_b.values, y=tc_b.index, orientation="h",
                        color=tc_b.index,
                        color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
                        text=tc_b.values)
        fig_tc.update_layout(**pb(280), showlegend=False, xaxis_title="", yaxis_title="",
                             yaxis=dict(categoryorder="total ascending"))
        fig_tc.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig_tc, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("**Komposisi Warna Keseluruhan**")
        wc_b = compute_warna_distribusi(DF)
        names_ord = [w for w in WARNA_ORDER if wc_b.get(w,0) > 0]
        fig_wc = px.pie(values=[wc_b[w] for w in names_ord],
                        names=[w.replace("_"," ") for w in names_ord], hole=0.4,
                        color=[w.replace("_"," ") for w in names_ord],
                        color_discrete_map={w.replace("_"," "): WARNA_HEX[w] for w in WARNA_ORDER})
        fig_wc.update_layout(**pb(260))
        fig_wc.update_traces(textinfo="percent+label", textfont_size=10)
        st.plotly_chart(fig_wc, use_container_width=True)

    with col_d:
        st.markdown("**Gaya Ilustrasi**")
        gc2 = DF["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        fig_gi = px.bar(x=gc2.values, y=gc2.index, orientation="h",
                        color=gc2.index,
                        color_discrete_map={GAYA_ID[k]: GAYA_CLR[k] for k in GAYA_ID})
        fig_gi.update_layout(**pb(260), showlegend=False, xaxis_title="", yaxis_title="",
                             yaxis=dict(categoryorder="total ascending"))
        fig_gi.update_traces(marker_line_width=0)
        st.plotly_chart(fig_gi, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Top Genre**")
    gc_b = [(g,n) for g,n in _gc.most_common() if g not in GENRE_EXCLUDE and n >= 5]
    n_gr = st.slider("Top N genre", 10, min(len(gc_b),40), 20, 5, key="beranda_gn")
    df_gb = pd.DataFrame(gc_b[:n_gr], columns=["Genre","Jumlah"])
    fig_gb = px.bar(df_gb, x="Jumlah", y="Genre", orientation="h",
                    color_discrete_sequence=["#1E88E5"], text="Jumlah")
    fig_gb.update_layout(**pb(max(300,n_gr*26)), showlegend=False, xaxis_title="", yaxis_title="",
                         yaxis=dict(categoryorder="total ascending"))
    fig_gb.update_traces(textposition="outside", marker_line_width=0)
    st.plotly_chart(fig_gb, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# WARNA
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Warna":
    st.markdown("## Analisis Warna")

    with st.expander("Cara kerja analisis warna", expanded=False):
        st.markdown(
            "**K-Means Clustering (k=5) pada ruang warna HSV**\n\n"
            "Sampul → 150×150px → BGR→HSV → K-Means k=5 → label warna dari rentang Hue. "
            "Re-klasifikasi otomatis dijalankan saat load data. **Akurasi ~87%** (200 sampel)."
        )

    wc_full = compute_warna_distribusi(DF)

    ca, cb = st.columns([1, 2])
    with ca:
        st.markdown("**Distribusi Warna Keseluruhan**")
        names_ord = [w for w in WARNA_ORDER if wc_full.get(w,0) > 0]
        fig = px.pie(values=[wc_full[w] for w in names_ord],
                     names=[w.replace("_"," ") for w in names_ord], hole=0.42,
                     color=[w.replace("_"," ") for w in names_ord],
                     color_discrete_map={w.replace("_"," "): WARNA_HEX[w] for w in WARNA_ORDER})
        fig.update_layout(**pb(300))
        fig.update_traces(textinfo="percent", textfont_size=10)
        st.plotly_chart(fig, use_container_width=True)

    with cb:
        st.markdown("**Tren Warna per Tahun**")
        rows_trend = []
        for yr,grp in DF[DF["YEAR"]>0].groupby("YEAR"):
            wc_yr = compute_warna_distribusi(grp)
            nb = len(grp)
            for w in WARNA_ORDER:
                rows_trend.append({"YEAR":yr,"warna":w.replace("_"," "),"bobot":wc_yr.get(w,0)*nb})
        trnd = pd.DataFrame(rows_trend)
        fig2 = px.bar(trnd, x="YEAR", y="bobot", color="warna",
                      color_discrete_map={w.replace("_"," "): WARNA_HEX[w] for w in WARNA_ORDER},
                      barmode="stack")
        fig2.update_layout(**pb(360), xaxis_title="", yaxis_title="Bobot",
                           showlegend=True, legend=dict(orientation="h", y=-.15, font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Peta Panas Warna × Genre**")
    hn_w = st.slider("Jumlah genre", 6, 20, 16, 2, key="hn_warna")
    st.plotly_chart(heatmap_warna_genre(DF, hn_w), use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Kecerahan vs Saturasi per Warna**")
    df_sc = DF.dropna(subset=["brightness_mean","saturation_mean","warna_kategori"]).copy()
    fig_sc = px.scatter(
        df_sc, x="brightness_mean", y="saturation_mean",
        color=df_sc["warna_kategori"].str.replace("_"," "),
        color_discrete_map={w.replace("_"," "): WARNA_HEX[w] for w in WARNA_ORDER},
        opacity=.35, custom_data=["TITLE","AUTHOR","YEAR"],
    )
    fig_sc.update_traces(marker=dict(size=4),
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} · %{customdata[2]}<extra></extra>")
    fig_sc.update_layout(**pb(300), showlegend=True,
        legend=dict(orientation="h", y=-.18, font=dict(size=10)),
        xaxis_title="Kecerahan (V)", yaxis_title="Saturasi (S)")
    st.plotly_chart(fig_sc, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Filter Warna Kombinasi**")
    warna_combo = st.multiselect(
        "Pilih 1–3 warna", options=list(WARNA_HEX.keys()), default=[],
        format_func=lambda w: w.replace("_"," ").capitalize(), key="warna_combo"
    )
    if warna_combo:
        def has_all_colors(row, colors):
            row_w = set()
            for i in range(1,6):
                w = str(row.get(f"warna_{i}","") or "").strip().lower()
                if w and w not in ("nan",""): row_w.add(w)
            return all(c in row_w for c in colors)
        mask_c = DF.apply(lambda r: has_all_colors(r, warna_combo), axis=1)
        df_combo = DF[mask_c & DF["image_ok"]].copy()
        st.markdown(f"**{len(df_combo):,} buku** dengan kombinasi warna terpilih.")
        if not df_combo.empty:
            grid(df_combo.head(st.slider("Tampilkan", 4,32,8,4, key="n_warna_combo")))

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Cari Buku berdasarkan Warna**")
    wc1,wc2,wc3 = st.columns([2,2,1])
    with wc1: q_w = st.text_input("Judul / penulis", key="w_q")
    with wc2: w_sel = st.selectbox("Filter warna", ["Semua"]+list(WARNA_HEX.keys()),
                                   format_func=lambda w: "Semua" if w=="Semua" else w.replace("_"," ").capitalize(),
                                   key="w_sel")
    with wc3: n_w = st.slider("Tampilkan", 4,32,8,4, key="w_n")
    dw = DF[DF["image_ok"]].copy()
    if q_w:
        ql = q_w.lower()
        dw = dw[dw["TITLE"].str.lower().str.contains(ql,na=False)|dw["AUTHOR"].str.lower().str.contains(ql,na=False)]
    if w_sel != "Semua": dw = dw[dw["warna_kategori"] == w_sel]
    if not dw.empty: grid(dw.head(n_w))


# ══════════════════════════════════════════════════════════════════════════════
# TIPOGRAFI
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Tipografi":
    st.markdown("## Analisis Tipografi")
 
    # ── Catatan metodologi — prominern di atas ────────────────────────────────
    st.markdown(
        """
        <div style="background:#FFF8E1;border-left:4px solid #F9A825;border-radius:0 8px 8px 0;
        padding:10px 16px;margin-bottom:.8rem;">
        <div style="font-weight:600;font-size:.82rem;color:#795548;margin-bottom:4px;">
            Catatan Metodologi
        </div>
        <div style="font-size:.78rem;color:#5D4037;line-height:1.6;">
        Analisis tipografi di sini bekerja pada dua lapisan dengan reliabilitas berbeda.<br>
        <b>Lapisan 1 — Klasifikasi visual</b> (5.069 buku): model CLIP menganalisis fitur piksel
        huruf dan menghasilkan kategori <i>typeface</i>. Karena tidak semua teks pada sampul adalah
        judul/nama penulis, klasifikasi ini memiliki noise yang cukup tinggi dan sebaiknya
        dibaca sebagai <i>estimasi</i>.<br>
        <b>Lapisan 2 — Identifikasi font konkret</b> (788 buku, ~15%): EasyOCR mendeteksi teks,
        lalu dicocokkan ke basis data Google Fonts. Hasilnya lebih presisi namun terbatas
        pada sampul yang teks fontnya terbaca oleh OCR. Di antara 788 ini,
        terdapat potensi false positive dari kata-kata pendek dalam judul yang kebetulan cocok
        dengan nama font (mis. "rasa", "anta", "sura") — sehingga bagian ini juga harus
        dibaca dengan kehati-hatian.
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Kategori typeface cards
    st.markdown("**Enam Kategori Typeface**")
    tf_cols = st.columns(len(TF_ANALISIS))
    for col_tf, key in zip(tf_cols, TF_ANALISIS):
        clr = TYPEFACE_CLR[key]
        font = TYPEFACE_FONT[key]
        with col_tf:
            st.markdown(
                f'<div style="border:1px solid rgba(128,128,128,.18);border-radius:8px;'
                f'padding:.55rem .45rem;text-align:center;">'
                f'<div style="font-family:{font};font-size:1.5rem;color:{clr};font-weight:700;">Aa</div>'
                f'<div style="font-size:.63rem;font-weight:600;margin:.2rem 0 .1rem">{TYPEFACE_ID[key]}</div>'
                f'<div style="font-size:.58rem;opacity:.5;text-align:left;line-height:1.35">{TYPEFACE_DESC[key]}</div></div>',
                unsafe_allow_html=True
            )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # ── Distribusi & Tren ─────────────────────────────────────────────────────
    ca, cb = st.columns(2)
    with ca:
        st.markdown("**Distribusi Typeface**")
        tc = DF_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts()
        fig = px.bar(x=tc.values, y=tc.index, orientation="h",
                     color=tc.index,
                     color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
                     text=tc.values)
        fig.update_layout(**pb(300), showlegend=False, xaxis_title="", yaxis_title="",
                          yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with cb:
        st.markdown("**Tren Typeface per Tahun**")
        dft2 = DF_tf[DF_tf["YEAR"]>0].copy()
        dft2["tf"] = dft2["typeface_kategori"].map(TYPEFACE_ID)
        tr2 = dft2.groupby(["YEAR","tf"]).size().reset_index(name="n")
        fig2 = px.bar(tr2, x="YEAR", y="n", color="tf", barmode="stack",
                      color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID})
        fig2.update_layout(**pb(300), xaxis_title="", yaxis_title="", showlegend=True,
                           legend=dict(orientation="h", y=-.22, font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Pergeseran per Dekade ─────────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Pergeseran Tipografi per Dekade**")
    st.caption("Apakah ada pergeseran dominasi typeface dari 2000 ke 2025?")
    df_shift = DF_tf[DF_tf["YEAR"]>0].copy()
    df_shift["tf_label"] = df_shift["typeface_kategori"].map(TYPEFACE_ID)
    df_shift["dekade"] = pd.cut(df_shift["YEAR"], bins=[1999,2004,2009,2014,2019,2025],
                                labels=["2000–04","2005–09","2010–14","2015–19","2020–25"])
    shift_g = df_shift.groupby(["dekade","tf_label"], observed=True).size().reset_index(name="n")
    shift_g["prop"] = shift_g.groupby("dekade", observed=True)["n"].transform(lambda x: x/x.sum())
    fig_shift = px.line(shift_g, x="dekade", y="prop", color="tf_label", markers=True,
                        color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
                        labels={"dekade":"","prop":"Proporsi","tf_label":"Typeface"})
    fig_shift.update_layout(**pb(320),
                            legend=dict(orientation="h", y=-.2, font=dict(size=10)))
    st.plotly_chart(fig_shift, use_container_width=True)

    # ── Heatmap Tipografi × Genre ─────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Peta Panas Tipografi × Genre**")
    hn_tf = st.slider("Jumlah genre", 6, 20, 12, 2, key="hn_tf")
    st.plotly_chart(heatmap_tf_genre(DF, hn_tf), use_container_width=True)

    # ── TIPOGRAFI PER GENRE (FITUR BARU) ─────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("### Tipografi per Genre — Analisis Mendalam")
    st.markdown(
        "<small>Pilih genre untuk melihat distribusi typeface, simpangan dari korpus, "
        "dan contoh sampul dengan confidence tertinggi.</small>",
        unsafe_allow_html=True
    )

    genre_opts = _top_genres(DF_tf, 30)
    tg_col1, tg_col2 = st.columns([3,1])
    with tg_col1:
        sel_genres_tf = st.multiselect(
            "Pilih genre",
            options=genre_opts,
            default=genre_opts[:6],
            key="tf_genre_sel"
        )
    with tg_col2:
        tf_mode = st.radio("Tampilan", ["Bar Bertumpuk","Heatmap"], key="tf_genre_mode")

    if sel_genres_tf:
        genre_lists_tf = expand_genres(DF_tf["GENRES"], normalize=True)

        # Hitung distribusi per genre
        tf_genre_data = {}
        for g in sel_genres_tf:
            mask = [g in gl for gl in genre_lists_tf]
            sub = DF_tf[mask]
            if sub.empty: continue
            vc = sub["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)
            tf_genre_data[g] = {TYPEFACE_ID[k]: vc.get(TYPEFACE_ID[k], 0.0) for k in TF_ANALISIS}

        if tf_genre_data:
            mat_tg = pd.DataFrame(tf_genre_data).T

            if tf_mode == "Bar Bertumpuk":
                rows_gb = []
                for genre, row_d in mat_tg.iterrows():
                    for tf_lbl, val in row_d.items():
                        kl = GENRE_KLASTER_MAP.get(genre)
                        gd = f"[{kl['id']}] {genre}" if kl else genre
                        rows_gb.append({"Genre": gd, "Typeface": tf_lbl, "Proporsi": val})
                fig_tg = px.bar(pd.DataFrame(rows_gb), x="Genre", y="Proporsi", color="Typeface",
                                barmode="stack",
                                color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID})
                fig_tg.update_layout(**pb(380), xaxis_title="", yaxis_title="Proporsi",
                                     xaxis_tickangle=-30,
                                     legend=dict(orientation="h", y=-.25, font=dict(size=9)))
                st.plotly_chart(fig_tg, use_container_width=True)
            else:
                tf_order = [TYPEFACE_ID[k] for k in TF_ANALISIS]
                y_lbl = []
                for g in mat_tg.index:
                    kl = GENRE_KLASTER_MAP.get(g)
                    y_lbl.append(f"{g}  [{kl['id']}]" if kl else g)
                text_m = (mat_tg[tf_order]*100).round(0).astype(int).astype(str)+"%"
                fig_hm = go.Figure(data=go.Heatmap(
                    z=mat_tg[tf_order].values, x=tf_order, y=y_lbl,
                    colorscale="Purples",
                    text=text_m.values, texttemplate="%{text}",
                    textfont=dict(size=10, color="#1A1A1A"),
                    showscale=True, zmin=0, zmax=1,
                ))
                fig_hm.update_layout(**pb(max(300,len(sel_genres_tf)*40),
                    margin=dict(l=180,r=20,t=32,b=90),
                    yaxis=dict(autorange="reversed"),
                    xaxis=dict(tickangle=-30)))
                st.plotly_chart(fig_hm, use_container_width=True)

            # Simpangan dari korpus
            st.markdown("**Simpangan dari Keseluruhan Korpus**")
            st.caption("Positif = genre ini lebih banyak memakai typeface tsb dibanding rata-rata.")
            tc_all = DF_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)
            rows_diff = []
            for g in sel_genres_tf:
                mask = [g in gl for gl in genre_lists_tf]
                sub = DF_tf[mask]
                if sub.empty: continue
                tc_g = sub["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)
                kl = GENRE_KLASTER_MAP.get(g)
                gd = f"[{kl['id']}] {g}" if kl else g
                for k in TF_ANALISIS:
                    lbl = TYPEFACE_ID[k]
                    rows_diff.append({"Genre":gd, "Typeface":lbl,
                                      "Delta": tc_g.get(lbl,0) - tc_all.get(lbl,0)})
            df_diff = pd.DataFrame(rows_diff)
            if not df_diff.empty:
                fig_diff = px.bar(df_diff, x="Delta", y="Genre", color="Typeface",
                                  orientation="h", barmode="group",
                                  color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID})
                fig_diff.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
                fig_diff.update_layout(**pb(max(300, len(sel_genres_tf)*55)),
                                       xaxis_title="Selisih proporsi vs korpus", yaxis_title="",
                                       legend=dict(orientation="h", y=-.2, font=dict(size=9)))
                st.plotly_chart(fig_diff, use_container_width=True)

            # Cross-tab Typeface × Gaya Ilustrasi
            st.markdown("<hr class='thin'>", unsafe_allow_html=True)
            st.markdown("**Typeface × Gaya Ilustrasi** — apakah keduanya berkorelasi?")
            df_cross = DF[DF["typeface_kategori"].isin(TF_ANALISIS) & DF["gaya_ilustrasi"].notna()].copy()

            # Filter ke genre yang dipilih
            gl_cross = expand_genres(df_cross["GENRES"], normalize=True)
            mask_cross = [any(g in gl for g in sel_genres_tf) for gl in gl_cross]
            df_cross_f = df_cross[mask_cross]

            if not df_cross_f.empty:
                ct = pd.crosstab(
                    df_cross_f["typeface_kategori"].map(TYPEFACE_ID),
                    df_cross_f["gaya_ilustrasi"].map(GAYA_ID),
                    normalize="index"
                )
                text_ct = (ct*100).round(0).astype(int).astype(str)+"%"
                fig_ct = go.Figure(data=go.Heatmap(
                    z=ct.values, x=ct.columns.tolist(), y=ct.index.tolist(),
                    colorscale="RdYlGn",
                    text=text_ct.values, texttemplate="%{text}",
                    textfont=dict(size=10, color="#1A1A1A"),
                    showscale=True, zmin=0, zmax=0.6,
                ))
                fig_ct.update_layout(**pb(300,
                    margin=dict(l=160,r=20,t=32,b=90),
                    yaxis=dict(autorange="reversed"),
                    xaxis_title="Gaya Ilustrasi", yaxis_title="Typeface"))
                st.plotly_chart(fig_ct, use_container_width=True)

            # Contoh buku per genre
            st.markdown("<hr class='thin'>", unsafe_allow_html=True)
            st.markdown("**Contoh Sampul — Confidence Tertinggi per Genre × Typeface**")
            df_ex = DF_tf[DF_tf["image_ok"]].copy()
            df_ex["typeface_skor"] = pd.to_numeric(df_ex["typeface_skor"], errors="coerce")
            gl_ex = expand_genres(df_ex["GENRES"], normalize=True)

            for g in sel_genres_tf[:4]:
                mask_ex = [g in gl for gl in gl_ex]
                sub_ex = df_ex[mask_ex]
                if sub_ex.empty: continue

                kl = GENRE_KLASTER_MAP.get(g)
                kl_c = kl["color"] if kl else "#555"
                kl_bg = kl["bg"] if kl else "#F5F5F5"
                st.markdown(
                    f'<div style="background:{kl_bg};border-left:4px solid {kl_c};'
                    f'border-radius:0 8px 8px 0;padding:6px 14px;margin:.8rem 0 .4rem;">'
                    f'<span style="font-weight:600;color:{kl_c};">{g}</span>'
                    f'<span style="font-size:.7rem;color:{kl_c};opacity:.65;margin-left:8px;">'
                    f'— {len(sub_ex):,} buku</span></div>',
                    unsafe_allow_html=True
                )
                tf_present = [k for k in TF_ANALISIS if k in sub_ex["typeface_kategori"].values]
                if not tf_present: continue
                ex_cols = st.columns(min(len(tf_present), 6))
                for col_ex, tk in zip(ex_cols, tf_present[:6]):
                    sub_tk = sub_ex[sub_ex["typeface_kategori"]==tk]
                    if sub_tk.empty: continue
                    best_tk = sub_tk.nlargest(1,"typeface_skor").iloc[0]
                    clr_tk = TYPEFACE_CLR.get(tk,"#999")
                    with col_ex:
                        cp = cover_path(best_tk.get("IMAGE_FILE"))
                        if cp: st.image(cp, use_container_width=True)
                        try: sc_tk = f"{float(best_tk.get('typeface_skor',0)):.2f}"
                        except: sc_tk = "–"
                        st.markdown(
                            f'<div style="font-size:.6rem;text-align:center;padding:.2rem 0;">'
                            f'<strong style="color:{clr_tk}">{TYPEFACE_ID.get(tk,tk)}</strong><br>'
                            f'<span style="opacity:.6">{str(best_tk.get("TITLE",""))[:20]}</span><br>'
                            f'<span style="opacity:.45">skor {sc_tk}</span></div>',
                            unsafe_allow_html=True
                        )
    else:
        st.caption("Pilih minimal satu genre di atas.")

    # ── Confidence keseluruhan ────────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Contoh Buku — Confidence Tertinggi per Typeface (Keseluruhan)**")
    df_tv = DF_tf[DF_tf["image_ok"]].copy()
    df_tv["typeface_skor"] = pd.to_numeric(df_tv["typeface_skor"], errors="coerce")
    ex_cols7 = st.columns(len(TF_ANALISIS))
    for col_ex, key in zip(ex_cols7, TF_ANALISIS):
        sub = df_tv[df_tv["typeface_kategori"]==key]
        if sub.empty: continue
        best = sub.nlargest(1,"typeface_skor").iloc[0]
        clr = TYPEFACE_CLR[key]
        with col_ex:
            cp = cover_path(best.get("IMAGE_FILE"))
            if cp: st.image(cp, use_container_width=True)
            try: sc = f"{float(best.get('typeface_skor',0)):.2f}"
            except: sc = "–"
            st.markdown(
                f'<div style="font-size:.62rem;padding:.25rem 0;">'
                f'<div style="font-weight:600;color:{clr}">{TYPEFACE_ID[key]}</div>'
                f'<div style="opacity:.6;line-height:1.3">{str(best.get("TITLE",""))[:24]}</div>'
                f'<div style="opacity:.5">skor {sc}</div></div>',
                unsafe_allow_html=True
            )

    # ── Cari buku ─────────────────────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Cari Buku berdasarkan Tipografi**")
    tfc1,tfc2,tfc3 = st.columns([2,2,1])
    with tfc1: q_tf = st.text_input("Judul / penulis", key="tf_q")
    with tfc2:
        tf_sel = st.selectbox("Filter typeface", ["Semua"]+[TYPEFACE_ID[k] for k in TF_ANALISIS], key="tf_sel")
    with tfc3: n_tf2 = st.slider("Tampilkan", 4,32,8,4, key="tf_n")
    dtf = DF_tf[DF_tf["image_ok"]].copy()
    if q_tf:
        ql2 = q_tf.lower()
        dtf = dtf[dtf["TITLE"].str.lower().str.contains(ql2,na=False)|dtf["AUTHOR"].str.lower().str.contains(ql2,na=False)]
    if tf_sel != "Semua":
        tf_rev = {v:k for k,v in TYPEFACE_ID.items()}
        dtf = dtf[dtf["typeface_kategori"]==tf_rev.get(tf_sel,tf_sel)]
    if not dtf.empty: grid(dtf.head(n_tf2), show_tf=True)


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
            "3. **CLIP ViT-B/32** — klasifikasi 6 gaya visual. **Akurasi ~72%** (200 sampel)."
        )

    gcols6 = st.columns(6)
    for gcol, key in zip(gcols6, GAYA_ID):
        clr = GAYA_CLR[key]
        with gcol:
            st.markdown(
                f'<div style="border:1px solid rgba(128,128,128,.18);border-radius:8px;'
                f'padding:.55rem .45rem;text-align:center;">'
                f'<div style="font-size:1.5rem">{GAYA_ICON[key]}</div>'
                f'<div style="font-size:.66rem;font-weight:600;margin:.2rem 0 .1rem;color:{clr}">{GAYA_ID[key]}</div>'
                f'<div style="font-size:.58rem;opacity:.55;text-align:left;line-height:1.35">{GAYA_ICON[key]} {key}</div></div>',
                unsafe_allow_html=True
            )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca:
        st.markdown("**Distribusi Gaya**")
        gc = DF["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        fig = px.bar(x=gc.values, y=gc.index, orientation="h",
                     color=gc.index,
                     color_discrete_map={GAYA_ID[k]: GAYA_CLR[k] for k in GAYA_ID},
                     text=gc.values)
        fig.update_layout(**pb(290), showlegend=False, xaxis_title="", yaxis_title="",
                          yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with cb:
        st.markdown("**Tren Gaya per Tahun**")
        dfg = DF[(DF["YEAR"]>0) & DF["gaya_ilustrasi"].notna()].copy()
        dfg["gaya"] = dfg["gaya_ilustrasi"].map(GAYA_ID)
        trg = dfg.groupby(["YEAR","gaya"]).size().reset_index(name="n")
        fig2 = px.bar(trg, x="YEAR", y="n", color="gaya", barmode="stack",
                      color_discrete_map={GAYA_ID[k]: GAYA_CLR[k] for k in GAYA_ID})
        fig2.update_layout(**pb(290), xaxis_title="", yaxis_title="", showlegend=True,
                           legend=dict(orientation="h", y=-.2, font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Peta Panas Gaya × Genre**")
    hn_gi = st.slider("Jumlah genre", 6,20,12,2, key="hn_gi")
    st.plotly_chart(heatmap_gaya_genre(DF, hn_gi), use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Figur Manusia vs Non-Manusia**")
    yh = int(DF["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
    dh = int(DF["detr_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
    tot = len(DF)
    agree = int((DF["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") &
                 DF["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")).sum())
    man_a, man_b = st.columns([2,1])
    with man_a:
        fig_man = go.Figure(data=[
            go.Bar(name="YOLOv8n", x=["Ada manusia","Tidak ada"], y=[yh,tot-yh],
                   marker_color=["#66BB6A","rgba(128,128,128,.15)"]),
            go.Bar(name="DETR", x=["Ada manusia","Tidak ada"], y=[dh,tot-dh],
                   marker_color=["#42A5F5","rgba(128,128,128,.08)"]),
        ])
        fig_man.update_layout(**pb(240), barmode="group", showlegend=True,
                              legend=dict(orientation="h",y=-.15))
        st.plotly_chart(fig_man, use_container_width=True)
    with man_b:
        st.metric("Sepakat keduanya", f"{agree:,}", f"{agree/tot*100:.1f}%")
        st.metric("Hanya YOLOv8n", f"{yh-agree:,}")
        st.metric("Hanya DETR", f"{dh-agree:,}")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Cari Buku berdasarkan Gaya Ilustrasi**")
    gic1,gic2,gic3,gic4 = st.columns([2,2,1,1])
    with gic1: q_gi = st.text_input("Judul / penulis", key="gi_q")
    with gic2: gaya_sel = st.selectbox("Filter gaya", ["Semua"]+[GAYA_ID[k] for k in GAYA_ID], key="gi_sel")
    with gic3: ada_man = st.checkbox("Ada manusia", key="gi_man")
    with gic4: n_gi2 = st.slider("Tampilkan", 4,32,8,4, key="gi_n")
    dgi = DF[DF["image_ok"]].copy()
    if q_gi:
        ql3 = q_gi.lower()
        dgi = dgi[dgi["TITLE"].str.lower().str.contains(ql3,na=False)|dgi["AUTHOR"].str.lower().str.contains(ql3,na=False)]
    if ada_man:
        dgi = dgi[dgi["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE")|
                  dgi["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")]
    if gaya_sel != "Semua":
        grev = {v:k for k,v in GAYA_ID.items()}
        dgi = dgi[dgi["gaya_ilustrasi"]==grev.get(gaya_sel,gaya_sel)]
    if not dgi.empty: grid(dgi.head(n_gi2), show_gi=True)


# ══════════════════════════════════════════════════════════════════════════════
# GENRE
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Genre":
    st.markdown("## Analisis Genre")

    with st.expander("Catatan metodologi", expanded=False):
        st.markdown(
            f"Genre dari metadata Goodreads (multi-label). **{_n_unik} genre unik** setelah normalisasi.\n\n"
            "**Normalisasi:** Cinta/Roman → Romansa · Thriller/Misteri → Thriller/Misteri · Humor → Komedi\n\n"
            "Genre *Sastra Indonesia*, *Fiksi*, *Sastra* dikecualikan dari visualisasi."
        )

    cooc_df, cooc_counts = compute_cooccurrence(DF)

    st.markdown("**Tiga Klaster Co-occurrence Genre**")
    kl_leg = st.columns(3)
    for kc, kl in zip(kl_leg, KLASTER_COOC):
        genre_str = ", ".join(kl["genres"][:5]) + "…"
        kc.markdown(
            f'<div style="background:{kl["bg"]};border-left:4px solid {kl["color"]};'
            f'border-radius:0 8px 8px 0;padding:8px 12px;">'
            f'<div style="font-weight:600;color:{kl["color"]};font-size:12px;">[{kl["id"]}] {kl["label"].split("—")[1].strip()}</div>'
            f'<div style="font-size:10px;opacity:.6;margin-top:4px;">{genre_str}</div></div>',
            unsafe_allow_html=True
        )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Tabel Co-occurrence Genre**")
    render_cooc_table(cooc_df, cooc_counts)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Peta Panas Tumpang Tindih Genre**")
    all_items = [(g,n) for g,n in _gc.most_common() if g not in GENRE_EXCLUDE and n >= 3]
    n_co = st.slider("Jumlah genre", 8, min(len(all_items),30), 16, 2, key="n_co")
    top_co = [g for g,_ in all_items[:n_co]]
    co = pd.DataFrame(0, index=top_co, columns=top_co)
    for gl in expand_genres(DF["GENRES"], normalize=True):
        rel = [g for g in gl if g in top_co]
        for i,g1 in enumerate(rel):
            for g2 in rel[i+1:]:
                co.loc[g1,g2]+=1; co.loc[g2,g1]+=1
    for g in top_co: co.loc[g,g] = _gc[g]
    y_lbl_co = []
    for g in top_co:
        kl = GENRE_KLASTER_MAP.get(g)
        y_lbl_co.append(f"{g}  [{kl['id']}]" if kl else g)
    fig_co = go.Figure(data=go.Heatmap(
        z=co.values, x=y_lbl_co, y=y_lbl_co,
        colorscale="Oranges",
        text=co.values.astype(int).astype(str),
        texttemplate="%{text}", textfont=dict(size=9,color="#1A1A1A"),
        showscale=True,
    ))
    fig_co.update_layout(**pb(max(420,n_co*28),
        margin=dict(l=150,r=20,t=32,b=150),
        xaxis=dict(tickangle=-40),
        yaxis=dict(autorange="reversed"),
    ))
    st.plotly_chart(fig_co, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Analisis per Genre**")
    top_btn = [g for g,_ in all_items[:40]]
    if "sel_genre" not in st.session_state:
        st.session_state["sel_genre"] = top_btn[0] if top_btn else None
    for cs in range(0, len(top_btn), 8):
        chunk_g = top_btn[cs:cs+8]
        btn_row = st.columns(len(chunk_g))
        for col_b, g in zip(btn_row, chunk_g):
            kl = GENRE_KLASTER_MAP.get(g)
            label = f"{g} [{kl['id']}]" if kl else g
            if col_b.button(label, key=f"gbtn_{g}", use_container_width=True):
                st.session_state["sel_genre"] = g

    sel_genre = st.session_state["sel_genre"]
    if sel_genre:
        st.markdown("<hr class='thin'>", unsafe_allow_html=True)
        genre_lists_all = expand_genres(DF["GENRES"], normalize=True)
        mask_g = [sel_genre in gl for gl in genre_lists_all]
        df_gs = DF[mask_g]
        if df_gs.empty:
            st.info(f"Tidak ada buku genre *{sel_genre}*.")
        else:
            kl = GENRE_KLASTER_MAP.get(sel_genre)
            st.markdown(f'#### Genre: **{sel_genre}** — {len(df_gs):,} buku')
            tab_w, tab_tf, tab_gi = st.tabs(["🎨 Warna","🔤 Tipografi","📷 Ilustrasi"])

            with tab_w:
                wc_g = compute_warna_distribusi(df_gs)
                wc_all = compute_warna_distribusi(DF)
                cw1,cw2 = st.columns(2)
                with cw1:
                    names_g = [w for w in WARNA_ORDER if wc_g.get(w,0)>0]
                    fig_wg = px.pie(values=[wc_g[w] for w in names_g],
                                   names=[w.replace("_"," ") for w in names_g], hole=0.42,
                                   color=[w.replace("_"," ") for w in names_g],
                                   color_discrete_map={w.replace("_"," "): WARNA_HEX[w] for w in WARNA_ORDER})
                    fig_wg.update_layout(**pb(260))
                    fig_wg.update_traces(textinfo="percent+label", textfont_size=10)
                    st.plotly_chart(fig_wg, use_container_width=True)
                with cw2:
                    diff = (wc_g-wc_all).dropna().sort_values(ascending=False)
                    diff_df = diff.reset_index(); diff_df.columns = ["warna","delta"]
                    diff_df["warna_disp"] = diff_df["warna"].str.replace("_"," ")
                    fig_d = px.bar(diff_df, x="delta", y="warna_disp", orientation="h",
                                   color="warna", color_discrete_map=WARNA_HEX)
                    fig_d.update_layout(**pb(260), showlegend=False,
                                        xaxis_title="Simpangan", yaxis_title="",
                                        yaxis=dict(categoryorder="total ascending"))
                    fig_d.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
                    st.plotly_chart(fig_d, use_container_width=True)

            with tab_tf:
                df_gs_tf = df_gs[df_gs["typeface_kategori"].isin(TF_ANALISIS)]
                if df_gs_tf.empty:
                    st.info("Belum ada data tipografi untuk genre ini.")
                else:
                    tc_g = df_gs_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts()
                    tc_all2 = DF_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts()
                    ctf1,ctf2 = st.columns(2)
                    with ctf1:
                        fig_tg = px.pie(values=tc_g.values, names=tc_g.index, hole=0.42,
                                        color=tc_g.index,
                                        color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID})
                        fig_tg.update_layout(**pb(250))
                        fig_tg.update_traces(textinfo="percent+label", textfont_size=10)
                        st.plotly_chart(fig_tg, use_container_width=True)
                    with ctf2:
                        diff_tf = (tc_g/len(df_gs_tf) - tc_all2/len(DF_tf)).dropna().sort_values(ascending=False)
                        diff_tf_df = diff_tf.reset_index(); diff_tf_df.columns = ["tipografi","delta"]
                        fig_dtf = px.bar(diff_tf_df, x="delta", y="tipografi", orientation="h",
                                         color="tipografi",
                                         color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID})
                        fig_dtf.update_layout(**pb(250), showlegend=False,
                                              xaxis_title="Simpangan", yaxis_title="",
                                              yaxis=dict(categoryorder="total ascending"))
                        fig_dtf.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
                        st.plotly_chart(fig_dtf, use_container_width=True)

            with tab_gi:
                gc_g = df_gs["gaya_ilustrasi"].map(GAYA_ID).value_counts()
                gc_all2 = DF["gaya_ilustrasi"].map(GAYA_ID).value_counts()
                cg1,cg2 = st.columns(2)
                with cg1:
                    fig_gg = px.pie(values=gc_g.values, names=gc_g.index, hole=0.42,
                                    color=gc_g.index,
                                    color_discrete_map={GAYA_ID[k]: GAYA_CLR[k] for k in GAYA_ID})
                    fig_gg.update_layout(**pb(250))
                    fig_gg.update_traces(textinfo="percent+label", textfont_size=10)
                    st.plotly_chart(fig_gg, use_container_width=True)
                with cg2:
                    diff_gi = (gc_g/len(df_gs) - gc_all2/len(DF)).dropna().sort_values(ascending=False)
                    diff_gi_df = diff_gi.reset_index(); diff_gi_df.columns = ["gaya","delta"]
                    fig_dgi = px.bar(diff_gi_df, x="delta", y="gaya", orientation="h",
                                     color="gaya",
                                     color_discrete_map={GAYA_ID[k]: GAYA_CLR[k] for k in GAYA_ID})
                    fig_dgi.update_layout(**pb(250), showlegend=False,
                                          xaxis_title="Simpangan", yaxis_title="",
                                          yaxis=dict(categoryorder="total ascending"))
                    fig_dgi.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
                    st.plotly_chart(fig_dgi, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ILLUSTRATOR
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Illustrator":
    st.markdown("## Illustrator Sampul")
    has_ill = DF["ILLUSTRATOR"].ne("")
    n_ill = has_ill.sum()
    st.markdown(f"**{n_ill} buku** dari {len(DF):,} yang menyebutkan nama illustrator.")
    df_ill = DF[has_ill].copy()
    q_ill = st.text_input("Cari illustrator atau judul", key="ill_q")
    if q_ill:
        ql = q_ill.lower()
        df_ill = df_ill[df_ill["ILLUSTRATOR"].str.lower().str.contains(ql,na=False)|
                        df_ill["TITLE"].str.lower().str.contains(ql,na=False)]

    ill_sum = (
        df_ill.groupby("ILLUSTRATOR").agg(
            Buku=("TITLE","count"),
            Judul=("TITLE", lambda x: " · ".join(x.values.tolist()[:3])),
            Tahun=("YEAR", lambda x: ", ".join(sorted({str(int(v)) for v in x if v>0})))
        ).reset_index().sort_values("Buku", ascending=False)
        .rename(columns={"ILLUSTRATOR":"Illustrator"})
    )
    st.dataframe(ill_sum, use_container_width=True, hide_index=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Simpangan Gaya: Dengan vs Tanpa Illustrator**")
    df_with = DF[has_ill].copy()
    df_wout = DF[~has_ill].copy()
    n_no_ill = (~has_ill).sum()

    gc_w = df_with["gaya_ilustrasi"].map(GAYA_ID).value_counts()
    gc_o = df_wout["gaya_ilustrasi"].map(GAYA_ID).value_counts()
    diff_g = (gc_w/n_ill - gc_o/n_no_ill).dropna().sort_values(ascending=False)
    diff_g_df = diff_g.reset_index(); diff_g_df.columns = ["gaya","delta"]
    fig_dg = px.bar(diff_g_df, x="delta", y="gaya", orientation="h",
                    color="gaya",
                    color_discrete_map={GAYA_ID[k]: GAYA_CLR[k] for k in GAYA_ID})
    fig_dg.update_layout(**pb(240), showlegend=False,
                         xaxis_title="Selisih proporsi", yaxis_title="",
                         yaxis=dict(categoryorder="total ascending"))
    fig_dg.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
    st.plotly_chart(fig_dg, use_container_width=True)
    st.caption("Nilai positif = gaya lebih sering pada buku dengan illustrator.")


# ══════════════════════════════════════════════════════════════════════════════
# JELAJAH BUKU
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Jelajah Buku":
    st.markdown("## Jelajah Buku")
    st.markdown("Temukan buku dari kombinasi kriteria visual dan metadata.")
    top25_j = [g for g,_ in _gc.most_common() if g not in GENRE_EXCLUDE][:25]

    with st.form("form_jelajah"):
        r1 = st.columns(4)
        q_j     = r1[0].text_input("Judul / penulis")
        warna_j = r1[1].selectbox("Warna dominan", ["Semua"]+sorted(DF["warna_kategori"].dropna().unique()),
                                  format_func=lambda w: "Semua" if w=="Semua" else w.replace("_"," ").capitalize())
        tf_j    = r1[2].selectbox("Tipografi", ["Semua"]+[TYPEFACE_ID[k] for k in TF_ANALISIS])
        gaya_j  = r1[3].selectbox("Gaya ilustrasi", ["Semua"]+[GAYA_ID[k] for k in GAYA_ID])
        r2 = st.columns(4)
        genre_j = r2[0].selectbox("Genre", ["Semua"]+top25_j)
        rak_j   = r2[1].selectbox("Rak", ["Semua","Fiksi","Puisi"])
        ill_j   = r2[2].selectbox("Illustrator", ["Semua","Dengan illustrator"])
        man_j   = r2[3].checkbox("Ada figur manusia")
        r3 = st.columns([3,1])
        n_j = r3[1].slider("Tampilkan", 8,48,16,8)
        st.form_submit_button("🔍 Cari")

    dj = DF[DF["image_ok"]].copy()
    if q_j:
        ql = q_j.lower()
        dj = dj[dj["TITLE"].str.lower().str.contains(ql,na=False)|dj["AUTHOR"].str.lower().str.contains(ql,na=False)]
    if warna_j != "Semua": dj = dj[dj["warna_kategori"]==warna_j]
    if tf_j != "Semua":
        tf_rev3 = {v:k for k,v in TYPEFACE_ID.items()}
        dj = dj[dj["typeface_kategori"]==tf_rev3.get(tf_j,tf_j)]
    if gaya_j != "Semua":
        grev3 = {v:k for k,v in GAYA_ID.items()}
        dj = dj[dj["gaya_ilustrasi"]==grev3.get(gaya_j,gaya_j)]
    if genre_j != "Semua":
        gl_j = expand_genres(dj["GENRES"], normalize=True)
        dj = dj[[genre_j in gl for gl in gl_j]]
    if rak_j == "Fiksi":   dj = dj[dj["SHELF"]=="fiksi"]
    elif rak_j == "Puisi": dj = dj[dj["SHELF"]=="puisi-asli"]
    if ill_j == "Dengan illustrator": dj = dj[dj["ILLUSTRATOR"].ne("")]
    if man_j:
        dj = dj[dj["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE")|
                dj["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")]

    st.markdown(f"**{len(dj):,} buku ditemukan**")
    if not dj.empty:
        grid(dj.head(n_j), show_tf=True, show_gi=True)
