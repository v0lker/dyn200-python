import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation

data_store = None
ax = None
shutdown = None

def animate(n):
    ti, to, s, p = data_store.data_get()
    ax.clear()
    ax.plot(ti, to)


def on_close(event):
    shutdown()


def show_ui(ds, shutdown_fn):
    global ax
    global data_store
    global shutdown

    data_store = ds
    shutdown = shutdown_fn

    fig, ax = plt.subplots(figsize=(4, 3))
    fig.canvas.mpl_connect('close_event', on_close)
    ani = FuncAnimation(fig, animate, frames=20, interval=100, repeat=True)
    plt.show()

