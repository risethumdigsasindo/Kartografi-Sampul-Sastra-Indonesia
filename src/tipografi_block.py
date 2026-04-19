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
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ── Konstanta (redundan dengan app utama; aman jika diimpor ulang) ────────────

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

# Kategori yang digunakan dalam analisis (excluding unknown)
TF_ANALISIS = [k for k in TYPEFACE_ID if k != "unknown"]

# Kategori yang digunakan sebagai fallback (clip_cat_1 untuk unknown)
TF_ALL = list(TYPEFACE_ID.keys())

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

# ── Konstanta Klaster Genre (sinkron dengan app utama) ────────────────────────
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
    """Badge kualitas data."""
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
        "Cinta": "Romansa", "Roman": "Romansa", "Romansa Kontemporer": "Romansa",
        "Kontemporer": "Romansa", "Thriller": "Thriller/Misteri",
        "Misteri": "Thriller/Misteri", "Sejarah": "Fiksi Sejarah",
        "Historical Fiction": "Fiksi Sejarah", "Historical": "Fiksi Sejarah",
        "Humor": "Komedi", "Fiksi Ilmiah": "Fiksi Sains",
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
    GENRE_EXCLUDE = {"Sastra Indonesia", "Sastra", "Fiksi", "Nonfiction", "Non-fiction"}
    c = Counter()
    for gl in expand_genres(df["GENRES"], normalize=True):
        c.update(gl)
    return [g for g, cnt in c.most_common() if g not in GENRE_EXCLUDE and cnt >= 5][:n]


def _genre_mask(df, genre):
    gl = expand_genres(df["GENRES"], normalize=True)
    return [genre in g for g in gl]


def _effective_cat(row):
    """Gunakan typeface_kategori jika bukan unknown, fallback ke clip_cat_1."""
    cat = str(row.get("typeface_kategori", "unknown") or "unknown")
    if cat != "unknown":
        return cat
    return str(row.get("clip_cat_1", "unknown") or "unknown")


# ── Tab 1: Gambaran Umum ───────────────────────────────────────────────────────

