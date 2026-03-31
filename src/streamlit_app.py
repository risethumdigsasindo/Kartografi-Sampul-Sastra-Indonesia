"""
Analisis Visual Sampul Sastra Indonesia
Fokus: Analisis Warna (Modul A)
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image
import os, re
from collections import Counter
from sklearn.cluster import KMeans
import cv2

def extract_palette_with_percent(image_path, k=5):
    try:
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (100, 100))

        pixels = img.reshape(-1, 3)

        kmeans = KMeans(n_clusters=k, n_init=10)
        labels = kmeans.fit_predict(pixels)

        colors = kmeans.cluster_centers_.astype(int)

        # hitung persentase
        counts = np.bincount(labels)
        percents = counts / counts.sum()

        palette = []
        for color, p in zip(colors, percents):
            hex_color = "#{:02x}{:02x}{:02x}".format(*color)
            palette.append((hex_color, float(p)))

        # sort dari paling dominan
        palette = sorted(palette, key=lambda x: x[1], reverse=True)

        return palette

    except:
        return None
# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
COVER_DIR   = "covers"          # folder gambar sampul
DATA_PATH   = "src/data.csv"        # CSV hasil analisis
PAGE_TITLE  = "Analisis Visual Sampul Sastra Indonesia"
MAX_COVERS  = 48                # grid maks per halaman

WARNA_HEX = {
    "Merah"              : "#e63946",
    "Oranye"             : "#f4a261",
    "Cokelat"            : "#8d5524",   # baru (dipisah dari oranye)
    "Kuning"             : "#f4d35e",   # termasuk emas
    "Hijau"              : "#2a9d8f",   # termasuk lime
    "Toska"              : "#00b4d8",
    "Biru"               : "#4895ef",
    "Ungu"               : "#7209b7",   # termasuk magenta
    "Merah Muda (Pink)"  : "#ff8fab",
    "Hitam"              : "#1a1a1a",
    "Abu-abu"            : "#adb5bd",
    "Putih"              : "#f8f9fa",
    "Lainnya"            : "#dddddd",
}
WARNA_ORDER = list(WARNA_HEX.keys())

# ─────────────────────────────────────────────────────────────────────────────
# PAGE SETUP
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .cover-card {border-radius:8px; overflow:hidden; box-shadow:0 2px 8px #0002;}
  .palette-strip {height:24px; border-radius:4px; margin:4px 0;}
  .metric-box {background:#f8f9fa; border-radius:8px; padding:12px; text-align:center;}
  h1 {font-family: Georgia, serif;}
  .stSelectbox label, .stSlider label {font-size:13px;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        return None
    df = pd.read_csv(DATA_PATH, encoding="utf-8")
    # numeric cleanup
    df["RATING_AVG"]   = pd.to_numeric(df["RATING_AVG"],   errors="coerce")
    df["TAHUN_TERBIT"] = pd.to_numeric(df["TAHUN_TERBIT"], errors="coerce")
    df["warna_h"]      = pd.to_numeric(df["warna_h"],      errors="coerce")
    df["warna_s"]      = pd.to_numeric(df["warna_s"],      errors="coerce")
    df["warna_v"]      = pd.to_numeric(df["warna_v"],      errors="coerce")
    df["warna_r"]      = pd.to_numeric(df["warna_r"],      errors="coerce")
    df["warna_g"]      = pd.to_numeric(df["warna_g"],      errors="coerce")
    df["warna_b"]      = pd.to_numeric(df["warna_b"],      errors="coerce")
    df["TOTAL_RATINGS"] = pd.to_numeric(df["TOTAL_RATINGS"], errors="coerce")
    # fill missing warna_kategori
    df["warna_kategori"] = df["warna_kategori"].fillna("Lainnya")
    return df

# --- POPULARITY SCORE ---

    C = df["RATING_AVG"].mean()
    m = df["TOTAL_RATINGS"].quantile(0.75)  # threshold (bisa diubah)

def compute_popularity(row):
    v = row["TOTAL_RATINGS"]
    R = row["RATING_AVG"]

    if pd.isna(v) or pd.isna(R):
        return np.nan

    return (v/(v+m))*R + (m/(v+m))*C

    df["POPULARITY_SCORE"] = df.apply(compute_popularity, axis=1)

def get_cover_path(filename):
    return os.path.join(COVER_DIR, str(filename))

@st.cache_data
def get_all_genres(df):
    genres = set()
    df["GENRES"].dropna().str.split(",").apply(
        lambda x: [genres.add(g.strip()) for g in x]
    )
    return sorted(genres)

@st.cache_data
def get_all_authors(df):
    return sorted(df["PENULIS"].dropna().unique().tolist())

def hex_to_rgb_tuple(hex_str):
    h = str(hex_str).lstrip("#")
    if len(h) != 6:
        return (170, 170, 170)
    try:
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except:
        return (170, 170, 170)
import colorsys

def hex_to_hsv(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)

def map_to_color_category(hex_color):
    h, s, v = hex_to_hsv(hex_color)
    h = h * 360

    # warna gelap & netral dulu
    if v < 0.15:
        return "Hitam"
    elif s < 0.15 and v > 0.85:
        return "Putih"
    elif s < 0.2:
        return "Abu-abu"



    # warna kromatik (berdasarkan hue)
    elif 0 <= h < 20 or 340 <= h <= 360:
        return "Merah"
    elif 20 <= h < 35:
        return "Oranye"
    elif 35 <= h < 50:
        return "Cokelat"
    elif 50 <= h < 70:
        return "Kuning"
    elif 70 <= h < 160:
        return "Hijau"
    elif 160 <= h < 200:
        return "Toska"
    elif 160 <= h < 260:
        return "Biru"
    elif 260 <= h < 300:
        return "Ungu"
    elif 300 <= h < 345:
        return "Merah Muda (Pink)"

    return "Lainnya"
# ─────────────────────────────────────────────────────────────────────────────
# VISUALISASI HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def make_palette_strip_fig(hex_list, width=4, height=0.4):
    """Render horizontal palette strip dari list hex colors."""
    fig, ax = plt.subplots(figsize=(width, height))
    n = len(hex_list)
    for i, hx in enumerate(hex_list):
        ax.add_patch(plt.Rectangle(
            (i/n, 0), 1/n, 1,
            facecolor=hx, edgecolor="none"
        ))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    fig.patch.set_alpha(0)
    plt.tight_layout(pad=0)
    return fig

def make_donut_chart(counts_dict, title=""):
    """Donut chart distribusi warna."""
    cats   = [k for k in WARNA_ORDER if k in counts_dict and counts_dict[k] > 0]
    vals   = [counts_dict[k] for k in cats]
    colors = [WARNA_HEX[k] for k in cats]
    fig, ax = plt.subplots(figsize=(4, 4))
    wedges, texts, autotexts = ax.pie(
        vals, labels=None, colors=colors,
        autopct="%1.0f%%", startangle=90,
        pctdistance=0.75,
        wedgeprops=dict(width=0.5, edgecolor="white", linewidth=1.5),
    )
    for at in autotexts:
        at.set_fontsize(8); at.set_color("white"); at.set_fontweight("bold")
    if title:
        ax.set_title(title, fontsize=10, fontweight="bold", pad=6)
    handles = [mpatches.Patch(color=WARNA_HEX[k], label=f"{k} ({counts_dict.get(k,0)})")
               for k in cats]
    ax.legend(handles=handles, loc="lower center",
              bbox_to_anchor=(0.5, -0.30), ncol=2, fontsize=7,
              frameon=False)
    fig.tight_layout()
    return fig

def make_bar_chart(df_group, x_col, y_col="warna_kategori",
                   title="", xlabel="", normalize=True):
    """Stacked bar chart warna per x_col."""
    pivot = pd.crosstab(df_group[x_col], df_group[y_col])
    if normalize:
        pivot = pivot.div(pivot.sum(axis=1), axis=0) * 100

    # Only keep categories that exist
    cats_present = [c for c in WARNA_ORDER if c in pivot.columns]
    pivot = pivot[cats_present]

    fig, ax = plt.subplots(figsize=(12, 4))
    bottom = np.zeros(len(pivot))
    for cat in cats_present:
        vals = pivot[cat].values
        ax.bar(pivot.index.astype(str), vals, bottom=bottom,
               color=WARNA_HEX[cat], label=cat, width=0.8)
        bottom += vals

    ax.set_xlabel(xlabel or x_col, fontsize=9)
    ax.set_ylabel("%" if normalize else "n", fontsize=9)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.tick_params(axis="x", rotation=45, labelsize=7)
    ax.tick_params(axis="y", labelsize=8)
    ax.spines[["top","right"]].set_visible(False)
    handles = [mpatches.Patch(color=WARNA_HEX[c], label=c) for c in cats_present]
    ax.legend(handles=handles, bbox_to_anchor=(1.01,1), loc="upper left",
              fontsize=7, frameon=False)
    fig.tight_layout()
    return fig

def make_scatter_hsv(df_sub, color_by="warna_kategori"):
    """Scatter brightness × saturation, colored by warna_kategori."""
    df_ok = df_sub.dropna(subset=["warna_v","warna_s","warna_kategori"])
    fig, ax = plt.subplots(figsize=(5, 4))
    for cat, grp in df_ok.groupby("warna_kategori"):
        ax.scatter(grp["warna_v"], grp["warna_s"],
                   c=WARNA_HEX.get(cat,"#888"),
                   s=12, alpha=0.6, linewidths=0, label=cat)
    ax.set_xlabel("Brightness (V)", fontsize=9)
    ax.set_ylabel("Saturation (S)", fontsize=9)
    ax.set_title("Brightness × Saturation\n(setiap titik = 1 buku)", fontsize=9, fontweight="bold")
    ax.tick_params(labelsize=7)
    ax.spines[["top","right"]].set_visible(False)
    ax.legend(fontsize=6, frameon=False, bbox_to_anchor=(1.01,1), loc="upper left")
    fig.tight_layout()
    return fig

def make_rating_bar(df_sub):
    """Rata-rata rating per warna_kategori."""
    rby = (df_sub.dropna(subset=["RATING_AVG","warna_kategori"])
           .groupby("warna_kategori")["RATING_AVG"]
           .agg(mean="mean", se=lambda x: x.std()/np.sqrt(len(x)), n="count")
           .reset_index()
           .sort_values("mean", ascending=False))
    rby = rby[rby["warna_kategori"].isin(WARNA_ORDER)]

    fig, ax = plt.subplots(figsize=(6, 3.5))
    bars = ax.bar(
        rby["warna_kategori"], rby["mean"],
        color=[WARNA_HEX.get(k,"#aaa") for k in rby["warna_kategori"]],
        edgecolor="white", linewidth=0.8,
        yerr=rby["se"], capsize=3,
        error_kw=dict(elinewidth=1, capthick=1, ecolor="#555")
    )
    global_m = df_sub["RATING_AVG"].mean()
    ax.axhline(global_m, ls="--", lw=1.2, color="#333",
               label=f"rata-rata keseluruhan ({global_m:.2f})")
    ax.set_ylim(rby["mean"].min() - 0.15, rby["mean"].max() + 0.15)
    ax.set_ylabel("Rata-rata Rating", fontsize=9)
    ax.set_title("Rating Pembaca per Warna Dominan Sampul\n(error bar = SE)",
                 fontsize=9, fontweight="bold")
    ax.tick_params(axis="x", rotation=35, labelsize=7)
    ax.tick_params(axis="y", labelsize=8)
    ax.spines[["top","right"]].set_visible(False)
    ax.legend(fontsize=7, frameon=False)
    for b, row in zip(bars, rby.itertuples()):
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.01,
                f"n={row.n}", ha="center", fontsize=6, color="#555")
    fig.tight_layout()
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────────────────
df = load_data()

@st.cache_data(show_spinner=True)
def load_palettes(df):
    palette_dict = {}
    
    for idx, row in df.iterrows():
        path = get_cover_path(row["NAMA_FILE_GAMBAR"])
        
        if os.path.exists(path):
            palette = extract_palette_with_percent(path)
            palette_dict[idx] = palette
        else:
            palette_dict[idx] = None
    
    return palette_dict

palette_dict = load_palettes(df)
new_categories = []

for idx in df.index:
    palette = palette_dict.get(idx)
    if palette:
        dominant_hex = palette[0][0]
        cat = map_to_color_category(dominant_hex)
    else:
        cat = "Lainnya"
    new_categories.append(cat)

df["warna_kategori"] = new_categories
if df is None:
    st.error("⚠️ File `src/data.csv` tidak ditemukan di root repositori.")
    st.stop()

all_genres  = get_all_genres(df)
all_authors = get_all_authors(df)

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Di bawah ini merupakan filter untuk membantu menginterpretasi data:")
    # TAMBAHKAN DI SINI
    st.markdown("---")
    sort_option = st.selectbox(
    "🔃 Urutkan berdasarkan:",
    ["Judul (A–Z)", "Rating Tertinggi", "Tahun Terbaru", "Paling Populer"]
    )
    # Search
    q_judul   = st.text_input("🔍 Cari Judul Buku", placeholder="cth: Bumi Manusia")
    q_penulis = st.selectbox("✍️ Penulis",
                              ["(semua penulis)"] + all_authors,
                              index=0)
    q_genre   = st.selectbox("🏷️ Genre",
                              ["(semua genre)"] + all_genres,
                              index=0)
    
    st.markdown("---")
    view_mode = st.radio("Mode Tampilan",
                          ["🖼️ Grid Sampul","📊 Tren Warna per Tahun","📈 Analisis Agregat", "Analisis Genre"],
                          index=0)
    n_covers = st.slider("Maks. sampul ditampilkan (Grid)", 6, MAX_COVERS, 24, 6)

    st.markdown("---")
    st.markdown("#### 📅 Filter Tahun")
    min_y = int(df["TAHUN_TERBIT"].dropna().min())
    max_y = int(df["TAHUN_TERBIT"].dropna().max())
    min_y = max(min_y, 2000)   # default mulai 2000
    sel_tahun = st.slider("Rentang Tahun Terbit",
                           min_value=2000, max_value=2025,
                           value=(2000, 2025), step=1)

    st.markdown("---")
    st.markdown("#### ⭐ Filter Rating")
    sel_rating = st.slider("Rentang Rating (Goodreads)",
                            min_value=1.0, max_value=5.0,
                            value=(1.0, 5.0), step=0.05,
                            format="%.2f")

    st.markdown("---")
    st.markdown("#### 🎨 Filter Warna")
    sel_warna = st.multiselect("Kategori Warna Dominan",
                                WARNA_ORDER,
                                default=[])

# ── FILTER ───────────────────────────────────────────────────────────────────
mask = pd.Series(True, index=df.index)

if q_judul.strip():
    mask &= df["JUDUL"].str.contains(q_judul.strip(), case=False, na=False, regex=False)

if q_penulis != "(semua penulis)":
    mask &= df["PENULIS"].str.contains(q_penulis, case=False, na=False, regex=False)

if q_genre != "(semua genre)":
    mask &= df["GENRES"].str.contains(q_genre, na=False)

mask &= (
    df["TAHUN_TERBIT"].isna() |
    ((df["TAHUN_TERBIT"] >= sel_tahun[0]) & (df["TAHUN_TERBIT"] <= sel_tahun[1]))
)

mask &= (
    df["RATING_AVG"].isna() |
    ((df["RATING_AVG"] >= sel_rating[0]) & (df["RATING_AVG"] <= sel_rating[1]))
)

if sel_warna:
    mask &= df["warna_kategori"].isin(sel_warna)

fdf = df[mask].copy()

# TARUH DI SINI
if sort_option == "Judul (A–Z)":
    fdf = fdf.sort_values("JUDUL", ascending=True, na_position="last")

elif sort_option == "Rating Tertinggi":
    fdf = fdf.sort_values(
        by=["RATING_AVG", "TOTAL_RATINGS"],
        ascending=[False, False],
        na_position="last"
    )

elif sort_option == "Tahun Terbaru":
    fdf = fdf.sort_values(
        by="TAHUN_TERBIT",
        ascending=False,
        na_position="last"
    )

elif sort_option == "Paling Populer":
    fdf = fdf.sort_values(
        by="POPULARITY_SCORE",
        ascending=False,
        na_position="last"
    )

# ── HEADER ───────────────────────────────────────────────────────────────────
st.title("📚 Warna Wajah Sastra Indonesia: Analisis Warna Sampul Buku Sastra Indonesia")

# Metrics row
c1, c2, c3, c4 = st.columns(4)
c1.metric("Jumlah Buku", f"{len(fdf):,}")
c2.metric("Penulis",   f"{fdf['PENULIS'].nunique():,}")
c3.metric("Rata-rata rating", f"{fdf['RATING_AVG'].mean():.2f}" if fdf["RATING_AVG"].notna().any() else "—")
top_w = fdf["warna_kategori"].value_counts().idxmax() if len(fdf) > 0 else "—"
c4.metric("Warna dominan terbanyak", top_w)

st.markdown("---")

if len(fdf) == 0:
    st.warning("Tidak ada buku yang cocok dengan filter yang dipilih.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# VIEW: GRID SAMPUL
# ─────────────────────────────────────────────────────────────────────────────
if view_mode == "🖼️ Grid Sampul":
    # --- Dynamic label ---

    # --- Dynamic label ---
    label_parts = []

    if sort_option:
        label_parts.append(sort_option)

    if q_penulis != "(semua penulis)":
        label_parts.append(f"Penulis: {q_penulis}")

    if q_genre != "(semua genre)":
        label_parts.append(f"Genre: {q_genre}")

    if sel_warna:
        label_parts.append("Warna: " + ", ".join(sel_warna))

    label_parts.append(f"Terbitan Tahun: {sel_tahun[0]}–{sel_tahun[1]}")

    label_text = " ".join(label_parts)

    st.subheader(f"Sampul Buku {label_text}")
    st.caption("⭐: rating · 👥: jumlah pemberi rating · 🔥: popularity · 🎨: warna dominan")

    # GRID
    subset = fdf.head(n_covers)
    cols_per_row = 6
    rows = [subset.iloc[i:i+cols_per_row] for i in range(0, len(subset), cols_per_row)]

    subset = fdf.head(n_covers)
    cols_per_row = 6
    rows = [subset.iloc[i:i+cols_per_row] for i in range(0, len(subset), cols_per_row)]

    for row_df in rows:
        cols = st.columns(cols_per_row)
        for col, (_, book) in zip(cols, row_df.iterrows()):
            with col:
                img_path = get_cover_path(book["NAMA_FILE_GAMBAR"])
                if os.path.exists(img_path):
                    try:
                        img = Image.open(img_path)
                        st.image(img, use_container_width=True)
                    except:
                        st.markdown("*(sampul tidak dapat dibuka)*")
                else:
                    # Placeholder berwarna sesuai warna dominan
                    hex_c = str(book.get("warna_hex_dominan","#cccccc"))
                    st.markdown(
                        f'<div style="background:{hex_c};height:120px;'
                        f'border-radius:6px;display:flex;align-items:center;'
                        f'justify-content:center;color:white;font-size:20px;">'
                        f'Sampul</div>',
                        unsafe_allow_html=True
                    )
                palette = palette_dict.get(book.name)

                # Palette strip
                palette = palette_dict.get(book.name)

                if palette:
                    bars = ""
                    for hex_color, pct in palette:
                        width = pct * 100
                        percent_text = f"{pct*100:.1f}%"    
                        cat = map_to_color_category(hex_color)
                        bars += f'''
                <div title="{cat} | {percent_text}"
                    style="width:{width}%;height:18px;background:{hex_color};cursor:pointer;">
                </div>
                '''
                    bars_html = f"""
                <div style="display:flex;border-radius:3px;overflow:hidden;margin:4px 0;position:relative;z-index:10;">
                {bars}
                </div>
                """

                    st.markdown(bars_html, unsafe_allow_html=True)
                        
                else:
                    # fallback lama
                    hex_c = str(book.get("warna_hex_dominan", "#cccccc"))
                    st.markdown(
                        f'<div style="height:10px;background:{hex_c};border-radius:3px;"></div>',
                        unsafe_allow_html=True
                    )

                # Caption
                judul  = str(book["JUDUL"])[:30]
                rating = book.get("RATING_AVG")
                tahun  = int(book["TAHUN_TERBIT"]) if pd.notna(book.get("TAHUN_TERBIT")) else "—"
                warna  = str(book.get("warna_kategori","—"))
                pop = book.get("POPULARITY_SCORE")
                p_str = f"🔥 {pop:.2f}" if pd.notna(pop) else "🔥 —"
                r_str  = f"⭐ {rating:.2f}/5" if pd.notna(rating) else "⭐ —"
                total = book.get("TOTAL_RATINGS")
                t_str = f"👥 {int(total):,}" if pd.notna(total) else "👥 —"
                st.caption(f"**{judul}**  \n⭐ {rating:.2f} · {tahun}  \n{t_str}  \n🔥 {pop:.2f}  \n🎨 {warna}")

    if len(fdf) > n_covers:
        st.info(f"Menampilkan {n_covers} dari {len(fdf)} buku. Perkecil filter untuk hasil lebih spesifik.")

# ─────────────────────────────────────────────────────────────────────────────
# VIEW: TREN WARNA PER TAHUN
# ─────────────────────────────────────────────────────────────────────────────
elif view_mode == "📊 Tren Warna per Tahun":
    st.subheader("Tren Distribusi Warna Sampul per Tahun Terbit")
    st.caption("Menampilkan distribusi palet warna dominan dalam kurun tahun yang dipilih. "
               "Bukan daftar sampul — melainkan persentase kategori warna per tahun.")

    df_yr = fdf.dropna(subset=["TAHUN_TERBIT","warna_kategori"]).copy()
    df_yr["TAHUN_TERBIT"] = df_yr["TAHUN_TERBIT"].astype(int)

    if len(df_yr) < 5:
        st.warning("Terlalu sedikit data untuk menampilkan tren. Perluas filter tahun atau warna.")
    else:
        # ── Stacked bar chart ─────────────────────────────────────────────
        fig_bar = make_bar_chart(
            df_yr, x_col="TAHUN_TERBIT",
            title=f"Komposisi Warna Dominan Sampul per Tahun ({sel_tahun[0]}–{sel_tahun[1]})",
            xlabel="Tahun Terbit",
            normalize=True
        )
        st.pyplot(fig_bar)

        # ── Line chart: persentase warna tertentu ─────────────────────────
        st.markdown("#### Tren Tiap Kategori Warna (% per tahun)")
        pivot = pd.crosstab(df_yr["TAHUN_TERBIT"], df_yr["warna_kategori"])
        pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

        cats_sel = st.multiselect(
            "Tampilkan kategori warna:",
            [c for c in WARNA_ORDER if c in pivot_pct.columns],
            default=[c for c in ["Merah","Biru","Abu-abu/Putih"] if c in pivot_pct.columns]
        )
        if cats_sel:
            fig_line, ax = plt.subplots(figsize=(12, 4))
            for cat in cats_sel:
                ax.plot(pivot_pct.index, pivot_pct[cat],
                        color=WARNA_HEX.get(cat,"#888"),
                        linewidth=2, marker="o", markersize=3.5, label=cat)
            ax.set_xlabel("Tahun", fontsize=9)
            ax.set_ylabel("%", fontsize=9)
            ax.set_title("Persentase Warna per Tahun", fontsize=10, fontweight="bold")
            ax.legend(fontsize=8, frameon=False, bbox_to_anchor=(1.01,1), loc="upper left")
            ax.tick_params(axis="x", rotation=45, labelsize=7)
            ax.spines[["top","right"]].set_visible(False)
            ax.grid(axis="y", alpha=0.25, ls="--")
            fig_line.tight_layout()
            st.pyplot(fig_line)

        # ── Rata-rata hex warna per tahun (color strip) ───────────────────
        st.markdown("#### Rata-rata Warna Dominan per Tahun")
        st.caption("Setiap strip = rata-rata RGB dari semua sampul yang terbit tahun tersebut.")

        df_rgb = fdf.dropna(subset=["TAHUN_TERBIT","warna_r","warna_g","warna_b"]).copy()
        df_rgb["TAHUN_TERBIT"] = df_rgb["TAHUN_TERBIT"].astype(int)
        avg_rgb = (df_rgb.groupby("TAHUN_TERBIT")[["warna_r","warna_g","warna_b"]]
                   .mean().round().astype(int).reset_index())
        avg_rgb = avg_rgb[(avg_rgb["TAHUN_TERBIT"] >= sel_tahun[0]) &
                          (avg_rgb["TAHUN_TERBIT"] <= sel_tahun[1])]

        if len(avg_rgb) > 0:
            hex_list = [
                "#{:02x}{:02x}{:02x}".format(r["warna_r"], r["warna_g"], r["warna_b"])
                for _, r in avg_rgb.iterrows()
            ]
            fig_strip = make_palette_strip_fig(hex_list, width=14, height=0.7)
            st.pyplot(fig_strip)

            # Label tahun di bawah strip
            year_labels = avg_rgb["TAHUN_TERBIT"].tolist()
            n_labels = min(12, len(year_labels))
            step     = max(1, len(year_labels)//n_labels)
            labels_to_show = year_labels[::step]
            st.caption("  |  ".join([str(y) for y in labels_to_show]))

        # ── Tabel ringkasan ───────────────────────────────────────────────
        with st.expander("📋 Tabel Data Tren Warna"):
            pivot_display = pivot_pct.round(1)
            st.dataframe(pivot_display.style.background_gradient(cmap="YlOrRd", axis=None),
                         use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# VIEW: ANALISIS AGREGAT
# ─────────────────────────────────────────────────────────────────────────────
elif view_mode == "📈 Analisis Agregat":
    st.subheader("Analisis Agregat Warna — Hasil Filter")

    col_a, col_b = st.columns([1, 1.4])

    with col_a:
        # Donut
        counts = fdf["warna_kategori"].value_counts().to_dict()
        fig_donut = make_donut_chart(counts, title="Distribusi Kategori Warna")
        st.pyplot(fig_donut)

        # Palette strip: all dominant colors in filter
        hex_vals = fdf["warna_hex_dominan"].dropna().tolist()
        # Sort by hue
        def hue_sort_key(h):
            rgb = hex_to_rgb_tuple(h)
            import colorsys
            return colorsys.rgb_to_hsv(rgb[0]/255,rgb[1]/255,rgb[2]/255)[0]
        hex_sorted = sorted(hex_vals, key=hue_sort_key)
        if hex_sorted:
            st.markdown("**Semua warna dominan (urut hue):**")
            fig_all = make_palette_strip_fig(hex_sorted, width=10, height=0.5)
            st.pyplot(fig_all)

    with col_b:
        # Scatter HSV
        fig_sc = make_scatter_hsv(fdf)
        st.pyplot(fig_sc)

    st.markdown("---")

    # Rating per warna
    col_c, col_d = st.columns(2)
    with col_c:
        fig_rating = make_rating_bar(fdf)
        st.pyplot(fig_rating)

    with col_d:
        # Warna per genre (top 8)
        df_genre_exploded = fdf.copy()
        df_genre_exploded["GENRE_SINGLE"] = df_genre_exploded["GENRES"].str.split(",")
        df_genre_exploded = df_genre_exploded.explode("GENRE_SINGLE")
        df_genre_exploded["GENRE_SINGLE"] = df_genre_exploded["GENRE_SINGLE"].str.strip()
        top_genres = df_genre_exploded["GENRE_SINGLE"].value_counts().head(8).index
        df_top = df_genre_exploded[df_genre_exploded["GENRE_SINGLE"].isin(top_genres)]

        if len(df_top) > 5:
            pivot_g = pd.crosstab(df_top["GENRE_SINGLE"], df_top["warna_kategori"])
            pivot_g = pivot_g.div(pivot_g.sum(axis=1), axis=0) * 100
            cats_g  = [c for c in WARNA_ORDER if c in pivot_g.columns]
            pivot_g = pivot_g[cats_g]

            fig_g, ax_g = plt.subplots(figsize=(6, 4))
            bottom = np.zeros(len(pivot_g))
            for cat in cats_g:
                vals = pivot_g[cat].values
                ax_g.barh(pivot_g.index, vals, left=bottom,
                          color=WARNA_HEX[cat], label=cat, height=0.7)
                bottom += vals
            ax_g.set_xlabel("%", fontsize=9)
            ax_g.set_title("Warna Dominan per Genre (top 8)",
                           fontsize=9, fontweight="bold")
            ax_g.tick_params(axis="y", labelsize=7)
            ax_g.spines[["top","right"]].set_visible(False)
            handles = [mpatches.Patch(color=WARNA_HEX[c], label=c) for c in cats_g]
            ax_g.legend(handles=handles, fontsize=6, frameon=False,
                        bbox_to_anchor=(1.01,1), loc="upper left")
            fig_g.tight_layout()
            st.pyplot(fig_g)

    st.markdown("---")

    # Raw data table
    with st.expander("📋 Tabel Data (hasil filter)"):
        cols_show = ["JUDUL","PENULIS","RATING_AVG","TAHUN_TERBIT",
                     "GENRES","warna_kategori","warna_hex_dominan"]
        st.dataframe(
            fdf[cols_show].rename(columns={
                "JUDUL":"Judul","PENULIS":"Penulis",
                "RATING_AVG":"Rating","TAHUN_TERBIT":"Tahun",
                "GENRES":"Genre","warna_kategori":"Warna",
                "warna_hex_dominan":"Hex"
            }).sort_values("Rating", ascending=False),
            use_container_width=True
        )
        st.download_button(
            "⬇️ Download CSV hasil filter",
            data=fdf.to_csv(index=False, encoding="utf-8"),
            file_name="hasil_filter_warna.csv",
            mime="text/csv"
        )

# ─────────────────────────────────────────────────────────────────────────────
# VIEW: ANALISIS GENRE
# ─────────────────────────────────────────────────────────────────────────────
elif view_mode == "🏷️ Analisis Genre":
    st.subheader("Analisis Genre Buku")

    # ── PREP DATA ─────────────────────────
    if fdf.empty:
        st.warning("Tidak ada data setelah filter.")
        st.stop()

    df_genre = fdf.copy()

    # pastikan tidak ada NaN
    df_genre = df_genre[df_genre["GENRES"].notna()]

    # split genre
    df_genre["GENRE_LIST"] = df_genre["GENRES"].astype(str).str.split(",")
    df_genre = df_genre.explode("GENRE_LIST")

    # bersihkan teks
    df_genre["GENRE_LIST"] = df_genre["GENRE_LIST"].astype(str).str.strip()

    # buang yang kosong
    df_genre = df_genre[df_genre["GENRE_LIST"] != ""]

    if df_genre.empty:
        st.warning("Genre tidak ditemukan di data ini.")
        st.stop()

    # ── KLASIFIKASI ─────────────────────────
    def classify_genre_type(g):
        g = g.lower()

        if g in ["novel","novella","cerita pendek","short stories","puisi","poetry","drama","komik","manga"]:
            return "Jenis Karya"
        elif g in ["romance","fantasy","horror","thriller","mystery","science fiction","fiction"]:
            return "Fiksi"
        elif g in ["biography","biografi","history","sejarah","philosophy","filsafat","psychology","agama","religion"]:
            return "Non-Fiksi"
        else:
            return "Tematik"

    df_genre["GENRE_TYPE"] = df_genre["GENRE_LIST"].apply(classify_genre_type)

    # ── METRICS ─────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Genre", int(df_genre["GENRE_LIST"].nunique()))
    col2.metric("Genre Tematik",
                int(df_genre[df_genre["GENRE_TYPE"]=="Tematik"]["GENRE_LIST"].nunique()))
    col3.metric("Jenis Karya",
                int(df_genre[df_genre["GENRE_TYPE"]=="Jenis Karya"]["GENRE_LIST"].nunique()))
    col4.metric("Total Buku", int(len(fdf)))

    st.markdown("---")

    # ── DISTRIBUSI GENRE TYPE ─────────────────────────
    colA, colB = st.columns(2)

    with colA:
        st.markdown("### Distribusi Jenis Genre")

        type_counts = df_genre["GENRE_TYPE"].value_counts()

        if len(type_counts) > 0:
            fig, ax = plt.subplots()
            ax.pie(type_counts, labels=type_counts.index, autopct="%1.0f%%")
            st.pyplot(fig)
        else:
            st.info("Tidak ada data untuk pie chart")

    with colB:
        st.markdown("### Top Genre")

        top_genre = df_genre["GENRE_LIST"].value_counts().head(10)

        if len(top_genre) > 0:
            st.bar_chart(top_genre)
        else:
            st.info("Tidak ada data genre")

    st.markdown("---")

    # ── GENRE TEMATIK ─────────────────────────
    st.markdown("### Genre Tematik Teratas")

    tematik = df_genre[df_genre["GENRE_TYPE"]=="Tematik"]
    tematik_counts = tematik["GENRE_LIST"].value_counts().head(15)

    if len(tematik_counts) > 0:
        st.bar_chart(tematik_counts)
    else:
        st.info("Tidak ada genre tematik")

    st.markdown("---")

    # ── GENRE VS WARNA ─────────────────────────
    st.markdown("### Warna Dominan per Genre")

    if "warna_kategori" not in df_genre.columns:
        st.warning("Kolom warna_kategori tidak ditemukan.")
    else:
        df_g = df_genre.copy()

        top_g = df_g["GENRE_LIST"].value_counts().head(8).index
        df_g = df_g[df_g["GENRE_LIST"].isin(top_g)]

        if len(df_g) > 0:
            pivot = pd.crosstab(df_g["GENRE_LIST"], df_g["warna_kategori"])

            if pivot.shape[0] > 0:
                pivot = pivot.div(pivot.sum(axis=1), axis=0) * 100

                fig, ax = plt.subplots(figsize=(8,4))
                bottom = np.zeros(len(pivot))

                for cat in WARNA_ORDER:
                    if cat in pivot.columns:
                        vals = pivot[cat].values
                        ax.barh(pivot.index, vals, left=bottom,
                                color=WARNA_HEX[cat], label=cat)
                        bottom += vals

                ax.set_xlabel("%")
                ax.set_title("Distribusi Warna per Genre")
                ax.legend(fontsize=6, bbox_to_anchor=(1.05,1))
                st.pyplot(fig)
            else:
                st.info("Pivot kosong")
        else:
            st.info("Tidak cukup data untuk analisis warna vs genre")


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Analisis warna Distant Reading (Tilton & Arnold 2023) & Cultural Analytics (Manovich 2020). "
    "Warna diekstrak via KMeans (k=5) pada ruang RGB. "
    "Kategorisasi warna berdasarkan rentang hue HSV."
)
