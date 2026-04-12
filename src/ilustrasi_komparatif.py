"""
ilustrasi_komparatif.py
=======================
Tambahkan fungsi ini ke app Streamlit utama Anda.
Panggil render_ilustrasi_komparatif(DF) di dalam blok HAL == "Ilustrasi",
setelah bagian "Peta Panas Gaya Ilustrasi × Genre".

Dependensi: semua konstanta dan fungsi yang sudah ada di app utama
(GAYA_CLR, GAYA_ID, GAYA_ICON, cover_path, expand_genres, genre_map, dsb.)
"""

import streamlit as st
import pandas as pd

# Konstanta diimpor dari app utama via wildcard — pastikan file ini
# diletakkan di folder yang sama dengan streamlit_app.py dan diimpor
# setelah konstanta didefinisikan. Atau definisikan ulang di sini
# jika perlu berdiri sendiri.
try:
    # Jika diimpor dari app utama, konstanta sudah tersedia di namespace global
    _ = GAYA_CLR
except NameError:
    # Fallback: definisi minimal agar tidak error saat diimpor mandiri
    GAYA_CLR  = {
        "photograph":    "#1E88E5",
        "flat_graphic":  "#43A047",
        "hand_drawn":    "#FB8C00",
        "text_dominant": "#E53935",
        "abstract":      "#8E24AA",
        "collage":       "#00ACC1",
    }
    GAYA_ID   = {
        "photograph":    "Fotografi",
        "flat_graphic":  "Ilustrasi Datar",
        "hand_drawn":    "Gambar Tangan",
        "text_dominant": "Dominan Teks",
        "abstract":      "Abstrak",
        "collage":       "Kolase",
    }
    GAYA_ICON = {
        "photograph":    "📷",
        "flat_graphic":  "🎨",
        "hand_drawn":    "✏️",
        "text_dominant": "🔤",
        "abstract":      "🔷",
        "collage":       "🗂️",
    }

    def cover_path(img):
        import os
        COVER_DIR = os.path.join(os.path.dirname(__file__), "..", "covers")
        if not img or str(img) in ("", "nan"):
            return None
        p = os.path.join(COVER_DIR, str(img))
        return p if os.path.exists(p) else None

# ──────────────────────────────────────────────────────────────────────────────
# HELPER: ambil top-N buku per genre+style berdasarkan confidence
# ──────────────────────────────────────────────────────────────────────────────

def _get_top_books(df, genre_keywords, style_key, n=5, lowest=False):
    """
    Kembalikan DataFrame top-N buku berdasarkan gaya_skor.
    genre_keywords: list string yang dicek via str.contains (OR logic).
    """
    mask_style = df["gaya_ilustrasi"] == style_key
    mask_genre = df["GENRES"].str.contains(
        "|".join(genre_keywords), case=False, na=False
    )
    sub = df[mask_style & mask_genre & df["image_ok"]].copy()
    sub["gaya_skor"] = pd.to_numeric(sub["gaya_skor"], errors="coerce")
    sub = sub.dropna(subset=["gaya_skor"])
    if sub.empty:
        return sub
    if lowest:
        return sub.nsmallest(n, "gaya_skor")
    return sub.nlargest(n, "gaya_skor")


# ──────────────────────────────────────────────────────────────────────────────
# CARD: satu sampul buku dengan semua info analisis
# ──────────────────────────────────────────────────────────────────────────────

