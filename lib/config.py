from dataclasses import dataclass
from functools import cached_property
from json import loads as load_json_string
from os.path import join as path_join
from re import DOTALL as regex_DOTALL
from re import Pattern
from re import compile as regex_compile
from re import sub as regex_sub

from Typing import SCRIPT_ROOT


def read_jsonc(filepath: str):
    # read jsonc file
    with open(filepath, 'r') as f:
        jsonc_str = f.read()

    # Remove single-line comments (//)
    jsonc_str = regex_sub(r'//.*', '', jsonc_str)
    # Remove multi-line comments (/* */)
    jsonc_str = regex_sub(r'/\*.*?\*/', '', jsonc_str, flags=regex_DOTALL)

    # read json
    return load_json_string(jsonc_str)

@dataclass
class PatcherConfig():
    staging: str
    stardew_valley: str
    config_mod_regex: Pattern
    patch_version: int

    FILENAME = 'config_patcher.config.jsonc'

    __CONFIG_FILE_CONTENT_TEMPLATE = '''{
    // Full path to the Stardew Valley folder
    "stardew_valley": "{stardew_valley}",
    // Full path to the staging folder of Vortex
    "staging": "{staging}",
    // Regex pattern to match for config mods in the staging folder
    "config_mod_regex": "{config_mod_regex}",
    // DO NOT EDIT THIS VALUE
    // AS THIS TRACKS THE CURRENT PATCH VERSION
    "patch_version": {patch_version}
}'''

    @dataclass
    class Keys():
        STAGING = "staging"
        STARDEW_VALLEY = "stardew_valley"
        CONFIG_MOD_REGEX = "config_mod_regex"
        PATCH_VERSION = "patch_version"
    
    @classmethod
    def filepath(cls) -> str:
        return path_join(SCRIPT_ROOT, cls.FILENAME)
    
    @cached_property
    def mods(self) -> str:
        return path_join(self.stardew_valley, 'Mods')

    @classmethod
    def from_file(cls) -> 'PatcherConfig':
        data = read_jsonc(filepath=cls.filepath())
        
        assert isinstance(data, dict)

        def get_str(key: str) -> str:
            d = data[key]
            assert isinstance(d, str)
            return d
        
        def get_int(key: str) -> int:
            d = data[key]
            assert isinstance(d, int)
            return d

        staging = get_str(cls.Keys.STAGING)
        stardew_valley = get_str(cls.Keys.STARDEW_VALLEY)
        config_mod_regex = get_str(cls.Keys.CONFIG_MOD_REGEX)
        patch_version = get_int(cls.Keys.PATCH_VERSION)

        return cls(
            staging=staging,
            stardew_valley=stardew_valley,
            config_mod_regex=regex_compile(config_mod_regex),
            patch_version=patch_version,
        )
    
    def set_version(self, version: int):
        self.patch_version = version
    
    def increment_version(self):
        self.set_version(self.patch_version + 1)

    def save(self):
        config_file_content = {
            self.Keys.STAGING: self.staging.replace('\\','\\\\'),
            self.Keys.STARDEW_VALLEY: self.stardew_valley.replace('\\','\\\\'),
            self.Keys.CONFIG_MOD_REGEX: self.config_mod_regex.pattern.replace('\\','\\\\'),
            self.Keys.PATCH_VERSION: self.patch_version,
        }

        #jsonc_str = self.__CONFIG_FILE_CONTENT_TEMPLATE.format_map(config_file_content)
        jsonc_str = self.__CONFIG_FILE_CONTENT_TEMPLATE
        for key, value in config_file_content.items():
            placeholder = f"{{{key}}}"
            jsonc_str = jsonc_str.replace(placeholder, str(value))

        with open(self.filepath(), 'w') as f:
            f.write(jsonc_str)