"""상태별 고객 알림 문구.

상태마다 문구 틀 하나를 두고, 주문 id와 금액을 넣어 돌려준다.
상태 코드는 orders.codes.주문상태만 가져다 쓴다.
"""

from typing import Dict

from orders.codes import 주문상태
from orders.models import 주문

# 문구 틀. {주문id}와 {금액}이 들어간다. 금액은 천 단위 쉼표 + "원"으로 이미 만들어 넣는다.
문구틀: Dict[주문상태, str] = {
    주문상태.주문: "주문번호 {주문id} 주문이 접수되었습니다. ({금액})",
    주문상태.결제: "주문번호 {주문id} 결제가 완료되었습니다. ({금액})",
    주문상태.취소: "주문번호 {주문id} 주문이 취소되었습니다. ({금액})",
}


def build_message(대상주문: 주문) -> str:
    """대상주문의 현재 상태에 맞는 알림 문구를 만든다.

    문구 틀이 없는 상태이면 ValueError. 알 수 없는 상태를 조용히 넘기지 않는다.
    """
    틀 = 문구틀.get(대상주문.상태)
    if 틀 is None:
        raise ValueError(
            "알림 문구가 없는 상태입니다: {}".format(대상주문.상태.value)
        )
    return 틀.format(주문id=대상주문.주문id, 금액="{:,}원".format(대상주문.금액()))