def _komparatif_card(row, rank_label="", rank_color="#333", rank_bg="#f0f0f0",
                     show_warna=True):
    """Render satu kartu buku komparatif dengan info lengkap."""

    # ── Sampul ──────────────────────────────────────────────────────────────
    cp = cover_path(row.get("IMAGE_FILE"))
    if cp:
        st.image(cp, use_container_width=True)
    else:
        st.markdown(
            '<div style="height:160px;background:rgba(128,128,128,.08);'
            'border-radius:8px 8px 0 0;display:flex;align-items:center;'
            'justify-content:center;font-size:2rem;">📖</div>',
            unsafe_allow_html=True,
        )

    # ── Metadata dasar ───────────────────────────────────────────────────────
    gaya_key  = str(row.get("gaya_ilustrasi", ""))
    gaya_lbl  = GAYA_ID.get(gaya_key, gaya_key)
    gaya_clr  = GAYA_CLR.get(gaya_key, "#999")
    gaya_icon = GAYA_ICON.get(gaya_key, "")
    try:
        skor = float(row.get("gaya_skor", 0))
        skor_str = f"{skor:.3f}"
    except Exception:
        skor_str = "–"

    year  = int(row["YEAR"]) if row.get("YEAR", 0) and int(row.get("YEAR", 0)) > 0 else "–"
    url   = str(row.get("URL", "") or "")
    title = str(row.get("TITLE", "–"))
    title_html = (
        f'<a href="{url}" target="_blank" '
        f'style="text-decoration:none;color:inherit;">{title}</a>'
        if url else title
    )

    # ── Rank badge ───────────────────────────────────────────────────────────
    rank_html = (
        f'<span style="display:inline-block;background:{rank_bg};color:{rank_color};'
        f'border-radius:10px;padding:1px 8px;font-size:.6rem;font-weight:700;'
        f'margin-bottom:3px;">{rank_label}</span><br>'
        if rank_label else ""
    )

    # ── YOLO info ────────────────────────────────────────────────────────────
    ada_manusia  = str(row.get("yolo_ada_manusia", "")).upper() == "TRUE"
    detr_manusia = str(row.get("detr_ada_manusia", "")).upper() == "TRUE"
    objek_str    = str(row.get("yolo_objek", "") or "")
    objek_list   = [
        o.strip() for o in objek_str.split(",")
        if o.strip() and o.strip() not in ("0", "nan", "")
    ][:6]

    figur_srcs = []
    if ada_manusia:  figur_srcs.append("YOLO")
    if detr_manusia: figur_srcs.append("DETR")

    if figur_srcs:
        figur_html = (
            f'<span style="background:#E3F2FD;color:#1565C0;border-radius:6px;'
            f'padding:1px 6px;font-size:.57rem;font-weight:600;">'
            f'👤 {", ".join(figur_srcs)}</span>'
        )
    else:
        figur_html = (
            '<span style="background:#F5F5F5;color:#aaa;border-radius:6px;'
            'padding:1px 6px;font-size:.57rem;">— non-manusia</span>'
        )

    obj_html = ""
    if objek_list:
        tags = "".join(
            f'<span style="background:#FAFAFA;color:#666;border:1px solid #E8E8E8;'
            f'border-radius:5px;padding:0px 4px;font-size:.52rem;margin:1px;">{o}</span>'
            for o in objek_list
        )
        obj_html = f'<div style="margin-top:2px;line-height:2.1">{tags}</div>'

    yolo_box = (
        f'<div style="margin-top:4px;padding:3px 5px;'
        f'background:rgba(128,128,128,.04);'
        f'border:1px solid rgba(128,128,128,.1);border-radius:5px;">'
        f'<div style="font-size:.54rem;font-weight:600;opacity:.45;'
        f'text-transform:uppercase;letter-spacing:.04em;margin-bottom:2px;">'
        f'Objek YOLO/DETR</div>'
        f'{figur_html}{obj_html}'
        f'</div>'
    )

    # ── Prob bars ────────────────────────────────────────────────────────────
    prob_keys = ["photograph", "hand_drawn", "abstract", "flat_graphic", "text_dominant"]
    probs = {k: float(row.get(f"gaya_prob_{k}", 0) or 0) for k in prob_keys}
    bars_inner = ""
    for k, v in sorted(probs.items(), key=lambda x: -x[1]):
        lbl  = GAYA_ID.get(k, k)
        clr  = GAYA_CLR.get(k, "#999")
        pct  = v * 100
        fw   = "font-weight:700;" if k == gaya_key else ""
        bars_inner += (
            f'<div style="margin-bottom:2px;">'
            f'<div style="display:flex;justify-content:space-between;'
            f'font-size:.54rem;color:#666;margin-bottom:1px;">'
            f'<span style="{fw}">{lbl}</span>'
            f'<span style="{fw}color:{clr}">{pct:.1f}%</span></div>'
            f'<div style="background:rgba(128,128,128,.1);border-radius:2px;'
            f'height:4px;overflow:hidden;">'
            f'<div style="width:{pct:.1f}%;background:{clr};height:4px;'
            f'border-radius:2px;"></div></div></div>'
        )
    prob_box = (
        f'<div style="margin-top:4px;padding:3px 5px;'
        f'background:rgba(128,128,128,.04);'
        f'border:1px solid rgba(128,128,128,.1);border-radius:5px;">'
        f'<div style="font-size:.54rem;font-weight:600;opacity:.45;'
        f'text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px;">'
        f'Distribusi Gaya CLIP</div>{bars_inner}</div>'
    )

    # ── Palet warna ──────────────────────────────────────────────────────────
    warna_html = ""
    if show_warna:
        parts = []
        for i in range(1, 6):
            hx  = str(row.get(f"warna_hex_{i}", "") or "").strip()
            pct_w = row.get(f"warna_pct_{i}", 0)
            try: pct_w = float(pct_w)
            except: pct_w = 0.0
            if not hx or hx in ("nan", "") or pct_w <= 0: continue
            if not hx.startswith("#"): hx = "#" + hx
            parts.append((hx, pct_w))
        total_w = sum(p for _, p in parts)
        if parts and total_w > 0:
            sw = "".join(
                f'<div style="background:{hx};width:{p/total_w*100:.1f}%;'
                f'height:100%;"></div>'
                for hx, p in parts
            )
            warna_html = (
                f'<div style="display:flex;height:8px;border-radius:3px;'
                f'overflow:hidden;gap:1px;margin:.25rem 0;">{sw}</div>'
            )

    # ── Render ───────────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="padding:.35rem .4rem .5rem;'
        f'border:1px solid rgba(128,128,128,.1);'
        f'border-top:3px solid {gaya_clr};border-radius:0 0 8px 8px;'
        f'font-size:.62rem;">'
        f'{rank_html}'
        f'<span style="background:{gaya_clr}18;color:{gaya_clr};'
        f'border-radius:5px;padding:1px 5px;font-size:.58rem;font-weight:600;">'
        f'{gaya_icon} {gaya_lbl} · {skor_str}</span>'
        f'<div style="font-family:\'Lora\',serif;font-size:.75rem;font-weight:600;'
        f'line-height:1.3;margin:.2rem 0 .05rem;">{title_html}</div>'
        f'<div style="font-size:.62rem;color:#999;">'
        f'{row.get("AUTHOR","–")} · {year}</div>'
        f'{warna_html}'
        f'{yolo_box}'
        f'{prob_box}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# SECTION HEADER
