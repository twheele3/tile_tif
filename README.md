# tile_tif
 A package to tile large N-dimensional tiff files through memmapping for ease of processing.

## Overview

tile_tif is a package to aid in the processing of large N-dimensional tif files with the use of memmapped tiles. Generator objects allow for pipeline analysis on smaller scale computers. This package is a single class with methods for 

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