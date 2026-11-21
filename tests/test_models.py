import unittest
from datetime import date

from orders.codes import 주문상태
from orders.models import 주문, 품목


def 예시주문() -> 주문:
    return 주문(
        주문id="A-001",
        주문날짜=date(2026, 11, 21),
        품목목록=[품목("볼펜", 2, 1500), 품목("공책", 1, 3000)],
        상태=주문상태.결제,
    )


class 품목테스트(unittest.TestCase):
    def test_dict_왕복(self):
        p = 품목("볼펜", 2, 1500)
        self.assertEqual(p.to_dict(), {"상품명": "볼펜", "수량": 2, "단가": 1500})
        self.assertEqual(품목.from_dict(p.to_dict()), p)


class 주문테스트(unittest.TestCase):
    def test_dict_왕복(self):
        o = 예시주문()
        self.assertEqual(주문.from_dict(o.to_dict()), o)

    def test_to_dict_형식(self):
        d = 예시주문().to_dict()
        self.assertEqual(d["주문id"], "A-001")
        self.assertEqual(d["주문날짜"], "2026-11-21")
        self.assertEqual(d["상태"], "결제")
        self.assertIsInstance(d["상태"], str)
        self.assertEqual(len(d["품목목록"]), 2)

    def test_from_dict_변환(self):
        o = 주문.from_dict(예시주문().to_dict())
        self.assertIsInstance(o.주문날짜, date)
        self.assertIs(o.상태, 주문상태.결제)
        self.assertIsInstance(o.품목목록[0], 품목)

    def test_상태는_문자열로_넘겨도_공통_코드로_바뀐다(self):
        o = 주문("A-002", date(2026, 11, 21), [], "주문")
        self.assertIs(o.상태, 주문상태.주문)

    def test_상태는_반드시_넘긴다(self):
        with self.assertRaises(TypeError):
            주문("A-003", date(2026, 11, 21), [])  # type: ignore[call-arg]

    def test_알_수_없는_상태는_ValueError(self):
        d = 예시주문().to_dict()
        d["상태"] = "환불"
        with self.assertRaises(ValueError):
            주문.from_dict(d)

    def test_ISO가_아닌_날짜는_ValueError(self):
        d = 예시주문().to_dict()
        d["주문날짜"] = "2026/11/21"
        with self.assertRaises(ValueError):
            주문.from_dict(d)

    def test_금액은_수량_곱하기_단가의_합(self):
        self.assertEqual(예시주문().금액(), 2 * 1500 + 1 * 3000)

    def test_품목이_없으면_금액은_0(self):
        self.assertEqual(주문("A-004", date(2026, 11, 21), [], 주문상태.주문).금액(), 0)


if __name__ == "__main__":
    unittest.main()
