"""
gradcam_module.py — Grad-CAM Visualization for DenseNet ELA Model
Phase 5 USP feature.

Computes Grad-CAM for the last convolutional layer of the DenseNet model
to show which image regions the neural network focused on when classifying.
"""

import numpy as np
import cv2
import base64
import tensorflow as tf


# Name of the last Conv2D layer in the DenseNet121 model
LAST_CONV_LAYER = "conv5_block16_2_conv"


def compute_gradcam(model, np_img, ela_pil, predicted_class_idx=1):
    """
    Compute Grad-CAM heatmap and alpha-blend over the ELA image.

    Parameters
    ----------
    model              : keras Model — the loaded DenseNet ELA model
    np_img             : np.ndarray  — preprocessed input (1, 128, 128, 3)
    ela_pil            : PIL.Image   — the raw ELA image (for blending)
    predicted_class_idx: int         — class index to visualize (1 = Tampered)

    Returns
    -------
    str — base64-encoded JPEG of the Grad-CAM overlay
    """
    # Build a sub-model that outputs last conv activations + final predictions
    last_conv_layer = model.get_layer(LAST_CONV_LAYER)
    grad_model = tf.keras.Model(
        inputs=model.input,
        outputs=[last_conv_layer.output, model.output]
    )

    # Use GradientTape to get gradients of the predicted class score
    inp_tensor = tf.cast(np_img, tf.float32)
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(inp_tensor)
        class_score = predictions[:, predicted_class_idx]

    # Gradients of the class score w.r.t. the last conv layer activations
    grads = tape.gradient(class_score, conv_outputs)

    # Global average pooling of gradients → channel weights
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    # Weight each channel by its importance and sum
    conv_outputs = conv_outputs[0]
    heatmap = tf.reduce_sum(conv_outputs * pooled_grads, axis=-1).numpy()

    # ReLU — only keep positive influence
    heatmap = np.maximum(heatmap, 0)

    # Normalize to [0, 1]
    if heatmap.max() > 0:
        heatmap /= heatmap.max()

    # Resize heatmap to 128×128
    heatmap_resized = cv2.resize(heatmap, (128, 128))

    # Convert to uint8 and apply JET colormap
    heatmap_uint8 = np.uint8(255 * heatmap_resized)
    heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

    # Prepare ELA image at 128×128 for blending
    ela_resized = np.array(ela_pil.resize((128, 128)).convert("RGB"))
    ela_bgr = cv2.cvtColor(ela_resized, cv2.COLOR_RGB2BGR)

    # Alpha-blend: heatmap at 0.4 opacity over ELA image
    blended = cv2.addWeighted(heatmap_color, 0.4, ela_bgr, 0.6, 0)

    # Encode to base64 JPEG
    _, buf = cv2.imencode(".jpg", blended)
    return base64.b64encode(buf).decode("utf-8")
