"""
ilustrasi_block.py  ·  v4
Halaman analisis gaya ilustrasi — Kartografi Sampul Sastra Indonesia.
Dipanggil dari app.py:
    from ilustrasi_block import render_ilustrasi
    render_ilustrasi(DF, cover_dir=COVER_DIR)

Perubahan v4:
  - flat_graphic → "Ilustrasi Digital", hand_drawn → "Ilustrasi Manual"
  - Terjemahan label objek YOLO (COCO-80) ke Bahasa Indonesia
  - Normalisasi genre case-insensitive: semua varian Romansa → "Romansa"
  - Heatmap diurutkan K1 → K2 → K3, garis separator antar klaster
  - Heatmap objek × genre dengan nama objek terjemahan
  - Filter pencarian buku: gaya + genre + figur manusia
"""

import base64
import os
from collections import Counter

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ═══════════════════════════════════════════════════════════════════════════════
# TERJEMAHAN LABEL OBJEK YOLO (COCO-80) → BAHASA INDONESIA
# ═══════════════════════════════════════════════════════════════════════════════
YOLO_ID = {
    # Manusia
    "person": "orang",
    # Kendaraan
    "bicycle": "sepeda", "car": "mobil", "motorcycle": "motor",
    "airplane": "pesawat", "bus": "bus", "train": "kereta",
    "truck": "truk", "boat": "perahu",
    # Jalan & rambu
    "traffic light": "lampu lalu lintas", "fire hydrant": "hidran",
    "stop sign": "rambu stop", "parking meter": "meteran parkir",
    "bench": "bangku",
    # Hewan
    "bird": "burung", "cat": "kucing", "dog": "anjing",
    "horse": "kuda", "sheep": "domba", "cow": "sapi",
    "elephant": "gajah", "bear": "beruang", "zebra": "zebra",
    "giraffe": "jerapah",
    # Aksesori
    "backpack": "ransel", "umbrella": "payung", "handbag": "tas tangan",
    "tie": "dasi", "suitcase": "koper",
    # Olahraga
    "frisbee": "frisbee", "skis": "ski", "snowboard": "papan salju",
    "sports ball": "bola olahraga", "kite": "layang-layang",
    "baseball bat": "tongkat baseball", "baseball glove": "sarung tangan baseball",
    "skateboard": "skateboard", "surfboard": "papan selancar",
    "tennis racket": "raket tenis",
    # Dapur & makan
    "bottle": "botol", "wine glass": "gelas anggur", "cup": "cangkir",
    "fork": "garpu", "knife": "pisau", "spoon": "sendok",
    "bowl": "mangkuk",
    # Makanan
    "banana": "pisang", "apple": "apel", "sandwich": "sandwich",
    "orange": "jeruk", "broccoli": "brokoli", "carrot": "wortel",
    "hot dog": "hot dog", "pizza": "pizza", "donut": "donat",
    "cake": "kue",
    # Furnitur & ruangan
    "chair": "kursi", "couch": "sofa", "potted plant": "tanaman pot",
    "bed": "tempat tidur", "dining table": "meja makan",
    "toilet": "toilet", "tv": "televisi", "laptop": "laptop",
    "mouse": "tetikus", "remote": "remote", "keyboard": "keyboard",
    "cell phone": "ponsel",
    # Elektronik & rumah tangga
    "microwave": "microwave", "oven": "oven", "toaster": "pemanggang roti",
    "sink": "wastafel", "refrigerator": "kulkas",
    # Buku & kerja
    "book": "buku", "clock": "jam", "vase": "vas",
    "scissors": "gunting", "teddy bear": "boneka beruang",
    "hair drier": "pengering rambut", "toothbrush": "sikat gigi",
}

def _terjemahkan_objek(label: str) -> str:
    """Terjemahkan label YOLO ke Bahasa Indonesia; kembalikan aslinya jika tidak ada."""
    return YOLO_ID.get(label.strip().lower(), label.strip())


