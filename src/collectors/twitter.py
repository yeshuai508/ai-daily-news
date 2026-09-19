"""Read-only X collector using twikit."""
import asyncio, os, yaml
from datetime import datetime, timedelta, timezone
from twikit import Client
from dotenv import load_dotenv
load_dotenv()
MAX_TWEETS_PER_ACCOUNT=40
async def _collect_report(hours=40):
    auth=os.getenv("X_AUTH_TOKEN"); ct0=os.getenv("X_CT0")
    if not auth or not ct0: raise RuntimeError("X read-only secrets are required")
    client=Client("en-US",proxy=os.getenv("PROXY_URL"))
    client.set_cookies({"auth_token":auth,"ct0":ct0})
    config=yaml.safe_load(open("config/x_accounts.yaml")) or {}
    cutoff=datetime.now(timezone.utc)-timedelta(hours=hours)
    items=[]; targets=[]
    for account in config.get("accounts",[]):
        h=account["handle"]
        try:
            user=await client.get_user_by_screen_name(h)
            tweets=await user.get_tweets("Tweets",count=MAX_TWEETS_PER_ACCOUNT)
            n=0
            for t in tweets:
                created=datetime.strptime(t.created_at,"%a %b %d %H:%M:%S %z %Y")
                if created < cutoff: continue
                items.append({"title":f"@{h}: {t.text[:80]}","url":f"https://x.com/{h}/status/{t.id}","summary":t.text,"source":f"@{h}","source_type":"twitter","published":created.isoformat()})
                n+=1
            targets.append({"handle":h,"ok":True,"items":n})
        except Exception as e:
            targets.append({"handle":h,"ok":False,"error":str(e)[:300]})
        await asyncio.sleep(2)
    ok=sum(1 for x in targets if x["ok"]); expected=len(targets)
    coverage="COMPLETE" if expected and ok==expected else ("FAILED" if ok==0 else "PARTIAL")
    return {"coverage":coverage,"expected_accounts":expected,"successful_accounts":ok,"targets":targets,"items":items}
def collect_twitter_report(hours=40): return asyncio.run(_collect_report(hours))
def collect_twitter(hours=24): return collect_twitter_report(hours)["items"]
