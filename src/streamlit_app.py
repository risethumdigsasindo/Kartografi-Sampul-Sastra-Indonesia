"""
Kartografi Sampul Sastra Indonesia (2000–2025)
Versi terpadu — warna · tipografi · ilustrasi (10 corak CLIP) · genre
"""

import os
from collections import Counter
from itertools import combinations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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
# KONSTANTA TIPOGRAFI
# ─────────────────────────────────────────────────────────────────────────────
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
# Urutan tampil dari yang paling banyak ke sedikit (berdasarkan data)
CORAK_ORDER = [
    "kartunal","minimalis","ekspresionisme","fotografi_kolase","abstrak",
    "dekoratif","realisme","surealis_absurd","pop_art","kubisme",
]

# Alias normalisasi untuk parsing nilai CSV
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

# Gaya ilustrasi lama (6 kategori) — tetap dipertahankan untuk tab Ilustrasi Lama
GAYA_ID = {
    "photograph":    "Fotografi",
    "flat_graphic":  "Ilustrasi Digital",
    "hand_drawn":    "Ilustrasi Manual",
    "text_dominant": "Dominan Teks",
    "abstract":      "Abstrak",
    "collage":       "Kolase",
}
GAYA_CLR = {
    "photograph":   "#1E88E5","flat_graphic": "#43A047","hand_drawn":    "#FB8C00",
    "text_dominant":"#E53935","abstract":     "#8E24AA","collage":       "#00ACC1",
}
GAYA_PROB_KEYS = ["photograph","hand_drawn","abstract","flat_graphic","text_dominant"]


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

_base    = os.path.dirname(__file__)
DATA_PATH = os.path.join(_base, "data.csv")
COVER_DIR = os.path.join(_base, "..", "covers")


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
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
            out.append([])
            continue
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
    """Parse format 'label|conf, label|conf' atau 'label:count'"""
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
                try: int(float(parts[1].strip()))
                except: pass
            else:
                raw_label = raw.strip()
            if raw_label:
                label = _terjemahkan_objek(raw_label)
                ctr[label] += 1
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
        clr = CORAK_CLR.get(k, "#999")
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

    # Numerik umum
    for c in ["YEAR","RATING","TOTAL_RATING","TOTAL_REVIEW",
              "brightness_mean","saturation_mean","gaya_skor",
              "teks_coverage","n_region_teks","judul_match_score",
              "yolo_n_objek","detr_objek_n","ocr_confidence","clip_margin"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")

    # Warna
    for i in range(1, 6):
        for s in ["pct","h","s","v"]:
            c = f"warna_{s}_{i}"
            if c in d.columns:
                d[c] = pd.to_numeric(d[c], errors="coerce")

    # CLIP gaya prob
    for c in d.columns:
        if c.startswith("gaya_prob_"):
            d[c] = pd.to_numeric(d[c], errors="coerce")

    # Corak CLIP 10 kategori
    corak_skor_cols = [f"corak_skor_{k}" for k in CORAK_ID]
    for c in corak_skor_cols:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0.0)

    if "corak_konfiden" in d.columns:
        d["corak_konfiden"] = pd.to_numeric(d["corak_konfiden"], errors="coerce").fillna(0.0)

    # Normalisasi corak_ilustrasi → key resmi
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

    # Tipografi
    valid_tf = set(TYPEFACE_ID.keys())
    if "typeface_kategori" in d.columns:
        d["typeface_kategori"] = d["typeface_kategori"].fillna("unknown").astype(str).str.strip()
        d["typeface_kategori"] = d["typeface_kategori"].where(
            d["typeface_kategori"].isin(valid_tf), other="unknown")

    # Gaya ilustrasi lama
    if "gaya_ilustrasi" in d.columns:
        d["gaya_ilustrasi"] = d["gaya_ilustrasi"].where(
            d["gaya_ilustrasi"].astype(str).str.strip().isin(set(GAYA_ID.keys())),
            other=pd.NA)

    # Warna dominan (reklasifikasi dari HSV)
    def _reklasifikasi(row):
        try:
            h = float(row.get("warna_h_1",0) or 0)
            s = float(row.get("warna_s_1",0) or 0)
            v = float(row.get("warna_v_1",0) or 0)
        except: return "putih"
        return _klasifikasi_hsv(h,s,v) or "putih"
    d["warna_kategori"] = d.apply(_reklasifikasi, axis=1)

    # has_person boolean
    if "has_person" in d.columns:
        d["has_person"] = d["has_person"].astype(str).str.upper().isin(["TRUE","1","YES"])
    if "objects_count" in d.columns:
        d["objects_count"] = pd.to_numeric(d["objects_count"], errors="coerce").fillna(0).astype(int)

    return d


