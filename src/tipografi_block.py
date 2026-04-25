"""
tipografi_block.py
==================
Blok analisis tipografi untuk Kartografi Sampul Sastra Indonesia (2000–2025).
Menggunakan data dari hasil_tipografi_v5 yang sudah dimerge ke data.csv.

Kolom v5 yang tersedia di DF:
  typeface_kategori  : unknown / script / sans_serif / modern_serif /
                       humanist_serif / display / slab_serif / transitional_serif
  typeface_low_conf  : True / False
  tipe_font          : nama font spesifik (Rozha One, Kalam, dsb.)
  font_source        : Google Fonts / DaFont / Adobe Fonts / CLIP_only
  match_type         : clip / clip_unlisted / ocr_exact / ocr_partial / no_image
  ocr_text           : teks yang berhasil di-OCR
  ocr_confidence     : skor OCR
  clip_font_1..5     : kandidat font dari CLIP
  clip_score_1..5    : skor CLIP per kandidat
  clip_cat_1..5      : kategori kandidat
  clip_margin        : selisih skor top-1 vs top-2

Panggil render_tipografi(DF) dari app utama di blok elif HAL == "Tipografi".

CHANGELOG:
  - FIX: "Romansa Kontemporer" ditambahkan ke GENRE_NORM lokal di expand_genres()
  - FIX: threshold _top_genres() diturunkan dari 5 → 3
  - FIX: indentasi blok with tab1..7 diperbaiki (masuk ke dalam render_tipografi)
  - BARU: Tab "⚖️ Perbandingan 5069 vs 2587" untuk melihat perbedaan dua subset data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ── Konstanta ────────────────────────────────────────────────────────────────

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

TYPEFACE_FONT_CSS = {
    "humanist_serif":     "Georgia, 'Times New Roman', serif",
    "transitional_serif": "'Palatino Linotype', Georgia, serif",
    "modern_serif":       "'Didot', 'Bodoni MT', Georgia, serif",
    "slab_serif":         "'Courier New', 'Rockwell', monospace",
    "sans_serif":         "Helvetica, Arial, sans-serif",
    "script":             "cursive",
    "display":            "Impact, 'Arial Black', fantasy",
    "unknown":            "inherit",
}

TYPEFACE_DESC = {
    "humanist_serif":     "Kontras sedang, axis diagonal mengikuti gerak tangan. Contoh: Garamond, Sabon.",
    "transitional_serif": "Kontras lebih tinggi, axis mendekati vertikal. Contoh: Baskerville, Times New Roman.",
    "modern_serif":       "Kontras ekstrem, serif hairline, axis vertikal tegas. Contoh: Bodoni, Didot.",
    "slab_serif":         "Serif persegi tebal, kontras rendah. Lahir untuk poster. Contoh: Clarendon, Rockwell.",
    "sans_serif":         "Tanpa serif, stroke seragam. Modernisme industri. Contoh: Helvetica, Futura.",
    "script":             "Stroke mengalir, menyerupai kaligrafi atau tulisan tangan.",
    "display":            "Bentuk sangat stilistik dan ornamental, untuk impak visual besar.",
    "unknown":            "Tidak dapat diklasifikasi oleh pipeline v5.",
}

TYPEFACE_LUPTON = {
    "humanist_serif":     "Abad ke-15. Menggabungkan kaligrafi dan Renaisans. Kesan klasik, humanis.",
    "transitional_serif": "Abad ke-18. Seiring mesin cetak presisi. Kesan formal, otoritatif.",
    "modern_serif":       "Akhir abad ke-18. Firmin Didot & Bodoni. Abstrak, geometris, modernitas awal.",
    "slab_serif":         "Abad ke-19. Poster dan iklan. Kokoh, tegas, mudah dibaca dari jauh.",
    "sans_serif":         "Abad ke-19–20. Bauhaus, Swiss typography. Bentuk mengikuti fungsi.",
    "script":             "Terinspirasi tulisan tangan. Kontras dan tekanan mengikuti pena tradisional.",
    "display":            "Tidak terikat sejarah tertentu. Menampung eksperimen bentuk. Maknanya kontekstual.",
    "unknown":            "—",
}

TF_ANALISIS = [k for k in TYPEFACE_ID if k != "unknown"]
TF_ALL = list(TYPEFACE_ID.keys())

# ── Extended Font → Typeface mapping ─────────────────────────────────────────
# Digunakan di apply_font_mapping() untuk mengisi typeface_kategori yang masih
# 'unknown' berdasarkan nama font di kolom tipe_font.
# Semua key huruf kecil — matching dilakukan case-insensitive.
EXTENDED_FONT_TO_TYPEFACE = {
    # script / handwriting
    'merienda': 'script', 'crafty girls': 'script', 'over the rainbow': 'script',
    'parisienne': 'script', 'mountains of christmas': 'script', 'homemade apple': 'script',
    'covered by your grace': 'script', 'swanky and moo moo': 'script', 'zeyada': 'script',
    'la belle aurore': 'script', 'norican': 'script', 'kiwi maru': 'script',
    'marck script': 'script', 'my soul': 'script', 'euphoria script': 'script',
    'allura': 'script', 'alex brush': 'script', 'petit formal script': 'script',
    'ruthie': 'script', 'stalemate': 'script', 'niconne': 'script', 'tangerine': 'script',
    'just another hand': 'script', 'handlee': 'script', 'rock salt': 'script',
    'luckiest guy': 'script', 'coming soon': 'script', 'gochi hand': 'script',
    'ink free': 'script', 'jua': 'script', 'architects daughter': 'script',
    'caveat': 'script', 'caveat brush': 'script', 'dancing script': 'script',
    'sacramento': 'script', 'great vibes': 'script', 'satisfy': 'script',
    'permanent marker': 'script', 'gloria hallelujah': 'script', 'kalam': 'script',
    'cookie': 'script', 'yellowtail': 'script', 'courgette': 'script',
    'pinyon script': 'script', 'patrick hand': 'script', 'indie flower': 'script',
    'shadows into light': 'script', 'amatic sc': 'script', 'special elite': 'script',
    'lobster': 'script', 'pacifico': 'script', 'boogaloo': 'script',
    'kaushan script': 'script', 'fredoka': 'script', 'abril fatface': 'script',
    'fredoka one': 'script', 'merienda one': 'script', 'comfortaa': 'script',
    'poiret one': 'script',
    # font lokal Indonesia
    'cerita': 'script', 'mister': 'script', 'kurnia': 'script', 'ketika': 'script',
    'rahasia': 'script', 'jakarta': 'sans_serif', 'jessica': 'script', 'series': 'sans_serif',
    'pulang': 'script', 'catatan': 'script', 'indonesia': 'display', 'nusantara': 'display',
    'garuda': 'display', 'aksara': 'display', 'pena': 'script',
    # slab_serif
    'ultra': 'slab_serif', 'kameron': 'slab_serif', 'kurale': 'slab_serif',
    'enriqueta': 'slab_serif', 'laila': 'slab_serif', 'rokkitt': 'slab_serif',
    'crete round': 'slab_serif', 'eczar': 'slab_serif', 'gimenez': 'slab_serif',
    'kreon': 'slab_serif', 'slabo 27px': 'slab_serif', 'bree serif': 'slab_serif',
    'aleo': 'slab_serif', 'alfa slab one': 'slab_serif', 'rockwell': 'slab_serif',
    'roboto slab': 'slab_serif', 'zilla slab': 'slab_serif', 'bitter': 'slab_serif',
    'arvo': 'slab_serif', 'josefin slab': 'slab_serif', 'chaparral pro': 'slab_serif',
    'podkova': 'slab_serif', 'rasa': 'slab_serif', 'scope one': 'slab_serif',
    'sura': 'slab_serif',
    # modern_serif
    'gfs didot': 'modern_serif', 'noto serif display': 'modern_serif', 'unna': 'modern_serif',
    'tienne': 'modern_serif', 'artifika': 'modern_serif', 'cambo': 'modern_serif',
    'fenix': 'modern_serif', 'hedvig letters serif': 'modern_serif', 'rufina': 'modern_serif',
    'bodoni moda': 'modern_serif', 'dm serif display': 'modern_serif',
    'marcellus': 'modern_serif', 'cinzel': 'modern_serif', 'cinzel decorative': 'modern_serif',
    'yeseva one': 'modern_serif', 'rozha one': 'modern_serif', 'fraunces': 'modern_serif',
    'trajan pro 3': 'modern_serif',
    # transitional_serif
    'martel': 'transitional_serif', 'petrona': 'transitional_serif',
    'solway': 'transitional_serif', 'trocchi': 'transitional_serif',
    'volkhov': 'transitional_serif', 'playfair display': 'transitional_serif',
    'playfair display sc': 'transitional_serif', 'spectral': 'transitional_serif',
    'merriweather': 'transitional_serif', 'libre baskerville': 'transitional_serif',
    'noto serif': 'transitional_serif', 'ibm plex serif': 'transitional_serif',
    'vidaloka': 'transitional_serif', 'lora': 'transitional_serif',
    # humanist_serif
    'gentium book plus': 'humanist_serif', 'karma': 'humanist_serif',
    'neuton': 'humanist_serif', 'proza libre': 'humanist_serif',
    'piazzolla': 'humanist_serif', 'oranienbaum': 'humanist_serif',
    'im fell english': 'humanist_serif', 'kepler std': 'humanist_serif',
    'mrs eaves': 'humanist_serif', 'sabon next': 'humanist_serif',
    'almendra': 'humanist_serif', 'ff scala': 'humanist_serif',
    'cormorant': 'humanist_serif', 'alegreya': 'humanist_serif',
    'lustria': 'humanist_serif', 'cardo': 'humanist_serif', 'judson': 'humanist_serif',
    'cormorant infant': 'humanist_serif', 'philosopher': 'humanist_serif',
    'cormorant garamond': 'humanist_serif', 'garamond': 'humanist_serif',
    'arno pro': 'humanist_serif', 'garamond premier pro': 'humanist_serif',
    'calluna': 'humanist_serif', 'georgia': 'humanist_serif', 'vollkorn': 'humanist_serif',
    # sans_serif
    'rajdhani': 'sans_serif', 'be vietnam pro': 'sans_serif', 'ubuntu': 'sans_serif',
    'hanken grotesk': 'sans_serif', 'cairo': 'sans_serif', 'brandon grotesque': 'sans_serif',
    'gill sans nova': 'sans_serif', 'itc franklin gothic': 'sans_serif', 'teko': 'sans_serif',
    'geologica': 'sans_serif', 'quicksand': 'sans_serif', 'poppins': 'sans_serif',
    'league spartan': 'sans_serif', 'karla': 'sans_serif', 'outfit': 'sans_serif',
    'trebuchet ms': 'sans_serif', 'josefin sans': 'sans_serif', 'montserrat': 'sans_serif',
    'ibm plex sans': 'sans_serif', 'urbanist': 'sans_serif', 'oswald': 'sans_serif',
    # display
    'creepster': 'display', 'pirata one': 'display', 'lilita one': 'display',
    'press start 2p': 'display', 'fjalla one': 'display', 'almendra display': 'display',
    'league gothic': 'display', 'michroma': 'display', 'exo': 'display',
    'sancreek': 'display', 'pixelify sans': 'display', 'gasoek one': 'display',
    'rubik one': 'display', 'grenze gotisch': 'display', 'black ops one': 'display',
    'bangers': 'display', 'new rocker': 'display', 'bebas neue': 'display',
    'anton': 'display', 'passion one': 'display', 'righteous': 'display',
    'unbounded': 'display', 'metamorphous': 'display', 'metal mania': 'display',
    'rye': 'display', 'uncial antiqua': 'display', 'impact': 'display',
    'freight display pro': 'display', 'orbitron': 'display', 'electrolize': 'display',
    'audiowide': 'display', 'share tech': 'display', 'vt323': 'display',
    'faster one': 'display', 'bowlby one sc': 'display', 'fredericka the great': 'display',
    'grenze': 'display',
}


def apply_font_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """
    Patch typeface_kategori langsung di DF untuk semua baris yang masih 'unknown'
    dengan mencari nama font (tipe_font) di EXTENDED_FONT_TO_TYPEFACE.

    Kolom baru yang ditambahkan:
      - typeface_kategori_orig : salinan typeface_kategori sebelum di-patch
                                 (berguna untuk audit / perbandingan di tab ⚖️)

    Kolom typeface_kategori langsung diupdate agar seluruh tab bekerja
    tanpa perubahan apapun.
    """
    df = df.copy()
    mapping = {k.lower(): v for k, v in EXTENDED_FONT_TO_TYPEFACE.items()}

    # Simpan versi asli dulu
    df["typeface_kategori_orig"] = df["typeface_kategori"].copy()

    mask_unknown = df["typeface_kategori"].astype(str).str.strip() == "unknown"
    fonts = df.loc[mask_unknown, "tipe_font"].astype(str).str.strip().str.lower()
    resolved = fonts.map(lambda f: mapping.get(f, "unknown"))
    df.loc[mask_unknown, "typeface_kategori"] = resolved

    return df


FONT_SOURCE_CLR = {
    "Google Fonts": "#4285F4",
    "DaFont":       "#E53935",
    "Adobe Fonts":  "#FF0000",
    "CLIP_only":    "#9E9E9E",
}

MATCH_TYPE_ID = {
    "ocr_exact":    "OCR Exact",
    "ocr_partial":  "OCR Partial",
    "clip":         "CLIP+DB",
    "clip_unlisted":"CLIP Only",
    "no_image":     "No Image",
}

MATCH_TYPE_CLR = {
    "ocr_exact":    "#2E7D32",
    "ocr_partial":  "#558B2F",
    "clip":         "#1565C0",
    "clip_unlisted":"#6A1B9A",
    "no_image":     "#BDBDBD",
}

COVER_DIR = os.path.join(os.path.dirname(__file__), "..", "covers")

# ── Klaster Genre ──────────────────────────────────────────────────────────────

KLASTER_COOC = [
    {
        "id": "K1", "label": "Klaster 1 — Novel sebagai genre bentuk yang dominan",
        "short": "Klaster 1", "color": "#2E4057", "bg": "#EEF2F7",
        "genres": ["Novel", "Cerita Pendek", "Antologi", "Puisi"],
    },
    {
        "id": "K2", "label": "Klaster 2 — Romansa sebagai gravitasi genre tematik",
        "short": "Klaster 2", "color": "#993556", "bg": "#FBF0F3",
        "genres": ["Romansa", "Chick Lit", "Persahabatan", "Remaja", "Dewasa",
                   "Keluarga", "Drama", "Slice of Life", "Komedi"],
    },
    {
        "id": "K3", "label": "Klaster 3 — Eskapisme: fantasi, aksi & ketegangan",
        "short": "Klaster 3", "color": "#1D9E75", "bg": "#EEF8F4",
        "genres": ["Fantasi", "Fiksi Sejarah", "Petualangan", "Aksi", "Fiksi Sains",
                   "Thriller/Misteri", "Horor", "Anak-anak"],
    },
]

GENRE_KLASTER_MAP_LOCAL = {}
for _kl in KLASTER_COOC:
    for _g in _kl["genres"]:
        if _g not in GENRE_KLASTER_MAP_LOCAL:
            GENRE_KLASTER_MAP_LOCAL[_g] = _kl


# ── Helpers ────────────────────────────────────────────────────────────────────

def cover_path(img):
    if not img or str(img) in ("", "nan"):
        return None
    p = os.path.join(COVER_DIR, str(img))
    return p if os.path.exists(p) else None


def pb(height=320, **kw):
    b = dict(
        height=height,
        margin=dict(l=8, r=8, t=28, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color="#1A1A1A"),
    )
    b.update(kw)
    return b


def _klaster_label(genre):
    kl = GENRE_KLASTER_MAP_LOCAL.get(genre)
    return f"{genre}  [{kl['id']}]" if kl else genre


def _section_header(title, subtitle="", color="#2E4057", bg="#EEF2F7"):
    st.markdown(
        f'<div style="background:{bg};border-left:4px solid {color};'
        f'border-radius:0 8px 8px 0;padding:8px 14px;margin:1.2rem 0 .6rem;">'
        f'<div style="font-family:Lora,serif;font-weight:600;color:{color};font-size:.95rem;">{title}</div>'
        f'{"<div style=font-size:.72rem;color:"+color+";opacity:.7;margin-top:3px;>"+subtitle+"</div>" if subtitle else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _konfidence_badge(match_type, low_conf):
    if match_type == "ocr_exact":
        return '<span style="background:#E8F5E9;color:#1B5E20;border-radius:10px;padding:1px 7px;font-size:.6rem;font-weight:700;">✓ OCR Exact</span>'
    elif match_type == "ocr_partial":
        return '<span style="background:#F1F8E9;color:#33691E;border-radius:10px;padding:1px 7px;font-size:.6rem;">~ OCR Partial</span>'
    elif match_type == "clip" and not low_conf:
        return '<span style="background:#E3F2FD;color:#0D47A1;border-radius:10px;padding:1px 7px;font-size:.6rem;">CLIP+DB</span>'
    elif match_type == "clip" and low_conf:
        return '<span style="background:#EDE7F6;color:#4527A0;border-radius:10px;padding:1px 7px;font-size:.6rem;">CLIP+DB ⚠</span>'
    elif match_type == "clip_unlisted":
        return '<span style="background:#FCE4EC;color:#880E4F;border-radius:10px;padding:1px 7px;font-size:.6rem;">CLIP only</span>'
    return '<span style="background:#F5F5F5;color:#888;border-radius:10px;padding:1px 7px;font-size:.6rem;">–</span>'


def expand_genres(series, normalize=True):
    GENRE_NORM = {
        "Cinta":                "Romansa",
        "Roman":                "Romansa",
        "Romansa Kontemporer":  "Romansa",
        "Roman Kontemporer":    "Romansa",
        "Romantis":             "Romansa",
        "Romance":              "Romansa",
        "Kontemporer":          "Romansa",
        "Romansatic":           "Romansa",
        "Young Adult Romansace":"Romansa",
        "Thriller":             "Thriller/Misteri",
        "Misteri":              "Thriller/Misteri",
        "Misteri Thriller":     "Thriller/Misteri",
        "Thriller Suspense":    "Thriller/Misteri",
        "Psychological Thriller":"Thriller/Misteri",
        "Suspense":             "Thriller/Misteri",
        "Detective":            "Thriller/Misteri",
        "Kriminal":             "Thriller/Misteri",
        "Supranatural":         "Horor",
        "Humor":                "Komedi",
        "New Adult":            "Remaja",
        "Collections":          "Antologi",
        "Middle Grade":         "Fantasi",
        "Fiksi Ilmiah":         "Fiksi Sains",
        "Distopia":             "Fiksi Sains",
        "Sejarah":              "Fiksi Sejarah",
        "Historical Fiction":   "Fiksi Sejarah",
        "Historical":           "Fiksi Sejarah",
    }
    out = []
    for v in series:
        if pd.isna(v) or str(v).strip() == "":
            out.append([])
            continue
        raw = [g.strip() for g in str(v).split(",") if g.strip()]
        if normalize:
            seen, normed = set(), []
            for g in raw:
                g2 = GENRE_NORM.get(g, g)
                if g2 not in seen:
                    normed.append(g2)
                    seen.add(g2)
            out.append(normed)
        else:
            out.append(raw)
    return out


def _top_genres(df, n=16):
    from collections import Counter
    GENRE_EXCLUDE = {"Sastra Indonesia", "Sastra", "Fiksi", "Nonfiction", "Non-fiction",
                     "Nonfiksi", "Non Fiksi", "Non-fiksi"}
    c = Counter()
    for gl in expand_genres(df["GENRES"], normalize=True):
        c.update(gl)
    return [g for g, cnt in c.most_common() if g not in GENRE_EXCLUDE and cnt >= 3][:n]


def _genre_mask(df, genre):
    gl = expand_genres(df["GENRES"], normalize=True)
    return [genre in g for g in gl]


def _effective_cat(row):
    cat = str(row.get("typeface_kategori", "unknown") or "unknown")
    if cat != "unknown":
        return cat
    return str(row.get("clip_cat_1", "unknown") or "unknown")


def _get_title_col(df):
    """Cari kolom judul — bisa 'TITLE' atau 'title'."""
    for c in ["TITLE", "title"]:
        if c in df.columns:
            return c
    return None


# ── Tab 1: Gambaran Umum ───────────────────────────────────────────────────────

def _tab_gambaran(df):
    df_known = df[df["typeface_kategori"].isin(TF_ANALISIS)].copy()
    df_low   = df[df["typeface_low_conf"].astype(str).str.upper() == "TRUE"]
    df_high  = df[df["typeface_low_conf"].astype(str).str.upper() == "FALSE"]
    n_unknown = (df["typeface_kategori"] == "unknown").sum()
    n_total   = len(df)

    c1, c2, c3, c4 = st.columns(4)
    stats = [
        ("Terklasifikasi",       len(df_known), f"{len(df_known)/n_total*100:.1f}% dari total", "#8E24AA"),
        ("Tidak Terklasifikasi", n_unknown,     f"{n_unknown/n_total*100:.1f}% dari total",     "#BDBDBD"),
        ("High Confidence",      len(df_high),  "low_conf = False",                              "#2E7D32"),
        ("Low Confidence",       len(df_low),   "low_conf = True",                               "#E65100"),
    ]
    for col, (lbl, val, sub, clr) in zip([c1, c2, c3, c4], stats):
        with col:
            st.markdown(
                f'<div style="border:1px solid {clr}30;border-top:3px solid {clr};'
                f'border-radius:0 0 8px 8px;padding:.6rem .7rem;margin-bottom:.4rem;">'
                f'<div style="font-size:.65rem;color:#888;">{lbl}</div>'
                f'<div style="font-size:1.5rem;font-weight:700;color:{clr};">{val:,}</div>'
                f'<div style="font-size:.6rem;color:#aaa;">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<hr style='margin:.5rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)

    ca, cb = st.columns(2)
    with ca:
        st.markdown("**Distribusi Typeface (terklasifikasi)**")
        tc = df_known["typeface_kategori"].map(TYPEFACE_ID).value_counts()
        fig = px.bar(
            x=tc.values, y=tc.index, orientation="h",
            color=tc.index,
            color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
            text=tc.values,
        )
        fig.update_layout(**pb(290), showlegend=False, xaxis_title="", yaxis_title="",
                          yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with cb:
        st.markdown("**Metode Klasifikasi (match_type)**")
        mt = df["match_type"].map(MATCH_TYPE_ID).value_counts()
        fig2 = px.pie(
            values=mt.values, names=mt.index, hole=0.42,
            color=mt.index,
            color_discrete_map={MATCH_TYPE_ID[k]: MATCH_TYPE_CLR[k] for k in MATCH_TYPE_ID},
        )
        fig2.update_layout(**pb(290))
        fig2.update_traces(textinfo="percent+label", textfont_size=10)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<hr style='margin:.5rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    st.markdown("**Tren Typeface per Tahun (terklasifikasi)**")
    df_yr = df_known[df_known["YEAR"] > 0].copy()
    df_yr["tf"] = df_yr["typeface_kategori"].map(TYPEFACE_ID)
    tr = df_yr.groupby(["YEAR", "tf"]).size().reset_index(name="n")
    fig3 = px.bar(
        tr, x="YEAR", y="n", color="tf", barmode="stack",
        color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
    )
    fig3.update_layout(**pb(320), xaxis_title="", yaxis_title="",
                       legend=dict(orientation="h", y=-.2, font=dict(size=9)))
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("<hr style='margin:.5rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    st.markdown("**Pergeseran Tipografi per Dekade**")
    df_dk = df_known[df_known["YEAR"] > 0].copy()
    df_dk["tf_label"] = df_dk["typeface_kategori"].map(TYPEFACE_ID)
    df_dk["dekade"] = pd.cut(
        df_dk["YEAR"],
        bins=[1999, 2004, 2009, 2014, 2019, 2025],
        labels=["2000–04", "2005–09", "2010–14", "2015–19", "2020–25"],
    )
    shift = df_dk.groupby(["dekade", "tf_label"], observed=True).size().reset_index(name="n")
    shift["prop"] = shift.groupby("dekade", observed=True)["n"].transform(lambda x: x / x.sum())
    fig4 = px.line(
        shift, x="dekade", y="prop", color="tf_label", markers=True,
        color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
        labels={"dekade": "", "prop": "Proporsi", "tf_label": "Typeface"},
    )
    fig4.update_layout(**pb(320), legend=dict(orientation="h", y=-.22, font=dict(size=10)))
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("<hr style='margin:.5rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    st.markdown("**Sumber Font**")
    src = df["font_source"].value_counts()
    fig5 = px.bar(
        x=src.values, y=src.index, orientation="h",
        color=src.index, color_discrete_map=FONT_SOURCE_CLR, text=src.values,
    )
    fig5.update_layout(**pb(240), showlegend=False, xaxis_title="", yaxis_title="",
                       yaxis=dict(categoryorder="total ascending"))
    fig5.update_traces(textposition="outside", marker_line_width=0)
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown("<hr style='margin:.5rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    with st.expander("⚠️ Catatan Metodologis dan Keterbatasan Data (v5)", expanded=False):
        st.markdown("""
