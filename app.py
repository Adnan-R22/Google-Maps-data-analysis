import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from collections import Counter
import re
from fpdf import FPDF
from io import BytesIO

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
    'nih', 'nya', 'cuma', 'hanya', 'the', 'and', 'but', 'was', 'with', 'you', 'are', 'not', 'very',
    'good', 'tempat', 'sangat', 'sekali', 'enak', 'banget', 'bintang', 'mantap', 'baik', 'banyak', 'buat', 'cukup', 'disini', 'tapi', 'kalau', 'pasti', 'untuk', 'dengan', 'saat', 'dapat', 'lagi', 'sudah', 'memang', 'pun', 'juga',
    'selama', 'serta', 'hingga', 'bahwa', 'tanpa', 'tentang'
}


# === FUNGSI PEMBANTU ===
def most_common_words(text_series, top_n=20):
    """Menghitung kata-kata yang paling sering muncul."""
    words = []
    for text in text_series.dropna():
        tokens = re.findall(r'\b\w{3,}\b', text.lower())
        filtered = [word for word in tokens if word not in stopwords]
        words.extend(filtered)
    counter = Counter(words)
    return pd.DataFrame(counter.most_common(top_n), columns=["Kata", "Frekuensi"])

def create_rating_plot(df):
    """Membuat histogram distribusi rating."""
    rating_counts = df['Star Given'].value_counts().sort_index().reset_index()
    rating_counts.columns = ['Rating', 'Jumlah']
    color_map = {1: '#EF5350', 2: '#FFCA28', 3: '#FFEE58', 4: '#66BB6A', 5: '#43A047'}
    fig = px.bar(rating_counts, x="Rating", y="Jumlah", title="Distribusi Rating", 
                 color='Rating', color_discrete_map=color_map,
                 labels={'Rating': 'Bintang', 'Jumlah': 'Jumlah Ulasan'}, text='Jumlah')
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(xaxis_title="Bintang", yaxis_title="Jumlah Ulasan")
    return fig

def create_monthly_trend(df):
    """Membuat plot garis tren ulasan per bulan."""
    df["Month"] = df["Publish Date"].dt.to_period("M").astype(str)
    trend = df.groupby("Month").size().reset_index(name="Jumlah Review")
    fig = px.line(trend, x="Month", y="Jumlah Review", markers=True, title="Tren Jumlah Review per Bulan",
                  color_discrete_sequence=px.colors.qualitative.Plotly, labels={'Month': 'Bulan', 'Jumlah Review': 'Jumlah Ulasan'})
    fig.update_traces(marker=dict(size=10))
    return fig

def generate_summary(df):
    """Menghasilkan ringkasan dari data ulasan."""
    total_reviews = len(df)
    if total_reviews == 0:
        return "Tidak ada data ulasan untuk dianalisis."
    average_rating = df["Star Given"].mean()
    most_common_rating = df["Star Given"].mode().iloc[0] if not df["Star Given"].mode().empty else "N/A"
    df_monthly_avg = df.groupby(df['Publish Date'].dt.to_period('M'))['Star Given'].mean().reset_index()
    df_monthly_avg['Publish Date'] = df_monthly_avg['Publish Date'].astype(str)
    trend_summary = ""
    if len(df_monthly_avg) > 1:
        first_month_avg = df_monthly_avg.iloc[0]['Star Given']
        last_month_avg = df_monthly_avg.iloc[-1]['Star Given']
        if last_month_avg > first_month_avg:
            trend_summary = f"Tren rating menunjukkan peningkatan dari **{first_month_avg:.2f}** menjadi **{last_month_avg:.2f}**."
        elif last_month_avg < first_month_avg:
            trend_summary = f"Tren rating menunjukkan penurunan dari **{first_month_avg:.2f}** menjadi **{last_month_avg:.2f}**."
        else:
            trend_summary = "Tren rating relatif stabil."
    summary_text = f"""
    ### 📝 Kesimpulan Analisis Ulasan

    Berdasarkan data yang difilter, terdapat total **{total_reviews} ulasan**.
    * **Rating Rata-Rata:** Rata-rata bintang yang diberikan adalah **{average_rating:.2f} dari 5**.
    * **Rating Paling Umum:** Rating yang paling sering diberikan adalah **{most_common_rating} bintang**.
    * **Tren Rating:** {trend_summary}
    Analisis kata-kata yang sering muncul juga bisa memberikan wawasan lebih lanjut tentang area yang perlu diperhatikan atau dipertahankan.
    """
    return summary_text

