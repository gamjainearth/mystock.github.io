"""
섹터 매핑 관리 모듈
sectors.json을 읽어 섹터/종목 데이터를 제공
추후 자동 분류 확장을 위해 SectorProvider 인터페이스 분리 가능
"""

import json
from pathlib import Path
from typing import Optional

SECTORS_FILE = Path(__file__).parent / "sectors.json"


class SectorManager:
    def __init__(self, path: Optional[str] = None):
        self._path = Path(path) if path else SECTORS_FILE
        self._data = self._load()

    def _load(self) -> dict:
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def reload(self):
        """설정 파일 재로드"""
        self._data = self._load()

    @property
    def sectors(self) -> list[dict]:
        return self._data.get("sectors", [])

    def get_sector_names(self) -> list[str]:
        """섹터 한국어 이름 목록"""
        return [s["name_ko"] for s in self.sectors]

    def get_sector_by_name(self, name_ko: str) -> Optional[dict]:
        """한국어 이름으로 섹터 검색"""
        for s in self.sectors:
            if s["name_ko"] == name_ko:
                return s
        return None

    def get_sector_by_id(self, sector_id: str) -> Optional[dict]:
        for s in self.sectors:
            if s["id"] == sector_id:
                return s
        return None

    def get_stocks(self, sector_id: str) -> list[dict]:
        """특정 섹터의 종목 리스트"""
        sector = self.get_sector_by_id(sector_id)
        if not sector:
            return []
        return sector.get("stocks", [])

    def search(self, query: str) -> list[dict]:
        """티커 또는 회사명으로 검색 (한국어/영어 모두)"""
        query = query.strip().upper()
        if not query:
            return []
        results = []
        for sector in self.sectors:
            for stock in sector.get("stocks", []):
                ticker_match = query in stock["ticker"].upper()
                name_ko_match = query.lower() in stock["name_ko"].lower()
                name_en_match = query.lower() in stock["name_en"].lower()
                if ticker_match or name_ko_match or name_en_match:
                    results.append({
                        **stock,
                        "sector_name": sector["name_ko"],
                        "sector_id": sector["id"],
                    })
        return results

    def get_all_stocks(self) -> list[dict]:
        """전체 종목 리스트 (섹터 정보 포함)"""
        all_stocks = []
        for sector in self.sectors:
            for stock in sector.get("stocks", []):
                all_stocks.append({
                    **stock,
                    "sector_name": sector["name_ko"],
                    "sector_id": sector["id"],
                })
        return all_stocks
