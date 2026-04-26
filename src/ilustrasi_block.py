"""
ilustrasi_block_v7.py
Halaman analisis corak ilustrasi — versi CLIP 10 kategori.

Dipanggil dari app.py:
    from ilustrasi_block_v7 import render_ilustrasi
    render_ilustrasi(DF, cover_dir=COVER_DIR)

Kolom utama:
- corak_ilustrasi, corak_konfiden, corak_metode
- corak_skor_realisme, corak_skor_dekoratif, dst.
- objects_detected, objects_count, has_person, has_nature, dominant_object
- IMAGE_FILE, TITLE, AUTHOR, YEAR, GENRES, ILLUSTRATOR
"""

import os
from collections import Counter

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


CORAK_ID = {
    "realisme": "Realisme",
    "dekoratif": "Dekoratif",
    "kartunal": "Kartunal",
    "ekspresionisme": "Ekspresionisme",
    "surealis_absurd": "Surealis / Absurd",
    "pop_art": "Pop Art",
    "kubisme": "Kubisme",
    "abstrak": "Abstrak",
    "minimalis": "Minimalis",
    "fotografi_kolase": "Fotografi / Digital Collage",
}

CORAK_CLR = {
    "realisme": "#1E88E5",
    "dekoratif": "#43A047",
    "kartunal": "#FB8C00",
    "ekspresionisme": "#E53935",
    "surealis_absurd": "#8E24AA",
    "pop_art": "#FDD835",
    "kubisme": "#6D4C41",
    "abstrak": "#00ACC1",
    "minimalis": "#757575",
    "fotografi_kolase": "#3949AB",
}

CORAK_ICON = {
    "realisme": "🧍",
    "dekoratif": "🌺",
    "kartunal": "🧸",
    "ekspresionisme": "🔥",
    "surealis_absurd": "🌀",
    "pop_art": "💥",
    "kubisme": "🔶",
    "abstrak": "🔷",
    "minimalis": "⚪",
    "fotografi_kolase": "📷",
}

CORAK_DESKRIPSI = {
    "realisme": "Objek digambarkan menyerupai dunia nyata: proporsi akurat, detail tinggi, perspektif dan pencahayaan natural.",
    "dekoratif": "Visual datar dengan ornamen, pola repetitif, garis tegas, warna solid, dan minim ilusi kedalaman.",
    "kartunal": "Bentuk disederhanakan atau dilebih-lebihkan, ekspresi kuat, outline jelas, dan nuansa jenaka atau komikal.",
    "ekspresionisme": "Bentuk dan warna didistorsi untuk menekankan emosi, suasana dramatik, dan intensitas psikologis.",
    "surealis_absurd": "Kombinasi objek atau ruang yang tidak logis, aneh, mimpi, absurd, atau melanggar kenyataan.",
    "pop_art": "Warna cerah, kontras tinggi, bahasa visual komik/iklan, halftone, dan kesan budaya populer.",
    "kubisme": "Objek terpecah menjadi bidang geometris, sudut tajam, fragmentasi, dan banyak perspektif sekaligus.",
    "abstrak": "Tidak menghadirkan objek nyata secara jelas; fokus pada warna, garis, bentuk, tekstur, dan komposisi.",
    "minimalis": "Elemen visual sedikit, ruang kosong dominan, warna terbatas, bentuk sederhana, dan komposisi bersih.",
    "fotografi_kolase": "Menggunakan foto, montase, manipulasi digital, atau gabungan elemen fotografis dan grafis.",
}

CORAK_ORDER = [
    "kartunal", "minimalis", "ekspresionisme", "fotografi_kolase", "abstrak",
    "surealis_absurd", "dekoratif", "pop_art", "realisme", "kubisme",
]

