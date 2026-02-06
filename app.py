"""
myStock - 섹터별 종목 리스트 & 차트 확인 봇 (MVP)
Streamlit 기반 한국어 인터페이스
"""

import streamlit as st
import pandas as pd

from sector_manager import SectorManager
from data_provider import fetch_price_for_chart, fetch_info, format_market_cap
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
        placeholder="티커 또는 회사명 입력 (예: 엔비디아, TSLA)",
        help="한글 회사명, 영문명, 티커 모두 검색 가능",
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
            (f"{s['icon']} {s['name_ko']}" for s in sm.sectors if s["name_ko"] == name),
            name,
        ),
    )

# ──────────────────────────────────────
# 헬퍼: 종목 선택 UI + 차트 렌더
# ──────────────────────────────────────

def render_stock_table(stocks: list[dict], sector: dict | None = None, key_prefix: str = "tbl"):
    """종목 리스트를 테이블로 표시하고, selectbox 로 종목 선택"""
    if not stocks:
        return None

    # selectbox 로 종목 선택 (기본: 첫 번째)
    display_labels = [
        f"{s['ticker']}  {s['name_ko']}  {'🇰🇷' if s['market'] == 'KR' else '🇺🇸'}"
        for s in stocks
    ]
    selected_idx = st.selectbox(
        "종목 선택",
        options=range(len(stocks)),
        format_func=lambda i: display_labels[i],
        key=f"{key_prefix}_select",
    )
    selected = stocks[selected_idx]

    # 전체 종목 리스트 표
    with st.expander(f"📋 전체 종목 리스트 ({len(stocks)}개)", expanded=False):
        rows = []
        for s in stocks:
            rows.append({
                "티커": s["ticker"],
                "회사명": s["name_ko"],
                "시장": "🇰🇷 한국" if s["market"] == "KR" else "🇺🇸 미국",
                "설명": s["description"],
                "섹터": s.get("sector_name", sector["name_ko"] if sector else "-"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    return {
        **selected,
        "sector_name": selected.get("sector_name", sector["name_ko"] if sector else "-"),
        "sector_id": selected.get("sector_id", sector["id"] if sector else ""),
    }


def render_chart(stock: dict):
    """선택된 종목의 차트 + 지표를 렌더링"""
    st.subheader(f"📊 {stock['name_ko']} ({stock['ticker']})")
    market_label = "🇰🇷 한국" if stock["market"] == "KR" else "🇺🇸 미국"
    st.caption(f"섹터: {stock.get('sector_name', '-')} | 시장: {market_label}")

    # 옵션 행: 기간 / 일봉·주봉
    opt_cols = st.columns([2, 2, 6])
    period_options = {"1개월": "1mo", "3개월": "3mo", "1년": "1y"}
    selected_period_label = opt_cols[0].radio(
        "기간", list(period_options.keys()), horizontal=True, key="period_radio",
    )
    period = period_options[selected_period_label]

    chart_mode_map = {"일봉": "daily", "주봉": "weekly"}
    selected_mode_label = opt_cols[1].radio(
        "차트 유형", list(chart_mode_map.keys()), horizontal=True, key="mode_radio",
    )
    chart_mode = chart_mode_map[selected_mode_label]

    # 데이터 조회 (이평선용 확장 기간)
    with st.spinner("데이터를 불러오는 중..."):
        df = fetch_price_for_chart(stock["ticker"], stock["market"], period)

    if df.empty:
        st.error(
            f"⚠️ '{stock['ticker']}' 종목의 가격 데이터를 불러올 수 없습니다.\n"
            "티커가 올바른지 확인하거나, 잠시 후 다시 시도해 주세요."
        )
        return

    # 요약 지표 카드
    info = fetch_info(stock["ticker"], stock["market"])
    metric_cols = st.columns(4)

    current_price = info.get("currentPrice")
    if current_price:
        sym = "₩" if stock["market"] == "KR" else "$"
        metric_cols[0].metric("현재가", f"{sym}{current_price:,.0f}")

    mcap = info.get("marketCap")
    if mcap:
        metric_cols[1].metric("시가총액", format_market_cap(mcap, info.get("currency", "USD")))

    pe = info.get("peRatio")
    if pe:
        metric_cols[2].metric("PER", f"{pe:.1f}")

    if len(df) >= 2:
        change = ((df["Close"].iloc[-1] / df["Close"].iloc[0]) - 1) * 100
        metric_cols[3].metric("기간 수익률", f"{change:+.1f}%")

    # 차트 렌더링
    chart_title = f"{stock['name_ko']} ({stock['ticker']})"
    fig = build_stock_chart(df, title=chart_title, chart_mode=chart_mode)
    st.plotly_chart(fig, use_container_width=True)

    # 최근 데이터 테이블
    with st.expander("📋 최근 거래 데이터"):
        display_df = df.tail(10).copy()
        display_df.index = display_df.index.strftime("%Y-%m-%d")
        display_cols = ["Open", "High", "Low", "Close"]
        if "Volume" in display_df.columns:
            display_cols.append("Volume")
        col_names = {
            "Open": "시가", "High": "고가", "Low": "저가",
            "Close": "종가", "Volume": "거래량",
        }
        display_df = display_df[display_cols].rename(columns=col_names)
        st.dataframe(display_df, use_container_width=True)


# ──────────────────────────────────────
# 메인 영역
# ──────────────────────────────────────

if search_query and search_query.strip():
    # ── 검색 모드 ──
    results = sm.search(search_query)
    st.header(f"🔍 \"{search_query}\" 검색 결과")

    if not results:
        st.warning("검색 결과가 없습니다. 다른 키워드로 시도해 보세요.")
    else:
        st.info(f"총 {len(results)}개 종목을 찾았습니다.")
        selected = render_stock_table(results, key_prefix="search")
        if selected:
            st.divider()
            render_chart(selected)

else:
    # ── 섹터 탐색 모드 ──
    sector = sm.get_sector_by_name(selected_sector_name)
    if sector:
        st.header(f"{sector['icon']} {sector['name_ko']} 섹터")
        stocks = sector.get("stocks", [])

        selected = render_stock_table(stocks, sector=sector, key_prefix="sector")
        if selected:
            st.divider()
            render_chart(selected)

# ──────────────────────────────────────
# 푸터
# ──────────────────────────────────────
st.divider()
st.caption(
    "myStock MVP | 데이터: yfinance (미국) · pykrx (한국) | "
    "⚠️ 투자 참고용이며, 투자 판단의 책임은 본인에게 있습니다."
)
