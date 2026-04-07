import requests
from bs4 import BeautifulSoup
import time
import datetime
import os
import json
import sys

CHECK_INTERVAL_SECONDS = 30
KEYWORDS = ["포코피아", "포켓몬 포코피아", "Pokopia"]
EXCLUDE_KEYWORDS = ["종료", "품절", "마감", "다운로드", "DL판", "🔒"]
SEEN_IDS_FILE = "seen_ids.json"
RULIWEB_URL = "https://bbs.ruliweb.com/market/board/1020"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9"
}

def send_notification(title, message, url=""):
    print(f"\n{'='*60}\n🚨 [알림] {title}\n   {message}")
    if url:
        print(f"   링크: {url}")
    print(f"{'='*60}\n")
    if sys.platform == "win32":
        try:
            from plyer import notification
            notification.notify(title=title, message=message[:200], app_name="포코피아 모니터", timeout=10)
        except:
            pass
        import winsound
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    elif sys.platform == "darwin":
        os.system(f'osascript -e \'display notification "{message}" with title "{title}"\'')
        os.system("afplay /System/Library/Sounds/Glass.aiff")

def load_seen_ids():
    if os.path.exists(SEEN_IDS_FILE):
        with open(SEEN_IDS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen_ids(seen_ids):
    with open(SEEN_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_ids)[-500:], f)

def fetch_posts():
    try:
        resp = requests.get(RULIWEB_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"요청 실패: {e}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    posts = []
    for row in soup.select("tr.table_body"):
        tag = row.select_one("a.deco")
        if not tag:
            continue
        title = tag.get_text(strip=True)
        link = tag.get("href", "")
        if link and not link.startswith("http"):
            link = "https://bbs.ruliweb.com" + link
        post_id = link.rstrip("/").split("/")[-1]
        posts.append({"id": post_id, "title": title, "link": link})
    return posts

def is_target(title):
    t = title.lower()
    return any(k.lower() in t for k in KEYWORDS) and not any(e.lower() in t for e in EXCLUDE_KEYWORDS)

def now():
    return datetime.datetime.now().strftime("%H:%M:%S")

def main():
    print("="*60)
    print("  포코피아 재고 모니터링 시작 | Ctrl+C 로 종료")
    print(f"  확인 주기: {CHECK_INTERVAL_SECONDS}초")
    print("="*60)
    seen_ids = load_seen_ids()
    count = 0
    while True:
        count += 1
        print(f"[{now()}] #{count} 확인 중...", end=" ")
        posts = fetch_posts()
        targets = [p for p in posts if p["id"] not in seen_ids and is_target(p["title"])]
        for p in posts:
            seen_ids.add(p["id"])
        save_seen_ids(seen_ids)
        if targets:
            for p in targets:
                send_notification("🎮 포코피아 패키지 핫딜!", p["title"], p["link"])
        else:
            print(f"없슨 (다음: {CHECK_INTERVAL_SECONDS}초 후)")
        try:
            time.sleep(CHECK_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\n종료.")
            break

if __name__ == "__main__":
    main()