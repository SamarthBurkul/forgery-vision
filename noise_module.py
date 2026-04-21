"""
noise_module.py — Laplacian Variance Noise Inconsistency Map
Phase 3 USP feature.

Approach:
  • Compute Laplacian variance for every 16×16 block of the grayscale image.
  • Natural images have roughly uniform noise distribution.
  • Spliced regions often have a different noise fingerprint than the host.
  • The *coefficient of variation* of block variances is used as the
    global noise inconsistency score (0 = very uniform → authentic,
    1 = highly uneven → suspicious).
  • A HOT colormap heatmap is returned as base64 JPEG.
"""

import numpy as np
import cv2
import base64
from PIL import Image as PILImage


BLOCK_SIZE = 16


def compute_noise_map(pil_image: PILImage.Image, block_size: int = BLOCK_SIZE):
    """
    Parameters
    ----------
    pil_image  : PIL.Image (RGB)
    block_size : tile size in pixels (default 16)

    Returns
    -------
    noise_b64  : str  — base64-encoded HOT-colormap JPEG of the variance map
    noise_score: float — noise inconsistency score in [0, 1]
    """
    img = np.array(pil_image.convert("L"), dtype=np.float64)
    h, w = img.shape

    blocks_h = h // block_size
    blocks_w = w // block_size

    variance_grid = np.zeros((blocks_h, blocks_w), dtype=np.float64)
    vis_map       = np.zeros((h, w), dtype=np.float32)

    for by in range(blocks_h):
        for bx in range(blocks_w):
            y0, x0 = by * block_size, bx * block_size
            block   = img[y0:y0 + block_size, x0:x0 + block_size]
            lap     = cv2.Laplacian(block, cv2.CV_64F)
            var     = float(lap.var())
            variance_grid[by, bx] = var
            vis_map[y0:y0 + block_size, x0:x0 + block_size] = var

    # ── Score: coefficient of variation → clamp to [0, 1] ──────────────────
    mean_var = variance_grid.mean()
    if mean_var > 1e-6:
        cv_score = variance_grid.std() / mean_var
        # empirically, CV > 2 is very suspicious; normalise to 0-1
        noise_score = float(min(1.0, cv_score / 2.0))
    else:
        noise_score = 0.0

    # ── Visualisation ───────────────────────────────────────────────────────
    vis_norm = cv2.normalize(vis_map, None, 0, 255, cv2.NORM_MINMAX)
    colored  = cv2.applyColorMap(vis_norm.astype(np.uint8), cv2.COLORMAP_HOT)

    _, buf    = cv2.imencode(".jpg", colored)
    noise_b64 = base64.b64encode(bytes(buf)).decode("utf-8")

    return noise_b64, noise_score
