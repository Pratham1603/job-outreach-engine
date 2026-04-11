import re
import time
import csv
import os
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

def parse_name_from_title(title: str) -> str | None:
    if not title:
        return None

    title = title.replace("...", "").strip()

    name = title.split(" - ")[0].strip()

    name = re.sub(r'^(Dr\.|Mr\.|Ms\.|Mrs\.|Capt\.)\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r',?\s*(Ph\.?D\.?|MBA|BBA|SHRMCP|PHR).*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^a-zA-Z\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()

    words = name.split()

    if len(words) >= 2:
        first = words[0]
        last = words[1]

        if len(last) >= 1:
            return f"{first} {last}"

    return None


def scrape_hr_names(company: str, domain: str, roles: list = None, progress_callback=None) -> list:
    print(f"\n[🔍] Scraping profiles for: {company}")

    # Build query and keyword filter from roles
    if not roles:
        roles = ["HR", "Human Resources", "Talent Acquisition"]

    role_query = " OR ".join([f'"{r}"' for r in roles])
    role_keywords = [r.lower() for r in roles]

    all_names = []
    seen = set()
    start = 0
    page = 1

    while True:
        msg = f"📄 Fetching page {page} (start={start})..."
        print(msg)

        if progress_callback:
            progress_callback(msg)

        params = {
            "engine": "google",
            "q": f'site:linkedin.com/in ({role_query}) "{company}"',
            "api_key": SERPAPI_KEY,
            "num": 10,
            "start": start,
            "hl": "en"
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
        except Exception as e:
            print(f"  [!] API error: {e}")
            break

        organic = results.get("organic_results", [])

        if not organic:
            print(f"  [✓] No more results at page {page} — stopping")
            break

        for r in organic:
            title = r.get("title", "")
            link  = r.get("link", "")

            if "linkedin.com/in/" not in link:
                continue

            title_lower = title.lower()

            if company.lower() not in title_lower:
                continue

            # Filter using dynamic role keywords
            if not any(kw in title_lower for kw in role_keywords):
                continue

            name = parse_name_from_title(title)

            if name and name not in seen:
                seen.add(name)
                all_names.append({
                    "name": name,
                    "company": company,
                    "domain": domain,
                    "linkedin_url": link,
                    "title": title
                })
                print(f"  [✓] {name:<30} ← {title}")
            else:
                print(f"  [✗] SKIP ← {title}")

        if len(organic) < 5:
            print(f"  [✓] Last page reached — stopping")
            break

        start += 10
        page += 1
        time.sleep(1.5)

    print(f"\n[✓] Total profiles found: {len(all_names)}")
    return all_names


def export_names_csv(names: list, output_path: str = "data/output/hr_names.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "company", "domain", "linkedin_url", "title"])
        writer.writeheader()
        writer.writerows(names)
    print(f"[✓] Saved {len(names)} names → {output_path}")