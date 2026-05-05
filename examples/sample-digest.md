# AI日报 - 2026-02-18

## 🔥 今日要闻

- **Anthropic发布Claude Sonnet 4.6**：新模型在代码、长文本和工具调用上全面逼近旗舰Opus，价格却维持中端。  
  💬 洞见：性能曲线继续上移，意味着“够用且便宜”的模型窗口正快速挤占高端市场，开发者可把Opus级能力当日常API用。  
  [来源](https://x.com/alexalbert__/status/2023817479580221795)

- **Claude新增“先过滤后阅读”联网工具**：模型先写代码筛网页，再让有效结果进入上下文，准确率+13%、输入token-32%。  
  💬 洞见：把“写脚本”内化为模型原生能力，提示词里再也不用教它“先搜再总结”，直接省成本。  
  [来源](https://x.com/alexalbert__/status/2023834863858769975)

- **印度8个月 vibe-coding 公司 Emergent 自称ARR破1亿美元**：主打“一句话生成完整商业软件”，客户多为非技术小商家。  
  💬 洞见：当编码边际成本趋零，首批付费者不是程序员而是小老板，AI原生SaaS的定价逻辑将被重新书写。  
  [来源](https://techcrunch.com/2026/02/17/emergent-hits-100m-arr-eight-months-after-launch-rolls-out-mobile-app/)

- **Meta与Nvidia签下多年芯片大单**：首次大规模部署Grace CPU，目标数据中心能效比再提一档。  
  💬 洞见：GPU之外抢CPU，说明大模型训练/推理的瓶颈正向“内存-带宽-功耗”转移，硬件竞争进入细颗粒阶段。  
  [来源](https://www.theverge.com/ai-artificial-intelligence/880513/nvidia-meta-ai-grace-vera-chips)

- **苹果被曝同步开发三款AI可穿戴**：智能眼镜、AI吊坠、带摄像头的AirPods，均靠iPhone算力与Siri视觉交互。  
  💬 洞见：把“视觉版Siri”拆成多形态配件，苹果在试探谁能成为下一代平台入口，而非一次性押注一款头显。  
  [来源](https://www.theverge.com/tech/880293/apple-ai-hardware-smart-glasses-pin-airpods)

## 💡 值得关注的观点

- “LLM正在重写编程语言的约束条件，C→Rust迁移热只是早期信号。” —— **Andrej Karpathy**（前Tesla AI总监，前OpenAI研究员）[原文](https://x.com/karpathy/status/2023476423055601903)

- “计算机使用能力从‘几乎为零’到‘接近人类水平’只用了一年半，提醒所有人迭代速度还在加快。” —— **Alex Albert**（Anthropic Claude关系负责人）[原文](https://x.com/alexalbert__/status/2023820589983801796)

- “当AI吃掉全部代码生产链后，人类最后的护城河是‘分销’——谁能触达并留住用户。” —— **Lenny Rachitsky**（产品增长顾问）[原文](https://x.com/lennysan/status/2023533747128476111)

- “未来的软件会像消费品一样被挑：先看‘氛围’，再看功能；品牌与口碑决定下载。” —— **Zara Zhang**（AI内容创作者）[原文](https://x.com/zarazhangrui/status/2023870703716696429)

- “AI原生=从prompt升级到skill；持续叠加的自定义工作流才是高阶用法。” —— **Peter Yang**（产品负责人）归纳Factory.ai联创访谈[原文](https://x.com/petergyang/status/2023422563612025095)

- “别空谈AI，先把自己埋进工具里天天用；没 relentless 用过就没有发言权。” —— **Riley Brown**（vibe coding教育者）[原文](https://x.com/rileybrown/status/2023806044699586704)

- “评估（evals）是AI产品快速迭代的核心；招人就让他们带一份自己引以为傲的eval作品。” —— **Cat Wu**（Anthropic Claude Code产品负责人）[原文](https://x.com/_catwu/status/2023966387300110629)

- “欧洲议会全面禁用生成式AI应用，怕的是数据流向美国服务器——地缘数据主权优先于效率。” —— **TechCrunch**评欧盟设备封禁[原文](https://techcrunch.com/2026/02/17/european-parliament-blocks-ai-on-lawmakers-devices-citing-security-risks/)

## 🔧 产品动态

- **WordPress.com上线AI助理**：在后台侧边栏用自然语言就能改文字、调样式、一键生图，无需手动折腾区块编辑器。[来源](https://techcrunch.com/2026/02/17/wordpress-com-adds-an-ai-assistant-that-can-edit-adjust-styles-create-images-and-more/)

- **Figma × Claude Code双向打通**：可把Claude Code生成的UI直接导入Figma变成可编辑帧，设计-代码循环缩到一句话。[来源](https://x.com/trq212/status/2023797194017706290)

- **NotebookLM推出“提示式修订”**：Premium用户可在生成简报后，用自然语言让AI增删幻灯片、换配图、调叙事顺序。[来源](https://x.com/joshwoodward/status/2023882859183042634)

- **Replit给所有用户原生云隔离**：每个Repl默认跑在独立容器，安全与性能 baseline 直接对齐企业级。[来源](https://x.com/amasad/status/2023536371605151801)

- **Mistral收购Koyeb**：拿下无服务器部署平台，补齐“模型- infra -应用”全栈，对标OpenAI+微软生态。[来源](https://techcrunch.com/2026/02/17/mistral-ai-buys-koyeb-in-first-acquisition-to-back-its-cloud-ambitions/)

- **印度Sarvam发布30B/105B开源多模态系列+边缘TTS/ASR模型**：最小体积以MB计，目标跑在功能机、车载与智能眼镜。[来源](https://techcrunch.com/2026/02/18/indian-ai-lab-sarvams-new-models-are-a-major-bet-on-the-viability-of-open-source-ai/)

- **Perplexity宣布暂缓广告变现**：担心“带商业目的的答案”损害用户信任，先靠订阅续命。[来源](https://www.theverge.com/ai-artificial-intelligence/880562/perplexity-ditches-ai-ads)

- **Google搜索AI模式新增“悬停源链接弹窗”**：鼠标指向摘要即可展开来源与完整链接，缓解“AI不引用”争议。[来源](https://www.theverge.com/tech/880475/google-ai-overviews-ai-mode-links-update)

- **Google I/O 2026定档5月19-20日**：官方预告将集中发布Gemini、Android等全线AI更新。[来源](https://www.theverge.com/tech/880401/google-io-2026-dates-ai)

- **World Labs获Autodesk 2亿美元B轮**：把“世界模型”塞进3D娱乐工作流，先攻影视与游戏场景。[来源](https://techcrunch.com/2026/02/18/world-labs-lands-200m-from-autodesk-to-bring-world-models-into-3d-workflows/)

## 📎 也值得一看

- **OpenClaw技能生态62K+**：Vercel联手Socket、Snyk等持续审计，安全门槛随规模同步抬高。[来源](https://x.com/rauchg/status/2023880088564232665)

- **Spotify CEO在财报点名Claude Code**：内部已把“写spec→自动实现”做成标准流程，AI编程进入大厂KPI。[来源](https://x.com/_catwu/status/2023972220377145422)

- **Y Combinator周六黑客马拉松最后名额**：优胜者直通YC面试，现场送出最后几台Mac mini。[来源](https://x.com/garrytan/status/2023847417951756295)

- **Google.org发起“AI for Science”挑战**：面向全球科研组织开放资助，重点砸向可扩展的AI科学发现项目。[来源](https://blog.google/company-news/outreach-and-initiatives/google-org/impact-challenge-ai-science-open-call/)

- **Cohere推出Tiny Aya多语言模型家族**：70+语言、全部开源，主打低算力场景下的多语理解与生成。[来源](https://techcrunch.com/2026/02/17/cohere-launches-a-family-of-open-multilingual-models/)

- **SpaceX老兵创企Mesh融资5000万美元**：量产数据中心光互连，瞄准AI集群对高带宽、低延迟的饥渴需求。[来源](https://techcrunch.com/2026/02/17/spacex-vets-raise-50m-series-a-for-data-center-links/)