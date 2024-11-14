from collections import namedtuple
from functools import lru_cache
from os.path import join as path_join, isdir, isfile
from os import makedirs
from typing import Any, NamedTuple, Optional, Tuple
from json import load as json_load, dump as json_dump

from Typing import SCRIPT_ROOT
from lib.ui.items import Direction

ModName = str
FlatKey = str
ModPatchValue = NamedTuple('ModPatchValue', [('direction', Direction), ('value', Any)])
ModPatchSettings = dict[FlatKey, ModPatchValue]
PatchSettings = dict[ModName, ModPatchSettings]


class PatchCreationConfig():
    _CONFIG_FOLDER_NAME = 'create_configs'
    _EXTENSION = '.cc'

    _settings: PatchSettings
    _config_folder_name: Optional[str]

    def __init__(self, config_folder_name: Optional[str], settings: Optional[dict[str, dict]] = None):
        self._settings = settings if settings else {}
        self._config_folder_name = config_folder_name

    @lru_cache
    @classmethod
    def _get_config_folder_(cls) -> str:
        return path_join(SCRIPT_ROOT, cls._CONFIG_FOLDER_NAME)

    @classmethod
    def _create_filepath_(cls, config_folder_name: str) -> str:
        return path_join(cls._get_config_folder_(), f"{config_folder_name}{cls._EXTENSION}")
    
    @classmethod
    def read(cls, config_folder_name: str) -> 'PatchCreationConfig':
        settings: Optional[dict] = None
        path = cls._create_filepath_(config_folder_name)

        if isfile(path):
            with open(path, 'r') as f:
                settings = json_load(f)

            assert isinstance(settings, dict)
            for mod, d in settings.items():
                assert isinstance(mod, str)
                assert isinstance(d, dict)

                for key in d.keys():
                    assert isinstance(key, str)
        
        return PatchCreationConfig(config_folder_name, settings)
    
    def write(self) -> None:
        if self._config_folder_name is None:
            return
        
        path = self._create_filepath_(self._config_folder_name)
        folder_path = self._get_config_folder_()

        if not isdir(folder_path):
            makedirs(folder_path)

        with open(path, 'w') as f:
            json_dump(self._settings, f, indent=None)

    def get_creation_state(self, mod_config_path: str, config_data: dict[str, Any]) -> dict[str, Direction]:
        mod_settings = self._settings.get(mod_config_path, None)
        if mod_settings is None:
            return dict()
        
        res: dict[str, Direction] = {}
        for key, c_value in config_data.items():
            if (key in mod_settings) and (m_value := mod_settings[key]) != c_value:
                mod_settings[key] = m_value

        return res

    def _create_mod_settings_(self, patched_config: dict[str, Any], user_choice: dict[str, Direction]):
        patched_keys = set(patched_config.keys())
        keys = patched_keys.intersection(user_choice.keys())
        assert keys == patched_keys

        return {
            k : ModPatchValue(direction=user_choice[k], value=patched_config[k])
            for k
            in patched_config
        }
    
    def add_mod_settings(self, mod_config_path: str, on_disk_flattend: dict[str, Any], user_choice: dict[str, Direction]):
        settings = self._create_mod_settings_(on_disk_flattend, user_choice)
        self._settings[mod_config_path] = settings
