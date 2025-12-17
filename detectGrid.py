import time
import cv2
import numpy as np
from ultralytics import YOLO


DEFAULT_WEIGHTS = "best2.pt"
DEFAULT_INTERVAL = 1.0
DEFAULT_DEVICE = "cpu"  # or "cuda"
DEFAULT_CONF = 0.25
ID2TOKEN = {0: "X", 1: "O", 2: " "}


def _cell_index_from_center(cx: float, cy: float, W: int, H: int):
    nx, ny = cx / max(W, 1), cy / max(H, 1)
    col = int(min(2, max(0, nx * 3.0)))
    row = int(min(2, max(0, ny * 3.0)))
    return row, col

def save_debug_image(frame):
    import os, cv2, glob
    os.makedirs("debug", exist_ok=True)
    n = len(glob.glob("debug/img_*.png")) + 1
    path = f"debug/img_{n:02d}.png"
    cv2.imwrite(path, frame)
    return path

def process_frame(frame_bgr, model, conf_thr=0.25):
    # save_debug_image(frame_bgr)
    H, W = frame_bgr.shape[:2]
    result = model.predict(source=frame_bgr, conf=conf_thr, verbose=False)

    board = [[" " for _ in range(3)] for _ in range(3)]
    best_conf = [[-1.0 for _ in range(3)] for _ in range(3)]
    annotated = frame_bgr.copy()

    # draw grid
    for k in range(1, 3):
        x = int(W * k / 3.0)
        y = int(H * k / 3.0)
        cv2.line(annotated, (x, 0), (x, H), (0, 255, 255), 1, cv2.LINE_AA)
        cv2.line(annotated, (0, y), (W, y), (0, 255, 255), 1, cv2.LINE_AA)

    if not result:
        return board, annotated

    r0 = result[0]
    if r0.boxes is None or r0.boxes.data is None or len(r0.boxes) == 0:
        return board, annotated

    xyxy = r0.boxes.xyxy.cpu().numpy()
    cls = r0.boxes.cls.cpu().numpy().astype(int)
    conf = r0.boxes.conf.cpu().numpy()

    for i in range(xyxy.shape[0]):
        x1, y1, x2, y2 = xyxy[i]
        c = int(cls[i])
        p = float(conf[i])
        cx = 0.5 * (x1 + x2)
        cy = 0.5 * (y1 + y2)
        row, col = _cell_index_from_center(cx, cy, W, H)
        token = ID2TOKEN.get(c, " ")
        if p > best_conf[row][col]:
            board[row][col] = token
            best_conf[row][col] = p
        cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 255), 1)
        cv2.putText(
            annotated,
            f"{token}:{p:.2f}",
            (int(x1), int(y1) - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
    return reverse_nested_lists(board), annotated


def _overlay_board_text(img: np.ndarray, board):
    """Overlay the 3x3 board as text on the image (top-left)."""
    x0, y0 = 10, 25
    dy = 25
    cv2.putText(img, "Board:", (x0, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
    for r in range(3):
        row_txt = " | ".join(board[r])
        cv2.putText(
            img,
            row_txt,
            (x0, y0 + (r + 1) * dy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

def reverse_nested_lists(data):
    return [inner[::-1] for inner in data[::-1]]

def _print_board(board):
    # board = reverse_nested_lists(board)
    lines = []
    for r in range(3):
        row = " | ".join(board[r])
        lines.append(" " + row + " ")
        if r < 2:
            lines.append("---+---+---")
    print("\n".join(lines))

# ------------------ FOR TESTING INDIVIDUAL CLASS ------------------

def main():
    model = YOLO(DEFAULT_WEIGHTS)
    cap = None
    for idx in range(1,5):
        test = cv2.VideoCapture(idx)
        if test.isOpened():
            cap = test
            print(f"✅ Using camera index {idx}")
            break
        test.release()

    if cap is None or not cap.isOpened():
        print("❌ Cannot open any camera (tried indices 0-2).")
        return

    cv2.namedWindow("TicTacToe Detector", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("TicTacToe Detector", 800, 600)

    last_capture_time = 0

    print("Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("⚠️ Failed to grab frame.")
            break

        current_time = time.time()
        if current_time - last_capture_time >= 5:
            last_capture_time = current_time
            board, annotated = process_frame(frame, model, conf_thr=DEFAULT_CONF)

            print("\nDetected Board:")
            _print_board(board)

            _overlay_board_text(annotated, board)
            cv2.imshow("TicTacToe Detector", annotated)
        else:
            cv2.imshow("TicTacToe Detector", frame)

        # required for OpenCV window refresh
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
