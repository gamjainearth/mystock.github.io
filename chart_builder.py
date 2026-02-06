"""
차트 생성 모듈 - Plotly 기반
일봉/주봉 캔들 + 거래량 막대 + 이동평균선(30/60/120)
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 이동평균선 설정
MA_CONFIGS = [
    {"window": 30,  "color": "#FF6B35", "name": "30일선"},
    {"window": 60,  "color": "#1E88E5", "name": "60일선"},
    {"window": 120, "color": "#9C27B0", "name": "120일선"},
]


def resample_to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """일봉 데이터를 주봉으로 리샘플링"""
    if df.empty:
        return df
    weekly = df.resample("W").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum",
    }).dropna()
    return weekly


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """이동평균선 컬럼 추가"""
    for ma in MA_CONFIGS:
        col = f"MA{ma['window']}"
        df[col] = df["Close"].rolling(window=ma["window"], min_periods=1).mean()
    return df


def build_stock_chart(
    df: pd.DataFrame,
    title: str = "",
    chart_mode: str = "daily",
    show_volume: bool = True,
    show_ma: bool = True,
) -> go.Figure:
    """
    주가 차트 생성
    - chart_mode: "daily"(일봉) 또는 "weekly"(주봉)
    - 상단: 캔들차트 + 이동평균선
    - 하단: 거래량 막대차트
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="데이터가 없습니다",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray"),
        )
        fig.update_layout(height=400, template="plotly_white")
        return fig

    # 주봉 리샘플링
    plot_df = resample_to_weekly(df.copy()) if chart_mode == "weekly" else df.copy()
    if plot_df.empty:
        plot_df = df.copy()

    # 이동평균 계산
    if show_ma:
        plot_df = add_moving_averages(plot_df)

    has_volume = "Volume" in plot_df.columns and plot_df["Volume"].sum() > 0

    # 서브플롯 구성
    if show_volume and has_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.06,
            row_heights=[0.75, 0.25],
        )
    else:
        fig = make_subplots(rows=1, cols=1)

    # 캔들스틱 차트
    fig.add_trace(
        go.Candlestick(
            x=plot_df.index,
            open=plot_df["Open"],
            high=plot_df["High"],
            low=plot_df["Low"],
            close=plot_df["Close"],
            name="가격",
            increasing_line_color="#EF5350",   # 상승: 빨강 (한국식)
            decreasing_line_color="#1E88E5",   # 하락: 파랑 (한국식)
            increasing_fillcolor="#EF5350",
            decreasing_fillcolor="#1E88E5",
        ),
        row=1, col=1,
    )

    # 이동평균선
    if show_ma:
        for ma in MA_CONFIGS:
            col = f"MA{ma['window']}"
            if col in plot_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=plot_df.index,
                        y=plot_df[col],
                        mode="lines",
                        name=ma["name"],
                        line=dict(color=ma["color"], width=1.2),
                        hovertemplate=f"{ma['name']}: %{{y:,.0f}}<extra></extra>",
                    ),
                    row=1, col=1,
                )

    # 거래량 막대
    if show_volume and has_volume:
        vol_colors = []
        for i in range(len(plot_df)):
            if i == 0:
                vol_colors.append("#EF5350")
            elif plot_df["Close"].iloc[i] >= plot_df["Close"].iloc[i - 1]:
                vol_colors.append("#EF5350")
            else:
                vol_colors.append("#1E88E5")

        fig.add_trace(
            go.Bar(
                x=plot_df.index,
                y=plot_df["Volume"],
                name="거래량",
                marker_color=vol_colors,
                opacity=0.7,
                hovertemplate="%{x|%Y-%m-%d}<br>거래량: %{y:,.0f}<extra></extra>",
            ),
            row=2, col=1,
        )

    mode_label = "주봉" if chart_mode == "weekly" else "일봉"
    fig.update_layout(
        title=dict(text=f"{title} [{mode_label}]", font=dict(size=16)),
        height=580 if (show_volume and has_volume) else 420,
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
            font=dict(size=11),
        ),
        margin=dict(l=10, r=10, t=60, b=10),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="가격", row=1, col=1)
    if show_volume and has_volume:
        fig.update_yaxes(title_text="거래량", row=2, col=1)

    # 주말/공휴일 갭 제거
    fig.update_xaxes(type="category", row=1, col=1, nticks=10)
    if show_volume and has_volume:
        fig.update_xaxes(type="category", row=2, col=1, nticks=10)

    return fig