# ─────────────────────────────────────────────────────────────────────────────
# BOOK CARDS
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
        year = int(row["YEAR"]) if row.get("YEAR",0) and int(row.get("YEAR",0)) > 0 else "–"
        url   = row.get("URL","")
        title = str(row.get("TITLE","–"))
        title_html = (f'<a href="{url}" target="_blank" style="text-decoration:none;'
                      f'color:inherit;">{title}</a>' if url else title)
        shelf = SHELF_LABEL.get(str(row.get("SHELF","")), "")
        badges = f'<span class="badge">{shelf}</span>' if shelf else ""

        if show_corak:
            corak = str(row.get("corak_ilustrasi","") or "")
            if corak and corak != "nan":
                label  = CORAK_ID.get(corak, corak)
                clr    = CORAK_CLR.get(corak, "#999")
                icon   = CORAK_ICON.get(corak, "🎨")
                conf   = float(row.get("corak_konfiden", 0) or 0)
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
    hov = ("Genre: %{y}<br>Corak: %{x}<br>Proporsi: %{text}<extra></extra>"
           if normalize != "count"
           else "Genre: %{y}<br>Corak: %{x}<br>Jumlah: %{z}<extra></extra>")
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=corak_labels, y=_y_labels(genres),
        colorscale="Greens",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=9,color="#1A1A1A"),
        showscale=True, hovertemplate=hov,
    ))
    fig.update_layout(**_pb(max(380,top_n*32),
        margin=dict(l=210,r=20,t=42,b=100),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickangle=-35),
        xaxis_title="", yaxis_title="",
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
        xaxis_title="", yaxis_title="",
    ))
    return fig


def heatmap_tf_genre(d, top_n=12):
    genres = _top_genres(d, top_n)
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
        xaxis_title="", yaxis_title="",
    ))
    return fig


def heatmap_gaya_genre(d, top_n=12):
    genres    = _top_genres(d, top_n)
    gaya_keys = list(GAYA_ID.keys())
    mat = pd.DataFrame(0.0, index=genres, columns=[GAYA_ID[k] for k in gaya_keys])
    d2  = d[d["gaya_ilustrasi"].notna()]
    genre_lists = expand_genres(d2["GENRES"])
    for g in genres:
        sub = d2[[g in gl for gl in genre_lists]]
        if len(sub) == 0: continue
        vc = sub["gaya_ilustrasi"].map(GAYA_ID).value_counts(normalize=True)
        for k in gaya_keys: mat.loc[g, GAYA_ID[k]] = vc.get(GAYA_ID[k], 0.0)
    text_mat = (mat*100).round(0).astype(int).astype(str)+"%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=[GAYA_ID[k] for k in gaya_keys], y=_y_labels(genres),
        colorscale="Greens",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=9,color="#1A1A1A"),
        showscale=True,
    ))
    fig.update_layout(**_pb(max(340,top_n*28),
        margin=dict(l=180,r=20,t=32,b=60),
        yaxis=dict(autorange="reversed"),
        xaxis_title="", yaxis_title="",
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
        xaxis_title="", yaxis_title="",
        title="% sampul per genre yang mengandung objek",
        shapes=_klaster_shapes(genres),
    ))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# LOAD
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
        "Beranda","Warna","Tipografi","Corak Ilustrasi","Genre","Illustrator","Jelajah Buku"
    ], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Filter Tahun**")
    yr_range = st.slider("Tahun", 2000, 2025, (2000,2025), label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<small>Metode: K-Means HSV · CLIP 10 corak · YOLOv8n · DETR ResNet-50</small>",
                unsafe_allow_html=True)

