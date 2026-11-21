import unittest

from orders.codes import 주문상태


class 주문상태테스트(unittest.TestCase):
    def test_멤버는_주문_결제_취소_세_개(self):
        self.assertEqual([s.name for s in 주문상태], ["주문", "결제", "취소"])

    def test_값은_멤버_이름과_같은_문자열(self):
        for s in 주문상태:
            self.assertEqual(s.value, s.name)
            self.assertEqual(s, s.name)  # str을 섞어 문자열과 비교된다

    def test_문자열로_다시_찾는다(self):
        self.assertIs(주문상태("결제"), 주문상태.결제)

    def test_공통_코드_밖의_값은_ValueError(self):
        with self.assertRaises(ValueError):
            주문상태("환불")


if __name__ == "__main__":
    unittest.main()
