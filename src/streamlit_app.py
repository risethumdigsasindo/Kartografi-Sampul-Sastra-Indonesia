"""
Kartografi Sampul Sastra Indonesia (2000–2025)
Versi terpadu v8 — warna · tipografi · ilustrasi (10 corak) · genre · popularitas
"""

import os
from collections import Counter
from itertools import combinations

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Import tipografi dari modul terpisah
try:
    from tipografi_4cat import (
        TYPEFACE_ID, TYPEFACE_CLR, TF_ANALISIS,
        render_tab as render_tipografi_tab,
    )
    _TIPOGRAFI_MODUL = True
except ImportError:
    _TIPOGRAFI_MODUL = False


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
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
.stat-card{border:1px solid rgba(128,128,128,.15);border-radius:12px;padding:1.1rem 1.2rem 1rem;
           text-align:center;transition:transform .15s,box-shadow .15s;}
.stat-card:hover{transform:translateY(-3px);box-shadow:0 6px 18px rgba(0,0,0,.10);}
.stat-card .lbl{font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;opacity:.55;}
.stat-card .val{font-family:'Lora',serif;font-size:2.1rem;font-weight:600;line-height:1.1;}
.stat-card .sub{font-size:.72rem;opacity:.5;margin-top:.15rem;}
.bk-info{padding:.55rem .7rem .75rem;}
.bk-title{font-family:'Lora',serif;font-size:.82rem;font-weight:600;line-height:1.3;}
.bk-meta{font-size:.71rem;opacity:.6;margin:.15rem 0 .3rem;}
.badge{display:inline-block;font-size:.64rem;font-weight:500;padding:1px 7px;border-radius:20px;
       border:1px solid rgba(128,128,128,.2);margin:2px 2px 0 0;opacity:.82;}
