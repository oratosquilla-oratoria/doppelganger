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

from unittest import TestCase, mock

from PyQt5 import QtCore, QtTest, QtWidgets

from doppelganger import signals
from doppelganger.gui import aboutwindow, mainwindow, preferenceswindow

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])


MAIN_WINDOW = 'doppelganger.gui.mainwindow.'
IMAGE_VIEW_WIDGET = 'doppelganger.gui.imageviewwidget.'
PROC_GRP_BOX = 'doppelganger.gui.processinggroupbox.'


# pylint: disable=unused-argument,missing-class-docstring


class TestMainForm(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.w = mainwindow.MainWindow()


class TestMainFormMethodInit(TestMainForm):

    def test_init_values(self):
        self.assertIsInstance(self.w.aboutWindow, aboutwindow.AboutWindow)
        self.assertIsInstance(self.w.preferencesWindow,
                              preferenceswindow.PreferencesWindow)
        self.assertIsInstance(self.w.signals, signals.Signals)
        self.assertIsInstance(self.w.threadpool, QtCore.QThreadPool)

        self.assertIsInstance(self.w.interruptionMsg, QtWidgets.QMessageBox)
        self.assertEqual(self.w.interruptionMsg.standardButtons(),
                         QtWidgets.QMessageBox.NoButton)

        self.assertFalse(self.w.interrupted)
        self.assertFalse(self.w.processing_run)


class TestMainFormMethodSwitchDelFolderAction(TestMainForm):

    PATCH_SELECETED = 'PyQt5.QtWidgets.QListWidget.selectedItems'

    def test_delFolderAction_enabled_if_there_are_selected_paths(self):
        self.w.delFolderAction.setEnabled(False)
        with mock.patch(self.PATCH_SELECETED, return_value=True):
            self.w.switchDelFolderAction()

        self.assertTrue(self.w.delFolderAction.isEnabled())

    def test_delFolderAction_disabled_if_there_arent_selected_paths(self):
        self.w.delFolderAction.setEnabled(True)
        with mock.patch(self.PATCH_SELECETED, return_value=False):
            self.w.switchDelFolderAction()

        self.assertFalse(self.w.delFolderAction.isEnabled())


class TestMainFormMethodSwitchStartBtn(TestMainForm):

    PATCH_COUNT = 'PyQt5.QtWidgets.QListWidget.count'

    def test_startBtn_enabled_if_there_are_paths_and_not_processing_run(self):
        self.w.processingGrp.startBtn.setEnabled(False)
        self.w.processing_run = False
        with mock.patch(self.PATCH_COUNT, return_value=1):
            self.w.switchStartBtn()

        self.assertTrue(self.w.processingGrp.startBtn.isEnabled())

    def test_startBtn_disabled_if_there_are_paths_and_processing_run(self):
        self.w.processingGrp.startBtn.setEnabled(False)
        self.w.processing_run = True
        with mock.patch(self.PATCH_COUNT, return_value=1):
            self.w.switchStartBtn()

        self.assertFalse(self.w.processingGrp.startBtn.isEnabled())

    def test_startBtnn_disabled_if_there_are_no_paths(self):
        self.w.processingGrp.startBtn.setEnabled(True)
        with mock.patch(self.PATCH_COUNT, return_value=0):
            self.w.switchStartBtn()

        self.assertFalse(self.w.processingGrp.startBtn.isEnabled())


class TestMainFormMethodSetImageProcessingObj(TestMainForm):

    PATCH_IMG_PROC = 'doppelganger.processing.ImageProcessing'

    def setUp(self):
        super().setUp()

        self.mock_proc_obj = mock.Mock()

    def test_args_ImageProcessing_called_with(self):
        with mock.patch(self.PATCH_IMG_PROC,
                        return_value=self.mock_proc_obj) as mock_proc_call:
            self.w._setImageProcessingObj()

        mock_proc_call.assert_called_once_with(
            self.w.signals,
            self.w.pathsGrp.paths(),
            self.w.sensitivityGrp.sensitivity,
            self.w.preferencesWindow.conf
        )

    def test_return_ImageProcessing_obj(self):
        with mock.patch(self.PATCH_IMG_PROC, return_value=self.mock_proc_obj):
            res = self.w._setImageProcessingObj()

        self.assertEqual(res, self.mock_proc_obj)


class TestMainFormMethodStartProcessing(TestMainForm):

    @mock.patch('PyQt5.QtCore.QThreadPool.start')
    def test_attr_processing_run_set_to_True(self, mock_pool):
        self.w.processing_run = False
        self.w.startProcessing()

        self.assertTrue(self.w.processing_run)

    @mock.patch('PyQt5.QtCore.QThreadPool.start')
    def test_ImageViewWidget_clear_called(self, mock_pool):
        PATCH_CLEAR = IMAGE_VIEW_WIDGET + 'ImageViewWidget.clear'
        with mock.patch(PATCH_CLEAR) as mock_clear:
            self.w.startProcessing()

        mock_clear.assert_called_once_with()

    @mock.patch('PyQt5.QtCore.QThreadPool.start')
    def test_autoSelectBtn_disabled(self, mock_pool):
        self.w.actionsGrp.autoSelectBtn.setEnabled(True)
        self.w.startProcessing()

        self.assertFalse(self.w.actionsGrp.autoSelectBtn.isEnabled())

    @mock.patch('PyQt5.QtCore.QThreadPool.start')
    def test_autoSelectAction_disabled(self, mock_pool):
        self.w.autoSelectAction.setEnabled(True)
        self.w.startProcessing()

        self.assertFalse(self.w.autoSelectAction.isEnabled())

    @mock.patch('PyQt5.QtCore.QThreadPool.start')
    def test_processinggroupbox_startProcessing_called(self, mock_pool):
        PATCH_STARTPROC = PROC_GRP_BOX + 'ProcessingGroupBox.startProcessing'
        with mock.patch(PATCH_STARTPROC) as mock_start_call:
            self.w.startProcessing()

        mock_start_call.assert_called_once_with()


class TestMainFormMethodStopProcessing(TestMainForm):

    def setUp(self):
        super().setUp()

        self.w.interruptionMsg = mock.Mock()

    def test_interrupted_signal_emitted(self):
        spy = QtTest.QSignalSpy(self.w.signals.interrupted)
        self.w.stopProcessing()

        self.assertEqual(len(spy), 1)

    def test_change_iterrupted_attr_to_True(self):
        self.w.stopProcessing()

        self.assertTrue(self.w.interrupted)

    def test_show_msg_bos(self):
        self.w.stopProcessing()

        self.w.interruptionMsg.exec.assert_called_once_with()


class TestMainFormMethodCloseEvent(TestMainForm):

    def setUp(self):
        super().setUp()

        self.mock_event = mock.Mock()

    def test_stopProcessing_not_called_if_no_confirmation_and_no_stopBtn(self):
        self.w.preferencesWindow.conf['close_confirmation'] = False
        self.w.processing_run = False
        with mock.patch(MAIN_WINDOW+'MainWindow.stopProcessing') as mock_stop:
            self.w.closeEvent(self.mock_event)

        mock_stop.assert_not_called()

    def test_stopProcessing_called_if_no_confirmation_and_stopBtn(self):
        self.w.preferencesWindow.conf['close_confirmation'] = False
        self.w.processing_run = True
        with mock.patch(MAIN_WINDOW+'MainWindow.stopProcessing') as mock_stop:
            self.w.closeEvent(self.mock_event)

        mock_stop.assert_called_once_with()

    def test_stopProcessing_not_called_if_Yes_confirmation_no_stopBtn(self):
        self.w.preferencesWindow.conf['close_confirmation'] = True
        self.w.processing_run = False
        with mock.patch(MAIN_WINDOW+'MainWindow.stopProcessing') as mock_stop:
            with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                            return_value=QtWidgets.QMessageBox.Yes):
                self.w.closeEvent(self.mock_event)

        mock_stop.assert_not_called()

    def test_stopProcessing_called_if_Yes_confirmation_and_stopBtn(self):
        self.w.preferencesWindow.conf['close_confirmation'] = True
        self.w.processing_run = True
        with mock.patch(MAIN_WINDOW+'MainWindow.stopProcessing') as mock_stop:
            with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                            return_value=QtWidgets.QMessageBox.Yes):
                self.w.closeEvent(self.mock_event)

        mock_stop.assert_called_once_with()

    def test_stopProcessing_not_called_if_confirmation_Cancel(self):
        self.w.preferencesWindow.conf['close_confirmation'] = True
        with mock.patch(MAIN_WINDOW+'MainWindow.stopProcessing') as mock_stop:
            with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                            return_value=QtWidgets.QMessageBox.Cancel):
                self.w.closeEvent(self.mock_event)

        mock_stop.assert_not_called()

    def test_event_ignored_if_confirmation_Cancel(self):
        self.w.preferencesWindow.conf['close_confirmation'] = True
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Cancel):
            self.w.closeEvent(self.mock_event)

        self.mock_event.ignore.assert_called_once_with()

    def test_imageviewwidget_attr_interrupted_set_to_True(self):
        self.w.preferencesWindow.conf['close_confirmation'] = False
        self.w.imageViewWidget.interrupted = False

        self.w.closeEvent(self.mock_event)

        self.assertTrue(self.w.imageViewWidget.interrupted)

    def test_threadpool_cleared(self):
        self.w.preferencesWindow.conf['close_confirmation'] = False
        self.w.imageViewWidget.interrupted = False
        mock_pool = mock.Mock()

        with mock.patch('PyQt5.QtCore.QThreadPool.globalInstance',
                        return_value=mock_pool):
            self.w.closeEvent(self.mock_event)

        mock_pool.clear.assert_called_once_with()
        mock_pool.waitForDone.assert_called_once_with()


