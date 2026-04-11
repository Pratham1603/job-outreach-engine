import csv
import os
import argparse

PATTERNS = [
    ("first.last",  lambda f, l: f"{f}.{l}"),
    ("firstlast",   lambda f, l: f"{f}{l}"),
    ("first_last",  lambda f, l: f"{f}_{l}"),
    ("flast",       lambda f, l: f"{f[0]}{l}"),
    ("f.last",      lambda f, l: f"{f[0]}.{l}"),
    ("last.first",  lambda f, l: f"{l}.{f}"),
    ("firstname",   lambda f, l: f"{f}"),
    ("first.l",     lambda f, l: f"{f}.{l[0]}")
]

def predict_emails(full_name: str, domain: str) -> list:
    parts = full_name.strip().lower().split()

    if len(parts) < 2:
        return []

    first = parts[0]
    last = parts[1]

    domain = domain.strip().lower().replace("@", "")

    results = []
    for pattern_name, fn in PATTERNS:
        try:
            local = fn(first, last)
            email = f"{local}@{domain}"

            results.append({
                "name": full_name,
                "pattern": pattern_name,
                "email": email
            })
        except:
            continue

    return results


def predict_bulk(names: list, domain: str) -> list:
    all_results = []
    for name in names:
        all_results.extend(predict_emails(name, domain))
    return all_results


def export_csv(results: list, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "pattern", "email"])
        writer.writeheader()
        writer.writerows(results)
    print(f"[✓] Saved {len(results)} emails → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict HR emails from name + domain")
    parser.add_argument("--name",   type=str, help="Full name e.g. 'Priya Sharma'")
    parser.add_argument("--domain", type=str, help="Company domain e.g. jio.com")
    parser.add_argument("--output", type=str, default="data/output/emails.csv")
    args = parser.parse_args()

    if args.name and args.domain:
        results = predict_emails(args.name, args.domain)
        for r in results:
            print(f"  {r['pattern']:<15} {r['email']}")
        export_csv(results, args.output)
    else:
        # Quick test
        test_names = ["Priya Sharma", "Rahul Mehta", "Sneha Joshi"]
        results = predict_bulk(test_names, "jio.com")
        for r in results:
            print(f"  {r['pattern']:<15} {r['email']}")
        export_csv(results, args.output)