.pal-row{display:flex;height:10px;border-radius:4px;overflow:hidden;margin:.35rem 0 .4rem;gap:1px;}
hr.thin{border:none;border-top:1px solid rgba(128,128,128,.12);margin:1.3rem 0;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# KONSTANTA WARNA
# ─────────────────────────────────────────────────────────────────────────────
WARNA_HEX = {
    "putih":   "#F5F5F0", "hitam": "#1A1A1A", "abu":    "#8E8E93",
    "merah":   "#E53935", "pink":  "#F06292", "oranye": "#FB8C00",
    "cokelat": "#795548", "kuning":"#FDD835", "hijau":  "#43A047",
    "biru":    "#1E88E5", "ungu":  "#8E24AA",
}
WARNA_ORDER = ["putih","oranye","cokelat","biru","merah","pink","hitam","kuning","ungu","hijau","abu"]


# ─────────────────────────────────────────────────────────────────────────────
# KONSTANTA TIPOGRAFI (fallback jika modul tidak tersedia)
# ─────────────────────────────────────────────────────────────────────────────
if not _TIPOGRAFI_MODUL:
    TYPEFACE_ID = {
        "humanist_serif":     "Humanist Serif",
        "transitional_serif": "Transitional Serif",
        "modern_serif":       "Modern Serif",
        "slab_serif":         "Slab Serif",
        "sans_serif":         "Sans-serif",
        "script":             "Kaligrafi/Script",
        "display":            "Display/Dekoratif",
        "unknown":            "Tidak Terklasifikasi",
    }
    TYPEFACE_CLR = {
        "humanist_serif":      "#5C6BC0",
        "transitional_serif":  "#7E57C2",
        "modern_serif":        "#AB47BC",
        "slab_serif":          "#EC407A",
        "sans_serif":          "#42A5F5",
        "script":              "#26A69A",
        "display":             "#FFA726",
        "unknown":             "#BDBDBD",
    }
    TF_ANALISIS = [k for k in TYPEFACE_ID if k != "unknown"]


# ─────────────────────────────────────────────────────────────────────────────
# KONSTANTA CORAK ILUSTRASI (10 kategori CLIP)
# ─────────────────────────────────────────────────────────────────────────────
CORAK_ID = {
    "realisme":        "Realisme",
    "dekoratif":       "Dekoratif",
    "kartunal":        "Kartunal",
    "ekspresionisme":  "Ekspresionisme",
    "surealis_absurd": "Surealis/Absurd",
    "pop_art":         "Pop Art",
    "kubisme":         "Kubisme",
    "abstrak":         "Abstrak",
    "minimalis":       "Minimalis",
    "fotografi_kolase":"Fotografi/Kolase",
}
CORAK_CLR = {
    "realisme":        "#1E88E5",
    "dekoratif":       "#43A047",
    "kartunal":        "#FB8C00",
    "ekspresionisme":  "#E53935",
    "surealis_absurd": "#8E24AA",
    "pop_art":         "#FDD835",
    "kubisme":         "#6D4C41",
    "abstrak":         "#00ACC1",
    "minimalis":       "#757575",
    "fotografi_kolase":"#3949AB",
}
CORAK_ICON = {
    "realisme":        "🧍",
    "dekoratif":       "🌺",
    "kartunal":        "🧸",
    "ekspresionisme":  "🔥",
    "surealis_absurd": "🌀",
    "pop_art":         "💥",
    "kubisme":         "🔶",
    "abstrak":         "🔷",
    "minimalis":       "⚪",
    "fotografi_kolase":"📷",
}
CORAK_DESC = {
    "realisme":        "Proporsi akurat, detail tinggi, pencahayaan natural.",
    "dekoratif":       "Visual datar, ornamen, pola repetitif, warna solid.",
    "kartunal":        "Bentuk disederhanakan/dilebih-lebihkan, outline jelas.",
    "ekspresionisme":  "Bentuk & warna terdistorsi, suasana dramatis.",
    "surealis_absurd": "Kombinasi objek tidak logis, mimpi, absurd.",
    "pop_art":         "Warna cerah, halftone, bahasa visual komik/iklan.",
    "kubisme":         "Objek terpecah jadi bidang geometris, multi-perspektif.",
    "abstrak":         "Tanpa objek nyata, fokus warna/garis/komposisi.",
    "minimalis":       "Elemen sedikit, ruang kosong dominan, komposisi bersih.",
    "fotografi_kolase":"Foto, montase, manipulasi digital, elemen fotografis.",
}
CORAK_ORDER = [
    "kartunal","minimalis","ekspresionisme","fotografi_kolase","abstrak",
    "dekoratif","realisme","surealis_absurd","pop_art","kubisme",
]
CORAK_ALIAS = {
    "realisme":"realisme","realism":"realisme","realistis":"realisme",
    "dekoratif":"dekoratif","decorative":"dekoratif",
    "kartunal":"kartunal","kartun":"kartunal","cartoon":"kartunal","cartoonal":"kartunal",
    "ekspresionisme":"ekspresionisme","expressionism":"ekspresionisme",
    "surealis_absurd":"surealis_absurd","surealis / absurd":"surealis_absurd",
    "surealis/absurd":"surealis_absurd","surealis":"surealis_absurd","surreal":"surealis_absurd",
    "surrealism":"surealis_absurd","absurd":"surealis_absurd","absurdisme":"surealis_absurd",
    "pop_art":"pop_art","pop art":"pop_art",
    "kubisme":"kubisme","cubism":"kubisme",
    "abstrak":"abstrak","abstract":"abstrak",
    "minimalis":"minimalis","minimalism":"minimalis",
    "fotografi_kolase":"fotografi_kolase","fotografi / digital collage":"fotografi_kolase",
    "fotografi":"fotografi_kolase","photography":"fotografi_kolase",
    "digital collage":"fotografi_kolase","collage":"fotografi_kolase",
}


# ─────────────────────────────────────────────────────────────────────────────
# KONSTANTA GENRE
# ─────────────────────────────────────────────────────────────────────────────
GENRE_EXCLUDE = {"Sastra Indonesia","Sastra","Fiksi","Nonfiction","Non-fiction",
                 "Nonfiksi","Non Fiksi","Non-fiksi",""}
GENRE_NORM = {
    "Cinta":"Romansa","Roman":"Romansa","Romansa Kontemporer":"Romansa",
    "Romansa kontemporer":"Romansa","Kontemporer":"Romansa","Romansatic":"Romansa",
    "Young Adult Romansace":"Romansa","Roman Kontemporer":"Romansa",
    "Thriller":"Thriller/Misteri","Misteri":"Thriller/Misteri",
    "Misteri Thriller":"Thriller/Misteri","Thriller Suspense":"Thriller/Misteri",
    "Psychological Thriller":"Thriller/Misteri","Suspense":"Thriller/Misteri",
    "Detective":"Thriller/Misteri","Kriminal":"Thriller/Misteri",
    "Supranatural":"Horor","Humor":"Komedi","New Adult":"Remaja",
    "Collections":"Antologi","Middle Grade":"Fantasi",
    "Fiksi Ilmiah":"Fiksi Sains","Distopia":"Fiksi Sains",
    "Sejarah":"Fiksi Sejarah","Historical Fiction":"Fiksi Sejarah",
    "Historical":"Fiksi Sejarah",
}
KLASTER = [
    {"id":"K1","label":"Novel & Bentuk","color":"#2E4057","bg":"#EEF2F7",
     "genres":["Novel","Cerita Pendek","Antologi","Puisi"],
     "pairs":[("Drama","Novel"),("Novel","Remaja"),("Antologi","Cerita Pendek"),
              ("Novel","Romansa"),("Fiksi Sejarah","Novel")]},
    {"id":"K2","label":"Romansa & Relasi","color":"#993556","bg":"#FBF0F3",
     "genres":["Romansa","Chick Lit","Persahabatan","Remaja","Dewasa","Keluarga","Drama","Slice of Life"],
     "pairs":[("Chick Lit","Romansa"),("Persahabatan","Romansa"),("Remaja","Romansa"),
              ("Dewasa","Romansa"),("Keluarga","Romansa"),("Drama","Romansa")]},
    {"id":"K3","label":"Eskapisme & Aksi","color":"#1D9E75","bg":"#EEF8F4",
     "genres":["Fantasi","Fiksi Sejarah","Petualangan","Anak-anak",
               "Fiksi Sains","Thriller/Misteri","Horor","Komedi"],
     "pairs":[("Fantasi","Fiksi Sains"),("Fantasi","Petualangan"),("Anak-anak","Fantasi"),
              ("Horor","Thriller/Misteri"),("Fiksi Sejarah","Novel"),("Komedi","Horor")]},
]
GENRE_KLASTER_MAP = {}
for _kl in KLASTER:
    for _g in _kl["genres"]:
        if _g not in GENRE_KLASTER_MAP:
            GENRE_KLASTER_MAP[_g] = _kl
_KLASTER_GENRE_ORDER = [g for kl in KLASTER for g in kl["genres"]]
SHELF_LABEL = {"fiksi":"Fiksi","puisi-asli":"Puisi"}

YOLO_ID = {
    "person":"orang","bicycle":"sepeda","car":"mobil","motorcycle":"motor",
    "airplane":"pesawat","bus":"bus","train":"kereta","truck":"truk","boat":"perahu",
    "bird":"burung","cat":"kucing","dog":"anjing","horse":"kuda","sheep":"domba",
    "cow":"sapi","elephant":"gajah","bear":"beruang","zebra":"zebra","giraffe":"jerapah",
    "backpack":"ransel","umbrella":"payung","handbag":"tas tangan","tie":"dasi",
    "suitcase":"koper","sports ball":"bola olahraga","kite":"layang-layang",
    "bottle":"botol","wine glass":"gelas anggur","cup":"cangkir","fork":"garpu",
    "knife":"pisau","spoon":"sendok","bowl":"mangkuk","banana":"pisang","apple":"apel",
    "sandwich":"sandwich","orange":"jeruk","broccoli":"brokoli","carrot":"wortel",
    "pizza":"pizza","donut":"donat","cake":"kue","chair":"kursi","couch":"sofa",
    "potted plant":"tanaman pot","bed":"tempat tidur","dining table":"meja makan",
    "tv":"televisi","laptop":"laptop","cell phone":"ponsel","book":"buku",
    "clock":"jam","vase":"vas","scissors":"gunting","teddy bear":"boneka beruang",
}

_base     = os.path.dirname(__file__)
DATA_PATH = os.path.join(_base, "data.csv")
COVER_DIR = os.path.join(_base, "..", "covers")


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS UMUM
# ─────────────────────────────────────────────────────────────────────────────
def _pb(height=320, **kw):
    base = dict(height=height, margin=dict(l=8,r=8,t=34,b=8),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(size=11, color="#1A1A1A"))
    base.update(kw)
    return base

def _hr():
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

def _klasifikasi_hsv(h, s, v):
    try: h,s,v = float(h or 0), float(s or 0), float(v or 0)
    except: return None
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

def compute_warna_distribusi(d):
    acc = {w: 0.0 for w in WARNA_ORDER}
    for _, row in d.iterrows():
        for i in range(1, 6):
            pct = row.get(f"warna_pct_{i}", 0)
            try: pct = float(pct or 0)
            except: pct = 0.0
            if pct <= 0: continue
            k = _klasifikasi_hsv(row.get(f"warna_h_{i}",0),
                                 row.get(f"warna_s_{i}",0),
                                 row.get(f"warna_v_{i}",0))
            if k and k in acc: acc[k] += pct
    total = sum(acc.values())
    if total > 0: acc = {k: v/total for k,v in acc.items()}
    return pd.Series(acc)

def _norm_genre(g):
    return GENRE_NORM.get(g.strip(), g.strip())

def expand_genres(series, normalize=True):
    out = []
    for v in series:
        if pd.isna(v) or str(v).strip() == "":
            out.append([]); continue
        raw = [g.strip() for g in str(v).split(",") if g.strip()]
        if normalize:
            seen, normed = set(), []
            for g in raw:
                g2 = _norm_genre(g)
                if g2 not in seen: normed.append(g2); seen.add(g2)
            out.append(normed)
        else:
            out.append(raw)
    return out

def genre_counts(d, normalize=True):
    c = Counter()
    for gl in expand_genres(d["GENRES"], normalize=normalize):
        c.update(gl)
    return c

def _top_genres(d, n=16, min_count=3):
    gc = genre_counts(d, normalize=True)
    eligible = {g for g,c in gc.items() if g not in GENRE_EXCLUDE and c >= min_count}
    ordered = [g for g in _KLASTER_GENRE_ORDER if g in eligible]
    rest    = [g for g,_ in gc.most_common() if g in eligible and g not in ordered]
    return (ordered + rest)[:n]

def _klaster_shapes(genres):
    shapes, prev = [], None
    for i, g in enumerate(genres):
        kl = GENRE_KLASTER_MAP.get(g, {}).get("id")
        if kl != prev and i > 0:
            shapes.append(dict(type="line",xref="paper",yref="y",x0=0,x1=1,
                               y0=i-.5,y1=i-.5,
                               line=dict(color="rgba(0,0,0,.3)",width=1.5,dash="dot")))
        prev = kl
    return shapes

def _y_labels(genres):
    return [f"{g}  [{GENRE_KLASTER_MAP[g]['id']}]" if g in GENRE_KLASTER_MAP else g
            for g in genres]

def _terjemahkan_objek(label):
    return YOLO_ID.get(str(label).strip().lower(), str(label).strip().lower())

def _parse_objects_detected(series):
    ctr = Counter()
    for val in series:
        if pd.isna(val) or str(val).strip() in ("","nan","[]"): continue
        items = [x.strip() for x in str(val).replace(";",",").split(",") if x.strip()]
        for item in items:
            raw = item.strip().strip("[]{}\"'")
            if "|" in raw:
                raw_label = raw.split("|",1)[0].strip()
            elif ":" in raw:
                parts = raw.split(":",1)
                raw_label = parts[0].strip()
            else:
                raw_label = raw.strip()
            if raw_label:
                ctr[_terjemahkan_objek(raw_label)] += 1
    return ctr

def cover_path(img):
    if not img or str(img) in ("","nan","None"): return None
    p = os.path.join(COVER_DIR, str(img))
    return p if os.path.exists(p) else None

def _nama_warna(hex_str):
    try:
        h = hex_str.lstrip("#")
        r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    except: return hex_str
    best, best_d = "lainnya", float("inf")
    for nama,hx in WARNA_HEX.items():
        try:
            hh = hx.lstrip("#")
            rr,gg,bb = int(hh[0:2],16), int(hh[2:4],16), int(hh[4:6],16)
            dist = (r-rr)**2+(g-gg)**2+(b-bb)**2
            if dist < best_d: best,best_d = nama,dist
        except: pass
    return best

def palette_html(row, n=5):
    parts, total = [], 0.0
    for i in range(1, n+1):
        hx  = str(row.get(f"warna_hex_{i}","") or "").strip()
        pct = row.get(f"warna_pct_{i}", 0)
        try: pct = float(pct)
        except: pct = 0.0
        if not hx or hx in ("nan",""): continue
        if not hx.startswith("#"): hx = "#"+hx
        parts.append((hx, pct, _nama_warna(hx))); total += pct
    if not parts: return ""
    scale = 100.0/total if total > 0 else 1.0
    sw = "".join(
        f'<div style="flex-shrink:0;background:{hx};width:{pct*scale:.1f}%;" title="{nm} ({pct:.1f}%)"></div>'
        for hx,pct,nm in parts
    )
    return f'<div class="pal-row">{sw}</div>'

def prob_bars_corak_html(row):
    vals = []
    for k in CORAK_ID:
        col = f"corak_skor_{k}"
        if col in row.index:
            try: vals.append((k, float(row.get(col, 0) or 0)))
            except: pass
    if not vals: return ""
    html = ""
    for k, val in sorted(vals, key=lambda x: -x[1])[:5]:
        pct = val * 100
        label = CORAK_ID.get(k, k)
        clr   = CORAK_CLR.get(k, "#999")
        html += (
            f'<div style="margin:.1rem 0;">'
            f'<div style="font-size:.6rem;display:flex;justify-content:space-between;margin-bottom:1px;opacity:.72;">'
            f'<span>{label}</span><span>{pct:.1f}%</span></div>'
            f'<div style="background:rgba(128,128,128,.12);border-radius:3px;height:5px;">'
            f'<div style="width:{pct:.1f}%;height:5px;border-radius:3px;background:{clr};"></div>'
            f'</div></div>'
        )
    return html


# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data(path):
    d = pd.read_csv(path, sep=",", encoding="utf-8-sig",
                    on_bad_lines="skip", engine="python")
    d = d[d["SHELF"].isin(["fiksi","puisi-asli"])].copy()

    for c in ["YEAR","RATING","TOTAL_RATING","TOTAL_REVIEW",
              "brightness_mean","saturation_mean","gaya_skor",
              "teks_coverage","n_region_teks","judul_match_score",
              "yolo_n_objek","detr_objek_n","ocr_confidence","clip_margin"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")

    for i in range(1, 6):
        for s in ["pct","h","s","v"]:
            c = f"warna_{s}_{i}"
            if c in d.columns:
                d[c] = pd.to_numeric(d[c], errors="coerce")

    for c in d.columns:
        if c.startswith("gaya_prob_") or c.startswith("corak_skor_"):
            d[c] = pd.to_numeric(d[c], errors="coerce")

    if "corak_konfiden" in d.columns:
        d["corak_konfiden"] = pd.to_numeric(d["corak_konfiden"], errors="coerce").fillna(0.0)

    if "corak_ilustrasi" in d.columns:
        raw = (d["corak_ilustrasi"].fillna("").astype(str)
               .str.strip().str.lower()
               .str.replace("-","_",regex=False)
               .str.replace("  "," ",regex=False))
        d["corak_ilustrasi"] = raw.map(lambda x: CORAK_ALIAS.get(x, x))
        invalid = ["","nan","none","null","gagal_load","error_model"]
        d.loc[d["corak_ilustrasi"].isin(invalid), "corak_ilustrasi"] = pd.NA
        d.loc[~d["corak_ilustrasi"].isin(CORAK_ID.keys()), "corak_ilustrasi"] = pd.NA

    d["YEAR"] = pd.to_numeric(d["YEAR"], errors="coerce").fillna(0).astype(int)
    d["image_ok"] = d["image_ok"].astype(str).str.upper().isin(["TRUE","1","YES"])
    d["ILLUSTRATOR"] = d["ILLUSTRATOR"].fillna("").astype(str).str.strip()
    d.loc[d["ILLUSTRATOR"].isin(["nan","NaN","None","none"]), "ILLUSTRATOR"] = ""

    # Normalisasi penerbit
    if "PUBLISHER" in d.columns:
        d["PUBLISHER"] = d["PUBLISHER"].fillna("").astype(str).str.strip()
        d.loc[d["PUBLISHER"].isin(["nan","NaN","None","none",""]), "PUBLISHER"] = "Tidak Diketahui"
    else:
        d["PUBLISHER"] = "Tidak Diketahui"

    valid_tf = set(TYPEFACE_ID.keys())
    if "typeface_kategori" in d.columns:
        d["typeface_kategori"] = d["typeface_kategori"].fillna("unknown").astype(str).str.strip()
        d["typeface_kategori"] = d["typeface_kategori"].where(
            d["typeface_kategori"].isin(valid_tf), other="unknown")

    def _reklasifikasi(row):
        try:
            h = float(row.get("warna_h_1",0) or 0)
            s = float(row.get("warna_s_1",0) or 0)
            v = float(row.get("warna_v_1",0) or 0)
        except: return "putih"
        return _klasifikasi_hsv(h,s,v) or "putih"
    d["warna_kategori"] = d.apply(_reklasifikasi, axis=1)

    if "has_person" in d.columns:
        d["has_person"] = d["has_person"].astype(str).str.upper().isin(["TRUE","1","YES"])
    if "objects_count" in d.columns:
        d["objects_count"] = pd.to_numeric(d["objects_count"], errors="coerce").fillna(0).astype(int)

    # Kolom popularitas terstandarisasi
    for c in ["RATING","TOTAL_RATING","TOTAL_REVIEW"]:
        if c not in d.columns:
            d[c] = np.nan

    return d


# ─────────────────────────────────────────────────────────────────────────────
# BOOK CARD
# ─────────────────────────────────────────────────────────────────────────────
def book_card(row, col_obj, show_corak=False, show_probs=False):
    with col_obj:
        cp = cover_path(row.get("IMAGE_FILE"))
        if cp:
            st.image(cp, use_container_width=True)
        else:
            st.markdown('<div style="height:160px;background:rgba(128,128,128,.09);'
                        'border-radius:8px 8px 0 0;display:flex;align-items:center;'
                        'justify-content:center;font-size:2rem;">📖</div>',
                        unsafe_allow_html=True)
        year  = int(row["YEAR"]) if row.get("YEAR",0) and int(row.get("YEAR",0)) > 0 else "–"
        url   = row.get("URL","")
        title = str(row.get("TITLE","–"))
        title_html = (f'<a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">{title}</a>'
                      if url else title)
        shelf  = SHELF_LABEL.get(str(row.get("SHELF","")), "")
        badges = f'<span class="badge">{shelf}</span>' if shelf else ""
        if show_corak:
            corak = str(row.get("corak_ilustrasi","") or "")
            if corak and corak != "nan":
                label = CORAK_ID.get(corak, corak)
                clr   = CORAK_CLR.get(corak, "#999")
                icon  = CORAK_ICON.get(corak, "🎨")
                conf  = float(row.get("corak_konfiden", 0) or 0)
                badges += (f'<span class="badge" style="border-color:{clr};color:{clr};">'
                           f'{icon} {label} {conf:.2f}</span>')
        prob_html = ""
        if show_probs:
            pb_html = prob_bars_corak_html(row)
            if pb_html:
                prob_html = f'<div style="margin-top:.4rem;">{pb_html}</div>'
        st.markdown(
            f'<div class="bk-info"><div class="bk-title">{title_html}</div>'
            f'<div class="bk-meta">{row.get("AUTHOR","–")} · {year}</div>'
            f'{palette_html(row)}{badges}{prob_html}</div>',
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
        for j, (_,row) in enumerate(chunk.iterrows()):
            book_card(row, cols[j], **kw)


# ─────────────────────────────────────────────────────────────────────────────
# HEATMAPS
# ─────────────────────────────────────────────────────────────────────────────
def heatmap_corak_genre(d, top_n=16, min_count=3, normalize="index"):
    genres       = _top_genres(d, top_n, min_count)
    corak_keys   = [k for k in CORAK_ORDER if k in CORAK_ID]
    corak_labels = [CORAK_ID[k] for k in corak_keys]
    mat = pd.DataFrame(0.0, index=genres, columns=corak_labels)
    d2  = d[d["corak_ilustrasi"].notna()].copy()
    if d2.empty or "GENRES" not in d2.columns: return go.Figure()
    genre_lists = expand_genres(d2["GENRES"])
    for g in genres:
        sub = d2[[g in gl for gl in genre_lists]]
        if sub.empty: continue
        if normalize == "count":
            vc = sub["corak_ilustrasi"].value_counts()
            for k in corak_keys: mat.loc[g, CORAK_ID[k]] = vc.get(k, 0)
        else:
            vc = sub["corak_ilustrasi"].value_counts(normalize=True)
            for k in corak_keys: mat.loc[g, CORAK_ID[k]] = vc.get(k, 0.0)
    text_mat = ((mat*100).round(0).astype(int).astype(str)+"%"
                if normalize != "count"
                else mat.round(0).astype(int).astype(str))
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=corak_labels, y=_y_labels(genres),
        colorscale="Greens",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=9,color="#1A1A1A"),
        showscale=True,
        hovertemplate="Genre: %{y}<br>Corak: %{x}<br>Nilai: %{text}<extra></extra>",
    ))
    fig.update_layout(**_pb(max(380,top_n*32),
        margin=dict(l=210,r=20,t=42,b=100),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickangle=-35),
        shapes=_klaster_shapes(genres),
    ))
    return fig

