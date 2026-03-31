# =============================================================================
# streamlit_app.py
# Dashboard Analisis Sampul Buku Fiksi Indonesia 2000–2025
# Deploy ke HuggingFace Spaces: src/streamlit_app.py
#
# Struktur repo HuggingFace yang diperlukan:
#   src/
#     streamlit_app.py    ← file ini
#     data.csv            ← output data_final.csv dari notebook analisis
#   covers/               ← folder gambar (Git LFS)
#     *.jpg
#   requirements.txt
#
# requirements.txt:
#   streamlit>=1.32.0
#   pandas>=2.0.0
#   numpy>=1.24.0
#   matplotlib>=3.7.0
#   plotly>=5.18.0
#   pillow>=10.0.0
# =============================================================================

import os
import ast
import json
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import streamlit as st

# ── Konfigurasi halaman ──────────────────────────────────────────────────────
st.set_page_config(
    page_title='Analisis Sampul Fiksi Indonesia',
    page_icon='📚',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── Path ─────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(__file__)
DATA_PATH   = os.path.join(BASE_DIR, 'data.csv')
COVERS_DIR  = os.path.join(os.path.dirname(BASE_DIR), 'covers')

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #6c757d;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        border-left: 4px solid #3498db;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.3rem;
        margin: 1.2rem 0 0.8rem 0;
    }
    .cover-caption {
        font-size: 0.75rem;
        color: #6c757d;
        text-align: center;
        margin-top: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, sep=';', encoding='utf-8-sig', dtype=str)
    df.columns = df.columns.str.strip().str.upper()

    # Normalisasi tipe
    for col in ['RATING_AVG']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            # Format integer lama: 411 → 4.11
            mask = df[col] > 10
            df.loc[mask, col] = df.loc[mask, col] / 100

    for col in ['TAHUN_TERBIT', 'TAHUN']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    for col in ['BRIGHTNESS_MEAN', 'SATURATION_MEAN', 'TEKS_COVERAGE',
                'TYPEFACE_CONFIDENCE', 'GAYA_SKOR', 'YOLO_N_OBJEK',
                'DETR_OBJEK_N', 'JUDUL_MATCH_SCORE']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    for col in ['WARNA_PCT_1', 'WARNA_PCT_2', 'WARNA_PCT_3',
                'WARNA_PCT_4', 'WARNA_PCT_5']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df


df = load_data(DATA_PATH)


# ── Tentukan kolom kunci ─────────────────────────────────────────────────────
TITLE_COL  = next((c for c in ['JUDUL', 'TITLE', 'NAMA_BUKU'] if c in df.columns), None)
AUTHOR_COL = next((c for c in ['PENULIS', 'AUTHOR', 'PENGARANG'] if c in df.columns), None)
IMG_COL    = next((c for c in ['NAMA_FILE_GAMBAR', 'IMAGE_FILE', 'GAMBAR'] if c in df.columns), None)
YEAR_COL   = next((c for c in ['TAHUN_TERBIT', 'TAHUN', 'YEAR'] if c in df.columns), None)
GENRE_COL  = next((c for c in ['GENRES', 'GENRE', 'KATEGORI'] if c in df.columns), None)
RATING_COL = next((c for c in ['RATING_AVG', 'RATING', 'AVERAGE_RATING'] if c in df.columns), None)


# ── Helper: multi-label genre filter ────────────────────────────────────────
def get_books_for_genre(df, genre):
    if not GENRE_COL or genre == 'Semua':
        return df
    return df[df[GENRE_COL].fillna('').str.contains(genre, case=False, na=False)]


def get_all_genres(df):
    if not GENRE_COL:
        return ['Semua']
    genres = set()
    for val in df[GENRE_COL].dropna():
        for g in str(val).split(','):
            g = g.strip()
            if g:
                genres.add(g)
    return ['Semua'] + sorted(genres)


