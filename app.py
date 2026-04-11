import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from scraper.linkedin_scraper import scrape_hr_names
from predictor.email_predictor import predict_emails

load_dotenv()

st.set_page_config(
    page_title="Job Outreach Engine",
    page_icon="🎯",
    layout="centered"
)

st.title("🎯 Job Outreach Engine")
st.caption("Find HR emails from LinkedIn for cold job outreach")

st.divider()

# --- Inputs ---
col1, col2 = st.columns(2)
with col1:
    company = st.text_input("Company Name", placeholder="e.g. Jio")
with col2:
    domain = st.text_input("Company Domain", placeholder="e.g. jio.com")

# num_results = st.slider("Max LinkedIn profiles to scan", 5, 50, 10)

# --- Patterns ---
st.subheader("Email Patterns")
PATTERNS = [
    "first.last", "firstlast", "first_last",
    "flast", "f.last", "last.first", "firstname", "first.l"
]
selected_patterns = st.multiselect(
    "Select patterns to generate",
    options=PATTERNS,
    default=["first.last", "flast", "f.last", "firstlast"]
)

st.divider()

# --- Run Button ---
if st.button("🔍 Find HR Emails", use_container_width=True, type="primary"):
    if not company or not domain:
        st.error("Please enter both company name and domain!")
    elif not selected_patterns:
        st.error("Please select at least one email pattern!")
    else:
        # Step 1 — Scrape
        with st.status("Scraping LinkedIn profiles...", expanded=True) as status:
            st.write(f"Searching for HR profiles at {company}...")
            hr_names = scrape_hr_names(company, domain)

            if not hr_names:
                status.update(label="No profiles found!", state="error")
                st.stop()

            st.write(f"✅ Found {len(hr_names)} HR profiles")

            # Step 2 — Predict
            st.write("Generating email predictions...")
            all_emails = []
            for hr in hr_names:
                emails = predict_emails(hr["name"], domain)
                # Filter only selected patterns
                emails = [e for e in emails if e["pattern"] in selected_patterns]
                all_emails.extend(emails)

            st.write(f"✅ Generated {len(all_emails)} email predictions")
            status.update(label="Done!", state="complete")

        st.divider()

        # --- Results ---
        st.subheader(f"Results — {company}")

        df = pd.DataFrame(all_emails)

        # Show by person
        for name in df["name"].unique():
            person_df = df[df["name"] == name][["pattern", "email"]]
            with st.expander(f"👤 {name}"):
                st.dataframe(person_df, hide_index=True, use_container_width=True)

        st.divider()

        # --- Full Table ---
        st.subheader("All Emails")
        st.dataframe(df, hide_index=True, use_container_width=True)

        # --- Download ---
        csv = df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"{company.lower()}_hr_emails.csv",
            mime="text/csv",
            use_container_width=True
        )