# code imported from jupiter notebook
#[1] Required libraries
from pathlib import Path
import random

import matplotlib.pyplot as plt
import torch
import torch.nn.functional as F
from torch.autograd import Variable
from torchvision import transforms

from segmentation.datasets import HerbariumSheets, ImageFolder, SemiSupervisedDataLoader
from segmentation.instances import DiscriminativeLoss, mean_shift, visualise_embeddings, visualise_instances
from segmentation.network import SemanticInstanceSegmentation
from segmentation.training import train

#[2] create model and clustening function
#**************************************************
# extracted label classes as parameters
#**************************************************
# set the number of label classes
label_classes = 5
model = SemanticInstanceSegmentation(label_classes = 5) #From network
instance_clustering = DiscriminativeLoss() #From instances

#[3] random transforms for pictures
#    cropping for herbarium sheets:
#      96 dpi = h: 1728 w: 1152
#      72 dpi = h: 1320 w:  872
#***************************************************
# convert to parameters random crop heigth and width
#***************************************************
transform = transforms.Compose([ #torchvision
    transforms.RandomRotation(5),
    transforms.RandomCrop((1728, 1152)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.ToTensor()])

target_transform = transforms.Compose([transform, transforms.Lambda(lambda x: (x * 255).long())])

#**************************************************
#convert to parameter batch size
#**************************************************
batch_size = 3

# WARNING: Don't use multiple workers for loading! Doesn't work with setting random seed
# Slides: copies the data if required into the data/raw/images,
# HerbariumSheets, labels] directories and returns
# import pdb; pdb.set_trace()
train_data_labelled = HerbariumSheets(download=True, train=True, root='data', transform=transform, target_transform=target_transform)
train_loader_labelled = torch.utils.data.DataLoader(train_data_labelled, batch_size=batch_size, drop_last=True, shuffle=True)
train_data_unlabelled = ImageFolder(root='data/sheets', transform=transform)
train_loader_unlabelled = torch.utils.data.DataLoader(train_data_unlabelled, batch_size=batch_size, drop_last=True, shuffle=True)
train_loader = SemiSupervisedDataLoader(train_loader_labelled, train_loader_unlabelled)

test_data_labelled = HerbariumSheets(download=True, train=False, root='data', transform=transform, target_transform=target_transform)
test_loader_labelled = torch.utils.data.DataLoader(test_data_labelled, batch_size=batch_size, drop_last=True, shuffle=True)
test_data_unlabelled = ImageFolder(root='data/sheets', transform=transform)
test_loader_unlabelled = torch.utils.data.DataLoader(test_data_unlabelled, batch_size=batch_size, drop_last=True, shuffle=True)
test_loader = SemiSupervisedDataLoader(test_loader_labelled, test_loader_unlabelled)


#[4] Train model
#**************************************************
# extracted epochs and label classes as parameters
#**************************************************
epochs = 40
label_classes = 5
train(model, instance_clustering, train_loader, test_loader, epochs, label_classes)


