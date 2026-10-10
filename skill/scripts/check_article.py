#!/usr/bin/env python3
# check_article.py -- Markdown structure, style sanity, and reader-payoff checks

import re
import sys
from pathlib import Path

# style-guide.md § 禁用表达清单 — AI 腔套话 + 书面词汇 + 空洞表达 + 夸张美学 + 模糊归因 + 助手感开场白
BANNED_EXPRESSIONS = [
    # AI 腔套话
    "在当今时代", "综上所述", "总的来说", "归根结底",
    "值得注意的是", "不难发现", "显而易见", "毋庸置疑", "毫无疑问", "可以说",
    "有助于", "使得", "从而实现",
    "首先…其次", "其次…最后",
    # 书面词汇
    "显著提升", "充分利用", "进行操作", "获取结果", "实现功能", "相关方案",
    # 空洞表达
    "具有显著优势", "效果非常好", "值得推荐使用",
    # 夸张美学
    "充满活力", "蓬勃发展", "里程碑", "革命性", "重塑",
    # 模糊归因
    "专家认为", "研究表明", "据统计", "众所周知",
    # 助手感开场白
    "当然可以", "很高兴为您", "没问题", "作为一名AI",
    # 原有条目保留
    "不得不说", "总结一下", "本文将", "笔者认为", "由此可见", "因此，我们",
]

REVIEW_REPORT_MARKERS = ["【审校报告】", "【第一遍】", "【第二遍】", "【第三遍】", "【第四遍】"]

CHATBOT_ARTIFACTS = [
    "希望这对你有帮助", "如果你需要我可以继续", "以下是", "当然可以",
]

GENERIC_FUTURE_CLOSERS = [
    "未来可期", "让我们拭目以待", "拭目以待", "只有时间会给出答案", "未来值得期待",
]

PROMO_INFLATION = [
    "史诗级", "全网最强", "革命性", "颠覆式", "重新定义", "极致体验", "不容错过",
]

FALSE_DEPTH_PATTERNS = [
    re.compile(r'不是[^。！？\n]{1,40}而是[^。！？\n]{1,60}'),
    re.compile(r'与其说[^。！？\n]{1,40}不如说[^。！？\n]{1,60}'),
    re.compile(r'重要的不是[^。！？\n]{1,40}而是[^。！？\n]{1,60}'),
]

SHORT_SENTENCE_BURST = re.compile(r'(?:[^。！？\n]{2,8}[。！？]){4,}')


# ---------------------------------------------------------------------------
# reader-payoff.md § R1-R5 — 读者兑现门禁
# ---------------------------------------------------------------------------

# R1 标题核心术语：ASCII 词（长度 >= 2）+ 书名号/引号/方括号内的中文短语
R1_ASCII_TERM = re.compile(r'[A-Za-z][A-Za-z0-9\.\-_]{1,}')
R1_QUOTED_TERM = re.compile(r'[《「【"“]([^》」】"”\n]{2,20})[》」】"”]')
# 本号读者已具备的环境词汇与通用文章词：要求开篇定义它们没有信息量（统一大写存储）
R1_TERM_STOPLIST = {
    "AI", "API", "CLI", "GPT", "LLM", "MCP", "RAG", "AGI", "SDK", "UI", "OS", "PC",
    "OK", "THE", "AND", "FOR", "APP", "CODE", "DATA", "TOOL", "GUIDE", "INTRO",
    "NOTES", "PART", "UPDATE", "RELEASE", "REVIEW", "STEP", "CASE", "FILE", "WEB",
    "DEEP", "DEMO", "CHAT", "NEW", "使用",
}

# R1 定义信号：术语首次出现附近出现这些词，说明作者在解释「它是什么」
# 只保留强定义信号；「是 / 把 / 只 / 由」等高频虚词会让检查永远不触发，失去意义。
R1_DEFINITION_SIGNALS = [
    "属于", "定义", "区别", "不同于", "不一样", "差别", "也就是说", "简单说",
    "换句话说", "它是", "是一个", "它不是", "而不是", "不接", "不生成", "不返回",
    "不负责", "不会", "提供", "接收", "返回", "负责", "接口", "协议", "字段",
    "指", "指的", "叫作", "称作", "简称",
]