# ── Warna untuk kategori ─────────────────────────────────────────────────────
WARNA_HEX = {
    'merah':  '#e74c3c', 'biru':    '#3498db', 'hijau':  '#2ecc71',
    'kuning': '#f1c40f', 'oranye':  '#e67e22', 'ungu':   '#9b59b6',
    'hitam':  '#2c3e50', 'putih':   '#ecf0f1', 'abu':    '#95a5a6',
}
GAYA_COLORS = {
    'photograph':    '#3498db', 'hand_drawn':    '#e74c3c',
    'abstract':      '#9b59b6', 'flat_graphic':  '#2ecc71',
    'collage':       '#f39c12', 'text_dominant': '#1abc9c',
    'unknown':       '#bdc3c7',
}
TYPEFACE_COLORS = {
    'serif': '#2c3e50', 'sans-serif': '#3498db', 'slab-serif': '#e67e22',
    'script': '#e74c3c', 'display': '#9b59b6', 'monospace': '#27ae60',
    'unknown': '#bdc3c7',
}


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image('https://upload.wikimedia.org/wikipedia/commons/1/1b/DKJ_logo.png',
             width=80) if False else None  # placeholder, ganti dengan logo jika ada
    st.markdown('### 📚 Filter Dataset')

    # Filter genre
    all_genres = get_all_genres(df)
    selected_genre = st.selectbox('Genre', all_genres)

    # Filter tahun
    if YEAR_COL and df[YEAR_COL].max() > 0:
        year_min = int(df[YEAR_COL][df[YEAR_COL] > 1990].min())
        year_max = int(df[YEAR_COL].max())
        year_range = st.slider('Rentang Tahun',
                                min_value=year_min, max_value=year_max,
                                value=(year_min, year_max))
    else:
        year_range = (2000, 2025)

    st.markdown('---')
    st.markdown('### 🔍 Navigasi')
    page = st.radio('Halaman', [
        '📊 Ringkasan',
        '🎨 Modul A — Warna',
        '🔤 Modul B — Typeface',
        '🖼️ Modul C — Ilustrasi',
        '📖 Jelajah Buku',
    ])

    st.markdown('---')
    st.markdown(
        '<small>**Referensi:**<br>'
        'Arnold & Tilton (2023) *Distant Viewing*<br>'
        'Lupton (2024) *Thinking with Type*<br>'
        'Genette (1997) *Paratexts*<br>'
        'Manovich (2020) *Cultural Analytics*</small>',
        unsafe_allow_html=True
    )


# ── Filter dataframe ──────────────────────────────────────────────────────────
df_filtered = get_books_for_genre(df, selected_genre)
if YEAR_COL:
    df_filtered = df_filtered[
        (df_filtered[YEAR_COL] >= year_range[0]) &
        (df_filtered[YEAR_COL] <= year_range[1])
    ]


