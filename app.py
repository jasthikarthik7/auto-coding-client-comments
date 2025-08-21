# ===============================
# app.py  (modularized)
# ===============================
# Imports  (from your original L1–18)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from tachyon import generate
import json
from streamlit.web import cli
from io import StringIO
from datetime import datetime, timedelta
from preprocess import preprocess
import re
from matplotlib.ticker import FuncFormatter

# -------------------------------
# Cached loaders / core pipeline
# -------------------------------

# from your original L14–23
@st.cache_data
def load_themes_config():
    try:
        with open("themes_config.json", "r") as f:
            themes_config = json.load(f)
            print("themes configuration loaded successfully")
            return themes_config
    except Exception as e:
        st.error(f"Failed to load themes configuration: {e}")
        return {}

# from your original L26–86 (preprocess_and_classify + JSON-parse)
@st.cache_data
def preprocess_and_classify(uploaded_file, themes_config):
    try:
        df = pd.read_csv(uploaded_file, encoding="ISO-8859-1", parse_dates=["timestamp"])
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")

    df["processed_text"] = df["comment_text"].apply(preprocess)

    # messages (from L37–47)
    comments = df["processed_text"].tolist()
    themes = list(themes_config.keys()) + ["not_matched"]

    user_message = {
        "role": "user",
        "content": "\n".join(comments)
    }

    # system prompt (from L49–74)
    system_prompt = {
        "role": "system",
        "content": (
            "You are a themes classifier.\n"
            "Classify the following user comments into one of the defined themes.\n"
            "If it matches more than one, choose only one theme.\n"
            "These are the possible themes:\n"
            "\n".join(themes) + "\n"
            "Also do the sentiment analysis of the comment. Find out the financial product linked to the comment if a detail is available.\n"
            "Respond in the following JSON format:\n"
            "[ { \"comment\": \"<comment>\", \"themes\": \"<primary theme>\", \"sentiment\": \"<sentiment>\", \"product\": \"<product>\" },\n"
            "]\n"
            "If no match is found for a comment, try to come up with a high level theme for the comment.Put a star mark in that new theme"
        )
    }

    chat_history = [system_prompt, user_message]

    try:
        raw_response = generate(chat_history).strip()
        print("RAW Response :", raw_response)

        # Find JSON (your L76–84)
        json_start = raw_response.find('[')
        json_end   = raw_response.rfind(']') + 1
        if json_start == -1 or json_end == 0:
            parsed = json.loads(raw_response)
        else:
            parsed = json.loads(raw_response[json_start:json_end])

        # Convert to DataFrame (your L87–95)
        parsed_df = pd.DataFrame(parsed)
        df["themes"]    = parsed_df["themes"]
        df["sentiment"] = parsed_df["sentiment"]
        df["product"]   = parsed_df["product"]
        return df

    except Exception as e:
        print(f"Failed to convert raw_response to DataFrame: {str(e)}")
        return df  # keep original behavior of falling through (no structural change)

# -------------------------------
# UI helpers (pure rearrangement)
# -------------------------------

