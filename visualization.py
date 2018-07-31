from matplotlib.animation import FuncAnimation
from matplotlib.font_manager import FontProperties
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def annotate(ax, P, labels=None):
    if labels is None:
        labels = range(len(P))

    font = FontProperties()
    font.set_weight("bold")

    for label, p in zip(labels, P):
        ax.text(*p, label, alpha=0.8, fontproperties=font)


def plot2d(P, do_annotate=False, color=None):
    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.scatter(P[:, 0], P[:, 1], c=color)

    if do_annotate:
        annotate(ax, P, labels=range(0, len(P), 50))

    ax.set_xlabel('x axis')
    ax.set_ylabel('y axis')
    ax.set_aspect('equal', 'datalim')

    plt.show()


def plot3d(P, do_annotate=False, elev=45, azim=0, color=None):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(P[:, 0], P[:, 1], P[:, 2], c=color)

    if do_annotate:
        annotate(ax, P)

    ax.set_xlabel('x axis')
    ax.set_ylabel('y axis')
    ax.set_zlabel('z axis')
    ax.view_init(elev, azim)
    ax.set_aspect('equal', 'datalim')

    plt.show()
