# Omphalina 故事线数据 — 第二层：LLM 创作层

> 内容：Schema 定义 + 7 化合物故事线 YAML + 跨化合物连接 + 因果图摘要
> 用途：叙事引擎的结构化骨架，每条因果边带有 drama_score 和 irony_level 评分

---

# PART 1: 数据结构定义 (Schema)

```yaml
# Omphalina 故事线 Schema 定义
# 本文件定义故事线 YAML 的数据结构规范
# 所有 storylines/compounds/*.yaml 文件必须符合此 Schema

# ============================================================
# 节点类型定义
# ============================================================

node_types:

  Compound:
    description: "人造化合物实体"
    required_fields:
      - id            # string | 唯一标识符，如 "aspirin"
      - name_zh       # string | 中文名
      - name_en       # string | 英文名
      - aliases_zh    # list[string] | 中文别名，用于用户识别
      - category      # string | 分类，如 "药物", "农药", "材料"
      - year_invented # int | 发明/发现年份
    optional_fields:
      - formula       # string | 化学式
      - cas_number    # string | CAS 注册号
      - safety_note   # string | 安全说明（必须强调不提供合成方法）

  Person:
    description: "与化合物历史相关的关键人物"
    required_fields:
      - id            # string | 唯一标识符，如 "fritz_haber"
      - name_zh       # string | 中文名
      - name_en       # string | 英文名
      - role          # string | 角色/身份
    optional_fields:
      - birth_year    # int
      - death_year    # int
      - nationality   # string
      - nobel_year    # int | 获诺贝尔奖年份（如适用）
      - irony_note    # string | 此人身上的讽刺性注释

  Event:
    description: "与化合物相关的历史事件"
    required_fields:
      - id            # string | 唯一标识符
      - name_zh       # string | 中文事件名
      - name_en       # string | 英文事件名
      - year          # int | 事件年份
      - domain        # string | 领域: 战争/农业/医学/环保/法律/文化/科学/工业
    optional_fields:
      - end_year      # int | 事件结束年份（如跨多年）
      - location      # string | 地点
      - scale         # string | 规模: 个人/国家/区域/全球
      - quote         # string | 可引用的名言或名场面描述
      - source_ref    # string | 出处引注（对应 encyclopedia/ 中的文件和章节）

  Consequence:
    description: "事件的后果或涟漪效应"
    required_fields:
      - id            # string | 唯一标识符
      - description_zh # string | 中文描述
      - description_en # string | 英文描述
      - type          # string | 类型: 正面/负面/双刃/讽刺
      - domain        # string | 影响领域
    optional_fields:
      - scale         # string | 规模
      - ongoing       # bool | 是否仍在持续
      - quantifier    # string | 量化描述（如 "影响40亿人"）


# ============================================================
# 边类型定义（因果关系）
# ============================================================

edge_types:

  INVENTED_BY:
    description: "化合物由某人发明/发现"
    source_type: Compound
    target_type: Person
    attributes:
      - year          # int | 发明年份
      - context       # string | 发明背景

  ENABLED:
    description: "化合物使某事件成为可能"
    source_type: Compound
    target_type: Event
    attributes:
      - drama_score   # float 0-1 | 戏剧性评分
      - irony_level   # float 0-1 | 讽刺性评分
      - time_lag_years # int | 从化合物发明到事件发生的时间差
      - domains       # list[string] | 涉及的领域
      - description_zh # string | 因果关系中文描述
      - description_en # string | 因果关系英文描述

  CAUSED:
    description: "事件导致了某后果"
    source_type: Event
    target_type: Consequence
    attributes:
      - drama_score   # float 0-1
      - irony_level   # float 0-1
      - domains       # list[string]
      - description_zh # string

  IRONIC_TWIST:
    description: "反讽因果链——后果导致了与初衷相反的新后果"
    source_type: Consequence
    target_type: Consequence
    attributes:
      - drama_score   # float 0-1
      - irony_level   # float 0-1
      - description_zh # string

  DERIVED_FROM:
    description: "化合物之间的衍生关系"
    source_type: Compound
    target_type: Compound
    attributes:
      - relationship  # string | 关系描述

  CONTEMPORANEOUS:
    description: "同时期发生的相关事件"
    source_type: Event
    target_type: Event
    attributes:
      - relationship  # string | 关系说明


# ============================================================
# 评分体系
# ============================================================

scoring:

  drama_score:
    description: "衡量一个因果关系的戏剧性程度 (0.0 - 1.0)"
    dimensions:
      - name: scale
        weight: 0.30
        description: "影响规模——波及多少人/面积/产业？"
      - name: surprise
        weight: 0.25
        description: "意外性——结果是否出人意料？"
      - name: cross_domain
        weight: 0.20
        description: "跨领域度——影响跨越了几个领域？"
      - name: time_span
        weight: 0.15
        description: "时间跨度——因果链跨越多少年？"
      - name: quotability
        weight: 0.10
        description: "可引用性——是否有著名引语或名场面？"

  irony_level:
    description: "衡量一个因果关系的讽刺性程度 (0.0 - 1.0)"
    dimensions:
      - name: purpose_reversal
        weight: 0.40
        description: "目的反转——初衷与结果的反差程度"
      - name: same_agent
        weight: 0.30
        description: "同一主体——同一人/组织同时造成正面和负面结果？"
      - name: hindsight_irony
        weight: 0.20
        description: "事后讽刺——回头看有多讽刺？"
      - name: narrative_tension
        weight: 0.10
        description: "叙事张力——放进故事里能产生多强的效果？"


# ============================================================
# 跨化合物连接
# ============================================================

cross_connection:
  description: "描述两个化合物之间的关联关系"
  required_fields:
    - source_compound   # string | 源化合物 id
    - target_compound   # string | 目标化合物 id
    - relationship_zh   # string | 中文关系描述
    - relationship_en   # string | 英文关系描述
    - connection_type   # string | 连接类型（见下）
  connection_types:
    - "同属双用途"       # 如合成氨(化肥/炸药)、DDT(农药/军用)
    - "同一发明者"       # 如含铅汽油和氟利昂（Midgley）
    - "先追捧后质疑"     # 如味精、DDT
    - "环保危机系列"     # 如塑料污染、臭氧层空洞
    - "药物范式对比"     # 如阿司匹林(化学合成) vs 青霉素(生物发现)
    - "诺贝尔讽刺"       # 如多个获奖发明后来造成灾难
    - "战争催化"         # 如二战推动了青霉素量产和DDT使用


# ============================================================
# 安全护栏
# ============================================================

safety:
  required_in_every_compound:
    - safety_note: "本条目仅讨论历史和社会影响，不涉及合成方法或配方"
  
  forbidden_content:
    - "合成步骤或反应条件"
    - "精确配比或浓度数据"
    - "实验操作流程"
    - "原料采购渠道"
  
  guardrail_note: >
    query_engine.py 在生成 Gemini prompt 时，
    必须包含系统指令禁止输出任何合成方法相关内容。
    这是架构层面的安全设计。

```

---

# PART 2: 化合物故事线 (7 篇)


================================================================================
## 故事线：aspirin
================================================================================

```yaml
# 阿司匹林故事线 — 基于 encyclopedia/compounds/aspirin.md 提取
# 戏剧性历史节点 + 因果网络 + 评分

compound:
  id: aspirin
  name_zh: 阿司匹林
  name_en: Aspirin (Acetylsalicylic Acid)
  aliases_zh: [阿司匹林, 阿斯匹灵, 乙酰水杨酸]
  category: 药物
  year_invented: 1897
  formula: C₉H₈O₄
  cas_number: "50-78-2"
  safety_note: "本条目仅讨论历史和社会影响，不涉及合成方法或配方"

  people:
    - id: felix_hoffmann
      name_zh: 费利克斯·霍夫曼
      name_en: Felix Hoffmann
      role: 拜耳化学家，1897年合成纯化乙酰水杨酸
      nationality: 德国
      year: 1897
      irony_note: "同一个人在两周内合成了阿司匹林和海洛因——一个救人，一个毁人"

    - id: arthur_eichengruen
      name_zh: 阿图尔·艾兴格林
      name_en: Arthur Eichengrün
      role: 拜耳研究主管，声称是阿司匹林真正的推动者
      nationality: 德国（犹太裔）
      irony_note: "纳粹时期被关入集中营，功劳被归于'雅利安人'霍夫曼"

    - id: hippocrates
      name_zh: 希波克拉底
      name_en: Hippocrates
      role: 古希腊医学之父，公元前400年记录柳树皮止痛
      birth_year: -460
      death_year: -370

    - id: john_vane
      name_zh: 约翰·罗伯特·韦恩
      name_en: John Robert Vane
      role: 发现阿司匹林抑制前列腺素的机制
      nobel_year: 1982
      nationality: 英国

  events:
    - id: willow_bark_ancient
      name_zh: 柳树皮药用的古老历史——从苏美尔到希波克拉底
      name_en: Ancient use of willow bark as medicine
      year: -2400
      end_year: -400
      domain: 医学
      scale: 区域
      quote: "公元前2400年的苏美尔泥板已记录柳树皮的止痛用途"
      source_ref: "encyclopedia/compounds/aspirin.md ## 发现与早期历史"

    - id: bayer_synthesis_1897
      name_zh: 拜耳公司实验室合成阿司匹林
      name_en: Bayer synthesizes aspirin
      year: 1897
      domain: 工业
      scale: 全球
      location: 德国伍珀塔尔
      quote: "霍夫曼在两周内先后合成了阿司匹林和海洛因"

    - id: bayer_heroin_same_lab
      name_zh: 同一实验室、同一时期合成海洛因
      name_en: Heroin synthesized in same Bayer lab
      year: 1898
      domain: 医学
      scale: 全球
      quote: "拜耳将海洛因作为'不上瘾的吗啡替代品'销售"

    - id: aspirin_trademark_lost
      name_zh: 一战后拜耳失去"Aspirin"美国商标
      name_en: Bayer loses Aspirin trademark in US after WWI
      year: 1919
      domain: 法律
      scale: 国家
      location: 美国
      quote: "作为凡尔赛条约战争赔偿的一部分，Aspirin在美国变为通用名"

    - id: reye_syndrome_warning
      name_zh: 发现儿童使用阿司匹林与瑞氏综合征的关联
      name_en: Link between aspirin and Reye's syndrome in children
      year: 1963
      domain: 医学
      scale: 全球
      quote: "最安全的药物之一被发现对儿童可能致命"

    - id: vane_mechanism_discovery
      name_zh: 韦恩发现阿司匹林抑制前列腺素的机制
      name_en: Vane discovers aspirin inhibits prostaglandin synthesis
      year: 1971
      domain: 科学
      scale: 全球
      quote: "使用了70年后，人类才搞清楚这个药到底是怎么起作用的"

    - id: heart_attack_prevention
      name_zh: 低剂量阿司匹林被发现可预防心脏病
      name_en: Low-dose aspirin for heart attack prevention
      year: 1988
      domain: 医学
      scale: 全球
      quote: "止痛药变身心血管救星"

  consequences:
    - id: aspirin_global_consumption
      description_zh: 全球每年消费超过1000亿片阿司匹林
      description_en: Over 100 billion aspirin tablets consumed annually worldwide
      type: 正面
      domain: 医学
      scale: 全球
      ongoing: true
      quantifier: "1000亿片/年"

    - id: heroin_epidemic
      description_zh: 海洛因（同一实验室产物）引发全球成瘾危机
      description_en: Heroin (from same lab) caused global addiction crisis
      type: 讽刺
      domain: 社会
      scale: 全球
      ongoing: true

    - id: eichengruen_erasure
      description_zh: 犹太科学家艾兴格林的贡献被纳粹抹去
      description_en: Jewish scientist Eichengrün's contribution erased by Nazis
      type: 讽刺
      domain: 文化
      scale: 个人

    - id: reye_children_deaths
      description_zh: 儿童因服用阿司匹林引发瑞氏综合征死亡
      description_en: Children died from Reye's syndrome linked to aspirin
      type: 负面
      domain: 医学
      scale: 全球

  causal_chains:
    # 化合物 → 事件
    - source: aspirin
      target: willow_bark_ancient
      type: ENABLED
      drama_score: 0.70
      irony_level: 0.30
      description_zh: "4400年的药用史——人类最古老的药物之一"
      description_en: "4400 years of medicinal use"
      domains: [医学, 历史]

    - source: aspirin
      target: bayer_synthesis_1897
      type: ENABLED
      drama_score: 0.80
      irony_level: 0.60
      description_zh: "工业化学让古老的柳树皮智慧变成小药片"
      domains: [化学工业, 医学]

    - source: aspirin
      target: bayer_heroin_same_lab
      type: ENABLED
      drama_score: 0.95
      irony_level: 0.98
      description_zh: "同一个化学家、同一间实验室、相隔两周：一个成为人类最常用的药物，一个成为最臭名昭著的毒品"
      description_en: "Same chemist, same lab, two weeks apart: one became humanity's most used medicine, the other its most infamous drug"
      domains: [化学工业, 医学, 社会]
      time_lag_years: 1

    - source: aspirin
      target: aspirin_trademark_lost
      type: ENABLED
      drama_score: 0.75
      irony_level: 0.70
      description_zh: "战争让一个商标名变成了通用名——拜耳在美国永远失去了'Aspirin'"
      domains: [法律, 战争]
      time_lag_years: 22

    - source: aspirin
      target: reye_syndrome_warning
      type: ENABLED
      drama_score: 0.85
      irony_level: 0.80
      description_zh: "最安全的成人药物之一，却可能杀死儿童"
      domains: [医学]
      time_lag_years: 66

    - source: aspirin
      target: vane_mechanism_discovery
      type: ENABLED
      drama_score: 0.80
      irony_level: 0.65
      description_zh: "全世界吃了70年才搞清楚它为什么有效"
      domains: [科学, 医学]
      time_lag_years: 74

    - source: aspirin
      target: heart_attack_prevention
      type: ENABLED
      drama_score: 0.85
      irony_level: 0.50
      description_zh: "一个止痛药意外地成了心脏病的救星"
      domains: [医学, 科学]
      time_lag_years: 91

    # 事件 → 后果
    - source: bayer_heroin_same_lab
      target: heroin_epidemic
      type: CAUSED
      drama_score: 0.98
      irony_level: 0.99
      description_zh: "拜耳将海洛因作为'不上瘾的吗啡替代品'推向市场——史上最大的医学营销灾难之一"
      domains: [医学, 社会]

    - source: bayer_synthesis_1897
      target: eichengruen_erasure
      type: CAUSED
      drama_score: 0.80
      irony_level: 0.90
      description_zh: "纳粹政权将犹太科学家的贡献从历史中抹去，功劳归于'雅利安人'"
      domains: [文化, 政治]

    - source: reye_syndrome_warning
      target: reye_children_deaths
      type: CAUSED
      drama_score: 0.85
      irony_level: 0.80
      description_zh: "被认为最安全的药竟然成为儿童的威胁"
      domains: [医学]

    # 讽刺反转链
    - source: heroin_epidemic
      target: aspirin_global_consumption
      type: IRONIC_TWIST
      drama_score: 0.90
      irony_level: 0.95
      description_zh: "同一间实验室的双胞胎——一个每年被消费1000亿片，另一个被全球禁止"

  cross_connections:
    - target_compound: penicillin
      relationship_zh: "药物发现的两种范式：化学合成 vs 生物发现"
      connection_type: 药物范式对比

```