YOLO_ID = {
    "person": "orang", "bicycle": "sepeda", "car": "mobil", "motorcycle": "motor",
    "airplane": "pesawat", "bus": "bus", "train": "kereta", "truck": "truk", "boat": "perahu",
    "traffic light": "lampu lalu lintas", "fire hydrant": "hidran", "stop sign": "rambu stop",
    "parking meter": "meteran parkir", "bench": "bangku", "bird": "burung", "cat": "kucing",
    "dog": "anjing", "horse": "kuda", "sheep": "domba", "cow": "sapi", "elephant": "gajah",
    "bear": "beruang", "zebra": "zebra", "giraffe": "jerapah", "backpack": "ransel",
    "umbrella": "payung", "handbag": "tas tangan", "tie": "dasi", "suitcase": "koper",
    "sports ball": "bola olahraga", "kite": "layang-layang", "bottle": "botol",
    "wine glass": "gelas anggur", "cup": "cangkir", "fork": "garpu", "knife": "pisau",
    "spoon": "sendok", "bowl": "mangkuk", "banana": "pisang", "apple": "apel",
    "sandwich": "sandwich", "orange": "jeruk", "broccoli": "brokoli", "carrot": "wortel",
    "hot dog": "hot dog", "pizza": "pizza", "donut": "donat", "cake": "kue",
    "chair": "kursi", "couch": "sofa", "potted plant": "tanaman pot", "bed": "tempat tidur",
    "dining table": "meja makan", "toilet": "toilet", "tv": "televisi", "laptop": "laptop",
    "mouse": "tetikus", "remote": "remote", "keyboard": "keyboard", "cell phone": "ponsel",
    "book": "buku", "clock": "jam", "vase": "vas", "scissors": "gunting",
    "teddy bear": "boneka beruang", "toothbrush": "sikat gigi",
}

GENRE_EXCLUDE = {
    "Sastra Indonesia", "Sastra", "Fiksi", "Nonfiction", "Non-fiction",
    "Nonfiksi", "Non Fiksi", "Non-fiksi", ""
}

_GENRE_NORM_RAW = {
    "Cinta": "Romansa", "Roman": "Romansa", "Romansa Kontemporer": "Romansa",
    "Romansa kontemporer": "Romansa", "Kontemporer": "Romansa", "Romansatic": "Romansa",
    "Young Adult Romansace": "Romansa", "Thriller": "Thriller/Misteri", "Misteri": "Thriller/Misteri",
    "Misteri Thriller": "Thriller/Misteri", "Thriller Suspense": "Thriller/Misteri",
    "Psychological Thriller": "Thriller/Misteri", "Suspense": "Thriller/Misteri",
    "Detective": "Thriller/Misteri", "Kriminal": "Thriller/Misteri", "Supranatural": "Horor",
    "Humor": "Komedi", "New Adult": "Remaja", "Collections": "Antologi", "Middle Grade": "Fantasi",
    "Fiksi Ilmiah": "Fiksi Sains", "Distopia": "Fiksi Sains", "Sejarah": "Fiksi Sejarah",
    "Historical Fiction": "Fiksi Sejarah", "Historical": "Fiksi Sejarah",
}
_GENRE_NORM_LOWER = {k.lower(): v for k, v in _GENRE_NORM_RAW.items()}

KLASTER_ORDERED = [
    {"id": "K1", "genres": ["Novel", "Cerita Pendek", "Antologi", "Puisi"]},
    {"id": "K2", "genres": ["Romansa", "Chick Lit", "Persahabatan", "Remaja", "Dewasa", "Keluarga", "Drama", "Slice of Life"]},
    {"id": "K3", "genres": ["Fantasi", "Fiksi Sejarah", "Petualangan", "Anak-anak", "Fiksi Sains", "Thriller/Misteri", "Horor", "Komedi"]},
]
GENRE_KLASTER_MAP = {}
for _kl in KLASTER_ORDERED:
    for _g in _kl["genres"]:
        GENRE_KLASTER_MAP.setdefault(_g, _kl)
_KLASTER_GENRE_ORDER = [g for kl in KLASTER_ORDERED for g in kl["genres"]]


def pb(height=320, **kw):
    base = dict(
        height=height,
        margin=dict(l=8, r=8, t=34, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color="#1A1A1A"),
    )
    base.update(kw)
    return base


def _hr():
    st.markdown("<hr style='border:none;border-top:1px solid rgba(128,128,128,.12);margin:1.3rem 0;'>", unsafe_allow_html=True)


def _terjemahkan_objek(label: str) -> str:
    label = str(label).strip().lower()
    return YOLO_ID.get(label, label)


def _norm_genre(g: str) -> str:
    g = str(g).strip()
    return _GENRE_NORM_LOWER.get(g.lower(), g)


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
                if g2 not in seen:
                    normed.append(g2)
                    seen.add(g2)
            out.append(normed)
        else:
            out.append(raw)
    return out