def heatmap_warna_genre(d, top_n=16):
    genres = _top_genres(d, top_n)
    mat    = pd.DataFrame(0.0, index=genres, columns=WARNA_ORDER)
    genre_lists = expand_genres(d["GENRES"])
    for g in genres:
        sub = d[[g in gl for gl in genre_lists]]
        if len(sub) == 0: continue
        vc = compute_warna_distribusi(sub)
        for w in WARNA_ORDER: mat.loc[g,w] = vc.get(w,0.0)
    warna_global = compute_warna_distribusi(d)
    x_labels = [f"{w}<br>({warna_global.get(w,0)*100:.1f}%)" for w in WARNA_ORDER]
    text_mat = (mat*100).round(1).astype(str)+"%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=x_labels, y=_y_labels(genres),
        colorscale="YlOrRd",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=9,color="#1A1A1A"),
        showscale=True, zmin=0, zmax=1,
    ))
    fig.update_layout(**_pb(max(360,top_n*30),
        margin=dict(l=180,r=20,t=40,b=90),
        yaxis=dict(autorange="reversed"),
    ))
    return fig

def heatmap_tf_genre(d, top_n=12):
    genres    = _top_genres(d, top_n)
    tf_keys   = TF_ANALISIS
    tf_labels = [TYPEFACE_ID[k] for k in tf_keys]
    mat = pd.DataFrame(0.0, index=genres, columns=tf_labels)
    d2  = d[d["typeface_kategori"].isin(tf_keys)]
    genre_lists = expand_genres(d2["GENRES"])
    for g in genres:
        sub = d2[[g in gl for gl in genre_lists]]
        if len(sub) == 0: continue
        vc = sub["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)
        for k in tf_keys: mat.loc[g, TYPEFACE_ID[k]] = vc.get(TYPEFACE_ID[k], 0.0)
    text_mat = (mat*100).round(0).astype(int).astype(str)+"%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=tf_labels, y=_y_labels(genres),
        colorscale="Purples",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=9,color="#1A1A1A"),
        showscale=True,
    ))
    fig.update_layout(**_pb(max(340,top_n*28),
        margin=dict(l=180,r=20,t=32,b=90),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickangle=-30),
    ))
    return fig

def heatmap_objek_genre(d, object_col, top_n_obj=20, top_n_genre=14):
    genres = _top_genres(d, top_n_genre)
    if not genres: return None
    ctr_global = _parse_objects_detected(d[object_col])
    if not ctr_global: return None
    top_objs = [o for o,_ in ctr_global.most_common(top_n_obj)]
    mat = pd.DataFrame(0.0, index=genres, columns=top_objs)
    genre_lists = expand_genres(d["GENRES"])
    for g in genres:
        sub = d[[g in gl for gl in genre_lists]]
        n_sub = len(sub)
        if n_sub == 0: continue
        for obj in top_objs:
            obj_en = [k for k,v in YOLO_ID.items() if v == obj]
            obj_candidates = [obj.lower()] + [x.lower() for x in obj_en]
            def has_obj(val, cands=obj_candidates):
                s = str(val).lower()
                return any(x in s for x in cands)
            mat.loc[g, obj] = sub[object_col].apply(has_obj).sum() / n_sub
    text_mat = (mat*100).round(0).astype(int).astype(str)+"%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=top_objs, y=_y_labels(genres),
        colorscale="YlOrRd",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=8,color="#1A1A1A"),
        showscale=True, zmin=0, zmax=max(float(mat.values.max()),0.01),
    ))
    fig.update_layout(**_pb(max(380,top_n_genre*32),
        margin=dict(l=210,r=20,t=42,b=115),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickangle=-40),
        title="% sampul per genre yang mengandung objek",
        shapes=_klaster_shapes(genres),
    ))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS ILUSTRASI — perbandingan WITH/WITHOUT ILLUSTRATOR
# ─────────────────────────────────────────────────────────────────────────────
def _chart_diff_corak(d_with, d_without, label_with="Dengan illustrator",
                      label_without="Tanpa illustrator", height=300):
    """Bar chart simpangan corak: with vs without."""
    vc_w = d_with["corak_ilustrasi"].value_counts(normalize=True) if len(d_with) > 0 else pd.Series(dtype=float)
    vc_o = d_without["corak_ilustrasi"].value_counts(normalize=True) if len(d_without) > 0 else pd.Series(dtype=float)
    all_keys = list(CORAK_ID.keys())
    rows = []
    for k in all_keys:
        rows.append({"corak": CORAK_ID[k], "Kelompok": label_with,    "proporsi": vc_w.get(k, 0)})
        rows.append({"corak": CORAK_ID[k], "Kelompok": label_without, "proporsi": vc_o.get(k, 0)})
    df_bar = pd.DataFrame(rows)
    fig = px.bar(df_bar, x="proporsi", y="corak", color="Kelompok", barmode="group",
                 orientation="h",
                 color_discrete_sequence=["#1E88E5","#E53935"],
                 text=df_bar["proporsi"].map(lambda x: f"{x*100:.1f}%"))
    fig.update_layout(**_pb(height), showlegend=True,
                      xaxis_title="Proporsi", yaxis_title="",
                      legend=dict(orientation="h", y=1.08, font=dict(size=9)),
                      yaxis=dict(categoryorder="total ascending"))
    fig.update_traces(textposition="outside", marker_line_width=0)
    return fig

def _tren_corak_tahun(d, normalize=True):
    """Stacked bar tren corak per tahun."""
    dy = d[d["YEAR"] > 0].copy()
    dy["corak_label"] = dy["corak_ilustrasi"].map(CORAK_ID)
    if normalize:
        tr = dy.groupby(["YEAR","corak_label"]).size().reset_index(name="n")
        totals = tr.groupby("YEAR")["n"].transform("sum")
        tr["pct"] = tr["n"] / totals
        y_col = "pct"; y_title = "Proporsi"
    else:
        tr = dy.groupby(["YEAR","corak_label"]).size().reset_index(name="n")
        y_col = "n"; y_title = "Jumlah"
    fig = px.bar(tr, x="YEAR", y=y_col, color="corak_label", barmode="stack",
                 color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID})
    fig.update_layout(**_pb(360), xaxis_title="", yaxis_title=y_title,
                      legend=dict(orientation="h", y=-.25, font=dict(size=9)))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS POPULARITAS
# ─────────────────────────────────────────────────────────────────────────────
def _segmentasi_popularitas(d, kolom="TOTAL_RATING", n_top=20, n_bottom=20):
    """
    Bagi buku menjadi tiga segmen: populer (top-N), menengah, kurang populer (bottom-N).
    Kembalikan (df_top, df_mid, df_bot).
    """
    d2 = d.dropna(subset=[kolom]).copy()
    if d2.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    d2 = d2.sort_values(kolom, ascending=False).reset_index(drop=True)
    df_top = d2.head(n_top)
    df_bot = d2.tail(n_bottom)
    df_mid = d2.iloc[n_top:-n_bottom] if len(d2) > n_top + n_bottom else pd.DataFrame()
    return df_top, df_mid, df_bot