---


================================================================================
## 故事线：synthetic_ammonia
================================================================================

```yaml
# 合成氨故事线 — 基于 encyclopedia/compounds/synthetic_ammonia.md 提取
# 戏剧性历史节点 + 因果网络 + 评分

compound:
  id: synthetic_ammonia
  name_zh: 合成氨 (哈伯法)
  name_en: Synthetic Ammonia (Haber-Bosch Process)
  aliases_zh: [合成氨, 哈伯法, 哈伯-博施法]
  category: 工业化学
  year_invented: 1909
  formula: N₂ + 3H₂ → 2NH₃
  safety_note: "本条目仅讨论历史和社会影响，不涉及合成方法或配方"

  people:
    - id: fritz_haber
      name_zh: 弗里茨·哈伯
      name_en: Fritz Haber
      role: 合成氨实验室发明者，化学武器之父
      nationality: 德国（犹太裔）
      year: 1909
      nobel_year: 1918
      irony_note: "喂养了40亿人口，也主导了化学武器——妻子因此自杀，自己因犹太身份被纳粹流放"

    - id: carl_bosch
      name_zh: 卡尔·博施
      name_en: Carl Bosch
      role: 将实验室工艺放大到工业规模的工程师
      nationality: 德国
      year: 1913
      nobel_year: 1931
      irony_note: "缔造了BASF帝国，却在纳粹时代因反对排犹而失势，酗酒抑郁而终"

    - id: clara_immerwahr
      name_zh: 克拉拉·伊默瓦尔
      name_en: Clara Immerwahr
      role: 哈伯之妻，德国第一位女性化学博士
      nationality: 德国
      year: 1915
      irony_note: "坚决反对丈夫参与化学武器研发，在伊普尔毒气攻击庆功宴当晚用丈夫的军用手枪自杀"

    - id: gerhard_ertl
      name_zh: 格哈德·埃特尔
      name_en: Gerhard Ertl
      role: 解析了哈伯法催化机制的表面化学家
      nationality: 德国
      nobel_year: 2007
      irony_note: "将近一百年后，人类才真正理解这个喂养了全世界的反应在催化剂表面是怎么发生的"

  events:
    - id: nitrogen_crisis_1900
      name_zh: 二十世纪初的氮素危机——即将耗尽的智利硝石
      name_en: Early 20th century nitrogen crisis — dwindling Chilean saltpeter
      year: 1898
      end_year: 1910
      domain: 农业
      scale: 全球
      quote: "科学家警告：若不能从空气中固氮，全球粮食供应将在数十年内崩溃"
      source_ref: "encyclopedia/compounds/synthetic_ammonia.md ## History"

    - id: haber_lab_demo_1909
      name_zh: 哈伯在实验室以每小时125毫升的速度从空气中制氨
      name_en: Haber demonstrates lab-scale ammonia synthesis
      year: 1909
      domain: 科学
      scale: 全球
      location: 德国卡尔斯鲁厄
      quote: "他们从空气中一滴一滴地'挤'出了氨水——人类第一次驯服了最稳定的三键"

    - id: basf_industrial_1913
      name_zh: BASF奥堡工厂实现工业化量产
      name_en: BASF Oppau plant begins industrial-scale production
      year: 1913
      domain: 工业
      scale: 全球
      location: 德国奥堡
      quote: "1914年日产20吨氨——从实验室的125毫升到工厂的20吨，博施完成了人类工程史上最壮观的放大"

    - id: wwi_munitions
      name_zh: 合成氨拯救德国战争机器——无它德国数月内必败
      name_en: Synthetic ammonia sustains Germany's WWI war effort
      year: 1914
      end_year: 1918
      domain: 军事
      scale: 全球
      quote: "历史学家普遍认为，没有哈伯法，被封锁了硝石进口的德国将在几个月内因弹药耗尽而投降"
      source_ref: "encyclopedia/compounds/synthetic_ammonia.md ## History"

    - id: chemical_weapons_ypres
      name_zh: 哈伯亲赴前线指挥伊普尔毒气攻击
      name_en: Haber personally directs chlorine gas attack at Ypres
      year: 1915
      domain: 军事
      scale: 全球
      location: 比利时伊普尔
      quote: "这位将来的诺贝尔奖得主亲自站在战壕前，观看6000个氯气钢瓶释放的绿色烟云吞噬协约国士兵"

    - id: clara_suicide
      name_zh: 克拉拉在毒气攻击庆功宴后举枪自杀
      name_en: Clara Immerwahr's suicide after Ypres celebration
      year: 1915
      domain: 个人
      scale: 个人
      location: 德国柏林
      quote: "她用丈夫的军用手枪在自家花园射杀了自己——被12岁的儿子发现。次日清晨，哈伯照常出发前往东线"

    - id: haber_nobel_1918
      name_zh: 哈伯获1918年诺贝尔化学奖——引发巨大争议
      name_en: Haber awarded 1918 Nobel Prize in Chemistry amid outrage
      year: 1918
      domain: 科学
      scale: 全球
      quote: "协约国科学家联合抗议：一个'化学武器之父'怎么能获得诺贝尔奖？"

    - id: haber_nazi_exile
      name_zh: 纳粹上台后哈伯因犹太身份被迫流亡
      name_en: Haber forced into exile by Nazi racial laws
      year: 1933
      domain: 政治
      scale: 个人
      location: 德国 → 英国 → 瑞士
      quote: "他为德国发明了养活全国的化肥和赢得战争的弹药，但德国以民族的名义将他驱逐出境"

    - id: zyklon_b_irony
      name_zh: 哈伯的杀虫剂研究成果被改造为Zyklon B
      name_en: Haber's pesticide research adapted into Zyklon B
      year: 1942
      domain: 军事
      scale: 全球
      quote: "哈伯1920年代研发的Zyklon杀虫剂被纳粹改良为Zyklon B——用于毒杀集中营囚犯，包括哈伯自己的亲属"

  consequences:
    - id: feeds_four_billion
      description_zh: 合成氨化肥养活了全球约一半人口（~40亿人）
      description_en: Synthetic ammonia fertilizers feed roughly half the world's population (~4 billion)
      type: 正面
      domain: 农业
      scale: 全球
      ongoing: true
      quantifier: "~40亿人"

    - id: nitrogen_pollution_dead_zones
      description_zh: 过量氮肥流入水体造成全球400+个海洋死区
      description_en: Excess nitrogen fertilizer creates 400+ marine dead zones worldwide
      type: 负面
      domain: 环境
      scale: 全球
      ongoing: true
      quantifier: "400+个死区"

    - id: carbon_emissions_ammonia
      description_zh: 全球氨生产占全球碳排放约3%、能源消耗1-2%
      description_en: Ammonia production accounts for ~3% of global carbon emissions
      type: 负面
      domain: 环境
      scale: 全球
      ongoing: true
      quantifier: "全球碳排放3%"

    - id: clara_legacy_feminism
      description_zh: 克拉拉成为反战与女性科学家抗争的象征
      description_en: Clara Immerwahr became a symbol of anti-war resistance and women in science
      type: 讽刺
      domain: 文化
      scale: 全球

  causal_chains:
    # 化合物 → 事件
    - source: synthetic_ammonia
      target: nitrogen_crisis_1900
      type: ENABLED
      drama_score: 0.75
      irony_level: 0.20
      description_zh: "全球粮食安全危机催生了固氮研究的紧迫需求"
      domains: [农业, 科学]

    - source: synthetic_ammonia
      target: haber_lab_demo_1909
      type: ENABLED
      drama_score: 0.85
      irony_level: 0.30
      description_zh: "从空气中每小时滴出125毫升氨——人类首次打破了最稳定的化学键之一"
      domains: [化学, 工业]

    - source: synthetic_ammonia
      target: basf_industrial_1913
      type: ENABLED
      drama_score: 0.80
      irony_level: 0.25
      description_zh: "博施将实验室的桌面装置放大十万倍——工程史上最惊人的scale-up之一"
      domains: [工程, 工业]
      time_lag_years: 4

    - source: synthetic_ammonia
      target: wwi_munitions
      type: ENABLED
      drama_score: 0.95
      irony_level: 0.90
      description_zh: "本为解决饥荒的发明，却成了延长战争数年的军事关键——没有合成氨，一战可能在1915年就结束了"
      description_en: "Invention meant to end famine instead prolonged WWI by years"
      domains: [军事, 化学工业]
      time_lag_years: 5

    - source: fritz_haber
      target: chemical_weapons_ypres
      type: ENABLED
      drama_score: 0.95
      irony_level: 0.95
      description_zh: "喂养了亿万人的科学家亲手将科学变成了大规模屠杀工具"
      domains: [军事, 科学伦理]

    - source: chemical_weapons_ypres
      target: clara_suicide
      type: CAUSED
      drama_score: 0.98
      irony_level: 0.95
      description_zh: "妻子无法接受丈夫的科学成就被用于屠杀，在庆功宴当晚选择了死亡——而丈夫次日照常出发"
      domains: [个人, 伦理]

    - source: synthetic_ammonia
      target: haber_nobel_1918
      type: ENABLED
      drama_score: 0.90
      irony_level: 0.92
      description_zh: "'化学武器之父'因'造福人类'获得诺贝尔奖——科学界最具争议的授奖之一"
      domains: [科学, 伦理]
      time_lag_years: 9

    - source: haber_nazi_exile
      target: zyklon_b_irony
      type: IRONIC_TWIST
      drama_score: 0.99
      irony_level: 1.00
      description_zh: "哈伯自己研发的杀虫剂被改造成毒杀他同胞的工具——几乎无法想象更残酷的讽刺"
      description_en: "Haber's own pesticide research was adapted to murder his own people"
      domains: [军事, 种族灭绝, 科学伦理]
      time_lag_years: 9

    # 事件 → 后果
    - source: basf_industrial_1913
      target: feeds_four_billion
      type: CAUSED
      drama_score: 0.90
      irony_level: 0.60
      description_zh: "工业化合成氨使全球人口从18亿增长到80亿成为可能——人类史上影响最大的化学发明"
      domains: [农业, 人口]

    - source: feeds_four_billion
      target: nitrogen_pollution_dead_zones
      type: IRONIC_TWIST
      drama_score: 0.85
      irony_level: 0.85
      description_zh: "养活半个地球的同时毒杀了海洋——氮肥流入河流，催生了400+个'死区'"
      domains: [环境, 农业]

    - source: feeds_four_billion
      target: carbon_emissions_ammonia
      type: IRONIC_TWIST
      drama_score: 0.75
      irony_level: 0.70
      description_zh: "养活人类的同时加速气候变化——氨生产占全球能耗1-2%"
      domains: [环境, 能源]

    - source: clara_suicide
      target: clara_legacy_feminism
      type: IRONIC_TWIST
      drama_score: 0.80
      irony_level: 0.75
      description_zh: "一位被历史遗忘的女科学家的自杀，一个世纪后成为反战与女权叙事的符号"
      domains: [文化, 性别]

  cross_connections:
    - target_compound: ddt
      relationship_zh: "同属双用途：农业/军事的双面刃"
      connection_type: 同属双用途

    - target_compound: cfc
      relationship_zh: "三个争议性诺贝尔奖的讽刺链"
      connection_type: 诺贝尔讽刺

    - target_compound: aspirin
      relationship_zh: "同一时代的德国化学工业双子星，一个救人一个也杀人"
      connection_type: 德国化学工业

```

