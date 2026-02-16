#!/usr/bin/env python3
import os.path
import sys

import requests, json, yt_dlp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.async_api import async_playwright
import asyncio
from typing import Optional, Dict
# load cookies (common format: list of dicts with name/value/domain/path)
with open("cookies.json", "r", encoding="utf-8") as f:
    cookies = json.load(f)

#https://coomer.st/fansly/user/286621667281612800
#https://coomer.st/onlyfans/user/sethifanz
#there are generally two types of links
# ----------------------------------------------------------------------
# CONFIGURATION (edit these before running)
# ----------------------------------------------------------------------
#YT_DLP RATE LIMIT
RATELIMIT = 100000 * 1024
# 1️⃣  Proxy – change to your real proxy host/port or comment out.
PROXIES = {
    # "http":  "socks5://domain_or_ip:port",
    # "https": "socks5://domain_or_ip.:port",
}
# 2️⃣  Custom User‑Agent (you can copy‑paste a real browser UA)
USER_AGENT = (
"Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0"
)
if "--verbose" in sys.argv:
    VERBOSE = True

else:
    VERBOSE = False
print("VERBOSE: " + str(VERBOSE))
if "--no-proxy" in sys.argv:
    PROXIES = {}
else:
    PROXIES = {
        "http": "socks5://espobuilt.com:1080",
        "https": "socks5://espobuilt.com:1080",
    }
print("PROXIES: " + str(PROXIES))

if len(sys.argv) > 1:
    first_arg = sys.argv[1]# first arg is username
else:
    print("Usage: scraper.py username on coomer.st platform ")
    print("Example for https://coomer.st/fansly/user/286621667281612800 : scraper.py 286621667281612800 fansly")

if "o" in sys.argv or "onlyfans" in sys.argv:
    URL = f"https://coomer.st/onlyfans/user/{first_arg}"
    PLATFORM = "onlyfans"
elif "f" in sys.argv or "fansly" in sys.argv:
    URL = f"https://coomer.st/fansly/user/{first_arg}"
    PLATFORM = "fansly"
else:
    print("Specify platform with o/onlyfans or f/fansly")
    exit()
BASE_SAVE_URL = "/mnt/wdblue2/.of"
if VERBOSE:
    print("PLATFORM: " + PLATFORM)
    print("Selecting user link: " + URL)
    print("BASE_SAVE_URL: " + BASE_SAVE_URL)
if "--restart" in sys.argv:
    iterator_f = f"{BASE_SAVE_URL}/{first_arg}/iterator.txt"
    if os.path.exists(iterator_f):
        os.remove(iterator_f)
        print("Deleted iterator.txt for " + first_arg)

print(sys.argv)
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
LINKS_COLLECTOR = []

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

async def scrape_content_page(URL, browser, context, page_n):
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
        LINKS_COLLECTOR.append(data_hrefs)
        attachments = soup.find_all("a", class_="post__attachment-link")

        if VERBOSE:
            print(f"{URL} has", str(len(data_hrefs)), "files.")
        if PLATFORM == "onlyfans":
            username = first_arg
            user_dir = f"{BASE_SAVE_URL}/{username}"
        elif PLATFORM == "fansly":
            username = soup.find("a", class_="post__user-name").get_text(strip=True)
            user_dir = f"{BASE_SAVE_URL}/{username}"
        os.makedirs(f"{user_dir}/images", exist_ok=True)
        os.makedirs(f"{user_dir}/videos", exist_ok=True)
        if len(attachments) > 0:
            if VERBOSE:
                print(f"Found {len(attachments)} attachments.")
            LINKS_COLLECTOR.append(attachments)
            #SCRAPE ATTACHMENTS
            for attachment in attachments:
                format = attachment['href'].split(".")[-1]
                filename = attachment['href'].split("?f=")[-1]
                if VERBOSE:
                    print(f"Downloading attachment: {filename}")
                if format in IMAGE_EXTS:
                    download_file(url=attachment['href'], dest=f"{user_dir}/images/", filename=filename, timeout=TIMEOUT_SECS, proxies=PROXIES)
                elif format in VIDEO_EXTS:
                    i = 1
                    while i != 10:
                        try:
                            #download_file(url=attachment['href'], dest=f"{user_dir}/videos/", filename=filename, timeout=TIMEOUT_SECS, proxies=PROXIES)
                            ydl_opts = {
                                'outtmpl': BASE_SAVE_URL + "/" + username + "/videos/" + filename,
                                'ratelimit': RATELIMIT,  # Limit download speed to 100KB/s
                                'retries': 10,  # Retry failed downloads up to 10 times
                                'fragment_retries': 10,
                                'skip_unavailable_fragments': True,
                                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',  # Mimic browser
                                # add other options as needed
                            }
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                ydl.download(attachment['href'])
                            break
                        except Exception as e:
                            print(e)
                            print("Retrying attachment download: " + str(i))
                            i += 1
                            pass
            return

        for data_href in data_hrefs:
            format = data_href.split(".")[-1]
            filename = data_href.split("?f=")[-1]
            content_filename = filename.split(".")[0] + ".txt"

            if format in IMAGE_EXTS:
                if not post_content == "":
                    if not os.path.exists(f"{user_dir}/images/{content_filename}"):
                        save_txt(f"{user_dir}/images/{content_filename}", post_content)
                    else:
                        if VERBOSE:
                            print("Text already saved: " + content_filename)
                if not os.path.exists(f"{user_dir}/images/{filename}"):
                    if VERBOSE:
                        print("Downloading image: " + data_href)
                    i = 1
                    while i != 10:
                        try:
                            download_file(url=data_href, dest=f"{user_dir}/images/", filename=filename, timeout=TIMEOUT_SECS, proxies=PROXIES)
                            break
                        except Exception as e:
                            print(e)
                            print("Retrying image download: " + str(i))
                            i += 1
                            pass

                else:
                    if VERBOSE:
                        print("Image already downloaded: " + filename)

            elif format in VIDEO_EXTS:
                if not post_content == "":
                    if not os.path.exists(f"{user_dir}/videos/{content_filename}"):
                        save_txt(f"{user_dir}/videos/{content_filename}", post_content)
                if not os.path.exists(f"{user_dir}/videos/{filename}"):
                    if VERBOSE:
                        print("Downloading video: " + data_href)
                    i = 1
                    while i != 10:
                        try:
                            #download_file(url=data_href, dest=f"{user_dir}/videos/", filename=filename, timeout=TIMEOUT_SECS, proxies=PROXIES)
                            ydl_opts = {
                                'outtmpl': BASE_SAVE_URL + "/" + username + "/videos/" + filename,
                                'ratelimit': RATELIMIT,  # Limit download speed to 100KB/s
                                'retries': 10,  # Retry failed downloads up to 10 times
                                'fragment_retries': 10,
                                'skip_unavailable_fragments': True,
                                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',  # Mimic browser
                                # add other options as needed
                            }
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                ydl.download(data_href)
                                ydl.close()
                            if VERBOSE:
                                print(f"Video {filename} downloaded successfully.")
                            break
                        except Exception as e:
                            print(e)
                            print("Retrying video download: " + str(i))
                            i += 1
                            pass
                else:
                    if VERBOSE:
                        print("Video already downloaded: " + filename)
            write_iterator(page_n, URL, username)
        #await page.close()
        #await browser.close()

