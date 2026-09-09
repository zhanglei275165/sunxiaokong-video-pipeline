#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
孙小空明末镇魔录 第一集 -> 真·胶卷视频
================================================================
一盘胶卷 = 片头 + 14 幕连续画面，每幕按字幕时间点切换，
缓慢推拉运镜(胶卷转盘感) + 交叉淡入，再 + 整集语音合成。

依赖: 先跑 gen_ep1_scenes.py 生成 scenes_ep001.json 与 img/ep001_scene_XX.png
"""
import os, sys, json

from film_mode import make_film

BASE = r"F:\投标AI知识库变现项目\wan21\孙小空明末镇魔录"
MANIFEST = os.path.join(BASE, "scenes_ep001.json")
INTRO = os.path.join(BASE, "intro_card.png")
AUDIO = os.path.join(BASE, "audio", "ep_001.mp3")
OUT = os.path.join(BASE, "video", "孙小空明末镇魔录_第一集_胶卷.mp4")

T = 1.0  # 交叉淡入时长(秒)


def main():
    if not os.path.exists(MANIFEST):
        raise SystemExit("先跑 gen_ep1_scenes.py 生成画面与 manifest")
    man = json.load(open(MANIFEST, encoding="utf-8"))
    if not man:
        raise SystemExit("manifest 为空，生图可能失败")

    # 组装有序画面: 片头 + 14 幕
    seq = []  # (image, span_start, span_end)
    if os.path.exists(INTRO):
        seq.append((INTRO, 0.0, man[0]["start"]))
    for m in man:
        seq.append((m["image"], m["start"], m["end"]))

    images = [s[0] for s in seq]
    # 每幕时长 = 字幕跨度 + 过渡时长；xfade 偏移 = 前序累计跨度，
    # 使每幕切换点精确落在字幕时间上(见 film_mode 注释)
    durations = ["%.3f" % (s[2] - s[1] + T) for s in seq]
    total = sum(float(d) for d in durations) - (len(images) - 1) * T
    print("[合成] %d 幕(含片头), 预计视频时长 %.1fs" % (len(images), total))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    make_film(
        images, AUDIO, OUT,
        duration=None,            # 用 durations 覆盖
        durations=durations,
        transition=T,
        kenburns=True,
        kb_zoom=1.12,             # 每幕缓缓推近 12%(胶卷转盘感, 不糊)
        resolution="720x1280",
        fps=30,
        crf=23,
    )
    print("完成 ->", OUT)


if __name__ == "__main__":
    main()