---


================================================================================
## 故事线：plastics
================================================================================

```yaml
# 塑料故事线 — 基于 encyclopedia/compounds/plastics.md 提取
# 戏剧性历史节点 + 因果网络 + 评分

compound:
  id: plastics
  name_zh: 塑料
  name_en: Plastics
  aliases_zh: [塑料, 塑膠, 合成高分子]
  category: 合成材料
  year_invented: 1907
  formula: "(各种聚合物)"
  safety_note: "本条目仅讨论历史和社会影响，不涉及合成方法或化学配方"

  people:
    - id: leo_baekeland
      name_zh: 利奥·贝克兰
      name_en: Leo Baekeland
      role: 发明了世界上第一种全合成塑料"电木"(Bakelite)，并创造了"塑料"一词
      nationality: 比利时/美国
      year: 1907
      irony_note: "他创造了'plastics'这个词——如今这个词既代表'现代奇迹'也代表'环境灾难'"

    - id: alexander_parkes
      name_zh: 亚历山大·帕克斯
      name_en: Alexander Parkes
      role: 1855年发明赛璐珞(Parkesine)——第一种人造塑料
      nationality: 英国
      year: 1855
      irony_note: "赛璐珞最初被用来模仿象牙——一种为拯救大象而生的材料，最终制造了远超象牙的环境危机"

    - id: hermann_staudinger
      name_zh: 赫尔曼·施陶丁格
      name_en: Hermann Staudinger
      role: '"高分子化学之父"，证明了聚合物是真正的大分子'
      nationality: 德国
      year: 1920
      nobel_year: 1953
      irony_note: "在同行嘲笑他的理论几十年后获得了诺贝尔奖"

    - id: giulio_natta
      name_zh: 朱利奥·纳塔
      name_en: Giulio Natta
      role: 发现了聚丙烯的等规聚合法
      nationality: 意大利
      year: 1954
      nobel_year: 1963
      irony_note: "他的发明使塑料包装变得廉价到可以随手丢弃——这恰恰导致了全球塑料污染"

  events:
    - id: parkesine_1855
      name_zh: 帕克斯发明赛璐珞——第一种人造塑料
      name_en: Parkes invents Parkesine — first man-made plastic
      year: 1855
      domain: 化学
      scale: 国家
      location: 英国
      quote: "用硝酸处理纤维素，可以塑造成仿象牙——1862年伦敦国际博览会上获铜奖"
      source_ref: "encyclopedia/compounds/plastics.md ## History"

    - id: bakelite_1907
      name_zh: 贝克兰发明电木(Bakelite)——世界第一种全合成塑料
      name_en: Baekeland invents Bakelite — world's first fully synthetic plastic
      year: 1907
      domain: 化学/工业
      scale: 全球
      location: 美国纽约
      quote: "贝克兰不仅发明了电木，还创造了'plastics'这个词——由此开启了塑料时代"

    - id: polyethylene_accident_1933
      name_zh: ICI实验室意外发现聚乙烯——一个实验事故改变了世界
      name_en: ICI researchers accidentally discover polyethylene
      year: 1933
      domain: 化学
      scale: 全球
      location: 英国
      quote: "Reginald Gibson和Eric Fawcett的一个'失败的'高压实验，意外产生了如今产量最大的塑料"

    - id: nylon_and_mass_production_1940s
      name_zh: 二战后塑料大爆发——尼龙、聚苯乙烯、PVC进入千家万户
      name_en: Post-WWII plastic explosion — nylon, PS, PVC enter everyday life
      year: 1940
      end_year: 1960
      domain: 工业
      scale: 全球
      quote: "从军需品到消费品，塑料用量在1940-1960年间爆发式增长"

    - id: polypropylene_1954
      name_zh: 纳塔发现聚丙烯——使廉价一次性包装成为可能
      name_en: Natta discovers polypropylene — enabling disposable packaging
      year: 1954
      domain: 化学/工业
      scale: 全球
      location: 意大利
      quote: "聚丙烯使塑料包装变得如此便宜，以至于人类开始把包装当作'用完就扔'"

    - id: production_milestone_9_billion
      name_zh: 1950-2017年人类共生产92亿吨塑料
      name_en: 9.2 billion tonnes of plastic produced between 1950-2017
      year: 2017
      domain: 工业
      scale: 全球
      quote: "92亿吨——其中超过一半是2004年以后生产的。仅9%被回收，12%被焚烧，79%在垃圾场或自然环境中"

    - id: great_pacific_garbage_patch
      name_zh: 太平洋垃圾带——海洋塑料污染的象征
      name_en: Great Pacific Garbage Patch — symbol of marine plastic pollution
      year: 1997
      domain: 环境
      scale: 全球
      location: 太平洋
      quote: "海洋垃圾中50%-80%是塑料——形成了面积比法国还大的垃圾漂浮带"

    - id: microplastics_discovery
      name_zh: 微塑料被发现无处不在——食物链、人体血液、北极冰层
      name_en: Microplastics found everywhere — food chain, human blood, Arctic ice
      year: 2004
      end_year: 2026
      domain: 环境/健康
      scale: 全球
      quote: "1960年代首次在海鸟肠道中发现微塑料，如今在人体血液、胎盘和北极冰芯中都检测到了"

    - id: plasticosis_2023
      name_zh: '发现新疾病"塑料病"——海鸟因吞食塑料导致消化道纤维化'
      name_en: '"Plasticosis" discovered — new disease in seabirds from plastic ingestion'
      year: 2023
      domain: 生态
      scale: 全球
      quote: "2023年，科学家在海鸟体内发现了一种全新的疾病——因持续吞食塑料碎片导致消化道永久性纤维化"

    - id: global_plastic_treaty_negotiations
      name_zh: 联合国启动全球塑料公约谈判
      name_en: UN begins negotiations for global plastics treaty
      year: 2022
      end_year: 2025
      domain: 国际法
      scale: 全球
      quote: "2025年，历史上首次几乎所有国家不仅讨论回收，还讨论减产——因为塑料占全球碳排放3-5%"

  consequences:
    - id: modern_life_transformation
      description_zh: 塑料彻底改变了现代生活——从医疗器械到建筑材料到食品包装
      description_en: Plastics fundamentally transformed modern life
      type: 正面
      domain: 工业/社会
      scale: 全球
      ongoing: true
      quantifier: "全球年产4亿+吨"

    - id: ocean_plastic_crisis
      description_zh: 每年800-1200万吨塑料入海，形成海洋生态灾难
      description_en: 8-12 million tonnes of plastic enter oceans annually
      type: 负面
      domain: 环境
      scale: 全球
      ongoing: true
      quantifier: "年入海800-1200万吨"

    - id: microplastic_health_threat
      description_zh: 微塑料进入食物链和人体，长期健康影响尚不明确
      description_en: Microplastics enter food chain and human bodies — long-term effects unknown
      type: 负面
      domain: 健康/环境
      scale: 全球
      ongoing: true

    - id: recycling_failure
      description_zh: 全球塑料仅9%被回收——回收神话与现实的巨大鸿沟
      description_en: Only ~9% of all plastic ever produced has been recycled
      type: 讽刺
      domain: 环境
      scale: 全球
      ongoing: true
      quantifier: "仅9%"

  causal_chains:
    # 化合物 → 事件
    - source: plastics
      target: parkesine_1855
      type: ENABLED
      drama_score: 0.60
      irony_level: 0.55
      description_zh: "为模仿象牙而生的材料——一个拯救大象的初衷，最终制造了远超象牙贸易的环境危机"
      domains: [化学, 环境]

    - source: plastics
      target: bakelite_1907
      type: ENABLED
      drama_score: 0.80
      irony_level: 0.50
      description_zh: "世界上第一种完全由化学家从零创造的材料——人类从此可以'设计'物质"
      domains: [化学, 工业]

    - source: plastics
      target: polyethylene_accident_1933
      type: ENABLED
      drama_score: 0.85
      irony_level: 0.70
      description_zh: "如今产量最大的塑料诞生于一个'失败的'实验——科学史上又一个改变世界的意外"
      description_en: "The world's most produced plastic was born from a 'failed' experiment"
      domains: [化学, 工业]

    - source: plastics
      target: nylon_and_mass_production_1940s
      type: ENABLED
      drama_score: 0.75
      irony_level: 0.40
      description_zh: "二战推动了塑料从实验室新奇事物到工业必需品的转变"
      domains: [工业, 军事]

    - source: plastics
      target: polypropylene_1954
      type: ENABLED
      drama_score: 0.70
      irony_level: 0.60
      description_zh: "使一次性包装变得'太便宜不值得回收'的发明——便利性杀死了可持续性"
      domains: [化学, 工业, 环境]

    - source: plastics
      target: production_milestone_9_billion
      type: CAUSED
      drama_score: 0.88
      irony_level: 0.75
      description_zh: "92亿吨——其中一半以上是2004年以后生产的。人类创造了一种比自己活得更久的材料"
      description_en: "9.2 billion tonnes — more than half produced after 2004. We created a material that outlives us"
      domains: [工业, 环境]

    - source: plastics
      target: great_pacific_garbage_patch
      type: CAUSED
      drama_score: 0.90
      irony_level: 0.80
      description_zh: "太平洋上漂浮着一个塑料'大陆'——面积比法国还大"
      domains: [环境, 海洋]

    - source: plastics
      target: microplastics_discovery
      type: CAUSED
      drama_score: 0.92
      irony_level: 0.85
      description_zh: "我们制造的塑料碎成了肉眼看不见的微粒，如今存在于每一个人的血液中"
      description_en: "The plastic we made shattered into invisible particles now found in every human's blood"
      domains: [环境, 健康]

    - source: plastics
      target: plasticosis_2023
      type: CAUSED
      drama_score: 0.85
      irony_level: 0.82
      description_zh: "人类制造出了一种全新的疾病——不是病毒，不是细菌，是我们自己的垃圾"
      domains: [生态, 健康]

    # 事件 → 后果
    - source: bakelite_1907
      target: modern_life_transformation
      type: CAUSED
      drama_score: 0.80
      irony_level: 0.45
      description_zh: "从电木到聚乙烯到尼龙——塑料定义了20世纪的物质文明"
      domains: [工业, 社会]

    - source: great_pacific_garbage_patch
      target: ocean_plastic_crisis
      type: CAUSED
      drama_score: 0.88
      irony_level: 0.70
      description_zh: "每年8-12百万吨塑料入海——海洋垃圾中80%是塑料"
      domains: [环境, 海洋]

    - source: microplastics_discovery
      target: microplastic_health_threat
      type: CAUSED
      drama_score: 0.90
      irony_level: 0.80
      description_zh: "微塑料已进入人体——但其长期健康影响依然是巨大的未知"
      domains: [健康, 环境]

    # 讽刺反转链
    - source: modern_life_transformation
      target: ocean_plastic_crisis
      type: IRONIC_TWIST
      drama_score: 0.93
      irony_level: 0.90
      description_zh: "20世纪最伟大的发明正在成为21世纪最严重的环境危机——便利性的代价"
      description_en: "The 20th century's greatest invention is becoming the 21st century's worst environmental crisis"
      domains: [工业, 环境]

    - source: modern_life_transformation
      target: recycling_failure
      type: IRONIC_TWIST
      drama_score: 0.85
      irony_level: 0.92
      description_zh: "回收的承诺维持了塑料的正当性——但数据显示只有9%被回收。回收是神话还是遮羞布？"
      description_en: "The promise of recycling sustained plastic's legitimacy — but only 9% is actually recycled"
      domains: [环境, 工业]

    - source: parkesine_1855
      target: ocean_plastic_crisis
      type: IRONIC_TWIST
      drama_score: 0.80
      irony_level: 0.88
      description_zh: "为拯救大象从象牙贸易中解放出来而发明的材料，最终成为海洋生态系统的噩梦"
      description_en: "Material invented to save elephants from ivory trade became an oceanic ecological nightmare"
      domains: [环境, 历史]

  cross_connections:
    - target_compound: cfc
      relationship_zh: "石化工业双胞胎灾难：CFC捅破天，塑料堵塞地"
      connection_type: 同属环保危机

    - target_compound: synthetic_ammonia
      relationship_zh: "20世纪化工业两大'造福人类后反噬'的发明"
      connection_type: 双面刃发明

```

