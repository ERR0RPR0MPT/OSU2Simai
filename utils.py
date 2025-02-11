import random

from config import *
import numpy as np


def convert_value(value):
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            if ',' in value:
                return [int(i) for i in value.split(',')]
            return value


def closest_fraction(x, y):
    target = x / y
    max_denominator = 96
    from fractions import Fraction
    fraction = Fraction(target).limit_denominator(max_denominator)
    return fraction.numerator, fraction.denominator


def compress_dashes(input_str):
    from math import gcd
    import re
    parts = re.split('(,+)', input_str)
    data_parts = parts[::2]
    dash_parts = parts[1::2]

    _gcd = 96
    for i in dash_parts:
        _gcd = gcd(_gcd, len(i))

    new_dash_counts = [len(i) // _gcd for i in dash_parts]

    new_str = re.sub(r'\{.*?}', '{' + str(96 // _gcd) + '}', data_parts[0])
    for i in range(len(dash_parts)):
        new_str += ',' * new_dash_counts[i] + data_parts[i + 1]

    return new_str


def parse_timing_point(timing_string):
    parts = timing_string.split(',')

    offset = float(parts[0])
    bpm = round(60000 / float(parts[1])) if float(parts[1]) > 0 else -1
    time_signature = int(parts[2])
    meter_time = int(parts[3])
    inherit = bool(int(parts[4]))
    volume = int(parts[5])
    effects = bool(int(parts[6]))
    sample_set = int(parts[7])

    return {
        'Offset': offset,
        'BPM': str(bpm),
        'BeatLength': float(parts[1]) if float(parts[1]) > 0 else -1,
        'Time Signature': f"{time_signature}/{meter_time}",
        'Inherited': inherit,
        'Volume': volume,
        'Effects': effects,
        'Sample Set': sample_set
    }


def parse_common_parts(para):
    x = int(para[0])
    y = int(para[1])
    time = int(para[2])
    note_type = int(para[3])
    para = int(para[5].split(':')[0])
    return x, y, time, note_type, para


def has_overlap(x1, x2, y1, y2):
    a_start, a_end = sorted([x1, x2])
    b_start, b_end = sorted([y1, y2])
    return max(a_start, b_start) <= min(a_end, b_end)


star_objects = []
touch_hold_objects = []


def note_to_str(param, beatLength, key_num, prev, same_notes):
    note_pos = KEYS[key_num][param['x']]

    # if RANDOM:
    #     if RANDOM == 2:
    #         if note_pos == 4:
    #             note_pos = np.random.randint(low=1, high=5)
    #         else:
    #             note_pos = np.random.randint(low=5, high=9)
    #     else:
    #         note_pos = np.random.randint(low=1, high=9)
    #         while note_pos in prev:
    #             note_pos = np.random.randint(low=1, high=9)

    if param['object_type'] != 128:
        if not RANDOM_NOTE_TYPE:
            return f"{note_pos}"

        # 随机决定 ExNote
        is_ex = 'x' if random.random() < RANDOM_NOTE_PROBABILITIES["tap-ex-note"] else ''
        # 随机决定 break tap
        is_break_tap = 'b' if random.random() < RANDOM_NOTE_PROBABILITIES["break-tap"] else ''
        # 随机决定 fire
        is_fire = 'f' if random.random() < RANDOM_NOTE_PROBABILITIES["fire"] else ''

        probabilities = RANDOM_NOTE_PROBABILITIES["1"]
        keys = list(probabilities.keys())
        weights = list(probabilities.values())
        is_touch = random.choices(keys, weights=weights, k=1)[0]

        touch_c = ""
        if is_touch == "touch":
            is_break_tap = ""
            probabilities = RANDOM_NOTE_PROBABILITIES["3"]
            keys = list(probabilities.keys())
            weights = list(probabilities.values())
            touch_c = random.choices(keys, weights=weights, k=1)[0]
            if note_pos != 1 and note_pos != 2 and touch_c == "C":
                note_pos = random.choice([1, 2])

        # 检测生成的 note 是否在星星尾部并删除音符
        if RANDOM_STAR_TAIL_HIT_DETECT:
            star_overlap_count = 0
            current_start = param['time']
            current_end = param['end'] if param['end'] != 0 else current_start
            tail_end_list = []
            for obj in star_objects:
                obj_end = obj['end'] + RANDOM_STAR_TAIL_HIT_DETECT_DELETE_DELAY if obj['end'] != 0 else obj['time']
                if has_overlap(current_start, current_end, obj['time'], obj_end):
                    tail_end_temp = obj["tail_end"]
                    # tail_end_list.append(tail_end_temp)
                    # tail_end_list.append(tail_end_temp - 1 if note_pos != 1 else 8)
                    # tail_end_list.append(tail_end_temp + 1 if note_pos != 8 else 1)
                    for ik in range(0, 9):
                        tail_end_list.append(ik)
                    star_overlap_count += 1
            if star_overlap_count > 0 and note_pos in tail_end_list:
                if RANDOM_STAR_TAIL_HIT_DETECT_DELETE_NOTE_INSTANTLY:
                    print(f"检测到{is_touch}撞尾，已自动删除撞尾音符")
                    return "delete"
                print(f"检测到{is_touch}撞尾，已自动添加 ExNote")
                is_ex = 'x'

        # 检测生成的 note 是否在星星尾部并加 ExNote
        if RANDOM_STAR_TAIL_HIT_DETECT:
            star_overlap_count = 0
            current_start = param['time']
            current_end = param['end'] if param['end'] != 0 else current_start
            tail_end_list = []
            for obj in star_objects:
                obj_end = obj['end'] + RANDOM_STAR_TAIL_HIT_DETECT_EX_DELAY if obj['end'] != 0 else obj['time']
                if has_overlap(current_start, current_end, obj['time'], obj_end):
                    tail_end_temp = obj["tail_end"]
                    # tail_end_list.append(tail_end_temp)
                    # tail_end_list.append(tail_end_temp - 1 if note_pos != 1 else 8)
                    # tail_end_list.append(tail_end_temp + 1 if note_pos != 8 else 1)
                    for ik in range(0, 9):
                        tail_end_list.append(ik)
                    star_overlap_count += 1
            if star_overlap_count > 0 and note_pos in tail_end_list:
                print(f"检测到{is_touch}撞尾，已自动添加 ExNote")
                is_ex = 'x'

        return f"{touch_c}{note_pos}{is_break_tap}{is_ex}{is_fire}"

    note_length = param['end'] - param['time']
    beat_len, beat_fac = closest_fraction(note_length, beatLength)
    if not RANDOM_NOTE_TYPE:
        return str(note_pos) + f'h[{beat_fac}:{beat_len}]'

    # 按随机决定音符类型
    probabilities = RANDOM_NOTE_PROBABILITIES["2"]
    keys = list(probabilities.keys())
    weights = list(probabilities.values())
    selected_key = random.choices(keys, weights=weights, k=1)[0]

    # 随机决定 break hold
    is_break_hold = 'b' if random.random() < RANDOM_NOTE_PROBABILITIES["break-hold"] else ''
    # 随机决定 break slide
    is_break_slide = 'b' if random.random() < RANDOM_NOTE_PROBABILITIES["break-slide"] else ''
    # 随机决定 ExNote
    is_ex = 'x' if random.random() < RANDOM_NOTE_PROBABILITIES["hold-ex-note"] else ''
    # 随机决定 fire
    is_fire = 'f' if random.random() < RANDOM_NOTE_PROBABILITIES["fire"] else ''

    # 随机决定 slide 类型
    probabilities = RANDOM_NOTE_PROBABILITIES["4"]
    keys = list(probabilities.keys())
    weights = list(probabilities.values())
    slide_type = random.choices(keys, weights=weights, k=1)[0]
    # slide_type = random.choice(['-', '^', '<', '>', 'v', 's', 'z', 'p', 'q', 'pp', 'qq', 'w'])
    # 随机决定 slide 终点
    p_list_without_a = [1, 2, 3, 4, 5, 6, 7, 8]
    p_list_without_a.remove(note_pos)
    # 当 slide 类型为某些值的时候去除
    angle_map = {
        1: 5, 2: 6, 3: 7, 4: 8, 5: 1, 6: 2, 7: 3, 8: 4,
    }
    if slide_type in ["-", "<", ">"]:
        p_list_without_a.remove(note_pos - 1 if note_pos != 1 else 8)
        p_list_without_a.remove(note_pos + 1 if note_pos != 8 else 1)
    elif slide_type in ["s", "z", "w"]:
        # 只能选对角线
        p_list_without_a = [angle_map[note_pos]]
    elif slide_type in ["^", "v"]:
        # 不能选对角线
        p_list_without_a.remove(angle_map[note_pos])
    slide_p = random.choice(p_list_without_a)

    # 检测 slide 是否存在重复音符和是否存在超出限制长度的星星
    if selected_key == "slide":
        star_overlap_count = 0
        current_start = param['time']
        current_end = param['end'] if param['end'] != 0 else current_start
        d = current_end - current_start
        if d < RANDOM_STAR_DURATION_MIN or d > RANDOM_STAR_DURATION_MAX:
            print("检测到超出限制长度的星星，转换为 hold")
            selected_key = "hold"
        else:
            for obj in star_objects:
                obj_end = obj['end'] if obj['end'] != 0 else obj['time']
                if has_overlap(current_start, current_end, obj['time'], obj_end):
                    star_overlap_count += 1
            if star_overlap_count >= 1:
                selected_key = "hold"

    # 检测 touch hold 是否存在重复音符和是否存在超出限制长度的 touch hold
    if selected_key == "touch-hold":
        touch_hold_overlap_count = 0
        current_start = param['time']
        current_end = param['end'] if param['end'] != 0 else current_start
        d = current_end - current_start
        if d < RANDOM_TOUCH_HOLD_DURATION_MIN or d > RANDOM_TOUCH_HOLD_DURATION_MAX:
            print("检测到超出限制长度的 Touch Hold，转换为 hold")
            selected_key = "hold"
        else:
            for obj in touch_hold_objects:
                obj_end = obj['end'] if obj['end'] != 0 else obj['time']
                if has_overlap(current_start, current_end, obj['time'], obj_end):
                    touch_hold_overlap_count += 1
            if touch_hold_overlap_count >= 1:
                selected_key = "hold"

    # 检测生成的 note 是否在星星尾部并删除音符
    if RANDOM_STAR_TAIL_HIT_DETECT:
        star_overlap_count = 0
        current_start = param['time']
        current_end = param['end'] if param['end'] != 0 else current_start
        tail_end_list = []
        for obj in star_objects:
            obj_end = obj['end'] + RANDOM_STAR_TAIL_HIT_DETECT_DELETE_DELAY if obj['end'] != 0 else obj['time']
            if has_overlap(current_start, current_end, obj['time'], obj_end):
                # tail_end_temp = obj["tail_end"]
                # tail_end_list.append(tail_end_temp)
                # tail_end_list.append(tail_end_temp - 1 if note_pos != 1 else 8)
                # tail_end_list.append(tail_end_temp + 1 if note_pos != 8 else 1)\
                for ik in range(0, 9):
                    tail_end_list.append(ik)
                # 当星星类型为绕圈时，对经过的note进行处理
                star_overlap_count += 1
        if star_overlap_count > 0 and note_pos in tail_end_list:
            if RANDOM_STAR_TAIL_HIT_DETECT_DELETE_NOTE_INSTANTLY:
                print(f"检测到{selected_key}撞尾，已自动删除撞尾音符")
                return "delete"
            print(f"检测到{selected_key}撞尾，已自动添加 ExNote")
            is_ex = 'x'

    # 检测生成的 note 是否在星星尾部并加 ExNote
    if RANDOM_STAR_TAIL_HIT_DETECT:
        star_overlap_count = 0
        current_start = param['time']
        current_end = param['end'] if param['end'] != 0 else current_start
        tail_end_list = []
        for obj in star_objects:
            obj_end = obj['end'] + RANDOM_STAR_TAIL_HIT_DETECT_EX_DELAY if obj['end'] != 0 else obj['time']
            if has_overlap(current_start, current_end, obj['time'], obj_end):
                # tail_end_temp = obj["tail_end"]
                # tail_end_list.append(tail_end_temp)
                # tail_end_list.append(tail_end_temp - 1 if note_pos != 1 else 8)
                # tail_end_list.append(tail_end_temp + 1 if note_pos != 8 else 1)\
                for ik in range(0, 9):
                    tail_end_list.append(ik)
                # 当星星类型为绕圈时，对经过的note进行处理
                star_overlap_count += 1
        if star_overlap_count > 0 and note_pos in tail_end_list:
            print(f"检测到{selected_key}撞尾，已自动添加 ExNote")
            is_ex = 'x'

    if selected_key == "hold" or same_notes:
        return f'{note_pos}{is_break_hold}{is_ex}h[{beat_fac}:{beat_len}]'
    elif selected_key == "slide":
        # 添加 star_type
        param["star_type"] = slide_type
        # 添加 tail 结束的位置
        param["tail_end"] = slide_p
        # 对 end 时间进行延长处理来避免重合
        param["end"] += RANDOM_STAR_DELAY
        star_objects.append(param)
        return f'{note_pos}{is_break_slide}{is_ex}{slide_type}{slide_p}[{beat_fac}:{beat_len}]'
    elif selected_key == "touch-hold":
        # 对 end 时间进行延长处理来避免重合
        param["end"] += RANDOM_TOUCH_HOLD_DELAY
        touch_hold_objects.append(param)
        return f'Ch{is_fire}[{beat_fac}:{beat_len}]'


def time_to_measure(time, BeatLength):
    beats = time / BeatLength
    measure = int(beats)
    position = int((beats - measure) * 1920)
    return measure + 1, position
