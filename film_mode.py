#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
胶卷模式视频合成 (Film Mode)
===========================
多张图片 + 音频 -> mp4。
完全复刻「胶卷」本质：连续静帧 + 转盘投影(交叉淡入) + 缓慢运镜(Ken Burns)。
纯 CPU / ffmpeg，零 GPU、零矩阵乘法负担，低配机无压力。

用法:
    python film_mode.py --images 1.jpg 2.jpg 3.jpg --audio bg.mp3 --out out.mp4
或作为模块:
    from film_mode import make_film
    make_film(["1.jpg","2.jpg"], "bg.mp3", "out.mp4", duration=4.0, kenburns=True)
    # duration=None 时按音频时长自动平分每图显示时长(最适合「多图+整段语音」)
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile


def get_ffmpeg():
    """优先用 imageio-ffmpeg 自带二进制，否则用系统 ffmpeg。"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    raise RuntimeError("未找到 ffmpeg：请 pip install imageio-ffmpeg 或安装系统 ffmpeg")


def _parse_res(res):
    w, h = res.lower().split("x")
    return int(w), int(h)


def _kb_filt(W, H, kb_zoom, duration):
    """流式 Ken Burns 运镜：把图放大 kb_zoom 倍后，crop 窗口随时间 t 缓慢平移，
    形成「推近+平移」的胶卷转盘感。
    关键：不用 zoompan（长视频会整段缓冲到内存 -> OOM），改用 crop 的 t 表达式，
    单帧流式处理，176 秒长片也安全。"""
    sw, sh = int(round(W * kb_zoom)), int(round(H * kb_zoom))
    D = max(0.1, float(duration))
    return ("scale=%d:%d:force_original_aspect_ratio=increase," % (sw, sh) +
            "crop=%d:%d:x='(iw-ow)*(t/%f)':y='(ih-oh)*(t/%f)*0.5',setsar=1" % (W, H, D, D))


def get_audio_duration(audio):
    """解析音频时长(秒)，兼容无 ffprobe 的环境。"""
    ffmpeg = get_ffmpeg()
    out = subprocess.run([ffmpeg, "-i", audio], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    txt = out.stderr.decode("utf-8", "ignore")
    for line in txt.splitlines():
        if "Duration" in line:
            # Duration: 00:08:48.34, start: ...
            try:
                t = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = t.split(":")
                return int(h) * 3600 + int(m) * 60 + float(s)
            except Exception:
                pass
    return None


def _run(cmd):
    print("[film_mode] 执行 ffmpeg ...")
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", "ignore")
        raise RuntimeError("ffmpeg 失败(%d):\n%s" % (p.returncode, err[-1500:]))
    print("[film_mode] 完成")


def make_film(images, audio, out,
              duration=None, transition=1.0, kenburns=True,
              kb_zoom=1.10, resolution="1080x1920", fps=30, crf=23,
              durations=None):
    """
    合成胶卷风格视频。
    :param images: 图片路径列表(按顺序)
    :param audio:  背景音频路径
    :param out:    输出 mp4 路径
    :param duration: 每张图时长(秒)。None/<=0 时按音频时长自动平分每图显示时长。
    :param transition: 交叉淡入时长(秒)
    :param kenburns: 是否开启缓慢推拉运镜(胶卷转盘感)
    :param kb_zoom: 每张图在其显示时长内总共推近的总倍率(1.10=推近10%)。
                    与显示时长无关，避免长图糊掉、短图没动感。
    :param resolution: 输出分辨率 WxH
    :param fps: 帧率
    :param crf: 画质(越低越好)
    :param durations: 每图独立时长(秒)列表，长度须等于 images。提供时覆盖 duration，
                      用于「画面随旁白时间点切换」的精确对齐(每幕切到字幕对应时刻)。
    """
    if not images:
        raise ValueError("images 不能为空")
    if not audio or not os.path.exists(audio):
        raise ValueError("audio 不存在: %s" % audio)
    for im in images:
        if not os.path.exists(im):
            raise ValueError("图片不存在: %s" % im)

    ffmpeg = get_ffmpeg()
    W, H = _parse_res(resolution)
    n = len(images)
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    # 计算每图时长
    if durations and len(durations) == n:
        durs = [float(x) for x in durations]
        total = sum(durs)
        print("[film_mode] 逐图时长: 共 %.2fs, %d 张, 首张 %.2fs" % (total, n, durs[0]))
    elif not duration or duration <= 0:
        total = get_audio_duration(audio) or (n * 4.0)
        duration = (total + (n - 1) * transition) / n
        durs = [duration] * n
        print("[film_mode] 自动平分: 每图 %.2fs (音频 %.1fs, %d 张)" % (duration, total, n))
    else:
        total = duration * n - (n - 1) * transition
        durs = [duration] * n

    # 单图：直接缩放裁剪 + 可选运镜，配音频
    if n == 1:
        filt = "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,setsar=1" % (W, H, W, H)
        if kenburns:
            filt = _kb_filt(W, H, kb_zoom, total)
        cmd = [ffmpeg, "-y", "-loop", "1", "-i", images[0], "-i", audio,
               "-vf", filt,
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf),
               "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
        _run(cmd)
        return out

    # 多图：先每张渲染成独立片段 mp4(避免 zoompan 直接进 xfade 的时长 bug)，再做交叉淡入
    tmpdir = tempfile.mkdtemp(prefix="film_")
    segs = []
    try:
        for i, im in enumerate(images):
            seg = os.path.join(tmpdir, "seg%d.mp4" % i)
            d = durs[i]
            if kenburns:
                filt = _kb_filt(W, H, kb_zoom, d)
            else:
                filt = "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,setsar=1" % (W, H, W, H)
            cmd = [ffmpeg, "-y", "-loop", "1", "-t", "%.3f" % d, "-i", im,
                   "-vf", filt, "-t", "%.3f" % d, "-r", str(fps),
                   "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), seg]
            _run(cmd)
            segs.append(seg)

        # 串联 xfade。第 i 次过渡偏移 = 前 i 段累计时长 - i*过渡时长，段首尾正确重叠，
        # 使每幕切换点精确落在字幕时间上(逐图时长模式)
        inputs = []
        for s in segs:
            inputs += ["-i", s]
        pre = []
        chain = "[0:v]"
        cum = 0.0
        for i in range(1, n):
            cum += durs[i - 1]
            off = cum - i * transition
            nxt = "c%d" % (i - 1)
            pre.append("%s[%d:v]xfade=transition=fade:duration=%.3f:offset=%.3f[%s]"
                       % (chain, i, transition, off, nxt))
            chain = "[%s]" % nxt
        filter_complex = ";".join(pre)

        cmd = [ffmpeg, "-y"] + inputs + ["-i", audio,
               "-filter_complex", filter_complex,
               "-map", chain, "-map", "%d:a" % n,
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf),
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
        _run(cmd)
    finally:
        for s in segs:
            try:
                os.remove(s)
            except Exception:
                pass
        try:
            os.rmdir(tmpdir)
        except Exception:
            pass
    return out


def main():
    ap = argparse.ArgumentParser(description="胶卷模式: 多张图片+音频 -> mp4")
    ap.add_argument("--images", nargs="+", required=True, help="图片列表")
    ap.add_argument("--audio", required=True, help="背景音频")
    ap.add_argument("--out", required=True, help="输出 mp4")
    ap.add_argument("--duration", type=float, default=0.0,
                    help="每张图时长(秒)，0=按音频自动平分")
    ap.add_argument("--durations", default="",
                    help="每图独立时长(秒)，逗号分隔，如 3,5,4；提供时覆盖 --duration")
    ap.add_argument("--transition", type=float, default=1.0)
    ap.add_argument("--kb-zoom", type=float, default=1.10, help="每张图总推近倍率")
    ap.add_argument("--resolution", default="1080x1920")
    ap.add_argument("--no-kenburns", action="store_true")
    ap.add_argument("--fps", type=int, default=30)
    args = ap.parse_args()
    durs = None
    if args.durations.strip():
        durs = [float(x) for x in args.durations.split(",") if x.strip()]
    out = make_film(args.images, args.audio, args.out,
                    duration=args.duration, transition=args.transition,
                    kenburns=not args.no_kenburns, kb_zoom=args.kb_zoom,
                    resolution=args.resolution, fps=args.fps, durations=durs)
    print("OK ->", out)


if __name__ == "__main__":
    main()
