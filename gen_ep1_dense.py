# -*- coding: utf-8 -*-
"""
第一集高密度连续画面生成（"胶卷"模式）。
把 247 条字幕按 step=2 聚合成 ~124 个连续镜头，每个镜头对齐到旁白时间，
用 Pollinations 免费通道生成 720x1280 竖版图（去水印/flux），转真 PNG。
输出 img_dense/ep001_dNNN.png + scenes_ep001_dense.json（image/start/end/text）。
"""
import os, re, json, sys, time, urllib.parse, subprocess
from PIL import Image

ROOT = r'F:/投标AI知识库变现项目/wan21/孙小空明末镇魔录'
IMG_DIR = os.path.join(ROOT, 'img_dense')
os.makedirs(IMG_DIR, exist_ok=True)
SRT = os.path.join(ROOT, 'srt', 'ep_001.srt')
MANIFEST = os.path.join(ROOT, 'scenes_ep001_dense.json')

STYLE = ("中国古代水墨画，明末乱世，电影感竖构图，细腻笔触，暖褐与青灰色调，"
         "人物有神，场景有纵深，")

def parse_srt(path):
    txt = open(path, encoding='utf-8').read()
    blocks = re.split(r'\n\s*\n', txt.strip())
    subs = []
    for b in blocks:
        lines = b.strip().split('\n')
        if len(lines) < 3:
            continue
        m = re.match(r'(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)', lines[1])
        if not m:
            continue
        def ts(a, b, c, d):
            return int(a) * 3600 + int(b) * 60 + int(c) + int(d) / 1000
        start = ts(*m.groups()[:4])
        end = ts(*m.groups()[4:])
        text = ' '.join(lines[2:]).strip()
        subs.append((start, end, text))
    return subs

def gen_image(prompt, out_path, w=720, h=1280, retries=4):
    q = urllib.parse.quote(prompt)
    seed = int(time.time() * 1000) % 100000
    url = ("https://image.pollinations.ai/prompt/%s?width=%d&height=%d&nologo=true&model=flux&seed=%d"
           % (q, w, h, seed))
    for _ in range(retries):
        try:
            r = subprocess.run(['curl', '-sS', '-m', '45', '-o', out_path, url],
                               capture_output=True)
            if r.returncode == 0 and os.path.getsize(out_path) > 3000:
                im = Image.open(out_path).convert('RGB')
                im = im.resize((w, h), Image.LANCZOS)
                im.save(out_path, 'PNG')
                return True
        except Exception:
            time.sleep(2)
        time.sleep(1.5)
    return False

def main():
    subs = parse_srt(SRT)
    # 前 10 秒是 intro_card 片头，正片镜头从 9.5s 之后开始，避免与片头重叠
    subs = [s for s in subs if s[0] >= 9.5]
    print('字幕条数(正片)', len(subs))
    step = 2
    scenes = []
    for i in range(0, len(subs), step):
        grp = subs[i:i + step]
        start = grp[0][0]
        end = grp[-1][1]
        text = ' '.join(g[2] for g in grp)
        prompt = STYLE + text
        scenes.append({'idx': len(scenes) + 1, 'start': round(start, 3),
                       'end': round(end, 3), 'text': text, 'prompt': prompt})
    print('镜头数', len(scenes))

    done = 0
    for s in scenes:
        fname = "ep001_d%03d.png" % s['idx']
        fpath = os.path.join(IMG_DIR, fname)
        s['image'] = fpath
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            print('skip', fname)
            done += 1
            continue
        ok = gen_image(s['prompt'], fpath)
        done += 1
        print(('%d/%d %s' % (done, len(scenes), 'OK' if ok else 'FAIL')), fname,
              s['text'][:18])
        time.sleep(0.4)
    json.dump(scenes, open(MANIFEST, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('manifest written, 镜头=%d' % len(scenes))

if __name__ == '__main__':
    main()
