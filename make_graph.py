import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import random
from datetime import datetime, timedelta
from collections import defaultdict

# --- 1. 데이터 생성 조건 설정 ---
start_time = datetime(2025, 8, 29, 14, 0, 0)
end_time = datetime(2025, 8, 29, 17, 0, 0)
cutoff_time = datetime(2025, 8, 29, 16, 30, 0)
num_events = 200
minute_delta = 3

# --- 2. 설정된 시간 범위 내에서 무작위 데이터 생성 ---
raw_data = []
total_seconds_in_range = (end_time - start_time).total_seconds()

for _ in range(num_events):
    random_seconds = random.randint(0, int(total_seconds_in_range))
    event_time = start_time + timedelta(seconds=random_seconds)
    flag = random.choices([0, 1, 2, 3], weights=[10, 8, 3, 3])[0]
    raw_data.append((event_time, flag))


# --- 3. 5분 단위로 데이터 집계 (Binning) ---
binned_data = defaultdict(lambda: {'green': 0, 'red': 0, 'orange': 0, 'dark_grey': 0, 'blue': 0})

for event_time, flag in raw_data:
    bin_key = event_time.replace(
        minute=(event_time.minute // minute_delta) * minute_delta, second=0, microsecond=0
    )

    if bin_key >= cutoff_time:
        binned_data[bin_key]['blue'] += 1
    else:
        if flag == 0:
            binned_data[bin_key]['green'] += 1
        elif flag == 1:
            binned_data[bin_key]['red'] += 1
        elif flag == 2:
            binned_data[bin_key]['orange'] += 1
        elif flag == 3:
            binned_data[bin_key]['dark_grey'] += 1

# --- 4. 그래프 그리기 ---
fig, ax = plt.subplots(figsize=(15, 4))
fig.set_facecolor('#28343B')
ax.set_facecolor('#28343B')

sorted_bins = sorted(binned_data.items())

max_positive_count = 0
max_negative_count = 0
for _, counts in sorted_bins:
    max_positive_count = max(max_positive_count, counts['green'] + counts['blue'])
    negative_sum = counts['red'] + counts['orange'] + counts['dark_grey']
    max_negative_count = max(max_negative_count, negative_sum)

for time_bin, counts in sorted_bins:
    bar_width = timedelta(minutes=3)

    if counts['blue'] > 0:
        ax.bar(time_bin, counts['blue'], color='skyblue', width=bar_width, align='edge')
    if counts['green'] > 0:
        ax.bar(time_bin, counts['green'], color='lime', width=bar_width, align='edge')
    if counts['red'] > 0:
        ax.bar(time_bin, -counts['red'], color='red', width=bar_width, align='edge')
    if counts['orange'] > 0:
        ax.bar(time_bin, -counts['orange'], bottom=-counts['red'], color='orange', width=bar_width, align='edge')
    if counts['dark_grey'] > 0:
        bottom_position = -(counts['red'] + counts['orange'])
        ax.bar(time_bin, -counts['dark_grey'], bottom=bottom_position, color='dimgrey', width=bar_width, align='edge')

# --- 5. 그래프 스타일링 ---
# 중앙 수평선만 남김
ax.axhline(0, color='grey', linewidth=2.5)
ax.set_ylim(-(max_negative_count + 1), max_positive_count + 1)
if max_positive_count == 0 and max_negative_count == 0:
    ax.set_ylim(-3, 3)

ax.set_xlim(start_time, end_time)

# ⭐️ 변경점: X축과 Y축 관련 시각요소 모두 숨기기
ax.xaxis.set_visible(False)
ax.yaxis.set_visible(False)

# ⭐️ 변경점: 모든 테두리(spines)를 보이지 않게 처리
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)

plt.tight_layout()

fig.patch.set_alpha(0.0)
ax.patch.set_alpha(0.0)
plt.show()
# plt.savefig('your_graph.png', transparent=True)