def write_list_to_file(LINKS_COLLECTOR):
    with open(f"{BASE_SAVE_URL}/{first_arg}/links.txt", "w", encoding="utf-8") as f:
        for link in LINKS_COLLECTOR:
            f.write(str(link) + "\n")
    print(f"Wrote {str(len(LINKS_COLLECTOR))} links. to {BASE_SAVE_URL}/{first_arg}/links.txt")

def write_iterator(page_n, post_n, username):
    with open(f"{BASE_SAVE_URL}/{username}/iterator.txt", "w", encoding="utf-8") as f:
        f.write(str(page_n) + "\n")
        f.write(str(post_n.split("/")[-1]) + "\n")

def read_iterator(username):
    with open(f"{BASE_SAVE_URL}/{username}/iterator.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        return (lines[0].strip(), lines[1].strip())

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
        #hrefs_post = [link['href'] for link in soup.find_all("a", href=True) if link["href"].__contains__("/post/")]
        hrefs_user = [link['href'] for link in soup.find_all("a", href=True) if link["href"].__contains__("?o") and link["href"].__contains__(first_arg)]
        for href in hrefs_user:
            if int(href.split("=")[-1]) < 0:
                hrefs_user.remove(href)
        #hrefs_user = list(set(hrefs_user))

        #scraper first page, if iterator does not exist
        isIterator = False
        if not os.path.exists(f"{BASE_SAVE_URL}/{first_arg}/iterator.txt"):
            content_page = f"{base_url}/{PLATFORM}/user/{first_arg}"
            await page.goto(content_page, wait_until="networkidle")
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            hrefs_post = [link['href'] for link in soup.find_all("a", href=True) if link["href"].__contains__("/post/")]
            for href in hrefs_post:
                content_url = urljoin(base_url, href)
                if VERBOSE:
                    print("Scraping post page: ", content_url)
                await scrape_content_page(content_url, browser=browser, context=context, page_n="0")
            i = 50
        #first page scraped
        else:
            isIterator = True
            if PLATFORM == "onlyfans":
                username = first_arg
            elif PLATFORM == "fansly":
                username = soup.find("a", class_="post__user-name").get_text(strip=True)
            iterator_tuple = read_iterator(username)
            print(f"ReadIterator: platform={PLATFORM}\no?={iterator_tuple[0]}\n{iterator_tuple[1]}")
            i = int(iterator_tuple[0])
            post_to_scrape = int(iterator_tuple[1])

        while True:
            await browser.close()
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            content_page = f"{base_url}/{PLATFORM}/user/{first_arg}?o={i}"
            if VERBOSE:
                print("Navigating to content page: " + f"{content_page}")
            await page.goto(content_page, wait_until="networkidle")
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            hrefs_post = [link['href'] for link in soup.find_all("a", href=True) if link["href"].__contains__("/post/")]
            if VERBOSE:
                print(f"{content_page} has {len(hrefs_post)} post pages.")
            if len(hrefs_post) == 0:
                if VERBOSE:
                    print("Since on this page there are no posts found, we are considering that we have already scraped all content.\nExiting...")
                    write_list_to_file(LINKS_COLLECTOR)
                    await browser.close()
                    exit()
            for href in hrefs_post:
                if isIterator:
                    post_ = int(href.split("/")[-1])
                    if post_ != post_to_scrape:
                        continue
                content_url = urljoin(base_url, href)
                if VERBOSE:
                    print("Scraping content page: ", content_url)
                await scrape_content_page(content_url, browser=browser, context=context, page_n=str(i))

                if VERBOSE:
                    print(f"Iterator={i}, post={href}")
            i += 50
asyncio.run(scraper_user(URL))