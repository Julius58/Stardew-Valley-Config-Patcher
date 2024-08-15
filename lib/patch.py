from dataclasses import dataclass
from functools import cached_property
from json import dump as json_dump
from json import dumps as json_dumps
from json import load as json_load
from json import loads as json_loads
from os import listdir, makedirs
from os.path import exists as path_exists
from os.path import isfile, dirname
from os.path import join as path_join
from re import compile as regex_compile
from typing import Any, Tuple

from lib.config import PatcherConfig
from lib.ui.console import ConsoleUserInterface

PATCH_FOLDER_NAME = 'Patches'

def PATCH_FOLDER(config: PatcherConfig) -> str:
    return path_join(config.stardew_valley, PATCH_FOLDER_NAME)
    
def _config_diff_(config: dict, patch: dict) -> Tuple[dict, dict, dict]:
    #region Diff
    def diff(config: dict, patch: dict) -> Tuple[dict | None, dict | None, dict | None]:
        create_on_missing, overwrite, remove = dict(), dict(), dict()

        for key, config_value in config.items():
            if key not in patch: # Create on missing
                create_on_missing[key] = config_value
            else:
                patch_value = patch[key]
                if type(config_value) != type(patch_value): # New config structure
                    overwrite[key] = config_value
                else:
                    if isinstance(config_value, dict): # Recursive scan
                        con, o , r = diff(config_value, patch_value)
                        # Update dictionaries
                        if con is not None:
                            create_on_missing[key] = con
                        if o is not None:
                            overwrite[key] = o
                        if r is not None:
                            remove[key] = r
                    else:
                        if not config_value.__eq__(patch_value): # Overwrite Value
                            overwrite[key] = config_value

        # Check for removed key-value pairs
        for key in set(patch.keys()).difference(set(config.keys())):
            remove[key] = {}
        
        return create_on_missing if len(create_on_missing) > 0 else None, overwrite if len(overwrite) > 0 else None, remove if len(remove) > 0 else None
    #endregion Diff
    
    con, o, r = diff(config, patch)

    if not isinstance(con, dict):
        con = {}
    if not isinstance(o, dict):
        o = {}
    if not isinstance(r, dict):
        r = {}

    return con, o, r

@dataclass(init=False)
class Patch():
    create_on_missing: str
    overwrite: str
    remove: str

    @cached_property
    def _create_on_missing(self) -> dict[str, Any]:
        return json_loads(self.create_on_missing)
    
    @cached_property
    def _overwrite(self) -> dict[str, Any]:
        return json_loads(self.overwrite)
    
    @cached_property
    def _remove(self) -> dict:
        return json_loads(self.remove)

    def __init__(self, *args: str) -> None:
        assert len(args) == 3

        self.create_on_missing = args[0]
        self.overwrite = args[1]
        self.remove = args[2]

    def __json__(self) -> list[str]:
        return [self.create_on_missing, self.overwrite, self.remove]

    @classmethod
    def from_dicts(cls, create_on_missing: dict = {}, overwrite: dict = {}, remove: dict = {}) -> 'Patch':
        return cls(
            json_dumps(create_on_missing),
            json_dumps(overwrite),
            json_dumps(remove),
        )

    @classmethod
    def new_patch(cls, config_path: str, old_patches: list['Patch'], rel_path: str, cui: ConsoleUserInterface) -> 'Patch | None':
        patched_config = {}

        for patch in old_patches:
            patched_config = patch._apply_(patched_config)

        if not isfile(config_path):
            return None
        
        with open(config_path, 'r') as f:
            on_disk_config = json_load(f)

        create_on_missing, overwrite, remove = cui.compare(rel_path, on_disk=on_disk_config, patch=patched_config)

        if len(create_on_missing) == 0 and len(overwrite) == 0 and len(remove) == 0:
            return None

        return Patch.from_dicts(
            create_on_missing=create_on_missing,
            overwrite=overwrite,
            remove=remove,
        )
    
    @staticmethod
    def _apply_on_missing_(on_disk: dict, patch: dict) -> None:
        for key, patch_value in patch.items():
            if key not in on_disk:
                on_disk[key] = patch_value
            else:
                if isinstance(patch_value, dict):
                    on_disk_value = on_disk[key]

                    assert isinstance(on_disk_value, dict) # Invalid Config

                    Patch._apply_on_missing_(on_disk_value, patch_value)

    @staticmethod
    def _apply_overwrite_(on_disk: dict, patch: dict) -> None:
        for key, patch_value in patch.items():
            if (
                isinstance(patch_value, dict)
                and key in on_disk
                and isinstance((on_disk_value := on_disk[key]), dict)
            ):
                Patch._apply_overwrite_(on_disk_value, patch_value)
            else:
                on_disk[key] = patch_value

    @staticmethod
    def _apply_remove_(on_disk: dict, patch: dict) -> None:
        for key, patch_value in patch.items():
            if key not in on_disk:
                continue

            assert isinstance(patch_value, dict)

            if len(patch_value) > 0: # contains sub keys
                on_disk_value = on_disk[key]
                assert isinstance(on_disk_value, dict)

                Patch._apply_remove_(on_disk_value, patch_value)
            else:
                on_disk.pop(key)


    def _apply_(self, config: dict | None) -> dict:
        if config is None:
            config = {}

        self._apply_on_missing_(config, self._create_on_missing)
        self._apply_overwrite_(config, self._overwrite)
        self._apply_remove_(config, self._remove)

        return config       

    def apply(self, config_path: str) -> None:
        if isfile(config_path):
            with open(config_path, 'r') as f:
                config = json_load(f)
        else:
            config = None

        config = self._apply_(config)
        # TODO: add option to remove config files

        folder = dirname(config_path)
        if not path_exists(folder):
            makedirs(folder)

        with open(config_path, 'w') as f:
            json_dump(config, f, indent=2)

@dataclass
class PatchFile(dict[str, Patch]):
    FILENAME_TEMPLATE = 'v{version}.patch'
    FILENAME_PATTERN = r'^[vV](\d+)\.patch$'
    FILENAME_REGEX = regex_compile(FILENAME_PATTERN)
    version: int
    
    def __init__(self, filename: str, config: PatcherConfig):
        if not (match := self.FILENAME_REGEX.match(filename)):
            raise ValueError(f'Patch file must be of pattern "{self.FILENAME_PATTERN}", put got "{filename}" instead.')
        
        filepath = path_join(PATCH_FOLDER(config), filename)
        assert isfile(filepath)

        version = int(match.group(1))

        self.version = version

        with open(filepath, 'r') as f:
            json = json_load(f)

        assert isinstance(json, dict)

        for key, value in json.items():
            self[key] = Patch(*value)

    @classmethod
    def create_and_save(cls, version: int, patches: dict[str, Patch], config: PatcherConfig) -> None:
        patch_folder = PATCH_FOLDER(config)

        if not path_exists(patch_folder):
            makedirs(patch_folder)

        filename = cls.FILENAME_TEMPLATE.format(version=version)
        filepath = path_join(patch_folder, filename)
        if path_exists(filepath):
            raise ValueError(f"File {filename} already exists")
        
        json_patches = {k: p.__json__() for k, p in patches.items()}
        
        with open(filepath, 'w') as f:
            json_dump(json_patches, f, indent=None)

def load_patches(config: PatcherConfig) -> dict[int, PatchFile]:
    patchfiles: dict[int, PatchFile] = {}
    for item in listdir(PATCH_FOLDER(config)):
        try:
            pf = PatchFile(item, config)
            patchfiles[pf.version] = pf
        except Exception as e:
            print(e)

    return patchfiles