def _radar_visual(df_top, df_mid, df_bot, title="Profil Visual"):
    """
    Radar chart perbandingan profil visual: warna, corak, tipografi.
    Menggunakan proporsi corak dominan sebagai dimensi.
    """
    def _profil(df):
        if df.empty: return {}
        p = {}
        # Corak
        vc = df["corak_ilustrasi"].value_counts(normalize=True)
        for k in CORAK_ID: p[CORAK_ID[k]] = vc.get(k, 0)
        return p

    profil_top = _profil(df_top)
    profil_bot = _profil(df_bot)
    if not profil_top: return go.Figure()

    categories = list(profil_top.keys())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[profil_top.get(c,0)*100 for c in categories] + [profil_top.get(categories[0],0)*100],
        theta=categories + [categories[0]],
        fill='toself', name="Populer (Top)",
        line_color="#1E88E5", fillcolor="rgba(30,136,229,.15)"
    ))
    if not df_bot.empty:
        fig.add_trace(go.Scatterpolar(
            r=[profil_bot.get(c,0)*100 for c in categories] + [profil_bot.get(categories[0],0)*100],
            theta=categories + [categories[0]],
            fill='toself', name="Kurang populer",
            line_color="#E53935", fillcolor="rgba(229,57,53,.10)"
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,30])),
        showlegend=True, height=360,
        margin=dict(l=40,r=40,t=50,b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        title=dict(text=title, font=dict(size=13)),
    )
    return fig

