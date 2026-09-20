---
name: ai-daily-news-v3
description: 生成、审核、增量修订与维护《AI机会情报晨报 V3》。用于日报内容、四路云端采集、OpenAI事实边界、GitHub Today深度拆解、V3视觉和固定信箱路由；不得改动聊天侧栏、擅自新建日报任务/窗口、公开发布或把采集健康误称为全网零遗漏。
metadata:
  version: 1.1.0
  production_state: PRODUCTION_STABLE
---

# AI机会情报晨报 V3

## 当前冻结生产状态

- PRODUCTION_STABLE=true
- 正式日报唯一目的地：AI报纸信箱｜只收日报
- 治理/审核窗口：CHAT｜AI情报晨报总控-4
- 正式日程：每天 07:00 JST
- 每日生产不依赖 Mac、Remote、V2 或本地 Codex
- 默认只生成日报；仅 Owner 明确要求“日报 + 小红书照片”时额外生成小红书图片
- 朋友圈版本已取消

## 使用场景

- 生产新一期：按当前日期窗口采集与核验，只建立一份正式主稿。
- 同日更新：先读取上一正式版，只增量加入新增/变化/纠错，递增版本并记录 supersedes。
- 补发：重发同一正式文件，不改变新闻截止，不重新写稿。
- 只读审核：检查内容、来源、渲染、采集健康与路由，不擅自新建任务或窗口。
- 工程维修：仅修改采集器、HTML生成器、云端脚本或测试程序时使用 Codex；Codex不是每日生产前置。

## 新闻窗口与事实纪律

- 时区固定 Asia/Tokyo。
- 新闻窗口：前一自然日00:00 → 本次生成时刻。
- 跨日去重；只有实质新增才写后续。
- OpenAI/GPT/Codex最高优先级。
- 美国、中国、日本分区；未坐实信号单列。
- 主要事实来源优先：官方 News、Release Notes、Help、Developers/开发文档、官方GitHub、政府官网、企业官方公告、原始论文。
- X、媒体、社区用于发现线索，重要信息尽量回原始来源。
- 区分事实、公司自述、媒体报道、员工评论、会议预告、研究、编辑分析、创业推演、未坐实信号。
- 发布日期 ≠ 事件发生日。
- ChatGPT Release Notes 最新功能日期 ≠ OpenAI News 所有公司动态日期。
- 转帖、作品展示、Linux desktop评论、keynote预告不得包装成正式新品发布。
- 早期接入不等于人人可用；开源不等于免费运行；自动安全检查不等于法律/监管认证。

## 四路云端采集合同

正式读取 yeshuai508/ai-daily-news 仓库 x-cloud-cache 分支四个缓存。

### 1. x-latest.json｜固定X必检层

- schema=ai-daily-news.x-cloud.v1
- write_actions=NONE
- 当前正式预设16个核心账号。
- 检查 generated_at、window_start/window_end、coverage 和逐账号结果。
- coverage=COMPLETE 且运行开始距 generated_at <=120分钟：固定层健康。
- PARTIAL：只纳入成功账号，整体至少黄。
- FAILED / 缺失 / 年龄>120分钟：整体至少黄；关键采集整体失败才红。
- COMPLETE只表示预设账号读取成功，不代表X全站、分页、回复、长帖、受保护内容或所有转帖零遗漏。

### 2. x-discovery-latest.json｜X动态补漏发现层

- schema=ai-daily-news.x-discovery.v1
- scope=DYNAMIC_NETWORK_EXPANSION_FROM_CORE_X
- candidate_only=true
- verification_required=true
- 读取 coverage、semantic_health、扩展账号和发现证据。
- 从核心账号当日转发/提及扩展外部账号，再读这些账号近期公开内容。
- 这是补漏发现层，不是X全站搜索。
- 重要候选必须追溯原帖/官方公告后才可写成事实。
- FAILED / DEGRADED / SUSPECT_EMPTY 且无充分替代发现证据时，整体至少黄。

### 3. web-discovery-latest.json｜Web候选发现层

- schema=ai-daily-news.web-discovery.v1
- candidate_only=true
- verification_required=true
- 覆盖四组：美国核心AI、Agent/工具、中国AI、日本AI。
- COMPLETE只代表预设查询完成，不代表互联网零遗漏。
- 重要候选必须回原始媒体、官方公告或一手文档核验。

### 4. github-trending-latest.json｜GitHub Trending Today

- schema=ai-daily-news.github-trending.v1
- source_url必须等于 https://github.com/trending?since=daily
- range=today
- write_actions=NONE
- 保留官方页面读取时顺序。
- 使用 stars_today，不用累计Stars替代。
- 不用GitHub搜索排序代替Trending。
- 不自行按 stars_today 重新排序。
- 不拿昨天榜单冒充今天。

