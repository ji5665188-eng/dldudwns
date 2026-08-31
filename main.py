import streamlit as st
import statsapi
from pybaseball import batting_stats
import pandas as pd

# Page Configuration
st.set_page_config(page_title="MLB 선수 성적 검색기", page_icon="⚾", layout="centered")

st.title("⚾ MLB 선수 성적 검색기")
st.write("선수의 이름을 영문으로 입력하고 검색할 시즌을 선택하세요. (예: Ohtani, Judge, Trout)")

# 입력 폼 설정
col_input1, col_input2 = st.columns([3, 1])
with col_input1:
    player_name = st.text_input("선수 이름 (영문):", value="Shohei Ohtani")
with col_input2:
    season = st.number_input("시즌:", min_value=1900, max_value=2026, value=2024)

search_button = st.button("성적 조회하기", use_container_width=True)

# FanGraphs 데이터 캐싱 함수
@st.cache_data(ttl=3600, show_spinner=False)
def get_fan_graphs_data(target_season):
    try:
        df = batting_stats(target_season, qual=1)
        return df
    except Exception:
        return None

if search_button and player_name.strip():
    with st.spinner("선수 정보를 불러오는 중입니다..."):
        try:
            # 1. MLB Official StatsAPI 선수 검색
            lookup_results = statsapi.lookup_player(player_name)
            
            if not lookup_results:
                st.error(f"'{player_name}' 선수를 찾을 수 없습니다. 영문 철자를 확인해 주세요.")
            else:
                player = lookup_results[0]
                player_id = player['id']
                full_name = player['fullName']
                primary_position = player.get('primaryPosition', {}).get('abbreviation', 'N/A')
                
                # 선수 이미지 URL 생성
                image_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:silo:current.png/w_400,q_auto:best/v1/people/{player_id}/headshot/silo/current"

                # 2. MLB StatsAPI 기본 성적 추출 (안타, 홈런, 삼진, 볼넷)
                stats = statsapi.player_stat_data(player_id, type='hitting', group='hitting', season=season)
                stat_dict = {}
                if stats.get('stats'):
                    stat_dict = stats['stats'][0].get('stats', {})

                hits = stat_dict.get('hits', 0)
                home_runs = stat_dict.get('homeRuns', 0)
                strike_outs = stat_dict.get('strikeOuts', 0)
                base_on_balls = stat_dict.get('baseOnBalls', 0)

                # 3. FanGraphs 기반 wRC+ 추출
                wrc_plus = "N/A"
                fg_df = get_fan_graphs_data(season)
                
                if fg_df is not None and not fg_df.empty:
                    matched = fg_df[fg_df['Name'].str.lower() == full_name.lower()]
                    if matched.empty:
                        matched = fg_df[fg_df['Name'].str.contains(player_name, case=False, na=False)]
                    
                    if not matched.empty and 'wRC+' in matched.columns:
                        raw_wrc = matched.iloc[0]['wRC+']
                        if pd.notna(raw_wrc):
                            wrc_plus = round(float(raw_wrc), 1)

                # 4. 결과 출력
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
                    st.metric(label="wRC+", value=str(wrc_plus))

        except Exception as err:
            st.error("데이터를 처리하는 중 오류가 발생했습니다.")
            st.caption(f"상세 에러 원인: {err}")
