"""
tipografi_4cat.py
=================
Modul analisis tipografi untuk Esai DKJ — Kartografi Sampul Sastra Indonesia.
Menggunakan typeface_paper (4 kategori: Serif, Script, Sans-serif, Fancy)
sebagai sistem klasifikasi utama, menggantikan pipeline 7-kategori v5.

Perubahan dari versi sebelumnya:
  - Kategori typeface: 4 (Serif / Script / Sans-serif / Fancy)
  - Komedi dipindah ke Klaster 3
  - Sumber data: kolom typeface_paper dari CSV

Panggil render_tipografi_4cat(DF) dari app utama.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import os

# ─────────────────────────────────────────────────────────────────────────────
# KONSTANTA
# ─────────────────────────────────────────────────────────────────────────────

TYPEFACE_4 = ["Serif", "Script", "Sans-serif", "Fancy"]

TYPEFACE_CLR = {
    "Serif":      "#3949AB",
    "Script":     "#00897B",
    "Sans-serif": "#1565C0",
    "Fancy":      "#E65100",
    "unknown":    "#BDBDBD",
}

TYPEFACE_DESC = {
    "Serif":      "Memiliki kait pada ujung stroke. Kesan formal, tradisional, otoritatif. Contoh: Garamond, Bodoni, Baskerville.",
    "Script":     "Menyerupai tulisan tangan dengan stroke yang mengalir. Kesan personal, intim, romantis.",
    "Sans-serif": "Tanpa kait, stroke seragam dan bersih. Kesan modern, fungsional, minimalis.",
    "Fancy":      "Bentuk eksperimental dan ornamental, keluar dari konvensi tipografis. Kesan dramatis, unik, spekulatif.",
}

TYPEFACE_LUPTON = {
    "Serif":      "Mewarisi tradisi cetak sejak abad ke-15 (humanis) hingga abad ke-19 (slab). Backbone tipografi sastra dan penerbitan formal.",
    "Script":     "Terinspirasi tulisan tangan dan kaligrafi. Membawa keintiman komunikasi personal ke dalam desain sampul.",
    "Sans-serif": "Lahir dari modernisme industri abad ke-19–20. Bauhaus dan Swiss typography menjadikannya lambang fungsionalisme.",
    "Fancy":      "Tidak terikat sejarah tipografis tertentu. Menampung eksperimen bentuk yang melampaui konvensi.",
}

# ─────────────────────────────────────────────────────────────────────────────
# KLASTER — Komedi di K3
# ─────────────────────────────────────────────────────────────────────────────

KLASTER = [
    {
        "id": "K1",
        "label": "Klaster 1 — Novel sebagai genre bentuk yang dominan",
        "short": "Klaster 1",
        "color": "#2E4057",
        "bg": "#EEF2F7",
        "genres": ["Novel", "Cerita Pendek", "Antologi", "Puisi"],
    },
    {
        "id": "K2",
        "label": "Klaster 2 — Romansa sebagai gravitasi genre tematik",
        "short": "Klaster 2",
        "color": "#993556",
        "bg": "#FBF0F3",
        "genres": ["Romansa", "Chick Lit", "Persahabatan", "Remaja",
                   "Dewasa", "Keluarga", "Drama", "Slice of Life"],
    },
    {
        "id": "K3",
        "label": "Klaster 3 — Eskapisme: fantasi, aksi, ketegangan & humor",
        "short": "Klaster 3",
        "color": "#1D9E75",
        "bg": "#EEF8F4",
        "genres": ["Fantasi", "Fiksi Sejarah", "Petualangan", "Aksi",
                   "Fiksi Sains", "Thriller/Misteri", "Horor",
                   "Anak-anak", "Komedi"],
    },
]

GENRE_TO_KLASTER = {}
for kl in KLASTER:
    for g in kl["genres"]:
        GENRE_TO_KLASTER[g] = kl

# ─────────────────────────────────────────────────────────────────────────────
# NORMALISASI GENRE
# ─────────────────────────────────────────────────────────────────────────────

GENRE_NORM_MAP = {
    "Cinta": "Romansa", "Roman": "Romansa", "Romansa Kontemporer": "Romansa",
    "Roman Kontemporer": "Romansa", "Romantis": "Romansa", "Romance": "Romansa",
    "Kontemporer": "Romansa", "Romansatic": "Romansa",
    "Young Adult Romansace": "Romansa",
    "Thriller": "Thriller/Misteri", "Misteri": "Thriller/Misteri",
    "Misteri Thriller": "Thriller/Misteri", "Thriller Suspense": "Thriller/Misteri",
    "Psychological Thriller": "Thriller/Misteri", "Suspense": "Thriller/Misteri",
    "Detective": "Thriller/Misteri", "Kriminal": "Thriller/Misteri",
    "Supranatural": "Horor", "Horror": "Horor",
    "Humor": "Komedi",
    "New Adult": "Remaja",
    "Collections": "Antologi",
    "Middle Grade": "Fantasi", "Fantasy": "Fantasi",
    "Fiksi Ilmiah": "Fiksi Sains", "Distopia": "Fiksi Sains", "Sains Fiksi": "Fiksi Sains",
    "Sejarah": "Fiksi Sejarah", "Historical Fiction": "Fiksi Sejarah",
    "Historical": "Fiksi Sejarah", "Fiksi Sejarah": "Fiksi Sejarah",
    "Anak": "Anak-anak", "Anak-anak": "Anak-anak",
    "Cerpen": "Cerita Pendek",
    "Chicklit": "Chick Lit", "Chick-lit": "Chick Lit",
    "Sajak": "Puisi", "Syair": "Puisi",
}

GENRE_EXCLUDE = {
    "Sastra Indonesia", "Sastra", "Fiksi", "Nonfiction", "Non-fiction",
    "Nonfiksi", "Non Fiksi", "Non-fiksi", "Novel", "Roman",
}

# Genre-genre yang masuk analisis
ALL_GENRES = sorted(set(g for kl in KLASTER for g in kl["genres"]))

COVER_DIR = os.path.join(os.path.dirname(__file__), "..", "covers")


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def expand_genres(series):
    """Return list of list of normalized genre strings."""
    out = []
    for v in series:
        if pd.isna(v) or str(v).strip() == "":
            out.append([])
            continue
        raw = [g.strip() for g in str(v).split(",") if g.strip()]
        seen, normed = set(), []
        for g in raw:
            g2 = GENRE_NORM_MAP.get(g, g)
            if g2 not in GENRE_EXCLUDE and g2 not in seen:
                normed.append(g2)
                seen.add(g2)
        out.append(normed)
    return out


def genre_mask(genre_lists, genre):
    return [genre in gl for gl in genre_lists]


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


def klaster_label(genre):
    kl = GENRE_TO_KLASTER.get(genre)
    return f"{genre}  [{kl['id']}]" if kl else genre


def section_header(title, subtitle="", color="#2E4057", bg="#EEF2F7"):
    st.markdown(
        f'<div style="background:{bg};border-left:4px solid {color};'
        f'border-radius:0 8px 8px 0;padding:8px 14px;margin:1.2rem 0 .6rem;">'
        f'<div style="font-family:Georgia,serif;font-weight:600;color:{color};font-size:.95rem;">{title}</div>'
        f'{"<div style=font-size:.72rem;color:"+color+";opacity:.7;margin-top:3px;>"+subtitle+"</div>" if subtitle else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )


def prepare_df(df):
    """Filter ke typeface_paper yang valid, tambah genre_norm dan klaster."""
    df = df.copy()
    df = df[df["typeface_paper"].isin(TYPEFACE_4)].copy()
    gl = expand_genres(df["GENRES"])
    df["_genre_lists"] = gl

    # Genre utama (pertama yang dikenali)
    def first_known(gl_row):
        for g in gl_row:
            if g in GENRE_TO_KLASTER:
                return g
        return None

    df["genre_norm"] = [first_known(gl_row) for gl_row in gl]
    df["klaster_id"] = df["genre_norm"].map(
        lambda g: GENRE_TO_KLASTER[g]["id"] if g and g in GENRE_TO_KLASTER else None
    )
    return df


def build_crosstab(df, genre_list):
    """Build normalized crosstab: rows=genre, cols=typeface."""
    gl_all = df["_genre_lists"].tolist()
    rows = {}
    counts = {}
    for g in genre_list:
        mask = [g in gl for gl in gl_all]
        sub = df[mask]
        if len(sub) < 3:
            continue
        vc = sub["typeface_paper"].value_counts(normalize=True)
        rows[g] = {tf: vc.get(tf, 0.0) for tf in TYPEFACE_4}
        counts[g] = len(sub)
    mat = pd.DataFrame(rows).T
    return mat, counts


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: GAMBARAN UMUM
# ─────────────────────────────────────────────────────────────────────────────

def tab_gambaran(df, df_clean):
    n_total = len(df)
    n_clean = len(df_clean)
    n_unknown = (df["typeface_paper"] == "unknown").sum()

    # Stat cards
    c1, c2, c3, c4 = st.columns(4)
    stats = [
        ("Total Buku", n_total, "dalam korpus", "#2E4057"),
        ("Terklasifikasi", n_clean, f"{n_clean/n_total*100:.1f}% dari total", "#1D9E75"),
        ("Tidak Terklasifikasi", n_unknown, f"{n_unknown/n_total*100:.1f}% dari total", "#BDBDBD"),
        ("Kategori Typeface", 4, "Serif · Script · Sans-serif · Fancy", "#993556"),
    ]
    for col, (lbl, val, sub, clr) in zip([c1, c2, c3, c4], stats):
        with col:
            st.markdown(
                f'<div style="border:1px solid {clr}30;border-top:3px solid {clr};'
                f'border-radius:0 0 8px 8px;padding:.6rem .8rem;">'
                f'<div style="font-size:.62rem;color:#888;text-transform:uppercase;letter-spacing:.04em;">{lbl}</div>'
                f'<div style="font-size:1.6rem;font-weight:700;color:{clr};">{val:,}</div>'
                f'<div style="font-size:.58rem;color:#aaa;">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        section_header("Distribusi Typeface Keseluruhan", color="#2E4057")
        tc = df_clean["typeface_paper"].value_counts()
        fig = px.bar(
            x=tc.values, y=tc.index, orientation="h",
            color=tc.index,
            color_discrete_map=TYPEFACE_CLR,
            text=[f"{v:,}  ({v/n_clean*100:.1f}%)" for v in tc.values],
        )
        fig.update_layout(**pb(260), showlegend=False, xaxis_title="", yaxis_title="",
                          yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        section_header("Tren Typeface per Tahun", color="#2E4057")
        df_yr = df_clean[df_clean["YEAR"] > 0].copy()
        tr = df_yr.groupby(["YEAR", "typeface_paper"]).size().reset_index(name="n")
        fig2 = px.bar(
            tr, x="YEAR", y="n", color="typeface_paper",
            barmode="stack", color_discrete_map=TYPEFACE_CLR,
            labels={"typeface_paper": "Typeface"},
        )
        fig2.update_layout(**pb(260), xaxis_title="", yaxis_title="",
                           legend=dict(orientation="h", y=-.25, font=dict(size=10)))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<hr style='border:none;border-top:1px solid #eee;margin:1rem 0;'>", unsafe_allow_html=True)
    section_header("Pergeseran Tipografi per Dekade", color="#2E4057",
                   subtitle="Proporsi typeface dalam lima periode 2000–2025")

    df_dk = df_clean[df_clean["YEAR"] > 0].copy()
    df_dk["dekade"] = pd.cut(
        df_dk["YEAR"],
        bins=[1999, 2004, 2009, 2014, 2019, 2025],
        labels=["2000–04", "2005–09", "2010–14", "2015–19", "2020–25"],
    )
    shift = df_dk.groupby(["dekade", "typeface_paper"], observed=True).size().reset_index(name="n")
    shift["prop"] = shift.groupby("dekade", observed=True)["n"].transform(lambda x: x / x.sum())

    fig3 = px.line(
        shift, x="dekade", y="prop", color="typeface_paper",
        markers=True, color_discrete_map=TYPEFACE_CLR,
        labels={"dekade": "", "prop": "Proporsi", "typeface_paper": "Typeface"},
    )
    fig3.update_layout(**pb(300), legend=dict(orientation="h", y=-.25, font=dict(size=11)))
    fig3.update_traces(line_width=2.5)
    st.plotly_chart(fig3, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: HEATMAP GENRE
# ─────────────────────────────────────────────────────────────────────────────

def tab_heatmap(df_clean):
    section_header("Peta Panas Typeface × Genre",
                   subtitle="Persentase penggunaan typeface per genre, dikelompokkan berdasarkan klaster ko-kemunculan",
                   color="#2E4057")

    st.caption(f"n = {len(df_clean):,} buku terklasifikasi")

    # Build matrix
    gl_all = df_clean["_genre_lists"].tolist()
    mat, counts = build_crosstab(df_clean, ALL_GENRES)

    if mat.empty:
        st.info("Data tidak cukup.")
        return

    # Sort by klaster order
    klaster_order = {g: (["K1", "K2", "K3"].index(GENRE_TO_KLASTER[g]["id"]) * 100 + i)
                     for kl in KLASTER for i, g in enumerate(kl["genres"])}
    mat = mat.loc[[g for g in mat.index if g in klaster_order]]
    mat = mat.sort_values(by=mat.index.tolist(), key=lambda idx: [klaster_order.get(g, 999) for g in idx])

    y_labels = [f"{klaster_label(g)}  (n={counts.get(g,0)})" for g in mat.index]
    text_mat = (mat * 100).round(0).astype(int).astype(str) + "%"

    fig = go.Figure(data=go.Heatmap(
        z=mat.values,
        x=TYPEFACE_4,
        y=y_labels,
        colorscale="Purples",
        text=text_mat.values,
        texttemplate="%{text}",
        textfont=dict(size=11, color="#1A1A1A"),
        showscale=True,
        zmin=0, zmax=0.8,
    ))
    fig.update_layout(**pb(
        max(380, len(mat) * 34),
        margin=dict(l=210, r=20, t=36, b=90),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickangle=0, tickfont=dict(size=12)),
    ))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr style='border:none;border-top:1px solid #eee;margin:1rem 0;'>", unsafe_allow_html=True)

    # Delta chart
    section_header("Simpangan per Genre dari Rata-rata Korpus",
                   subtitle="Positif = genre lebih banyak memakai typeface ini dibanding rata-rata",
                   color="#37474F", bg="#ECEFF1")

    tc_all = df_clean["typeface_paper"].value_counts(normalize=True)
    rows_diff = []
    for g in mat.index:
        mask = [g in gl for gl in gl_all]
        sub = df_clean[mask]
        if sub.empty:
            continue
        tc_g = sub["typeface_paper"].value_counts(normalize=True)
        for tf in TYPEFACE_4:
            rows_diff.append({
                "Genre": klaster_label(g),
                "Typeface": tf,
                "Delta": tc_g.get(tf, 0) - tc_all.get(tf, 0),
            })

    df_diff = pd.DataFrame(rows_diff)
    if not df_diff.empty:
        fig_d = px.bar(
            df_diff, x="Delta", y="Genre", color="Typeface",
            orientation="h", barmode="group",
            color_discrete_map=TYPEFACE_CLR,
        )
        fig_d.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
        fig_d.update_layout(
            **pb(max(320, len(mat) * 52),
                 margin=dict(l=210, r=20, t=28, b=60)),
            xaxis_title="Selisih proporsi vs korpus", yaxis_title="",
            legend=dict(orientation="h", y=-.12, font=dict(size=10)),
        )
        st.plotly_chart(fig_d, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: PER KLASTER
# ─────────────────────────────────────────────────────────────────────────────

def tab_klaster(df_clean):
    section_header(
        "Tipografi berdasarkan Klaster Genre",
        subtitle="Tiga klaster merepresentasikan gravitasi tematik yang berbeda",
        color="#2E4057",
    )

    gl_all = df_clean["_genre_lists"].tolist()
    tc_all = df_clean["typeface_paper"].value_counts(normalize=True)

    # Summary cards
    kl_cols = st.columns(3)
    for kc, kl in zip(kl_cols, KLASTER):
        kl_set = set(kl["genres"])
        mask = [bool(kl_set & set(gl)) for gl in gl_all]
        n_kl = sum(mask)
        sub_kl = df_clean[mask]
        top = sub_kl["typeface_paper"].mode()
        top_str = top.iloc[0] if len(top) > 0 else "—"
        top_clr = TYPEFACE_CLR.get(top_str, "#888")
        with kc:
            st.markdown(
                f'<div style="background:{kl["bg"]};border-left:4px solid {kl["color"]};'
                f'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:.6rem;">'
                f'<div style="font-weight:700;font-size:.78rem;color:{kl["color"]};">'
                f'[{kl["id"]}] {kl["label"].split("—")[1].strip()}</div>'
                f'<div style="font-size:1.5rem;font-weight:700;color:{kl["color"]};'
                f'font-family:Georgia,serif;margin:.25rem 0 .1rem;">{n_kl:,}</div>'
                f'<div style="font-size:.62rem;opacity:.65;">buku terkait genre klaster</div>'
                f'<div style="margin-top:.4rem;font-size:.68rem;">'
                f'Typeface dominan: <span style="color:{top_clr};font-weight:600;">'
                f'{top_str}</span></div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Per-klaster detail
    for kl in KLASTER:
        st.markdown(
            f'<div style="background:{kl["bg"]};border-left:5px solid {kl["color"]};'
            f'border-radius:0 10px 10px 0;padding:10px 18px;margin:1rem 0 .5rem;">'
            f'<span style="font-family:Georgia,serif;font-weight:700;font-size:1rem;'
            f'color:{kl["color"]};">[{kl["id"]}] {kl["label"]}</span></div>',
            unsafe_allow_html=True,
        )

        kl_set = set(kl["genres"])
        mask = [bool(kl_set & set(gl)) for gl in gl_all]
        sub_kl = df_clean[mask]

        if sub_kl.empty:
            st.caption("Data tidak cukup.")
            continue

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Distribusi Typeface**")
            tc_kl = sub_kl["typeface_paper"].value_counts()
            fig_pie = px.pie(
                values=tc_kl.values, names=tc_kl.index,
                hole=0.42, color=tc_kl.index,
                color_discrete_map=TYPEFACE_CLR,
            )
            fig_pie.update_layout(**pb(260))
            fig_pie.update_traces(textinfo="percent+label", textfont_size=10)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_b:
            st.markdown("**Simpangan vs Korpus**")
            tc_kl_norm = sub_kl["typeface_paper"].value_counts(normalize=True)
            diff = (tc_kl_norm - tc_all).dropna().sort_values(ascending=False)
            d_df = diff.reset_index()
            d_df.columns = ["Typeface", "Delta"]
            fig_d = px.bar(
                d_df, x="Delta", y="Typeface", orientation="h",
                color="Typeface", color_discrete_map=TYPEFACE_CLR,
            )
            fig_d.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
            fig_d.update_layout(**pb(260), showlegend=False,
                                xaxis_title="Selisih vs korpus", yaxis_title="",
                                yaxis=dict(categoryorder="total ascending"))
            st.plotly_chart(fig_d, use_container_width=True)

        # Heatmap per klaster
        st.markdown("**Heatmap Typeface × Genre dalam Klaster**")
        mat_kl, counts_kl = build_crosstab(sub_kl, kl["genres"])
        if not mat_kl.empty:
            y_kl = [f"{g}  (n={counts_kl.get(g,0)})" for g in mat_kl.index]
            text_kl = (mat_kl * 100).round(0).astype(int).astype(str) + "%"
            cscale = {"K1": "Blues", "K2": "RdPu", "K3": "Greens"}.get(kl["id"], "Purples")
            fig_hm = go.Figure(data=go.Heatmap(
                z=mat_kl.values, x=TYPEFACE_4, y=y_kl,
                colorscale=cscale,
                text=text_kl.values, texttemplate="%{text}",
                textfont=dict(size=11, color="#1A1A1A"),
                showscale=True, zmin=0, zmax=0.8,
            ))
            fig_hm.update_layout(**pb(
                max(240, len(mat_kl) * 38),
                margin=dict(l=190, r=20, t=28, b=70),
                yaxis=dict(autorange="reversed"),
                xaxis=dict(tickangle=0),
            ))
            st.plotly_chart(fig_hm, use_container_width=True)
        else:
            st.caption("Data genre tidak cukup untuk heatmap.")

        # Tren per tahun dalam klaster
        df_kl_yr = sub_kl[sub_kl["YEAR"] > 0].copy()
        if len(df_kl_yr) >= 5:
            st.markdown("**Tren Typeface per Tahun**")
            tr = df_kl_yr.groupby(["YEAR", "typeface_paper"]).size().reset_index(name="n")
            fig_tr = px.bar(
                tr, x="YEAR", y="n", color="typeface_paper",
                barmode="stack", color_discrete_map=TYPEFACE_CLR,
            )
            fig_tr.update_layout(**pb(240), xaxis_title="", yaxis_title="",
                                  legend=dict(orientation="h", y=-.25, font=dict(size=9)))
            st.plotly_chart(fig_tr, use_container_width=True)

        st.markdown("<hr style='border:none;border-top:1px solid #eee;margin:.8rem 0;'>",
                    unsafe_allow_html=True)

    # Perbandingan antar klaster
    section_header("Perbandingan Typeface Antar Klaster",
                   subtitle="Proporsi setiap typeface di masing-masing klaster",
                   color="#37474F", bg="#ECEFF1")

    rows_cmp = []
    for kl in KLASTER:
        kl_set = set(kl["genres"])
        mask = [bool(kl_set & set(gl)) for gl in gl_all]
        sub = df_clean[mask]
        if sub.empty:
            continue
        tc = sub["typeface_paper"].value_counts(normalize=True)
        for tf in TYPEFACE_4:
            rows_cmp.append({
                "Klaster": kl["short"],
                "Typeface": tf,
                "Proporsi": tc.get(tf, 0.0),
            })

    df_cmp = pd.DataFrame(rows_cmp)
    if not df_cmp.empty:
        fig_cmp = px.bar(
            df_cmp, x="Klaster", y="Proporsi", color="Typeface",
            barmode="group", color_discrete_map=TYPEFACE_CLR,
            text=df_cmp["Proporsi"].map(lambda x: f"{x*100:.1f}%"),
        )
        fig_cmp.update_traces(textposition="outside", textfont_size=9)
        fig_cmp.update_layout(
            **pb(340), xaxis_title="", yaxis_title="Proporsi",
            legend=dict(orientation="h", y=-.18, font=dict(size=10)),
            yaxis=dict(tickformat=".0%"),
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

        # Tabel ringkasan
        pivot = df_cmp.pivot(index="Typeface", columns="Klaster", values="Proporsi")
        pivot = pivot.sort_values(by="Klaster 1", ascending=False)
        rows_html = []
        for tf, row_d in pivot.iterrows():
            clr = TYPEFACE_CLR.get(tf, "#888")
            cells = f'<td style="padding:5px 12px;border:1px solid #E0E0E0;font-weight:600;color:{clr};">{tf}</td>'
            for col_n in pivot.columns:
                val = row_d.get(col_n, 0)
                cells += f'<td style="padding:5px 12px;border:1px solid #E0E0E0;text-align:center;">{val*100:.1f}%</td>'
            rows_html.append(f"<tr>{cells}</tr>")

        hdr = "<th style='padding:6px 12px;background:#37474F;color:white;text-align:left;'>Typeface</th>"
        for kl in KLASTER:
            hdr += (
                f'<th style="padding:6px 12px;background:{kl["color"]};color:white;text-align:center;">'
                f'{kl["short"]}</th>'
            )
        st.markdown(
            f'<table style="width:100%;border-collapse:collapse;font-size:12px;margin-top:.5rem;">'
            f'<thead><tr>{hdr}</tr></thead>'
            f'<tbody>{"".join(rows_html)}</tbody></table>',
            unsafe_allow_html=True,
        )
        st.caption("Proporsi typeface (%) di dalam setiap klaster genre.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: PER GENRE
# ─────────────────────────────────────────────────────────────────────────────

def tab_per_genre(df_clean):
    gl_all = df_clean["_genre_lists"].tolist()
    tc_all = df_clean["typeface_paper"].value_counts(normalize=True)

    # Genre yang punya data cukup
    genre_opts = []
    for g in ALL_GENRES:
        mask = [g in gl for gl in gl_all]
        n = sum(mask)
        if n >= 5:
            genre_opts.append((g, n))
    genre_opts.sort(key=lambda x: -x[1])

    if not genre_opts:
        st.info("Tidak ada genre dengan data cukup.")
        return

    col_g, col_n = st.columns([3, 1])
    with col_g:
        sel = st.selectbox(
            "Pilih genre",
            options=[g for g, _ in genre_opts],
            format_func=klaster_label,
            key="pg4_sel",
        )
    with col_n:
        n_sel = next(n for g, n in genre_opts if g == sel)
        st.metric("Jumlah buku", f"{n_sel:,}")

    mask = [sel in gl for gl in gl_all]
    sub = df_clean[mask]
    kl_obj = GENRE_TO_KLASTER.get(sel)

    if kl_obj:
        st.markdown(
            f'<div style="background:{kl_obj["bg"]};border-left:4px solid {kl_obj["color"]};'
            f'border-radius:0 8px 8px 0;padding:7px 14px;margin:.3rem 0 .8rem;">'
            f'<span style="font-weight:700;color:{kl_obj["color"]};">{sel}</span>'
            f'<span style="font-size:.72rem;color:#888;margin-left:10px;">'
            f'[{kl_obj["id"]}] {kl_obj["label"].split("—")[1].strip()}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    ca, cb, cc = st.columns(3)

    with ca:
        st.markdown("**Distribusi Typeface**")
        tc_g = sub["typeface_paper"].value_counts()
        fig_pie = px.pie(
            values=tc_g.values, names=tc_g.index,
            hole=0.42, color=tc_g.index, color_discrete_map=TYPEFACE_CLR,
        )
        fig_pie.update_layout(**pb(240))
        fig_pie.update_traces(textinfo="percent+label", textfont_size=9)
        st.plotly_chart(fig_pie, use_container_width=True)

    with cb:
        st.markdown("**Simpangan dari Korpus**")
        tc_gn = sub["typeface_paper"].value_counts(normalize=True)
        diff = (tc_gn - tc_all).dropna().sort_values(ascending=False)
        d_df = diff.reset_index()
        d_df.columns = ["Typeface", "Delta"]
        fig_d = px.bar(
            d_df, x="Delta", y="Typeface", orientation="h",
            color="Typeface", color_discrete_map=TYPEFACE_CLR,
        )
        fig_d.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
        fig_d.update_layout(**pb(240), showlegend=False,
                            xaxis_title="Selisih vs korpus", yaxis_title="",
                            yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig_d, use_container_width=True)

    with cc:
        st.markdown("**Font Spesifik Terbanyak**")
        top_fonts = sub["tipe_font"].dropna().value_counts().head(10)
        if not top_fonts.empty:
            fig_f = px.bar(
                x=top_fonts.values, y=top_fonts.index, orientation="h",
                color_discrete_sequence=[TYPEFACE_CLR.get(
                    sub[sub["tipe_font"] == top_fonts.index[0]]["typeface_paper"].mode().iloc[0]
                    if len(sub[sub["tipe_font"] == top_fonts.index[0]]["typeface_paper"].mode()) > 0
                    else "Serif", "#3949AB"
                )],
                text=top_fonts.values,
            )
            fig_f.update_layout(**pb(240), showlegend=False, xaxis_title="", yaxis_title="",
                                yaxis=dict(categoryorder="total ascending"))
            fig_f.update_traces(textposition="outside", marker_line_width=0,
                                marker_color=[
                                    TYPEFACE_CLR.get(
                                        sub[sub["tipe_font"] == fn]["typeface_paper"].mode().iloc[0]
                                        if len(sub[sub["tipe_font"] == fn]["typeface_paper"].mode()) > 0
                                        else "Serif", "#888"
                                    ) for fn in top_fonts.index
                                ])
            st.plotly_chart(fig_f, use_container_width=True)
        else:
            st.caption("—")

    # Tren per tahun
    df_gyr = sub[sub["YEAR"] > 0]
    if len(df_gyr) >= 5:
        st.markdown("<hr style='border:none;border-top:1px solid #eee;margin:.8rem 0;'>",
                    unsafe_allow_html=True)
        st.markdown("**Tren Typeface per Tahun**")
        tr = df_gyr.groupby(["YEAR", "typeface_paper"]).size().reset_index(name="n")
        fig_tr = px.bar(
            tr, x="YEAR", y="n", color="typeface_paper",
            barmode="stack", color_discrete_map=TYPEFACE_CLR,
        )
        fig_tr.update_layout(**pb(260), xaxis_title="", yaxis_title="",
                              legend=dict(orientation="h", y=-.25, font=dict(size=9)))
        st.plotly_chart(fig_tr, use_container_width=True)

    # Typeface × Gaya Ilustrasi
    if "gaya_ilustrasi" in sub.columns:
        st.markdown("<hr style='border:none;border-top:1px solid #eee;margin:.8rem 0;'>",
                    unsafe_allow_html=True)
        section_header("Typeface × Gaya Ilustrasi",
                       subtitle="Korelasi pilihan typeface dengan gaya ilustrasi pada genre ini",
                       color="#5C6BC0", bg="#EDE7F6")

        GAYA_ID = {
            "photograph": "Fotografi", "flat_graphic": "Ilustrasi Datar",
            "hand_drawn": "Gambar Tangan", "text_dominant": "Dominan Teks",
            "abstract": "Abstrak", "collage": "Kolase",
        }
        sub_g = sub[sub["gaya_ilustrasi"].notna()].copy()
        sub_g["gaya_label"] = sub_g["gaya_ilustrasi"].map(GAYA_ID)

        if len(sub_g) >= 5:
            ct = pd.crosstab(sub_g["typeface_paper"], sub_g["gaya_label"], normalize="index")
            text_ct = (ct * 100).round(0).astype(int).astype(str) + "%"
            fig_ct = go.Figure(data=go.Heatmap(
                z=ct.values, x=ct.columns.tolist(), y=ct.index.tolist(),
                colorscale="RdYlGn",
                text=text_ct.values, texttemplate="%{text}",
                textfont=dict(size=11, color="#1A1A1A"),
                showscale=True, zmin=0, zmax=0.6,
            ))
            fig_ct.update_layout(**pb(
                260, margin=dict(l=120, r=20, t=28, b=90),
                yaxis=dict(autorange="reversed"),
                xaxis=dict(tickangle=-30),
            ))
            st.plotly_chart(fig_ct, use_container_width=True)
        else:
            st.caption("Data tidak cukup untuk cross-analisis.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5: TYPEFACE × ILUSTRASI (GLOBAL)
# ─────────────────────────────────────────────────────────────────────────────

def tab_typeface_ilustrasi(df_clean):
    if "gaya_ilustrasi" not in df_clean.columns:
        st.info("Kolom gaya_ilustrasi tidak tersedia.")
        return

    section_header(
        "Typeface × Gaya Ilustrasi — Keseluruhan Korpus",
        subtitle="Apakah pilihan typeface berkorelasi sistematis dengan gaya ilustrasi?",
        color="#4A148C", bg="#F3E5F5",
    )

    GAYA_ID = {
        "photograph": "Fotografi", "flat_graphic": "Ilustrasi Datar",
        "hand_drawn": "Gambar Tangan", "text_dominant": "Dominan Teks",
        "abstract": "Abstrak", "collage": "Kolase",
    }

    sub = df_clean[df_clean["gaya_ilustrasi"].notna()].copy()
    sub["gaya_label"] = sub["gaya_ilustrasi"].map(GAYA_ID)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Heatmap: Typeface → Gaya Ilustrasi (proporsi baris)**")
        ct = pd.crosstab(sub["typeface_paper"], sub["gaya_label"], normalize="index")
        text_ct = (ct * 100).round(0).astype(int).astype(str) + "%"
        fig = go.Figure(data=go.Heatmap(
            z=ct.values, x=ct.columns.tolist(), y=ct.index.tolist(),
            colorscale="Purples",
            text=text_ct.values, texttemplate="%{text}",
            textfont=dict(size=11, color="#1A1A1A"),
            showscale=True, zmin=0, zmax=0.5,
        ))
        fig.update_layout(**pb(
            260, margin=dict(l=120, r=20, t=28, b=90),
            yaxis=dict(autorange="reversed"),
            xaxis=dict(tickangle=-30),
        ))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("**Heatmap: Gaya Ilustrasi → Typeface (proporsi baris)**")
        ct2 = pd.crosstab(sub["gaya_label"], sub["typeface_paper"], normalize="index")
        text_ct2 = (ct2 * 100).round(0).astype(int).astype(str) + "%"
        fig2 = go.Figure(data=go.Heatmap(
            z=ct2.values, x=ct2.columns.tolist(), y=ct2.index.tolist(),
            colorscale="Greens",
            text=text_ct2.values, texttemplate="%{text}",
            textfont=dict(size=11, color="#1A1A1A"),
            showscale=True, zmin=0, zmax=0.7,
        ))
        fig2.update_layout(**pb(
            280, margin=dict(l=160, r=20, t=28, b=70),
            yaxis=dict(autorange="reversed"),
            xaxis=dict(tickangle=0),
        ))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<hr style='border:none;border-top:1px solid #eee;margin:1rem 0;'>",
                unsafe_allow_html=True)

    # Distribusi gaya ilustrasi per typeface (grouped bar)
    section_header("Distribusi Gaya Ilustrasi per Typeface",
                   color="#37474F", bg="#ECEFF1")

    rows = []
    for tf in TYPEFACE_4:
        sub_tf = sub[sub["typeface_paper"] == tf]
        if sub_tf.empty:
            continue
        vc = sub_tf["gaya_label"].value_counts(normalize=True)
        for gaya, prop in vc.items():
            rows.append({"Typeface": tf, "Gaya Ilustrasi": gaya, "Proporsi": prop})

    df_rows = pd.DataFrame(rows)
    if not df_rows.empty:
        GAYA_CLR = {
            "Fotografi": "#1565C0", "Ilustrasi Datar": "#00897B",
            "Gambar Tangan": "#E65100", "Dominan Teks": "#6A1B9A",
            "Abstrak": "#AD1457", "Kolase": "#F9A825",
        }
        fig3 = px.bar(
            df_rows, x="Typeface", y="Proporsi", color="Gaya Ilustrasi",
            barmode="group", color_discrete_map=GAYA_CLR,
            text=df_rows["Proporsi"].map(lambda x: f"{x*100:.0f}%"),
        )
        fig3.update_traces(textposition="outside", textfont_size=8)
        fig3.update_layout(
            **pb(320), xaxis_title="", yaxis_title="Proporsi",
            legend=dict(orientation="h", y=-.2, font=dict(size=10)),
            yaxis=dict(tickformat=".0%"),
        )
        st.plotly_chart(fig3, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 6: CATATAN METODOLOGIS
# ─────────────────────────────────────────────────────────────────────────────

def tab_metodologi(df, df_clean):
    section_header("Catatan Metodologis", color="#B71C1C", bg="#FFEBEE")

    n_total = len(df)
    n_clean = len(df_clean)
    n_high = (df["typeface_paper_low_conf"] == False).sum() if "typeface_paper_low_conf" in df.columns else 0

    st.markdown(f"""
