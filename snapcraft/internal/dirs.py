# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright (C) 2015 Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import snapcraft.internal.errors
import os.path
import site
import sys


def _find_windows_data_dir(topdir):
    # On Windows we need to search for data directory:
    #
    # Option (a) - Running with pip install --user.
    # > topdir=C:\Users\chris\AppData\Roaming\Python\Python37\site-packages
    # > site.USER_BASE=C:\Users\chris\AppData\Roaming\Python
    # > sys.prefix=c:\program files\python37
    #
    # In this case, data_dir should be:
    # > C:\Users\chris\AppData\Roaming\Python\share\snapcraft
    #
    # Option (b) - Running with pyinstaller frozen exe:
    # > topdir=C:\Users\chris\AppData\Local\Temp\_MEI110562
    # > site.USER_BASE=
    # > sys.prefix=C:\Users\chris\AppData\Local\Temp\_MEI110562
    #
    # In this case, data_dir should be:
    # > C:\Users\chris\AppData\Local\Temp\_MEI110562\share\snapcraft
    #
    # Option (c) - Running with pip install (system-wide).
    # > topdir=c:\program files\python37\lib\site-packages
    # > site.USER_BASE=C:\Users\chris\AppData\Roaming\Python
    # > sys.prefix=c:\program files\python37
    #
    # In this case, data_dir should be:
    # > c:\program files\python37\share\snapcraft

    # Handle Option (a).
    if topdir.startswith(site.USER_BASE):
        data_dir = os.path.join(site.USER_BASE, "share", "snapcraft")
        if os.path.exists(data_dir):
            return data_dir

    # Handle Options (b) & (c).
    if topdir.startswith(sys.prefix):
        data_dir = os.path.join(sys.prefix, "share", "snapcraft")
        if os.path.exists(data_dir):
            return data_dir

    # Do our best to find something...
    for data_dir in [topdir, sys.prefix, site.USER_BASE]:
        data_dir = os.path.join(data_dir, "share", "snapcraft")
        if os.path.exists(data_dir):
            return data_dir

    raise snapcraft.internal.errors.SnapcraftDataDirectoryMissingError()


def setup_dirs() -> None:
    """
    Ensure that snapcraft.common plugindir is setup correctly
    and support running out of a development snapshot
    """
    from snapcraft.internal import common

    topdir = os.path.abspath(os.path.join(__file__, "..", "..", ".."))

    # Only change the default if we are running from a checkout or from the
    # snap, or in Windows.
    if os.path.exists(os.path.join(topdir, "setup.py")):
        common.set_plugindir(os.path.join(topdir, "snapcraft", "plugins"))
        common.set_schemadir(os.path.join(topdir, "schema"))
        common.set_extensionsdir(os.path.join(topdir, "extensions"))
        common.set_keyringsdir(os.path.join(topdir, "keyrings"))

    # The default paths are relative to sys.prefix, which works well for
    # Snapcraft as a deb or in a venv. However, the Python plugin installs
    # packages into $SNAP/ as a prefix, while Python itself is contained in
    # $SNAP/usr/. As a result, using sys.prefix (which is '/usr') to find these
    # files won't work in the snap.
    elif common.is_snap():
        parent_dir = os.path.join(os.environ.get("SNAP"), "share", "snapcraft")
        common.set_plugindir(os.path.join(parent_dir, "plugins"))
        common.set_schemadir(os.path.join(parent_dir, "schema"))
        common.set_extensionsdir(os.path.join(parent_dir, "extensions"))
        common.set_keyringsdir(os.path.join(parent_dir, "keyrings"))
        common.set_legacy_snapcraft_dir(
            os.path.join(os.environ.get("SNAP"), "legacy_snapcraft")
        )

    elif sys.platform == "win32":
        common.set_plugindir(os.path.join(topdir, "snapcraft", "plugins"))

        data_dir = _find_windows_data_dir(topdir)
        common.set_schemadir(os.path.join(data_dir, "schema"))
        common.set_extensionsdir(os.path.join(data_dir, "extensions"))
        common.set_keyringsdir(os.path.join(data_dir, "keyrings"))

    else:
        raise snapcraft.internal.errors.SnapcraftDataDirectoryMissingError()
