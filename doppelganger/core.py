'''Copyright 2019-2020 Maxim Shpak <maxim.shpak@posteo.uk>

This file is part of Doppelgänger.

Doppelgänger is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Doppelgänger is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Doppelgänger. If not, see <https://www.gnu.org/licenses/>.


This file incorporates work covered by the following copyright and
permission notice:

    MIT License

    Copyright (c) 2019 Maxim Shpak <maxim.shpak@posteo.uk>

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files
    (the "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to permit
    persons to whom the Software is furnished to do so, subject to
    the following conditions:

        The above copyright notice and this permission notice shall be
        included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.

-------------------------------------------------------------------------------

This module provides core functions for processing images and find duplicates
'''

from __future__ import annotations

import os
import pickle
from functools import wraps
from multiprocessing import Pool
from pathlib import Path
from typing import (Any, Callable, Collection, Dict, Iterable, List, Optional,
                    Set, Tuple, TypeVar, Union)

import dhash
import pybktree
from PIL import Image as PILImage
from PIL import ImageFile

# Crazy hack not to get error 'IOError: image file is truncated...'
ImageFile.LOAD_TRUNCATED_IMAGES = True

def find_images(folders: Iterable[FolderPath],
                recursive: bool = True) -> Set[ImagePath]:
    '''Find all the images in :folders:

    :param folders: paths of the folders,
    :param recursive: recursive search (include subfolders),
    :return: full paths of the images,
    :raise FileNotFoundError: any of the folders does not exist
    '''

    paths = set()
    for path in folders:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f'{path} does not exist')
        paths.update(_search(p, recursive))
    return paths

def _search(path: Path, recursive: bool) -> Set[ImagePath]:
    paths = set()
    if recursive:
        patterns = ['**/*.png', '**/*.jpg', '**/*.jpeg', '**/*.bmp']
    else:
        patterns = ['*.png', '*.jpg', '*.jpeg', '*.bmp']

    for pattern in patterns:
        for filename in path.glob(pattern):
            if filename.is_file():
                paths.add(str(filename))
    return paths

def hamming(image1: HashedImage, image2: HashedImage) -> Distance:
    '''Calculate the Hamming distance between two images

    :param image1: the first image,
    :param image2: the second image,
    :return: Hamming distance
    '''

    return dhash.get_num_bits_different(image1.hash, image2.hash)

def image_grouping(images: Collection[HashedImage],
                   sensitivity: Sensitivity) -> List[Group]:
    '''Find similar images and group them

    :param images: images to process,
    :param sensitivity: maximal difference between hashes of 2 images
                        when they are considered similar,
    :return: groups of similar images. If there are no duplicate
             images, an empty list is returned,
    :raise TypeError: any of the hashes is not integer
    '''

    if len(images) <= 1:
        return []

    image_groups = []
    checked: Set[HashedImage] = set()
    try:
        bkt = pybktree.BKTree(hamming, images)
    except TypeError:
        raise TypeError('While grouping, image hashes must be integers')

    for image in images:
        if image in checked:
            continue

        closests = bkt.find(image, sensitivity)

        # If there's one element in 'closests', it's the 'image' itself
        if len(closests) == 1:
            continue

        image_groups.append(_new_group(closests, checked))

    #return [sorted(g, key=lambda x: x.difference) for g in image_groups]
    return image_groups

def _new_group(closests: List[Tuple[Distance, HashedImage]],
               checked: Set[HashedImage]) -> Group:
    image_group = []
    for dist, img in closests:
        if img not in checked:
            img.difference = dist
            image_group.append(img)
            checked.add(img)
    return image_group

def load_cache() -> Cache:
    '''Load the cache with earlier calculated hashes

    :return: dictionary with pairs 'image path: hash',
    :raise EOFError: the cache file cannot be read
    '''

    try:
        with open('image_hashes.p', 'rb') as f:
            cached_hashes = pickle.load(f)
    except FileNotFoundError:
        cached_hashes = {}
    except EOFError:
        raise EOFError('The cache file might be corrupted (or empty)')
    return cached_hashes

