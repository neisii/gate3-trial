import copy
import os
import tempfile
import unittest
from datetime import date
from decimal import Decimal

from orders.codes import 주문상태
from orders.models import 주문, 품목
from orders.repository import 주문저장소


def 결제주문() -> 주문:
    return 주문(
        주문id="A-001",
        주문날짜=date(2026, 11, 21),
        품목목록=[품목("볼펜", 2, 1500), 품목("공책", 1, 3000), 품목("지우개", 3, 500)],
        상태=주문상태.결제,
    )


class 부분취소테스트(unittest.TestCase):
    def test_줄_하나를_취소한다(self):
        o = 결제주문()
        환불 = o.부분취소([1])
        self.assertEqual(환불, 3000)
        self.assertIs(o.상태, 주문상태.부분취소)
        self.assertEqual(o.품목목록, [품목("볼펜", 2, 1500), 품목("지우개", 3, 500)])
        self.assertEqual(o.취소품목목록, [품목("공책", 1, 3000)])
        self.assertEqual(o.환불금액, 3000)

    def test_여러_줄은_넘긴_순서와_상관없이_원래_순서를_지킨다(self):
        o = 결제주문()
        환불 = o.부분취소([2, 0])
        self.assertEqual(환불, 2 * 1500 + 3 * 500)
        self.assertEqual(o.품목목록, [품목("공책", 1, 3000)])
        self.assertEqual(o.취소품목목록, [품목("볼펜", 2, 1500), 품목("지우개", 3, 500)])
        self.assertEqual(o.환불금액, 환불)

    def test_돌려준_값은_환불금액과_같다(self):
        o = 결제주문()
        self.assertEqual(o.부분취소([0]), o.환불금액)

    def test_금액은_남은_품목의_합이고_환불금액을_더하면_원래_금액(self):
        o = 결제주문()
        원래금액 = o.금액()
        o.부분취소([0, 2])
        self.assertEqual(o.금액(), 3000)
        self.assertEqual(o.금액() + o.환불금액, 원래금액)

    def test_만든_뒤_상태에_문자열을_대입해도_결제로_본다(self):
        o = 결제주문()
        o.상태 = "결제"  # type: ignore[assignment]
        self.assertEqual(o.부분취소([0]), 3000)
        self.assertIs(o.상태, 주문상태.부분취소)

    def test_부분취소하지_않은_주문은_취소_기록이_비어_있다(self):
        o = 결제주문()
        self.assertEqual(o.취소품목목록, [])
        self.assertEqual(o.환불금액, 0)


class 부분취소거절테스트(unittest.TestCase):
    def assert_거절하고_그대로(self, o: 주문, 위치들):
        이전 = copy.deepcopy(o)
        with self.assertRaises(ValueError):
            o.부분취소(위치들)
        self.assertEqual(o, 이전)

    def test_결제가_아닌_상태는_거절한다(self):
        for 상태 in (주문상태.주문, 주문상태.취소, 주문상태.부분취소):
            with self.subTest(상태=상태.value):
                o = 결제주문()
                o.상태 = 상태
                self.assert_거절하고_그대로(o, [0])

    def test_부분취소한_주문은_다시_부분취소할_수_없다(self):
        o = 결제주문()
        o.부분취소([0])
        self.assert_거절하고_그대로(o, [0])

    def test_위치가_없으면_거절한다(self):
        self.assert_거절하고_그대로(결제주문(), [])

    def test_범위_밖_위치는_거절한다(self):
        for 위치들 in ([3], [0, 99], [-1]):
            with self.subTest(위치들=위치들):
                self.assert_거절하고_그대로(결제주문(), 위치들)

    def test_정수가_아닌_위치는_거절한다(self):
        for 위치들 in (
            [1.5], [0.5, 1.5], [1.0], [Decimal("1.5")], ["1"], [None], [0, 1.5], [True], [False], [0, True]
        ):
            with self.subTest(위치들=위치들):
                self.assert_거절하고_그대로(결제주문(), 위치들)

    def test_목록이_아닌_단일_값은_거절한다(self):
        for 위치들 in (1, 1.5, None):
            with self.subTest(위치들=위치들):
                self.assert_거절하고_그대로(결제주문(), 위치들)

    def test_dict로_넘기면_거절한다(self):
        for 위치들 in ({1: 5}, {0: 1}):
            with self.subTest(위치들=위치들):
                self.assert_거절하고_그대로(결제주문(), 위치들)

    def test_같은_위치가_두_번이면_거절한다(self):
        self.assert_거절하고_그대로(결제주문(), [1, 1])

    def test_모든_줄을_고르면_거절한다(self):
        self.assert_거절하고_그대로(결제주문(), [0, 1, 2])

    def test_품목이_하나뿐이면_부분취소할_수_없다(self):
        o = 주문("A-002", date(2026, 11, 21), [품목("볼펜", 1, 1500)], 주문상태.결제)
        self.assert_거절하고_그대로(o, [0])


