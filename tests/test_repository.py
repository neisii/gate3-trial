import json
import os
import stat
import tempfile
import unittest
from datetime import date
from unittest import mock

from orders.codes import 주문상태
from orders.models import 주문, 품목
from orders.repository import 주문저장소


def 주문들():
    return [
        주문("A-001", date(2026, 11, 21), [품목("볼펜", 2, 1500)], 주문상태.결제),
        주문("A-002", date(2026, 11, 22), [품목("공책", 1, 3000), 품목("지우개", 3, 500)], 주문상태.주문),
    ]


class 주문저장소테스트(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.경로 = os.path.join(self._tmp.name, "orders.json")
        self.저장소 = 주문저장소(self.경로)

    def tearDown(self):
        self._tmp.cleanup()

    def test_저장_후_불러오기_왕복(self):
        원본 = 주문들()
        self.저장소.저장(원본)
        self.assertEqual(self.저장소.불러오기(), 원본)

    def test_파일이_없으면_빈_목록(self):
        self.assertFalse(os.path.exists(self.경로))
        self.assertEqual(self.저장소.불러오기(), [])

    def test_빈_목록_저장(self):
        self.저장소.저장([])
        with open(self.경로, encoding="utf-8") as f:
            self.assertEqual(json.load(f), [])
        self.assertEqual(self.저장소.불러오기(), [])

    def test_한글을_그대로_저장한다(self):
        self.저장소.저장(주문들())
        with open(self.경로, encoding="utf-8") as f:
            내용 = f.read()
        self.assertIn("볼펜", 내용)
        self.assertIn('"상태": "결제"', 내용)
        self.assertNotIn("\\u", 내용)

    def test_덮어쓰면_이전_내용이_남지_않는다(self):
        self.저장소.저장(주문들())
        새것 = [주문("B-001", date(2026, 12, 1), [], 주문상태.취소)]
        self.저장소.저장(새것)
        self.assertEqual(self.저장소.불러오기(), 새것)

    def test_저장_뒤_임시_파일이_남지_않는다(self):
        self.저장소.저장(주문들())
        self.assertEqual(os.listdir(self._tmp.name), ["orders.json"])

    def test_저장_중_예외가_나면_임시_파일을_지우고_기존_파일을_유지한다(self):
        원본 = 주문들()
        self.저장소.저장(원본)
        with mock.patch("orders.repository.json.dump", side_effect=RuntimeError("쓰기 실패")):
            with self.assertRaises(RuntimeError):
                self.저장소.저장([])
        self.assertEqual(os.listdir(self._tmp.name), ["orders.json"])
        self.assertEqual(self.저장소.불러오기(), 원본)


@unittest.skipUnless(os.name == "posix", "파일 권한 비트는 POSIX에서만 확인한다")
class 주문저장소권한테스트(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.경로 = os.path.join(self._tmp.name, "orders.json")
        self.저장소 = 주문저장소(self.경로)
        self._이전_umask = os.umask(0o022)

    def tearDown(self):
        os.umask(self._이전_umask)
        self._tmp.cleanup()

    def 권한(self):
        return stat.S_IMODE(os.stat(self.경로).st_mode)

    def test_새_파일은_umask_기준_권한(self):
        self.저장소.저장(주문들())
        self.assertEqual(self.권한(), 0o644)

    def test_새_파일은_다른_umask도_따른다(self):
        os.umask(0o077)
        self.저장소.저장(주문들())
        self.assertEqual(self.권한(), 0o600)

    def test_기존_파일의_권한을_유지한다(self):
        for 기존권한 in (0o644, 0o640, 0o600):
            with self.subTest(기존권한=oct(기존권한)):
                with open(self.경로, "w", encoding="utf-8") as f:
                    f.write("[]\n")
                os.chmod(self.경로, 기존권한)
                self.저장소.저장(주문들())
                self.assertEqual(self.권한(), 기존권한)


if __name__ == "__main__":
    unittest.main()