# ═══════════════════════════════════════════════════════════════════════════════
# KONSTANTA GAYA ILUSTRASI
# ═══════════════════════════════════════════════════════════════════════════════
GAYA_ID = {
    "photograph":    "Fotografi",
    "flat_graphic":  "Ilustrasi Digital",
    "hand_drawn":    "Ilustrasi Manual",
    "text_dominant": "Dominan Teks",
    "abstract":      "Abstrak",
    "collage":       "Kolase",
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
GAYA_DESKRIPSI = {
    "photograph":    "Gambar dihasilkan dari rekaman kamera; menyerupai realitas.",
    "flat_graphic":  "Ilustrasi digital vektor bersih tanpa jejak tangan; garis sempurna dan warna solid. Dihasilkan melalui perangkat lunak seperti Illustrator atau Canva.",
    "hand_drawn":    "Ada jejak tangan yang tampak di permukaan: goresan, tekstur kuas atau pensil, ketidaksempurnaan garis yang organik.",
    "text_dominant": "Sampul didominasi elemen tipografi; minim elemen gambar.",
    "abstract":      "Bentuk-bentuk non-figuratif yang tidak merepresentasikan objek nyata secara langsung.",
    "collage":       "Gabungan beberapa elemen visual dari sumber yang berbeda.",
}
GAYA_PROD_MODE = {
    "photograph":    "recording technologies",
    "flat_graphic":  "synthesizing technologies",
    "hand_drawn":    "technologies of the hand",
    "text_dominant": "synthesizing technologies",
    "abstract":      "synthesizing technologies",
    "collage":       "synthesizing technologies",
}
GAYA_PROB_KEYS = ["photograph", "hand_drawn", "abstract", "flat_graphic", "text_dominant"]

# ═══════════════════════════════════════════════════════════════════════════════
# KONSTANTA GENRE
# ═══════════════════════════════════════════════════════════════════════════════
GENRE_EXCLUDE = {
    "Sastra Indonesia", "Sastra", "Fiksi", "Nonfiction", "Non-fiction",
    "Nonfiksi", "Non Fiksi", "Non-fiksi",
}

# Semua varian → bentuk baku; lookup dibuat lowercase agar case-insensitive
_GENRE_NORM_RAW = {
    # Romansa — semua varian
    "Cinta": "Romansa", "Roman": "Romansa",
    "Romansa Kontemporer": "Romansa",
    "Romansa kontemporer": "Romansa",
    "Kontemporer": "Romansa",
    "Romansatic": "Romansa",
    "Young Adult Romansace": "Romansa",
    # Thriller
    "Thriller": "Thriller/Misteri", "Misteri": "Thriller/Misteri",
    "Misteri Thriller": "Thriller/Misteri", "Thriller Suspense": "Thriller/Misteri",
    "Psychological Thriller": "Thriller/Misteri", "Suspense": "Thriller/Misteri",
    "Detective": "Thriller/Misteri", "Kriminal": "Thriller/Misteri",
    # Lainnya
    "Supranatural": "Horor", "Humor": "Komedi",
    "New Adult": "Remaja", "Collections": "Antologi", "Middle Grade": "Fantasi",
    "Fiksi Ilmiah": "Fiksi Sains", "Distopia": "Fiksi Sains",
    "Sejarah": "Fiksi Sejarah", "Historical Fiction": "Fiksi Sejarah",
    "Historical": "Fiksi Sejarah",
}
_GENRE_NORM_LOWER = {k.lower(): v for k, v in _GENRE_NORM_RAW.items()}

# Klaster — Komedi di K3, urutan K1 → K2 → K3
KLASTER_ORDERED = [
    {
        "id": "K1", "color": "#2E4057", "bg": "#EEF2F7",
        "genres": ["Novel", "Cerita Pendek", "Antologi", "Puisi"],
    },
    {
        "id": "K2", "color": "#993556", "bg": "#FBF0F3",
        "genres": ["Romansa", "Chick Lit", "Persahabatan", "Remaja", "Dewasa",
                   "Keluarga", "Drama", "Slice of Life"],
    },
    {
        "id": "K3", "color": "#1D9E75", "bg": "#EEF8F4",
        "genres": ["Fantasi", "Fiksi Sejarah", "Petualangan", "Anak-anak",
                   "Fiksi Sains", "Thriller/Misteri", "Horor", "Komedi"],
    },
]
GENRE_KLASTER_MAP: dict = {}
for _kl in KLASTER_ORDERED:
    for _g in _kl["genres"]:
        GENRE_KLASTER_MAP.setdefault(_g, _kl)

_KLASTER_GENRE_ORDER = [g for kl in KLASTER_ORDERED for g in kl["genres"]]

PIPELINE_IMAGE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "assets", "pipeline_ilustrasi.png"
)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS GENRE
# ═══════════════════════════════════════════════════════════════════════════════
def _norm_genre(g: str) -> str:
    return _GENRE_NORM_LOWER.get(g.strip().lower(), g.strip())


def expand_genres(series, normalize=False):
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
    for gl in expand_genres(d["GENRES"], normalize=True):
        gc.update(gl)
    return gc


def _top_genres_ordered(d: pd.DataFrame, n: int = 16) -> list:
    """Genre diurutkan sesuai klaster (K1 → K2 → K3), sisanya di belakang."""
    gc = _genre_counts(d)
    eligible = {g for g, c in gc.items() if g not in GENRE_EXCLUDE and c >= 3}
    ordered = [g for g in _KLASTER_GENRE_ORDER if g in eligible]
    rest = [g for g, _ in gc.most_common() if g in eligible and g not in ordered]
    return (ordered + rest)[:n]


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
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


def _hr():
    st.markdown(
        "<hr style='border:none;border-top:1px solid rgba(128,128,128,.12);margin:1.3rem 0;'>",
        unsafe_allow_html=True,
    )


def cover_path(img, cover_dir):
    if not img or str(img) in ("", "nan"):
        return None
    p = os.path.join(cover_dir, str(img))
    return p if os.path.exists(p) else None


def palette_html(row, n=5):
    parts, total = [], 0.0
    for i in range(1, n + 1):
        hx = str(row.get(f"warna_hex_{i}", "") or "").strip()
        pct = row.get(f"warna_pct_{i}", 0)
        try:
            pct = float(pct)
        except Exception:
            pct = 0.0
        if not hx or hx in ("nan", ""):
            continue
        if not hx.startswith("#"):
            hx = "#" + hx
        parts.append((hx, pct))
        total += pct
    if not parts:
        return ""
    scale = 100.0 / total if total > 0 else 1.0
    sw = "".join(
        f'<div style="background:{hx};width:{pct*scale:.1f}%;height:100%;"></div>'
        for hx, pct in parts
    )
    return (
        f'<div style="display:flex;height:8px;border-radius:4px;overflow:hidden;'
        f'margin:.35rem 0 .4rem;gap:1px;">{sw}</div>'
    )


