"""
Scrape X handles from a faces.site page using headless browser.
Usage: python scripts/scrape_x_handles.py <url>
"""

import sys
import re
import yaml
from playwright.sync_api import sync_playwright


IGNORE_HANDLES = {
    "home", "search", "explore", "notifications", "messages",
    "settings", "i", "intent", "login", "signup", "compose",
}


def extract_x_handle(url: str) -> str | None:
    match = re.search(r"(?:x\.com|twitter\.com)/(@?[\w]+)/?$", url)
    if match:
        handle = match.group(1).lstrip("@")
        if handle.lower() not in IGNORE_HANDLES:
            return handle
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/scrape_x_handles.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    handles = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Load main page
        print(f"Fetching: {url}")
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # Get all links from main page
        links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        print(f"Found {len(links)} links on main page")

        # Check for direct X links
        for link in links:
            handle = extract_x_handle(link)
            if handle and handle.lower() not in seen:
                seen.add(handle.lower())
                handles.append(handle)
                print(f"  Direct: @{handle}")

        # If no direct X links, follow sub-links
        if not handles:
            print("No direct X links, following sub-links...")
            sub_links = [l for l in links if l != url and url.split("//")[1].split("/")[0] in l]
            for link in sub_links:
                print(f"  Visiting: {link}")
                try:
                    page.goto(link, wait_until="networkidle", timeout=15000)
                    page.wait_for_timeout(1000)
                    inner_links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
                    for inner in inner_links:
                        handle = extract_x_handle(inner)
                        if handle and handle.lower() not in seen:
                            seen.add(handle.lower())
                            handles.append(handle)
                            print(f"    Found: @{handle}")
                except Exception as e:
                    print(f"    Error: {e}")

        browser.close()

    print(f"\n--- Found {len(handles)} X handles ---")
    for h in handles:
        print(f"@{h}")

    if handles:
        config = {"accounts": [{"handle": h, "weight": "medium"} for h in handles]}
        with open("config/x_accounts.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        print(f"\nWritten to config/x_accounts.yaml")


if __name__ == "__main__":
    main()