# =============================================================================
# HALAMAN 1: RINGKASAN
# =============================================================================
if page == '📊 Ringkasan':
    st.markdown('<div class="main-header">Analisis Sampul Buku Fiksi Indonesia 2000–2025</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Pipeline komputasional: K-Means warna (Modul A) · '
        'Typeface KNN (Modul B) · YOLO+DETR+CLIP ilustrasi (Modul C)</div>',
        unsafe_allow_html=True
    )

    # Metrik utama
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric('Total Buku', f'{len(df_filtered):,}')
    with col2:
        if YEAR_COL:
            years = df_filtered[YEAR_COL][df_filtered[YEAR_COL] > 0]
            st.metric('Rentang Tahun', f'{years.min()–{years.max()}' if len(years) > 0 else '-')
    with col3:
        if GENRE_COL:
            n_genre = len(get_all_genres(df_filtered)) - 1
            st.metric('Genre Unik', n_genre)
    with col4:
        if 'GAYA_ILUSTRASI' in df_filtered.columns:
            top_gaya = df_filtered['GAYA_ILUSTRASI'].value_counts().idxmax()
            st.metric('Gaya Dominan', top_gaya)

    st.markdown('---')
    col_a, col_b, col_c = st.columns(3)

    # Distribusi warna
    with col_a:
        st.markdown('<div class="section-title">Warna Dominan (Modul A)</div>', unsafe_allow_html=True)
        if 'WARNA_KATEGORI' in df_filtered.columns:
            vc = df_filtered['WARNA_KATEGORI'].value_counts().reset_index()
            vc.columns = ['warna', 'jumlah']
            vc['persen'] = (vc['jumlah'] / vc['jumlah'].sum() * 100).round(1)
            vc['hex'] = vc['warna'].map(lambda x: WARNA_HEX.get(x, '#cccccc'))
            fig = px.bar(vc, x='warna', y='jumlah',
                         color='warna',
                         color_discrete_map={r['warna']: r['hex'] for _, r in vc.iterrows()},
                         text='persen',
                         labels={'jumlah': 'Jumlah', 'warna': ''})
            fig.update_traces(texttemplate='%{text}%', textposition='outside')
            fig.update_layout(showlegend=False, height=300,
                              margin=dict(t=10, b=10, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

    # Distribusi typeface
    with col_b:
        st.markdown('<div class="section-title">Kategori Typeface (Modul B)</div>', unsafe_allow_html=True)
        if 'TYPEFACE_KATEGORI' in df_filtered.columns:
            vc = df_filtered['TYPEFACE_KATEGORI'].value_counts().reset_index()
            vc.columns = ['typeface', 'jumlah']
            vc['persen'] = (vc['jumlah'] / vc['jumlah'].sum() * 100).round(1)
            vc['hex'] = vc['typeface'].map(lambda x: TYPEFACE_COLORS.get(x, '#cccccc'))
            fig = px.bar(vc, x='typeface', y='jumlah',
                         color='typeface',
                         color_discrete_map={r['typeface']: r['hex'] for _, r in vc.iterrows()},
                         text='persen',
                         labels={'jumlah': 'Jumlah', 'typeface': ''})
            fig.update_traces(texttemplate='%{text}%', textposition='outside')
            fig.update_layout(showlegend=False, height=300,
                              margin=dict(t=10, b=10, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

    # Distribusi gaya ilustrasi
    with col_c:
        st.markdown('<div class="section-title">Gaya Ilustrasi (Modul C)</div>', unsafe_allow_html=True)
        if 'GAYA_ILUSTRASI' in df_filtered.columns:
            vc = df_filtered['GAYA_ILUSTRASI'].value_counts().reset_index()
            vc.columns = ['gaya', 'jumlah']
            vc['persen'] = (vc['jumlah'] / vc['jumlah'].sum() * 100).round(1)
            vc['hex'] = vc['gaya'].map(lambda x: GAYA_COLORS.get(x, '#cccccc'))
            fig = px.bar(vc, y='gaya', x='jumlah',
                         orientation='h',
                         color='gaya',
                         color_discrete_map={r['gaya']: r['hex'] for _, r in vc.iterrows()},
                         text='persen',
                         labels={'jumlah': 'Jumlah', 'gaya': ''})
            fig.update_traces(texttemplate='%{text}%', textposition='outside')
            fig.update_layout(showlegend=False, height=300,
                              margin=dict(t=10, b=10, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

    # Tren per tahun
    if YEAR_COL and 'WARNA_KATEGORI' in df_filtered.columns:
        st.markdown('<div class="section-title">Tren Warna Dominan per Tahun</div>',
                    unsafe_allow_html=True)
        df_yr = df_filtered[df_filtered[YEAR_COL] > 0].copy()
        tren = df_yr.groupby([YEAR_COL, 'WARNA_KATEGORI']).size().reset_index(name='n')
        color_map = {w: WARNA_HEX.get(w, '#cccccc') for w in tren['WARNA_KATEGORI'].unique()}
        fig = px.area(tren, x=YEAR_COL, y='n', color='WARNA_KATEGORI',
                      color_discrete_map=color_map,
                      labels={YEAR_COL: 'Tahun', 'n': 'Jumlah Buku', 'WARNA_KATEGORI': 'Warna'})
        fig.update_layout(height=300, margin=dict(t=10, b=10, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# HALAMAN 2: MODUL A — WARNA
# =============================================================================
elif page == '🎨 Modul A — Warna':
    st.markdown('<div class="main-header">Modul A — Analisis Warna</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">K-Means k=5 pada ruang warna HSV · '
        'Rujukan: Arnold & Tilton (2023) *Distant Viewing*</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="section-title">Distribusi Warna Dominan</div>', unsafe_allow_html=True)
        if 'WARNA_KATEGORI' in df_filtered.columns:
            vc = df_filtered['WARNA_KATEGORI'].value_counts().reset_index()
            vc.columns = ['warna', 'jumlah']
            vc['persen'] = (vc['jumlah'] / vc['jumlah'].sum() * 100).round(1)
            vc['hex'] = vc['warna'].map(lambda x: WARNA_HEX.get(x, '#cccccc'))
            fig = px.pie(vc, names='warna', values='jumlah',
                         color='warna',
                         color_discrete_map={r['warna']: r['hex'] for _, r in vc.iterrows()},
                         hole=0.4)
            fig.update_traces(texttemplate='%{label}<br>%{percent:.1%}')
            fig.update_layout(height=380, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Kecerahan vs Saturasi</div>', unsafe_allow_html=True)
        if 'BRIGHTNESS_MEAN' in df_filtered.columns and 'SATURATION_MEAN' in df_filtered.columns:
            df_sc = df_filtered.dropna(subset=['BRIGHTNESS_MEAN', 'SATURATION_MEAN']).copy()
            df_sc['warna_hex'] = df_sc['WARNA_KATEGORI'].map(
                lambda x: WARNA_HEX.get(str(x), '#cccccc')
            ) if 'WARNA_KATEGORI' in df_sc.columns else '#3498db'
            fig = px.scatter(
                df_sc.sample(min(500, len(df_sc)), random_state=42),
                x='BRIGHTNESS_MEAN', y='SATURATION_MEAN',
                color='WARNA_KATEGORI' if 'WARNA_KATEGORI' in df_sc.columns else None,
                color_discrete_map=WARNA_HEX,
                labels={
                    'BRIGHTNESS_MEAN': 'Kecerahan (Value mean)',
                    'SATURATION_MEAN': 'Saturasi (Saturation mean)',
                    'WARNA_KATEGORI': 'Warna'
                },
                opacity=0.6,
                hover_data=[TITLE_COL] if TITLE_COL else None,
            )
            fig.update_layout(height=380, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

    # Palet K-Means sample covers
    st.markdown('<div class="section-title">Contoh Palet K-Means (sampel acak)</div>',
                unsafe_allow_html=True)
    warna_cols  = [f'WARNA_{i}' for i in range(1, 6)]
    pct_cols    = [f'WARNA_PCT_{i}' for i in range(1, 6)]
    hex_cols    = [f'WARNA_HEX_{i}' for i in range(1, 6)]

    has_palette = all(c in df_filtered.columns for c in warna_cols[:1])

    if has_palette and IMG_COL:
        sample = df_filtered.dropna(subset=[IMG_COL]).sample(
            min(8, len(df_filtered)), random_state=42
        )
        cols = st.columns(min(4, len(sample)))
        for i, (_, row) in enumerate(sample.iterrows()):
            with cols[i % 4]:
                img_path = os.path.join(COVERS_DIR, str(row[IMG_COL]))
                if os.path.exists(img_path):
                    st.image(img_path, use_column_width=True)
                title_short = str(row.get(TITLE_COL, ''))[:25] if TITLE_COL else ''

                # Palet strip
                fig_pal, ax_pal = plt.subplots(figsize=(3, 0.4))
                ax_pal.axis('off')
                cumul = 0
                for rank in range(1, 6):
                    pct = float(row.get(f'WARNA_PCT_{rank}', 0) or 0)
                    hex_c = str(row.get(f'WARNA_HEX_{rank}', '#cccccc') or '#cccccc')
                    lbl   = str(row.get(f'WARNA_{rank}', '') or '')
                    bar = mpatches.Rectangle(
                        (cumul / 100, 0), pct / 100, 1,
                        facecolor=hex_c, linewidth=0
                    )
                    ax_pal.add_patch(bar)
                    if pct > 8:
                        ax_pal.text(
                            (cumul + pct / 2) / 100, 0.5,
                            f'{pct:.0f}%', ha='center', va='center',
                            fontsize=5, color='white',
                            fontweight='bold'
                        )
                    cumul += pct
                ax_pal.set_xlim(0, 1)
                ax_pal.set_ylim(0, 1)
                plt.tight_layout(pad=0)
                st.pyplot(fig_pal, use_container_width=True)
                plt.close(fig_pal)
                st.markdown(f'<div class="cover-caption">{title_short}</div>',
                            unsafe_allow_html=True)


# =============================================================================
# HALAMAN 3: MODUL B — TYPEFACE
# =============================================================================
elif page == '🔤 Modul B — Typeface':
    st.markdown('<div class="main-header">Modul B — Analisis Typeface</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">EasyOCR + KNN · '
        'Terminologi: *typeface* = entitas desain (Lupton 2024, hal. 54–57) · '
        '6 kategori: serif, sans-serif, slab-serif, script, display, monospace</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="section-title">Distribusi Kategori Typeface</div>',
                    unsafe_allow_html=True)
        if 'TYPEFACE_KATEGORI' in df_filtered.columns:
            vc = df_filtered['TYPEFACE_KATEGORI'].value_counts().reset_index()
            vc.columns = ['typeface', 'jumlah']
            vc['persen'] = (vc['jumlah'] / vc['jumlah'].sum() * 100).round(1)
            vc['hex'] = vc['typeface'].map(lambda x: TYPEFACE_COLORS.get(x, '#cccccc'))
            fig = px.bar(vc, x='typeface', y='jumlah',
                         color='typeface',
                         color_discrete_map={r['typeface']: r['hex'] for _, r in vc.iterrows()},
                         text='persen',
                         labels={'jumlah': 'Jumlah', 'typeface': 'Kategori Typeface'})
            fig.update_traces(texttemplate='%{text}%', textposition='outside')
            fig.update_layout(showlegend=False, height=350,
                              margin=dict(t=20, b=20, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Confidence & Coverage Teks</div>',
                    unsafe_allow_html=True)
        if 'TYPEFACE_CONFIDENCE' in df_filtered.columns and 'TEKS_COVERAGE' in df_filtered.columns:
            df_tc = df_filtered.dropna(subset=['TYPEFACE_CONFIDENCE', 'TEKS_COVERAGE'])
            fig = px.scatter(
                df_tc.sample(min(500, len(df_tc)), random_state=42),
                x='TEKS_COVERAGE', y='TYPEFACE_CONFIDENCE',
                color='TYPEFACE_KATEGORI' if 'TYPEFACE_KATEGORI' in df_tc.columns else None,
                color_discrete_map=TYPEFACE_COLORS,
                labels={
                    'TEKS_COVERAGE': 'Coverage teks (proporsi area)',
                    'TYPEFACE_CONFIDENCE': 'Confidence KNN',
                    'TYPEFACE_KATEGORI': 'Typeface'
                },
                opacity=0.6,
                hover_data=[TITLE_COL] if TITLE_COL else None,
            )
            fig.update_layout(height=350, margin=dict(t=20, b=20, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

    # Typeface per genre
    if GENRE_COL and 'TYPEFACE_KATEGORI' in df_filtered.columns:
        st.markdown('<div class="section-title">Typeface per Genre</div>', unsafe_allow_html=True)
        genres_list = [g for g in get_all_genres(df) if g != 'Semua'][:10]
        heat_data = {}
        for g in genres_list:
            sub = get_books_for_genre(df_filtered, g)
            if len(sub) > 0:
                heat_data[g] = sub['TYPEFACE_KATEGORI'].value_counts(normalize=True) * 100

        if heat_data:
            heat_df = pd.DataFrame(heat_data).fillna(0).T
            fig = px.imshow(
                heat_df,
                color_continuous_scale='Blues',
                labels={'color': '% buku'},
                text_auto='.1f',
            )
            fig.update_layout(height=350, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# HALAMAN 4: MODUL C — ILUSTRASI
# =============================================================================
elif page == '🖼️ Modul C — Ilustrasi':
    st.markdown('<div class="main-header">Modul C — Analisis Ilustrasi</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">YOLOv8n · DETR ResNet-50 (Distant Viewing 2.4) · '
        'CLIP ViT-B/32 zero-shot · 6 label gaya yang direvisi</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="section-title">Distribusi Gaya Ilustrasi (CLIP)</div>',
                    unsafe_allow_html=True)
        if 'GAYA_ILUSTRASI' in df_filtered.columns:
            vc = df_filtered['GAYA_ILUSTRASI'].value_counts().reset_index()
            vc.columns = ['gaya', 'jumlah']
            vc['persen'] = (vc['jumlah'] / vc['jumlah'].sum() * 100).round(1)
            vc['hex'] = vc['gaya'].map(lambda x: GAYA_COLORS.get(x, '#cccccc'))
            fig = px.bar(vc, y='gaya', x='jumlah',
                         orientation='h',
                         color='gaya',
                         color_discrete_map={r['gaya']: r['hex'] for _, r in vc.iterrows()},
                         text='persen',
                         labels={'jumlah': 'Jumlah', 'gaya': 'Gaya Ilustrasi'})
            fig.update_traces(texttemplate='%{text}%', textposition='outside')
            fig.update_layout(showlegend=False, height=350,
                              margin=dict(t=20, b=20, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Ada Figur Manusia (YOLO vs DETR)</div>',
                    unsafe_allow_html=True)
        if 'YOLO_ADA_MANUSIA' in df_filtered.columns and 'DETR_ADA_MANUSIA' in df_filtered.columns:
            def bool_str(val):
                if str(val).lower() in ('true', '1', 'yes'):
                    return True
                return False

            df_m = df_filtered.copy()
            df_m['YOLO_ADA_MANUSIA'] = df_m['YOLO_ADA_MANUSIA'].apply(bool_str)
            df_m['DETR_ADA_MANUSIA']  = df_m['DETR_ADA_MANUSIA'].apply(bool_str)

            n_total  = len(df_m)
            y_yes    = df_m['YOLO_ADA_MANUSIA'].sum()
            d_yes    = df_m['DETR_ADA_MANUSIA'].sum()
            konsisten = (df_m['YOLO_ADA_MANUSIA'] == df_m['DETR_ADA_MANUSIA']).sum()

            comp_data = pd.DataFrame({
                'Model': ['YOLOv8n', 'DETR ResNet-50'],
                'Ada Manusia': [y_yes, d_yes],
                'Tidak Ada': [n_total - y_yes, n_total - d_yes],
            })
            fig = go.Figure(data=[
                go.Bar(name='Ada Manusia', x=comp_data['Model'], y=comp_data['Ada Manusia'],
                       marker_color='#e74c3c'),
                go.Bar(name='Tidak Ada', x=comp_data['Model'], y=comp_data['Tidak Ada'],
                       marker_color='#bdc3c7'),
            ])
            fig.update_layout(
                barmode='stack', height=300,
                margin=dict(t=20, b=20, l=0, r=0),
                legend=dict(orientation='h', yanchor='bottom', y=1.02)
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                f'Konsistensi YOLO–DETR: {konsisten}/{n_total} '
                f'({konsisten/n_total*100:.1f}%)'
            )

    # Jumlah objek YOLO
    if 'YOLO_N_OBJEK' in df_filtered.columns:
        st.markdown('<div class="section-title">Distribusi Jumlah Objek Terdeteksi (YOLOv8n)</div>',
                    unsafe_allow_html=True)
        df_obj = df_filtered['YOLO_N_OBJEK'].dropna()
        fig = px.histogram(df_obj, nbins=15,
                           labels={'value': 'Jumlah Objek', 'count': 'Frekuensi'},
                           color_discrete_sequence=['#3498db'])
        fig.update_layout(height=280, margin=dict(t=10, b=10, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    # Gaya per genre heatmap
    if GENRE_COL and 'GAYA_ILUSTRASI' in df_filtered.columns:
        st.markdown('<div class="section-title">Gaya Ilustrasi per Genre</div>',
                    unsafe_allow_html=True)
        genres_list = [g for g in get_all_genres(df) if g != 'Semua'][:10]
        heat_data = {}
        for g in genres_list:
            sub = get_books_for_genre(df_filtered, g)
            if len(sub) > 5:
                heat_data[g] = sub['GAYA_ILUSTRASI'].value_counts(normalize=True) * 100
        if heat_data:
            heat_df = pd.DataFrame(heat_data).fillna(0).T
            fig = px.imshow(
                heat_df,
                color_continuous_scale='Oranges',
                labels={'color': '% buku'},
                text_auto='.1f',
            )
            fig.update_layout(height=350, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# HALAMAN 5: JELAJAH BUKU
# =============================================================================
elif page == '📖 Jelajah Buku':
    st.markdown('<div class="main-header">Jelajah Buku</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Telusuri setiap sampul beserta hasil analisis ketiga modul.</div>',
        unsafe_allow_html=True
    )

    # Search
    query = st.text_input('🔍 Cari judul atau penulis', placeholder='mis. Pramoedya, Laskar...')
    if query and TITLE_COL:
        mask = (
            df_filtered[TITLE_COL].str.contains(query, case=False, na=False) |
            (df_filtered[AUTHOR_COL].str.contains(query, case=False, na=False)
             if AUTHOR_COL else False)
        )
        df_show = df_filtered[mask].copy()
    else:
        df_show = df_filtered.copy()

    st.caption(f'{len(df_show)} buku ditemukan')

    # Pagination
    PAGE_SIZE = 20
    n_pages = max(1, (len(df_show) - 1) // PAGE_SIZE + 1)
    page_num = st.selectbox('Halaman', range(1, n_pages + 1)) if n_pages > 1 else 1
    df_page = df_show.iloc[(page_num - 1) * PAGE_SIZE: page_num * PAGE_SIZE]

    # Grid tampilan
    COLS = 4
    rows = [df_page.iloc[i:i + COLS] for i in range(0, len(df_page), COLS)]

    for row_df in rows:
        cols = st.columns(COLS)
        for col, (_, book) in zip(cols, row_df.iterrows()):
            with col:
                # Gambar
                if IMG_COL:
                    img_path = os.path.join(COVERS_DIR, str(book.get(IMG_COL, '')))
                    if os.path.exists(img_path):
                        st.image(img_path, use_column_width=True)
                    else:
                        st.markdown('*(tidak ada gambar)*')

                # Judul & penulis
                title_str  = str(book.get(TITLE_COL, ''))[:50] if TITLE_COL else ''
                author_str = str(book.get(AUTHOR_COL, ''))[:30] if AUTHOR_COL else ''
                year_str   = str(int(book.get(YEAR_COL, 0))) if YEAR_COL else ''

                st.markdown(
                    f'**{title_str}**  \n'
                    f'<small>{author_str} · {year_str}</small>',
                    unsafe_allow_html=True
                )

                # Badge hasil analisis
                warna = book.get('WARNA_KATEGORI', '')
                tf    = book.get('TYPEFACE_KATEGORI', '')
                gaya  = book.get('GAYA_ILUSTRASI', '')
                if warna or tf or gaya:
                    badges = ' · '.join(filter(None, [
                        f'🎨 {warna}' if warna else '',
                        f'🔤 {tf}' if tf else '',
                        f'🖼 {gaya}' if gaya else '',
                    ]))
                    st.markdown(f'<small style="color:#6c757d">{badges}</small>',
                                unsafe_allow_html=True)

                # Palet warna mini
                has_palette = 'WARNA_HEX_1' in book
                if has_palette:
                    cols_pal = []
                    for rank in range(1, 6):
                        hex_c = str(book.get(f'WARNA_HEX_{rank}', '') or '')
                        pct   = float(book.get(f'WARNA_PCT_{rank}', 0) or 0)
                        if hex_c and pct > 0:
                            cols_pal.append((hex_c, pct))

                    if cols_pal:
                        fig_pal, ax_pal = plt.subplots(figsize=(2, 0.25))
                        ax_pal.axis('off')
                        cumul = 0
                        for hex_c, pct in cols_pal:
                            bar = mpatches.Rectangle(
                                (cumul / 100, 0), pct / 100, 1,
                                facecolor=hex_c, linewidth=0
                            )
                            ax_pal.add_patch(bar)
                            if pct > 12:
                                ax_pal.text(
                                    (cumul + pct / 2) / 100, 0.5,
                                    f'{pct:.0f}%', ha='center', va='center',
                                    fontsize=4, color='white', fontweight='bold'
                                )
                            cumul += pct
                        ax_pal.set_xlim(0, 1)
                        ax_pal.set_ylim(0, 1)
                        plt.tight_layout(pad=0)
                        st.pyplot(fig_pal, use_container_width=True)
                        plt.close(fig_pal)

                st.markdown('---')
