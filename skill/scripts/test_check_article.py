"""Run with python3 scripts/test_check_article.py; no external dependencies."""

import subprocess
import sys
import tempfile
from pathlib import Path

from check_article import _r1_cold_start, _r2_promise


article = "# 实测 Foobar 提升 99%\n\n今天完成了整理。"
for prefix in ("", "\n", "\n\n", "文章说明\n\n"):
    assert _r1_cold_start(prefix + article) == _r1_cold_start(article)
    assert _r2_promise(prefix + article) == _r2_promise(article)
assert len(_r2_promise(article)) == 2
assert _r1_cold_start("# Foobar")
assert _r2_promise("# 实测提升 99%")
assert not _r2_promise("# 实测提升 99%\n\n运行日志：\n```text\n99%\n```")

script = Path(__file__).with_name("check_article.py")
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "article.md"
    samples = {
        "R1": "# Foobar\n\n今天完成了整理。",
        "R2": "# 节省 99%\n\n今天完成了整理。",
        "R3": "# 工作小记\n\n实测完成，测试结束。",
        "R4": "# 工作小记\n\n阈值设为 80，结果通过。",
        "R5": "# 工作小记\n\n这次整理结束以后，我把过程重新记录了一遍，希望读者可以理解这套整理过程的来龙去脉和整体经过。",
    }
    for rule, content in samples.items():
        path.write_text(content, encoding="utf-8")
        for strict in (False, True):
            result = subprocess.run(
                [sys.executable, str(script), str(path)] + (["--strict"] if strict else []),
                capture_output=True, text=True,
            )
            blocked = strict and rule != "R5"
            assert result.returncode == int(blocked), (rule, strict, result.stdout, result.stderr)
            assert ("[ERROR] " if blocked else "[WARN] ") + "[" + rule + "]" in result.stderr
print("PASS: title/body parsing and R1-R5 CLI exit codes")
