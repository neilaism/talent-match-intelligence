import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# Page Config
st.set_page_config(
    page_title="Talent Match Intelligence",
    page_icon="🎯",
    layout="wide",
)
# Sidebar navigation
page = st.sidebar.selectbox(
    label="Select Page:",
    options=[
        "Home Page - Talent Match Intelligence",
        "Dashboard Visualization"
    ]
)

# Supabase Setup
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# AI Recommendation
OPENROUTER_KEY = st.secrets["OPENROUTER_KEY"]

if page == "Home Page - Talent Match Intelligence":
    # Title
    st.title("🎯 AI Talent Match Intelligence & Recommendation")

    # Role filter
    roles = supabase.table("expected_output_final").select("role").execute()
    unique_roles = sorted({r["role"] for r in roles.data if r["role"]})
    selected_role = st.selectbox("Select Role", unique_roles)

    # Grade level
    grades = supabase.table("expected_output_final").select("grade").execute()
    unique_grades = sorted({r["grade"] for r in grades.data if r["grade"]})
    selected_grade = st.selectbox("Select Grade Level", unique_grades)

    # Role Purpose
    role_purpose = st.text_area(
        "Role Purpose",
        placeholder="e.g., Responsible for overseeing end-to-end project execution...",
    )

    # Employee Benchmarking
    try:
        # Ambil semua employee_id dari tabel
        employees = supabase.table("expected_output_final").select("employee_id").execute()

        # Ambil unique employee IDs
        employee_ids = sorted(list({e["employee_id"] for e in employees.data if e.get("employee_id")}))

    except Exception as ex:
        st.error(f"Error fetching employee list: {ex}")
        employee_ids = []

    if not employee_ids:
        st.warning("⚠️ No employee data found.")
    else:
        selected_benchmarks = st.multiselect(
            "Select Employee Benchmarking (max 3)",
            options=employee_ids,
            max_selections=3,
        )

    if st.button("Generate Job Description & Variable Score"):
        if not selected_benchmarks:
            st.warning("Please select at least one employee benchmark (max 3).")
        else:
            benchmark_ids = selected_benchmarks

            # Fetch expected output data
            df = pd.DataFrame(
                supabase.table("expected_output_final")
                .select("*")
                .in_("employee_id", benchmark_ids)
                .execute()
                .data
            )

            if df.empty:
                st.warning("No data found for selected benchmarks in expected_output_final.")
            else:
                # Aggregate & sort
                agg_df = (
                    df.groupby(["employee_id", "role", "grade", "directorate"], as_index=False)
                    .agg({"final_match_rate": "max"})
                    .sort_values("final_match_rate", ascending=False)
                )

                topk = agg_df.to_dict(orient="records")

                # Prompt
                prompt = f"""
                You are an AI HR Analyst helping to define job standards for the role **{selected_role}** ({selected_grade} level).

                Role purpose: {role_purpose}

                The following employees are selected as performance benchmarks (by ID): {benchmark_ids}.

                Based on their variable scores and competency profiles, generate:

                1️**Job Requirements** — education, skills, certifications.  
                2**Job Description** — 100–150 words, professional and concise.  
                3️**Key Competencies** — top 5 traits observed across benchmarks.  
                4️**Ranked Talent List** — order the benchmarks from strongest to weakest, with 1–2 reasons per ID.

                Return the response in clear Markdown format with headers and bullet points.
                            """

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
                    ai_output = response.json()["choices"][0]["message"]["content"]
                    st.markdown(ai_output)
                except Exception as e:
                    st.error(f"Error calling AI API: {e}")

elif page == "Dashboard Visualization":
    st.title("Visualization Dashboard – Talent Match Insights")
    st.markdown("---")

    # filter role
    roles = supabase.table("expected_output_final").select("role").execute()
    unique_roles = sorted({r["role"] for r in roles.data if r["role"]})
    selected_role = st.selectbox("Select Role to Visualize", unique_roles)

    df = pd.DataFrame(
        supabase.table("expected_output_final").select("*").eq("role", selected_role).execute().data
    )

    if df.empty:
        st.warning("No data available for this role.")
    else:
        # 1MATCH RATE DISTRIBUTION
        st.subheader("Match Rate Distribution")
        fig1 = px.histogram(df, x="final_match_rate", nbins=20, title="Distribution of Final Match Rate")
        st.plotly_chart(fig1, use_container_width=True)

        # TGV STRENGTHS & GAPS
        tgv_df = (
            df.groupby("tgv_name", as_index=False)
            .agg({"tgv_match_rate": "mean"})
            .sort_values("tgv_match_rate", ascending=False)
        )
        st.subheader("Top Strengths and Gaps (TGV)")
        fig2 = px.bar(tgv_df, x="tgv_name", y="tgv_match_rate", text_auto=True)
        st.plotly_chart(fig2, use_container_width=True)

        # SUMMARY INSIGHTS
        avg_score = df["final_match_rate"].mean().round(3)
        top_tgv = tgv_df.iloc[0]["tgv_name"]
        weakest_tgv = tgv_df.iloc[-1]["tgv_name"]

        st.markdown(f"""
        ### Summary Insights
        - Average match rate: **{avg_score}**
        - Strongest TGV: **{top_tgv}**
        - Weakest TGV: **{weakest_tgv}**
        """)

        # RADAR CHART BENCHMARK VS AVG
        st.subheader("Benchmark vs Average Comparison")
        radar_df = df.groupby("tgv_name", as_index=False).agg({"tgv_match_rate": "mean"})
        fig3 = go.Figure()
        fig3.add_trace(go.Scatterpolar(
            r=radar_df["tgv_match_rate"],
            theta=radar_df["tgv_name"],
            fill='toself',
            name='Average Benchmark',
        ))
        fig3.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])))
        st.plotly_chart(fig3, use_container_width=True)