# R2 标题动作词 → 正文必须出现的证据词（承诺兑现）
R2_PROMISE_MAP = [
    (["接入", "接进", "集成", "对接"], ["接口", "API", "请求", "返回", "调用", "字段"]),
    (["跑通", "跑完", "实测", "评测", "测评"], ["实测", "运行", "记录", "日志", "结果", "案例"]),
    (["对比", "对照", "相比", "vs"], ["对比", "对照", "基线", "两者", "分别"]),
    (["全部", "每个", "所有", "全流程", "端到端"], ["全部", "每个", "所有", "全流程", "端到端", "每"]),
    (["复现", "可复现", "照做"], ["步骤", "命令", "配置", "代码", "示例"]),
]

# R3 产物证据触发词（命中 >= 2 次才判定为实测/接入类文章）
R3_TRIGGER_TERMS = [
    "实测", "评测", "测评", "基准", "实验", "接入", "跑通", "调通", "联调", "压测",
    "真实调用", "真实运行", "测试", "验证",
]

# R4 自证参数词 / 就近免责词
R4_SELF_SET_PARAM = [
    "阈值", "区间", "上限", "下限", "量表", "评分标准", "打分标准", "基线",
    "对照样本", "演示规则", "教学阈值", "分档", "评级",
]
R4_DISCLAIMER = [
    "未校准", "尚未校准", "待校准", "没有校准", "教学", "演示", "虚构", "模拟",
    "我设", "自己定", "我定", "自定", "演示用", "非生产", "仅用于本文",
    "自己的", "标注数据", "上线前", "标定", "需要用真实", "按自己的",
    "我写", "由我", "我出", "我编", "我改", "我拍", "自己", "我这套",
]
# 只有「自设参数」与「由它产生的结果」出现在同一段时，才算 R4 命中；
# 单纯讨论阈值概念（例如介绍产品设计取舍）不触发。
R4_RESULT_SIGNAL = [
    "结果", "所以", "因此", "于是", "最终", "判定", "分类", "分数", "得分", "打分",
    "通过", "拒绝", "选择", "选中", "输出", "返回", "落在", "命中", "准确",
]

# R5 结尾新信息信号
R5_ACTION_MARKERS = [
    "下一步", "该做", "应该先", "建议", "先做", "先挑", "先从", "可以先", "不要",
    "别", "需要准备", "该准备", "接下来", "校准", "重跑", "换一批", "改成", "去掉",
    "保留", "想自己试", "下一篇", "预告", "什么时候", "值得", "不适合", "适合",
    "如果你是", "你会发现", "别把它", "不要把它",
]
R5_EVIDENCE_MARKERS = ["http", "见文末", "见下", "表格", "见上"]


def _strip_fenced_code(text):
    """Remove fenced code block content to avoid false positives in heading checks."""
    return re.sub(r'```[\s\S]*?```', '', text)


def _title_and_body(content):
    lines = content.splitlines()
    for index, line in enumerate(lines):
        m = re.match(r'^#[ \t]+(\S.*)$', line)
        if m:
            return m.group(1).strip(), "\n".join(lines[index + 1:])
    return "", content


def _paragraphs(content):
    """Split body into paragraphs, dropping headings, images, and code blocks."""
    body = _strip_fenced_code(content)
    body = re.sub(r'^\s*!\[.*?\]\(.*?\)\s*$', '', body, flags=re.M)
    body = re.sub(r'^#{1,6}\s+.*$', '', body, flags=re.M)
    body = re.sub(r'<video[\s\S]*?</video>', '', body)
    blocks = [b.strip() for b in re.split(r'\n\s*\n', body)]
    return [b for b in blocks if b]