---


================================================================================
## 故事线：ddt
================================================================================

```yaml
# DDT故事线 — 基于 encyclopedia/compounds/ddt.md 提取
# 戏剧性历史节点 + 因果网络 + 评分

compound:
  id: ddt
  name_zh: 滴滴涕
  name_en: DDT (Dichlorodiphenyltrichloroethane)
  aliases_zh: [滴滴涕, DDT, 双对氯苯基三氯乙烷]
  category: 农药/杀虫剂
  year_invented: 1939
  formula: (ClC₆H₄)₂CH(CCl₃)
  cas_number: "50-29-3"
  safety_note: "本条目仅讨论历史和社会影响，不涉及合成方法或使用指导"

  people:
    - id: paul_mueller
      name_zh: 保罗·赫尔曼·穆勒
      name_en: Paul Hermann Müller
      role: 发现DDT杀虫活性的瑞士化学家
      nationality: 瑞士
      year: 1939
      nobel_year: 1948
      irony_note: "因'发现DDT对节肢动物的高效接触毒性'获诺贝尔奖——24年后DDT在美国被禁"

    - id: rachel_carson
      name_zh: 蕾切尔·卡森
      name_en: Rachel Carson
      role: 《寂静的春天》作者，现代环保运动之母
      nationality: 美国
      year: 1962
      irony_note: "一位海洋生物学家用一本书推翻了一个诺贝尔奖的遗产，催生了整个环保运动"

    - id: othmar_zeidler
      name_zh: 奥特马尔·蔡德勒
      name_en: Othmar Zeidler
      role: 1874年首次合成DDT的奥地利化学家
      nationality: 奥地利
      year: 1874
      irony_note: "合成了DDT却完全没有意识到它的杀虫特性——这个分子在抽屉里沉睡了65年"

    - id: victor_yannacone
      name_zh: 维克多·扬纳科内
      name_en: Victor Yannacone
      role: 环保律师，环境保护基金会(EDF)联合创始人
      nationality: 美国
      year: 1967
      irony_note: "一个律师用法庭而非实验室改变了化学品监管的历史"

  events:
    - id: ddt_first_synthesis_1874
      name_zh: 蔡德勒首次合成DDT——然后被遗忘65年
      name_en: Zeidler first synthesizes DDT — then forgotten for 65 years
      year: 1874
      domain: 化学
      scale: 个人
      location: 奥地利
      quote: "一个化学博士生合成了一种将改变世界的分子，但他和全世界一样，完全没有意识到"
      source_ref: "encyclopedia/compounds/ddt.md ## History"

    - id: mueller_discovers_insecticide_1939
      name_zh: 穆勒发现DDT的强力杀虫活性
      name_en: Müller discovers DDT's potent insecticidal properties
      year: 1939
      domain: 化学
      scale: 全球
      location: 瑞士巴塞尔
      quote: "距首次合成65年后，一位瑞士科学家终于发现了这个分子的超能力"

    - id: wwii_malaria_typhus_control
      name_zh: 二战中DDT拯救数百万军人和平民免于疟疾和斑疹伤寒
      name_en: DDT saves millions from malaria and typhus in WWII
      year: 1943
      end_year: 1945
      domain: 军事/公共卫生
      scale: 全球
      quote: "盟军在南太平洋空中喷洒DDT，效果堪称壮观——疟疾和登革热的发病率断崖式下降"

    - id: mueller_nobel_1948
      name_zh: 穆勒获1948年诺贝尔生理学或医学奖
      name_en: Müller awarded 1948 Nobel Prize in Physiology or Medicine
      year: 1948
      domain: 科学
      scale: 全球
      quote: "表彰他'发现DDT作为多种节肢动物的接触毒物的高效性'"

    - id: who_malaria_eradication_1955
      name_zh: WHO发起全球疟疾根除计划，严重依赖DDT
      name_en: WHO launches global malaria eradication program relying heavily on DDT
      year: 1955
      domain: 公共卫生
      scale: 全球
      quote: "该计划成功消灭了北美、欧洲、苏联等地区的疟疾，但在热带地区失败了"

    - id: silent_spring_1962
      name_zh: 蕾切尔·卡森出版《寂静的春天》
      name_en: Rachel Carson publishes Silent Spring
      year: 1962
      domain: 文化/环境
      scale: 全球
      location: 美国
      quote: "这本书引发了公众的强烈反响，启动了现代环保运动——虽然卡森从未直接呼吁全面禁止DDT"
      source_ref: "encyclopedia/compounds/ddt.md ## History"

    - id: bald_eagle_near_extinction
      name_zh: DDT导致白头海雕（美国国鸟）和游隼濒临灭绝
      name_en: DDT drives bald eagle and peregrine falcon to near extinction
      year: 1960
      end_year: 1972
      domain: 生态
      scale: 国家
      location: 美国
      quote: "DDT的代谢产物DDE使猛禽蛋壳变薄至无法孵化——美国国鸟差点因一种杀虫剂灭绝"

    - id: edf_founded_lawsuit_1967
      name_zh: 环境保护基金会(EDF)成立并起诉DDT使用
      name_en: Environmental Defense Fund founded to sue against DDT
      year: 1967
      domain: 法律
      scale: 国家
      location: 美国纽约
      quote: "一场鱼类死亡事件促成了世界上第一个环保法律组织的诞生"

    - id: us_ban_1972
      name_zh: 美国禁止农业使用DDT
      name_en: US bans agricultural use of DDT
      year: 1972
      domain: 法律/环境
      scale: 国家
      location: 美国
      quote: "EPA署长Ruckelshaus取消了DDT的大部分使用许可——但公共卫生豁免保留"

    - id: stockholm_convention_2004
      name_zh: 斯德哥尔摩公约全球禁止DDT农业使用
      name_en: Stockholm Convention globally restricts DDT
      year: 2004
      domain: 国际法
      scale: 全球
      quote: "170+国家签署——但公共卫生用途豁免保留，因为在某些疟疾流行区仍无替代品"

  consequences:
    - id: environmental_movement_born
      description_zh: 《寂静的春天》催生了现代环保运动和环保立法
      description_en: Silent Spring catalyzed the modern environmental movement
      type: 正面
      domain: 环境/政治
      scale: 全球
      ongoing: true

    - id: eggshell_thinning_wildlife
      description_zh: DDT及DDE导致猛禽蛋壳变薄，多个物种濒临灭绝
      description_en: DDT/DDE caused eggshell thinning, driving raptors to near extinction
      type: 负面
      domain: 生态
      scale: 全球
      quantifier: "白头海雕、游隼、鹗、褐鹈鹕"

    - id: malaria_resurgence
      description_zh: DDT禁令争议——撤除喷洒后部分热带地区疟疾反弹
      description_en: Malaria resurged in some tropical regions after DDT spraying was curtailed
      type: 讽刺
      domain: 公共卫生
      scale: 全球
      ongoing: true

    - id: persistent_pollution
      description_zh: DDT在环境中持久存在——2018年研究仍在欧洲土壤和西班牙河流中检出
      description_en: DDT residues persist in environment decades after ban
      type: 负面
      domain: 环境
      scale: 全球
      ongoing: true
      quantifier: "土壤半衰期22天至30年"

  causal_chains:
    # 化合物 → 事件
    - source: ddt
      target: ddt_first_synthesis_1874
      type: ENABLED
      drama_score: 0.60
      irony_level: 0.50
      description_zh: "一个沉睡65年的发明——合成它的人完全不知道它有什么用"
      domains: [化学]

    - source: ddt
      target: mueller_discovers_insecticide_1939
      type: ENABLED
      drama_score: 0.80
      irony_level: 0.35
      description_zh: "65年后被重新发现的杀虫超能力"
      domains: [化学, 农业]
      time_lag_years: 65

    - source: ddt
      target: wwii_malaria_typhus_control
      type: ENABLED
      drama_score: 0.90
      irony_level: 0.60
      description_zh: "DDT成为二战中的隐形英雄——保护了数百万军人免于热带疾病"
      domains: [军事, 公共卫生]
      time_lag_years: 4

    - source: ddt
      target: mueller_nobel_1948
      type: ENABLED
      drama_score: 0.85
      irony_level: 0.90
      description_zh: "因'造福人类'获诺贝尔奖——24年后被美国禁用，56年后被全球禁止"
      description_en: "Nobel for 'benefiting humanity' — banned 24 years later, globally restricted 56 years later"
      domains: [科学, 讽刺]
      time_lag_years: 9

    - source: ddt
      target: who_malaria_eradication_1955
      type: ENABLED
      drama_score: 0.80
      irony_level: 0.70
      description_zh: "DDT成了WHO消灭疟疾的主要武器——但蚊子很快进化出抗药性"
      domains: [公共卫生]

    - source: ddt
      target: bald_eagle_near_extinction
      type: CAUSED
      drama_score: 0.92
      irony_level: 0.88
      description_zh: "保护人类健康的杀虫剂几乎杀死了美国国鸟——DDT沿食物链富集到猛禽体内"
      description_en: "The insecticide that protected humans nearly killed America's national bird"
      domains: [生态, 化学]

    - source: rachel_carson
      target: silent_spring_1962
      type: ENABLED
      drama_score: 0.95
      irony_level: 0.70
      description_zh: "一本书改变了世界——一位海洋生物学家对抗整个化工产业"
      domains: [文化, 环境, 科学]

    - source: silent_spring_1962
      target: us_ban_1972
      type: CAUSED
      drama_score: 0.88
      irony_level: 0.65
      description_zh: "从畅销书到法律——十年内从公众觉醒到政府行动"
      domains: [法律, 环境]
      time_lag_years: 10

    - source: us_ban_1972
      target: stockholm_convention_2004
      type: ENABLED
      drama_score: 0.75
      irony_level: 0.55
      description_zh: "美国带头禁令推动了全球性约束——但留下了疟疾控制的豁免悖论"
      domains: [国际法, 环境]
      time_lag_years: 32

    # 事件 → 后果
    - source: silent_spring_1962
      target: environmental_movement_born
      type: CAUSED
      drama_score: 0.90
      irony_level: 0.55
      description_zh: "一本书催生了一场运动——EPA的建立、《濒危物种法》都可追溯到此"
      domains: [文化, 政治, 环境]

    - source: bald_eagle_near_extinction
      target: eggshell_thinning_wildlife
      type: CAUSED
      drama_score: 0.88
      irony_level: 0.80
      description_zh: "化学品在食物链中的生物放大效应——DDT浓度在猛禽体内放大了上百万倍"
      domains: [生态, 化学]

    # 讽刺反转链
    - source: mueller_nobel_1948
      target: us_ban_1972
      type: IRONIC_TWIST
      drama_score: 0.92
      irony_level: 0.95
      description_zh: "诺贝尔奖的化合物被发奖国所在大洲纷纷禁用——科学荣誉与环境灾难的极致碰撞"
      description_en: "The Nobel-winning compound was banned by country after country"
      domains: [科学, 法律, 环境]

    - source: wwii_malaria_typhus_control
      target: malaria_resurgence
      type: IRONIC_TWIST
      drama_score: 0.85
      irony_level: 0.88
      description_zh: "禁掉DDT后疟疾在部分地区反弹——引发'为了鸟还是为了人'的伦理争论"
      domains: [公共卫生, 伦理]

  cross_connections:
    - target_compound: synthetic_ammonia
      relationship_zh: "同属双用途：农业/军事的双面刃"
      connection_type: 同属双用途

    - target_compound: penicillin
      relationship_zh: "二战同时催化了两者的量产——命运却截然不同"
      connection_type: 战争催化

    - target_compound: msg
      relationship_zh: "都经历了'先追捧后恐慌'的命运，但结局不同"
      connection_type: 先追捧后质疑

```

