import unittest
from datetime import date
from unittest import mock

from orders import notifications
from orders.codes import 주문상태
from orders.models import 주문, 품목
from orders.notifications import build_message


def 주문만들기(상태: 주문상태, 주문id: str = "A-001", 품목목록=None) -> 주문:
    if 품목목록 is None:
        품목목록 = [품목("볼펜", 2, 1500)]  # 합계 3,000원
    return 주문(주문id, date(2026, 11, 21), 품목목록, 상태)


class 알림문구테스트(unittest.TestCase):
    def test_주문_문구(self):
        self.assertEqual(
            build_message(주문만들기(주문상태.주문)),
            "주문번호 A-001 주문이 접수되었습니다. (3,000원)",
        )

    def test_결제_문구(self):
        self.assertEqual(
            build_message(주문만들기(주문상태.결제)),
            "주문번호 A-001 결제가 완료되었습니다. (3,000원)",
        )

    def test_취소_문구(self):
        self.assertEqual(
            build_message(주문만들기(주문상태.취소)),
            "주문번호 A-001 주문이 취소되었습니다. (3,000원)",
        )

    def test_주문id와_금액이_문구에_따라_바뀐다(self):
        o = 주문만들기(주문상태.결제, "B-777", [품목("공책", 3, 2000)])
        self.assertEqual(
            build_message(o), "주문번호 B-777 결제가 완료되었습니다. (6,000원)"
        )

    def test_천_단위_쉼표(self):
        o = 주문만들기(주문상태.결제, 품목목록=[품목("노트북", 1, 1234567)])
        self.assertIn("(1,234,567원)", build_message(o))

    def test_금액이_1000_미만이면_쉼표_없음(self):
        o = 주문만들기(주문상태.결제, 품목목록=[품목("사탕", 1, 500)])
        self.assertIn("(500원)", build_message(o))

    def test_품목이_없으면_0원(self):
        o = 주문만들기(주문상태.주문, 품목목록=[])
        self.assertIn("(0원)", build_message(o))

    def test_상태가_다르면_문구가_모두_다르다(self):
        문구들 = {build_message(주문만들기(s)) for s in 주문상태}
        self.assertEqual(len(문구들), len(list(주문상태)))

    def test_문구에_상태_표기가_섞이지_않는다(self):
        # str(주문상태.결제)는 Python 3.9에서 "주문상태.결제"가 된다. 문구에 들어가면 안 된다.
        for s in 주문상태:
            self.assertNotIn("주문상태.", build_message(주문만들기(s)))

    def test_주문상태_모든_멤버에_문구가_있다(self):
        # W1이 부분취소를 더하면 이 테스트가 실패해 문구 추가를 알린다.
        for s in 주문상태:
            self.assertIn(s, notifications.문구틀, "문구 없음: {}".format(s.value))

    def test_문구_없는_상태는_ValueError(self):
        with mock.patch.dict(notifications.문구틀):
            del notifications.문구틀[주문상태.결제]
            with self.assertRaises(ValueError):
                build_message(주문만들기(주문상태.결제))
        # patch.dict가 원래 표를 되돌린다.
        self.assertIn(주문상태.결제, notifications.문구틀)


if __name__ == "__main__":
    unittest.main()