def _genre_counts(d: pd.DataFrame) -> Counter:
    gc = Counter()
    if "GENRES" not in d.columns:
        return gc
    for gl in expand_genres(d["GENRES"], normalize=True):
        gc.update(gl)
    return gc


def _top_genres_ordered(d: pd.DataFrame, n: int = 16, min_count: int = 3) -> list:
    gc = _genre_counts(d)
    eligible = {g for g, c in gc.items() if g not in GENRE_EXCLUDE and c >= min_count}
    ordered = [g for g in _KLASTER_GENRE_ORDER if g in eligible]
    rest = [g for g, _ in gc.most_common() if g in eligible and g not in ordered]
    return (ordered + rest)[:n]


def _klaster_shapes(genres: list) -> list:
    shapes, prev_kl = [], None
    for i, g in enumerate(genres):
        kl = GENRE_KLASTER_MAP.get(g, {}).get("id")
        if kl != prev_kl and i > 0:
            shapes.append(dict(type="line", xref="paper", yref="y", x0=0, x1=1, y0=i - 0.5, y1=i - 0.5, line=dict(color="rgba(0,0,0,.3)", width=1.5, dash="dot")))
        prev_kl = kl
    return shapes


def _make_y_labels(genres: list) -> list:
    return [f"{g}  [{GENRE_KLASTER_MAP[g]['id']}]" if g in GENRE_KLASTER_MAP else g for g in genres]


def cover_path(img, cover_dir):
    if not img or str(img) in ("", "nan", "None"):
        return None
    p = os.path.join(cover_dir, str(img))
    return p if os.path.exists(p) else None


def _bool_series(s):
    return s.astype(str).str.upper().isin(["TRUE", "1", "YES", "YA"])


def _prepare_df(DF: pd.DataFrame) -> pd.DataFrame:
    d = DF.copy()
    if "gaya_ilustrasi" in d.columns and "corak_ilustrasi" not in d.columns:
        d = d.rename(columns={"gaya_ilustrasi": "corak_ilustrasi"})
    if "gaya_skor" in d.columns and "corak_konfiden" not in d.columns:
        d = d.rename(columns={"gaya_skor": "corak_konfiden"})
    if "corak_ilustrasi" in d.columns:
        d["corak_ilustrasi"] = d["corak_ilustrasi"].astype(str).str.strip()
        d.loc[d["corak_ilustrasi"].isin(["nan", "None", ""]), "corak_ilustrasi"] = pd.NA
    if "corak_konfiden" in d.columns:
        d["corak_konfiden"] = pd.to_numeric(d["corak_konfiden"], errors="coerce").fillna(0.0)
    else:
        d["corak_konfiden"] = 0.0
    if "YEAR" in d.columns:
        d["YEAR"] = pd.to_numeric(d["YEAR"], errors="coerce").fillna(0).astype(int)
    if "IMAGE_FILE" in d.columns and "image_ok" not in d.columns:
        d["image_ok"] = True
    if "ILLUSTRATOR" in d.columns:
        d["ILLUSTRATOR"] = d["ILLUSTRATOR"].fillna("").astype(str).str.strip()
        d.loc[d["ILLUSTRATOR"].isin(["nan", "NaN", "None"]), "ILLUSTRATOR"] = ""
    return d


def _parse_objects_detected(series, terjemahkan=True) -> Counter:
    ctr = Counter()
    for val in series:
        if pd.isna(val) or str(val).strip() in ("", "nan", "[]", "{}"):
            continue
        items = [x.strip() for x in str(val).replace(";", ",").split(",") if x.strip()]
        for item in items:
            raw = item.strip().strip("[]{}\"'")
            count = 1
            if "|" in raw:
                raw_label = raw.split("|", 1)[0].strip()
            elif ":" in raw:
                raw_label, raw_count = raw.split(":", 1)
                raw_label = raw_label.strip()
                try:
                    count = int(float(raw_count.strip()))
                except Exception:
                    count = 1
            else:
                raw_label = raw.strip()
            if raw_label:
                label = _terjemahkan_objek(raw_label) if terjemahkan else raw_label
                ctr[label] += count
    return ctr