---


================================================================================
## 故事线：cfc
================================================================================

```yaml
# CFC (氯氟烃) 故事线 — 基于 encyclopedia/compounds/cfc.md 提取
# 戏剧性历史节点 + 因果网络 + 评分

compound:
  id: cfc
  name_zh: 氯氟烃 (氟利昂)
  name_en: Chlorofluorocarbon (CFC / Freon)
  aliases_zh: [氯氟烃, 氟利昂, CFC, 氟氯碳化合物]
  category: 工业化学品
  year_invented: 1928
  formula: CCl₂F₂ (CFC-12)
  safety_note: "本条目仅讨论历史和社会影响，不涉及合成方法或配方"

  people:
    - id: thomas_midgley
      name_zh: 小托马斯·米基利
      name_en: Thomas Midgley Jr.
      role: CFC发明者，通用汽车化学家
      nationality: 美国
      year: 1928
      irony_note: "被环境史学家称为'对大气层影响最大的单个有机体'——同时还发明了含铅汽油"

    - id: sherwood_rowland
      name_zh: 弗兰克·舍伍德·罗兰
      name_en: F. Sherwood Rowland
      role: 发现CFC破坏臭氧层的化学家
      nationality: 美国
      year: 1974
      nobel_year: 1995
      irony_note: "发表论文后遭化工行业攻击多年，直到臭氧空洞被发现才得到平反"

    - id: mario_molina
      name_zh: 马里奥·莫利纳
      name_en: Mario Molina
      role: 与罗兰共同发现CFC-臭氧机制的墨西哥化学家
      nationality: 墨西哥
      year: 1974
      nobel_year: 1995
      irony_note: "一位博士后改变了全球大气化学——并推动了人类历史上最成功的环保条约"

    - id: james_lovelock
      name_zh: 詹姆斯·拉夫洛克
      name_en: James Lovelock
      role: 用自研电子捕获检测器首次发现大气中CFC
      nationality: 英国
      year: 1970
      irony_note: "自费研究发现CFC无处不在，却得出了'对环境无害'的错误结论"

  events:
    - id: toxic_refrigerant_accidents
      name_zh: 1920年代致命制冷剂泄漏事故频发
      name_en: Fatal refrigerant leaks in the 1920s
      year: 1920
      end_year: 1928
      domain: 工业安全
      scale: 国家
      location: 美国
      quote: "氨、二氧化硫、氯甲烷——早期冰箱使用的制冷剂频繁泄漏致死"
      source_ref: "encyclopedia/compounds/cfc.md ## History"

    - id: midgley_demo_1930
      name_zh: 米基利当众吸入氟利昂并吹灭蜡烛
      name_en: Midgley inhales Freon and blows out a candle in demo
      year: 1930
      domain: 工业
      scale: 国家
      location: 美国
      quote: "在美国化学学会的演示中，他深吸一口氟利昂并用它吹灭蜡烛——炫耀其无毒无燃性"

    - id: freon_mass_production
      name_zh: 通用汽车与杜邦成立Kinetic公司量产氟利昂
      name_en: GM and DuPont mass-produce Freon
      year: 1930
      domain: 工业
      scale: 全球
      quote: "到1935年，800万台使用R-12的冰箱售出。城市公共卫生法规指定CFC为公共建筑唯一合法制冷剂"

    - id: peak_cfc_production
      name_zh: CFC年产超百万吨，年销售超10亿美元
      name_en: CFC production peaks at over 1 million metric tonnes annually
      year: 1974
      domain: 工业
      scale: 全球
      quote: "从冰箱到气雾罐到灭火器——CFC渗透到现代生活的每个角落"

    - id: rowland_molina_paper_1974
      name_zh: 罗兰和莫利纳发表CFC破坏臭氧层的论文
      name_en: Rowland and Molina publish CFC-ozone depletion theory
      year: 1974
      domain: 科学
      scale: 全球
      quote: "CFC最吸引人的特性——低反应性——恰恰是它最具破坏性的根源：化学惰性让它活到平流层"
      source_ref: "encyclopedia/compounds/cfc.md ## Regulation"

    - id: industry_attacks_scientists
      name_zh: 化工行业攻击罗兰和莫利纳——杜邦带头反对
      name_en: Chemical industry attacks Rowland-Molina findings
      year: 1975
      end_year: 1986
      domain: 政治/工业
      scale: 全球
      quote: "杜邦成立'负责任CFC政策联盟'游说团体对抗监管——直到自己的替代品专利到手才转向"

    - id: ozone_hole_discovered
      name_zh: 发现南极臭氧空洞——季节性臭氧层剧烈耗损
      name_en: Discovery of the Antarctic ozone hole
      year: 1985
      domain: 科学/环境
      scale: 全球
      location: 南极
      quote: "令人震惊的观测数据——南极上空的臭氧层在每年春季几乎消失殆尽"

    - id: montreal_protocol_1987
      name_zh: 蒙特利尔议定书签署——要求大幅削减CFC
      name_en: Montreal Protocol signed — drastic CFC reduction
      year: 1987
      domain: 国际法
      scale: 全球
      location: 加拿大蒙特利尔
      quote: "被联合国称为'也许是迄今为止最成功的国际环保协议'"

    - id: dupont_reversal_1986
      name_zh: 杜邦公司立场反转——从CFC捍卫者变为禁令推动者
      name_en: DuPont reverses position — from CFC defender to ban advocate
      year: 1986
      domain: 工业/政治
      scale: 全球
      quote: "手握替代品HCFC专利的杜邦代表出现在蒙特利尔议定书上，呼吁全球禁止CFC"

    - id: ozone_recovery_2018
      name_zh: NASA宣布臭氧层空洞开始恢复
      name_en: NASA announces ozone hole has begun to recover
      year: 2018
      domain: 环境
      scale: 全球
      quote: "人类证明了集体行动可以修复全球性环境损害——这也许是人类环保史上最鼓舞人心的故事"

  consequences:
    - id: ozone_depletion_global
      description_zh: CFC导致全球臭氧层大规模耗损，南极出现臭氧空洞
      description_en: CFCs caused massive ozone depletion and the Antarctic ozone hole
      type: 负面
      domain: 环境
      scale: 全球
      ongoing: true

    - id: montreal_protocol_success
      description_zh: 蒙特利尔议定书成为人类史上最成功的全球环保条约
      description_en: Montreal Protocol became the most successful global environmental treaty
      type: 正面
      domain: 国际合作
      scale: 全球
      ongoing: true

    - id: super_greenhouse_effect
      description_zh: CFC作为超级温室气体——单分子温室效应远超CO₂
      description_en: CFCs are super greenhouse gases — far more potent per molecule than CO₂
      type: 负面
      domain: 气候
      scale: 全球
      ongoing: true

    - id: midgley_legacy_infamy
      description_zh: 米基利被称为"对大气层影响最大的单个有机体"——同时发明了含铅汽油和CFC
      description_en: Midgley called 'most destructive single organism in Earth's history'
      type: 讽刺
      domain: 科学史
      scale: 全球

  causal_chains:
    # 化合物 → 事件
    - source: cfc
      target: toxic_refrigerant_accidents
      type: ENABLED
      drama_score: 0.65
      irony_level: 0.60
      description_zh: "早期致命制冷剂催生了对'安全替代品'的需求——没人预料到解决方案比问题更可怕"
      domains: [工业安全, 化学]

    - source: cfc
      target: midgley_demo_1930
      type: ENABLED
      drama_score: 0.80
      irony_level: 0.92
      description_zh: "当众吸入CFC证明它'完全安全'——半个世纪后人类发现它在头顶撕开了一个洞"
      description_en: "Publicly inhaled to prove safety — decades later found to tear a hole in the sky"
      domains: [工业, 科学]

    - source: cfc
      target: freon_mass_production
      type: ENABLED
      drama_score: 0.70
      irony_level: 0.50
      description_zh: "城市法规指定CFC为公共建筑唯一合法制冷剂——因为它'最安全'"
      domains: [工业, 法律]

    - source: cfc
      target: peak_cfc_production
      type: ENABLED
      drama_score: 0.75
      irony_level: 0.65
      description_zh: "年产百万吨，年销十亿美元——CFC帝国在荣光顶点坠落"
      domains: [工业, 经济]

    - source: cfc
      target: rowland_molina_paper_1974
      type: ENABLED
      drama_score: 0.95
      irony_level: 0.90
      description_zh: "CFC最大的优点（化学惰性）正是它最可怕的缺陷——惰性让它活到平流层被紫外线撕裂，释放出催化臭氧分解的氯原子"
      description_en: "CFC's greatest strength (inertness) was its most destructive flaw"
      domains: [科学, 化学]

    - source: rowland_molina_paper_1974
      target: industry_attacks_scientists
      type: CAUSED
      drama_score: 0.80
      irony_level: 0.75
      description_zh: "科学家vs化工巨头——杜邦的专利即将到期时突然'发现良心'"
      domains: [政治, 工业, 科学]

    - source: rowland_molina_paper_1974
      target: ozone_hole_discovered
      type: ENABLED
      drama_score: 0.92
      irony_level: 0.55
      description_zh: "11年后理论被壮观地证实——南极上空的臭氧层每年春季几乎消失"
      domains: [科学, 环境]
      time_lag_years: 11

    - source: ozone_hole_discovered
      target: montreal_protocol_1987
      type: CAUSED
      drama_score: 0.90
      irony_level: 0.40
      description_zh: "震惊世界的臭氧空洞照片在两年内促成了史上最成功的全球环保条约"
      domains: [国际法, 环境]
      time_lag_years: 2

    - source: dupont_reversal_1986
      target: montreal_protocol_1987
      type: ENABLED
      drama_score: 0.82
      irony_level: 0.88
      description_zh: "CFC最大的生产商——杜邦——手握替代品专利后立场180度反转：从反对禁令到推动禁令"
      description_en: "DuPont reversed stance once they had patent for replacement chemicals"
      domains: [工业, 政治]

    - source: montreal_protocol_1987
      target: ozone_recovery_2018
      type: CAUSED
      drama_score: 0.85
      irony_level: 0.30
      description_zh: "人类史上罕见的好消息：集体行动确实可以修复全球性环境损害"
      domains: [环境, 国际合作]
      time_lag_years: 31

    # 事件 → 后果
    - source: ozone_hole_discovered
      target: ozone_depletion_global
      type: CAUSED
      drama_score: 0.90
      irony_level: 0.70
      description_zh: "无毒、不燃、化学惰性的'完美'制冷剂在地球上空撕开了一个洞"
      domains: [环境, 化学]

    - source: montreal_protocol_1987
      target: montreal_protocol_success
      type: CAUSED
      drama_score: 0.80
      irony_level: 0.30
      description_zh: "科学 → 公众觉醒 → 国际合作 → 修复——环保问题应该怎么解决的教科书案例"
      domains: [国际合作, 环境]

    # 讽刺反转链
    - source: midgley_demo_1930
      target: midgley_legacy_infamy
      type: IRONIC_TWIST
      drama_score: 0.95
      irony_level: 0.98
      description_zh: "当众吸入气体向世界炫耀'安全'的人，同时也发明了含铅汽油——一人造成了两场全球性环境灾难"
      description_en: "The man who publicly inhaled CFC to show safety also invented leaded gasoline — one person, two global environmental disasters"
      domains: [科学史, 环境]

    - source: ozone_depletion_global
      target: montreal_protocol_success
      type: IRONIC_TWIST
      drama_score: 0.88
      irony_level: 0.75
      description_zh: "人类造成的最大大气灾难催生了人类最成功的国际合作——CFC的故事同时是人类最愚蠢和最伟大的时刻"
      domains: [环境, 国际合作]

  cross_connections:
    - target_compound: plastics
      relationship_zh: "石化工业双胞胎灾难：CFC捅破天，塑料堵塞地"
      connection_type: 同属环保危机

    - target_compound: synthetic_ammonia
      relationship_zh: "三个争议性诺贝尔奖的讽刺链"
      connection_type: 诺贝尔讽刺

    - target_compound: ddt
      relationship_zh: "都是被誉为'安全奇迹'后造成全球环境灾难的化学品"
      connection_type: 安全悖论

```

