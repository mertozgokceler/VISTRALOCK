#!/usr/bin/env bash

echo "Mini Talon sistemi kapatiliyor..."

tmux kill-session -t talon 2>/dev/null || true

pkill -f mavproxy.py 2>/dev/null || true
pkill -f throttle_bridge.py 2>/dev/null || true
pkill -f auto_takeoff.py 2>/dev/null || true
pkill -f "rostopic pub.*tracking/enabled" 2>/dev/null || true
pkill -f arduplane 2>/dev/null || true
pkill -f gzclient 2>/dev/null || true
pkill -f gzserver 2>/dev/null || true

echo "Mini Talon sistemi kapatildi."