class 부분취소저장테스트(unittest.TestCase):
    def test_dict_왕복(self):
        o = 결제주문()
        o.부분취소([1])
        self.assertEqual(주문.from_dict(o.to_dict()), o)

    def test_부분취소_주문의_to_dict_형식(self):
        o = 결제주문()
        o.부분취소([1])
        d = o.to_dict()
        self.assertEqual(d["상태"], "부분취소")
        self.assertEqual(d["취소품목목록"], [{"상품명": "공책", "수량": 1, "단가": 3000}])
        self.assertEqual(d["환불금액"], 3000)
        self.assertEqual(len(d["품목목록"]), 2)

    def test_환불이_0원인_취소도_취소_기록_키를_쓴다(self):
        o = 주문("A-003", date(2026, 11, 21), [품목("볼펜", 2, 1500), 품목("사은품", 1, 0)], 주문상태.결제)
        self.assertEqual(o.부분취소([1]), 0)
        d = o.to_dict()
        self.assertEqual(d["취소품목목록"], [{"상품명": "사은품", "수량": 1, "단가": 0}])
        self.assertEqual(d["환불금액"], 0)
        self.assertEqual(주문.from_dict(d), o)

    def test_환불금액만_있는_주문도_취소_기록_키를_쓴다(self):
        o = 주문("A-004", date(2026, 11, 21), [품목("볼펜", 2, 1500)], 주문상태.결제, [], 500)
        d = o.to_dict()
        self.assertEqual(d["취소품목목록"], [])
        self.assertEqual(d["환불금액"], 500)
        self.assertEqual(주문.from_dict(d), o)

    def test_이터레이터로_넘겨도_된다(self):
        o = 결제주문()
        self.assertEqual(o.부분취소(iter([0])), 3000)

    def test_취소_기록이_없는_주문은_키가_네_개뿐이다(self):
        d = 결제주문().to_dict()
        self.assertEqual(list(d.keys()), ["주문id", "주문날짜", "품목목록", "상태"])

    def test_새_키가_없는_예전_JSON도_불러온다(self):
        d = {
            "주문id": "A-001",
            "주문날짜": "2026-11-21",
            "품목목록": [{"상품명": "볼펜", "수량": 2, "단가": 1500}],
            "상태": "결제",
        }
        o = 주문.from_dict(d)
        self.assertEqual(o.취소품목목록, [])
        self.assertEqual(o.환불금액, 0)

    def test_저장소_왕복(self):
        o = 결제주문()
        o.부분취소([0])
        다른주문 = 결제주문()
        다른주문.주문id = "A-002"
        with tempfile.TemporaryDirectory() as 폴더:
            저장소 = 주문저장소(os.path.join(폴더, "orders.json"))
            저장소.저장([o, 다른주문])
            self.assertEqual(저장소.불러오기(), [o, 다른주문])


if __name__ == "__main__":
    unittest.main()
