"""Main pipeline: collect → preprocess → generate daily digest."""

import sys
import os
import json
import yaml
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collectors.rss import collect_rss
from src.collectors.twitter import collect_twitter
from src.processor.preprocessor import preprocess
from src.processor.generator import generate_digest
from src.publisher.wechat import publish as wechat_publish


def run(hours=24):
    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"=== AI Feeds Daily Digest: {date_str} ===\n")

    # 1. Collect
    print("[1/5] Collecting RSS feeds...")
    rss_items = collect_rss(hours=hours)
    print(f"  Total RSS items: {len(rss_items)}\n")

    print("[2/5] Collecting X/Twitter...")
    twitter_items = collect_twitter(hours=hours)
    print(f"  Total Twitter items: {len(twitter_items)}\n")

    all_items = rss_items + twitter_items
    print(f"Total items collected: {len(all_items)}\n")

    if not all_items:
        print("No items found. Try increasing the time window.")
        return

    # Save raw data
    os.makedirs("data", exist_ok=True)
    raw_path = f"data/raw-{date_str}.json"
    with open(raw_path, "w") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    print(f"Raw data saved to {raw_path}")

    # 2. Preprocess
    print("\n[3/5] Preprocessing (score → dedup → classify → sort)...")
    with open("config/x_accounts.yaml") as f:
        accounts_config = yaml.safe_load(f)

    processed_items, stats = preprocess(all_items, accounts_config)
    print(f"  Original: {stats['original']} → After dedup: {stats['after_dedup']} (removed {stats['removed']})")

    # Save processed data
    processed_path = f"data/processed-{date_str}.json"
    with open(processed_path, "w") as f:
        json.dump(processed_items, f, ensure_ascii=False, indent=2)
    print(f"  Processed data saved to {processed_path}")

    # 3. Generate digest
    print(f"\n[4/5] Generating digest with LLM...")
    digest = generate_digest(processed_items, date_str)

    # 4. Save output
    output_path = f"data/digest-{date_str}.md"
    with open(output_path, "w") as f:
        f.write(digest)
    print(f"\nDigest saved to {output_path}")

    # 5. Publish to WeChat
    if os.environ.get("WECHAT_APP_ID"):
        print(f"\n[5/5] Publishing to WeChat...")
        try:
            wechat_publish(digest, date_str)
        except Exception as e:
            print(f"  WeChat publish failed: {e}")
    else:
        print("\n[5/5] Skipping WeChat publish (WECHAT_APP_ID not set)")

    print("\n" + "=" * 50)
    print(digest)


if __name__ == "__main__":
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    run(hours=hours)