def _bar_popularitas_visual(d, kolom_visual, label_map, kolom_pop="TOTAL_RATING",
                            judul="Rata-rata rating per kategori", color_map=None):
    """Bar chart rata-rata kolom popularitas per kategori visual."""
    d2 = d.dropna(subset=[kolom_visual, kolom_pop]).copy()
    if d2.empty: return go.Figure()
    d2["_label"] = d2[kolom_visual].map(label_map).fillna(d2[kolom_visual])
    agg = d2.groupby("_label")[kolom_pop].agg(["mean","count"]).reset_index()
    agg.columns = ["Kategori","Rata-rata","Jumlah buku"]
    agg = agg[agg["Jumlah buku"] >= 5].sort_values("Rata-rata", ascending=True)
    fig = px.bar(agg, x="Rata-rata", y="Kategori", orientation="h",
                 color="Kategori", text=agg["Rata-rata"].map(lambda x: f"{x:,.0f}"),
                 color_discrete_map=color_map or {},
                 hover_data={"Jumlah buku":True})
    fig.update_layout(**_pb(max(280, len(agg)*30)), showlegend=False,
                      xaxis_title=kolom_pop, yaxis_title="",
                      title=dict(text=judul, font=dict(size=12)))
    fig.update_traces(textposition="outside", marker_line_width=0)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA & DERIVED FRAMES
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner("Memuat data…"):
    df = load_data(DATA_PATH)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📖 Kartografi Sampul")
    st.markdown("<small>Analisis komputasional sampul buku sastra Indonesia 2000–2025</small>",
                unsafe_allow_html=True)
    st.markdown("---")
    HAL = st.radio("Navigasi", [
        "Beranda",
        "Warna",
        "Tipografi",
        "Corak Ilustrasi",
        "Genre",
        "Penerbit",
        "Popularitas",
        "Illustrator",
        "Jelajah Buku",
    ], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Filter Tahun**")
    yr_range = st.slider("Tahun", 2000, 2025, (2000,2025), label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<small>Metode: K-Means HSV · CLIP 10 corak · YOLOv8m · DETR ResNet-50</small>",
                unsafe_allow_html=True)

DF      = df[(df["YEAR"] >= yr_range[0]) & (df["YEAR"] <= yr_range[1])].copy()
_gc     = genre_counts(DF)
_n_unik = len([g for g in _gc if g not in GENRE_EXCLUDE])
DF_tf   = DF[DF["typeface_kategori"].isin(TF_ANALISIS)].copy()
D_corak = DF[DF["corak_ilustrasi"].notna()].copy()
D_ill   = DF[DF["ILLUSTRATOR"].ne("")].copy()


# ══════════════════════════════════════════════════════════════════════════════
# BERANDA
# ══════════════════════════════════════════════════════════════════════════════
if HAL == "Beranda":
    st.markdown("# Kartografi Sampul Sastra Indonesia")
    st.markdown(
        f"Pemetaan komputasional terhadap **{len(DF):,} sampul buku** fiksi dan puisi Indonesia "
        f"terbit 2000–2025, dianalisis melalui tiga aspek visual: warna, tipografi, dan corak ilustrasi."
    )
    _hr()
    c1,c2,c3,c4 = st.columns(4)
    for col,(lbl,val,sub,clr) in zip([c1,c2,c3,c4],[
        ("Total Buku",       len(DF),      "teranalisis",                "#1E88E5"),
        ("Tipografi",        len(DF_tf),   "typeface terklasifikasi",    "#8E24AA"),
        ("Corak Ilustrasi",  len(D_corak), "terkategorikan (10 corak)",  "#E53935"),
        ("Genre Unik",       _n_unik,      "genre ditemukan",            "#00ACC1"),
    ]):
        with col:
            st.markdown(
                f'<div class="stat-card" style="border-top:3px solid {clr};">'
                f'<div class="lbl">{lbl}</div>'
                f'<div class="val" style="color:{clr};">{int(val):,}</div>'
                f'<div class="sub">{sub}</div></div>',
                unsafe_allow_html=True
            )
    _hr()
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Tren Terbit per Tahun**")
        yr = DF[DF["YEAR"]>0].groupby("YEAR").size().reset_index(name="n")
        fig = px.bar(yr, x="YEAR", y="n", color_discrete_sequence=["#1E88E5"])
        fig.update_layout(**_pb(280), xaxis_title="", yaxis_title="", showlegend=False)
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        st.markdown("**Distribusi 10 Corak Ilustrasi**")
        vc_corak = D_corak["corak_ilustrasi"].value_counts()
        labels_c = [CORAK_ID.get(k,k) for k in vc_corak.index]
        fig2 = px.bar(x=vc_corak.values, y=labels_c, orientation="h",
                      color=labels_c,
                      color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID},
                      text=vc_corak.values)
        fig2.update_layout(**_pb(280), showlegend=False, xaxis_title="", yaxis_title="",
                           yaxis=dict(categoryorder="total ascending"))
        fig2.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig2, use_container_width=True)
    _hr()
    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("**Komposisi Warna Keseluruhan**")
        wc = compute_warna_distribusi(DF)
        names_ord = [w for w in WARNA_ORDER if wc.get(w,0) > 0]
        fig3 = px.pie(values=[wc[w] for w in names_ord], names=[w for w in names_ord], hole=0.4,
                      color=[w for w in names_ord], color_discrete_map=WARNA_HEX)
        fig3.update_layout(**_pb(260))
        fig3.update_traces(textinfo="percent+label", textfont_size=10)
        st.plotly_chart(fig3, use_container_width=True)
    with col_d:
        st.markdown("**Distribusi Tipografi**")
        tc = DF_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts()
        fig4 = px.bar(x=tc.values, y=tc.index, orientation="h",
                      color=tc.index,
                      color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
                      text=tc.values)
        fig4.update_layout(**_pb(260), showlegend=False, xaxis_title="", yaxis_title="",
                           yaxis=dict(categoryorder="total ascending"))
        fig4.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig4, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# WARNA
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Warna":
    st.markdown("## Analisis Warna")
    wc_full = compute_warna_distribusi(DF)
    ca, cb  = st.columns([1,2])
    with ca:
        st.markdown("**Distribusi Warna Keseluruhan**")
        names_ord = [w for w in WARNA_ORDER if wc_full.get(w,0) > 0]
        fig = px.pie(values=[wc_full[w] for w in names_ord], names=names_ord, hole=0.42,
                     color=names_ord, color_discrete_map=WARNA_HEX)
        fig.update_layout(**_pb(300))
        fig.update_traces(textinfo="percent", textfont_size=10)
        st.plotly_chart(fig, use_container_width=True)
    with cb:
        st.markdown("**Tren Warna per Tahun**")
        rows_trend = []
        for yr, grp in DF[DF["YEAR"]>0].groupby("YEAR"):
            wc_yr = compute_warna_distribusi(grp)
            nb = len(grp)
            for w in WARNA_ORDER:
                rows_trend.append({"YEAR":yr,"warna":w,"bobot":wc_yr.get(w,0)*nb})
        trnd = pd.DataFrame(rows_trend)
        fig2 = px.bar(trnd, x="YEAR", y="bobot", color="warna",
                      color_discrete_map=WARNA_HEX, barmode="stack")
        fig2.update_layout(**_pb(360), xaxis_title="", yaxis_title="Bobot",
                           legend=dict(orientation="h",y=-.15,font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)
    _hr()
    st.markdown("**Peta Panas Warna × Genre**")
    hn_w = st.slider("Jumlah genre", 6, 20, 16, 2, key="hn_warna")
    st.plotly_chart(heatmap_warna_genre(DF, hn_w), use_container_width=True)
    _hr()
    st.markdown("**Kecerahan vs Saturasi per Warna**")
    df_sc = DF.dropna(subset=["brightness_mean","saturation_mean","warna_kategori"]).copy()
    fig_sc = px.scatter(df_sc, x="brightness_mean", y="saturation_mean",
                        color="warna_kategori", color_discrete_map=WARNA_HEX, opacity=.35,
                        custom_data=["TITLE","AUTHOR","YEAR"])
    fig_sc.update_traces(marker=dict(size=4),
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} · %{customdata[2]}<extra></extra>")
    fig_sc.update_layout(**_pb(300), showlegend=True,
        legend=dict(orientation="h",y=-.18,font=dict(size=10)),
        xaxis_title="Kecerahan (V)", yaxis_title="Saturasi (S)")
    st.plotly_chart(fig_sc, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TIPOGRAFI
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Tipografi":
    st.markdown("## Analisis Tipografi")
    if _TIPOGRAFI_MODUL:
        render_tipografi_tab(DF)
    else:
        # Fallback: render inline seperti sebelumnya
        st.info("Modul tipografi_4cat.py tidak terdeteksi — menampilkan analisis bawaan.")
        n_unk = int((DF["typeface_kategori"] == "unknown").sum())
        c1,c2,c3 = st.columns(3)
        c1.metric("Terklasifikasi", f"{len(DF_tf):,}")
        c2.metric("Tidak terklasifikasi", f"{n_unk:,}")
        c3.metric("Cakupan", f"{len(DF_tf)/len(DF)*100:.1f}%")
        _hr()
        ca, cb = st.columns(2)
        with ca:
            st.markdown("**Distribusi Typeface**")
            tc = DF_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts()
            fig = px.bar(x=tc.values, y=tc.index, orientation="h",
                         color=tc.index,
                         color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
                         text=tc.values)
            fig.update_layout(**_pb(300), showlegend=False, xaxis_title="", yaxis_title="",
                              yaxis=dict(categoryorder="total ascending"))
            fig.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)
        with cb:
            st.markdown("**Tren Tipografi per Tahun**")
            dy = DF_tf[DF_tf["YEAR"]>0].copy()
            dy["tf_label"] = dy["typeface_kategori"].map(TYPEFACE_ID)
            tr = dy.groupby(["YEAR","tf_label"]).size().reset_index(name="n")
            fig2 = px.bar(tr, x="YEAR", y="n", color="tf_label", barmode="stack",
                          color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID})
            fig2.update_layout(**_pb(300), xaxis_title="", yaxis_title="Jumlah",
                               legend=dict(orientation="h",y=-.25,font=dict(size=9)))
            st.plotly_chart(fig2, use_container_width=True)
        _hr()
        st.markdown("**Heatmap Tipografi × Genre**")
        hn_tf = st.slider("Jumlah genre", 6, 20, 12, 2, key="hn_tf")
        st.plotly_chart(heatmap_tf_genre(DF, hn_tf), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# CORAK ILUSTRASI
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Corak Ilustrasi":
    st.markdown("## Analisis Corak Ilustrasi")
    st.caption("CLIP zero-shot 10 kategori · multi-prompt voting · YOLOv8m")

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Total terkategorikan", f"{len(D_corak):,}")
    m2.metric("Dari total buku", f"{len(D_corak)/len(DF)*100:.1f}%")
    if "corak_konfiden" in D_corak.columns:
        m3.metric("Rata-rata confidence", f"{D_corak['corak_konfiden'].mean():.3f}")
        m4.metric("Ambigu < 0.22", f"{(D_corak['corak_konfiden'] < 0.22).sum():,}")
    _hr()

    # Kartu 10 corak
    st.markdown("### Sepuluh Corak Ilustrasi")
    for row_keys in [CORAK_ORDER[:5], CORAK_ORDER[5:]]:
        cols = st.columns(5)
        for col, key in zip(cols, row_keys):
            n   = int((D_corak["corak_ilustrasi"] == key).sum())
            pct = n / len(D_corak) * 100 if len(D_corak) else 0
            clr = CORAK_CLR.get(key,"#999")
            with col:
                st.markdown(
                    f'<div style="border:1px solid rgba(128,128,128,.18);border-radius:10px;'
                    f'padding:.65rem .55rem .75rem;text-align:center;height:100%;">'
                    f'<div style="font-size:1.6rem;margin-bottom:.25rem;">{CORAK_ICON[key]}</div>'
                    f'<div style="font-size:.7rem;font-weight:700;color:{clr};margin-bottom:.25rem;">'
                    f'{CORAK_ID[key]}</div>'
                    f'<div style="font-size:1.25rem;font-weight:700;">{n:,}</div>'
                    f'<div style="font-size:.62rem;opacity:.55;">{pct:.1f}%</div>'
                    f'<div style="font-size:.58rem;opacity:.62;line-height:1.35;text-align:left;'
                    f'margin-top:.45rem;">{CORAK_DESC[key]}</div></div>',
                    unsafe_allow_html=True
                )

    _hr()

    # ── TREN PER TAHUN ──────────────────────────────────────────────────────
    st.markdown("### Tren Corak Ilustrasi per Tahun")
    st.caption(
        "Komposisi corak ilustrasi berubah seiring waktu. "
        "Mode proporsi menunjukkan pergeseran relatif; mode jumlah menunjukkan volume produksi."
    )
    tc1, tc2 = st.columns([1,3])
    with tc1:
        tren_mode = st.radio("Mode tren", ["Proporsi","Jumlah"], key="tren_corak_mode")
        tren_annotasi = st.checkbox("Tampilkan annotation tren dominan", value=True, key="tren_ann")
    with tc2:
        fig_tren = _tren_corak_tahun(D_corak, normalize=(tren_mode == "Proporsi"))
        # Tambahkan annotation corak dominan per tahun jika diminta
        if tren_annotasi and not D_corak[D_corak["YEAR"]>0].empty:
            dy_ann = D_corak[D_corak["YEAR"]>0].copy()
            dom_per_year = (
                dy_ann.groupby("YEAR")["corak_ilustrasi"]
                .agg(lambda x: x.value_counts().index[0] if len(x)>0 else "")
            )
            for yr_a, kat_a in dom_per_year.items():
                if kat_a:
                    clr_a = CORAK_CLR.get(kat_a, "#999")
                    fig_tren.add_annotation(
                        x=yr_a, y=0, yref="paper",
                        text=CORAK_ICON.get(kat_a,""),
                        showarrow=False, font=dict(size=9),
                        xanchor="center", yanchor="bottom"
                    )
        st.plotly_chart(fig_tren, use_container_width=True)

    # Line chart corak tertentu
    _hr()
    st.markdown("**Sorot Corak Tertentu**")
    corak_pilih = st.multiselect(
        "Pilih corak untuk disorot",
        options=[CORAK_ID[k] for k in CORAK_ORDER],
        default=[CORAK_ID["minimalis"], CORAK_ID["fotografi_kolase"], CORAK_ID["kartunal"]],
        key="tren_sorot"
    )
    if corak_pilih:
        rev_corak = {v:k for k,v in CORAK_ID.items()}
        dy_line   = D_corak[D_corak["YEAR"].between(2000,2025)].copy()
        tot_year  = dy_line.groupby("YEAR").size().rename("total")
        rows_line = []
        for label in corak_pilih:
            k = rev_corak.get(label, label)
            grp = dy_line[dy_line["corak_ilustrasi"]==k].groupby("YEAR").size().rename("n")
            merged = grp.to_frame().join(tot_year).reset_index()
            merged["pct"] = merged["n"] / merged["total"] * 100
            merged["Corak"] = label
            rows_line.append(merged)
        df_line = pd.concat(rows_line)
        fig_line = px.line(df_line, x="YEAR", y="pct", color="Corak",
                           color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID},
                           markers=True)
        fig_line.update_layout(**_pb(320), xaxis_title="Tahun",
                               yaxis_title="% dari semua sampul",
                               legend=dict(orientation="h",y=1.1,font=dict(size=10)))
        st.plotly_chart(fig_line, use_container_width=True)

    _hr()

    # ── ILLUSTRATOR vs TANPA ────────────────────────────────────────────────
    st.markdown("### Ilustrasi: Dengan vs Tanpa Nama Illustrator")
    has_ill_mask = D_corak["ILLUSTRATOR"].fillna("").astype(str).str.strip().ne("")
    D_dengan_ill = D_corak[has_ill_mask]
    D_tanpa_ill  = D_corak[~has_ill_mask]

    ia1, ia2, ia3 = st.columns(3)
    ia1.metric("Dengan illustrator", f"{len(D_dengan_ill):,}")
    ia2.metric("Tanpa illustrator", f"{len(D_tanpa_ill):,}")
    ia3.metric("Prop. dengan illustrator", f"{len(D_dengan_ill)/len(D_corak)*100:.1f}%")

    if len(D_dengan_ill) > 0 and len(D_tanpa_ill) > 0:
        ib1, ib2 = st.columns(2)
        with ib1:
            st.markdown("**Perbandingan Distribusi Corak**")
            st.plotly_chart(
                _chart_diff_corak(D_dengan_ill, D_tanpa_ill),
                use_container_width=True
            )
        with ib2:
            st.markdown("**Simpangan dari Rata-rata Keseluruhan**")
            vc_w  = D_dengan_ill["corak_ilustrasi"].value_counts(normalize=True)
            vc_all = D_corak["corak_ilustrasi"].value_counts(normalize=True)
            diff  = (vc_w - vc_all).dropna().sort_values(ascending=False)
            df_diff = pd.DataFrame({
                "corak": [CORAK_ID.get(k,k) for k in diff.index],
                "delta": diff.values
            })
            fig_diff = px.bar(df_diff, x="delta", y="corak", orientation="h",
                              color="corak",
                              color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID})
            fig_diff.update_layout(**_pb(300), showlegend=False,
                                   xaxis_title="Simpangan dari total",
                                   yaxis=dict(categoryorder="total ascending"))
            fig_diff.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
            st.plotly_chart(fig_diff, use_container_width=True)

        st.caption("Nilai positif pada grafik simpangan = corak lebih sering pada buku "
                   "yang mencantumkan nama illustrator.")

        # Tren WITH/WITHOUT per tahun
        _hr()
        st.markdown("**Tren Corak per Tahun: Dengan vs Tanpa Illustrator**")
        corak_compare = st.selectbox(
            "Pilih corak untuk dibandingkan",
            [CORAK_ID[k] for k in CORAK_ORDER],
            key="compare_ill_corak"
        )
        rev_c     = {v:k for k,v in CORAK_ID.items()}
        k_compare = rev_c.get(corak_compare, corak_compare)

        def _prop_per_tahun(d_sub, k):
            d2 = d_sub[d_sub["YEAR"].between(2000,2025)].copy()
            tot  = d2.groupby("YEAR").size().rename("total")
            hits = d2[d2["corak_ilustrasi"]==k].groupby("YEAR").size().rename("n")
            m    = hits.to_frame().join(tot).reset_index().fillna(0)
            m["pct"] = m["n"] / m["total"] * 100
            return m

        prop_w = _prop_per_tahun(D_dengan_ill, k_compare)
        prop_w["Kelompok"] = "Dengan illustrator"
        prop_o = _prop_per_tahun(D_tanpa_ill, k_compare)
        prop_o["Kelompok"] = "Tanpa illustrator"
        df_tren_ill = pd.concat([prop_w, prop_o])

        fig_tren_ill = px.line(df_tren_ill, x="YEAR", y="pct", color="Kelompok",
                               color_discrete_sequence=["#1E88E5","#E53935"], markers=True)
        fig_tren_ill.update_layout(**_pb(300),
                                   xaxis_title="Tahun",
                                   yaxis_title=f"% {corak_compare}",
                                   legend=dict(orientation="h", y=1.1, font=dict(size=10)))
        st.plotly_chart(fig_tren_ill, use_container_width=True)

    _hr()

    # ── HEATMAP & EXPLORER ──────────────────────────────────────────────────
    st.markdown("### Heatmap Corak × Genre")
    h1,h2,h3 = st.columns([1,1,1])
    with h1: n_genre    = st.slider("Jumlah genre", 6, 30, 16, 2, key="hm_corak_genre_n")
    with h2: min_count  = st.slider("Min. buku per genre", 1, 20, 3, 1, key="hm_corak_min")
    with h3: norm_mode  = st.selectbox("Mode nilai", ["Persentase","Jumlah"], key="hm_corak_mode")
    st.plotly_chart(
        heatmap_corak_genre(D_corak, top_n=n_genre, min_count=min_count,
                            normalize="count" if norm_mode=="Jumlah" else "index"),
        use_container_width=True
    )

    _hr()
    st.markdown("### Sampul Confidence Tertinggi per Corak")
    n_top = st.slider("Jumlah sampul per corak", 3, 10, 5, 1, key="top_conf_corak")
    show_probs_top = st.checkbox("Tampilkan skor semua corak", value=False, key="show_probs_top")
    tabs = st.tabs([f"{CORAK_ICON[k]} {CORAK_ID[k]}" for k in CORAK_ORDER])
    for tab, key in zip(tabs, CORAK_ORDER):
        with tab:
            sub = (D_corak[D_corak["corak_ilustrasi"] == key]
                   .sort_values("corak_konfiden", ascending=False)
                   .head(n_top))
            total_n = int((D_corak["corak_ilustrasi"] == key).sum())
            st.markdown(f"**{CORAK_ID[key]}** — {total_n:,} sampul  |  {CORAK_DESC[key]}")
            grid(sub, n_cols=min(5,n_top), show_corak=True, show_probs=show_probs_top)

    _hr()
    st.markdown("### Jelajah Sampul berdasarkan Corak")
    genre_opts = [g for g,c in _gc.most_common() if g not in GENRE_EXCLUDE and c >= 3][:40]
    f1,f2,f3,f4 = st.columns([2,2,2,1])
    with f1: q_js      = st.text_input("Judul / penulis", key="corak_q")
    with f2: corak_sel = st.selectbox("Corak", ["Semua"]+[CORAK_ID[k] for k in CORAK_ORDER], key="corak_sel")
    with f3: genre_sel = st.selectbox("Genre", ["Semua"]+genre_opts, key="corak_genre_sel")
    with f4: n_show    = st.slider("Tampilkan", 4, 40, 12, 4, key="corak_n_show")
    f5,f6 = st.columns(2)
    with f5: min_conf_js  = st.slider("Min. confidence", 0.0, 1.0, 0.0, 0.05, key="corak_min_conf")
    with f6: show_probs_s = st.checkbox("Skor semua corak", key="corak_show_probs")

    DS = D_corak.copy()
    if q_js:
        ql   = q_js.lower()
        mask = DS["TITLE"].astype(str).str.lower().str.contains(ql,na=False)
        if "AUTHOR" in DS.columns: mask |= DS["AUTHOR"].astype(str).str.lower().str.contains(ql,na=False)
        DS = DS[mask]
    if corak_sel != "Semua":
        rev = {v:k for k,v in CORAK_ID.items()}
        DS  = DS[DS["corak_ilustrasi"] == rev.get(corak_sel,corak_sel)]
    if genre_sel != "Semua" and "GENRES" in DS.columns:
        gl = expand_genres(DS["GENRES"])
        DS = DS[[genre_sel in x for x in gl]]
    if min_conf_js > 0:
        DS = DS[DS["corak_konfiden"] >= min_conf_js]
    st.markdown(f"**{len(DS):,} buku ditemukan**")
    if not DS.empty:
        grid(DS.sort_values("corak_konfiden",ascending=False).head(n_show),
             n_cols=4, show_corak=True, show_probs=show_probs_s)


