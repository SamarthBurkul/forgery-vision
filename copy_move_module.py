"""
copy_move_module.py — Copy-Move Forgery Detection via SIFT Feature Matching
Phase 4 USP feature.

Detects cloned (copy-move) regions within a single image by finding
SIFT keypoint pairs that have similar descriptors but are spatially
far apart (≥ 40 px).  If more than 10 such pairs are found, the image
likely contains copy-move forgery.
"""

import cv2
import numpy as np
import base64
from PIL import Image


def detect_copy_move(pil_image, ratio_thresh=0.75, min_distance=40, min_matches=10):
    """
    Detect copy-move forgery in a PIL image using SIFT + BFMatcher.

    Parameters
    ----------
    pil_image      : PIL.Image — input image (RGB)
    ratio_thresh   : float     — Lowe's ratio test threshold (default 0.75)
    min_distance   : int       — minimum pixel distance between matched
                                 keypoints to qualify as copy-move (default 40)
    min_matches    : int       — minimum number of qualifying pairs to
                                 declare copy-move detected (default 10)

    Returns
    -------
    dict with keys:
        copy_move_detected   : bool
        match_count          : int
        annotated_image_base64 : str | None  (base64 JPEG, only when detected)
    """
    # Convert to grayscale numpy array
    gray = np.array(pil_image.convert("L"))

    # Detect keypoints and compute descriptors
    sift = cv2.SIFT_create()
    keypoints, descriptors = sift.detectAndCompute(gray, None)

    # Need at least 2 keypoints to match
    if descriptors is None or len(keypoints) < 2:
        return {"copy_move_detected": False, "match_count": 0}

    # BFMatcher with knnMatch (k=2) for Lowe's ratio test
    bf = cv2.BFMatcher()
    raw_matches = bf.knnMatch(descriptors, descriptors, k=2)

    # Apply Lowe's ratio test + spatial distance filter
    good_pairs = []
    for m, n in raw_matches:
        # Skip self-matches (queryIdx == trainIdx)
        if m.queryIdx == m.trainIdx:
            continue
        # Lowe's ratio test on second-best match
        if m.distance < ratio_thresh * n.distance:
            # Spatial distance — same content but different location
            pt1 = np.array(keypoints[m.queryIdx].pt)
            pt2 = np.array(keypoints[m.trainIdx].pt)
            dist = np.linalg.norm(pt1 - pt2)
            if dist >= min_distance:
                good_pairs.append(m)

    match_count = len(good_pairs)

    if match_count >= min_matches:
        # Draw match lines on a copy of the original
        orig_bgr = cv2.cvtColor(np.array(pil_image.convert("RGB").copy()), cv2.COLOR_RGB2BGR)
        annotated = cv2.drawMatches(
            orig_bgr, keypoints,
            orig_bgr, keypoints,
            good_pairs[:50],          # cap at 50 lines for readability
            None,
            matchColor=(0, 255, 0),   # green lines
            singlePointColor=None,
            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
        )
        _, buf = cv2.imencode(".jpg", annotated)
        annotated_b64 = base64.b64encode(buf).decode("utf-8")

        return {
            "copy_move_detected": True,
            "match_count": match_count,
            "annotated_image_base64": annotated_b64,
        }
    else:
        return {
            "copy_move_detected": False,
            "match_count": match_count,
        }