def prob_bars_html(probs_dict):
    html = ""
    for key, val in sorted(probs_dict.items(), key=lambda x: -x[1]):
        label = GAYA_ID.get(key, key)
        clr = GAYA_CLR.get(key, "#999")
        pct = val * 100
        html += (
            f'<div style="margin:.1rem 0;">'
            f'<div style="font-size:.6rem;display:flex;justify-content:space-between;'
            f'margin-bottom:1px;opacity:.72;"><span>{label}</span><span>{pct:.1f}%</span></div>'
            f'<div style="background:rgba(128,128,128,.12);border-radius:3px;height:5px;">'
            f'<div style="width:{pct:.1f}%;height:5px;border-radius:3px;background:{clr};"></div>'
            f'</div></div>'
        )
    return html


# ═══════════════════════════════════════════════════════════════════════════════
# KARTU BUKU & GRID
# ═══════════════════════════════════════════════════════════════════════════════
def book_card_gi(row, col_obj, cover_dir, show_probs=False):
    with col_obj:
        cp = cover_path(row.get("IMAGE_FILE"), cover_dir)
        if cp:
            st.image(cp, use_container_width=True)
        else:
            st.markdown(
                '<div style="height:160px;background:rgba(128,128,128,.09);'
                'border-radius:8px 8px 0 0;display:flex;align-items:center;'
                'justify-content:center;font-size:2rem;">📖</div>',
                unsafe_allow_html=True,
            )

        gk = str(row.get("gaya_ilustrasi", "") or "")
        clr = GAYA_CLR.get(gk, "#999")
        try:
            sc = f"{float(row.get('gaya_skor', 0)):.2f}"
        except Exception:
            sc = "–"

        year = (
            int(row["YEAR"])
            if row.get("YEAR", 0) and int(row.get("YEAR", 0)) > 0
            else "–"
        )
        url = row.get("URL", "")
        title = str(row.get("TITLE", "–"))
        title_html = (
            f'<a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">{title}</a>'
            if url else title
        )
        badge = (
            f'<span style="display:inline-block;font-size:.64rem;font-weight:500;'
            f'padding:1px 7px;border-radius:20px;border:1px solid {clr};'
            f'color:{clr};margin:2px 2px 0 0;">'
            f'{GAYA_ICON.get(gk, "")} {GAYA_ID.get(gk, gk)} {sc}</span>'
        ) if gk else ""

        gi_bars = ""
        if show_probs:
            probs = {k: float(row.get(f"gaya_prob_{k}", 0) or 0) for k in GAYA_PROB_KEYS}
            if any(probs.values()):
                gi_bars = f'<div style="margin-top:.4rem;">{prob_bars_html(probs)}</div>'

        st.markdown(
            f'<div style="padding:.55rem .7rem .75rem;">'
            f'<div style="font-family:\'Lora\',serif;font-size:.82rem;font-weight:600;'
            f'line-height:1.3;">{title_html}</div>'
            f'<div style="font-size:.71rem;opacity:.6;margin:.15rem 0 .3rem;">'
            f'{row.get("AUTHOR", "–")} · {year}</div>'
            f'{palette_html(row)}{badge}{gi_bars}</div>',
            unsafe_allow_html=True,
        )


def grid_gi(subset, n_cols=4, cover_dir="", show_probs=False):
    subset = subset.reset_index(drop=True)
    if subset.empty:
        st.info("Tidak ada buku yang cocok dengan filter ini.")
        return
    for start in range(0, len(subset), n_cols):
        chunk = subset.iloc[start:start + n_cols]
        cols = st.columns(n_cols)
        for j, (_, row) in enumerate(chunk.iterrows()):
            book_card_gi(row, cols[j], cover_dir, show_probs=show_probs)


# ═══════════════════════════════════════════════════════════════════════════════
# PARSING OBJEK YOLO — dengan terjemahan otomatis ke Bahasa Indonesia
# ═══════════════════════════════════════════════════════════════════════════════
def _parse_yolo_objects(series, terjemahkan=True) -> Counter:
    """
    Parsing kolom objek YOLO. Format yang didukung:
      "person,car,book"  |  "['person','car']"  |  "{person:2,car:1}"  |  "person:2;car:1"

    Jika terjemahkan=True, label diterjemahkan ke Bahasa Indonesia via YOLO_ID.
    """
    ctr: Counter = Counter()
    for val in series:
        if pd.isna(val) or str(val).strip() in ("", "nan", "[]", "{}"):
            continue
        s = str(val).strip().strip("[]{}\"'")
        items = [x.strip().strip("\"'") for x in s.replace(";", ",").split(",")]
        for item in items:
            if not item:
                continue
            if ":" in item:
                parts = item.split(":", 1)
                raw_label = parts[0].strip().strip("\"'")
                try:
                    count = int(float(parts[1].strip()))
                except Exception:
                    count = 1
            else:
                raw_label = item
                count = 1
            if not raw_label or len(raw_label) <= 1:
                continue
            label = _terjemahkan_objek(raw_label) if terjemahkan else raw_label
            ctr[label] += count
    return ctr


def _detect_yolo_col(df: pd.DataFrame):
    """Deteksi otomatis nama kolom objek YOLO."""
    candidates = [
        "yolo_objek", "yolo_objek_list", "yolo_label_list",
        "yolo_labels", "yolo_objects", "objek_list", "detected_objects",
    ]
    found = next((c for c in candidates if c in df.columns), None)
    if found:
        return found
    # Fallback: kolom yang mengandung kata 'objek' atau 'label'
    auto = [c for c in df.columns if "objek" in c.lower() or "yolo" in c.lower()]
    return auto[0] if auto else None


