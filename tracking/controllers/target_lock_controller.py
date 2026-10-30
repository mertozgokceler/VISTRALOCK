#!/usr/bin/env python3


import math
import time


class TargetLockController:
    def __init__(
        self,
        lock_required=3,
        lost_neutralize_frames=2,
        reacquire_after_frames=3,
        reacquire_required=4,
    ):
        self.lock_required = lock_required
        self.lost_neutralize_frames = lost_neutralize_frames
        self.reacquire_after_frames = reacquire_after_frames
        self.reacquire_required = reacquire_required

        self.roi_margin_x = 0.25
        self.roi_margin_y = 0.10
        self.roi_min_coverage = 0.90
        self.lock_duration = 4.0
        self.max_detection_gap = 1.0
        self.completed_lock_targets = set()

        self.completed_target_observations = {}
        self.completed_track_aliases = {}
        self.reid_max_gap = 5.0
        self.reset()

    def reset(self):
        self.active_track_id = None
        self.last_bbox = None
        self.last_center = None
        self.lost_frames = 0
        self.lock_candidate_id = None
        self.lock_hits = 0
        self.reacquire_candidate_id = None
        self.reacquire_hits = 0
        self.reset_roi_lock()

    def reset_success_history(self):
        self.completed_lock_targets.clear()
        self.completed_target_observations.clear()
        self.completed_track_aliases.clear()
        self.reset_roi_lock()

    def reset_roi_lock(self):
        self.roi_track_id = None
        self.roi_start_time = None
        self.roi_last_seen_time = None
        self.roi_elapsed = 0.0
        self.roi_lock_success = False

    def get_bbox_center(self, bbox):
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def update_last_target(self, detection):
        self.last_bbox = detection['bbox']
        self.last_center = self.get_bbox_center(self.last_bbox)

    def is_continuous(self, detection):
        if self.last_bbox is None:
            return True
        previous_x, previous_y = self.get_bbox_center(self.last_bbox)
        current_x, current_y = self.get_bbox_center(detection['bbox'])
        distance = math.hypot(current_x - previous_x, current_y - previous_y)
        x1, y1, x2, y2 = self.last_bbox
        diagonal = math.hypot(x2 - x1, y2 - y1)
        max_jump = max(70.0, min(160.0, diagonal * 2.0))
        return distance <= max_jump

    def find_initial_candidate(self, detections, image_width, image_height):
        center_x = image_width / 2.0
        center_y = image_height / 2.0

        def distance_to_center(detection):
            x, y = self.get_bbox_center(detection['bbox'])
            return math.hypot(x - center_x, y - center_y)

        return min(detections, key=distance_to_center)

    def find_reacquire_candidate(self, detections):
        if self.last_center is None:
            return None
        reference_x, reference_y = self.last_center
        if self.last_bbox is None:
            radius = 100.0
        else:
            x1, y1, x2, y2 = self.last_bbox
            diagonal = math.hypot(x2 - x1, y2 - y1)
            radius = max(90.0, min(180.0, diagonal * 2.5))
        candidates = []
        for detection in detections:
            x, y = self.get_bbox_center(detection['bbox'])
            distance = math.hypot(x - reference_x, y - reference_y)
            if distance <= radius:
                candidates.append((distance, detection))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    @staticmethod
    def _result(event, detection=None, track_id=None, neutralize=False, **extra):
        return {
            'event': event,
            'detection': detection,
            'track_id': track_id,
            'neutralize': neutralize,
            **extra,
        }

    def update(self, detections, image_width, image_height, aircraft_id=None):
        valid_detections = [
            d for d in (detections or [])
            if isinstance(d, dict) and d.get('track_id') is not None
            and isinstance(d.get('bbox'), (tuple, list)) and len(d['bbox']) == 4
        ]
        if self.active_track_id is None:
            result = self.handle_initial_lock(valid_detections, image_width, image_height)
        else:
            result = self.handle_locked_target(valid_detections)

        return self._update_roi_progress(
            result, image_width, image_height,
            aircraft_id=aircraft_id, detections=valid_detections,
        )

    def handle_initial_lock(self, detections, image_width, image_height):
        if not detections:
            self.lock_candidate_id = None
            self.lock_hits = 0
            return self._result('WAITING')

        candidate = self.find_initial_candidate(detections, image_width, image_height)
        candidate_id = candidate['track_id']
        if candidate_id == self.lock_candidate_id:
            self.lock_hits += 1
        else:
            self.lock_candidate_id = candidate_id
            self.lock_hits = 1

        if self.lock_hits < self.lock_required:
            return self._result('LOCKING', track_id=candidate_id)

        self.active_track_id = candidate_id
        self.lock_candidate_id = None
        self.lock_hits = 0
        self.lost_frames = 0
        self.update_last_target(candidate)
        return self._result('LOCKED', candidate, self.active_track_id, True)

    def handle_locked_target(self, detections):
        target_detection = None
        for detection in detections:
            if detection.get('track_id') != self.active_track_id:
                continue
            if not self.is_continuous(detection):
                continue
            target_detection = detection
            break

        if target_detection is not None:
            self.lost_frames = 0
            self.reacquire_candidate_id = None
            self.reacquire_hits = 0
            self.update_last_target(target_detection)
            return self._result('TRACKING', target_detection, self.active_track_id)

        self.lost_frames += 1
        neutralize = self.lost_frames == self.lost_neutralize_frames
        if self.lost_frames < self.reacquire_after_frames:
            return self._result('LOST', track_id=self.active_track_id, neutralize=neutralize)

        candidate = self.find_reacquire_candidate(detections)
        if candidate is None:
            self.reacquire_candidate_id = None
            self.reacquire_hits = 0
            return self._result('LOST', track_id=self.active_track_id, neutralize=neutralize)

        candidate_id = candidate['track_id']
        if candidate_id == self.reacquire_candidate_id:
            self.reacquire_hits += 1
        else:
            self.reacquire_candidate_id = candidate_id
            self.reacquire_hits = 1

        if self.reacquire_hits < self.reacquire_required:
            return self._result(
                'REACQUIRING', track_id=self.active_track_id,
                neutralize=neutralize, candidate_id=candidate_id,
            )

        old_track_id = self.active_track_id
        self.active_track_id = candidate_id
        self.lost_frames = 0
        self.reacquire_candidate_id = None
        self.reacquire_hits = 0
        self.update_last_target(candidate)
        return self._result(
            'REACQUIRED', candidate, self.active_track_id,
            old_track_id=old_track_id,
        )

    def roi_coverage(self, bbox, image_width, image_height):
        if image_width <= 0 or image_height <= 0:
            return 0.0
        x1, y1, x2, y2 = map(float, bbox)
        x1 = max(0.0, min(image_width, x1))
        x2 = max(0.0, min(image_width, x2))
        y1 = max(0.0, min(image_height, y1))
        y2 = max(0.0, min(image_height, y2))
        box_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        if box_area <= 0.0:
            return 0.0
        rx1, rx2 = image_width * self.roi_margin_x, image_width * (1 - self.roi_margin_x)
        ry1, ry2 = image_height * self.roi_margin_y, image_height * (1 - self.roi_margin_y)
        inside_w = max(0.0, min(x2, rx2) - max(x1, rx1))
        inside_h = max(0.0, min(y2, ry2) - max(y1, ry1))
        return (inside_w * inside_h) / box_area

    @staticmethod
    def _similar_recent_box(previous, current):
        px1, py1, px2, py2 = map(float, previous)
        x1, y1, x2, y2 = map(float, current)
        pw, ph = max(1., px2-px1), max(1., py2-py1)
        w, h = max(1., x2-x1), max(1., y2-y1)
        if not (0.55 <= w/pw <= 1.85 and 0.55 <= h/ph <= 1.85):
            return None
        distance = math.hypot((x1+x2-px1-px2)/2, (y1+y2-py1-py2)/2)
        diagonal = math.hypot(max(w,pw), max(h,ph))
        threshold = min(95., max(24., 1.6*diagonal))
        if distance > threshold:
            return None
        return distance / max(1., threshold)

    def _match_recent_completed(self, detection, now, detections, aircraft_id):

        bbox = detection['bbox']
        candidates = []
        for key, previous in self.completed_target_observations.items():
            if now - previous['last_seen'] > self.reid_max_gap:
                continue
            known_aircraft = previous.get('aircraft_id')
            if (aircraft_id is not None and known_aircraft is not None
                    and str(aircraft_id) != str(known_aircraft)):
                continue
            score = self._similar_recent_box(previous['bbox'], bbox)
            if score is not None:
                candidates.append((score, key))
        candidates.sort(key=lambda item: item[0])
        if len(candidates) != 1:
            return None
        score, key = candidates[0]
        previous = self.completed_target_observations[key]
        close_boxes = sum(
            self._similar_recent_box(previous['bbox'], d['bbox']) is not None
            for d in detections
            if isinstance(d, dict) and isinstance(d.get('bbox'), (list, tuple))
            and len(d['bbox']) == 4
        )
        return key if close_boxes == 1 else None

    def _remember_completed_observation(self, key, detection, now, aircraft_id):
        if detection is None:
            return
        previous = self.completed_target_observations.get(key, {})
        self.completed_target_observations[key] = {
            'bbox': tuple(detection['bbox']),
            'last_seen': now,
            'aircraft_id': (aircraft_id if aircraft_id is not None
                            else previous.get('aircraft_id')),
        }
        self.completed_track_aliases[str(detection['track_id'])] = (key, now)

    def _update_roi_progress(self, result, image_width, image_height, aircraft_id=None, detections=None):
        now = time.monotonic()
        detection = result.get('detection')
        track_id = result.get('track_id')
        valid = (
            detection is not None
            and track_id is not None
            and track_id == self.active_track_id
            and detection.get('track_id') == track_id
            and self.roi_coverage(detection['bbox'], image_width, image_height)
            >= self.roi_min_coverage
        )

        target_key = (
            ('aircraft', str(aircraft_id)) if aircraft_id is not None
            else ('track', str(track_id))
        )

        if valid and target_key not in self.completed_lock_targets:
            alias = self.completed_track_aliases.get(str(track_id))
            if alias is not None and now - alias[1] <= self.reid_max_gap:
                alias_key = alias[0]
                known = self.completed_target_observations.get(alias_key, {})
                if (aircraft_id is None or known.get('aircraft_id') is None
                        or str(aircraft_id) == str(known['aircraft_id'])):
                    target_key = alias_key
            if target_key not in self.completed_lock_targets:
                matched = self._match_recent_completed(
                    detection, now, detections or [], aircraft_id
                )
                if matched is not None:
                    target_key = matched

        already_completed = bool(valid and target_key in self.completed_lock_targets)
        if already_completed:
            self._remember_completed_observation(
                target_key, detection, now, aircraft_id
            )

        if not valid:
            self.reset_roi_lock()
        elif already_completed:
            if self.roi_lock_success and self.roi_track_id == track_id:

                self.roi_last_seen_time = now
                self.roi_elapsed = self.lock_duration
            else:

                self.reset_roi_lock()
        elif (
            self.roi_track_id != track_id
            or self.roi_start_time is None
            or (
                self.roi_last_seen_time is not None
                and now - self.roi_last_seen_time > self.max_detection_gap
            )
        ):
            self.roi_track_id = track_id
            self.roi_start_time = now
            self.roi_last_seen_time = now
            self.roi_elapsed = 0.0
            self.roi_lock_success = False
        else:
            self.roi_last_seen_time = now
            self.roi_elapsed = min(self.lock_duration, now - self.roi_start_time)

        just_succeeded = bool(
            valid and self.roi_elapsed >= self.lock_duration and not self.roi_lock_success
        )
        if just_succeeded:
            self.roi_lock_success = True
            self.completed_lock_targets.add(target_key)
            self._remember_completed_observation(
                target_key, detection, now, aircraft_id
            )
        result.update({
            'lock_seconds': self.roi_elapsed,
            'lock_duration': self.lock_duration,
            'lock_progress': self.roi_elapsed / self.lock_duration,
            'lock_success': self.roi_lock_success,
            'lock_just_succeeded': just_succeeded,
            'roi_valid': valid,
            'already_locked': bool(already_completed),
        })
        return result

    def get_roi_progress(self):
        if (
            self.roi_last_seen_time is not None
            and time.monotonic() - self.roi_last_seen_time > self.max_detection_gap
        ):
            self.reset_roi_lock()
        return self.roi_elapsed, self.roi_lock_success