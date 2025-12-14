# file: scrape_linkedin_company.py
import json
import re
from typing import Optional, Dict
from urllib.parse import urlparse
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SESSION_FILE = Path("linkedin_session/storage.json")

def _normalize_company_url(url: str) -> str:
    if not url.startswith("http"):
        raise ValueError("Provide a full https:// LinkedIn company URL.")
    parsed = urlparse(url)
    if "linkedin.com" not in parsed.netloc or "/company/" not in parsed.path:
        raise ValueError("URL must look like https://www.linkedin.com/company/<slug>/")
    path = parsed.path.rstrip("/")
    if "/about" not in path:
        path = path + "/about"
    return f"{parsed.scheme}://{parsed.netloc}{path}/"

def _safe_inner_text(locator) -> Optional[str]:
    try:
        txt = locator.inner_text(timeout=4000).strip()
        return txt or None
    except Exception:
        return None

def _safe_attr(locator, name: str) -> Optional[str]:
    try:
        val = locator.get_attribute(name, timeout=4000)
        return (val or "").strip() or None
    except Exception:
        return None

def _extract_dt_dd(page, term: str) -> Optional[str]:
    try:
        dt = page.locator(f"dt:has-text('{term}')").first
        if dt.count() == 0:
            return None
        dd = dt.locator("xpath=following-sibling::dd[1]").first
        return _safe_inner_text(dd)
    except Exception:
        return None

def _parse_followers(raw: Optional[str]) -> Optional[int]:
    if not raw:
        return None
    raw = raw.replace("\u202f", " ").replace("\xa0", " ")
    m = re.search(r"([\d,]+)", raw)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except Exception:
        return None

def _assert_logged_in(page) -> None:
    """
    Why: LinkedIn hides fields unless authenticated; fail fast if session is invalid.
    """
    page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
    # Presence of the global nav or "Start a post" composer is a good signal.
    signed_in = (
        page.locator("header.global-nav, div.share-box-feed-entry__closed-share-box").first.count() > 0
    )
    # Login page heuristics
    login_gate = (
        page.url.startswith("https://www.linkedin.com/login")
        or page.locator("input#username").first.count() > 0
        or page.locator("a[href*='/login']").first.count() > 0
    )
    if not signed_in or login_gate:
        raise RuntimeError(
            "Not authenticated to LinkedIn. Re-run save_session.py and ensure storage.json contains linkedin.com cookies."
        )

def scrape_company(url: str, storage_state: str = str(SESSION_FILE)) -> Dict[str, Optional[str]]:
    about_url = _normalize_company_url(url)
    storage_path = Path(storage_state)
    if not storage_path.exists():
        raise FileNotFoundError(f"Session not found: {storage_path}. Run save_session.py first.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(storage_path),
            viewport={"width": 1366, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        # Preflight session validation
        _assert_logged_in(page)

        data: Dict[str, Optional[str]] = {
            "name": None,
            "followers": None,
            "tagline": None,
            "description": None,
            "industry": None,
            "website": None,
            "headquarters": None,
            "founded": None,
            "company_size": None,
            "specialties": None,
            "employees_on_linkedin": None,
            "source_about_url": about_url,
        }

        # Main page: top card basics
        main_url = about_url.replace("/about/", "/")
        try:
            page.goto(main_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("section.org-top-card, h1", timeout=15000)
        except PlaywrightTimeoutError:
            pass

        data["name"] = (
            _safe_inner_text(page.locator("h1.org-top-card-summary__title").first)
            or _safe_inner_text(page.locator("h1").first)
        )
        followers_raw = (
            _safe_inner_text(page.locator("div.org-top-card-summary__followers-count").first)
            or _safe_inner_text(page.locator("span:has-text('followers')").first)
            or _safe_inner_text(page.locator("a:has-text('followers')").first)
        )
        data["followers"] = _parse_followers(followers_raw)
        data["tagline"] = (
            _safe_inner_text(page.locator("p.org-top-card-summary__tagline").first)
            or _safe_inner_text(page.locator("div.org-top-card-summary__tagline").first)
        )

        # About page: structured fields
        try:
            page.goto(about_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("section.org-grid__wide-column, section:has(dt)", timeout=15000)
        except PlaywrightTimeoutError:
            context.close()
            browser.close()
            return data

        data["description"] = (
            _safe_inner_text(page.locator("section:has(h2:has-text('About')) p").first)
            or _extract_dt_dd(page, "About")
        )
        data["industry"] = _extract_dt_dd(page, "Industry")
        data["headquarters"] = _extract_dt_dd(page, "Headquarters")
        data["founded"] = _extract_dt_dd(page, "Founded")
        data["company_size"] = _extract_dt_dd(page, "Company size")
        data["specialties"] = _extract_dt_dd(page, "Specialties")
        data["employees_on_linkedin"] = _extract_dt_dd(page, "Employees on LinkedIn")

        # Website link next to label
        try:
            dt = page.locator("dt:has-text('Website')").first
            if dt.count() > 0:
                site_link = dt.locator("xpath=following-sibling::dd[1]//a").first
                data["website"] = _safe_attr(site_link, "href")
        except Exception:
            pass

        context.close()
        browser.close()
        return data

if __name__ == "__main__":
    url = "https://www.linkedin.com/company/deepsolv/"
    result = scrape_company(url)
    print(json.dumps(result, indent=2, ensure_ascii=False))