# ═══════════════════════════════════════════════════════════════════════════════
# HEATMAPS
# ═══════════════════════════════════════════════════════════════════════════════
def _klaster_shapes(genres: list) -> list:
    """Garis putus-putus pemisah antar klaster pada heatmap."""
    shapes, prev_kl = [], None
    for i, g in enumerate(genres):
        kl = GENRE_KLASTER_MAP.get(g, {}).get("id")
        if kl != prev_kl and i > 0:
            shapes.append(dict(
                type="line", xref="paper", yref="y",
                x0=0, x1=1, y0=i - 0.5, y1=i - 0.5,
                line=dict(color="rgba(0,0,0,.3)", width=1.5, dash="dot"),
            ))
        prev_kl = kl
    return shapes


def _make_y_labels(genres: list) -> list:
    return [
        f"{g}  [{GENRE_KLASTER_MAP[g]['id']}]" if g in GENRE_KLASTER_MAP else g
        for g in genres
    ]


def heatmap_gaya_genre(d: pd.DataFrame, top_n=12):
    genres = _top_genres_ordered(d, top_n)
    gaya_keys = list(GAYA_ID.keys())
    gaya_lbls = [GAYA_ID[k] for k in gaya_keys]

    mat = pd.DataFrame(0.0, index=genres, columns=gaya_lbls)
    d2 = d[d["gaya_ilustrasi"].notna()].copy()
    gl_all = expand_genres(d2["GENRES"], normalize=True)

    for g in genres:
        sub = d2[[g in gl for gl in gl_all]]
        if sub.empty:
            continue
        vc = sub["gaya_ilustrasi"].map(GAYA_ID).value_counts(normalize=True)
        for k in gaya_keys:
            mat.loc[g, GAYA_ID[k]] = vc.get(GAYA_ID[k], 0.0)

    y_labels = _make_y_labels(genres)
    text_mat = (mat * 100).round(0).astype(int).astype(str) + "%"

    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=gaya_lbls, y=y_labels,
        colorscale="Greens",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=9, color="#1A1A1A"),
        showscale=True,
    ))
    fig.update_layout(**pb(
        max(340, top_n * 30),
        margin=dict(l=190, r=20, t=32, b=60),
        yaxis=dict(autorange="reversed"),
        shapes=_klaster_shapes(genres),
        xaxis_title="", yaxis_title="",
    ))
    return fig


def heatmap_objek_genre(d: pd.DataFrame, yolo_col: str,
                         top_n_obj=20, top_n_genre=14):
    """
    Heatmap nama objek (terjemahan Indonesia) × genre.
    Nilai sel = % sampul dalam genre tersebut yang mengandung objek itu.
    """
    genres = _top_genres_ordered(d, top_n_genre)
    gl_all = expand_genres(d["GENRES"], normalize=True)

    # Kumpulkan frekuensi objek global (sudah diterjemahkan)
    ctr_global = _parse_yolo_objects(d[yolo_col], terjemahkan=True)
    if not ctr_global:
        return None
    top_objs = [o for o, _ in ctr_global.most_common(top_n_obj)]

    mat = pd.DataFrame(0.0, index=genres, columns=top_objs)
    for g in genres:
        sub = d[[g in gl for gl in gl_all]]
        n_sub = len(sub)
        if n_sub == 0:
            continue
        # Terjemahkan kolom objek untuk subset ini, lalu cek keberadaan per objek
        sub_ctr = _parse_yolo_objects(sub[yolo_col], terjemahkan=True)
        for obj in top_objs:
            # Hitung % sampul yang mengandung objek ini
            has_obj = sub[yolo_col].astype(str).apply(
                lambda val: obj in [
                    _terjemahkan_objek(x.strip().strip("\"'[]{}").split(":")[0].strip())
                    for x in str(val).replace(";", ",").split(",")
                    if x.strip()
                ]
            )
            mat.loc[g, obj] = has_obj.sum() / n_sub

    y_labels = _make_y_labels(genres)
    text_mat = (mat * 100).round(0).astype(int).astype(str) + "%"

    zmax = float(mat.values.max()) if mat.values.max() > 0 else 1.0

    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=top_objs, y=y_labels,
        colorscale="YlOrRd",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=8, color="#1A1A1A"),
        showscale=True, zmin=0, zmax=zmax,
    ))
    fig.update_layout(**pb(
        max(380, top_n_genre * 30),
        margin=dict(l=190, r=20, t=40, b=110),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(tickangle=-40),
        shapes=_klaster_shapes(genres),
        title="% sampul per genre yang mengandung objek",
        xaxis_title="", yaxis_title="",
    ))
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE DIAGRAM
# ═══════════════════════════════════════════════════════════════════════════════
def _pipeline_svg() -> str:
    steps = [
        ("📥", "Masukan",          "Gambar\nsampul buku"),
        ("🔧", "Pra-pemrosesan",   "ubah ukuran · normalisasi\nkoreksi warna"),
        ("🎯", "YOLOv8n",          "Deteksi objek\nCOCO-80 (≥ 0,25)"),
        ("🔍", "DETR ResNet-50",   "Validasi figur\nmanusia (≥ 0,85)"),
        ("🧠", "CLIP ViT-B/32",    "Ekstraksi fitur\nembedding 512 dim"),
        ("🏷️","Pencocokan Gaya",  "6 kandidat gaya\nzero-shot cosine sim"),
        ("✅", "Keluaran",         "Gaya terpilih\n+ skor kemiripan"),
    ]
    clrs = ["#E3F2FD","#FFF3E0","#E8F5E9","#FCE4EC","#F3E5F5","#E0F2F1","#F5F5F5"]
    bw, bh, gap = 128, 74, 20
    tw = len(steps) * bw + (len(steps) - 1) * gap + 40
    th = bh + 90

    parts = []
    for i, (icon, title, desc) in enumerate(steps):
        x = 20 + i * (bw + gap)
        y = 38
        lines = desc.split("\n")
        parts.append(
            f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="8" '
            f'fill="{clrs[i]}" stroke="rgba(0,0,0,.1)" stroke-width="1"/>'
            f'<text x="{x+bw//2}" y="{y+17}" text-anchor="middle" font-size="15">{icon}</text>'
            f'<text x="{x+bw//2}" y="{y+31}" text-anchor="middle" '
            f'font-size="9.5" font-weight="700" fill="#333">{title}</text>'
        )
        for li, line in enumerate(lines):
            parts.append(
                f'<text x="{x+bw//2}" y="{y+45+li*12}" text-anchor="middle" '
                f'font-size="8" fill="#555">{line}</text>'
            )
        if i < len(steps) - 1:
            ax, ay = x + bw + 2, y + bh // 2
            parts.append(
                f'<line x1="{ax}" y1="{ay}" x2="{ax+gap-4}" y2="{ay}" '
                f'stroke="#aaa" stroke-width="1.5" marker-end="url(#arr)"/>'
            )

    body = "\n".join(parts)
    return f"""<svg viewBox="0 0 {tw} {th}" xmlns="http://www.w3.org/2000/svg"
  style="width:100%;border:1px solid rgba(128,128,128,.13);border-radius:12px;
         background:#fafafa;padding:4px;">
  <defs>
    <marker id="arr" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#aaa"/>
    </marker>
  </defs>
  {body}
  <text x="{tw//2}" y="{th-6}" text-anchor="middle"
        font-size="8.5" fill="#bbb" font-style="italic">
    Alur Analisis Ilustrasi · YOLOv8n + DETR ResNet-50 + CLIP ViT-B/32
  </text>
</svg>"""


