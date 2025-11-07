import cv2
import numpy as np
import time
from datetime import datetime


def compute_vari(frame_bgr: np.ndarray) -> np.ndarray:
    # VARI = (G - R) / (G + R - B)
    b, g, r = cv2.split(frame_bgr.astype(np.float32))
    denom = (g + r - b)
    eps = 1e-6
    vari = (g - r) / (denom + eps)
    # Clip to a sane range for visualization
    vari = np.clip(vari, -1.0, 1.0)
    return vari


def compute_exg(frame_bgr: np.ndarray) -> np.ndarray:
    # Excess Green: ExG = 2G - R - B (not normalized). Useful for vegetation segmentation
    b, g, r = cv2.split(frame_bgr.astype(np.float32))
    exg = 2 * g - r - b
    return exg


def classify_health(vari: np.ndarray, exg: np.ndarray) -> tuple[str, dict]:
    # Normalize ExG to 0..1 for a combined score
    exg_norm = cv2.normalize(exg, None, 0.0, 1.0, cv2.NORM_MINMAX)
    vari_norm = (vari + 1.0) / 2.0  # bring -1..1 to 0..1

    # Combined vegetation score
    score = 0.5 * vari_norm + 0.5 * exg_norm

    # Estimate vegetation mask with Otsu threshold on score
    score_u8 = np.uint8(np.clip(score * 255.0, 0, 255))
    _, thr = cv2.threshold(score_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    vegetation_ratio = float(np.count_nonzero(thr)) / float(thr.size + 1e-6)
    mean_vari = float(np.mean(vari))
    mean_exg = float(np.mean(exg_norm))

    # Simple rule-based classification; tweak thresholds as needed
    healthy = (vegetation_ratio > 0.25) and (mean_vari > 0.02) and (mean_exg > 0.45)
    status = "Healthy" if healthy else "Unhealthy"

    metrics = {
        "vegetation_ratio": vegetation_ratio,
        "mean_vari": mean_vari,
        "mean_exg": mean_exg,
    }
    return status, metrics


essential_text_color = (10, 240, 10)
alert_text_color = (0, 0, 255)
shadow_color = (0, 0, 0)


def overlay_hud(frame: np.ndarray, status: str, metrics: dict, fps: float) -> np.ndarray:
    h, w = frame.shape[:2]
    out = frame.copy()

    # Background panel for text
    panel_h = 90
    overlay = out.copy()
    cv2.rectangle(overlay, (0, 0), (w, panel_h), (0, 0, 0), thickness=-1)
    out = cv2.addWeighted(overlay, 0.35, out, 0.65, 0)

    # Text lines
    x, y = 12, 24
    scale = 0.6
    thick = 2

    # Status
    status_color = essential_text_color if status == "Healthy" else alert_text_color

    def put_text(label: str, value: str, y_off: int, color=(255, 255, 255)):
        text = f"{label}: {value}"
        # shadow
        cv2.putText(out, text, (x + 1, y + y_off + 1), cv2.FONT_HERSHEY_SIMPLEX, scale, shadow_color, thick, cv2.LINE_AA)
        # text
        cv2.putText(out, text, (x, y + y_off), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thick, cv2.LINE_AA)

    put_text("Health", status, 0, status_color)
    put_text("FPS", f"{fps:.1f}", 24)
    put_text("Vegetation %", f"{metrics['vegetation_ratio'] * 100:.1f}", 48)
    put_text("VARI (mean)", f"{metrics['mean_vari']:.3f}", 72)

    # Instructions
    instr = "[q] quit  [s] save frame"
    (tw, th), _ = cv2.getTextSize(instr, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.putText(out, instr, (w - tw - 10, panel_h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (230, 230, 230), 1, cv2.LINE_AA)

    return out


def run_camera_scanner(camera_index: int = 0, width: int = 1280, height: int = 720):
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        # Retry without CAP_DSHOW
        cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open camera index {camera_index}. Try a different index (0/1/2) or check permissions.")

    # Set desired resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    win_name = "Smart Farming - Real-time Crop Health"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, width, height)

    t_prev = time.time()
    fps = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            # Compute indices
            vari = compute_vari(frame)
            exg = compute_exg(frame)
            status, metrics = classify_health(vari, exg)

            # FPS
            t_now = time.time()
            dt = t_now - t_prev
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt) if fps > 0 else (1.0 / dt)
            t_prev = t_now

            # Overlay heads-up display
            vis = overlay_hud(frame, status, metrics, fps)

            cv2.imshow(win_name, vis)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            if key == ord('s'):
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = f"saved_frame_{ts}_{status}.jpg"
                cv2.imwrite(path, vis)
                # Small on-screen confirmation
                cv2.displayOverlay(win_name, f"Saved {path}", 1200)

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        run_camera_scanner()
    except Exception as e:
        print(f"ERROR: {e}")
