"""Tencent SCF: transparent proxy for api.weixin.qq.com/cgi-bin/*"""

import json
import urllib.request
import urllib.parse

WECHAT_BASE = "https://api.weixin.qq.com/cgi-bin"


def main_handler(event, context):
    # API Gateway trigger: event contains httpMethod, path, queryString, body
    path = event.get("path", "/")
    method = event.get("httpMethod", "GET").upper()
    query = event.get("queryString") or {}
    body = event.get("body") or ""

    # Build target URL
    qs = urllib.parse.urlencode(query) if query else ""
    url = f"{WECHAT_BASE}{path}"
    if qs:
        url += f"?{qs}"

    # Forward request
    headers = {"Content-Type": "application/json"}
    data = body.encode("utf-8") if body and method == "POST" else None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = resp.read().decode("utf-8")

    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": result,
    }
