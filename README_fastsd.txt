孙小空明末镇魔录 · 本地生图方案（FastSD CPU / stable-diffusion.cpp）
==================================================================

为什么换这套方案？
-----------------
原来用 Pollinations 免费在线通道出图，图和剧情没关系，因为：
1) 在线免费模型对中文长 prompt 服从度差；
2) 直接把字幕原文当 prompt，没有抽取出"视觉主体/动作/场景"。

现在改用本地 sd-turbo（FastSD CPU 的底层引擎 stable-diffusion.cpp）：
- 本地可控，prompt 严格生效；
- 零 Python/torch 安装（就一个 sd-cli.exe）；
- 真机 GPU/Vulkan 下几秒钟一张；
- 英文视觉 prompt 含"角色圣经"，孙小空/大圣/老道 长相稳定。

已就绪文件
----------
F:\LugangAI-Source\tongyu_engine\bin\sdcpp\sd-cli.exe           (引擎)
F:\LugangAI-Source\fastsdcpu\models\sd-turbo\sd_turbo.safetensors (权重, ~5.2GB)
F:\投标AI知识库变现项目\wan21\孙小空明末镇魔录\gen_fastsd_sdcpp.py  (生成器)
F:\投标AI知识库变现项目\wan21\孙小空明末镇魔录\gen_fastsd.py        (prompt 与 6 幕定义)

双击运行
--------
run_fastsd_demo.bat   → 先生成 6 个关键画面（验证剧情相关性）
run_fastsd_ep001.bat  → 生成第一集全部 122 张连续画面

坑
--
1. sd-cli 不能直接把图片写到中文路径，所以脚本先把图写到 ASCII 临时名，再移回 img_fastsd/。
2. 沙箱里只能跑 --backend cpu；你真机有显卡/核显时，改成 vulkan0 会快很多。
3. 第一集已有 122 张在线图(img_dense)，但它们剧情相关度低；建议用本地 sd-turbo 重新出 122 张，再合成新视频。
