import cv2, json, socket, time
import mediapipe as mp

# -------- UDP CONFIG ----------
UDP_IP   = "127.0.0.1"   # Unity の PC／スマホ IP
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# -------- MediaPipe SETUP -----
mp_hands   = mp.solutions.hands
hands      = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5
)
finger_tips = [4, 8, 12, 16, 20]  # 親指～小指 tip id

# -------- Gesture 判定ユーティリティ -------------
def fingers_open(hand_landmarks):
    lm = hand_landmarks.landmark
    open_status = []
    # 親指は x 座標方向で判定（右手）
    open_status.append(lm[finger_tips[0]].x < lm[finger_tips[0]-2].x)
    # 他 4 指は y 座標（tip が pip より上なら開いている）
    for tip in finger_tips[1:]:
        open_status.append(lm[tip].y < lm[tip-2].y)
    return open_status.count(True)

# -------- Main Loop -----------
cap = cv2.VideoCapture(0)
last_send = 0
while cap.isOpened():
    ok, frame = cap.read()
    if not ok: break
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    if res.multi_hand_landmarks:
        f_open = fingers_open(res.multi_hand_landmarks[0])
        if f_open == 5 and time.time() - last_send > 0.5:  # debounce 0.5 s
            payload = json.dumps({"gesture": "open_hand"})
            print(payload)
            sock.sendto(payload.encode(), (UDP_IP, UDP_PORT))
            last_send = time.time()

        # デバッグ描画
        mp.solutions.drawing_utils.draw_landmarks(
            frame, res.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS
        )

    cv2.imshow("Gesture", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release(); cv2.destroyAllWindows()
