"""
ilustrasi_block.py
Halaman analisis gaya ilustrasi untuk Kartografi Sampul Sastra Indonesia.
Dipanggil dari app.py via: from ilustrasi_block import render_ilustrasi
"""

import base64
import os
from collections import Counter

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Konstanta (harus sinkron dengan app.py) ───────────────────────────────────
GAYA_ID = {
    "photograph":    "Fotografi",
    "flat_graphic":  "Ilustrasi Datar",
    "hand_drawn":    "Gambar Tangan",
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
    "flat_graphic":  "Ilustrasi digital vektor bersih tanpa tekstur tangan; garis sempurna.",
    "hand_drawn":    "Ada jejak tangan: goresan, tekstur kuas/pensil, ketidaksempurnaan garis.",
    "text_dominant": "Sampul didominasi elemen tipografi, minim elemen gambar.",
    "abstract":      "Bentuk-bentuk non-figuratif; tidak merepresentasikan objek nyata secara langsung.",
    "collage":       "Gabungan beberapa elemen visual dari sumber berbeda.",
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

WARNA_HEX = {
    "putih": "#F5F5F0", "hitam": "#1A1A1A", "abu":    "#8E8E93",
    "merah": "#E53935", "pink":  "#F06292", "oranye": "#FB8C00",
    "cokelat": "#795548", "kuning": "#FDD835", "hijau":  "#43A047",
    "biru":  "#1E88E5", "ungu":  "#8E24AA",
}
WARNA_ORDER = ["putih","oranye","cokelat","biru","merah","pink",
               "hitam","kuning","ungu","hijau","abu"]

GENRE_EXCLUDE = {
    "Sastra Indonesia","Sastra","Fiksi","Nonfiction","Non-fiction",
    "Nonfiksi","Non Fiksi","Non-fiksi"
}
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

# ── Klaster (Komedi masuk Klaster 3) ─────────────────────────────────────────
KLASTER_COOC = [
    {
        "id": "K1", "color": "#2E4057", "bg": "#EEF2F7",
        "genres": ["Novel","Cerita Pendek","Antologi","Puisi"],
    },
    {
        "id": "K2", "color": "#993556", "bg": "#FBF0F3",
        "genres": ["Romansa","Chick Lit","Persahabatan","Remaja","Dewasa",
                   "Keluarga","Drama","Slice of Life"],
    },
    {
        "id": "K3", "color": "#1D9E75", "bg": "#EEF8F4",
        "genres": ["Fantasi","Fiksi Sejarah","Petualangan","Anak-anak",
                   "Fiksi Sains","Thriller/Misteri","Horor","Komedi"],
    },
]
GENRE_KLASTER_MAP = {}
for _kl in KLASTER_COOC:
    for _g in _kl["genres"]:
        if _g not in GENRE_KLASTER_MAP:
            GENRE_KLASTER_MAP[_g] = _kl


# ── Pipeline diagram (SVG inline) ─────────────────────────────────────────────
PIPELINE_IMAGE_PATH = os.path.join(
    os.path.dirname(__file__), "assets", "pipeline_ilustrasi.png"
)


def _pipeline_html(img_path: str) -> str:
    """Embed gambar pipeline sebagai base64 agar bisa tampil di Streamlit cloud."""
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = img_path.rsplit(".", 1)[-1].lower()
        mime = "image/png" if ext == "png" else f"image/{ext}"
        return (
            f'<div style="border:1px solid rgba(128,128,128,.15);border-radius:12px;'
            f'overflow:hidden;margin:.5rem 0;">'
            f'<img src="data:{mime};base64,{b64}" style="width:100%;display:block;">'
            f"</div>"
        )
    # Fallback: teks diagram jika file tidak ada
    return _pipeline_svg_fallback()


def _pipeline_svg_fallback() -> str:
    """SVG sederhana sebagai fallback jika file gambar pipeline tidak tersedia."""
    steps = [
        ("📥", "Input", "Sampul buku\n(gambar)"),
        ("🔧", "Preprocessing", "resize · normalize\ncolor correction"),
        ("🎯", "YOLOv8n", "Deteksi objek\nCOCO-80 (≥0.25)"),
        ("🔍", "DETR ResNet-50", "Validasi\nfigur manusia (≥0.85)"),
        ("🧠", "CLIP ViT-B/32", "Ekstraksi fitur\n512-dim embedding"),
        ("🏷️", "Klasifikasi Gaya", "6 kandidat gaya\nzero-shot matching"),
        ("✅", "Output", "Gaya terpilih\n+ skor similarity"),
    ]
    clrs = ["#E3F2FD","#F3E5F5","#FFF3E0","#E8F5E9","#FCE4EC","#E0F2F1","#F5F5F5"]
    box_w, box_h, gap = 130, 70, 18
    total_w = len(steps) * box_w + (len(steps)-1) * gap + 40
    total_h = box_h + 80

    rects = ""
    for i,(icon,title,desc) in enumerate(steps):
        x = 20 + i*(box_w+gap)
        y = 40
        lines = desc.split("\n")
        rects += (
            f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="8" '
            f'fill="{clrs[i]}" stroke="rgba(0,0,0,.1)" stroke-width="1"/>'
            f'<text x="{x+box_w//2}" y="{y+16}" text-anchor="middle" '
            f'font-size="16">{icon}</text>'
            f'<text x="{x+box_w//2}" y="{y+32}" text-anchor="middle" '
            f'font-size="10" font-weight="600" fill="#333">{title}</text>'
        )
        for li, line in enumerate(lines):
            rects += (
                f'<text x="{x+box_w//2}" y="{y+45+li*12}" text-anchor="middle" '
                f'font-size="8.5" fill="#555">{line}</text>'
            )
        if i < len(steps)-1:
            ax = x + box_w + 2
            ay = y + box_h//2
            rects += (
                f'<line x1="{ax}" y1="{ay}" x2="{ax+gap-4}" y2="{ay}" '
                f'stroke="#999" stroke-width="1.5" marker-end="url(#arr)"/>'
            )

    svg = f"""<svg viewBox="0 0 {total_w} {total_h}" xmlns="http://www.w3.org/2000/svg"
    style="width:100%;border:1px solid rgba(128,128,128,.15);border-radius:12px;padding:4px;background:#fafafa;">
  <defs>
    <marker id="arr" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#999"/>
    </marker>
  </defs>
  {rects}
  <text x="{total_w//2}" y="{total_h-6}" text-anchor="middle"
    font-size="9" fill="#aaa" font-style="italic">
    Pipeline Analisis Gaya Ilustrasi · YOLOv8n + DETR ResNet-50 + CLIP ViT-B/32
  </text>
</svg>"""
    return svg


# ── Helpers ───────────────────────────────────────────────────────────────────
def _norm_genre(g: str) -> str:
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
                        normed.append(g2)
                        seen.add(g2)
                out.append(normed)
            else:
                out.append(raw)
    return out


def _top_genres(d, n=16):
    gc = Counter()
    for gl in expand_genres(d["GENRES"], normalize=True):
        gc.update(gl)
    return [g for g, _ in gc.most_common()
            if g not in GENRE_EXCLUDE and gc[g] >= 3][:n]


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


def cover_path(img, cover_dir):
    if not img or str(img) in ("", "nan"):
        return None
    p = os.path.join(cover_dir, str(img))
    return p if os.path.exists(p) else None


def palette_html(row, n=5):
    parts, total = [], 0.0
    for i in range(1, n+1):
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


def prob_bars(probs_dict):
    html = ""
    for key, val in sorted(probs_dict.items(), key=lambda x: -x[1]):
        label = GAYA_ID.get(key, key)
        clr = GAYA_CLR.get(key, "#999")
        pct = val * 100
        html += (
            f'<div style="margin:.1rem 0;">'
            f'<div style="font-size:.6rem;display:flex;justify-content:space-between;'
            f'margin-bottom:1px;opacity:.72;">'
            f'<span>{label}</span><span>{pct:.1f}%</span></div>'
            f'<div style="background:rgba(128,128,128,.12);border-radius:3px;height:5px;">'
            f'<div style="width:{pct:.1f}%;height:5px;border-radius:3px;'
            f'background:{clr};"></div></div></div>'
        )
    return html


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

        year = int(row["YEAR"]) if row.get("YEAR", 0) and int(row.get("YEAR", 0)) > 0 else "–"
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
            f'{GAYA_ICON.get(gk,"")} {GAYA_ID.get(gk,gk)} {sc}</span>'
        ) if gk else ""

        gi_bars = ""
        if show_probs:
            probs = {k: float(row.get(f"gaya_prob_{k}", 0) or 0) for k in GAYA_PROB_KEYS}
            if any(probs.values()):
                gi_bars = (
                    f'<div style="margin-top:.4rem;">{prob_bars(probs)}</div>'
                )

        st.markdown(
            f'<div style="padding:.55rem .7rem .75rem;">'
            f'<div style="font-family:\'Lora\',serif;font-size:.82rem;font-weight:600;'
            f'line-height:1.3;">{title_html}</div>'
            f'<div style="font-size:.71rem;opacity:.6;margin:.15rem 0 .3rem;">'
            f'{row.get("AUTHOR","–")} · {year}</div>'
            f'{palette_html(row)}{badge}{gi_bars}</div>',
            unsafe_allow_html=True,
        )