### Sistem Klasifikasi 4 Kategori

Modul ini menggunakan kolom **`typeface_paper`** yang mengklasifikasikan seluruh font ke dalam empat kategori besar berdasarkan kerangka tipografi Lupton (*Thinking with Type*, 2024):

| Kategori | Deskripsi | Contoh Font |
|---|---|---|
| **Serif** | Ada kait, kontras stroke, kesan formal | Garamond, Bodoni, Baskerville, Times New Roman |
| **Script** | Stroke mengalir, menyerupai tulisan tangan | Kalam, Dancing Script, Parisienne, Great Vibes |
| **Sans-serif** | Tanpa kait, stroke seragam, kesan modern | Helvetica, Montserrat, Poppins, Oswald |
| **Fancy** | Ornamental, eksperimental, di luar konvensi | Impact, Bebas Neue, Pirata One, Creepster |

### Pipeline Klasifikasi

Klasifikasi `typeface_paper` menggunakan pendekatan bertingkat:
1. **OCR (EasyOCR)** — deteksi teks di sampul → *fuzzy string matching* ke metadata judul/penulis
2. **Database lookup** — cocokkan ke 920 font dari Google Fonts + DaFont → ambil kategori dari DB
3. **CLIP fallback** — jika tidak ditemukan di DB, gunakan CLIP ViT-B/32 untuk klasifikasi visual langsung

