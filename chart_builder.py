"""
차트 생성 모듈 - Plotly 기반
종가 라인 + 거래량 막대 차트를 서브플롯으로 구성
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def build_stock_chart(
    df: pd.DataFrame,
    title: str = "",
    show_volume: bool = True,
) -> go.Figure:
    """
    주가 차트 생성
    - 상단: 종가 라인차트
    - 하단: 거래량 막대차트 (show_volume=True 시)
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="📊 데이터가 없습니다",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray"),
        )
        fig.update_layout(
            height=400,
            template="plotly_white",
        )
        return fig

    has_volume = "Volume" in df.columns and df["Volume"].sum() > 0

    if show_volume and has_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.7, 0.3],
            subplot_titles=("", "거래량"),
        )
    else:
        fig = make_subplots(rows=1, cols=1)

    # 종가 라인
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            name="종가",
            line=dict(color="#1f77b4", width=2),
            hovertemplate="%{x|%Y-%m-%d}<br>종가: %{y:,.0f}<extra></extra>",
        ),
        row=1, col=1,
    )

    # 거래량 막대
    if show_volume and has_volume:
        colors = []
        for i in range(len(df)):
            if i == 0:
                colors.append("#26a69a")
            elif df["Close"].iloc[i] >= df["Close"].iloc[i - 1]:
                colors.append("#26a69a")  # 상승: 녹색
            else:
                colors.append("#ef5350")  # 하락: 적색
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"],
                name="거래량",
                marker_color=colors,
                hovertemplate="%{x|%Y-%m-%d}<br>거래량: %{y:,.0f}<extra></extra>",
            ),
            row=2, col=1,
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=18)),
        height=500 if (show_volume and has_volume) else 380,
        template="plotly_white",
        showlegend=False,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_rangeslider_visible=False,
    )
    fig.update_yaxes(title_text="가격", row=1, col=1)
    if show_volume and has_volume:
        fig.update_yaxes(title_text="", row=2, col=1)

    return fig
