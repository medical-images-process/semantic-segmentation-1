# code imported from jupiter notebook
#[1] Required libraries
import sys

from itertools import islice
import logging

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

def validate_epoch(argv):
    print('Argument List:', argv)
    try:
      epoch = argv[0]
    except:
        print("provide int number of epoch to validate")
        
    #[2] create model and clustening function
    model = SemanticInstanceSegmentation() #From network
    instance_clustering = DiscriminativeLoss() #From instances

    #[3] random transforms for pictures
    transform = transforms.Compose([ #torchvision
        transforms.RandomRotation(5),
        transforms.RandomCrop((1764, 1169)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.ToTensor()])

    target_transform = transforms.Compose([transform, transforms.Lambda(lambda x: (x * 255).long())])

    batch_size = 3

    # WARNING: Don't use multiple workers for loading! Doesn't work with setting random seed
    # Slides: copies the data if required into the data/raw/[images,
    # instances, labels] directories and returns
    # import pdb; pdb.set_trace()
    train_data_labelled = HerbariumSheets(download=False, train=True, root='data', transform=transform, target_transform=target_transform)
    train_loader_labelled = torch.utils.data.DataLoader(train_data_labelled, batch_size=batch_size, drop_last=True, shuffle=True)
    train_data_unlabelled = ImageFolder(root='data/slides', transform=transform)
    train_loader_unlabelled = torch.utils.data.DataLoader(train_data_unlabelled, batch_size=batch_size, drop_last=True, shuffle=True)
    train_loader = SemiSupervisedDataLoader(train_loader_labelled, train_loader_unlabelled)

##    test_data_labelled = HerbariumSheets(download=True, train=False, root='data', transform=transform, target_transform=target_transform)
##    test_loader_labelled = torch.utils.data.DataLoader(test_data_labelled, batch_size=batch_size, drop_last=True, shuffle=True)
##    test_data_unlabelled = ImageFolder(root='data/slides', transform=transform)
##    test_loader_unlabelled = torch.utils.data.DataLoader(test_data_unlabelled, batch_size=batch_size, drop_last=True, shuffle=True)
##    test_loader = SemiSupervisedDataLoader(test_loader_labelled, test_loader_unlabelled)



    train_loader = torch.utils.data.DataLoader(train_data_labelled, batch_size=1, shuffle=False)

    image, labels, instances = next(iter(train_loader))

    image = Variable(image)
    instances = Variable(instances + 1)
    current_labels = labels[0, 0]
    current_instances = instances[0]

    fig, axes = plt.subplots(3, 1, figsize=(10, 14))
    for ax in axes.flatten(): ax.axis('off')

    axes[0].set_title('Original image')
    axes[0].imshow(image[0].data.numpy().transpose(1, 2, 0))
    axes[1].set_title('Ground truth classes')
    axes[1].imshow(current_labels.cpu().numpy().squeeze())
    axes[2].set_title('Ground truth instances')
    axes[2].imshow(current_instances.cpu().numpy().squeeze())
    plt.show()

if __name__ == "__main__":
   validate_epoch(sys.argv[1:])
