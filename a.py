import requests
import pandas as pd
from datetime import datetime
import os
import time
import html

# --- 1. 설정 및 수집 대상 단지 목록 ---
TELEGRAM_TOKEN = "8683637658:AAHOUm2Q04bEqOR83TvEpoP19d26v-sZzjg"
CHAT_ID = "98017929"

# 여기에 수집하고 싶은 단지번호(hscpNo)와 이름을 추가하세요.
COMPLEX_LIST = [
    {"id": "3450", "name": "문래힐스테이트"},
    {"id": "3452", "name": "문래자이"}, # 예시 단지 추가
    # {"id": "12345", "name": "추가단지이름"},
]

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload)
        if not res.json().get("ok"):
            print(f"❌ 전송 실패: {res.json().get('description')}")
    except Exception as e:
        print(f"❌ 네트워크 에러: {e}")

def get_naver_land_data(hscpNo, hscpName):
    all_articles = []
    # 페이지 수집 (1~3페이지만 훑어도 웬만한 최신 매물은 다 나옵니다)
    for page in range(1, 4):
        url = f"https://m.land.naver.com/complex/getComplexArticleList?hscpNo={hscpNo}&tradTpCd=A1&order=prc&showConfirm=false&page={page}"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36", "Referer": "https://m.land.naver.com/"}
        try:
            response = requests.get(url, headers=headers)
            articles = response.json().get('result', {}).get('list', [])
            if not articles: break
            all_articles.extend(articles)
            time.sleep(0.5)
        except: break

    if not all_articles:
        print(f"{hscpName} 데이터 없음")
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
        
        item_str = f"📍 <b>{name} ({floor})</b>\n"
        item_str += f"💰 <b>{price}</b> ({spc1}/{spc2}㎡)\n"
        item_str += f"📝 {feature[:40]}...\n\n"

        if len(msg + item_str) > 4000:
            send_telegram_msg(msg)
            msg = header + " (계속)\n\n"
        
        msg += item_str

    send_telegram_msg(msg)
    print(f"✅ {hscpName} 전송 완료")

# --- 메인 실행부 ---
print(f"🚀 수집 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

for complex_info in COMPLEX_LIST:
    get_naver_land_data(complex_info["id"], complex_info["name"])
    time.sleep(1) # 단지 사이의 간격을 둬서 차단 방지

print("🏁 모든 단지 수집 및 전송 완료!")