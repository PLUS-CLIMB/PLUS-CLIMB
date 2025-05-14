
import matplotlib.pyplot as plt
import numpy as np
import math

def plot_band(array, title="Band", cmap="gray", figsize=(6, 5)):
    """
    Plot a single raster array.

    Parameters:
    - array: 2D numpy array
    - title: Title of the plot
    - cmap: Colormap
    - figsize: Figure size (tuple)
    """
    plt.figure(figsize=figsize)
    plt.imshow(array, cmap=cmap)
    plt.title(title)
    plt.colorbar()
    plt.axis("off")
    plt.tight_layout()
    plt.show()


def plot_multiple_bands(bands_dict, cmap="gray", figsize=(6, 5)):
    """
    Plot multiple bands in a 2-column layout.

    Parameters:
    - bands_dict: Dictionary {band_name: array}
    - cmap: Colormap for all bands
    - figsize: Base size per subplot (width, height)
    """
    n = len(bands_dict)
    n_cols = 2
    n_rows = math.ceil(n / n_cols)

    fig, axs = plt.subplots(n_rows, n_cols, figsize=(figsize[0] * n_cols, figsize[1] * n_rows))
    axs = axs.flatten()  # ensure it's a flat list

    for i, (band_name, array) in enumerate(bands_dict.items()):
        im = axs[i].imshow(array, cmap=cmap)
        axs[i].set_title(band_name)
        axs[i].axis("off")
        plt.colorbar(im, ax=axs[i], orientation='vertical', fraction=0.046, pad=0.04)

    # Turn off any unused axes
    for j in range(i + 1, len(axs)):
        axs[j].axis("off")

    plt.tight_layout()
    plt.show()