def grid_gi(subset, n_cols=4, cover_dir="", show_probs=False):
    subset = subset.reset_index(drop=True)
    if subset.empty:
        st.info("Tidak ada buku yang cocok dengan filter ini.")
        return
    for start in range(0, len(subset), n_cols):
        chunk = subset.iloc[start:start+n_cols]
        cols = st.columns(n_cols)
        for j, (_, row) in enumerate(chunk.iterrows()):
            book_card_gi(row, cols[j], cover_dir, show_probs=show_probs)


def heatmap_gaya_genre(d, top_n=12):
    genres = _top_genres(d, top_n)
    gaya_keys = list(GAYA_ID.keys())
    gaya_labels = [GAYA_ID[k] for k in gaya_keys]
    mat = pd.DataFrame(0.0, index=genres, columns=gaya_labels)
    d2 = d[d["gaya_ilustrasi"].notna()].copy()
    genre_lists = expand_genres(d2["GENRES"], normalize=True)
    for g in genres:
        mask = [g in gl for gl in genre_lists]
        sub = d2[mask]
        if len(sub) == 0:
            continue
        vc = sub["gaya_ilustrasi"].map(GAYA_ID).value_counts(normalize=True)
        for k in gaya_keys:
            mat.loc[g, GAYA_ID[k]] = vc.get(GAYA_ID[k], 0.0)

    y_labels = []
    for g in genres:
        kl = GENRE_KLASTER_MAP.get(g)
        y_labels.append(f"{g}  [{kl['id']}]" if kl else g)

    text_mat = (mat * 100).round(0).astype(int).astype(str) + "%"
    fig = go.Figure(data=go.Heatmap(
        z=mat.values, x=gaya_labels, y=y_labels,
        colorscale="Greens",
        text=text_mat.values, texttemplate="%{text}",
        textfont=dict(size=9, color="#1A1A1A"),
        showscale=True,
    ))
    fig.update_layout(**pb(
        max(340, top_n * 28),
        margin=dict(l=180, r=20, t=32, b=60),
        yaxis=dict(autorange="reversed"),
        xaxis_title="", yaxis_title="",
    ))
    return fig