## 健康灯

- 🟢：OpenAI官方源、固定X、动态X、Web发现、美国/中国/日本主要来源、GitHub Trending、去重、事实核验均有本轮真实证据。
- 🟡：重要来源受限、缓存过期、动态发现异常或候选无法充分核验。
- 🔴：关键采集整体失败。
- 绿灯只表示预设采集链通过，绝不表示X全站或全网理论意义零遗漏。

## 固定12栏目

01 今日总览
02 GPT / Codex 一级情报
03 美国AI
04 中国AI｜企业使用 + 政府政策
05 日本AI
06 前沿AI落地 / 真产品
07 AI爆款产品商业拆解
08 GitHub 今日开源 Top 3
09 补充情报雷达
10 每日AI创业建议
11 机会筛选器
12 老板结论

条数由真实信息决定。不得为了数量制造新闻。

## GitHub Top 3九类深度

每个项目必须保留：
1. 用途
2. 工作方式
3. 使用场景
4. 潜在客户
5. 交付物
6. 可能收费方式
7. 最小验证
8. 今日热度依据
9. 风险限制

最后只使用一个行动标签：今天值得试 / 先收藏观察 / 与现有方向关系不大。
商业机会属于分析/假设，不得包装成已有客户、已有收入或已经盈利。
只有存在真实连续3—7天历史快照，才允许写“持续升温”；历史不足就明确历史不足。

## V3最终视觉规则

- 深蓝背景 #06101c
- 蓝紫渐变首页
- 浅色中文正文
- 通透内容卡片
- 栏目色条
- 桌面双栏、手机单栏
- 手机正文不小于17px
- 首页只放新闻主标题、导读、日期、版本、信息截止和小型采集状态
- 工程旁白只允许进入文末“来源与采集状态说明”折叠区

标题：桌面/平板优先2行，手机优先2—3行；按完整语义换行。禁止词内断行、孤字、孤立短词，也不得为避免换行把字号缩得过小。

普通正文不得出现 schema、16/16、workflow、Secrets、Remote、Mac、Codex施工、缓存年龄、GitHub Actions施工、内部测试号或费用等工程旁白。

## 左侧窗口与投递治理｜最高优先级

冻结名称：
- 正式日报信箱：AI报纸信箱｜只收日报
- 治理窗口：CHAT｜AI情报晨报总控-4

未经Owner明确授权，绝对不得：
1. 修改任何聊天窗口名称
2. 自动重命名
3. 置顶或取消置顶
4. 改变窗口排序
5. 移动、分组、归档或删除
6. 为自动化/调试/终验新建替代聊天窗口
7. 为修复路由修改任务名称冒充聊天名称
8. 新建第二个正式日报任务

任务名称 ≠ 聊天窗口名称。

正式日报正文与HTML附件只能进入 AI报纸信箱｜只收日报。
CHAT｜AI情报晨报总控-4 只负责规则治理、质量验收、故障排查、Skill维护与版本升级，原则上不交付正式日报成品。

## 单一正式主稿

- 每天只有一份正式主稿。
- 补发只重发同一文件。
- 同日更新必须在上一正式版基础上增量修订并记录 supersedes。
- 保留仍有价值的旧分析；禁止从头重写导致GitHub解释缩水、边界消失或已修问题复发。

## 机械与事实验收

至少确认：12栏目齐全、手机正文>=17px、桌面标题优先2行、手机2—3行、无横向溢出、无词内断行/孤字、GitHub三项目九类完整、外链语法正常。

机械检查不能替代新闻事实、来源新鲜度、浏览器真实渲染、目标信箱路由或用户可见送达。

## 绝对红线

- 不修改聊天侧栏。
- 不新建平行信箱或第二个正式日报任务。
- 不为了绿灯放宽120分钟阈值、伪造generated_at或删除风险提示。
- 不读取/展示Secrets、Cookie、会话令牌。
- 不因日常生产调用Remote、Mac、V2或本地Codex。
- 没有Owner明确授权，不付费、不公开发布。

## 安装与触发说明

这是仓库级Codex Skill。Codex从仓库的 .agents/skills 目录自动发现Skill；当任务与description匹配时可自动选择，也可显式调用。
Skill文件存在或被读取不代表ChatGPT侧原生Skill已安装。

## 版本

ai-daily-news-v3 v1.1.0
冻结日期：2026-09-20
来源包：AI_DAILY_NEWS_V3_SKILL_v1.1.0
冻结生产状态：PRODUCTION_STABLE