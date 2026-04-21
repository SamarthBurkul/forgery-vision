"""
edge_module.py — Gradient Direction Consistency Edge Map
Phase 3 USP feature.

Approach:
  • Compute per-pixel gradient direction using Sobel operators.
  • For every 16×16 block compute the *circular variance* of gradient angles.
    Circular variance = 1 − R  where R = |mean complex unit vector|.
    R ≈ 1  → directions are tightly clustered   → natural region.
    R ≈ 0  → directions are random / inconsistent → potential forgery.
  • The mean circular variance across all blocks becomes the edge score.
  • A JET-colormap heatmap with Canny edge overlay is returned as base64 JPEG.
"""

import numpy as np
import cv2
import base64
from PIL import Image as PILImage


BLOCK_SIZE = 16


def compute_edge_map(pil_image: PILImage.Image, block_size: int = BLOCK_SIZE):
    """
    Parameters
    ----------
    pil_image  : PIL.Image (RGB)
    block_size : tile size in pixels (default 16)

    Returns
    -------
    edge_b64   : str   — base64-encoded JET+Canny-overlay JPEG
    edge_score : float — mean circular variance in [0, 1]
                         (higher → more inconsistent → more suspicious)
    """
    img = np.array(pil_image.convert("L"), dtype=np.float32)
    h, w = img.shape

    # ── Gradient angles ──────────────────────────────────────────────────────
    sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
    angle  = np.arctan2(sobely, sobelx)          # shape (h, w), range (−π, π)

    blocks_h = h // block_size
    blocks_w = w // block_size

    incon_map    = np.zeros((h, w), dtype=np.float32)
    block_scores = []

    for by in range(blocks_h):
        for bx in range(blocks_w):
            y0, x0        = by * block_size, bx * block_size
            block_angle   = angle[y0:y0 + block_size, x0:x0 + block_size]

            # Circular mean resultant length
            sin_m = np.sin(block_angle).mean()
            cos_m = np.cos(block_angle).mean()
            R     = np.sqrt(sin_m ** 2 + cos_m ** 2)  # in [0, 1]
            incon = float(1.0 - R)                     # 0 = consistent, 1 = random

            incon_map[y0:y0 + block_size, x0:x0 + block_size] = incon
            block_scores.append(incon)

    edge_score = float(np.mean(block_scores)) if block_scores else 0.0

    # ── Visualisation: JET heatmap + Canny overlay ──────────────────────────
    incon_norm = cv2.normalize(incon_map, None, 0, 255, cv2.NORM_MINMAX)
    colored    = cv2.applyColorMap(incon_norm.astype(np.uint8), cv2.COLORMAP_JET)

    canny      = cv2.Canny(img.astype(np.uint8), 50, 150)
    canny_3ch  = cv2.cvtColor(canny, cv2.COLOR_GRAY2BGR)
    combined   = cv2.addWeighted(colored, 0.75, canny_3ch, 0.25, 0)

    _, buf    = cv2.imencode(".jpg", combined)
    edge_b64  = base64.b64encode(bytes(buf)).decode("utf-8")

    return edge_b64, edge_score
