"""X/Twitter collector using twikit."""

import asyncio
import yaml
import os
from datetime import datetime, timedelta, timezone
from twikit import Client
from dotenv import load_dotenv

load_dotenv()


async def _collect(hours=24) -> list[dict]:
    proxy = os.getenv("PROXY_URL")
    client = Client("en-US", proxy=proxy)
    client.set_cookies({
        "auth_token": os.getenv("X_AUTH_TOKEN"),
        "ct0": os.getenv("X_CT0"),
    })

    with open("config/x_accounts.yaml") as f:
        config = yaml.safe_load(f)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items = []

    for account in config.get("accounts", []):
        handle = account["handle"]
        name = account.get("name", handle)
        bio = account.get("bio", "")
        print(f"  Fetching X: @{handle}")
        try:
            user = await client.get_user_by_screen_name(handle)
            tweets = await user.get_tweets("Tweets", count=10)
            count = 0
            for tweet in tweets:
                created = datetime.strptime(
                    tweet.created_at, "%a %b %d %H:%M:%S %z %Y"
                )
                if created < cutoff:
                    continue
                items.append({
                    "title": f"@{handle}: {tweet.text[:80]}",
                    "url": f"https://x.com/{handle}/status/{tweet.id}",
                    "summary": tweet.text,
                    "source": f"@{handle}",
                    "source_name": name,
                    "source_bio": bio,
                    "source_type": "twitter",
                    "published": created.isoformat(),
                    "metrics": {
                        "likes": tweet.favorite_count,
                        "retweets": tweet.retweet_count,
                        "replies": tweet.reply_count,
                    },
                })
                count += 1
            print(f"    Got {count} tweets")
            await asyncio.sleep(3)  # rate limit
        except Exception as e:
            if "429" in str(e):
                print(f"    Rate limited, waiting 60s...")
                await asyncio.sleep(60)
                try:
                    user = await client.get_user_by_screen_name(handle)
                    tweets = await user.get_tweets("Tweets", count=10)
                    count = 0
                    for tweet in tweets:
                        created = datetime.strptime(
                            tweet.created_at, "%a %b %d %H:%M:%S %z %Y"
                        )
                        if created < cutoff:
                            continue
                        items.append({
                            "title": f"@{handle}: {tweet.text[:80]}",
                            "url": f"https://x.com/{handle}/status/{tweet.id}",
                            "summary": tweet.text,
                            "source": f"@{handle}",
                            "source_name": name,
                            "source_bio": bio,
                            "source_type": "twitter",
                            "published": created.isoformat(),
                            "metrics": {
                                "likes": tweet.favorite_count,
                                "retweets": tweet.retweet_count,
                                "replies": tweet.reply_count,
                            },
                        })
                        count += 1
                    print(f"    Retry got {count} tweets")
                except Exception as e2:
                    print(f"    Retry failed: {e2}")
            else:
                print(f"    Error: {e}")

    return items


def collect_twitter(hours=24) -> list[dict]:
    return asyncio.run(_collect(hours))