class TestMainFormMethodOpenWindow(TestMainForm):

    PATCH_SENDER = MAIN_WINDOW + 'MainWindow.sender'

    def setUp(self):
        super().setUp()

        self.mock_sender = mock.Mock()
        self.mock_window = mock.Mock()
        self.mock_sender.data.return_value = self.mock_window

    def test_activate_window_if_it_is_open(self):
        self.mock_window.isVisible.return_value = True
        with mock.patch(self.PATCH_SENDER, return_value=self.mock_sender):
            self.w.openWindow()

        self.mock_window.activateWindow.assert_called_once_with()

    def test_show_window_if_it_is_not_open(self):
        self.mock_window.isVisible.return_value = False
        with mock.patch(self.PATCH_SENDER, return_value=self.mock_sender):
            self.w.openWindow()

        self.mock_window.show.assert_called_once_with()


class TestMainFormMethodOpenDocs(TestMainForm):

    def test_webbrowser_open_called(self):
        URL = 'https://github.com/oratosquilla-oratoria/doppelganger'
        with mock.patch('webbrowser.open') as mock_open_call:
            self.w.openDocs()

        mock_open_call.assert_called_once_with(URL)


class TestMainFormMethodSwitchImgActionsAndBtns(TestMainForm):

    PATCH_SELECTED = IMAGE_VIEW_WIDGET + 'ImageViewWidget.hasSelectedWidgets'
    PATCH_ENABLED = ('doppelganger.gui.actionsgroupbox.'
                     'ActionsGroupBox.setEnabled')

    def test_actions_btns_enabled_if_there_are_selected_widgets(self):
        with mock.patch(self.PATCH_SELECTED, return_value=True):
            with mock.patch(self.PATCH_ENABLED) as mock_set_call:
                self.w.switchImgActionsAndBtns()

        mock_set_call.assert_called_once_with(True)

    def test_move_menu_action_enabled_if_there_are_selected_widgets(self):
        self.w.moveAction.setEnabled(False)
        with mock.patch(self.PATCH_SELECTED, return_value=True):
            self.w.switchImgActionsAndBtns()

        self.assertTrue(self.w.moveAction.isEnabled())

    def test_delete_menu_action_enabled_if_there_are_selected_widgets(self):
        self.w.deleteAction.setEnabled(False)
        with mock.patch(self.PATCH_SELECTED, return_value=True):
            self.w.switchImgActionsAndBtns()

        self.assertTrue(self.w.deleteAction.isEnabled())

    def test_unselect_menu_action_enabled_if_there_are_selected_widgets(self):
        self.w.unselectAction.setEnabled(False)
        with mock.patch(self.PATCH_SELECTED, return_value=True):
            self.w.switchImgActionsAndBtns()

        self.assertTrue(self.w.unselectAction.isEnabled())

    def test_actions_btns_disabled_if_no_selected_widgets(self):
        with mock.patch(self.PATCH_SELECTED, return_value=False):
            with mock.patch(self.PATCH_ENABLED) as mock_set_call:
                self.w.switchImgActionsAndBtns()

        mock_set_call.assert_called_once_with(False)

    def test_move_menu_action_disabled_if_no_selected_widgets(self):
        self.w.moveAction.setEnabled(True)
        with mock.patch(self.PATCH_SELECTED, return_value=False):
            self.w.switchImgActionsAndBtns()

        self.assertFalse(self.w.moveAction.isEnabled())

    def test_delete_menu_action_disabled_if_no_selected_widgets(self):
        self.w.deleteAction.setEnabled(True)
        with mock.patch(self.PATCH_SELECTED, return_value=False):
            self.w.switchImgActionsAndBtns()

        self.assertFalse(self.w.deleteAction.isEnabled())

    def test_unselect_menu_action_disabled_if_no_selected_widgets(self):
        self.w.unselectAction.setEnabled(True)
        with mock.patch(self.PATCH_SELECTED, return_value=False):
            self.w.switchImgActionsAndBtns()

        self.assertFalse(self.w.unselectAction.isEnabled())


