---
name: ai-write-flow
description: "写作、改编或审校中文技术文章、公众号长文和图卡文案；也用于为已有文章规划并生成章节 SVG 配图。"
---

# ai-write-flow — 技术博客写作工作流

**脚本路径：** `{skill_root}` 指本次加载的 `SKILL.md` 所在目录；执行命令前替换为该目录的绝对路径。它与保存稿件的 `{workspace}` 不同，不依赖工作区内存在 `skill/`。

## 快捷入口：审校模式

**优先级：** 高于所有 Step，包括 Step 0。检测到本意图时直接进入 Review 流程，不执行输出模式路由。

**触发意图：** 用户传入已有文章 + 表达"降AI味 / 审校 / 去掉AI腔 / 润色"等意图

**跳过步骤：** Step 0 及 Steps 1-4 全部跳过

**直接加载：** `references/fact-policy.md` + `references/reader-payoff.md` + `references/persona.md` + `references/style-guide.md` + `references/checklist.md` + `references/ai-flavor-patterns.md` + `references/human-voice-policy.md`

**执行流程：** 直接进入 Step 5 审校（R1-R5 读者兑现门禁 → 内容 → 作者手迹保护 → AI 味检测/降噪 → 细节 → 二次扫描）

**输出结构：** 审校报告（对话窗口展示）+ 关键改动说明 + 修订后全文；若用户要求“只检查/先别改/detect/audit only”，只输出检测报告，不输出修订全文

**范围优先：** 只润色、降 AI 味或只审查时，R1–R4 未通过记录为结构或证据缺口，不自动回到 Step 4 重写，不追加事实或进入发布流程；交付本轮范围内的修订或检查报告。用户明确要求完整重写、补证据或发布就绪稿时，才适用后文完整写作的返工与落盘门禁。

**事实处理规则（审校模式专项）：**
- 审校模式不得新增、改写或强化高风险事实（版本号、性能数据、价格、模型名、发布时间等）
- 若原文中发现缺少来源支撑的高风险事实，在审校报告的"内容审校"栏列为「待核验事实」，不替用户补全或修改
- 文风润色不改变事实表述；如要修改数字或版本号，必须先告知用户并等待确认

---

## Step 0：输出模式路由（Output Mode Routing）

**触发条件：** 工作流启动时自动执行（审校快捷入口优先级更高，命中时跳过本步骤）

**路由规则：**

| 触发关键词 | 输出模式 | 进入流程 |
|-----------|---------|---------|
| 图卡 / 贴图 / 卡片 / 小红书 / card / 图卡生成系统 / 1000字以内的内容 | `card_post` | 加载 card-post-config.md，进入图卡流程 |
| 配图 / 章节配图 / 分段配图 / SVG 插图 / 给文章加图 | `longform_article + illustration_extension` | 加载 illustration-config.md，进入章节配图流程 |
| 以上均无 | `longform_article` | 继续 Step 1-6 长文流程 |

**illustration_extension 路由规则：**
- 用户只要求「给已有文章配图」→ 跳过 Step 1-4 写作流程，直接进入章节 SVG 配图扩展
- 用户要求「写文章并配图」→ 先完成 Step 1-6，文章稳定后再进入章节 SVG 配图扩展
- 未明确要求配图时，不主动生成配图，不打断写作流程

**card_post 模式加载文件：**

- `references/card-post-config.md`
- `references/fact-policy.md`
- `references/research-config.md`
- `references/persona.md`（语气参考）
- `references/style-guide.md`（语气参考，不强制文章结构）

---

## 图卡流程（card_post 模式）

card_post 模式共执行 4 步：Step 1（工作区检查）→ Step 2（调研与核查）→ 卡片草稿 → 落盘输出。

**Step 1 和 Step 2 与长文主流程相同**（见下方主流程章节），但 Step 2 额外执行 research-config.md 中的 `card_post 事实核查补充规则`，并在 JSON 中输出 `card_safe_claims[]` 和 `excluded_claims[]`。

---

### 图卡 Step 3：卡片草稿（Card Draft）

**触发条件：** Step 2 调研通过后执行

**加载文件：** `references/card-post-config.md`（已在 Step 0 加载）+ `references/fact-policy.md`

