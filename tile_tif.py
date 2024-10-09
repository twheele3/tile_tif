import os
import tifffile
import numpy as np
from matplotlib import pyplot as plt

class tile_tif():
    """
    Tile tif files into manageable pieces for your memory spec. Flexible parameterization works with ND-images with options to designate channels, define overlap to prevent pipeline clipping, and quantile normalization.
    
    Args:
        filename (str) : Full filename (with directory) of tif file.
        tile_axes (list) : List of ints correlating to axes to tile over. Negative indexing allowed.
        channel_axis (int) : Axis index corresponding to channels, used for normalization. Negative indexing allowed.
        pixel_max (int) : Maximum number of pixels allowed per tile. 
        overlap (float) : Factor by which to extend boundaries that overlap with neighboring tiles.
        scale_quantile (float) : Quantile to set as min/reciprocal max for scaling.
    """
    def __init__(self, filename, tile_axes = [-2,-1], channel_axis = None, pixel_max = 16e6, overlap = 0., scale_quantile = 0.005):
        ## Initial checks
        # Checks for valid tiff file
        self.filename = filename
        assert os.path.exists(filename), AssertionError("Specified file does not exist.")
        assert os.path.splitext(filename)[1].lower() in ['.tif','.tiff'], AssertionError("Invalid filetype.")
        # Getting shape of tiff
        self.shape = tifffile.memmap(self.filename,mode='r').shape
        # Checking that all tile_axes correspond to existing axes in the tiff shape
        assert np.all(np.abs(tile_axes) <= len(self.shape)),AssertionError("tile_axes do not match tif shape.")
        ## Declaring attributes
        # Parsing negative axis calls
        self.tile_axes = [(len(self.shape)+i)%len(self.shape) for i in tile_axes]
        if channel_axis:
            self.channel_axis = (len(self.shape)+channel_axis)%len(self.shape)
        else:
            self.channel_axis = None
        self.scale_quantile = scale_quantile
        self.overlap = overlap
        self.pixel_max = pixel_max
        # Updating hidden attributes
        self.update()
    
    def update(self):
        """
        Method for updating tiling after changing attributes.
        """
        self.split_factor = np.ceil((np.prod(self.shape) / (self.pixel_max/(1+self.overlap)))**(1/len(self.tile_axes))).astype(int)
        self.__tile_range = np.repeat(self.split_factor,len(self.tile_axes))
        self.__idxarrs = []
        for i in range(len(self.shape)):
            if i not in self.tile_axes:
                self.__idxarrs.append(list())
                continue
            idx = np.linspace(0,self.shape[i],self.split_factor+1).astype(int)
            margin = int(((1+self.overlap)**(1/len(self.tile_axes)) - 1) * idx[1])
            a1 = idx[:-1] - margin
            a2 = idx[1:] + margin
            a1[a1 < 0] = 0
            a2[a2 > self.shape[i]] = self.shape[i]
            self.__idxarrs.append(np.array([a1,a2]).T)

        self.__tile_idx = np.array([i.flatten() for i in np.indices(self.__tile_range)]).T
        self.len = len(self.__tile_idx)

        if not self.channel_axis:
            slice_tuple = tuple([slice(0,j,self.split_factor) if i in self.tile_axes else slice(0,j,None) for i,j in enumerate(self.shape)])
            self.max = np.quantile(tifffile.memmap(self.filename,mode='r')[slice_tuple],1-self.scale_quantile)
            self.min = np.quantile(tifffile.memmap(self.filename,mode='r')[slice_tuple],self.scale_quantile)
        else:
            self.max = []
            self.min = []
            for ch in range(self.shape[self.channel_axis]):
                slice_tuple = tuple([slice(0,j,self.split_factor) if i in self.tile_axes else slice(0,j,None) if i != self.channel_axis else slice(ch,ch+1,None) for i,j in enumerate(self.shape)])
                self.max.append(np.quantile(tifffile.memmap(self.filename,mode='r')[slice_tuple],1-self.scale_quantile))
                self.min.append(np.quantile(tifffile.memmap(self.filename,mode='r')[slice_tuple],self.scale_quantile))
        
        
        
    def __get_slice_index(self,idx):    
        ## Generates an array of [start,stop] indices in array format based on idx called and tiling attributes.
        if (type(idx) == int):
            try:
                pull_idx = self.__tile_idx[idx]
            except:
                raise Exception("Index is outside of tile range.")
        else:
            try: 
                if len(idx) == len(self.tile_axes):
                    pull_idx = idx
                else:
                    raise Exception("Index length does not match tile axes.")
            except:
                raise Exception("Could not parse index.")
        slice_idx = [[0,i] for i in self.shape]
        for i,j in enumerate(self.tile_axes):
            slice_idx[j] = self.__idxarrs[j][pull_idx[i]]
        return np.array(slice_idx)
    
    
    
    def __get_slice_tuple(self,idx):
        ## Transforms array indices into a tuple for call.
        return tuple([slice(i,j) for i,j in self.__get_slice_index(idx)])

    
    
    def tiles(self):
        """
        Yields a generator for all tiles in tiled tif. 
        """
        for index in range(self.len):
            yield tifffile.memmap(self.filename,mode='r')[self.__get_slice_tuple(index)]
            
            
            
    def offsets(self):
        """
        Yields a generator for all offsets of tiles in tiled tif.
        """
        for index in range(self.len):
            yield (self.__get_slice_index(idx))
            
            
            
    def split(self):
        """
        Yields a generator for (tile,offset) of each locus in the tiled tif.
        """
        for index in range(self.len):
            tile = tifffile.memmap(self.filename,mode='r')[self.__get_slice_tuple(index)]
            offset = (self.__get_slice_index(index))
            yield tile,offset
        
        
        
    def get_tile(self, index):
        """
        Gets tile by index. Index may be either an int < tile_tif.len, or a list-like of ints corresponding to tile location.
        """
        return tifffile.memmap(self.filename,mode='r')[self.__get_slice_tuple(index)]
    
    
    
    def get_offset(self,index):
        """
        Gets offset by index. Index may be either an int < tile_tif.len, or a list-like of ints corresponding to tile location.
        """
        return self.__get_slice_index(index)
        
        
        
    def normalize(self,arr,trim=False):
        """
        Normalizes array between [0,1] with respect to quantilized channel scales. Optionally trims any values falling outside of this range.
        
        Args:
            arr  (array)   : Array to be normalized. Must be declared as array (cannot be raw memmap tile)
            trim (boolean) : Whether to trim values falling outside of [0,1]
            
        Returns:
            array
        """
        if not self.channel_axis:
            arr = (arr - self.min) / (self.max - self.min)
        else: 
            for ch in range(self.shape[self.channel_axis]):
                slice_tuple = tuple([slice(0,j,None) if i != self.channel_axis else slice(ch,ch+1,None) for i,j in enumerate(self.shape)])
                arr[slice_tuple] = (arr[slice_tuple] - self.min[ch]) / (self.max[ch] - self.min[ch])
        if trim:
            arr[arr>1] = 1
            arr[arr<0] = 0
        return arr
