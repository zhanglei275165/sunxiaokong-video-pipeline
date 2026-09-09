# 孙小空明末镇魔录 · 本地零成本 AI 视频生成流水线

一条**零成本、纯本地**的「连续图片生产 → 语音合成视频」流水线，用于把《孙小空明末镇魔录》做成"胶卷模式"真视频（多张连续画面 + 配音合成成片）。

> 为什么做这个：高质量 AI 视频（可灵 / 即梦 / Sora）依赖云端海量数据训练的大模型，个人无海量数据无法复现。本仓库走"本地小模型 + 开源工具"路线，把整条流水线脚本化，零经济投入即可跑通。

## 流水线构成

1. **剧本 / 大纲**：`gen_outlines.py`、`outline_600.json`、`episodes.json`、`rules.json` — 故事设定与分集场景数据。
2. **本地生图**：`gen_fastsd.py` / `gen_fastsd_sdcpp.py` / `gen_fastsd_minimal.py` — 调用本地 Stable Diffusion（SD1.5 基础模型 + `sd-cli` / Stable Diffusion.cpp）按剧情幕生成连续画面；`run_fastsd_demo.bat` / `run_fastsd_ep001.bat` 为真机一键脚本。
3. **配音 + 合成**：`make_film_pipeline.py` / `make_ep1_film.py` / `make_ep1_film_dense.py` — 把图片序列 + 字幕/语音合成为视频。

## 快速开始（生图）

```bat
:: 真机（Windows，需本地 sd-cli + SD1.5 权重）
run_fastsd_demo.bat      :: 生成 6 个关键剧情画面做验证
run_fastsd_ep001.bat     :: 生成第一集全部连续画面
```

`gen_fastsd_sdcpp.py` 关键参数：`--backend cpu|vulkan0`、`--threads N`、`--steps 25`、`--start N`（断点续跑）。

## 已知局限（诚实说明）

- 本地 SD1.5 基础模型**训练数据里中国神话人物占比极少**，直接生图孙悟空形象不稳定（多手 / 脸崩）。**待补一个「孙悟空 / 西游记」LoRA** 锁定角色形象。
- 成片视频、音频、私人素材库等体积较大，**未纳入本仓库**（见 `.gitignore`）。

## 仓库结构（源码）

```
├── gen_outlines.py          剧本/大纲生成
├── outline_600.json         600集大纲数据
├── episodes.json            分集场景
├── rules.json               角色/自称/禁词规则
├── gen_fastsd.py            生图 prompt 构造 + FastSD CPU API 调用
├── gen_fastsd_sdcpp.py      直接调用 sd-cli 生图（推荐）
├── gen_fastsd_minimal.py    diffusers 兜底生图
├── make_film_pipeline.py    图片+配音合成视频流水线
├── make_ep1_film.py         第一集合成
├── run_fastsd_demo.bat      生图验证一键脚本
├── run_fastsd_ep001.bat     第一集生图一键脚本
├── README_fastsd.txt        生图方案与坑记录
├── 大纲_600集_v1.md         故事大纲文档
├── 故事设定v1.0.md          世界观设定
└── img_fastsd/              生图验证样张（demo_*.png）
```

## 许可

MIT —— 自由使用、修改、再分发。