**行为规范：**

1. 基于 Step 2 的 `card_safe_claims[]`，决定信息单元数量，输出【卡片数量决策】
2. 等待用户确认卡片数量（可微调）
3. 用户确认后，按 card-post-config.md 的输出结构，依序输出：
   - 【事实核查摘要】
   - 【卡片数量决策】（确认版）
   - 【发布配文】
   - 【图卡内容排版】（封面图卡 + Card 01…）
4. 所有图卡要点必须可追溯到 `card_safe_claims[]` 中 `can_use_in_card: true` 的 supported claim
5. `excluded_claims[]` 中的事实禁止出现在发布内容（【发布配文】与【图卡内容排版】）

**阻断规则：** 用户未确认卡片数量决策前，不生成图卡文案

---

### 图卡 Step 4：落盘输出（Card Publish）

**触发条件：** 图卡 Step 3 完成后执行

**行为规范：**

1. 将完整输出（含事实核查摘要、卡片数量决策、发布配文、图卡内容排版）保存到：
   `{workspace}/output/{YYYYMMDD}-card-{topic-slug}.txt`
2. 文件名格式：`YYYYMMDD` 为今日日期，`topic-slug` 为主题的 kebab-case 版本
3. 落盘前运行图卡校验（必须带 `--research` 做事实追溯，缺少 research JSON 时阻断，不得落盘）：
   ```
   python3 "{skill_root}/scripts/check_card_post.py" \
       {workspace}/output/{YYYYMMDD}-card-{topic-slug}.txt \
       --research {workspace}/research/{YYYYMMDD}-{topic-slug}.json
   ```
   - 若退出码非零：按错误提示修订图卡内容（修改在对话窗口内完成），重新运行校验通过后再落盘
4. 输出保存路径供用户确认

**阻断规则：** 文件写入失败时报错，列出路径，请用户检查目录是否存在

---

## 主流程（longform_article 模式，6 步）

### Step 1：工作区解析 & 素材检查（Workspace & Brief Check）

**触发条件：** 工作流启动时自动执行

**加载文件：** `references/workspace-local.md`（不存在时回退到 `references/workspace-config.md`）

**行为规范：**

1. 首先检查 `references/workspace-local.md` 是否存在：
   - 若存在 → 从中读取 `workspace_path` 字段，使用该路径
   - 若不存在 → 加载 `references/workspace-config.md`，按以下优先级解析运行时工作区：
     - 若用户在本次对话中明确指定路径 → 使用该路径
     - 若环境变量 `AI_WRITE_FLOW_WORKSPACE` 已设置 → 使用该路径
     - 若 `~/Documents/workspace/ai-write-flow` 存在 → 使用该路径（约定默认路径）
     - 否则 → 询问用户工作区位置，等待回复后继续

2. 解析工作区后检查 `{workspace}/briefs/` 目录
3. 若目录为空或不存在 → 记录状态，继续执行
4. 若目录有文件 → 按多格式素材处理原则生成材料清单，继续执行

**多格式素材处理原则：**

支持文件类型：PDF、Markdown、TXT、DOCX、图片、表格、JSON、网页摘录

对每个文件生成材料清单条目：

| 字段 | 说明 |
|------|------|
| 文件名 | 原始文件名 |
| 类型 | 文件格式 |
| 读取状态 | 成功 / 失败 |
| 提取摘要 | 主要内容要点（100字以内）|
| 可信度备注 | 来源性质（用户原创素材、截图、第三方文章等）|

无法读取的文件不得跳过，必须列入"未解析文件清单"并提示用户处理方式。

**写入规则：** 运行产物（研究 JSON、成品文章、图片）只能写入 `{resolved_workspace}`，严禁写入 Skill 安装目录。

**固定输出模板（措辞不可改写）：**

```
【Step 1 工作区 & 素材检查】
工作区：{resolved workspace path}
素材状态：{无 briefs | 已加载 N 个文件}
说明：{workspace/briefs/ 目录为空，本次创作不含外部素材约束 | 已加载以下文件作为创作约束：[文件名列表]}
未解析文件：{无 | [文件名列表，请确认是否需要转写或提供文本版]}
处理：继续执行 Step 2
```

