# 📈 myStock - 섹터별 종목 탐색 & 차트 확인 봇

섹터별 종목 리스트 조회와 주가 차트를 확인할 수 있는 한국어 인터페이스 웹 앱(MVP)입니다.

## 주요 기능

- **섹터 목록 보기**: 반도체, AI, 에너지, 로봇, 금융, 2차전지 등
- **종목 리스트**: 섹터별 종목의 티커, 회사명, 시총, 설명 확인
- **차트 보기**: 1개월/3개월/1년 기간별 종가 라인 + 거래량 막대 차트
- **종목 검색**: 티커 또는 회사명(한/영)으로 검색
- **미국/한국 주식 지원**: yfinance(미국), pykrx(한국)

## 실행 방법

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 로 접속합니다.

## 파일 구조

```
mystock.github.io/
├── app.py              # Streamlit 메인 앱 (UI)
├── data_provider.py    # 데이터 조회 모듈 (yfinance/pykrx + 캐시)
├── sector_manager.py   # 섹터/종목 매핑 관리
├── chart_builder.py    # Plotly 차트 생성
├── sectors.json        # 섹터/종목 설정 데이터
├── requirements.txt    # Python 의존성
└── .gitignore
```

## 섹터/종목 편집

`sectors.json` 파일을 수정하여 섹터와 종목을 추가/변경할 수 있습니다.

## 데이터 출처

- 미국 주식: [yfinance](https://github.com/ranaroussi/yfinance)
- 한국 주식: [pykrx](https://github.com/sharebook-kr/pykrx)

> ⚠️ 투자 참고용이며, 투자 판단의 책임은 본인에게 있습니다.
