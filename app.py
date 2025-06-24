import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from collections import Counter
import re

# === SETUP STREAMLIT ===
st.set_page_config(page_title="📍 Google Maps Review Dashboard", layout="wide", initial_sidebar_state="expanded")
st.markdown("<h1 style='color:#4FC3F7'>📍 Dashboard Ulasan Google Maps</h1>", unsafe_allow_html=True)

# === FILE UPLOADER ===
uploaded_file = st.sidebar.file_uploader("📎 Upload file CSV ulasan", type="csv")

# === STOPWORDS ===
stopwords = {
    'yang', 'dan', 'untuk', 'dengan', 'juga', 'saya', 'kami', 'ada', 'itu', 'di',
    'ke', 'dari', 'pada', 'atau', 'tidak', 'karena', 'dalam', 'lagi', 'sudah',
    'kalau', 'jadi', 'semua', 'bisa', 'aja', 'akan', 'oleh', 'seperti', 'mau',
    'nih', 'nya', 'cuma', 'hanya', 'the'
}

# === FUNGSI PEMBANTU ===
def most_common_words(text_series, top_n=20):
    words = []
    for text in text_series.dropna():
        tokens = re.findall(r'\b\w{3,}\b', text.lower())
        filtered = [word for word in tokens if word not in stopwords]
        words.extend(filtered)
    counter = Counter(words)
    return pd.DataFrame(counter.most_common(top_n), columns=["Kata", "Frekuensi"])

def create_rating_plot(df):
    fig = px.histogram(df, x="Star Given", nbins=5, title="Distribusi Rating", color_discrete_sequence=["#00bcd4"])
    return fig

def create_monthly_trend(df):
    df["Month"] = df["Publish Date"].dt.to_period("M").astype(str)
    trend = df.groupby("Month").size().reset_index(name="Jumlah Review")
    fig = px.line(trend, x="Month", y="Jumlah Review", markers=True, title="Tren Jumlah Review per Bulan")
    return fig

# === MAIN APP ===
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Pembersihan data
    df = df.dropna(subset=["Review Text", "Star Given"])
    df["Star Given"] = pd.to_numeric(df["Star Given"], errors="coerce")
    df = df.dropna(subset=["Star Given"])
    df["Star Given"] = df["Star Given"].astype(int)
    df["Publish Date"] = pd.to_datetime(df["Publish Date"], errors='coerce')

    # Sidebar
    st.sidebar.header("🎛️ Filter")
    rating = st.sidebar.slider("Filter Rating", 1, 5, (1, 5))
    keyword = st.sidebar.text_input("🔍 Kata kunci (opsional)")
    show_table = st.sidebar.checkbox("📋 Tampilkan Tabel", value=True)

    # Apply filter
    filtered_df = df[(df["Star Given"] >= rating[0]) & (df["Star Given"] <= rating[1])]
    if keyword:
        filtered_df = filtered_df[filtered_df["Review Text"].str.contains(keyword, case=False, na=False)]

    st.success(f"✨ Ditemukan **{len(filtered_df)}** ulasan setelah filter")

    # Tabel
    if show_table:
        st.markdown("### 🧾 Tabel Ulasan")
        st.dataframe(filtered_df[["Reviewer Name", "Publish Date", "Star Given", "Review Text"]], use_container_width=True)

    # Visualisasi berdasarkan filtered_df
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_rating_plot(filtered_df), use_container_width=True)
    with col2:
        st.plotly_chart(create_monthly_trend(filtered_df), use_container_width=True)

    # Kata paling sering berdasarkan filtered_df
    st.markdown("### 🔠 Kata Paling Sering Muncul")
    common_words = most_common_words(filtered_df["Review Text"])
    st.bar_chart(common_words.set_index("Kata"))

    # Unduh CSV
    csv = filtered_df.to_csv(index=False)
    st.download_button("⬇️ Unduh Data Filtered (CSV)", data=csv, file_name="filtered_reviews.csv", mime="text/csv")

else:
    st.info("⬆️ Upload file CSV dengan kolom: Reviewer Name, Review Text, Star Given, Publish Date.")