Metode pencocokan yang digunakan (match_type):
""")

    if "match_type" in df.columns:
        mt = df["match_type"].value_counts()
        mt_pct = (mt / len(df) * 100).round(1)
        for k, v in mt.items():
            st.markdown(f"- **{k}**: {v:,} buku ({mt_pct[k]}%)")

    st.markdown(f"""

### Keterbatasan Data

**1. Coverage ({n_clean:,} dari {n_total:,} buku = {n_clean/n_total*100:.1f}%)**  
Tidak semua sampul berhasil diklasifikasikan. Sampul dengan teks yang sangat dekoratif, kecil, atau tumpang tindih dengan ilustrasi cenderung gagal terdeteksi OCR dan masuk kategori `unknown`. Hasil analisis mencerminkan buku-buku yang *berhasil* terklasifikasi, bukan seluruh korpus.

**2. Akurasi CLIP**  
Model CLIP ViT-B/32 tidak dilatih khusus untuk identifikasi font, sehingga prediksinya merupakan aproksimasi visual. Khususnya untuk font-font dekoratif yang unik, hasil klasifikasi perlu dibaca sebagai kecenderungan kategori, bukan identifikasi font yang pasti.

**3. Sample size genre kecil**  
Beberapa genre (Aksi, Petualangan, Slice of Life, Dewasa, Persahabatan) memiliki jumlah sampel yang sangat kecil (< 10 buku). Persentase pada genre-genre ini tidak dapat diandalkan untuk generalisasi dan sebaiknya dibaca sebagai indikasi saja.

