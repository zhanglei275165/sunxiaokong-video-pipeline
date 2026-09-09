# -*- coding: utf-8 -*-
"""
孙小空明末镇魔录 · 本地生图（stable-diffusion.cpp / sd-cli 后端）
============================================================
这是 FastSD CPU 底层真正用的引擎（stable-diffusion.cpp），独立 exe、零 Python/零 torch 安装。
- 沙箱无 GPU：--backend cpu（慢，约 3 分钟/张，仅用于验证）
- 用户真机有 GPU：--backend vulkan0（几秒/张）

关键坑：sd-cli 是 C++ 程序，Windows 下写"中文路径"会失败 → 输出先写 ASCII 临时名，再移回项目目录。

用法：
  python gen_fastsd_sdcpp.py --demo            # 6 个关键幕(沙箱/真机都能跑)
  python gen_fastsd_sdcpp.py --ep 001          # 字幕驱动整集
  python gen_fastsd_sdcpp.py --demo --backend vulkan0   # 真机 GPU 加速
"""
import os, sys, time, shutil, subprocess, argparse, json
sys.path.insert(0, r'F:/投标AI知识库变现项目/wan21/孙小空明末镇魔录')
from gen_fastsd import DEMO_SCENES, LOCAL_MODEL, W, H, NEG, build_prompt

ROOT = r'F:/投标AI知识库变现项目/wan21/孙小空明末镇魔录'
IMG_DIR = os.path.join(ROOT, 'img_fastsd')
os.makedirs(IMG_DIR, exist_ok=True)
SDCPP_EXE = r'F:/LugangAI-Source/tongyu_engine/bin/sdcpp/sd-cli.exe'
MODEL = LOCAL_MODEL  # sd-turbo 权重
TMP_OUT = r'F:/LugangAI-Source/tongyu_engine/bin/sdcpp/_gen_tmp.png'

def gen_one(prompt, seed, backend, threads=4, steps=1, cfg=1.0):
    cmd = [SDCPP_EXE, '--backend', backend, '-t', str(threads),
           '-m', MODEL, '-p', prompt, '-n', NEG,
           '-o', TMP_OUT, '-W', str(W), '-H', str(H),
           '--steps', str(steps), '--cfg-scale', str(cfg), '--seed', str(seed)]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, encoding='utf-8', errors='replace')
    return r.returncode == 0 and os.path.exists(TMP_OUT) and os.path.getsize(TMP_OUT) > 3000

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--demo', action='store_true')
    ap.add_argument('--ep', default=None)
    ap.add_argument('--backend', default='cpu', help='cpu(沙箱) 或 vulkan0(真机GPU)')
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--start', type=int, default=1, help='从第几个场景开始(用于断点续跑)')
    a = ap.parse_args()

    manifest_path = os.path.join(ROOT, "scenes_ep001_fastsd.json")
    manifest = []
    if os.path.exists(manifest_path):
        try:
            manifest = json.load(open(manifest_path, encoding='utf-8'))
        except Exception:
            manifest = []

    if a.demo or not a.ep:
        scenes = DEMO_SCENES[a.start-1:] if a.start > 1 else DEMO_SCENES
        for i, (name, prompt) in enumerate(scenes, a.start):
            final = os.path.join(IMG_DIR, "demo_%02d.png" % i)
            print("[%d/6] %s" % (i, name))
            seed = 1000 + i
            if not gen_one(prompt, seed, a.backend, a.threads):
                print("  !! 失败"); continue
            shutil.copy2(TMP_OUT, final)  # copy 不删临时文件，避开沙箱批量删除守卫
            print("  ->", final)
            manifest.append({"name": name, "prompt": prompt, "image": final, "seed": seed})
        json.dump(manifest, open(manifest_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print("完成 %d 张" % len(manifest))
        return

    # 整集（沿用 gen_fastsd 的字幕解析）
    from gen_fastsd import parse_srt, SRT
    subs = [s for s in parse_srt(SRT) if s[0] >= 9.5]
    step = 2
    scenes = []
    for i in range(0, len(subs), step):
        grp = subs[i:i+step]
        text = ' '.join(g[2] for g in grp)
        scenes.append({'idx': len(scenes)+1, 'prompt': build_prompt(text)})
    for s in scenes:
        final = os.path.join(IMG_DIR, "ep%s_d%03d.png" % (a.ep, s['idx']))
        print("[%d/%d]" % (s['idx'], len(scenes)))
        seed = 1000 + s['idx']
        if not gen_one(s['prompt'], seed, a.backend, a.threads):
            print("  !! 失败"); continue
        shutil.copy2(TMP_OUT, final)  # copy 不删临时文件，避开沙箱批量删除守卫
        s['image'] = final; s['seed'] = seed
        manifest.append(s)
    json.dump(manifest, open(manifest_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print("完成 %d 张" % len(manifest))

if __name__ == '__main__':
    main()