DF    = df[(df["YEAR"] >= yr_range[0]) & (df["YEAR"] <= yr_range[1])].copy()
_gc   = genre_counts(DF)
_n_unik = len([g for g in _gc if g not in GENRE_EXCLUDE])
DF_tf = DF[DF["typeface_kategori"].isin(TF_ANALISIS)].copy()
D_corak = DF[DF["corak_ilustrasi"].notna()].copy()


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
        ("Total Buku",         len(DF),       "teranalisis",                "#1E88E5"),
        ("Tipografi",          len(DF_tf),    "typeface terklasifikasi",    "#8E24AA"),
        ("Corak Ilustrasi",    len(D_corak),  "terkategorikan (10 corak)",  "#E53935"),
        ("Genre Unik",         _n_unik,       "genre ditemukan",            "#00ACC1"),
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
        fig3 = px.pie(values=[wc[w] for w in names_ord],
                      names=[w for w in names_ord], hole=0.4,
                      color=[w for w in names_ord],
                      color_discrete_map=WARNA_HEX)
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

    _hr()
    st.markdown("**Top Genre**")
    gc_b  = [(g,n) for g,n in _gc.most_common() if g not in GENRE_EXCLUDE and n >= 5]
    n_gr  = st.slider("Top N genre", 10, min(len(gc_b),40), 20, 5, key="beranda_gn")
    df_gb = pd.DataFrame(gc_b[:n_gr], columns=["Genre","Jumlah"])
    fig5  = px.bar(df_gb, x="Jumlah", y="Genre", orientation="h",
                   color_discrete_sequence=["#1E88E5"], text="Jumlah")
    fig5.update_layout(**_pb(max(300,n_gr*26)), showlegend=False,
                       xaxis_title="", yaxis_title="",
                       yaxis=dict(categoryorder="total ascending"))
    fig5.update_traces(textposition="outside", marker_line_width=0)
    st.plotly_chart(fig5, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# WARNA
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Warna":
    st.markdown("## Analisis Warna")
    with st.expander("Cara kerja analisis warna", expanded=False):
        st.markdown(
            "**K-Means Clustering (k=5) pada ruang warna HSV**\n\n"
            "Sampul → 150×150px → BGR→HSV → K-Means k=5 → label warna dari rentang Hue. "
            "Re-klasifikasi otomatis dijalankan saat load data."
        )
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
                        color="warna_kategori",
                        color_discrete_map=WARNA_HEX, opacity=.35,
                        custom_data=["TITLE","AUTHOR","YEAR"])
    fig_sc.update_traces(marker=dict(size=4),
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} · %{customdata[2]}<extra></extra>")
    fig_sc.update_layout(**_pb(300), showlegend=True,
        legend=dict(orientation="h",y=-.18,font=dict(size=10)),
        xaxis_title="Kecerahan (V)", yaxis_title="Saturasi (S)")
    st.plotly_chart(fig_sc, use_container_width=True)

    _hr()
    st.markdown("**Cari Buku berdasarkan Warna**")
    wc1,wc2,wc3 = st.columns([2,2,1])
    with wc1: q_w = st.text_input("Judul / penulis", key="w_q")
    with wc2: w_sel = st.selectbox("Filter warna dominan", ["Semua"]+list(WARNA_HEX.keys()), key="w_sel")
    with wc3: n_w  = st.slider("Tampilkan", 4, 32, 8, 4, key="w_n")
    dw = DF.copy()
    if q_w:
        ql = q_w.lower()
        dw = dw[dw["TITLE"].str.lower().str.contains(ql,na=False) |
                dw["AUTHOR"].str.lower().str.contains(ql,na=False)]
    if w_sel != "Semua": dw = dw[dw["warna_kategori"] == w_sel]
    if not dw.empty: grid(dw.head(n_w))


