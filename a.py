import requests
import pandas as pd
from datetime import datetime
import os
import time
import html

# --- 설정 (환경 변수 방식) ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

COMPLEX_LIST = [
    {"id": "19672", "name": "동탄솔빛쌍용예가"},
    # 추가 단지가 있다면 여기에 넣으세요
]

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        # 텔레그램 전송에도 타임아웃 추가
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"텔레그램 발송 실패: {e}")

def get_naver_land_data(hscpNo, hscpName):
    print(f"🔍 {hscpName} 수집 시작...")
    all_articles = []
    
    for page in range(1, 4):
        url = f"https://m.land.naver.com/complex/getComplexArticleList?hscpNo={hscpNo}&tradTpCd=A1&order=prc&showConfirm=false&page={page}"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36", "Referer": "https://m.land.naver.com/"}
        
        try:
            # [핵심] timeout=10 추가: 10초 동안 응답 없으면 중단하고 다음으로!
            response = requests.get(url, headers=headers, timeout=10)
            articles = response.json().get('result', {}).get('list', [])
            if not articles: break
            all_articles.extend(articles)
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ {hscpName} {page}페이지 수집 중 타임아웃 또는 에러: {e}")
            break

    if not all_articles:
        print(f"❌ {hscpName} 데이터 없음")
        return

    df = pd.DataFrame(all_articles).drop_duplicates(subset=['atclNo'])
    header = f"<b>🏢 {hscpName} ({len(df)}건)</b>\n"
    msg = header

    for i, row in df.iterrows():
        name = html.escape(str(row.get('atclNm', '매물')))
        price = html.escape(str(row.get('tradePriceHan') or row.get('prcInfo') or '가격없음'))
        feature = html.escape(str(row.get('atclFetrDesc', '')))
        floor = html.escape(str(row.get('flrInfo', '-')))
        spc1 = str(row.get('spc1', '-'))
        spc2 = str(row.get('spc2', '-'))
        
        item_str = f"📍 <b>{name} ({floor})</b>\n💰 <b>{price}</b> ({spc1}/{spc2}㎡)\n📝 {feature[:40]}...\n\n"

        if len(msg + item_str) > 4000:
            send_telegram_msg(msg)
            msg = header + " (계속)\n\n"
        msg += item_str

    send_telegram_msg(msg)
    print(f"✅ {hscpName} 전송 완료")

# 메인 실행
if __name__ == "__main__":
    for complex_info in COMPLEX_LIST:
        get_naver_land_data(complex_info["id"], complex_info["name"])
    print("🏁 작업 종료")
