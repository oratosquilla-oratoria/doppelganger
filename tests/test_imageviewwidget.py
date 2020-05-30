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
'''


import logging
from unittest import TestCase, mock

from PyQt5 import QtCore, QtGui, QtTest, QtWidgets

from doppelganger import core, signals
from doppelganger.gui import imageviewwidget
from doppelganger.resources import Image

# Configure a logger for testing purposes
logger = logging.getLogger('main')
logger.setLevel(logging.WARNING)
if not logger.handlers:
    nh = logging.NullHandler()
    logger.addHandler(nh)

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


VIEW = 'doppelganger.gui.imageviewwidget.'


# pylint: disable=unused-argument,missing-class-docstring


class TestInfoLabel(TestCase):

    def setUp(self):
        self.text = 'text'
        self.width = 200
        self.w = imageviewwidget.InfoLabel(self.text, self.width)


class TestInfoLabelMethodInit(TestInfoLabel):

    def test_init_values(self):
        self.assertEqual(self.w.widget_width, self.width)

    def test_alignment(self):
        self.assertEqual(self.w.alignment(), QtCore.Qt.AlignHCenter)

    def test_text_is_set(self):
        self.assertEqual(self.w.text(), self.text)


class TestInfoLabelMethodSetText(TestInfoLabel):

    def test_wordWrap_called(self):
        with mock.patch(VIEW+'InfoLabel._wordWrap') as mock_wrap_call:
            with mock.patch('PyQt5.QtWidgets.QLabel.setText'):
                self.w.setText(self.text)

        mock_wrap_call.assert_called_once_with(self.text)

    def test_parent_setText_called(self):
        wrapped = 'wrapped\ntext'
        with mock.patch(VIEW+'InfoLabel._wordWrap', return_value=wrapped):
            with mock.patch('PyQt5.QtWidgets.QLabel.setText') as mock_set_call:
                self.w.setText(self.text)

        mock_set_call.assert_called_once_with(wrapped)

    def test_updateGeometry_called(self):
        QLabel = 'PyQt5.QtWidgets.QLabel.'
        with mock.patch(QLabel+'setText'):
            with mock.patch(QLabel+'updateGeometry') as mock_upd_call:
                self.w.setText(self.text)

        mock_upd_call.assert_called_once_with()


class TestInfoLabelMethodWordWrap(TestInfoLabel):

    @mock.patch('PyQt5.QtCore.QSize.width', return_value=200)
    def test_word_wrap_more_than_one_line(self, mock_width):
        res = self.w._wordWrap('test')

        self.assertEqual(res, '\nt\ne\ns\nt')

    @mock.patch('PyQt5.QtCore.QSize.width', return_value=200 - 10)
    def test_word_wrap_one_line(self, mock_width):
        res = self.w._wordWrap('test')

        self.assertEqual(res, 'test')


class ImageSizeLabel(TestCase):

    @mock.patch(VIEW+'InfoLabel.__init__')
    def test_init(self, mock_init):
        w, h = 100, 200
        file_size = 222
        size_format = core.SizeFormat.MB
        widget_width = 55
        imageviewwidget.ImageSizeLabel(w, h, file_size, size_format,
                                       widget_width)

        mock_init.assert_called_once_with('100x200, 222 MB', 55, None)

class ImagePathLabel(TestCase):

    @mock.patch(VIEW+'InfoLabel.__init__')
    def test_init(self, mock_init):
        path = 'path'
        mock_qfile = mock.Mock()
        with mock.patch('PyQt5.QtCore.QFileInfo',
                        return_value=mock_qfile) as mock_q_file_call:
            imageviewwidget.ImagePathLabel(path, 200)

        mock_q_file_call.assert_called_once_with(path)
        mock_qfile.canonicalFilePath.assert_called_once_with()


class TestThumbnailWidget(TestCase):

    ThW = VIEW + 'ThumbnailWidget.'

    def setUp(self):
        self.mock_image = mock.Mock(autospec=core.Image)
        self.mock_image.thumb = None
        self.size = 333
        self.lazy = True

        with mock.patch(self.ThW+'_setEmptyPixmap'):
            with mock.patch(self.ThW+'_setSize'):
                self.w = imageviewwidget.ThumbnailWidget(self.mock_image,
                                                         self.size, self.lazy)


class TestThumbnailWidgetMethodInit(TestThumbnailWidget):

    def test_init_values(self):
        self.assertEqual(self.w.image, self.mock_image)
        self.assertEqual(self.w.size, self.size)
        self.assertEqual(self.w.lazy, self.lazy)
        self.assertTrue(self.w.empty, True)

    def test_size_policy(self):
        size_policy = self.w.sizePolicy()
        self.assertEqual(size_policy.horizontalPolicy(),
                         QtWidgets.QSizePolicy.Fixed)
        self.assertEqual(size_policy.verticalPolicy(),
                         QtWidgets.QSizePolicy.Fixed)

    def test_frame_style(self):
        self.assertEqual(self.w.frameStyle(), QtWidgets.QFrame.Box)

    def test_setEmptyPixmap_called(self):
        with mock.patch(self.ThW+'_setEmptyPixmap') as mock_empty_call:
            with mock.patch(self.ThW+'_setSize'):
                imageviewwidget.ThumbnailWidget(self.mock_image,
                                                self.size, self.lazy)

        mock_empty_call.assert_called_once_with()

    def test_setSize_called(self):
        with mock.patch(self.ThW+'_setSize') as mock_size_call:
            imageviewwidget.ThumbnailWidget(self.mock_image, self.size,
                                            True)

        mock_size_call.assert_called_once_with()

    def test_QTimer_made_if_lazy(self):
        with mock.patch(self.ThW+'_setEmptyPixmap'):
            with mock.patch(self.ThW+'_setSize'):
                w = imageviewwidget.ThumbnailWidget(self.mock_image,
                                                    self.size, True)

        self.assertIsInstance(w.qtimer, QtCore.QTimer)

    def test_makeThumbnail_called_if_not_lazy(self):
        with mock.patch(self.ThW+'_setEmptyPixmap'):
            with mock.patch(self.ThW+'_makeThumbnail') as mock_make_call:
                imageviewwidget.ThumbnailWidget(self.mock_image, self.size,
                                                False)

        mock_make_call.assert_called_once_with()


class TestThumbnailWidgetMethodSetSize(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.width, self.height = 1905, 1917
        self.mock_image.scaling_dimensions.return_value = (self.width,
                                                           self.height)

    def test_scaling_dimensions_called_with_attr_size(self):
        self.w._setSize()

        self.mock_image.scaling_dimensions.assert_called_once_with(self.size)

    def test_fixed_width_set(self):
        self.w._setSize()

        self.assertEqual(self.w.minimumWidth(), self.width)
        self.assertEqual(self.w.maximumWidth(), self.width)

    def test_fixed_height_set(self):
        self.w._setSize()

        self.assertEqual(self.w.minimumHeight(), self.height)
        self.assertEqual(self.w.maximumHeight(), self.height)

    def test_updateGeometry_called(self):
        with mock.patch(self.ThW+'updateGeometry') as mock_upd_call:
            self.w._setEmptyPixmap()

        mock_upd_call.assert_called_once_with()


class TestThumbnailWidgetMethodSetEmptyPixmap(TestThumbnailWidget):

    def test_null_QPixmap_made(self):
        with mock.patch('PyQt5.QtGui.QPixmap') as mock_QPixmap_call:
            with mock.patch(self.ThW+'setPixmap'):
                self.w._setEmptyPixmap()

        mock_QPixmap_call.assert_called_once_with()

    def test_setPixmap_called_with_QPixmap_result(self):
        mock_pixmap = mock.Mock(autospec=QtGui.QPixmap)
        with mock.patch('PyQt5.QtGui.QPixmap', return_value=mock_pixmap):
            with mock.patch(self.ThW+'setPixmap') as mock_setPixmap_call:
                self.w._setEmptyPixmap()

        mock_setPixmap_call.assert_called_once_with(mock_pixmap)

    def test_updateGeometry_called(self):
        with mock.patch('PyQt5.QtGui.QPixmap'):
            with mock.patch(self.ThW+'setPixmap'):
                with mock.patch(self.ThW+'updateGeometry') as mock_upd_call:
                    self.w._setEmptyPixmap()

        mock_upd_call.assert_called_once_with()

    def test_attr_empty_set_to_True(self):
        self.w.empty = False
        with mock.patch('PyQt5.QtGui.QPixmap'):
            with mock.patch(self.ThW+'setPixmap'):
                self.w._setEmptyPixmap()

        self.assertTrue(self.w.empty)


class TestThumbnailWidgetMethodSetThumbnail(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.mock_pixmap = mock.Mock(autospec=QtGui.QPixmap)
        self.w.pixmap = self.mock_pixmap

    def test_convertFromImage_called_with_image_thumb_arg_if_not_lazy(self):
        self.w.lazy = False
        self.mock_pixmap.convertFromImage.return_value = True
        with mock.patch(self.ThW+'setPixmap'):
            self.w._setThumbnail()

        self.mock_pixmap.convertFromImage.assert_called_once_with(
            self.w.image.thumb
        )

    def test_setPixmap_called_with_image_from_attr_thumb_if_not_lazy(self):
        self.w.lazy = False
        self.mock_pixmap.convertFromImage.return_value = True
        with mock.patch(self.ThW+'setPixmap') as mock_setPixmap_call:
            self.w._setThumbnail()

        mock_setPixmap_call.assert_called_once_with(self.mock_pixmap)

    def test_errorThumbnail_called_if_image_thumb_cant_be_read__not_lazy(self):
        self.w.lazy = False
        self.mock_pixmap.convertFromImage.return_value = False
        with mock.patch(self.ThW+'setPixmap'):
            with mock.patch(self.ThW+'_errorThumbnail') as mock_err_call:
                self.w._setThumbnail()

        mock_err_call.assert_called_once_with()

    def test_setPixmap_called__error_img_if_thumb_cant_be_read__not_lazy(self):
        self.w.lazy = False
        self.mock_pixmap.convertFromImage.return_value = False
        with mock.patch(self.ThW+'setPixmap') as mock_setPixmap_call:
            with mock.patch(self.ThW+'_errorThumbnail',
                            return_value='error_image'):
                self.w._setThumbnail()

        mock_setPixmap_call.assert_called_once_with('error_image')

    def test_updateGeometry_called_if_not_lazy(self):
        self.w.lazy = False
        self.mock_pixmap.convertFromImage.return_value = True
        with mock.patch(self.ThW+'setPixmap'):
            with mock.patch(self.ThW+'updateGeometry') as mock_upd_call:
                self.w._setThumbnail()

        mock_upd_call.assert_called_once_with()

    def test_empty_attr_set_to_False_if_not_lazy(self):
        self.w.lazy = False
        self.mock_pixmap.convertFromImage.return_value = True
        self.w.empty = True
        with mock.patch(self.ThW+'setPixmap'):
            self.w._setThumbnail()

        self.assertFalse(self.w.empty)

    def test_qtimer_start_not_called_if_not_lazy(self):
        self.w.lazy = False
        self.mock_pixmap.convertFromImage.return_value = True
        qtimer = mock.Mock()
        self.w.qtimer = qtimer
        with mock.patch(self.ThW+'setPixmap'):
            self.w._setThumbnail()

        qtimer.start.assert_not_called()

    def test_convertFromImage_called_with_img_thumb_if_lazy_and_visible(self):
        self.w.lazy = True
        self.mock_pixmap.convertFromImage.return_value = True
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'setPixmap'):
                self.w._setThumbnail()

        self.mock_pixmap.convertFromImage.assert_called_once_with(
            self.w.image.thumb
        )

    def test_setPixmap_called_with_img_read_from_thumb_if_lazy_and_vis(self):
        self.w.lazy = True
        self.mock_pixmap.convertFromImage.return_value = True
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'setPixmap') as mock_setPixmap_call:
                self.w._setThumbnail()

        mock_setPixmap_call.assert_called_once_with(self.mock_pixmap)

    def test_errorThumbnail_called_if_img_cant_be_read_if_lazy_and_vis(self):
        self.w.lazy = True
        self.mock_pixmap.convertFromImage.return_value = False
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'setPixmap'):
                with mock.patch(self.ThW+'_errorThumbnail') as mock_err_call:
                    self.w._setThumbnail()

        mock_err_call.assert_called_once_with()

    def test_setPixmap_called__err_img_if_thumb_cant_be_read__lazy__vis(self):
        self.w.lazy = True
        self.mock_pixmap.convertFromImage.return_value = False
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'setPixmap') as mock_setPixmap_call:
                with mock.patch(self.ThW+'_errorThumbnail',
                                return_value='error_image'):
                    self.w._setThumbnail()

        mock_setPixmap_call.assert_called_once_with('error_image')

    def test_updateGeometry_called_if_lazy_and_visible(self):
        self.w.lazy = True
        self.mock_pixmap.convertFromImage.return_value = True
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'setPixmap'):
                with mock.patch(self.ThW+'updateGeometry') as mock_upd_call:
                    self.w._setThumbnail()

        mock_upd_call.assert_called_once_with()

    def test_empty_attr_set_to_False_if_lazy_and_visible(self):
        self.w.lazy = True
        self.mock_pixmap.convertFromImage.return_value = True
        self.w.empty = True
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'setPixmap'):
                self.w._setThumbnail()

        self.assertFalse(self.w.empty)

    def test_qtimer_start_called_if_lazy_and_visible(self):
        self.w.lazy = True
        self.mock_pixmap.convertFromImage.return_value = True
        qtimer = mock.Mock()
        self.w.qtimer = qtimer
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'setPixmap'):
                self.w._setThumbnail()

        qtimer.start.assert_called_once_with(10000)

    def test_convertFromImage_not_called_if_lazy_and_not_visible(self):
        self.w.lazy = True
        with mock.patch(self.ThW+'isVisible', return_value=False):
            with mock.patch('PyQt5.QtGui.QPixmap',
                            return_value=self.mock_pixmap):
                self.w._setThumbnail()

        self.mock_pixmap.convertFromImage.assert_not_called()

    def test_setPixmap_not_called_if_lazy_and_not_visible(self):
        self.w.lazy = True
        with mock.patch(self.ThW+'isVisible', return_value=False):
            with mock.patch(self.ThW+'setPixmap') as mock_setPixmap_call:
                self.w._setThumbnail()

        mock_setPixmap_call.assert_not_called()

    def test_errorThumbnail_not_called_if_lazy_and_not_visible(self):
        self.w.lazy = True
        with mock.patch(self.ThW+'isVisible', return_value=False):
            with mock.patch(self.ThW+'_errorThumbnail') as mock_err_call:
                self.w._setThumbnail()

        mock_err_call.assert_not_called()

    def test_updateGeometry_not_called_if_lazy_and_not_visible(self):
        self.w.lazy = True
        with mock.patch(self.ThW+'isVisible', return_value=False):
            with mock.patch(self.ThW+'updateGeometry') as mock_upd_call:
                self.w._setThumbnail()

        mock_upd_call.assert_not_called()

    def test_empty_attr_stay_True_if_lazy_and_not_visible(self):
        self.w.lazy = True
        self.w.empty = True
        with mock.patch(self.ThW+'isVisible', return_value=False):
            self.w._setThumbnail()

        self.assertTrue(self.w.empty)

    def test_qtimer_start_not_called_if_lazy_and_not_visible(self):
        self.w.lazy = True
        qtimer = mock.Mock()
        self.w.qtimer = qtimer
        with mock.patch(self.ThW+'isVisible', return_value=False):
            self.w._setThumbnail()

        qtimer.start.assert_not_called()

    def test_assign_None_to_image_attr_thumb_if_lazy_and_not_visible(self):
        self.w.lazy = True
        with mock.patch(self.ThW+'isVisible', return_value=False):
            self.w._setThumbnail()

        self.assertIsNone(self.w.image.thumb)


class TestThumbnailWidgetMethodErrorThumbnail(TestThumbnailWidget):

    def test_logging(self):
        with self.assertLogs('main.widgets', 'ERROR'):
            self.w._errorThumbnail()

    def test_QPixmap_called_with_error_image_path(self):
        with mock.patch('PyQt5.QtGui.QPixmap') as mock_pixmap_call:
            self.w._errorThumbnail()

        mock_pixmap_call.assert_called_once_with(Image.ERR_IMG.abs_path) # pylint: disable=no-member

    def test_return_scaled_image_with_size_from_attr_size(self):
        mock_pixmap = mock.Mock()
        scaled_img = 'scaled_img'
        mock_pixmap.scaled.return_value = scaled_img
        with mock.patch('PyQt5.QtGui.QPixmap', return_value=mock_pixmap):
            res = self.w._errorThumbnail()

        mock_pixmap.scaled.assert_called_once_with(self.w.size, self.w.size)
        self.assertEqual(res, scaled_img)


class TestThumbnailWidgetMethodMakeThumbnail(TestThumbnailWidget):

    PROC = 'doppelganger.workers.'

    def test_args_ThumbnailProcessing_called_with_if_lazy(self):
        self.w.lazy = True
        with mock.patch(self.PROC+'ThumbnailProcessing') as mock_proc_call:
            with mock.patch('PyQt5.QtCore.QThreadPool.globalInstance'):
                self.w._makeThumbnail()

        mock_proc_call.assert_called_once_with(self.w.image, self.w.size,
                                               self.w)

    def test_args_ThumbnailProcessing_called_with_if_not_lazy(self):
        self.w.lazy = False
        with mock.patch(self.PROC+'ThumbnailProcessing') as mock_proc_call:
            with mock.patch('PyQt5.QtCore.QThreadPool.globalInstance'):
                self.w._makeThumbnail()

        mock_proc_call.assert_called_once_with(self.w.image, self.w.size)

    def test_worker_created(self):
        mock_processing_obj = mock.Mock()
        with mock.patch(self.PROC+'ThumbnailProcessing',
                        return_value=mock_processing_obj):
            with mock.patch('PyQt5.QtCore.QThreadPool.globalInstance'):
                with mock.patch(self.PROC+'Worker') as mock_worker_call:
                    self.w._makeThumbnail()

        mock_worker_call.assert_called_once_with(mock_processing_obj.run)

    def test_worker_pushed_to_thread(self):
        mock_threadpool = mock.Mock()
        mock_worker = mock.Mock()
        with mock.patch(self.PROC+'ThumbnailProcessing'):
            with mock.patch('PyQt5.QtCore.QThreadPool.globalInstance',
                            return_value=mock_threadpool):
                with mock.patch(self.PROC+'Worker', return_value=mock_worker):
                    self.w._makeThumbnail()

        mock_threadpool.start.assert_called_once_with(mock_worker)


class TestThumbnailWidgetMethodPaintEvent(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.mock_event = mock.Mock()
        self.w.qtimer = mock.Mock()

    def test_render_called_if_lazy_and_empty(self):
        self.w.lazy, self.w.empty = True, True
        with mock.patch('PyQt5.QtWidgets.QLabel.paintEvent'):
            with mock.patch(self.ThW+'_makeThumbnail') as mock_make_call:
                self.w.paintEvent(self.mock_event)

        mock_make_call.assert_called_once_with()

    def test_QLabel_paintEvent_called_if_lazy_and_empty(self):
        self.w.lazy, self.w.empty = True, True
        with mock.patch('PyQt5.QtWidgets.QLabel.paintEvent') as mock_ev_call:
            with mock.patch(self.ThW+'_makeThumbnail'):
                self.w.paintEvent(self.mock_event)

        mock_ev_call.assert_called_once_with(self.mock_event)

    def test_render_not_called_if_lazy_and_not_empty(self):
        self.w.lazy, self.w.empty = True, False
        with mock.patch('PyQt5.QtWidgets.QLabel.paintEvent'):
            with mock.patch(self.ThW+'_makeThumbnail') as mock_make_call:
                self.w.paintEvent(self.mock_event)

        mock_make_call.assert_not_called()

    def test_QLabel_paintEvent_called_if_lazy_and_not_empty(self):
        self.w.lazy, self.w.empty = True, False
        with mock.patch('PyQt5.QtWidgets.QLabel.paintEvent') as mock_ev_call:
            with mock.patch(self.ThW+'_makeThumbnail'):
                self.w.paintEvent(self.mock_event)

        mock_ev_call.assert_called_once_with(self.mock_event)

    def test_render_not_called_if_not_lazy(self):
        self.w.lazy = False
        with mock.patch('PyQt5.QtWidgets.QLabel.paintEvent'):
            with mock.patch(self.ThW+'_makeThumbnail') as mock_make_call:
                self.w.paintEvent(self.mock_event)

        mock_make_call.assert_not_called()

    def test_QLabel_paintEvent_called_if_not_lazy(self):
        self.w.lazy = False
        with mock.patch('PyQt5.QtWidgets.QLabel.paintEvent') as mock_ev_call:
            with mock.patch(self.ThW+'_makeThumbnail'):
                self.w.paintEvent(self.mock_event)

        mock_ev_call.assert_called_once_with(self.mock_event)


class TestThumbnailWidgetMethodClear(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.w.qtimer = mock.Mock()

    def test_qtimer_stop_not_called_if_empty(self):
        self.w.empty = True
        with mock.patch(self.ThW+'_setEmptyPixmap'):
            self.w._clear()

        self.w.qtimer.stop.assert_not_called()

    def test_setEmptyPixmap_not_called_if_empty(self):
        self.w.empty = True
        with mock.patch(self.ThW+'_setEmptyPixmap') as mock_set_call:
            self.w._clear()

        mock_set_call.assert_not_called()

    def test_attr_image_thumb_is_not_None_if_empty(self):
        self.w.empty = True
        self.w.image.thumb = 'thumb'
        with mock.patch(self.ThW+'_setEmptyPixmap'):
            self.w._clear()

        self.assertIsNotNone(self.w.image.thumb)

    def test_attr_empty_stay_True_if_empty(self):
        self.w.empty = True
        with mock.patch(self.ThW+'_setEmptyPixmap'):
            self.w._clear()

        self.assertTrue(self.w.empty)

    def test_qtimer_stop_not_called_if_not_empty_and_visible(self):
        self.w.empty = False
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'_setEmptyPixmap'):
                self.w._clear()

        self.w.qtimer.stop.assert_not_called()

    def test_setEmptyPixmap_not_called_if_not_empty_and_visible(self):
        self.w.empty = False
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'_setEmptyPixmap') as mock_set_call:
                self.w._clear()

        mock_set_call.assert_not_called()

    def test_attr_image_thumb_is_not_None_if_not_empty_and_visible(self):
        self.w.empty = False
        self.w.image.thumb = 'thumb'
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'_setEmptyPixmap'):
                self.w._clear()

        self.assertIsNotNone(self.w.image.thumb)

    def test_attr_empty_stay_False_if_not_empty_and_visible(self):
        self.w.empty = False
        with mock.patch(self.ThW+'isVisible', return_value=True):
            with mock.patch(self.ThW+'_setEmptyPixmap'):
                self.w._clear()

        self.assertFalse(self.w.empty)

    def test_setEmptyPixmap_called_if_not_empty_and_not_visible(self):
        self.w.empty = False
        with mock.patch(self.ThW+'isVisible', return_value=False):
            with mock.patch(self.ThW+'_setEmptyPixmap') as mock_set_call:
                self.w._clear()

        mock_set_call.assert_called_once_with()

    def test_attr_image_thumb_set_to_None_if_not_empty_and_not_visible(self):
        self.w.empty = False
        self.w.image.thumb = 'thumb'
        with mock.patch(self.ThW+'isVisible', return_value=False):
            with mock.patch(self.ThW+'_setEmptyPixmap'):
                self.w._clear()

        self.assertIsNone(self.w.image.thumb)

    def test_attr_empty_set_to_True_if_not_empty_and_not_visible(self):
        self.w.empty = False
        with mock.patch(self.ThW+'isVisible', return_value=False):
            with mock.patch(self.ThW+'_setEmptyPixmap'):
                self.w._clear()

        self.assertTrue(self.w.empty)


class TestThumbnailWidgetMethodMark(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.w.pixmap = mock.Mock()
        self.copy = mock.Mock()

    @mock.patch('PyQt5.QtGui.QBrush')
    @mock.patch('PyQt5.QtGui.QPainter')
    def test_setPixmap_called_with_darker_thumbnail(self, mock_paint, mock_br):
        self.w.pixmap.copy.return_value = self.copy
        with mock.patch(VIEW+'ThumbnailWidget.setPixmap') as mock_pixmap_call:
            self.w.mark()

        mock_pixmap_call.assert_called_once_with(self.copy)


class TestThumbnailWidgetMethodUnmark(TestThumbnailWidget):

    def setUp(self):
        super().setUp()

        self.w.pixmap = mock.Mock()

    def test_setPixmap_with_pixmap_attr_called(self):
        with mock.patch(VIEW+'ThumbnailWidget.setPixmap') as mock_pixmap_call:
            self.w.unmark()

        mock_pixmap_call.assert_called_once_with(self.w.pixmap)


class TestDuplicateWidget(TestCase):

    DW = VIEW + 'DuplicateWidget.'

    def setUp(self):
        self.conf = {'size': 200,
                     'size_format': 1,
                     'show_similarity': False,
                     'show_size': False,
                     'show_path': False}
        self.mock_image = mock.Mock()

        with mock.patch(self.DW+'_setThumbnailWidget'):
            self.w = imageviewwidget.DuplicateWidget(self.mock_image,
                                                     self.conf)


class TestDuplicateWidgetMethodInit(TestDuplicateWidget):

    def test_init_values(self):
        self.assertEqual(self.w.image, self.mock_image)
        self.assertEqual(self.w.conf, self.conf)
        self.assertFalse(self.w.selected)
        self.assertIsInstance(self.w.signals, signals.DuplicateWidgetSignals)

        self.assertEqual(self.w.minimumWidth(), self.conf['size'])
        self.assertEqual(self.w.maximumWidth(), self.conf['size'])

    def test_layout(self):
        margins = self.w.layout.contentsMargins()
        self.assertEqual(margins.top(), 0)
        self.assertEqual(margins.right(), 0)
        self.assertEqual(margins.bottom(), 0)
        self.assertEqual(margins.left(), 0)

        self.assertIsInstance(self.w.layout, QtWidgets.QVBoxLayout)
        self.assertEqual(self.w.layout.alignment(), QtCore.Qt.AlignTop)

    def test_setThumbnailWidget_called(self):
        with mock.patch(self.DW+'_setThumbnailWidget') as mock_widget_call:
            self.w = imageviewwidget.DuplicateWidget(self.mock_image,
                                                     self.conf)

        mock_widget_call.assert_called_once_with()

    def test_setSimilarityLabel_called_if_show_similarity_True(self):
        self.conf['show_similarity'] = True
        with mock.patch(self.DW+'_setThumbnailWidget'):
            with mock.patch(self.DW+'_setSimilarityLabel') as mock_label_call:
                self.w = imageviewwidget.DuplicateWidget(self.mock_image,
                                                         self.conf)

        mock_label_call.assert_called_once_with()

    def test_setImageSizeLabel_called_if_show_size_True(self):
        self.conf['show_size'] = True
        with mock.patch(self.DW+'_setThumbnailWidget'):
            with mock.patch(self.DW+'_setImageSizeLabel') as mock_label_call:
                self.w = imageviewwidget.DuplicateWidget(self.mock_image,
                                                         self.conf)

        mock_label_call.assert_called_once_with()

    def test_setImagePathLabel_called_if_show_path_True(self):
        self.conf['show_path'] = True
        with mock.patch(self.DW+'_setThumbnailWidget'):
            with mock.patch(self.DW+'_setImagePathLabel') as mock_label_call:
                self.w = imageviewwidget.DuplicateWidget(self.mock_image,
                                                         self.conf)

        mock_label_call.assert_called_once_with()


class TestMethodSetThumbnailWidget(TestDuplicateWidget):

    VBL = 'PyQt5.QtWidgets.QVBoxLayout.'
    ThW = VIEW + 'ThumbnailWidget'

    def setUp(self):
        super().setUp()

        self.conf['lazy'] = False
        self.w.layout = mock.Mock()

        self.imageLabel = 'ThumbnailWidget'

    def test_args_ThumbnailWidget_called_with(self):
        with mock.patch(self.ThW) as mock_widget_call:
            self.w._setThumbnailWidget()

        mock_widget_call.assert_called_once_with(self.mock_image,
                                                 self.conf['size'],
                                                 self.conf['lazy'])

    def test_addWidget_called_with_ThumbnailWidget_result(self):
        with mock.patch(self.ThW, return_value=self.imageLabel):
            self.w._setThumbnailWidget()

        self.w.layout.addWidget.assert_called_once_with(self.imageLabel)

    def test_horizontal_alignment(self):
        with mock.patch(self.ThW, return_value=self.imageLabel):
            self.w._setThumbnailWidget()

        self.w.layout.setAlignment.assert_called_once_with(
            self.imageLabel,
            QtCore.Qt.AlignHCenter
        )

    def test_return_ThumbnailWidget_result(self):
        with mock.patch(self.ThW, return_value=self.imageLabel):
            res = self.w._setThumbnailWidget()

        self.assertEqual(res, self.imageLabel)

    def test_updateGeometry_called(self):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(self.ThW):
            with mock.patch(updateGem) as mock_upd_call:
                self.w._setThumbnailWidget()

        mock_upd_call.assert_called_once_with()


class TestMethodSetSimilarityLabel(TestDuplicateWidget):

    ADD = 'PyQt5.QtWidgets.QVBoxLayout.addWidget'
    SL = VIEW + 'SimilarityLabel'

    def test_args_SimilarityLabel_called_with(self):
        self.mock_image.similarity.return_value = 13
        with mock.patch(self.SL) as mock_widget_call:
            with mock.patch(self.ADD):
                self.w._setSimilarityLabel()

        mock_widget_call.assert_called_once_with('13%', self.conf['size'])

    def test_addWidget_called_with_SimilarityLabel_result(self):
        SL_obj = 'label'
        with mock.patch(self.SL, return_value=SL_obj):
            with mock.patch(self.ADD) as mock_add_call:
                self.w._setSimilarityLabel()

        mock_add_call.assert_called_once_with(SL_obj)

    def test_return_SimilarityLabel_result(self):
        SL_obj = 'label'
        with mock.patch(self.SL, return_value=SL_obj):
            with mock.patch(self.ADD):
                res = self.w._setSimilarityLabel()

        self.assertEqual(res, SL_obj)

    def test_updateGeometry_called(self):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(self.SL):
            with mock.patch(self.ADD):
                with mock.patch(updateGem) as mock_upd_call:
                    self.w._setSimilarityLabel()

        mock_upd_call.assert_called_once_with()


class TestMethodSetImageSizeLabel(TestDuplicateWidget):

    ADD = 'PyQt5.QtWidgets.QVBoxLayout.addWidget'
    ISL = VIEW + 'ImageSizeLabel'

    def setUp(self):
        super().setUp()

        self.conf['size_format'] = 0 # Bytes

        type(self.mock_image).width = mock.PropertyMock(return_value=33)
        type(self.mock_image).height = mock.PropertyMock(return_value=55)

    def test_args_ImageSizeLabel_called_with(self):
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL) as mock_widget_call:
            with mock.patch(self.ADD):
                self.w._setImageSizeLabel()

        mock_widget_call.assert_called_once_with(33, 55, 5000,
                                                 core.SizeFormat.B, 200)

    def test_filesize_called_with_SizeFormat_B(self):
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL):
            with mock.patch(self.ADD):
                self.w._setImageSizeLabel()

        self.mock_image.filesize.assert_called_once_with(core.SizeFormat.B)

    def test_args_ImageSizeLabel_called_with_if_width_raise_OSError(self):
        type(self.mock_image).width = mock.PropertyMock(side_effect=OSError)
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL) as mock_widget_call:
            with mock.patch(self.ADD):
                self.w._setImageSizeLabel()

        mock_widget_call.assert_called_once_with(0, 0, 5000,
                                                 core.SizeFormat.B, 200)

    def test_logging_if_width_raise_OSError(self):
        type(self.mock_image).width = mock.PropertyMock(side_effect=OSError)
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL):
            with mock.patch(self.ADD):
                with self.assertLogs('main', 'ERROR'):
                    self.w._setImageSizeLabel()

    def test_args_ImageSizeLabel_called_with_if_height_raise_OSError(self):
        type(self.mock_image).height = mock.PropertyMock(side_effect=OSError)
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL) as mock_widget_call:
            with mock.patch(self.ADD):
                self.w._setImageSizeLabel()

        mock_widget_call.assert_called_once_with(0, 0, 5000,
                                                 core.SizeFormat.B, 200)

    def test_logging_if_height_raise_OSError(self):
        type(self.mock_image).height = mock.PropertyMock(side_effect=OSError)
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL):
            with mock.patch(self.ADD):
                with self.assertLogs('main', 'ERROR'):
                    self.w._setImageSizeLabel()

    def test_args_ImageSizeLabel_called_with_if_filesize_raise_OSError(self):
        self.mock_image.filesize.side_effect = OSError
        with mock.patch(self.ISL) as mock_widget_call:
            with mock.patch(self.ADD):
                self.w._setImageSizeLabel()

        mock_widget_call.assert_called_once_with(33, 55, 0,
                                                 core.SizeFormat.B, 200)

    def test_logging_if_filesize_raise_OSError(self):
        self.mock_image.filesize.side_effect = OSError
        with mock.patch(self.ISL):
            with mock.patch(self.ADD):
                with self.assertLogs('main', 'ERROR'):
                    self.w._setImageSizeLabel()

    def test_addWidget_called_with_ImageSizeLabel_result(self):
        ISL_obj = 'label'
        with mock.patch(self.ISL, return_value=ISL_obj):
            with mock.patch(self.ADD) as mock_add_call:
                self.w._setImageSizeLabel()

        mock_add_call.assert_called_once_with(ISL_obj)

    def test_return_ImageSizeLabel_result(self):
        ISL_obj = 'label'
        with mock.patch(self.ISL, return_value=ISL_obj):
            with mock.patch(self.ADD):
                res = self.w._setImageSizeLabel()

        self.assertEqual(res, ISL_obj)

    def test_updateGeometry_called(self):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(self.ISL):
            with mock.patch(self.ADD):
                with mock.patch(updateGem) as mock_upd_call:
                    self.w._setImageSizeLabel()

        mock_upd_call.assert_called_once_with()


class TestMethodSetImagePathLabel(TestDuplicateWidget):

    ADD = 'PyQt5.QtWidgets.QVBoxLayout.addWidget'
    IPL = VIEW + 'ImagePathLabel'

    def test_args_ImagePathLabel_called_with(self):
        self.mock_image.similarity.return_value = 13
        with mock.patch(self.IPL) as mock_widget_call:
            with mock.patch(self.ADD):
                self.w._setImagePathLabel()

        mock_widget_call.assert_called_once_with(self.mock_image.path,
                                                 self.conf['size'])

    def test_addWidget_called_with_ImagePathLabel_result(self):
        IPL_obj = 'label'
        with mock.patch(self.IPL, return_value=IPL_obj):
            with mock.patch(self.ADD) as mock_add_call:
                self.w._setImagePathLabel()

        mock_add_call.assert_called_once_with(IPL_obj)

    def test_return_ImagePathLabel_result(self):
        IPL_obj = 'label'
        with mock.patch(self.IPL, return_value=IPL_obj):
            with mock.patch(self.ADD):
                res = self.w._setImagePathLabel()

        self.assertEqual(res, IPL_obj)

    def test_updateGeometry_called(self):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(self.IPL):
            with mock.patch(self.ADD):
                with mock.patch(updateGem) as mock_upd_call:
                    self.w._setImagePathLabel()

        mock_upd_call.assert_called_once_with()


class TestDuplicateWidgetMethodOpenImage(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.mock_msg_box = mock.Mock()

    @mock.patch('sys.platform')
    def test_subprocess_run_called(self, mock_platform):
        with mock.patch('subprocess.run') as mock_run:
            self.w.openImage()

        mock_run.assert_called_once_with(['Unknown platform',
                                          self.mock_image.path],
                                         check=True)

    @mock.patch('sys.platform')
    def test_log_error_if_run_raise_exception(self, mock_platform):
        with mock.patch('subprocess.run', side_effect=FileNotFoundError):
            with mock.patch('PyQt5.QtWidgets.QMessageBox',
                            return_value=self.mock_msg_box):
                with self.assertLogs('main.widgets', 'ERROR'):
                    self.w.openImage()

    @mock.patch('sys.platform')
    def test_show_msg_box_if_run_raise_exception(self, mock_platform):
        with mock.patch('subprocess.run', side_effect=FileNotFoundError):
            with mock.patch('PyQt5.QtWidgets.QMessageBox',
                            return_value=self.mock_msg_box):
                self.w.openImage()

        self.mock_msg_box.exec.assert_called_once_with()


class TestDuplicateWidgetMethodRenameImage(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.INPUT = 'PyQt5.QtWidgets.QInputDialog.getText'
        self.mock_image.path = 'path'
        self.w.infoLabel = mock.Mock()

    def test_nothing_happens_if_QInputDialog_not_return_ok(self):
        with mock.patch(self.INPUT, return_value=('new_name', False)):
            self.w.renameImage()

        self.mock_image.rename.assert_not_called()

    def test_image_rename_called_with_new_name_arg(self):
        with mock.patch(self.INPUT, return_value=('new_name', True)):
            self.w.renameImage()

        self.mock_image.rename.assert_called_once_with('new_name')

    def test_ImagePathLabel_text_changed_if_image_name_is_changed(self):
        with mock.patch(self.INPUT, return_value=('new_name', True)):
            self.w.renameImage()

        label = self.w.infoLabel.imagePathLabel
        label.setText.assert_called_once_with(self.mock_image.path)

    def test_log_error_if_image_rename_raise_FileExistsError(self):
        self.mock_image.rename.side_effect = FileExistsError
        mock_msg_box = mock.Mock()
        with mock.patch(self.INPUT, return_value=('new_name', True)):
            with mock.patch('PyQt5.QtWidgets.QMessageBox',
                            return_value=mock_msg_box):
                with self.assertLogs('main.widgets', 'ERROR'):
                    self.w.renameImage()

    def test_show_msg_box_if_image_rename_raise_FileExistsError(self):
        self.mock_image.rename.side_effect = FileExistsError
        mock_msg_box = mock.Mock()
        with mock.patch(self.INPUT, return_value=('new_name', True)):
            with mock.patch('PyQt5.QtWidgets.QMessageBox',
                            return_value=mock_msg_box):
                self.w.renameImage()

        mock_msg_box.exec.assert_called_once_with()


class TestDuplicateWidgetMethodContextMenuEvent(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.mock_menu = mock.Mock()
        self.mock_event = mock.Mock()

    @mock.patch(VIEW+'DuplicateWidget.mapToGlobal')
    @mock.patch(VIEW+'DuplicateWidget.openImage')
    def test_openImage_called(self, mock_open, mock_map):
        openAction = 'open'
        self.mock_menu.addAction.side_effect = ['open', 'Rename']
        self.mock_menu.exec_.return_value = openAction
        with mock.patch('PyQt5.QtWidgets.QMenu', return_value=self.mock_menu):
            self.w.contextMenuEvent(self.mock_event)

        mock_open.assert_called_once_with()

    @mock.patch(VIEW+'DuplicateWidget.mapToGlobal')
    @mock.patch(VIEW+'DuplicateWidget.renameImage')
    def test_renameImage_called(self, mock_rename, mock_map):
        openAction = 'Rename'
        self.mock_menu.addAction.side_effect = ['open', 'Rename']
        self.mock_menu.exec_.return_value = openAction
        with mock.patch('PyQt5.QtWidgets.QMenu', return_value=self.mock_menu):
            self.w.contextMenuEvent(self.mock_event)

        mock_rename.assert_called_once_with()


class TestDuplicateWidgetMethodClick(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.imageLabel = mock.Mock()
        self.w.imageLabel = self.imageLabel

    def test_unselect_widget_if_selected(self):
        self.w.selected = True
        self.w.click()

        self.assertFalse(self.w.selected)

    def test_imageLabel_unmark_called_if_selected(self):
        self.w.selected = True
        self.w.click()

        self.imageLabel.unmark.assert_called_once_with()

    def test_select_widget_if_unselected(self):
        self.w.selected = False
        self.w.click()

        self.assertTrue(self.w.selected)

    def test_imageLabel_mark_called_if_unselected(self):
        self.w.selected = False
        self.w.click()

        self.imageLabel.mark.assert_called_once_with()

    def test_emit_signal_clicked(self):
        spy = QtTest.QSignalSpy(self.w.signals.clicked)
        self.w.click()

        self.assertEqual(len(spy), 1)


class TestDuplicateWidgetMethodMouseReleaseEvent(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.mock_event = mock.Mock()

    @mock.patch(VIEW+'DuplicateWidget.click')
    def test_click_called(self, mock_click):
        self.w.mouseReleaseEvent(self.mock_event)

        mock_click.assert_called_once_with()

    @mock.patch(VIEW+'DuplicateWidget.click')
    def test_event_ignored(self, mock_click):
        self.w.mouseReleaseEvent(self.mock_event)

        self.mock_event.ignore.assert_called_once_with()


class TestDuplicateWidgetMethodDelete(TestDuplicateWidget):

    def test_image_delete_called(self):
        self.w.delete()

        self.mock_image.delete.assert_called_once_with()

    def test_unselect_widget_if_image_delete_is_ok(self):
        self.w.delete()

        self.assertFalse(self.w.selected)

    @mock.patch(VIEW+'DuplicateWidget.hide')
    def test_widget_hide_called_if_image_delete_is_ok(self, mock_hide):
        self.w.delete()

        mock_hide.assert_called_once_with()

    def test_raise_OSError_if_image_delete_raise_OSError(self):
        self.mock_image.delete.side_effect = OSError
        with self.assertRaises(OSError):
            self.w.delete()


class TestDuplicateWidgetMethodMove(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.dst = 'new_folder'

    def test_image_move_called(self):
        self.w.move(self.dst)

        self.mock_image.move.assert_called_once_with(self.dst)

    def test_unselect_widget_if_image_move_is_ok(self):
        self.w.move(self.dst)

        self.assertFalse(self.w.selected)

    @mock.patch(VIEW+'DuplicateWidget.hide')
    def test_widget_hide_called_if_image_move_is_ok(self, mock_hide):
        self.w.move(self.dst)

        mock_hide.assert_called_once_with()

    def test_raise_OSError_if_image_move_raise_OSError(self):
        self.mock_image.move.side_effect = OSError
        with self.assertRaises(OSError):
            self.w.move(self.dst)


class TestImageGroupWidget(TestCase):

    IGW = VIEW + 'ImageGroupWidget'

    def setUp(self):
        self.conf = {}
        self.mock_image = mock.Mock()
        self.image_group = [self.mock_image]
        with mock.patch(self.IGW+'._setDuplicateWidgets'):
            self.w = imageviewwidget.ImageGroupWidget(self.image_group,
                                                      self.conf)


class TestImageGroupWidgetMethodInit(TestImageGroupWidget):

    def test_initial_value(self):
        self.assertDictEqual(self.w.conf, self.conf)
        self.assertListEqual(self.w.widgets, [])
        self.assertListEqual(self.w.image_group, self.image_group)

    def test_widget_layout(self):
        self.assertEqual(self.w.layout.spacing(), 10)
        self.assertIsInstance(self.w.layout, QtWidgets.QHBoxLayout)
        self.assertEqual(self.w.layout.alignment(),
                         QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

    def test_setDuplicateWidgets_called(self):
        with mock.patch(self.IGW+'._setDuplicateWidgets') as mock_dupl_call:
            imageviewwidget.ImageGroupWidget(self.image_group, self.conf)

        mock_dupl_call.assert_called_once_with()


class TestImageGroupWidgetMethodSetDuplicateWidgets(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.conf['lazy'] = True

        self.mock_dupl_w = mock.Mock()

    @mock.patch('PyQt5.QtWidgets.QHBoxLayout.addWidget')
    def test_args_DuplicateWidget_called_with(self, mock_add):
        with mock.patch(VIEW+'DuplicateWidget',
                        return_value=self.mock_dupl_w) as mock_widg_call:
            self.w._setDuplicateWidgets()

        mock_widg_call.assert_called_once_with(self.image_group[0],
                                               self.conf)

    @mock.patch('PyQt5.QtWidgets.QHBoxLayout.addWidget')
    def test_DuplicateWidget_added_to_widgets_attr(self, mock_add):
        with mock.patch(VIEW+'DuplicateWidget', return_value=self.mock_dupl_w):
            self.w._setDuplicateWidgets()

        self.assertListEqual(self.w.widgets, [self.mock_dupl_w])

    @mock.patch('PyQt5.QtWidgets.QHBoxLayout.addWidget')
    def test_DuplicateWidget_added_to_layout(self, mock_add):
        with mock.patch(VIEW+'DuplicateWidget', return_value=self.mock_dupl_w):
            self.w._setDuplicateWidgets()

        mock_add.assert_called_once_with(self.mock_dupl_w)

    @mock.patch('PyQt5.QtWidgets.QHBoxLayout.addWidget')
    def test_updateGeometry_called(self, mock_add):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(VIEW+'DuplicateWidget', return_value=self.mock_dupl_w):
            with mock.patch(updateGem) as mock_upd_call:
                self.w._setDuplicateWidgets()

        mock_upd_call.assert_called_once_with()


class TestImageGroupWidgetMethodSelectedWidgets(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.w.widgets = [mock.Mock()]

    def test_selected_widget_in_result_list(self):
        self.w.widgets[0].selected = True
        res = self.w.selectedWidgets()

        self.assertIn(self.w.widgets[0], res)
        self.assertEqual(len(res), 1)

    def test_not_selected_widgets_not_in_result_list(self):
        self.w.widgets[0].selected = False
        res = self.w.selectedWidgets()

        self.assertNotIn(self.w.widgets[0], res)
        self.assertEqual(len(res), 0)


class TestImageGroupWidgetMethodvisibleWidgets(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.w.widgets = [mock.Mock()]

    def test_isVisible_called(self):
        self.w.visibleWidgets()

        self.w.widgets[0].isVisible.assert_called_once_with()


class TestImageGroupWidgetMethodHasSelectedWidgets(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.mock_dupl_w = mock.Mock()
        self.w.widgets = [self.mock_dupl_w]

    def test_return_True_if_hasSelectedWidgets_return_True(self):
        self.mock_dupl_w.selected = True
        res = self.w.hasSelectedWidgets()

        self.assertTrue(res)

    def test_return_False_if_hasSelectedWidgets_not_return_True(self):
        self.mock_dupl_w.selected = False
        res = self.w.hasSelectedWidgets()

        self.assertFalse(res)


class TestImageGroupWidgetMethodAutoSelect(TestImageGroupWidget):

    def setUp(self):
        super().setUp()

        self.w.widgets = [mock.Mock(), mock.Mock()]

    def test_click_called_if_widget_is_not_selected(self):
        self.w.widgets[1].selected = False
        self.w.autoSelect()

        self.w.widgets[1].click.assert_called_once_with()

    def test_click_not_called_if_widget_selected(self):
        self.w.widgets[1].selected = True
        self.w.autoSelect()

        self.w.widgets[1].click.assert_not_called()


class TestImageViewWidget(TestCase):

    IVW = VIEW + 'ImageViewWidget.'

    def setUp(self):
        self.conf = {'delete_dirs': False}
        self.w = imageviewwidget.ImageViewWidget(self.conf)


class TestImageViewWidgetMethodInit(TestImageViewWidget):

    def test_conf_attr_initial_value(self):
        self.assertDictEqual(self.w.conf, self.conf)

    def test_widgets_attr_initial_value(self):
        self.assertListEqual(self.w.widgets, [])

    def test_signals_attr_set(self):
        self.assertIsInstance(self.w.signals, signals.WidgetsRenderingSignals)

    def test_interrupted_attr_initial_value(self):
        self.assertFalse(self.w.interrupted)

    def test_widget_layout(self):
        margins = self.w.contentsMargins()

        self.assertIsInstance(self.w.layout, QtWidgets.QVBoxLayout)
        self.assertEqual(margins.left(), 0)
        self.assertEqual(margins.top(), 0)
        self.assertEqual(margins.right(), 0)
        self.assertEqual(margins.bottom(), 0)
        self.assertEqual(self.w.layout.spacing(), 0)
        self.assertEqual(self.w.layout.alignment(),
                         QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)


class TestImageViewWidgetMethodRender(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.conf['lazy'] = True
        self.conf['sort'] = 0

        self.w.layout = mock.Mock()

        mock_image = mock.Mock(autospec=core.Image)
        self.image_groups = [[mock_image]]
        self.mock_group_w = mock.Mock()

    def test_args_ImageGroupWidget_called_with(self):
        with mock.patch(VIEW+'ImageGroupWidget',
                        return_value=self.mock_group_w) as mock_widg:
            self.w.render(self.image_groups)

        mock_widg.assert_called_once_with(self.image_groups[0], self.conf)

    def test_ImageGroupWidget_added_to_widgets_attr(self):
        with mock.patch(VIEW+'ImageGroupWidget',
                        return_value=self.mock_group_w):
            self.w.render(self.image_groups)

        self.assertListEqual(self.w.widgets, [self.mock_group_w])

    def test_ImageGroupWidget_added_to_layout(self):
        with mock.patch(VIEW+'ImageGroupWidget',
                        return_value=self.mock_group_w):
            self.w.render(self.image_groups)

        self.w.layout.addWidget.assert_called_once_with(self.mock_group_w)

    def test_updateGeometry_called(self):
        updateGem = 'PyQt5.QtWidgets.QWidget.updateGeometry'
        with mock.patch(VIEW+'ImageGroupWidget',
                        return_value=self.mock_group_w):
            with mock.patch(updateGem) as mock_upd_call:
                self.w.render(self.image_groups)

        mock_upd_call.assert_called_once_with()

    def test_updateProgressBar_called_with_proper_args(self):
        self.w.progressBarValue = 11
        with mock.patch(self.IVW+'_progressBarStep',
                        return_value=23) as mock_step_call:
            with mock.patch(self.IVW+'_updateProgressBar') as mock_upd_call:
                with mock.patch(VIEW+'ImageGroupWidget',
                                return_value=self.mock_group_w):
                    self.w.render(self.image_groups)

        mock_step_call.assert_called_once_with(len(self.image_groups))
        mock_upd_call.assert_called_once_with(11+23)

    def test_processEvents_called(self):
        proc_events = 'PyQt5.QtCore.QCoreApplication.processEvents'
        with mock.patch(VIEW+'ImageGroupWidget',
                        return_value=self.mock_group_w):
            with mock.patch(proc_events) as mock_proc_call:
                self.w.render(self.image_groups)

        mock_proc_call.assert_called_once_with()

    def test_finished_signal_emitted(self):
        proc_events = 'PyQt5.QtCore.QCoreApplication.processEvents'
        spy = QtTest.QSignalSpy(self.w.signals.finished)

        with mock.patch(VIEW+'ImageGroupWidget',
                        return_value=self.mock_group_w):
            with mock.patch(proc_events):
                self.w.render(self.image_groups)

        self.assertEqual(len(spy), 1)

    def test_nothing_called_if_attr_interrupted_True(self):
        self.w.interrupted = True
        proc_events = 'PyQt5.QtCore.QCoreApplication.processEvents'
        with mock.patch(VIEW+'ImageGroupWidget') as mock_igw_call:
            with mock.patch(proc_events) as mock_proc_call:
                self.w.render(self.image_groups)

        mock_igw_call.assert_not_called()
        self.w.layout.addWidget.assert_not_called()
        self.assertListEqual(self.w.widgets, [])
        mock_proc_call.assert_not_called()

    def test_interrupted_signal_emitted_if_attr_interrupted_True(self):
        self.w.interrupted = True
        spy = QtTest.QSignalSpy(self.w.signals.interrupted)

        self.w.render(self.image_groups)

        self.assertEqual(len(spy), 1)


class TestImageViewWidgetMethodUpdateProgressBar(TestImageViewWidget):

    def test_attr_progressBarValue_set_to_value_arg(self):
        self.w.progressBarValue = 33
        self.w._updateProgressBar(44)

        self.assertEqual(self.w.progressBarValue, 44)

    def test_signal_emitted(self):
        spy = QtTest.QSignalSpy(self.w.signals.update_progressbar)
        self.w._updateProgressBar(44)

        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0][0], 44)


class TestImageViewWidgetMethodProgressBarStep(TestImageViewWidget):

    def test_return_0_if_progressBarValue_100__denominator_1(self):
        self.w.progressBarValue = 100
        res = self.w._progressBarStep(1)

        self.assertAlmostEqual(res, 0)

    def test_return_100_if_progressBarValue_0__denominator_1(self):
        self.w.progressBarValue = 0
        res = self.w._progressBarStep(1)

        self.assertAlmostEqual(res, 100)

    def test_return_50_if_progressBarValue_50__denominator_1(self):
        self.w.progressBarValue = 50
        res = self.w._progressBarStep(1)

        self.assertAlmostEqual(res, 50)

class TestImageViewWidgetMethodHasSelectedWidgets(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_group_w = mock.Mock()
        self.w.widgets = [self.mock_group_w]

    def test_return_True_if_hasSelectedWidgets_return_True(self):
        self.mock_group_w.hasSelectedWidgets.return_value = True
        res = self.w.hasSelectedWidgets()

        self.assertTrue(res)

    def test_return_False_if_hasSelectedWidgets_not_return_True(self):
        self.mock_group_w.hasSelectedWidgets.return_value = False
        res = self.w.hasSelectedWidgets()

        self.assertFalse(res)


class TestImageViewWidgetMethodClear(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.conf['lazy'] = False

        self.mock_group_w = mock.Mock()
        self.w.widgets = [self.mock_group_w]
        self.w.widgets = [self.mock_group_w]

    def test_threadpool_clear_called(self):
        self.conf['lazy'] = True
        threadpool = mock.Mock()
        with mock.patch('PyQt5.QtCore.QThreadPool.globalInstance',
                        return_value=threadpool):
            self.w.clear()

        threadpool.clear.assert_called_once_with()

    def test_threadpool_waitForDone_called(self):
        self.conf['lazy'] = True
        threadpool = mock.Mock()
        with mock.patch('PyQt5.QtCore.QThreadPool.globalInstance',
                        return_value=threadpool):
            self.w.clear()

        threadpool.waitForDone.assert_called_once_with()

    def test_deleteLater_called(self):
        self.w.clear()

        self.mock_group_w.deleteLater.assert_called_once_with()

    def test_clear_widgets_attr(self):
        self.w.clear()

        self.assertListEqual(self.w.widgets, [])


class TestImageViewWidgetMethodDelete(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.CALL_ON = self.IVW + '_callOnSelectedWidgets'
        self.mock_msg_box = mock.Mock()

    def test_args_callOnSelectedWidgets_called_with(self):
        with mock.patch(self.CALL_ON) as mock_on:
            self.w.delete()

        mock_on.assert_called_once_with(imageviewwidget.DuplicateWidget.delete)

    @mock.patch('PyQt5.QtWidgets.QMessageBox')
    def test_log_error_if_callOnSelectedWidgets_raise_OSError(self, mock_box):
        with mock.patch(self.CALL_ON, side_effect=OSError):
            with self.assertLogs('main.widgets', 'ERROR'):
                self.w.delete()

    def test_show_msgbox_if_callOnSelectedWidgets_raise_OSError(self):
        with mock.patch(self.CALL_ON, side_effect=OSError):
            with mock.patch('PyQt5.QtWidgets.QMessageBox',
                            return_value=self.mock_msg_box):
                self.w.delete()

        self.mock_msg_box.exec.assert_called_once_with()


class TestImageViewWidgetMethodMove(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.dst = 'new_folder'

        self.CALL_ON = self.IVW + '_callOnSelectedWidgets'
        self.mock_msg_box = mock.Mock()

    def test_args_callOnSelectedWidgets_called_with(self):
        with mock.patch(self.CALL_ON) as mock_on:
            self.w.move(self.dst)

        mock_on.assert_called_once_with(imageviewwidget.DuplicateWidget.move,
                                        self.dst)

    @mock.patch('PyQt5.QtWidgets.QMessageBox')
    def test_log_error_if_callOnSelectedWidgets_raise_OSError(self, mock_box):
        with mock.patch(self.CALL_ON, side_effect=OSError):
            with self.assertLogs('main.widgets', 'ERROR'):
                self.w.move(self.dst)

    def test_show_msgbox_if_callOnSelectedWidgets_raise_OSError(self):
        with mock.patch(self.CALL_ON, side_effect=OSError):
            with mock.patch('PyQt5.QtWidgets.QMessageBox',
                            return_value=self.mock_msg_box):
                self.w.move(self.dst)

        self.mock_msg_box.exec.assert_called_once_with()


class TestImageViewWidgetMethodCallOnSelectedWidgets(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_func = mock.Mock()

        self.mock_group_w = mock.MagicMock()
        self.mock_group_w.__len__.return_value = 10
        self.mock_selected_w = mock.Mock()
        self.mock_group_w.selectedWidgets.return_value = [self.mock_selected_w]
        self.w.widgets.append(self.mock_group_w)

    def test_args_func_called_with(self):
        self.w._callOnSelectedWidgets(self.mock_func, 'arg', karg='karg')

        self.mock_func.assert_called_once_with(self.mock_selected_w,
                                               'arg', karg='karg')

    def test_raise_OSError_if_func_raise_OSError(self):
        self.mock_func.side_effect = OSError
        with self.assertRaises(OSError):
            self.w._callOnSelectedWidgets(self.mock_func)

    def test_call_del_parent_dir_if_conf_param_delete_dirs_is_True(self):
        self.conf['delete_dirs'] = True
        self.w._callOnSelectedWidgets(self.mock_func)

        self.mock_selected_w.image.del_parent_dir.assert_called_once_with()

    def test_hide_group_widget_if_less_than_2_visible(self):
        self.mock_group_w.visibleWidgets.return_value = ['widget']
        self.w._callOnSelectedWidgets(self.mock_func)

        self.mock_group_w.hide.assert_called_once_with()

    def test_not_hide_group_widget_if_more_than_2_visible(self):
        self.mock_group_w.visibleWidgets.return_value = ['widget1', 'widget2']
        self.w._callOnSelectedWidgets(self.mock_func)

        self.mock_group_w.hide.assert_not_called()


class TestImageViewWidgetMethodAutoSelect(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_img_grp = mock.Mock()
        self.w.widgets.append(self.mock_img_grp)

    def test_ImageGroupWidget_autoSelect_called(self):
        self.w.autoSelect()

        self.mock_img_grp.autoSelect.assert_called_once_with()


class TestImageViewWidgetMethodUnselect(TestImageViewWidget):

    def setUp(self):
        super().setUp()

        self.mock_img_grp = mock.Mock()
        self.mock_selected_w = mock.Mock()
        self.mock_img_grp.selectedWidgets.return_value = [self.mock_selected_w]
        self.w.widgets.append(self.mock_img_grp)

    def test_DuplicateWidget_click_called(self):
        self.w.unselect()

        self.mock_selected_w.click.assert_called_once_with()
