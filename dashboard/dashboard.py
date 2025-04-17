import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import streamlit as st
from babel.numbers import format_currency
sns.set(style='dark')

def create_hourly_rentals_df(df):
    max_date = df.loc[df["cnt"].idxmax()]
    top_date = max_date["dteday"]
    top_day_df = df[df["dteday"] == top_date].copy()
    top_day_df["Hour"] = top_day_df["hr"] + 1
    tabel_jam = top_day_df[["Hour", "cnt", "casual", "registered"]].rename(columns={
        "Hour": "Jam",
        "cnt": "Jumlah Penyewaan",
        "casual": "Jumlah Penyewaan Casual",
        "registered": "Jumlah Penyewaan Terdaftar"
    })
    return tabel_jam, pd.to_datetime(top_date)

    
def create_monthly_trend_df(df):
    df["dteday"] = pd.to_datetime(df["dteday"])
    monthly_trend_df = df.resample(rule='ME', on='dteday').agg({
        "cnt": "sum"
    })
    df["dteday"] = pd.to_datetime(df["dteday"])
    monthly_trend_df.index = monthly_trend_df.index.strftime('%Y-%m')
    monthly_trend_df = monthly_trend_df.reset_index()
    monthly_trend_df.rename(columns={
        "dteday": "year_month",
        "cnt": "total_rentals"
    }, inplace=True)
    return monthly_trend_df
    


def create_bins_df(df):
    if df.empty or df["cnt"].isna().all():
        return pd.Series(dtype='int')
    max_cnt = df["cnt"].max()
    if max_cnt <= 2500:
        bins = [0, max_cnt + 1]
        labels = ["Rendah"]
    elif max_cnt <= 5000:
        bins = [0, 2500, max_cnt + 1]
        labels = ["Rendah", "Sedang"]
    else:
        bins = [0, 2500, 5000, max_cnt + 1]
        labels = ["Rendah", "Sedang", "Tinggi"]
        
    df["rental_category"] = pd.cut(df["cnt"], bins=bins, labels=labels, include_lowest=True)
    rental_counts = df["rental_category"].value_counts()
    return rental_counts
   
day_df = pd.read_csv("dashboard/day_df.csv")
hour_df = pd.read_csv("dashboard/hour_df.csv")

with st.sidebar:
    weathersit_option = st.selectbox(
        label="Pilih Kondisi Cuaca",
        options=["All", "1", "2", "3", "4"])
weather_map = {
    "1": 1,      
    "2": 2,        
    "3": 3, 
    "4": 4   }

filtered_day_df = day_df.copy()
filtered_hour_df = hour_df.copy()


if weathersit_option != "All":
    selected_weather = weather_map[weathersit_option]
    filtered_day_df = day_df[day_df["weathersit"] == selected_weather]
    filtered_hour_df = hour_df[hour_df["weathersit"] == selected_weather]
    
selected_option = st.sidebar.radio(
    "Pilih Tren yang Ingin Ditampilkan:",
    ("Tren Penyewaan per Bulan", "Tren Penyewaan Jam", "Distribusi Penyewaan Sepeda Berdasarkan Jumlah Per Hari")
)


if selected_option == "Tren Penyewaan per Bulan":
    st.subheader('Tren Penyewaan Sepeda per Bulan')
    if filtered_day_df.empty:
        st.warning("Data tidak tersedia untuk kondisi cuaca yang dipilih.")
    else:
        monthly_trend_df = create_monthly_trend_df(filtered_day_df)

        max_month = monthly_trend_df.loc[monthly_trend_df["total_rentals"].idxmax()]
        st.metric("Tren teritinggi pada Bulan", value=str(max_month["year_month"]))
    
        fig, ax = plt.subplots(figsize=(12, 10))
        ax.set_facecolor('white') 
    
        ax.plot(
          monthly_trend_df["year_month"], monthly_trend_df["total_rentals"],
          label="total_rentals", 
          color="#FF9999",
          marker="o", 
          linewidth=2.5
          )
    
    
        ax.set_title(f"Penyewaan Sepeda Per Bulan Sejak 2021", pad=20, fontsize=14)
        ax.set_xlabel("Bulan", labelpad=10)
        ax.set_ylabel("Jumlah Penyewaan", labelpad=10)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', alpha=0.3, color='gray')
        ax.legend(loc='upper left')
        
        fig.tight_layout()
        st.pyplot(fig)

if selected_option == "Tren Penyewaan Jam":
    hourly_trend_df, top_date = create_hourly_rentals_df(filtered_hour_df)
    st.subheader("Tren Penyewaan Sepeda Berdasarkan Jam")

    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_facecolor('white') 
    ax.plot(
        hourly_trend_df["Jam"], hourly_trend_df["Jumlah Penyewaan"],
        label="Total Penyewaan", color="#72BCD4",
        marker="o", linewidth=2.5
    )
    ax.plot(
        hourly_trend_df["Jam"], hourly_trend_df["Jumlah Penyewaan Terdaftar"],
        label="Registered", color="#66B3FF",
        linestyle="--", marker="s", linewidth=2
    )
    ax.plot(
        hourly_trend_df["Jam"], hourly_trend_df["Jumlah Penyewaan Casual"],
        label="Casual", color="#FF9999",
        linestyle="--", marker="^", linewidth=2
    )   
    ax.set_title(f"Penyewaan Sepeda per Jam pada {top_date.strftime('%d %B %Y')}", pad=20, fontsize=14)
    ax.set_xlabel("Jam ke-", labelpad=10)
    ax.set_ylabel("Jumlah Penyewaan", labelpad=10)
    ax.set_xticks(range(0, 25))
    ax.set_yticks(range(0, 1001, 50))
    ax.grid(axis='y', alpha=0.3, color='gray')
    ax.legend(loc='upper left')   
    fig.tight_layout()
    st.pyplot(fig)

if selected_option == "Distribusi Penyewaan Sepeda Berdasarkan Jumlah Per Hari":
    st.subheader("Distribusi Penyewaan Sepeda Berdasarkan Jumlah Per Hari")
    if filtered_day_df.empty:
        st.warning("Data tidak tersedia untuk kondisi cuaca yang dipilih.")
    else:
        rental_counts = create_bins_df(filtered_day_df)
        rental_counts = rental_counts.reindex(["Rendah", "Sedang", "Tinggi"], fill_value=0)
        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(rental_counts, labels=rental_counts.index, autopct="%1.1f%%", 
        colors=["#ff9999", "#66b3ff", "#99ff99"], startangle=140)
        legend_labels = [
            f" Rendah (<2500)",
            f" Sedang (2500–5000)",
            f" Tinggi (>5000)"
        ]
        ax.legend(wedges, legend_labels, title="Kategori", loc="center left", bbox_to_anchor=(1, 0.5))
        st.pyplot(fig)

