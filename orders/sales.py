"""일별 매출 집계.

결제·부분취소 상태인 주문을 매출로 센다. 부분취소 주문은 남은 품목의 금액
(주문.금액())만 센다. 환불된 분은 매출에서 빠진다.
취소·주문 상태는 합계에 넣지 않는다.
날짜는 주문날짜 기준이다. 부분취소한 날짜는 주문에 없으므로, 나중에 부분취소하면
이미 집계한 주문날짜의 합계가 줄어들 수 있다.
"""

import unicodedata
from datetime import date
from typing import List

from orders.codes import 주문상태
from orders.models import 주문


# 주문상태의 모든 멤버는 둘 중 한 곳에 있어야 한다(테스트가 확인한다).
# 새 상태가 생기면 어느 쪽인지 정해야 하고, 정하지 않으면 테스트가 실패한다.
_매출_포함_상태 = (주문상태.결제, 주문상태.부분취소)
_매출_제외_상태 = (주문상태.주문, 주문상태.취소)


def _그날_매출_주문(주문들: List[주문], 날짜: date) -> List[주문]:
    return [
        o for o in 주문들 if o.주문날짜 == 날짜 and o.상태 in _매출_포함_상태
    ]


def daily_sales(주문들: List[주문], 날짜: date) -> int:
    """날짜 하루의 매출 합계(원). 그날 결제·부분취소 주문의 금액을 더한다."""
    return sum(o.금액() for o in _그날_매출_주문(주문들, 날짜))


def _폭(글: str) -> int:
    """터미널 표시 폭. 한글 등 넓은 글자는 두 칸으로 센다."""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in 글)


def _왼쪽맞춤(글: str, 폭: int) -> str:
    return 글 + " " * (폭 - _폭(글))


def _오른쪽맞춤(글: str, 폭: int) -> str:
    return " " * (폭 - _폭(글)) + 글


def _금액표기(금액: int) -> str:
    """천 단위 쉼표와 '원'을 붙인다. 예: 3000 -> '3,000원', 0 -> '0원'."""
    return "{:,}원".format(금액)


def format_daily_sales(주문들: List[주문], 날짜: date) -> str:
    """일별 매출을 표 형태 텍스트로 만든다.

    제목, 머리줄(주문id·상태·금액), 그날 결제·부분취소 주문(입력 순서), 합계 줄.
    """
    매출주문 = _그날_매출_주문(주문들, 날짜)
    합계 = sum(o.금액() for o in 매출주문)

    머리 = ("주문id", "상태", "금액")
    행들 = [(o.주문id, o.상태.value, _금액표기(o.금액())) for o in 매출주문]
    합계줄 = ("합계", "", _금액표기(합계))

    폭들 = [
        max(_폭(줄[i]) for 줄 in [머리] + 행들 + [합계줄]) for i in range(3)
    ]

    def 한줄(줄) -> str:
        return (
            _왼쪽맞춤(줄[0], 폭들[0])
            + "  "
            + _왼쪽맞춤(줄[1], 폭들[1])
            + "  "
            + _오른쪽맞춤(줄[2], 폭들[2])
        ).rstrip()

    줄들 = ["일별 매출 {}".format(날짜.isoformat()), 한줄(머리)]
    줄들.extend(한줄(r) for r in 행들)
    줄들.append(한줄(합계줄))
    return "\n".join(줄들)
