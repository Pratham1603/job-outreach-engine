# 🎯 Job Outreach Engine

Predict HR email addresses from public names + company domains for cold job outreach.

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Personal Use](https://img.shields.io/badge/use-personal%20only-orange)

## What this does

- Takes HR names (from LinkedIn search) + company domain
- Generates all common corporate email patterns
- Exports a clean CSV ready for outreach
- Google dork-based name discovery — no direct scraping

## Email patterns supported

```
first.last@company.com
firstlast@company.com
first_last@company.com
flast@company.com
f.last@company.com
last.first@company.com
firstname@company.com
first.l@company.com
```

## Project structure

```
job-outreach-engine/
├── scraper/
│   └── linkedin_scraper.py   # Google dork-based HR name finder
├── predictor/
│   └── email_predictor.py    # Pattern generation + CSV export
├── data/
│   ├── companies.txt         # Input: one company per line
│   └── output/               # Generated email CSVs
├── requirements.txt
└── README.md
```

## Quick start

```bash
git clone https://github.com/yourusername/job-outreach-engine
cd job-outreach-engine
pip install -r requirements.txt

# Add HR names manually or run scraper
python predictor/email_predictor.py --name "Priya Sharma" --domain "jio.com"
```

## Output example

```
Name,Pattern,Email
Priya Sharma,first.last,priya.sharma@jio.com
Priya Sharma,flast,psharma@jio.com
Priya Sharma,firstlast,priyasharma@jio.com
```

## Future scope

- Email verification via SMTP ping
- Auto email sender (Gmail API)
- Hunter.io / RocketReach API integration
- Web UI (Streamlit)

## Disclaimer

This tool is for **personal/educational use only**. Only use publicly available information. Respect LinkedIn's Terms of Service. The author is not responsible for misuse.