# ══════════════════════════════════════════════════════════════════════════════
# GENRE
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Genre":
    st.markdown("## Analisis Genre")
    all_items = [(g,n) for g,n in _gc.most_common() if g not in GENRE_EXCLUDE and n >= 3]

    st.markdown("**Klaster Genre**")
    kl_leg = st.columns(3)
    for kc,kl in zip(kl_leg, KLASTER):
        genre_str = ", ".join(kl["genres"][:5])+"…"
        kc.markdown(
            f'<div style="background:{kl["bg"]};border-left:4px solid {kl["color"]};'
            f'border-radius:0 8px 8px 0;padding:8px 12px;">'
            f'<div style="font-weight:600;color:{kl["color"]};font-size:12px;">'
            f'[{kl["id"]}] {kl["label"]}</div>'
            f'<div style="font-size:10px;opacity:.6;margin-top:4px;">{genre_str}</div></div>',
            unsafe_allow_html=True
        )
    _hr()
    n_co  = st.slider("Jumlah genre", 8, min(len(all_items),30), 16, 2, key="n_co")
    top_co = [g for g,_ in all_items[:n_co]]
    co = pd.DataFrame(0, index=top_co, columns=top_co)
    for gl in expand_genres(DF["GENRES"]):
        rel = [g for g in gl if g in top_co]
        for i,g1 in enumerate(rel):
            for g2 in rel[i+1:]:
                co.loc[g1,g2]+=1; co.loc[g2,g1]+=1
    for g in top_co: co.loc[g,g] = _gc[g]
    fig_co = go.Figure(data=go.Heatmap(
        z=co.values, x=_y_labels(top_co), y=_y_labels(top_co),
        colorscale="Oranges",
        text=co.values.astype(int).astype(str),
        texttemplate="%{text}", textfont=dict(size=9,color="#1A1A1A"),
        showscale=True,
    ))
    fig_co.update_layout(**_pb(max(420,n_co*28),
        margin=dict(l=150,r=20,t=32,b=150),
        xaxis=dict(tickangle=-40),
        yaxis=dict(autorange="reversed"),
    ))
    st.plotly_chart(fig_co, use_container_width=True)

    _hr()
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
        _hr()
        genre_lists_all = expand_genres(DF["GENRES"])
        mask_g  = [sel_genre in gl for gl in genre_lists_all]
        df_gs   = DF[mask_g]
        D_gs    = D_corak[[sel_genre in gl for gl in expand_genres(D_corak["GENRES"])]]
        if not df_gs.empty:
            st.markdown(f'#### Genre: **{sel_genre}** — {len(df_gs):,} buku')
            tab_w, tab_tf, tab_corak = st.tabs(["🎨 Warna","🔤 Tipografi","🖼️ Corak Ilustrasi"])
            with tab_w:
                wc_g   = compute_warna_distribusi(df_gs)
                wc_all = compute_warna_distribusi(DF)
                cw1,cw2 = st.columns(2)
                with cw1:
                    names_g = [w for w in WARNA_ORDER if wc_g.get(w,0) > 0]
                    fig = px.pie(values=[wc_g[w] for w in names_g], names=names_g, hole=0.42,
                                 color=names_g, color_discrete_map=WARNA_HEX)
                    fig.update_layout(**_pb(260))
                    fig.update_traces(textinfo="percent+label",textfont_size=10)
                    st.plotly_chart(fig, use_container_width=True)
                with cw2:
                    diff = (pd.Series(wc_g) - pd.Series(wc_all)).dropna().sort_values(ascending=False)
                    fig_d = px.bar(diff.reset_index().rename(columns={"index":"warna",0:"delta"}),
                                   x="delta", y="warna", orientation="h",
                                   color="warna", color_discrete_map=WARNA_HEX)
                    fig_d.update_layout(**_pb(260),showlegend=False,
                                        xaxis_title="Simpangan",yaxis_title="",
                                        yaxis=dict(categoryorder="total ascending"))
                    fig_d.add_vline(x=0,line_dash="dash",line_color="rgba(128,128,128,.4)")
                    st.plotly_chart(fig_d, use_container_width=True)
            with tab_tf:
                df_gs_tf = df_gs[df_gs["typeface_kategori"].isin(TF_ANALISIS)]
                if not df_gs_tf.empty:
                    tc_g = df_gs_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts()
                    tc_all2 = DF_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts()
                    ctf1,ctf2 = st.columns(2)
                    with ctf1:
                        fig = px.pie(values=tc_g.values,names=tc_g.index,hole=0.42,
                                     color=tc_g.index,
                                     color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID})
                        fig.update_layout(**_pb(250))
                        fig.update_traces(textinfo="percent+label",textfont_size=10)
                        st.plotly_chart(fig, use_container_width=True)
                    with ctf2:
                        diff_tf = (tc_g/len(df_gs_tf) - tc_all2/len(DF_tf)).dropna().sort_values(ascending=False)
                        fig_dtf = px.bar(diff_tf.reset_index().rename(columns={"index":"tipografi",0:"delta"}),
                                         x="delta",y="tipografi",orientation="h",
                                         color="tipografi",
                                         color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID})
                        fig_dtf.update_layout(**_pb(250),showlegend=False,
                                              xaxis_title="Simpangan",yaxis_title="",
                                              yaxis=dict(categoryorder="total ascending"))
                        fig_dtf.add_vline(x=0,line_dash="dash",line_color="rgba(128,128,128,.4)")
                        st.plotly_chart(fig_dtf, use_container_width=True)
            with tab_corak:
                if not D_gs.empty:
                    vc_corak_g   = D_gs["corak_ilustrasi"].value_counts(normalize=True)
                    vc_corak_all = D_corak["corak_ilustrasi"].value_counts(normalize=True)
                    cc1,cc2 = st.columns(2)
                    with cc1:
                        fig = px.pie(
                            values=vc_corak_g.values,
                            names=[CORAK_ID.get(k,k) for k in vc_corak_g.index],
                            hole=0.42, color=[CORAK_ID.get(k,k) for k in vc_corak_g.index],
                            color_discrete_map={CORAK_ID[k]:CORAK_CLR[k] for k in CORAK_ID}
                        )
                        fig.update_layout(**_pb(250))
                        fig.update_traces(textinfo="percent+label",textfont_size=10)
                        st.plotly_chart(fig, use_container_width=True)
                    with cc2:
                        diff_c = (vc_corak_g - vc_corak_all).dropna().sort_values(ascending=False)
                        df_dc  = pd.DataFrame({
                            "corak":[CORAK_ID.get(k,k) for k in diff_c.index],
                            "delta":diff_c.values
                        })
                        fig_dc = px.bar(df_dc, x="delta", y="corak", orientation="h",
                                        color="corak",
                                        color_discrete_map={CORAK_ID[k]:CORAK_CLR[k] for k in CORAK_ID})
                        fig_dc.update_layout(**_pb(250),showlegend=False,
                                             xaxis_title="Simpangan dari rata-rata",yaxis_title="",
                                             yaxis=dict(categoryorder="total ascending"))
                        fig_dc.add_vline(x=0,line_dash="dash",line_color="rgba(128,128,128,.4)")
                        st.plotly_chart(fig_dc, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PENERBIT
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Penerbit":
    st.markdown("## Analisis per Penerbit")
    st.caption("Bandingkan gaya visual (corak, warna, tipografi) antar penerbit.")

    # Ambil penerbit terbanyak
    top_pub = (
        DF[DF["PUBLISHER"] != "Tidak Diketahui"]["PUBLISHER"]
        .value_counts()
    )
    n_pub_slider = st.slider("Tampilkan Top-N penerbit", 5, min(50, len(top_pub)), 20, 5, key="n_pub")
    top_pub_list = top_pub.head(n_pub_slider).index.tolist()

    # Pilih penerbit untuk dianalisis
    pub_pilih = st.multiselect(
        "Pilih penerbit untuk perbandingan detail",
        options=top_pub_list,
        default=top_pub_list[:min(5, len(top_pub_list))],
        key="pub_pilih"
    )

    if not pub_pilih:
        st.info("Pilih minimal satu penerbit.")
    else:
        DF_pub = DF[DF["PUBLISHER"].isin(pub_pilih)].copy()
        D_corak_pub = DF_pub[DF_pub["corak_ilustrasi"].notna()].copy()

        # ── Ringkasan statistik per penerbit ────────────────────────────────
        _hr()
        st.markdown("**Ringkasan Statistik per Penerbit**")
        pub_stats = []
        for p in pub_pilih:
            dp = DF_pub[DF_pub["PUBLISHER"] == p]
            dp_c = D_corak_pub[D_corak_pub["PUBLISHER"] == p]
            dom_corak = dp_c["corak_ilustrasi"].value_counts().index[0] if len(dp_c)>0 else "–"
            dom_warna = dp["warna_kategori"].value_counts().index[0] if len(dp)>0 else "–"
            dom_tf    = dp[dp["typeface_kategori"].isin(TF_ANALISIS)]["typeface_kategori"].value_counts().index[0] \
                        if len(dp[dp["typeface_kategori"].isin(TF_ANALISIS)])>0 else "–"
            pub_stats.append({
                "Penerbit": p,
                "Jumlah Buku": len(dp),
                "Corak Dominan": CORAK_ID.get(dom_corak, dom_corak),
                "Warna Dominan": dom_warna,
                "Tipografi Dominan": TYPEFACE_ID.get(dom_tf, dom_tf),
                "Rata-rata Rating": f"{dp['RATING'].mean():.2f}" if dp["RATING"].notna().any() else "–",
                "Total Rating": f"{int(dp['TOTAL_RATING'].sum()):,}" if dp["TOTAL_RATING"].notna().any() else "–",
            })
        st.dataframe(pd.DataFrame(pub_stats), use_container_width=True, hide_index=True)

        _hr()
        # ── Heatmap corak per penerbit ───────────────────────────────────────
        st.markdown("**Distribusi Corak per Penerbit**")
        mat_pub = pd.DataFrame(0.0, index=pub_pilih, columns=[CORAK_ID[k] for k in CORAK_ORDER])
        for p in pub_pilih:
            sub = D_corak_pub[D_corak_pub["PUBLISHER"] == p]
            if len(sub) == 0: continue
            vc = sub["corak_ilustrasi"].value_counts(normalize=True)
            for k in CORAK_ORDER:
                mat_pub.loc[p, CORAK_ID[k]] = vc.get(k, 0.0)
        text_pub = (mat_pub*100).round(0).astype(int).astype(str)+"%"
        fig_pub = go.Figure(data=go.Heatmap(
            z=mat_pub.values,
            x=[CORAK_ID[k] for k in CORAK_ORDER],
            y=pub_pilih,
            colorscale="Teal",
            text=text_pub.values, texttemplate="%{text}",
            textfont=dict(size=9,color="#1A1A1A"),
            showscale=True,
        ))
        fig_pub.update_layout(**_pb(max(300, len(pub_pilih)*40),
            margin=dict(l=180,r=20,t=32,b=90),
            yaxis=dict(autorange="reversed"),
            xaxis=dict(tickangle=-35),
        ))
        st.plotly_chart(fig_pub, use_container_width=True)

        _hr()
        # ── Distribusi warna per penerbit ─────────────────────────────────
        st.markdown("**Distribusi Warna per Penerbit**")
        mat_warna_pub = pd.DataFrame(0.0, index=pub_pilih, columns=WARNA_ORDER)
        for p in pub_pilih:
            sub = DF_pub[DF_pub["PUBLISHER"] == p]
            if len(sub) == 0: continue
            vc = compute_warna_distribusi(sub)
            for w in WARNA_ORDER: mat_warna_pub.loc[p, w] = vc.get(w, 0.0)
        fig_wp = go.Figure(data=go.Heatmap(
            z=mat_warna_pub.values, x=WARNA_ORDER, y=pub_pilih,
            colorscale="YlOrRd",
            text=(mat_warna_pub*100).round(1).astype(str)+"%",
            texttemplate="%{text}",
            textfont=dict(size=9,color="#1A1A1A"),
            showscale=True,
        ))
        fig_wp.update_layout(**_pb(max(280, len(pub_pilih)*40),
            margin=dict(l=180,r=20,t=32,b=60),
            yaxis=dict(autorange="reversed"),
        ))
        st.plotly_chart(fig_wp, use_container_width=True)

        _hr()
        # ── Tren terbit per penerbit ─────────────────────────────────────
        st.markdown("**Tren Terbit per Tahun per Penerbit**")
        df_tren_pub = (
            DF_pub[DF_pub["YEAR"].between(2000,2025)]
            .groupby(["YEAR","PUBLISHER"]).size().reset_index(name="n")
        )
        fig_tren_pub = px.line(df_tren_pub, x="YEAR", y="n", color="PUBLISHER", markers=True)
        fig_tren_pub.update_layout(**_pb(320), xaxis_title="Tahun", yaxis_title="Jumlah buku",
                                   legend=dict(orientation="h",y=-.25,font=dict(size=9)))
        st.plotly_chart(fig_tren_pub, use_container_width=True)

        _hr()
        # ── Jelajah per penerbit ─────────────────────────────────────────
        st.markdown("**Jelajah Sampul per Penerbit**")
        pub_jelajah = st.selectbox("Pilih penerbit", pub_pilih, key="pub_jelajah")
        n_pub_show  = st.slider("Tampilkan", 4, 24, 8, 4, key="n_pub_show")
        df_pub_show = D_corak_pub[D_corak_pub["PUBLISHER"] == pub_jelajah]
        grid(df_pub_show.head(n_pub_show), n_cols=4, show_corak=True)


# ══════════════════════════════════════════════════════════════════════════════
# POPULARITAS
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Popularitas":
    st.markdown("## Popularitas & Profil Visual")
    st.markdown(
        "Apakah buku yang paling banyak dirating, direview, atau memiliki nilai tertinggi "
        "memiliki kecenderungan visual tertentu — corak ilustrasi, warna, atau tipografi?"
    )

    # ── Sidebar konfigurasi popularitas ─────────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        st.markdown("**Metrik Popularitas**")
        METRIK_POP = st.selectbox(
            "Gunakan sebagai ukuran popularitas",
            ["TOTAL_RATING","RATING","TOTAL_REVIEW"],
            format_func=lambda x: {
                "TOTAL_RATING":"Jumlah rating (suara)",
                "RATING":"Nilai rating (bintang)",
                "TOTAL_REVIEW":"Jumlah ulasan",
            }[x],
            key="metrik_pop_sel"
        )
        N_TOP_POP = st.slider("Top N populer", 20, 200, 50, 10, key="n_top_pop")
        N_BOT_POP = st.slider("Bottom N kurang populer", 20, 200, 50, 10, key="n_bot_pop")
        MIN_RATING_N = st.slider("Min. jumlah rating untuk diikutkan",
                                 0, 500, 10, 10, key="min_rating_n")
        st.markdown("---")

    # Filter minimum
    DF_pop = DF.dropna(subset=[METRIK_POP]).copy()
    if METRIK_POP == "TOTAL_RATING" and "TOTAL_RATING" in DF_pop.columns:
        DF_pop = DF_pop[DF_pop["TOTAL_RATING"] >= MIN_RATING_N]
    DF_pop = DF_pop.sort_values(METRIK_POP, ascending=False).reset_index(drop=True)

    D_corak_pop = DF_pop[DF_pop["corak_ilustrasi"].notna()].copy()

    metrik_label = {
        "TOTAL_RATING": "Jumlah rating",
        "RATING": "Nilai rating",
        "TOTAL_REVIEW": "Jumlah ulasan",
    }[METRIK_POP]

    st.markdown(f"*Metrik: **{metrik_label}** | Dataset: {len(DF_pop):,} buku (min. {MIN_RATING_N} rating)*")

    # Segmentasi
    df_top, df_mid, df_bot = _segmentasi_popularitas(DF_pop, METRIK_POP, N_TOP_POP, N_BOT_POP)
    D_corak_top = df_top[df_top["corak_ilustrasi"].notna()]
    D_corak_bot = df_bot[df_bot["corak_ilustrasi"].notna()]

    # ── Metrik ringkasan ────────────────────────────────────────────────────
    p1,p2,p3 = st.columns(3)
    p1.metric(f"Top {N_TOP_POP} populer", f"rata-rata {df_top[METRIK_POP].mean():,.0f}")
    p2.metric("Menengah", f"{len(df_mid):,} buku")
    p3.metric(f"Bottom {N_BOT_POP}", f"rata-rata {df_bot[METRIK_POP].mean():,.0f}")
    _hr()

    # ── Distribusi popularitas (scatter) ────────────────────────────────────
    st.markdown("### Distribusi Popularitas & Corak")
    sc1, sc2 = st.columns([2,1])
    with sc1:
        st.markdown("**Scatter: popularitas × tahun**")
        df_sc_pop = D_corak_pop.dropna(subset=["YEAR"]).copy()
        df_sc_pop["corak_label"] = df_sc_pop["corak_ilustrasi"].map(CORAK_ID)
        fig_sc = px.scatter(
            df_sc_pop, x="YEAR", y=METRIK_POP,
            color="corak_label",
            color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID},
            opacity=0.5, size_max=8,
            hover_data=["TITLE","AUTHOR","corak_label"],
            log_y=(METRIK_POP in ["TOTAL_RATING","TOTAL_REVIEW"]),
        )
        fig_sc.update_traces(marker=dict(size=5))
        fig_sc.update_layout(**_pb(360),
                             xaxis_title="Tahun terbit",
                             yaxis_title=metrik_label,
                             legend=dict(orientation="h",y=-.2,font=dict(size=9)))
        st.plotly_chart(fig_sc, use_container_width=True)
    with sc2:
        st.markdown("**Top 10 buku terpopuler**")
        top10 = df_top.head(10)[["TITLE","AUTHOR","YEAR",METRIK_POP,"corak_ilustrasi"]].copy()
        top10["corak_ilustrasi"] = top10["corak_ilustrasi"].map(CORAK_ID).fillna("–")
        top10 = top10.rename(columns={
            "TITLE":"Judul","AUTHOR":"Penulis","YEAR":"Tahun",
            METRIK_POP: metrik_label,"corak_ilustrasi":"Corak"
        })
        st.dataframe(top10, use_container_width=True, hide_index=True)

    _hr()

    # ── Profil visual: populer vs kurang populer ────────────────────────────
    st.markdown("### Profil Visual: Populer vs Kurang Populer")

    tab_corak_pop, tab_warna_pop, tab_tf_pop = st.tabs([
        "🖼️ Corak Ilustrasi", "🎨 Warna", "🔤 Tipografi"
    ])

    with tab_corak_pop:
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown("**Distribusi corak: populer vs kurang populer**")
            st.plotly_chart(
                _chart_diff_corak(
                    D_corak_top, D_corak_bot,
                    label_with=f"Top {N_TOP_POP}",
                    label_without=f"Bottom {N_BOT_POP}",
                    height=320
                ),
                use_container_width=True
            )
        with cc2:
            st.markdown("**Radar profil corak**")
            st.plotly_chart(
                _radar_visual(D_corak_top, pd.DataFrame(), D_corak_bot),
                use_container_width=True
            )
        st.markdown("**Rata-rata popularitas per corak**")
        st.plotly_chart(
            _bar_popularitas_visual(
                D_corak_pop, "corak_ilustrasi", CORAK_ID, METRIK_POP,
                judul=f"Rata-rata {metrik_label} per corak ilustrasi",
                color_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID}
            ),
            use_container_width=True
        )
        st.caption(
            "Catatan: nilai ini adalah korelasi deskriptif, bukan kausal. "
            "Buku populer juga mendapat lebih banyak rating, bukan berarti coraknya "
            "menjadi penyebab popularitas."
        )

    with tab_warna_pop:
        cw1, cw2 = st.columns(2)
        with cw1:
            st.markdown(f"**Warna dominan — Top {N_TOP_POP}**")
            wc_top = compute_warna_distribusi(df_top)
            fig_wt = px.pie(
                values=[wc_top.get(w,0) for w in WARNA_ORDER if wc_top.get(w,0)>0],
                names=[w for w in WARNA_ORDER if wc_top.get(w,0)>0],
                color=[w for w in WARNA_ORDER if wc_top.get(w,0)>0],
                color_discrete_map=WARNA_HEX, hole=0.4
            )
            fig_wt.update_layout(**_pb(280))
            fig_wt.update_traces(textinfo="percent+label",textfont_size=9)
            st.plotly_chart(fig_wt, use_container_width=True)
        with cw2:
            st.markdown(f"**Simpangan warna: Top vs Bottom**")
            wc_bot = compute_warna_distribusi(df_bot)
            diff_w = (pd.Series(wc_top) - pd.Series(wc_bot)).dropna().sort_values(ascending=False)
            fig_wd = px.bar(
                diff_w.reset_index().rename(columns={"index":"warna",0:"delta"}),
                x="delta", y="warna", orientation="h",
                color="warna", color_discrete_map=WARNA_HEX
            )
            fig_wd.update_layout(**_pb(280), showlegend=False,
                                 xaxis_title=f"Selisih proporsi (Top−Bottom)",
                                 yaxis=dict(categoryorder="total ascending"))
            fig_wd.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
            st.plotly_chart(fig_wd, use_container_width=True)
        st.markdown("**Rata-rata popularitas per warna dominan**")
        st.plotly_chart(
            _bar_popularitas_visual(
                DF_pop, "warna_kategori", {w:w for w in WARNA_ORDER}, METRIK_POP,
                judul=f"Rata-rata {metrik_label} per warna dominan",
                color_map=WARNA_HEX
            ),
            use_container_width=True
        )

    with tab_tf_pop:
        DF_pop_tf = DF_pop[DF_pop["typeface_kategori"].isin(TF_ANALISIS)].copy()
        ct1, ct2 = st.columns(2)
        with ct1:
            st.markdown(f"**Tipografi — Top {N_TOP_POP}**")
            tc_top = df_top[df_top["typeface_kategori"].isin(TF_ANALISIS)]["typeface_kategori"].map(TYPEFACE_ID).value_counts()
            fig_tt = px.pie(values=tc_top.values, names=tc_top.index,
                            color=tc_top.index,
                            color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID},
                            hole=0.4)
            fig_tt.update_layout(**_pb(280))
            fig_tt.update_traces(textinfo="percent+label",textfont_size=9)
            st.plotly_chart(fig_tt, use_container_width=True)
        with ct2:
            st.markdown(f"**Simpangan tipografi: Top vs Bottom**")
            tc_bot = df_bot[df_bot["typeface_kategori"].isin(TF_ANALISIS)]["typeface_kategori"].map(TYPEFACE_ID).value_counts()
            if len(tc_top) > 0 and len(tc_bot) > 0:
                diff_tf = (tc_top/tc_top.sum() - tc_bot/tc_bot.sum()).dropna().sort_values(ascending=False)
                fig_tfd = px.bar(
                    diff_tf.reset_index().rename(columns={"index":"tipografi",0:"delta"}),
                    x="delta", y="tipografi", orientation="h",
                    color="tipografi",
                    color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID}
                )
                fig_tfd.update_layout(**_pb(280), showlegend=False,
                                      xaxis_title="Selisih proporsi (Top−Bottom)",
                                      yaxis=dict(categoryorder="total ascending"))
                fig_tfd.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
                st.plotly_chart(fig_tfd, use_container_width=True)
        st.markdown("**Rata-rata popularitas per tipografi**")
        st.plotly_chart(
            _bar_popularitas_visual(
                DF_pop_tf, "typeface_kategori", TYPEFACE_ID, METRIK_POP,
                judul=f"Rata-rata {metrik_label} per tipografi",
                color_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID}
            ),
            use_container_width=True
        )

    _hr()
    # ── Buku terpopuler per corak ────────────────────────────────────────────
    st.markdown("### Top Buku Populer per Corak")
    n_pop_buku = st.slider("Tampilkan per corak", 3, 8, 4, 1, key="n_pop_buku")
    tabs_pop   = st.tabs([f"{CORAK_ICON[k]} {CORAK_ID[k]}" for k in CORAK_ORDER])
    for tab_p, key in zip(tabs_pop, CORAK_ORDER):
        with tab_p:
            sub_p = (D_corak_pop[D_corak_pop["corak_ilustrasi"] == key]
                     .nlargest(n_pop_buku, METRIK_POP))
            st.markdown(f"**{CORAK_ID[key]}** — top {n_pop_buku} berdasarkan {metrik_label}")
            grid(sub_p, n_cols=min(4, n_pop_buku), show_corak=True)


