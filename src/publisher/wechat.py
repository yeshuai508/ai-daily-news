"""WeChat Official Account publisher: markdown → HTML → draft."""

import os
import time
import json
import requests
import markdown

# Token cache
_token_cache = {"token": None, "expires_at": 0}

WECHAT_API = os.environ.get("WECHAT_API_BASE", "https://api.weixin.qq.com/cgi-bin")


def get_access_token():
    """Get access_token with caching (valid for 2 hours)."""
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["token"]

    app_id = os.environ["WECHAT_APP_ID"]
    app_secret = os.environ["WECHAT_APP_SECRET"]

    resp = requests.get(
        f"{WECHAT_API}/token",
        params={
            "grant_type": "client_credential",
            "appid": app_id,
            "secret": app_secret,
        },
        timeout=10,
    )
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Failed to get access_token: {data}")

    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 7200)
    return _token_cache["token"]


def md_to_html(markdown_text):
    """Convert markdown to WeChat-compatible HTML with inline styles."""
    import re

    # Remove h1 title (duplicates draft title)
    text = re.sub(r'^#\s+.+\n*', '', markdown_text, count=1)

    # Extract links and replace with footnote markers before HTML conversion
    # Handles both [来源](url) and [原文](url) patterns
    footnotes = []

    def replace_link(match):
        url = match.group(2)
        footnotes.append(url)
        return f'<sup style="font-size:10px;color:#999;">[{len(footnotes)}]</sup>'

    text = re.sub(r'\s*\[([^\]]*?)\]\((https?://[^\)]+)\)', replace_link, text)

    html_body = markdown.markdown(
        text,
        extensions=["extra", "nl2br", "sane_lists"],
    )

    # Remove <p> tags nested inside <li> (WeChat renders them poorly)
    html_body = re.sub(r'<li>\s*<p>', '<li>', html_body)
    html_body = re.sub(r'</p>\s*</li>', '</li>', html_body)

    # Replace <ul>/<li> with styled <section> blocks for better WeChat compatibility
    def replace_list(match):
        items = re.findall(r'<li(?:[^>]*)>(.*?)</li>', match.group(0), re.DOTALL)
        sections = []
        for item in items:
            sections.append(
                f'<section style="font-size:15px;color:#333;line-height:1.8;'
                f'margin:12px 0;padding:10px 12px;background:#f7f7f7;border-radius:4px;">'
                f'{item.strip()}</section>'
            )
        return '\n'.join(sections)

    html_body = re.sub(r'<ul[^>]*>.*?</ul>', replace_list, html_body, flags=re.DOTALL)

    # Inline styles for remaining elements
    styled = html_body
    styled = styled.replace("<h2>", '<h2 style="font-size:18px;font-weight:bold;color:#333;margin:24px 0 10px;padding-bottom:6px;border-bottom:2px solid #eee;">')
    styled = styled.replace("<h3>", '<h3 style="font-size:16px;font-weight:bold;color:#555;margin:14px 0 6px;">')
    styled = styled.replace("<p>", '<p style="font-size:15px;color:#333;line-height:1.8;margin:8px 0;">')
    styled = styled.replace("<ol>", '<ol style="margin:8px 0;padding-left:20px;">')
    styled = styled.replace("<blockquote>", '<blockquote style="border-left:4px solid #ddd;padding:8px 16px;color:#666;margin:10px 0;background:#f9f9f9;">')
    styled = styled.replace("<strong>", '<strong style="color:#333;">')
    styled = styled.replace("<hr>", '<hr style="border:none;border-top:1px solid #eee;margin:16px 0;">')
    styled = styled.replace("<hr/>", '<hr style="border:none;border-top:1px solid #eee;margin:16px 0;"/>')
    styled = styled.replace("<hr />", '<hr style="border:none;border-top:1px solid #eee;margin:16px 0;" />')

    # Append footnotes section
    if footnotes:
        styled += '<hr style="border:none;border-top:1px solid #eee;margin:20px 0;" />'
        styled += '<section style="font-size:12px;color:#999;line-height:2;margin:10px 0;">'
        styled += '<p style="font-size:13px;color:#666;margin-bottom:6px;">参考链接（长按可复制）：</p>'
        for i, url in enumerate(footnotes, 1):
            styled += f'<p style="font-size:12px;color:#999;margin:2px 0;word-break:break-all;">[{i}] {url}</p>'
        styled += '</section>'

    return f'<div style="padding:10px 16px;font-family:-apple-system,BlinkMacSystemFont,sans-serif;">{styled}</div>'


