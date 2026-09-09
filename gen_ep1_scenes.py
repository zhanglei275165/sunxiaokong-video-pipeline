#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
孙小空明末镇魔录 第一集 -> 生成「一盘胶卷」所需的连续画面
================================================================
1. 解析 srt/ep_001.srt 拿到每条字幕起止时间
2. 把第一集剧情拆成 14 幕(scene)，每幕对齐到字幕时间区间
3. 每幕用 Pollinations 免费生图(720x1280 竖版/去水印)，零成本、不占本机算力
4. 输出 img/ep001_scene_XX.png + scenes_ep001.json(图片路径+每幕起止秒)

用法:
  python gen_ep1_scenes.py            # 生成全部 14 幕
  python gen_ep1_scenes.py --check    # 只打印分幕时间，不联网
"""
import os, sys, re, json, time, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SRT = os.path.join(HERE, "srt", "ep_001.srt")
IMG_DIR = os.path.join(HERE, "img")
MANIFEST = os.path.join(HERE, "scenes_ep001.json")
STYLE = ("Chinese ink-wash animation style, muted earth tones, "
         "detailed linework, cinematic composition, ")

# 14 幕：对齐到 srt 字幕序号(1-based)，prompt 为英文(生图质量更稳)
SCENES = [
    (5, 18,  STYLE + "aerial view of war-torn Ming dynasty China 1642, barren scorched land, long lines of starving refugees fleeing, empty plague-stricken villages, famine, somber"),
    (19, 29, STYLE + "Sun Wukong as the Victorious Fighting Buddha seated on a cloud high in the sky, golden kasaya and pilu Buddhist hat, serene face with hidden sharpness, gazing down at the mortal world, warm golden light"),
    (30, 45, STYLE + "overhead view of starving peasants collapsed on a road, dead bodies, desolate villages, a compassionate Buddha eye watching from above, grim muted tones"),
    (46, 73, STYLE + "close-up of Sun Wukong on the cloud, hand raised pointing east, a faint golden thread of heavenly law, determined expression, divine aura"),
    (74, 94, STYLE + "a small golden-furred monkey napping by a mountain stream in Flower-Fruit Mountain, a beam of golden light descending from the sky, lush green paradise, cute and spirited"),
    (95, 119, STYLE + "a sleeping golden monkey, a glowing golden robed figure vaguely visible in golden light, ethereal dreamscape, mystical"),
    (120, 135, STYLE + "close-up of the small monkey waking up startled, a glowing golden book with floating Chinese characters appearing before his eyes, magical glow"),
    (136, 154, STYLE + "the golden monkey bowing to a troop of cheerful monkeys on Flower-Fruit Mountain, then leaping down the mountain path, farewell, lush green mountain"),
    (155, 164, STYLE + "Sun Xiaokong transformed into a handsome young scholar in human form, jade-like face, bright eyes, grey rough-spun robe, carrying a peach-wood staff, elegant"),
    (165, 177, STYLE + "outside Luoyang city gate 1642, a long line of ragged starving refugees, lazy soldiers leaning on spears, grim Ming dynasty"),
    (178, 199, STYLE + "inside a Ming dynasty rice shop, a trembling old man with a cloth bag of copper coins thrown down, a burly clerk pushing him away, tense crowd"),
    (200, 212, STYLE + "the handsome scholar clenching his peach-wood staff, eyes blazing with anger, a glowing golden book showing a quest floating before him, determined"),
    (213, 228, STYLE + "a line of covered grain carts rumbling through a Ming dynasty street at dusk, mysterious, the young scholar watching from afar"),
    (229, 247, STYLE + "the young scholar chasing the grain carts gripping his staff with a resolute smile, and in the crowd a ragged old Taoist priest in tattered robe squinting after him, mysterious"),
]


def parse_srt(path):
    """返回 {idx: (start_sec, end_sec)}"""
    txt = open(path, encoding="utf-8", errors="ignore").read()
    blocks = re.split(r"\n\s*\n", txt.strip())
    out = {}
    for b in blocks:
        lines = [l for l in b.splitlines() if l.strip()]
        if len(lines) < 3:
            continue
        try:
            idx = int(lines[0].strip())
        except Exception:
            continue
        m = re.match(r"(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+)", lines[1])
        if not m:
            continue
        def sec(a, b, c, d):
            return int(a) * 3600 + int(b) * 60 + int(c) + int(d) / 1000.0
        s = sec(*m.groups()[:4])
        e = sec(*m.groups()[4:])
        out[idx] = (s, e)
    return out


def gen_image(prompt, out_path, seed, timeout=60):
    """用 Pollinations 免费通道生图；返回 True/False。失败时重试由调用方处理。"""
    from urllib.parse import quote
    url = ("https://image.pollinations.ai/prompt/%s?width=720&height=1280"
           "&nologo=true&model=flux&seed=%d" % (quote(prompt), seed))
    cmd = ["curl", "-sS", "-L", "-m", str(timeout), "-o", out_path, "-w",
           "HTTP=%{http_code}", url]
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=timeout + 20)
    except Exception as ex:
        print("  [curl异常] %s" % ex)
        return False
    # 校验文件有效
    if not os.path.exists(out_path) or os.path.getsize(out_path) < 3000:
        print("  [无效图] 大小不足, 删除")
        try:
            os.remove(out_path)
        except Exception:
            pass
        return False
    head = open(out_path, "rb").read(8)
    if head[:3] == b"\xff\xd8\xff" or head[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    print("  [非图片] magic=%r, 删除" % head)
    try:
        os.remove(out_path)
    except Exception:
        pass
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只打印分幕时间")
    args = ap.parse_args()

    subs = parse_srt(SRT)
    print("[SRT] 共 %d 条字幕, 时间轴 %.1fs" % (len(subs), subs[max(subs)][1]))

    spans = []
    for (a, b, prompt) in SCENES:
        s = subs[a][0]
        e = subs[b][1]
        spans.append((a, b, s, e, prompt))
        print("  幕 %02d  字幕[%02d-%02d]  %6.2fs ~ %6.2fs  (%.2fs)" %
              (len(spans), a, b, s, e, e - s))

    if args.check:
        return

    os.makedirs(IMG_DIR, exist_ok=True)
    man = []
    for i, (a, b, s, e, prompt) in enumerate(spans, 1):
        out_path = os.path.join(IMG_DIR, "ep001_scene_%02d.png" % i)
        ok = False
        for attempt in range(1, 7):
            seed = i * 1000 + attempt
            print("[生图] 幕 %02d 尝试 %d -> %s" % (i, attempt, os.path.basename(out_path)))
            if gen_image(prompt, out_path, seed):
                ok = True
                break
            time.sleep(3)
        if not ok:
            print("  [失败] 幕 %02d 放弃" % i)
            continue
        man.append({"scene": i, "sub_start": a, "sub_end": b,
                    "start": round(s, 3), "end": round(e, 3),
                    "image": out_path, "prompt": prompt})
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1)
    print("\n[完成] %d/%d 幕生图成功 -> %s" % (len(man), len(SCENES), MANIFEST))


if __name__ == "__main__":
    main()
