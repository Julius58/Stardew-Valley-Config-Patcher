from json import load as json_load
from os import makedirs
from os.path import basename, isdir, isfile
from os.path import join as path_join
from re import compile as regex_compile
from re import error as RegexError
from typing import Any, Tuple

from consolemenu import ConsoleMenu
from consolemenu.items import SelectionItem

from lib.config import PatcherConfig
from lib.ui.items import (Direction, DirectionSelectionItem, InputItem,
                          ValidatorItem)
from Typing import SCRIPT_ROOT


class _PatcherConfigCreationMenu(ConsoleMenu):
    _stardew_valley_folder_item: InputItem
    _staging_folder_item: InputItem
    _config_mod_regex_item: InputItem

    class PatcherConfigValidatorItem(ValidatorItem):
        def __init__(self, menu: ConsoleMenu) -> None:
            super().__init__('Confirm', menu, menu_char='c')

        def get_menu(self) -> '_PatcherConfigCreationMenu':
            assert isinstance(self.menu, _PatcherConfigCreationMenu)
            return self.menu

        def validate(self) -> bool:
            menu = self.get_menu()
            errors: list[str] = list()

            #region Stardew Valley folder path
            stardew_valley_folder_path = menu._stardew_valley_folder_item.get_return()
            item_name = menu._stardew_valley_folder_item.text

            if not isdir(stardew_valley_folder_path):
                errors.append(f'{item_name} is not a directory.')
            else:
                stardew_valley_exe_path = path_join(stardew_valley_folder_path, 'Stardew Valley.exe')

                if not isfile(stardew_valley_exe_path):
                    errors.append(f'{item_name} does not contain the Stardew Valley executable (Stardew Valley.exe).')
            #endregion Stardew Valley folder path

            #region Vortex staging folder path
            vortex_staging_folder_path = menu._staging_folder_item.get_return()
            item_name = menu._staging_folder_item.text
            
            if not isdir(vortex_staging_folder_path):
                errors.append(f'{item_name} is not a directory.')
            else:
                staging_folder_file_path = path_join(vortex_staging_folder_path, '__vortex_staging_folder')

                if not isfile(staging_folder_file_path):
                    errors.append(f'{item_name} does not contain \'__vortex_staging_folder\'.')
                else:
                    with open(staging_folder_file_path, 'r') as f:
                        d = json_load(f)
                    
                    if not isinstance(d, dict):
                        errors.append(f'{item_name}\'s __vortex_staging_folder is not a JSON dictionary.')
                    else:
                        game = d.get('game', '')
                        if game != 'stardewvalley':
                            errors.append(f'{item_name}\'s __vortex_staging_folder does not contain stardewvalley as the game, got instead: {game}')
            #endregion Vortex staging folder path

            #region Config mod regex
            config_mod_regex = menu._config_mod_regex_item.get_return()
            item_name = menu._config_mod_regex_item.text
            try:
                _ = regex_compile(config_mod_regex)
            except RegexError as re_err:
                errors.append(str(re_err))
            #endregion Config mod regex

            if len(errors) > 0:
                menu.prologue_text = '\n'.join(errors)
                return False

            return True

    def __init__(self) -> None:
        super().__init__(
            title='Create a new PatcherConfig',
            show_exit_option=False
        )

        self._stardew_valley_folder_item = InputItem(item_text='Stardew Valley folder path', prompt='Enter the full path to the Stardew Valley folder: ', menu=self, menu_char='v')
        self._staging_folder_item = InputItem(item_text='Vortex mod staging folder path', prompt='Enter the full path to the staging folder of Vortex: ', menu=self, menu_char='s')
        self._config_mod_regex_item = InputItem(item_text='Config mod regex pattern', prompt='Enter a valid regex pattern to search for config mod folders (e.g. \'^Config - .+\'): ', menu=self, menu_char='r')

        self.append_item(self._stardew_valley_folder_item)
        self.append_item(self._staging_folder_item)
        self.append_item(self._config_mod_regex_item)

        self.append_item(self.PatcherConfigValidatorItem(self))

    def show(self) -> PatcherConfig:
        self.prologue_text = None
        super().show(False)

        return PatcherConfig(
            staging=self._staging_folder_item.get_return(),
            stardew_valley=self._stardew_valley_folder_item.get_return(),
            config_mod_regex=regex_compile(self._config_mod_regex_item.get_return()),
            patch_version=-1,
        )

