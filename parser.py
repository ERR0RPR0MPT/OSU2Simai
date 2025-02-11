import random

from utils import *


class OsuFileParser:
    def __init__(self):
        self.data = {}
        self.timing = []
        self.objects = []
        self.keys = 4
        self.bg = ''
        self.cst_keys = False
        self.cst_keys_list = 0
        self.cst_keys_end_time = 0

    def parse(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            section = None
            for line in file:
                line = line.strip()
                if not line or line.startswith('//'):
                    continue
                elif line.startswith('[') and line.endswith(']'):
                    section = line[1:-1]
                    self.data[section] = {}
                else:
                    self.parse_line(line, section)

    def parse_line(self, line, section):
        import re
        match = re.match(r'(\w+):(.*)', line)
        match_time = re.match(r'([\w.]+)(,(.*))+', line) or re.match(r'-([\w.]+)(,(.*))+', line)
        if match:
            key, value = match.groups()
            if section:
                if not key.startswith("AI"):
                    self.data[section][key] = convert_value(value)
            if section == 'Difficulty' and key == 'CircleSize':
                self.keys = convert_value(value)
        elif match_time:
            max_retries = 10
            is_finished = False
            parts = line.split(',')
            if len(parts) == 6:
                common = parse_common_parts(parts)

                from math import floor
                hit_object = {
                    'x': floor(self.keys * common[0] / 512),
                    'y': common[1],
                    'time': common[2],
                    'object_type': common[3],
                    'end': common[4],
                }

                note_pos = hit_object['x']
                if RANDOM:
                    for _ in range(max_retries):
                        # print("第", i, "次循环")
                        # 生成随机位置
                        if RANDOM == 2:
                            if note_pos == 4:
                                new_pos = np.random.randint(low=1, high=5)
                            else:
                                new_pos = np.random.randint(low=5, high=9)
                        else:
                            if RANDOM_CONSEQUENT_KEYS_ENABLE:
                                if not self.cst_keys:
                                    self.cst_keys = True
                                    # 计算随机轨道列表
                                    for k, v in RANDOM_CONSEQUENT_KEYS.items():
                                        temp_list = k.split(",")
                                        for k2, v2 in enumerate(temp_list):
                                            temp_list[k2] = int(v2)
                                        for _ in range(v):
                                            temp_consequent_keys_list.append(temp_list)

                                # 检测固定轨道是否已经存在
                                if common[2] > self.cst_keys_end_time or self.cst_keys_end_time == 0:
                                    self.cst_keys_end_time = common[2] + np.random.randint(
                                        low=RANDOM_CONSEQUENT_KEYS_DURATION_MIN,
                                        high=RANDOM_CONSEQUENT_KEYS_DURATION_MAX)
                                    self.cst_keys_list = random.choice(temp_consequent_keys_list)

                                # # 随机单音符轨道
                                # new_pos = random.choice(self.cst_keys_list) - 1
                                # 尝试直接使用原谱索引
                                new_pos = self.cst_keys_list[note_pos] - 1
                            else:
                                new_pos = np.random.randint(low=0, high=8)

                        # 轨道重叠检测
                        conflict = False
                        current_start = hit_object['time']
                        current_end = hit_object['end'] if hit_object['end'] != 0 else current_start
                        for obj in self.objects:
                            # 计算现有对象的结束时间
                            obj_end = obj['end'] if obj['end'] != 0 else obj['time']
                            # 检查同一轨道且时间重叠
                            if obj['x'] == new_pos and has_overlap(current_start, current_end, obj['time'],
                                                                   obj_end):
                                print(f"检测到轨道重叠")
                                conflict = True
                                break

                        # 没有冲突则采用新位置
                        if not conflict:
                            is_finished = True
                            note_pos = new_pos
                            break

                if is_finished:
                    hit_object['x'] = note_pos
                    print(hit_object)

                    # 双压检测：相同起始时间的数量
                    existing_time_count = sum(1 for obj in self.objects if obj['time'] == hit_object['time'])

                    # 多押检测：时间段重叠的数量
                    overlap_count = 0
                    current_start = hit_object['time']
                    current_end = hit_object['end'] if hit_object['end'] != 0 else current_start
                    for obj in self.objects:
                        obj_end = obj['end'] if obj['end'] != 0 else obj['time']
                        if has_overlap(current_start, current_end, obj['time'], obj_end):
                            overlap_count += 1

                    # 合并条件进行判断
                    if existing_time_count < 2 and overlap_count < 2:
                        self.objects.append(hit_object)
                    else:
                        skip_reason = []
                        if existing_time_count >= 2:
                            skip_reason.append("大于双压")
                        if overlap_count >= 2:
                            skip_reason.append("多押冲突")
                        print(f"检测到{' 且 '.join(skip_reason)}，跳过转换")
                else:
                    print("达到最大尝试次数，跳过该音符转换")

            elif len(parts) == 8:
                self.timing.append(parse_timing_point(line))
            elif len(parts) == 5 and self.bg == '':
                # print(parts)
                if parts[2].endswith('.jpg"') or parts[2].endswith('.png"'):
                    self.bg = parts[2][1:-1]

    def get_data(self):
        return self.data

    def get_timing(self):
        return self.timing

    def get_objects(self):
        return self.objects

    def get_bg(self):
        return self.bg

    def convert_simai_header(self):
        header = "&title=" + str(self.data['Metadata']['TitleUnicode']) + '\n'
        header = header + "&artist=" + str(self.data['Metadata']['ArtistUnicode']) + '\n'
        header = header + "&first=" + str(self.timing[0]['Offset'] / 1000) + '\n'
        header = header + "&des=" + AUTHOR + '\n'
        header = header + "&wholebpm=" + self.timing[0]['BPM'] + '\n'
        header = header + "&lv_5={}\n&inote_5=".format(LEVEL)

        simai = ''

        _STEPS = 96
        cur_bpm_pointer = 0
        cur_time = self.timing[0]['Offset']
        time_step = self.timing[0]['BeatLength'] * 4 / _STEPS
        cur_note = 0
        sub_count = 0

        _size = len(self.objects)
        _timing_size = len(self.timing)
        while cur_note < _size:
            note_str = ''
            first_note = True
            while cur_bpm_pointer < _timing_size and self.timing[cur_bpm_pointer]['Offset'] <= round(cur_time):
                if self.timing[cur_bpm_pointer]['BPM'] != '-1':
                    # print(self.timing[cur_bpm_pointer]['BPM'])
                    last_bpm = self.timing[cur_bpm_pointer]['BeatLength']
                    note_str = note_str + '\n(' + self.timing[cur_bpm_pointer]['BPM'] + ')'
                    time_step = last_bpm * 4 / _STEPS
                    sub_count = 0
                cur_bpm_pointer += 1
            if sub_count == 0:
                note_str = note_str + '\n{96}'
                sub_count = _STEPS
            lst_notes = []
            same_notes = False
            last_note_deleted = False
            while cur_note < _size and self.objects[cur_note]['time'] <= round(cur_time):
                if (not SAME) and same_notes:
                    cur_note += 1
                    continue
                if first_note:
                    first_note = False
                else:
                    if not last_note_deleted:
                        last_note_deleted = False
                        note_str = note_str + '/'
                        same_notes = True
                new_note = note_to_str(self.objects[cur_note], self.timing[0]['BeatLength'] * 4, self.keys,
                                       lst_notes, same_notes)
                # # 修改为随机的轨道值
                # self.objects[cur_note]['x'] = note_pos
                cur_note += 1
                if new_note == "delete":
                    last_note_deleted = True
                    continue
                lst_notes.append(new_note)
                note_str = note_str + new_note
            if note_str is not None:
                # 检测最后一个same音符是否为空
                if len(note_str) > 0 and note_str[-1] == '/':
                    note_str = note_str[:-1]
                simai = simai + note_str + ','
                sub_count -= 1
            cur_time += time_step

        simai = simai + '\nE\n'

        reduce_result = ''
        for line in simai.splitlines():
            reduce_result = reduce_result + compress_dashes(line) + '\n'

        return header + reduce_result

    def convert_ongeki_header(self):
        header = "Header.Version\t:\t1.0.0\n"
        header += "Header.Creator\t:\t{}\n".format(AUTHOR)
        header += "Header.FirstBpm\t:\t{}\n".format(self.timing[0]['BPM'])
        header += "Header.CommonBpm\t:\t{}\n".format(self.timing[0]['BPM'])
        header += "Header.MaximumBpm\t:\t{}\n".format(self.timing[0]['BPM'])
        header += "Header.MinimumBpm\t:\t{}\n".format(self.timing[0]['BPM'])
        header += "Header.Meter\t:\t4 / 4\n"
        header += "Header.TRESOLUTION\t:\t1920\n"
        header += "Header.XRESOLUTION\t:\t4096\n"
        header += "Header.ClickDefinition\t:\t1920\n"
        header += "Header.Tutorial\t:\tFalse\n"
        header += "Header.BeamDamage\t:\t2\n"
        header += "Header.HardBulletDamage\t:\t2\n"
        header += "Header.DangerBulletDamage\t:\t4\n"
        header += "Header.BulletDamage\t:\t1\n"
        header += "Header.ProgJudgeBpm\t:\t{}\n".format(240)

        header += "\n\n\n\n\n"

        output_tap = []
        output_hold = []

        beat_len = self.timing[0]['BeatLength'] * 4
        start = self.timing[0]['Offset']
        tot_len = 0

        for note_id, obj in enumerate(self.objects):
            x_value = ONGEKI_KEYS[obj['x']]
            measure, position = time_to_measure(obj['time'] - start, beat_len)
            tot_len = max(tot_len, measure)

            if obj['object_type'] <= 5:
                line = f"Tap\t:\t{obj['x']}\t:\tX[{x_value},0], T[{measure},{position}], C[False]"
                output_tap.append(line)

            elif obj['object_type'] == 128:
                end_measure, end_position = time_to_measure(obj['end'] - start, beat_len)
                line = (f"Hold\t:\t{obj['x']}, False, False\t:\t"
                        f"(X[{x_value},0], T[{measure},{position}])\t->\t"
                        f"(X[{x_value},0], T[{end_measure},{end_position}])")
                output_hold.append(line)
                tot_len = max(tot_len, end_measure)

        header += "Lane: 2:    (Type[LRS], X[{}, 0], T[0, 0])    ->    (Type[LRE], X[{}, 0], T[{}, 0])\n".format(
            ONGEKI_KEYS[2], ONGEKI_KEYS[2], tot_len)
        header += "Lane: 5:    (Type[LRS], X[{}, 0], T[0, 0])    ->    (Type[LRE], X[{}, 0], T[{}, 0])\n\n".format(
            ONGEKI_KEYS[5], ONGEKI_KEYS[5], tot_len)
        header += "Lane: 0:    (Type[LLS], X[{}, 0], T[0, 0])    ->    (Type[LLE], X[{}, 0], T[{}, 0])\n".format(
            ONGEKI_KEYS[0], ONGEKI_KEYS[0], tot_len)
        header += "Lane: 3:    (Type[LLS], X[{}, 0], T[0, 0])    ->    (Type[LLE], X[{}, 0], T[{}, 0])\n\n".format(
            ONGEKI_KEYS[3], ONGEKI_KEYS[3], tot_len)
        header += "Lane: 1:    (Type[LCS], X[{}, 0], T[0, 0])    ->    (Type[LCE], X[{}, 0], T[{}, 0])\n".format(
            ONGEKI_KEYS[1], ONGEKI_KEYS[1], tot_len)
        header += "Lane: 4:    (Type[LCS], X[{}, 0], T[0, 0])    ->    (Type[LCE], X[{}, 0], T[{}, 0])\n\n".format(
            ONGEKI_KEYS[4], ONGEKI_KEYS[4], tot_len)

        return header + "\n\n\n\n\n" + '\n'.join(output_tap) + "\n\n\n\n\n" + '\n'.join(output_hold)
