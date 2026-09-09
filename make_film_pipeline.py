# -*- coding: utf-8 -*-
"""
孙小空明末镇魔录 · 通用胶卷视频生产流水线
=========================================
一条命令完成：分镜 -> 连续图片 -> 语音合成视频。

用法:
  # 在线免费通道生图(默认，零成本，不占本机算力)
  python make_film_pipeline.py --ep 001

  # 本地 SD.cpp 生图(需自备引擎+权重，离线/一致/快)
  python make_film_pipeline.py --ep 001 --backend sdcpp --sdcpp "D:/sd.cpp/sd.exe" --ckpt "D:/models/sd15.safetensors"

  # 批量生产第二~三十六集
  for %i in (002 003 ... 036) do python make_film_pipeline.py --ep %i

输出:
  img_{ep}/ep{ep}_dNNN.png   连续画面
  scenes_{ep}.json           分镜 manifest
  video/孙小空明末镇魔录_第{ep}集_胶卷.mp4  成品
"""
import argparse, os, re, json, sys, time, urllib.parse, subprocess
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
from film_mode import make_film

STYLE = ("中国古代水墨画，明末乱世，电影感竖构图，细腻笔触，暖褐与青灰色调，"
         "人物有神，场景有纵深，")

W, H = 720, 1280
INTRO_SEC = 10.0
T = 0.5  # 交叉淡入时长


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
        subs.append((ts(*m.groups()[:4]), ts(*m.groups()[4:]), ' '.join(lines[2:]).strip()))
    return subs


def plan_shots(srt_path, step=2):
    """把字幕按 step 聚合成连续镜头，跳过片头声明(前 INTRO_SEC 秒)。"""
    subs = [s for s in parse_srt(srt_path) if s[0] >= INTRO_SEC - 0.5]
    shots = []
    for i in range(0, len(subs), step):
        grp = subs[i:i + step]
        shots.append({'start': round(grp[0][0], 3), 'end': round(grp[-1][1], 3),
                      'text': ' '.join(g[2] for g in grp)})
    return shots


def gen_pollinations(prompt, out_path, retries=4):
    """在线免费通道(flux)，返回即转真 PNG 720x1280。"""
    q = urllib.parse.quote(prompt)
    seed = int(time.time() * 1000) % 100000
    url = "https://image.pollinations.ai/prompt/%s?width=%d&height=%d&nologo=true&model=flux&seed=%d" % (q, W, H, seed)
    for _ in range(retries):
        try:
            r = subprocess.run(['curl', '-sS', '-m', '45', '-o', out_path, url], capture_output=True)
            if r.returncode == 0 and os.path.getsize(out_path) > 3000:
                im = Image.open(out_path).convert('RGB')
                im = im.resize((W, H), Image.LANCZOS)
                im.save(out_path, 'PNG')
                return True
        except Exception:
            time.sleep(2)
        time.sleep(1.5)
    return False


def gen_sdcpp(prompt, out_path, engine, ckpt, steps=25, cfg=7.0, seed=-1):
    """本地 SD.cpp 生图(需自备 engine 可执行 + ckpt 权重)。离线、快、可挂角色 LoRA。"""
    cmd = [engine, '-m', ckpt, '-p', prompt, '-o', out_path,
           '-W', str(W), '-H', str(H), '--steps', str(steps),
           '--cfg-scale', str(cfg), '-s', str(seed)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 3000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ep', required=True, help='集数, 如 001')
    ap.add_argument('--backend', default='pollinations', choices=['pollinations', 'sdcpp'])
    ap.add_argument('--step', type=int, default=2, help='每几条字幕合成一个镜头(越小越密)')
    ap.add_argument('--sdcpp', default='', help='本地 sd.cpp 可执行路径(backend=sdcpp 时必填)')
    ap.add_argument('--ckpt', default='', help='本地模型权重路径(backend=sdcpp 时必填)')
    args = ap.parse_args()

    img_dir = os.path.join(ROOT, 'img_%s' % args.ep)
    os.makedirs(img_dir, exist_ok=True)
    srt = os.path.join(ROOT, 'srt', 'ep_%s.srt' % args.ep)
    audio = os.path.join(ROOT, 'audio', 'ep_%s.mp3' % args.ep)
    intro = os.path.join(ROOT, 'intro_card.png')
    manifest = os.path.join(ROOT, 'scenes_%s.json' % args.ep)
    out = os.path.join(ROOT, 'video', '孙小空明末镇魔录_第%s集_胶卷.mp4' % args.ep)

    if not os.path.exists(srt):
        print('缺失字幕:', srt); return
    if not os.path.exists(audio):
        print('缺失音频:', audio); return

    shots = plan_shots(srt, args.step)
    print('[%s] 镜头数=%d 后端=%s' % (args.ep, len(shots), args.backend))

    for k, s in enumerate(shots, 1):
        fname = 'ep%s_d%03d.png' % (args.ep, k)
        fpath = os.path.join(img_dir, fname)
        s['image'] = fpath
        if os.path.exists(fpath) and os.path.getsize(fpath) > 5000:
            continue
        prompt = STYLE + s['text']
        ok = (gen_sdcpp(prompt, fpath, args.sdcpp, args.ckpt) if args.backend == 'sdcpp'
              else gen_pollinations(prompt, fpath))
        print('%d/%d %s' % (k, len(shots), 'OK' if ok else 'FAIL'), fname, s['text'][:16])
        time.sleep(0.4)
    json.dump(shots, open(manifest, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    seq = [(intro, 0.0, INTRO_SEC)] + [(s['image'], s['start'], s['end']) for s in shots]
    images = [x[0] for x in seq]
    durations = ['%.3f' % (x[2] - x[1] + T) for x in seq]
    make_film(images, audio, out, durations=durations, transition=T,
              kenburns=True, kb_zoom=1.08, resolution='%dx%d' % (W, H), fps=30, crf=23)
    print('DONE size=', os.path.getsize(out), out)


if __name__ == '__main__':
    main()
