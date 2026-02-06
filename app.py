"""
myStock - 섹터별 종목 리스트 & 차트 확인 봇 (MVP)
Streamlit 기반 한국어 인터페이스
"""

import streamlit as st
import pandas as pd

from sector_manager import SectorManager
from data_provider import fetch_price, fetch_info, format_market_cap
from chart_builder import build_stock_chart

# ──────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────
st.set_page_config(
    page_title="myStock - 섹터별 종목 탐색",
    page_icon="📈",
    layout="wide",
)

# ──────────────────────────────────────
# 세션 상태 초기화
# ──────────────────────────────────────
if "sector_mgr" not in st.session_state:
    st.session_state.sector_mgr = SectorManager()
if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = None

sm: SectorManager = st.session_state.sector_mgr

# ──────────────────────────────────────
# 사이드바 - 검색 & 섹터 선택
# ──────────────────────────────────────
with st.sidebar:
    st.title("📈 myStock")
    st.caption("섹터별 종목 탐색 & 차트 확인")
    st.divider()

    # 검색
    search_query = st.text_input(
        "🔍 종목 검색",
        placeholder="티커 또는 회사명 입력",
        help="예: NVDA, 삼성전자, Tesla",
    )

    st.divider()

    # 섹터 목록
    st.subheader("섹터 선택")
    sector_names = sm.get_sector_names()
    selected_sector_name = st.radio(
        "섹터를 선택하세요",
        options=sector_names,
        label_visibility="collapsed",
        format_func=lambda name: next(
            (f"{s['icon']} {s['name_ko']}" for s in sm.sectors if s['name_ko'] == name),
            name,
        ),
    )

# ──────────────────────────────────────
# 메인 영역
# ──────────────────────────────────────

# ── 검색 결과 모드 ──
if search_query and search_query.strip():
    results = sm.search(search_query)
    st.header(f"🔍 \"{search_query}\" 검색 결과")

    if not results:
        st.warning("검색 결과가 없습니다. 다른 키워드로 시도해 보세요.")
    else:
        st.info(f"총 {len(results)}개 종목을 찾았습니다.")
        cols = st.columns([1, 2, 2, 1, 3])
        cols[0].markdown("**티커**")
        cols[1].markdown("**회사명**")
        cols[2].markdown("**섹터**")
        cols[3].markdown("**시장**")
        cols[4].markdown("**설명**")

        for stock in results:
            cols = st.columns([1, 2, 2, 1, 3])
            if cols[0].button(stock["ticker"], key=f"search_{stock['ticker']}_{stock['sector_id']}"):
                st.session_state.selected_stock = stock
            cols[1].write(stock["name_ko"])
            cols[2].write(stock["sector_name"])
            cols[3].write("🇰🇷" if stock["market"] == "KR" else "🇺🇸")
            cols[4].write(stock["description"])

# ── 섹터 상세 모드 ──
else:
    sector = sm.get_sector_by_name(selected_sector_name)
    if sector:
        st.header(f"{sector['icon']} {sector['name_ko']} 섹터")
        stocks = sector.get("stocks", [])

        # 종목 리스트 테이블
        st.subheader("📋 종목 리스트")

        cols_header = st.columns([1, 2, 1, 2, 3])
        cols_header[0].markdown("**티커**")
        cols_header[1].markdown("**회사명**")
        cols_header[2].markdown("**시장**")
        cols_header[3].markdown("**시총**")
        cols_header[4].markdown("**설명**")

        for stock in stocks:
            cols = st.columns([1, 2, 1, 2, 3])
            if cols[0].button(stock["ticker"], key=f"sector_{stock['ticker']}"):
                st.session_state.selected_stock = {
                    **stock,
                    "sector_name": sector["name_ko"],
                    "sector_id": sector["id"],
                }
            cols[1].write(stock["name_ko"])
            cols[2].write("🇰🇷" if stock["market"] == "KR" else "🇺🇸")

            # 시총 조회 (캐시 활용)
            info = fetch_info(stock["ticker"], stock["market"])
            mcap = format_market_cap(info.get("marketCap"), info.get("currency", "USD"))
            cols[3].write(mcap)
            cols[4].write(stock["description"])

# ──────────────────────────────────────
# 차트 영역 (종목 선택 시)
# ──────────────────────────────────────
st.divider()

selected = st.session_state.selected_stock

if selected:
    st.header(f"📊 {selected['name_ko']} ({selected['ticker']})")
    st.caption(f"섹터: {selected.get('sector_name', '-')} | 시장: {'🇰🇷 한국' if selected['market'] == 'KR' else '🇺🇸 미국'}")

    # 기간 선택
    period_options = {"1개월": "1mo", "3개월": "3mo", "1년": "1y"}
    selected_period_label = st.radio(
        "기간 선택",
        options=list(period_options.keys()),
        horizontal=True,
    )
    period = period_options[selected_period_label]

    # 데이터 조회
    with st.spinner("데이터를 불러오는 중..."):
        df = fetch_price(selected["ticker"], selected["market"], period)

    if df.empty:
        st.error(
            f"⚠️ '{selected['ticker']}' 종목의 가격 데이터를 불러올 수 없습니다.\n"
            "티커가 올바른지 확인하거나, 잠시 후 다시 시도해 주세요."
        )
    else:
        # 요약 지표
        info = fetch_info(selected["ticker"], selected["market"])
        metric_cols = st.columns(4)

        current_price = info.get("currentPrice")
        if current_price:
            currency_symbol = "₩" if selected["market"] == "KR" else "$"
            metric_cols[0].metric("현재가", f"{currency_symbol}{current_price:,.0f}")

        mcap = info.get("marketCap")
        if mcap:
            metric_cols[1].metric("시가총액", format_market_cap(mcap, info.get("currency", "USD")))

        pe = info.get("peRatio")
        if pe:
            metric_cols[2].metric("PER", f"{pe:.1f}")

        if len(df) >= 2:
            change = ((df["Close"].iloc[-1] / df["Close"].iloc[0]) - 1) * 100
            metric_cols[3].metric(
                f"{selected_period_label} 수익률",
                f"{change:+.1f}%",
            )

        # 차트 렌더링
        chart_title = f"{selected['name_ko']} ({selected['ticker']}) - {selected_period_label}"
        fig = build_stock_chart(df, title=chart_title)
        st.plotly_chart(fig, use_container_width=True)

        # 최근 데이터 테이블
        with st.expander("📋 최근 거래 데이터 보기"):
            display_df = df.tail(10).copy()
            display_df.index = display_df.index.strftime("%Y-%m-%d")
            display_cols = ["Open", "High", "Low", "Close"]
            if "Volume" in display_df.columns:
                display_cols.append("Volume")
            col_names = {"Open": "시가", "High": "고가", "Low": "저가", "Close": "종가", "Volume": "거래량"}
            display_df = display_df[display_cols].rename(columns=col_names)
            st.dataframe(display_df, use_container_width=True)
else:
    st.info("👆 왼쪽 사이드바에서 섹터를 선택하고, 티커 버튼을 클릭하면 차트를 확인할 수 있습니다.")

# ──────────────────────────────────────
# 푸터
# ──────────────────────────────────────
st.divider()
st.caption(
    "myStock MVP | 데이터 출처: yfinance (미국), pykrx (한국) | "
    "⚠️ 투자 참고용이며, 투자 판단의 책임은 본인에게 있습니다."
)
