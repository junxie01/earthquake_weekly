import matplotlib.pyplot as plt
from obspy.imaging.beachball import beach

# --- 设定参数 ---
strike, dip, rake = 150, 45, 90 

fig, ax = plt.subplots(figsize=(6, 6))

# 使用 beach 函数替代 beachball
# xy=(0, 0) 表示球心的位置
# width=200 是球的直径
focmec = [strike, dip, rake]
beach_plot = beach(focmec, xy=(0, 0), width=200, linewidth=1, facecolor='red')

# 将震源球添加到当前的坐标轴
ax.add_collection(beach_plot)

# --- 必须设置坐标轴范围，否则球可能在视野之外 ---
ax.set_xlim(-120, 120)
ax.set_ylim(-120, 120)
ax.set_aspect('equal')
ax.axis('off')

plt.title(f"Focal Mechanism\nStrike: {strike}°, Dip: {dip}°, Rake: {rake}°")
plt.show()