# from L89–105 (page + header + uploader)
def setup_page():
    st.set_page_config(
        page_title="LLM Powered VOC Themes Classifier",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("Voice of Customer Classification")
    st.markdown("<h1 style='text-align: center;'>✨ LLM Powered VOC Themes Classifier</h1>", unsafe_allow_html=True)

def upload_csv():
    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"], key="file_upload")
    upload_success = uploaded_file is not None and uploaded_file.name.endswith(".csv")
    if not upload_success:
        st.info("Please upload a CSV file to proceed.")
        return None
    st.success("The attached CSV file was uploaded successfully.")
    return uploaded_file

# from L106–120 (calling pipeline + session_state)
def get_or_build_classified_df(uploaded_file):
    if "classified_df" not in st.session_state:
        try:
            themes_config = load_themes_config()
            processed_df = preprocess_and_classify(uploaded_file, themes_config)
            processed_df = processed_df.drop(columns=["processed_text"])
            st.session_state["classified_df"] = processed_df
        except Exception as e:
            st.error(f"Error processing file: {e}")
    return st.session_state.get("classified_df", None)

# from L121–160 (sidebar filters)
def render_sidebar_filters(df):
    st.sidebar.header("🔎 Filters")
    if df is None:
        return None, None, None, None, None

    selected_themes   = st.sidebar.selectbox("By Theme", options=["All"] + df["themes"].unique().tolist())
    time_filter       = st.sidebar.selectbox("By Time Period", options=["All", "Last 7 days", "Last 1 month", "Last 3 months"])
    selected_group    = st.sidebar.selectbox("By Group", options=["All"] + df.get("group", pd.Series(dtype=str)).unique().tolist())
    selected_sentiment= st.sidebar.selectbox("By Sentiment", options=["All"] + df["sentiment"].unique().tolist())
    selected_product  = st.sidebar.selectbox("By Product", options=["All"] + df["product"].unique().tolist())

    # your code uses `column` as a flag to draw charts later
    column = "themes"
    return selected_themes, time_filter, selected_group, selected_sentiment, selected_product, column

# from L133–158 (apply filters)
def apply_filters(df, selected_themes, time_filter, selected_group, selected_sentiment, selected_product):
    if df is None:
        return None
    filtered_df = df.copy()

    if selected_themes != "All":
        filtered_df = filtered_df[filtered_df["themes"] == selected_themes]

    now = datetime.now()
    if time_filter == "Last 7 days":
        filtered_df = filtered_df[filtered_df["timestamp"] >= now - timedelta(days=7)]
    elif time_filter == "Last 1 month":
        filtered_df = filtered_df[filtered_df["timestamp"] >= now - timedelta(days=30)]
    elif time_filter == "Last 3 months":
        filtered_df = filtered_df[filtered_df["timestamp"] >= now - timedelta(days=90)]

    if selected_group != "All":
        filtered_df = filtered_df[filtered_df["group"] == selected_group]

    if selected_sentiment != "All":
        filtered_df = filtered_df[filtered_df["sentiment"] == selected_sentiment]

    if selected_product != "All":
        filtered_df = filtered_df[filtered_df["product"] == selected_product]

    return filtered_df

# from L160–206 (table + pie + stacked bar)
def render_tables_and_charts(filtered_df, column):
    if filtered_df is None:
        return

    st.dataframe(filtered_df)
    st.markdown("---")

    if column:
        st.markdown("### 📊 Themes Distribution")
        themes_counts  = filtered_df["themes"].value_counts()
        themes_percent = (themes_counts / len(filtered_df) * 100).round(1).astype(str) + '%'
        themes_summary = themes_percent.reset_index()
        themes_summary.columns = ["Themes", "Percentage of Comments"]
        st.table(themes_summary)

        st.markdown("### 🥧 Themes Pie Chart")
        fig_pie, ax_pie = plt.subplots(figsize=(10, 4))
        ax_pie.pie(themes_counts, labels=themes_counts.index, startangle=90)
        ax_pie.axis("equal")
        fig_pie.patch.set_alpha(0)
        for text in ax_pie.texts:
            text.set_color("white")
        st.pyplot(fig_pie)

        # stacked over time (L186–206)
        filtered_theme_df = filtered_df.copy()
        filtered_theme_df["month"] = filtered_theme_df["timestamp"].dt.to_period("M").dt.to_timestamp()
        theme_counts = filtered_theme_df.groupby(["month", "themes"]).size().unstack(fill_value=0)
        theme_percentages = theme_counts.div(theme_counts.sum(axis=1), axis=0) * 100

        fig_time_theme, ax = plt.subplots(figsize=(12, 5))
        theme_percentages.plot(kind="bar", stacked=True, ax=ax)
        ax.set_ylabel("Percentage of Comments")
        ax.set_xlabel("Month")
        ax.set_title("Themes Distribution Over Time (Monthly %)")
        ax.set_ylim(0, 100)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.0f}%'))
        ax.set_xticklabels([d.strftime('%b %Y') for d in theme_percentages.index], rotation=45)
        ax.legend(title="Themes", bbox_to_anchor=(1.05, 1), loc="upper left")
        st.pyplot(fig_time_theme)

# from L206–231 (KPIs + sentiment chart)
def render_kpis(filtered_df):
    if filtered_df is None:
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🧮 Total Number of Comments")
        total_comments = len(filtered_df)
        fig2, ax2 = plt.subplots(figsize=(5, 4))
        ax2.pie([total_comments], startangle=90)
        ax2.axis("equal")
        ax2.text(0, 0, f"{total_comments}\n total comments", ha="center", va="center", fontsize=14, fontweight="bold")
        st.pyplot(fig2)

    with col2:
        st.markdown("### 🙂 Sentiment Distribution")
        fig_sentiment, ax_sentiment = plt.subplots(figsize=(5, 5))
        filtered_df["sentiment"].value_counts().plot(kind="bar", ax=ax_sentiment)
        ax_sentiment.set_xlabel("Sentiment")
        ax_sentiment.set_ylabel("Number of Comments")
        st.pyplot(fig_sentiment)

    print(st.session_state["classified_df"])

# from L231–252 (reset + download)
def render_download_and_reset(filtered_df):
    if filtered_df is None:
        return

    colA, colB, colC = st.columns([1, 2, 1])
    with colB:
        col1, col2 = st.columns(2)

        with col1:
            reset_clicked = st.button(" Reset", use_container_width=True)

        with col2:
            download_clicked = st.download_button(
                label="Download Processed CSV",
                data=filtered_df.to_csv(index=False),
                file_name="processed_data.csv",
                mime="text/csv"
            )

    if 'reset_clicked' in locals() and reset_clicked:
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.cache_data.clear()
        st.rerun()
        st.toast("UI reset successfully")

# -------------------------------
# Entry point (ties everything)
# -------------------------------
def main():
    setup_page()

    uploaded_file = upload_csv()
    if not uploaded_file:
        return

    df = get_or_build_classified_df(uploaded_file)
    if df is None:
        return

    selected_themes, time_filter, selected_group, selected_sentiment, selected_product, column = render_sidebar_filters(df)
    filtered_df = apply_filters(df, selected_themes, time_filter, selected_group, selected_sentiment, selected_product)

    st.dataframe(filtered_df)
    st.markdown("---")

    render_tables_and_charts(filtered_df, column)
    render_kpis(filtered_df)
    st.markdown("### ")
    st.markdown("---")
    render_download_and_reset(filtered_df)

if __name__ == "__main__":
    main()
