import pandas as pd
import os
import glob
from dotenv import load_dotenv

load_dotenv()
from config.settings import DELAY_RANGE
from config.platforms import ENABLE_GOOGLE, ENABLE_CHATGPT, ENABLE_CLAUDE
from scanners.google_ai import scan_google, create_driver
from scanners.chatgpt import scan_chatgpt
from scanners.claude import scan_claude
from core.utils import sleep_random
from output.sheet_writer import write_result_row, init_output_file, load_completed_keywords


def run():
    # --- Read input keywords ---
    input_files = glob.glob('input/*.xlsx')
    if not input_files:
        print("❌ No input Excel file found in input/ directory.")
        return

    print(f"📂 Reading keywords from {input_files[0]}")
    df = pd.read_excel(input_files[0], engine="openpyxl")

    if "Keywords" not in df.columns:
        for col in df.columns:
            if col.lower().strip() in ("keyword", "keywords", "kw"):
                df.rename(columns={col: "Keywords"}, inplace=True)
                break
        else:
            print(f"❌ Could not find 'Keywords' column. Available columns: {list(df.columns)}")
            return

    # Process up to 20 keywords
    keywords_to_process = df["Keywords"].dropna().head(20).tolist()
    total = len(keywords_to_process)
    print(f"📋 Found {total} keywords to process")

    # --- Initialize output file ---
    output_file = "output/results.xlsx"
    init_output_file(output_file)

    # --- Check for already-completed keywords (resume support) ---
    completed = load_completed_keywords(output_file)
    if completed:
        print(f"⏩ Resuming — {len(completed)} keywords already processed, skipping them")

    # --- Open browser ONCE for all keywords ---
    print("🌐 Opening browser...")
    browser = create_driver()

    try:
        for i, kw in enumerate(keywords_to_process, 1):
            kw = str(kw).strip()

            # Skip already processed keywords
            if kw.lower() in completed:
                print(f"  [{i}/{total}] ⏭️  Skipping (already done): {kw}")
                continue

            print(f"\n{'='*60}")
            print(f"  [{i}/{total}] 🔍 Processing: {kw}")
            print(f"{'='*60}")

            row = {"Keyword": kw}

            # --- Check if browser is still alive, restart if needed ---
            try:
                browser.current_url  # Quick check
            except Exception:
                print("  🔄 Browser crashed, restarting...")
                try:
                    browser.quit()
                except Exception:
                    pass
                browser = create_driver()

            # --- Step 1: Google AI Overview ---
            if ENABLE_GOOGLE:
                print(f"  📌 Searching Google...")
                g = scan_google(kw, browser)
                row["AI Overview Present"] = g["ai_present"]
                row["Pristyn Care in AI Overview"] = g["pristyn_in_google"]
                print(f"     AI Overview: {g['ai_present']} | Pristyn Care: {g['pristyn_in_google']}")
            else:
                row["AI Overview Present"] = "Skipped"
                row["Pristyn Care in AI Overview"] = "Skipped"

            # --- Step 2: ChatGPT (browser) ---
            if ENABLE_CHATGPT:
                print(f"  📌 Checking ChatGPT...")
                try:
                    browser.current_url
                except Exception:
                    print("  🔄 Browser crashed, restarting...")
                    try:
                        browser.quit()
                    except Exception:
                        pass
                    browser = create_driver()
                c = scan_chatgpt(kw, browser)
                row["Pristyn Care in ChatGPT"] = c["pristyn_in_chatgpt"]
                print(f"     Pristyn Care in ChatGPT: {c['pristyn_in_chatgpt']}")
            else:
                row["Pristyn Care in ChatGPT"] = "Skipped"

            # --- Step 3: Claude (browser) ---
            if ENABLE_CLAUDE:
                print(f"  📌 Checking Claude...")
                try:
                    browser.current_url
                except Exception:
                    print("  🔄 Browser crashed, restarting...")
                    try:
                        browser.quit()
                    except Exception:
                        pass
                    browser = create_driver()
                cl = scan_claude(kw, browser)
                row["Pristyn Care in Claude"] = cl["pristyn_in_claude"]
                print(f"     Pristyn Care in Claude: {cl['pristyn_in_claude']}")
            else:
                row["Pristyn Care in Claude"] = "Skipped"

            # --- Write result immediately ---
            write_result_row(output_file, row)
            print(f"  ✅ Result saved for: {kw}")

            # Delay between keywords (skip for the last one)
            if i < total:
                delay = sleep_random(*DELAY_RANGE)
                print(f"  ⏳ Waiting {delay}s before next keyword...")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Results saved so far. You can resume later.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        print("\n🔒 Closing browser...")
        try:
            browser.quit()
        except Exception:
            pass

    print(f"\n✅ Done! Results saved to {output_file}")


if __name__ == "__main__":
    run()
