"""주문 저장소: JSON 파일 하나에 저장하고 불러온다."""

import json
import os
import stat
import uuid
from typing import List

from orders.models import 주문


class 주문저장소:
    def __init__(self, 경로: str) -> None:
        self.경로 = 경로

    def 저장(self, 주문들: List[주문]) -> None:
        """주문 목록 전체를 파일에 쓴다.

        같은 폴더의 임시 파일에 먼저 쓰고 os.replace로 바꿔 넣는다.
        쓰다가 멈춰도 기존 파일은 깨지지 않는다.
        파일 권한: 기존 파일이 있으면 그 권한을 유지하고,
        없으면 일반 파일 생성과 같이 0o666에 umask를 적용한 권한이 된다.
        """
        데이터 = [o.to_dict() for o in 주문들]
        절대경로 = os.path.abspath(self.경로)
        폴더 = os.path.dirname(절대경로)
        임시경로 = os.path.join(
            폴더, ".{}.{}.tmp".format(os.path.basename(절대경로), uuid.uuid4().hex)
        )
        # 0o666으로 만들면 umask가 적용된다(tempfile.mkstemp는 0o600으로 고정).
        fd = os.open(임시경로, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(데이터, f, ensure_ascii=False, indent=2)
                f.write("\n")
            if os.path.exists(절대경로):
                os.chmod(임시경로, stat.S_IMODE(os.stat(절대경로).st_mode))
            os.replace(임시경로, 절대경로)
        except BaseException:
            if os.path.exists(임시경로):
                os.unlink(임시경로)
            raise

    def 불러오기(self) -> List[주문]:
        """파일 전체를 읽어 주문 목록으로 돌려준다. 파일이 없으면 빈 목록."""
        if not os.path.exists(self.경로):
            return []
        with open(self.경로, encoding="utf-8") as f:
            데이터 = json.load(f)
        return [주문.from_dict(d) for d in 데이터]
