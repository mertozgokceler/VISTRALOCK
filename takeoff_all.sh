#!/usr/bin/env bash

set -e

SESSION="talon"

LOGDIR="$HOME/talon_sim/logs"

DEFAULTS="$HOME/talon_sim/talon_defaults.parm"

# ID1: standard constant post-takeoff throttle command (1800 PWM).
# ID2: smooth separation-based thrust control after both takeoffs.

mkdir -p "$LOGDIR"

mkdir -p "$HOME/talon_sim/plane1"

mkdir -p "$HOME/talon_sim/plane2"

echo

echo "=========================================="

echo "        VISTRALOCK - 2 UAV SYSTEM"

echo "=========================================="

echo

echo "[1/10] Eski sistem temizleniyor..."

tmux kill-session -t "$SESSION" 2>/dev/null || true

pkill -f mavproxy.py 2>/dev/null || true

pkill -f throttle_bridge.py 2>/dev/null || true

pkill -f auto_takeoff.py 2>/dev/null || true

pkill -f arduplane 2>/dev/null || true

pkill -f gzclient 2>/dev/null || true

pkill -f gzserver 2>/dev/null || true

pkill -f "rostopic pub.\*tracking/enabled" 2>/dev/null || true

sleep 1

echo "[2/10] Gazebo baslatiliyor..."

nohup bash -lc '

source /opt/ros/noetic/setup.bash

export GAZEBO_MODEL_DATABASE_URI=""

export GAZEBO_MODEL_PATH="$HOME/.gazebo/models:$HOME/ardupilot_gazebo/models\:/usr/share/gazebo-11/models:${GAZEBO_MODEL_PATH:-}"

export GAZEBO_PLUGIN_PATH="$HOME/talon_thrust_plugin/build:${GAZEBO_PLUGIN_PATH:-}"

roslaunch gazebo_ros empty_world.launch \
world_name:=$HOME/ardupilot_gazebo/worlds/talon_clean.world \
gui:=false \
paused:=true \
use_sim_time:=true \
verbose:=true

' > "$LOGDIR/gazebo_server.log" 2>&1 &

source /opt/ros/noetic/setup.bash

echo "Gazebo servisleri bekleniyor..."

OK=0

for i in $(seq 1 60)

do

    if rosservice list 2>/dev/null | grep -q "/gazebo/unpause_physics"

    then

        OK=1

        break

    fi

    sleep 1

done

if [ "$OK" -ne 1 ]

then

    echo "HATA: Gazebo acilamadi."

    tail -n 30 "$LOGDIR/gazebo_server.log"

    exit 1

fi

echo "Gazebo hazir."

echo "[3/10] ID1 ve ID2, dunya dosyasindaki modellerden kullaniliyor."

echo "Tracking sistemi STANDBY durumuna aliniyor..."

nohup rostopic pub -r 1 \
/tracking/enabled \
std_msgs/Bool \
"data: false" \
> "$LOGDIR/tracking_enabled.log" 2>&1 &

TRACKING_PUB_PID=$!

echo "Tracking DISABLED."

echo "[4/10] Gazebo GUI aciliyor..."

nohup bash -lc '

export GAZEBO_MODEL_DATABASE_URI=""

gzclient --verbose

' > "$LOGDIR/gazebo_gui.log" 2>&1 &

echo "[5/10] ArduPlane instance'lari baslatiliyor..."

tmux new-session \
-d \
-s "$SESSION" \
-n "AP1" \
"bash -lc '

cd \$HOME/talon_sim/plane1

\$HOME/ardupilot/build/sitl/bin/arduplane \
--wipe \
--model gazebo-zephyr \
--speedup 1 \
--slave 0 \
--defaults \$HOME/talon_sim/talon_defaults.parm \
--sim-address=127.0.0.1 \
-I0 \
--sysid 1

exec bash

'"

tmux new-window \
-t "$SESSION" \
-n "AP2" \
"bash -lc '

cd \$HOME/talon_sim/plane2

\$HOME/ardupilot/build/sitl/bin/arduplane \
--wipe \
--model gazebo-zephyr \
--speedup 1 \
--slave 0 \
--defaults \$HOME/talon_sim/talon_defaults.parm \
--sim-address=127.0.0.1 \
-I1 \
--sysid 2

exec bash

'"

wait_port()

{

    local PORT="$1"

    for i in $(seq 1 60)

    do

        if (

            echo > /dev/tcp/127.0.0.1/"$PORT"

        ) >/dev/null 2>&1

        then

            return 0

        fi

        sleep 1

    done

    return 1

}

echo "[6/10] ArduPlane TCP portlari bekleniyor..."

for PORT in 5760 5770

do

    echo "TCP $PORT bekleniyor..."

    if ! wait_port "$PORT"

    then

        echo "HATA: TCP $PORT acilmadi."

        kill "$TRACKING_PUB_PID" 2>/dev/null || true

        exit 1

    fi

    echo "TCP $PORT hazir."

done

echo "[7/10] MAVProxy instance'lari baslatiliyor..."

