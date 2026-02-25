import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config.settings import CHATGPT_URL, AI_RESPONSE_TIMEOUT, BRAND_VARIANTS


def _human_type(element, text):
    """Type text character-by-character with random delays."""
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.04, 0.15))


def _wait_for_chatgpt_response(browser, timeout=AI_RESPONSE_TIMEOUT):
    """Wait for ChatGPT to finish generating its response."""
    start = time.time()
    time.sleep(5)  # Initial wait for response to start

    while time.time() - start < timeout:
        try:
            # Check if the "stop generating" button is present (means still typing)
            stop_buttons = browser.find_elements(By.CSS_SELECTOR,
                "button[aria-label='Stop generating'],"
                "button[data-testid='stop-button'],"
                "button.stop-button"
            )
            if stop_buttons and any(b.is_displayed() for b in stop_buttons):
                time.sleep(2)
                continue

            # Also check for any streaming indicators
            streaming = browser.find_elements(By.CSS_SELECTOR,
                "div.result-streaming, div.markdown.result-streaming"
            )
            if streaming and any(s.is_displayed() for s in streaming):
                time.sleep(2)
                continue

            # No streaming indicators found — response is likely complete
            time.sleep(2)
            return True

        except Exception:
            time.sleep(2)

    return True  # Timeout reached, proceed anyway


def scan_chatgpt(keyword, browser):
    """Open ChatGPT in a new tab, search the keyword, check for Pristyn Care.

    Returns dict with:
        pristyn_in_chatgpt: "Yes" or "No"
    """
    pristyn_in_chatgpt = "No"
    original_window = browser.current_window_handle

    try:
        # Open new tab
        browser.execute_script("window.open('');")
        time.sleep(1)
        browser.switch_to.window(browser.window_handles[-1])

        # Navigate to ChatGPT
        browser.get(CHATGPT_URL)
        time.sleep(random.uniform(3, 5))

        # Find the chat input area — try multiple selectors
        input_selectors = [
            "div#prompt-textarea",           # Main prompt textarea (contenteditable div)
            "textarea#prompt-textarea",      # Textarea variant
            "div[contenteditable='true']",   # Generic contenteditable
            "textarea[placeholder*='Message']",  # Placeholder-based
            "textarea[placeholder*='Ask']",      # Alt placeholder
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
            print(f"  ⚠️  ChatGPT: Could not find input field for '{keyword}'")
            return {"pristyn_in_chatgpt": "No"}

        # Click and type the keyword
        chat_input.click()
        time.sleep(0.5)
        _human_type(chat_input, keyword)
        time.sleep(random.uniform(0.5, 1.0))

        # Submit — try Enter key first, then look for send button
        try:
            send_buttons = browser.find_elements(By.CSS_SELECTOR,
                "button[data-testid='send-button'],"
                "button[aria-label='Send prompt'],"
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
        _wait_for_chatgpt_response(browser)

        # Extract response text — get the last assistant message
        response_selectors = [
            "div[data-message-author-role='assistant']",
            "div.markdown.prose",
            "div.agent-turn div.markdown",
            "div[class*='response']",
        ]

        response_text = ""
        for selector in response_selectors:
            try:
                elements = browser.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # Get the last response element (most recent)
                    response_text = elements[-1].text
                    break
            except Exception:
                continue

        # Check for Pristyn Care
        if response_text:
            text_lower = response_text.lower()
            if any(v in text_lower for v in BRAND_VARIANTS):
                pristyn_in_chatgpt = "Yes"

    except Exception as e:
        print(f"  ❌ ChatGPT scan failed for '{keyword}': {e}")

    finally:
        # Close the ChatGPT tab and switch back
        try:
            browser.close()
            browser.switch_to.window(original_window)
        except Exception:
            pass

    return {"pristyn_in_chatgpt": pristyn_in_chatgpt}
