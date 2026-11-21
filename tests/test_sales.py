import unittest
from datetime import date

from orders import 주문, 주문상태, 품목
from orders.sales import (
    _매출_제외_상태,
    _매출_포함_상태,
    daily_sales,
    format_daily_sales,
)

그날 = date(2026, 11, 21)
다른날 = date(2026, 11, 20)


def 만들기(주문id, 상태, 날짜=그날, 품목목록=None):
    if 품목목록 is None:
        품목목록 = [품목("볼펜", 2, 1500)]
    return 주문(주문id, 날짜, 품목목록, 상태)


class 합계테스트(unittest.TestCase):
    def test_결제_여러_건_합계(self):
        주문들 = [
            만들기("A-001", 주문상태.결제),  # 3000
            만들기("A-002", 주문상태.결제, 품목목록=[품목("공책", 1, 2000)]),  # 2000
        ]
        self.assertEqual(daily_sales(주문들, 그날), 5000)

    def test_취소와_주문_상태는_합계에_없다(self):
        주문들 = [
            만들기("A-001", 주문상태.결제),
            만들기("A-002", 주문상태.취소),
            만들기("A-003", 주문상태.주문),
        ]
        self.assertEqual(daily_sales(주문들, 그날), 3000)

    def test_다른_날짜_주문은_무시한다(self):
        주문들 = [
            만들기("A-001", 주문상태.결제),
            만들기("A-002", 주문상태.결제, 날짜=다른날),
        ]
        self.assertEqual(daily_sales(주문들, 그날), 3000)

    def test_주문이_없으면_0(self):
        self.assertEqual(daily_sales([], 그날), 0)
        self.assertEqual(
            daily_sales([만들기("A-001", 주문상태.결제, 날짜=다른날)], 그날), 0
        )

    def test_품목_없는_결제_주문은_0원(self):
        주문들 = [만들기("A-001", 주문상태.결제, 품목목록=[])]
        self.assertEqual(daily_sales(주문들, 그날), 0)

    def test_합계는_int(self):
        self.assertIsInstance(daily_sales([만들기("A-001", 주문상태.결제)], 그날), int)


class 표테스트(unittest.TestCase):
    def test_표_전체_문자열(self):
        주문들 = [
            만들기("A-001", 주문상태.결제),
            만들기("A-002", 주문상태.취소),
            만들기("A-1003", 주문상태.결제, 품목목록=[품목("공책", 1, 2000)]),
            만들기("B-001", 주문상태.결제, 날짜=다른날),
        ]
        기대 = "\n".join(
            [
                "일별 매출 2026-11-21",
                "주문id  상태     금액",
                "A-001   결제  3,000원",
                "A-1003  결제  2,000원",
                "합계          5,000원",
            ]
        )
        self.assertEqual(format_daily_sales(주문들, 그날), 기대)

    def test_빈_날은_제목_머리줄_합계_0원(self):
        기대 = "\n".join(
            [
                "일별 매출 2026-11-21",
                "주문id  상태  금액",
                "합계           0원",
            ]
        )
        self.assertEqual(format_daily_sales([], 그날), 기대)

    def test_합계줄이_daily_sales와_같다(self):
        주문들 = [
            만들기("A-001", 주문상태.결제),
            만들기("A-002", 주문상태.결제, 품목목록=[품목("공책", 3, 700)]),
        ]
        마지막줄 = format_daily_sales(주문들, 그날).splitlines()[-1]
        기대금액 = "{:,}원".format(daily_sales(주문들, 그날))
        self.assertEqual(마지막줄.split()[0], "합계")
        self.assertEqual(마지막줄.split()[-1], 기대금액)

    def test_천_단위_쉼표(self):
        주문들 = [만들기("A-001", 주문상태.결제, 품목목록=[품목("노트북", 1, 1234567)])]
        줄들 = format_daily_sales(주문들, 그날).splitlines()
        self.assertTrue(줄들[2].endswith("1,234,567원"))
        self.assertTrue(줄들[3].endswith("1,234,567원"))

    def test_한글_주문id도_폭을_두_칸으로_센다(self):
        주문들 = [만들기("가나", 주문상태.결제)]  # 폭 4
        줄들 = format_daily_sales(주문들, 그날).splitlines()
        # 머리 "주문id"(폭 6)가 가장 넓다. "가나"(폭 4) 뒤에 공백 2칸이 더 붙는다.
        self.assertEqual(줄들[1], "주문id  상태     금액")
        self.assertEqual(줄들[2], "가나    결제  3,000원")

    def test_품목_없는_결제_주문도_표에_행으로_나온다(self):
        주문들 = [만들기("A-001", 주문상태.결제, 품목목록=[])]
        줄들 = format_daily_sales(주문들, 그날).splitlines()
        self.assertEqual(줄들[2], "A-001   결제   0원")
        self.assertEqual(len(줄들), 4)

    def test_결제_전_주문_상태는_표에_없다(self):
        주문들 = [만들기("A-001", 주문상태.주문), 만들기("A-002", 주문상태.취소)]
        줄들 = format_daily_sales(주문들, 그날).splitlines()
        self.assertEqual(len(줄들), 3)  # 제목, 머리줄, 합계줄
        self.assertNotIn("A-001", "\n".join(줄들))
        self.assertNotIn("A-002", "\n".join(줄들))


