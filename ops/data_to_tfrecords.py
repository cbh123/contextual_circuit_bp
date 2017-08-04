import re
import os
import sys
import traceback
import shutil
import numpy as np
import tensorflow as tf
from scipy import misc
from glob import glob
from tqdm import tqdm
from skimage import transform


def load_image(f, im_size):
    image = misc.imread(f).astype(np.float32)
    it_im_size = image.shape
    if im_size != it_im_size:
        image = transform.resize(image, im_size[:2], preserve_range=True)
    if len(image.shape) < 3:
        image = np.repeat(image[:, :, None], im_size[-1], axis=-1)
    return image


def create_example(data_dict):
    return tf.train.Example(
        # Example contains a Features proto object
        features=tf.train.Features(
            # Features has a map of string to Feature proto objects
            feature=data_dict
        )
    )


def data_to_tfrecords(
        files,
        labels,
        targets,
        ds_name,
        im_size):
    image_count = 0
    print 'Building dataset: %s' % ds_name
    for idx, ((fk, fv), (lk, lv)) in enumerate(
        zip(
            files.iteritems(),
            labels.iteritems())):
        it_ds_name = '%s_%s.tfrecords' % (ds_name, fk)
        with tf.python_io.TFRecordWriter(it_ds_name) as tfrecord_writer:
            for it_f, it_l in tqdm(zip(fv, lv), total=len(fv), desc='Building %s' % fk): 
                image = load_image(it_f, im_size).astype(np.float32)
                data_dict = {
                    'image': targets['image'](image.tostring()),
                    'label': targets['label'](it_l)
                }
                example = create_example(data_dict)
                if example is not None:
                    # Keep track of how many images we use
                    image_count += 1
                    # use the proto object to serialize the example to a string
                    serialized = example.SerializeToString()
                    # write the serialized object to disk
                    tfrecord_writer.write(serialized)
                    example = None
        print 'Finished %s with %s images (dropped %s)' % (
            it_ds_name, image_count, len(fv) - image_count)
