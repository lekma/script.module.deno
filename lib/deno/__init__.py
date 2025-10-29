# -*- coding: utf-8 -*-


import os
import pathlib
import platform
import stat
import subprocess
import urllib
import zipfile

import xbmc, xbmcaddon, xbmcgui, xbmcvfs

from packaging.version import Version


# ------------------------------------------------------------------------------
# DenoInstaller

class DenoInstaller(object):

    __addon_id__ = "script.module.deno"
    __addon__ = xbmcaddon.Addon(__addon_id__)

    __kodi_path__ = "special://home/system/deno/deno"
    __path__ = pathlib.Path(xbmcvfs.translatePath(__kodi_path__))
    __url__ = urllib.parse.urlparse("https://dl.deno.land")

    __progress__ = xbmcgui.DialogProgress()
    __mode__ = (stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

    __current_version__ = None
    __latest_version__ = None
    __confirmed__ = None

    @classmethod
    def __log__(cls, msg, level=xbmc.LOGINFO):
        xbmc.log(f"[{cls.__addon_id__}] {msg}", level=level)

    @classmethod
    def __string__(cls, _id_):
        return cls.__addon__.getLocalizedString(_id_)

    @classmethod
    def __installed__(cls):
        return (cls.__path__.is_file() and os.access(cls.__path__, os.X_OK))

    @classmethod
    def __run__(cls, *args, check=True):
        return subprocess.run(
            args, check=check, stdout=subprocess.PIPE, text=True
        ).stdout.strip()

    @classmethod
    def __confirm__(cls):
        if cls.__confirmed__ is None:
            cls.__confirmed__ = xbmcgui.Dialog().yesno(
                cls.__string__(30000),
                cls.__string__(30001).format(cls.__latest__())
            )
        return cls.__confirmed__

    @classmethod
    def __current__(cls):
        if not cls.__current_version__:
            cls.__current_version__ = cls.__run__(
                f"{cls.__path__}", "eval", "-p", "Deno.version.deno"
            )
        return cls.__current_version__

    @classmethod
    def __latest__(cls):
        if not cls.__latest_version__:
            with urllib.request.urlopen(
                cls.__url__._replace(path="release-latest.txt").geturl()
            ) as response:
                cls.__latest_version__ =  response.read().decode("utf-8").strip()
        return cls.__latest_version__

    __systems__ = {
        "Linux": {
            "suffix": "unknown-linux-gnu"
        },
        "Darwin": {
            "suffix": "apple-darwin",
            "machines": {
                "arm64": "aarch64"
            }
        }
    }

    @classmethod
    def __target__(cls):
        system = cls.__systems__[platform.system()]
        machine = system.get("machines", {}).get(
            (machine := platform.machine()), machine
        )
        return f"deno-{machine}-{system['suffix']}"

    @classmethod
    def __update__(cls, block_count, block_size, total_size):
        cls.__progress__.update(
            ((block_count * block_size) * 100) // total_size
        )

    @classmethod
    def __install__(cls):
        url = cls.__url__._replace(
            path=f"release/{cls.__latest__()}/{cls.__target__()}.zip"
        ).geturl()
        cls.__progress__.create(
            cls.__string__(30000),
            cls.__string__(30002).format(cls.__latest__())
        )
        path, _ = urllib.request.urlretrieve(url, reporthook=cls.__update__)
        cls.__progress__.close()
        os.makedirs(cls.__path__.parent, exist_ok=True)
        with zipfile.ZipFile(path, "r") as zip_file:
            zip_file.extract("deno", path=cls.__path__.parent)
        pathlib.Path(path).unlink()
        cls.__path__.chmod(cls.__mode__)
        cls.__current_version__ = None
        xbmcgui.Dialog().ok(
            cls.__string__(30000),
            cls.__string__(30004).format(cls.__latest__())
        )

    # --------------------------------------------------------------------------

    def __init__(self):
        if (
            (
                (not self.__installed__()) or
                (Version(self.__current__()) < Version(self.__latest__()))
            ) and
            self.__confirm__()
        ):
            self.__install__()


# ------------------------------------------------------------------------------

def path():
    if ((installer := DenoInstaller()).__installed__()):
        return str(installer.__path__)

def version():
    if ((installer := DenoInstaller()).__installed__()):
        return str(installer.__current__())