---


================================================================================
## 故事线：penicillin
================================================================================

```yaml
# 青霉素故事线 — 基于 encyclopedia/compounds/penicillin.md 提取
# 戏剧性历史节点 + 因果网络 + 评分

compound:
  id: penicillin
  name_zh: 青霉素
  name_en: Penicillin
  aliases_zh: [青霉素, 盘尼西林, 青黴素]
  category: 药物/抗生素
  year_invented: 1928
  formula: R-C₉H₁₁N₂O₄S
  safety_note: "本条目仅讨论历史和社会影响，不涉及合成方法或临床用法"

  people:
    - id: alexander_fleming
      name_zh: 亚历山大·弗莱明
      name_en: Alexander Fleming
      role: 偶然发现青霉菌杀菌作用的苏格兰医生
      nationality: 英国（苏格兰）
      year: 1928
      nobel_year: 1945
      irony_note: "发现了改变世界的药物却无法说服任何人它很重要——青霉素在抽屉里沉睡了十年"

    - id: howard_florey
      name_zh: 霍华德·弗洛里
      name_en: Howard Florey
      role: 领导牛津团队纯化青霉素，推动其量产
      nationality: 澳大利亚
      year: 1940
      nobel_year: 1945
      irony_note: "拒绝为青霉素申请专利——被告知'这样做不道德'——结果专利被美国人拿去了"

    - id: ernst_chain
      name_zh: 恩斯特·鲍里斯·钱恩
      name_en: Ernst Boris Chain
      role: 在牛津纯化出青霉素活性成分的德裔犹太化学家
      nationality: 德国→英国
      year: 1940
      nobel_year: 1945
      irony_note: "因犹太身份逃离纳粹德国，在英国发现了拯救盟军的药物——用德国的敌人英国的实验室"

    - id: dorothy_hodgkin
      name_zh: 多萝西·霍奇金
      name_en: Dorothy Crowfoot Hodgkin
      role: 用X射线晶体学确定了青霉素的化学结构
      nationality: 英国
      year: 1945
      nobel_year: 1964
      irony_note: "青霉素分子结构之争持续多年，一位女晶体学家用X射线一锤定音——然后获得了诺贝尔化学奖"

  events:
    - id: fleming_accidental_discovery
      name_zh: 弗莱明偶然发现培养皿上的霉菌杀死了葡萄球菌
      name_en: Fleming's accidental discovery of penicillin mould killing bacteria
      year: 1928
      domain: 科学
      scale: 全球
      location: 英国伦敦圣玛丽医院
      quote: "1928年9月3日，度假归来的弗莱明注意到一个被污染的培养皿上，霉菌周围出现了细菌的'空白区'"
      source_ref: "encyclopedia/compounds/penicillin.md ## History"

    - id: decade_of_neglect
      name_zh: 青霉素被发现后沉寂十年——弗莱明无法说服任何人
      name_en: Penicillin ignored for a decade after discovery
      year: 1929
      end_year: 1939
      domain: 科学
      scale: 个人
      quote: "弗莱明无法纯化足够的青霉素来证明其临床价值，药物开发看起来'不可能'"

    - id: oxford_team_purification
      name_zh: 弗洛里和钱恩在牛津纯化青霉素并证明临床疗效
      name_en: Florey and Chain purify penicillin at Oxford, prove clinical efficacy
      year: 1940
      domain: 科学/医学
      scale: 全球
      location: 英国牛津
      quote: "1941年第一位病人——警察Albert Alexander：病情好转，然后青霉素用完了，他死了"

    - id: first_patient_dies
      name_zh: 第一位青霉素病人好转后因药物耗尽而死亡
      name_en: First penicillin patient improves then dies when supply runs out
      year: 1941
      domain: 医学
      scale: 个人
      location: 英国牛津
      quote: "药有效了——但产量太少。Albert Alexander眼看着要康复，却因为青霉素不够而死去"

    - id: mouldy_cantaloupe_peoria
      name_zh: 一颗发霉的哈密瓜改变了青霉素量产的命运
      name_en: A mouldy cantaloupe from Peoria market transforms penicillin production
      year: 1943
      domain: 工业
      scale: 全球
      location: 美国伊利诺伊州皮奥里亚
      quote: "实验员Mary Hunt在超市捡到一颗长满青霉的哈密瓜——这个菌株的产量是弗莱明原始菌株的6倍"

    - id: dday_penicillin
      name_zh: 诺曼底登陆时盟军携带230万剂青霉素
      name_en: 2.3 million doses of penicillin ready for D-Day
      year: 1944
      domain: 军事/医学
      scale: 全球
      location: 法国诺曼底
      quote: "從一颗能治一个人创伤感染都不够的培养皿，到D-Day时230万剂——仅四年时间"
      source_ref: "encyclopedia/compounds/penicillin.md ## Mass production"

    - id: urine_recycling
      name_zh: 青霉素如此珍贵——医生从病人尿液中回收再利用
      name_en: Penicillin so precious that doctors recycled it from patients' urine
      year: 1943
      domain: 医学
      scale: 全球
      quote: "80%的青霉素在3-4小时内被肾脏排出——它太珍贵了，所以医生收集病人的尿来回收"

    - id: nobel_1945
      name_zh: 弗莱明、弗洛里、钱恩共享1945年诺贝尔生理学或医学奖
      name_en: Fleming, Florey and Chain share 1945 Nobel Prize
      year: 1945
      domain: 科学
      scale: 全球
      quote: "三人共享诺贝尔奖——但弗洛里拒绝申请专利，被告知'不道德'"

    - id: antibiotic_resistance_crisis
      name_zh: 抗生素耐药性成为21世纪全球健康威胁
      name_en: Antibiotic resistance becomes a 21st century global health threat
      year: 1940
      end_year: 2026
      domain: 医学
      scale: 全球
      quote: "弗莱明在诺贝尔演讲中就警告过：不当使用会导致耐药性。他的预言不幸成真"

  consequences:
    - id: saved_millions_wwii
      description_zh: 二战中青霉素挽救了约12-15%的盟军伤亡人命
      description_en: Penicillin saved an estimated 12-15% of Allied casualties in WWII
      type: 正面
      domain: 军事/医学
      scale: 全球
      quantifier: "12-15%伤亡率下降"

    - id: antibiotic_era_begins
      description_zh: 开启了抗生素时代——人类平均寿命显著延长
      description_en: Launched the antibiotic era — significantly extending human life expectancy
      type: 正面
      domain: 医学
      scale: 全球
      ongoing: true

    - id: mrsa_superbugs
      description_zh: 过度使用导致MRSA等超级细菌出现——抗生素军备竞赛
      description_en: Overuse created MRSA superbugs — an antimicrobial arms race
      type: 讽刺
      domain: 医学
      scale: 全球
      ongoing: true
      quantifier: "2000+种β-内酰胺酶"

    - id: patent_ethics_debate
      description_zh: 弗洛里拒绝专利→美国企业获得量产专利→引发药物专利伦理辩论
      description_en: Florey refused patent → US firms patented production methods → drug patent ethics debate
      type: 讽刺
      domain: 法律/伦理
      scale: 全球

  causal_chains:
    # 化合物 → 事件
    - source: penicillin
      target: fleming_accidental_discovery
      type: ENABLED
      drama_score: 0.90
      irony_level: 0.50
      description_zh: "科学史上最著名的意外之一——一个度假归来未洗的培养皿改变了医学史"
      description_en: "One of science's most famous accidents — an unwashed petri dish changed medical history"
      domains: [科学, 医学]

    - source: fleming_accidental_discovery
      target: decade_of_neglect
      type: CAUSED
      drama_score: 0.75
      irony_level: 0.70
      description_zh: "发现了能改变世界的药物，却没人觉得值得研究——青霉素被搁置了十年"
      domains: [科学]
      time_lag_years: 10

    - source: penicillin
      target: oxford_team_purification
      type: ENABLED
      drama_score: 0.85
      irony_level: 0.40
      description_zh: "十年后牛津团队从弗莱明的'不可能'中提取出了临床奇迹"
      domains: [科学, 医学]
      time_lag_years: 12

    - source: oxford_team_purification
      target: first_patient_dies
      type: CAUSED
      drama_score: 0.92
      irony_level: 0.85
      description_zh: "药有效了——但Albert Alexander还是死了，因为产量太少。药效和产量的残酷赛跑"
      description_en: "The drug worked — but the patient died because supply ran out"
      domains: [医学]

    - source: penicillin
      target: mouldy_cantaloupe_peoria
      type: ENABLED
      drama_score: 0.85
      irony_level: 0.75
      description_zh: "拯救人类的药物菌株来自一颗超市里的烂哈密瓜——产量是弗莱明原始菌株的6倍"
      description_en: "The strain that saved humanity came from a rotten cantaloupe in a supermarket"
      domains: [工业, 生物学]

    - source: mouldy_cantaloupe_peoria
      target: dday_penicillin
      type: ENABLED
      drama_score: 0.90
      irony_level: 0.45
      description_zh: "从实验室的微量到诺曼底的230万剂——医学和工程的完美冲刺"
      domains: [军事, 工业, 医学]
      time_lag_years: 1

    - source: penicillin
      target: urine_recycling
      type: ENABLED
      drama_score: 0.80
      irony_level: 0.80
      description_zh: "青霉素珍贵到需要从病人尿液中回收——80%会在3-4小时内被肾脏排出"
      domains: [医学]

    - source: penicillin
      target: nobel_1945
      type: ENABLED
      drama_score: 0.70
      irony_level: 0.55
      description_zh: "三人共享诺贝尔奖，但关于'谁才是真正的发现者'的争论至今未息"
      domains: [科学]

    # 事件 → 后果
    - source: dday_penicillin
      target: saved_millions_wwii
      type: CAUSED
      drama_score: 0.88
      irony_level: 0.30
      description_zh: "青霉素在战场上首次大规模使用——感染伤口的死亡率断崖式下降"
      domains: [军事, 医学]

    - source: oxford_team_purification
      target: antibiotic_era_begins
      type: CAUSED
      drama_score: 0.85
      irony_level: 0.40
      description_zh: "青霉素打开了抗生素时代——人类第一次可以系统性地战胜细菌感染"
      domains: [医学]

    - source: antibiotic_era_begins
      target: mrsa_superbugs
      type: IRONIC_TWIST
      drama_score: 0.90
      irony_level: 0.90
      description_zh: "拯救了无数生命的抗生素正在失效——细菌的进化速度超过了人类研发新药的速度"
      description_en: "The antibiotics that saved millions are failing — bacteria evolve faster than we develop new drugs"
      domains: [医学, 进化]

    - source: nobel_1945
      target: patent_ethics_debate
      type: IRONIC_TWIST
      drama_score: 0.75
      irony_level: 0.80
      description_zh: "弗洛里因'道德'拒绝专利，结果被美国企业拿去赚了数十亿——至今仍是药物伦理辩论的焦点"
      domains: [法律, 伦理, 医学]

  cross_connections:
    - target_compound: aspirin
      relationship_zh: "药物发现的两种范式：化学合成 vs 自然发现"
      connection_type: 药物范式对比

    - target_compound: ddt
      relationship_zh: "二战同时催化了两者的量产——青霉素救治伤兵，DDT保护军人免受疟疾"
      connection_type: 战争催化

```

