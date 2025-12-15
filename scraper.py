#!/usr/bin/env python3
#To use this scraper you have to log in and save your cookies with an addon for firefox
import os.path
import sys
import requests, json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import urljoin
from playwright.async_api import async_playwright
import asyncio
from typing import Optional, Dict
# load cookies (common format: list of dicts with name/value/domain/path)
#load your cookies and save them with https://addons.mozilla.org/en-US/firefox/addon/cookie-quick-manager/ Addon for Firefox
with open("cookies.json", "r", encoding="utf-8") as f:
    cookies = json.load(f)
#have your cookies.json in the working directory of the script

# ----------------------------------------------------------------------
# CONFIGURATION (edit these before running)
# ----------------------------------------------------------------------
# 1️⃣  Proxy – change to your real proxy host/port or comment out.
PROXIES = {
    #"http":  "socks5://IP:1080",
    #"https": "socks5://IP:1080",
}
# 2️⃣  Custom User‑Agent (you can copy‑paste a real browser UA)
#Change it to yours
USER_AGENT = (
"Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0"
)
first_arg = sys.argv[1]
#first_arg = "tu_angel_caotico"
URL = f"https://coomer.st/onlyfans/user/{first_arg}"
#VERY IMPORTANT, SET THE ROOT DIRECTORY, WHERE ALL DOWNLOADS WILL BE
BASE_SAVE_URL = ""
base_url = "https://coomer.st/"
# ------------------------------------
# Image file extensions (no leading '.')
# ------------------------------------
IMAGE_EXTS = {
    "jpg", "jpeg", "png", "gif", "bmp", "webp",
    "tiff", "tif", "heic", "heif", "svg", "ico",
    "raw", "cr2", "nef", "arw", "orf", "sr2", "psd",
}

# ------------------------------------
# Video file extensions (no leading '.')
# ------------------------------------
VIDEO_EXTS = {
    "mp4", "mkv", "webm", "mov", "avi", "flv",
    "wmv", "mpg", "mpeg", "3gp", "3g2", "m4v",
    "ogv", "vob", "ts", "m2ts", "mts", "dvb",
    "f4v", "qt", "mp4v",
}

def download_file(
    url: str,
    dest: str,
    filename: str,
    *,
    chunk_size: int = 8192,
    timeout: int | None = 60,
    proxies: Optional[Dict[str, str]] = None,      # <-- added
) -> None:
    req_kwargs = {
        "stream": True,
        "timeout": timeout,
    }
    if proxies:
        req_kwargs["proxies"] = proxies

    with requests.get(url, **req_kwargs) as resp:
        resp.raise_for_status()
        with open(f"{dest}/{filename}", "wb") as fh:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    fh.write(chunk)

async def scrape_content_page(URL, browser, context):
    async with async_playwright() as p:
        page = await browser.new_page()
        await page.goto(URL, wait_until="networkidle")
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        #print(soup.title.get_text(strip=True) if soup.title else "no title")
        post_content = soup.find("div", class_="post__content")
        #hrefs = [href['href'] for href in soup.find_all("a", href=True) if h]
        data_hrefs = [href['href'] for href in soup.find_all("a") if "data" in href['href']]
        attachments = soup.find_all("a", class_="post__attachment-link")
        print("Found", str(len(data_hrefs)), "files.")
        user_dir = f"{BASE_SAVE_URL}/{first_arg}"
        i = 0
        for data_href in data_hrefs:
            format = data_href.split(".")[-1]
            #filename = f"{first_arg}_{i}.{format}"
            filename = data_href.split("?f=")[-1]
            if format in IMAGE_EXTS:
                if not os.path.exists(f"{user_dir}/images/{filename}"):
                    print("Downloading image: " + data_href)
                    download_file(url=data_href, dest=f"{user_dir}/images/", filename=filename, chunk_size=8192, timeout=60, proxies=PROXIES)
                else:
                    print("Image already downloaded: " + filename)
            elif data_href.split(".")[-1] in VIDEO_EXTS:
                if not os.path.exists(f"{user_dir}/videos/{filename}"):
                    print("Downloading video: " + data_href)
                    download_file(url=data_href, dest=f"{user_dir}/videos/", filename=filename, chunk_size=8192, timeout=60, proxies=PROXIES)
                else:
                    print("Video already downloaded: " + filename)

async def scraper_user(URL: Optional[str]):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        #create user dirs if they not exist
        if not os.path.exists(f"{BASE_SAVE_URL}/{first_arg}/images/"):
            os.makedirs(f"{BASE_SAVE_URL}/{first_arg}/images/")
            print(f"Created directory: {BASE_SAVE_URL}/{first_arg}/images/")
        if not os.path.exists(f"{BASE_SAVE_URL}/{first_arg}/videos/"):
            os.makedirs(f"{BASE_SAVE_URL}/{first_arg}/videos/")
            print(f"Created directory: {BASE_SAVE_URL}/{first_arg}/videos/")

        page = await context.new_page()
        await page.goto(URL, wait_until="networkidle")  # let JS finish
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        print(soup.title.get_text(strip=True) if soup.title else "no title")
        hrefs_post = [link['href'] for link in soup.find_all("a", href=True) if link["href"].__contains__("/post/")]
        hrefs_user = [link['href'] for link in soup.find_all("a", href=True) if link["href"].__contains__("?o") and link["href"].__contains__(first_arg)]
        for href in hrefs_user:
            if int(href.split("=")[-1]) < 0:
                hrefs_user.remove(href)
        hrefs_user = list(set(hrefs_user))

        fancy_links_leads_to_other_content_pages = soup.find_all('a.fancy-link')
        #scrape posts on landing user page
        for href in hrefs_post:
            print("Scraping init page: ", urljoin(base_url, href))
            await scrape_content_page(urljoin(base_url, href), browser=browser, context=context)
        #scrape posts on other found pages
        for content_page in fancy_links_leads_to_other_content_pages:
            print("Navigating to content page: " + f"{URL}/{content_page["url"]}")
            await page.goto(f"{URL}/{content_page["url"]}", wait_until="networkidle")
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            hrefs_post = [link['href'] for link in soup.find_all("a", href=True) if link["href"].__contains__("/post/")]
            for href in hrefs_post:
                print("Scraping content page: ", urljoin(base_url, href))
                await scrape_content_page(f"{base_url}/{href}", browser=browser, context=context)
            await browser.close()
asyncio.run(scraper_user(URL))