def _parse_yolo_objects(series) -> Counter:
    """
    Parsing kolom yolo_objek_list atau yolo_label_list.
    Mendukung format: "person,car,book" atau "['person','car']" atau "{person:2, car:1}".
    """
    ctr = Counter()
    for val in series:
        if pd.isna(val) or str(val).strip() in ("", "nan", "[]", "{}"):
            continue
        s = str(val).strip()
        # hapus bracket/brace
        s = s.strip("[]{}\"'")
        # split by koma atau titik koma
        items = [x.strip().strip("\"'") for x in s.replace(";", ",").split(",")]
        for item in items:
            if not item:
                continue
            # format "label:count"
            if ":" in item:
                parts = item.split(":")
                label = parts[0].strip().strip("\"'")
                try:
                    count = int(parts[1].strip())
                except Exception:
                    count = 1
            else:
                label = item
                count = 1
            if label and len(label) > 1:
                ctr[label] += count
    return ctr


# ═════════════════════════════════════════════════════════════════════════════
# RENDER UTAMA
# ═════════════════════════════════════════════════════════════════════════════
def render_ilustrasi(DF: pd.DataFrame, cover_dir: str = ""):
    """
    Fungsi utama yang dipanggil dari app.py.
    DF   : DataFrame yang sudah difilter tahun.
    cover_dir : path ke folder gambar sampul.
    """
    st.markdown("## Analisis Gaya Ilustrasi")

    # ── 0. Penjelasan CLIP ────────────────────────────────────────────────────
    with st.expander("📖 Cara kerja analisis ilustrasi & model CLIP", expanded=False):
        st.markdown("""
Jika tipografi bekerja pada level karakter dan garis huruf, analisis ilustrasi beroperasi
pada level makna visual yang lebih luas — objek, komposisi, dan gaya produksi gambar secara
keseluruhan. Tiga algoritma bekerja **secara paralel dan saling melengkapi**:

| Algoritma | Peran | Detail |
|---|---|---|
| **CLIP ViT-B/32** | Klasifikasi *gaya* ilustrasi | Zero-shot · 400 juta pasang gambar-teks · cosine similarity |
| **YOLOv8n** | Inventarisasi *objek* | COCO-80 · confidence ≥ 0.25 |
| **DETR ResNet-50** | Validasi *figur manusia* | confidence ≥ 0.85 |

Berbeda dengan penggunaannya dalam analisis tipografi yang berfokus pada pencocokan
karakter huruf terhadap database font, **CLIP dalam analisis ilustrasi bekerja pada
skala gambar penuh** (*whole-image level*). Dengan mengajukan deskripsi tekstual seperti
*"a book cover with hand-drawn illustration"* atau *"a book cover with flat graphic design"*,
CLIP mengklasifikasikan gaya berdasarkan kedekatan semantik antara representasi gambar
dan teks deskripsi tersebut.

> **Akurasi tervalidasi manual:** ~72% (200 sampel acak).
        """)

    # ── 1. Pipeline diagram ───────────────────────────────────────────────────
    st.markdown("### Pipeline Analisis")
    svg_or_html = _pipeline_svg_fallback()
    if os.path.exists(PIPELINE_IMAGE_PATH):
        svg_or_html = _pipeline_html(PIPELINE_IMAGE_PATH)
        st.markdown(svg_or_html, unsafe_allow_html=True)
    else:
        st.markdown(svg_or_html, unsafe_allow_html=True)
        st.caption(
            "💡 Untuk menampilkan diagram pipeline asli, letakkan file gambar di "
            "`assets/pipeline_ilustrasi.png`"
        )

    st.markdown("<hr style='border:none;border-top:1px solid rgba(128,128,128,.12);margin:1.3rem 0;'>",
                unsafe_allow_html=True)

    # ── 2. Kartu gaya ilustrasi ───────────────────────────────────────────────
    st.markdown("### Enam Gaya Ilustrasi")
    st.caption("Berdasarkan tiga mode produksi visual Kress & van Leeuwen (2001).")
    gcols = st.columns(6)
    for gcol, key in zip(gcols, GAYA_ID):
        clr = GAYA_CLR[key]
        mode = GAYA_PROD_MODE[key]
        with gcol:
            st.markdown(
                f'<div style="border:1px solid rgba(128,128,128,.18);border-radius:10px;'
                f'padding:.6rem .5rem .65rem;text-align:center;height:100%;">'
                f'<div style="font-size:1.6rem;margin-bottom:.25rem;">{GAYA_ICON[key]}</div>'
                f'<div style="font-size:.68rem;font-weight:700;color:{clr};margin-bottom:.2rem;">'
                f'{GAYA_ID[key]}</div>'
                f'<div style="font-size:.6rem;opacity:.55;line-height:1.35;text-align:left;">'
                f'{GAYA_DESKRIPSI[key]}</div>'
                f'<div style="margin-top:.4rem;display:inline-block;font-size:.56rem;'
                f'padding:1px 6px;border-radius:8px;background:rgba(128,128,128,.1);'
                f'color:#666;font-style:italic;">{mode}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<hr style='border:none;border-top:1px solid rgba(128,128,128,.12);margin:1.3rem 0;'>",
                unsafe_allow_html=True)

    # ── 3. Distribusi & tren ──────────────────────────────────────────────────
    st.markdown("### Distribusi & Tren")
    ca, cb = st.columns(2)
    with ca:
        st.markdown("**Distribusi Gaya Keseluruhan**")
        gc = DF["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        if gc.empty:
            st.info("Belum ada data gaya ilustrasi.")
        else:
            fig_dist = px.bar(
                x=gc.values, y=gc.index, orientation="h",
                color=gc.index,
                color_discrete_map={GAYA_ID[k]: GAYA_CLR[k] for k in GAYA_ID},
                text=gc.values,
            )
            fig_dist.update_layout(
                **pb(290), showlegend=False,
                xaxis_title="", yaxis_title="",
                yaxis=dict(categoryorder="total ascending"),
            )
            fig_dist.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_dist, use_container_width=True)

    with cb:
        st.markdown("**Tren Gaya per Tahun**")
        dfg = DF[(DF["YEAR"] > 0) & DF["gaya_ilustrasi"].notna()].copy()
        if dfg.empty:
            st.info("Belum ada data tren.")
        else:
            dfg["gaya"] = dfg["gaya_ilustrasi"].map(GAYA_ID)
            trg = dfg.groupby(["YEAR", "gaya"]).size().reset_index(name="n")
            fig_tren = px.bar(
                trg, x="YEAR", y="n", color="gaya", barmode="stack",
                color_discrete_map={GAYA_ID[k]: GAYA_CLR[k] for k in GAYA_ID},
            )
            fig_tren.update_layout(
                **pb(290), xaxis_title="", yaxis_title="", showlegend=True,
                legend=dict(orientation="h", y=-.2, font=dict(size=9)),
            )
            st.plotly_chart(fig_tren, use_container_width=True)

    st.markdown("<hr style='border:none;border-top:1px solid rgba(128,128,128,.12);margin:1.3rem 0;'>",
                unsafe_allow_html=True)

    # ── 4. Peta panas gaya × genre ────────────────────────────────────────────
    st.markdown("### Peta Panas Gaya × Genre")
    hn_gi = st.slider("Jumlah genre", 6, 20, 12, 2, key="hn_gi_blk")
    st.plotly_chart(heatmap_gaya_genre(DF, hn_gi), use_container_width=True)

    st.markdown("<hr style='border:none;border-top:1px solid rgba(128,128,128,.12);margin:1.3rem 0;'>",
                unsafe_allow_html=True)

    # ── 5. Contoh sampul per gaya ─────────────────────────────────────────────
    st.markdown("### Contoh Sampul per Gaya Ilustrasi")
    st.caption("Sampul diambil acak dari masing-masing kategori gaya.")

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
                    st.info(f"Belum ada sampul terklasifikasi sebagai {GAYA_ID[gaya_key]}.")
                else:
                    n_show_ex = st.slider(
                        "Tampilkan", 4, min(16, len(df_gaya)), 8, 4,
                        key=f"ex_{gaya_key}"
                    )
                    sample_df = df_gaya.sample(
                        min(n_show_ex, len(df_gaya)), random_state=42
                    ).reset_index(drop=True)
                    grid_gi(sample_df, n_cols=4, cover_dir=cover_dir, show_probs=True)

    st.markdown("<hr style='border:none;border-top:1px solid rgba(128,128,128,.12);margin:1.3rem 0;'>",
                unsafe_allow_html=True)

    # ── 6. Analisis objek (YOLO) ──────────────────────────────────────────────
    st.markdown("### Objek yang Terdeteksi dalam Sampul")
    st.caption(
        "Objek dideteksi oleh YOLOv8n (COCO-80). "
        "Pilih gaya ilustrasi untuk melihat distribusi objek spesifiknya."
    )

    # Cari kolom objek YOLO yang tersedia
    YOLO_COL_CANDIDATES = [
        "yolo_objek_list", "yolo_label_list", "yolo_labels",
        "yolo_objects", "objek_list", "detected_objects",
    ]
    yolo_col = next((c for c in YOLO_COL_CANDIDATES if c in DF.columns), None)

    if yolo_col is None:
        # Coba deteksi otomatis: kolom yang mengandung kata 'objek' atau 'label'
        candidates = [c for c in DF.columns if "objek" in c.lower() or "label" in c.lower()]
        if candidates:
            yolo_col = candidates[0]

    obj_tab_labels = ["🌐 Semua Gaya"] + [
        f"{GAYA_ICON[k]} {GAYA_ID[k]}" for k in GAYA_ID
    ]
    obj_tabs = st.tabs(obj_tab_labels)

    def _render_obj_tab(df_sub, tab_key, n_top=25):
        if yolo_col is None:
            st.warning(
                "Kolom data objek YOLO tidak ditemukan. "
                "Pastikan kolom bernama salah satu dari: "
                + ", ".join(YOLO_COL_CANDIDATES)
            )
            # Fallback: gunakan yolo_n_objek jika ada
            if "yolo_n_objek" in df_sub.columns:
                st.markdown("**Distribusi jumlah objek per sampul (fallback)**")
                n_obj = df_sub["yolo_n_objek"].dropna()
                fig_n = px.histogram(
                    n_obj, nbins=20,
                    color_discrete_sequence=["#43A047"],
                    labels={"value": "Jumlah objek", "count": "Frekuensi"},
                )
                fig_n.update_layout(**pb(220), showlegend=False)
                st.plotly_chart(fig_n, use_container_width=True)
            return

        ctr = _parse_yolo_objects(df_sub[yolo_col])
        if not ctr:
            st.info("Tidak ada data objek untuk kategori ini.")
            return

        top_items = ctr.most_common(n_top)
        df_obj = pd.DataFrame(top_items, columns=["Objek", "Frekuensi"])

        co1, co2 = st.columns([2, 1])
        with co1:
            fig_obj = px.bar(
                df_obj, x="Frekuensi", y="Objek", orientation="h",
                color="Frekuensi",
                color_continuous_scale="Greens",
                text="Frekuensi",
            )
            fig_obj.update_layout(
                **pb(max(260, len(top_items)*22)),
                showlegend=False, coloraxis_showscale=False,
                xaxis_title="Frekuensi deteksi", yaxis_title="",
                yaxis=dict(categoryorder="total ascending"),
            )
            fig_obj.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_obj, use_container_width=True)

        with co2:
            st.markdown("**Top 10 objek**")
            for obj, freq in top_items[:10]:
                pct = freq / sum(ctr.values()) * 100
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;'
                    f'font-size:.78rem;padding:.15rem 0;border-bottom:1px solid '
                    f'rgba(128,128,128,.08);">'
                    f'<span>{obj}</span>'
                    f'<span style="font-weight:600;color:#43A047;">{pct:.1f}%</span></div>',
                    unsafe_allow_html=True,
                )

        # Buku yang mengandung objek tertentu
        st.markdown("**Cari buku berdasarkan objek yang terdeteksi**")
        if top_items:
            top_obj_names = [o for o, _ in top_items[:20]]
            sel_obj = st.selectbox(
                "Pilih objek", top_obj_names, key=f"obj_sel_{tab_key}"
            )
            if sel_obj and yolo_col in df_sub.columns:
                mask_obj = df_sub[yolo_col].astype(str).str.lower().str.contains(
                    sel_obj.lower(), na=False
                )
                df_obj_books = df_sub[mask_obj & (df_sub["image_ok"] == True)]
                st.markdown(f"**{len(df_obj_books):,}** sampul mengandung objek *{sel_obj}*")
                if not df_obj_books.empty:
                    n_obj_show = st.slider(
                        "Tampilkan", 4, min(16, len(df_obj_books)), 8, 4,
                        key=f"obj_n_{tab_key}"
                    )
                    grid_gi(
                        df_obj_books.head(n_obj_show),
                        n_cols=4, cover_dir=cover_dir,
                    )

    # Tab semua gaya
    with obj_tabs[0]:
        n_top_all = st.slider("Top N objek", 10, 40, 25, 5, key="n_top_obj_all")
        _render_obj_tab(DF, "all", n_top=n_top_all)

    # Tab per gaya
    for tab_o, gaya_key in zip(obj_tabs[1:], GAYA_ID):
        with tab_o:
            df_g = DF[DF["gaya_ilustrasi"] == gaya_key]
            if df_g.empty:
                st.info(f"Tidak ada sampul terklasifikasi sebagai {GAYA_ID[gaya_key]}.")
            else:
                n_top_g = st.slider("Top N objek", 10, 30, 15, 5, key=f"n_top_obj_{gaya_key}")
                _render_obj_tab(df_g, gaya_key, n_top=n_top_g)

    st.markdown("<hr style='border:none;border-top:1px solid rgba(128,128,128,.12);margin:1.3rem 0;'>",
                unsafe_allow_html=True)

    # ── 7. Figur manusia ─────────────────────────────────────────────────────
    st.markdown("### Figur Manusia vs Non-Manusia")
    yh = int(DF["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
    dh = int(DF["detr_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
    tot = len(DF)
    agree = int(
        (
            DF["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") &
            DF["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")
        ).sum()
    )

    man_a, man_b = st.columns([2, 1])
    with man_a:
        fig_man = go.Figure(data=[
            go.Bar(
                name="YOLOv8n",
                x=["Ada manusia", "Tidak ada"],
                y=[yh, tot - yh],
                marker_color=["#66BB6A", "rgba(128,128,128,.15)"],
            ),
            go.Bar(
                name="DETR",
                x=["Ada manusia", "Tidak ada"],
                y=[dh, tot - dh],
                marker_color=["#42A5F5", "rgba(128,128,128,.08)"],
            ),
        ])
        fig_man.update_layout(
            **pb(240), barmode="group", showlegend=True,
            legend=dict(orientation="h", y=-.15),
        )
        st.plotly_chart(fig_man, use_container_width=True)

    with man_b:
        st.metric("Sepakat keduanya", f"{agree:,}", f"{agree/tot*100:.1f}%")
        st.metric("Hanya YOLOv8n", f"{yh-agree:,}")
        st.metric("Hanya DETR", f"{dh-agree:,}")

    # Persentase manusia per gaya
    st.markdown("**Kehadiran figur manusia per gaya ilustrasi**")
    rows_man = []
    for gk in GAYA_ID:
        sub = DF[DF["gaya_ilustrasi"] == gk]
        if sub.empty:
            continue
        pct_y = sub["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE").mean() * 100
        pct_d = sub["detr_ada_manusia"].astype(str).str.upper().eq("TRUE").mean() * 100
        rows_man.append({"Gaya": GAYA_ID[gk], "YOLOv8n (%)": round(pct_y,1), "DETR (%)": round(pct_d,1)})
    if rows_man:
        df_man_gaya = pd.DataFrame(rows_man)
        fig_mg = go.Figure()
        fig_mg.add_trace(go.Bar(
            name="YOLOv8n", x=df_man_gaya["Gaya"], y=df_man_gaya["YOLOv8n (%)"],
            marker_color="#66BB6A",
        ))
        fig_mg.add_trace(go.Bar(
            name="DETR", x=df_man_gaya["Gaya"], y=df_man_gaya["DETR (%)"],
            marker_color="#42A5F5",
        ))
        fig_mg.update_layout(**pb(260), barmode="group",
                             yaxis_title="% sampul dengan figur manusia",
                             xaxis_title="",
                             legend=dict(orientation="h", y=-.15))
        st.plotly_chart(fig_mg, use_container_width=True)

    st.markdown("<hr style='border:none;border-top:1px solid rgba(128,128,128,.12);margin:1.3rem 0;'>",
                unsafe_allow_html=True)

    # ── 8. Simpangan Illustrator ──────────────────────────────────────────────
    st.markdown("### Sampul Dengan vs Tanpa Nama Ilustrator")
    has_ill = DF["ILLUSTRATOR"].ne("")
    n_ill = has_ill.sum()
    n_no_ill = (~has_ill).sum()
    if n_ill > 0 and n_no_ill > 0:
        df_with = DF[has_ill]
        df_wout = DF[~has_ill]
        gc_w = df_with["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        gc_o = df_wout["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        diff_g = (gc_w / n_ill - gc_o / n_no_ill).dropna().sort_values(ascending=False)
        diff_g_df = diff_g.reset_index()
        diff_g_df.columns = ["gaya", "delta"]
        fig_dg = px.bar(
            diff_g_df, x="delta", y="gaya", orientation="h",
            color="gaya",
            color_discrete_map={GAYA_ID[k]: GAYA_CLR[k] for k in GAYA_ID},
        )
        fig_dg.update_layout(
            **pb(240), showlegend=False,
            xaxis_title="Selisih proporsi", yaxis_title="",
            yaxis=dict(categoryorder="total ascending"),
        )
        fig_dg.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
        st.plotly_chart(fig_dg, use_container_width=True)
        st.caption("Nilai positif = gaya lebih sering muncul pada buku **dengan** nama ilustrator.")

    st.markdown("<hr style='border:none;border-top:1px solid rgba(128,128,128,.12);margin:1.3rem 0;'>",
                unsafe_allow_html=True)

    # ── 9. Pencarian buku ─────────────────────────────────────────────────────
    st.markdown("### Cari Buku berdasarkan Gaya Ilustrasi")

    # Daftar genre untuk filter
    _gc_all = Counter()
    for gl in expand_genres(DF["GENRES"], normalize=True):
        _gc_all.update(gl)
    top_genres_list = [
        g for g, _ in _gc_all.most_common()
        if g not in GENRE_EXCLUDE and _gc_all[g] >= 3
    ][:30]

    gic1, gic2, gic3 = st.columns([2, 2, 1])
    gic4, gic5, gic6 = st.columns([2, 1, 1])

    with gic1:
        q_gi = st.text_input("Judul / penulis", key="gi_q_blk")
    with gic2:
        gaya_sel = st.selectbox(
            "Filter gaya ilustrasi",
            ["Semua"] + [GAYA_ID[k] for k in GAYA_ID],
            key="gi_sel_blk",
        )
    with gic3:
        ada_man = st.checkbox("Ada figur manusia", key="gi_man_blk")
    with gic4:
        genre_sel = st.selectbox(
            "Filter genre",
            ["Semua"] + top_genres_list,
            key="gi_genre_blk",
        )
    with gic5:
        show_probs_search = st.checkbox("Tampilkan skor probabilitas", key="gi_probs_blk")
    with gic6:
        n_gi2 = st.slider("Tampilkan", 4, 32, 8, 4, key="gi_n_blk")

    dgi = DF[DF["image_ok"] == True].copy()

    if q_gi:
        ql3 = q_gi.lower()
        dgi = dgi[
            dgi["TITLE"].str.lower().str.contains(ql3, na=False) |
            dgi["AUTHOR"].str.lower().str.contains(ql3, na=False)
        ]

    if gaya_sel != "Semua":
        grev = {v: k for k, v in GAYA_ID.items()}
        dgi = dgi[dgi["gaya_ilustrasi"] == grev.get(gaya_sel, gaya_sel)]

    if genre_sel != "Semua":
        gl_search = expand_genres(dgi["GENRES"], normalize=True)
        dgi = dgi[[genre_sel in gl for gl in gl_search]]

    if ada_man:
        dgi = dgi[
            dgi["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE") |
            dgi["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")
        ]

    st.markdown(f"**{len(dgi):,} buku ditemukan**")
    if not dgi.empty:
        grid_gi(dgi.head(n_gi2), n_cols=4, cover_dir=cover_dir, show_probs=show_probs_search)
