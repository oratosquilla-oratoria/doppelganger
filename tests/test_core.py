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

    Copyright (c) 2019-2020 Maxim Shpak <maxim.shpak@posteo.uk>

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
'''

from unittest import TestCase, mock

from doppelganger import core

CORE = 'doppelganger.core.'


# pylint: disable=unused-argument,missing-class-docstring


class TestFuncFindImage(TestCase):

    def setUp(self):
        self.mock_path = mock.Mock()

    def test_return_nothing_if_pass_empty_folders_list(self):
        paths = list(core.find_image([]))

        self.assertListEqual(paths, [])

    def test_raise_FileNotFoundError(self):
        self.mock_path.exists.return_value = False
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            with self.assertRaises(FileNotFoundError):
                res = list(core.find_image(['folder'])) #pylint: disable=unused-variable

    def test_glob_pattern_if_recursive_search(self):
        self.mock_path.exists.return_value = True
        self.mock_path.glob.return_value = []
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            res = list(core.find_image(['folder'], # pylint: disable=unused-variable
                                       recursive=True))

        self.mock_path.glob.assert_called_once_with('**/*')

    def test_glob_pattern_if_nonrecursive_search(self):
        self.mock_path.exists.return_value = True
        self.mock_path.glob.return_value = []
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            res = list(core.find_image(['folder'], # pylint: disable=unused-variable
                                       recursive=False))

        self.mock_path.glob.assert_called_once_with('*')

    def test_return_nothing_if_path_isnt_file(self):
        self.mock_path.exists.return_value = True
        image_path = mock.Mock()
        image_path.is_file.return_value = False
        self.mock_path.glob.return_value = [image_path]
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            res = list(core.find_image(['folder'], recursive=False))

        self.assertListEqual(res, [])

    def test_return_nothing_if_path_is_file_but_wrong_suffix(self):
        self.mock_path.exists.return_value = True
        image_path = mock.Mock()
        image_path.is_file.return_value = True
        image_path.suffix = '.www'
        self.mock_path.glob.return_value = [image_path]
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            res = list(core.find_image(['folder'], recursive=False))

        self.assertListEqual(res, [])

    def test_return_image_path(self):
        self.mock_path.exists.return_value = True
        image_path = mock.MagicMock()
        image_path.is_file.return_value = True
        image_path.suffix = '.png'
        image_path.__str__.return_value = 'image'
        self.mock_path.glob.return_value = [image_path]
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            res = list(core.find_image(['folder'], recursive=False))

        self.assertListEqual(res, ['image'])


class TestFuncImageGrouping(TestCase):

    def setUp(self):
        self.image1 = mock.Mock()
        self.image1.hash = 0
        self.image2 = mock.Mock
        self.image2.hash = 1
        self.images = [self.image1, self.image2]
        self.tree = 'bktree'

    def test_return_empty_list_if_no_images(self):
        res = list(core.image_grouping([], 0))

        self.assertListEqual(res[-1], [])

    def test_return_empty_list_if_one_image(self):
        with mock.patch('pybktree.BKTree'):
            with mock.patch(CORE+'_closest', return_value=(None, None)):
                res = list(core.image_grouping(['image'], 0))

        self.assertListEqual(res[-1], [])

    def test_BKTree_called_with_hamming_dist_and_images_args(self):
        with mock.patch('pybktree.BKTree') as mock_tree:
            with mock.patch(CORE+'_closest', return_value=(None, None)):
                list(core.image_grouping(self.images, 0))

        mock_tree.assert_called_once_with(core.hamming, self.images)

    def test_BKTree_raise_TypeError(self):
        with mock.patch('pybktree.BKTree', side_effect=TypeError):
            with self.assertRaises(TypeError):
                list(core.image_grouping(self.images, 0))

    def test_find_called_with_image_and_sensitivity_args(self):
        sens = 0
        with mock.patch('pybktree.BKTree', return_value=self.tree):
            with mock.patch(CORE+'_closest',
                            return_value=(None, None)) as mock_closest_call:
                list(core.image_grouping(self.images, sens))

        calls = [mock.call(self.tree, self.image1, sens),
                 mock.call(self.tree, self.image2, sens)]
        mock_closest_call.assert_has_calls(calls)

    @mock.patch(CORE+'_add_new_group')
    def test_loop_continue_if_there_is_no_closest_image(self, mock_group):
        with mock.patch('pybktree.BKTree', return_value=self.tree):
            with mock.patch(CORE+'_closest', return_value=(None, None)):
                list(core.image_grouping(self.images, 0))

        mock_group.assert_not_called()

    def test_return_if_image_and_closest_not_in_checked(self):
        closest1 = (17, mock.Mock())
        closest2 = (19, mock.Mock())
        with mock.patch('pybktree.BKTree', return_value=self.tree):
            with mock.patch(CORE+'_closest', side_effect=[closest1, closest2]):
                res = list(core.image_grouping(self.images, 0))

        self.assertListEqual(res[-1], [[self.image1, closest1[1]],
                                       [self.image2, closest2[1]]])

    def test_return_if_image_in_checked_and_closest_not_in_checked(self):
        closest1 = (17, self.image2)
        closest2 = (19, mock.Mock())
        closest2[1].hash = 2
        with mock.patch('pybktree.BKTree', return_value=self.tree):
            with mock.patch(CORE+'_closest', side_effect=[closest1, closest2]):
                res = list(core.image_grouping(self.images, 0))

        self.assertListEqual(res[-1], [[self.image1, self.image2,
                                        closest2[1]]])

    def test_return_if_image_not_in_checked_and_closest_in_checked(self):
        closest1 = (17, mock.Mock())
        closest2 = (19, self.image1)
        closest1[1].hash = 2
        with mock.patch('pybktree.BKTree', return_value=self.tree):
            with mock.patch(CORE+'_closest', side_effect=[closest1, closest2]):
                res = list(core.image_grouping(self.images, 0))

        self.assertListEqual(res[-1], [[self.image1, closest1[1],
                                        self.image2]])


class TestFuncClosest(TestCase):

    def setUp(self):
        self.mock_tree = mock.Mock()
        self.mock_image = mock.Mock()
        self.mock_tree.find.return_value = [(0, self.mock_image)]
        self.sensitivity = 0

    def test_pybktree_find_called_with_image_and_sensitivity_args(self):
        core._closest(self.mock_tree, self.mock_image, self.sensitivity)

        self.mock_tree.find.assert_called_once_with(self.mock_image,
                                                    self.sensitivity)

    def test_return_None_if_result_is_image_itself(self):
        res = core._closest(self.mock_tree, self.mock_image, self.sensitivity)

        self.assertTupleEqual(res, (None, None))

    def test_return_if_image_itself_is_first(self):
        close_img = mock.Mock()
        self.mock_tree.find.return_value = [(0, self.mock_image),
                                            (0, close_img)]
        res = core._closest(self.mock_tree, self.mock_image, self.sensitivity)

        self.assertTupleEqual(res, (0, close_img))

    def test_return_if_image_itself_is_second(self):
        close_img = mock.Mock()
        self.mock_tree.find.return_value = [(0, close_img),
                                            (0, self.mock_image)]
        res = core._closest(self.mock_tree, self.mock_image, self.sensitivity)

        self.assertTupleEqual(res, (0, close_img))


class TestFuncAddImgToExistingGroup(TestCase):

    def setUp(self):
        self.mock_image = mock.Mock()
        self.mock_image.hash = 235
        self.checked = {self.mock_image: 0}
        self.image_groups = [[self.mock_image]]

        self.mock_img_not_in = mock.Mock()
        self.mock_img_not_in.hash = 487

    @mock.patch(CORE+'hamming')
    def test_image_added_to_proper_group(self, mock_hamming):
        core._add_img_to_existing_group(self.mock_image, self.mock_img_not_in,
                                        self.checked, self.image_groups)

        self.assertListEqual(self.image_groups, [[self.mock_image,
                                                  self.mock_img_not_in]])

    @mock.patch(CORE+'hamming', return_value=999)
    def test_assign_distance_to_image_difference_attr(self, mock_hamming):
        core._add_img_to_existing_group(self.mock_image, self.mock_img_not_in,
                                        self.checked, self.image_groups)

        self.assertEqual(self.mock_img_not_in.difference, 999)

    @mock.patch(CORE+'hamming')
    def test_checked_dict_changed_properly(self, mock_hamming):
        core._add_img_to_existing_group(self.mock_image, self.mock_img_not_in,
                                        self.checked, self.image_groups)

        self.assertDictEqual(self.checked, {self.mock_image: 0,
                                            self.mock_img_not_in: 0})


class TestFuncAddNewGroup(TestCase):

    def setUp(self):
        self.mock_main_image = mock.Mock()
        self.mock_closest_img = mock.Mock()
        self.checked = {}
        self.image_groups = []
        self.distance = 888

    def test_images_added_to_proper_group(self):
        core._add_new_group(self.mock_main_image, self.mock_closest_img,
                            self.checked, self.image_groups, self.distance)

        self.assertListEqual(self.image_groups, [[self.mock_main_image,
                                                  self.mock_closest_img]])

    def test_assign_distance_to_image_difference_attr(self):
        core._add_new_group(self.mock_main_image, self.mock_closest_img,
                            self.checked, self.image_groups, self.distance)

        self.assertEqual(self.mock_closest_img.difference, self.distance)

    def test_checked_dict_changed_properly(self):
        core._add_new_group(self.mock_main_image, self.mock_closest_img,
                            self.checked, self.image_groups, self.distance)

        self.assertDictEqual(self.checked, {self.mock_main_image: 0,
                                            self.mock_closest_img: 0})


class TestFuncLoadCache(TestCase):

    CACHE_FILE = 'cache_file'

    @mock.patch('pickle.load')
    def test_load_from_cache_p(self, mock_load):
        with mock.patch('builtins.open', mock.mock_open()) as mock_open:
            core.load_cache(self.CACHE_FILE)

        mock_open.assert_called_once_with(self.CACHE_FILE, 'rb')

    @mock.patch('pickle.load', return_value='hashes')
    def test_return_loaded_hashes(self, mock_load):
        with mock.patch('builtins.open', mock.mock_open()):
            res = core.load_cache(self.CACHE_FILE)

        self.assertEqual(res, 'hashes')

    @mock.patch('builtins.open', side_effect=FileNotFoundError)
    def test_return_empty_dict_if_FileNotFoundError(self, mock_open):
        res = core.load_cache(self.CACHE_FILE)

        self.assertDictEqual(res, {})

    @mock.patch('builtins.open', side_effect=EOFError)
    def test_raise_EOFError_if_open_raise_EOFError(self, mock_open):
        with self.assertRaises(EOFError):
            core.load_cache(self.CACHE_FILE)

    @mock.patch('builtins.open', side_effect=OSError)
    def test_raise_OSError_if_open_raise_OSError(self, mock_open):
        with self.assertRaises(OSError):
            core.load_cache(self.CACHE_FILE)


class TestFuncCheckCache(TestCase):

    def setUp(self):
        self.cache = {'path2': 'hash'}

    def test_return_empty_lists_if_pass_empty_paths(self):
        paths = []
        not_cached = core.check_cache(paths, self.cache)

        self.assertListEqual(not_cached, [])

    def test_return_if_path_is_not_cached(self):
        paths = ['path1']
        not_cached = core.check_cache(paths, self.cache)

        self.assertEqual(len(not_cached), 1)
        self.assertEqual(not_cached[0], 'path1')

    def test_return_if_path_is_cached(self):
        paths = ['path2']
        not_cached = core.check_cache(paths, self.cache)

        self.assertListEqual(not_cached, [])


class TestFuncExtendCache(TestCase):

    def setUp(self):
        self.cache = {'path1': 'hash1'}

    def test_return_same_cache_if_pass_empty_paths_arg(self):
        expected = self.cache.copy()
        res = core.extend_cache(self.cache, [], [])

        self.assertDictEqual(res, expected)

    def test_new_hash_added_to_cache_if_hash_is_not_None(self):
        path, dhash = 'path2', 'hash2'
        expected = self.cache.copy()
        expected.update({path: dhash})
        res = core.extend_cache(self.cache, [path], [dhash])

        self.assertDictEqual(res, expected)

    def test_new_hash_not_added_to_cache_if_hash_is_None(self):
        path, dhash = 'path2', None
        expected = self.cache.copy()
        res = core.extend_cache(self.cache, [path], [dhash])

        self.assertDictEqual(res, expected)


class TestFuncSaveCache(TestCase):
    '''!!! BE AWARE WHEN CHANGE THESE TESTS. IF THERE'S
    ALREADY POPULATED CACHE FILE AND YOU DON'T PATCH OPEN()
    AND DUMP(), YOU'LL REWRITE THE FILE
    '''

    CACHE_FILE = 'cache_file'

    def setUp(self):
        self.cache = {'path1': 'hash1'}

    @mock.patch('pickle.dump')
    def test_load_from_cache_p(self, mock_dump):
        with mock.patch('builtins.open', mock.mock_open()) as mock_open:
            core.save_cache(self.CACHE_FILE, self.cache)

        mock_open.assert_called_once_with(self.CACHE_FILE, 'wb')

    @mock.patch('pickle.dump')
    def test_dump_called_with_cache_arg(self, mock_dump):
        with mock.patch('builtins.open', mock.mock_open()):
            core.save_cache(self.CACHE_FILE, self.cache)

        self.assertEqual(mock_dump.call_args[0][0], self.cache)

    @mock.patch('builtins.open', side_effect=OSError)
    def test_raise_OSError_if_open_raise_OSError(self, mock_open):
        with self.assertRaises(OSError):
            core.save_cache(self.CACHE_FILE, self.cache)


class TestFuncCalculateHashes(TestCase):

    def setUp(self):
        self.mock_Pool = mock.MagicMock()
        self.mock_context_obj = mock.Mock()
        self.mock_Pool.__enter__.return_value = self.mock_context_obj

    def test_args_imap_called_with(self):
        paths = ['path']
        self.mock_context_obj.imap.return_value = (h for h in ['hash'])

        with mock.patch(CORE+'Pool', return_value=self.mock_Pool):
            list(core.calculate_hashes(paths))

        self.mock_context_obj.imap.assert_called_once_with(core.Image.dhash,
                                                           paths)

    def test_imap_result(self):
        paths = ['path1', 'path2']
        hashes = ['hash1', 'hash2']
        self.mock_context_obj.imap.return_value = (h for h in hashes)

        with mock.patch(CORE+'Pool', return_value=self.mock_Pool):
            res = list(core.calculate_hashes(paths))

        self.assertListEqual(res, hashes)


class TestClassImage(TestCase):

    def setUp(self):
        self.image = core.Image('image.png', dhash='hash')


class TestMethodDhash(TestClassImage):

    def setUp(self):
        self.mock_image = mock.Mock()

    def test_return_if_open_raise_OSError(self):
        with mock.patch(CORE+'PILImage.open', side_effect=OSError):
            dhash = core.Image.dhash('image')

        self.assertIsNone(dhash)

    @mock.patch('dhash.dhash_int')
    def test_dhash_int_called_with_pil_open_return(self, mock_hash):
        with mock.patch(CORE+'PILImage.open', return_value=self.mock_image):
            core.Image.dhash('image')

        mock_hash.assert_called_once_with(self.mock_image)

    @mock.patch('dhash.dhash_int')
    def test_image_closed(self, mock_hash):
        with mock.patch(CORE+'PILImage.open', return_value=self.mock_image):
            core.Image.dhash('image')

        self.mock_image.close.assert_called_once_with()

    @mock.patch('dhash.dhash_int', return_value='hash')
    def test_dhash_return_hash(self, mock_hash):
        with mock.patch(CORE+'PILImage.open'):
            dhash = core.Image.dhash('image')

        self.assertEqual(dhash, 'hash')


class TestMethodDimensions(TestClassImage):

    def setUp(self):
        super().setUp()

        self.width = 333
        self.height = 444
        self.mock_img = mock.Mock()
        self.mock_img.size = (self.width, self.height)

    def test_pil_open_called_with_image_path(self):
        with mock.patch(CORE + 'PILImage.open',
                        return_value=self.mock_img) as mock_pil:
            self.image._set_dimensions()

        mock_pil.assert_called_once_with(self.image.path)

    def test_raise_OSError_if_pil_open_raise_OSError(self):
        with mock.patch(CORE + 'PILImage.open', side_effect=OSError):
            with self.assertRaises(OSError):
                self.image._set_dimensions()

    def test_dims_assigned_to_image_attrs(self):
        with mock.patch(CORE + 'PILImage.open', return_value=self.mock_img):
            self.image._set_dimensions()

        self.assertEqual(self.image._width, self.width)
        self.assertEqual(self.image._height, self.height)

    def test_close_called_on_opened_image(self):
        with mock.patch(CORE + 'PILImage.open', return_value=self.mock_img):
            self.image._set_dimensions()

        self.mock_img.close.assert_called_once_with()


class TestPropertyWidth(TestClassImage):

    def test_dimensions_called_if_width_is_None(self):
        self.image._width = None
        with mock.patch(CORE + 'Image._set_dimensions') as mock_dim:
            self.image.width # pylint: disable=pointless-statement

        mock_dim.assert_called_once_with()

    def test_return_width_attr(self):
        w = 34
        self.image._width = w
        res = self.image.width

        self.assertEqual(res, w)


class TestPropertyHeight(TestClassImage):

    def test_dimensions_called_if_height_is_None(self):
        self.image._height = None
        with mock.patch(CORE + 'Image._set_dimensions') as mock_dim:
            self.image.height # pylint: disable=pointless-statement

        mock_dim.assert_called_once_with()

    def test_return_height_attr(self):
        h = 34
        self.image._height = h
        res = self.image.height

        self.assertEqual(res, h)


class TestMethodSetFilesize(TestClassImage):

    @mock.patch('os.path.getsize', return_value=1024)
    def test_getsize_called_with_image_path_arg(self, mock_size):
        self.image.filesize()

        mock_size.assert_called_once_with(self.image.path)

    @mock.patch('os.path.getsize', side_effect=OSError)
    def test_raise_OSError_if_getsize_raise_OSError(self, mock_size):
        with self.assertRaises(OSError):
            self.image.filesize()

    @mock.patch('os.path.getsize', return_value=1024)
    def test_assign_result_of_getsize_to_size_attr(self, mock_size):
        self.image.filesize(core.SizeFormat.B)

        self.assertEqual(self.image.size, 1024)


class TestMethodFilesize(TestClassImage):

    def h_set_filesize(self):
        self.image.size = 1

    def test_return_image_size_attr_if_Bytes_format(self):
        self.image.size = 1024
        filesize = self.image.filesize(size_format=core.SizeFormat.B)

        self.assertAlmostEqual(filesize, self.image.size)

    def test_return_image_size_attr_if_KiloBytes_format(self):
        self.image.size = 1024
        filesize = self.image.filesize(size_format=core.SizeFormat.KB)

        self.assertAlmostEqual(filesize, 1)

    def test_return_image_size_attr_if_MegaBytes_format(self):
        self.image.size = 1024**2
        filesize = self.image.filesize(size_format=core.SizeFormat.MB)

        self.assertAlmostEqual(filesize, 1)

    def test_set_filesize_called_if_size_attr_is_None(self):
        self.image.size = None
        with mock.patch(CORE + 'Image._set_filesize',
                        side_effect=self.h_set_filesize) as mock_size_call:
            self.image.filesize(size_format=core.SizeFormat.B)

        mock_size_call.assert_called_once_with()

    def test_set_filesize_not_called_if_size_attr_is_not_None(self):
        self.image.size = 1024
        with mock.patch(CORE + 'Image._set_filesize') as mock_size_call:
            self.image.filesize(size_format=core.SizeFormat.B)

        mock_size_call.assert_not_called()


class TestMethodDelete(TestClassImage):

    @mock.patch('os.remove', side_effect=OSError)
    def test_raise_OSError_if_remove_raise_OSError(self, mock_remove):
        with self.assertRaises(OSError):
            self.image.delete()

    @mock.patch('os.remove')
    def test_remove_called_with_image_path_arg(self, mock_remove):
        self.image.delete()

        mock_remove.assert_called_once_with(self.image.path)

    # func 'move'

    @mock.patch('os.rename', side_effect=OSError)
    def test_raise_OSError_if_move_raise_OSError(self, mock_move):
        with self.assertRaises(OSError):
            self.image.move('new_dst')

    @mock.patch('os.rename')
    def test_what_args_is_Path_called_with(self, mock_move):
        new_dst = 'new_dst'
        mock_path = mock.MagicMock()
        calls = [mock.call(self.image.path), mock.call(new_dst)]
        with mock.patch(CORE+'Path', return_value=mock_path) as patch:
            self.image.move(new_dst)

        patch.assert_has_calls(calls)

    @mock.patch('os.rename')
    def test_move_called_with_image_path_and_new_path_args(self, mock_move):
        dst = 'new_dst'
        new_path = dst + '/' + self.image.path
        mock_path = mock.MagicMock()
        mock_path.__truediv__.return_value = new_path
        with mock.patch(CORE+'Path', return_value=mock_path):
            self.image.move(dst)

        mock_move.assert_called_once_with(self.image.path, new_path)


class TestMethodRename(TestClassImage):

    def setUp(self):
        super().setUp()

        self.new_name = 'new_name.png'
        self.mock_path = mock.MagicMock()
        self.mock_path.parent.__truediv__.return_value = self.new_name

    def test_rename_called_with_new_name_arg(self):
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            self.image.rename(self.new_name)

        self.mock_path.rename.assert_called_once_with(self.new_name)

    def test_new_name_assigned_to_image_path_attr(self):
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            self.image.rename(self.new_name)

        self.assertEqual(self.image.path, self.new_name)

    def test_raise_FileExistsError_if_rename_raise_FileExistsError(self):
        self.mock_path.rename.side_effect = FileExistsError
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            with self.assertRaises(FileExistsError):
                self.image.rename(self.new_name)


class TestMethodDelParentDir(TestClassImage):

    def setUp(self):
        super().setUp()

        self.mock_path = mock.Mock()
        self.mock_path.parent.glob.return_value = []

    def test_Path_called_with_image_path_arg(self):
        with mock.patch(CORE+'Path', return_value=self.mock_path) as patch:
            self.image.del_parent_dir()

        patch.assert_called_once_with(self.image.path)

    def test_glob_search_all_files(self):
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            self.image.del_parent_dir()

        self.mock_path.parent.glob.assert_called_once_with('*')

    def test_rmdir_not_called_if_dir_is_not_empty(self):
        self.mock_path.parent.glob.return_value = ['file']
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            self.image.del_parent_dir()

        self.mock_path.parent.rmdir.assert_not_called()

    def test_rmdir_called_if_dir_is_empty(self):
        with mock.patch(CORE+'Path', return_value=self.mock_path):
            self.image.del_parent_dir()

        self.mock_path.parent.rmdir.assert_called_once_with()


class TestSort(TestCase):

    def setUp(self):
        self.img1 = core.Image('test3', 'hash1')
        self.img1.difference = 5
        self.img1.size = 3072
        self.img1._width = 4
        self.img1._height = 6
        self.img2 = core.Image('test1', 'hash2')
        self.img2.difference = 0
        self.img2.size = 1024
        self.img2._width = 1
        self.img2._height = 1
        self.img3 = core.Image('test2', 'hash3')
        self.img3.difference = 3
        self.img3.size = 2048
        self.img3._width = 5
        self.img3._height = 3
        self.img_groups = [[self.img1, self.img2, self.img3]]

    def test_similarity_sort(self):
        s = core.Sort(self.img_groups)
        s.sort(0)

        self.assertListEqual(self.img_groups[0],
                             [self.img2, self.img3, self.img1])

    def test_size_sort(self):
        '''Image.filesize returns values in KB by default.
        So do not use small numbers or you might get incorrect
        sort results
        '''

        s = core.Sort(self.img_groups)
        s.sort(1)

        self.assertListEqual(self.img_groups[0],
                             [self.img1, self.img3, self.img2])

    def test_dimensions_sort(self):
        s = core.Sort(self.img_groups)
        s.sort(2)

        self.assertListEqual(self.img_groups[0],
                             [self.img1, self.img3, self.img2])

    def test_path_sort(self):
        s = core.Sort(self.img_groups)
        s.sort(3)

        self.assertListEqual(self.img_groups[0],
                             [self.img2, self.img3, self.img1])