class TestMainFormMethodDeleteImages(TestMainForm):

    @mock.patch(MAIN_WINDOW+'MainWindow.switchImgActionsAndBtns')
    @mock.patch(IMAGE_VIEW_WIDGET+'ImageViewWidget.delete')
    def test_nothing_happens_if_btn_Cancel_chosen(self, mock_del, mock_switch):
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Cancel):
            self.w.deleteImages()

        mock_del.assert_not_called()
        mock_switch.assert_not_called()

    @mock.patch(MAIN_WINDOW+'MainWindow.switchImgActionsAndBtns')
    @mock.patch(IMAGE_VIEW_WIDGET+'ImageViewWidget.delete')
    def test_delete_called_if_btn_Yes_chosen(self, mock_del, mock_switch):
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Yes):
            self.w.deleteImages()

        mock_del.assert_called_once_with()

    @mock.patch(MAIN_WINDOW+'MainWindow.switchImgActionsAndBtns')
    @mock.patch(IMAGE_VIEW_WIDGET+'ImageViewWidget.delete')
    def test_switchImgActionsAndBtns_called_if_btn_Yes_chosen(self, mock_del,
                                                              mock_switch):
        with mock.patch('PyQt5.QtWidgets.QMessageBox.question',
                        return_value=QtWidgets.QMessageBox.Yes):
            self.w.deleteImages()

        mock_switch.assert_called_once_with()


