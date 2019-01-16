"""
Generate training clips and save the images in h5py to reduce clutter
"""
import argparse
import numpy as np
import os
import h5py
import pandas as pd
from DeepForest import onthefly_generator, preprocess, config
import sys
import gc

#supress warnings
import warnings
warnings.simplefilter("ignore")

def parse_args():    
    
    #Set tile from command line args
    parser = argparse.ArgumentParser(description='Generate crops for training')
    parser.add_argument('--tile', help='filename of the LIDAR tile to process' )
    args = parser.parse_args()    
    
    return args

def run(tile,DeepForest_config):
    
    """Crop 4 channel arrays from RGB and LIDAR CHM
    tile: the CSV training file containing the tree detections
    """
    
    #Read in data
    data = preprocess.load_data(data_dir=tile, res=0.1, lidar_path=DeepForest_config["lidar_path"])
    
    #Create windows
    windows = preprocess.create_windows(data, DeepForest_config)
    
    if windows is None:
        print("Invalid window")
        return None
    
    #Create generate
    generator = onthefly_generator.OnTheFlyGenerator(data, windows, DeepForest_config)
    
    #Get tile filename for storing
    tilename = os.path.split(tile)[-1]
    tilename = os.path.splitext(tilename)[0]
    
    #Create h5 dataset    
    # open a hdf5 file and create arrays
    h5_filename = os.path.join(DeepForest_config["h5_dir"], tilename + ".h5")
    hdf5_file = h5py.File(h5_filename, mode='w')    
    
    #A 4 channel image of square patch size.
    train_shape = (generator.size(), DeepForest_config["patch_size"], DeepForest_config["patch_size"], 4)
    
    #Create h5 dataset to fill
    hdf5_file.create_dataset("train_imgs", train_shape, dtype='f')
    
    #Generate crops and annotations
    labels = {}
    
    for i in range(generator.size()):
        
        print("window {i} from tile {tilename}".format(i=i, tilename=tilename))

        #Load images
        image = generator.load_image(i)
        
        #If image window is corrupt (RGB/LIDAR missing), go to next tile, it won't be in labeldf
        if image is None:
            continue
            
        hdf5_file["train_imgs"][i,...] = image        
        
        #Load annotations and write a pandas frame
        label = generator.load_annotations(i)
        labeldf = pd.DataFrame(label)
        
        #Add tilename and window ID
        labeldf['tile'] = tilename
        labeldf['window'] = i
        
        #add to labels
        labels[i] = labeldf
    
    #Write labels to pandas frame
    labeldf = pd.concat(labels, ignore_index=True)
    
    csv_filename = os.path.join(DeepForest_config["h5_dir"], tilename + ".csv")    
    labeldf.to_csv(csv_filename,index=False)
    
    #Need to close h5py?
    hdf5_file.close()
    
    #flush system
    sys.stdout.flush()
    
    #force garbage collect
    gc.collect()
    
    return "{} completed".format(tilename)
    
if __name__ == "__main__":
    import yaml
    
    #parse args
    args=parse_args()
    
    #load config
    with open('_config.yml', 'r') as f:
        DeepForest_config = yaml.load(f)    
    
    run(args.tile, DeepForest_config)


    
    