**Pipeline v5 menggunakan pendekatan DB-first:**
1. OCR (EasyOCR) mendeteksi teks di sampul → fuzzy matching ke metadata judul/penulis
2. Teks yang cocok di-query ke Google Fonts + DaFont → kategori typeface dari database
3. Jika tidak ditemukan di DB, CLIP ViT-B/32 mengklasifikasi langsung dari fitur visual

**Tiga keterbatasan utama:**

**1. 48.2% `unknown`** — Bukan bug sepenuhnya. Sekitar 1.032 dapat di-recover.
Sisanya ~1.187 genuinely unclassifiable.

**2. Dominasi Rozha One** — 608 sampul (13.2%) terdeteksi sebagai Rozha One, semuanya `clip_unlisted`.
Rozha One diklasifikasikan sebagai `modern_serif` karena kontras stroke, tapi secara tipografis ia lebih
tepat disebut *display-serif*. Klaim tentang dominasi `modern_serif` perlu dibaca dengan hati-hati.

**3. Script bias CLIP** — Ketika `unknown`, `clip_cat_1` cenderung menebak `script` (1.151 dari 2.219 unknown).
Ini mencerminkan bias CLIP terhadap stroke yang mengalir, bukan selalu mencerminkan font yang sebenarnya.

**Rekomendasi pembacaan:** Gunakan lapisan High Confidence (`typeface_low_conf = False`, n=1.537)
untuk klaim yang kuat; gunakan keseluruhan data untuk melihat tren.
        """)


# ── Tab 2: Heatmap Genre ───────────────────────────────────────────────────────

def _tab_heatmap_genre(df):
    st.markdown("**Peta Panas Typeface × Genre**")

    col_opt1, col_opt2 = st.columns([3, 1])
    with col_opt1:
        lapisan = st.radio(
            "Lapisan data",
            ["Semua terklasifikasi", "High confidence saja", "Termasuk CLIP fallback (incl. unknown)"],
            key="hm_lapisan",
            horizontal=True,
        )
    with col_opt2:
        n_genre = st.slider("Jumlah genre", 6, 20, 12, 2, key="hm_n_genre")

    if lapisan == "High confidence saja":
        df_hm = df[df["typeface_low_conf"].astype(str).str.upper() == "FALSE"].copy()
        df_hm = df_hm[df_hm["typeface_kategori"].isin(TF_ANALISIS)]
        cat_col = "typeface_kategori"
    elif lapisan == "Termasuk CLIP fallback (incl. unknown)":
        df_hm = df.copy()
        df_hm["_eff_cat"] = df_hm.apply(_effective_cat, axis=1)
        df_hm = df_hm[df_hm["_eff_cat"].isin(TF_ANALISIS)]
        cat_col = "_eff_cat"
    else:
        df_hm = df[df["typeface_kategori"].isin(TF_ANALISIS)].copy()
        cat_col = "typeface_kategori"

    st.caption(f"n = {len(df_hm):,} buku dalam lapisan ini")

    genres = _top_genres(df_hm, n_genre)
    tf_keys = TF_ANALISIS
    tf_labels = [TYPEFACE_ID[k] for k in tf_keys]
    y_labels = [_klaster_label(g) for g in genres]

    mat = pd.DataFrame(0.0, index=genres, columns=tf_labels)
    genre_lists = expand_genres(df_hm["GENRES"], normalize=True)

    for g in genres:
        mask = [g in gl for gl in genre_lists]
        sub = df_hm[mask]
        if sub.empty:
            continue
        vc = sub[cat_col].map(TYPEFACE_ID).value_counts(normalize=True)
        for k in tf_keys:
            mat.loc[g, TYPEFACE_ID[k]] = vc.get(TYPEFACE_ID[k], 0.0)

    text_mat = (mat * 100).round(0).astype(int).astype(str) + "%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=tf_labels, y=y_labels,
        colorscale="Purples",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=10, color="#1A1A1A"),
        showscale=True, zmin=0, zmax=1,
    ))
    fig.update_layout(**pb(
        max(340, n_genre * 32),
        margin=dict(l=190, r=20, t=32, b=90),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickangle=-30),
        xaxis_title="", yaxis_title="",
    ))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr style='margin:.5rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    st.markdown("**Simpangan per Genre dari Rata-rata Korpus**")
    st.caption("Positif = genre lebih banyak memakai typeface ini dibanding rata-rata keseluruhan.")

    tc_all = df_hm[cat_col].map(TYPEFACE_ID).value_counts(normalize=True)
    rows_diff = []
    for g in genres:
        mask = [g in gl for gl in genre_lists]
        sub = df_hm[mask]
        if sub.empty:
            continue
        tc_g = sub[cat_col].map(TYPEFACE_ID).value_counts(normalize=True)
        genre_display = _klaster_label(g)
        for k in tf_keys:
            lbl = TYPEFACE_ID[k]
            rows_diff.append({
                "Genre": genre_display,
                "Typeface": lbl,
                "Delta": tc_g.get(lbl, 0) - tc_all.get(lbl, 0),
            })

    df_diff = pd.DataFrame(rows_diff)
    if not df_diff.empty:
        fig_d = px.bar(
            df_diff, x="Delta", y="Genre", color="Typeface",
            orientation="h", barmode="group",
            color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
        )
        fig_d.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.35)")
        fig_d.update_layout(
            **pb(max(300, n_genre * 55), margin=dict(l=200, r=20, t=28, b=50)),
            xaxis_title="Selisih proporsi vs korpus", yaxis_title="",
            legend=dict(orientation="h", y=-.18, font=dict(size=9)),
        )
        st.plotly_chart(fig_d, use_container_width=True)


# ── Tab 3: Per Genre ───────────────────────────────────────────────────────────

def _tab_per_genre(df):
    genre_opts = _top_genres(df, 30)
    if not genre_opts:
        st.info("Tidak ada data genre yang cukup.")
        return

    col_g1, col_g2 = st.columns([3, 1])
    with col_g1:
        sel_genre = st.selectbox(
            "Pilih genre", options=genre_opts,
            format_func=_klaster_label, key="tf_per_genre_sel",
        )
    with col_g2:
        lapisan_pg = st.radio("Lapisan", ["Semua", "High conf"],
                              key="tf_per_genre_lapisan", horizontal=True)

    mask_g = _genre_mask(df, sel_genre)
    df_g = df[mask_g].copy()
    if lapisan_pg == "High conf":
        df_g = df_g[df_g["typeface_low_conf"].astype(str).str.upper() == "FALSE"]

    df_g_known = df_g[df_g["typeface_kategori"].isin(TF_ANALISIS)]
    n_total_g = len(df_g)
    n_known_g = len(df_g_known)

    if df_g.empty:
        st.info(f"Tidak ada data untuk genre *{sel_genre}*.")
        return

    kl_obj = GENRE_KLASTER_MAP_LOCAL.get(sel_genre)
    kl_badge = ""
    if kl_obj:
        kl_badge = (
            f'<span style="background:{kl_obj["bg"]};color:{kl_obj["color"]};'
            f'border-radius:8px;padding:1px 8px;font-size:.68rem;font-weight:600;'
            f'margin-left:8px;">[{kl_obj["id"]}] {kl_obj["label"].split("—")[1].strip()}</span>'
        )

    st.markdown(
        f'<div style="padding:6px 14px;background:#F3E5F5;border-left:4px solid #8E24AA;'
        f'border-radius:0 8px 8px 0;margin:.5rem 0;">'
        f'<b style="color:#6A1B9A;">{sel_genre}</b>{kl_badge}'
        f'<span style="font-size:.72rem;color:#888;margin-left:10px;">'
        f'{n_total_g:,} buku total · {n_known_g:,} terklasifikasi typeface</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    ca, cb, cc = st.columns(3)

    with ca:
        st.markdown("**Distribusi Typeface**")
        if df_g_known.empty:
            st.caption("Tidak ada data.")
        else:
            tc_g = df_g_known["typeface_kategori"].map(TYPEFACE_ID).value_counts()
            fig_pie = px.pie(
                values=tc_g.values, names=tc_g.index, hole=0.42,
                color=tc_g.index,
                color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
            )
            fig_pie.update_layout(**pb(240))
            fig_pie.update_traces(textinfo="percent+label", textfont_size=9)
            st.plotly_chart(fig_pie, use_container_width=True)

    with cb:
        st.markdown("**Simpangan dari Korpus**")
        if df_g_known.empty:
            st.caption("—")
        else:
            df_all_k = df[df["typeface_kategori"].isin(TF_ANALISIS)]
            tc_all = df_all_k["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)
            tc_gn  = df_g_known["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)
            diff   = (tc_gn - tc_all).dropna().sort_values(ascending=False)
            d_df   = diff.reset_index()
            d_df.columns = ["tipografi", "delta"]
            fig_d2 = px.bar(
                d_df, x="delta", y="tipografi", orientation="h",
                color="tipografi",
                color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
            )
            fig_d2.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
            fig_d2.update_layout(**pb(240), showlegend=False,
                                  xaxis_title="Selisih vs korpus", yaxis_title="",
                                  yaxis=dict(categoryorder="total ascending"))
            st.plotly_chart(fig_d2, use_container_width=True)

    with cc:
        st.markdown("**Font Spesifik Terbanyak**")
        top_fonts = df_g["tipe_font"].dropna().value_counts().head(10)
        if top_fonts.empty:
            st.caption("—")
        else:
            font_cats = {}
            for fn in top_fonts.index:
                sub_f = df_g[df_g["tipe_font"] == fn]
                cat = sub_f["typeface_kategori"].mode()
                font_cats[fn] = cat.iloc[0] if len(cat) > 0 else "unknown"

            fig_f = px.bar(
                x=top_fonts.values, y=top_fonts.index, orientation="h",
                color=[TYPEFACE_ID.get(font_cats.get(fn, "unknown"), "?") for fn in top_fonts.index],
                color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
                text=top_fonts.values,
            )
            fig_f.update_layout(**pb(240), showlegend=False, xaxis_title="", yaxis_title="",
                                 yaxis=dict(categoryorder="total ascending"))
            fig_f.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_f, use_container_width=True)

    st.markdown("<hr style='margin:.5rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    st.markdown("**Contoh Sampul per Typeface**")
    st.caption("Buku dengan skor OCR confidence tertinggi per kategori.")

    # pastikan kolom image_ok ada
    if "image_ok" not in df_g_known.columns:
        st.caption("Kolom image_ok tidak tersedia.")
        return

    df_g_img = df_g_known[df_g_known["image_ok"].astype(str).str.upper() == "TRUE"].copy()
    df_g_img["ocr_confidence"] = pd.to_numeric(df_g_img["ocr_confidence"], errors="coerce")

    tf_present = [k for k in TF_ANALISIS if k in df_g_img["typeface_kategori"].values]
    if not tf_present:
        st.caption("Tidak ada sampul dengan gambar untuk genre ini.")
        return

    ex_cols = st.columns(min(len(tf_present), 7))
    for col_ex, tk in zip(ex_cols, tf_present):
        sub_tk = df_g_img[df_g_img["typeface_kategori"] == tk]
        if sub_tk.empty:
            continue
        high = sub_tk[sub_tk["typeface_low_conf"].astype(str).str.upper() == "FALSE"]
        pool = high if not high.empty else sub_tk
        best = pool.sort_values("ocr_confidence", ascending=False).iloc[0]
        clr = TYPEFACE_CLR.get(tk, "#999")
        with col_ex:
            cp = cover_path(best.get("IMAGE_FILE"))
            if cp:
                st.image(cp, use_container_width=True)
            else:
                st.markdown(
                    '<div style="height:140px;background:rgba(128,128,128,.08);'
                    'border-radius:6px;display:flex;align-items:center;'
                    'justify-content:center;font-size:1.5rem;">📖</div>',
                    unsafe_allow_html=True,
                )
            font_name = str(best.get("tipe_font", "—") or "—")
            match_t   = str(best.get("match_type", "") or "")
            low_c     = str(best.get("typeface_low_conf", "")).upper() == "TRUE"
            st.markdown(
                f'<div style="font-size:.6rem;padding:.2rem 0;text-align:center;">'
                f'<div style="font-weight:700;color:{clr}">{TYPEFACE_ID.get(tk, tk)}</div>'
                f'<div style="opacity:.65;margin:.1rem 0;">{font_name[:22]}</div>'
                f'{_konfidence_badge(match_t, low_c)}'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<hr style='margin:.5rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    st.markdown("**Tren Typeface per Tahun**")
    df_g_yr = df_g_known[df_g_known["YEAR"] > 0].copy()
    if len(df_g_yr) < 5:
        st.caption("Data tidak cukup untuk tren.")
        return
    df_g_yr["tf"] = df_g_yr["typeface_kategori"].map(TYPEFACE_ID)
    tr_g = df_g_yr.groupby(["YEAR", "tf"]).size().reset_index(name="n")
    fig_tr = px.bar(
        tr_g, x="YEAR", y="n", color="tf", barmode="stack",
        color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
    )
    fig_tr.update_layout(**pb(270), xaxis_title="", yaxis_title="",
                          legend=dict(orientation="h", y=-.22, font=dict(size=9)))
    st.plotly_chart(fig_tr, use_container_width=True)


# ── Tab 4: Font Spesifik ───────────────────────────────────────────────────────

def _tab_font_spesifik(df):
    st.markdown("**Font Terbanyak di Seluruh Dataset**")

    lapisan_fs = st.radio(
        "Lapisan",
        ["Semua buku", "Hanya terklasifikasi", "High confidence"],
        key="fs_lapisan", horizontal=True,
    )
    if lapisan_fs == "Hanya terklasifikasi":
        df_fs = df[df["typeface_kategori"].isin(TF_ANALISIS)].copy()
    elif lapisan_fs == "High confidence":
        df_fs = df[
            (df["typeface_low_conf"].astype(str).str.upper() == "FALSE") &
            (df["typeface_kategori"].isin(TF_ANALISIS))
        ].copy()
    else:
        df_fs = df.copy()

    n_top = st.slider("Top N font", 10, 40, 20, 5, key="fs_n_top")
    top_fonts = df_fs["tipe_font"].dropna().value_counts().head(n_top)

    if top_fonts.empty:
        st.caption("Tidak ada data.")
        return

    font_cat_map = {}
    for fn in top_fonts.index:
        sub_f = df_fs[df_fs["tipe_font"] == fn]
        cat = sub_f["typeface_kategori"].mode()
        font_cat_map[fn] = cat.iloc[0] if len(cat) > 0 else "unknown"

    colors = [TYPEFACE_CLR.get(font_cat_map.get(fn, "unknown"), "#999") for fn in top_fonts.index]
    fig_top = go.Figure(data=go.Bar(
        x=top_fonts.values, y=top_fonts.index, orientation="h",
        marker_color=colors, text=top_fonts.values, textposition="outside",
    ))
    fig_top.update_layout(
        **pb(max(320, n_top * 28), margin=dict(l=180, r=40, t=28, b=8)),
        showlegend=False, xaxis_title="", yaxis_title="",
        yaxis=dict(categoryorder="total ascending"),
    )
    st.plotly_chart(fig_top, use_container_width=True)

    st.markdown("<hr style='margin:.5rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    st.markdown("**Eksplorasi Font Individual**")

    all_fonts = sorted(df["tipe_font"].dropna().unique())
    if not all_fonts:
        st.caption("Tidak ada data font.")
        return

    sel_font = st.selectbox(
        "Pilih font", options=all_fonts, key="fs_sel_font",
        format_func=lambda x: (
            f"{x} ({df[df['tipe_font']==x]['typeface_kategori'].mode().iloc[0] if not df[df['tipe_font']==x]['typeface_kategori'].mode().empty else '?'})"
        ),
    )

    df_font = df[df["tipe_font"] == sel_font].copy()
    n_font = len(df_font)
    cat_font = df_font["typeface_kategori"].mode()
    cat_str  = cat_font.iloc[0] if len(cat_font) > 0 else "unknown"
    src_font = df_font["font_source"].mode()
    src_str  = src_font.iloc[0] if len(src_font) > 0 else "—"
    clr_font = TYPEFACE_CLR.get(cat_str, "#999")

    st.markdown(
        f'<div style="padding:8px 16px;background:{clr_font}14;'
        f'border-left:4px solid {clr_font};border-radius:0 8px 8px 0;margin:.5rem 0;">'
        f'<span style="font-weight:700;font-size:1rem;color:{clr_font};">{sel_font}</span>'
        f'<span style="font-size:.75rem;color:#888;margin-left:10px;">'
        f'Kategori: {TYPEFACE_ID.get(cat_str, cat_str)} · Sumber: {src_str} · {n_font:,} buku'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    fa, fb = st.columns(2)
    with fa:
        st.markdown("**Genre Terbanyak**")
        from collections import Counter
        gc = Counter()
        for gl in expand_genres(df_font["GENRES"], normalize=True):
            gc.update(gl)
        EXCL = {"Sastra Indonesia", "Sastra", "Fiksi"}
        top_g = [(g, n) for g, n in gc.most_common(10) if g not in EXCL]
        if top_g:
            gdf = pd.DataFrame(
                [(_klaster_label(g), n) for g, n in top_g], columns=["Genre", "N"]
            )
            fig_gf = px.bar(gdf, x="N", y="Genre", orientation="h",
                            color_discrete_sequence=[clr_font], text="N")
            fig_gf.update_layout(**pb(240), showlegend=False, xaxis_title="", yaxis_title="",
                                  yaxis=dict(categoryorder="total ascending"))
            fig_gf.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_gf, use_container_width=True)
        else:
            st.caption("Tidak ada data genre.")

    with fb:
        st.markdown("**Tren per Tahun**")
        df_fyr = df_font[df_font["YEAR"] > 0].groupby("YEAR").size().reset_index(name="n")
        if len(df_fyr) >= 2:
            fig_fyr = px.bar(df_fyr, x="YEAR", y="n",
                             color_discrete_sequence=[clr_font], text="n")
            fig_fyr.update_layout(**pb(240), xaxis_title="", yaxis_title="", showlegend=False)
            fig_fyr.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_fyr, use_container_width=True)
        else:
            st.caption("Data tidak cukup untuk tren.")

    st.markdown("**Contoh Sampul**")
    if "image_ok" not in df_font.columns:
        st.caption("Kolom image_ok tidak tersedia.")
        return
    df_font_img = df_font[df_font["image_ok"].astype(str).str.upper() == "TRUE"].head(8)
    if df_font_img.empty:
        st.caption("Tidak ada sampul.")
    else:
        cols = st.columns(min(len(df_font_img), 8))
        for col_fi, (_, row) in zip(cols, df_font_img.iterrows()):
            with col_fi:
                cp = cover_path(row.get("IMAGE_FILE"))
                if cp:
                    st.image(cp, use_container_width=True)
                url   = str(row.get("URL", "") or "")
                title_col = _get_title_col(df_font_img)
                titl  = str(row.get(title_col, "–") if title_col else "–")
                titl_h = (
                    f'<a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">{titl[:20]}</a>'
                    if url else titl[:20]
                )
                mt  = str(row.get("match_type", "") or "")
                lc  = str(row.get("typeface_low_conf", "")).upper() == "TRUE"
                st.markdown(
                    f'<div style="font-size:.58rem;text-align:center;padding:.15rem 0;">'
                    f'{titl_h}<br>{_konfidence_badge(mt, lc)}</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("<hr style='margin:.5rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    _section_header(
        "Typeface × Gaya Ilustrasi",
        "Apakah pilihan typeface berkorelasi dengan gaya ilustrasi?",
        color="#5C6BC0", bg="#EDE7F6",
    )
    if "gaya_ilustrasi" not in df.columns:
        st.caption("Kolom gaya_ilustrasi tidak tersedia di dataset ini.")
        return

    GAYA_ID_local = {
        "photograph": "Fotografi", "flat_graphic": "Ilustrasi Datar",
        "hand_drawn": "Gambar Tangan", "text_dominant": "Dominan Teks",
        "abstract": "Abstrak", "collage": "Kolase",
    }
    df_cross = df[
        df["typeface_kategori"].isin(TF_ANALISIS) & df["gaya_ilustrasi"].notna()
    ].copy()

    if df_cross.empty:
        st.caption("Tidak ada data untuk cross-analisis.")
        return

    df_cross["gaya_label"] = df_cross["gaya_ilustrasi"].map(GAYA_ID_local)
    ct = pd.crosstab(
        df_cross["typeface_kategori"].map(TYPEFACE_ID),
        df_cross["gaya_label"],
        normalize="index",
    )
    text_ct = (ct * 100).round(0).astype(int).astype(str) + "%"
    fig_ct = go.Figure(data=go.Heatmap(
        z=ct.values, x=ct.columns.tolist(), y=ct.index.tolist(),
        colorscale="RdYlGn",
        text=text_ct.values, texttemplate="%{text}",
        textfont=dict(size=10, color="#1A1A1A"),
        showscale=True, zmin=0, zmax=0.5,
    ))
    fig_ct.update_layout(**pb(
        300,
        margin=dict(l=170, r=20, t=32, b=90),
        yaxis=dict(autorange="reversed"),
        xaxis_title="Gaya Ilustrasi", yaxis_title="Typeface",
    ))
    st.plotly_chart(fig_ct, use_container_width=True)


# ── Tab 5: Klaster Genre ──────────────────────────────────────────────────────

def _tab_klaster_genre(df):
    from collections import Counter

    _section_header(
        "Tipografi berdasarkan Klaster Genre",
        "Tiga klaster merepresentasikan gravitasi tematik berbeda dalam sastra Indonesia 2000–2025.",
        color="#2E4057", bg="#EEF2F7",
    )

    col_lp, col_ng = st.columns([3, 1])
    with col_lp:
        lapisan = st.radio(
            "Lapisan data",
            ["Semua terklasifikasi", "High confidence saja"],
            key="kl_lapisan", horizontal=True,
        )
    with col_ng:
        show_covers = st.checkbox("Tampilkan sampul", value=True, key="kl_show_covers")

    if lapisan == "High confidence saja":
        df_kl = df[
            (df["typeface_low_conf"].astype(str).str.upper() == "FALSE") &
            (df["typeface_kategori"].isin(TF_ANALISIS))
        ].copy()
    else:
        df_kl = df[df["typeface_kategori"].isin(TF_ANALISIS)].copy()

    st.caption(f"n = {len(df_kl):,} buku dalam lapisan ini")
    st.markdown("<hr style='margin:.5rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)

    kl_cols = st.columns(3)
    genre_lists_global = expand_genres(df_kl["GENRES"], normalize=True)
    for kc, kl in zip(kl_cols, KLASTER_COOC):
        kl_genres_set = set(kl["genres"])
        mask_kl = [bool(kl_genres_set & set(gl)) for gl in genre_lists_global]
        n_kl = sum(mask_kl)
        df_kl_sub = df_kl[mask_kl]
        top_tf = df_kl_sub["typeface_kategori"].mode()
        top_tf_str = TYPEFACE_ID.get(top_tf.iloc[0], "—") if len(top_tf) > 0 else "—"
        top_tf_clr = TYPEFACE_CLR.get(top_tf.iloc[0], "#888") if len(top_tf) > 0 else "#888"
        with kc:
            st.markdown(
                f'<div style="background:{kl["bg"]};border-left:4px solid {kl["color"]};'
                f'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:.6rem;">'
                f'<div style="font-weight:700;font-size:.8rem;color:{kl["color"]};">'
                f'[{kl["id"]}] {kl["label"].split("—")[1].strip()}</div>'
                f'<div style="font-size:1.4rem;font-weight:700;margin:.3rem 0 .15rem;'
                f'font-family:Lora,serif;color:{kl["color"]};">{n_kl:,}</div>'
                f'<div style="font-size:.65rem;opacity:.7;">buku terkait genre klaster</div>'
                f'<div style="margin-top:.4rem;font-size:.68rem;">'
                f'Typeface dominan: <span style="color:{top_tf_clr};font-weight:600;">'
                f'{top_tf_str}</span></div></div>',
                unsafe_allow_html=True,
            )

    tc_all_global = df_kl["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)

    for kl in KLASTER_COOC:
        st.markdown("<hr style='margin:.5rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
        st.markdown(
            f'<div style="background:{kl["bg"]};border-left:5px solid {kl["color"]};'
            f'border-radius:0 10px 10px 0;padding:10px 16px;margin:.8rem 0 .5rem;">'
            f'<span style="font-family:Lora,serif;font-weight:700;font-size:1rem;'
            f'color:{kl["color"]};">[{kl["id"]}] {kl["label"]}</span></div>',
            unsafe_allow_html=True,
        )

        kl_genres_set = set(kl["genres"])
        mask_kl2 = [bool(kl_genres_set & set(gl)) for gl in genre_lists_global]
        df_kl_sub = df_kl[mask_kl2].copy()

        if df_kl_sub.empty:
            st.caption("Tidak ada data untuk klaster ini.")
            continue

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Distribusi Typeface dalam Klaster**")
            tc_kl = df_kl_sub["typeface_kategori"].map(TYPEFACE_ID).value_counts()
            fig_pie_kl = px.pie(
                values=tc_kl.values, names=tc_kl.index, hole=0.42,
                color=tc_kl.index,
                color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
            )
            fig_pie_kl.update_layout(**pb(260))
            fig_pie_kl.update_traces(textinfo="percent+label", textfont_size=9)
            st.plotly_chart(fig_pie_kl, use_container_width=True)

        with col_b:
            st.markdown("**Simpangan Klaster vs Korpus**")
            st.caption("Positif = typeface lebih banyak di klaster ini vs rata-rata semua buku.")
            tc_kl_norm = df_kl_sub["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)
            diff_kl = (tc_kl_norm - tc_all_global).dropna().sort_values(ascending=False)
            diff_kl_df = diff_kl.reset_index()
            diff_kl_df.columns = ["Typeface", "Delta"]
            fig_diff_kl = px.bar(
                diff_kl_df, x="Delta", y="Typeface", orientation="h",
                color="Typeface",
                color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
            )
            fig_diff_kl.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.35)")
            fig_diff_kl.update_layout(**pb(260), showlegend=False,
                                      xaxis_title="Selisih proporsi", yaxis_title="",
                                      yaxis=dict(categoryorder="total ascending"))
            st.plotly_chart(fig_diff_kl, use_container_width=True)

        st.markdown("**Heatmap Typeface × Genre dalam Klaster**")
        genres_in_kl = kl["genres"]
        genre_lists_sub = expand_genres(df_kl_sub["GENRES"], normalize=True)

        mat_kl = pd.DataFrame(0.0, index=genres_in_kl, columns=[TYPEFACE_ID[k] for k in TF_ANALISIS])
        valid_genres = []
        n_per_genre = {}
        for g in genres_in_kl:
            mask_g = [g in gl for gl in genre_lists_sub]
            sub_g = df_kl_sub[mask_g]
            if len(sub_g) < 3:
                continue
            valid_genres.append(g)
            n_per_genre[g] = sum(mask_g)
            vc_g = sub_g["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)
            for k in TF_ANALISIS:
                mat_kl.loc[g, TYPEFACE_ID[k]] = vc_g.get(TYPEFACE_ID[k], 0.0)

        mat_kl = mat_kl.loc[valid_genres] if valid_genres else mat_kl.head(0)

        if mat_kl.empty:
            st.caption("Data genre tidak cukup untuk heatmap.")
        else:
            y_labels_kl = [f"{_klaster_label(g)} (n={n_per_genre.get(g,0)})" for g in valid_genres]
            text_mat_kl = (mat_kl * 100).round(0).astype(int).astype(str) + "%"
            cscale = {"K1": "Blues", "K2": "RdPu", "K3": "Greens"}.get(kl["id"], "Purples")
            fig_hm_kl = go.Figure(data=go.Heatmap(
                z=mat_kl.values,
                x=[TYPEFACE_ID[k] for k in TF_ANALISIS],
                y=y_labels_kl,
                colorscale=cscale,
                text=text_mat_kl.values, texttemplate="%{text}",
                textfont=dict(size=10, color="#1A1A1A"),
                showscale=True, zmin=0, zmax=1,
            ))
            fig_hm_kl.update_layout(**pb(
                max(260, len(valid_genres) * 36),
                margin=dict(l=220, r=20, t=32, b=90),
                yaxis=dict(autorange="reversed"),
                xaxis=dict(tickangle=-30),
                xaxis_title="", yaxis_title="",
            ))
            st.plotly_chart(fig_hm_kl, use_container_width=True)

        st.markdown("**Tren Typeface per Tahun dalam Klaster**")
        df_kl_yr = df_kl_sub[df_kl_sub["YEAR"] > 0].copy()
        if len(df_kl_yr) >= 5:
            df_kl_yr["tf"] = df_kl_yr["typeface_kategori"].map(TYPEFACE_ID)
            tr_kl = df_kl_yr.groupby(["YEAR", "tf"]).size().reset_index(name="n")
            fig_tr_kl = px.bar(
                tr_kl, x="YEAR", y="n", color="tf", barmode="stack",
                color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
            )
            fig_tr_kl.update_layout(
                **pb(260), xaxis_title="", yaxis_title="",
                legend=dict(orientation="h", y=-.22, font=dict(size=9)),
            )
            st.plotly_chart(fig_tr_kl, use_container_width=True)
        else:
            st.caption("Data tidak cukup untuk tren tahun.")

        if show_covers and "image_ok" in df_kl_sub.columns:
            st.markdown("**Contoh Sampul Representatif per Typeface**")
            df_kl_img = df_kl_sub[df_kl_sub["image_ok"].astype(str).str.upper() == "TRUE"].copy()
            df_kl_img["ocr_confidence"] = pd.to_numeric(df_kl_img["ocr_confidence"], errors="coerce")
            tf_present_kl = [k for k in TF_ANALISIS if k in df_kl_img["typeface_kategori"].values]

            if tf_present_kl:
                ex_cols_kl = st.columns(min(len(tf_present_kl), 7))
                title_col = _get_title_col(df_kl_img)
                for col_ex_kl, tk in zip(ex_cols_kl, tf_present_kl):
                    sub_tk = df_kl_img[df_kl_img["typeface_kategori"] == tk]
                    if sub_tk.empty:
                        continue
                    high = sub_tk[sub_tk["typeface_low_conf"].astype(str).str.upper() == "FALSE"]
                    pool = high if not high.empty else sub_tk
                    best = pool.sort_values("ocr_confidence", ascending=False).iloc[0]
                    clr_tk = TYPEFACE_CLR.get(tk, "#999")
                    with col_ex_kl:
                        cp = cover_path(best.get("IMAGE_FILE"))
                        if cp:
                            st.image(cp, use_container_width=True)
                        else:
                            st.markdown(
                                '<div style="height:130px;background:rgba(128,128,128,.08);'
                                'border-radius:6px;display:flex;align-items:center;'
                                'justify-content:center;font-size:1.5rem;">📖</div>',
                                unsafe_allow_html=True,
                            )
                        fn_kl  = str(best.get("tipe_font", "—") or "—")
                        mt_kl  = str(best.get("match_type", "") or "")
                        lc_kl  = str(best.get("typeface_low_conf", "")).upper() == "TRUE"
                        url_kl = str(best.get("URL", "") or "")
                        titl_kl = str(best.get(title_col, "–") if title_col else "–")
                        titl_h_kl = (
                            f'<a href="{url_kl}" target="_blank" '
                            f'style="text-decoration:none;color:inherit;">{titl_kl[:20]}</a>'
                            if url_kl else titl_kl[:20]
                        )
                        st.markdown(
                            f'<div style="font-size:.58rem;text-align:center;padding:.2rem 0;">'
                            f'<div style="font-weight:700;color:{clr_tk};margin-bottom:2px;">'
                            f'{TYPEFACE_ID.get(tk, tk)}</div>'
                            f'{titl_h_kl}<br>'
                            f'<span style="opacity:.55;">{fn_kl[:18]}</span><br>'
                            f'{_konfidence_badge(mt_kl, lc_kl)}</div>',
                            unsafe_allow_html=True,
                        )
            else:
                st.caption("Tidak ada sampul dengan gambar untuk klaster ini.")

    st.markdown("<hr style='margin:.5rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    _section_header(
        "Perbandingan Typeface Antar Klaster",
        "Grouped bar chart — proporsi setiap typeface di masing-masing klaster.",
        color="#37474F", bg="#ECEFF1",
    )

    rows_compare = []
    genre_lists_global2 = expand_genres(df_kl["GENRES"], normalize=True)
    for kl in KLASTER_COOC:
        kl_genres_set2 = set(kl["genres"])
        mask_kl2 = [bool(kl_genres_set2 & set(gl)) for gl in genre_lists_global2]
        df_kl2 = df_kl[mask_kl2]
        if df_kl2.empty:
            continue
        tc_kl2 = df_kl2["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)
        for k in TF_ANALISIS:
            rows_compare.append({
                "Klaster": kl["short"],
                "Typeface": TYPEFACE_ID[k],
                "Proporsi": tc_kl2.get(TYPEFACE_ID[k], 0.0),
            })

    df_compare = pd.DataFrame(rows_compare)
    if not df_compare.empty:
        fig_cmp = px.bar(
            df_compare, x="Klaster", y="Proporsi", color="Typeface",
            barmode="group",
            color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
            text=df_compare["Proporsi"].map(lambda x: f"{x*100:.1f}%"),
        )
        fig_cmp.update_traces(textposition="outside", textfont_size=8)
        fig_cmp.update_layout(
            **pb(360), xaxis_title="", yaxis_title="Proporsi",
            legend=dict(orientation="h", y=-.18, font=dict(size=9)),
            yaxis=dict(tickformat=".0%"),
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

        pivot = df_compare.pivot(index="Typeface", columns="Klaster", values="Proporsi")
        pivot = pivot.sort_values(by=pivot.columns[0], ascending=False)
        styled_rows = []
        for tf_name, row_data in pivot.iterrows():
            tf_key = next((k for k, v in TYPEFACE_ID.items() if v == tf_name), None)
            clr_tf = TYPEFACE_CLR.get(tf_key, "#888")
            cells = (
                f'<td style="padding:5px 10px;border:1px solid #E0E0E0;'
                f'font-weight:600;color:{clr_tf};">{tf_name}</td>'
            )
            for col_name in pivot.columns:
                val = row_data.get(col_name, 0)
                cells += (
                    f'<td style="padding:5px 10px;border:1px solid #E0E0E0;'
                    f'text-align:center;">{val*100:.1f}%</td>'
                )
            styled_rows.append(f"<tr>{cells}</tr>")

        header_cells = "<th style='padding:6px 10px;background:#37474F;color:white;text-align:left;'>Typeface</th>"
        for col_name in pivot.columns:
            kl_obj = next((k for k in KLASTER_COOC if k["short"] == col_name), None)
            bg_h = kl_obj["color"] if kl_obj else "#37474F"
            header_cells += (
                f'<th style="padding:6px 10px;background:{bg_h};color:white;text-align:center;">'
                f'{col_name}</th>'
            )
        st.markdown(
            f'<table style="width:100%;border-collapse:collapse;font-size:12px;">'
            f'<thead><tr>{header_cells}</tr></thead>'
            f'<tbody>{"".join(styled_rows)}</tbody></table>',
            unsafe_allow_html=True,
        )
        st.caption("Proporsi typeface (%) di dalam setiap klaster genre.")


# ── Tab 6: Cari Buku ───────────────────────────────────────────────────────────

def _tab_cari(df):
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    with c1:
        q = st.text_input("Judul / penulis", key="tf_cari_q")
    with c2:
        tf_sel = st.selectbox(
            "Typeface", ["Semua"] + [TYPEFACE_ID[k] for k in TF_ANALISIS], key="tf_cari_tf",
        )
    with c3:
        font_sel = st.selectbox(
            "Font spesifik",
            ["Semua"] + sorted(df["tipe_font"].dropna().unique().tolist()),
            key="tf_cari_font",
        )
    with c4:
        only_hc = st.checkbox("High conf saja", key="tf_cari_hc")
        n_show  = st.slider("Tampilkan", 4, 32, 8, 4, key="tf_cari_n")

    if "image_ok" not in df.columns:
        st.caption("Kolom image_ok tidak tersedia.")
        return

    dt = df[df["image_ok"].astype(str).str.upper() == "TRUE"].copy()
    title_col = _get_title_col(dt)

    if q and title_col:
        ql = q.lower()
        dt = dt[
            dt[title_col].str.lower().str.contains(ql, na=False) |
            dt["AUTHOR"].str.lower().str.contains(ql, na=False)
        ]
    if tf_sel != "Semua":
        tf_rev = {v: k for k, v in TYPEFACE_ID.items()}
        dt = dt[dt["typeface_kategori"] == tf_rev.get(tf_sel, tf_sel)]
    if font_sel != "Semua":
        dt = dt[dt["tipe_font"] == font_sel]
    if only_hc:
        dt = dt[dt["typeface_low_conf"].astype(str).str.upper() == "FALSE"]

    st.markdown(f"**{len(dt):,} buku ditemukan**")
    if dt.empty:
        st.info("Tidak ada buku yang cocok.")
        return

    dt = dt.head(n_show).reset_index(drop=True)
    n_cols = 4
    for start in range(0, len(dt), n_cols):
        chunk = dt.iloc[start:start + n_cols]
        cols  = st.columns(n_cols)
        for j, (_, row) in enumerate(chunk.iterrows()):
            with cols[j]:
                cp = cover_path(row.get("IMAGE_FILE"))
                if cp:
                    st.image(cp, use_container_width=True)
                tk    = str(row.get("typeface_kategori", "unknown") or "unknown")
                clr   = TYPEFACE_CLR.get(tk, "#999")
                mt    = str(row.get("match_type", "") or "")
                lc    = str(row.get("typeface_low_conf", "")).upper() == "TRUE"
                fn    = str(row.get("tipe_font", "—") or "—")
                url   = str(row.get("URL", "") or "")
                titl  = str(row.get(title_col, "–") if title_col else "–")
                year  = int(row["YEAR"]) if row.get("YEAR", 0) and int(row.get("YEAR", 0)) > 0 else "–"
                titl_h = (
                    f'<a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">{titl}</a>'
                    if url else titl
                )
                ocr_t = str(row.get("ocr_text", "") or "").strip()
                ocr_snip = (
                    f'<div style="font-size:.57rem;color:#888;opacity:.7;margin-top:2px;font-style:italic;">'
                    f'OCR: {ocr_t[:40]}…</div>'
                ) if len(ocr_t) > 4 else ""

                st.markdown(
                    f'<div style="border:1px solid rgba(128,128,128,.12);'
                    f'border-top:3px solid {clr};border-radius:0 0 8px 8px;'
                    f'padding:.4rem .5rem .5rem;font-size:.63rem;">'
                    f'<span style="background:{clr}18;color:{clr};border-radius:5px;'
                    f'padding:1px 5px;font-size:.58rem;font-weight:600;">{TYPEFACE_ID.get(tk, tk)}</span><br>'
                    f'<span style="font-size:.68rem;font-weight:600;margin:.15rem 0 .05rem;display:block;">{titl_h}</span>'
                    f'<span style="opacity:.55;">{row.get("AUTHOR","–")} · {year}</span><br>'
                    f'<span style="opacity:.6;">{fn}</span><br>'
                    f'{_konfidence_badge(mt, lc)}{ocr_snip}'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ── Tab 7: Pipeline Diagram ────────────────────────────────────────────────────

def _tab_pipeline_diagram(df):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyBboxPatch
        import numpy as np
        from PIL import Image
        import io
    except ImportError as e:
        st.error(f"Library yang dibutuhkan tidak tersedia: {e}")
        return

    BG    = "#F8F8F6"; WHITE = "#FFFFFF"; DARK  = "#1A1A2E"
    GREY  = "#6B7280"; LGREY = "#E5E7EB"; DGREY = "#374151"

    ACC_MAP = {
        "modern_serif":       ("#7B3F9E", "#F3E5F5", "#9C6FB5"),
        "humanist_serif":     ("#3949AB", "#EDE7F6", "#5C6BC0"),
        "transitional_serif": ("#512DA8", "#EDE7F6", "#7E57C2"),
        "slab_serif":         ("#AD1457", "#FCE4EC", "#D81B60"),
        "sans_serif":         ("#1565C0", "#E3F2FD", "#1976D2"),
        "script":             ("#00695C", "#E0F2F1", "#00897B"),
        "display":            ("#E65100", "#FFF3E0", "#F57C00"),
        "unknown":            ("#546E7A", "#ECEFF1", "#78909C"),
    }

    def get_accent(cat):
        return ACC_MAP.get(str(cat), ACC_MAP["unknown"])

    def rbox(ax, x, y, w, h, fc, ec, lw=1.0, r=3):
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
            facecolor=fc, edgecolor=ec, linewidth=lw, clip_on=False,
        ))

    _section_header(
        "Diagram Pipeline v5 — Per Buku",
        "Pilih buku untuk melihat alur OCR → Edit Distance → CLIP → hasil secara visual.",
        color="#37474F", bg="#ECEFF1",
    )

    if "image_ok" not in df.columns:
        st.caption("Kolom image_ok tidak tersedia.")
        return

    df_img = df[df["image_ok"].astype(str).str.upper() == "TRUE"].copy()
    title_col = _get_title_col(df_img)
    if title_col is None:
        st.caption("Kolom TITLE tidak ditemukan.")
        return

    col_s1, col_s2, col_s3 = st.columns([3, 2, 2])
    with col_s1:
        search_q = st.text_input("Cari judul / penulis", key="pd_search",
                                  placeholder="mis. Laut Bercerita, Leila…")
    with col_s2:
        tf_filter = st.selectbox(
            "Filter typeface",
            ["Semua"] + [TYPEFACE_ID[k] for k in TF_ANALISIS] + ["Tidak Terklasifikasi"],
            key="pd_tf_filter",
        )
    with col_s3:
        conf_filter = st.radio("Confidence", ["Semua", "High conf", "Low conf"],
                               key="pd_conf", horizontal=True)

    df_sel = df_img.copy()
    if search_q:
        ql = search_q.lower()
        df_sel = df_sel[
            df_sel[title_col].str.lower().str.contains(ql, na=False) |
            df_sel["AUTHOR"].str.lower().str.contains(ql, na=False)
        ]
    if tf_filter != "Semua":
        tf_rev = {v: k for k, v in TYPEFACE_ID.items()}
        target = tf_rev.get(tf_filter, "unknown")
        df_sel = df_sel[df_sel["typeface_kategori"] == target]
    if conf_filter == "High conf":
        df_sel = df_sel[df_sel["typeface_low_conf"].astype(str).str.upper() == "FALSE"]
    elif conf_filter == "Low conf":
        df_sel = df_sel[df_sel["typeface_low_conf"].astype(str).str.upper() == "TRUE"]

    if df_sel.empty:
        st.info("Tidak ada buku yang sesuai filter.")
        return

    book_options = df_sel[title_col].tolist()
    sel_title = st.selectbox(
        f"Pilih buku ({len(df_sel):,} tersedia)",
        options=book_options, key="pd_book_sel",
    )

    row = df_sel[df_sel[title_col] == sel_title].iloc[0]
    acc, alt, med = get_accent(row.get("typeface_kategori", "unknown"))

    tf_lbl   = TYPEFACE_ID.get(str(row.get("typeface_kategori", "unknown")), "?")
    low_conf = str(row.get("typeface_low_conf", "")).upper() == "TRUE"
    mt       = str(row.get("match_type", "") or "")
    conf_lbl = "Low Confidence" if low_conf else "High Confidence"
    conf_col = "#B71C1C" if low_conf else "#1B5E20"

    st.markdown(
        f'<div style="background:{alt};border-left:4px solid {acc};'
        f'border-radius:0 8px 8px 0;padding:8px 16px;margin:.5rem 0 1rem;">'
        f'<b style="font-size:.95rem;color:{acc};">{sel_title}</b>'
        f'<span style="font-size:.75rem;color:#374151;margin-left:10px;">'
        f'{row.get("AUTHOR","—")} · {int(row.get("YEAR",0)) if row.get("YEAR",0) else "—"}'
        f'</span><br>'
        f'<span style="font-size:.72rem;">Typeface: <b style="color:{acc};">{tf_lbl}</b>'
        f' · Font: <b>{str(row.get("tipe_font","—"))}</b>'
        f' · Match: <b>{mt}</b>'
        f' · <b style="color:{conf_col};">{conf_lbl}</b></span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    img_path = cover_path(row.get("IMAGE_FILE"))
    cover_arr = None
    if img_path:
        try:
            cover_arr = np.array(Image.open(img_path))
        except Exception:
            cover_arr = None

    fig, ax = plt.subplots(1, 1, figsize=(18, 8))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.axis("off")

    TOP = 96; BOT = 6; MID = (TOP + BOT) / 2

    for xp in [33.0, 56.5, 74.5]:
        ax.annotate("", xy=(xp + 2, MID), xytext=(xp, MID),
            arrowprops=dict(arrowstyle="->", color=GREY, lw=1.4))

    ax.text(50, TOP + 2, f"Pipeline Analisis Tipografi — {sel_title}",
        ha="center", va="bottom", fontsize=11.5, color=acc,
        fontfamily="DejaVu Serif", style="italic", fontweight="bold")

    cx, cy, cw, ch = 0.5, BOT + 2, 14.5, TOP - BOT - 9
    if cover_arr is not None:
        ax_c = ax.inset_axes([cx / 100, cy / 100, cw / 100, ch / 100])
        ax_c.imshow(cover_arr); ax_c.axis("off")
        ax_c.add_patch(plt.Rectangle((0, 0), 1, 1, fill=False,
            edgecolor=acc, lw=1.8, transform=ax_c.transAxes))
    else:
        rbox(ax, cx, cy, cw, ch, alt, acc, lw=1.5)
        ax.text(cx + cw / 2, cy + ch * 0.5, str(sel_title)[:18],
            ha="center", va="center", fontsize=7, color=acc, fontweight="bold")

    my = BOT - 0.5
    rbox(ax, cx, my, cw, 5.5, "#FFFDE7", "#F9A825", lw=0.8, r=3)
    ax.text(cx + 0.6, my + 4.5, "metadata:", fontsize=5.5, color="#F57F17",
        fontfamily="monospace", style="italic", va="top")
    ax.text(cx + 0.6, my + 3.0,
        f'judul  = "{str(sel_title)[:18]}"',
        fontsize=5.0, color=DARK, fontfamily="monospace", va="top")
    ax.text(cx + 0.6, my + 1.5,
        f'penulis= "{str(row.get("AUTHOR",""))[:18]}"',
        fontsize=5.0, color=DARK, fontfamily="monospace", va="top")

    ax.annotate("", xy=(cx + cw, my + 2.5), xytext=(57 + 8.75, my + 2.5),
        arrowprops=dict(arrowstyle="->", color=med, lw=1.0,
            connectionstyle="arc3,rad=0.22"))

    dx, dy, dw, dh = 17, BOT + 2, 14.5, TOP - BOT - 9
    if cover_arr is not None:
        ax_d = ax.inset_axes([dx / 100, dy / 100, dw / 100, dh / 100])
        ax_d.imshow(cover_arr); ax_d.axis("off")
        ax_d.add_patch(plt.Rectangle((0.02, 0.01), 0.76, 0.14,
            fill=False, edgecolor="#E53935", lw=2.2, transform=ax_d.transAxes))
        ax_d.add_patch(plt.Rectangle((0.02, 0.17), 0.90, 0.09,
            fill=False, edgecolor="#FF8F00", lw=1.5, transform=ax_d.transAxes))
        ax_d.add_patch(plt.Rectangle((0, 0), 1, 1, fill=False,
            edgecolor=acc, lw=1.2, transform=ax_d.transAxes))
    else:
        rbox(ax, dx, dy, dw, dh, alt, acc, lw=1.2)
        rbox(ax, dx + 0.5, dy + dh - 18, dw - 1, 8, "#FFEBEE", "#E53935", lw=1.5)

    ox = 34; ow = 21
    ocr_raw   = str(row.get("ocr_text", "") or "")
    ocr_conf  = float(row.get("ocr_confidence", 0) or 0)
    ocr_zone  = str(row.get("ocr_zone", "full"))
    author_str = str(row.get("AUTHOR", ""))

    ocr_blocks = [
        (ocr_raw[:28] if ocr_raw else "—", f"{ocr_conf:.2f}", True),
        (author_str[:28], "—", False),
        (f'[zone: {ocr_zone}]', "—", False),
    ]
    bh = (TOP - BOT - 11) / len(ocr_blocks) - 1.5
    for i, (txt_o, conf_o, is_t) in enumerate(ocr_blocks):
        by = TOP - 9 - (i + 1) * (bh + 1.5)
        fc = "#FFEBEE" if is_t else ("#FFF8E1" if i == 1 else WHITE)
        ec = "#E53935" if is_t else ("#FF8F00" if i == 1 else LGREY)
        lw = 1.6 if is_t else 0.8
        rbox(ax, ox, by, ow, bh, fc, ec, lw)
        ax.text(ox + 0.8, by + bh - 2.2, txt_o,
            fontsize=7.2, color=DARK, fontfamily="monospace",
            fontweight="bold" if is_t else "normal", va="top")
        if conf_o != "—":
            ax.text(ox + 0.8, by + 1.5, f"conf. {conf_o}",
                fontsize=6, color=GREY, fontfamily="monospace", va="bottom")

    ex = 57; ew = 17
    title_norm = str(sel_title).lower()
    rbox(ax, ex, TOP - 10, ew, 6.5, acc, acc, lw=0, r=3)
    ax.text(ex + ew / 2, TOP - 6.5, "candidate generation",
        ha="center", va="center", fontsize=6.8, color=WHITE, fontweight="bold")

    cands_raw = [
        (title_norm[:20], "0.00", True),
        ((ocr_raw.lower()[:20] if ocr_raw.lower() != title_norm else title_norm.split()[0]), "~0.1", False),
        (title_norm.split()[0] if " " in title_norm else title_norm, "0.4+", False),
        (author_str.lower()[:18], "0.7+", False),
    ]
    rs = TOP - 12; rh = 5.0
    fy = rs  # init
    for i, (ct, sc, im) in enumerate(cands_raw):
        cy2 = rs - (i + 1) * rh
        rbox(ax, ex, cy2, ew, rh - 0.4,
            alt if im else WHITE, acc if im else LGREY, 1.5 if im else 0.6)
        ax.text(ex + 0.8, cy2 + rh / 2, ct, va="center",
            fontsize=6.5, color=acc if im else DGREY,
            fontfamily="monospace", fontweight="bold" if im else "normal")
        ax.text(ex + ew - 0.8, cy2 + rh / 2, sc, va="center", ha="right",
            fontsize=6.5, color=acc if im else GREY, fontfamily="monospace")
        fy = cy2
    ax.text(ex + ew / 2, fy - 3.5, "…", ha="center", fontsize=9, color=GREY)

    ny = fy - 8.5
    rbox(ax, ex, ny, ew, 4.2, "#F3F4F6", med, lw=0.8, r=3)
    ax.text(ex + ew / 2, ny + 2.1, "normalisasi",
        ha="center", va="center", fontsize=6.5, color=med)
    nry = ny - 5.5
    rbox(ax, ex, nry, ew, 4.5, alt, acc, lw=1.2)
    ax.text(ex + ew / 2, nry + 2.2, title_norm[:22],
        ha="center", va="center", fontsize=7.5, color=acc,
        fontfamily="monospace", fontweight="bold")

    cy3 = nry - 6
    rbox(ax, ex, cy3, ew, 4.5, med, med, lw=0, r=3)
    ax.text(ex + ew / 2, cy3 + 2.2, "perbandingan (edit distance)",
        ha="center", va="center", fontsize=6.3, color=WHITE)

    fin = [
        (title_norm[:20], "0.00", True),
        ((title_norm[:17] + "…" if len(title_norm) > 17 else title_norm), "0.11", False),
        (title_norm.split()[0] if " " in title_norm else title_norm, "0.45", False),
        (author_str.lower()[:18], "0.72", False),
    ]
    fs = cy3 - 0.5
    fy2 = fs
    for i, (ct, sc, im) in enumerate(fin):
        fy2 = fs - (i + 1) * rh
        rbox(ax, ex, fy2, ew, rh - 0.4,
            alt if im else WHITE, acc if im else LGREY, 1.8 if im else 0.6)
        ax.text(ex + 0.8, fy2 + rh / 2, ct, va="center",
            fontsize=6.5, color=acc if im else DGREY,
            fontfamily="monospace", fontweight="bold" if im else "normal")
        ax.text(ex + ew - 0.8, fy2 + rh / 2, sc, va="center", ha="right",
            fontsize=6.5, color=acc if im else GREY, fontfamily="monospace")
    ax.text(ex + ew / 2, fy2 - 3.2, "…", ha="center", fontsize=9, color=GREY)

    rx = 76; rw = 23.5
    rbox(ax, rx, TOP - 10, rw, 6.5, alt, acc, lw=1.5)
    ax.text(rx + rw / 2, TOP - 6.5, "hasil analisis tipografi",
        ha="center", va="center", fontsize=7.5, color=acc, fontweight="bold")

    tipe_font = str(row.get("tipe_font", "—") or "—")
    tf_cat    = str(row.get("typeface_kategori", "unknown") or "unknown")
    clip1     = str(row.get("clip_font_1", "—") or "—")
    cs1       = float(row.get("clip_score_1", 0) or 0)
    margin    = float(row.get("clip_margin", 0) or 0)
    src       = str(row.get("font_source", "—") or "—")

    card_h = TOP - 13 - BOT - 3
    rbox(ax, rx, BOT + 1, rw, card_h, alt, acc, lw=1.5)

    y_cur = BOT + card_h - 1.5

    def rf(label, value, val_color=DARK):
        nonlocal y_cur
        ax.text(rx + 0.9, y_cur, label,  fontsize=5.8, color=GREY, va="top")
        ax.text(rx + 9.5, y_cur, value,  fontsize=7.0, color=val_color, va="top", fontweight="bold")
        y_cur -= 6.5

    ax.text(rx + 0.9, y_cur, f'teks: "{ocr_raw[:22]}"',
        fontsize=6.2, color=DGREY, fontfamily="monospace", fontweight="bold", va="top")
    y_cur -= 4.5
    ax.plot([rx + 0.9, rx + rw - 0.9], [y_cur, y_cur], color=LGREY, lw=0.6)
    y_cur -= 2.5

    rf("font:", tipe_font[:20], acc)
    rf("CLIP top-1:", f"{clip1[:18]} ({cs1:.3f})", DGREY)
    rf("kategori:", TYPEFACE_ID.get(tf_cat, tf_cat), acc)
    rf("sumber:", src, DGREY)
    rf("match_type:", mt, DGREY)
    rf("margin:", f"{margin:.4f}", "#E65100" if margin < 0.01 else DARK)

    ax.plot([rx + 0.9, rx + rw - 0.9], [y_cur + 2, y_cur + 2], color=LGREY, lw=0.6)
    y_cur -= 1
    conf_txt_lbl = "HIGH" if not low_conf else "LOW"
    conf_txt_col = "#1B5E20" if not low_conf else "#B71C1C"
    ax.text(rx + 0.9, y_cur, "confidence:", fontsize=5.8, color=GREY, va="top")
    ax.text(rx + 9.5, y_cur, conf_txt_lbl, fontsize=10,
        color=conf_txt_col, fontweight="bold", va="top")

    fig.text(0.5, 0.01,
        "Kartografi Sampul Sastra Indonesia  |  Esai DKJ  |  Modul B v5  |  "
        "EasyOCR + Edit Distance + CLIP ViT-B/32 + Font DB",
        ha="center", fontsize=6.5, color=GREY, fontfamily="monospace")

    import io
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=160, bbox_inches="tight",
        facecolor=BG, edgecolor="none", pad_inches=0.12)
    plt.close(fig)
    buf.seek(0)
    st.image(buf, use_container_width=True)

    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in sel_title)
    st.download_button(
        label="Unduh diagram (PNG)",
        data=buf.getvalue(),
        file_name=f"pipeline_{safe_title[:40]}.png",
        mime="image/png",
        key="pd_download",
    )

    with st.expander("Data mentah buku ini (dari CSV)", expanded=False):
        show_cols = [
            title_col, "AUTHOR", "YEAR", "ocr_text", "ocr_confidence", "ocr_zone",
            "clip_font_1", "clip_score_1", "clip_cat_1",
            "clip_font_2", "clip_score_2", "clip_font_3", "clip_score_3",
            "clip_margin", "tipe_font", "font_source",
            "match_type", "typeface_kategori", "typeface_low_conf",
        ]
        available = [c for c in show_cols if c in row.index]
        st.dataframe(row[available].to_frame(name="nilai").T, use_container_width=True)


# ── Tab 8 (BARU): Perbandingan 5069 vs 2587 ────────────────────────────────────

def _tab_perbandingan(df):
    """
    Membandingkan dua subset data:
      A = seluruh dataset (5.069 buku)
      B = subset 2.587 buku (typeface_kategori != unknown, yaitu yang berhasil diklasifikasi)

    Tampilkan perbedaan distribusi, tren, dan font terbanyak antara keduanya.
    """
    _section_header(
        "Perbandingan: Semua Buku (5.069) vs Terklasifikasi (2.587)",
        "Seberapa besar perbedaan profil tipografi jika kita hanya melihat buku yang berhasil diklasifikasi?",
        color="#1A237E", bg="#E8EAF6",
    )

    # ── Definisi dua subset ──────────────────────────────────────────────────
    df_all  = df.copy()                                         # ~5.069 buku
    df_cls  = df[df["typeface_kategori"].isin(TF_ANALISIS)].copy()  # ~2.587 buku

    n_all = len(df_all)
    n_cls = len(df_cls)
    n_unk = (df_all["typeface_kategori"] == "unknown").sum()
    n_no_img = (df_all["match_type"] == "no_image").sum() if "match_type" in df_all.columns else 0

    # ── Stat cards ──────────────────────────────────────────────────────────
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1:
        st.markdown(
            f'<div style="border-top:3px solid #1A237E;border-radius:0 0 8px 8px;'
            f'padding:.6rem .7rem;border:1px solid #c5cae9;">'
            f'<div style="font-size:.65rem;color:#888;">Total Korpus</div>'
            f'<div style="font-size:1.6rem;font-weight:700;color:#1A237E;">{n_all:,}</div>'
            f'<div style="font-size:.6rem;color:#aaa;">Semua buku 2000–2025</div></div>',
            unsafe_allow_html=True,
        )
    with cc2:
        st.markdown(
            f'<div style="border-top:3px solid #00897B;border-radius:0 0 8px 8px;'
            f'padding:.6rem .7rem;border:1px solid #b2dfdb;">'
            f'<div style="font-size:.65rem;color:#888;">Terklasifikasi Typeface</div>'
            f'<div style="font-size:1.6rem;font-weight:700;color:#00897B;">{n_cls:,}</div>'
            f'<div style="font-size:.6rem;color:#aaa;">{n_cls/n_all*100:.1f}% dari total</div></div>',
            unsafe_allow_html=True,
        )
    with cc3:
        st.markdown(
            f'<div style="border-top:3px solid #BDBDBD;border-radius:0 0 8px 8px;'
            f'padding:.6rem .7rem;border:1px solid #e0e0e0;">'
            f'<div style="font-size:.65rem;color:#888;">Tidak Terklasifikasi</div>'
            f'<div style="font-size:1.6rem;font-weight:700;color:#757575;">{n_unk:,}</div>'
            f'<div style="font-size:.6rem;color:#aaa;">{n_unk/n_all*100:.1f}% dari total</div></div>',
            unsafe_allow_html=True,
        )
    with cc4:
        st.markdown(
            f'<div style="border-top:3px solid #EF9A9A;border-radius:0 0 8px 8px;'
            f'padding:.6rem .7rem;border:1px solid #ffcdd2;">'
            f'<div style="font-size:.65rem;color:#888;">No Image</div>'
            f'<div style="font-size:1.6rem;font-weight:700;color:#C62828;">{n_no_img:,}</div>'
            f'<div style="font-size:.6rem;color:#aaa;">{n_no_img/n_all*100:.1f}% dari total</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin:.8rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)

    # ── 1. Distribusi Typeface: side-by-side ─────────────────────────────────
    st.markdown("### 1 · Distribusi Typeface")
    st.caption(
        "Kiri = distribusi dalam subset terklasifikasi (n=2.587). "
        "Kanan = estimasi distribusi di seluruh korpus (menganggap unknown tidak memiliki typeface dominan)."
    )

    tc_cls  = df_cls["typeface_kategori"].map(TYPEFACE_ID).value_counts()
    # Untuk seluruh korpus: hanya count yang diketahui (sama dengan tc_cls), tapi proporsi berbeda
    tc_all_known = df_all["typeface_kategori"].map(TYPEFACE_ID).value_counts()
    tc_all_known = tc_all_known[tc_all_known.index != "Tidak Terklasifikasi"]

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown(f"**Subset Terklasifikasi (n={n_cls:,})**")
        fig_cls = px.bar(
            x=tc_cls.values, y=tc_cls.index, orientation="h",
            color=tc_cls.index,
            color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
            text=[f"{v} ({v/tc_cls.sum()*100:.1f}%)" for v in tc_cls.values],
        )
        fig_cls.update_layout(**pb(290), showlegend=False, xaxis_title="", yaxis_title="",
                              yaxis=dict(categoryorder="total ascending"))
        fig_cls.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig_cls, use_container_width=True)

    with col_d2:
        st.markdown(f"**Proporsi terhadap Total Korpus (n={n_all:,})**")
        # proporsi = jumlah / total_all (termasuk unknown)
        fig_all = px.bar(
            x=tc_all_known.values, y=tc_all_known.index, orientation="h",
            color=tc_all_known.index,
            color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
            text=[f"{v} ({v/n_all*100:.1f}%)" for v in tc_all_known.values],
        )
        fig_all.update_layout(**pb(290), showlegend=False, xaxis_title="", yaxis_title="",
                              yaxis=dict(categoryorder="total ascending"))
        fig_all.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig_all, use_container_width=True)

    # ── 2. Proporsi relatif: grouped bar ──────────────────────────────────────
    st.markdown("<hr style='margin:.8rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    st.markdown("### 2 · Pergeseran Proporsi: Terklasifikasi vs Total Korpus")
    st.caption(
        "Positif = typeface lebih sering muncul secara proporsi dalam subset terklasifikasi "
        "dibanding ketika dihitung terhadap seluruh 5.069 buku."
    )

    prop_cls = tc_cls / tc_cls.sum()
    prop_all = tc_all_known / n_all

    rows_delta = []
    for k in TF_ANALISIS:
        lbl = TYPEFACE_ID[k]
        p_cls = prop_cls.get(lbl, 0)
        p_all = prop_all.get(lbl, 0)
        rows_delta.append({
            "Typeface": lbl,
            "Prop. Terklasifikasi (%)": round(p_cls * 100, 2),
            "Prop. Total Korpus (%)":   round(p_all * 100, 2),
            "Delta (pp)":               round((p_cls - p_all) * 100, 2),
        })

    df_delta = pd.DataFrame(rows_delta).sort_values("Delta (pp)", ascending=False)

    fig_delta = go.Figure()
    fig_delta.add_trace(go.Bar(
        name=f"Subset Terklasifikasi ({n_cls:,})",
        x=df_delta["Typeface"],
        y=df_delta["Prop. Terklasifikasi (%)"],
        marker_color=[TYPEFACE_CLR.get(next((k for k, v in TYPEFACE_ID.items() if v == tf), "unknown"), "#999")
                      for tf in df_delta["Typeface"]],
        opacity=1.0,
    ))
    fig_delta.add_trace(go.Bar(
        name=f"Total Korpus ({n_all:,})",
        x=df_delta["Typeface"],
        y=df_delta["Prop. Total Korpus (%)"],
        marker_color=[TYPEFACE_CLR.get(next((k for k, v in TYPEFACE_ID.items() if v == tf), "unknown"), "#999")
                      for tf in df_delta["Typeface"]],
        opacity=0.40,
        marker_line_color="rgba(0,0,0,.15)",
        marker_line_width=1,
    ))
    fig_delta.update_layout(
        **pb(300), barmode="group",
        xaxis_title="", yaxis_title="Proporsi (%)",
        legend=dict(orientation="h", y=-.2, font=dict(size=10)),
    )
    st.plotly_chart(fig_delta, use_container_width=True)

    # Tabel delta
    st.dataframe(
        df_delta.style
            .background_gradient(subset=["Delta (pp)"], cmap="RdYlGn", vmin=-10, vmax=10)
            .format({"Prop. Terklasifikasi (%)": "{:.2f}%",
                     "Prop. Total Korpus (%)":   "{:.2f}%",
                     "Delta (pp)":               "{:+.2f} pp"}),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Delta positif = typeface ini *over-represented* dalam subset terklasifikasi "
        "(artinya buku dengan font ini lebih mudah dikenali oleh pipeline OCR/CLIP). "
        "Delta negatif = kemungkinan ada sampul dari kategori ini yang gagal terdeteksi."
    )

    # ── 3. Tren per tahun: dua lapisan ───────────────────────────────────────
    st.markdown("<hr style='margin:.8rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    st.markdown("### 3 · Tren per Tahun: Total vs Terklasifikasi")
    st.caption("Garis putus-putus = total buku per tahun. Bar = yang berhasil diklasifikasi typeface.")

    yr_all = df_all[df_all["YEAR"] > 0].groupby("YEAR").size().reset_index(name="n_all")
    yr_cls = df_cls[df_cls["YEAR"] > 0].copy()
    yr_cls["tf"] = yr_cls["typeface_kategori"].map(TYPEFACE_ID)
    yr_cls_grp = yr_cls.groupby(["YEAR", "tf"]).size().reset_index(name="n")

    fig_yr = px.bar(
        yr_cls_grp, x="YEAR", y="n", color="tf", barmode="stack",
        color_discrete_map={TYPEFACE_ID[k]: TYPEFACE_CLR[k] for k in TYPEFACE_ID},
        labels={"YEAR": "", "n": "Jumlah buku", "tf": "Typeface"},
    )
    fig_yr.add_scatter(
        x=yr_all["YEAR"], y=yr_all["n_all"],
        mode="lines+markers", name="Total buku (termasuk unknown)",
        line=dict(color="#1A237E", dash="dot", width=2),
        marker=dict(size=5, color="#1A237E"),
    )
    fig_yr.update_layout(
        **pb(340), xaxis_title="", yaxis_title="Jumlah buku",
        legend=dict(orientation="h", y=-.22, font=dict(size=9)),
    )
    st.plotly_chart(fig_yr, use_container_width=True)

    # ── 4. Coverage rate per tahun ────────────────────────────────────────────
    st.markdown("### 4 · Coverage Rate per Tahun")
    st.caption(
        "Persentase buku yang berhasil diklasifikasi typeface-nya per tahun. "
        "Tahun dengan coverage rendah = lebih banyak sampul yang tidak teridentifikasi."
    )

    yr_cls_total = yr_cls.groupby("YEAR").size().reset_index(name="n_cls")
    yr_merged = pd.merge(yr_all, yr_cls_total, on="YEAR", how="left").fillna(0)
    yr_merged["coverage"] = yr_merged["n_cls"] / yr_merged["n_all"] * 100

    fig_cov = go.Figure()
    fig_cov.add_bar(
        x=yr_merged["YEAR"], y=yr_merged["n_all"],
        name="Total buku", marker_color="#C5CAE9", opacity=0.6,
    )
    fig_cov.add_bar(
        x=yr_merged["YEAR"], y=yr_merged["n_cls"],
        name="Terklasifikasi", marker_color="#3949AB",
    )
    fig_cov.update_layout(
        **pb(280), barmode="overlay",
        xaxis_title="", yaxis_title="Jumlah buku",
        legend=dict(orientation="h", y=-.2, font=dict(size=10)),
    )
    st.plotly_chart(fig_cov, use_container_width=True)

    # Line chart coverage %
    fig_cov2 = px.line(
        yr_merged, x="YEAR", y="coverage", markers=True,
        labels={"YEAR": "", "coverage": "Coverage (%)"},
        color_discrete_sequence=["#1A237E"],
    )
    fig_cov2.add_hline(y=50, line_dash="dash", line_color="rgba(200,0,0,.4)",
                       annotation_text="50%")
    fig_cov2.update_layout(**pb(240), yaxis_title="Coverage (%)", xaxis_title="")
    st.plotly_chart(fig_cov2, use_container_width=True)

    # ── 5. Genre: apakah subset bias ke genre tertentu? ──────────────────────
    st.markdown("<hr style='margin:.8rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    st.markdown("### 5 · Apakah Subset Terklasifikasi Bias Genre?")
    st.caption(
        "Jika pipeline lebih berhasil mengenali buku dari genre tertentu, "
        "representasi genre di subset terklasifikasi akan berbeda dari total korpus."
    )

    from collections import Counter

    def genre_counter(df_in):
        c = Counter()
        EXCL = {"Sastra Indonesia", "Sastra", "Fiksi", "Nonfiction", "Non-fiction",
                "Nonfiksi", "Non Fiksi", "Non-fiksi"}
        for gl in expand_genres(df_in["GENRES"], normalize=True):
            c.update([g for g in gl if g not in EXCL])
        return c

    gc_all = genre_counter(df_all)
    gc_cls = genre_counter(df_cls)

    top_g = [g for g, _ in gc_all.most_common(16)]
    rows_gb = []
    for g in top_g:
        n_a = gc_all.get(g, 0)
        n_c = gc_cls.get(g, 0)
        if n_a == 0:
            continue
        rows_gb.append({
            "Genre": _klaster_label(g),
            f"Total ({n_all:,})": n_a,
            f"Terklasifikasi ({n_cls:,})": n_c,
            "Coverage Genre (%)": round(n_c / n_a * 100, 1),
            "Prop. All (%)":  round(n_a / n_all * 100, 2),
            "Prop. Cls (%)":  round(n_c / n_cls * 100, 2) if n_cls > 0 else 0,
        })

    df_gb = pd.DataFrame(rows_gb).sort_values("Coverage Genre (%)", ascending=False)

    fig_gb = go.Figure()
    fig_gb.add_bar(
        x=df_gb["Genre"],
        y=df_gb[f"Prop. All (%)"],
        name=f"Total ({n_all:,})",
        marker_color="#90A4AE", opacity=0.7,
    )
    fig_gb.add_bar(
        x=df_gb["Genre"],
        y=df_gb[f"Prop. Cls (%)"],
        name=f"Terklasifikasi ({n_cls:,})",
        marker_color="#1A237E",
    )
    fig_gb.update_layout(
        **pb(320), barmode="group",
        xaxis_title="", yaxis_title="Proporsi (%)",
        xaxis=dict(tickangle=-30),
        legend=dict(orientation="h", y=-.25, font=dict(size=10)),
    )
    st.plotly_chart(fig_gb, use_container_width=True)

    st.dataframe(
        df_gb.style
            .background_gradient(subset=["Coverage Genre (%)"], cmap="RdYlGn", vmin=30, vmax=80)
            .format({"Coverage Genre (%)": "{:.1f}%",
                     "Prop. All (%)": "{:.2f}%",
                     "Prop. Cls (%)": "{:.2f}%"}),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Coverage Genre = berapa % buku dari genre tersebut berhasil terklasifikasi typeface-nya. "
        "Genre dengan coverage rendah kemungkinan menggunakan font yang lebih sulit dikenali pipeline."
    )

    # ── 6. Font terbanyak: perbandingan ─────────────────────────────────────
    st.markdown("<hr style='margin:.8rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    st.markdown("### 6 · Font Terbanyak: Total vs Terklasifikasi")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.markdown(f"**Top 15 Font — Total Korpus ({n_all:,})**")
        tf_all_top = df_all["tipe_font"].dropna().value_counts().head(15)
        if not tf_all_top.empty:
            fig_ta = px.bar(
                x=tf_all_top.values, y=tf_all_top.index, orientation="h",
                color_discrete_sequence=["#90A4AE"], text=tf_all_top.values,
            )
            fig_ta.update_layout(**pb(340, margin=dict(l=170, r=40, t=28, b=8)),
                                  showlegend=False, xaxis_title="", yaxis_title="",
                                  yaxis=dict(categoryorder="total ascending"))
            fig_ta.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_ta, use_container_width=True)

    with col_f2:
        st.markdown(f"**Top 15 Font — Terklasifikasi ({n_cls:,})**")
        tf_cls_top = df_cls["tipe_font"].dropna().value_counts().head(15)
        if not tf_cls_top.empty:
            font_cat_cls = {}
            for fn in tf_cls_top.index:
                sub_f = df_cls[df_cls["tipe_font"] == fn]
                cat = sub_f["typeface_kategori"].mode()
                font_cat_cls[fn] = cat.iloc[0] if len(cat) > 0 else "unknown"
            colors_cls = [TYPEFACE_CLR.get(font_cat_cls.get(fn, "unknown"), "#999") for fn in tf_cls_top.index]
            fig_tc = go.Figure(data=go.Bar(
                x=tf_cls_top.values, y=tf_cls_top.index, orientation="h",
                marker_color=colors_cls, text=tf_cls_top.values, textposition="outside",
            ))
            fig_tc.update_layout(**pb(340, margin=dict(l=170, r=40, t=28, b=8)),
                                  showlegend=False, xaxis_title="", yaxis_title="",
                                  yaxis=dict(categoryorder="total ascending"))
            st.plotly_chart(fig_tc, use_container_width=True)

    # ── 7. Ringkasan Interpretasi ─────────────────────────────────────────────
    st.markdown("<hr style='margin:.8rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)
    _section_header("Ringkasan Interpretasi", color="#1A237E", bg="#E8EAF6")
    st.markdown(f"""
