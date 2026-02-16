#!/usr/bin/env python3
"""
coomer_onlyfans.py
~~~~~~~~~~~~~~~~~~

Usage:
    python coomer_onlyfans.py <first_given_arg>

Example:
    python coomer_onlyfans.py someuser

The script:
    1. Builds https://coomer.st/onlyfans/user/<first_given_arg>
    2. Uses a custom User‑Agent and a proxy.
    3. Parses the page and prints all hrefs that contain the word "post".
"""
import sys
import requests, json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
# load cookies (common format: list of dicts with name/value/domain/path)
with open("cookies.json", "r", encoding="utf-8") as f:
    cookies = json.load(f)
# 1️⃣  Proxy – change to your real proxy host/port or comment out.
PROXIES = {
    # "http":  "socks5://domain_or_ip:port",
    # "https": "socks5://domain_or_ip.:port",
}
# 2️⃣  Custom User‑Agent (you can copy‑paste a real browser UA)
USER_AGENT = (
"Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0"
)
# ----------------------------------------------------------------------
def main():
    headers = {"User-Agent": USER_AGENT}
    sess = requests.Session()
    sess.headers.update(headers)
    sess.proxies.update(PROXIES)
    for c in cookies:
        # Grab the *raw* keys – they’re the ones the exporter gives you.
        name   = c.get("Name raw")
        value  = c.get("Content raw")
        host   = c.get("Host raw")          # e.g. "http://coomer.st/"
        domain = urlparse(host).netloc      # strip scheme → "coomer.st"
        path   = c.get("Path raw", "/")
        # Optional: expiration, HttpOnly, SameSite, etc.
        sess.cookies.set(name, value, domain=domain, path=path)

    if len(sys.argv) < 2:
        print("❌  Usage: python coomer_onlyfans.py <first_given_arg>")
        sys.exit(1)

    first_arg = sys.argv[1]
    url = f"https://coomer.st/onlyfans/user/{first_arg}"
    print(f"📡  Requesting: {url}")


    try:
        '''
        response = requests.get(
            url,
            headers=headers,
            proxies=PROXIES,
            timeout=15,          # seconds
            allow_redirects=True
        )
        response.raise_for_status()'''
        response = sess.get(url, timeout=15, allow_redirects=True)
    except requests.RequestException as exc:
        print(f"❌  Request failed: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Parse with BeautifulSoup and filter hrefs that contain "post"
    # ------------------------------------------------------------------
    soup = BeautifulSoup(response.text, "html.parser")
    print("status:", response.status_code)
    print("final url:", response.url)
    print("content-type:", response.headers.get("content-type"))
    print("bytes:", len(response.content))
    print("first 300 chars:\n", response.text[:300])
    post_links = [
        a["href"]
        for a in soup.find_all("a", href=True)
        #if "post" in a["href"]
    ]

    if not post_links:
        print("⚠️  No links containing 'post' were found.")
    else:
        print(f"\n✅  Found {len(post_links)} link(s) containing 'post':")
        for link in post_links:
            # Make sure links are absolute
            abs_link = requests.compat.urljoin(url, link)
            print(f"   {abs_link}")