---


================================================================================
## 故事线：msg
================================================================================

```yaml
# 味精故事线 — 基于 encyclopedia/compounds/msg.md 提取
# 戏剧性历史节点 + 因果网络 + 评分

compound:
  id: msg
  name_zh: 味精 (谷氨酸钠)
  name_en: MSG (Monosodium Glutamate)
  aliases_zh: [味精, 味素, 谷氨酸钠, 味之素]
  category: 食品添加剂
  year_invented: 1908
  formula: C₅H₈NNaO₄
  cas_number: "142-47-2"
  safety_note: "本条目仅讨论历史和社会影响，不涉及食品安全建议"

  people:
    - id: kikunae_ikeda
      name_zh: 池田菊苗
      name_en: Kikunae Ikeda
      role: 东京帝国大学教授，发现鲜味并发明味精
      nationality: 日本
      year: 1908
      irony_note: "发现了酸甜苦咸之外的第五种味道——西方科学界花了近一个世纪才正式承认它的存在"

    - id: robert_ho_man_kwok
      name_zh: '"郭浩民"（可能是虚构身份）'
      name_en: Robert Ho Man Kwok (possibly fictitious)
      role: 1968年写信给《新英格兰医学杂志》声称吃中餐后出现不适
      nationality: 美国
      year: 1968
      irony_note: "据调查可能是两名美国年轻医生的恶作剧——杜撰的一封信建立了持续数十年的种族偏见"

    - id: suzuki_brothers
      name_zh: 铃木兄弟
      name_en: Suzuki Brothers
      role: 1909年开始商业化生产味精，创立味之素品牌
      nationality: 日本
      year: 1909
      irony_note: "味之素（'风味之精华'）成为全球品牌——同时也成了西方反MSG恐慌的靶子"

  events:
    - id: ikeda_umami_discovery
      name_zh: 池田菊苗从海带中分离出谷氨酸——发现第五种味道"鲜味"
      name_en: Ikeda isolates glutamic acid from kombu — discovers umami
      year: 1908
      domain: 科学/食品
      scale: 全球
      location: 日本东京
      quote: "他注意到柴鱼片和海带的高汤有一种'甜酸苦咸都无法描述'的独特滋味，命名为'鲜味'(umami)"
      source_ref: "encyclopedia/compounds/msg.md ## History"

    - id: ajinomoto_commercial_1909
      name_zh: 铃木兄弟开始商业化生产"味之素"
      name_en: Suzuki Brothers begin commercial MSG production as Ajinomoto
      year: 1909
      domain: 工业/食品
      scale: 全球
      location: 日本
      quote: "'味之素'——日文'风味之精华'——世界上第一种被提纯的鲜味增强剂"

    - id: chinese_restaurant_syndrome_letter
      name_zh: 《新英格兰医学杂志》发表"中餐馆综合症"读者来信
      name_en: '"Chinese Restaurant Syndrome" letter published in NEJM'
      year: 1968
      domain: 文化/医学
      scale: 全球
      location: 美国
      quote: "一封署名'Robert Ho Man Kwok'的信声称每次吃中餐后都出现头痛、麻木、心悸——引发了持续数十年的MSG恐慌"

    - id: hoax_revelation
      name_zh: 调查揭示"郭浩民"可能是两名美国医生打赌的恶作剧
      name_en: Investigation reveals the letter may have been a hoax by two young doctors
      year: 2018
      domain: 文化/媒体
      scale: 全球
      quote: "迈克尔·布兰丁的调查报道：那封信可能是两个年轻美国医生打赌谁能在严肃学术期刊上发表胡说八道"
      source_ref: "encyclopedia/compounds/msg.md ## 中菜館綜合症"

    - id: fda_gras_status
      name_zh: FDA将味精列为"公认安全"(GRAS)
      name_en: FDA classifies MSG as Generally Recognized as Safe (GRAS)
      year: 1958
      domain: 法律/食品安全
      scale: 国家
      location: 美国
      quote: "美国食品药品监督管理局认定味精在正常食用量下对人体安全"

    - id: faseb_1995_report
      name_zh: FASEB报告结论：正常食用量下MSG是安全的
      name_en: FASEB report concludes MSG is safe at customary levels
      year: 1995
      domain: 科学
      scale: 全球
      quote: "双盲安慰剂对照实验反复证明：正常餐食中的MSG含量不会引起任何症状"

    - id: umami_finally_accepted
      name_zh: 鲜味被科学界正式承认为第五种基本味觉
      name_en: Umami officially recognized as the fifth basic taste
      year: 2002
      domain: 科学
      scale: 全球
      quote: "发现鲜味味觉受体后，西方科学终于承认了池田菊苗1908年就描述的'第五种味道'"

    - id: pakistan_ban_and_lift
      name_zh: 巴基斯坦旁遮普省禁止味精后又解禁
      name_en: Pakistan Punjab bans then lifts MSG ban after scientific review
      year: 2018
      end_year: 2024
      domain: 法律/食品安全
      scale: 国家
      location: 巴基斯坦
      quote: "科学委员会审查后确认MSG是安全的食品添加剂——禁令被撤销"

  consequences:
    - id: umami_revolution
      description_zh: 鲜味概念改变了全球烹饪和食品工业
      description_en: Umami concept transformed global cuisine and food industry
      type: 正面
      domain: 食品/文化
      scale: 全球
      ongoing: true

    - id: racial_food_stigma
      description_zh: '"中餐馆综合症"成为针对亚洲食品的种族偏见标签'
      description_en: '"Chinese Restaurant Syndrome" became a racially charged stigma against Asian food'
      type: 负面
      domain: 文化/种族
      scale: 全球
      ongoing: true

    - id: scientific_vindication
      description_zh: 数十年双盲研究最终证明MSG在正常食用量下无害
      description_en: Decades of blinded studies ultimately proved MSG safe at normal levels
      type: 正面
      domain: 科学
      scale: 全球

    - id: western_umami_appropriation
      description_zh: 西方曾嘲讽味精的文化后来拥抱"鲜味"为高级烹饪概念
      description_en: Western culture that stigmatized MSG later embraced "umami" as haute cuisine
      type: 讽刺
      domain: 文化
      scale: 全球
      ongoing: true

  causal_chains:
    # 化合物 → 事件
    - source: msg
      target: ikeda_umami_discovery
      type: ENABLED
      drama_score: 0.80
      irony_level: 0.50
      description_zh: "一碗海带高汤引发的科学发现——酸甜苦咸之外的第五种味道"
      domains: [科学, 食品]

    - source: msg
      target: ajinomoto_commercial_1909
      type: ENABLED
      drama_score: 0.65
      irony_level: 0.30
      description_zh: "'味之素'开创了现代调味品工业"
      domains: [工业, 食品]
      time_lag_years: 1

    - source: msg
      target: chinese_restaurant_syndrome_letter
      type: ENABLED
      drama_score: 0.90
      irony_level: 0.95
      description_zh: "一封可能是恶作剧的读者来信，让一个安全的调味品背负了几十年的种族偏见骂名"
      description_en: "A possibly hoax letter burdened a safe seasoning with decades of racial stigma"
      domains: [文化, 种族, 媒体]

    - source: chinese_restaurant_syndrome_letter
      target: hoax_revelation
      type: IRONIC_TWIST
      drama_score: 0.88
      irony_level: 0.98
      description_zh: "50年后调查揭示：改变公众认知的那封信可能只是两个医生的赌注游戏"
      description_en: "50 years later: the letter that changed public perception may have been a bet between two doctors"
      domains: [媒体, 文化]
      time_lag_years: 50

    - source: msg
      target: fda_gras_status
      type: ENABLED
      drama_score: 0.60
      irony_level: 0.45
      description_zh: "FDA早在1958年就认定MSG安全——但公众恐慌持续了数十年不为所动"
      domains: [法律, 科学]

    - source: msg
      target: faseb_1995_report
      type: ENABLED
      drama_score: 0.70
      irony_level: 0.60
      description_zh: "大规模双盲试验反复得出同一结论：正常食用量的MSG不会引起任何症状——但公众依然恐惧"
      domains: [科学, 医学]

    - source: msg
      target: umami_finally_accepted
      type: ENABLED
      drama_score: 0.82
      irony_level: 0.80
      description_zh: "池田1908年就命名的'鲜味'，西方科学花了近一个世纪才正式承认——直到发现鲜味受体"
      description_en: "Ikeda named 'umami' in 1908 — it took nearly a century for Western science to formally accept it"
      domains: [科学, 文化]
      time_lag_years: 94

    # 事件 → 后果
    - source: ikeda_umami_discovery
      target: umami_revolution
      type: CAUSED
      drama_score: 0.75
      irony_level: 0.40
      description_zh: "第五种味觉重新定义了烹饪——如今每个米其林厨师都谈论'鲜味层次'"
      domains: [食品, 文化]

    - source: chinese_restaurant_syndrome_letter
      target: racial_food_stigma
      type: CAUSED
      drama_score: 0.88
      irony_level: 0.92
      description_zh: "一封来路不明的信建造了针对亚洲食品长达数十年的种族偏见——'中餐综合症'本身就是偏见"
      description_en: "A letter of dubious origin constructed decades of racial bias against Asian food"
      domains: [种族, 文化, 媒体]

    - source: faseb_1995_report
      target: scientific_vindication
      type: CAUSED
      drama_score: 0.75
      irony_level: 0.55
      description_zh: "科学最终为味精平反——但修正公众偏见比做实验难多了"
      domains: [科学]

    # 讽刺反转链
    - source: racial_food_stigma
      target: western_umami_appropriation
      type: IRONIC_TWIST
      drama_score: 0.92
      irony_level: 0.98
      description_zh: "同一个文化先嘲讽'中餐馆放味精太多'，后来又追捧'鲜味是高级料理的灵魂'——本质上是同一种化学物质"
      description_en: "Same culture first mocked Chinese restaurants for MSG, then celebrated 'umami' as haute cuisine — same chemical substance"
      domains: [文化, 种族, 食品]

    - source: chinese_restaurant_syndrome_letter
      target: scientific_vindication
      type: IRONIC_TWIST
      drama_score: 0.85
      irony_level: 0.90
      description_zh: "一封可能的恶作剧信引发了几十年的科学研究——结论是：信是假的，味精是安全的"
      domains: [科学, 媒体]

  cross_connections:
    - target_compound: ddt
      relationship_zh: "都经历了'先追捧后恐慌'的命运——但味精最终被科学平反"
      connection_type: 先追捧后质疑

    - target_compound: aspirin
      relationship_zh: "日常生活中渗透最深的两种化学品——一个缓解疼痛，一个增强滋味"
      connection_type: 日常渗透

```