# ══════════════════════════════════════════════════════════════════════════════
# TIPOGRAFI
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Tipografi":
    st.markdown("## Analisis Tipografi")
    with st.expander("Metodologi tipografi", expanded=False):
        st.markdown(
            "Deteksi font menggunakan **CLIP zero-shot + OCR** dengan 7 kategori typeface. "
            "Nilai *unknown* dikecualikan dari analisis distribusi.\n\n"
            "| Kode | Kategori | Contoh Font |\n|---|---|---|\n"
            "| humanist_serif | Humanist Serif | Garamond, Sabon |\n"
            "| transitional_serif | Transitional Serif | Baskerville, Times |\n"
            "| modern_serif | Modern Serif | Bodoni, Didot |\n"
            "| slab_serif | Slab Serif | Clarendon, Rockwell |\n"
            "| sans_serif | Sans-serif | Helvetica, Futura |\n"
            "| script | Kaligrafi/Script | Pacifico, Dancing Script |\n"
            "| display | Display/Dekoratif | Impact, berbagai display font |"
        )

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

    _hr()
    st.markdown("**Jelajah Buku per Tipografi**")
    tf_options = ["Semua"] + [TYPEFACE_ID[k] for k in TF_ANALISIS]
    tf_j = st.selectbox("Pilih typeface", tf_options, key="tf_sel")
    n_tf_show = st.slider("Tampilkan", 4, 32, 8, 4, key="n_tf_show")
    d_tf_show = DF_tf.copy()
    if tf_j != "Semua":
        tf_rev = {v:k for k,v in TYPEFACE_ID.items()}
        d_tf_show = d_tf_show[d_tf_show["typeface_kategori"] == tf_rev.get(tf_j, tf_j)]
    if not d_tf_show.empty:
        grid(d_tf_show.head(n_tf_show))


