import unittest
from datetime import date

from orders import 주문, 주문상태, 품목
from orders.sales import daily_sales, format_daily_sales

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


if __name__ == "__main__":
    unittest.main()
