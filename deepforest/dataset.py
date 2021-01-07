"""
Dataset model

https://pytorch.org/docs/stable/torchvision/models.html#object-detection-instance-segmentation-and-person-keypoint-detection

During training, the model expects both the input tensors, as well as a targets (list of dictionary), containing:

boxes (FloatTensor[N, 4]): the ground-truth boxes in [x1, y1, x2, y2] format, with values between 0 and H and 0 and W

labels (Int64Tensor[N]): the class label for each ground-truth box

https://colab.research.google.com/github/benihime91/pytorch_retinanet/blob/master/demo.ipynb#scrollTo=0zNGhr6D7xGN

"""
import os
import pandas as pd
from skimage import io
from torch.utils.data import Dataset
from deepforest import transforms as T
import numpy as np

def get_transform(train):
    transforms = []
    transforms.append(T.ToTensor())
    if train:
        transforms.append(T.RandomHorizontalFlip(0.5))
    return T.Compose(transforms)

idx_to_label = {
    "Tree": 0
}

class TreeDataset(Dataset):
    def __init__(self, csv_file, root_dir, transforms):
        """
        Args:
            csv_file (string): Path to the csv file with annotations.
            root_dir (string): Directory with all the images.
            transform (callable, optional): Optional transform to be applied
                on a sample.
        """
        self.annotations = pd.read_csv(csv_file)
        self.root_dir = root_dir
        self.transform = transforms

    def __len__(self):
        return self.annotations.shape[0]

    def __getitem__(self, idx):
        path = self.annotations.loc[idx, "image_path"]
        img_name = os.path.join(self.root_dir, path)
        image = io.imread(img_name)

        #rescale to 0-1
        image = image/255

        #select annotations
        image_annotations = self.annotations[self.annotations.image_path ==
                                             path]
        targets = {}
        targets["boxes"] = image_annotations[["xmin", "ymin", "xmax",
                                   "ymax"]].values.astype(float)
        
        #Labels need to be encoded? 0 or 1 indexed?, ALl tree for the moment.
        targets["labels"] = image_annotations.label.apply(lambda x: idx_to_label[x]).values.astype(int)

        if self.transform:
            image, targets = self.transform(image, targets)

        return image, targets   