class TestMainFormMethodMoveImages(TestMainForm):

    def setUp(self):
        super().setUp()

        self.new_dst = 'new_folder'

    @mock.patch(MAIN_WINDOW+'MainWindow.switchImgActionsAndBtns')
    @mock.patch(IMAGE_VIEW_WIDGET+'ImageViewWidget.move')
    def test_nothing_happens_if_path_not_chosen(self, mock_move, mock_switch):
        with mock.patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory',
                        return_value=''):
            self.w.moveImages()

        mock_move.assert_not_called()
        mock_switch.assert_not_called()

    @mock.patch(MAIN_WINDOW+'MainWindow.switchImgActionsAndBtns')
    @mock.patch(IMAGE_VIEW_WIDGET+'ImageViewWidget.move')
    def test_delete_called_if_path_chosen(self, mock_move, mock_switch):
        with mock.patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory',
                        return_value=self.new_dst):
            self.w.moveImages()

        mock_move.assert_called_once_with(self.new_dst)

    @mock.patch(MAIN_WINDOW+'MainWindow.switchImgActionsAndBtns')
    @mock.patch(IMAGE_VIEW_WIDGET+'ImageViewWidget.move')
    def test_switchImgActionsAndBtns_called_if_path_chosen(self, mock_move,
                                                           mock_switch):
        with mock.patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory',
                        return_value=self.new_dst):
            self.w.moveImages()

        mock_switch.assert_called_once_with()


