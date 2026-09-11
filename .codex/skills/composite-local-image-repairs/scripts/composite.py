#!/usr/bin/env python3
"""Composite visually selected repairs without changing any other source pixels."""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--repaired', type=Path, required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--regions', type=Path)
    selection.add_argument('--mask', type=Path)
    parser.add_argument('--output-prefix', type=Path, required=True)
    args = parser.parse_args()

    with Image.open(args.original) as src, Image.open(args.repaired) as fix:
        if src.size != fix.size or src.mode != fix.mode:
            raise ValueError('Inputs must have identical dimensions and color modes.')
        if src.mode not in ('RGB', 'RGBA'):
            raise ValueError('Use RGB or RGBA inputs; no implicit color conversion is performed.')
        size = src.size
        original, repaired = np.array(src), np.array(fix)
        # Keep original color metadata where available; pixel arrays stay untouched.
        metadata = {k: src.info[k] for k in ('icc_profile', 'dpi') if k in src.info}

    if args.regions:
        polygons = json.loads(args.regions.read_text(encoding='utf-8'))['polygons']
        if not polygons:
            raise ValueError('At least one visually selected polygon is required.')
        canvas = Image.new('L', size, 0)
        draw = ImageDraw.Draw(canvas)
        for polygon in polygons:
            points = np.asarray(polygon, dtype=float)
            if (points.ndim != 2 or points.shape[1] != 2 or len(points) < 3
                    or not np.isfinite(points).all()):
                raise ValueError('Each polygon must contain at least three finite (x, y) pairs.')
            if (np.any(points < 0) or np.any(points[:, 0] > size[0] - 1)
                    or np.any(points[:, 1] > size[1] - 1)):
                raise ValueError('Polygon coordinates must lie inside the full-resolution image.')
            draw.polygon([tuple(point) for point in points], fill=1)
        mask = np.array(canvas, dtype=bool)
    else:
        raw = np.load(args.mask, allow_pickle=False)
        if raw.shape != (size[1], size[0]) or not np.isin(raw, [0, 1]).all():
            raise ValueError('Mask must match (height, width) and contain only 0/1 values.')
        mask = raw.astype(bool)

    names = {key: Path(str(args.output_prefix) + suffix) for key, suffix in {
        'mask_npy': '.mask.npy', 'mask_png': '.mask.png',
        'final': '.final.png', 'overlay': '.overlay.png',
    }.items()}
    for path in names.values():
        if path.exists() or path.is_symlink():
            raise FileExistsError(f'Refusing to overwrite: {path}')
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)

    final = np.where(mask[..., None], repaired, original)
    np.save(names['mask_npy'], mask, allow_pickle=False)
    indexed = Image.fromarray(mask.astype(np.uint8)).convert('P')
    indexed.putpalette([0, 0, 0, 255, 255, 255] + [0] * 762)
    indexed.save(names['mask_png'], bits=1)
    Image.fromarray(final).save(names['final'], **metadata)
    overlay = original.copy()
    rgb = overlay[..., :3]
    rgb[mask] = np.rint(original[..., :3][mask] * 0.55
                        + np.array([0, 220, 255]) * 0.45).astype(np.uint8)
    Image.fromarray(overlay).save(names['overlay'], **metadata)

    saved_mask = np.array(Image.open(names['mask_png']))
    saved_bool = np.load(names['mask_npy'], allow_pickle=False)
    saved_final = np.array(Image.open(names['final']))
    valid = (saved_bool.dtype == np.bool_
             and np.array_equal(saved_bool, mask)
             and np.array_equal(saved_mask, mask.astype(np.uint8))
             and saved_final.shape == original.shape
             and np.array_equal(saved_final[~mask], original[~mask])
             and np.array_equal(saved_final[mask], repaired[mask]))
    if not valid:
        raise RuntimeError('Saved artifact verification failed.')
    print(json.dumps({'size': size, 'repair_pixels': int(mask.sum()),
                      'repair_percent': round(float(mask.mean()) * 100, 3),
                      'outside_mask_exact_match': True, 'inside_mask_exact_match': True,
                      'files': {key: str(path) for key, path in names.items()}},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