class _CompareMenu(ConsoleMenu):
    def __init__(self) -> None:
        super().__init__(
            title='',
            show_exit_option=True,
            exit_option_text='Confirm',
            exit_menu_char='c',
        )

    def _flatten_dict_(self, d: dict, parent_key='', sep='.') -> dict:
        items: list[Tuple[str, Any]] = []

        for k, v in d.items():
            new_key = f'{parent_key}{sep}{k}' if parent_key else k

            if isinstance(v, dict):
                items.extend(self._flatten_dict_(d=v, parent_key=new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    def _unflatten_dict_(self, d: dict, sep='.') -> dict:
        result_dict = {}

        for k, v in d.items():
            keys = k.split(sep)
            d_temp: dict = result_dict

            for key in keys[:-1]:
                d_temp = d_temp.setdefault(key, {})

            d_temp[keys[-1]] = v

        return result_dict
    
    def show(self, filename: str, on_disk: dict, patch: dict) -> Tuple[dict, dict, dict]:
        self.subtitle = filename

        on_disk_flattend = self._flatten_dict_(on_disk)
        patch_flattend = self._flatten_dict_(patch)
        
        CREATE_D_IDENT, OVERWRITE_D_IDENT, REMOVE_D_IDENT = 0,1,2
        create_d, overwrite_d, remove_d = dict(), dict(), dict()
        key_map: dict[str, Tuple[int, dict]] = {}

        for k, on_disk_value in on_disk_flattend.items():
            if k in patch_flattend:
                patch_value = patch_flattend[k]

                if on_disk_value != patch_value:
                    key_map[k] = (OVERWRITE_D_IDENT, overwrite_d)
            else:
                key_map[k] = (CREATE_D_IDENT, create_d)

        for k in patch_flattend.keys():
            if k not in on_disk_flattend:
                key_map[k] = (REMOVE_D_IDENT, remove_d)

        self.items.clear()

        if len(key_map) < 1:
            return {}, {}, {}

        for k, d in key_map.items():
            id_, d = d
            on_disk_value = 'REMOVE' if id_ == REMOVE_D_IDENT else str(on_disk_flattend[k])
            patch_value = 'IGNORE' if id_ == CREATE_D_IDENT else str(patch_flattend[k])

            self.append_item(DirectionSelectionItem(
                key=k,
                on_disk_value=on_disk_value,
                default_value=Direction.CONFIG,
                patch_value=patch_value,
                menu=self
            ))
            
        super().show(True)

        for item in self.items:
            if not isinstance(item, DirectionSelectionItem):
                continue

            k = item.get_key()

            id_, d = key_map[k]

            match item.get_return():
                case Direction.CONFIG:
                    if id_ == REMOVE_D_IDENT:
                        d[k] = {}
                    else:
                        d[k] = on_disk_flattend[k]
                case Direction.PATCH:
                    if id_ != CREATE_D_IDENT:
                        d[k] = patch_flattend[k]
                case Direction.IGNORE:
                    continue
        
        create_d_nested = self._unflatten_dict_(create_d)
        overwrite_d_nested = self._unflatten_dict_(overwrite_d)
        remove_d_nested = self._unflatten_dict_(remove_d)

        return create_d_nested, overwrite_d_nested, remove_d_nested

class FolderSelectionMenu(ConsoleMenu):
    def __init__(self):
        super().__init__(title='Select output folder', show_exit_option=True, exit_option_text='Temporary folder', exit_menu_char='t')

    def show(self, folders: list[str]) -> str:
        self.items.clear()
        idx_map: dict[str, str] = {}

        for idx, folder in enumerate(folders):
            name = basename(folder)
            idx_map[name] = folder
            self.append_item(SelectionItem(
                text=name,
                index=idx,
                menu=self,
            ))


        super().show(True)

        sel_item = self.selected_item

        if sel_item and sel_item != self.exit_item:
            assert isinstance(sel_item, SelectionItem)
            return idx_map[sel_item.get_text()]
        else:
            temp_folder = path_join(SCRIPT_ROOT, 'temp')
            if not isdir(temp_folder):
                makedirs(temp_folder)
            return temp_folder

class ConsoleUserInterface():
    _patcherConfig_creation_menu: _PatcherConfigCreationMenu
    _compare_menu: _CompareMenu
    _output_folder_selection_menu: FolderSelectionMenu

    def __init__(self) -> None:
        self._patcherConfig_creation_menu = _PatcherConfigCreationMenu()
        self._compare_menu = _CompareMenu()
        self._output_folder_selection_menu = FolderSelectionMenu()

    def create_PatcherConfig(self) -> PatcherConfig:
        return self._patcherConfig_creation_menu.show()

    def compare(self, filename: str, on_disk: dict, patch: dict) -> Tuple[dict, dict, dict]:
        return self._compare_menu.show(filename=filename, on_disk=on_disk, patch=patch)
    
    def output_folder(self, folders: list[str]) -> str:
        return self._output_folder_selection_menu.show(folders=folders)