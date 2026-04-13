"""Kartografi Sampul Sastra Indonesia (2000-2025)"""
import io
import os
from collections import Counter
from itertools import combinations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from ilustrasi_komparatif import render_ilustrasi_komparatif

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
.cooc-table{width:100%;border-collapse:collapse;font-size:12px;font-family:'Inter',sans-serif;}
.cooc-table th{background:#2E4057;color:white;font-weight:600;padding:7px 10px;text-align:center;font-size:11px;border:1px solid #ccc;}
.cooc-table th:first-child,.cooc-table th:nth-child(2){text-align:left;}
.cooc-table td{padding:6px 10px;border:1px solid #E0E0E0;}
.cooc-table td:nth-child(n+3){text-align:center;}
.cooc-table tr.cluster-row td{font-style:italic;font-weight:600;font-size:11px;letter-spacing:.03em;padding:8px 10px 5px;}
.cooc-table tr:not(.cluster-row):nth-child(even) td{background:#F7F9FB;}
.cooc-table tr:not(.cluster-row):nth-child(odd) td{background:#FFFFFF;}
.pill-cooc{display:inline-block;padding:1px 8px;border-radius:10px;font-weight:700;font-size:11px;}
.warna-legend-item{display:flex;align-items:center;gap:6px;font-size:12px;padding:4px 0;}
.warna-dot{width:12px;height:12px;border-radius:3px;flex-shrink:0;}
</style>""", unsafe_allow_html=True)

# ── KONSTANTA WARNA ───────────────────────────────────────────────────────────
WARNA_HEX = {
    "putih":"#F5F5F0","hitam":"#1A1A1A","abu":"#8E8E93","merah":"#E53935",
    "pink":"#F06292","oranye":"#FB8C00","cokelat":"#795548","kuning":"#FDD835",
    "hijau":"#43A047","biru":"#1E88E5","ungu":"#8E24AA",
}
WARNA_TXT = {
    "putih":"#333","hitam":"#eee","abu":"#fff","merah":"#fff","pink":"#fff",
    "oranye":"#fff","cokelat":"#fff","kuning":"#333","hijau":"#fff","biru":"#fff","ungu":"#fff",
}
WARNA_ORDER = ["putih","oranye","cokelat","biru","merah","pink","hitam","kuning","ungu","hijau","abu"]

# ── KONSTANTA TIPOGRAFI ───────────────────────────────────────────────────────
TYPEFACE_ID = {
    "humanist_serif":     "Humanist Serif",
    "transitional_serif": "Transitional Serif",
    "modern_serif":       "Modern Serif",
    "slab_serif":         "Slab Serif",
    "sans_serif":         "Sans-serif",
    "script":             "Kaligrafi/Script",
    "display":            "Display/Dekoratif",
}
TYPEFACE_CLR = {
    "humanist_serif":"#5C6BC0","transitional_serif":"#7E57C2","modern_serif":"#AB47BC",
    "slab_serif":"#EC407A","sans_serif":"#42A5F5","script":"#26A69A","display":"#FFA726",
}
TYPEFACE_FONT = {
    "humanist_serif":"Georgia,serif","transitional_serif":"'Times New Roman',serif",
    "modern_serif":"'Playfair Display',Georgia,serif","slab_serif":"'Courier New',monospace",
    "sans_serif":"Helvetica,Arial,sans-serif","script":"cursive","display":"Impact,fantasy",
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

# ── KONSTANTA ILUSTRASI ───────────────────────────────────────────────────────
GAYA_ID = {
    "photograph":"Fotografi","flat_graphic":"Ilustrasi Datar","hand_drawn":"Gambar Tangan",
    "text_dominant":"Dominan Teks","abstract":"Abstrak","collage":"Kolase",
}
GAYA_CLR = {
    "photograph":"#1E88E5","flat_graphic":"#43A047","hand_drawn":"#FB8C00",
    "text_dominant":"#E53935","abstract":"#8E24AA","collage":"#00ACC1",
}
GAYA_ICON = {
    "photograph":"📷","flat_graphic":"🎨","hand_drawn":"✏️",
    "text_dominant":"🔤","abstract":"🔷","collage":"🗂️",
}
GAYA_DESC = {
    "photograph":"Gambar fotografis realistis.",
    "flat_graphic":"Flat design: warna solid, bentuk geometris.",
    "hand_drawn":"Sketsa, cat air, ilustrasi ekspresif.",
    "text_dominant":"Teks mendominasi elemen visual.",
    "abstract":"Bentuk non-representasional, pola, tekstur.",
    "collage":"Gabungan foto, ilustrasi, teks dari berbagai sumber.",
}
GAYA_PROB_KEYS = ["photograph","hand_drawn","abstract","flat_graphic","text_dominant"]
SHELF_LABEL = {"fiksi":"Fiksi","puisi-asli":"Puisi"}
GENRE_NORM = {
    "Sastra":"Sastra Indonesia","Cinta":"Romansa","Roman":"Romansa",
    "Romansa Kontemporer":"Romansa","Kontemporer":"Romansa",
    "Thriller":"Thriller/Misteri","Misteri":"Thriller/Misteri",
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
        "genres":["Romansa","Chick Lit","Persahabatan","Remaja","Dewasa","Keluarga",
                  "Drama","Slice of Life","Komedi"],
        "pairs":[("Chick Lit","Romansa"),("Persahabatan","Romansa"),("Remaja","Romansa"),
                 ("Dewasa","Romansa"),("Keluarga","Romansa"),("Drama","Romansa")],
    },
    {
        "id":"K3","label":"Klaster 3 — Eskapisme: fantasi, aksi & ketegangan",
        "short":"Klaster 3","color":"#1D9E75","bg":"#EEF8F4",
        "genres":["Fantasi","Fiksi Sejarah","Petualangan","Aksi","Fiksi Sains",
                  "Thriller/Misteri","Horor","Anak-anak"],
        "pairs":[("Fantasi","Fiksi Sains"),("Fantasi","Petualangan"),("Aksi","Fantasi"),
                 ("Aksi","Petualangan"),("Horor","Thriller/Misteri"),("Fiksi Sejarah","Novel")],
    },
]
GENRE_KLASTER_MAP = {}
for kl in KLASTER_COOC:
    for g in kl["genres"]:
        if g not in GENRE_KLASTER_MAP:
            GENRE_KLASTER_MAP[g] = kl

def _pill_color(pct):
    if pct >= 80: return "#FADADD","#922B21"
    if pct >= 56: return "#FDEBD0","#784212"
    if pct >= 40: return "#D6EAF8","#1A5276"
    if pct >= 20: return "#D5F5E3","#1E8449"
    return "#F0F0F0","#555555"

_v2_path = os.path.join(os.path.dirname(__file__), "data_final_v2.csv")
_v1_path = os.path.join(os.path.dirname(__file__), "data.csv")
DATA_PATH = _v2_path if os.path.exists(_v2_path) else _v1_path
COVER_DIR = os.path.join(os.path.dirname(__file__), "..", "covers")

# ── FUNGSI TIPOGRAFI v3 ───────────────────────────────────────────────────────

def redistribute_tidak_terklasifikasi(df_input):
    """
    Distribusikan 'tidak_terklasifikasi' ke kategori lain berdasarkan
    vektor probabilitas per buku (typeface_prob_*).
    Return: (proportions Series, n_classified, n_unclassified)
    """
    tf_keys = list(TYPEFACE_ID.keys())
    df_cl  = df_input[df_input["typeface_kategori"].isin(tf_keys)].copy()
    df_unc = df_input[df_input["typeface_kategori"] == "tidak_terklasifikasi"].copy()
    n_cl, n_unc = len(df_cl), len(df_unc)
    n_total = len(df_input)

    base = {k: float(df_cl["typeface_kategori"].value_counts().get(k, 0)) for k in tf_keys}
    prob_cols = {k: f"typeface_prob_{k}" for k in tf_keys}
    avail = {k: c for k, c in prob_cols.items() if c in df_unc.columns}

    for _, row in df_unc.iterrows():
        if avail:
            probs = {k: float(row.get(c, 0) or 0) for k, c in avail.items()}
            total_p = sum(probs.values())
            if total_p > 0.01:
                for k, p in probs.items():
                    base[k] += p / total_p
            else:
                for k in tf_keys:
                    base[k] += 1.0 / len(tf_keys)
        else:
            for k in tf_keys:
                base[k] += 1.0 / len(tf_keys)

    total = sum(base.values())
    props = {k: v/total for k, v in base.items()} if total > 0 else {k: 1/len(tf_keys) for k in tf_keys}
    return pd.Series(props), n_cl, n_unc


def get_typeface_metode_breakdown(df_input):
    if "typeface_metode" not in df_input.columns:
        return pd.Series(dtype=float)
    return df_input["typeface_metode"].value_counts()


def get_typeface_confidence_stats(df_input):
    if "typeface_confidence" not in df_input.columns:
        return None
    return df_input[
        df_input["typeface_kategori"].isin(TYPEFACE_ID.keys()) &
        df_input["typeface_confidence"].notna()
    ].copy()


# ── KLASIFIKASI WARNA ────────────────────────────────────────────────────────
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
            try: pct = float(pct or 0)
            except Exception: pct = 0.0
            if pct <= 0: continue
            kategori = _klasifikasi_hsv(
                row.get(f"warna_h_{i}", 0), row.get(f"warna_s_{i}", 0), row.get(f"warna_v_{i}", 0)
            )
            if kategori and kategori in acc:
                acc[kategori] += pct
    total = sum(acc.values())
    if total > 0:
        acc = {k: v/total for k, v in acc.items()}
    return pd.Series(acc)


@st.cache_data(show_spinner=False)
def load_data(path):
    d = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    d = d[d["SHELF"].isin(["fiksi","puisi-asli"])].copy()
    num_cols = ["YEAR","RATING","TOTAL_RATING","TOTAL_REVIEW",
                "brightness_mean","saturation_mean","typeface_skor",
                "gaya_skor","teks_coverage","n_region_teks","judul_match_score",
                "yolo_n_objek","detr_objek_n","typeface_confidence"]
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

    # Tipografi: normalisasi unclassified → tidak_terklasifikasi
    if "typeface_kategori" in d.columns:
        d["typeface_kategori"] = d["typeface_kategori"].fillna("tidak_terklasifikasi")
        d["typeface_kategori"] = d["typeface_kategori"].astype(str).str.strip()
        d["typeface_kategori"] = d["typeface_kategori"].replace({"unclassified":"tidak_terklasifikasi"})
        valid_tf = set(TYPEFACE_ID.keys()) | {"tidak_terklasifikasi"}
        d["typeface_kategori"] = d["typeface_kategori"].where(
            d["typeface_kategori"].isin(valid_tf), other="tidak_terklasifikasi"
        )

    if "gaya_ilustrasi" in d.columns:
        d["gaya_ilustrasi"] = d["gaya_ilustrasi"].where(
            d["gaya_ilustrasi"].astype(str).str.strip().isin(set(GAYA_ID.keys())), other=pd.NA
        )
    d["warna_kategori"] = d.apply(_reklasifikasi_warna, axis=1)
    return d

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
    top = {g for g, c in freq.items() if c >= min_count}
    counts, cooc = {}, Counter()
    for gl in genre_lists:
        gl_top = [g for g in gl if g in top]
        for g in gl_top: counts[g] = counts.get(g, 0) + 1
        for a, b in combinations(sorted(gl_top), 2): cooc[(a, b)] += 1
    rows = []
    for (a, b), ov in cooc.items():
        ca, cb = counts.get(a, 0), counts.get(b, 0)
        pct = round(ov / min(ca, cb) * 100)
        rows.append({"g1":a,"g2":b,"ca":ca,"cb":cb,"ov":ov,"pct":pct})
    return pd.DataFrame(rows).sort_values("pct", ascending=False), counts


def render_cooc_table(cooc_df, counts):
    lookup = {}
    for _, r in cooc_df.iterrows():
        lookup[(r["g1"],r["g2"])] = r
        lookup[(r["g2"],r["g1"])] = r
    def _lookup(g1, g2):
        r = lookup.get((g1,g2))
        return r if r is not None else lookup.get((g2,g1))
    puisi_pairs = [("Puisi","Sastra"),("Puisi","Romansa"),("Puisi","Novel")]
    html = """<table class="cooc-table"><thead><tr>
      <th>Genre 1</th><th>Genre 2</th>
      <th>N Genre 1</th><th>N Genre 2</th>
      <th>Overlap</th><th>Overlap %</th>
    </tr></thead><tbody>"""
    for kl in KLASTER_COOC:
        html += (f'<tr class="cluster-row"><td colspan="6" style="background:{kl["bg"]};color:{kl["color"]};">'
                 f'{kl["label"]}</td></tr>\n')
        for pair in kl["pairs"]:
            if len(pair) < 2: continue
            g1, g2 = pair[0], pair[1]
            r = _lookup(g1, g2)
            if r is None: continue
            pct = int(r["pct"])
            bg, fg = _pill_color(pct)
            n1 = f"{int(r['ca']):,}".replace(",",".")
            n2 = f"{int(r['cb']):,}".replace(",",".")
            ov = f"{int(r['ov']):,}".replace(",",".")
            html += (f"<tr><td><strong>{g1}</strong></td><td><strong>{g2}</strong></td>"
                     f"<td>{n1}</td><td>{n2}</td><td>{ov}</td>"
                     f"<td><span class='pill-cooc' style='background:{bg};color:{fg};'>{pct}%</span></td></tr>\n")
    html += ('<tr class="cluster-row"><td colspan="6" style="background:#F0F4F0;color:#3A5A3A;">'
             "Catatan — Puisi sebagai anomali struktural</td></tr>\n")
    for g1, g2 in puisi_pairs:
        r = _lookup(g1, g2)
        if r is None: continue
        pct = int(r["pct"])
        bg, fg = _pill_color(pct)
        n1 = f"{int(r['ca']):,}".replace(",",".")
        n2 = f"{int(r['cb']):,}".replace(",",".")
        ov = f"{int(r['ov']):,}".replace(",",".")
        html += (f"<tr><td><strong>{g1}</strong></td><td><strong>{g2}</strong></td>"
                 f"<td>{n1}</td><td>{n2}</td><td>{ov}</td>"
                 f"<td><span class='pill-cooc' style='background:{bg};color:{fg};'>{pct}%</span></td></tr>\n")
    html += "</tbody></table>"
    legend = "<div style='display:flex;gap:12px;flex-wrap:wrap;margin-top:10px;font-size:11px;'>"
    for label, pct_s in [("≥80% sangat tinggi",90),("56–79% tinggi",65),("40–55% sedang",45),("≤23% rendah",10)]:
        bg, fg = _pill_color(pct_s)
        legend += (f"<span><span class='pill-cooc' style='background:{bg};color:{fg};font-size:10px;'>"
                   f"{label.split()[0]}</span> {' '.join(label.split()[1:])}</span>")
    legend += "</div>"
    st.markdown(html + legend, unsafe_allow_html=True)


with st.spinner("Memuat data..."):
    df = load_data(DATA_PATH)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def cover_path(img):
    if not img or str(img) in ("","nan"): return None
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
                    if g2 not in seen: normed.append(g2); seen.add(g2)
                out.append(normed)
            else:
                out.append(raw)
    return out

def genre_counts(d, normalize=True):
    c = Counter()
    for gl in expand_genres(d["GENRES"], normalize=normalize): c.update(gl)
    return c

def pb(height=320, **kw):
    b = dict(height=height, margin=dict(l=8,r=8,t=28,b=8),
             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
             font=dict(size=11, color="#1A1A1A"))
    b.update(kw)
    return b

def _nama_warna(hex_str):
    try:
        h = hex_str.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    except Exception:
        return hex_str
    best, best_d = "lainnya", float("inf")
    for nama, hx in WARNA_HEX.items():
        try:
            hh = hx.lstrip("#")
            rr, gg, bb = int(hh[0:2],16), int(hh[2:4],16), int(hh[4:6],16)
            dist = (r-rr)**2 + (g-gg)**2 + (b-bb)**2
            if dist < best_d: best, best_d = nama, dist
        except Exception: pass
    return best

def palette_html(row, n=5):
    parts, total = [], 0.0
    for i in range(1, n+1):
        hx = str(row.get(f"warna_hex_{i}","") or "").strip()
        pct = row.get(f"warna_pct_{i}", 0)
        try: pct = float(pct)
        except Exception: pct = 0.0
        if not hx or hx in ("nan",""): continue
        if not hx.startswith("#"): hx = "#" + hx
        nama = _nama_warna(hx)
        parts.append((hx, pct, nama)); total += pct
    if not parts: return ""
    scale = 100.0/total if total > 0 else 1.0
    sw = "".join(
        f'<div class="pal-sw" style="background:{hx};width:{pct*scale:.1f}%;" title="{nama} ({pct:.1f}%)"></div>'
        for hx, pct, nama in parts
    )
    return f'<div class="pal-row">{sw}</div>'

def prob_bars(probs_dict, colors_dict, label_map):
    html = ""
    for key, val in sorted(probs_dict.items(), key=lambda x: -x[1]):
        label = label_map.get(key, key)
        clr = colors_dict.get(key, "#999")
        pct = val * 100
        html += (f'<div class="prob-bar-wrap"><div class="prob-label"><span>{label}</span>'
                 f'<span>{pct:.1f}%</span></div><div class="prob-bar-bg">'
                 f'<div class="prob-bar-fill" style="width:{pct:.1f}%;background:{clr};"></div>'
                 f"</div></div>")
    return html

def book_card(row, col_obj, show_tf=False, show_gi=False):
    with col_obj:
        cp = cover_path(row.get("IMAGE_FILE"))
        if cp:
            st.image(cp, use_container_width=True)
        else:
            st.markdown('<div style="height:160px;background:rgba(128,128,128,.09);border-radius:8px 8px 0 0;'
                        'display:flex;align-items:center;justify-content:center;font-size:2rem">📖</div>',
                        unsafe_allow_html=True)
        year = int(row["YEAR"]) if row.get("YEAR",0) and int(row.get("YEAR",0)) > 0 else "–"
        url = row.get("URL","")
        title = str(row.get("TITLE","–"))
        title_html = (f'<a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">{title}</a>'
                      if url else title)
        shelf_lbl = SHELF_LABEL.get(str(row.get("SHELF","")), str(row.get("SHELF","")))
        badges = f'<span class="badge">{shelf_lbl}</span>'
        tf_bars = gi_bars = ""
        if show_tf and row.get("typeface_kategori") in TYPEFACE_ID:
            tk = str(row["typeface_kategori"])
            clr = TYPEFACE_CLR.get(tk, "#999")
            conf_col = "typeface_confidence" if "typeface_confidence" in row.index else "typeface_skor"
            try: sc = f"{float(row.get(conf_col,0)):.2f}"
            except Exception: sc = "–"
            badges += f'<span class="badge" style="border-color:{clr};color:{clr};">{TYPEFACE_ID.get(tk,tk)} {sc}</span>'
            probs = {k: float(row.get(f"typeface_prob_{k}",0) or 0) for k in TYPEFACE_ID}
            if any(probs.values()): tf_bars = prob_bars(probs, TYPEFACE_CLR, TYPEFACE_ID)
        if show_gi and pd.notna(row.get("gaya_ilustrasi")):
            gk = str(row["gaya_ilustrasi"])
            clr = GAYA_CLR.get(gk, "#999")
            try: sc_gi = f"{float(row.get('gaya_skor',0)):.2f}"
            except Exception: sc_gi = "–"
            badges += f'<span class="badge" style="border-color:{clr};color:{clr};">{GAYA_ID.get(gk,gk)} {sc_gi}</span>'
            probs_gi = {k: float(row.get(f"gaya_prob_{k}",0) or 0) for k in GAYA_PROB_KEYS}
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

def _top_genres_filtered(d, n=12):
    gc = genre_counts(d, normalize=True)
    return [g for g, _ in gc.most_common() if g not in GENRE_EXCLUDE and gc[g] >= 3][:n]

# ── HEATMAP FUNCTIONS ────────────────────────────────────────────────────────
def heatmap_warna_genre_klaster(d, top_n=16):
    genres = _top_genres_filtered(d, top_n)
    warna_keys = WARNA_ORDER
    mat = pd.DataFrame(0.0, index=genres, columns=warna_keys)
    genre_lists = expand_genres(d["GENRES"], normalize=True)
    for genre in genres:
        mask = [genre in gl for gl in genre_lists]
        sub = d[mask]
        if len(sub) == 0: continue
        vc = compute_warna_distribusi(sub)
        for w in warna_keys: mat.loc[genre, w] = vc.get(w, 0.0)
    y_labels = []
    for g in genres:
        kl = GENRE_KLASTER_MAP.get(g)
        y_labels.append(f"{g}  [{kl['id']}]" if kl else g)
    warna_global = compute_warna_distribusi(d)
    x_labels = [f"{w}<br>({warna_global.get(w,0)*100:.1f}%)" for w in warna_keys]
    text_mat = (mat*100).round(1).astype(str) + "%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=x_labels, y=y_labels, colorscale="YlOrRd",
        text=text_mat.values, texttemplate="%{text}", textfont=dict(size=9,color="#1A1A1A"),
        hovertemplate="Genre: %{y}<br>Warna: %{x}<br>Proporsi: %{text}<extra></extra>",
        showscale=True, zmin=0, zmax=1,
    ))
    kl_ids = [GENRE_KLASTER_MAP.get(g,{}).get("id","none") for g in genres]
    shapes = []
    for i in range(1, len(kl_ids)):
        if kl_ids[i] != kl_ids[i-1]:
            shapes.append(dict(type="line",x0=-0.5,x1=len(warna_keys)-0.5,y0=i-0.5,y1=i-0.5,
                               line=dict(color="rgba(50,50,50,0.35)",width=1.5,dash="dot")))
    fig.update_layout(**pb(max(360,top_n*30),margin=dict(l=180,r=20,t=40,b=90),
                           yaxis=dict(autorange="reversed"),xaxis_title="",yaxis_title="",
                           title=dict(text="Peta Panas Warna × Genre",font=dict(size=12),x=0,xanchor="left"),
                           shapes=shapes if shapes else []))
    return fig


def heatmap_tf_genre(d, top_n=12):
    genres = _top_genres_filtered(d, top_n)
    tf_keys = list(TYPEFACE_ID.keys())
    tf_labels = [TYPEFACE_ID[k] for k in tf_keys]
    mat = pd.DataFrame(0.0, index=genres, columns=tf_labels)
    d2 = d[d["typeface_kategori"].isin(tf_keys)]
    genre_lists = expand_genres(d2["GENRES"], normalize=True)
    for genre in genres:
        mask = [genre in gl for gl in genre_lists]
        sub = d2[mask]
        if len(sub) == 0: continue
        vc = sub["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)
        for k in tf_keys: mat.loc[genre, TYPEFACE_ID[k]] = vc.get(TYPEFACE_ID[k], 0.0)
    y_labels = []
    for g in genres:
        kl = GENRE_KLASTER_MAP.get(g)
        y_labels.append(f"{g}  [{kl['id']}]" if kl else g)
    text_mat = (mat*100).round(0).astype(int).astype(str) + "%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=tf_labels, y=y_labels, colorscale="Purples",
        text=text_mat.values, texttemplate="%{text}", textfont=dict(size=9,color="#1A1A1A"),
        hovertemplate="Genre: %{y}<br>Tipografi: %{x}<br>Proporsi: %{text}<extra></extra>",
        showscale=True
    ))
    fig.update_layout(**pb(max(340,top_n*28),margin=dict(l=180,r=20,t=32,b=90),
                           yaxis=dict(autorange="reversed"),xaxis=dict(tickangle=-30),
                           xaxis_title="",yaxis_title=""))
    return fig


def heatmap_gaya_genre(d, top_n=12):
    genres = _top_genres_filtered(d, top_n)
    gaya_keys = list(GAYA_ID.keys())
    gaya_labels = [GAYA_ID[k] for k in gaya_keys]
    mat = pd.DataFrame(0.0, index=genres, columns=gaya_labels)
    d2 = d[d["gaya_ilustrasi"].notna()]
    genre_lists = expand_genres(d2["GENRES"], normalize=True)
    for genre in genres:
        mask = [genre in gl for gl in genre_lists]
        sub = d2[mask]
        if len(sub) == 0: continue
        vc = sub["gaya_ilustrasi"].map(GAYA_ID).value_counts(normalize=True)
        for k in gaya_keys: mat.loc[genre, GAYA_ID[k]] = vc.get(GAYA_ID[k], 0.0)
    y_labels = []
    for g in genres:
        kl = GENRE_KLASTER_MAP.get(g)
        y_labels.append(f"{g}  [{kl['id']}]" if kl else g)
    text_mat = (mat*100).round(0).astype(int).astype(str) + "%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=gaya_labels, y=y_labels, colorscale="Greens",
        text=text_mat.values, texttemplate="%{text}", textfont=dict(size=9,color="#1A1A1A"),
        hovertemplate="Genre: %{y}<br>Gaya: %{x}<br>Proporsi: %{text}<extra></extra>",
        showscale=True
    ))
    fig.update_layout(**pb(max(340,top_n*28),margin=dict(l=180,r=20,t=32,b=60),
                           yaxis=dict(autorange="reversed"),xaxis_title="",yaxis_title=""))
    return fig

# ── WARNA LEGEND & PALETTE ───────────────────────────────────────────────────
def render_warna_legend(wc_series, is_proporsi=False):
    items = []
    if is_proporsi:
        for w in WARNA_ORDER:
            pct = float(wc_series.get(w,0))*100
            dot_style = "border:1px solid rgba(0,0,0,.15);" if w == "putih" else ""
            items.append((w, pct, dot_style))
    else:
        total = wc_series.sum()
        for w in WARNA_ORDER:
            n = int(wc_series.get(w,0))
            pct = n/total*100 if total > 0 else 0
            dot_style = "border:1px solid rgba(0,0,0,.15);" if w == "putih" else ""
            items.append((w, pct, dot_style))
    col_a, col_b = st.columns(2)
    half = (len(items)+1)//2
    for col, chunk in zip([col_a,col_b],[items[:half],items[half:]]):
        with col:
            for w, pct, dot_style in chunk:
                display = w.replace("_"," ")
                st.markdown(
                    f'<div class="warna-legend-item">'
                    f'<div class="warna-dot" style="background:{WARNA_HEX[w]};{dot_style}"></div>'
                    f'<span style="font-weight:500;min-width:72px;">{display}</span>'
                    f'<span style="color:#888;font-size:11px;">{pct:.1f}%</span>'
                    f"</div>", unsafe_allow_html=True
                )


def render_color_palette_by_genre(d):
    gc = genre_counts(d, normalize=True)
    all_genres = [g for g, _ in gc.most_common() if g not in GENRE_EXCLUDE and gc[g] >= 3]
    genre_labels = {g:(f"[{GENRE_KLASTER_MAP[g]['id']}] {g}" if g in GENRE_KLASTER_MAP else g) for g in all_genres}
    label_to_genre = {v: k for k, v in genre_labels.items()}
    pal_c1, pal_c2 = st.columns([3,1])
    with pal_c1:
        sel_labels = st.multiselect("Pilih genre yang ditampilkan",
            options=[genre_labels[g] for g in all_genres],
            default=[genre_labels[g] for g in all_genres[:12]], key="pal_genre_sel")
    with pal_c2:
        pal_cols_opt = st.selectbox("Kolom tampilan",[1,2],index=0,key="pal_cols")
    genres_sel = [label_to_genre[lbl] for lbl in sel_labels if lbl in label_to_genre]
    if not genres_sel:
        st.caption("Pilih minimal satu genre.")
        return
    genre_lists = expand_genres(d["GENRES"], normalize=True)
    cols_html = st.columns(pal_cols_opt)
    for gi, g in enumerate(genres_sel):
        mask = [g in gl for gl in genre_lists]
        sub = d[mask]
        if sub.empty: continue
        wc = compute_warna_distribusi(sub)
        items = [(w, wc.get(w,0)*100) for w in WARNA_ORDER if wc.get(w,0) > 0]
        items.sort(key=lambda x: -x[1])
        bar_parts = ""
        legend_parts = ""
        for _w, _pct in items:
            _border = "border:1px solid rgba(0,0,0,.10);" if _w == "putih" else ""
            bar_parts += (f'<div style="background:{WARNA_HEX[_w]};width:{_pct:.1f}%;'
                          f'display:flex;align-items:center;justify-content:center;{_border}"'
                          f' title="{_w.replace("_"," ")}: {_pct:.1f}%">'
                          f'<span style="color:{WARNA_TXT[_w]};font-size:.55rem;font-weight:700;white-space:nowrap;">'
                          f'{"" if _pct < 9 else f"{_pct:.0f}%"}</span></div>')
        for _w, _pct in items[:6]:
            _border = "border:1px solid rgba(0,0,0,.10);" if _w == "putih" else ""
            _dn = _w.replace("_"," ")
            legend_parts += (f'<span style="display:inline-flex;align-items:center;gap:4px;'
                             f'font-size:10px;margin-right:9px;">'
                             f'<span style="width:9px;height:9px;border-radius:2px;'
                             f'background:{WARNA_HEX[_w]};{_border}flex-shrink:0;display:inline-block;"></span>'
                             f'<span style="font-weight:500">{_dn}</span>'
                             f'<span style="color:#888">({_pct:.1f}%)</span></span>')
        kl = GENRE_KLASTER_MAP.get(g)
        kl_badge = ""
        if kl:
            kl_badge = (f'<span style="font-size:10px;background:{kl["bg"]};color:{kl["color"]};'
                       f'padding:1px 7px;border-radius:8px;margin-left:6px;font-weight:600;">'
                       f'[{kl["id"]}]</span>')
        with cols_html[gi % pal_cols_opt]:
            st.markdown(
                f'<div style="margin-bottom:1rem;padding:.6rem .7rem;'
                f'border:1px solid rgba(128,128,128,.1);border-radius:8px;">'
                f'<div style="font-size:12px;font-weight:600;margin-bottom:5px;">'
                f'{g}{kl_badge}'
                f'<span style="font-weight:400;color:#888;font-size:11px;margin-left:6px;">'
                f"— {len(sub):,} buku</span></div>"
                f'<div style="display:flex;height:22px;border-radius:5px;overflow:hidden;gap:1px;">'
                f"{bar_parts}</div>"
                f'<div style="margin-top:5px;line-height:1.7">{legend_parts}</div>'
                f"</div>", unsafe_allow_html=True
            )


def render_klaster_visual(d, analysis_type="warna"):
    genre_lists_all = expand_genres(d["GENRES"], normalize=True)
    for kl in KLASTER_COOC:
        mask = [any(g in gl for g in kl["genres"]) for gl in genre_lists_all]
        df_kl = d[mask]
        if df_kl.empty: continue
        with st.expander(f"**{kl['label']}** — {len(df_kl):,} buku", expanded=True):
            if analysis_type == "warna":
                wc = compute_warna_distribusi(df_kl)
                wc_all = compute_warna_distribusi(d)
                c1, c2 = st.columns(2)
                with c1:
                    names_ord = [w for w in WARNA_ORDER if wc.get(w,0) > 0]
                    fig = px.pie(values=[wc[w] for w in names_ord],
                                 names=[w.replace("_"," ") for w in names_ord], hole=0.42,
                                 color=[w.replace("_"," ") for w in names_ord],
                                 color_discrete_map={w.replace("_"," "): WARNA_HEX[w] for w in WARNA_ORDER})
                    fig.update_layout(**pb(260))
                    fig.update_traces(textinfo="percent+label", textfont_size=10)
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    diff = (wc-wc_all).dropna().sort_values(ascending=False)
                    diff_df = diff.reset_index(); diff_df.columns = ["warna","delta"]
                    diff_df["warna_disp"] = diff_df["warna"].str.replace("_"," ")
                    fig2 = px.bar(diff_df, x="delta", y="warna_disp", orientation="h",
                                  color="warna", color_discrete_map=WARNA_HEX)
                    fig2.update_layout(**pb(260),showlegend=False,
                                       xaxis_title="Simpangan proporsi",yaxis_title="",
                                       yaxis=dict(categoryorder="total ascending"))
                    fig2.add_vline(x=0,line_dash="dash",line_color="rgba(128,128,128,.4)")
                    st.plotly_chart(fig2, use_container_width=True)
            elif analysis_type == "tipografi":
                df_kl_tf = df_kl[df_kl["typeface_kategori"].isin(TYPEFACE_ID.keys())]
                if df_kl_tf.empty:
                    st.info("Belum ada data tipografi.")
                    continue
                tc = df_kl_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts()
                tc_all = d[d["typeface_kategori"].isin(TYPEFACE_ID.keys())
                           ]["typeface_kategori"].map(TYPEFACE_ID).value_counts()
                c1, c2 = st.columns(2)
                with c1:
                    fig = px.pie(values=tc.values, names=tc.index, hole=0.42,
                                 color=tc.index,
                                 color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID})
                    fig.update_layout(**pb(260))
                    fig.update_traces(textinfo="percent+label",textfont_size=10)
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    diff = (tc/len(df_kl_tf)-tc_all/tc_all.sum()).dropna().sort_values(ascending=False)
                    diff_df = diff.reset_index(); diff_df.columns = ["tipografi","delta"]
                    fig2 = px.bar(diff_df, x="delta", y="tipografi", orientation="h",
                                  color="tipografi",
                                  color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID})
                    fig2.update_layout(**pb(260),showlegend=False,
                                       xaxis_title="Simpangan proporsi",yaxis_title="",
                                       yaxis=dict(categoryorder="total ascending"))
                    fig2.add_vline(x=0,line_dash="dash",line_color="rgba(128,128,128,.4)")
                    st.plotly_chart(fig2, use_container_width=True)
            elif analysis_type == "ilustrasi":
                df_kl_gi = df_kl[df_kl["gaya_ilustrasi"].notna()]
                if df_kl_gi.empty:
                    st.info("Belum ada data ilustrasi.")
                    continue
                gc = df_kl_gi["gaya_ilustrasi"].map(GAYA_ID).value_counts()
                gc_all = d["gaya_ilustrasi"].map(GAYA_ID).value_counts()
                c1, c2 = st.columns(2)
                with c1:
                    fig = px.pie(values=gc.values, names=gc.index, hole=0.42,
                                 color=gc.index,
                                 color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID})
                    fig.update_layout(**pb(260))
                    fig.update_traces(textinfo="percent+label",textfont_size=10)
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    diff = (gc/len(df_kl_gi)-gc_all/gc_all.sum()).dropna().sort_values(ascending=False)
                    diff_df = diff.reset_index(); diff_df.columns = ["gaya","delta"]
                    fig2 = px.bar(diff_df, x="delta", y="gaya", orientation="h",
                                  color="gaya",
                                  color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID})
                    fig2.update_layout(**pb(260),showlegend=False,
                                       xaxis_title="Simpangan proporsi",yaxis_title="",
                                       yaxis=dict(categoryorder="total ascending"))
                    fig2.add_vline(x=0,line_dash="dash",line_color="rgba(128,128,128,.4)")
                    st.plotly_chart(fig2, use_container_width=True)

# ── ILUSTRASI CONFIDENCE FUNCTIONS ───────────────────────────────────────────
def _yolo_info(row):
    ada_manusia = str(row.get("yolo_ada_manusia","")).upper() == "TRUE"
    detr_manusia = str(row.get("detr_ada_manusia","")).upper() == "TRUE"
    n_objek = row.get("yolo_n_objek",0)
    try: n_objek = int(float(n_objek))
    except Exception: n_objek = 0
    objek_str = str(row.get("yolo_objek","") or "")
    objek_list = [o.strip() for o in objek_str.split(",") if o.strip() and o.strip() not in ("0","nan")]
    return {"ada_manusia":ada_manusia,"detr_manusia":detr_manusia,
            "n_objek":n_objek,"objek_list":objek_list[:8]}


def _render_confidence_card(row, label_top="", label_top_color="#333",
                             badge_text="", badge_bg="#eee", badge_fg="#333"):
    cp = cover_path(row.get("IMAGE_FILE"))
    if cp: st.image(cp, use_container_width=True)
    else:
        st.markdown('<div style="height:150px;background:rgba(128,128,128,.08);border-radius:8px 8px 0 0;'
                    'display:flex;align-items:center;justify-content:center;font-size:2rem;">📖</div>',
                    unsafe_allow_html=True)
    try: skor_str = f"{float(row.get('gaya_skor',0)):.3f}"
    except Exception: skor_str = "–"
    gaya_key = str(row.get("gaya_ilustrasi",""))
    gaya_label = GAYA_ID.get(gaya_key, gaya_key)
    gaya_clr = GAYA_CLR.get(gaya_key, "#999")
    gaya_icon = GAYA_ICON.get(gaya_key,"")
    year = int(row["YEAR"]) if row.get("YEAR",0) and int(row.get("YEAR",0)) > 0 else "–"
    url = str(row.get("URL","") or "")
    title = str(row.get("TITLE","–"))
    title_html = (f'<a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">{title}</a>' if url else title)
    conf_label_html = f'<div style="font-size:.58rem;font-weight:700;color:{label_top_color};letter-spacing:.05em;text-transform:uppercase;margin-bottom:2px;">{label_top}</div>' if label_top else ""
    badge_html = (f'<span style="display:inline-block;background:{badge_bg};color:{badge_fg};border-radius:10px;padding:1px 8px;font-size:.63rem;font-weight:700;margin-bottom:3px;">{badge_text}</span> ') if badge_text else ""
    yolo = _yolo_info(row)
    figur_src = []
    if yolo["ada_manusia"]: figur_src.append("YOLO")
    if yolo["detr_manusia"]: figur_src.append("DETR")
    if figur_src:
        figur_html = (f'<span style="background:#E3F2FD;color:#1565C0;border-radius:8px;'
                      f'padding:1px 6px;font-size:.58rem;font-weight:600;">👤 Manusia ({", ".join(figur_src)})</span>')
    else:
        figur_html = '<span style="background:#F5F5F5;color:#999;border-radius:8px;padding:1px 6px;font-size:.58rem;">— Non-manusia</span>'
    obj_tags_html = ""
    if yolo["objek_list"]:
        tags = "".join(f'<span style="background:#FAFAFA;color:#666;border:1px solid #E8E8E8;border-radius:6px;padding:0px 5px;font-size:.55rem;margin:1px 2px 0 0;">{o}</span>' for o in yolo["objek_list"])
        obj_tags_html = f'<div style="margin-top:2px;line-height:2.0">{tags}</div>'
    yolo_box_html = (f'<div style="margin-top:5px;padding:4px 6px;background:rgba(128,128,128,.04);border:1px solid rgba(128,128,128,.1);border-radius:6px;">'
                     f'<div style="font-size:.58rem;font-weight:600;opacity:.5;letter-spacing:.05em;text-transform:uppercase;margin-bottom:3px;">Deteksi Objek</div>'
                     f'{figur_html}{obj_tags_html}</div>')
    probs = {k: float(row.get(f"gaya_prob_{k}",0) or 0) for k in GAYA_PROB_KEYS}
    prob_html = ""
    if any(probs.values()):
        sorted_probs = sorted(probs.items(), key=lambda x: -x[1])
        bars_inner = ""
        for k, v in sorted_probs:
            lbl = GAYA_ID.get(k,k); clr = GAYA_CLR.get(k,"#999"); pct = v*100
            is_top = k == gaya_key
            highlight = f"box-shadow:0 0 0 1.5px {gaya_clr};" if is_top else ""
            fw = "font-weight:700;" if is_top else ""
            bars_inner += (f'<div style="margin-bottom:3px;"><div style="display:flex;justify-content:space-between;font-size:.57rem;color:#666;margin-bottom:1px;">'
                          f'<span style="{fw}">{lbl}</span><span style="{fw}color:{clr}">{pct:.1f}%</span></div>'
                          f'<div style="background:rgba(128,128,128,.1);border-radius:3px;height:5px;overflow:hidden;{highlight}">'
                          f'<div style="width:{pct:.1f}%;background:{clr};height:5px;border-radius:3px;"></div></div></div>')
        prob_html = (f'<div style="margin-top:5px;padding:4px 6px;background:rgba(128,128,128,.04);border:1px solid rgba(128,128,128,.1);border-radius:6px;">'
                    f'<div style="font-size:.58rem;font-weight:600;opacity:.5;letter-spacing:.05em;text-transform:uppercase;margin-bottom:4px;">Distribusi Gaya Visual</div>'
                    f'{bars_inner}</div>')
    st.markdown(
        f'<div style="padding:.4rem .45rem .6rem;border:1px solid rgba(128,128,128,.1);border-top:3px solid {gaya_clr};border-radius:0 0 8px 8px;">'
        f'{conf_label_html}{badge_html}'
        f'<span style="display:inline-block;background:{gaya_clr}18;color:{gaya_clr};border-radius:6px;padding:1px 6px;font-size:.6rem;font-weight:600;margin-bottom:3px;">'
        f'{gaya_icon} {gaya_label} · {skor_str}</span>'
        f'<div style="font-family:\'Lora\',serif;font-size:.76rem;font-weight:600;line-height:1.3;margin:.2rem 0 .1rem;">{title_html}</div>'
        f'<div style="font-size:.65rem;color:#999;margin-bottom:.2rem;">{row.get("AUTHOR","–")} · {year}</div>'
        f'{yolo_box_html}{prob_html}</div>', unsafe_allow_html=True
    )


def render_confidence_by_gaya(d):
    if "gaya_ilustrasi" not in d.columns or "gaya_skor" not in d.columns:
        st.info("Kolom gaya_ilustrasi atau gaya_skor tidak ditemukan.")
        return
    d_valid = d[d["gaya_ilustrasi"].notna() & d["image_ok"].astype(str).str.upper().isin(["TRUE","1"])].copy()
    d_valid["gaya_skor"] = pd.to_numeric(d_valid["gaya_skor"], errors="coerce")
    d_valid = d_valid.dropna(subset=["gaya_skor"])
    if d_valid.empty:
        st.info("Tidak ada data ilustrasi yang valid.")
        return
    scol1, scol2 = st.columns([3,1])
    with scol1:
        sel_gaya = st.multiselect("Pilih gaya ilustrasi", options=list(GAYA_ID.keys()),
                                   default=list(GAYA_ID.keys()),
                                   format_func=lambda k: f"{GAYA_ICON.get(k,'')} {GAYA_ID.get(k,k)}",
                                   key="conf_gaya_sel")
    with scol2:
        n_sample_g = st.selectbox("Sampel per sisi",[2,3,4,5],index=1,key="conf_gaya_n")
    if not sel_gaya:
        st.caption("Pilih minimal satu gaya ilustrasi.")
        return
    for gaya_key in sel_gaya:
        df_gaya = d_valid[d_valid["gaya_ilustrasi"] == gaya_key].copy()
        if df_gaya.empty: continue
        gaya_label = GAYA_ID.get(gaya_key,gaya_key)
        gaya_clr = GAYA_CLR.get(gaya_key,"#999")
        gaya_icon = GAYA_ICON.get(gaya_key,"")
        n_total = len(df_gaya)
        mean_s = df_gaya["gaya_skor"].mean()
        median_s = df_gaya["gaya_skor"].median()
        with st.expander(f"{gaya_icon} **{gaya_label}** — {n_total:,} buku  ·  mean {mean_s:.3f}  ·  median {median_s:.3f}", expanded=True):
            skor_hist = df_gaya["gaya_skor"].dropna()
            bins_edges = [0.0,0.2,0.4,0.6,0.8,1.0]
            bin_labels = ["0–20%","20–40%","40–60%","60–80%","80–100%"]
            bin_colors = ["#EF9A9A","#FFCC80","#FFF176","#A5D6A7","#66BB6A"]
            counts_arr, _ = np.histogram(skor_hist, bins=bins_edges)
            total_h = counts_arr.sum()
            hist_html = ""
            for i, (lbl, cnt) in enumerate(zip(bin_labels,counts_arr)):
                pct_h = (cnt/total_h*100) if total_h > 0 else 0
                bc = bin_colors[i]
                hist_html += (f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">'
                              f'<div style="width:56px;font-size:.6rem;color:#777;text-align:right;flex-shrink:0;">{lbl}</div>'
                              f'<div style="flex:1;background:rgba(128,128,128,.08);border-radius:3px;height:13px;overflow:hidden;">'
                              f'<div style="width:{pct_h:.1f}%;background:{bc};height:13px;border-radius:3px;display:flex;align-items:center;padding-left:4px;">'
                              f'<span style="font-size:.56rem;font-weight:700;color:#444;">{cnt if pct_h >= 5 else ""}</span></div></div>'
                              f'<div style="width:28px;font-size:.58rem;color:#aaa;flex-shrink:0;">{cnt}</div></div>')
            st.markdown(f'<div style="padding:8px 10px;background:rgba(128,128,128,.03);border:1px solid rgba(128,128,128,.1);border-radius:8px;margin-bottom:.8rem;">'
                        f'<div style="font-size:.62rem;font-weight:600;color:{gaya_clr};margin-bottom:5px;letter-spacing:.05em;text-transform:uppercase;">Distribusi Skor Confidence</div>'
                        f'{hist_html}</div>', unsafe_allow_html=True)
            hdr_a, hdr_b = st.columns(2)
            with hdr_a:
                st.markdown(f'<div style="text-align:center;background:#E8F5E9;border-radius:8px;padding:5px;font-size:.7rem;font-weight:700;color:#1B7D3C;margin-bottom:.4rem;">✦ Confidence Tertinggi (top {n_sample_g})</div>', unsafe_allow_html=True)
            with hdr_b:
                st.markdown(f'<div style="text-align:center;background:#FFEBEE;border-radius:8px;padding:5px;font-size:.7rem;font-weight:700;color:#B71C1C;margin-bottom:.4rem;">▾ Confidence Terendah (bottom {n_sample_g})</div>', unsafe_allow_html=True)
            top_rows = df_gaya.nlargest(n_sample_g,"gaya_skor")
            bot_rows = df_gaya.nsmallest(n_sample_g,"gaya_skor")
            n_grid = n_sample_g*2
            all_rows_gaya = list(top_rows.iterrows()) + list(bot_rows.iterrows())
            card_cols = st.columns(n_grid)
            for i, (_, row) in enumerate(all_rows_gaya):
                is_top = i < n_sample_g
                rank = (i+1) if is_top else (i-n_sample_g+1)
                with card_cols[i]:
                    _render_confidence_card(row,
                        label_top="✦ Tertinggi" if is_top else "▾ Terendah",
                        label_top_color="#1B7D3C" if is_top else "#B71C1C",
                        badge_text=f"#{rank} · {float(row.get('gaya_skor',0)):.3f}",
                        badge_bg="#E8F5E9" if is_top else "#FFEBEE",
                        badge_fg="#1B7D3C" if is_top else "#B71C1C")

# ── SIDEBAR & FILTER ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Kartografi Sampul")
    st.markdown("<small>Analisis komputasional sampul buku sastra Indonesia</small>", unsafe_allow_html=True)
    st.markdown("---")
    HAL = st.radio("Navigasi",
        ["Beranda","Warna","Tipografi","Ilustrasi","Genre","Illustrator","Jelajah Buku"],
        label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Filter Tahun**")
    yr_range = st.slider("Tahun",2000,2025,(2000,2025),label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<small>Metode: K-Means HSV · EasyOCR · YOLOv8n · DETR ResNet-50</small>", unsafe_allow_html=True)

DF = df[(df["YEAR"] >= yr_range[0]) & (df["YEAR"] <= yr_range[1])].copy()
_gc = genre_counts(DF, normalize=True)
_n_unik = len([g for g in _gc if g not in GENRE_EXCLUDE])

# ══════════════════════════════════════════════════════════════════════════════
# BERANDA
# ══════════════════════════════════════════════════════════════════════════════
if HAL == "Beranda":
    st.markdown("# Kartografi Sampul Sastra Indonesia")
    st.markdown(f"Pemetaan komputasional terhadap **{len(DF):,} sampul buku** fiksi dan puisi Indonesia "
                f"yang terbit periode 2000–2025, dianalisis melalui tiga aspek visual: warna, tipografi, dan gaya ilustrasi.")
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    n_warna = int(DF["warna_kategori"].notna().sum())
    n_tf = int(DF[DF["typeface_kategori"].isin(TYPEFACE_ID.keys())].shape[0])
    n_gi = int(DF["gaya_ilustrasi"].notna().sum())

    c1,c2,c3,c4 = st.columns(4)
    for col,(lbl,val,sub,clr) in zip([c1,c2,c3,c4],[
        ("Warna",n_warna,"teranalisis","#FB8C00"),
        ("Tipografi",n_tf,"terklasifikasi","#8E24AA"),
        ("Ilustrasi",n_gi,"terklasifikasi","#E53935"),
        ("Genre",_n_unik,"genre unik","#00ACC1"),
    ]):
        with col:
            st.markdown(f'<div class="stat-card" style="border-top:3px solid {clr};">'
                        f'<div class="lbl">{lbl}</div><div class="val" style="color:{clr};">{int(val):,}</div>'
                        f'<div class="sub">{sub}</div></div>', unsafe_allow_html=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Tren Terbit per Tahun**")
    yr = DF[DF["YEAR"] > 0].groupby("YEAR").size().reset_index(name="n")
    fig_yr = px.bar(yr, x="YEAR", y="n")
    fig_yr.update_layout(**pb(280), xaxis_title="", yaxis_title="", showlegend=False)
    fig_yr.update_traces(marker_line_width=0)
    st.plotly_chart(fig_yr, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Distribusi Genre**")
    gc_beranda = [(g,n) for g,n in _gc.most_common() if g not in GENRE_EXCLUDE and n >= 5]
    n_gr_show = st.slider("Tampilkan top N genre",10,min(len(gc_beranda),40),20,5,key="beranda_gn")
    df_gb = pd.DataFrame(gc_beranda[:n_gr_show], columns=["Genre","Jumlah"])
    fig_gb = px.bar(df_gb, x="Jumlah", y="Genre", orientation="h",
                    color_discrete_sequence=["#1E88E5"], text="Jumlah")
    fig_gb.update_layout(**pb(max(300,n_gr_show*26)),showlegend=False,xaxis_title="",yaxis_title="",
                         yaxis=dict(categoryorder="total ascending"))
    fig_gb.update_traces(textposition="outside",marker_line_width=0)
    st.plotly_chart(fig_gb, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca:
        st.markdown("**Komposisi Warna Keseluruhan**")
        wc_beranda = compute_warna_distribusi(DF)
        names_ord = [w for w in WARNA_ORDER if wc_beranda.get(w,0) > 0]
        fig3 = px.pie(values=[wc_beranda[w] for w in names_ord],
                      names=[w.replace("_"," ") for w in names_ord], hole=0.4,
                      color=[w.replace("_"," ") for w in names_ord],
                      color_discrete_map={w.replace("_"," "): WARNA_HEX[w] for w in WARNA_ORDER})
        fig3.update_layout(**pb(260))
        fig3.update_traces(textinfo="percent+label",textfont_size=10)
        st.plotly_chart(fig3, use_container_width=True)
    with cb:
        st.markdown("**Gaya Ilustrasi**")
        gc2 = DF["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        fig4 = px.bar(x=gc2.values, y=gc2.index, orientation="h",
                      color=gc2.index,
                      color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID})
        fig4.update_layout(**pb(260),showlegend=False,xaxis_title="",yaxis_title="",
                           yaxis=dict(categoryorder="total ascending"))
        fig4.update_traces(marker_line_width=0)
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# WARNA
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Warna":
    st.markdown("## Analisis Warna")
    with st.expander("Cara kerja analisis warna", expanded=False):
        st.markdown("**K-Means Clustering (k=5) pada ruang warna HSV**\n\n"
                    "1. Sampul → 150×150 piksel → BGR→HSV.\n"
                    "2. K-Means k=5, 10 inisialisasi acak.\n"
                    "3. Label warna dari rentang Hue dominan (skala OpenCV 0–180).\n"
                    "4. Re-klasifikasi otomatis dijalankan pada load data.")
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    wc_full = compute_warna_distribusi(DF)
    ca2, cb2 = st.columns([1,2])
    with ca2:
        st.markdown("**Distribusi Warna Keseluruhan**")
        names_ord = [w for w in WARNA_ORDER if wc_full.get(w,0) > 0]
        fig = px.pie(values=[wc_full[w] for w in names_ord],
                     names=[w.replace("_"," ") for w in names_ord], hole=0.42,
                     color=[w.replace("_"," ") for w in names_ord],
                     color_discrete_map={w.replace("_"," "): WARNA_HEX[w] for w in WARNA_ORDER})
        fig.update_layout(**pb(300))
        fig.update_traces(textinfo="percent",textfont_size=10)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("**Keterangan**")
        render_warna_legend(wc_full, is_proporsi=True)
    with cb2:
        st.markdown("**Tren Warna per Tahun**")
        rows_trend = []
        for yr, grp in DF[DF["YEAR"] > 0].groupby("YEAR"):
            wc_yr = compute_warna_distribusi(grp)
            n_buku = len(grp)
            for w in WARNA_ORDER:
                rows_trend.append({"YEAR":yr,"warna":w.replace("_"," "),"bobot":wc_yr.get(w,0)*n_buku})
        trnd = pd.DataFrame(rows_trend)
        fig2 = px.bar(trnd, x="YEAR", y="bobot", color="warna",
                      color_discrete_map={w.replace("_"," "): WARNA_HEX[w] for w in WARNA_ORDER},
                      barmode="stack")
        fig2.update_layout(**pb(360),xaxis_title="",yaxis_title="Bobot warna",showlegend=True,
                           legend=dict(orientation="h",y=-.15,font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Kecerahan vs Saturasi per Warna**")
    df_sc = DF.dropna(subset=["brightness_mean","saturation_mean","warna_kategori"]).copy()
    df_sc["warna_disp"] = df_sc["warna_kategori"].str.replace("_"," ")
    fig_sc = px.scatter(df_sc, x="brightness_mean", y="saturation_mean", color="warna_disp",
                        color_discrete_map={w.replace("_"," "): WARNA_HEX[w] for w in WARNA_ORDER},
                        opacity=.35, custom_data=["TITLE","AUTHOR","YEAR","warna_disp"])
    fig_sc.update_traces(marker=dict(size=4),
                         hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} · %{customdata[2]}<br>Warna: %{customdata[3]}<br>V: %{x:.2f} · S: %{y:.2f}<extra></extra>")
    fig_sc.update_layout(**pb(300),showlegend=True,legend=dict(orientation="h",y=-.18,font=dict(size=10)),
                         xaxis_title="Kecerahan (V)",yaxis_title="Saturasi (S)")
    st.plotly_chart(fig_sc, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Distribusi Warna per Klaster Genre**")
    render_klaster_visual(DF, analysis_type="warna")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Peta Panas Warna × Genre**")
    hn_w = st.slider("Jumlah genre",6,20,16,2,key="hn_warna")
    st.plotly_chart(heatmap_warna_genre_klaster(DF, hn_w), use_container_width=True)
    kl_cols = st.columns(3)
    for kc, kl in zip(kl_cols, KLASTER_COOC):
        kc.markdown(f'<span style="background:{kl["bg"]};color:{kl["color"]};padding:2px 10px;border-radius:8px;font-size:11px;font-weight:600;">[{kl["id"]}] {kl["label"].split("—")[1].strip()}</span>', unsafe_allow_html=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Palet Warna per Genre**")
    render_color_palette_by_genre(DF)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Cari Buku berdasarkan Warna**")
    wc1, wc2, wc3 = st.columns([2,2,1])
    with wc1: q_w = st.text_input("Judul / penulis", key="w_q")
    with wc2:
        w_sel = st.selectbox("Filter warna",["Semua"]+list(WARNA_HEX.keys()),
                             format_func=lambda w: "Semua" if w=="Semua" else w.replace("_"," ").capitalize(),key="w_sel")
    with wc3: n_w = st.slider("Tampilkan",4,32,8,4,key="w_n")
    dw = DF[DF["image_ok"]].copy()
    if q_w:
        ql = q_w.lower()
        dw = dw[dw["TITLE"].str.lower().str.contains(ql,na=False) | dw["AUTHOR"].str.lower().str.contains(ql,na=False)]
    if w_sel != "Semua": dw = dw[dw["warna_kategori"] == w_sel]
    if not dw.empty: grid(dw.head(n_w))

# ══════════════════════════════════════════════════════════════════════════════
# TIPOGRAFI (v3 — dengan redistribusi tidak_terklasifikasi)
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Tipografi":
    st.markdown("## Analisis Tipografi")

    with st.expander("Cara kerja analisis tipografi (Modul B v3)", expanded=False):
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.markdown(
                "**Pipeline v3 (analisis piksel huruf, tanpa CLIP):**\n\n"
                "1. **EasyOCR** — deteksi bounding box teks\n"
                "2. **Font DB Lookup** — 928 font Google Fonts & DaFont → kategori Lupton\n"
                "3. **Analisis fitur visual huruf** per karakter:\n"
                "   - `stroke_uniformity`, `serif_score`, `stroke_contrast`\n"
                "   - `curvature`, `connectivity`, `axis_angle`\n"
                "4. **Score matrix rule-based** → 7 kategori Lupton\n\n"
                "Jika confidence < 0.12 → `tidak_terklasifikasi`"
            )
        with col_info2:
            metode_vc = get_typeface_metode_breakdown(DF)
            if not metode_vc.empty:
                metode_labels = {
                    "v3_db_exact":"Database (exact match)","v3_db_fuzzy":"Database (fuzzy match)",
                    "v3_visual":"Analisis piksel visual","v3_visual_noocr":"Visual (OCR gagal)",
                    "v3_visual_lowconf":"Visual (confidence rendah → tidak terklasifikasi)",
                    "error_file_not_found":"Error: file tidak ditemukan",
                    "error_file_unreadable":"Error: file tidak terbaca",
                }
                metode_html = ""
                for m, n in metode_vc.items():
                    lbl = metode_labels.get(m, m)
                    pct = n/len(DF)*100
                    is_error = str(m).startswith("error_")
                    is_low = "lowconf" in str(m)
                    color = "#E53935" if is_error else ("#FB8C00" if is_low else "#43A047")
                    metode_html += (f'<div style="display:flex;justify-content:space-between;font-size:.68rem;margin-bottom:2px;">'
                                   f'<span style="color:{color};">{lbl}</span>'
                                   f'<span style="font-weight:600;">{n:,} ({pct:.1f}%)</span></div>')
                st.markdown(f'<div style="padding:8px 10px;background:rgba(128,128,128,.04);border:1px solid rgba(128,128,128,.12);border-radius:8px;">'
                            f'<div style="font-size:.65rem;font-weight:700;opacity:.5;letter-spacing:.05em;text-transform:uppercase;margin-bottom:6px;">Distribusi Metode</div>'
                            f'{metode_html}</div>', unsafe_allow_html=True)

    st.markdown("**Tujuh Kategori Typeface (Lupton 2024, hal. 54–57)**")
    tf_cols7 = st.columns(7)
    for col_tf, key in zip(tf_cols7, TYPEFACE_ID):
        clr = TYPEFACE_CLR[key]; font = TYPEFACE_FONT[key]
        with col_tf:
            st.markdown(f'<div style="border:1px solid rgba(128,128,128,.18);border-radius:8px;padding:.55rem .45rem;text-align:center;">'
                        f'<div style="font-family:{font};font-size:1.5rem;color:{clr};font-weight:700;line-height:1.2">Aa</div>'
                        f'<div style="font-size:.63rem;font-weight:600;opacity:.72;margin:.2rem 0 .1rem">{TYPEFACE_ID[key]}</div>'
                        f'<div style="font-size:.58rem;opacity:.5;text-align:left;line-height:1.35">{TYPEFACE_DESC[key]}</div></div>',
                        unsafe_allow_html=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # Statistik
    n_total_tf     = len(DF)
    n_classified   = int(DF["typeface_kategori"].isin(TYPEFACE_ID.keys()).sum())
    n_unclassified = int((DF["typeface_kategori"] == "tidak_terklasifikasi").sum())
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Total sampul", f"{n_total_tf:,}")
    mc2.metric("Terklasifikasi", f"{n_classified:,}", f"{n_classified/n_total_tf*100:.1f}%")
    mc3.metric("Tidak terklasifikasi", f"{n_unclassified:,}", f"-{n_unclassified/n_total_tf*100:.1f}%", delta_color="inverse")
    st.caption(f"**{n_unclassified:,} sampul** tidak terklasifikasi karena confidence < 0.12. "
               "Sampul ini memiliki vektor probabilitas yang dapat didistribusikan secara proporsional.")

    # Toggle distribusi
    show_distributed = st.toggle(
        "Distribusikan `tidak_terklasifikasi` secara proporsional ke kategori lain",
        value=True,
        help="Menggunakan vektor typeface_prob_* per buku untuk mendistribusikan buku tidak_terklasifikasi ke 7 kategori Lupton."
    )

    if show_distributed:
        props_tf, n_cl, n_uncl = redistribute_tidak_terklasifikasi(DF)
        st.info(f"**Distribusi proporsional aktif.** {n_cl:,} terklasifikasi + {n_uncl:,} tidak_terklasifikasi → total tetap {n_total_tf:,} buku.")
        tc_display = (props_tf * n_total_tf).round().astype(int)
        tc_display.index = tc_display.index.map(TYPEFACE_ID)
        tc_display = tc_display.sort_values(ascending=False)
        mode_label = "Terdistribusi"
    else:
        DF_tf_raw = DF[DF["typeface_kategori"].isin(TYPEFACE_ID.keys())]
        tc_display = DF_tf_raw["typeface_kategori"].map(TYPEFACE_ID).value_counts()
        mode_label = "Terklasifikasi saja"

    ca3, cb3 = st.columns(2)
    with ca3:
        st.markdown(f"**Distribusi Typeface ({mode_label})**")
        rev_map = {v: k for k, v in TYPEFACE_ID.items()}
        fig_donut = go.Figure(data=[go.Pie(
            labels=tc_display.index.tolist(), values=tc_display.values.tolist(), hole=0.45,
            marker=dict(colors=[TYPEFACE_CLR.get(rev_map.get(n,""),"#999") for n in tc_display.index]),
            textinfo="percent+label", textfont=dict(size=10),
            hovertemplate="%{label}<br>%{value:,} buku (%{percent})<extra></extra>",
        )])
        fig_donut.update_layout(**pb(300))
        st.plotly_chart(fig_donut, use_container_width=True)
    with cb3:
        st.markdown("**Tren Typeface per Tahun**")
        dft2 = DF[DF["typeface_kategori"].isin(TYPEFACE_ID.keys()) & (DF["YEAR"] > 0)].copy()
        dft2["tf"] = dft2["typeface_kategori"].map(TYPEFACE_ID)
        tr2 = dft2.groupby(["YEAR","tf"]).size().reset_index(name="n")
        fig_tren = px.bar(tr2, x="YEAR", y="n", color="tf", barmode="stack",
                          color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID})
        fig_tren.update_layout(**pb(300),xaxis_title="",yaxis_title="",showlegend=True,
                               legend=dict(orientation="h",y=-.22,font=dict(size=9)))
        st.plotly_chart(fig_tren, use_container_width=True)

    # Perbandingan Raw vs Terdistribusi
    with st.expander("Perbandingan: Raw vs Terdistribusi", expanded=False):
        props_full, _, _ = redistribute_tidak_terklasifikasi(DF)
        DF_tf_raw_cmp = DF[DF["typeface_kategori"].isin(TYPEFACE_ID.keys())]
        tc_raw_cmp  = DF_tf_raw_cmp["typeface_kategori"].value_counts()
        tc_dist_cmp = (props_full * n_total_tf).round().astype(int)
        cmp_data = []
        for k in TYPEFACE_ID:
            raw_n  = int(tc_raw_cmp.get(k,0))
            dist_n = int(tc_dist_cmp.get(k,0))
            cmp_data.append({"Kategori":TYPEFACE_ID[k],"Raw":raw_n,"Terdistribusi":dist_n,"Selisih":dist_n-raw_n})
        cmp_df = pd.DataFrame(cmp_data).sort_values("Terdistribusi",ascending=False)
        fig_cmp = go.Figure()
        for name, alpha, col_key in [("Raw",0.45,"Raw"),("Terdistribusi",0.9,"Terdistribusi")]:
            fig_cmp.add_trace(go.Bar(
                name=name, x=cmp_df["Kategori"], y=cmp_df[col_key], opacity=alpha,
                marker_color=[TYPEFACE_CLR.get(rev_map.get(r["Kategori"],""),"#999") for _,r in cmp_df.iterrows()],
            ))
        fig_cmp.update_layout(**pb(280),barmode="group",showlegend=True,
                               legend=dict(orientation="h",y=-.18,font=dict(size=10)),
                               xaxis_title="",yaxis_title="Jumlah buku",xaxis=dict(tickangle=-30))
        st.plotly_chart(fig_cmp, use_container_width=True)
        st.dataframe(cmp_df.style.format({"Raw":"{:,}","Terdistribusi":"{:,}","Selisih":"{:+,}"}),
                     use_container_width=True, hide_index=True)

    # Confidence stats
    df_conf_stats = get_typeface_confidence_stats(DF)
    if df_conf_stats is not None and len(df_conf_stats) > 0:
        st.markdown("<hr class='thin'>", unsafe_allow_html=True)
        st.markdown("**Distribusi Confidence per Kategori**")
        st.caption("Confidence = selisih probabilitas kategori terbaik vs kedua terbaik. Threshold: 0.12.")
        conf_col1, conf_col2 = st.columns([2,1])
        with conf_col1:
            df_conf_stats["tf_label"] = df_conf_stats["typeface_kategori"].map(TYPEFACE_ID)
            fig_conf = px.box(df_conf_stats, x="tf_label", y="typeface_confidence",
                              color="tf_label",
                              color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID},
                              points="outliers")
            fig_conf.update_layout(**pb(300),showlegend=False,xaxis_title="",yaxis_title="Confidence",
                                   xaxis=dict(tickangle=-30))
            fig_conf.add_hline(y=0.12,line_dash="dash",line_color="rgba(200,0,0,.5)",
                               annotation_text="Threshold 0.12",annotation_position="top right",
                               annotation_font_size=10)
            st.plotly_chart(fig_conf, use_container_width=True)
        with conf_col2:
            conf_tbl = (df_conf_stats.groupby("typeface_kategori")["typeface_confidence"]
                        .agg(["mean","median","count"])
                        .rename(columns={"mean":"Rata-rata","median":"Median","count":"N"})
                        .reset_index())
            conf_tbl["Kategori"] = conf_tbl["typeface_kategori"].map(TYPEFACE_ID)
            conf_tbl = conf_tbl[["Kategori","N","Rata-rata","Median"]].sort_values("Rata-rata",ascending=False)
            st.dataframe(conf_tbl.style.format({"N":"{:,}","Rata-rata":"{:.3f}","Median":"{:.3f}"}),
                         use_container_width=True, hide_index=True, height=280)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Distribusi Tipografi per Klaster Genre**")
    render_klaster_visual(DF, analysis_type="tipografi")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Peta Panas Tipografi × Genre**")
    hn_tf = st.slider("Jumlah genre",6,20,12,2,key="hn_tf")
    st.plotly_chart(heatmap_tf_genre(DF, hn_tf), use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Contoh Buku — Confidence Tertinggi per Kategori**")
    df_tv = DF[DF["typeface_kategori"].isin(TYPEFACE_ID.keys()) & DF["image_ok"]].copy()
    score_col = "typeface_confidence" if "typeface_confidence" in df_tv.columns else "typeface_skor"
    if score_col in df_tv.columns:
        df_tv[score_col] = pd.to_numeric(df_tv[score_col], errors="coerce")
    ex_cols7 = st.columns(7)
    for col_ex, key in zip(ex_cols7, TYPEFACE_ID):
        sub = df_tv[df_tv["typeface_kategori"] == key]
        if sub.empty: continue
        best = sub.nlargest(1, score_col).iloc[0] if score_col in sub.columns else sub.iloc[0]
        clr = TYPEFACE_CLR[key]
        with col_ex:
            cp = cover_path(best.get("IMAGE_FILE"))
            if cp: st.image(cp, use_container_width=True)
            try: sc = f"{float(best.get(score_col,0)):.3f}"
            except Exception: sc = "–"
            probs_b = {k: float(best.get(f"typeface_prob_{k}",0) or 0) for k in TYPEFACE_ID}
            bars = prob_bars(probs_b, TYPEFACE_CLR, TYPEFACE_ID) if any(probs_b.values()) else ""
            metode_b = str(best.get("typeface_metode",""))
            metode_colors = {"v3_db_exact":"#43A047","v3_db_fuzzy":"#66BB6A","v3_visual":"#1E88E5","v3_visual_noocr":"#FB8C00"}
            mc_b = metode_colors.get(metode_b,"#999")
            metode_badge = f'<div style="font-size:.55rem;color:{mc_b};margin-top:2px;">{metode_b}</div>' if metode_b else ""
            st.markdown(f'<div style="font-size:.62rem;padding:.25rem 0;">'
                        f'<div style="font-weight:600;color:{clr}">{TYPEFACE_ID[key]}</div>'
                        f'<div style="opacity:.6;line-height:1.3">{str(best.get("TITLE",""))[:28]}</div>'
                        f'<div style="opacity:.5">conf {sc}</div>{metode_badge}'
                        f'{"<div style=margin-top:.35rem>" + bars + "</div>" if bars else ""}</div>',
                        unsafe_allow_html=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Cari Buku berdasarkan Tipografi**")
    tfc1, tfc2, tfc3, tfc4 = st.columns([2,2,1,1])
    with tfc1: q_tf = st.text_input("Judul / penulis", key="tf_q")
    with tfc2:
        tf_sel = st.selectbox("Filter typeface",
                              ["Semua"]+[TYPEFACE_ID[k] for k in TYPEFACE_ID]+["Tidak terklasifikasi"],
                              key="tf_sel")
    with tfc3:
        sort_tf = st.selectbox("Urut berdasarkan",["Confidence","Tahun","Rating"],key="tf_sort")
    with tfc4: n_tf2 = st.slider("Tampilkan",4,32,8,4,key="tf_n")
    dtf_search = DF[DF["image_ok"]].copy()
    if q_tf:
        ql2 = q_tf.lower()
        dtf_search = dtf_search[dtf_search["TITLE"].str.lower().str.contains(ql2,na=False) |
                                 dtf_search["AUTHOR"].str.lower().str.contains(ql2,na=False)]
    if tf_sel == "Tidak terklasifikasi":
        dtf_search = dtf_search[dtf_search["typeface_kategori"] == "tidak_terklasifikasi"]
    elif tf_sel != "Semua":
        tf_rev = {v: k for k, v in TYPEFACE_ID.items()}
        dtf_search = dtf_search[dtf_search["typeface_kategori"] == tf_rev.get(tf_sel, tf_sel)]
    if sort_tf == "Confidence":
        sc_sort = "typeface_confidence" if "typeface_confidence" in dtf_search.columns else "typeface_skor"
        if sc_sort in dtf_search.columns:
            dtf_search = dtf_search.sort_values(sc_sort, ascending=False, na_position="last")
    elif sort_tf == "Tahun":
        dtf_search = dtf_search.sort_values("YEAR", ascending=False)
    elif sort_tf == "Rating" and "RATING" in dtf_search.columns:
        dtf_search = dtf_search.sort_values("RATING", ascending=False, na_position="last")
    st.caption(f"{len(dtf_search):,} buku ditemukan")
    if not dtf_search.empty: grid(dtf_search.head(n_tf2), show_tf=True)

# ══════════════════════════════════════════════════════════════════════════════
# ILUSTRASI
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Ilustrasi":
    st.markdown("## Analisis Gaya Ilustrasi")
    with st.expander("Cara kerja analisis ilustrasi", expanded=False):
        st.markdown("**YOLOv8n + DETR ResNet-50 + CLIP zero-shot**\n\n"
                    "1. **YOLOv8n** — deteksi objek COCO-80, confidence ≥ 0.25.\n"
                    "2. **DETR ResNet-50** — validator keberadaan manusia, confidence ≥ 0.85.\n"
                    "3. **CLIP ViT-B/32** — klasifikasi 6 gaya visual.")

    st.markdown("**Enam Kategori Gaya Ilustrasi**")
    gcols6 = st.columns(6)
    for gcol, key in zip(gcols6, GAYA_ID):
        clr = GAYA_CLR[key]
        with gcol:
            st.markdown(f'<div style="border:1px solid rgba(128,128,128,.18);border-radius:8px;padding:.55rem .45rem;text-align:center;">'
                        f'<div style="font-size:1.5rem">{GAYA_ICON[key]}</div>'
                        f'<div style="font-size:.66rem;font-weight:600;margin:.2rem 0 .1rem;color:{clr}">{GAYA_ID[key]}</div>'
                        f'<div style="font-size:.58rem;opacity:.55;text-align:left;line-height:1.35">{GAYA_DESC[key]}</div></div>',
                        unsafe_allow_html=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    ca4, cb4 = st.columns(2)
    with ca4:
        st.markdown("**Distribusi Gaya**")
        gc = DF["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        fig = px.bar(x=gc.values, y=gc.index, orientation="h",
                     color=gc.index, color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID}, text=gc.values)
        fig.update_layout(**pb(290),showlegend=False,xaxis_title="",yaxis_title="",
                          yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside",marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    with cb4:
        st.markdown("**Tren Gaya per Tahun**")
        dfg = DF[(DF["YEAR"] > 0) & DF["gaya_ilustrasi"].notna()].copy()
        dfg["gaya"] = dfg["gaya_ilustrasi"].map(GAYA_ID)
        trg = dfg.groupby(["YEAR","gaya"]).size().reset_index(name="n")
        fig2 = px.bar(trg, x="YEAR", y="n", color="gaya", barmode="stack",
                      color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID})
        fig2.update_layout(**pb(290),xaxis_title="",yaxis_title="",showlegend=True,
                           legend=dict(orientation="h",y=-.2,font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Distribusi Gaya Ilustrasi per Klaster Genre**")
    render_klaster_visual(DF, analysis_type="ilustrasi")

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Peta Panas Gaya Ilustrasi × Genre**")
    hn_gi = st.slider("Jumlah genre",6,20,12,2,key="hn_gi")
    st.plotly_chart(heatmap_gaya_genre(DF, hn_gi), use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    try:
        render_ilustrasi_komparatif(DF)
        st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    except Exception:
        pass

    st.markdown("**Figur Manusia vs Non-Manusia**")
    yh = int(DF["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
    dh = int(DF["detr_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
    tot = len(DF)
    agree = int((DF["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") &
                 DF["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")).sum())
    man_a, man_b, man_c = st.columns([2,1,2])
    with man_a:
        fig_man = go.Figure(data=[
            go.Bar(name="YOLOv8n",x=["Ada manusia","Tidak ada"],y=[yh,tot-yh],
                   marker_color=["#66BB6A","rgba(128,128,128,.15)"]),
            go.Bar(name="DETR",x=["Ada manusia","Tidak ada"],y=[dh,tot-dh],
                   marker_color=["#42A5F5","rgba(128,128,128,.08)"]),
        ])
        fig_man.update_layout(**pb(240),barmode="group",showlegend=True,
                              legend=dict(orientation="h",y=-.15),xaxis_title="",yaxis_title="")
        st.plotly_chart(fig_man, use_container_width=True)
    with man_b:
        st.metric("Sepakat keduanya",f"{agree:,}",f"{agree/tot*100:.1f}%")
        st.metric("Hanya YOLOv8n",f"{yh-agree:,}")
        st.metric("Hanya DETR",f"{dh-agree:,}")
    with man_c:
        st.markdown("**Top Objek Non-Manusia (YOLO)**")
        obj_ctr = Counter()
        for v in DF["yolo_objek"].dropna():
            s = str(v).strip()
            if s and s not in ("0","nan"):
                for o in s.split(","):
                    o = o.strip()
                    if o and o not in ("person","0"): obj_ctr[o] += 1
        if obj_ctr:
            top_obj = pd.DataFrame(obj_ctr.most_common(12), columns=["Objek","Jumlah"])
            fig_obj = px.bar(top_obj, x="Jumlah", y="Objek", orientation="h",
                             color_discrete_sequence=["#00ACC1"], text="Jumlah")
            fig_obj.update_layout(**pb(300),showlegend=False,xaxis_title="",yaxis_title="",
                                  yaxis=dict(categoryorder="total ascending"))
            fig_obj.update_traces(textposition="outside",marker_line_width=0)
            st.plotly_chart(fig_obj, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("### Confidence Tertinggi & Terendah per Gaya Ilustrasi")
    render_confidence_by_gaya(DF)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Contoh Buku — Confidence Tertinggi per Gaya**")
    df_gv = DF[DF["gaya_ilustrasi"].notna() & DF["image_ok"]].copy()
    df_gv["gaya_skor"] = pd.to_numeric(df_gv["gaya_skor"], errors="coerce")
    ex_gcols6 = st.columns(6)
    for gcol_ex, key in zip(ex_gcols6, GAYA_ID):
        sub_g = df_gv[df_gv["gaya_ilustrasi"] == key]
        if sub_g.empty: continue
        best_g = sub_g.nlargest(1,"gaya_skor").iloc[0]
        clr = GAYA_CLR[key]
        with gcol_ex:
            cp = cover_path(best_g.get("IMAGE_FILE"))
            if cp: st.image(cp, use_container_width=True)
            try: sg = f"{float(best_g.get('gaya_skor',0)):.2f}"
            except Exception: sg = "–"
            probs_bg = {k: float(best_g.get(f"gaya_prob_{k}",0) or 0) for k in GAYA_PROB_KEYS}
            bars_g = prob_bars(probs_bg, GAYA_CLR, GAYA_ID) if any(probs_bg.values()) else ""
            st.markdown(f'<div style="font-size:.62rem;padding:.25rem 0;">'
                        f'<div style="font-weight:600;color:{clr}">{GAYA_ID[key]}</div>'
                        f'<div style="opacity:.6;line-height:1.3">{str(best_g.get("TITLE",""))[:28]}</div>'
                        f'<div style="opacity:.5">skor {sg}</div>'
                        f'{"<div style=margin-top:.35rem>" + bars_g + "</div>" if bars_g else ""}</div>',
                        unsafe_allow_html=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Cari Buku berdasarkan Gaya Ilustrasi**")
    gic1, gic2, gic3, gic4 = st.columns([2,2,1,1])
    with gic1: q_gi = st.text_input("Judul / penulis", key="gi_q")
    with gic2:
        gaya_sel = st.selectbox("Filter gaya",["Semua"]+[GAYA_ID[k] for k in GAYA_ID],key="gi_sel")
    with gic3: ada_man = st.checkbox("Ada manusia", key="gi_man")
    with gic4: n_gi2 = st.slider("Tampilkan",4,32,8,4,key="gi_n")
    dgi = DF[DF["image_ok"]].copy()
    if q_gi:
        ql3 = q_gi.lower()
        dgi = dgi[dgi["TITLE"].str.lower().str.contains(ql3,na=False) |
                  dgi["AUTHOR"].str.lower().str.contains(ql3,na=False)]
    if ada_man:
        dgi = dgi[dgi["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") |
                  dgi["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")]
    if gaya_sel != "Semua":
        grev = {v: k for k, v in GAYA_ID.items()}
        dgi = dgi[dgi["gaya_ilustrasi"] == grev.get(gaya_sel,gaya_sel)]
    if not dgi.empty: grid(dgi.head(n_gi2), show_gi=True)

# ══════════════════════════════════════════════════════════════════════════════
# GENRE
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Genre":
    st.markdown("## Analisis Genre")
    with st.expander("Catatan metodologi & normalisasi", expanded=False):
        st.markdown(f"Genre dari metadata Goodreads (crowd-sourced, multi-label). "
                    f"Terdapat **{_n_unik} genre unik** setelah normalisasi.\n\n"
                    "**Overlap %** = `overlap / min(N_G1, N_G2)`")

    st.markdown("**Tiga Klaster Co-occurrence**")
    kl_leg = st.columns(3)
    for kc, kl in zip(kl_leg, KLASTER_COOC):
        genre_list_str = ", ".join(kl["genres"][:6]) + ("…" if len(kl["genres"]) > 6 else "")
        kc.markdown(
            f'<div style="background:{kl["bg"]};border-left:4px solid {kl["color"]};border-radius:0 8px 8px 0;padding:8px 12px;margin-bottom:4px;">'
            f'<div style="font-weight:600;color:{kl["color"]};font-size:12px;">[{kl["id"]}] {kl["label"].split("—")[0].strip()}</div>'
            f'<div style="font-size:11px;color:{kl["color"]};opacity:.8;margin-top:2px;">{kl["label"].split("—")[1].strip()}</div>'
            f'<div style="font-size:10px;opacity:.6;margin-top:4px;">{genre_list_str}</div></div>',
            unsafe_allow_html=True
        )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Tabel Co-occurrence Genre**")
    cooc_df, cooc_counts = compute_cooccurrence(DF)
    render_cooc_table(cooc_df, cooc_counts)

    with st.expander("Lihat semua pasangan genre"):
        display_df = cooc_df.copy()
        display_df.columns = ["Genre 1","Genre 2","N Genre 1","N Genre 2","Overlap","Overlap %"]
        for col in ["N Genre 1","N Genre 2","Overlap"]:
            display_df[col] = display_df[col].apply(lambda x: f"{int(x):,}".replace(",","."))
        display_df["Overlap %"] = display_df["Overlap %"].apply(lambda x: f"{int(x)}%")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Peta Panas Tumpang Tindih Genre**")
    all_items = [(g,n) for g,n in _gc.most_common() if g not in GENRE_EXCLUDE and n >= 3]
    n_co = st.slider("Jumlah genre teratas",8,min(len(all_items),30),16,2,key="n_co")
    top_co = [g for g, _ in all_items[:n_co]]
    co = pd.DataFrame(0, index=top_co, columns=top_co)
    for gl in expand_genres(DF["GENRES"], normalize=True):
        rel = [g for g in gl if g in top_co]
        for i, g1 in enumerate(rel):
            for g2 in rel[i+1:]:
                co.loc[g1,g2] += 1; co.loc[g2,g1] += 1
    for g in top_co: co.loc[g,g] = _gc[g]
    y_labels_co = []
    for g in top_co:
        kl = GENRE_KLASTER_MAP.get(g)
        y_labels_co.append(f"{g}  [{kl['id']}]" if kl else g)
    fig_co = go.Figure(data=go.Heatmap(
        z=co.values, x=y_labels_co, y=y_labels_co, colorscale="Oranges",
        text=co.values.astype(int).astype(str), texttemplate="%{text}", textfont=dict(size=9,color="#1A1A1A"),
        hovertemplate="Genre A: %{y}<br>Genre B: %{x}<br>Co-occurrence: %{z}<extra></extra>",
        showscale=True
    ))
    fig_co.update_layout(**pb(max(420,n_co*28),margin=dict(l=150,r=20,t=32,b=150),
                              xaxis=dict(tickangle=-40),yaxis=dict(autorange="reversed"),
                              xaxis_title="",yaxis_title=""))
    st.plotly_chart(fig_co, use_container_width=True)

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Analisis per Genre**")
    if "sel_genre" not in st.session_state:
        st.session_state["sel_genre"] = all_items[0][0] if all_items else None
    top_btn = [g for g, _ in all_items[:40]]
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
            st.info(f"Tidak ada buku dengan genre *{sel_genre}*.")
        else:
            kl = GENRE_KLASTER_MAP.get(sel_genre)
            st.markdown(f'#### Genre: **{sel_genre}** <span style="font-family:Inter;font-size:1rem;font-weight:400;opacity:.6">— {len(df_gs):,} buku</span>', unsafe_allow_html=True)
            if kl:
                st.markdown(f'<span style="font-size:.75rem;background:{kl["bg"]};color:{kl["color"]};padding:2px 10px;border-radius:10px;border:1px solid {kl["color"]}44;">[{kl["id"]}] {kl["label"]}</span>', unsafe_allow_html=True)
            tab_w, tab_tf, tab_gi = st.tabs(["Warna","Tipografi","Ilustrasi"])
            with tab_w:
                wc_g = compute_warna_distribusi(df_gs)
                wc_all = compute_warna_distribusi(DF)
                cw1, cw2 = st.columns(2)
                with cw1:
                    names_g = [w for w in WARNA_ORDER if wc_g.get(w,0) > 0]
                    fig_wg = px.pie(values=[wc_g[w] for w in names_g],
                                    names=[w.replace("_"," ") for w in names_g], hole=0.42,
                                    color=[w.replace("_"," ") for w in names_g],
                                    color_discrete_map={w.replace("_"," "): WARNA_HEX[w] for w in WARNA_ORDER})
                    fig_wg.update_layout(**pb(260)); fig_wg.update_traces(textinfo="percent+label",textfont_size=10)
                    st.plotly_chart(fig_wg, use_container_width=True)
                with cw2:
                    diff = (wc_g-wc_all).dropna().sort_values(ascending=False)
                    diff_df = diff.reset_index(); diff_df.columns = ["warna","delta"]
                    diff_df["warna_disp"] = diff_df["warna"].str.replace("_"," ")
                    fig_diff = px.bar(diff_df,x="delta",y="warna_disp",orientation="h",color="warna",color_discrete_map=WARNA_HEX)
                    fig_diff.update_layout(**pb(260),showlegend=False,xaxis_title="Simpangan proporsi",yaxis_title="",yaxis=dict(categoryorder="total ascending"))
                    fig_diff.add_vline(x=0,line_dash="dash",line_color="rgba(128,128,128,.4)")
                    st.plotly_chart(fig_diff, use_container_width=True)
            with tab_tf:
                df_gs_tf = df_gs[df_gs["typeface_kategori"].isin(TYPEFACE_ID.keys())]
                if df_gs_tf.empty:
                    st.info("Belum ada data tipografi untuk genre ini.")
                else:
                    tc_g = df_gs_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts()
                    tc_all = DF[DF["typeface_kategori"].isin(TYPEFACE_ID.keys())]["typeface_kategori"].map(TYPEFACE_ID).value_counts()
                    ctf1, ctf2 = st.columns(2)
                    with ctf1:
                        fig_tg = px.pie(values=tc_g.values, names=tc_g.index, hole=0.42,
                                        color=tc_g.index, color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID})
                        fig_tg.update_layout(**pb(250)); fig_tg.update_traces(textinfo="percent+label",textfont_size=10)
                        st.plotly_chart(fig_tg, use_container_width=True)
                    with ctf2:
                        diff_tf = (tc_g/len(df_gs_tf)-tc_all/tc_all.sum()).dropna().sort_values(ascending=False)
                        diff_tf_df = diff_tf.reset_index(); diff_tf_df.columns = ["tipografi","delta"]
                        fig_dtf = px.bar(diff_tf_df,x="delta",y="tipografi",orientation="h",color="tipografi",
                                         color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID})
                        fig_dtf.update_layout(**pb(250),showlegend=False,xaxis_title="Simpangan proporsi",yaxis_title="",yaxis=dict(categoryorder="total ascending"))
                        fig_dtf.add_vline(x=0,line_dash="dash",line_color="rgba(128,128,128,.4)")
                        st.plotly_chart(fig_dtf, use_container_width=True)
            with tab_gi:
                gc_g = df_gs["gaya_ilustrasi"].map(GAYA_ID).value_counts()
                gc_all_d = DF["gaya_ilustrasi"].map(GAYA_ID).value_counts()
                cg1, cg2 = st.columns(2)
                with cg1:
                    fig_gg = px.pie(values=gc_g.values, names=gc_g.index, hole=0.42,
                                    color=gc_g.index, color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID})
                    fig_gg.update_layout(**pb(250)); fig_gg.update_traces(textinfo="percent+label",textfont_size=10)
                    st.plotly_chart(fig_gg, use_container_width=True)
                with cg2:
                    diff_gi = (gc_g/len(df_gs)-gc_all_d/len(DF)).dropna().sort_values(ascending=False)
                    diff_gi_df = diff_gi.reset_index(); diff_gi_df.columns = ["gaya","delta"]
                    fig_dgi = px.bar(diff_gi_df,x="delta",y="gaya",orientation="h",color="gaya",
                                     color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID})
                    fig_dgi.update_layout(**pb(250),showlegend=False,xaxis_title="Simpangan proporsi",yaxis_title="",yaxis=dict(categoryorder="total ascending"))
                    fig_dgi.add_vline(x=0,line_dash="dash",line_color="rgba(128,128,128,.4)")
                    st.plotly_chart(fig_dgi, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ILLUSTRATOR
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Illustrator":
    st.markdown("## Illustrator Sampul")
    has_ill = DF["ILLUSTRATOR"].ne("")
    n_ill = has_ill.sum()
    n_no_ill = (~has_ill).sum()
    st.markdown(f"**{n_ill} buku** dari {len(DF):,} yang menyebutkan nama illustrator.")
    df_ill = DF[has_ill].copy()
    q_ill = st.text_input("Cari illustrator atau judul buku", key="ill_q")
    if q_ill:
        ql = q_ill.lower()
        df_ill = df_ill[df_ill["ILLUSTRATOR"].str.lower().str.contains(ql,na=False) |
                        df_ill["TITLE"].str.lower().str.contains(ql,na=False)]
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    ill_sum = (df_ill.groupby("ILLUSTRATOR").agg(
                   Buku=("TITLE","count"),
                   Judul=("TITLE",lambda x: " · ".join(x.values.tolist())),
                   Tahun=("YEAR",lambda x: ", ".join(sorted({str(int(v)) for v in x if v > 0})))
               ).reset_index().sort_values("Buku",ascending=False)
               .rename(columns={"ILLUSTRATOR":"Illustrator"}))
    st.dataframe(ill_sum, use_container_width=True, hide_index=True,
                 column_config={
                     "Illustrator":st.column_config.TextColumn(width="medium"),
                     "Buku":st.column_config.NumberColumn(width="small"),
                     "Judul":st.column_config.TextColumn(width="large"),
                     "Tahun":st.column_config.TextColumn(width="small"),
                 })

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("### Perbandingan: Dengan vs Tanpa Illustrator")
    df_with = DF[has_ill].copy()
    df_wout = DF[~has_ill].copy()
    for d_tmp in [df_with,df_wout]:
        for c in ["brightness_mean","saturation_mean","gaya_skor","typeface_skor","typeface_confidence"]:
            if c in d_tmp.columns: d_tmp[c] = pd.to_numeric(d_tmp[c],errors="coerce")
    met_cols = st.columns(4)
    for mcol,(lbl,col) in zip(met_cols,[
        ("Kecerahan","brightness_mean"),("Saturasi","saturation_mean"),
        ("Skor Gaya","gaya_skor"),("Skor Tipografi","typeface_confidence"),
    ]):
        v_w = df_with[col].mean() if col in df_with.columns else 0
        v_o = df_wout[col].mean() if col in df_wout.columns else 0
        mcol.metric(f"{lbl} (dengan ill.)",f"{v_w:.3f}",f"{v_w-v_o:+.3f} vs tanpa")

    st.markdown("**Distribusi Warna Keseluruhan**")
    wc_w = compute_warna_distribusi(df_with)
    wc_o = compute_warna_distribusi(df_wout)
    all_w = [w for w in WARNA_ORDER if wc_w.get(w,0) > 0 or wc_o.get(w,0) > 0]
    warna_cmp = pd.DataFrame({
        "Dengan Illustrator":[wc_w.get(w,0) for w in all_w],
        "Tanpa Illustrator":[wc_o.get(w,0) for w in all_w],
    }, index=[w.replace("_"," ") for w in all_w])
    fig_wc = go.Figure()
    fig_wc.add_trace(go.Bar(name="Dengan Illustrator",x=warna_cmp.index,y=warna_cmp["Dengan Illustrator"],
                            marker_color=[WARNA_HEX.get(w,"#999") for w in all_w],opacity=.9))
    fig_wc.add_trace(go.Bar(name="Tanpa Illustrator",x=warna_cmp.index,y=warna_cmp["Tanpa Illustrator"],
                            marker_color=[WARNA_HEX.get(w,"#999") for w in all_w],opacity=.35))
    fig_wc.update_layout(**pb(280),barmode="group",showlegend=True,xaxis_title="",yaxis_title="Proporsi",
                         legend=dict(orientation="h",y=-.15))
    st.plotly_chart(fig_wc, use_container_width=True)

    il2a, il2b = st.columns(2)
    with il2a:
        st.markdown("**Gaya Ilustrasi — Dengan Illustrator**")
        gc_w = df_with["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        fig_gw = px.pie(values=gc_w.values,names=gc_w.index,hole=.5,color=gc_w.index,
                        color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID})
        fig_gw.update_layout(**pb(240),showlegend=True,legend=dict(orientation="h",y=-.1,font=dict(size=10)))
        fig_gw.update_traces(textinfo="percent",textfont_size=10)
        st.plotly_chart(fig_gw, use_container_width=True)
    with il2b:
        st.markdown("**Gaya Ilustrasi — Tanpa Illustrator**")
        gc_o = df_wout["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        fig_go = px.pie(values=gc_o.values,names=gc_o.index,hole=.5,color=gc_o.index,
                        color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID})
        fig_go.update_layout(**pb(240),showlegend=True,legend=dict(orientation="h",y=-.1,font=dict(size=10)))
        fig_go.update_traces(textinfo="percent",textfont_size=10)
        st.plotly_chart(fig_go, use_container_width=True)

    st.markdown("**Simpangan Gaya: Dengan − Tanpa Illustrator**")
    diff_gaya = (gc_w/n_ill-gc_o/n_no_ill).dropna().sort_values(ascending=False)
    diff_gaya_df = diff_gaya.reset_index(); diff_gaya_df.columns = ["gaya","delta"]
    fig_dg = px.bar(diff_gaya_df,x="delta",y="gaya",orientation="h",color="gaya",
                    color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID})
    fig_dg.update_layout(**pb(240),showlegend=False,xaxis_title="Selisih proporsi",yaxis_title="",
                         yaxis=dict(categoryorder="total ascending"))
    fig_dg.add_vline(x=0,line_dash="dash",line_color="rgba(128,128,128,.4)")
    st.plotly_chart(fig_dg, use_container_width=True)
    st.markdown("<small style='opacity:.55'>Nilai positif = gaya lebih sering pada buku dengan illustrator.</small>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# JELAJAH BUKU
# ══════════════════════════════════════════════════════════════════════════════
elif HAL == "Jelajah Buku":
    st.markdown("## Jelajah Buku")
    st.markdown("Temukan buku dari kombinasi kriteria visual dan metadata.")
    top25_j = [g for g, _ in _gc.most_common() if g not in GENRE_EXCLUDE][:25]
    with st.form("form_jelajah"):
        r1 = st.columns(4)
        q_j     = r1[0].text_input("Judul / penulis")
        warna_j = r1[1].selectbox("Warna dominan",["Semua"]+sorted(DF["warna_kategori"].dropna().unique()),
                                   format_func=lambda w: "Semua" if w=="Semua" else w.replace("_"," ").capitalize())
        tf_j    = r1[2].selectbox("Tipografi",["Semua"]+[TYPEFACE_ID[k] for k in TYPEFACE_ID])
        gaya_j  = r1[3].selectbox("Gaya ilustrasi",["Semua"]+[GAYA_ID[k] for k in GAYA_ID])
        r2 = st.columns(4)
        genre_j = r2[0].selectbox("Genre",["Semua"]+top25_j)
        rak_j   = r2[1].selectbox("Rak",["Semua","Fiksi","Puisi"])
        ill_j   = r2[2].selectbox("Illustrator",["Semua","Dengan illustrator"])
        man_j   = r2[3].checkbox("Ada figur manusia")
        r3 = st.columns([3,1])
        n_j = r3[1].slider("Tampilkan",8,48,16,8)
        st.form_submit_button("Cari")

    dj = DF[DF["image_ok"]].copy()
    if q_j:
        ql = q_j.lower()
        dj = dj[dj["TITLE"].str.lower().str.contains(ql,na=False) |
                dj["AUTHOR"].str.lower().str.contains(ql,na=False)]
    if warna_j != "Semua": dj = dj[dj["warna_kategori"] == warna_j]
    if tf_j != "Semua":
        tf_rev3 = {v: k for k, v in TYPEFACE_ID.items()}
        dj = dj[dj["typeface_kategori"] == tf_rev3.get(tf_j, tf_j)]
    if gaya_j != "Semua":
        grev3 = {v: k for k, v in GAYA_ID.items()}
        dj = dj[dj["gaya_ilustrasi"] == grev3.get(gaya_j, gaya_j)]
    if genre_j != "Semua":
        gl_all = expand_genres(dj["GENRES"], normalize=True)
        mask_j = [genre_j in gl for gl in gl_all]
        dj = dj[mask_j]
    if rak_j == "Fiksi":   dj = dj[dj["SHELF"] == "fiksi"]
    elif rak_j == "Puisi": dj = dj[dj["SHELF"] == "puisi-asli"]
    if ill_j == "Dengan illustrator": dj = dj[dj["ILLUSTRATOR"].ne("")]
    if man_j:
        dj = dj[dj["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") |
                dj["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")]
    st.markdown(f"**{len(dj):,} buku ditemukan**")
    if not dj.empty: grid(dj.head(n_j), show_tf=True, show_gi=True)

