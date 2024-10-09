# tile_tif
 A package to tile large N-dimensional tiff files through memmapping for ease of processing.

## Overview

tile_tif is a package to aid in the processing of large N-dimensional tif files with the use of memmapped tiles. Generator objects allow for pipeline analysis on smaller scale computers. This package is a single class with methods for getting tiles and offsets, as well as normalization.

## Instantiation

To begin, a tile_tif object must be instantiated with a filename. Optionally, several more arguments can be specified if you already know the structure of your tif. 

```{python}
from tile_tif import tile_tif

t = tile_tif('./images/file.tif',
             tile_axes = [-3,-2], # Axes you want to tile over. Can be any two or more 
             channel_axis = -1, # 
             pixel_max = 15e6, # Maximum pixels per tile. Keep your computer's memory spec in mind with this.
             overlap = 0.1, # Fractional overlap between tiles, to mitigate clipping errors.
             scale_quantile = 0.0005 # Fractional quantile to normalize min/max values around. 
)
```

## Application

Tiles can then be generated and processed individually.

```{python}
import numpy as np
from matplotlib import pyplot as plt
plt.figure(figsize=(20,20))
for i,(tile,offset) in enumerate(t.split()):
    arr = t.normalize(np.array(tile).astype(float),trim=True)
    arr = np.moveaxis(arr,1,-1)
    arr = arr.mean(0)
    arr = np.concatenate([arr,np.zeros_like(arr[...,:1])],axis=-1)
    plt.subplot(t.split_factor,t.split_factor,i+1)
    plt.imshow(arr)
    plt.axis('off')
```


## Generators

Class methods exist to create generators for tiles, offsets, and both at once. As this is meant to apply to very large tif files, you normally wouldn't output to lists.

```{python}
# Tile generator
tiles = [i for i in t.tiles()]
# Offset generator
offsets = [i for i in t.offsets()]
# (Tile,Offset) generator
splits = [(tiles,offsets) for tiles,offsets in t.split()]
```

## Single tile calls

When you need to get a single tile, you can use the following method:

```{python}
index = [2,3] # An index of the tile you want to show. This can be either an integer or list-like of same shape as tile_axes.
tile = t.get_tile(index) # Instantiates a memmap tile
offset = t.get_offset(index)
```
## Normalization

tile_tif has an inbuilt method to help with normalizing values. It uses a two-tailed quantile-based approach, where the minimum is set to the qth fractional quantile, and maximum to the 1-qth fractional quantile. It uses memmapped splicing to subsample the full array on the assumptions that there is a large enough subsample to be broadly valid. If a channel_axis is specified, the mins and maxes are per-channel. 

```{python}
arr = np.array(t.get_tile(index)) # This must be instantiated as an array to have operations performed on it.
arr = t.normalize(arr,       # Array is normalized based on values.
				  trim=True) # Default false. Will set all values to within [0,1] if true.
```

## Updating parameters

Parameters can be respecified and the object updated without reinstantiating. For instance:

```{python}
t.scale_quantile = 0.002
t.update()
```