# ══════════════════════════════════════════════════════════════════════════════
# ILLUSTRATOR
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Illustrator":
    st.markdown("## Illustrator Sampul")
    has_ill = DF["ILLUSTRATOR"].ne("")
    n_ill   = has_ill.sum()
    st.markdown(f"**{n_ill:,} buku** dari {len(DF):,} menyebutkan nama illustrator.")

    df_ill = DF[has_ill].copy()
    q_ill  = st.text_input("Cari illustrator atau judul", key="ill_q")
    if q_ill:
        ql     = q_ill.lower()
        df_ill = df_ill[
            df_ill["ILLUSTRATOR"].str.lower().str.contains(ql,na=False) |
            df_ill["TITLE"].str.lower().str.contains(ql,na=False)
        ]

    ill_sum = (
        df_ill.groupby("ILLUSTRATOR").agg(
            Buku  =("TITLE","count"),
            Judul =("TITLE", lambda x: " · ".join(x.values.tolist()[:3])),
            Tahun =("YEAR",  lambda x: ", ".join(sorted({str(int(v)) for v in x if v>0}))),
        ).reset_index().sort_values("Buku", ascending=False)
        .rename(columns={"ILLUSTRATOR":"Illustrator"})
    )
    st.dataframe(ill_sum, use_container_width=True, hide_index=True)

    _hr()
    st.markdown("**Simpangan Corak: Dengan vs Tanpa Illustrator**")
    D_with  = D_corak[D_corak["ILLUSTRATOR"].ne("")]
    D_wout  = D_corak[D_corak["ILLUSTRATOR"].eq("")]
    if len(D_with) > 0 and len(D_wout) > 0:
        st.plotly_chart(
            _chart_diff_corak(D_with, D_wout, height=300),
            use_container_width=True
        )

    _hr()
    st.markdown("**Simpangan Tipografi: Dengan vs Tanpa Illustrator**")
    tf_with = DF[has_ill & DF["typeface_kategori"].isin(TF_ANALISIS)]
    tf_wout = DF[~has_ill & DF["typeface_kategori"].isin(TF_ANALISIS)]
    if len(tf_with) > 0 and len(tf_wout) > 0:
        tc_w  = tf_with["typeface_kategori"].map(TYPEFACE_ID).value_counts()
        tc_o  = tf_wout["typeface_kategori"].map(TYPEFACE_ID).value_counts()
        diff2 = (tc_w/len(tf_with) - tc_o/len(tf_wout)).dropna().sort_values(ascending=False)
        fig2  = px.bar(diff2.reset_index().rename(columns={"index":"tipografi",0:"delta"}),
                       x="delta",y="tipografi",orientation="h",
                       color="tipografi",
                       color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID})
        fig2.update_layout(**_pb(260),showlegend=False,
                           xaxis_title="Selisih proporsi",yaxis_title="",
                           yaxis=dict(categoryorder="total ascending"))
        fig2.add_vline(x=0,line_dash="dash",line_color="rgba(128,128,128,.4)")
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Nilai positif = typeface lebih sering pada buku dengan illustrator bernama.")


