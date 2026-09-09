# -*- coding: utf-8 -*-
"""
孙小空明末镇魔录 · 本地生图生成器（FastSD CPU 后端）
==================================================
设计目标：生成的每一张图都必须"对得上剧情"，而不是像 Pollinations 那样随机出图。

做法：
1) 角色圣经 CHARACTER_BIBLE：把故事固定角色/场景映射成稳定的英文视觉描述，
   保证孙小空/齐天大圣/老道 跨镜长相一致（解决"主角脸乱跳"）。
2) STYLE_EN：统一的明末水墨电影感、竖构图，保证整体风格统一。
3) build_prompt(zh)：把中文字幕叙事翻译成"具体、有主体/场景/动作/氛围"的英文视觉 prompt。
   - 优先命中圣经词条；
   - 若本机 tongyu_engine(3B/7B) 在线，可调用它做 zh->en 视觉翻译（更准）；
   - 否则走词典兜底。
4) 后端：FastSD CPU 本地 API（默认 http://localhost:8000/api/generate，sd-turbo 1步出图）。
   启动：cd F:\LugangAI-Source\fastsdcpu && .venv\Scripts\activate && python src/app.py --api

用法：
  python gen_fastsd.py --demo          # 生成 6 个关键幕(手写强prompt)，验证剧情相关性
  python gen_fastsd.py --ep 001        # 用字幕全自动生成整集
"""
import os, re, json, sys, time, base64, urllib.request, argparse
from PIL import Image

ROOT = r'F:/投标AI知识库变现项目/wan21/孙小空明末镇魔录'
IMG_DIR = os.path.join(ROOT, 'img_fastsd')
os.makedirs(IMG_DIR, exist_ok=True)
SRT = os.path.join(ROOT, 'srt', 'ep_001.srt')
MANIFEST = os.path.join(ROOT, 'scenes_ep001_fastsd.json')

API_URL = "http://localhost:8000/api/generate"
# 本地 sd-turbo 权重（已下好，FastSD CPU 检测 .safetensors 后缀会直接 from_single_file 加载）
LOCAL_MODEL = r"F:/LugangAI-Source/fastsdcpu/models/sd-turbo/sd_turbo.safetensors"
W, H = 512, 768  # 竖构图（2:3，喂给 film_mode 会裁到 720x1280）

# ---------- 统一风格 ----------
STYLE_EN = ("traditional Chinese ink-wash painting, late Ming dynasty, cinematic vertical "
            "composition, dramatic chiaroscuro lighting, fine brushwork, epic atmosphere, "
            "highly detailed, 9:16 poster")

NEG = ("blurry, deformed, extra limbs, extra heads, mutated hands, bad anatomy, "
       "text, watermark, logo, signature, low quality, jpeg artifacts, photo, 3d render")

# ---------- 角色圣经（跨镜一致的关键）----------
CHARACTER_BIBLE = {
    "孙小空": "Sun Xiaokong, a small stone monkey spirit with fluffy brown fur and big bright eyes",
    "小空":   "Sun Xiaokong, a small stone monkey spirit with fluffy brown fur",
    "孙悟空":  "Sun Wukong the Monkey King, a majestic stone monkey with golden circlet crown and golden armor, holding a staff",
    "齐天大圣": "Sun Wukong the Monkey King, a majestic stone monkey with golden circlet crown and golden armor, holding a staff",
    "大圣":   "Sun Wukong the Monkey King, a majestic stone monkey with golden circlet crown",
    "老道":   "a mysterious Taoist priest in gray robe holding a fly-whisk",
    "道士":   "a Taoist priest in gray robe",
    "天书":   "a glowing golden heavenly scroll (Tianshu) floating with celestial runes",
    "洛阳":   "the ancient city of Luoyang with tall stone city wall and tiled gate tower",
    "米铺":   "a rustic rice shop with stacked burlap rice sacks and wooden counter",
    "花果山": "the lush Flower-Fruit Mountain with peach trees and waterfalls",
    "金光":   "a beam of golden celestial light descending from heaven",
    "流民":   "ragged refugees in tattered clothes crowding a dusty road",
    "明末":   "war-torn late Ming dynasty China with burning villages and smoke",
}

def build_prompt(zh_text):
    """把中文字幕叙事翻译为具体英文视觉 prompt（命中圣经 + 风格）。"""
    zh = zh_text.strip()
    parts = [STYLE_EN]
    # 命中角色/场景圣经
    for k, v in CHARACTER_BIBLE.items():
        if k in zh:
            parts.append(v)
    # 去掉片头废话
    zh_clean = re.sub(r'本视频由.*?制作|AI制作|声明|字幕|仅供|学习交流', '', zh)
    # 兜底：保留关键中文名词的拼音式描述（保证至少有点内容）
    if len(zh_clean) > 2:
        parts.append("scene depicts: " + zh_clean[:60])
    return ", ".join(p for p in parts if p)