**阻断规则：** 无法解析工作区时阻断，等待用户提供路径后继续

---

### Step 2：调研（Research）

**触发条件：** Step 1 完成后执行

**加载文件：** `references/research-config.md`

**执行模式（根据 briefs/ 状态自动选择）：**
- `briefs/` 有内容 → `brief_first_verify_mode`（三段式）
- `briefs/` 为空 → `publish_mode`（全量调研，跑满 Layer 1-4）

**行为规范 A — `brief_first_verify_mode`（briefs/ 有内容时执行）**

**Stage A — Brief Ingest（提取候选事实）**
- 从 briefs/ 中提取所有候选事实，每条标记为 `Tier 1 Candidate`，**不是 Tier 1 Final**
- 重点覆盖高风险字段：产品名称、产品定位、发布主体、版本/日期、截图功能归属、价格/API 地址/兼容性

**Stage B — Targeted Verification（定点核查）**
- 仅对 Stage A 提取的高风险字段做外部核查
- 不机械跑满 Layer 1-4，只验证易变、易混淆、有多义性的候选事实
- 用 research-config.md 中的 Source Tiers 判断外部来源质量

**Stage C — Discrepancy Report（差异报告）**
- 无差异 → 候选事实升级为 `verified`，输出 JSON，继续 Step 3
- 发现差异 → 输出【差异确认】格式，**立即阻断，等待用户确认后再进入 Step 3**

差异门禁触发条件（任一满足即阻断）：
- 用户截图和公开资料表述不一致
- 产品名称相近但主体不同
- 功能演示成立，但官方定位描述不同
- 时间相关信息（版本、定价、可用性）无法确认最新性

【差异确认】固定输出格式（措辞不可改写）：

```
【差异确认】
事实项：[具体字段名]
用户素材：[简报/截图中的描述]
外部证据：[外部来源的描述，附 URL]
风险：[若直接写入正文可能导致的问题]
建议处理：
1. [处理方案 A]
2. [处理方案 B]
请用户确认后继续
```

**行为规范 B — `publish_mode`（briefs/ 为空时执行）**

- 判断 topic_type，执行 research-config.md 中的 Layer 1-4 完整调研流程
- 所有 claim 须有 Tier 1/2 来源支撑，30 天时效门禁严格执行
- 输出 JSON 结构到 `{workspace}/research/{YYYYMMDD}-{topic-slug}.json`

**JSON 输出（两种模式均适用）：** 路径 `{workspace}/research/{YYYYMMDD}-{topic-slug}.json`，候选事实单独列入 `tier_1_candidates` 字段

**阻断规则：**
- `brief_first_verify_mode`：Stage C 发现任一差异 → 阻断，等待用户确认后继续
- `publish_mode`：`quality_check.passed == false` → 阻断，列出不达标原因，等待用户补充材料

---

### Step 3：选题讨论（Topic）

**触发条件：** Step 2 调研通过后执行

**加载文件：** `references/title-naming.md` + `references/reader-payoff.md`（基于 Step 2 调研结果，使用 `explore_mode`）

**行为规范：**

先从已核验素材中提取：内容对象、目标读者、核心收益、主要张力和证据边界。然后生成 3-4 个选题与标题方向，每个方向须包含以下维度：

| 维度 | 说明 |
|------|------|
| 文章类型 | 实战评测 / 深度解析 / 教程指南 / 经验分享（对应 style-guide.md 4 种模板）|
| 工作量 | 轻（1000-1500字）/ 中（2000-3000字）/ 重（3000-4000字）|
| 是否需要真实测试数据 | 是 / 否 |
| 核心角度 | 一句话描述差异化切入点 |
| 读者冷启动一句话 | 陌生读者读完开头 300 字能说出：文章讲什么、它和同类有何不同、作者亲手做了什么。写不出就是选题没冷启动（reader-payoff.md § R1）|
| 产物证据计划 | 实测 / 接入 / 评测类必填：正文将放哪几项真实产物（代码块 / 真实截图 / 带口径数据表 / 真实请求体），至少两项（§ R3）|
| 标题候选 | 该方向对应的工作标题，候选之间必须使用不同的点击理由 |
| 标题承诺 | 读者打开后能得到的具体收益或判断 |
| 承诺落点预判 | 标题里的每个数字、动词（接入/实测/对比/全部/复现）在正文对应哪一段兑现（§ R2）|
| 证据要求 | 正文必须提供的数字、案例、测试或来源 |
| 风险 | 可能歧义、过度承诺或依赖时效的地方 |

