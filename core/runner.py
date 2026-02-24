import pandas as pd
import os
import glob
from dotenv import load_dotenv

load_dotenv()
from config.settings import BRAND_NAME, DELAY_RANGE
from scanners.google_ai import scan_google, create_driver
from scanners.chatgpt import scan_chatgpt
from scanners.claude import scan_claude
from core.brand_matcher import is_brand_mentioned
from core.utils import sleep_random

def run():
    input_files = glob.glob('input/*.xlsx')
    if not input_files:
        print("No input excel file found in input/ directory.")
        return
    
    print(f"Reading keywords from {input_files[0]}")
    df = pd.read_excel(input_files[0], engine="openpyxl")

    output_file = "output/results.csv"
    
    # Process up to 100 keywords
    keywords_to_process = df["Keywords"].dropna().head(100)

    # Open browser ONCE for all keywords
    print("Opening browser...")
    browser = create_driver()

    try:
        for i, kw in enumerate(keywords_to_process, 1):
            print(f"[{i}/100] Processing keyword: {kw}")
            row = {"keyword": kw}

            g = scan_google(kw, browser)
            row["google_ai_present"] = g["ai_present"]
            row["google_mentioned"] = is_brand_mentioned(g["text"], BRAND_NAME)

            try:
                c = scan_chatgpt(kw)
                row["chatgpt_mentioned"] = is_brand_mentioned(c["text"], BRAND_NAME)
            except Exception as e:
                print(f"ChatGPT scan failed for '{kw}': {e}")
                row["chatgpt_mentioned"] = False

            try:
                cl = scan_claude(kw)
                row["claude_mentioned"] = is_brand_mentioned(cl["text"], BRAND_NAME)
            except Exception as e:
                print(f"Claude scan failed for '{kw}': {e}")
                row["claude_mentioned"] = False

            row_df = pd.DataFrame([row])
            if not os.path.isfile(output_file):
                row_df.to_csv(output_file, index=False)
            else:
                row_df.to_csv(output_file, mode='a', header=False, index=False)

            if i < len(keywords_to_process):
                sleep_random(*DELAY_RANGE)
    finally:
        # Close browser only after ALL keywords are done
        print("Closing browser...")
        browser.quit()

if __name__ == "__main__":
    run()

