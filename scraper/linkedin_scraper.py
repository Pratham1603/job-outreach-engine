import re
import time
import csv
import os
import requests
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")


# ── Name parser ───────────────────────────────────────────────
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
        if len(words[1]) >= 1:
            return f"{words[0]} {words[1]}"

    return None


# ── SerpAPI search ────────────────────────────────────────────
def search_via_serpapi(query: str, start: int = 0) -> list | None:
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 10,
            "start": start,
            "hl": "en"
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            print(f"  [SerpAPI] Error: {results['error']}")
            return None

        organic = results.get("organic_results", [])
        return [
            {
                "title":   r.get("title", ""),
                "link":    r.get("link", ""),
                "snippet": r.get("snippet", "")
            }
            for r in organic
        ]

    except Exception as e:
        print(f"  [SerpAPI] Exception: {e}")
        return None


# ── Serper.dev search ─────────────────────────────────────────
def search_via_serper(query: str, start: int = 0) -> list | None:
    try:
        page = (start // 10) + 1
        payload = {
            "q": query,
            "num": 10,
            "page": page,
            "hl": "en"
        }
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        response = requests.post(
            "https://google.serper.dev/search",
            json=payload,
            headers=headers
        )
        results = response.json()

        if "error" in results:
            print(f"  [Serper] Error: {results['error']}")
            return None

        organic = results.get("organic", [])
        return [
            {
                "title":   r.get("title", ""),
                "link":    r.get("link", ""),
                "snippet": r.get("snippet", "")
            }
            for r in organic
        ]

    except Exception as e:
        print(f"  [Serper] Exception: {e}")
        return None


# ── Chain: Serper first → SerpAPI fallback ────────────────────
def search_google(query: str, start: int = 0) -> tuple[list, str]:

    if SERPER_API_KEY:
        results = search_via_serper(query, start)
        if results is not None:
            return results, "Serper"
        print(f"  [⚡] Serper failed — falling back to SerpAPI...")

    if SERPAPI_KEY:
        results = search_via_serpapi(query, start)
        if results is not None:
            return results, "SerpAPI"
        print(f"  [❌] SerpAPI also failed!")

    return [], "none"


# ── Scrape single query ───────────────────────────────────────
def scrape_single_query(query: str, company: str, role_keywords: list, seen: set, progress_callback=None) -> list:
    results = []
    start = 0
    page = 1

    while True:
        msg = f"  📄 Page {page} — query: {query[:60]}..."
        print(msg)
        if progress_callback:
            progress_callback(msg)

        organic, source = search_google(query, start)

        if not organic:
            if source == "none":
                msg = "  ❌ All APIs exhausted — stopping"
                print(msg)
                if progress_callback:
                    progress_callback(msg)
            else:
                print(f"  [✓] No more results at page {page}")
            break

        msg = f"  [✓] Page {page} via {source} — {len(organic)} results"
        print(msg)
        if progress_callback:
            progress_callback(msg)

        for r in organic:
            title   = r.get("title", "")
            link    = r.get("link", "")
            snippet = r.get("snippet", "")

            if "linkedin.com/in" not in link:
                continue

            title_lower   = title.lower()
            snippet_lower = snippet.lower()

            company_aliases = [company.lower()] + company.lower().split()
            if not any(alias in title_lower or alias in snippet_lower for alias in company_aliases):
                continue

            if not any(kw in title_lower or kw in snippet_lower for kw in role_keywords):
                continue

            name = parse_name_from_title(title)

            if name and name not in seen:
                seen.add(name)
                results.append({
                    "name":         name,
                    "company":      company,
                    "domain":       "",
                    "linkedin_url": link,
                    "title":        title
                })
                print(f"  [✓] {name:<30} ← {title}")
            else:
                print(f"  [✗] SKIP ← {title}")

        if len(organic) < 3:
            print(f"  [✓] Last page reached")
            break

        start += 10
        page += 1
        time.sleep(1.5)

    return results


# ── Main scraper ──────────────────────────────────────────────
def scrape_hr_names(company: str, domain: str, roles: list = None, progress_callback=None) -> list:
    print(f"\n[🔍] Scraping profiles for: {company}")

    if not roles:
        roles = ["HR", "Human Resources", "Talent Acquisition"]

    role_query   = " OR ".join([f'"{r}"' for r in roles])
    role_keywords = [r.lower() for r in roles]

    # Multiple query variations
    queries = [
        f'site:linkedin.com/in ({role_query}) "{company}"',
    ]

    all_names = []
    seen = set()  # shared across all queries — dedup globally

    for i, query in enumerate(queries):
        msg = f"\n🔎 Running query {i+1}/{len(queries)}..."
        print(msg)
        if progress_callback:
            progress_callback(msg)

        results = scrape_single_query(query, company, role_keywords, seen, progress_callback)

        # attach domain
        for r in results:
            r["domain"] = domain

        all_names.extend(results)

        msg = f"✅ Query {i+1} done — {len(results)} new profiles (total: {len(all_names)})"
        print(msg)
        if progress_callback:
            progress_callback(msg)

        time.sleep(2)  # pause between queries

    print(f"\n[✓] Total profiles found: {len(all_names)}")
    return all_names


# ── Export ────────────────────────────────────────────────────
def export_names_csv(names: list, output_path: str = "data/output/hr_names.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "company", "domain", "linkedin_url", "title"])
        writer.writeheader()
        writer.writerows(names)
    print(f"[✓] Saved {len(names)} names → {output_path}")