# Talent Match Intelligence Dashboard

**Talent Match Intelligence Dashboard** is a data-driven HR analytics system that identifies and benchmarks top-performing employees using data exploration, SQL modeling, and AI-generated insights.

This project integrates **Supabase (PostgreSQL)**, **Streamlit**, and **OpenRouter (GPT-4)** to deliver interactive analytics, talent benchmarking, and AI-based job intelligence.

---

## Overview

The **Talent Match Intelligence Dashboard** helps organizations to:

- Identify key success patterns among high performers.  
- Benchmark employees based on behavioral, cognitive, and contextual indicators.  
- Generate AI-driven job descriptions and competency frameworks.  
- Visualize performance alignment and organizational strengths interactively.

This end-to-end pipeline was developed as part of a professional data analytics project under Rakamin Academy.

---

## System Architecture

| Component | Description |
|------------|-------------|
| **Python (Exploration)** | Data cleaning, feature engineering, and success pattern discovery (`exploration.ipynb`). |
| **Supabase (SQL)** | Operationalized benchmark scoring using median-based baseline logic. |
| **Streamlit App** | Interactive dashboard for HR analytics and visualization. |
| **OpenRouter API** | AI text generation for job requirements, key competencies, and ranked talent recommendations. |

---

## Key Features

- **Success Pattern Discovery** — Uncovers the traits and metrics that define top performers.  
- **SQL Benchmark Model** — Calculates employee match rates using median-based baseline comparison.  
- **AI Job Insights** — Generates contextual job descriptions and ranked talent lists using LLM prompts.  
- **Dynamic Visualization** — Displays match distributions, TGV strengths, and performance gaps across the organization.  

---

Deployment

The app is deployed on Hugging Face Spaces and connected securely to Supabase and OpenRouter APIs.

Public deployment link: [Streamlit Cloud](https://talent-match-intelligence-neilaism.streamlit.app/)

---

Credits

Developed by Neila Ismahunnisa