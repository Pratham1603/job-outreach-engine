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

    # Remove "..." at end
    title = title.replace("...", "").strip()

    # Format: "Name - Role | LinkedIn" or "Name - Company"
    # Split on " - " and take first part
    parts = title.split(" - ")
    name = parts[0].strip()

    # Remove prefixes like "Capt.", "Dr.", "Mr.", "Ms."
    name = re.sub(r'^(Capt\.|Dr\.|Mr\.|Ms\.|Mrs\.)\s*', '', name, flags=re.IGNORECASE).strip()

    # Remove single letter initials with dot e.g. "Geeta B." → "Geeta"
    # Keep only if we have at least 2 proper words
    words = name.split()
    words = [w for w in words if not re.fullmatch(r'[A-Z]\.', w)]

    if len(words) >= 2:
        return " ".join(words)
    elif len(words) == 1 and len(words[0]) > 3:
        return words[0]

    return None


def scrape_hr_names(company: str, domain: str) -> list:
    print(f"\n[🔍] Scraping HR profiles for: {company}")

    all_names = []
    seen = set()
    start = 0
    page = 1

    while True:
        print(f"  [📄] Fetching page {page} (start={start})...")

        params = {
            "engine": "google",
            "q": f'site:linkedin.com/in ("HR" OR "Human Resources") "{company}" "{domain}"',
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

        # Stop if last page
        if len(organic) < 5:
            print(f"  [✓] Last page reached — stopping")
            break

        start += 10
        page += 1
        time.sleep(1.5)

    print(f"\n[✓] Total HR profiles found: {len(all_names)}")
    return all_names


def export_names_csv(names: list, output_path: str = "data/output/hr_names.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "company", "domain", "linkedin_url", "title"])
        writer.writeheader()
        writer.writerows(names)
    print(f"[✓] Saved {len(names)} names → {output_path}")


if __name__ == "__main__":
    results = scrape_hr_names("Jio", "jio.com")
    export_names_csv(results)