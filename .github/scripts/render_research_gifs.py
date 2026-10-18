#!/usr/bin/env python3
"""Render restrained, reproducible GIF motion from the existing scientific SVG artwork.

The static SVG is the authoritative design. GIF motion highlights paths/dots
decoratively; it does not depict experimental data, prove a theorem, or change a
scientific claim. Python/Pillow/CairoSVG are used only for the visual export.
"""
from __future__ import annotations
import argparse
import io
import math
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw

COLORS = {
    "project-mgsc": (172, 145, 255),
    "project-assam": (69, 211, 195),
    "project-claim-evidence": (147, 176, 255),
    "project-msw": (75, 223, 183),
    "project-vele": (100, 177, 255),
    "project-egfr": (189, 147, 255),
    "project-agrr": (244, 179, 91),
    "project-conformal": (92, 195, 244),
    "project-operation-spectra": (89, 214, 248),
    "research-banner": (119, 191, 255),
    "repository-banner": (114, 193, 255)
}
PALETTE_BY_REPO = {
    "VELE-PowerGrid-Reproducibility": (89, 166, 255),
    "EGFR-Graph-QSAR-Reproducibility": (183, 137, 255),
    "Assam-Road-Inspection-Benchmark": (60, 202, 193),
    "Claim-Evidence-Consistency-Reproducibility": (102, 163, 251),
    "applicability-gated-molecular-ai": (237, 176, 83),
    "operation-marked-route-spectra": (104, 213, 250),
    "mutation-geodesic-shielding-protein-stability": (172, 152, 255),
    "global-msw-reliability-under-shift": (66, 214, 181),
    "PAPER-JCMM-reproducibility": (84, 180, 247),
}
FRAMES = 18
DURATION_MS = 200

def render(svg: Path, output: Path, *, project: str = "") -> None:
    source = svg.read_bytes()
    width = 960 if svg.stem == "research-banner" else (840 if svg.stem == "repository-banner" else 560)
    raster = cairosvg.svg2png(bytestring=source, output_width=width)
    base = Image.open(io.BytesIO(raster)).convert("RGBA")
    w, h = base.size
    col = COLORS.get(svg.stem, PALETTE_BY_REPO.get(project, (111, 190, 247)))
    palette = base.convert("RGB").quantize(colors=144, method=Image.Quantize.FASTOCTREE)
    frames = []
    # Motion stays near the artwork's right-hand side, at modest opacity.
    for t in range(FRAMES):
        phase = 2.0 * math.pi * t / FRAMES
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer, "RGBA")
        cx = int(w * .76)
        cy = int(h * .50)
        amplitude = max(8, round(h * .13))
        # A path of light encodes traversal, not direction-specific physical flow.
        coords = []
        for j in range(32):
            u = j / 31
            x = int(w * (.61 + .32*u))
            y = int(cy + amplitude * math.sin(u * 2.0 * math.pi + phase))
            coords.append((x, y))
        draw.line(coords, fill=(*col, 32), width=max(1, w//400))
        for k in range(3):
            u = ((t / FRAMES) + k/3) % 1.0
            x = int(w * (.61 + .32*u))
            y = int(cy + amplitude * math.sin(u * 2.0 * math.pi + phase))
            rad = max(3, round(w * (.004 + .002*math.sin(phase + k))))
            draw.ellipse((x-rad*2, y-rad*2, x+rad*2, y+rad*2), fill=(*col, 25))
            draw.ellipse((x-rad, y-rad, x+rad, y+rad), fill=(*col, 150))
        # Tiny lower-corner cyclical spectral/graph motif.
        px = int(w*.92)
        py = int(h*.82)
        for k in range(3):
            r = int(max(3, h*.015)*(1+.12*math.sin(phase+2*k)))
            x = px - k*int(w*.034)
            y = py - (k%2)*int(h*.06)
            draw.ellipse((x-r,y-r,x+r,y+r),outline=(*col,105),width=2)
            if k:
                draw.line((x,y,px-(k-1)*int(w*.034), py-((k-1)%2)*int(h*.06)),fill=(*col,60),width=1)
        frame = Image.alpha_composite(base, layer).convert("RGB")
        frames.append(frame.quantize(palette=palette, dither=Image.Dither.NONE))
    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(output, save_all=True, append_images=frames[1:],
                   duration=DURATION_MS, loop=0, optimize=True, disposal=2)
    print(f"{svg} -> {output} ({output.stat().st_size:,} bytes)")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo", default="")
    args = parser.parse_args()
    if not args.input.exists():
        raise SystemExit(f"Cannot render missing SVG: {args.input}")
    render(args.input, args.output, project=args.repo)

if __name__ == "__main__":
    main()