标题候选优先覆盖结果承诺、问题诊断、对比冲突、案例证据、判断选择等不同机制；不要只做同义改写。对候选按清晰度、点击理由、具体性、悬念质量、可信度各 1-5 分内部评分，推荐一个主选和最多两个备选，并说明推荐理由。

若用户已提供标题，先将其作为工作标题评估，不得无理由替换。若标题涉及版本、价格、数字、发布时间、人物或机构，必须与 Step 2 的事实边界一致。

**选题与账号定位对齐：** 实测选题的场景必须落在 `persona.md` 的「内容方向」和「目标读者」范围内。场景本身对目标读者无共鸣时，优先换角度（例如从「报销怎么批」改成「结构化决策原语怎么设计」），而不是硬写。

**阻断规则：** 用户未明确选定选题和工作标题前，不进入 Step 4

---

### Step 4：两阶段创作（Draft）

**触发条件：** 用户确认选题后执行

**加载文件：** `references/persona.md` + `references/style-guide.md` + `references/fact-policy.md` + `references/title-naming.md` + `references/reader-payoff.md`

**行为规范（两阶段，严格顺序）：**

**第一阶段：骨架生成**
- 基于选定选题和 persona.md 生成文章骨架
- 骨架包含：工作标题、读者问题、开篇抓手、叙事推进、章节或场景的转场理由、每部分要用的证据/案例/图片、结尾落点；只有用户需要控篇幅时才估算分章节字数
- 对实测与经验文章，先搭“为什么做 → 我怎么试 → 案例逐步增加难度/代价 → 记录支持什么 → 哪些结论仍不能下 → 给读者什么判断”的叙事架构，再决定章节标题；不要先套目录模板
- 骨架阶段使用工作标题；正文最强证据若暴露出更准确的核心承诺，先提出最终标题建议并等待用户确认，不能静默改名
- 用户确认最终标题后，正式文章的 `#` 标题只能出现一次；副标题如有，必须补充范围、方法或证据，不得重复主标题
- `#` 标题全文只出现一次。`##` / `###` / `####` 按语义选用，编号仅在用户要求或确实方便扫读时使用；使用 `####` 时，标题开头必须按同一父级下的顺序使用 `①`、`②`、`③`、`④`……；不要要求每个章节都拥有相同层级和数量的小标题。
- 开篇可从作者身份、真实触发点、问题、结果或图片切入；结尾可收束观点、给行动建议、预告下一篇或邀请读者互动，按文章目标决定，不固定叫“写在最后”。
- 评测文章需要表格时，用它承载真正可比的数据；没有可比基线时，不强行生成 Before/After 表格。

**第一阶段必须同时产出两张表（缺一不进入第二阶段）：**

1. **【读者兑现映射表】**（reader-payoff.md § R2）

   | 标题承诺 | 正文章节 | 兑现证据 | 状态 |
   |---------|---------|---------|------|

   逐项拆解标题里的数字、动词和范围词。**不允许出现状态为「空」的项**；无法兑现的项必须改标题或改角度。

2. **【证据账单】**（reader-payoff.md § R3、fact-policy.md）

   列出素材里所有可用证据（日志、benchmark 报告、telemetry、成本、截图、demo 界面），标注「是否进正文 / 放在哪一节」。然后回答：读者只读这一篇能拿到的最硬证据是什么，它在正文里吗。实测 / 接入 / 评测类文章正文须含至少两项真实产物（代码块 / 真实截图 / 带口径数据表 / 真实请求体或日志）；SVG 示意图不计入。

3. **【自设参数清单】**（fact-policy.md § R4）

   列出正文用到的所有自设阈值、量表、基线、标签、演示制度，逐项写明「谁定的 / 它决定了什么 / 去掉它还剩什么结论」。这三条要写进对应段落，就近披露，不放文末免责段。

- 骨架在对话窗口展示，等待用户确认

