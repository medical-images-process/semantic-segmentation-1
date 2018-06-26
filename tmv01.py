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

from segmentation.datasets import Slides, ImageFolder, SemiSupervisedDataLoader
from segmentation.instances import DiscriminativeLoss, mean_shift, visualise_embeddings, visualise_instances
from segmentation.network import SemanticInstanceSegmentation
from segmentation.training import train

def validate_epoch(argv):
    print('Argument List:', argv)
    #[2] create model and clustening function
    model = SemanticInstanceSegmentation() #From network
    instance_clustering = DiscriminativeLoss() #From instances

    #[3] random transforms for pictures
    transform = transforms.Compose([ #torchvision
        transforms.RandomRotation(5),
        transforms.RandomCrop((256, 768)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.ToTensor()])

    target_transform = transforms.Compose([transform, transforms.Lambda(lambda x: (x * 255).long())])

    batch_size = 3

    # WARNING: Don't use multiple workers for loading! Doesn't work with setting random seed
    # Slides: copies the data if required into the data/raw/[images,
    # instances, labels] directories and returns
    # import pdb; pdb.set_trace()
    ##train_data_labelled = Slides(download=True, train=True, root='data', transform=transform, target_transform=target_transform)
    ##train_loader_labelled = torch.utils.data.DataLoader(train_data_labelled, batch_size=batch_size, drop_last=True, shuffle=True)
    ##train_data_unlabelled = ImageFolder(root='data/slides', transform=transform)
    ##train_loader_unlabelled = torch.utils.data.DataLoader(train_data_unlabelled, batch_size=batch_size, drop_last=True, shuffle=True)
    ##train_loader = SemiSupervisedDataLoader(train_loader_labelled, train_loader_unlabelled)

    test_data_labelled = Slides(download=True, train=False, root='data', transform=transform, target_transform=target_transform)
    test_loader_labelled = torch.utils.data.DataLoader(test_data_labelled, batch_size=batch_size, drop_last=True, shuffle=True)
    test_data_unlabelled = ImageFolder(root='data/slides', transform=transform)
    test_loader_unlabelled = torch.utils.data.DataLoader(test_data_unlabelled, batch_size=batch_size, drop_last=True, shuffle=True)
    test_loader = SemiSupervisedDataLoader(test_loader_labelled, test_loader_unlabelled)


    #[4] test model

    model.load_state_dict(torch.load('models/epoch_14'))
    model.eval()

    train_loader = torch.utils.data.DataLoader(test_data_labelled, batch_size=1, shuffle=True)

    image, labels, instances = next(iter(train_loader))

    image = Variable(image)
    instances = Variable(instances + 1)
    _, logits, instance_embeddings = model.forward_clean(image)

    current_logits = logits[0]
    current_labels = labels[0, 0]
    current_instances = instances[0]

    predicted_class = current_logits.data.max(0)[1]
    predicted_instances = [None] * 5
    for class_index in range(5):
        mask = predicted_class.view(-1) == class_index
        if mask.max() > 0:
            label_embedding = instance_embeddings[0].view(1, instance_embeddings.shape[1], -1)[..., mask]
            label_embedding = label_embedding.data.cpu().numpy()[0]

            predicted_instances[class_index] = mean_shift(label_embedding)


    plt.rcParams['image.cmap'] = 'Paired'

    fig, axes = plt.subplots(3, 2, figsize=(15, 10))
    for ax in axes.flatten(): ax.axis('off')

    axes[0, 0].set_title('Original image')
    axes[0, 0].imshow(image[0].data.numpy().transpose(1, 2, 0))
    axes[1, 0].set_title('Ground truth classes')
    axes[1, 0].imshow(current_labels.cpu().numpy().squeeze())
    axes[2, 0].set_title('Ground truth instances')
    axes[2, 0].imshow(current_instances.cpu().numpy().squeeze())
    axes[1, 1].set_title('Predicted classes')
    axes[1, 1].imshow(predicted_class.cpu().numpy().squeeze())
    instance_image = visualise_instances(predicted_instances, predicted_class, num_classes=5)
    axes[2, 1].set_title('Predicted instances')
    axes[2, 1].imshow(instance_image)
    plt.show()

if __name__ == "__main__":
   validate_epoch(sys.argv[1:])
