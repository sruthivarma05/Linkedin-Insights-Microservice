# file: save_session.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List
from playwright.sync_api import sync_playwright

SESSION_DIR = Path("linkedin_session")
SESSION_FILE = SESSION_DIR / "storage.json"

def _has_linkedin_cookies(state: Dict[str, Any]) -> bool:
    cookies: List[Dict[str, Any]] = state.get("cookies", [])
    for c in cookies:
        domain = c.get("domain", "")
        name = c.get("name", "")
        # Why: presence of any linkedin.com cookie (ideally li_at) indicates a signed-in context
        if "linkedin.com" in domain and name:
            return True
    return False

def main() -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # manual login
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")

        print("\n=== ACTION REQUIRED ===")
        print("1) Log into LinkedIn in the opened window (complete any 2FA).")
        print("2) Wait until your feed loads at https://www.linkedin.com/feed/.")
        input("3) Press Enter here to save the session... ")

        raw_state = context.storage_state()  # in-memory first
        # Validate we captured linkedin.com cookies (not google.com, etc.)
        if not _has_linkedin_cookies(raw_state):
            browser.close()
            raise SystemExit(
                "No linkedin.com cookies captured. Make sure you logged in to LinkedIn "
                "in the opened window (not another tab), then run save_session.py again."
            )

        context.storage_state(path=str(SESSION_FILE))
        print(f"Saved LinkedIn session → {SESSION_FILE.resolve()}")
        browser.close()

if __name__ == "__main__":
    main()