# ══════════════════════════════════════════════════════════════════════════════
# JELAJAH BUKU
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Jelajah Buku":
    st.markdown("## Jelajah Buku")
    top25_j = [g for g,_ in _gc.most_common() if g not in GENRE_EXCLUDE][:25]

    with st.form("form_jelajah"):
        r1 = st.columns(4)
        q_j     = r1[0].text_input("Judul / penulis")
        warna_j = r1[1].selectbox("Warna dominan",
                                  ["Semua"]+sorted(DF["warna_kategori"].dropna().unique()))
        corak_j = r1[2].selectbox("Corak ilustrasi",
                                  ["Semua"]+[CORAK_ID[k] for k in CORAK_ORDER])
        tf_j    = r1[3].selectbox("Tipografi", ["Semua"]+[TYPEFACE_ID[k] for k in TF_ANALISIS])
        r2 = st.columns(4)
        genre_j = r2[0].selectbox("Genre", ["Semua"]+top25_j)
        rak_j   = r2[1].selectbox("Rak", ["Semua","Fiksi","Puisi"])
        pub_j   = r2[2].selectbox("Penerbit", ["Semua"]+
                                  [p for p in DF["PUBLISHER"].value_counts().index[:30]
                                   if p != "Tidak Diketahui"])
        ill_j   = r2[3].selectbox("Illustrator", ["Semua","Dengan illustrator"])
        r3 = st.columns([2,1,1])
        min_conf_j = r3[1].slider("Min. confidence corak", 0.0, 1.0, 0.0, 0.05, key="jelajah_conf")
        n_j        = r3[2].slider("Tampilkan", 8, 48, 16, 8)
        st.form_submit_button("🔍 Cari")

    dj = DF.copy()
    if q_j:
        ql = q_j.lower()
        dj = dj[dj["TITLE"].str.lower().str.contains(ql,na=False) |
                dj["AUTHOR"].str.lower().str.contains(ql,na=False)]
    if warna_j != "Semua": dj = dj[dj["warna_kategori"] == warna_j]
    if corak_j != "Semua":
        rev_c = {v:k for k,v in CORAK_ID.items()}
        dj    = dj[dj["corak_ilustrasi"] == rev_c.get(corak_j, corak_j)]
    if tf_j != "Semua":
        rev_tf = {v:k for k,v in TYPEFACE_ID.items()}
        dj     = dj[dj["typeface_kategori"] == rev_tf.get(tf_j, tf_j)]
    if genre_j != "Semua":
        gl_j = expand_genres(dj["GENRES"])
        dj   = dj[[genre_j in gl for gl in gl_j]]
    if rak_j == "Fiksi":   dj = dj[dj["SHELF"] == "fiksi"]
    elif rak_j == "Puisi": dj = dj[dj["SHELF"] == "puisi-asli"]
    if pub_j != "Semua":   dj = dj[dj["PUBLISHER"] == pub_j]
    if ill_j == "Dengan illustrator": dj = dj[dj["ILLUSTRATOR"].ne("")]
    if min_conf_j > 0 and "corak_konfiden" in dj.columns:
        dj = dj[dj["corak_konfiden"] >= min_conf_j]

    st.markdown(f"**{len(dj):,} buku ditemukan**")
    if not dj.empty:
        grid(dj.head(n_j), n_cols=4, show_corak=True)