def _is_link_block(block):
    """扩展阅读 / 参考链接 / 留档列表：不是结尾论述段，R5 跳过。"""
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    if not lines:
        return True
    linked = sum(1 for l in lines if re.search(r'\[[^\]]+\]\([^)]*\)', l))
    return linked >= max(1, len(lines) // 2)


def _check_structure(content):
    """Check the title and Markdown heading hierarchy, not a fixed article template."""
    errors = []
    clean = _strip_fenced_code(content)
    headings = []
    for line in clean.splitlines():
        match = re.match(r'^(#{1,6})[ \t]+\S', line)
        if match:
            headings.append((len(match.group(1)), line.strip()))

    h1_count = sum(level == 1 for level, _ in headings)
    if h1_count != 1:
        errors.append("完整文章应有且仅有一个 # 主标题，当前找到 " + str(h1_count) + " 个")
        print("[ERROR] Expected exactly one H1 title, found " + str(h1_count), file=sys.stderr)

    previous_level = 0
    circled = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
    h4_next = {}
    heading_stack = []
    for level, title in headings:
        if level > previous_level + 1:
            errors.append("标题层级跳级：" + title + " → Markdown 子标题应逐级展开")
            print("[ERROR] Heading level skipped at '" + title + "'", file=sys.stderr)
        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()
        if level == 4:
            parent_key = heading_stack[-1][1] if heading_stack else "__root__"
            expected = h4_next.get(parent_key, 0)
            heading_text = re.sub(r'^####[ \t]+', '', title)
            if expected >= len(circled) or not heading_text.startswith(circled[expected]):
                wanted = circled[expected] if expected < len(circled) else "下一个带圈数字"
                errors.append("#### 标题序号错误：" + title + " → 应以 " + wanted + " 开头")
                print("[ERROR] Fourth-level heading numbering at '" + title + "'", file=sys.stderr)
            h4_next[parent_key] = expected + 1
        heading_stack.append((level, title))
        previous_level = level

    return errors, []


# --- R1: 核心对象冷启动 -----------------------------------------------------
def _r1_cold_start(content):
    h1, body = _title_and_body(content)
    if not h1:
        return []
    terms = set()
    for m in R1_ASCII_TERM.finditer(h1):
        t = m.group(0)
        if t.upper() not in R1_TERM_STOPLIST and not t.isdigit():
            terms.add(t)
    for m in R1_QUOTED_TERM.finditer(h1):
        terms.add(m.group(1))

    body_clean = _strip_fenced_code(body)
    lead_len = max(300, int(len(body_clean) * 0.25))
    lead = body_clean[:lead_len]

    notes = []
    full_lower = body_clean.lower()
    lead_lower = lead.lower()
    for t in sorted(terms):
        tl = t.lower()
        pos = full_lower.find(tl)
        if pos < 0:
            notes.append(
                "[R1] 标题核心术语「" + t + "」在正文完全没有出现 → 开篇必须给出定义，"
                "读者读完仍不知道文章对象是什么"
            )
            continue
        window_start = max(0, pos - 60)
        window = body_clean[window_start:pos + 120]
        if tl in lead_lower and not any(sig in window for sig in R1_DEFINITION_SIGNALS):
            notes.append(
                "[R1] 术语「" + t + "」在开篇出现，但首次出现处 120 字内没有定义信号"
                "（是什么 / 和别的东西有何不同 / 负责什么）→ 读者会滑过"
            )
        elif pos > lead_len:
            notes.append(
                "[R1] 术语「" + t + "」首次出现在正文 " + str(round(pos / max(1, len(body_clean)) * 100))
                + "% 处（开篇 25% 之后）→ 陌生读者读完开头仍不知道文章讲什么"
            )
    return notes


# --- R2: 标题承诺兑现 -------------------------------------------------------
def _r2_promise(content):
    h1, body = _title_and_body(content)
    if not h1:
        return []
    notes = []

    numbers = set()
    for m in re.finditer(r'\d+(?:\.\d+)?%?', h1):
        tok = m.group(0)
        if len(tok) >= 2 or "." in tok or "%" in tok:
            numbers.add(tok)
    for n in sorted(numbers):
        if n.rstrip("%") not in body:
            notes.append(
                "[R2] 标题里的数字「" + n + "」在正文没有出现 → 标题承诺未被正文兑现，"
                "属于过度承诺（改标题或把该数字写进正文）"
            )

    for verbs, evidence in R2_PROMISE_MAP:
        if any(v in h1 for v in verbs) and not any(e in body for e in evidence):
            notes.append(
                "[R2] 标题承诺「" + " / ".join(verbs) + "」在正文找不到对应证据"
                "（期望出现：" + "、".join(evidence) + " 之一）→ 承诺量级与正文体量失配"
            )
    return notes


# --- R3: 产物证据 -----------------------------------------------------------
def _r3_artifact_evidence(content):
    hits = sum(content.count(t) for t in R3_TRIGGER_TERMS)
    if hits < 2:
        return []
    have_code = "```" in content
    have_photo = bool(re.search(r'!\[[^\]]*\]\([^)]*\.(?:png|jpe?g|webp|gif)(?:\)|["\'])', content, re.I))
    has_table = bool(re.search(r'^\s*\|[^\n]*\|\s*\n\s*\|[\s\-:|]+\|', content, re.M))

    missing = []
    if not have_code:
        missing.append("代码块")
    if not have_photo:
        missing.append("真实截图（非 SVG 示意图）")
    if not has_table:
        missing.append("数据表")
    if len(missing) >= 2:
        return [
            "[R3] 文章属实测 / 接入类（触发词命中 " + str(hits) + " 次），但只配了手绘示意图，"
            "缺少真实产物证据：" + "、".join(missing)
            + " → 至少补齐两项（代码块 / 真实截图 / 带口径的数据表）"
        ]
    return []


# --- R4: 自证参数就近披露 ---------------------------------------------------
def _r4_self_set_params(content):
    paras = _paragraphs(content)
    flagged, disclosed = [], 0
    for i, p in enumerate(paras):
        if not any(t in p for t in R4_SELF_SET_PARAM):
            continue
        if not any(s in p for s in R4_RESULT_SIGNAL):
            continue
        window = p
        if i + 1 < len(paras):
            window += "\n" + paras[i + 1]
        if i > 0:
            window = paras[i - 1] + "\n" + window
        if any(d in window for d in R4_DISCLAIMER):
            disclosed += 1
        else:
            snippet = p[:48].replace("\n", " ")
            flagged.append(snippet)

    if not flagged:
        return []
    total = disclosed + len(flagged)
    msg = (
        "[R4] 命中「自设参数 + 该参数产生的结果」" + str(total) + " 处，其中 " + str(len(flagged))
        + " 处没有就近声明「由作者设定 / 未校准 / 虚构」："
    )
    for s in flagged[:3]:
        msg += "\n        · " + s + "…"
    msg += (
        "\n        → 结论若依赖自设阈值、量表或基线，读者看到的是「模型判断正确」，"
        "实际是「结论被参数定义」。免责必须紧邻结论，不是放在文末免责段。"
    )
    return [msg]


# --- R5: 结尾新信息 ---------------------------------------------------------
def _r5_closing_new_info(content):
    paras = _paragraphs(content)
    # 跳过尾部扩展阅读 / 留档链接块
    while paras and _is_link_block(paras[-1]):
        paras.pop()
    if not paras:
        return []
    closing = paras[-1]
    if len(closing) < 30:
        return []
    has_evidence = bool(re.search(r'\d', closing)) or any(m in closing for m in R5_EVIDENCE_MARKERS)
    has_action = any(m in closing for m in R5_ACTION_MARKERS)
    if has_evidence and has_action:
        return []
    missing = []
    if not has_evidence:
        missing.append("具体数字 / 表格指向")
    if not has_action:
        missing.append("下一步具体动作（该做什么、先不做什么）")
    return [
        "[R5] 结尾段落缺少新信息信号：" + "、".join(missing)
        + "\n        → 结尾若只是把开篇或章节小结换个说法重讲，判定为同义重复；"
        "必须给下一步动作、判断标准或跑完才有资格说的发现"
    ]


def check(path, strict=False):
    content = Path(path).read_text(encoding="utf-8")
    issues = []
    advisory = []

    # --- structure checks (unique title and valid heading hierarchy) ---
    struct_errors, struct_warnings = _check_structure(content)
    issues.extend(struct_errors)
    advisory.extend(struct_warnings)

    # --- style checks (style-guide.md § 禁用表达清单) ---
    for expr in BANNED_EXPRESSIONS:
        count = content.count(expr)
        if count > 0:
            issues.append("含禁用表达「" + expr + "」（出现 " + str(count) + " 次）→ 建议替换为更自然的口语表达")
            print("[WARN] Banned expression '" + expr + "' found " + str(count) + " time(s)", file=sys.stderr)

    for marker in REVIEW_REPORT_MARKERS:
        if marker in content:
            issues.append("文件含审校报告标记「" + marker + "」→ 审校报告不得写入最终稿件，请删除")
            print("[ERROR] Review report marker '" + marker + "' found in article file", file=sys.stderr)

    double_dash_count = content.count("——")
    single_dash_count = content.replace("——", "").count("—")
    dash_count = double_dash_count + single_dash_count
    if dash_count > 1:
        issues.append("破折号 / em dash 出现 " + str(dash_count) + " 次 → 每篇最多 1 处，优先改成句号、逗号或冒号")
        print("[WARN] Dash/em dash appears " + str(dash_count) + " time(s)", file=sys.stderr)

    for expr in CHATBOT_ARTIFACTS:
        count = content.count(expr)
        if count > 0:
            issues.append("含聊天残留「" + expr + "」（出现 " + str(count) + " 次）→ 删除，不得进入最终稿")
            print("[ERROR] Chatbot artifact '" + expr + "' found " + str(count) + " time(s)", file=sys.stderr)

    for expr in GENERIC_FUTURE_CLOSERS:
        count = content.count(expr)
        if count > 0:
            issues.append("含万能展望结尾「" + expr + "」（出现 " + str(count) + " 次）→ 改成具体事实或下一步行动")
            print("[WARN] Generic future closer '" + expr + "' found " + str(count) + " time(s)", file=sys.stderr)

    for expr in PROMO_INFLATION:
        count = content.count(expr)
        if count > 0:
            issues.append("含宣传/夸张表达「" + expr + "」（出现 " + str(count) + " 次）→ 改成可验证事实")
            print("[WARN] Promotional inflation '" + expr + "' found " + str(count) + " time(s)", file=sys.stderr)

    for pattern in FALSE_DEPTH_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            issues.append("发现 " + str(len(matches)) + " 处“不是 X 而是 Y / 与其说 X 不如说 Y”结构 → 只保留真正服务论证的一处，其余改成直接判断")
            for m in matches[:3]:
                issues.append("  …" + m[:60] + "…")
            print("[WARN] False-depth construction found " + str(len(matches)) + " time(s)", file=sys.stderr)

    bursts = SHORT_SENTENCE_BURST.findall(content)
    if bursts:
        issues.append("发现 " + str(len(bursts)) + " 处连续短句轰炸 → 合并成自然句，保留必要节奏点")
        print("[WARN] Short-sentence burst found " + str(len(bursts)) + " time(s)", file=sys.stderr)

    # --- reader-payoff.md § R1-R5 ---
    reader_notes = []
    reader_notes.extend(_r1_cold_start(content))
    reader_notes.extend(_r2_promise(content))
    reader_notes.extend(_r3_artifact_evidence(content))
    reader_notes.extend(_r4_self_set_params(content))
    for n in reader_notes:
        print(("[ERROR] " if strict else "[WARN] ") + n.split("\n")[0], file=sys.stderr)
    if strict:
        issues.extend(reader_notes)
    else:
        advisory.extend(reader_notes)
    closing_notes = _r5_closing_new_info(content)
    advisory.extend(closing_notes)
    for n in closing_notes:
        print("[WARN] " + n.split("\n")[0], file=sys.stderr)

    if issues:
        print("\n【文章质量检查报告】")
        for issue in issues:
            print("  ✗ " + issue)
        if advisory:
            for w in advisory:
                print("  ⚠ " + w)
        print("\n共发现 " + str(len(issues)) + " 个问题，请按建议修改后再发布。")
        return False

    if advisory:
        print("【文章质量检查通过（含建议）】" + path)
        for w in advisory:
            print("  ⚠ " + w)
    else:
        print("【文章质量检查通过】" + path)
    return True


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    strict = "--strict" in sys.argv
    if len(args) < 1:
        print("用法：python check_article.py <article_md_path> [--strict]")
        print("  --strict  把读者兑现门禁 R1-R4 升级为阻断项，R5 保留建议（Step 6 收尾时使用）")
        sys.exit(1)
    ok = check(args[0], strict=strict)
    sys.exit(0 if ok else 1)