def _tab_gambaran(df):
    """Distribusi, tren, kualitas data."""

    df_known = df[df["typeface_kategori"].isin(TF_ANALISIS)].copy()
    df_low   = df[df["typeface_low_conf"].astype(str).str.upper() == "TRUE"]
    df_high  = df[df["typeface_low_conf"].astype(str).str.upper() == "FALSE"]
    n_unknown = (df["typeface_kategori"] == "unknown").sum()
    n_total   = len(df)

    # ── Stat cards ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    stats = [
        ("Terklasifikasi", len(df_known), f"{len(df_known)/n_total*100:.1f}% dari total", "#8E24AA"),
        ("Tidak Terklasifikasi", n_unknown, f"{n_unknown/n_total*100:.1f}% dari total", "#BDBDBD"),
        ("High Confidence", len(df_high), "low_conf = False", "#2E7D32"),
        ("Low Confidence", len(df_low),  "low_conf = True",  "#E65100"),
    ]
    for col, (lbl, val, sub, clr) in zip([c1, c2, c3, c4], stats):
        with col:
            st.markdown(
                f'<div class="stat-card" style="border-top:3px solid {clr};">'
                f'<div class="lbl">{lbl}</div>'
                f'<div class="val" style="color:{clr};">{val:,}</div>'
                f'<div class="sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # ── Distribusi + Match Type ──────────────────────────────────────────────
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
        fig.update_layout(**pb(290), showlegend=False,
                          xaxis_title="", yaxis_title="",
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

    # ── Tren per Tahun ───────────────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
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

    # ── Pergeseran per Dekade ────────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
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
    fig4.update_layout(**pb(320),
                       legend=dict(orientation="h", y=-.22, font=dict(size=10)))
    st.plotly_chart(fig4, use_container_width=True)

    # ── Font Source ──────────────────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Sumber Font**")
    src = df["font_source"].value_counts()
    fig5 = px.bar(
        x=src.values, y=src.index, orientation="h",
        color=src.index,
        color_discrete_map=FONT_SOURCE_CLR,
        text=src.values,
    )
    fig5.update_layout(**pb(240), showlegend=False, xaxis_title="", yaxis_title="",
                       yaxis=dict(categoryorder="total ascending"))
    fig5.update_traces(textposition="outside", marker_line_width=0)
    st.plotly_chart(fig5, use_container_width=True)

    # ── Catatan metodologis ──────────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    with st.expander("⚠️ Catatan Metodologis dan Keterbatasan Data (v5)", expanded=False):
        st.markdown("""
**Pipeline v5 menggunakan pendekatan DB-first:**
1. OCR (EasyOCR) mendeteksi teks di sampul → fuzzy matching ke metadata judul/penulis
2. Teks yang cocok di-query ke Google Fonts + DaFont → kategori typeface dari database
3. Jika tidak ditemukan di DB, CLIP ViT-B/32 mengklasifikasi langsung dari fitur visual

**Tiga keterbatasan utama:**

**1. 48.2% `unknown`** — Bukan bug sepenuhnya. Sekitar 1.032 dapat di-recover (bug `ocr_exact → unknown` + font lokal tanpa kategori di DB). Sisanya ~1.187 genuinely unclassifiable.

**2. Dominasi Rozha One** — 608 sampul (13.2%) terdeteksi sebagai Rozha One, semuanya `clip_unlisted`. Rozha One diklasifikasikan sebagai `modern_serif` karena kontras stroke, tapi secara tipografis ia lebih tepat disebut *display-serif*. Klaim tentang dominasi `modern_serif` perlu dibaca dengan hati-hati.

**3. Script bias CLIP** — Ketika `unknown`, `clip_cat_1` cenderung menebak `script` (1.151 dari 2.219 unknown). Ini mencerminkan bias CLIP terhadap stroke yang mengalir, bukan selalu mencerminkan font yang sebenarnya.

**Rekomendasi pembacaan:** Gunakan lapisan High Confidence (`typeface_low_conf = False`, n=1.537) untuk klaim yang kuat; gunakan keseluruhan data untuk melihat tren.
        """)


# ── Tab 2: Heatmap Genre ───────────────────────────────────────────────────────

def _tab_heatmap_genre(df):
    """Peta panas typeface × genre dengan opsi lapisan data."""

    st.markdown("**Peta Panas Typeface × Genre**")

    col_opt1, col_opt2 = st.columns([3, 1])
    with col_opt1:
        lapisan = st.radio(
            "Lapisan data",
            ["Semua terklasifikasi", "High confidence saja", "Termasuk CLIP fallback (incl. unknown)"],
            key="hm_lapisan",
            help=(
                "**Semua terklasifikasi**: hanya baris dengan typeface_kategori ≠ unknown\n\n"
                "**High confidence**: typeface_low_conf = False\n\n"
                "**CLIP fallback**: jika unknown, gunakan clip_cat_1 sebagai estimasi"
            ),
            horizontal=True,
        )
    with col_opt2:
        n_genre = st.slider("Jumlah genre", 6, 20, 12, 2, key="hm_n_genre")

    # Filter sesuai lapisan
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
        z=mat.values, x=tf_labels, y=genres,
        colorscale="Purples",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=10, color="#1A1A1A"),
        showscale=True, zmin=0, zmax=1,
    ))
    fig.update_layout(**pb(
        max(340, n_genre * 32),
        margin=dict(l=160, r=20, t=32, b=90),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickangle=-30),
        xaxis_title="", yaxis_title="",
    ))
    st.plotly_chart(fig, use_container_width=True)

    # ── Simpangan dari korpus ────────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
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
        for k in tf_keys:
            lbl = TYPEFACE_ID[k]
            rows_diff.append({
                "Genre": g,
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
            **pb(max(300, n_genre * 55)),
            xaxis_title="Selisih proporsi vs korpus", yaxis_title="",
            legend=dict(orientation="h", y=-.18, font=dict(size=9)),
        )
        st.plotly_chart(fig_d, use_container_width=True)


# ── Tab 3: Per Genre ───────────────────────────────────────────────────────────

def _tab_per_genre(df):
    """Analisis mendalam satu genre: distribusi, contoh sampul, font spesifik."""

    genre_opts = _top_genres(df, 30)

    col_g1, col_g2 = st.columns([3, 1])
    with col_g1:
        sel_genre = st.selectbox(
            "Pilih genre",
            options=genre_opts,
            key="tf_per_genre_sel",
        )
    with col_g2:
        lapisan_pg = st.radio(
            "Lapisan",
            ["Semua", "High conf"],
            key="tf_per_genre_lapisan",
            horizontal=True,
        )

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

    st.markdown(
        f'<div style="padding:6px 14px;background:#F3E5F5;border-left:4px solid #8E24AA;'
        f'border-radius:0 8px 8px 0;margin:.5rem 0;">'
        f'<b style="color:#6A1B9A;">{sel_genre}</b>'
        f'<span style="font-size:.72rem;color:#888;margin-left:10px;">'
        f'{n_total_g:,} buku total · {n_known_g:,} terklasifikasi typeface</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Distribusi pie ───────────────────────────────────────────────────────
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
        if df_g.empty:
            st.caption("—")
        else:
            top_fonts = df_g["tipe_font"].dropna().value_counts().head(10)
            if top_fonts.empty:
                st.caption("—")
            else:
                # Annotate dengan kategori
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
                fig_f.update_layout(**pb(240), showlegend=False,
                                     xaxis_title="", yaxis_title="",
                                     yaxis=dict(categoryorder="total ascending"))
                fig_f.update_traces(textposition="outside", marker_line_width=0)
                st.plotly_chart(fig_f, use_container_width=True)

    # ── Contoh sampul per typeface ───────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Contoh Sampul per Typeface**")
    st.caption("Buku dengan skor OCR confidence tertinggi per kategori.")

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
        # Prioritaskan high conf, lalu skor tertinggi
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

    # ── Tren per tahun untuk genre ini ──────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
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
    """Eksplorasi font individu, distribusi per kategori, dan keterkaitan dengan gaya."""

    st.markdown("**Font Terbanyak di Seluruh Dataset**")

    # Pilih lapisan
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

    # Warnai berdasarkan kategori
    font_cat_map = {}
    for fn in top_fonts.index:
        sub_f = df_fs[df_fs["tipe_font"] == fn]
        cat = sub_f["typeface_kategori"].mode()
        font_cat_map[fn] = cat.iloc[0] if len(cat) > 0 else "unknown"

    colors = [TYPEFACE_CLR.get(font_cat_map.get(fn, "unknown"), "#999") for fn in top_fonts.index]
    fig_top = go.Figure(data=go.Bar(
        x=top_fonts.values,
        y=top_fonts.index,
        orientation="h",
        marker_color=colors,
        text=top_fonts.values,
        textposition="outside",
    ))
    fig_top.update_layout(
        **pb(max(320, n_top * 28), margin=dict(l=180, r=40, t=28, b=8)),
        showlegend=False, xaxis_title="", yaxis_title="",
        yaxis=dict(categoryorder="total ascending"),
    )
    st.plotly_chart(fig_top, use_container_width=True)

    # ── Cari font spesifik ───────────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Eksplorasi Font Individual**")

    all_fonts = sorted(df["tipe_font"].dropna().unique())
    sel_font = st.selectbox(
        "Pilih font",
        options=all_fonts,
        key="fs_sel_font",
        format_func=lambda x: f"{x} ({df[df['tipe_font']==x]['typeface_kategori'].mode().iloc[0] if not df[df['tipe_font']==x]['typeface_kategori'].mode().empty else '?'})",
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
        f'Kategori: {TYPEFACE_ID.get(cat_str, cat_str)} · '
        f'Sumber: {src_str} · '
        f'{n_font:,} buku</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Distribusi genre untuk font ini
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
            gdf = pd.DataFrame(top_g, columns=["Genre", "N"])
            fig_gf = px.bar(gdf, x="N", y="Genre", orientation="h",
                            color_discrete_sequence=[clr_font], text="N")
            fig_gf.update_layout(**pb(240), showlegend=False,
                                  xaxis_title="", yaxis_title="",
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
            fig_fyr.update_layout(**pb(240), xaxis_title="", yaxis_title="",
                                   showlegend=False)
            fig_fyr.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_fyr, use_container_width=True)
        else:
            st.caption("Data tidak cukup untuk tren.")

    # Sampul dengan font ini
    st.markdown("**Contoh Sampul**")
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
                url  = str(row.get("URL", "") or "")
                titl = str(row.get("TITLE", "–"))
                titl_h = (f'<a href="{url}" target="_blank" '
                          f'style="text-decoration:none;color:inherit;">{titl[:20]}</a>'
                          if url else titl[:20])
                mt   = str(row.get("match_type", "") or "")
                lc   = str(row.get("typeface_low_conf", "")).upper() == "TRUE"
                st.markdown(
                    f'<div style="font-size:.58rem;text-align:center;padding:.15rem 0;">'
                    f'{titl_h}<br>{_konfidence_badge(mt, lc)}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Typeface × Gaya Ilustrasi ─────────────────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    _section_header(
        "Typeface × Gaya Ilustrasi",
        "Apakah pilihan typeface berkorelasi dengan gaya ilustrasi?",
        color="#5C6BC0", bg="#EDE7F6",
    )
    GAYA_ID_local = {
        "photograph": "Fotografi", "flat_graphic": "Ilustrasi Datar",
        "hand_drawn": "Gambar Tangan", "text_dominant": "Dominan Teks",
        "abstract": "Abstrak", "collage": "Kolase",
    }
    GAYA_CLR_local = {
        "photograph": "#1E88E5", "flat_graphic": "#43A047", "hand_drawn": "#FB8C00",
        "text_dominant": "#E53935", "abstract": "#8E24AA", "collage": "#00ACC1",
    }
    df_cross = df[
        df["typeface_kategori"].isin(TF_ANALISIS) &
        df["gaya_ilustrasi"].notna()
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


# ── Tab 5: Cari Buku ───────────────────────────────────────────────────────────

def _tab_cari(df):
    """Filter buku berdasarkan kriteria tipografi."""

    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    with c1:
        q = st.text_input("Judul / penulis", key="tf_cari_q")
    with c2:
        tf_sel = st.selectbox(
            "Typeface",
            ["Semua"] + [TYPEFACE_ID[k] for k in TF_ANALISIS],
            key="tf_cari_tf",
        )
    with c3:
        font_sel = st.selectbox(
            "Font spesifik",
            ["Semua"] + sorted(df["tipe_font"].dropna().unique().tolist()),
            key="tf_cari_font",
        )
    with c4:
        only_hc = st.checkbox("High conf saja", key="tf_cari_hc")
    with c4:
        n_show = st.slider("Tampilkan", 4, 32, 8, 4, key="tf_cari_n")

    dt = df[df["image_ok"].astype(str).str.upper() == "TRUE"].copy()

    if q:
        ql = q.lower()
        dt = dt[
            dt["TITLE"].str.lower().str.contains(ql, na=False) |
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
                titl  = str(row.get("TITLE", "–"))
                year  = int(row["YEAR"]) if row.get("YEAR", 0) and int(row.get("YEAR", 0)) > 0 else "–"
                titl_h = (
                    f'<a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">{titl}</a>'
                    if url else titl
                )

                # OCR text snippet
                ocr_t = str(row.get("ocr_text", "") or "").strip()
                ocr_snip = f'<div style="font-size:.57rem;color:#888;opacity:.7;margin-top:2px;font-style:italic;">OCR: {ocr_t[:40]}…</div>' if len(ocr_t) > 4 else ""

                st.markdown(
                    f'<div style="border:1px solid rgba(128,128,128,.12);'
                    f'border-top:3px solid {clr};border-radius:0 0 8px 8px;'
                    f'padding:.4rem .5rem .5rem;font-size:.63rem;">'
                    f'<span style="background:{clr}18;color:{clr};border-radius:5px;'
                    f'padding:1px 5px;font-size:.58rem;font-weight:600;">'
                    f'{TYPEFACE_ID.get(tk, tk)}</span><br>'
                    f'<span style="font-size:.68rem;font-weight:600;margin:.15rem 0 .05rem;display:block;">{titl_h}</span>'
                    f'<span style="opacity:.55;">{row.get("AUTHOR","–")} · {year}</span><br>'
                    f'<span style="opacity:.6;">{fn}</span><br>'
                    f'{_konfidence_badge(mt, lc)}'
                    f'{ocr_snip}'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ── Tab 6: Tipografi × Klaster Genre ──────────────────────────────────────────

def _tab_klaster_genre(df):
    """
    Analisis tipografi dikelompokkan menurut tiga klaster genre.
    Setiap klaster menampilkan:
      - Distribusi typeface keseluruhan klaster (pie)
      - Simpangan per genre di dalam klaster vs korpus (bar)
      - Heatmap typeface × genre dalam klaster
      - Contoh sampul representatif per typeface per klaster
    """
    from collections import Counter

    _section_header(
        "Tipografi berdasarkan Klaster Genre",
        "Tiga klaster merepresentasikan gravitasi tematik berbeda dalam sastra Indonesia 2000–2025.",
        color="#2E4057", bg="#EEF2F7",
    )

    st.markdown(
        "Genre dinormalisasi dan dikelompokkan ke dalam tiga klaster berbasis co-occurrence Goodreads. "
        "Analisis menggunakan kolom `typeface_kategori` v5 (exclude *unknown*).",
        unsafe_allow_html=False,
    )

    # Opsi lapisan data
    col_lp, col_ng = st.columns([3, 1])
    with col_lp:
        lapisan = st.radio(
            "Lapisan data",
            ["Semua terklasifikasi", "High confidence saja"],
            key="kl_lapisan",
            horizontal=True,
            help="**Semua terklasifikasi**: typeface_kategori ≠ unknown\n\n"
                 "**High confidence**: typeface_low_conf = False",
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

    # Statistik ringkas per klaster (cards di atas)
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    kl_cols = st.columns(3)
    for kc, kl in zip(kl_cols, KLASTER_COOC):
        # Hitung buku yang masuk klaster ini
        genre_lists_all = expand_genres(df_kl["GENRES"], normalize=True)
        kl_genres_set = set(kl["genres"])
        mask_kl = [bool(kl_genres_set & set(gl)) for gl in genre_lists_all]
        n_kl = sum(mask_kl)
        df_kl_sub = df_kl[mask_kl]
        # Typeface dominan
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
                f'{top_tf_str}</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Loop per klaster: analisis mendalam ─────────────────────────────────
    genre_lists_global = expand_genres(df_kl["GENRES"], normalize=True)
    tc_all_global = df_kl["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)

    for kl in KLASTER_COOC:
        st.markdown("<hr class='thin'>", unsafe_allow_html=True)
        st.markdown(
            f'<div style="background:{kl["bg"]};border-left:5px solid {kl["color"]};'
            f'border-radius:0 10px 10px 0;padding:10px 16px;margin:.8rem 0 .5rem;">'
            f'<span style="font-family:Lora,serif;font-weight:700;font-size:1rem;'
            f'color:{kl["color"]};">[{kl["id"]}] {kl["label"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Buku yang punya setidaknya satu genre dari klaster ini
        kl_genres_set = set(kl["genres"])
        mask_kl = [bool(kl_genres_set & set(gl)) for gl in genre_lists_global]
        df_kl_sub = df_kl[mask_kl].copy()
        n_kl_sub = len(df_kl_sub)

        if df_kl_sub.empty:
            st.caption("Tidak ada data untuk klaster ini.")
            continue

        col_a, col_b = st.columns(2)

        # ── Pie distribusi typeface klaster ──────────────────────────────────
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

        # ── Simpangan klaster vs korpus ──────────────────────────────────────
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

        # ── Heatmap typeface × genre dalam klaster ───────────────────────────
        st.markdown("**Heatmap Typeface × Genre dalam Klaster**")
        # Hanya genre yang ada di klaster DAN ada di data
        genres_in_kl = kl["genres"]
        genre_lists_sub = expand_genres(df_kl_sub["GENRES"], normalize=True)

        mat_kl = pd.DataFrame(0.0, index=genres_in_kl, columns=[TYPEFACE_ID[k] for k in TF_ANALISIS])
        valid_genres = []
        for g in genres_in_kl:
            mask_g = [g in gl for gl in genre_lists_sub]
            sub_g = df_kl_sub[mask_g]
            if len(sub_g) < 3:
                continue
            valid_genres.append(g)
            vc_g = sub_g["typeface_kategori"].map(TYPEFACE_ID).value_counts(normalize=True)
            for k in TF_ANALISIS:
                mat_kl.loc[g, TYPEFACE_ID[k]] = vc_g.get(TYPEFACE_ID[k], 0.0)

        mat_kl = mat_kl.loc[valid_genres] if valid_genres else mat_kl.head(0)

        if mat_kl.empty:
            st.caption("Data genre tidak cukup untuk heatmap.")
        else:
            # Hitung n per genre untuk label
            n_per_genre = {}
            for g in valid_genres:
                mask_g2 = [g in gl for gl in genre_lists_sub]
                n_per_genre[g] = sum(mask_g2)

            y_labels_kl = [f"{g} (n={n_per_genre.get(g,0)})" for g in valid_genres]
            text_mat_kl = (mat_kl * 100).round(0).astype(int).astype(str) + "%"
            # Pilih colorscale sesuai klaster
            cscale = {"K1": "Blues", "K2": "RdPu", "K3": "Greens"}.get(kl["id"], "Purples")
            fig_hm_kl = go.Figure(data=go.Heatmap(
                z=mat_kl.values,
                x=[TYPEFACE_ID[k] for k in TF_ANALISIS],
                y=y_labels_kl,
                colorscale=cscale,
                text=text_mat_kl.values,
                texttemplate="%{text}",
                textfont=dict(size=10, color="#1A1A1A"),
                showscale=True, zmin=0, zmax=1,
            ))
            fig_hm_kl.update_layout(**pb(
                max(260, len(valid_genres) * 36),
                margin=dict(l=200, r=20, t=32, b=90),
                yaxis=dict(autorange="reversed"),
                xaxis=dict(tickangle=-30),
                xaxis_title="", yaxis_title="",
            ))
            st.plotly_chart(fig_hm_kl, use_container_width=True)

        # ── Tren typeface per tahun dalam klaster ────────────────────────────
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

        # ── Contoh sampul representatif per typeface ─────────────────────────
        if show_covers:
            st.markdown("**Contoh Sampul Representatif per Typeface**")
            st.caption(f"Satu buku terbaik (high conf atau OCR tertinggi) per kategori typeface — dalam genre {kl['short']}.")
            df_kl_img = df_kl_sub[df_kl_sub["image_ok"].astype(str).str.upper() == "TRUE"].copy()
            df_kl_img["ocr_confidence"] = pd.to_numeric(df_kl_img["ocr_confidence"], errors="coerce")
            tf_present_kl = [k for k in TF_ANALISIS if k in df_kl_img["typeface_kategori"].values]

            if tf_present_kl:
                ex_cols_kl = st.columns(min(len(tf_present_kl), 7))
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
                        fn_kl   = str(best.get("tipe_font", "—") or "—")
                        mt_kl   = str(best.get("match_type", "") or "")
                        lc_kl   = str(best.get("typeface_low_conf", "")).upper() == "TRUE"
                        url_kl  = str(best.get("URL", "") or "")
                        titl_kl = str(best.get("TITLE", "–"))
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
                            f'{_konfidence_badge(mt_kl, lc_kl)}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
            else:
                st.caption("Tidak ada sampul dengan gambar untuk klaster ini.")

    # ── Perbandingan ringkas antar klaster ───────────────────────────────────
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
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
                "KlasterWarna": kl["color"],
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
            **pb(360),
            xaxis_title="", yaxis_title="Proporsi",
            legend=dict(orientation="h", y=-.18, font=dict(size=9)),
            yaxis=dict(tickformat=".0%"),
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

        # Tabel ringkas
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
            f'<table style="width:100%;border-collapse:collapse;font-size:12px;'
            f'font-family:Inter,sans-serif;">'
            f'<thead><tr>{header_cells}</tr></thead>'
            f'<tbody>{"".join(styled_rows)}</tbody></table>',
            unsafe_allow_html=True,
        )
        st.caption("Proporsi typeface (%) di dalam setiap klaster genre.")




def render_tipografi(DF):
    """
    Halaman Tipografi lengkap.
    Panggil dari app utama:

        elif HAL == "Tipografi":
            from tipografi_block import render_tipografi
            render_tipografi(DF)
    """
    st.markdown("## Analisis Tipografi")
    st.markdown(
        "Klasifikasi *typeface* pada 5.069 sampul buku sastra Indonesia (2000–2025) "
        "menggunakan pipeline DB-first v5: EasyOCR → fuzzy matching → Google Fonts/DaFont → CLIP fallback.",
        unsafe_allow_html=False,
    )

    # ── Enam kategori typeface — kartu ────────────────────────────────────────
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

    st.markdown("<hr class='thin'>", unsafe_allow_html=True)

    # ── Tab navigasi ──────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Gambaran Umum",
        "🗺 Peta Panas Genre",
        "🔍 Per Genre",
        "🔤 Font Spesifik",
        "🎭 Klaster Genre",
        "🔎 Cari Buku",
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
