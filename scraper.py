#!/usr/bin/env python3
import os.path
import sys
import requests, json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.async_api import async_playwright
import asyncio
from typing import Optional, Dict
# load cookies (common format: list of dicts with name/value/domain/path)
with open("cookies.json", "r", encoding="utf-8") as f:
    cookies = json.load(f)

#there are generally two types of links
# ----------------------------------------------------------------------
# CONFIGURATION (edit these before running)
# ----------------------------------------------------------------------
# 1️⃣  Proxy – change to your real proxy host/port or comment out.
PROXIES = {

}
# 2️⃣  Custom User‑Agent (you can copy‑paste a real browser UA)
USER_AGENT = (
"Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0"
)
if "--versbose" in sys.argv:
    VERBOSE = True
else:
    VERBOSE = False
if "--no-proxy" in sys.argv:
    PROXIES = {}
else:
    PROXIES = {
   # "http":  "socks5://yourproxy.com:1080",
   #"https": "socks5://yourproxy.com:1080",
    }
print("PROXIES: " + str(PROXIES))
if "--no-download" in sys.argv:
    NO_DOWNLOAD = True
    print("NO_DOWNLOAD set to True")
    print("Collecting all links and saving them.")
    links_list = []
else:
    NO_DOWNLOAD = False
if len(sys.argv) > 1:
    first_arg = sys.argv[1]# first arg is username
else:
    print("Usage: scraper.py username on coomer.st platform ")
    print("Example for https://coomer.st/fansly/user/286621667281612800 : scraper.py 286621667281612800 fansly")

print(sys.argv)
if "o" in sys.argv or "onlyfans" in sys.argv:
    URL = f"https://coomer.st/onlyfans/user/{first_arg}"
    PLATFORM = "onlyfans"
elif "f" in sys.argv or "fansly" in sys.argv:
    URL = f"https://coomer.st/fansly/user/{first_arg}"
    PLATFORM = "fansly"
else:
    print("Specify platform with o/onlyfans or f/fansly")
    exit()
print("PLATFORM: " + PLATFORM)
print("Selecting user link: " + URL)
BASE_SAVE_URL = "/yout/path/for/downloads"
print("BASE_SAVE_URL: " + BASE_SAVE_URL)
base_url = "https://coomer.st"
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


TIMEOUT_SECS = 600
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

def download_file_(
    url: str,
    dest: str,
    filename: str,
    *,
    timeout: int | None = 60,
    proxies: Optional[Dict[str, str]] = None,
) -> None:
    os.makedirs(dest, exist_ok=True)
    path = os.path.join(dest, filename)

    req_kwargs = {"timeout": timeout}
    if proxies:
        req_kwargs["proxies"] = proxies

    resp = requests.get(url, **req_kwargs)
    try:
        resp.raise_for_status()
        # downloads all at once (keeps the whole response in memory)
        with open(path, "wb") as fh:
            fh.write(resp.content)
    finally:
        resp.close()


def save_txt(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

async def scrape_content_page(URL, browser, context):
    async with async_playwright() as p:
        page = await browser.new_page()
        await page.goto(URL, wait_until="networkidle")
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        #print(soup.title.get_text(strip=True) if soup.title else "no title")
        try:
            post_content = soup.find("div", class_="post__content").text
        except Exception as e:
            post_content = ""
            if VERBOSE:
                print("No caption found for this post.")
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
            content_filename = filename.split(".")[0] + ".txt"
            #print(f"Content filename: {content_filename}")

            if format in IMAGE_EXTS:
                if not post_content == "":
                    if VERBOSE:
                        print(post_content)
                    if not os.path.exists(f"{user_dir}/images/{content_filename}"):
                        #print("Saving txt: " + post_content)
                        save_txt(f"{user_dir}/images/{content_filename}", post_content)
                    else:
                        if VERBOSE:
                            print("Text already saved: " + content_filename)
                if not os.path.exists(f"{user_dir}/images/{filename}") and not NO_DOWNLOAD:
                    if VERBOSE:
                        print("Downloading image: " + data_href)
                    i = 1
                    while i != 10:
                        try:
                            download_file(url=data_href, dest=f"{user_dir}/images/", filename=filename, timeout=TIMEOUT_SECS, proxies=PROXIES)
                            #print(f"Image {filename} downloaded successfully.")
                            break
                        except Exception as e:
                            print(e)
                            print("Retry number: " + str(i))
                            i += 1
                            pass

                else:
                    if VERBOSE:
                        print("Image already downloaded: " + filename)
                if NO_DOWNLOAD:
                    print(data_href)
                    links_list.append(data_href)
            elif format in VIDEO_EXTS:
                if not post_content == "":
                    if not os.path.exists(f"{user_dir}/videos/{content_filename}"):
                        if VERBOSE:
                            print("Saving txt: " + post_content)
                        save_txt(f"{user_dir}/images/{content_filename}", post_content)
                    #else:
                    #    print("Text already saved: " + content_filename)
                    #    print(post_content)
                if not os.path.exists(f"{user_dir}/videos/{filename}") and not NO_DOWNLOAD:
                    if VERBOSE:
                        print("Downloading video: " + data_href)
                    i = 1
                    while i != 10:
                        try:
                            download_file(url=data_href, dest=f"{user_dir}/videos/", filename=filename, timeout=TIMEOUT_SECS, proxies=PROXIES)
                            if VERBOSE:
                                print(f"Video {filename} downloaded successfully.")
                            break
                        except Exception as e:
                            print(e)
                            print("Retry number: " + str(i))
                            i += 1
                            pass
                else:
                    if VERBOSE:
                        print("Video already downloaded: " + filename)
                if NO_DOWNLOAD:
                    print(data_href)
                    links_list.append(data_href)
        await page.close()

def write_list_to_file(links_list):
    with open(f"{BASE_SAVE_URL}/{first_arg}/links.txt", "w", encoding="utf-8") as f:
        for link in links_list:
            f.write(link + "\n")

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
        i = 50
        while True:
            if i >= 1250:
                exit()
            content_page = f"{base_url}/{PLATFORM}/user/{first_arg}?o={i}"
            print("Navigating to content page: " + f"{content_page}")
            await page.goto(content_page, wait_until="networkidle")
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            hrefs_post = [link['href'] for link in soup.find_all("a", href=True) if link["href"].__contains__("/post/")]
            print(f"Found {len(hrefs_post)} posts.")
            if len(hrefs_post) == 0:
                if VERBOSE:
                    print("Since on this page there are no posts found, we are considering that we have already scraped all content.\n Exiting...")
                    write_list_to_file(links_list)
                    exit()
            for href in hrefs_post:
                content_url = urljoin(base_url, href)
                if VERBOSE:
                    print("Scraping content page: ", content_url)
                await scrape_content_page(content_url, browser=browser, context=context)
            i += 50
asyncio.run(scraper_user(URL))
