import googlemaps.client
import openai
import googlemaps
import streamlit as st
import random
import pandas as pd
import os

# 環境変数からAPIキーを取得
api_key = st.secrets["GOOGLE_MAPS_API_KEY"]

# Google Mapsクライアントを正しく初期化
gmaps = googlemaps.Client(key=api_key)

# OpenAI APIキーを設定
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 住所を緯度と経度に変換する関数
def geocode_address(address):
    geocode_result = gmaps.geocode(address, language='ja')
    if geocode_result:
        location = geocode_result[0]['geometry']['location']
        return location['lat'], location['lng']
    else:
        return None, None

# サウナのリストをGoogle Maps APIから取得する関数
def get_saunas_nearby(lat, lng, radius=100000):  # 半径100kmのサウナを検索
    places_result = gmaps.places_nearby(
        location=(lat, lng),
        radius=radius,
        keyword='sauna',
        language='ja'  # 日本語でのレスポンスを要求
    )
    return places_result['results']

# ラーメン屋のリストをGoogle Maps APIから取得する関数
def get_restaurants_nearby(lat, lng, radius=5000):  # サウナの近くの半径5km以内のラーメン屋を検索
    places_result = gmaps.places_nearby(
        location=(lat, lng),
        radius=radius,
        keyword='ラーメン',
        language='ja'  # 日本語でのレスポンスを要求
    )
    return places_result['results']

# OpenAIを使って気分を判定する関数
def analyze_mood(prompt):
    response = openai.chat.completions.create   (
        model="gpt-3.5-turbo",
        messages=[
             {"role": "system", "content": "あなたは日本語で応答するアシスタントです。"},
            {"role": "user", "content": prompt}
        ]
    )
    mood = response.choices[0].message.content.strip()
    return mood

# サウナをレコメンドする関数
def recommend_sauna(saunas, mood):
    random.seed(mood)
    return random.choice(saunas) if saunas else None

# Streamlit UI
st.title("サウナとラーメン屋レコメンドアプリ")

address = st.text_input("現在地の住所を入力してください（例: 東京都新宿区西新宿2-8-1）")
user_input = st.text_input("今日はどんな気分ですか？自由に入力してください。")

if st.button("サウナとラーメン屋をレコメンド"):
    if address and user_input:
        lat, lng = geocode_address(address)
        if lat and lng:
            saunas = get_saunas_nearby(lat, lng)
            mood = analyze_mood(f"今日は{user_input}気分です。おすすめのサウナを教えてください。")
            st.write(f"解析された気分: {mood}")

            recommended_sauna = recommend_sauna(saunas, mood)
            if recommended_sauna:
                st.write(f"あなたにオススメのサウナは: **{recommended_sauna['name']}**")
                st.write(f"住所: {recommended_sauna['vicinity']}")
                if 'rating' in recommended_sauna:
                    st.write(f"評価: {recommended_sauna['rating']}")

                    # Google Mapsで表示
                    st.map(pd.DataFrame({'lat': [lat], 'lon': [lng]}))

                # サウナの近くのラーメン屋を検索
                restaurants = get_restaurants_nearby(
                    recommended_sauna['geometry']['location']['lat'],
                    recommended_sauna['geometry']['location']['lng']
                )
                if restaurants:
                    st.write("近くのラーメン屋:")
                    for restaurant in restaurants[:5]:  # 上位5件を表示
                        st.write(f"**{restaurant['name']}**")
                        st.write(f"住所: {restaurant['vicinity']}")
                        if 'rating' in restaurant:
                            st.write(f"評価: {restaurant['rating']}")
                        st.write(f"[Google Mapsで表示](https://www.google.com/maps/search/?api=1&query={restaurant['geometry']['location']['lat']},{restaurant['geometry']['location']['lng']})")
                else:
                    st.write("近くのラーメン屋が見つかりませんでした。")
            else:
                st.write("ご指定の気分に合ったサウナが見つかりませんでした。")
        else:
            st.write("住所のジオコーディングに失敗しました。")
    else:
        st.write("住所と気分を入力してください。")