def _detect_object_col(df: pd.DataFrame):
    for c in ["objects_detected", "detected_objects", "yolo_objects", "yolo_objek", "yolo_labels"]:
        if c in df.columns:
            return c
    return None


def heatmap_corak_genre(d: pd.DataFrame, top_n=16, min_count=3, normalize="index"):
    genres = _top_genres_ordered(d, top_n, min_count=min_count)
    corak_keys = [k for k in CORAK_ORDER if k in CORAK_ID]
    corak_labels = [CORAK_ID[k] for k in corak_keys]
    mat = pd.DataFrame(0.0, index=genres, columns=corak_labels)
    d2 = d[d["corak_ilustrasi"].notna() & ~d["corak_ilustrasi"].isin(["gagal_load", "error_model"])].copy()
    if d2.empty or "GENRES" not in d2.columns:
        return go.Figure()
    genre_lists = expand_genres(d2["GENRES"], normalize=True)
    for g in genres:
        sub = d2[[g in gl for gl in genre_lists]]
        if sub.empty:
            continue
        if normalize == "count":
            vc = sub["corak_ilustrasi"].value_counts()
            for k in corak_keys:
                mat.loc[g, CORAK_ID[k]] = vc.get(k, 0)
        else:
            vc = sub["corak_ilustrasi"].value_counts(normalize=True)
            for k in corak_keys:
                mat.loc[g, CORAK_ID[k]] = vc.get(k, 0.0)
    y_labels = _make_y_labels(genres)
    if normalize == "count":
        text_mat = mat.round(0).astype(int).astype(str)
        z = mat.values
        hovertemplate = "Genre: %{y}<br>Corak: %{x}<br>Jumlah: %{z}<extra></extra>"
    else:
        text_mat = (mat * 100).round(0).astype(int).astype(str) + "%"
        z = mat.values
        hovertemplate = "Genre: %{y}<br>Corak: %{x}<br>Proporsi: %{text}<extra></extra>"
    fig = go.Figure(data=go.Heatmap(z=z, x=corak_labels, y=y_labels, colorscale="Greens", text=text_mat.values, texttemplate="%{text}", textfont=dict(size=9, color="#1A1A1A"), showscale=True, hovertemplate=hovertemplate))
    fig.update_layout(**pb(max(380, top_n * 32), margin=dict(l=210, r=20, t=42, b=95), yaxis=dict(autorange="reversed"), xaxis=dict(tickangle=-30), xaxis_title="", yaxis_title="", shapes=_klaster_shapes(genres)))
    return fig


def heatmap_objek_genre(d: pd.DataFrame, object_col: str, top_n_obj=20, top_n_genre=14):
    genres = _top_genres_ordered(d, top_n_genre)
    if object_col not in d.columns or not genres:
        return None
    ctr_global = _parse_objects_detected(d[object_col], terjemahkan=True)
    if not ctr_global:
        return None
    top_objs = [o for o, _ in ctr_global.most_common(top_n_obj)]
    mat = pd.DataFrame(0.0, index=genres, columns=top_objs)
    genre_lists = expand_genres(d["GENRES"], normalize=True)
    for g in genres:
        sub = d[[g in gl for gl in genre_lists]]
        n_sub = len(sub)
        if n_sub == 0:
            continue
        for obj in top_objs:
            obj_en_candidates = [k for k, v in YOLO_ID.items() if v == obj]
            obj_candidates = [obj.lower()] + [x.lower() for x in obj_en_candidates]
            def has_obj(val):
                s = str(val).lower()
                return any(x in s for x in obj_candidates)
            mat.loc[g, obj] = sub[object_col].apply(has_obj).sum() / n_sub
    text_mat = (mat * 100).round(0).astype(int).astype(str) + "%"
    fig = go.Figure(data=go.Heatmap(z=mat.values, x=top_objs, y=_make_y_labels(genres), colorscale="YlOrRd", text=text_mat.values, texttemplate="%{text}", textfont=dict(size=8, color="#1A1A1A"), showscale=True, zmin=0, zmax=max(float(mat.values.max()), 0.01)))
    fig.update_layout(**pb(max(380, top_n_genre * 32), margin=dict(l=210, r=20, t=42, b=115), yaxis=dict(autorange="reversed"), xaxis=dict(tickangle=-40), xaxis_title="", yaxis_title="", shapes=_klaster_shapes(genres), title="% sampul per genre yang mengandung objek"))
    return fig