**第二阶段：正文填充**
- 用户确认骨架后才进入正文
- 正文遵守 style-guide.md、persona.md 和用户本轮要求；事实与证据边界优先
- 标题层级服务导航，不作为正文填充模板；避免把每个段落改造成编号小节
- 结尾必须提供开篇没有的东西：下一步具体动作、读者可用的判断标准，或跑完才有资格说的发现（reader-payoff.md § R5）

**阻断规则：** 第一阶段骨架必须获得用户明确确认（"确认"/"可以"/"好的"），否则不进入第二阶段；【读者兑现映射表】和【证据账单】缺失时不进入第二阶段

---

### Step 5：多轮审校（Review）

**触发条件：** Step 4 正文完成后执行（或通过审校快捷入口直接触发）

**加载文件：** `references/fact-policy.md` + `references/reader-payoff.md` + `references/persona.md` + `references/checklist.md` + `references/ai-flavor-patterns.md` + `references/human-voice-policy.md`

**行为规范（顺序执行）：**

1. **前置：读者兑现门禁 R1-R5** — 按 `reader-payoff.md` 逐项判定 R1 冷启动、R2 标题兑现、R3 证据使用、R4 自设参数披露、R5 结尾新信息。**这 5 项先于常规内容审校**，完整写作模式中，R1–R4 不通过则回到 Step 4 补骨架或补证据，不得在正文里打补丁绕过；R5 记录为改进建议。每项判定须写入审校报告并给出正文位置
2. **第一遍：内容审校** — 技术准确性、数据一致性、逻辑结构；**检查正文中是否有缺少来源的高风险事实**（版本号、性能数据、价格、模型名、发布时间等），发现则列入审校报告"待核验事实"栏，不替用户补全
3. **第二遍：作者手迹保护** — 按 human-voice-policy.md 判断哪些句子不该动；已有文章优先保留作者的语气词、重复、停顿、抽象层级和不工整呼吸
4. **第三遍：AI 味检测/降噪** — 按 ai-flavor-patterns.md 标记 P0/P1/P2 问题；默认修复 P0/P1，P2 只在密度过高时处理
5. **第四遍：细节打磨** — 句长、段落、标点、朗读顺畅度
6. **二次扫描：只扫本轮改动过的句子** — 检查是否新增假深刻、意义拔高、金句、排比、虚构细节、未经核验事实；发现则回退或改成更白描的表达。**R4 免责句被删或后移、R3 限制性数字（样本量/口径/费用/延迟）被删，均视为新增缺陷，一并回退**

**detect-only 模式：**
- 触发词：只检查 / 先别改 / detect / audit only / 标出来 / 不要重写
- 只输出【AI 味检测报告】，不输出修订后全文，不落盘
- 每条问题包含：严重级别、原句、问题类型、建议方向

**改动约束：**
- 不主动添加金句、漂亮比喻、虚构时间地点、未经来源支撑的数据或案例
- 不为了“更专业”把自然口语改成书面套话
- 能少动就少动；每个关键改动必须说明原因，拿不准的标记“可还原”
- 已有文章的 R4 返工默认走「就地去重披露」：在每处自设参数结论旁补一句「谁定的 + 决定了什么」，而不是在文末加一段集中免责

**结构审校（随审校流程同步执行，发现问题即报告）：**
- 完整文章有一个清楚的主标题；标题层级符合 Markdown 语义，不跳级、不为套模板而过度细分
- 章节顺序能带读者从问题走到案例、解释和结论；场景转换有必要的承接
- 小标题能帮助读者定位；若标题比正文还密、同一观点多次总结，标为结构问题
- 结尾呼应文章实际证据和作者目的；不强制编号、固定标题、固定清单或固定长度
- 实验体量与文章体量匹配：demo 的场景数、界面完整度与正文实际呈现的内容同量级

**输出结构：**
- 审校报告：在对话窗口完整展示（含每遍发现的问题）
- **读者兑现门禁判定表**：R1-R5 每项给出「通过 / 不通过 / 部分」+ 正文位置或缺失证据，作为报告第一节
- 关键改动说明：列出原文、修改、原因、是否可还原
- 修订后全文：在对话窗口输出
- **审校报告禁止写入最终 .md 稿件文件**