def generate_pdf_report(filtered_df, common_words, summary_text):
    """Menghasilkan laporan PDF dari konten dashboard."""
    # 1. Muat (load) font Unicode (DejaVuSans)
    try:
        pdf = FPDF(format='A4', unit='mm')
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 12)
    except Exception as e:
        st.error(f"Gagal memuat font DejaVuSans.ttf. Pastikan file ada di folder yang sama. Error: {e}")
        pdf = FPDF(format='A4', unit='mm')
        pdf.set_font('Helvetica', '', 12)
        st.warning("Laporan PDF mungkin tidak menampilkan karakter khusus dengan benar.")

    pdf.add_page()
    
    # 2. Tambahkan Judul dan Ringkasan
    pdf.set_font("Helvetica", "B", size=16)
    pdf.cell(200, 10, txt="Laporan Hasil Analisis Google Maps", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font('DejaVu', '', 12)
    clean_summary = summary_text.replace('**', '').replace('###', '').strip()
    pdf.multi_cell(0, 8, txt=clean_summary)
    pdf.ln(10)

    # 3. Tambahkan Grafik sebagai Gambar
    
    # Grafik Distribusi Rating
    if pdf.get_y() > 200: pdf.add_page()
    pdf.set_font("Helvetica", "B", size=14)
    pdf.cell(200, 10, txt="Distribusi Rating", ln=True, align="L")
    pdf.ln(5)
    rating_fig = create_rating_plot(filtered_df)
    img_buffer_rating = BytesIO()
    rating_fig.write_image(img_buffer_rating, format='png', engine="kaleido")
    pdf.image(img_buffer_rating, x=10, y=pdf.get_y(), w=180)
    pdf.ln(90)

    # Grafik Tren Bulanan
    if not filtered_df.empty:
        if pdf.get_y() > 200: pdf.add_page()
        pdf.set_font("Helvetica", "B", size=14)
        pdf.cell(200, 10, txt="Tren Jumlah Review per Bulan", ln=True, align="L")
        pdf.ln(5)
        trend_fig = create_monthly_trend(filtered_df)
        img_buffer_trend = BytesIO()
        trend_fig.write_image(img_buffer_trend, format='png', engine="kaleido")
        pdf.image(img_buffer_trend, x=10, y=pdf.get_y(), w=180)
        pdf.ln(90)

    # Grafik Kata Paling Sering Muncul
    if not common_words.empty:
        if pdf.get_y() > 200: pdf.add_page()
        pdf.set_font("Helvetica", "B", size=14)
        pdf.cell(200, 10, txt="Kata Paling Sering Muncul", ln=True, align="L")
        pdf.ln(5)
        word_fig = px.bar(common_words, x='Kata', y='Frekuensi')
        img_buffer_word = BytesIO()
        word_fig.write_image(img_buffer_word, format='png', engine="kaleido")
        pdf.image(img_buffer_word, x=10, y=pdf.get_y(), w=180)
        pdf.ln(90)

    # TIDAK ADA BAGIAN TABEL

    # 5. Output PDF
    pdf_output = bytes(pdf.output(dest='S'))
    return pdf_output


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

    # Apply filter
    filtered_df = df[(df["Star Given"] >= rating[0]) & (df["Star Given"] <= rating[1])]
    if keyword:
        filtered_df = filtered_df[filtered_df["Review Text"].str.contains(keyword, case=False, na=False)]

    st.success(f"✨ Ditemukan **{len(filtered_df)}** ulasan setelah filter")

    # Visualisasi
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_rating_plot(filtered_df), use_container_width=True)
    with col2:
        st.plotly_chart(create_monthly_trend(filtered_df), use_container_width=True)

    # Tambahkan pemisah yang jelas untuk jarak
    st.divider() 

    # Kesimpulan
    st.markdown("---")
    summary_text = generate_summary(filtered_df)
    st.markdown(summary_text)
    st.markdown("---")

    # Kata paling sering berdasarkan filtered_df
    st.markdown("### 🔠 Kata Paling Sering Muncul")
    common_words = most_common_words(filtered_df["Review Text"])
    st.bar_chart(common_words.set_index("Kata"))

    # Unduh CSV
    csv = filtered_df.to_csv(index=False)
    st.download_button("⬇️ Unduh Data Filtered (CSV)", data=csv, file_name="filtered_reviews.csv", mime="text/csv")
    
    # --- BAGIAN UNDUH LAPORAN PDF ---
    st.markdown("---")
    st.markdown("### 📥 Unduh Laporan Lengkap (PDF)")
    
    # Panggil fungsi untuk membuat laporan PDF dan sediakan tombol unduh
    pdf_data = generate_pdf_report(filtered_df, common_words, summary_text)
    st.download_button(
        label="⬇️ Unduh Laporan PDF",
        data=pdf_data,
        file_name="Laporan_Dashboard.pdf",
        mime="application/pdf"
    )

else:
    st.info("⬆️ Upload file CSV dengan kolom: Reviewer Name, Review Text, Star Given, Publish Date.")