def prob_bars_html(row):
    vals = []
    for k in CORAK_ID:
        col = f"corak_skor_{k}"
        if col in row.index:
            try:
                vals.append((k, float(row.get(col, 0) or 0)))
            except Exception:
                pass
    if not vals:
        return ""
    bars = ""
    for k, val in sorted(vals, key=lambda x: -x[1])[:5]:
        pct = val * 100
        label = CORAK_ID.get(k, k)
        clr = CORAK_CLR.get(k, "#999")
        bars += f'<div style="margin:.1rem 0;"><div style="font-size:.6rem;display:flex;justify-content:space-between;margin-bottom:1px;opacity:.72;"><span>{label}</span><span>{pct:.1f}%</span></div><div style="background:rgba(128,128,128,.12);border-radius:3px;height:5px;"><div style="width:{pct:.1f}%;height:5px;border-radius:3px;background:{clr};"></div></div></div>'
    return bars


def book_card_corak(row, col_obj, cover_dir, show_probs=False):
    with col_obj:
        cp = cover_path(row.get("IMAGE_FILE"), cover_dir)
        if cp:
            st.image(cp, use_container_width=True)
        else:
            st.markdown('<div style="height:170px;background:rgba(128,128,128,.09);border-radius:8px 8px 0 0;display:flex;align-items:center;justify-content:center;font-size:2rem;">📖</div>', unsafe_allow_html=True)
        corak = str(row.get("corak_ilustrasi", "") or "")
        label = CORAK_ID.get(corak, corak)
        clr = CORAK_CLR.get(corak, "#999")
        icon = CORAK_ICON.get(corak, "🎨")
        conf = float(row.get("corak_konfiden", 0) or 0)
        title = str(row.get("TITLE", "–"))
        author = str(row.get("AUTHOR", "–"))
        year = row.get("YEAR", "–")
        url = row.get("URL", "")
        title_html = f'<a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">{title}</a>' if isinstance(url, str) and url.startswith("http") else title
        obj = str(row.get("dominant_object", "") or "")
        obj_id = _terjemahkan_objek(obj) if obj else ""
        prob_html = f'<div style="margin-top:.4rem;">{prob_bars_html(row)}</div>' if show_probs else ""
        obj_badge = f"<span style='display:inline-block;font-size:.62rem;padding:1px 7px;border-radius:20px;background:rgba(128,128,128,.1);margin-left:3px;'>Objek: {obj_id}</span>" if obj_id else ""
        st.markdown(f'<div style="padding:.55rem .7rem .75rem;"><div style="font-family:Lora,serif;font-size:.82rem;font-weight:600;line-height:1.3;">{title_html}</div><div style="font-size:.71rem;opacity:.6;margin:.15rem 0 .3rem;">{author} · {year}</div><span style="display:inline-block;font-size:.64rem;font-weight:500;padding:1px 7px;border-radius:20px;border:1px solid {clr};color:{clr};margin:2px 2px 0 0;">{icon} {label} {conf:.2f}</span>{obj_badge}{prob_html}</div>', unsafe_allow_html=True)


def grid_corak(subset, n_cols=4, cover_dir="", show_probs=False):
    subset = subset.reset_index(drop=True)
    if subset.empty:
        st.info("Tidak ada buku yang cocok dengan filter ini.")
        return
    for start in range(0, len(subset), n_cols):
        chunk = subset.iloc[start:start + n_cols]
        cols = st.columns(n_cols)
        for j, (_, row) in enumerate(chunk.iterrows()):
            book_card_corak(row, cols[j], cover_dir, show_probs=show_probs)


