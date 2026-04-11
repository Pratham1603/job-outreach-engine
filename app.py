import streamlit as st
import pandas as pd
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

st.divider()

# --- TOP PATTERNS ---
TOP_PATTERNS = ["first.last", "firstlast", "flast", "f.last"]

st.divider()

# --- Run Button ---
if st.button("🔍 Find HR Emails", use_container_width=True, type="primary"):

    if not company or not domain:
        st.error("Please enter both company name and domain!")
        st.stop()

    # --- Progress UI ---
    log_placeholder = st.empty()
    logs = []

    def progress_callback(msg):
        logs.append(msg)
        log_placeholder.code("\n".join(logs[-10:]))

    # --- SCRAPING ---
    with st.status("🔍 Scraping LinkedIn profiles...", expanded=True) as status:

        st.write(f"Searching for HR profiles at {company}...")

        hr_names = scrape_hr_names(
            company,
            domain,
            progress_callback=progress_callback
        )

        if not hr_names:
            status.update(label="❌ No profiles found!", state="error")
            st.stop()

        st.write(f"✅ Found {len(hr_names)} HR profiles")

        # --- EMAIL GENERATION (MULTIPLE PATTERNS PER HR) ---
        st.write("📧 Generating email predictions...")

        all_emails = []

        for hr in hr_names:
            # skip invalid names
            if len(hr["name"].split()) < 2:
                continue

            emails = predict_emails(hr["name"], domain)

            # keep only top patterns
            emails = [e for e in emails if e["pattern"] in TOP_PATTERNS]

            all_emails.extend(emails)

        st.write(f"✅ Generated {len(all_emails)} email predictions")

        status.update(label="✅ Done!", state="complete")

    st.divider()

    # --- RESULTS ---
    st.subheader(f"Results — {company}")

    df = pd.DataFrame(all_emails)

    if df.empty:
        st.warning("No emails generated.")
        st.stop()

    # ✅ KEEP DUPLICATE REMOVAL
    df = df.drop_duplicates(subset=["email"])

    # --- Group by person ---
    for name in df["name"].unique():
        person_df = df[df["name"] == name][["pattern", "email"]]

        with st.expander(f"👤 {name}"):
            st.dataframe(person_df, hide_index=True, use_container_width=True)

    st.divider()

    # --- FULL TABLE ---
    st.subheader("📋 All Emails")
    st.dataframe(df, hide_index=True, use_container_width=True)

    # --- DOWNLOAD ---
    csv = df.to_csv(index=False)

    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name=f"{company.lower()}_hr_emails.csv",
        mime="text/csv",
        use_container_width=True
    )