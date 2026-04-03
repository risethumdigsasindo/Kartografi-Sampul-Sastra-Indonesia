"""Kartografi Sampul Sastra Indonesia (2000-2025)"""
import os
from collections import Counter
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Kartografi Sampul Sastra Indonesia",
    page_icon="📖", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
h1,h2,h3{font-family:'Lora',serif;letter-spacing:-.02em;}
.stat-card{border:1px solid rgba(128,128,128,.15);border-radius:12px;padding:1.1rem 1.2rem 1rem;text-align:center;transition:transform .15s,box-shadow .15s;}
.stat-card:hover{transform:translateY(-3px);box-shadow:0 6px 18px rgba(0,0,0,.10);}
.stat-card .lbl{font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;opacity:.55;}
.stat-card .val{font-family:'Lora',serif;font-size:2.1rem;font-weight:600;line-height:1.1;}
.stat-card .sub{font-size:.72rem;opacity:.5;margin-top:.15rem;}
.bk-info{padding:.55rem .7rem .75rem;}
.bk-title{font-family:'Lora',serif;font-size:.82rem;font-weight:600;line-height:1.3;}
.bk-meta{font-size:.71rem;opacity:.6;margin:.15rem 0 .3rem;}
.badge{display:inline-block;font-size:.64rem;font-weight:500;padding:1px 7px;border-radius:20px;border:1px solid rgba(128,128,128,.2);margin:2px 2px 0 0;opacity:.82;}
.pal-row{display:flex;height:10px;border-radius:4px;overflow:hidden;margin:.35rem 0 .4rem;gap:1px;}
.pal-sw{flex-shrink:0;}
.prob-bar-wrap{margin:.12rem 0;}
.prob-label{font-size:.6rem;display:flex;justify-content:space-between;margin-bottom:1px;opacity:.72;}
.prob-bar-bg{background:rgba(128,128,128,.12);border-radius:3px;height:6px;overflow:hidden;}
.prob-bar-fill{height:6px;border-radius:3px;}
hr.thin{border:none;border-top:1px solid rgba(128,128,128,.12);margin:1.3rem 0;}
</style>""", unsafe_allow_html=True)

WARNA_HEX = {"putih":"#F5F5F0","hitam":"#1A1A1A","abu":"#8E8E93","merah":"#E53935",
    "oranye":"#FB8C00","kuning":"#FDD835","hijau":"#43A047","biru":"#1E88E5","ungu":"#8E24AA"}
WARNA_TXT = {"putih":"#333","hitam":"#eee","abu":"#fff","merah":"#fff","oranye":"#fff",
    "kuning":"#333","hijau":"#fff","biru":"#fff","ungu":"#fff"}
TYPEFACE_ID = {"humanist_serif":"Humanist Serif","transitional_serif":"Transitional Serif",
    "modern_serif":"Modern Serif","slab_serif":"Slab Serif","sans_serif":"Sans-serif",
    "script":"Kaligrafi/Script","display":"Display/Dekoratif"}
TYPEFACE_CLR = {"humanist_serif":"#5C6BC0","transitional_serif":"#7E57C2","modern_serif":"#AB47BC",
    "slab_serif":"#EC407A","sans_serif":"#42A5F5","script":"#26A69A","display":"#FFA726"}
TYPEFACE_FONT = {"humanist_serif":"Georgia,serif","transitional_serif":"'Times New Roman',serif",
    "modern_serif":"'Playfair Display',Georgia,serif","slab_serif":"'Courier New',monospace",
    "sans_serif":"Helvetica,Arial,sans-serif","script":"cursive","display":"Impact,fantasy"}
TYPEFACE_DESC = {"humanist_serif":"Kontras sedang, axis diagonal, bracket serif. Garamond, Sabon.",
    "transitional_serif":"Kontras lebih tinggi, axis hampir vertikal. Baskerville, Times.",
    "modern_serif":"Kontras ekstrem, hairline serif, axis vertikal. Bodoni, Didot.",
    "slab_serif":"Serif persegi tebal, kontras rendah. Clarendon, Rockwell.",
    "sans_serif":"Tanpa serif, stroke seragam. Helvetica, Futura.",
    "script":"Stroke mengalir, menyerupai kaligrafi atau tulisan tangan.",
    "display":"Bentuk huruf sangat stilistik, ornamental, untuk impak besar."}
GAYA_ID = {"photograph":"Fotografi","flat_graphic":"Ilustrasi Datar","hand_drawn":"Gambar Tangan",
    "text_dominant":"Dominan Teks","abstract":"Abstrak","collage":"Kolase"}
GAYA_CLR = {"photograph":"#1E88E5","flat_graphic":"#43A047","hand_drawn":"#FB8C00",
    "text_dominant":"#E53935","abstract":"#8E24AA","collage":"#00ACC1"}
GAYA_ICON = {"photograph":"📷","flat_graphic":"🎨","hand_drawn":"✏️",
    "text_dominant":"🔤","abstract":"🔷","collage":"🗂️"}
GAYA_DESC = {"photograph":"Gambar fotografis realistis.","flat_graphic":"Flat design: warna solid, bentuk geometris.",
    "hand_drawn":"Sketsa, cat air, ilustrasi ekspresif.","text_dominant":"Teks mendominasi elemen visual.",
    "abstract":"Bentuk non-representasional, pola, tekstur.","collage":"Gabungan foto, ilustrasi, teks dari berbagai sumber."}
SHELF_ID = {"fiksi":"Fiksi","non-fiksi":"Nonfiksi","puisi-asli":"Puisi"}
SHELF_REV = {v:k for k,v in SHELF_ID.items()}
JENIS_KARYA = {"Sastra Indonesia","Fiksi","Nonfiksi","Novel","Puisi","Cerita Pendek","Sastra"}

DATA_PATH = os.path.join(os.path.dirname(__file__), "data.csv")
COVER_DIR = os.path.join(os.path.dirname(__file__), "..", "covers")

@st.cache_data(show_spinner=False)
def load_data(path):
    d = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    for c in ["YEAR","RATING","TOTAL_RATING","TOTAL_REVIEW","brightness_mean","saturation_mean",
              "typeface_skor","gaya_skor","teks_coverage","n_region_teks","judul_match_score","yolo_n_objek","detr_objek_n"]:
        if c in d.columns: d[c] = pd.to_numeric(d[c], errors="coerce")
    for i in range(1,6):
        for s in ["pct","h","s","v"]:
            c = f"warna_{s}_{i}"
            if c in d.columns: d[c] = pd.to_numeric(d[c], errors="coerce")
    for c in d.columns:
        if c.startswith("typeface_prob_") or c.startswith("gaya_prob_"):
            d[c] = pd.to_numeric(d[c], errors="coerce")
    d["YEAR"] = d["YEAR"].fillna(0).astype(int)
    d["image_ok"] = d["image_ok"].astype(str).str.upper().isin(["TRUE","1"])
    d["ILLUSTRATOR"] = d["ILLUSTRATOR"].fillna("").astype(str).str.strip()
    d.loc[d["ILLUSTRATOR"].isin(["nan","NaN","None"]), "ILLUSTRATOR"] = ""
    if "typeface_kategori" in d.columns:
        d["typeface_kategori"] = d["typeface_kategori"].fillna("unclassified")

    valid_tf = set(TYPEFACE_ID.keys()) | {"unclassified"}

    d["typeface_kategori"] = d["typeface_kategori"].where(
        d["typeface_kategori"].astype(str).str.strip().isin(valid_tf),
        other="unclassified"
    )
    
    d["gaya_ilustrasi"] = d["gaya_ilustrasi"].where(
        d["gaya_ilustrasi"].astype(str).str.strip().isin(set(GAYA_ID.keys())), other=pd.NA)
    return d

with st.spinner("Memuat data..."):
    df = load_data(DATA_PATH)

def cover_path(img):
    if not img or str(img) in ("","nan"): return None
    p = os.path.join(COVER_DIR, str(img))
    return p if os.path.exists(p) else None

def expand_genres(series):
    out = []
    for v in series:
        if pd.isna(v) or str(v).strip() == "": out.append([])
        else: out.append([g.strip() for g in str(v).split(",") if g.strip()])
    return out

def genre_counts(d):
    c = Counter()
    for gl in expand_genres(d["GENRES"]): c.update(gl)
    return c

def pb(height=320, **kw):
    b = dict(height=height, margin=dict(l=8,r=8,t=28,b=8),
             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(size=11))
    b.update(kw)
    return b

def palette_html(row, n=5):
    parts, total = [], 0.0
    for i in range(1,n+1):
        hx = str(row.get(f"warna_hex_{i}","") or "").strip()
        pct = row.get(f"warna_pct_{i}",0)
        try: pct = float(pct)
        except: pct = 0.0
        if not hx or hx in ("nan",""): continue
        if not hx.startswith("#"): hx = "#"+hx
        parts.append((hx,pct)); total += pct
    if not parts: return ""
    scale = 100.0/total if total>0 else 1.0
    sw = "".join(f'<div class="pal-sw" style="background:{hx};width:{pct*scale:.1f}%;" title="{hx} {pct:.1f}%"></div>' for hx,pct in parts)
    return f'<div class="pal-row">{sw}</div>'

def prob_bars(probs_dict, colors_dict, label_map):
    html = ""
    for key, val in sorted(probs_dict.items(), key=lambda x: -x[1]):
        label = label_map.get(key, key); clr = colors_dict.get(key, "#999"); pct = val*100
        html += (f'<div class="prob-bar-wrap"><div class="prob-label"><span>{label}</span>'
                 f'<span>{pct:.1f}%</span></div><div class="prob-bar-bg">'
                 f'<div class="prob-bar-fill" style="width:{pct:.1f}%;background:{clr};"></div>'
                 f'</div></div>')
    return html

def book_card(row, col_obj, show_tf=False, show_gi=False):
    with col_obj:
        cp = cover_path(row.get("IMAGE_FILE"))
        if cp: st.image(cp, use_container_width=True)
        else:
            st.markdown('<div style="height:160px;background:rgba(128,128,128,.09);border-radius:8px 8px 0 0;display:flex;align-items:center;justify-content:center;font-size:2rem">📖</div>', unsafe_allow_html=True)
        year = int(row["YEAR"]) if row.get("YEAR",0) and int(row.get("YEAR",0))>0 else "–"
        url = row.get("URL",""); title = str(row.get("TITLE","–"))
        title_html = f'<a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">{title}</a>' if url else title
        badges = f'<span class="badge">{SHELF_ID.get(str(row.get("SHELF","")),"")} </span>'
        tf_bars = gi_bars = ""
        if show_tf and pd.notna(row.get("typeface_kategori")):
            tk = str(row["typeface_kategori"]); clr = TYPEFACE_CLR.get(tk,"#999")
            try: sc = f"{float(row.get('typeface_skor',0)):.2f}"
            except: sc = "–"
            badges += f'<span class="badge" style="border-color:{clr};color:{clr};">{TYPEFACE_ID.get(tk,tk)} {sc}</span>'
            probs = {k: float(row.get(f"typeface_prob_{k}",0) or 0) for k in TYPEFACE_ID}
            if any(probs.values()): tf_bars = prob_bars(probs, TYPEFACE_CLR, TYPEFACE_ID)
        if show_gi and pd.notna(row.get("gaya_ilustrasi")):
            gk = str(row["gaya_ilustrasi"]); clr = GAYA_CLR.get(gk,"#999")
            try: sc_gi = f"{float(row.get('gaya_skor',0)):.2f}"
            except: sc_gi = "–"
            badges += f'<span class="badge" style="border-color:{clr};color:{clr};">{GAYA_ID.get(gk,gk)} {sc_gi}</span>'
            probs_gi = {k: float(row.get(f"gaya_prob_{k}",0) or 0) for k in ["photograph","hand_drawn","abstract","flat_graphic","collage","text_dominant"]}
            if any(probs_gi.values()): gi_bars = prob_bars(probs_gi, GAYA_CLR, GAYA_ID)
        bars = tf_bars or gi_bars
        st.markdown(f'<div class="bk-info"><div class="bk-title">{title_html}</div><div class="bk-meta">{row.get("AUTHOR","–")} · {year}</div>{palette_html(row)}{badges}{"<div style=margin-top:.4rem>"+bars+"</div>" if bars else ""}</div>', unsafe_allow_html=True)

def grid(subset, n_cols=4, **kw):
    subset = subset.reset_index(drop=True)
    if subset.empty: st.info("Tidak ada buku yang cocok."); return
    for start in range(0, len(subset), n_cols):
        chunk = subset.iloc[start:start+n_cols]; cols = st.columns(n_cols)
        for j,(_, row) in enumerate(chunk.iterrows()): book_card(row, cols[j], **kw)

with st.sidebar:
    st.markdown("### Kartografi Sampul")
    st.markdown("<small>Analisis komputasional 7.453 sampul buku sastra Indonesia (2000–2025)</small>", unsafe_allow_html=True)
    st.markdown("---")
    HAL = st.radio("Navigasi", ["Beranda","Warna","Tipografi","Ilustrasi","Genre","Illustrator","Jelajah Buku"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Filter Rak**")
    rak_sel = st.selectbox("Rak", ["Semua Rak"]+list(SHELF_ID.values()), label_visibility="collapsed")
    st.markdown("**Filter Tahun**")
    yr_range = st.slider("Tahun", 2000, 2025, (2000,2025), label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<small>Metode: K-Means HSV · CLIP zero-shot · YOLOv8n · DETR ResNet-50</small>", unsafe_allow_html=True)

def af(d):
    if rak_sel != "Semua Rak": d = d[d["SHELF"]==SHELF_REV[rak_sel]]
    return d[(d["YEAR"]>=yr_range[0])&(d["YEAR"]<=yr_range[1])]

DF = af(df)
_gc = genre_counts(DF)
_n_unik = len(_gc)


# ── BERANDA ──────────────────────────────────────────────────
if HAL == "Beranda":
    st.markdown("# Kartografi Sampul Sastra Indonesia")
    st.markdown(f"Pemetaan komputasional terhadap **{len(DF):,} sampul buku** sastra Indonesia yang terbit antara 2000–2025, dianalisis melalui tiga modul: warna, tipografi, dan gaya ilustrasi.")
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    for col,(lbl,val,sub,clr) in zip([c1,c2,c3,c4],[
        ("Warna",DF["warna_kategori"].notna().sum(),"sampul dianalisis","#1E88E5"),
        ("Tipografi",len(DF),"sampul dianalisis","#8E24AA"),
        ("Ilustrasi",DF["gaya_ilustrasi"].notna().sum(),"sampul terklasifikasi","#43A047"),
        ("Genre",_n_unik,"genre unik teridentifikasi","#FB8C00"),
    ]):
        with col:
            st.markdown(f'<div class="stat-card" style="border-top:3px solid {clr};"><div class="lbl">{lbl}</div><div class="val" style="color:{clr};">{int(val):,}</div><div class="sub">{sub}</div></div>', unsafe_allow_html=True)
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    ca,cb,cc = st.columns(3)
    with ca:
        st.markdown("**Distribusi Rak**")
        sc = DF["SHELF"].map(SHELF_ID).value_counts()
        fig = px.pie(values=sc.values, names=sc.index, hole=.55, color_discrete_sequence=["#1E88E5","#FB8C00","#43A047"])
        fig.update_layout(**pb(260), showlegend=True, legend=dict(orientation="h",y=-.1))
        fig.update_traces(textinfo="percent+label", textfont_size=11)
        st.plotly_chart(fig, use_container_width=True)
    with cb:
        st.markdown("**Tren Terbit per Tahun**")
        yr = DF[DF["YEAR"]>0]["YEAR"].value_counts().sort_index()
        fig2 = px.bar(x=yr.index, y=yr.values, color_discrete_sequence=["#1E88E5"])
        fig2.update_layout(**pb(260), xaxis_title="", yaxis_title="")
        fig2.update_traces(marker_line_width=0)
        st.plotly_chart(fig2, use_container_width=True)
    with cc:
        st.markdown("**Warna Dominan**")
        wc = DF["warna_kategori"].value_counts()
        fig3 = px.bar(x=wc.values, y=wc.index, orientation="h", color=wc.index, color_discrete_map=WARNA_HEX)
        fig3.update_layout(**pb(260), showlegend=False, xaxis_title="", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
        fig3.update_traces(marker_line_width=0)
        st.plotly_chart(fig3, use_container_width=True)

# ── WARNA ─────────────────────────────────────────────────────
elif HAL == "Warna":
    st.markdown("## Analisis Warna")
    with st.expander("Cara kerja analisis warna", expanded=False):
        st.markdown("**K-Means Clustering (k=5) pada ruang warna HSV**\n\n1. Sampul → 150×150 piksel → BGR→HSV.\n2. K-Means k=5, 10 inisialisasi acak.\n3. Label warna dari rentang Hue dominan.\n4. Persentase dari bobot kluster.\n\n**Akurasi ~87%** (200 sampel).")
        hue_info = [("merah","0–10°&170–180°"),("oranye","10–25°"),("kuning","25–40°"),("hijau","40–85°"),("biru","85–130°"),("ungu","130–160°"),("abu","V&S rendah"),("hitam","V<50"),("putih","S<30")]
        hcols = st.columns(len(hue_info))
        for hc,(w,rng) in zip(hcols,hue_info):
            with hc:
                st.markdown(f'<div style="background:{WARNA_HEX[w]};border-radius:6px;padding:5px 3px;text-align:center;color:{WARNA_TXT[w]};font-size:.62rem;font-weight:600;">{w}<br><span style="font-weight:400;opacity:.85">{rng}</span></div>', unsafe_allow_html=True)
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    ca2,cb2 = st.columns(2)
    with ca2:
        st.markdown("**Distribusi Warna Dominan**")
        wc = DF["warna_kategori"].value_counts()
        fig = px.bar(x=wc.values, y=wc.index, orientation="h", color=wc.index, color_discrete_map=WARNA_HEX, text=wc.values)
        fig.update_layout(**pb(310), showlegend=False, xaxis_title="", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    with cb2:
        st.markdown("**Tren Warna per Tahun**")
        dft = DF[DF["YEAR"]>0].copy(); dft["warna"] = dft["warna_kategori"].fillna("lainnya")
        trnd = dft.groupby(["YEAR","warna"]).size().reset_index(name="n")
        fig2 = px.bar(trnd, x="YEAR", y="n", color="warna", color_discrete_map=WARNA_HEX, barmode="stack")
        fig2.update_layout(**pb(310), xaxis_title="", yaxis_title="", showlegend=True, legend=dict(orientation="h",y=-.2,font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)
    st.markdown("**Kecerahan vs Saturasi per Warna**")
    fig_sc = px.scatter(DF.dropna(subset=["brightness_mean","saturation_mean","warna_kategori"]), x="brightness_mean", y="saturation_mean", color="warna_kategori", color_discrete_map=WARNA_HEX, opacity=.35, hover_data=["TITLE","AUTHOR","YEAR"])
    fig_sc.update_layout(**pb(300), showlegend=True, legend=dict(orientation="h",y=-.18,font=dict(size=10)), xaxis_title="Kecerahan (V)", yaxis_title="Saturasi (S)")
    fig_sc.update_traces(marker=dict(size=4))
    st.plotly_chart(fig_sc, use_container_width=True)
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Cari Buku berdasarkan Warna**")
    wc1,wc2,wc3 = st.columns([2,2,1])
    with wc1: q_w = st.text_input("Judul / penulis", key="w_q")
    with wc2: w_sel = st.selectbox("Filter warna", ["Semua"]+sorted(DF["warna_kategori"].dropna().unique()), key="w_sel")
    with wc3: n_w = st.slider("Tampilkan", 4, 32, 8, 4, key="w_n")
    dw = DF[DF["image_ok"]].copy()
    if q_w:
        ql = q_w.lower(); dw = dw[dw["TITLE"].str.lower().str.contains(ql,na=False)|dw["AUTHOR"].str.lower().str.contains(ql,na=False)]
    if w_sel != "Semua": dw = dw[dw["warna_kategori"]==w_sel]
    if not dw.empty: grid(dw.head(n_w))

# ── TIPOGRAFI ─────────────────────────────────────────────────
elif HAL == "Tipografi":
    st.markdown("## Analisis Tipografi")
    with st.expander("Cara kerja analisis tipografi", expanded=False):
        st.markdown("**MSER + CLIP ViT-B/32 zero-shot (Lupton 2024, hal. 54–57)**\n\n1. **MSER** mendeteksi blob stabil khas huruf (delta=5, min_area=30). Region sepertiga atas di-crop sebagai area judul.\n2. **CLIP ViT-B/32** mengukur kemiripan dengan 7 deskripsi teks kategori typeface berdasarkan anatomi visual Lupton 2024.\n3. Softmax → probabilitas per kategori.\n\n**Akurasi ~68% top-1** (150 sampel). Script/Display paling presisi (>80%).")
    st.markdown("**Tujuh Kategori Typeface (Lupton 2024, hal. 54–57)**")
    tf_cols7 = st.columns(7)
    for col_tf,key in zip(tf_cols7,TYPEFACE_ID):
        clr = TYPEFACE_CLR[key]; font = TYPEFACE_FONT[key]
        with col_tf:
            st.markdown(f'<div style="border:1px solid rgba(128,128,128,.18);border-radius:8px;padding:.55rem .45rem;text-align:center;"><div style="font-family:{font};font-size:1.5rem;color:{clr};font-weight:700;line-height:1.2">Aa</div><div style="font-size:.63rem;font-weight:600;opacity:.72;margin:.2rem 0 .1rem">{TYPEFACE_ID[key]}</div><div style="font-size:.58rem;opacity:.5;text-align:left;line-height:1.35">{TYPEFACE_DESC[key]}</div></div>', unsafe_allow_html=True)
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    ca3,cb3 = st.columns(2)
    with ca3:
        st.markdown("**Distribusi Typeface**")
        tc = DF["typeface_kategori"].map(TYPEFACE_ID).value_counts()
        fig = px.bar(x=tc.values, y=tc.index, orientation="h", color=tc.index, color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID}, text=tc.values)
        fig.update_layout(**pb(300), showlegend=False, xaxis_title="", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    with cb3:
        st.markdown("**Tren Typeface per Tahun**")
        dft2 = DF[(DF["YEAR"]>0)&DF["typeface_kategori"].notna()].copy(); dft2["tf"] = dft2["typeface_kategori"].map(TYPEFACE_ID)
        tr2 = dft2.groupby(["YEAR","tf"]).size().reset_index(name="n")
        fig2 = px.bar(tr2, x="YEAR", y="n", color="tf", barmode="stack", color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID})
        fig2.update_layout(**pb(300), xaxis_title="", yaxis_title="", showlegend=True, legend=dict(orientation="h",y=-.22,font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)
    prob_cols_tf = [c for c in DF.columns if c.startswith("typeface_prob_")]
    if prob_cols_tf:
        st.markdown("**Rata-rata Probabilitas CLIP per Kategori**")
        means = DF[prob_cols_tf].mean().sort_values()
        means.index = [TYPEFACE_ID.get(c.replace("typeface_prob_",""),c) for c in means.index]
        fp = px.bar(x=means.values, y=means.index, orientation="h", color=means.index, color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID}, text=[f"{v:.3f}" for v in means.values])
        fp.update_layout(**pb(240), showlegend=False, xaxis_title="Rata-rata Softmax", yaxis_title="")
        fp.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fp, use_container_width=True)
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Contoh Buku — Kepercayaan Tertinggi per Kategori**")
    df_tv = DF[DF["typeface_kategori"].notna()&DF["image_ok"]].copy()
    df_tv["typeface_skor"] = pd.to_numeric(df_tv["typeface_skor"], errors="coerce")
    ex_cols7 = st.columns(7)
    for col_ex,key in zip(ex_cols7,TYPEFACE_ID):
        sub = df_tv[df_tv["typeface_kategori"]==key]
        if sub.empty: continue
        best = sub.nlargest(1,"typeface_skor").iloc[0]; clr = TYPEFACE_CLR[key]
        with col_ex:
            cp = cover_path(best.get("IMAGE_FILE"))
            if cp: st.image(cp, use_container_width=True)
            try: sc = f"{float(best.get('typeface_skor',0)):.2f}"
            except: sc = "–"
            probs_b = {k: float(best.get(f"typeface_prob_{k}",0) or 0) for k in TYPEFACE_ID}
            bars = prob_bars(probs_b, TYPEFACE_CLR, TYPEFACE_ID) if any(probs_b.values()) else ""
            st.markdown(f'<div style="font-size:.62rem;padding:.25rem 0;"><div style="font-weight:600;color:{clr}">{TYPEFACE_ID[key]}</div><div style="opacity:.6;line-height:1.3">{str(best.get("TITLE",""))[:28]}</div><div style="opacity:.5">skor {sc}</div>{"<div style=margin-top:.35rem>"+bars+"</div>" if bars else ""}</div>', unsafe_allow_html=True)
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Cari Buku berdasarkan Tipografi**")
    tfc1,tfc2,tfc3 = st.columns([2,2,1])
    with tfc1: q_tf = st.text_input("Judul / penulis", key="tf_q")
    with tfc2: tf_sel = st.selectbox("Filter typeface", ["Semua"]+[TYPEFACE_ID[k] for k in TYPEFACE_ID], key="tf_sel")
    with tfc3: n_tf = st.slider("Tampilkan", 4, 32, 8, 4, key="tf_n")
    dtf = DF[DF["image_ok"]].copy()
    if q_tf:
        ql2 = q_tf.lower(); dtf = dtf[dtf["TITLE"].str.lower().str.contains(ql2,na=False)|dtf["AUTHOR"].str.lower().str.contains(ql2,na=False)]
    if tf_sel != "Semua":
        tf_rev = {v:k for k,v in TYPEFACE_ID.items()}; dtf = dtf[dtf["typeface_kategori"]==tf_rev.get(tf_sel,tf_sel)]
    if not dtf.empty: grid(dtf.head(n_tf), show_tf=True)


# ── ILUSTRASI ─────────────────────────────────────────────────
elif HAL == "Ilustrasi":
    st.markdown("## Analisis Gaya Ilustrasi")
    with st.expander("Cara kerja analisis ilustrasi", expanded=False):
        st.markdown("**YOLOv8n + DETR ResNet-50 + CLIP zero-shot**\n\n1. **YOLOv8n** — deteksi objek COCO-80, confidence ≥ 0.25.\n2. **DETR ResNet-50** — validator keberadaan manusia, confidence ≥ 0.85.\n3. **CLIP ViT-B/32** — klasifikasi 6 gaya visual.\n\n**Akurasi ~72% top-1** (200 sampel). Fotografi >90%. YOLO–DETR sepakat ~83%.")
    st.markdown("**Enam Kategori Gaya Ilustrasi**")
    gcols6 = st.columns(6)
    for gcol,key in zip(gcols6,GAYA_ID):
        clr = GAYA_CLR[key]
        with gcol:
            st.markdown(f'<div style="border:1px solid rgba(128,128,128,.18);border-radius:8px;padding:.55rem .45rem;text-align:center;"><div style="font-size:1.5rem">{GAYA_ICON[key]}</div><div style="font-size:.66rem;font-weight:600;margin:.2rem 0 .1rem;color:{clr}">{GAYA_ID[key]}</div><div style="font-size:.58rem;opacity:.55;text-align:left;line-height:1.35">{GAYA_DESC[key]}</div></div>', unsafe_allow_html=True)
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    ca4,cb4 = st.columns(2)
    with ca4:
        st.markdown("**Distribusi Gaya**")
        gc = DF["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        fig = px.bar(x=gc.values, y=gc.index, orientation="h", color=gc.index, color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID}, text=gc.values)
        fig.update_layout(**pb(290), showlegend=False, xaxis_title="", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    with cb4:
        st.markdown("**Tren Gaya per Tahun**")
        dfg = DF[(DF["YEAR"]>0)&DF["gaya_ilustrasi"].notna()].copy(); dfg["gaya"] = dfg["gaya_ilustrasi"].map(GAYA_ID)
        trg = dfg.groupby(["YEAR","gaya"]).size().reset_index(name="n")
        fig2 = px.bar(trg, x="YEAR", y="n", color="gaya", barmode="stack", color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID})
        fig2.update_layout(**pb(290), xaxis_title="", yaxis_title="", showlegend=True, legend=dict(orientation="h",y=-.2,font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Figur Manusia vs Non-Manusia**")
    yh = int(DF["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
    dh = int(DF["detr_ada_manusia"].astype(str).str.upper().eq("TRUE").sum())
    tot = len(DF)
    agree = int((DF["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE")&DF["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")).sum())
    man_a,man_b,man_c = st.columns([2,1,2])
    with man_a:
        fig_man = go.Figure(data=[
            go.Bar(name="YOLOv8n", x=["Ada manusia","Tidak ada"], y=[yh,tot-yh], marker_color=["#66BB6A","rgba(128,128,128,.15)"]),
            go.Bar(name="DETR", x=["Ada manusia","Tidak ada"], y=[dh,tot-dh], marker_color=["#42A5F5","rgba(128,128,128,.08)"]),
        ])
        fig_man.update_layout(**pb(240), barmode="group", showlegend=True, legend=dict(orientation="h",y=-.15), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_man, use_container_width=True)
    with man_b:
        st.metric("Sepakat keduanya", f"{agree:,}", f"{agree/tot*100:.1f}%")
        st.metric("Hanya YOLOv8n", f"{yh-agree:,}")
        st.metric("Hanya DETR", f"{dh-agree:,}")
    with man_c:
        st.markdown("**Top Objek Non-Manusia (YOLO)**")
        obj_ctr = Counter()
        for v in DF["yolo_objek"].dropna():
            s = str(v).strip()
            if s and s not in ("0","nan"):
                for o in s.split(","):
                    o = o.strip()
                    if o and o not in ("person","0"): obj_ctr[o] += 1
        if obj_ctr:
            top_obj = pd.DataFrame(obj_ctr.most_common(12), columns=["Objek","Jumlah"])
            fig_obj = px.bar(top_obj, x="Jumlah", y="Objek", orientation="h", color_discrete_sequence=["#00ACC1"], text="Jumlah")
            fig_obj.update_layout(**pb(300), showlegend=False, xaxis_title="", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
            fig_obj.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig_obj, use_container_width=True)
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Contoh Buku — Kepercayaan Tertinggi per Gaya**")
    df_gv = DF[DF["gaya_ilustrasi"].notna()&DF["image_ok"]].copy()
    df_gv["gaya_skor"] = pd.to_numeric(df_gv["gaya_skor"], errors="coerce")
    gi_pk = ["photograph","hand_drawn","abstract","flat_graphic","collage","text_dominant"]
    ex_gcols6 = st.columns(6)
    for gcol_ex,key in zip(ex_gcols6,GAYA_ID):
        sub_g = df_gv[df_gv["gaya_ilustrasi"]==key]
        if sub_g.empty: continue
        best_g = sub_g.nlargest(1,"gaya_skor").iloc[0]; clr = GAYA_CLR[key]
        with gcol_ex:
            cp = cover_path(best_g.get("IMAGE_FILE"))
            if cp: st.image(cp, use_container_width=True)
            try: sg = f"{float(best_g.get('gaya_skor',0)):.2f}"
            except: sg = "–"
            probs_bg = {k: float(best_g.get(f"gaya_prob_{k}",0) or 0) for k in gi_pk}
            bars_g = prob_bars(probs_bg, GAYA_CLR, GAYA_ID) if any(probs_bg.values()) else ""
            st.markdown(f'<div style="font-size:.62rem;padding:.25rem 0;"><div style="font-weight:600;color:{clr}">{GAYA_ID[key]}</div><div style="opacity:.6;line-height:1.3">{str(best_g.get("TITLE",""))[:28]}</div><div style="opacity:.5">skor {sg}</div>{"<div style=margin-top:.35rem>"+bars_g+"</div>" if bars_g else ""}</div>', unsafe_allow_html=True)
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Cari Buku berdasarkan Gaya Ilustrasi**")
    gic1,gic2,gic3,gic4 = st.columns([2,2,1,1])
    with gic1: q_gi = st.text_input("Judul / penulis", key="gi_q")
    with gic2: gaya_sel = st.selectbox("Filter gaya", ["Semua"]+[GAYA_ID[k] for k in GAYA_ID], key="gi_sel")
    with gic3: ada_man = st.checkbox("Ada manusia", key="gi_man")
    with gic4: n_gi = st.slider("Tampilkan", 4, 32, 8, 4, key="gi_n")
    dgi = DF[DF["image_ok"]].copy()
    if q_gi:
        ql3 = q_gi.lower(); dgi = dgi[dgi["TITLE"].str.lower().str.contains(ql3,na=False)|dgi["AUTHOR"].str.lower().str.contains(ql3,na=False)]
    if ada_man: dgi = dgi[dgi["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE")|dgi["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")]
    if gaya_sel != "Semua":
        grev = {v:k for k,v in GAYA_ID.items()}; dgi = dgi[dgi["gaya_ilustrasi"]==grev.get(gaya_sel,gaya_sel)]
    if not dgi.empty: grid(dgi.head(n_gi), show_gi=True)


# ── GENRE ─────────────────────────────────────────────────────
elif HAL == "Genre":
    st.markdown("## Analisis Genre")
    with st.expander("Catatan metodologi", expanded=False):
        st.markdown(f"Genre dari metadata Goodreads (crowd-sourced, multi-label). Semua buku diberi label **Sastra Indonesia**. Terdapat **{_n_unik} genre unik** yang dikelompokkan menjadi **Jenis Karya** dan **Genre Tematik**.")
    gc_all = _gc
    jenis_items   = [(g,n) for g,n in gc_all.most_common() if g in JENIS_KARYA]
    tematik_items = [(g,n) for g,n in gc_all.most_common() if g not in JENIS_KARYA and n >= 3]
    cgl,cgr = st.columns(2)
    with cgl:
        st.markdown("**Jenis Karya**")
        df_jk = pd.DataFrame(jenis_items, columns=["Jenis","Jumlah"])
        fig_jk = px.bar(df_jk, x="Jumlah", y="Jenis", orientation="h", color_discrete_sequence=["#1E88E5"], text="Jumlah")
        fig_jk.update_layout(**pb(max(240,len(jenis_items)*36)), showlegend=False, xaxis_title="", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
        fig_jk.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig_jk, use_container_width=True)
    with cgr:
        st.markdown(f"**Genre Tematik** ({len(tematik_items)} genre)")
        n_top = st.slider("Tampilkan top N genre tematik", 5, min(len(tematik_items),60), min(20,len(tematik_items)), 5, key="gn_top")
        df_tm = pd.DataFrame(tematik_items[:n_top], columns=["Genre","Jumlah"])
        fig_tm = px.bar(df_tm, x="Jumlah", y="Genre", orientation="h", color_discrete_sequence=["#FB8C00"], text="Jumlah")
        fig_tm.update_layout(**pb(max(280,n_top*24)), showlegend=False, xaxis_title="", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
        fig_tm.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig_tm, use_container_width=True)
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Peta Panas Tumpang Tindih Genre Tematik (Top 12)**")
    top12t = [g for g,_ in tematik_items[:12]]
    co = pd.DataFrame(0, index=top12t, columns=top12t)
    for gl in expand_genres(DF["GENRES"]):
        rel = [g for g in gl if g in top12t]
        for i,g1 in enumerate(rel):
            for g2 in rel[i+1:]: co.loc[g1,g2]+=1; co.loc[g2,g1]+=1
    fig_co = px.imshow(co, color_continuous_scale="Oranges", aspect="auto", text_auto=True)
    fig_co.update_layout(**pb(400), xaxis_title="", yaxis_title="", coloraxis_showscale=False)
    fig_co.update_traces(textfont_size=10)
    st.plotly_chart(fig_co, use_container_width=True)
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("**Analisis per Genre**")
    st.markdown("<small>Klik genre untuk melihat analisis warna, tipografi, dan ilustrasi beserta contoh sampul representatif.</small>", unsafe_allow_html=True)
    if "sel_genre" not in st.session_state: st.session_state["sel_genre"] = jenis_items[0][0] if jenis_items else None
    jenis_sorted = [g for g,_ in gc_all.most_common() if g in JENIS_KARYA]
    tematik_sorted = [g for g,_ in gc_all.most_common() if g not in JENIS_KARYA and gc_all[g]>=5]
    GENRE_CLRS = {"Sastra Indonesia":"#5C6BC0","Fiksi":"#1E88E5","Nonfiksi":"#FB8C00","Novel":"#7E57C2","Puisi":"#43A047","Cerita Pendek":"#00ACC1","Sastra":"#EC407A"}
    st.markdown("*Jenis Karya:*")
    btn_j = st.columns(min(len(jenis_sorted),7))
    for col_b,g in zip(btn_j,jenis_sorted):
        if col_b.button(g, key=f"gbtn_j_{g}", use_container_width=True):
            st.session_state["sel_genre"] = g
    st.markdown("*Genre Tematik:*")
    for cs in range(0, min(len(tematik_sorted),48), 8):
        chunk_g = tematik_sorted[cs:cs+8]; btn_t = st.columns(len(chunk_g))
        for col_b,g in zip(btn_t,chunk_g):
            if col_b.button(g, key=f"gbtn_t_{g}", use_container_width=True):
                st.session_state["sel_genre"] = g
    sel_genre = st.session_state["sel_genre"]
    if sel_genre:
        st.markdown("<hr class='thin'>", unsafe_allow_html=True)
        mask_g = DF["GENRES"].apply(lambda x: sel_genre in [g.strip() for g in str(x).split(",")])
        df_gs = DF[mask_g]
        if df_gs.empty: st.info(f"Tidak ada buku dengan genre *{sel_genre}*.")
        else:
            st.markdown(f'#### Genre: **{sel_genre}** <span style="font-family:Inter;font-size:1rem;font-weight:400;opacity:.6">— {len(df_gs):,} buku</span>', unsafe_allow_html=True)
            tab_w,tab_tf,tab_gi = st.tabs(["Warna","Tipografi","Ilustrasi"])
            with tab_w:
                wc_g = df_gs["warna_kategori"].value_counts(); wc_all = DF["warna_kategori"].value_counts()
                cw1,cw2 = st.columns(2)
                with cw1:
                    fig_wg = px.bar(x=wc_g.values, y=wc_g.index, orientation="h", color=wc_g.index, color_discrete_map=WARNA_HEX, text=wc_g.values)
                    fig_wg.update_layout(**pb(260), showlegend=False, xaxis_title="Jumlah", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
                    fig_wg.update_traces(textposition="outside", marker_line_width=0)
                    st.plotly_chart(fig_wg, use_container_width=True)
                with cw2:
                    diff = (wc_g/len(df_gs)-wc_all/len(DF)).dropna().sort_values(ascending=False)
                    diff_df = diff.reset_index(); diff_df.columns = ["warna","delta"]
                    fig_diff = px.bar(diff_df, x="delta", y="warna", orientation="h", color="warna", color_discrete_map=WARNA_HEX)
                    fig_diff.update_layout(**pb(260), showlegend=False, xaxis_title="Simpangan proporsi", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
                    fig_diff.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
                    st.plotly_chart(fig_diff, use_container_width=True)
                st.markdown("**Contoh sampul per warna dominan**")
                top_w = wc_g.head(4).index.tolist(); ex_w = st.columns(len(top_w))
                df_gs_img = df_gs[df_gs["image_ok"]]
                for wcol,wkey in zip(ex_w,top_w):
                    sub_w = df_gs_img[df_gs_img["warna_kategori"]==wkey]
                    if sub_w.empty: continue
                    sample_w = sub_w.sample(1,random_state=7).iloc[0]
                    with wcol:
                        cp = cover_path(sample_w.get("IMAGE_FILE"))
                        if cp: st.image(cp, use_container_width=True)
                        st.markdown(f'<div style="font-size:.65rem;text-align:center;"><span style="display:inline-block;width:10px;height:10px;background:{WARNA_HEX.get(wkey,"#999")};border-radius:2px;margin-right:4px;vertical-align:middle;"></span><strong>{wkey}</strong><br><span style="opacity:.6">{str(sample_w.get("TITLE",""))[:30]}</span></div>', unsafe_allow_html=True)
            with tab_tf:
                df_gs_tf = df_gs[df_gs["typeface_kategori"].notna()]
                if df_gs_tf.empty: st.info("Belum ada data tipografi untuk genre ini.")
                else:
                    tc_g = df_gs_tf["typeface_kategori"].map(TYPEFACE_ID).value_counts()
                    tc_all = DF[DF["typeface_kategori"].notna()]["typeface_kategori"].map(TYPEFACE_ID).value_counts()
                    ctf1,ctf2 = st.columns(2)
                    with ctf1:
                        fig_tg = px.bar(x=tc_g.values, y=tc_g.index, orientation="h", color=tc_g.index, color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID}, text=tc_g.values)
                        fig_tg.update_layout(**pb(250), showlegend=False, xaxis_title="Jumlah", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
                        fig_tg.update_traces(textposition="outside", marker_line_width=0)
                        st.plotly_chart(fig_tg, use_container_width=True)
                    with ctf2:
                        diff_tf = (tc_g/len(df_gs_tf)-tc_all/len(DF[DF["typeface_kategori"].notna()])).dropna().sort_values(ascending=False)
                        diff_tf_df = diff_tf.reset_index(); diff_tf_df.columns = ["tipografi","delta"]
                        fig_dtf = px.bar(diff_tf_df, x="delta", y="tipografi", orientation="h", color="tipografi", color_discrete_map={TYPEFACE_ID[k]:TYPEFACE_CLR[k] for k in TYPEFACE_ID})
                        fig_dtf.update_layout(**pb(250), showlegend=False, xaxis_title="Simpangan proporsi", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
                        fig_dtf.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
                        st.plotly_chart(fig_dtf, use_container_width=True)
                    st.markdown("**Contoh sampul per tipografi**")
                    top_tf = [k for k,_ in df_gs_tf["typeface_kategori"].value_counts().head(4).items()]
                    ex_tf = st.columns(len(top_tf))
                    df_gs_tf_img = df_gs_tf[df_gs_tf["image_ok"]].copy()
                    df_gs_tf_img["typeface_skor"] = pd.to_numeric(df_gs_tf_img["typeface_skor"], errors="coerce")
                    for tcol,tkey in zip(ex_tf,top_tf):
                        sub_t = df_gs_tf_img[df_gs_tf_img["typeface_kategori"]==tkey]
                        if sub_t.empty: continue
                        best_t = sub_t.nlargest(1,"typeface_skor").iloc[0]; clr_t = TYPEFACE_CLR.get(tkey,"#999")
                        with tcol:
                            cp = cover_path(best_t.get("IMAGE_FILE"))
                            if cp: st.image(cp, use_container_width=True)
                            try: sc_t = f"{float(best_t.get('typeface_skor',0)):.2f}"
                            except: sc_t = "–"
                            st.markdown(f'<div style="font-size:.65rem;text-align:center;"><strong style="color:{clr_t}">{TYPEFACE_ID.get(tkey,tkey)}</strong><br><span style="opacity:.6">{str(best_t.get("TITLE",""))[:30]}</span><br><span style="opacity:.5">skor {sc_t}</span></div>', unsafe_allow_html=True)
            with tab_gi:
                gc_g = df_gs["gaya_ilustrasi"].map(GAYA_ID).value_counts(); gc_all_d = DF["gaya_ilustrasi"].map(GAYA_ID).value_counts()
                cg1,cg2 = st.columns(2)
                with cg1:
                    fig_gg = px.bar(x=gc_g.values, y=gc_g.index, orientation="h", color=gc_g.index, color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID}, text=gc_g.values)
                    fig_gg.update_layout(**pb(250), showlegend=False, xaxis_title="Jumlah", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
                    fig_gg.update_traces(textposition="outside", marker_line_width=0)
                    st.plotly_chart(fig_gg, use_container_width=True)
                with cg2:
                    diff_gi = (gc_g/len(df_gs)-gc_all_d/len(DF)).dropna().sort_values(ascending=False)
                    diff_gi_df = diff_gi.reset_index(); diff_gi_df.columns = ["gaya","delta"]
                    fig_dgi = px.bar(diff_gi_df, x="delta", y="gaya", orientation="h", color="gaya", color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID})
                    fig_dgi.update_layout(**pb(250), showlegend=False, xaxis_title="Simpangan proporsi", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
                    fig_dgi.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
                    st.plotly_chart(fig_dgi, use_container_width=True)
                st.markdown("**Contoh sampul per gaya ilustrasi**")
                top_gi = [k for k,_ in df_gs["gaya_ilustrasi"].value_counts().head(4).items()]
                ex_gi = st.columns(len(top_gi))
                df_gs_gi_img = df_gs[df_gs["image_ok"]].copy()
                df_gs_gi_img["gaya_skor"] = pd.to_numeric(df_gs_gi_img["gaya_skor"], errors="coerce")
                for gcoli,gikey in zip(ex_gi,top_gi):
                    sub_gi = df_gs_gi_img[df_gs_gi_img["gaya_ilustrasi"]==gikey]
                    if sub_gi.empty: continue
                    best_gi = sub_gi.nlargest(1,"gaya_skor").iloc[0]; clr_gi = GAYA_CLR.get(gikey,"#999")
                    with gcoli:
                        cp = cover_path(best_gi.get("IMAGE_FILE"))
                        if cp: st.image(cp, use_container_width=True)
                        try: sc_gi = f"{float(best_gi.get('gaya_skor',0)):.2f}"
                        except: sc_gi = "–"
                        st.markdown(f'<div style="font-size:.65rem;text-align:center;"><strong style="color:{clr_gi}">{GAYA_ICON.get(gikey,"")} {GAYA_ID.get(gikey,gikey)}</strong><br><span style="opacity:.6">{str(best_gi.get("TITLE",""))[:30]}</span><br><span style="opacity:.5">skor {sc_gi}</span></div>', unsafe_allow_html=True)


# ── ILLUSTRATOR ───────────────────────────────────────────────
elif HAL == "Illustrator":
    st.markdown("## Illustrator Sampul")
    has_ill = DF["ILLUSTRATOR"].ne(""); n_ill = has_ill.sum(); n_no_ill = (~has_ill).sum()
    st.markdown(f"**{n_ill} buku** dari {len(DF):,} yang menyebutkan nama illustrator di Goodreads.")
    df_ill = DF[has_ill].copy()
    q_ill = st.text_input("Cari illustrator atau judul buku", key="ill_q")
    if q_ill:
        ql = q_ill.lower()
        df_ill = df_ill[df_ill["ILLUSTRATOR"].str.lower().str.contains(ql,na=False)|df_ill["TITLE"].str.lower().str.contains(ql,na=False)]
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    ill_sum = (df_ill.groupby("ILLUSTRATOR").agg(Buku=("TITLE","count"),Judul=("TITLE",lambda x: " · ".join(x.values.tolist())),Tahun=("YEAR",lambda x: ", ".join(sorted({str(int(v)) for v in x if v>0})))).reset_index().sort_values("Buku",ascending=False).rename(columns={"ILLUSTRATOR":"Illustrator"}))
    st.dataframe(ill_sum, use_container_width=True, hide_index=True, column_config={"Illustrator":st.column_config.TextColumn(width="medium"),"Buku":st.column_config.NumberColumn(width="small"),"Judul":st.column_config.TextColumn(width="large"),"Tahun":st.column_config.TextColumn(width="small")})
    st.markdown("<hr class='thin'>", unsafe_allow_html=True)
    st.markdown("### Perbandingan Sampul: Dengan vs Tanpa Illustrator")
    st.markdown("Apakah sampul yang disebutkan nama illustratornya cenderung berbeda secara visual dari yang tidak?")
    df_with = DF[has_ill].copy(); df_wout = DF[~has_ill].copy()
    for d in [df_with,df_wout]:
        for c in ["brightness_mean","saturation_mean","gaya_skor","typeface_skor"]:
            if c in d.columns: d[c] = pd.to_numeric(d[c], errors="coerce")
    met_cols = st.columns(4)
    for mcol,(lbl,col) in zip(met_cols,[("Kecerahan","brightness_mean"),("Saturasi","saturation_mean"),("Skor Gaya","gaya_skor"),("Skor Tipografi","typeface_skor")]):
        v_w = df_with[col].mean() if col in df_with.columns else 0
        v_o = df_wout[col].mean() if col in df_wout.columns else 0
        mcol.metric(f"{lbl} (dengan ill.)", f"{v_w:.3f}", f"{v_w-v_o:+.3f} vs tanpa")
    st.markdown("**Distribusi Warna Dominan**")
    wc_w = df_with["warna_kategori"].value_counts(normalize=True)
    wc_o = df_wout["warna_kategori"].value_counts(normalize=True)
    all_w = sorted(set(wc_w.index)|set(wc_o.index))
    warna_cmp = pd.DataFrame({"Dengan Illustrator":[wc_w.get(w,0) for w in all_w],"Tanpa Illustrator":[wc_o.get(w,0) for w in all_w]}, index=all_w)
    fig_wc = go.Figure()
    fig_wc.add_trace(go.Bar(name="Dengan Illustrator", x=warna_cmp.index, y=warna_cmp["Dengan Illustrator"], marker_color=[WARNA_HEX.get(w,"#999") for w in all_w], opacity=.9))
    fig_wc.add_trace(go.Bar(name="Tanpa Illustrator", x=warna_cmp.index, y=warna_cmp["Tanpa Illustrator"], marker_color=[WARNA_HEX.get(w,"#999") for w in all_w], opacity=.35))
    fig_wc.update_layout(**pb(280), barmode="group", showlegend=True, xaxis_title="", yaxis_title="Proporsi", legend=dict(orientation="h",y=-.15))
    st.plotly_chart(fig_wc, use_container_width=True)
    il2a,il2b = st.columns(2)
    with il2a:
        st.markdown("**Gaya Ilustrasi — Dengan Illustrator**")
        gc_w = df_with["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        fig_gw = px.pie(values=gc_w.values, names=gc_w.index, hole=.5, color=gc_w.index, color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID})
        fig_gw.update_layout(**pb(240), showlegend=True, legend=dict(orientation="h",y=-.1,font=dict(size=10)))
        fig_gw.update_traces(textinfo="percent", textfont_size=10)
        st.plotly_chart(fig_gw, use_container_width=True)
    with il2b:
        st.markdown("**Gaya Ilustrasi — Tanpa Illustrator**")
        gc_o = df_wout["gaya_ilustrasi"].map(GAYA_ID).value_counts()
        fig_go = px.pie(values=gc_o.values, names=gc_o.index, hole=.5, color=gc_o.index, color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID})
        fig_go.update_layout(**pb(240), showlegend=True, legend=dict(orientation="h",y=-.1,font=dict(size=10)))
        fig_go.update_traces(textinfo="percent", textfont_size=10)
        st.plotly_chart(fig_go, use_container_width=True)
    st.markdown("**Simpangan Gaya: Dengan − Tanpa Illustrator**")
    diff_gaya = (gc_w/n_ill - gc_o/n_no_ill).dropna().sort_values(ascending=False)
    diff_gaya_df = diff_gaya.reset_index(); diff_gaya_df.columns = ["gaya","delta"]
    fig_dg = px.bar(diff_gaya_df, x="delta", y="gaya", orientation="h", color="gaya", color_discrete_map={GAYA_ID[k]:GAYA_CLR[k] for k in GAYA_ID})
    fig_dg.update_layout(**pb(240), showlegend=False, xaxis_title="Selisih proporsi", yaxis_title="", yaxis=dict(categoryorder="total ascending"))
    fig_dg.add_vline(x=0, line_dash="dash", line_color="rgba(128,128,128,.4)")
    st.plotly_chart(fig_dg, use_container_width=True)
    st.markdown("<small style='opacity:.55'>Nilai positif berarti gaya tersebut lebih sering ditemukan pada buku yang menyebutkan nama illustratornya.</small>", unsafe_allow_html=True)

# ── JELAJAH BUKU ─────────────────────────────────────────────
elif HAL == "Jelajah Buku":
    st.markdown("## Jelajah Buku")
    st.markdown("Temukan buku dari kombinasi kriteria visual dan metadata.")
    with st.form("form_jelajah"):
        r1 = st.columns(4)
        q_j = r1[0].text_input("Judul / penulis")
        warna_j = r1[1].selectbox("Warna dominan", ["Semua"]+sorted(DF["warna_kategori"].dropna().unique()))
        tf_j = r1[2].selectbox("Tipografi", ["Semua"]+[TYPEFACE_ID[k] for k in TYPEFACE_ID])
        gaya_j = r1[3].selectbox("Gaya ilustrasi", ["Semua"]+[GAYA_ID[k] for k in GAYA_ID])
        r2 = st.columns(4)
        top25_j = [g for g,_ in _gc.most_common(25)]
        genre_j = r2[0].selectbox("Genre", ["Semua"]+top25_j)
        ill_j = r2[1].selectbox("Illustrator", ["Semua","Dengan illustrator"])
        man_j = r2[2].checkbox("Ada figur manusia")
        n_j = r2[3].slider("Tampilkan", 8, 48, 16, 8)
        st.form_submit_button("Cari")
    dj = DF[DF["image_ok"]].copy()
    if q_j:
        ql = q_j.lower(); dj = dj[dj["TITLE"].str.lower().str.contains(ql,na=False)|dj["AUTHOR"].str.lower().str.contains(ql,na=False)]
    if warna_j != "Semua": dj = dj[dj["warna_kategori"]==warna_j]
    if tf_j != "Semua":
        tf_rev3 = {v:k for k,v in TYPEFACE_ID.items()}; dj = dj[dj["typeface_kategori"]==tf_rev3.get(tf_j,tf_j)]
    if gaya_j != "Semua":
        grev3 = {v:k for k,v in GAYA_ID.items()}; dj = dj[dj["gaya_ilustrasi"]==grev3.get(gaya_j,gaya_j)]
    if genre_j != "Semua": dj = dj[dj["GENRES"].apply(lambda x: genre_j in [g.strip() for g in str(x).split(",")])]
    if ill_j == "Dengan illustrator": dj = dj[dj["ILLUSTRATOR"].ne("")]
    if man_j: dj = dj[dj["yolo_ada_manusia"].astype(str).str.upper().eq("TRUE")|dj["detr_ada_manusia"].astype(str).str.upper().eq("TRUE")]
    st.markdown(f"**{len(dj):,} buku ditemukan**")
    if not dj.empty: grid(dj.head(n_j), show_tf=True, show_gi=True)
