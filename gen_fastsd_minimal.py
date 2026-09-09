# -*- coding: utf-8 -*-
"""
兜底最小生成器：直接用 diffusers 加载本地 sd-turbo 权重出图。
仅在 FastSD CPU 的 app.py 因 gradio/controlnet 等导入链起不来时使用。
依赖：torch + diffusers + transformers + accelerate + pillow（比 FastSD CPU 全套轻）
用法：
  .venv\Scripts\python.exe gen_fastsd_minimal.py --demo
"""
import os, sys, time
sys.path.insert(0, r'F:/投标AI知识库变现项目/wan21/孙小空明末镇魔录')
from gen_fastsd import DEMO_SCENES, LOCAL_MODEL, W, H, NEG

ROOT = r'F:/投标AI知识库变现项目/wan21/孙小空明末镇魔录'
IMG_DIR = os.path.join(ROOT, 'img_fastsd')
os.makedirs(IMG_DIR, exist_ok=True)

def main():
    import torch
    from diffusers import StableDiffusionPipeline, AutoPipelineForText2Image
    print("加载本地模型:", LOCAL_MODEL)
    dummy = StableDiffusionPipeline.from_single_file(
        LOCAL_MODEL, safety_checker=None, run_safety_checker=False,
        load_safety_checker=False, use_safetensors=True)
    pipe = AutoPipelineForText2Image.from_pipe(dummy)
    del dummy
    pipe.to("cpu")
    print("模型就绪")
    manifest = []
    for i, (name, prompt) in enumerate(DEMO_SCENES, 1):
        f = os.path.join(IMG_DIR, "demo_%02d.png" % i)
        print("[%d/6] %s" % (i, name))
        seed = int(time.time() * 1000) % 10**9
        g = torch.manual_seed(seed)
        # sd-turbo 推荐 1 步、guidance 1.0
        img = pipe(prompt, negative_prompt=NEG, num_inference_steps=1,
                   guidance_scale=1.0, width=W, height=H,
                   generator=g).images[0]
        img.save(f, "PNG")
        print("  ->", f, "seed=%d" % seed)
        manifest.append({"name": name, "prompt": prompt, "image": f, "seed": seed})
    import json
    json.dump(manifest, open(os.path.join(ROOT, "scenes_ep001_fastsd.json"),
                             'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print("完成")

if __name__ == '__main__':
    main()
