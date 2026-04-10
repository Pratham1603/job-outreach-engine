import re
import time
import csv
import os
from serpapi import GoogleSearch
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import os

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

NOISE = {"hr", "m", "mr", "ms", "dr", "in"}


def extract_name_from_slug(url):
    match = re.search(r'linkedin\.com/in/([a-z0-9\-]+)', url)
    if not match:
        return None

    slug = match.group(1)
    slug = re.sub(r'-[0-9a-f]{6,}$', '', slug)
    slug = re.sub(r'\d+$', '', slug)

    parts = slug.replace("-", " ").strip().split()
    parts = [p for p in parts if p not in NOISE]

    if len(parts) >= 2:
        return " ".join(p.capitalize() for p in parts[:2])
    return None


def fetch_name_from_page(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.find("title")
        if title:
            name = title.text.split("-")[0].strip()
            if len(name.split()) >= 2:
                return name
    except Exception:
        pass
    return None


def get_linkedin_urls(company, role="HR", num=20):
    query = f'site:linkedin.com/in "{role}" "{company}"'
    print(f"[🔍] Query: {query}")

    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": num
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    urls = []

    for r in results.get("organic_results", []):
        link = r.get("link", "")
        if "linkedin.com/in/" in link:
            urls.append(link)

    print(f"[✓] Found {len(urls)} LinkedIn URLs")
    return urls


def scrape_hr_names(company, domain, num=20):
    urls = get_linkedin_urls(company, num=num)
    names = []
    seen = set()

    for url in urls:
        # Step 1 — try slug
        name = extract_name_from_slug(url)

        # Step 2 — fallback to page fetch
        if not name:
            print(f"  [~] Fetching page for: {url.split('/in/')[1]}")
            name = fetch_name_from_page(url)
            time.sleep(1.5)

        if name and name not in seen:
            seen.add(name)
            names.append({
                "name": name,
                "company": company,
                "domain": domain,
                "linkedin_url": url
            })
            print(f"  [✓] {name}")
        else:
            print(f"  [✗] SKIP ← {url.split('/in/')[1]}")

    return names


def export_csv(names, output_path="data/output/hr_names.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "company", "domain", "linkedin_url"])
        writer.writeheader()
        writer.writerows(names)
    print(f"\n[✓] Saved {len(names)} names → {output_path}")


if __name__ == "__main__":
    results = scrape_hr_names(
        company="Jio",
        domain="jio.com",
        num=20
    )
    export_csv(results)