---

# PART 3: 跨化合物因果连接

```yaml
# Omphalina — 跨化合物因果连接
# 描述 7 个化合物之间的关联关系

connections:
  # ============================================================
  # 同属双用途（和平/战争）
  # ============================================================
  - source_compound: synthetic_ammonia
    target_compound: ddt
    connection_type: 同属双用途
    relationship_zh: "两者都是农业化学品/军事化学品的双面刃：合成氨生产化肥也生产炸药，DDT保护军人也毒害生态"
    relationship_en: "Both are dual-use agricultural/military chemicals"
    drama_score: 0.90
    bidirectional: true

  # ============================================================
  # 同一发明者 / 同一实验室
  # ============================================================
  - source_compound: cfc
    target_compound: plastics
    connection_type: 同属环保危机
    relationship_zh: "石化工业的双胞胎灾难：氟利昂捅破天（臭氧层），塑料堵塞地（海洋污染）"
    relationship_en: "Petrochemical twin disasters: CFCs pierced the sky, plastics choked the earth"
    drama_score: 0.85
    bidirectional: true

  # ============================================================
  # 先追捧后质疑
  # ============================================================
  - source_compound: msg
    target_compound: ddt
    connection_type: 先追捧后质疑
    relationship_zh: "都经历了'先被追捧为科学奇迹，后遭公众恐慌性抵制'的命运，但味精最终被科学平反，DDT至今仍有争议"
    relationship_en: "Both went from 'scientific miracle' to public panic, but MSG was vindicated while DDT remains controversial"
    drama_score: 0.80
    bidirectional: true

  # ============================================================
  # 药物发现范式对比
  # ============================================================
  - source_compound: aspirin
    target_compound: penicillin
    connection_type: 药物范式对比
    relationship_zh: "药物发现的两条路：阿司匹林代表'化学合成'路线（从柳树皮到实验室），青霉素代表'自然发现'路线（霉菌的偶然馈赠）"
    relationship_en: "Two paradigms of drug discovery: aspirin (chemical synthesis) vs penicillin (natural discovery)"
    drama_score: 0.75
    bidirectional: true

  # ============================================================
  # 诺贝尔讽刺
  # ============================================================
  - source_compound: synthetic_ammonia
    target_compound: cfc
    connection_type: 诺贝尔讽刺
    relationship_zh: "哈伯（合成氨）获1918诺贝尔奖后主导化学武器；DDT发明者穆勒获1948诺贝尔奖后DDT被全球禁用；CFC导致的臭氧层研究获1995诺贝尔奖——三个诺贝尔奖背后都是讽刺"
    relationship_en: "Three Nobel Prizes, three ironies: Haber (ammonia→chemical weapons), Müller (DDT→banned), Rowland/Molina (discovered CFC damage)"
    drama_score: 0.95
    bidirectional: true

  - source_compound: ddt
    target_compound: synthetic_ammonia
    connection_type: 诺贝尔讽刺
    relationship_zh: "DDT(1948诺贝尔奖)和合成氨(1918诺贝尔奖)的发明者都因'造福人类'获奖，后来都与生态/战争灾难联系在一起"
    relationship_en: "Both DDT and ammonia inventors won Nobels for 'benefiting humanity', both later linked to ecological/war disasters"
    drama_score: 0.92
    bidirectional: true

  # ============================================================
  # 战争催化
  # ============================================================
  - source_compound: penicillin
    target_compound: ddt
    connection_type: 战争催化
    relationship_zh: "二战同时催化了两者的量产：青霉素救治盟军伤兵，DDT保护盟军免受疟疾和伤寒——两种'战争英雄'的命运却截然不同"
    relationship_en: "WWII catalyzed mass production of both: penicillin healed soldiers, DDT protected them from disease — yet their fates diverged"
    drama_score: 0.88
    bidirectional: true

  # ============================================================
  # 个人悲剧的镜像
  # ============================================================
  - source_compound: synthetic_ammonia
    target_compound: aspirin
    connection_type: 个人悲剧
    relationship_zh: "发明者的个人悲剧：哈伯的妻子因抗议他参与化学武器而自杀；阿司匹林的（可能的）真正发明者艾兴格林因犹太身份被纳粹关入集中营"
    relationship_en: "Personal tragedies of inventors: Haber's wife committed suicide protesting his chemical weapons work; Eichengrün was imprisoned in a concentration camp"
    drama_score: 0.93
    bidirectional: true

  # ============================================================
  # 塑料与味精：日常生活的隐形统治者
  # ============================================================
  - source_compound: plastics
    target_compound: msg
    connection_type: 日常渗透
    relationship_zh: "两者都是20世纪初的发明，都无声地渗透了全人类的日常生活——塑料包裹我们的一切，味精藏在我们的每一口食物里"
    relationship_en: "Both early 20th century inventions silently permeated all of human daily life"
    drama_score: 0.65
    bidirectional: true

```

---

# PART 4: 因果图统计摘要

以下是从 NetworkX 因果图导出的统计摘要（原始图包含 125 节点、132 边）：

## 节点统计
- 总节点数: **125**
  - Compound: 7
  - Consequence: 28
  - Event: 63
  - Person: 27

## 边统计
- 总边数: **0**

## 高戏剧性因果边 TOP 0 (drama_score ≥ 0.85)
| # | 源节点 | → | 目标节点 | Drama | Irony | 类型 | 描述 |
|---|--------|---|----------|-------|-------|------|------|

## 高讽刺性因果边 TOP 0 (irony_level ≥ 0.85)
| # | 源节点 | → | 目标节点 | Irony | Drama | 类型 | 描述 |
|---|--------|---|----------|-------|-------|------|------|

---
