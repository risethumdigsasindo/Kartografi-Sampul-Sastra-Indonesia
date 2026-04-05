import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# ==============================
# LOAD DATA
# ==============================
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, sep=';', engine='python', encoding='latin1')
    df.columns = df.columns.str.strip().str.lower()
    return df

CSV_PATH = "data.csv"  # ganti path kamu
DF = load_data(CSV_PATH)

# ==============================
# WARNA BERBOBOT (CORE FIX)
# ==============================
def warna_weighted_counts(df):
    warna_dict = {}

    for i in range(1, 6):
        warna_col = f"warna_{i}"
        pct_col   = f"warna_pct_{i}"

        if warna_col not in df.columns:
            continue

        for warna, pct in zip(df[warna_col], df[pct_col]):
            if pd.isna(warna) or pd.isna(pct):
                continue

            warna_dict[warna] = warna_dict.get(warna, 0) + float(pct)

    total = sum(warna_dict.values())
    warna_dict = {k: v/total for k,v in warna_dict.items()}

    return pd.Series(warna_dict).sort_values(ascending=False)

# ==============================
# PIE CHART
# ==============================
def plot_pie(wc, title):
    fig, ax = plt.subplots()
    ax.pie(wc.values, labels=wc.index, autopct='%1.1f%%')
    ax.set_title(title)
    st.pyplot(fig)

# ==============================
# HEATMAP GENRE × WARNA
# ==============================
def heatmap_genre_warna(df):
    genres = df["genre"].dropna().unique()
    warna_all = set()

    # kumpulkan semua warna
    for i in range(1,6):
        warna_all.update(df[f"warna_{i}"].dropna().unique())

    warna_all = sorted(list(warna_all))

    matrix = []

    for genre in genres:
        subset = df[df["genre"] == genre]
        wc = warna_weighted_counts(subset)

        row = [wc.get(w, 0) for w in warna_all]
        matrix.append(row)

    matrix = np.array(matrix)

    fig, ax = plt.subplots(figsize=(12,6))
    im = ax.imshow(matrix)

    ax.set_xticks(range(len(warna_all)))
    ax.set_xticklabels(warna_all, rotation=90)

    ax.set_yticks(range(len(genres)))
    ax.set_yticklabels(genres)

    ax.set_title("Heatmap Warna × Genre (Weighted)")
    plt.colorbar(im)

    st.pyplot(fig)

# ==============================
# PALETTE PER GENRE
# ==============================
def show_palette(colors, title):
    fig, ax = plt.subplots(figsize=(6,1))
    ax.imshow([colors])
    ax.axis("off")
    ax.set_title(title)
    st.pyplot(fig)

def palette_per_genre(df):
    for genre, group in df.groupby("genre"):
        wc = warna_weighted_counts(group)

        top_colors = wc.head(5)

        # convert ke RGB dummy (kalau warna label)
        # kalau kamu punya HSV/RGB asli, bisa disesuaikan
        colors = []
        for w in top_colors.index:
            # fallback random (bisa diganti mapping)
            colors.append(np.random.randint(0,255,3))

        colors = np.array(colors)

        show_palette(colors, f"{genre} (Top Colors)")

# ==============================
# UI
# ==============================
st.title("📚 Analisis Warna Sampul Buku (Weighted)")

tab1, tab2, tab3 = st.tabs(["Distribusi", "Heatmap", "Palette"])

# ==============================
# TAB 1: DISTRIBUSI TOTAL
# ==============================
with tab1:
    st.subheader("Distribusi Warna Keseluruhan")

    wc = warna_weighted_counts(DF)
    plot_pie(wc, "Distribusi Warna (Weighted)")

# ==============================
# TAB 2: HEATMAP
# ==============================
with tab2:
    st.subheader("Heatmap Warna × Genre")

    heatmap_genre_warna(DF)

# ==============================
# TAB 3: PALETTE
# ==============================
with tab3:
    st.subheader("Palette Warna per Genre")

    palette_per_genre(DF)