tmux new-window \
-t "$SESSION" \
-n "MAV1" \
"bash -lc '

export PATH=\"\$HOME/.local/bin:\$PATH\"

mavproxy.py \
--master=tcp:127.0.0.1:5760 \
--out=udp:127.0.0.1:14600

exec bash

'"

tmux new-window \
-t "$SESSION" \
-n "MAV2" \
"bash -lc '

export PATH=\"\$HOME/.local/bin:\$PATH\"

mavproxy.py \
--master=tcp:127.0.0.1:5770 \
--out=udp:127.0.0.1:14610 \
--out=udp:127.0.0.1:14620

exec bash

'"

sleep 3

echo "[8/10] Throttle bridge'ler baslatiliyor..."

nohup bash -lc '

source /opt/ros/noetic/setup.bash

python3 -u "$HOME/talon_sim/throttle_bridge.py" \
--model mini_talon_clean \
--port 14600

' > "$LOGDIR/throttle1.log" 2>&1 &


nohup bash -lc '

source /opt/ros/noetic/setup.bash

python3 -u "$HOME/talon_sim/throttle_bridge.py" \
--model mini_talon_2 \
--port 14610 \
--pace-model mini_talon_clean \
--desired-gap 25 \
--lateral-limit 30 \
--min-own-speed 15 \
--max-own-speed 24 \
--max-thrust-increase 0.50 \
--max-thrust-reduction 0.25

' > "$LOGDIR/throttle2.log" 2>&1 &

tmux select-window -t "$SESSION:MAV1"

gnome-terminal \
--title="MINI TALON CONTROL" \
-- bash -lc \
"tmux attach-session -t $SESSION" \
>/dev/null 2>&1 &

echo "[9/10] Fizik aciliyor..."

rosservice call /gazebo/unpause_physics >/dev/null

sleep 6

echo "[10/10] Iki ucak kalkisa basliyor..."

echo

echo "ID1 kalkis..."

echo

python3 -u "$HOME/talon_sim/auto_takeoff.py" \
--model mini_talon_clean \
--window MAV1 \
--x -122 \
--y -12 \
> "$LOGDIR/takeoff1.log" 2>&1 &

PID1=$!

sleep 0.3

echo

echo "ID2 kalkis - OWN UAV..."

echo

python3 -u "$HOME/talon_sim/auto_takeoff.py" \
--model mini_talon_2 \
--window MAV2 \
--x -126 \
--y -18 \
> "$LOGDIR/takeoff2.log" 2>&1 &

PID2=$!

sleep 0.3

echo

echo "Iki ucak kalkis yapiyor..."

echo "Tracking halen DISABLED."

echo

tail -n +1 -F \
"$LOGDIR/takeoff1.log" \
"$LOGDIR/takeoff2.log" &

TAIL_PID=$!

set +e

wait "$PID1"

STATUS1=$?

wait "$PID2"

STATUS2=$?

set -e

kill "$TAIL_PID" 2>/dev/null || true

wait "$TAIL_PID" 2>/dev/null || true

echo

echo "=========================================="

echo "              KALKIS SONUCU"

echo "=========================================="

echo

echo "ID1 STATUS=$STATUS1"

echo "ID2 STATUS=$STATUS2"

echo

if (
    [ "$STATUS1" -eq 0 ] &&
    [ "$STATUS2" -eq 0 ]
)
then

    echo "Tum ucaklar stabil kalkisi tamamladi."

    echo "Tracking sistemi aktif ediliyor..."

    kill "$TRACKING_PUB_PID" 2>/dev/null || true

    wait "$TRACKING_PUB_PID" 2>/dev/null || true

    sleep 0.5

    nohup rostopic pub -r 1 \
    /tracking/enabled \
    std_msgs/Bool \
    "data: true" \
    > "$LOGDIR/tracking_enabled.log" 2>&1 &

    TRACKING_PUB_PID=$!

    echo

    echo "=========================================="

    echo "       2 UAV AIRBORNE"

    echo "       TRACKING ENABLED"

    echo "=========================================="

    echo

else

    echo

    echo "En az bir ucagin kalkisi basarisiz."

    echo "Tracking DISABLED olarak kalacak."

    echo

    for ID in 1 2

    do

        STATUS_VAR="STATUS${ID}"

        STATUS="${!STATUS_VAR}"

        if [ "$STATUS" -ne 0 ]

        then

            echo "ID${ID} son log:"

            tail -n 20 "$LOGDIR/takeoff${ID}.log"

            echo

        fi

    done

    exit 1

fi

echo "ID1"

echo "  Model : mini_talon_clean"

echo "  SYSID : 1"

echo "  MAV   : MAV1"

echo "  TCP   : 5760"

echo "  UDP   : 14600"

echo

echo "ID2 - OWN UAV"

echo "  Model     : mini_talon_2"

echo "  SYSID     : 2"

echo "  MAV       : MAV2"

echo "  TCP       : 5770"

echo "  UDP       : 14610"

echo "  Dashboard : 14620"

echo