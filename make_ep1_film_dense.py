# -*- coding: utf-8 -*-
"""高密度版合成：片头 + ~124 张连续画面 + 整集语音，调 film_mode.make_film。"""
import os, sys, json
from film_mode import make_film

ROOT = r'F:/投标AI知识库变现项目/wan21/孙小空明末镇魔录'
INTRO = os.path.join(ROOT, 'intro_card.png')
MANIFEST = os.path.join(ROOT, 'scenes_ep001_dense.json')
AUDIO = os.path.join(ROOT, 'audio', 'ep_001.mp3')
OUT = os.path.join(ROOT, 'video', '孙小空明末镇魔录_第一集_胶卷.mp4')

T = 0.5  # 交叉淡入时长
scenes = json.load(open(MANIFEST, encoding='utf-8'))
seq = [(INTRO, 0.0, 10.0)] + [(s['image'], s['start'], s['end']) for s in scenes]
images = [s[0] for s in seq]
durations = ['%.3f' % (s[2] - s[1] + T) for s in seq]
total = sum(float(d) for d in durations) - (len(images) - 1) * T
print('[合成] %d 段(含片头), 预计 %.1fs' % (len(images), total))
make_film(images, AUDIO, OUT, durations=durations, transition=T,
          kenburns=True, kb_zoom=1.08, resolution='720x1280', fps=30, crf=23)
print('DENSE FILM DONE size=', os.path.getsize(OUT))