def check_cache(
        paths: Iterable[ImagePath],
        cached_hashes: Cache
    ) -> Tuple[List[HashedImage], List[NoneImage]]:
    '''Check which images are cached and which ones are not

    :param paths: full paths of images,
    :param cached_hashes: dictionary with pairs 'image path: hash',
    :return: return a tuple with 2 lists. The images that are found
             in the cache are in the 1st one, the images that are not
             found in the cache are in the 2nd one
    '''

    cached, not_cached = [], []
    for path in paths:
        if path in cached_hashes:
            cached.append(Image(path, dhash=cached_hashes[path]))
        else:
            not_cached.append(Image(path, dhash=None))
    return cached, not_cached

def hashes_calculating(images: Iterable[NoneImage]) -> List[HashedImage]:
    '''Calculate the hashes of :images:

    :param images: images which hashes are not calculated yet,
    :return: images with calculated hashes
    '''

    with Pool() as p:
        calculated_images = p.map(Image.dhash, images)
    return calculated_images

def caching(images: Iterable[HashedImage], cached_hashes: Cache) -> None:
    '''Add new hashes to the cache and save them on the disk

    :param images: images to process,
    :param cached_hashes: dictionary with pairs 'image path: hash'
    '''

    for image in images:
        img_hash = image.hash
        if img_hash is not None:
            cached_hashes[image.path] = img_hash

    with open('image_hashes.p', 'wb') as f:
        pickle.dump(cached_hashes, f)

def return_obj(func: Callable[[T], Any]) -> Callable[[T], T]:
    '''Decorator needed for parallel hashes calculating.
    Multiprocessing lib does not allow to change an object
    in place (because it's a different process). So it's
    passed to the process, changed in there and then
    must be returned

    :param func: function to use in 'multiprocessing.Pool.map',
                 eg. 'Image.dhash',
    :return: object on which :func: is called, eg. 'Image' object
    '''

    @wraps(func)
    def wrapper(obj):
        func(obj)
        return obj
    return wrapper


class Image():
    '''Class that represents images'''

    def __init__(self, path: ImagePath, dhash: Optional[Hash] = None,
                 difference: Distance = 0, thumbnail: Any = None) -> None:
        self.path = path
        # Difference between the image's hash and the 1st
        # image's hash in the group
        self.difference = difference
        self.hash = dhash
        self.thumbnail = thumbnail
        self.suffix: Suffix = Path(path).suffix # '.jpg', '.png', etc.
        self.size: FileSize = None
        self.width: Width = None
        self.height: Height = None

    @return_obj
    def dhash(self) -> Optional[Hash]:
        '''Calculate the perceptual hash of the image using 'dhash' library

        :return: the hash of the image or None if there's any problem
        '''

        try:
            image = PILImage.open(self.path)
        except OSError:
            self.hash = None
        #except UnboundLocalError as e:
            # Sometimes UnboundLocalError in PIL/JpegImagePlugin.py
            # happens with some images. Should be fixed in PIL 6.1.0.
            # Till then these images are not processed
            #print(e, self.path)
            #self.hash = None
        else:
            self.hash = dhash.dhash_int(image)
        return self.hash

    def dimensions(self) -> Tuple[Width, Height]:
        '''Return the dimensions of the image

        :return: tuple with the image's width and height,
        :raise OSError: any problem while opening the image
        '''

        if self.width is None or self.height is None:
            try:
                image = PILImage.open(self.path)
            except OSError:
                raise OSError(f'Cannot get the dimensions of {self.path}')
            else:
                self.width, self.height = image.size
        return self.width, self.height

    def filesize(self, size_format: SizeFormat = 1) -> FileSize:
        '''Return the file size of the image

        :param size_format: bytes - 0, KiloBytes - 1, MegaBytes - 2,
        :return: file size in bytes, kilobytes or megabytes, rounded
                 to the first decimal place,
        :raise OSError: any problem while opening the image,
        :raise ValueError: :size_format: is not amongst the allowed values
        '''

        if self.size is None:
            try:
                image_size = os.path.getsize(self.path)
            except OSError:
                raise OSError(f'Cannot get the file size of {self.path}')
            else:
                self.size = image_size

        if size_format == 0:
            return self.size
        if size_format == 1:
            return round(self.size / 1024, 1)
        if size_format == 2:
            return round(self.size / (1024**2), 1)

        raise ValueError('Wrong size format')

    def delete(self) -> None:
        '''Delete the image from the disk

        :raise OSError: the file does not exist, is a folder, is in use, etc.
        '''

        try:
            os.remove(self.path)
        except OSError:
            raise OSError(f'{self.path} cannot be removed')

    def move(self, dst: FolderPath) -> None:
        r'''Move the image to a new directory

        :param dst: new location, eg. '/new/location/' or 'C:\location',
        :raise OSError: the file does not exist, is a folder,
                        :dst: exists, etc.
        '''

        file_name = Path(self.path).name
        new_path = str(Path(dst) / file_name)

        try:
            os.rename(self.path, new_path)
        except OSError:
            raise OSError(f'{self.path} cannot be moved')

    def rename(self, name: str) -> None:
        '''Rename the image

        :param name: new name of the image,
        :raise FileExistsError: if a file with name :new_name:
                                already exists (on Unix replaces
                                the old file silently)
        '''

        path = Path(self.path)
        new_name = path.parent / name
        try:
            path.rename(new_name)
        except FileExistsError as e:
            raise FileExistsError(f"File with name '{name}' already exists")
        else:
            self.path = str(new_name)

    def del_parent_dir(self) -> None:
        '''Delete the parent directory if it is empty'''

        parent_dir = Path(self.path).parent
        if not list(parent_dir.glob('*')):
            parent_dir.rmdir()

    def __str__(self) -> str:
        return self.path