**阻断规则（完整写作 / 发布就绪稿；局部审校遵循快捷入口范围）：** R1（冷启动）、R2（标题无空项）、R3（产物证据两项）、R4（自设参数就近披露）任一不通过，不得进入 Step 6 落盘；必须回到 Step 4 补骨架、补证据或改标题。R5 与其余 WARN 记录在报告中

---

### Step 6：落盘输出（Publish）

**触发条件：** Step 5 完成后执行

**加载文件：** 无

**行为规范：**

1. 将修订后全文保存为临时待校验 Markdown 文件，记其绝对路径为 `{draft_path}`；通过校验后再保存到 `{workspace}/output/{YYYYMMDD}-{title-slug}.md`
2. 文件名格式：`YYYYMMDD` 为今日日期，`title-slug` 为标题的 kebab-case 版本
3. 正式落盘前对临时稿运行结构与风格校验（读者兑现检查默认为 advisory，完整文章加 `--strict`）：
   ```
   python3 "{skill_root}/scripts/check_article.py" "{draft_path}" --strict
   ```
   - 默认模式：`R1`–`R5` 均为 `[WARN]`，不阻断，供快速体检
   - `--strict` 模式：`R1`/`R2`/`R3`/`R4` 命中时升级为 `[ERROR]`，退出码非零；R5 始终保留 `[WARN]`。**完整文章落盘前必须通过 strict**；brief、大纲、素材稿用默认模式
   - 以退出码为准：非零时先修复，不得正式落盘；结构和文风问题仍可能阻断
   - 退出码为零时，剩余建议记录在 Step 5 审校报告中
4. 校验通过后保存正式稿，输出保存路径供用户确认

**阻断规则：** 文件写入失败时报错，列出路径，请用户检查目录是否存在

---

## 工作区规则

详细工作区解析规则、目录说明与安全约束见 `references/workspace-config.md`。

## 参考文件索引

| 文件 | 负责什么 | 何时加载 |
|------|---------|---------|
| `references/reader-payoff.md` | **读者兑现门禁 R1-R5**：冷启动、标题承诺、证据使用、自设参数披露、结尾新信息 | Step 3 / Step 4 / Step 5 全程 |
| `references/fact-policy.md` | 输出门禁：claim 边界、禁止表述、自设参数披露、证据使用义务 | Step 3-6 |
| `references/checklist.md` | 审校逐遍执行清单 | Step 5 |
| `references/persona.md` | 账号人设、内容方向、目标读者 | Step 3-4 |
| `references/style-guide.md` | 4 种文章类型模板 | Step 4 |
| `references/ai-flavor-patterns.md` | AI 味模式库与修复动作 | Step 5 |
| `references/human-voice-policy.md` | 作者手迹保护规则 | Step 5 |
| `references/title-naming.md` | 标题命名机制 | Step 3 |
| `scripts/check_article.py` | 自动门禁：`--strict` 时 R1-R4 阻断 | Step 6 |

---

## 章节 SVG 配图扩展（optional）

Only run this flow when the user explicitly asks for article illustrations, section images, 分段配图, 章节配图, or SVG visuals.

Load `references/illustration-config.md`.

Flow:
1. Check that Markdown headings have a clear hierarchy; do not require fixed numbering or nested levels.
2. Parse the final article into illustration units using meaningful `##` sections when present. Exclude the opening and a closing section only when they are not visual subjects.
3. Extract each unit's `core_claim`, `keywords`, and classify its `diagram_type` via Semantic Shape Classification.
4. Produce a **【章节配图规划】** prompt outline table and wait for user confirmation.
5. After confirmation, save the plan JSON to `{workspace}/images/{YYYYMMDD}-{article-slug}/illustration-plan.json` (include `output_path` for each item).
6. Run `python3 "{skill_root}/scripts/check_illustration_plan.py" "{workspace}/images/{YYYYMMDD}-{article-slug}/illustration-plan.json"` — if non-zero, fix the plan and re-run until it passes.
7. For each approved unit, use the local svg-architect skill to generate one `wechat_article` SVG (1200×500) and save to the `output_path` specified in the plan.
8. Insert Markdown image references into the corresponding article sections (after the ordinary `##` heading, before the first `###` subheading).

Never call image2 or external image APIs in the default flow.
