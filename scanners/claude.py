import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config.settings import CLAUDE_URL, AI_RESPONSE_TIMEOUT, BRAND_VARIANTS


def _human_type(element, text):
    """Type text character-by-character with random delays."""
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.04, 0.15))


def _wait_for_claude_response(browser, timeout=AI_RESPONSE_TIMEOUT):
    """Wait for Claude to finish generating its response."""
    start = time.time()
    time.sleep(5)  # Initial wait for response to start

    while time.time() - start < timeout:
        try:
            # Check if Claude is still generating (stop button visible)
            stop_buttons = browser.find_elements(By.CSS_SELECTOR,
                "button[aria-label='Stop Response'],"
                "button[aria-label='Stop'],"
                "button.stop-button"
            )
            if stop_buttons and any(b.is_displayed() for b in stop_buttons):
                time.sleep(2)
                continue

            # Check for streaming cursor/indicator
            streaming = browser.find_elements(By.CSS_SELECTOR,
                "div.cursor-blink, span.cursor"
            )
            if streaming and any(s.is_displayed() for s in streaming):
                time.sleep(2)
                continue

            # Response likely complete
            time.sleep(2)
            return True

        except Exception:
            time.sleep(2)

    return True  # Timeout reached, proceed anyway


def scan_claude(keyword, browser):
    """Open Claude in a new tab, search the keyword, check for Pristyn Care.

    Returns dict with:
        pristyn_in_claude: "Yes" or "No"
    """
    pristyn_in_claude = "No"
    original_window = browser.current_window_handle

    try:
        # Open new tab
        browser.execute_script("window.open('');")
        time.sleep(1)
        browser.switch_to.window(browser.window_handles[-1])

        # Navigate to Claude
        browser.get(CLAUDE_URL)
        time.sleep(random.uniform(3, 5))

        # Find the chat input area — try multiple selectors
        input_selectors = [
            "div[contenteditable='true'].ProseMirror",  # Claude's ProseMirror editor
            "div[contenteditable='true']",               # Generic contenteditable
            "fieldset div[contenteditable='true']",      # Inside fieldset
            "textarea[placeholder*='Reply']",            # Textarea variant
            "div.ProseMirror",                           # ProseMirror class
        ]

        chat_input = None
        for selector in input_selectors:
            try:
                chat_input = WebDriverWait(browser, 8).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if chat_input:
                    break
            except Exception:
                continue

        if not chat_input:
            print(f"  ⚠️  Claude: Could not find input field for '{keyword}'")
            return {"pristyn_in_claude": "No"}

        # Click and type the keyword
        chat_input.click()
        time.sleep(0.5)
        _human_type(chat_input, keyword)
        time.sleep(random.uniform(0.5, 1.0))

        # Submit — try send button first, then Enter
        try:
            send_buttons = browser.find_elements(By.CSS_SELECTOR,
                "button[aria-label='Send Message'],"
                "button[aria-label='Send'],"
                "button.send-button"
            )
            if send_buttons and any(b.is_enabled() for b in send_buttons):
                for btn in send_buttons:
                    if btn.is_enabled():
                        btn.click()
                        break
            else:
                chat_input.send_keys(Keys.RETURN)
        except Exception:
            chat_input.send_keys(Keys.RETURN)

        # Wait for response to complete
        _wait_for_claude_response(browser)

        # Extract response text — get the last assistant message
        response_selectors = [
            "div[data-is-streaming]",
            "div.prose",
            "div.font-claude-message",
            "div[class*='response']",
            "div[class*='message'] div.prose",
        ]

        response_text = ""
        for selector in response_selectors:
            try:
                elements = browser.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    response_text = elements[-1].text
                    break
            except Exception:
                continue

        # Fallback: get all text from the page and look for response area
        if not response_text:
            try:
                body_text = browser.find_element(By.TAG_NAME, "body").text
                response_text = body_text
            except Exception:
                pass

        # Check for Pristyn Care
        if response_text:
            text_lower = response_text.lower()
            if any(v in text_lower for v in BRAND_VARIANTS):
                pristyn_in_claude = "Yes"

    except Exception as e:
        print(f"  ❌ Claude scan failed for '{keyword}': {e}")

    finally:
        # Close the Claude tab and switch back
        try:
            browser.close()
            browser.switch_to.window(original_window)
        except Exception:
            pass

    return {"pristyn_in_claude": pristyn_in_claude}
