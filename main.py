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
import logging.handlers as handlers
import pathlib
import sys

from PyQt5.QtWidgets import QApplication

import doppelganger.gui.mainwindow as mw

if __name__ == '__main__':
    logger = logging.getLogger('main')
    logger.setLevel(logging.WARNING)
    log_path = pathlib.Path(__file__).parent / 'errors.log'
    rh = handlers.RotatingFileHandler(log_path, maxBytes=1024**2,
                                      backupCount=1)
    FORMAT = '{asctime} - {name} - {levelname} - {message}'
    formatter = logging.Formatter(fmt=FORMAT, style='{')
    rh.setFormatter(formatter)
    logger.addHandler(rh)

    app = QApplication(sys.argv)
    ex = mw.MainWindow()
    ex.show()
    sys.exit(app.exec_())