**4. Klasifikasi genre**  
Genre dinormalisasi dari tag Goodreads yang bervariasi. Satu buku bisa memiliki beberapa tag genre; analisis ini menggunakan genre pertama yang dikenali dalam daftar prioritas klaster. Buku dengan genre yang ambigu atau tidak masuk dalam sistem klaster tidak diikutsertakan.
""")

    if "typeface_paper_low_conf" in df.columns:
        n_low = (df["typeface_paper_low_conf"] == True).sum()
        st.markdown(f"""
**5. Confidence**  
- High confidence: **{n_high:,} buku** ({n_high/n_total*100:.1f}%)  
- Low confidence: **{n_low:,} buku** ({n_low/n_total*100:.1f}%)  

Untuk klaim analitis yang kuat, disarankan membaca data *high confidence* saja.
""")

    st.markdown("""
### Klaster Genre (versi ini)

| Klaster | Genre |
|---|---|
| **K1** | Novel, Cerita Pendek, Antologi, Puisi |
| **K2** | Romansa, Chick Lit, Persahabatan, Remaja, Dewasa, Keluarga, Drama, Slice of Life |
| **K3** | Fantasi, Fiksi Sejarah, Petualangan, Aksi, Fiksi Sains, Thriller/Misteri, Horor, Anak-anak, **Komedi** |

