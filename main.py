import streamlit as st
import urllib.request
import json
import pandas as pd

st.set_page_config(page_title="MLB 선수 성적 검색기", page_icon="⚾", layout="centered")

st.title("⚾ MLB 선수 성적 검색기")
st.write("선수의 이름을 영문으로 입력하고 검색할 시즌을 선택하세요. (예: Ohtani, Judge, Trout)")

# 입력 폼
col_input1, col_input2 = st.columns([3, 1])
with col_input1:
    player_name = st.text_input("선수 이름 (영문):", value="Shohei Ohtani")
with col_input2:
    season = st.number_input("시즌:", min_value=1900, max_value=2026, value=2024)

search_button = st.button("성적 조회하기", use_container_width=True)

# 1. MLB Official API 호출 함수 (패키지 설치 불필요)
def search_mlb_player(name):
    encoded_name = urllib.parse.quote(name)
    url = f"https://statsapi.mlb.com/api/v1/people/search?names={encoded_name}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            people = data.get('people', [])
            return people[0] if people else None
    except Exception:
        return None

def get_player_stats(player_id, target_season):
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=statsSingleSeason&season={target_season}&group=hitting"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            stats_list = data.get('stats', [])
            if stats_list and stats_list[0].get('splits'):
                return stats_list[0]['splits'][0].get('stat', {})
            return {}
    except Exception:
        return {}

if search_button and player_name.strip():
    with st.spinner("선수 정보를 불러오는 중입니다..."):
        player_info = search_mlb_player(player_name)
        
        if not player_info:
            st.error(f"'{player_name}' 선수를 찾을 수 없습니다. 영문 철자를 확인해 주세요.")
        else:
            player_id = player_info.get('id')
            full_name = player_info.get('fullName')
            primary_position = player_info.get('primaryPosition', {}).get('abbreviation', 'N/A')
            
            # 선수 이미지 URL
            image_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:silo:current.png/w_400,q_auto:best/v1/people/{player_id}/headshot/silo/current"

            # 시즌 성적 조회
            stats = get_player_stats(player_id, season)

            hits = stats.get('hits', 0)
            home_runs = stats.get('homeRuns', 0)
            strike_outs = stats.get('strikeOuts', 0)
            base_on_balls = stats.get('baseOnBalls', 0)
            
            # OPS / 타율 정보 (MLB 기본 API에서 제공하는 주요 지표 추가)
            avg = stats.get('avg', '.---')
            ops = stats.get('ops', '.---')

            # 결과 화면 출력
            st.divider()
            col_img, col_info = st.columns([1, 2])
            with col_img:
                st.image(image_url, width=180)
            with col_info:
                st.subheader(full_name)
                st.write(f"**포지션:** {primary_position}")
                st.write(f"**시즌:** {season}년")

            st.write("---")
            st.markdown("### 📊 주요 타격 성적")

            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.metric(label="안타 (H)", value=f"{hits}개")
                st.metric(label="볼넷 (BB)", value=f"{base_on_balls}개")
            with m_col2:
                st.metric(label="홈런 (HR)", value=f"{home_runs}개")
                st.metric(label="삼진 (SO)", value=f"{strike_outs}개")
            with m_col3:
                st.metric(label="타율 (AVG)", value=str(avg))
                st.metric(label="OPS", value=str(ops))