Beberapa hal yang perlu diperhatikan ketika membandingkan dua subset ini:

**1. Selection bias pipeline OCR/CLIP**  
Pipeline v5 lebih berhasil pada sampul yang memiliki teks judul besar dan kontras tinggi (mudah di-OCR).
Sampul dengan desain ilustratif yang mendominasi (teks kecil atau dekoratif) cenderung masuk ke kategori `unknown`.
Ini berarti **typeface display dan script** mungkin *under-represented* dalam subset 2.587.

**2. Dominasi Rozha One**  
{tc_cls.get(TYPEFACE_ID.get("modern_serif",""), 0):,} sampul dikategorikan `modern_serif` dalam subset terklasifikasi.
Sebagian besar disumbang oleh Rozha One (via `clip_unlisted`), yang mungkin lebih tepat dikategorikan sebagai display-serif.
Perlu konfirmasi manual untuk klaim tentang dominasi `modern_serif`.

**3. Coverage tidak merata per tahun**  
Buku-buku tertentu (terutama sebelum 2005 dan sesudah 2022) cenderung memiliki coverage lebih rendah,
bisa karena kualitas gambar sampul yang berbeda atau variasi desain yang lebih luas.

**4. Implikasi untuk analisis**  
- Gunakan subset **{n_cls:,} terklasifikasi** untuk melihat *pola* typeface secara akurat
- Gunakan **{n_all:,} total** untuk melihat volume dan tren penerbitan
- Delta proporsi yang signifikan (> 5 pp) mengindikasikan bias pipeline yang perlu dicatat dalam temuan
    """)


# ── Entry point ────────────────────────────────────────────────────────────────

def render_tipografi(DF):
    """
    Halaman Tipografi lengkap.
    Panggil dari app utama:

        elif HAL == "Tipografi":
            from tipografi_block import render_tipografi
            render_tipografi(DF)
    """
    # ── Patch typeface_kategori yang masih 'unknown' via EXTENDED_FONT_TO_TYPEFACE ──
    # apply_font_mapping() langsung mengupdate kolom typeface_kategori sehingga
    # SELURUH tab di bawah otomatis mendapat data yang sudah di-patch
    # tanpa perlu mengubah fungsi-fungsi tab yang ada.
    n_unknown_before = (DF["typeface_kategori"].astype(str).str.strip() == "unknown").sum()
    DF = apply_font_mapping(DF)
    n_unknown_after  = (DF["typeface_kategori"].astype(str).str.strip() == "unknown").sum()
    n_recovered      = n_unknown_before - n_unknown_after

    st.markdown("## Analisis Tipografi")
    st.markdown(
        "Klasifikasi *typeface* pada 5.069 sampul buku sastra Indonesia (2000–2025) "
        "menggunakan pipeline DB-first v5: EasyOCR → fuzzy matching → Google Fonts/DaFont → CLIP fallback.",
        unsafe_allow_html=False,
    )

    # ── Banner hasil re-klasifikasi ───────────────────────────────────────────
    if n_recovered > 0:
        st.success(
            f"✅ **{n_recovered:,} font** berhasil di-reklasifikasi dari *unknown* "
            f"menggunakan extended font mapping "
            f"(sisa unknown: {n_unknown_after:,} dari {n_unknown_before:,} sebelumnya).",
            icon=None,
        )

    # ── Kartu tujuh kategori typeface ────────────────────────────────────────
    _section_header(
        "Tujuh Kategori Typeface (Lupton 2024)",
        "Dari Humanist Serif hingga Display/Dekoratif",
        color="#4A148C", bg="#F3E5F5",
    )
    tf_cols = st.columns(len(TF_ANALISIS))
    for col_tf, key in zip(tf_cols, TF_ANALISIS):
        clr  = TYPEFACE_CLR[key]
        font = TYPEFACE_FONT_CSS[key]
        with col_tf:
            st.markdown(
                f'<div style="border:1px solid {clr}30;border-top:3px solid {clr};'
                f'border-radius:0 0 8px 8px;padding:.55rem .5rem;text-align:center;">'
                f'<div style="font-family:{font};font-size:1.45rem;color:{clr};'
                f'font-weight:700;line-height:1.1;">Aa</div>'
                f'<div style="font-size:.63rem;font-weight:700;margin:.25rem 0 .1rem;'
                f'color:{clr};">{TYPEFACE_ID[key]}</div>'
                f'<div style="font-size:.56rem;opacity:.55;text-align:left;line-height:1.4;'
                f'margin-bottom:.2rem;">{TYPEFACE_DESC[key]}</div>'
                f'<div style="font-size:.54rem;opacity:.4;text-align:left;line-height:1.35;'
                f'font-style:italic;">{TYPEFACE_LUPTON[key]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<hr style='margin:.8rem 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)

    # ── Tab navigasi ──────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📊 Gambaran Umum",
        "🗺 Peta Panas Genre",
        "🔍 Per Genre",
        "🔤 Font Spesifik",
        "🎭 Klaster Genre",
        "🔎 Cari Buku",
        "🔬 Pipeline Diagram",
        "⚖️ 5069 vs 2587",
    ])

    with tab1:
        _tab_gambaran(DF)

    with tab2:
        _tab_heatmap_genre(DF)

    with tab3:
        _tab_per_genre(DF)

    with tab4:
        _tab_font_spesifik(DF)

    with tab5:
        _tab_klaster_genre(DF)

    with tab6:
        _tab_cari(DF)

    with tab7:
        _tab_pipeline_diagram(DF)

    with tab8:
        _tab_perbandingan(DF)