class TestMainFormMethodRender(TestMainForm):

    def test_ImageViewWidget_called_if_duplicates_found(self):
        PATCH_RENDER = IMAGE_VIEW_WIDGET + 'ImageViewWidget.render'
        img_group = ['image']
        mock_widget = mock.Mock()
        mock_widget.widgets = []
        self.w.imageViewWidget.widgets.append(mock_widget)
        with mock.patch(PATCH_RENDER) as mock_render_call:
            self.w.render(img_group)

        mock_render_call.assert_called_once_with(img_group)

    def test_msg_box_called_if_no_duplicates_found(self):
        PATCH_BOX = 'PyQt5.QtWidgets.QMessageBox'
        mock_box = mock.Mock()
        with mock.patch(PATCH_BOX, return_value=mock_box):
            self.w.render([])

        mock_box.exec.assert_called_once_with()


class TestMainFormMethodProcessingFinished(TestMainForm):

    def test_attr_processing_run_set_to_False(self):
        self.w.processing_run = True
        self.w.processingFinished()

        self.assertFalse(self.w.processing_run)

    def test_switchStartBtn_called(self):
        with mock.patch(MAIN_WINDOW+'MainWindow.switchStartBtn') as mock_btn:
            self.w.processingFinished()

        mock_btn.assert_called_once_with()

    def test_stopBtn_disabled(self):
        self.w.processingGrp.stopBtn.setEnabled(True)
        self.w.processingFinished()

        self.assertFalse(self.w.processingGrp.stopBtn.isEnabled())

    def test_progressBar_set_to_100(self):
        self.w.processingGrp.processProg.setValue(0)
        self.w.processingFinished()

        self.assertEqual(self.w.processingGrp.processProg.value(), 100)

    def test_autoSelectBtn_enabled_if_images_rendered(self):
        self.w.actionsGrp.autoSelectBtn.setEnabled(False)
        self.w.imageViewWidget.widgets = ['group_widget']
        self.w.processingFinished()

        self.assertTrue(self.w.actionsGrp.autoSelectBtn.isEnabled())

    def test_autoselect_menu_action_enabled_if_images_rendered(self):
        self.w.autoSelectAction.setEnabled(False)
        self.w.imageViewWidget.widgets = ['group_widget']
        self.w.processingFinished()

        self.assertTrue(self.w.autoSelectAction.isEnabled())

    def test_autoSelectBtn_disabled_if_images_not_rendered(self):
        self.w.actionsGrp.autoSelectBtn.setEnabled(False)
        self.w.imageViewWidget.widgets = []
        self.w.processingFinished()

        self.assertFalse(self.w.actionsGrp.autoSelectBtn.isEnabled())

    def test_autoselect_menu_action_disabled_if_images_not_rendered(self):
        self.w.autoSelectAction.setEnabled(False)
        self.w.imageViewWidget.widgets = []
        self.w.processingFinished()

        self.assertFalse(self.w.autoSelectAction.isEnabled())

    def test_change_interrupted_attr_to_False_if_it_is_True(self):
        self.w.interrupted = True
        self.w.interruptionMsg = mock.Mock()
        self.w.processingFinished()

        self.assertFalse(self.w.interrupted)

    def test_interruptionMsg_box_text_changed_if_interrupted_attr_True(self):
        self.w.interrupted = True
        self.w.interruptionMsg = mock.Mock()
        self.w.processingFinished()

        self.w.interruptionMsg.setText.assert_called_once()

    def test_Ok_btn_set_on_interruptionMsg_box_if_interrupted_attr_True(self):
        self.w.interrupted = True
        self.w.interruptionMsg = mock.Mock()
        self.w.processingFinished()

        self.w.interruptionMsg.setStandardButtons.assert_called_once_with(
            QtWidgets.QMessageBox.Ok
        )

    def test_interrupted_attr_stay_False_if_it_is_False(self):
        self.w.interrupted = False
        self.w.processingFinished()

        self.assertFalse(self.w.interrupted)

    def test_interruptionMsg_box_setText_not_called_if_interrupted_False(self):
        self.w.interrupted = False
        self.w.interruptionMsg = mock.Mock()
        self.w.processingFinished()

        self.w.interruptionMsg.setText.assert_not_called()

    def test_Ok_btn_not_set_on_interruptionMsg_box_if_interrupted_False(self):
        self.w.interrupted = False
        self.w.interruptionMsg = mock.Mock()
        self.w.processingFinished()

        self.w.interruptionMsg.setStandardButtons.assert_not_called()
