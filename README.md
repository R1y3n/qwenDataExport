# Qwen AI Chat Exporter 🚀

A lightweight Python CLI tool designed to batch-export complete conversation histories, metadata, and message payloads from [Qwen AI](https://chat.qwen.ai/).

It parses exported browser session cookies, automatically handles authentication token extraction, paginates through your entire account history, and saves each chat as a structured `.json` document.

---

## ✨ Key Features

- **Automated Cookie Parsing:** Supports standard Netscape `cookies.txt` formats exported directly from popular browser extension utilities.
- **Auto-Token Injection:** Extracts the `token` parameter from your session cookies and automatically configures the necessary `Authorization: Bearer <token>` HTTP headers.
- **Complete History Discovery:** Dynamically paginates through the Qwen chat index API until all historical sessions are discovered.
- **Index Generation:** Saves an overview file (`_index_chats.json`) containing all discovered session metadata alongside individual chat files.
- **Rate-Limited Requests:** Implements built-in delay intervals (`0.5s` page discovery / `1.0s` per chat export) to prevent hitting rate limits or endpoint throttling.

---

## 📋 Requirements

- Python **3.7+**
- `requests` library

```bash
pip install requests
```

#Usage
1. Export Session Cookies

    Log in to your account at chat.qwen.ai.

    Export your session cookies using a browser extension (such as Get cookies.txt LOCALLY for Chrome/Firefox).

    Save the exported file locally (e.g., cookies.txt).

2. Run the Exporter

Run the script by supplying the path to your cookie file:
Bash

python3 qwen_exporter.py cookies.txt

To specify a custom output directory:
Bash

python3 qwen_exporter.py cookies.txt -o my_qwen_backup

📂 Output Structure

The tool creates the specified output directory (defaulting to qwen_exports/) and populates it as follows:

qwen_exports/
├── _index_chats.json        # Full list of discovered chats with metadata
├── 8a2f1b4c-....json        # Full JSON payload for conversation #1
├── 3d5e7f9a-....json        # Full JSON payload for conversation #2
└── ...
