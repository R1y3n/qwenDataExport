#!/usr/bin/env python3
import argparse
import http.cookiejar
import json
import os
import sys
import time
import uuid
import requests

BASE_URL = "https://chat.qwen.ai/api/v2/chats"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://chat.qwen.ai/",
    "Version": "0.3.12",
    "source": "web",
}


def load_session(cookie_file_path, manual_token=None):
    """
    Loads cookies.txt into session and forces cookie matching across domains.
    Extracts Bearer token from cookies or command-line argument.
    """
    session = requests.Session()
    cookie_jar = http.cookiejar.MozillaCookieJar(cookie_file_path)

    try:
        cookie_jar.load(ignore_discard=True, ignore_expires=True)
    except Exception as err:
        print(f"[!] Error reading cookie file '{cookie_file_path}': {err}")
        sys.exit(1)

    extracted_token = manual_token
    cookie_dict = {}

    for cookie in cookie_jar:
        cookie_dict[cookie.name] = cookie.value
        if not extracted_token and cookie.name == "token":
            extracted_token = cookie.value

    # Force cookies directly into requests session
    session.cookies.update(cookie_dict)

    headers = DEFAULT_HEADERS.copy()
    if extracted_token:
        headers["Authorization"] = f"Bearer {extracted_token}"
    else:
        print("[!] Warning: No Bearer token found in cookies or CLI. API calls may fail.")

    session.headers.update(headers)
    return session


def get_request_headers(session):
    """Generates dynamic headers required by Qwen API."""
    headers = session.headers.copy()
    headers["X-Request-Id"] = str(uuid.uuid4())
    headers["Timezone"] = time.strftime("%a %b %d %Y %H:%M:%S GMT%z")
    return headers


def discover_all_chats(session):
    """Paginates through chat list pages until no more chat entries exist."""
    all_chats = []
    page = 1

    print("[*] Discovering chats across pages...")
    while True:
        url = f"{BASE_URL}/?page={page}&exclude_project=true"
        try:
            res = session.get(url, headers=get_request_headers(session), timeout=15)

            if res.status_code != 200:
                print(f"[!] HTTP {res.status_code} Error on page {page}. Server response:")
                print(res.text[:500])
                break

            try:
                data_json = res.json()
            except json.JSONDecodeError:
                print(f"[!] Failed to parse JSON on page {page}. Response content:")
                print(res.text[:500])
                break

            if not data_json.get("success"):
                print(f"[!] Unsuccessful response status on page {page}:")
                print(json.dumps(data_json, indent=2))
                break

            chat_batch = data_json.get("data", [])
            if not chat_batch:
                print(f"[*] Reached end of pagination at page {page}.")
                break

            print(f"[+] Page {page}: Discovered {len(chat_batch)} chats.")
            all_chats.extend(chat_batch)
            page += 1
            time.sleep(0.5)

        except Exception as err:
            print(f"[!] Request exception on page {page}: {err}")
            break

    return all_chats


def export_single_chat(session, chat_id):
    """Fetches export payload for a given chat ID."""
    url = f"{BASE_URL}/{chat_id}"
    try:
        res = session.get(url, headers=get_request_headers(session), timeout=15)
        if res.status_code == 200:
            payload = res.json()
            if payload.get("success"):
                return payload.get("data")

        print(f"[!] Export failed for chat {chat_id} (HTTP {res.status_code}):")
        print(res.text[:300])
    except Exception as err:
        print(f"[!] Exception fetching chat {chat_id}: {err}")
    return None


def main():
    parser = argparse.ArgumentParser(description="Export Qwen AI chat histories using cookies.txt.")
    parser.add_argument("cookies_file", help="Path to Netscape cookies.txt file")
    parser.add_argument("-o", "--output-dir", default="qwen_exports", help="Output directory for exported JSON files")
    parser.add_argument("-t", "--token", default=None, help="Optional manual Bearer token (JWT)")
    args = parser.parse_args()

    if not os.path.isfile(args.cookies_file):
        print(f"[!] Error: Cookie file '{args.cookies_file}' not found.")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    session = load_session(args.cookies_file, manual_token=args.token)

    chats = discover_all_chats(session)
    print(f"[*] Total chats discovered: {len(chats)}")

    if not chats:
        print("[!] Process ended with 0 chats. Inspect the response body above for authentication or WAF errors.")
        sys.exit(0)

    index_path = os.path.join(args.output_dir, "_index_chats.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(chats, f, indent=2, ensure_ascii=False)
    print(f"[+] Chat list index written to: {index_path}")

    print("[*] Requesting full exports for discovered chats...")
    for index, chat in enumerate(chats, start=1):
        chat_id = chat.get("id")
        title = chat.get("title", "Untitled")
        print(f"[{index}/{len(chats)}] Exporting: {chat_id} | Title: {title}")

        chat_data = export_single_chat(session, chat_id)
        if chat_data:
            out_file = os.path.join(args.output_dir, f"{chat_id}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(chat_data, f, indent=2, ensure_ascii=False)

        time.sleep(1.0)

    print(f"\n[+] Export completed. Files saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