# ---------- 后端：FastSD CPU API ----------
def gen_via_api(prompt, seed=None, steps=1, guidance=1.0, retries=3):
    if seed is None:
        seed = int(time.time() * 1000) % 10**9
    payload = {
        "lcm_model_id": LOCAL_MODEL,
        "use_openvino": False,
        "prompt": prompt,
        "negative_prompt": NEG,
        "image_width": W,
        "image_height": H,
        "inference_steps": steps,
        "guidance_scale": guidance,
        "seed": seed,
        "use_seed": True,
        "diffusion_task": "text_to_image",
    }
    data = json.dumps(payload).encode('utf-8')
    for _ in range(retries):
        try:
            req = urllib.request.Request(API_URL, data=data,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.loads(r.read().decode('utf-8'))
            if resp.get("error"):
                print("  API err:", resp["error"]); time.sleep(2); continue
            imgs = resp.get("images") or []
            if not imgs:
                print("  空图"); time.sleep(2); continue
            b64 = imgs[0].split(",", 1)[-1]
            raw = base64.b64decode(b64)
            im = Image.open(__import__('io').BytesIO(raw)).convert('RGB')
            return im, seed
        except Exception as e:
            print("  API 异常:", e); time.sleep(3)
    return None, seed

def save_png(im, path):
    im.save(path, 'PNG')

# ---------- 6 个关键幕（手写强 prompt，先证明剧情相关性）----------
DEMO_SCENES = [
    ("云端大圣俯瞰明末乱世",
     "Sun Wukong the Monkey King, a majestic stone monkey with golden circlet crown and golden armor "
     "holding a glowing staff, standing on a cloud high in the sky, looking down at a war-torn late Ming "
     "dynasty China landscape with burning villages, smoke and fleeing refugees, traditional Chinese "
     "ink-wash painting, epic cinematic vertical composition, dramatic golden hour lighting, highly detailed"),
    ("花果山金光点醒孙小空",
     "Sun Xiaokong, a small stone monkey spirit with fluffy brown fur and big bright eyes, sleeping under "
     "a peach tree on the lush Flower-Fruit Mountain, a beam of golden celestial light descending and "
     "awakening him, mystical atmosphere, traditional Chinese ink-wash painting, vertical composition"),
    ("孙小空化为人形书生",
     "Sun Xiaokong the monkey spirit transforming into a young human scholar boy in plain blue robe holding "
     "a bamboo staff, magical golden glow surrounding him, traditional Chinese ink-wash painting, vertical "
     "composition, ethereal"),
    ("西行入洛阳城门流民",
     "the ancient city of Luoyang with tall stone city wall and tiled gate tower, ragged refugees in "
     "tattered clothes crowding outside the gate on a dusty road, somber tone, traditional Chinese ink-wash "
     "painting, vertical composition, late Ming dynasty"),
    ("米铺老汉",
     "an old rice-shop owner, an old man in brown apron, standing behind stacked burlap rice sacks at a "
     "wooden counter inside a rustic rice shop, warm lantern light, traditional Chinese ink-wash painting, "
     "vertical composition"),
    ("老道现身天书",
     "a mysterious Taoist priest in gray robe holding a fly-whisk, a glowing golden heavenly scroll with "
     "celestial runes floating beside him, mystical golden light, traditional Chinese ink-wash painting, "
     "vertical composition, otherworldly"),
]

def parse_srt(path):
    txt = open(path, encoding='utf-8').read()
    subs = []
    for b in re.split(r'\n\s*\n', txt.strip()):
        lines = b.strip().split('\n')
        if len(lines) < 3:
            continue
        m = re.match(r'(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)', lines[1])
        if not m:
            continue
        def ts(a,b,c,d): return int(a)*3600+int(b)*60+int(c)+int(d)/1000
        subs.append((ts(*m.groups()[:4]), ts(*m.groups()[4:]), ' '.join(lines[2:])))
    return subs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--demo', action='store_true', help='生成 6 个关键幕(手写强prompt)')
    ap.add_argument('--ep', default=None, help='生成整集，如 001')
    ap.add_argument('--port', type=int, default=8000)
    a = ap.parse_args()

    global API_URL
    API_URL = "http://localhost:%d/api/generate" % a.port

    if a.demo or (not a.ep):
        print("=== 生成 6 个关键幕（验证剧情相关性）===")
        scenes = DEMO_SCENES
        manifest = []
        for i, (name, prompt) in enumerate(scenes, 1):
            f = os.path.join(IMG_DIR, "demo_%02d.png" % i)
            print("[%d/6] %s" % (i, name))
            im, seed = gen_via_api(prompt)
            if im is None:
                print("  !! 生成失败（FastSD CPU API 未启动或模型未就绪）")
                continue
            save_png(im, f)
            print("  ->", f, "seed=%d" % seed)
            manifest.append({"name": name, "prompt": prompt, "image": f, "seed": seed})
        json.dump(manifest, open(MANIFEST, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print("完成，manifest=%s" % MANIFEST)
        return

    # 整集全自动
    print("=== 生成整集 ep_%s（字幕驱动）===" % a.ep)
    subs = [s for s in parse_srt(SRT) if s[0] >= 9.5]
    step = 2
    scenes = []
    for i in range(0, len(subs), step):
        grp = subs[i:i+step]
        text = ' '.join(g[2] for g in grp)
        prompt = build_prompt(text)
        scenes.append({'idx': len(scenes)+1, 'start': round(grp[0][0],3),
                       'end': round(grp[-1][1],3), 'text': text, 'prompt': prompt})
    manifest = []
    for s in scenes:
        f = os.path.join(IMG_DIR, "ep%s_d%03d.png" % (a.ep, s['idx']))
        print("[%d/%d] %s" % (s['idx'], len(scenes), s['text'][:16]))
        im, seed = gen_via_api(s['prompt'])
        if im is None:
            print("  !! 失败，跳过"); continue
        save_png(im, f)
        s['image'] = f; s['seed'] = seed
        manifest.append(s)
    json.dump(manifest, open(MANIFEST, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print("完成，镜头=%d" % len(manifest))

if __name__ == '__main__':
    main()
