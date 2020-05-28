'''Copyright 2020 Maxim Shpak <maxim.shpak@posteo.uk>

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

-------------------------------------------------------------------------------

Module implementing window "Preferences"
'''

from __future__ import annotations

import os
from typing import List, Union

from PyQt5 import QtCore, QtWidgets, uic

from doppelganger import config, resources
from doppelganger.logger import Logger

logger = Logger.getLogger('preferences')


def load_config() -> config.Config:
    '''Load and return config with the programme's preferences

    :return: "Config" object
    '''

    conf = config.Config()
    try:
        conf.load(resources.Config.CONFIG.abs_path) # pylint: disable=no-member
    except OSError as e:
        logger.error(e)

        log_file = resources.Log.ERROR.value # pylint: disable=no-member

        msg_box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Warning,
            'Errors',
            ('Cannot load preferences from file "config.p". Default '
             'preferences will be loaded. For more details, '
             f'see "{log_file}"')
        )
        msg_box.exec()
    return conf

def save_config(conf: config.Config) -> None:
    '''Save config with the preferences

    :param conf: "Config" object
    '''

    try:
        conf.save(resources.Config.CONFIG.abs_path) # pylint: disable=no-member
    except OSError as e:
        logger.error(e)

        log_file = resources.Log.ERROR.value # pylint: disable=no-member

        msg_box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Warning,
            'Error',
            ("Cannot save preferences into file 'config.p'. "
             f"For more details, see '{log_file}'")
        )
        msg_box.exec()

def setVal(widget: Widget, val: Value) -> None:
    '''Set value of widget

    :param widget: widget to set,
    :param val: value to set
    '''

    if isinstance(widget, QtWidgets.QSpinBox):
        widget.setValue(val)
    if isinstance(widget, QtWidgets.QComboBox):
        widget.setCurrentIndex(val)
    if isinstance(widget, (QtWidgets.QCheckBox, QtWidgets.QGroupBox)):
        widget.setChecked(val)

def val(widget: Widget) -> Value:
    '''Get value of widget

    :param widget: widget whose value to get,
    :return: value of widget
    '''

    if isinstance(widget, QtWidgets.QSpinBox):
        v = widget.value()
    if isinstance(widget, QtWidgets.QComboBox):
        v = widget.currentIndex()
    if isinstance(widget, (QtWidgets.QCheckBox, QtWidgets.QGroupBox)):
        v = widget.isChecked()

    return v


class PreferencesWindow(QtWidgets.QMainWindow):
    '''Implementing window "Preferences"'''

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        pref_ui = resources.UI.PREFERENCES.abs_path # pylint: disable=no-member
        uic.loadUi(pref_ui, self)

        self.widgets = self._gather_widgets()
        self._init_widgets()

        self.conf = load_config()
        self.update_prefs(self.conf)

        self.saveBtn.clicked.connect(self.saveBtn_click)
        self.cancelBtn.clicked.connect(self.cancelBtn_click)

        sizeHint = self.sizeHint()
        self.setMaximumSize(sizeHint)
        self.resize(sizeHint)

        self.setWindowModality(QtCore.Qt.ApplicationModal)

    def _gather_widgets(self) -> List[Widget]:
        widget_types = [QtWidgets.QComboBox, QtWidgets.QCheckBox,
                        QtWidgets.QSpinBox, QtWidgets.QGroupBox]
        widgets = []

        for w_type in widget_types:
            for w in self.findChildren(w_type):
                if w.property('conf_param') is not None:
                    widgets.append(w)
        return widgets

    def _init_widgets(self) -> None:
        for w in self.widgets:
            if w.property('conf_param') == 'cores':
                w.setMaximum(os.cpu_count() or 1)

    def update_prefs(self, conf: config.Config) -> None:
        '''Update the form with new preferences

        :param conf: "Config" object
        '''

        for w in self.widgets:
            setVal(w, conf[w.property('conf_param')])

    def gather_prefs(self):
        '''Gather checked/unchecked/filled by the user options
        and update the config
        '''

        for w in self.widgets:
            self.conf[w.property('conf_param')] = val(w)

    def saveBtn_click(self) -> None:
        self.gather_prefs()
        save_config(self.conf)
        self.close()

    def cancelBtn_click(self) -> None:
        self.close()


###################################Types#######################################
Widget = Union[QtWidgets.QSpinBox, QtWidgets.QComboBox,
               QtWidgets.QCheckBox, QtWidgets.QGroupBox] # preference widgets
Value = Union[int, str] # values of preference widgets
###############################################################################
