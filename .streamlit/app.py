import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

st.set_page_config(
    page_title="Talent Match Intelligence",
    page_icon="🎯",
    layout="wide",
)

# Title
st.title("AI Talent Match Intelligence & Recommendation")

# Load dataset (offline mode)
try:
    df = pd.read_csv("src/expected_output_final.csv")
    st.success("Offline dataset loaded successfully.")
except FileNotFoundError:
    st.error("File 'expected_output_final.csv' not found. Please upload it to Hugging Face.")
    st.stop()

# Sidebar navigation
page = st.sidebar.selectbox(
    label="Select Page:",
    options=[
        "Home Page - Talent Match Intelligence",
        "Dashboard Visualization"
    ]
)

# OpenRouter API key
OPENROUTER_KEY = st.secrets.get("OPENROUTER_KEY", None)

# HOME PAGE
if page == "Home Page - Talent Match Intelligence":
    st.header("AI Job Recommendation Generator")

    # Role filter
    roles = sorted(df["role"].dropna().unique())
    selected_role = st.selectbox("Select Role", roles)

    # Grade level
    grades = sorted(df["grade"].dropna().unique())
    selected_grade = st.selectbox("Select Grade Level", grades)

    # Role purpose
    role_purpose = st.text_area(
        "Role Purpose",
        placeholder="e.g., Responsible for overseeing end-to-end project execution..."
    )

    # Benchmarking employees
    employee_ids = sorted(df["employee_id"].dropna().unique())
    selected_benchmarks = st.multiselect(
        "Select Employee Benchmarking (max 3)",
        options=employee_ids,
        max_selections=3
    )

    if st.button("Generate Job Description & Recommendations"):
        if not selected_benchmarks:
            st.warning("Please select at least one employee benchmark.")
        elif not OPENROUTER_KEY:
            st.error("Missing OpenRouter API key in secrets.")
        else:
            prompt = f"""
            You are an AI HR Analyst helping to define job standards for the role **{selected_role}** ({selected_grade} level).
            Role purpose: {role_purpose}

            The following employees are selected as performance benchmarks (IDs: {selected_benchmarks}).

            Based on their variable scores and competency profiles, generate:
            1. Job Requirements — education, skills, certifications.
            2. Job Description — 100–150 words, professional and concise.
            3. Key Competencies — top 5 traits observed across benchmarks.
            4. Ranked Talent List — order the benchmarks from strongest to weakest, with 1–2 reasons per ID.

            Return the response in Markdown format with headers and bullet points.
            """

            with st.spinner("Generating AI insights..."):
                try:
                    response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [{"role": "user", "content": prompt}],
                        },
                        timeout=60,
                    )
                    result = response.json()["choices"][0]["message"]["content"]
                    st.markdown(result)
                except Exception as e:
                    st.error(f"Error fetching AI recommendation: {e}")

# DASHBOARD VISUALIZATION
elif page == "Dashboard Visualization":
    st.header("Dashboard Visualization – Talent Match Insights")

    roles = sorted(df["role"].dropna().unique())
    selected_role = st.selectbox("Select Role to Visualize", roles)

    df_role = df[df["role"] == selected_role]
    if df_role.empty:
        st.warning("No data available for this role.")
    else:
        # Match Rate Distribution
        st.subheader("Match Rate Distribution")
        fig1 = px.histogram(df_role, x="final_match_rate", nbins=20, title="Distribution of Final Match Rate")
        st.plotly_chart(fig1, use_container_width=True)

        # TGV Strengths & Gaps
        st.subheader("Top Strengths and Gaps (TGV)")
        tgv_df = (
            df_role.groupby("tgv_name", as_index=False)
            .agg({"tgv_match_rate": "mean"})
            .sort_values("tgv_match_rate", ascending=False)
        )
        fig2 = px.bar(tgv_df, x="tgv_name", y="tgv_match_rate", text_auto=True)
        st.plotly_chart(fig2, use_container_width=True)

        # Summary Insights
        avg_score = df_role["final_match_rate"].mean().round(3)
        top_tgv = tgv_df.iloc[0]["tgv_name"]
        weakest_tgv = tgv_df.iloc[-1]["tgv_name"]

        st.markdown(f"""
        ### Summary Insights
        - Average Match Rate: **{avg_score}**
        - Strongest TGV: **{top_tgv}**
        - Weakest TGV: **{weakest_tgv}**
        """)

        # Radar Chart
        st.subheader("Benchmark vs Average Comparison")
        radar_df = df_role.groupby("tgv_name", as_index=False).agg({"tgv_match_rate": "mean"})
        fig3 = go.Figure()
        fig3.add_trace(go.Scatterpolar(
            r=radar_df["tgv_match_rate"],
            theta=radar_df["tgv_name"],
            fill='toself',
            name='Average Benchmark'
        ))
        fig3.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])))
        st.plotly_chart(fig3, use_container_width=True)
