import streamlit as st
import pandas as pd
from datetime import datetime

from preprocess import preprocess
from tachyon_classify import classify_with_tachyon
from cluster import cluster_other_comments

st.set_page_config(page_title="Client Feedback Classifier", layout="wide")
st.title("📋 Auto-Coding of Client Comments into Consistent Topics")

uploaded_file = st.file_uploader("📁 Upload VOC CSV File", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    st.sidebar.header("🕒 Time Filter")
    filter_option = st.sidebar.selectbox("Choose Time Range", ["All", "Last 7 Days", "Last 30 Days", "Last Quarter"])

    if filter_option == "Last 7 Days":
        df = df[df["timestamp"] >= pd.Timestamp.today() - pd.Timedelta(days=7)]
    elif filter_option == "Last 30 Days":
        df = df[df["timestamp"] >= pd.Timestamp.today() - pd.Timedelta(days=30)]
    elif filter_option == "Last Quarter":
        df = df[df["timestamp"] >= pd.Timestamp.today() - pd.Timedelta(days=90)]

    df["processed_text"] = df["comment_text"].apply(preprocess)
    df["category"] = df["processed_text"].apply(classify_with_tachyon)

    st.subheader("📊 Category Distribution")
    st.bar_chart(df["category"].value_counts())

    st.subheader("🧠 Emerging Themes from 'Other' Category")
    other_comments = df[df["category"] == "Other"]["processed_text"].tolist()
    if other_comments:
        labels = cluster_other_comments(other_comments, num_clusters=3)
        clustered_df = pd.DataFrame({"comment": other_comments, "cluster": labels})
        for cluster_id in sorted(clustered_df["cluster"].unique()):
            st.markdown(f"**Cluster {cluster_id + 1}**")
            samples = clustered_df[clustered_df["cluster"] == cluster_id]["comment"].head(3)
            for comment in samples:
                st.write(f"- {comment}")

    st.download_button("📥 Download Classified Comments", data=df.to_csv(index=False).encode("utf-8"),
                       file_name="classified_feedback.csv", mime="text/csv")