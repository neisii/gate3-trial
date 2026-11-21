"""주문과 품목."""

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List

from orders.codes import 주문상태


@dataclass
class 품목:
    상품명: str
    수량: int
    단가: int  # 원 단위 정수

    def to_dict(self) -> Dict[str, Any]:
        return {"상품명": self.상품명, "수량": self.수량, "단가": self.단가}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "품목":
        return cls(상품명=d["상품명"], 수량=d["수량"], 단가=d["단가"])


@dataclass
class 주문:
    주문id: str
    주문날짜: date
    품목목록: List[품목]
    상태: 주문상태  # 기본값 없음. 만들 때 반드시 넘긴다.

    def __post_init__(self) -> None:
        # 문자열로 받아도 공통 코드로 바꾼다. 공통 코드 밖의 값이면 ValueError.
        self.상태 = 주문상태(self.상태)

    def 금액(self) -> int:
        """품목별 수량×단가의 합(원)."""
        return sum(p.수량 * p.단가 for p in self.품목목록)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "주문id": self.주문id,
            "주문날짜": self.주문날짜.isoformat(),
            "품목목록": [p.to_dict() for p in self.품목목록],
            "상태": self.상태.value,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "주문":
        return cls(
            주문id=d["주문id"],
            주문날짜=date.fromisoformat(d["주문날짜"]),
            품목목록=[품목.from_dict(p) for p in d["품목목록"]],
            상태=주문상태(d["상태"]),
        )