def upload_thumb(image_path):
    """Upload cover image to WeChat material library, return media_id."""
    token = get_access_token()

    with open(image_path, "rb") as f:
        resp = requests.post(
            f"{WECHAT_API}/material/add_material",
            params={"access_token": token, "type": "image"},
            files={"media": ("cover.jpg", f, "image/jpeg")},
            timeout=30,
        )
    data = resp.json()
    if "media_id" not in data:
        raise RuntimeError(f"Failed to upload thumb: {data}")

    return data["media_id"]


def create_draft(title, html_content, thumb_media_id):
    """Create a draft article in WeChat backend."""
    token = get_access_token()

    payload = {
        "articles": [
            {
                "title": title,
                "author": "AI bot",
                "content": html_content,
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 0,
                "only_fans_can_comment": 0,
            }
        ]
    }

    resp = requests.post(
        f"{WECHAT_API}/draft/add",
        params={"access_token": token},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    data = resp.json()
    if data.get("errcode", 0) != 0:
        raise RuntimeError(f"Failed to create draft: {data}")

    return data.get("media_id")


def freepublish(media_id):
    """Publish a draft article (cannot be undone)."""
    token = get_access_token()
    resp = requests.post(
        f"{WECHAT_API}/freepublish/submit",
        params={"access_token": token},
        json={"media_id": media_id},
        timeout=15,
    )
    data = resp.json()
    if data.get("errcode", 0) != 0:
        raise RuntimeError(f"Failed to freepublish: {data}")
    return data.get("publish_id")


def upload_voice(audio_path):
    """Upload voice material to WeChat, return media_id."""
    token = get_access_token()

    with open(audio_path, "rb") as f:
        resp = requests.post(
            f"{WECHAT_API}/material/add_material",
            params={"access_token": token, "type": "voice"},
            files={"media": ("audio.mp3", f, "audio/mpeg")},
            timeout=60,
        )
    data = resp.json()
    if "media_id" not in data:
        raise RuntimeError(f"Failed to upload voice: {data}")

    return data["media_id"]


def embed_audio_in_html(html_content, voice_media_id):
    """Insert <mpvoice> tag after the opening <div> in HTML content."""
    voice_tag = (
        f'<mpvoice frameborder="0" width="580" height="55" '
        f'src="{voice_media_id}" name="AI Daily 语音版"></mpvoice>'
    )
    # Insert after the first <div ...>
    return html_content.replace(
        'font-family:-apple-system,BlinkMacSystemFont,sans-serif;">',
        f'font-family:-apple-system,BlinkMacSystemFont,sans-serif;">{voice_tag}',
        1,
    )


def publish(digest_md, date_str, filtered_info=None, audio_path=None):
    """Main entry: convert markdown → HTML, upload cover, create draft, publish."""
    print("  Converting markdown to HTML...")
    html_content = md_to_html(digest_md)

    # Embed audio if available
    if audio_path and os.path.isfile(audio_path):
        try:
            print("  Uploading voice material...")
            voice_media_id = upload_voice(audio_path)
            print(f"  Voice uploaded (media_id: {voice_media_id})")
            html_content = embed_audio_in_html(html_content, voice_media_id)
        except Exception as e:
            print(f"  Voice upload failed (publishing without audio): {e}")

    print("  Uploading cover image...")
    cover_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "assets",
        "cover.jpg",
    )
    thumb_media_id = upload_thumb(cover_path)

    print("  Creating draft...")
    title = f"AI Daily {date_str}"
    media_id = create_draft(title, html_content, thumb_media_id)
    print(f"  Draft created (media_id: {media_id})")

    print("  Publishing...")
    publish_id = freepublish(media_id)
    print(f"  Published (publish_id: {publish_id})")

    # Server酱微信通知
    serverchan_key = os.environ.get("SERVERCHAN_KEY")
    if serverchan_key:
        desp = f"日期：{date_str}\n\nmedia_id：`{media_id}`\n\npublish_id：`{publish_id}`"
        if filtered_info:
            desp += f"\n\n⚠ 已过滤敏感内容：{filtered_info}"
        try:
            requests.post(
                f"https://sctapi.ftqq.com/{serverchan_key}.send",
                data={
                    "title": "AI Daily 已自动发布",
                    "desp": desp,
                },
                timeout=10,
            )
            print("  Server酱通知已发送")
        except Exception as e:
            print(f"  Server酱通知失败: {e}")

    return media_id