########################## Types ##################################

FolderPath = str # Path to a folder
ImagePath = str # Path to an image
Hash = int # Perceptual hash of an image
Distance = int # Distance between 2 hashes
Sensitivity = int # Max 'Distance' when images are considered similar
Suffix = str # '.jpg', '.png', etc. (with a dot)
Width = int # Width of a image
Height = int # Height of a image
FileSize = Union[int, float] # Size of a file
SizeFormat = int # Units of file size (one of {0, 1, 2})
NoneImage = Image # Image whose hash is None
HashedImage = Image # Image whose hash is not None
Cache = Dict[ImagePath, Hash] # Cache containing image hashes
Group = List[HashedImage] # Group of similar images

T = TypeVar('T')

###################################################################


if __name__ == '__main__':

    print('This is a demonstration of finding duplicate (similar) images')
    print('It might take some time, Be patient')
    print('------------------------')

    msg = "Type the folder's path you want to find duplicate images in\n"
    folders = input(msg)
    msg = ('Type the searching sensitivity (a value '
           'between 0 and 50 is recommended)\n')
    sensitivity = input(msg)
    print('------------------------')

    try:
        paths = find_images([folders])
    except ValueError as e:
        print(e)
    print(f'There are {len(paths)} images in the folder')

    try:
        cached_hashes = load_cache()
    except EOFError as e:
        print(e)
        print('Delete (back up if needed) the corrupted (or empty) ',
              'cache file and run the script again')

    cached, not_cached = check_cache(paths, cached_hashes)
    print(f'{len(paths)-len(not_cached)} images have been found in the cache')

    print('Starting to calculate hashes...')
    if not_cached:
        calculated = hashes_calculating(not_cached)
        calculated = [image for image in calculated if image.hash is not None]
        caching(calculated, cached_hashes)
        cached.extend(calculated)
    print('All the hashes have been calculated')

    print('Starting to compare images...')
    try:
        image_groups = image_grouping(cached, int(sensitivity))
    except TypeError as e:
        print(e)
    print(f'{len(image_groups)} duplicate image groups have been found')
    print('------------------------')

    for i, group in enumerate(image_groups):
        print(f'Group {i+1}:')
        print('------------------------')
        for image in group:
            print(image)
        print('------------------------')

    print('That is it')
    input('Press any key to continue...')
