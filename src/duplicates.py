'''Functions to process images and find duplicates'''

import os
import pickle
from collections import defaultdict

import imagehash
from PIL import Image as pilimage


def get_images_paths(folders):
    '''Return all the images' full paths from
    the passed 'folders' argument

    :param folders: a collection of folders' paths,
    :returns: list, images' full paths
    '''

    IMG_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp'}
    images_paths = []

    for path in folders:
        for dirpath, _, filenames in os.walk(path):
            for filename in filenames:
                full_path = os.path.join(path, dirpath, filename)
                if os.path.isfile(full_path):
                    _, extension = os.path.splitext(filename)
                    if extension in IMG_EXTENSIONS:
                        images_paths.append(full_path)
    return images_paths

def _closest_images_populating(closest_images, images, i, j):
    '''Populates :closest_images:

    :param closest_images: dict of :images:' indices,
                           eg. {0: 0, 1: 0, 5: 0}. The 1st
                           and 5th's closest image is 0th,
    :param images: collection of <class Image> objects,
    :param i: int, :images:' index,
    :param j: int, :images:' index
    '''

    # Do nothing if ith and jth images have been added already
    if i in closest_images and j in closest_images:
        return
    # ...if the ith's closest image was added already, then the closest
    # image of this already added (ith closest) image become the ith's
    # closest image. Eg. we have :closest_images: = {0: 0, 1: 0} and
    # the 5th's closest image is the 1st one; 1 is in :closest_images: and its
    # closest image is the 0th one, so 0 becomes the 5th's closest image and
    # now we have :closest_images: = {0: 0, 1: 0, 5: 0}...
    if j in closest_images:
        images[i].difference = images[i].hash - images[closest_images[j]].hash
        closest_images[i] = closest_images[j]
    # ...and vice versa
    elif i in closest_images:
        images[j].difference = images[j].hash - images[closest_images[i]].hash
        closest_images[j] = closest_images[i]
    else:
        # else we add a new pair of images and the ith image pointing
        # to itself. Eg. :closest_images: = {0: 0, 1: 0, 5: 0} and
        # the 7th's closest image is the 2nd, then now we have
        # :closest_images: = {0: 0, 1: 0, 5: 0, 2: 7, 7: 7}
        images[j].difference = images[j].hash - images[i].hash
        closest_images[j] = i
        closest_images[i] = i

def _closest_images_search(images):
    '''Search every image's closest one

    :param images: collection of <class Image> objects,
    :returns: dict of :images:' indices, eg. {0: 0, 1: 0, 5: 0}.
              The 1st and 5th's closest image is 0th
    '''

    SENSITIVITY = 10
    # Here all the hashes are compared to each other and the closest (most
    # similar image) are added to dict 'closest_images'.
    closest_images = {}
    for i, image1 in enumerate(images):
        closest_image = None
        min_diff = float('inf')
        for j, image2 in enumerate(images):
            diff = image1.hash - image2.hash
            # If the difference less/equal than SENSITIVITY and this
            # image (image2) is closer to image1 (diff is less),
            # we remember image2 index
            if diff <= SENSITIVITY and i != j and min_diff > diff:
                closest_image = j
                min_diff = diff
        # If ith image has the closest one...
        if closest_image is not None:
            _closest_images_populating(closest_images, images, i, closest_image)
    return closest_images

def images_grouping(images):
    '''Returns groups of similar images

    :param images: collection of <class Image> objects,
    :returns: list, [[<class Image> obj 1.1, <class Image> obj 1.2, ...],
                     [<class Image> obj 2.1, <class Image> obj 2.2, ...], ...],
                    each sublist of which is sorted by image difference in
                    ascending order
    '''

    closest_images = _closest_images_search(images)

    final_groups = defaultdict(list)
    for i in closest_images:
        final_groups[closest_images[i]].append(images[i])

    return [sorted(final_groups[g], key=lambda x: x.difference) for g in final_groups]

def _load_cached_hashes():
    '''Returns cached image hashes

    :returns: dict, {image_path: str, image_hash: <class ImageHash> obj}
    '''

    try:
        with open('image_hashes.p', 'rb') as f:
            cached_hashes = pickle.load(f)
    except FileNotFoundError:
        cached_hashes = {}
    return cached_hashes

def _save_cached_hashes(cached_hashes):
    '''Save cached image hashes on the disk

    :param cached_hashes: dict, {image_path: str,
                                 image_hash: <class ImageHash> obj}
    '''

    with open('image_hashes.p', 'wb') as f:
        pickle.dump(cached_hashes, f)

def hashes_calculating(paths):
    '''Return a list with <class Image> objects which are
    ready for comparing (with hashes calculated)

    :param paths: list, images' full paths,
    :returns: list, [<class Image> obj 1, <class Image> obj 2, ...]
    '''

    cached_hashes = _load_cached_hashes()

    image_objs = []
    for path in paths:
        image = Image(path)
        if image.path in cached_hashes:
            image.hash = cached_hashes[image.path]
        else:
            try:
                image.hash = image.calc_dhash()
            except IOError:
                continue
            cached_hashes[image.path] = image.hash
        image_objs.append(image)

    _save_cached_hashes(cached_hashes)

    return image_objs

def image_processing(folders):
    '''Process images to find the duplicates

    :param folders: collection of str, folders to process,
    :returns: list, [[<class Image> obj 1.1, <class Image> obj 1.2, ...],
                     [<class Image> obj 2.1, <class Image> obj 2.2, ...], ...]
    '''

    #paths = get_images_paths(folders)
    paths = get_images_paths([r'C:\Users\Remote\Downloads\new folder\iAHFY'])
    images = hashes_calculating(paths)
    return images_grouping(images)


class Image():
    '''Class that represents images'''

    def __init__(self, path, difference=0, dhash=None):
        self.path = path
        self.difference = difference
        self.hash = dhash

    def calc_dhash(self):
        '''Calculate an image's difference hash using
        'dhash' function from 'imagehash' lib

        :returns: <class ImageHash> instance,
        :raise OSError: if there's any problem with
                        opening or reading an image
        '''

        try:
            image = pilimage.open(self.path)
        except OSError as e:
            print(e)
            raise OSError(e)
        return imagehash.dhash(image)

    def get_dimensions(self):
        '''Return an image dimensions

        :param path: str, full path to an image,
        :returns: tuple, (width: int, height: int),
        :raise OSError: if there's any problem with
                        opening or reading an image
        '''

        try:
            image = pilimage.open(self.path)
        except OSError as e:
            print(e)
            raise OSError(e)
        return image.size

    def get_filesize(self, size_format='KB'):
        '''Return an image file size

        :param size_format: str, ('B', 'KB', 'MB'),
        :returns: float, file size in bytes, kilobytes or megabytes,
                  rounded to the first decimal place,
        :raise ValueError: if :size_format: not amongst
                           the allowed values,
        :raise OSError: if the file does not exist or is
                        inaccessible
        '''

        try:
            image_size = os.path.getsize(self.path)
        except OSError as e:
            print(e)
            raise OSError(e)

        if size_format == 'B':
            return image_size
        if size_format == 'KB':
            return round(image_size / 1024, 1)
        if size_format == 'MB':
            return round(image_size / (1024**2), 1)

        raise ValueError('Wrong size format')

    def delete_image(self):
        '''Delete an image from the disk

        :raise OSError: if the file does not exist,
                        is a folder, is in use, etc.
        '''

        try:
            os.remove(self.path)
        except OSError as e:
            print(e)
            raise OSError(e)
