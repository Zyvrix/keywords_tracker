from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import os

from config.settings import BRAND_VARIANTS

# Persistent profile directory so Google sees a "returning" browser
PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".chrome_profile")


def create_driver():
    """Create a Chrome driver with anti-detection options."""
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/chromium-browser"

    # Anti-bot-detection flags
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Use a persistent profile to keep cookies across runs (reduces CAPTCHA)
    options.add_argument(f"--user-data-dir={os.path.abspath(PROFILE_DIR)}")

    # Real user-agent string
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    )

    # Misc flags to look more human
    options.add_argument("--start-maximized")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-popup-blocking")

    browser = webdriver.Chrome(options=options)

    # Remove navigator.webdriver flag via CDP
    browser.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )

    return browser


def _human_type(element, text):
    """Type text character-by-character with random delays to mimic human input."""
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.04, 0.15))


def scan_google(keyword, browser):
    """Search a keyword on Google and check for AI Overview + Pristyn Care.

    Returns dict with:
        ai_present: "Yes" or "No"
        pristyn_in_google: "Yes", "No", or "N/A" (if no AI Overview)
    """
    ai_present = "No"
    pristyn_in_google = "N/A"
    ai_text = ""

    try:
        browser.get("https://www.google.com")
        time.sleep(random.uniform(1.0, 2.0))

        # Accept consent if shown
        try:
            consent_btn = WebDriverWait(browser, 3).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                    "'abcdefghijklmnopqrstuvwxyz'), 'accept')]"))
            )
            consent_btn.click()
            time.sleep(1)
        except Exception:
            pass

        search_box = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )

        # Type like a human
        _human_type(search_box, keyword)
        time.sleep(random.uniform(0.5, 1.5))
        search_box.send_keys(Keys.RETURN)

        # Wait for page load and AI overview generation
        time.sleep(random.uniform(4, 6))

        # --- Detect AI Overview ---
        # Try multiple selectors Google uses for AI Overview
        ai_overview_selectors = [
            "div[id='kp-wp-tab-overview']",        # AI Overview container
            "div[class*='ai-overview']",            # Class-based
            "div[data-attrid='AIOverview']",        # Data attribute
            "div[jsname='N760b']",                  # jsname selector
            "div.wDYxhc[data-md]",                  # Common AI overview wrapper
        ]

        ai_overview_element = None
        for selector in ai_overview_selectors:
            try:
                elements = browser.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    ai_overview_element = elements[0]
                    break
            except Exception:
                continue

        # Fallback: check the entire page body text for AI Overview keywords
        page_text = browser.find_element(By.TAG_NAME, "body").text.lower()
        ai_keywords = [
            "ai overview",
            "generative ai",
            "ai-generated",
            "this response was generated",
        ]

        if ai_overview_element:
            ai_present = "Yes"
            ai_text = ai_overview_element.text
        elif any(k in page_text for k in ai_keywords):
            ai_present = "Yes"
            ai_text = page_text

        # --- Check Pristyn Care in AI Overview ---
        if ai_present == "Yes" and ai_text:
            text_lower = ai_text.lower()
            if any(v in text_lower for v in BRAND_VARIANTS):
                pristyn_in_google = "Yes"
            else:
                pristyn_in_google = "No"

    except Exception as e:
        print(f"  ❌ Error checking Google for '{keyword}': {e}")

    return {
        "ai_present": ai_present,
        "pristyn_in_google": pristyn_in_google,
    }
