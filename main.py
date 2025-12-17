import time
import copy
import cv2
from ultralytics import YOLO
import threading

from dobotGrid import DobotGrid
from detectGrid import process_frame, DEFAULT_CONF
from detectGrid import DEFAULT_WEIGHTS
from ticTacToe import evaluate, is_moves_left, evaluate_next_move

DETECT_INTERVAL_SEC = 15.0
CAM_INDEX_CANDIDATES = [1, 2, 3, 0]
PORT = "/dev/ttyACM0"

def open_camera():
    cap = None
    for idx in CAM_INDEX_CANDIDATES:
        c = cv2.VideoCapture(idx)
        if c.isOpened():
            cap = c
            print(f"[cam] Using camera index {idx}")
            break
        c.release()
    if cap is None:
        raise RuntimeError("No camera available (tried indices: %s)" % CAM_INDEX_CANDIDATES)
    cv2.namedWindow("Feed", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Feed", 960, 720)
    return cap

def show_board(board):
    rows = []
    for r in range(3):
        rows.append(" " + " | ".join(board[r]).replace('_', ' ') + " ")
        if r < 2: rows.append("---+---+---")
    print("\n".join(rows))

def detected_to_internal(det_board):
    return [[('x' if c == 'X' else ('o' if c == 'O' else '_')) for c in row] for row in det_board]

def count_diffs(A, B):
    diffs = []
    for i in range(3):
        for j in range(3):
            if A[i][j] != B[i][j]:
                diffs.append((i, j))
    return diffs

def winner_from_evaluate(val, robot_token):
    if val == 10:
        return "robot" if robot_token == 'x' else "human"
    if val == -10:
        return "robot" if robot_token == 'o' else "human"
    return None

def best_move_for_robot(board, robot_token):
    if robot_token == 'x':
        return evaluate_next_move(copy.deepcopy(board))
    swap = {'x':'o', 'o':'x', '_':'_'}
    swapped = [[swap[c] for c in row] for row in board]
    i, j = evaluate_next_move(swapped)
    return (i, j)

def draw_symbol(dobot, token, i, j):
    if token == 'x':
        dobot.draw_x(i+1, j+1, delay=0)
    else:
        dobot.draw_o(i+1, j+1)

class FrameGrabber:
    """Continuously grabs frames; read() returns the latest frame instantly."""
    def __init__(self, cap):
        self.cap = cap
        self._lock = threading.Lock()
        self._latest = None
        self._running = False
        self._t = None

    def start(self):
        if self._running: return
        self._running = True
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()

    def _loop(self):
        # grab -> retrieve keeps buffer small and reduces latency
        while self._running:
            if not self.cap.grab():
                time.sleep(0.01)
                continue
            ok, frame = self.cap.retrieve()
            if not ok: 
                time.sleep(0.005)
                continue
            with self._lock:
                self._latest = frame

    def read(self):
        """Returns a copy of the most recent frame (or None if not ready)."""
        with self._lock:
            if self._latest is None:
                return None
            return self._latest.copy()

    def stop(self):
        self._running = False
        if self._t:
            self._t.join(timeout=1.0)
            self._t = None    

def main():
    # 1) Initialize Dobot + grid
    dobot = DobotGrid(port=PORT)
    dobot.generate_points()
    dobot.generate_grid()
    dobot.draw_grid()

    # 2) YOLO + camera
    model = YOLO(DEFAULT_WEIGHTS)
    cap = open_camera()
    grabber = FrameGrabber(cap)
    grabber.start()
    last_poll = 0.0
    annotated_frame = None

    # 3) Game state
    current = [['_','_','_'], ['_','_','_'], ['_','_','_']]
    previous = copy.deepcopy(current)
    robot_move = False
    game_over = False

    # 4) Who goes first?
    #    If Dobot first: robot='x', human='o' and robot_move=True
    #    If Human first: human='x', robot='o' and robot_move=False
    while True:
        choice = input("Who goes first? Type 'robot' or 'human': ").strip().lower()
        if choice in ("robot", "human"):
            break
        print("Please type exactly 'robot' or 'human'.")
    if choice == "robot":
        robot_token, human_token = 'x', 'o'
        robot_move = True
        print("Dobot is 'X', Human is 'O'.")
    else:
        human_token, robot_token = 'x', 'o'
        robot_move = False
        print("Human is 'X', Dobot is 'O'.")

    print("\n--- Game start ---")
    show_board(current)

    try:
        while not game_over:
            frame = grabber.read()
            cv2.imshow("frame", frame)

            # Check terminal game status first (win/draw)
            val = evaluate(current)
            w = winner_from_evaluate(val, robot_token)
            if w is not None:
                print("\nFinal board:"); show_board(current)
                print("Result:", "Robot wins!" if w == "robot" else "Human wins!")
                game_over = True
            elif not is_moves_left(current):
                print("\nFinal board:"); show_board(current)
                print("Result: It's a draw!")
                game_over = True

            if game_over:
                cv2.imshow("Feed", annotated_frame if annotated_frame is not None else frame)
                cv2.waitKey(1)
                break

            # ------------ Human turn ------------
            if not robot_move:
                now = time.time()
                if now - last_poll >= DETECT_INTERVAL_SEC:
                    last_poll = now
                    dobot.move_to_intermediate()
                    frame = grabber.read()
                    det_board, annotated = process_frame(frame, model, conf_thr=DEFAULT_CONF)
                    annotated_frame = annotated
                    detected = detected_to_internal(det_board)

                    diffs = count_diffs(previous, detected)
                    if len(diffs) == 0:
                        print("[human] Please make your move...")
                    elif len(diffs) > 1:
                        print(previous)
                        print(detected)
                        print('YOU ARE A CHEATER, I DON\'T WANT TO PLAY. (1)')
                        game_over = True
                    else:
                        (ri, rj) = diffs[0]
                        if previous[ri][rj] != '_' or detected[ri][rj] != human_token:
                            print(previous)
                            print(detected)
                            print('YOU ARE A CHEATER, I DON\'T WANT TO PLAY. (2)')
                            game_over = True
                        else:
                            previous = copy.deepcopy(current)
                            current = detected
                            robot_move = True
                            print("\nBoard after human move:")
                            show_board(current)

                cv2.imshow("Feed", annotated_frame if annotated_frame is not None else frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("Quit requested."); break
                continue

            # ------------ Robot turn ------------
            if robot_move:
                i, j = best_move_for_robot(copy.deepcopy(current), robot_token)
                if i == -1 or j == -1 or not is_moves_left(current):
                    print("\nFinal board:"); show_board(current)
                    print("Result: No valid moves. It's a draw!")
                    game_over = True
                else:
                    print(f"[robot] Playing at row {i+1}, col {j+1} as '{robot_token.upper()}'")
                    draw_symbol(dobot, robot_token, i, j)
                    current[i][j] = robot_token
                    robot_move = False
                    print("\nBoard after robot move:")
                    show_board(current)

            previous = copy.deepcopy(current)
            cv2.imshow("Feed", annotated_frame if annotated_frame is not None else frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Quit requested."); break

    finally:
        # graceful shutdown
        grabber.stop()  
        cap.release()
        cv2.destroyAllWindows()
        try:
            dobot.disconnect()
        except Exception:
            pass
        print("\n[shutdown] Camera closed and Dobot disconnected.")
        

if __name__ == "__main__":
    main()