# ──────────────────────────────────────────────────────────────────────────────

def _section_header(title, subtitle="", color="#2E4057", bg="#EEF2F7"):
    st.markdown(
        f'<div style="background:{bg};border-left:4px solid {color};'
        f'border-radius:0 8px 8px 0;padding:8px 14px;margin:1.4rem 0 .6rem;">'
        f'<div style="font-family:\'Lora\',serif;font-weight:600;'
        f'color:{color};font-size:.95rem;">{title}</div>'
        f'{"<div style=font-size:.72rem;color:"+color+";opacity:.7;margin-top:2px;>"+subtitle+"</div>" if subtitle else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _subsection(label, color="#555", n_buku=0):
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:6px;'
        f'margin:.5rem 0 .3rem;">'
        f'<span style="width:10px;height:10px;border-radius:3px;'
        f'background:{color};display:inline-block;flex-shrink:0;"></span>'
        f'<span style="font-size:.82rem;font-weight:600;color:{color};">{label}</span>'
        f'<span style="font-size:.65rem;color:#bbb;">({n_buku} buku teranalisis)</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# RENDER SATU PASANGAN: dua genre, satu style, top-N + bottom-N
# ──────────────────────────────────────────────────────────────────────────────

def _render_pair(df, genre_a_kw, genre_b_kw, style_key,
                 label_a, label_b, color_a, color_b, n=5):
    """
    Tampilkan perbandingan genre A vs genre B untuk satu gaya ilustrasi.
    Masing-masing menampilkan top-n confidence tertinggi.
    """
    top_a = _get_top_books(df, genre_a_kw, style_key, n=n)
    top_b = _get_top_books(df, genre_b_kw, style_key, n=n)

    n_a = len(df[
        df["GENRES"].str.contains("|".join(genre_a_kw), case=False, na=False) &
        (df["gaya_ilustrasi"] == style_key)
    ])
    n_b = len(df[
        df["GENRES"].str.contains("|".join(genre_b_kw), case=False, na=False) &
        (df["gaya_ilustrasi"] == style_key)
    ])

    col_left, col_divider, col_right = st.columns([10, 1, 10])

    with col_left:
        _subsection(label_a, color_a, n_a)
        if top_a.empty:
            st.caption("Tidak ada data.")
        else:
            cols = st.columns(min(n, len(top_a)))
            for i, (_, row) in enumerate(top_a.iterrows()):
                if i >= len(cols): break
                with cols[i]:
                    _komparatif_card(
                        row,
                        rank_label=f"#{i+1} · {float(row.get('gaya_skor',0)):.3f}",
                        rank_color=color_a,
                        rank_bg=color_a + "22",
                    )

    with col_divider:
        st.markdown(
            '<div style="width:1px;background:rgba(128,128,128,.15);'
            'min-height:400px;margin:0 auto;"></div>',
            unsafe_allow_html=True,
        )

    with col_right:
        _subsection(label_b, color_b, n_b)
        if top_b.empty:
            st.caption("Tidak ada data.")
        else:
            cols = st.columns(min(n, len(top_b)))
            for i, (_, row) in enumerate(top_b.iterrows()):
                if i >= len(cols): break
                with cols[i]:
                    _komparatif_card(
                        row,
                        rank_label=f"#{i+1} · {float(row.get('gaya_skor',0)):.3f}",
                        rank_color=color_b,
                        rank_bg=color_b + "22",
                    )


# ──────────────────────────────────────────────────────────────────────────────
# RENDER: CONFIDENCE TERTINGGI VS TERENDAH untuk satu genre+style
# ──────────────────────────────────────────────────────────────────────────────

def _render_top_bottom(df, genre_kw, style_key, label, color, n=5):
    """Tampilkan top-n dan bottom-n confidence untuk satu genre+style."""
    top = _get_top_books(df, genre_kw, style_key, n=n, lowest=False)
    bot = _get_top_books(df, genre_kw, style_key, n=n, lowest=True)

    n_total = len(df[
        df["GENRES"].str.contains("|".join(genre_kw), case=False, na=False) &
        (df["gaya_ilustrasi"] == style_key) &
        df["image_ok"]
    ])

    _subsection(label, color, n_total)

    hdr_top, hdr_bot = st.columns(2)
    with hdr_top:
        st.markdown(
            '<div style="text-align:center;background:#E8F5E9;border-radius:6px;'
            'padding:3px;font-size:.65rem;font-weight:700;color:#1B7D3C;'
            'margin-bottom:.35rem;">✦ Confidence Tertinggi</div>',
            unsafe_allow_html=True,
        )
    with hdr_bot:
        st.markdown(
            '<div style="text-align:center;background:#FFEBEE;border-radius:6px;'
            'padding:3px;font-size:.65rem;font-weight:700;color:#B71C1C;'
            'margin-bottom:.35rem;">▾ Confidence Terendah</div>',
            unsafe_allow_html=True,
        )

    all_cols = st.columns(n * 2)
    for i, (_, row) in enumerate(top.iterrows()):
        if i >= n: break
        with all_cols[i]:
            _komparatif_card(
                row,
                rank_label=f"#{i+1} · {float(row.get('gaya_skor',0)):.3f}",
                rank_color="#1B7D3C", rank_bg="#E8F5E9",
            )
    for i, (_, row) in enumerate(bot.iterrows()):
        if i >= n: break
        with all_cols[n + i]:
            _komparatif_card(
                row,
                rank_label=f"▾ · {float(row.get('gaya_skor',0)):.3f}",
                rank_color="#B71C1C", rank_bg="#FFEBEE",
            )


# ──────────────────────────────────────────────────────────────────────────────
# GENERATE PNG — render grid sampul ke matplotlib figure
# ──────────────────────────────────────────────────────────────────────────────

import io
import os
import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from PIL import Image as PILImage
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False


def _load_cover_image(img_file, size=(200, 280)):
    """Muat gambar sampul sebagai numpy array. Kembalikan None jika gagal."""
    if not _HAS_PIL:
        return None
    cp = cover_path(img_file)
    if not cp:
        return None
    try:
        img = PILImage.open(cp).convert("RGB")
        img = img.resize(size, PILImage.LANCZOS)
        return np.array(img)
    except Exception:
        return None


def _build_komparatif_figure(rows_a, rows_b, label_a, label_b,
                              color_a, color_b, style_key,
                              title="", subtitle="", dpi=150):
    """
    Buat matplotlib figure berisi dua baris sampul (kiri = genre A, kanan = genre B).
    Setiap sampul ditampilkan dengan: gambar, judul, skor, palet warna, objek YOLO.
    """
    if not _HAS_PIL:
        return None

    WARNA_HEX_LOCAL = {
        "putih": "#F5F5F0", "hitam": "#1A1A1A", "abu": "#8E8E93",
        "merah": "#E53935", "pink": "#F06292", "oranye": "#FB8C00",
        "cokelat": "#795548", "kuning": "#FDD835", "hijau": "#43A047",
        "biru": "#1E88E5", "ungu": "#8E24AA",
    }

    n_a = len(rows_a)
    n_b = len(rows_b)
    n_cols = max(n_a, n_b)
    if n_cols == 0:
        return None

    # Layout: 2 baris genre × n_cols sampul
    # Tiap sel: gambar + info di bawahnya
    IMG_W, IMG_H = 1.6, 2.2          # inch per gambar
    INFO_H       = 1.3               # inch info di bawah gambar
    CELL_W       = IMG_W + 0.15
    CELL_H       = IMG_H + INFO_H + 0.1
    HEADER_H     = 0.55              # judul genre
    TOP_H        = 0.70              # judul chart
    GAP_H        = 0.25              # jarak antar baris genre
    DIVIDER_W    = 0.05

    fig_w = n_cols * CELL_W * 2 + DIVIDER_W + 0.4
    fig_h = TOP_H + 2 * (HEADER_H + CELL_H) + GAP_H + 0.3

    fig = plt.figure(figsize=(fig_w, fig_h), facecolor="white")

    # ── Judul utama ──────────────────────────────────────────────────────────
    fig.text(
        0.5, 1 - 0.08 / fig_h,
        title, ha="center", va="top",
        fontsize=11, fontweight="bold", color="#1A1A1A",
    )
    if subtitle:
        fig.text(
            0.5, 1 - (TOP_H * 0.62) / fig_h,
            subtitle, ha="center", va="top",
            fontsize=7.5, color="#888",
        )

    def _draw_genre_row(rows, label, color, row_idx):
        """Gambar satu baris genre di posisi row_idx (0 = kiri/atas, 1 = kanan/bawah)."""
        x0_frac = row_idx * (0.5 + DIVIDER_W / fig_w / 2)

        # Header genre
        y_hdr = 1 - (TOP_H + row_idx * (HEADER_H + CELL_H + GAP_H) + HEADER_H * 0.6) / fig_h
        fig.text(
            x0_frac + 0.01, y_hdr,
            f"{'✦' if row_idx == 0 else '▸'} {label}",
            ha="left", va="center",
            fontsize=9, fontweight="bold", color=color,
        )

        for ci, (_, row) in enumerate(rows):
            # Koordinat axes untuk gambar
            x_ax = (x0_frac + ci * CELL_W / fig_w)
            y_ax = 1 - (TOP_H + row_idx * (HEADER_H + CELL_H + GAP_H) + HEADER_H + CELL_H) / fig_h
            w_ax = IMG_W / fig_w
            h_ax = IMG_H / fig_h

            ax_img = fig.add_axes([x_ax, y_ax, w_ax, h_ax])
            img_arr = _load_cover_image(row.get("IMAGE_FILE"))
            if img_arr is not None:
                ax_img.imshow(img_arr)
            else:
                ax_img.set_facecolor("#F0F0F0")
                ax_img.text(0.5, 0.5, "📖", ha="center", va="center",
                            fontsize=18, transform=ax_img.transAxes)
            ax_img.axis("off")

            # Border warna genre
            for spine in ax_img.spines.values():
                spine.set_edgecolor(color)
                spine.set_linewidth(1.5)
                spine.set_visible(True)

            # ── Info di bawah gambar ─────────────────────────────────────
            ax_info = fig.add_axes([
                x_ax, y_ax - INFO_H / fig_h,
                w_ax, INFO_H / fig_h
            ])
            ax_info.set_xlim(0, 1)
            ax_info.set_ylim(0, 1)
            ax_info.axis("off")
            ax_info.set_facecolor("white")

            # Skor confidence
            try:
                skor = float(row.get("gaya_skor", 0))
                skor_str = f"{skor:.3f}"
            except Exception:
                skor_str = "–"

            gaya_lbl = GAYA_ID.get(str(row.get("gaya_ilustrasi", "")), "")
            ax_info.text(
                0.03, 0.97,
                f"{gaya_lbl} · {skor_str}",
                ha="left", va="top", fontsize=6,
                color=GAYA_CLR.get(str(row.get("gaya_ilustrasi", "")), "#999"),
                fontweight="bold",
                transform=ax_info.transAxes,
            )

            # Judul (maks 2 baris)
            title_txt = str(row.get("TITLE", "–"))
            if len(title_txt) > 32:
                title_txt = title_txt[:30] + "…"
            ax_info.text(
                0.03, 0.83,
                title_txt,
                ha="left", va="top", fontsize=6.5, fontweight="bold",
                color="#1A1A1A", wrap=True,
                transform=ax_info.transAxes,
            )

            # Penulis + tahun
            year = int(row["YEAR"]) if row.get("YEAR", 0) and int(row.get("YEAR", 0)) > 0 else "–"
            author = str(row.get("AUTHOR", "–"))
            if len(author) > 22: author = author[:20] + "…"
            ax_info.text(
                0.03, 0.68,
                f"{author} · {year}",
                ha="left", va="top", fontsize=5.5, color="#888",
                transform=ax_info.transAxes,
            )

            # Palet warna (mini bar)
            pal_parts = []
            for pi in range(1, 6):
                hx  = str(row.get(f"warna_hex_{pi}", "") or "").strip()
                pct = row.get(f"warna_pct_{pi}", 0)
                try: pct = float(pct)
                except: pct = 0.0
                if not hx or hx in ("nan", "") or pct <= 0: continue
                if not hx.startswith("#"): hx = "#" + hx
                pal_parts.append((hx, pct))
            if pal_parts:
                total_p = sum(p for _, p in pal_parts)
                cx = 0.03
                BAR_Y, BAR_H2 = 0.54, 0.06
                for hx, pct in pal_parts:
                    seg = (pct / total_p) * 0.94
                    rect = mpatches.FancyBboxPatch(
                        (cx, BAR_Y), seg - 0.005, BAR_H2,
                        boxstyle="square,pad=0",
                        facecolor=hx,
                        edgecolor=hx,
                        linewidth=0.2,
                        transform=ax_info.transAxes,
                    )
                    ax_info.add_patch(rect)
                    cx += seg

            # Figur manusia
            ada = str(row.get("yolo_ada_manusia", "")).upper() == "TRUE"
            detr = str(row.get("detr_ada_manusia", "")).upper() == "TRUE"
            figur_txt = "👤 " + ("+".join(filter(None, [
                "YOLO" if ada else "", "DETR" if detr else ""
            ])) or "—")
            ax_info.text(
                0.03, 0.44,
                figur_txt,
                ha="left", va="top", fontsize=5.5,
                color="#1565C0" if (ada or detr) else "#aaa",
                transform=ax_info.transAxes,
            )

            # Objek YOLO
            objek_str = str(row.get("yolo_objek", "") or "")
            objs = [
                o.strip() for o in objek_str.split(",")
                if o.strip() and o.strip() not in ("0", "nan", "")
            ][:5]
            obj_txt = ", ".join(objs) if objs else "—"
            if len(obj_txt) > 30: obj_txt = obj_txt[:28] + "…"
            ax_info.text(
                0.03, 0.32,
                obj_txt,
                ha="left", va="top", fontsize=5, color="#666",
                transform=ax_info.transAxes,
            )

    # Gambar dua baris
    _draw_genre_row(list(rows_a.iterrows()), label_a, color_a, 0)
    _draw_genre_row(list(rows_b.iterrows()), label_b, color_b, 1)

    # Garis pembatas tengah (vertikal untuk pair, horizontal untuk top/bottom)
    fig.add_axes([0.5, 0.05, 0.002, 0.85]).set_visible(False)

    # Caption
    fig.text(
        0.5, 0.01,
        "Sumber: Kartografi Sampul Sastra Indonesia 2000–2025  ·  "
        "Metode: CLIP zero-shot · YOLOv8n · DETR ResNet-50",
        ha="center", va="bottom", fontsize=5.5, color="#bbb",
    )

    fig.patch.set_facecolor("white")
    return fig


def _fig_to_bytes_komparatif(fig, dpi=200):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi,
                bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _download_row(df, genre_a_kw, genre_b_kw, style_key,
                  label_a, label_b, color_a, color_b,
                  filename, section_title, section_subtitle, n=4):
    """Render tombol unduh PNG di bawah setiap section."""
    dl_c1, dl_c2, dl_c3 = st.columns([3, 1, 1])
    with dl_c1:
        st.markdown(
            "<small>💡 <strong>Tips Word:</strong> Unduh PNG lalu sisipkan via "
            "<em>Insert → Pictures</em>. Klik kanan → "
            "<em>Wrap Text → In Line with Text</em>, "
            "tarik sudut sambil tahan Shift untuk resize proporsional.</small>",
            unsafe_allow_html=True,
        )
    with dl_c2:
        dpi_sel = st.selectbox(
            "Resolusi", [150, 200, 300], index=1,
            key=f"dpi_{filename}",
            help="300 DPI terbaik untuk cetak",
        )
    with dl_c3:
        if st.button(
            "🖼 Buat & Unduh PNG",
            key=f"btn_{filename}",
            use_container_width=True,
        ):
            with st.spinner("Membuat gambar…"):
                rows_a = _get_top_books(df, genre_a_kw, style_key, n=n)
                rows_b = _get_top_books(df, genre_b_kw, style_key, n=n)
                if rows_a.empty and rows_b.empty:
                    st.warning("Tidak ada data untuk diunduh.")
                    return
                fig = _build_komparatif_figure(
                    rows_a, rows_b,
                    label_a, label_b,
                    color_a, color_b,
                    style_key,
                    title=section_title,
                    subtitle=section_subtitle,
                    dpi=dpi_sel,
                )
                if fig is None:
                    st.warning(
                        "Pustaka Pillow tidak tersedia. "
                        "Jalankan: pip install pillow"
                    )
                    return
                img_bytes = _fig_to_bytes_komparatif(fig, dpi=dpi_sel)
                st.download_button(
                    label=f"⬇ Download {filename}.png",
                    data=img_bytes,
                    file_name=f"{filename}.png",
                    mime="image/png",
                    key=f"dl_{filename}",
                    use_container_width=True,
                )


def _download_row_single(df, genre_kw, style_key, label, color,
                         filename, section_title, section_subtitle, n=4):
    """Tombol unduh PNG untuk satu genre (top/bottom)."""
    dl_c1, dl_c2, dl_c3 = st.columns([3, 1, 1])
    with dl_c1:
        st.markdown(
            "<small>💡 <strong>Tips Word:</strong> Unduh PNG lalu sisipkan via "
            "<em>Insert → Pictures</em>. Klik kanan → "
            "<em>Wrap Text → In Line with Text</em>, "
            "tarik sudut sambil tahan Shift untuk resize proporsional.</small>",
            unsafe_allow_html=True,
        )
    with dl_c2:
        dpi_sel = st.selectbox(
            "Resolusi", [150, 200, 300], index=1,
            key=f"dpi_{filename}",
            help="300 DPI terbaik untuk cetak",
        )
    with dl_c3:
        if st.button(
            "🖼 Buat & Unduh PNG",
            key=f"btn_{filename}",
            use_container_width=True,
        ):
            with st.spinner("Membuat gambar…"):
                top = _get_top_books(df, genre_kw, style_key, n=n, lowest=False)
                bot = _get_top_books(df, genre_kw, style_key, n=n, lowest=True)
                if top.empty and bot.empty:
                    st.warning("Tidak ada data untuk diunduh.")
                    return
                fig = _build_komparatif_figure(
                    top, bot,
                    f"{label} — Tertinggi",
                    f"{label} — Terendah",
                    color, "#999",
                    style_key,
                    title=section_title,
                    subtitle=section_subtitle,
                    dpi=dpi_sel,
                )
                if fig is None:
                    st.warning("Pustaka Pillow tidak tersedia.")
                    return
                img_bytes = _fig_to_bytes_komparatif(fig, dpi=dpi_sel)
                st.download_button(
                    label=f"⬇ Download {filename}.png",
                    data=img_bytes,
                    file_name=f"{filename}.png",
                    mime="image/png",
                    key=f"dl_{filename}",
                    use_container_width=True,
                )


# ──────────────────────────────────────────────────────────────────────────────
# FUNGSI UTAMA — panggil ini dari app Streamlit
# ──────────────────────────────────────────────────────────────────────────────

def render_ilustrasi_komparatif(df):
    """
    Visualisasi komparatif gaya ilustrasi antar genre.
    Tambahkan ke halaman Ilustrasi di app utama:

        elif HAL == "Ilustrasi":
            ...
            st.markdown("<hr class='thin'>", unsafe_allow_html=True)
            render_ilustrasi_komparatif(DF)
    """
    st.markdown("### Analisis Komparatif Gaya Ilustrasi")
    st.markdown(
        "<small>Perbandingan sampul dengan confidence CLIP tertinggi "
        "per genre dan gaya ilustrasi. Setiap kartu menampilkan: "
        "skor confidence, distribusi probabilitas semua gaya, "
        "dan hasil deteksi objek YOLO + DETR.</small>",
        unsafe_allow_html=True,
    )

    n_sampel = st.slider(
        "Jumlah sampul per kelompok", 3, 5, 4,
        key="komparatif_n",
        help="Jumlah sampul confidence tertinggi yang ditampilkan per genre"
    )

    # ── TAB ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "✏️ Horor vs Anak-anak",
        "🎨 Fiksi Populer (Flat)",
        "📷 Fotografi: Puisi vs Fiksi Sejarah",
        "🗂️ Kolase",
        "🔷 Abstrak",
    ])

    # ── TAB 1: HOROR vs ANAK-ANAK (keduanya hand_drawn) ─────────────────────
    with tab1:
        _section_header(
            "Gambar Tangan: Horor vs Anak-anak",
            subtitle=(
                "Keduanya didominasi gaya hand_drawn, "
                "tetapi mode naratif dan palet warna berbeda. "
                "Horor: warna gelap, oranye, merah. "
                "Anak-anak: warna cerah, hangat, beragam."
            ),
            color="#FB8C00", bg="#FFF3E0",
        )
        _render_pair(
            df,
            genre_a_kw=["Horor", "Horror"],
            genre_b_kw=["Anak", "Children"],
            style_key="hand_drawn",
            label_a="Horor — Gambar Tangan",
            label_b="Anak-anak — Gambar Tangan",
            color_a="#B71C1C",
            color_b="#1565C0",
            n=n_sampel,
        )
        st.markdown(
            '<div style="margin:.8rem 0;padding:.5rem .8rem;'
            'background:rgba(128,128,128,.04);border-radius:8px;'
            'font-size:.72rem;color:#555;line-height:1.7;">'
            '<strong>Catatan baca:</strong> Perhatikan distribusi warna pada kartu masing-masing. '
            'Horor cenderung gelap (oranye tua, merah, ungu, abu) dengan kecerahan rendah. '
            'Anak-anak menggunakan spektrum yang lebih merata dan terang. '
            'Keduanya menggunakan <em>technologies of the hand</em> dalam kerangka Kress & van Leeuwen, '
            'tetapi warna yang menentukan konotasinya.'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<hr class='thin'>", unsafe_allow_html=True)
        _download_row(
            df,
            genre_a_kw=["Horor", "Horror"],
            genre_b_kw=["Anak", "Children"],
            style_key="hand_drawn",
            label_a="Horor — Gambar Tangan",
            label_b="Anak-anak — Gambar Tangan",
            color_a="#B71C1C",
            color_b="#1565C0",
            filename="komparatif_horor_vs_anak",
            section_title="Gambar Tangan: Horor vs Anak-anak",
            section_subtitle="Confidence CLIP tertinggi per genre — Kartografi Sampul Sastra Indonesia 2000–2025",
            n=n_sampel,
        )

    # ── TAB 2: FIKSI POPULER (flat_graphic) ──────────────────────────────────
    with tab2:
        _section_header(
            "Estetika Fiksi Populer — Ilustrasi Datar",
            subtitle=(
                "Romansa, Remaja, dan Chick Lit "
                "berbagi dominasi flat_graphic "
                "(synthesizing technologies). "
                "Estetika bersih, warna solid, "
                "dirancang untuk layar digital."
            ),
            color="#43A047", bg="#E8F5E9",
        )

        for genre_kw, label, color in [
            (["Romansa", "Romance", "Cinta"],   "Romansa",   "#E53935"),
            (["Remaja", "Young Adult"],          "Remaja",    "#FB8C00"),
            (["Chick Lit", "Chicklit"],          "Chick Lit", "#8E24AA"),
        ]:
            _render_top_bottom(
                df, genre_kw, "flat_graphic", label, color, n=n_sampel
            )
            st.markdown("<hr class='thin'>", unsafe_allow_html=True)
            _download_row_single(
                df, genre_kw, "flat_graphic", label, color,
                filename=f"komparatif_flat_{label.lower().replace(' ','_').replace('/','_')}",
                section_title=f"Ilustrasi Datar — {label}",
                section_subtitle="Confidence CLIP tertinggi & terendah — Kartografi Sampul Sastra Indonesia 2000–2025",
                n=n_sampel,
            )
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── TAB 3: FOTOGRAFI — Puisi vs Fiksi Sejarah ────────────────────────────
    with tab3:
        _section_header(
            "Fotografi: Puisi vs Fiksi Sejarah",
            subtitle=(
                "Keduanya didominasi fotografi (recording technologies), "
                "tetapi objek yang ditampilkan berbeda: "
                "Fiksi Sejarah menampilkan figur manusia dan hewan historis; "
                "Puisi cenderung menampilkan objek atmosferik dan simbolis."
            ),
            color="#1E88E5", bg="#E3F2FD",
        )
        _render_pair(
            df,
            genre_a_kw=["Puisi", "Poetry", "Sajak"],
            genre_b_kw=["Fiksi Sejarah", "Sejarah", "Historical"],
            style_key="photograph",
            label_a="Puisi — Fotografi",
            label_b="Fiksi Sejarah — Fotografi",
            color_a="#7B1FA2",
            color_b="#1B5E20",
            n=n_sampel,
        )
        st.markdown(
            '<div style="margin:.8rem 0;padding:.5rem .8rem;'
            'background:rgba(128,128,128,.04);border-radius:8px;'
            'font-size:.72rem;color:#555;line-height:1.7;">'
            '<strong>Panduan baca:</strong> Perhatikan kolom "Objek YOLO/DETR" '
            'di setiap kartu. Fiksi Sejarah umumnya mendeteksi person, horse, bird '
            '— objek yang mengacu pada kehadiran tubuh dan tindakan historis. '
            'Puisi mendeteksi objek yang lebih cair: jam, kucing, layang-layang, '
            'burung — benda-benda atmosferik dan simbolis.'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<hr class='thin'>", unsafe_allow_html=True)
        _download_row(
            df,
            genre_a_kw=["Puisi", "Poetry", "Sajak"],
            genre_b_kw=["Fiksi Sejarah", "Sejarah", "Historical"],
            style_key="photograph",
            label_a="Puisi — Fotografi",
            label_b="Fiksi Sejarah — Fotografi",
            color_a="#7B1FA2",
            color_b="#1B5E20",
            filename="komparatif_foto_puisi_vs_sejarah",
            section_title="Fotografi: Puisi vs Fiksi Sejarah",
            section_subtitle="Confidence CLIP tertinggi — Kartografi Sampul Sastra Indonesia 2000–2025",
            n=n_sampel,
        )

    # ── TAB 4: KOLASE ─────────────────────────────────────────────────────────
    with tab4:
        _section_header(
            "Gaya Kolase",
            subtitle=(
                "Chick Lit mencatatkan proporsi kolase tertinggi (20%), "
                "diikuti Fantasi (8,2%) dan Romansa (4%). "
                "Kolase menggabungkan elemen fotografis dan ilustratif "
                "dalam satu komposisi."
            ),
            color="#00ACC1", bg="#E0F7FA",
        )

        for genre_kw, label, color in [
            (["Chick Lit", "Chicklit"],         "Chick Lit", "#8E24AA"),
            (["Fantasi", "Fantasy"],             "Fantasi",   "#1565C0"),
            (["Romansa", "Romance", "Cinta"],    "Romansa",   "#E53935"),
        ]:
            _render_top_bottom(
                df, genre_kw, "collage", label, color, n=n_sampel
            )
            st.markdown("<hr class='thin'>", unsafe_allow_html=True)
            _download_row_single(
                df, genre_kw, "collage", label, color,
                filename=f"komparatif_kolase_{label.lower().replace(' ','_').replace('/','_')}",
                section_title=f"Kolase — {label}",
                section_subtitle="Confidence CLIP tertinggi & terendah — Kartografi Sampul Sastra Indonesia 2000–2025",
                n=n_sampel,
            )
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── TAB 5: ABSTRAK ────────────────────────────────────────────────────────
    with tab5:
        _section_header(
            "Gaya Abstrak",
            subtitle=(
                "Puisi mencatatkan proporsi abstrak tertinggi (7,7%), "
                "diikuti Fiksi Sejarah (8%) dan Fantasi (4,1%). "
                "Gaya abstrak mereduksi representasi ke bentuk esensial, "
                "melepaskan diri dari referensialitas fotografis."
            ),
            color="#8E24AA", bg="#F3E5F5",
        )

        for genre_kw, label, color in [
            (["Puisi", "Poetry"],                "Puisi",         "#7B1FA2"),
            (["Fiksi Sejarah", "Sejarah"],       "Fiksi Sejarah", "#1B5E20"),
            (["Fantasi", "Fantasy"],             "Fantasi",       "#1565C0"),
        ]:
            _render_top_bottom(
                df, genre_kw, "abstract", label, color, n=n_sampel
            )
            st.markdown("<hr class='thin'>", unsafe_allow_html=True)
            _download_row_single(
                df, genre_kw, "abstract", label, color,
                filename=f"komparatif_abstrak_{label.lower().replace(' ','_').replace('/','_')}",
                section_title=f"Abstrak — {label}",
                section_subtitle="Confidence CLIP tertinggi & terendah — Kartografi Sampul Sastra Indonesia 2000–2025",
                n=n_sampel,
            )
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# CARA INTEGRASI KE APP UTAMA
# ──────────────────────────────────────────────────────────────────────────────
#
# 1. Salin seluruh file ini ke folder yang sama dengan app.py
# 2. Di awal app.py, tambahkan:
#      from ilustrasi_komparatif import render_ilustrasi_komparatif
#
# 3. Di blok HAL == "Ilustrasi", tambahkan setelah heatmap gaya:
#      st.markdown("<hr class='thin'>", unsafe_allow_html=True)
#      render_ilustrasi_komparatif(DF)
#
# 4. Tidak perlu mengubah konstanta apapun — fungsi ini menggunakan
#    GAYA_CLR, GAYA_ID, GAYA_ICON, cover_path, expand_genres
#    yang sudah didefinisikan di app utama.
