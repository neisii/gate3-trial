"""주문과 품목."""

import operator
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Mapping

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
    # 부분취소 기록. 부분취소하지 않은 주문은 빈 목록·0이다.
    취소품목목록: List[품목] = field(default_factory=list)
    환불금액: int = 0  # 원 단위 정수

    def __post_init__(self) -> None:
        # 문자열로 받아도 공통 코드로 바꾼다. 공통 코드 밖의 값이면 ValueError.
        self.상태 = 주문상태(self.상태)

    def 금액(self) -> int:
        """품목별 수량×단가의 합(원). 부분취소한 주문은 남은 품목의 합이다."""
        return sum(p.수량 * p.단가 for p in self.품목목록)

    def 부분취소(self, 위치들: List[int]) -> int:
        """결제된 주문에서 품목 줄 일부를 취소하고 이번 환불 금액(원)을 돌려준다.

        위치들: 취소할 줄의 품목목록 안 위치(0부터). 순서는 상관없다.
        취소한 줄은 품목목록에서 빠져 취소품목목록으로 옮겨지고(원래 순서 유지),
        환불금액은 그 줄들의 수량×단가 합, 상태는 부분취소가 된다.

        다음 경우는 ValueError로 거절하고 주문을 바꾸지 않는다:
        위치들이 dict이거나 목록이 아님(예: 1, None), 상태가 결제가 아님, 위치가 없음, 정수가 아닌 위치(1.5·1.0·"1"·True·False 등),
        범위 밖·음수 위치, 같은 위치 중복, 모든 줄을 고름(전체 취소는 부분취소가 아니다).
        """
        # dict는 키만 위치로 읽혀 줄 전체가 취소되므로(예: {1: 5}) 잘못된 요청으로 거절한다.
        if isinstance(위치들, Mapping):
            raise ValueError("품목 위치는 dict가 아니라 위치 목록으로 넘긴다")
        try:
            위치목록 = list(위치들)
        except TypeError:
            # 목록이 아닌 단일 값(예: 1, None)도 잘못된 요청으로 거절한다.
            raise ValueError("품목 위치는 목록으로 넘긴다: {!r}".format(위치들)) from None
        # 만든 뒤 상태에 문자열을 대입했어도 공통 코드로 바꿔 비교한다.
        현재상태 = 주문상태(self.상태)
        if 현재상태 is not 주문상태.결제:
            raise ValueError(
                "결제된 주문만 부분취소할 수 있다(현재 상태: {})".format(현재상태.value)
            )
        if not 위치목록:
            raise ValueError("취소할 품목 위치가 없다")
        # 위치는 정수만 받는다. 1.5·1.0·"1"과 bool(True·False)은 잘못된 요청으로 거절한다.
        정수위치목록 = []
        for 위치 in 위치목록:
            if isinstance(위치, bool):
                raise ValueError("품목 위치는 정수여야 한다: {!r}".format(위치))
            try:
                정수위치목록.append(operator.index(위치))
            except TypeError:
                raise ValueError("품목 위치는 정수여야 한다: {!r}".format(위치)) from None
        위치목록 = 정수위치목록
        for 위치 in 위치목록:
            if not 0 <= 위치 < len(self.품목목록):
                raise ValueError("품목 위치가 범위 밖이다: {}".format(위치))
        취소위치 = set(위치목록)
        if len(취소위치) != len(위치목록):
            raise ValueError("같은 품목 위치가 두 번 들어 있다")
        if len(취소위치) == len(self.품목목록):
            raise ValueError("모든 품목을 취소하는 것은 부분취소가 아니다")

        취소품목 = [p for i, p in enumerate(self.품목목록) if i in 취소위치]
        남은품목 = [p for i, p in enumerate(self.품목목록) if i not in 취소위치]
        환불 = sum(p.수량 * p.단가 for p in 취소품목)

        self.품목목록 = 남은품목
        self.취소품목목록 = 취소품목
        self.환불금액 = 환불
        self.상태 = 주문상태.부분취소
        return 환불

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "주문id": self.주문id,
            "주문날짜": self.주문날짜.isoformat(),
            "품목목록": [p.to_dict() for p in self.품목목록],
            "상태": self.상태.value,
        }
        # 취소 기록이 있을 때만 키를 쓴다. 부분취소가 없는 주문의 형식은 그대로다.
        if self.취소품목목록 or self.환불금액 != 0:
            d["취소품목목록"] = [p.to_dict() for p in self.취소품목목록]
            d["환불금액"] = self.환불금액
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "주문":
        return cls(
            주문id=d["주문id"],
            주문날짜=date.fromisoformat(d["주문날짜"]),
            품목목록=[품목.from_dict(p) for p in d["품목목록"]],
            상태=주문상태(d["상태"]),
            취소품목목록=[품목.from_dict(p) for p in d.get("취소품목목록", [])],
            환불금액=d.get("환불금액", 0),
        )