def _pipeline_from_file(path: str) -> str:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = path.rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext == "png" else f"image/{ext}"
    return (
        f'<div style="border:1px solid rgba(128,128,128,.13);border-radius:12px;overflow:hidden;">'
        f'<img src="data:{mime};base64,{b64}" style="width:100%;display:block;"></div>'
    )


# ═══════════════════════════════════════════════════════════════════════════════
# RENDER UTAMA
# ═══════════════════════════════════════════════════════════════════════════════
def render_ilustrasi(DF: pd.DataFrame, cover_dir: str = ""):
    st.markdown("## Analisis Gaya Ilustrasi")

    # ── 0. Penjelasan model ───────────────────────────────────────────────────
    with st.expander("📖 Cara kerja analisis ilustrasi & model CLIP", expanded=False):
        st.markdown("""
Jika tipografi bekerja pada level karakter dan garis huruf, analisis ilustrasi beroperasi
pada level makna visual yang lebih luas — objek, komposisi, dan gaya produksi gambar
secara keseluruhan. Tiga algoritma bekerja **secara paralel dan saling melengkapi**:

| Algoritma | Peran | Detail |
|---|---|---|
| **CLIP ViT-B/32** | Klasifikasi *gaya* ilustrasi | Zero-shot · 400 juta pasang gambar-teks · cosine similarity |
| **YOLOv8n** | Inventarisasi *objek* | COCO-80 · confidence ≥ 0,25 |
| **DETR ResNet-50** | Validasi *figur manusia* | confidence ≥ 0,85 |

Berbeda dengan penggunaannya dalam analisis tipografi yang berfokus pada pencocokan
karakter huruf terhadap basis data font, **CLIP dalam analisis ilustrasi bekerja pada
skala gambar penuh** (*whole-image level*). Dengan mengajukan deskripsi seperti
*"a book cover with hand-drawn illustration"*, CLIP mengklasifikasikan gaya berdasarkan
kedekatan semantik antara representasi gambar dan teks — bukan karakter per karakter.

> **Akurasi tervalidasi manual:** ~72% (200 sampel acak).
        """)

    # ── 1. Alur pipeline ──────────────────────────────────────────────────────
    st.markdown("### Alur Analisis")
    if os.path.exists(PIPELINE_IMAGE_PATH):
        st.markdown(_pipeline_from_file(PIPELINE_IMAGE_PATH), unsafe_allow_html=True)
    else:
        st.markdown(_pipeline_svg(), unsafe_allow_html=True)
        st.caption(
            "💡 Letakkan gambar alur di `assets/pipeline_ilustrasi.png` "
            "untuk menampilkan diagram asli."
        )

    _hr()

    # ── 2. Kartu enam gaya ────────────────────────────────────────────────────
    st.markdown("### Enam Gaya Ilustrasi")
    st.caption(
        "Berdasarkan tiga mode produksi visual Kress & van Leeuwen (2001): "
        "*technologies of the hand*, *recording technologies*, dan *synthesizing technologies*."
    )
    gcols = st.columns(6)
    for gcol, key in zip(gcols, GAYA_ID):
        clr = GAYA_CLR[key]
        mode = GAYA_PROD_MODE[key]
        with gcol:
            st.markdown(
                f'<div style="border:1px solid rgba(128,128,128,.18);border-radius:10px;'
                f'padding:.6rem .5rem .7rem;text-align:center;height:100%;">'
                f'<div style="font-size:1.6rem;margin-bottom:.25rem;">{GAYA_ICON[key]}</div>'
                f'<div style="font-size:.68rem;font-weight:700;color:{clr};margin-bottom:.3rem;">'
                f'{GAYA_ID[key]}</div>'
                f'<div style="font-size:.59rem;opacity:.6;line-height:1.4;text-align:left;">'
                f'{GAYA_DESKRIPSI[key]}</div>'
                f'<div style="margin-top:.45rem;display:inline-block;font-size:.55rem;'
                f'padding:1px 6px;border-radius:8px;background:rgba(128,128,128,.1);'
                f'color:#666;font-style:italic;">{mode}</div></div>',
                unsafe_allow_html=True,
            )

    _hr()

    # ── 3. Distribusi & tren ──────────────────────────────────────────────────
    st.markdown("### Distribusi & Tren")
    ca, cb = st.columns(2)
    with ca:
        st.markdown("**Distribusi Gaya Keseluruhan**")
        gc = DF["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        if gc.empty:
            st.info("Belum ada data gaya ilustrasi.")
        else:
            fig_d = px.bar(
                x=gc.values, y=gc.index, orientation="h",
                color=gc.index,
                color_discrete_map={GAYA_ID[k]: GAYA_CLR[k] for k in GAYA_ID},
                text=gc.values,
            )
            fig_d.update_layout(**pb(290), showlegend=False, xaxis_title="", yaxis_title="",
                                yaxis=dict(categoryorder="total ascending"))
            fig_d.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_d, use_container_width=True)

    with cb:
        st.markdown("**Tren Gaya per Tahun**")
        dfg = DF[(DF["YEAR"] > 0) & DF["gaya_ilustrasi"].notna()].copy()
        if dfg.empty:
            st.info("Belum ada data tren.")
        else:
            dfg["gaya"] = dfg["gaya_ilustrasi"].map(GAYA_ID)
            trg = dfg.groupby(["YEAR", "gaya"]).size().reset_index(name="n")
            fig_t = px.bar(trg, x="YEAR", y="n", color="gaya", barmode="stack",
                           color_discrete_map={GAYA_ID[k]: GAYA_CLR[k] for k in GAYA_ID})
            fig_t.update_layout(**pb(290), xaxis_title="", yaxis_title="", showlegend=True,
                                legend=dict(orientation="h", y=-.2, font=dict(size=9)))
            st.plotly_chart(fig_t, use_container_width=True)

    _hr()

    # ── 4. Peta panas gaya × genre ────────────────────────────────────────────
    st.markdown("### Peta Panas Gaya × Genre")
    st.caption("Genre diurutkan K1 → K2 → K3. Garis putus-putus memisahkan antar klaster.")
    hn_gi = st.slider("Jumlah genre", 6, 20, 12, 2, key="hn_gi_blk")
    st.plotly_chart(heatmap_gaya_genre(DF, hn_gi), use_container_width=True)

    _hr()

    # ── 5. Contoh sampul per gaya ─────────────────────────────────────────────
    st.markdown("### Contoh Sampul per Gaya")
    tab_labels = [f"{GAYA_ICON[k]} {GAYA_ID[k]}" for k in GAYA_ID]
    tabs = st.tabs(tab_labels)
    for tab, gaya_key in zip(tabs, GAYA_ID):
        with tab:
            df_gaya = DF[
                (DF["gaya_ilustrasi"] == gaya_key) & (DF["image_ok"] == True)
            ].copy()
            col_info, col_ex = st.columns([1, 3])
            with col_info:
                clr = GAYA_CLR[gaya_key]
                st.markdown(
                    f'<div style="border-left:4px solid {clr};padding:.5rem .9rem;'
                    f'border-radius:0 8px 8px 0;background:rgba(128,128,128,.05);">'
                    f'<div style="font-size:2rem;margin-bottom:.3rem;">{GAYA_ICON[gaya_key]}</div>'
                    f'<div style="font-weight:700;color:{clr};margin-bottom:.3rem;">'
                    f'{GAYA_ID[gaya_key]}</div>'
                    f'<div style="font-size:.76rem;line-height:1.5;opacity:.7;">'
                    f'{GAYA_DESKRIPSI[gaya_key]}</div>'
                    f'<div style="margin-top:.5rem;font-size:.68rem;font-style:italic;opacity:.55;">'
                    f'Mode produksi: <strong>{GAYA_PROD_MODE[gaya_key]}</strong></div>'
                    f'<div style="margin-top:.7rem;font-size:.8rem;">'
                    f'<strong>{len(df_gaya):,}</strong> sampul terklasifikasi</div></div>',
                    unsafe_allow_html=True,
                )
            with col_ex:
                if df_gaya.empty:
                    st.info(f"Belum ada sampul {GAYA_ID[gaya_key]}.")
                else:
                    n_ex = st.slider(
                        "Tampilkan", 4, min(16, len(df_gaya)), 8, 4,
                        key=f"ex_{gaya_key}"
                    )
                    sample_df = df_gaya.sample(
                        min(n_ex, len(df_gaya)), random_state=42
                    ).reset_index(drop=True)
                    grid_gi(sample_df, n_cols=4, cover_dir=cover_dir, show_probs=True)

    _hr()

    # ── 6. Analisis objek YOLO ────────────────────────────────────────────────
    st.markdown("### Objek yang Terdeteksi dalam Sampul")
    st.caption(
        "Objek dideteksi oleh YOLOv8n (COCO-80) dan diterjemahkan ke Bahasa Indonesia. "
        "Pilih tab untuk melihat distribusi objek per gaya ilustrasi."
    )
    yolo_col = _detect_yolo_col(DF)

    if yolo_col is None:
        st.warning(
            "Kolom data objek YOLO tidak ditemukan. "
            "Pastikan ada kolom bernama salah satu dari: "
            "`yolo_objek`, `yolo_objek_list`, `yolo_label_list`, atau `detected_objects`."
        )
    else:
        # 6a. Peta panas objek × genre
        st.markdown("#### Peta Panas Objek × Genre")
        st.caption(
            "Nilai = % sampul dalam genre tersebut yang mengandung objek. "
            "Merah tua = objek sangat sering muncul di genre itu."
        )
        c_hm1, c_hm2 = st.columns(2)
        with c_hm1:
            n_obj_hm = st.slider("Jumlah objek ditampilkan", 10, 40, 20, 5, key="n_obj_hm")
        with c_hm2:
            n_genre_hm = st.slider("Jumlah genre", 8, 20, 14, 2, key="n_genre_hm")

        fig_hm = heatmap_objek_genre(DF, yolo_col,
                                      top_n_obj=n_obj_hm, top_n_genre=n_genre_hm)
        if fig_hm is not None:
            st.plotly_chart(fig_hm, use_container_width=True)
        else:
            st.info("Tidak ada data objek untuk membuat peta panas.")

        # 6b. Distribusi objek per gaya — tabs
        st.markdown("#### Distribusi Objek per Gaya Ilustrasi")

        def _render_obj_tab(df_sub: pd.DataFrame, tab_key: str, n_top: int = 25):
            ctr = _parse_yolo_objects(df_sub[yolo_col], terjemahkan=True)
            if not ctr:
                st.info("Tidak ada data objek untuk kategori ini.")
                return

            top_items = ctr.most_common(n_top)
            total_all = sum(ctr.values())
            df_obj = pd.DataFrame(top_items, columns=["Objek", "Frekuensi"])
            df_obj["Persen (%)"] = (df_obj["Frekuensi"] / total_all * 100).round(1)

            co1, co2 = st.columns([2, 1])
            with co1:
                fig_obj = px.bar(
                    df_obj, x="Frekuensi", y="Objek", orientation="h",
                    color="Frekuensi", color_continuous_scale="Greens",
                    text="Frekuensi",
                    hover_data={"Persen (%)": True},
                )
                fig_obj.update_layout(
                    **pb(max(280, len(top_items) * 22)),
                    showlegend=False, coloraxis_showscale=False,
                    xaxis_title="Frekuensi deteksi", yaxis_title="",
                    yaxis=dict(categoryorder="total ascending"),
                )
                fig_obj.update_traces(textposition="outside", marker_line_width=0)
                st.plotly_chart(fig_obj, use_container_width=True)

            with co2:
                st.markdown("**10 objek terbanyak**")
                for obj, freq in top_items[:10]:
                    pct = freq / total_all * 100
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;'
                        f'font-size:.78rem;padding:.18rem 0;border-bottom:1px solid '
                        f'rgba(128,128,128,.09);">'
                        f'<span>{obj}</span>'
                        f'<span style="font-weight:600;color:#43A047;">{pct:.1f}%</span></div>',
                        unsafe_allow_html=True,
                    )

            # Temukan sampul berdasarkan objek
            st.markdown("**Temukan sampul berdasarkan objek**")
            obj_choices = [o for o, _ in top_items[:25]]
            sel_obj = st.selectbox("Pilih objek", obj_choices, key=f"obj_sel_{tab_key}")
            if sel_obj:
                # Cari di kolom asli dengan reverse lookup (Indonesia → Inggris)
                _rev_map = {v: k for k, v in YOLO_ID.items()}
                sel_obj_en = _rev_map.get(sel_obj, sel_obj)
                mask_obj = df_sub[yolo_col].astype(str).str.lower().str.contains(
                    sel_obj_en.lower(), na=False
                ) | df_sub[yolo_col].astype(str).str.lower().str.contains(
                    sel_obj.lower(), na=False
                )
                df_obj_bk = df_sub[mask_obj & (df_sub["image_ok"] == True)]
                st.markdown(f"**{len(df_obj_bk):,}** sampul mengandung objek **{sel_obj}**")
                if not df_obj_bk.empty:
                    n_show = st.slider(
                        "Tampilkan", 4, min(16, len(df_obj_bk)), 8, 4,
                        key=f"obj_n_{tab_key}",
                    )
                    grid_gi(df_obj_bk.head(n_show), n_cols=4, cover_dir=cover_dir)

        obj_tab_labels = ["🌐 Semua Gaya"] + [
            f"{GAYA_ICON[k]} {GAYA_ID[k]}" for k in GAYA_ID
        ]
        obj_tabs = st.tabs(obj_tab_labels)

        with obj_tabs[0]:
            n_top_all = st.slider("Jumlah objek", 10, 40, 25, 5, key="n_top_obj_all")
            _render_obj_tab(DF, "all", n_top=n_top_all)

        for tab_o, gaya_key in zip(obj_tabs[1:], GAYA_ID):
            with tab_o:
                df_g = DF[DF["gaya_ilustrasi"] == gaya_key]
                if df_g.empty:
                    st.info(f"Tidak ada sampul {GAYA_ID[gaya_key]}.")
                else:
                    n_top_g = st.slider(
                        "Jumlah objek", 10, 30, 15, 5, key=f"n_top_obj_{gaya_key}"
                    )
                    _render_obj_tab(df_g, gaya_key, n_top=n_top_g)

    _hr()

    # ── 7. Figur manusia ──────────────────────────────────────────────────────
    st.markdown("### Figur Manusia vs Non-Manusia")
    yh = int(DF["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
    dh = int(DF["detr_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
    tot = len(DF)
    agree = int((
        DF["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") &
        DF["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")
    ).sum())

    man_a, man_b = st.columns([2, 1])
    with man_a:
        fig_man = go.Figure(data=[
            go.Bar(name="YOLOv8n", x=["Ada manusia", "Tidak ada"],
                   y=[yh, tot - yh], marker_color=["#66BB6A", "rgba(128,128,128,.15)"]),
            go.Bar(name="DETR", x=["Ada manusia", "Tidak ada"],
                   y=[dh, tot - dh], marker_color=["#42A5F5", "rgba(128,128,128,.08)"]),
        ])
        fig_man.update_layout(**pb(240), barmode="group", showlegend=True,
                              legend=dict(orientation="h", y=-.15))
        st.plotly_chart(fig_man, use_container_width=True)
    with man_b:
        st.metric("Sepakat keduanya", f"{agree:,}", f"{agree/tot*100:.1f}%")
        st.metric("Hanya YOLOv8n", f"{yh - agree:,}")
        st.metric("Hanya DETR", f"{dh - agree:,}")

    st.markdown("**Kehadiran figur manusia per gaya**")
    rows_man = []
    for gk in GAYA_ID:
        sub = DF[DF["gaya_ilustrasi"] == gk]
        if sub.empty:
            continue
        py = sub["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE").mean() * 100
        pd_ = sub["detr_ada_manusia"].astype(str).str.upper().eq("TRUE").mean() * 100
        rows_man.append({"Gaya": GAYA_ID[gk], "YOLOv8n": round(py, 1), "DETR": round(pd_, 1)})
    if rows_man:
        df_mg = pd.DataFrame(rows_man)
        fig_mg = go.Figure([
            go.Bar(name="YOLOv8n", x=df_mg["Gaya"], y=df_mg["YOLOv8n"],
                   marker_color="#66BB6A"),
            go.Bar(name="DETR", x=df_mg["Gaya"], y=df_mg["DETR"],
                   marker_color="#42A5F5"),
        ])
        fig_mg.update_layout(**pb(260), barmode="group",
                             yaxis_title="% sampul dengan figur manusia",
                             xaxis_title="",
                             legend=dict(orientation="h", y=-.15))
        st.plotly_chart(fig_mg, use_container_width=True)

    _hr()

    # ── 8. Simpangan illustrator ──────────────────────────────────────────────
    st.markdown("### Sampul Dengan vs Tanpa Nama Ilustrator")
    has_ill = DF["ILLUSTRATOR"].ne("")
    n_ill = has_ill.sum()
    n_no_ill = (~has_ill).sum()
    if n_ill > 0 and n_no_ill > 0:
        gc_w = DF[has_ill]["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        gc_o = DF[~has_ill]["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        diff_g = (gc_w / n_ill - gc_o / n_no_ill).dropna().sort_values(ascending=False)
        dg_df = diff_g.reset_index()
        dg_df.columns = ["gaya", "delta"]
        fig_dg = px.bar(dg_df, x="delta", y="gaya", orientation="h",
                        color="gaya",
                        color_discrete_map={GAYA_ID[k]: GAYA_CLR[k] for k in GAYA_ID})
        fig_dg.update_layout(**pb(240), showlegend=False,
                             xaxis_title="Selisih proporsi", yaxis_title="",
                             yaxis=dict(categoryorder="total ascending"))
        fig_dg.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
        st.plotly_chart(fig_dg, use_container_width=True)
        st.caption("Nilai positif = gaya lebih sering muncul pada buku **dengan** nama ilustrator.")

    _hr()

    # ── 9. Pencarian buku ─────────────────────────────────────────────────────
    st.markdown("### Cari Buku berdasarkan Gaya Ilustrasi")
    gc_all = _genre_counts(DF)
    top_genres_list = [
        g for g, _ in gc_all.most_common()
        if g not in GENRE_EXCLUDE and gc_all[g] >= 3
    ][:30]

    r1c1, r1c2, r1c3 = st.columns([2, 2, 1])
    r2c1, r2c2, r2c3 = st.columns([2, 2, 1])

    with r1c1:
        q_gi = st.text_input("Judul / penulis", key="gi_q_blk")
    with r1c2:
        gaya_sel = st.selectbox(
            "Gaya ilustrasi",
            ["Semua"] + [GAYA_ID[k] for k in GAYA_ID],
            key="gi_sel_blk",
        )
    with r1c3:
        ada_man = st.checkbox("Ada figur manusia", key="gi_man_blk")
    with r2c1:
        genre_sel = st.selectbox(
            "Genre",
            ["Semua"] + top_genres_list,
            key="gi_genre_blk",
        )
    with r2c2:
        show_probs_s = st.checkbox("Tampilkan skor probabilitas", key="gi_probs_blk")
    with r2c3:
        n_gi2 = st.slider("Tampilkan", 4, 32, 8, 4, key="gi_n_blk")

    dgi = DF[DF["image_ok"] == True].copy()

    if q_gi:
        ql = q_gi.lower()
        dgi = dgi[
            dgi["TITLE"].str.lower().str.contains(ql, na=False) |
            dgi["AUTHOR"].str.lower().str.contains(ql, na=False)
        ]
    if gaya_sel != "Semua":
        grev = {v: k for k, v in GAYA_ID.items()}
        dgi = dgi[dgi["gaya_ilustrasi"] == grev.get(gaya_sel, gaya_sel)]
    if genre_sel != "Semua":
        gl_s = expand_genres(dgi["GENRES"], normalize=True)
        dgi = dgi[[genre_sel in gl for gl in gl_s]]
    if ada_man:
        dgi = dgi[
            dgi["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") |
            dgi["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")
        ]

    st.markdown(f"**{len(dgi):,} buku ditemukan**")
    if not dgi.empty:
        grid_gi(dgi.head(n_gi2), n_cols=4, cover_dir=cover_dir, show_probs=show_probs_s)
