# tipografi_block.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

# ==============================
# 4 KATEGORI FINAL
# ==============================
TYPEFACE_SIMPLIFIED = {
    "humanist_serif": "Serif",
    "transitional_serif": "Serif",
    "modern_serif": "Serif",
    "slab_serif": "Serif",
    "sans_serif": "Sans-serif",
    "script": "Script",
    "display": "Fancy",
    "unknown": "Unknown",
}

COLOR_MAP = {
    "Serif": "#6A5ACD",
    "Sans-serif": "#42A5F5",
    "Script": "#26A69A",
    "Fancy": "#FFA726",
    "Unknown": "#BDBDBD",
}

# ==============================
# MAIN FUNCTION
# ==============================
def render_tipografi(df: pd.DataFrame):

    st.title("📚 Analisis Tipografi Sampul Buku")

    # ==============================
    # PREPROCESS
    # ==============================
    df = df.copy()
    df["typeface_simple"] = df["typeface_kategori"].map(TYPEFACE_SIMPLIFIED)

    # explode genre
    df["genre_list"] = df["GENRES"].fillna("").apply(
        lambda x: [g.strip() for g in str(x).split(",") if g.strip()]
    )
    df_exploded = df.explode("genre_list").reset_index(drop=True)
    df_exploded["genre_list"] = df_exploded["genre_list"].fillna("Unknown")
    df_exploded["typeface_simple"] = df_exploded["typeface_simple"].fillna("Unknown")
    # ==============================
    # SIDEBAR MENU
    # ==============================
    menu = st.sidebar.radio(
        "Menu",
        [
            "📊 Heatmap Genre",
            "🔤 Font Dominan",
            "🔍 Pipeline Analisis",
            "🎨 Ilustrasi vs Typeface"
        ]
    )

    # =====================================================
    # 1. HEATMAP (INI YANG MIRIP GAMBAR)
    # =====================================================
    if menu == "📊 Heatmap Genre":

        st.subheader("Heatmap Typeface × Genre")

        pivot = pd.crosstab(
            df_exploded["genre_list"],
            df_exploded["typeface_simple"],
            normalize="index"
        ) * 100

        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="Purples",
            text=pivot.round(0).astype(int).astype(str) + "%",
            texttemplate="%{text}",
        ))

        fig.update_layout(
            height=700,
            margin=dict(l=150, r=20, t=40, b=80)
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption("Semakin gelap = semakin dominan")

    # =====================================================
    # 2. FONT DOMINAN (KANAN SEPERTI GAMBAR)
    # =====================================================
    elif menu == "🔤 Font Dominan":

        st.subheader("Distribusi Typeface + Contoh Visual")

        col1, col2 = st.columns([3,1])

        # kiri → chart
        with col1:
            dist = df["typeface_simple"].value_counts()

            fig = px.bar(
                x=dist.values,
                y=dist.index,
                orientation="h",
                color=dist.index,
                color_discrete_map=COLOR_MAP,
                text=dist.values
            )

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        # kanan → contoh font
        with col2:
            st.markdown("### Serif")
            st.markdown(
                "<div style='font-family:serif;font-size:32px'>A A A A</div>",
                unsafe_allow_html=True
            )

            st.markdown("### Sans-serif")
            st.markdown(
                "<div style='font-family:sans-serif;font-size:32px'>A A A A</div>",
                unsafe_allow_html=True
            )

            st.markdown("### Script")
            st.markdown(
                "<div style='font-family:cursive;font-size:32px'>A A A A</div>",
                unsafe_allow_html=True
            )

            st.markdown("### Fancy")
            st.markdown(
                "<div style='font-family:Impact;font-size:32px'>A A A A</div>",
                unsafe_allow_html=True
            )

    # =====================================================
    # 3. PIPELINE (PAKAI GAMBAR KAMU)
    # =====================================================
    elif menu == "🔍 Pipeline Analisis":

        st.subheader("Pipeline Analisis Tipografi")

        try:
            img = Image.open("Hasil Tipografi dan Typeface.png")
            st.image(img, use_container_width=True)
        except:
            st.warning("File gambar pipeline tidak ditemukan")

        st.markdown("""
        ### Alur:
        1. Input sampul buku
        2. OCR teks
        3. Matching judul
        4. Kandidat font
        5. CLIP classification
        """)

    # =====================================================
    # 4. ILUSTRASI vs TYPEFACE
    # =====================================================
    elif menu == "🎨 Ilustrasi vs Typeface":

        st.subheader("Relasi Ilustrasi vs Typeface")

        if "gaya_ilustrasi" not in df.columns:
            st.warning("Kolom gaya_ilustrasi tidak tersedia")
            return

        ct = pd.crosstab(
            df["typeface_simple"],
            df["gaya_ilustrasi"],
            normalize="index"
        )

        fig = go.Figure(data=go.Heatmap(
            z=ct.values,
            x=ct.columns,
            y=ct.index,
            colorscale="RdYlGn",
            text=(ct*100).round(0).astype(int).astype(str)+"%",
            texttemplate="%{text}"
        ))

        fig.update_layout(height=500)

        st.plotly_chart(fig, use_container_width=True)

        st.caption("Relasi antara gaya ilustrasi dan kategori typeface")