# ══════════════════════════════════════════════════════════════════════════════
# CORAK ILUSTRASI (10 KATEGORI CLIP)
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Corak Ilustrasi":
    st.markdown("## Analisis Corak Ilustrasi")
    st.caption("CLIP zero-shot 10 kategori: realisme · dekoratif · kartunal · ekspresionisme · "
               "surealis/absurd · pop art · kubisme · abstrak · minimalis · fotografi/kolase")

    with st.expander("Metodologi CLIP 10 corak", expanded=False):
        st.markdown(
            "Setiap sampul dianalisis menggunakan **CLIP zero-shot classification** dengan prompt multi-bahasa "
            "per kategori. Skor tiap prompt diagregasikan melalui **multi-prompt voting**. "
            "Hasilnya adalah distribusi probabilistik, bukan label mutlak.\n\n"
            "- **Metode `voting`**: skor tertinggi dari seluruh prompt dipilih\n"
            "- **Metode `hierarki_fallback`**: fallback ke kategori induk bila confidence rendah\n"
            f"- **Threshold ambigu**: confidence < 0.22"
        )

    # Metrik ringkasan
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Total terkategorikan", f"{len(D_corak):,}")
    m2.metric("Dari total buku", f"{len(D_corak)/len(DF)*100:.1f}%")
    m3.metric("Rata-rata confidence", f"{D_corak['corak_konfiden'].mean():.3f}")
    m4.metric("Ambigu < 0.22", f"{(D_corak['corak_konfiden'] < 0.22).sum():,}")

    _hr()

    # Kartu 10 corak
    st.markdown("### Sepuluh Corak Ilustrasi")
    for row_keys in [CORAK_ORDER[:5], CORAK_ORDER[5:]]:
        cols = st.columns(5)
        for col, key in zip(cols, row_keys):
            n = int((D_corak["corak_ilustrasi"] == key).sum())
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
    st.markdown("### Distribusi & Tren")
    ca, cb = st.columns(2)
    with ca:
        st.markdown("**Distribusi Corak Keseluruhan**")
        vc = D_corak["corak_ilustrasi"].value_counts()
        labels = [CORAK_ID.get(k,k) for k in vc.index]
        fig = px.bar(x=vc.values, y=labels, orientation="h",
                     color=labels,
                     color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID},
                     text=vc.values)
        fig.update_layout(**_pb(330), showlegend=False, xaxis_title="Jumlah sampul",
                          yaxis_title="", yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    with cb:
        st.markdown("**Tren Corak per Tahun**")
        dyear = D_corak[D_corak["YEAR"]>0].copy()
        dyear["corak_label"] = dyear["corak_ilustrasi"].map(CORAK_ID)
        tr = dyear.groupby(["YEAR","corak_label"]).size().reset_index(name="n")
        fig2 = px.bar(tr, x="YEAR", y="n", color="corak_label", barmode="stack",
                      color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID})
        fig2.update_layout(**_pb(330), xaxis_title="", yaxis_title="Jumlah",
                           legend=dict(orientation="h",y=-.25,font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)

    _hr()
    st.markdown("### Heatmap Corak × Genre")
    st.caption("Genre diurutkan berdasarkan klaster K1 → K2 → K3.")
    h1,h2,h3 = st.columns([1,1,1])
    with h1: n_genre = st.slider("Jumlah genre", 6, 30, 16, 2, key="hm_corak_genre_n")
    with h2: min_count = st.slider("Min. buku per genre", 1, 20, 3, 1, key="hm_corak_min")
    with h3: norm_mode = st.selectbox("Mode nilai", ["Persentase","Jumlah"], key="hm_corak_mode")
    st.plotly_chart(
        heatmap_corak_genre(D_corak, top_n=n_genre, min_count=min_count,
                            normalize="count" if norm_mode=="Jumlah" else "index"),
        use_container_width=True
    )

    _hr()
    st.markdown("### Pemeriksaan Confidence")
    qc1, qc2 = st.columns(2)
    with qc1:
        st.markdown("**Sebaran Confidence per Corak**")
        tmp = D_corak.copy()
        tmp["corak_label"] = tmp["corak_ilustrasi"].map(CORAK_ID)
        fig_box = px.box(tmp, x="corak_label", y="corak_konfiden", color="corak_label",
                         color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID},
                         points="outliers")
        fig_box.update_layout(**_pb(330), showlegend=False, xaxis_title="",
                              yaxis_title="Confidence", xaxis=dict(tickangle=-35))
        st.plotly_chart(fig_box, use_container_width=True)
    with qc2:
        st.markdown("**Kasus Ambigu (confidence < 0.22) per Corak**")
        amb = D_corak[D_corak["corak_konfiden"] < 0.22]["corak_ilustrasi"].value_counts()
        if amb.empty:
            st.success("Tidak ada kasus di bawah threshold 0.22.")
        else:
            fig_amb = px.bar(x=amb.values, y=[CORAK_ID.get(k,k) for k in amb.index],
                             orientation="h", color=[CORAK_ID.get(k,k) for k in amb.index],
                             color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID},
                             text=amb.values)
            fig_amb.update_layout(**_pb(330), showlegend=False, xaxis_title="Jumlah",
                                  yaxis_title="", yaxis=dict(categoryorder="total ascending"))
            fig_amb.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_amb, use_container_width=True)

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
    st.markdown("### Objek Terdeteksi dalam Sampul")
    obj_col = None
    for c in ["objects_detected","detected_objects","yolo_objek","yolo_objects"]:
        if c in D_corak.columns:
            obj_col = c; break
    if obj_col is None:
        st.warning("Kolom objek tidak ditemukan.")
    else:
        co, ch = st.columns([1,2])
        with co:
            n_has_obj = int((D_corak.get("objects_count",pd.Series(dtype=int)) > 0).sum())
            st.metric("Sampul dengan objek terdeteksi", f"{n_has_obj:,}")
            if "has_person" in D_corak.columns:
                st.metric("Mengandung figur manusia",
                          f"{int(D_corak['has_person'].sum()):,}")
        with ch:
            ctr = _parse_objects_detected(D_corak[obj_col])
            if ctr:
                top_obj = pd.DataFrame(ctr.most_common(15), columns=["Objek","Frekuensi"])
                fig_obj = px.bar(top_obj, x="Frekuensi", y="Objek", orientation="h",
                                 color="Frekuensi", color_continuous_scale="YlOrRd",
                                 text="Frekuensi")
                fig_obj.update_layout(**_pb(300), coloraxis_showscale=False,
                                      xaxis_title="Frekuensi deteksi",
                                      yaxis_title="", yaxis=dict(categoryorder="total ascending"))
                fig_obj.update_traces(textposition="outside", marker_line_width=0)
                st.plotly_chart(fig_obj, use_container_width=True)

        st.markdown("**Heatmap Objek × Genre**")
        ho1,ho2 = st.columns(2)
        with ho1: n_obj  = st.slider("Jumlah objek",  10, 40, 20, 5, key="hm_obj_n")
        with ho2: n_gobj = st.slider("Jumlah genre", 8, 30, 16, 2, key="hm_obj_g")
        fig_og = heatmap_objek_genre(D_corak, obj_col, top_n_obj=n_obj, top_n_genre=n_gobj)
        if fig_og is not None:
            st.plotly_chart(fig_og, use_container_width=True)
        else:
            st.info("Data objek tidak cukup untuk heatmap.")

    _hr()
    st.markdown("### Dengan vs Tanpa Nama Illustrator")
    has_ill = D_corak["ILLUSTRATOR"].fillna("").astype(str).str.strip().ne("")
    n_ill, n_no = int(has_ill.sum()), int((~has_ill).sum())
    ci1,ci2,ci3 = st.columns(3)
    ci1.metric("Dengan illustrator", f"{n_ill:,}")
    ci2.metric("Tanpa illustrator", f"{n_no:,}")
    ci3.metric("Proporsi dengan illustrator", f"{n_ill/len(D_corak)*100:.1f}%" if len(D_corak) else "–")
    if n_ill > 0 and n_no > 0:
        vc_w = D_corak[has_ill]["corak_ilustrasi"].value_counts(normalize=True)
        vc_o = D_corak[~has_ill]["corak_ilustrasi"].value_counts(normalize=True)
        diff = (vc_w - vc_o).dropna().sort_values(ascending=False)
        df_diff = pd.DataFrame({"corak":[CORAK_ID.get(k,k) for k in diff.index], "delta":diff.values})
        fig_diff = px.bar(df_diff, x="delta", y="corak", orientation="h",
                          color="corak",
                          color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID})
        fig_diff.update_layout(**_pb(300), showlegend=False, xaxis_title="Selisih proporsi",
                               yaxis_title="", yaxis=dict(categoryorder="total ascending"))
        fig_diff.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
        st.plotly_chart(fig_diff, use_container_width=True)
        st.caption("Nilai positif = corak lebih sering pada buku dengan nama illustrator.")

    _hr()
    st.markdown("### Jelajah Sampul berdasarkan Corak")
    genre_opts = [g for g,c in _gc.most_common() if g not in GENRE_EXCLUDE and c >= 3][:40]
    f1,f2,f3,f4 = st.columns([2,2,2,1])
    with f1: q_js = st.text_input("Judul / penulis", key="corak_q")
    with f2: corak_sel = st.selectbox("Corak", ["Semua"]+[CORAK_ID[k] for k in CORAK_ORDER], key="corak_sel")
    with f3: genre_sel = st.selectbox("Genre", ["Semua"]+genre_opts, key="corak_genre_sel")
    with f4: n_show = st.slider("Tampilkan", 4, 40, 12, 4, key="corak_n_show")
    f5,f6,f7 = st.columns([1,1,1])
    with f5: only_person = st.checkbox("Ada figur manusia", key="corak_person")
    with f6: min_conf_js = st.slider("Min. confidence", 0.0, 1.0, 0.0, 0.05, key="corak_min_conf")
    with f7: show_probs_s = st.checkbox("Skor semua corak", key="corak_show_probs")

    DS = D_corak.copy()
    if q_js:
        ql = q_js.lower()
        mask = False
        if "TITLE" in DS.columns: mask = DS["TITLE"].astype(str).str.lower().str.contains(ql,na=False)
        if "AUTHOR" in DS.columns: mask = mask | DS["AUTHOR"].astype(str).str.lower().str.contains(ql,na=False)
        DS = DS[mask]
    if corak_sel != "Semua":
        rev = {v:k for k,v in CORAK_ID.items()}
        DS  = DS[DS["corak_ilustrasi"] == rev.get(corak_sel,corak_sel)]
    if genre_sel != "Semua" and "GENRES" in DS.columns:
        gl = expand_genres(DS["GENRES"])
        DS = DS[[genre_sel in x for x in gl]]
    if only_person and "has_person" in DS.columns:
        DS = DS[DS["has_person"].astype(bool)]
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
    with st.expander("Catatan metodologi", expanded=False):
        st.markdown(
            f"Genre dari metadata Goodreads (multi-label). **{_n_unik} genre unik** setelah normalisasi.\n\n"
            "**Normalisasi:** Cinta/Roman → Romansa · Thriller/Misteri → Thriller/Misteri\n\n"
            "Genre *Sastra Indonesia*, *Fiksi*, *Sastra* dikecualikan dari visualisasi."
        )

    all_items = [(g,n) for g,n in _gc.most_common() if g not in GENRE_EXCLUDE and n >= 3]
    top_co = [g for g,_ in all_items[:16]]

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
    st.markdown("**Peta Panas Tumpang Tindih Genre**")
    n_co = st.slider("Jumlah genre", 8, min(len(all_items),30), 16, 2, key="n_co")
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
        if df_gs.empty:
            st.info(f"Tidak ada buku genre *{sel_genre}*.")
        else:
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
                    diff = (wc_g-wc_all).dropna().sort_values(ascending=False)
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
                if df_gs_tf.empty:
                    st.info("Belum ada data tipografi untuk genre ini.")
                else:
                    tc_g    = df_gs_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts()
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
                if D_gs.empty:
                    st.info("Belum ada data corak untuk genre ini.")
                else:
                    vc_corak_g   = D_gs["corak_ilustrasi"].value_counts(normalize=True)
                    vc_corak_all = D_corak["corak_ilustrasi"].value_counts(normalize=True)
                    cc1,cc2 = st.columns(2)
                    with cc1:
                        fig = px.pie(
                            values=vc_corak_g.values,
                            names=[CORAK_ID.get(k,k) for k in vc_corak_g.index],
                            hole=0.42,
                            color=[CORAK_ID.get(k,k) for k in vc_corak_g.index],
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
# ILLUSTRATOR
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Illustrator":
    st.markdown("## Illustrator Sampul")
    has_ill = DF["ILLUSTRATOR"].ne("")
    n_ill   = has_ill.sum()
    st.markdown(f"**{n_ill} buku** dari {len(DF):,} menyebutkan nama illustrator.")
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
            Buku   =("TITLE","count"),
            Judul  =("TITLE", lambda x: " · ".join(x.values.tolist()[:3])),
            Tahun  =("YEAR",  lambda x: ", ".join(sorted({str(int(v)) for v in x if v>0}))),
        ).reset_index().sort_values("Buku", ascending=False)
        .rename(columns={"ILLUSTRATOR":"Illustrator"})
    )
    st.dataframe(ill_sum, use_container_width=True, hide_index=True)

    _hr()
    st.markdown("**Simpangan Corak: Dengan vs Tanpa Illustrator**")
    D_with  = D_corak[D_corak["ILLUSTRATOR"].ne("")]
    D_wout  = D_corak[D_corak["ILLUSTRATOR"].eq("")]
    if len(D_with) > 0 and len(D_wout) > 0:
        vc_w = D_with["corak_ilustrasi"].value_counts(normalize=True)
        vc_o = D_wout["corak_ilustrasi"].value_counts(normalize=True)
        diff = (vc_w - vc_o).dropna().sort_values(ascending=False)
        df_diff = pd.DataFrame({"corak":[CORAK_ID.get(k,k) for k in diff.index],"delta":diff.values})
        fig = px.bar(df_diff, x="delta", y="corak", orientation="h",
                     color="corak",
                     color_discrete_map={CORAK_ID[k]:CORAK_CLR[k] for k in CORAK_ID})
        fig.update_layout(**_pb(280),showlegend=False,
                          xaxis_title="Selisih proporsi",yaxis_title="",
                          yaxis=dict(categoryorder="total ascending"))
        fig.add_vline(x=0,line_dash="dash",line_color="rgba(128,128,128,.4)")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Nilai positif = corak lebih sering pada buku dengan nama illustrator.")

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
    st.markdown("Temukan buku dari kombinasi kriteria visual dan metadata.")
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
        ill_j   = r2[2].selectbox("Illustrator", ["Semua","Dengan illustrator"])
        man_j   = r2[3].checkbox("Ada figur manusia")
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
    if ill_j == "Dengan illustrator": dj = dj[dj["ILLUSTRATOR"].ne("")]
    if man_j and "has_person" in dj.columns:
        dj = dj[dj["has_person"].astype(bool)]
    if min_conf_j > 0 and "corak_konfiden" in dj.columns:
        dj = dj[dj["corak_konfiden"] >= min_conf_j]

    st.markdown(f"**{len(dj):,} buku ditemukan**")
    if not dj.empty:
        grid(dj.head(n_j), n_cols=4, show_corak=True)