def render_ilustrasi(DF: pd.DataFrame, cover_dir: str = ""):
    DF = _prepare_df(DF)
    st.markdown("## Analisis Corak Ilustrasi")
    st.caption("Versi CLIP 10 kategori: realisme, dekoratif, kartunal, ekspresionisme, surealis/absurd, pop art, kubisme, abstrak, minimalis, dan fotografi/digital collage.")
    if "corak_ilustrasi" not in DF.columns:
        st.error("Kolom `corak_ilustrasi` tidak ditemukan. Pastikan memakai hasil CSV pipeline ilustrasi terbaru.")
        return
    valid_mask = DF["corak_ilustrasi"].notna() & ~DF["corak_ilustrasi"].isin(["gagal_load", "error_model", ""])
    D = DF[valid_mask].copy()
    with st.expander("📖 Metode analisis ilustrasi", expanded=False):
        st.markdown("""
Analisis ilustrasi menggunakan **CLIP zero-shot classification** pada level gambar penuh (*whole-image level*).
Setiap kategori corak direpresentasikan oleh beberapa prompt tekstual, lalu skor setiap prompt diagregasikan
menjadi skor kategori melalui pendekatan **multi-prompt voting**. Hasilnya dibaca sebagai kecenderungan visual probabilistik, bukan label mutlak.
        """)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total sampul", f"{len(DF):,}")
    c2.metric("Terkategorikan", f"{len(D):,}")
    c3.metric("Rata-rata confidence", f"{D['corak_konfiden'].mean():.3f}" if len(D) else "–")
    c4.metric("Ambigu < 0.22", f"{(D['corak_konfiden'] < 0.22).sum():,}" if len(D) else "–")
    _hr()
    st.markdown("### Sepuluh Corak Ilustrasi")
    for row_keys in [CORAK_ORDER[:5], CORAK_ORDER[5:]]:
        cols = st.columns(len(row_keys))
        for col, key in zip(cols, row_keys):
            n = int((D["corak_ilustrasi"] == key).sum())
            pct = n / len(D) * 100 if len(D) else 0
            clr = CORAK_CLR.get(key, "#999")
            with col:
                st.markdown(f'<div style="border:1px solid rgba(128,128,128,.18);border-radius:10px;padding:.65rem .55rem .75rem;text-align:center;height:100%;"><div style="font-size:1.6rem;margin-bottom:.25rem;">{CORAK_ICON[key]}</div><div style="font-size:.7rem;font-weight:700;color:{clr};margin-bottom:.25rem;">{CORAK_ID[key]}</div><div style="font-size:1.25rem;font-weight:700;">{n:,}</div><div style="font-size:.62rem;opacity:.55;">{pct:.1f}%</div><div style="font-size:.58rem;opacity:.62;line-height:1.35;text-align:left;margin-top:.45rem;">{CORAK_DESKRIPSI[key]}</div></div>', unsafe_allow_html=True)
    _hr()
    st.markdown("### Distribusi & Tren Corak Ilustrasi")
    ca, cb = st.columns(2)
    with ca:
        st.markdown("**Distribusi Corak Keseluruhan**")
        vc = D["corak_ilustrasi"].value_counts()
        labels = [CORAK_ID.get(k, k) for k in vc.index]
        fig = px.bar(x=vc.values, y=labels, orientation="h", color=labels, color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID}, text=vc.values)
        fig.update_layout(**pb(330), showlegend=False, xaxis_title="Jumlah sampul", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    with cb:
        st.markdown("**Tren Corak per Tahun**")
        if "YEAR" in D.columns:
            dyear = D[D["YEAR"] > 0].copy()
            dyear["corak_label"] = dyear["corak_ilustrasi"].map(CORAK_ID)
            tr = dyear.groupby(["YEAR", "corak_label"]).size().reset_index(name="n")
            fig_t = px.bar(tr, x="YEAR", y="n", color="corak_label", barmode="stack", color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID})
            fig_t.update_layout(**pb(330), xaxis_title="", yaxis_title="Jumlah", legend=dict(orientation="h", y=-0.25, font=dict(size=9)))
            st.plotly_chart(fig_t, use_container_width=True)
        else:
            st.info("Kolom YEAR tidak tersedia.")
    _hr()
    st.markdown("### Heatmap Corak Ilustrasi × Genre")
    st.caption("Nilai sel menunjukkan proporsi atau jumlah corak dalam tiap genre. Genre diurutkan berdasarkan klaster K1 → K2 → K3.")
    h1, h2, h3 = st.columns([1, 1, 1])
    with h1:
        n_genre = st.slider("Jumlah genre", 6, 30, 16, 2, key="hm_corak_genre_n")
    with h2:
        min_count = st.slider("Minimum buku per genre", 1, 20, 3, 1, key="hm_corak_min")
    with h3:
        norm_mode = st.selectbox("Mode nilai", ["Persentase", "Jumlah"], key="hm_corak_mode")
    st.plotly_chart(heatmap_corak_genre(D, top_n=n_genre, min_count=min_count, normalize="count" if norm_mode == "Jumlah" else "index"), use_container_width=True)
    _hr()
    st.markdown("### Pemeriksaan Confidence")
    qc1, qc2 = st.columns(2)
    with qc1:
        st.markdown("**Sebaran Confidence per Corak**")
        tmp = D.copy()
        tmp["corak_label"] = tmp["corak_ilustrasi"].map(CORAK_ID)
        fig_box = px.box(tmp, x="corak_label", y="corak_konfiden", color="corak_label", color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID}, points="outliers")
        fig_box.update_layout(**pb(330), showlegend=False, xaxis_title="", yaxis_title="Confidence", xaxis=dict(tickangle=-35))
        st.plotly_chart(fig_box, use_container_width=True)
    with qc2:
        st.markdown("**Jumlah Kasus Ambigu per Corak**")
        amb = D[D["corak_konfiden"] < 0.22]["corak_ilustrasi"].value_counts()
        if amb.empty:
            st.success("Tidak ada kasus di bawah threshold 0.22.")
        else:
            fig_amb = px.bar(x=amb.values, y=[CORAK_ID.get(k, k) for k in amb.index], orientation="h", color=[CORAK_ID.get(k, k) for k in amb.index], color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID}, text=amb.values)
            fig_amb.update_layout(**pb(330), showlegend=False, xaxis_title="Jumlah", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
            fig_amb.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_amb, use_container_width=True)
    _hr()
    st.markdown("### Sampul Confidence Tertinggi per Corak")
    n_top = st.slider("Jumlah sampul per corak", 3, 10, 5, 1, key="top_conf_corak")
    show_probs_top = st.checkbox("Tampilkan skor semua corak", value=False, key="show_probs_top")
    tabs = st.tabs([f"{CORAK_ICON[k]} {CORAK_ID[k]}" for k in CORAK_ORDER])
    for tab, key in zip(tabs, CORAK_ORDER):
        with tab:
            sub = D[D["corak_ilustrasi"] == key].sort_values("corak_konfiden", ascending=False).head(n_top)
            st.markdown(f"**{CORAK_ID[key]}** — {len(D[D['corak_ilustrasi'] == key]):,} sampul")
            st.caption(CORAK_DESKRIPSI[key])
            grid_corak(sub, n_cols=min(5, n_top), cover_dir=cover_dir, show_probs=show_probs_top)
    _hr()
    st.markdown("### Objek Terdeteksi dalam Sampul")
    object_col = _detect_object_col(D)
    if object_col is None:
        st.warning("Kolom objek tidak ditemukan. Cari kolom `objects_detected` pada CSV hasil pipeline.")
    else:
        co, ch = st.columns([1, 2])
        with co:
            obj_count = pd.to_numeric(D.get("objects_count", 0), errors="coerce").fillna(0)
            st.metric("Sampul dengan objek", f"{(obj_count > 0).sum():,}")
            if "has_person" in D.columns:
                st.metric("Mengandung figur manusia", f"{_bool_series(D['has_person']).sum():,}")
        with ch:
            ctr = _parse_objects_detected(D[object_col], terjemahkan=True)
            if ctr:
                top_obj = pd.DataFrame(ctr.most_common(15), columns=["Objek", "Frekuensi"])
                fig_obj = px.bar(top_obj, x="Frekuensi", y="Objek", orientation="h", color="Frekuensi", color_continuous_scale="YlOrRd", text="Frekuensi")
                fig_obj.update_layout(**pb(300), coloraxis_showscale=False, xaxis_title="Frekuensi deteksi", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
                fig_obj.update_traces(textposition="outside", marker_line_width=0)
                st.plotly_chart(fig_obj, use_container_width=True)
        st.markdown("#### Heatmap Objek × Genre")
        hobj1, hobj2 = st.columns(2)
        with hobj1:
            n_obj = st.slider("Jumlah objek", 10, 40, 20, 5, key="hm_obj_n")
        with hobj2:
            n_genre_obj = st.slider("Jumlah genre objek", 8, 30, 16, 2, key="hm_obj_g")
        fig_og = heatmap_objek_genre(D, object_col, top_n_obj=n_obj, top_n_genre=n_genre_obj)
        if fig_og is not None:
            st.plotly_chart(fig_og, use_container_width=True)
        else:
            st.info("Tidak cukup data objek untuk heatmap.")
    _hr()
    if "ILLUSTRATOR" in D.columns:
        st.markdown("### Dengan vs Tanpa Nama Ilustrator")
        has_ill = D["ILLUSTRATOR"].fillna("").astype(str).str.strip().ne("")
        n_ill = int(has_ill.sum())
        n_no = int((~has_ill).sum())
        ci1, ci2, ci3 = st.columns(3)
        ci1.metric("Dengan ilustrator", f"{n_ill:,}")
        ci2.metric("Tanpa ilustrator", f"{n_no:,}")
        ci3.metric("Proporsi dengan ilustrator", f"{n_ill / len(D) * 100:.1f}%" if len(D) else "–")
        if n_ill > 0 and n_no > 0:
            vc_w = D[has_ill]["corak_ilustrasi"].value_counts(normalize=True)
            vc_o = D[~has_ill]["corak_ilustrasi"].value_counts(normalize=True)
            diff = (vc_w - vc_o).dropna().sort_values(ascending=False)
            df_diff = pd.DataFrame({"corak": [CORAK_ID.get(k, k) for k in diff.index], "delta": diff.values})
            fig_diff = px.bar(df_diff, x="delta", y="corak", orientation="h", color="corak", color_discrete_map={CORAK_ID[k]: CORAK_CLR[k] for k in CORAK_ID})
            fig_diff.update_layout(**pb(300), showlegend=False, xaxis_title="Selisih proporsi", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
            fig_diff.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
            st.plotly_chart(fig_diff, use_container_width=True)
            st.caption("Nilai positif = corak lebih sering muncul pada buku dengan nama ilustrator.")
    _hr()
    st.markdown("### Jelajah Sampul berdasarkan Corak")
    genre_counts = _genre_counts(D)
    top_genres = [g for g, c in genre_counts.most_common() if g not in GENRE_EXCLUDE and c >= 3][:40]
    f1, f2, f3, f4 = st.columns([2, 2, 2, 1])
    with f1:
        q = st.text_input("Judul / penulis", key="corak_q")
    with f2:
        corak_sel = st.selectbox("Corak", ["Semua"] + [CORAK_ID[k] for k in CORAK_ORDER], key="corak_sel")
    with f3:
        genre_sel = st.selectbox("Genre", ["Semua"] + top_genres, key="corak_genre_sel")
    with f4:
        n_show = st.slider("Tampilkan", 4, 40, 12, 4, key="corak_n_show")
    f5, f6, f7 = st.columns([1, 1, 1])
    with f5:
        only_person = st.checkbox("Ada figur manusia", key="corak_person")
    with f6:
        min_conf = st.slider("Min. confidence", 0.0, 1.0, 0.0, 0.05, key="corak_min_conf")
    with f7:
        show_probs_search = st.checkbox("Skor semua corak", key="corak_show_probs_search")
    DS = D.copy()
    if q:
        ql = q.lower()
        mask = False
        if "TITLE" in DS.columns:
            mask = DS["TITLE"].astype(str).str.lower().str.contains(ql, na=False)
        if "AUTHOR" in DS.columns:
            mask = mask | DS["AUTHOR"].astype(str).str.lower().str.contains(ql, na=False)
        DS = DS[mask]
    if corak_sel != "Semua":
        rev = {v: k for k, v in CORAK_ID.items()}
        DS = DS[DS["corak_ilustrasi"] == rev.get(corak_sel, corak_sel)]
    if genre_sel != "Semua" and "GENRES" in DS.columns:
        gl = expand_genres(DS["GENRES"], normalize=True)
        DS = DS[[genre_sel in x for x in gl]]
    if only_person and "has_person" in DS.columns:
        DS = DS[_bool_series(DS["has_person"])]
    if min_conf > 0:
        DS = DS[DS["corak_konfiden"] >= min_conf]
    st.markdown(f"**{len(DS):,} buku ditemukan**")
    if not DS.empty:
        grid_corak(DS.sort_values("corak_konfiden", ascending=False).head(n_show), n_cols=4, cover_dir=cover_dir, show_probs=show_probs_search)
