from os import walk
from os.path import join as path_join
from os.path import relpath

from lib.config import PatcherConfig
from lib.creation_config import PatchCreationConfig
from lib.patch import Patch, PatchFile, load_patches
from lib.ui.console import ConsoleUserInterface


def _scan_for_configs_(configs_folder: str) -> list[str]:
    configs = []

    for root, dirs, files in walk(configs_folder):
        if 'config.json' in files:
            config_path = path_join(root, 'config.json')
            configs.append(config_path)
            # Prevent from further processing of subdirectories, as no more config.json files should be contained in the current folder.
            dirs.clear()

    return configs

def create_patch_file(configs_folder: str, config: PatcherConfig, cui: ConsoleUserInterface, pcc: PatchCreationConfig):
    patches = load_patches(config)
    patch_version = list(sorted(patches.keys()))[-1] + 1 if len(patches) > 0 else 0

    old_patches_map: dict[str, list[Patch]] = {}

    for version in sorted(patches.keys()):
        patchfile = patches[version]

        for rel_config_path, value in patchfile.items():
            config_path = path_join(configs_folder, rel_config_path)

            if config_path not in old_patches_map:
                old_patches_map[config_path] = list()
            old_patches_map[config_path].append(value)

    for cfg_file in _scan_for_configs_(configs_folder):
        if cfg_file not in old_patches_map:
            old_patches_map[cfg_file] = list()

    new_patches: dict[str, Patch] = {}

    for config_path, old_patches in old_patches_map.items():
        rel_config_path = relpath(config_path, configs_folder)
        patch = Patch.new_patch(config_path=config_path, old_patches=old_patches, rel_path=rel_config_path, cui=cui, pcc=pcc)
        if patch is not None:
            new_patches[rel_config_path] = patch

    if len(new_patches) > 0:
        PatchFile.create_and_save(version=patch_version, patches = new_patches, config=config)
        print(f"[ ] Created patch file version {patch_version}")
    else:
        print("[!] Nothing to patch.")