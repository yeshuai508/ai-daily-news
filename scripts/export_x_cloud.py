import json,sys
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.collectors.twitter import collect_twitter_report
JST=ZoneInfo("Asia/Tokyo")
now=datetime.now(JST); prev=now.date()-timedelta(days=1); start=datetime(prev.year,prev.month,prev.day,tzinfo=JST)
r=collect_twitter_report(int((now-start).total_seconds()//3600)+2)
items=[x for x in r["items"] if start<=datetime.fromisoformat(x["published"]).astimezone(JST)<=now]
out={"schema":"ai-daily-news.x-cloud.v1","generated_at":now.isoformat(),"window_start":start.isoformat(),"window_end":now.isoformat(),"write_actions":"NONE","coverage":r["coverage"],"expected_accounts":r["expected_accounts"],"successful_accounts":r["successful_accounts"],"targets":r["targets"],"items":items}
Path("cloud-output").mkdir(exist_ok=True);Path("cloud-output/x-latest.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
print("X_CLOUD_EXPORT_PASS",out["coverage"],out["successful_accounts"],"/",out["expected_accounts"],len(items))