def 부분취소한_주문(주문id, 날짜=그날):
    """결제 주문(볼펜 2,000원 + 공책 3,000원)에서 볼펜 줄을 실제로 부분취소한다.

    남은 금액 3,000원, 환불금액 2,000원, 원래 금액 5,000원.
    """
    o = 만들기(
        주문id,
        주문상태.결제,
        날짜=날짜,
        품목목록=[품목("볼펜", 1, 2000), 품목("공책", 1, 3000)],
    )
    o.부분취소([0])
    return o


class 부분취소합계테스트(unittest.TestCase):
    def test_부분취소한_주문은_남은_금액만_센다(self):
        o = 부분취소한_주문("A-001")
        self.assertEqual(o.금액(), 3000)
        self.assertEqual(o.환불금액, 2000)
        self.assertEqual(daily_sales([o], 그날), 3000)

    def test_결제와_부분취소가_섞인_날의_합계(self):
        # 결제 3,000원 + 부분취소(원래 5,000원, 환불 2,000원, 남은 3,000원) = 6,000원
        주문들 = [만들기("A-001", 주문상태.결제), 부분취소한_주문("A-002")]
        self.assertEqual(daily_sales(주문들, 그날), 6000)

    def test_환불분은_합계에_없다(self):
        o = 부분취소한_주문("A-001")
        원래금액 = o.금액() + o.환불금액
        self.assertEqual(원래금액, 5000)
        self.assertEqual(daily_sales([o], 그날), 원래금액 - o.환불금액)

    def test_전체_취소와_주문_상태는_여전히_제외한다(self):
        주문들 = [
            부분취소한_주문("A-001"),
            만들기("A-002", 주문상태.취소),
            만들기("A-003", 주문상태.주문),
        ]
        self.assertEqual(daily_sales(주문들, 그날), 3000)

    def test_다른_날_주문을_부분취소해도_그날_합계는_그대로다(self):
        # 부분취소한 날짜는 기록되지 않는다. 주문날짜(다른날)의 합계에만 반영된다.
        o = 부분취소한_주문("A-001", 날짜=다른날)
        self.assertEqual(daily_sales([o], 그날), 0)
        self.assertEqual(daily_sales([o], 다른날), 3000)

    def test_나중에_부분취소하면_이미_본_날짜의_합계가_줄어든다(self):
        o = 만들기(
            "A-001",
            주문상태.결제,
            품목목록=[품목("볼펜", 1, 2000), 품목("공책", 1, 3000)],
        )
        이전 = daily_sales([o], 그날)
        o.부분취소([0])
        이후 = daily_sales([o], 그날)
        self.assertEqual((이전, 이후), (5000, 3000))

    def test_모든_상태가_매출_포함_또는_제외로_분류된다(self):
        분류됨 = set(_매출_포함_상태) | set(_매출_제외_상태)
        self.assertEqual(분류됨, set(주문상태))
        self.assertEqual(set(_매출_포함_상태) & set(_매출_제외_상태), set())

    def test_합계는_int(self):
        self.assertIsInstance(daily_sales([부분취소한_주문("A-001")], 그날), int)


class 부분취소표테스트(unittest.TestCase):
    def test_부분취소_주문이_행으로_나온다(self):
        주문들 = [만들기("A-001", 주문상태.결제), 부분취소한_주문("A-002")]
        기대 = "\n".join(
            [
                "일별 매출 2026-11-21",
                "주문id  상태         금액",
                "A-001   결제      3,000원",
                "A-002   부분취소  3,000원",
                "합계              6,000원",
            ]
        )
        self.assertEqual(format_daily_sales(주문들, 그날), 기대)

    def test_부분취소_표의_합계줄이_daily_sales와_같다(self):
        주문들 = [만들기("A-001", 주문상태.결제), 부분취소한_주문("A-002")]
        마지막줄 = format_daily_sales(주문들, 그날).splitlines()[-1]
        self.assertEqual(마지막줄.split()[0], "합계")
        self.assertEqual(마지막줄.split()[-1], "{:,}원".format(daily_sales(주문들, 그날)))

    def test_전체_취소_주문은_표에_없다(self):
        주문들 = [부분취소한_주문("A-001"), 만들기("A-002", 주문상태.취소)]
        표 = format_daily_sales(주문들, 그날)
        self.assertIn("A-001", 표)
        self.assertNotIn("A-002", 표)

    def test_다른_날_부분취소_주문은_표에_없다(self):
        표 = format_daily_sales([부분취소한_주문("A-001", 날짜=다른날)], 그날)
        self.assertEqual(len(표.splitlines()), 3)  # 제목, 머리줄, 합계줄


if __name__ == "__main__":
    unittest.main()