> **Catatan**: Komedi dimasukkan ke Klaster 3 (Eskapisme) karena secara mode naratif lebih dekat dengan genre-genre yang mengoperasikan dunia alternatif atau membangun jarak dengan realitas keseharian, berbeda dari genre K2 yang menonjolkan kedekatan emosional dengan realitas pembaca.
""")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def render_tipografi_4cat(DF):
    """
    Halaman Tipografi — versi 4 kategori (typeface_paper).
    Panggil dari app utama:

        elif HAL == "Tipografi":
            from tipografi_4cat import render_tipografi_4cat
            render_tipografi_4cat(DF)
    """
    st.markdown("## Analisis Tipografi")
    st.markdown(
        "Klasifikasi *typeface* pada 5.069 sampul buku sastra Indonesia (2000–2025) "
        "menggunakan empat kategori utama: **Serif · Script · Sans-serif · Fancy**.",
    )

    # ── Kartu 4 kategori ─────────────────────────────────────────────────────
    tf_cols = st.columns(4)
    font_examples = {
        "Serif":      ("Georgia, 'Times New Roman', serif", "Aa"),
        "Script":     ("cursive", "𝒜𝒶"),
        "Sans-serif": ("Helvetica, Arial, sans-serif", "Aa"),
        "Fancy":      ("Impact, 'Arial Black', fantasy", "Aa"),
    }
    for col_tf, tf in zip(tf_cols, TYPEFACE_4):
        clr = TYPEFACE_CLR[tf]
        font_css, sample = font_examples[tf]
        with col_tf:
            st.markdown(
                f'<div style="border:1px solid {clr}25;border-top:3px solid {clr};'
                f'border-radius:0 0 8px 8px;padding:.6rem .6rem;text-align:center;">'
                f'<div style="font-family:{font_css};font-size:1.6rem;color:{clr};'
                f'font-weight:700;line-height:1.1;">{sample}</div>'
                f'<div style="font-size:.7rem;font-weight:700;margin:.25rem 0 .1rem;color:{clr};">{tf}</div>'
                f'<div style="font-size:.57rem;opacity:.55;text-align:left;line-height:1.4;'
                f'margin-bottom:.2rem;">{TYPEFACE_DESC[tf]}</div>'
                f'<div style="font-size:.54rem;opacity:.38;text-align:left;line-height:1.35;'
                f'font-style:italic;">{TYPEFACE_LUPTON[tf]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<hr style='border:none;border-top:1px solid #eee;margin:1rem 0;'>",
                unsafe_allow_html=True)

    # ── Prepare data ──────────────────────────────────────────────────────────
    df_clean = prepare_df(DF)
    n_clean = len(df_clean)
    n_total = len(DF)

    st.caption(
        f"Data aktif: **{n_clean:,} buku** terklasifikasi dari {n_total:,} total "
        f"({n_clean/n_total*100:.1f}%). Sumber: kolom `typeface_paper`."
    )

    # ── Tab navigasi ──────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Gambaran Umum",
        "🗺 Peta Panas Genre",
        "🎭 Per Klaster",
        "🔍 Per Genre",
        "🖼 Typeface × Ilustrasi",
        "⚠️ Catatan Metodologis",
    ])

    with tab1:
        tab_gambaran(DF, df_clean)

    with tab2:
        tab_heatmap(df_clean)

    with tab3:
        tab_klaster(df_clean)

    with tab4:
        tab_per_genre(df_clean)

    with tab5:
        tab_typeface_ilustrasi(df_clean)

    with tab6:
        tab_metodologi(DF, df_clean)


# ─────────────────────────────────────────────────────────────────────────────
# ALIAS — kompatibilitas dengan import lama di streamlit_app.py
# ─────────────────────────────────────────────────────────────────────────────
render_tipografi = render_tipografi_4cat
